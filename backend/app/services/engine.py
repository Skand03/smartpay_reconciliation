"""Deterministic Financial Reconciliation Engine for SmartPay."""
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from typing import List, Dict, Any, Tuple, Optional
from collections import defaultdict
from app.schemas import (
    PlatformTransaction,
    BankSettlement,
    ReconciliationRow,
    ReconciliationSummary,
    ReconciliationResponse
)

def parse_date(date_str: str) -> Optional[date]:
    if not date_str:
        return None
    try:
        clean_str = date_str.split("T")[0].strip()
        return datetime.strptime(clean_str, "%Y-%m-%d").date()
    except Exception:
        return None

def format_curr(val: Decimal) -> str:
    return str(val.quantize(Decimal("0.01"), rounding=ROUND_HALF_UP))

class ReconciliationEngine:
    def __init__(self, settlement_window_days: int = 2):
        self.settlement_window_days = settlement_window_days

    def reconcile(
        self,
        platform_records: List[PlatformTransaction],
        bank_records: List[BankSettlement]
    ) -> ReconciliationResponse:
        
        output_rows: List[ReconciliationRow] = []
        
        # Track assignments to ensure 100% accounting
        matched_platform_indices = set()
        matched_bank_indices = set()
        
        # Summary trackers
        tot_plt_amt = Decimal("0.00")
        tot_bnk_gross = Decimal("0.00")
        tot_bnk_net = Decimal("0.00")
        tot_bnk_fees = Decimal("0.00")
        
        for p in platform_records:
            tot_plt_amt += p.amount
        for b in bank_records:
            tot_bnk_gross += b.gross_amount
            tot_bnk_net += b.net_amount
            tot_bnk_fees += b.fee_amount

        # Counts
        counts = defaultdict(int)
        duplicate_plt_exposure = Decimal("0.00")
        duplicate_bnk_exposure = Decimal("0.00")
        unmatched_refund_exposure = Decimal("0.00")
        timing_diff_volume = Decimal("0.00")
        rounding_diff_net = Decimal("0.00")
        unsettled_plt_volume = Decimal("0.00")
        unclaimed_bnk_volume = Decimal("0.00")
        total_discrepancy_amount = Decimal("0.00")
        
        category_exposure = defaultdict(lambda: Decimal("0.00"))

        # -------------------------------------------------------------
        # PASS 1: Identify Duplicate Platform Records
        # -------------------------------------------------------------
        plt_by_id = defaultdict(list)
        for idx, p in enumerate(platform_records):
            plt_by_id[p.transaction_id].append((idx, p))
            
        duplicate_plt_indices = set()
        for tid, instances in plt_by_id.items():
            if len(instances) > 1:
                # Primary is instances[0]
                for dup_idx, dup_p in instances[1:]:
                    duplicate_plt_indices.add(dup_idx)
                    matched_platform_indices.add(dup_idx)
                    counts["duplicate_platform"] += 1
                    duplicate_plt_exposure += dup_p.amount
                    category_exposure["Duplicate Platform"] += dup_p.amount
                    total_discrepancy_amount += dup_p.amount
                    
                    output_rows.append(ReconciliationRow(
                        id=f"PLT-ROW-{dup_p.source_row}",
                        source="PLATFORM",
                        record_id=dup_p.transaction_id,
                        order_id=dup_p.order_id,
                        date=dup_p.timestamp,
                        amount=format_curr(dup_p.amount),
                        currency=dup_p.currency,
                        status="DUPLICATE_PLATFORM",
                        difference_amount=format_curr(dup_p.amount),
                        category="Duplicate Entry",
                        explanation=f"Duplicate platform record detected. Primary record at source row {instances[0][1].source_row}. Financial exposure: ₹{format_curr(dup_p.amount)}."
                    ))

        # -------------------------------------------------------------
        # PASS 2: Identify Duplicate Bank Records
        # -------------------------------------------------------------
        bnk_by_id = defaultdict(list)
        for idx, b in enumerate(bank_records):
            # Duplicate by settlement_id or exact payload
            key = (b.settlement_id, b.platform_trx_id, b.bank_reference, b.settlement_date, b.gross_amount)
            bnk_by_id[b.settlement_id].append((idx, b))
            
        duplicate_bnk_indices = set()
        for sid, instances in bnk_by_id.items():
            if len(instances) > 1:
                for dup_idx, dup_b in instances[1:]:
                    duplicate_bnk_indices.add(dup_idx)
                    matched_bank_indices.add(dup_idx)
                    counts["duplicate_bank"] += 1
                    duplicate_bnk_exposure += dup_b.gross_amount
                    category_exposure["Duplicate Bank"] += dup_b.gross_amount
                    total_discrepancy_amount += dup_b.gross_amount
                    
                    output_rows.append(ReconciliationRow(
                        id=f"BNK-ROW-{dup_b.source_row}",
                        source="BANK",
                        record_id=dup_b.settlement_id,
                        order_id=dup_b.order_id,
                        date=dup_b.settlement_date,
                        amount=format_curr(dup_b.gross_amount),
                        fee_amount=format_curr(dup_b.fee_amount),
                        net_amount=format_curr(dup_b.net_amount),
                        currency=dup_b.currency,
                        matched_record_id=dup_b.platform_trx_id,
                        status="DUPLICATE_BANK",
                        difference_amount=format_curr(dup_b.gross_amount),
                        category="Duplicate Entry",
                        explanation=f"Duplicate bank settlement detected. Primary record at source row {instances[0][1].source_row}. Financial exposure: ₹{format_curr(dup_b.gross_amount)}."
                    ))

        # -------------------------------------------------------------
        # PASS 3: Refund Validation & Reconciliation
        # -------------------------------------------------------------
        # Check all bank refunds (type == 'REFUND' or gross_amount < 0)
        # and platform refunds (type == 'REFUND')
        platform_payment_ids = {
            p.transaction_id: p for p in platform_records if p.type == "PAYMENT"
        }
        
        for b_idx, b in enumerate(bank_records):
            if b_idx in matched_bank_indices:
                continue
            if b.type == "REFUND" or b.gross_amount < Decimal("0"):
                orig_ref = b.original_payment_ref or b.platform_trx_id
                
                # Check if original parent exists in platform payments
                if not orig_ref or orig_ref not in platform_payment_ids:
                    # Unmatched Refund
                    matched_bank_indices.add(b_idx)
                    counts["unmatched_refund"] += 1
                    refund_val = abs(b.gross_amount)
                    unmatched_refund_exposure += refund_val
                    category_exposure["Unmatched Refund"] += refund_val
                    total_discrepancy_amount += refund_val
                    
                    output_rows.append(ReconciliationRow(
                        id=f"BNK-ROW-{b.source_row}",
                        source="BANK",
                        record_id=b.settlement_id,
                        order_id=b.order_id,
                        date=b.settlement_date,
                        amount=format_curr(b.gross_amount),
                        fee_amount=format_curr(b.fee_amount),
                        net_amount=format_curr(b.net_amount),
                        currency=b.currency,
                        matched_record_id=orig_ref,
                        status="UNMATCHED_REFUND",
                        difference_amount=format_curr(refund_val),
                        category="Unmatched Refund",
                        explanation=f"Bank refund of ₹{format_curr(refund_val)} has no valid originating platform payment ('{orig_ref}'). Flagged for operational investigation."
                    ))
                else:
                    # Check for corresponding platform refund record
                    # Find platform refund matching parent_transaction_id == orig_ref
                    found_p_refund = None
                    for p_idx, p in enumerate(platform_records):
                        if p_idx not in matched_platform_indices and p.type == "REFUND":
                            if p.parent_transaction_id == orig_ref or p.transaction_id == b.platform_trx_id:
                                found_p_refund = (p_idx, p)
                                break
                    
                    if found_p_refund:
                        p_idx, p = found_p_refund
                        matched_platform_indices.add(p_idx)
                        matched_bank_indices.add(b_idx)
                        counts["matched_refund"] += 1
                        
                        output_rows.append(ReconciliationRow(
                            id=f"PLT-ROW-{p.source_row}",
                            source="PLATFORM",
                            record_id=p.transaction_id,
                            order_id=p.order_id,
                            date=p.timestamp,
                            amount=format_curr(p.amount),
                            currency=p.currency,
                            matched_record_id=b.settlement_id,
                            status="MATCHED_REFUND",
                            difference_amount="0.00",
                            category="Matched",
                            explanation=f"Valid refund verified against original payment {p.parent_transaction_id} and matched with bank settlement {b.settlement_id}."
                        ))
                        output_rows.append(ReconciliationRow(
                            id=f"BNK-ROW-{b.source_row}",
                            source="BANK",
                            record_id=b.settlement_id,
                            order_id=b.order_id,
                            date=b.settlement_date,
                            amount=format_curr(b.gross_amount),
                            fee_amount=format_curr(b.fee_amount),
                            net_amount=format_curr(b.net_amount),
                            currency=b.currency,
                            matched_record_id=p.transaction_id,
                            status="MATCHED_REFUND",
                            difference_amount="0.00",
                            category="Matched",
                            explanation=f"Bank refund settlement matched with platform refund {p.transaction_id} (Parent payment: {orig_ref})."
                        ))

        # Check any remaining platform refunds lacking parent
        for p_idx, p in enumerate(platform_records):
            if p_idx not in matched_platform_indices and p.type == "REFUND":
                if not p.parent_transaction_id or p.parent_transaction_id not in platform_payment_ids:
                    matched_platform_indices.add(p_idx)
                    counts["unmatched_refund"] += 1
                    ref_val = abs(p.amount)
                    unmatched_refund_exposure += ref_val
                    category_exposure["Unmatched Refund"] += ref_val
                    total_discrepancy_amount += ref_val
                    
                    output_rows.append(ReconciliationRow(
                        id=f"PLT-ROW-{p.source_row}",
                        source="PLATFORM",
                        record_id=p.transaction_id,
                        order_id=p.order_id,
                        date=p.timestamp,
                        amount=format_curr(p.amount),
                        currency=p.currency,
                        status="UNMATCHED_REFUND",
                        difference_amount=format_curr(ref_val),
                        category="Unmatched Refund",
                        explanation=f"Platform refund references missing or non-existent parent transaction '{p.parent_transaction_id}'."
                    ))

        # -------------------------------------------------------------
        # PASS 4: Legitimate Partial Settlement Matching
        # -------------------------------------------------------------
        # Group available bank records by platform_trx_id
        avail_bank_by_plt_id = defaultdict(list)
        for b_idx, b in enumerate(bank_records):
            if b_idx not in matched_bank_indices and b.platform_trx_id:
                avail_bank_by_plt_id[b.platform_trx_id].append((b_idx, b))
                
        for p_idx, p in enumerate(platform_records):
            if p_idx in matched_platform_indices:
                continue
                
            candidate_banks = avail_bank_by_plt_id.get(p.transaction_id, [])
            if len(candidate_banks) > 1:
                # Multiple distinct bank records for this platform transaction
                sum_bank_gross = sum(b.gross_amount for _, b in candidate_banks)
                if sum_bank_gross == p.amount:
                    # Legitimate partial settlement match!
                    matched_platform_indices.add(p_idx)
                    counts["matched_partial"] += 1
                    settlement_ids = [b.settlement_id for _, b in candidate_banks]
                    
                    output_rows.append(ReconciliationRow(
                        id=f"PLT-ROW-{p.source_row}",
                        source="PLATFORM",
                        record_id=p.transaction_id,
                        order_id=p.order_id,
                        date=p.timestamp,
                        amount=format_curr(p.amount),
                        currency=p.currency,
                        matched_record_id=", ".join(settlement_ids),
                        status="MATCHED_PARTIAL",
                        difference_amount="0.00",
                        category="Matched Partial",
                        explanation=f"Legitimate partial settlements: Transaction of ₹{format_curr(p.amount)} settled across {len(candidate_banks)} bank records ({', '.join(settlement_ids)})."
                    ))
                    
                    for b_idx, b in candidate_banks:
                        matched_bank_indices.add(b_idx)
                        output_rows.append(ReconciliationRow(
                            id=f"BNK-ROW-{b.source_row}",
                            source="BANK",
                            record_id=b.settlement_id,
                            order_id=b.order_id,
                            date=b.settlement_date,
                            amount=format_curr(b.gross_amount),
                            fee_amount=format_curr(b.fee_amount),
                            net_amount=format_curr(b.net_amount),
                            currency=b.currency,
                            matched_record_id=p.transaction_id,
                            status="MATCHED_PARTIAL",
                            difference_amount="0.00",
                            category="Matched Partial",
                            explanation=f"Partial settlement tranche of ₹{format_curr(b.gross_amount)} for platform transaction {p.transaction_id}."
                        ))

        # -------------------------------------------------------------
        # PASS 5: Batch-Level Aggregation Rounding Difference
        # -------------------------------------------------------------
        # Group remaining platform and bank records by batch_id
        plt_batches = defaultdict(list)
        for p_idx, p in enumerate(platform_records):
            if p_idx not in matched_platform_indices and p.batch_id:
                plt_batches[p.batch_id].append((p_idx, p))
                
        bnk_batches = defaultdict(list)
        for b_idx, b in enumerate(bank_records):
            if b_idx not in matched_bank_indices and b.batch_id:
                bnk_batches[b.batch_id].append((b_idx, b))
                
        common_batches = set(plt_batches.keys()) & set(bnk_batches.keys())
        for bid in common_batches:
            p_list = plt_batches[bid]
            b_list = bnk_batches[bid]
            
            p_sum = sum(p.amount for _, p in p_list)
            b_sum = sum(b.gross_amount for _, b in b_list)
            diff = p_sum - b_sum
            
            # Check if there is an aggregation variance within tolerance (0 < |diff| <= 0.05 * len(p_list))
            if Decimal("0.00") < abs(diff) <= (Decimal("0.05") * len(p_list)):
                counts["rounding_difference"] += 1
                rounding_diff_net += abs(diff)
                category_exposure["Rounding Difference"] += abs(diff)
                total_discrepancy_amount += abs(diff)
                
                explanation_text = (
                    f"Batch aggregation rounding in batch '{bid}': Platform sum ₹{format_curr(p_sum)} vs "
                    f"Bank gross sum ₹{format_curr(b_sum)} (Variance: ₹{format_curr(diff)}). "
                    f"Arises from individual line item rounded splits vs aggregate batch settlement."
                )
                
                for p_idx, p in p_list:
                    matched_platform_indices.add(p_idx)
                    output_rows.append(ReconciliationRow(
                        id=f"PLT-ROW-{p.source_row}",
                        source="PLATFORM",
                        record_id=p.transaction_id,
                        order_id=p.order_id,
                        date=p.timestamp,
                        amount=format_curr(p.amount),
                        currency=p.currency,
                        batch_id=bid,
                        status="ROUNDING_DIFFERENCE",
                        difference_amount=format_curr(diff),
                        category="Rounding Difference",
                        explanation=explanation_text
                    ))
                    
                for b_idx, b in b_list:
                    matched_bank_indices.add(b_idx)
                    output_rows.append(ReconciliationRow(
                        id=f"BNK-ROW-{b.source_row}",
                        source="BANK",
                        record_id=b.settlement_id,
                        order_id=b.order_id,
                        date=b.settlement_date,
                        amount=format_curr(b.gross_amount),
                        fee_amount=format_curr(b.fee_amount),
                        net_amount=format_curr(b.net_amount),
                        currency=b.currency,
                        batch_id=bid,
                        status="ROUNDING_DIFFERENCE",
                        difference_amount=format_curr(diff),
                        category="Rounding Difference",
                        explanation=explanation_text
                    ))

        # -------------------------------------------------------------
        # PASS 6: 1:1 Matching (Exact Match, Timing Difference, Currency Mismatch)
        # -------------------------------------------------------------
        bank_by_plt_id_single = {}
        for b_idx, b in enumerate(bank_records):
            if b_idx not in matched_bank_indices and b.platform_trx_id:
                bank_by_plt_id_single[b.platform_trx_id] = (b_idx, b)
                
        for p_idx, p in enumerate(platform_records):
            if p_idx in matched_platform_indices:
                continue
                
            if p.transaction_id in bank_by_plt_id_single:
                b_idx, b = bank_by_plt_id_single[p.transaction_id]
                
                # Check currency
                if p.currency != b.currency:
                    # Currency mismatch!
                    matched_platform_indices.add(p_idx)
                    matched_bank_indices.add(b_idx)
                    counts["manual_review"] += 1
                    category_exposure["Manual Review"] += p.amount
                    total_discrepancy_amount += p.amount
                    
                    explanation_curr = f"Currency mismatch detected: Platform currency '{p.currency}' vs Bank currency '{b.currency}'. Cross-currency auto-match barred."
                    
                    output_rows.append(ReconciliationRow(
                        id=f"PLT-ROW-{p.source_row}",
                        source="PLATFORM",
                        record_id=p.transaction_id,
                        order_id=p.order_id,
                        date=p.timestamp,
                        amount=format_curr(p.amount),
                        currency=p.currency,
                        matched_record_id=b.settlement_id,
                        status="CURRENCY_MISMATCH",
                        difference_amount=format_curr(p.amount),
                        category="Manual Review",
                        explanation=explanation_curr
                    ))
                    output_rows.append(ReconciliationRow(
                        id=f"BNK-ROW-{b.source_row}",
                        source="BANK",
                        record_id=b.settlement_id,
                        order_id=b.order_id,
                        date=b.settlement_date,
                        amount=format_curr(b.gross_amount),
                        fee_amount=format_curr(b.fee_amount),
                        net_amount=format_curr(b.net_amount),
                        currency=b.currency,
                        matched_record_id=p.transaction_id,
                        status="CURRENCY_MISMATCH",
                        difference_amount=format_curr(b.gross_amount),
                        category="Manual Review",
                        explanation=explanation_curr
                    ))
                    continue

                # Amounts check
                amt_diff = p.amount - b.gross_amount
                p_date = parse_date(p.timestamp)
                b_date = parse_date(b.settlement_date)
                
                if amt_diff == Decimal("0.00"):
                    matched_platform_indices.add(p_idx)
                    matched_bank_indices.add(b_idx)
                    
                    # Timing Difference Check: Cross-Month within settlement window
                    p_date = parse_date(p.timestamp)
                    b_date = parse_date(b.settlement_date)
                    cross_month = False
                    days_lag = 0
                    if p_date and b_date:
                        days_lag = (b_date - p_date).days
                        cross_month = (p_date.month != b_date.month) or (p_date.year != b_date.year)
                            
                    if cross_month:
                        if 1 <= days_lag <= self.settlement_window_days:
                            counts["timing_difference"] += 1
                            timing_diff_volume += p.amount
                            category_exposure["Timing Difference"] += p.amount
                            
                            exp = (
                                f"Timing difference: Platform recorded on {p_date}, settled by bank on {b_date} "
                                f"({days_lag}-day cross-month lag, within configured {self.settlement_window_days}-day clearing window)."
                            )
                            output_rows.append(ReconciliationRow(
                                id=f"PLT-ROW-{p.source_row}",
                                source="PLATFORM",
                                record_id=p.transaction_id,
                                order_id=p.order_id,
                                date=p.timestamp,
                                amount=format_curr(p.amount),
                                currency=p.currency,
                                matched_record_id=b.settlement_id,
                                status="TIMING_DIFFERENCE",
                                difference_amount="0.00",
                                category="Timing Difference",
                                explanation=exp
                            ))
                            output_rows.append(ReconciliationRow(
                                id=f"BNK-ROW-{b.source_row}",
                                source="BANK",
                                record_id=b.settlement_id,
                                order_id=b.order_id,
                                date=b.settlement_date,
                                amount=format_curr(b.gross_amount),
                                fee_amount=format_curr(b.fee_amount),
                                net_amount=format_curr(b.net_amount),
                                currency=b.currency,
                                matched_record_id=p.transaction_id,
                                status="TIMING_DIFFERENCE",
                                difference_amount="0.00",
                                category="Timing Difference",
                                explanation=exp
                            ))
                        else:
                            # Settlement exceeded the configured settlement window
                            counts["manual_review"] += 1
                            category_exposure["Manual Review"] += p.amount
                            total_discrepancy_amount += p.amount
                            
                            exp = (
                                f"Settlement window exceeded: Platform recorded on {p_date}, settled on {b_date} "
                                f"({days_lag}-day lag exceeds configured {self.settlement_window_days}-day limit). Flagged for review."
                            )
                            output_rows.append(ReconciliationRow(
                                id=f"PLT-ROW-{p.source_row}",
                                source="PLATFORM",
                                record_id=p.transaction_id,
                                order_id=p.order_id,
                                date=p.timestamp,
                                amount=format_curr(p.amount),
                                currency=p.currency,
                                matched_record_id=b.settlement_id,
                                status="MANUAL_REVIEW",
                                difference_amount=format_curr(p.amount),
                                category="Manual Review",
                                explanation=exp
                            ))
                            output_rows.append(ReconciliationRow(
                                id=f"BNK-ROW-{b.source_row}",
                                source="BANK",
                                record_id=b.settlement_id,
                                order_id=b.order_id,
                                date=b.settlement_date,
                                amount=format_curr(b.gross_amount),
                                fee_amount=format_curr(b.fee_amount),
                                net_amount=format_curr(b.net_amount),
                                currency=b.currency,
                                matched_record_id=p.transaction_id,
                                status="MANUAL_REVIEW",
                                difference_amount=format_curr(b.gross_amount),
                                category="Manual Review",
                                explanation=exp
                            ))
                    else:
                        counts["matched_exact"] += 1
                        exp = f"Exact match: Transaction ID and amount verified. Bank fee: ₹{format_curr(b.fee_amount)}."
                        output_rows.append(ReconciliationRow(
                            id=f"PLT-ROW-{p.source_row}",
                            source="PLATFORM",
                            record_id=p.transaction_id,
                            order_id=p.order_id,
                            date=p.timestamp,
                            amount=format_curr(p.amount),
                            currency=p.currency,
                            matched_record_id=b.settlement_id,
                            status="MATCHED_EXACT",
                            difference_amount="0.00",
                            category="Matched",
                            explanation=exp
                        ))
                        output_rows.append(ReconciliationRow(
                            id=f"BNK-ROW-{b.source_row}",
                            source="BANK",
                            record_id=b.settlement_id,
                            order_id=b.order_id,
                            date=b.settlement_date,
                            amount=format_curr(b.gross_amount),
                            fee_amount=format_curr(b.fee_amount),
                            net_amount=format_curr(b.net_amount),
                            currency=b.currency,
                            matched_record_id=p.transaction_id,
                            status="MATCHED_EXACT",
                            difference_amount="0.00",
                            category="Matched",
                            explanation=exp
                        ))
                elif abs(amt_diff) <= Decimal("0.05"):
                    # Individual penny rounding
                    matched_platform_indices.add(p_idx)
                    matched_bank_indices.add(b_idx)
                    counts["rounding_difference"] += 1
                    rounding_diff_net += abs(amt_diff)
                    category_exposure["Rounding Difference"] += abs(amt_diff)
                    total_discrepancy_amount += abs(amt_diff)
                    
                    exp = f"1:1 penny rounding difference: Platform ₹{format_curr(p.amount)} vs Bank gross ₹{format_curr(b.gross_amount)} (Diff: ₹{format_curr(amt_diff)})."
                    output_rows.append(ReconciliationRow(
                        id=f"PLT-ROW-{p.source_row}",
                        source="PLATFORM",
                        record_id=p.transaction_id,
                        order_id=p.order_id,
                        date=p.timestamp,
                        amount=format_curr(p.amount),
                        currency=p.currency,
                        matched_record_id=b.settlement_id,
                        status="ROUNDING_DIFFERENCE",
                        difference_amount=format_curr(amt_diff),
                        category="Rounding Difference",
                        explanation=exp
                    ))
                    output_rows.append(ReconciliationRow(
                        id=f"BNK-ROW-{b.source_row}",
                        source="BANK",
                        record_id=b.settlement_id,
                        order_id=b.order_id,
                        date=b.settlement_date,
                        amount=format_curr(b.gross_amount),
                        fee_amount=format_curr(b.fee_amount),
                        net_amount=format_curr(b.net_amount),
                        currency=b.currency,
                        matched_record_id=p.transaction_id,
                        status="ROUNDING_DIFFERENCE",
                        difference_amount=format_curr(amt_diff),
                        category="Rounding Difference",
                        explanation=exp
                    ))
                else:
                    # Amount mismatch > 0.05 -> Manual Review
                    matched_platform_indices.add(p_idx)
                    matched_bank_indices.add(b_idx)
                    counts["manual_review"] += 1
                    category_exposure["Manual Review"] += abs(amt_diff)
                    total_discrepancy_amount += abs(amt_diff)
                    
                    exp = f"Amount mismatch > ₹0.05: Platform ₹{format_curr(p.amount)} vs Bank gross ₹{format_curr(b.gross_amount)} (Delta: ₹{format_curr(amt_diff)}). Requires manual review."
                    output_rows.append(ReconciliationRow(
                        id=f"PLT-ROW-{p.source_row}",
                        source="PLATFORM",
                        record_id=p.transaction_id,
                        order_id=p.order_id,
                        date=p.timestamp,
                        amount=format_curr(p.amount),
                        currency=p.currency,
                        matched_record_id=b.settlement_id,
                        status="AMOUNT_MISMATCH",
                        difference_amount=format_curr(amt_diff),
                        category="Manual Review",
                        explanation=exp
                    ))
                    output_rows.append(ReconciliationRow(
                        id=f"BNK-ROW-{b.source_row}",
                        source="BANK",
                        record_id=b.settlement_id,
                        order_id=b.order_id,
                        date=b.settlement_date,
                        amount=format_curr(b.gross_amount),
                        fee_amount=format_curr(b.fee_amount),
                        net_amount=format_curr(b.net_amount),
                        currency=b.currency,
                        matched_record_id=p.transaction_id,
                        status="AMOUNT_MISMATCH",
                        difference_amount=format_curr(amt_diff),
                        category="Manual Review",
                        explanation=exp
                    ))

        # -------------------------------------------------------------
        # PASS 7: Suggested Match on Order ID (Zero Auto Fuzzy Match)
        # -------------------------------------------------------------
        # For remaining bank and platform records, check order_id match
        avail_bank_by_order = {}
        for b_idx, b in enumerate(bank_records):
            if b_idx not in matched_bank_indices and b.order_id:
                avail_bank_by_order[b.order_id] = (b_idx, b)
                
        for p_idx, p in enumerate(platform_records):
            if p_idx in matched_platform_indices:
                continue
            if p.order_id and p.order_id in avail_bank_by_order:
                b_idx, b = avail_bank_by_order[p.order_id]
                if p.amount == b.gross_amount:
                    # Suggested match - routes strictly to MANUAL_REVIEW
                    matched_platform_indices.add(p_idx)
                    matched_bank_indices.add(b_idx)
                    counts["manual_review"] += 1
                    category_exposure["Manual Review"] += p.amount
                    
                    exp = (
                        f"Suggested Match: Order ID '{p.order_id}' and amount ₹{format_curr(p.amount)} match, "
                        f"but platform_trx_id was missing in bank record. Requires manual review."
                    )
                    output_rows.append(ReconciliationRow(
                        id=f"PLT-ROW-{p.source_row}",
                        source="PLATFORM",
                        record_id=p.transaction_id,
                        order_id=p.order_id,
                        date=p.timestamp,
                        amount=format_curr(p.amount),
                        currency=p.currency,
                        matched_record_id=b.settlement_id,
                        status="SUGGESTED_MATCH",
                        difference_amount="0.00",
                        category="Manual Review",
                        explanation=exp
                    ))
                    output_rows.append(ReconciliationRow(
                        id=f"BNK-ROW-{b.source_row}",
                        source="BANK",
                        record_id=b.settlement_id,
                        order_id=b.order_id,
                        date=b.settlement_date,
                        amount=format_curr(b.gross_amount),
                        fee_amount=format_curr(b.fee_amount),
                        net_amount=format_curr(b.net_amount),
                        currency=b.currency,
                        matched_record_id=p.transaction_id,
                        status="SUGGESTED_MATCH",
                        difference_amount="0.00",
                        category="Manual Review",
                        explanation=exp
                    ))

        # -------------------------------------------------------------
        # PASS 8: Residual Unmatched Accounting (100% Row Accounting)
        # -------------------------------------------------------------
        # Any remaining platform records
        for p_idx, p in enumerate(platform_records):
            if p_idx not in matched_platform_indices:
                matched_platform_indices.add(p_idx)
                counts["unmatched_platform"] += 1
                unsettled_plt_volume += p.amount
                category_exposure["Unmatched Platform"] += p.amount
                total_discrepancy_amount += p.amount
                
                output_rows.append(ReconciliationRow(
                    id=f"PLT-ROW-{p.source_row}",
                    source="PLATFORM",
                    record_id=p.transaction_id,
                    order_id=p.order_id,
                    date=p.timestamp,
                    amount=format_curr(p.amount),
                    currency=p.currency,
                    status="UNMATCHED_PLATFORM",
                    difference_amount=format_curr(p.amount),
                    category="Unmatched Platform",
                    explanation="Platform transaction recorded but no matching bank settlement found (unsettled / missing deposit)."
                ))

        # Any remaining bank records
        for b_idx, b in enumerate(bank_records):
            if b_idx not in matched_bank_indices:
                matched_bank_indices.add(b_idx)
                counts["unmatched_bank"] += 1
                unclaimed_bnk_volume += b.gross_amount
                category_exposure["Unmatched Bank"] += b.gross_amount
                total_discrepancy_amount += b.gross_amount
                
                output_rows.append(ReconciliationRow(
                    id=f"BNK-ROW-{b.source_row}",
                    source="BANK",
                    record_id=b.settlement_id,
                    order_id=b.order_id,
                    date=b.settlement_date,
                    amount=format_curr(b.gross_amount),
                    fee_amount=format_curr(b.fee_amount),
                    net_amount=format_curr(b.net_amount),
                    currency=b.currency,
                    matched_record_id=b.platform_trx_id,
                    status="UNMATCHED_BANK",
                    difference_amount=format_curr(b.gross_amount),
                    category="Unmatched Bank",
                    explanation="Bank settlement credited but no corresponding platform transaction identified (unclaimed funds)."
                ))

        summary = ReconciliationSummary(
            total_platform_count=len(platform_records),
            total_bank_count=len(bank_records),
            total_platform_amount=format_curr(tot_plt_amt),
            total_bank_gross_amount=format_curr(tot_bnk_gross),
            total_bank_net_amount=format_curr(tot_bnk_net),
            total_bank_fees=format_curr(tot_bnk_fees),
            currency="INR",
            
            matched_exact_count=counts["matched_exact"],
            matched_partial_count=counts["matched_partial"],
            matched_refund_count=counts["matched_refund"],
            timing_difference_count=counts["timing_difference"],
            rounding_difference_count=counts["rounding_difference"],
            duplicate_platform_count=counts["duplicate_platform"],
            duplicate_bank_count=counts["duplicate_bank"],
            unmatched_refund_count=counts["unmatched_refund"],
            unmatched_platform_count=counts["unmatched_platform"],
            unmatched_bank_count=counts["unmatched_bank"],
            manual_review_count=counts["manual_review"],
            
            total_discrepancy_amount=format_curr(total_discrepancy_amount),
            duplicate_platform_exposure=format_curr(duplicate_plt_exposure),
            duplicate_bank_exposure=format_curr(duplicate_bnk_exposure),
            unmatched_refund_exposure=format_curr(unmatched_refund_exposure),
            timing_difference_volume=format_curr(timing_diff_volume),
            rounding_difference_net=format_curr(rounding_diff_net),
            unsettled_platform_volume=format_curr(unsettled_plt_volume),
            unclaimed_bank_volume=format_curr(unclaimed_bnk_volume)
        )
        
        # Build status distribution for charts
        status_distribution = {
            "Matched Exact": counts["matched_exact"],
            "Matched Partial": counts["matched_partial"],
            "Matched Refund": counts["matched_refund"],
            "Timing Difference": counts["timing_difference"],
            "Rounding Difference": counts["rounding_difference"],
            "Duplicate Platform": counts["duplicate_platform"],
            "Duplicate Bank": counts["duplicate_bank"],
            "Unmatched Refund": counts["unmatched_refund"],
            "Unmatched Platform": counts["unmatched_platform"],
            "Unmatched Bank": counts["unmatched_bank"],
            "Manual Review": counts["manual_review"]
        }
        
        category_exposure_str = {
            k: format_curr(v) for k, v in category_exposure.items()
        }
        
        return ReconciliationResponse(
            summary=summary,
            records=output_rows,
            status_distribution=status_distribution,
            category_exposure=category_exposure_str
        )

