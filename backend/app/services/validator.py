"""CSV Validator and Parser for SmartPay."""
import csv
import io
from decimal import Decimal, InvalidOperation
from datetime import datetime
from typing import List, Tuple, Dict, Any
from app.schemas import PlatformTransaction, BankSettlement

PLATFORM_REQUIRED_HEADERS = [
    "transaction_id", "order_id", "customer_id", "amount",
    "currency", "timestamp", "status", "type"
]

BANK_REQUIRED_HEADERS = [
    "settlement_id", "bank_reference", "settlement_date",
    "gross_amount", "fee_amount", "net_amount", "currency",
    "settlement_status", "type"
]

def parse_decimal(value: Any, field_name: str, row_idx: int) -> Decimal:
    try:
        val_str = str(value).strip().replace(",", "")
        return Decimal(val_str)
    except (InvalidOperation, ValueError, TypeError):
        raise ValueError(f"Row {row_idx}: Invalid decimal format for '{field_name}': '{value}'")

def validate_and_parse_platform_csv(content: str) -> Tuple[List[PlatformTransaction], List[str]]:
    errors = []
    transactions = []
    
    # Strip potential UTF-8 BOM
    clean_content = content.lstrip('\ufeff')
    reader = csv.DictReader(io.StringIO(clean_content))
    
    if not reader.fieldnames:
        return [], ["Platform CSV is empty or has no header row."]
        
    fieldnames = [f.strip() for f in reader.fieldnames if f]
    missing_headers = [h for h in PLATFORM_REQUIRED_HEADERS if h not in fieldnames]
    if missing_headers:
        return [], [f"Platform CSV missing required headers: {', '.join(missing_headers)}"]
        
    for row_idx, row in enumerate(reader, start=2):
        try:
            tid = row.get("transaction_id", "").strip()
            if not tid:
                errors.append(f"Row {row_idx}: Missing 'transaction_id'.")
                continue
                
            order_id = row.get("order_id", "").strip()
            customer_id = row.get("customer_id", "").strip()
            currency = row.get("currency", "INR").strip().upper()
            status = row.get("status", "").strip().upper()
            tx_type = row.get("type", "PAYMENT").strip().upper()
            ts = row.get("timestamp", "").strip()
            parent_id = row.get("parent_transaction_id", "").strip() or None
            batch_id = row.get("batch_id", "").strip() or None
            
            amount = parse_decimal(row.get("amount", ""), "amount", row_idx)
            
            # Amount sign and logic checks
            if tx_type == "PAYMENT" and amount <= 0:
                errors.append(f"Row {row_idx}: Payment amount must be greater than 0, got {amount}.")
                continue
                
            transactions.append(PlatformTransaction(
                transaction_id=tid,
                order_id=order_id,
                customer_id=customer_id,
                amount=amount,
                currency=currency,
                timestamp=ts,
                status=status,
                type=tx_type,
                parent_transaction_id=parent_id,
                batch_id=batch_id,
                source_row=row_idx
            ))
        except Exception as e:
            errors.append(f"Row {row_idx}: {str(e)}")
            
    return transactions, errors

def validate_and_parse_bank_csv(content: str) -> Tuple[List[BankSettlement], List[str]]:
    errors = []
    settlements = []
    
    clean_content = content.lstrip('\ufeff')
    reader = csv.DictReader(io.StringIO(clean_content))
    
    if not reader.fieldnames:
        return [], ["Bank CSV is empty or has no header row."]
        
    fieldnames = [f.strip() for f in reader.fieldnames if f]
    missing_headers = [h for h in BANK_REQUIRED_HEADERS if h not in fieldnames]
    if missing_headers:
        return [], [f"Bank CSV missing required headers: {', '.join(missing_headers)}"]
        
    for row_idx, row in enumerate(reader, start=2):
        try:
            sid = row.get("settlement_id", "").strip()
            if not sid:
                errors.append(f"Row {row_idx}: Missing 'settlement_id'.")
                continue
                
            plt_id = row.get("platform_trx_id", "").strip() or None
            order_id = row.get("order_id", "").strip() or None
            bank_ref = row.get("bank_reference", "").strip()
            s_date = row.get("settlement_date", "").strip()
            currency = row.get("currency", "INR").strip().upper()
            s_status = row.get("settlement_status", "SETTLED").strip().upper()
            s_type = row.get("type", "SETTLEMENT").strip().upper()
            batch_id = row.get("batch_id", "").strip() or None
            orig_payment_ref = row.get("original_payment_ref", "").strip() or None
            
            gross = parse_decimal(row.get("gross_amount", ""), "gross_amount", row_idx)
            fee = parse_decimal(row.get("fee_amount", "0"), "fee_amount", row_idx)
            net = parse_decimal(row.get("net_amount", ""), "net_amount", row_idx)
            
            # Financial equation validation: net = gross - fee (tolerance: exact 0.00)
            expected_net = gross - fee
            if abs(net - expected_net) > Decimal("0.001"):
                errors.append(f"Row {row_idx}: Financial validation failed. gross ({gross}) - fee ({fee}) != net ({net}).")
                # Do not reject row entirely; still parse for auditability
            
            settlements.append(BankSettlement(
                settlement_id=sid,
                platform_trx_id=plt_id,
                order_id=order_id,
                bank_reference=bank_ref,
                settlement_date=s_date,
                gross_amount=gross,
                fee_amount=fee,
                net_amount=net,
                currency=currency,
                settlement_status=s_status,
                type=s_type,
                batch_id=batch_id,
                original_payment_ref=orig_payment_ref,
                source_row=row_idx
            ))
        except Exception as e:
            errors.append(f"Row {row_idx}: {str(e)}")
            
    return settlements, errors

