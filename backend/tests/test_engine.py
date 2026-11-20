"""Unit and Integration Tests for SmartPay Reconciliation Engine."""
import pytest
from decimal import Decimal
from app.schemas import PlatformTransaction, BankSettlement
from app.services.engine import ReconciliationEngine
from app.services.validator import validate_and_parse_platform_csv, validate_and_parse_bank_csv
from app.services.sample_generator import generate_sample_datasets

@pytest.fixture
def engine():
    return ReconciliationEngine(settlement_window_days=2)

def test_100_percent_row_accounting(engine):
    """Verify that every single input row is accounted for in output."""
    plt_csv, bnk_csv = generate_sample_datasets()
    plt_records, p_errs = validate_and_parse_platform_csv(plt_csv)
    bnk_records, b_errs = validate_and_parse_bank_csv(bnk_csv)
    
    assert len(p_errs) == 0
    assert len(b_errs) == 0
    
    result = engine.reconcile(plt_records, bnk_records)
    
    # Check total rows
    total_input_rows = len(plt_records) + len(bnk_records)
    total_output_rows = len(result.records)
    assert total_output_rows == total_input_rows, (
        f"Expected {total_input_rows} rows in reconciliation output, but got {total_output_rows}"
    )

def test_duplicate_platform_transaction(engine):
    """Verify duplicate platform transactions are detected, primary matched, duplicate preserved with exposure."""
    plt_records = [
        PlatformTransaction(
            transaction_id="TRX-101", order_id="ORD-1", customer_id="C-1",
            amount=Decimal("1500.00"), currency="INR", timestamp="2026-03-10T10:00:00Z",
            status="SUCCESS", type="PAYMENT", source_row=2
        ),
        PlatformTransaction(
            transaction_id="TRX-101", order_id="ORD-1", customer_id="C-1",
            amount=Decimal("1500.00"), currency="INR", timestamp="2026-03-10T10:00:00Z",
            status="SUCCESS", type="PAYMENT", source_row=3
        )
    ]
    bnk_records = [
        BankSettlement(
            settlement_id="STL-101", platform_trx_id="TRX-101", bank_reference="REF-1",
            settlement_date="2026-03-11", gross_amount=Decimal("1500.00"), fee_amount=Decimal("15.00"),
            net_amount=Decimal("1485.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", source_row=2
        )
    ]
    
    res = engine.reconcile(plt_records, bnk_records)
    
    assert res.summary.duplicate_platform_count == 1
    assert res.summary.duplicate_platform_exposure == "1500.00"
    
    dup_rows = [r for r in res.records if r.status == "DUPLICATE_PLATFORM"]
    assert len(dup_rows) == 1
    assert dup_rows[0].record_id == "TRX-101"
    assert dup_rows[0].difference_amount == "1500.00"

def test_duplicate_bank_settlement(engine):
    """Verify duplicate bank settlements are detected without silent deletion."""
    plt_records = [
        PlatformTransaction(
            transaction_id="TRX-201", order_id="ORD-2", customer_id="C-2",
            amount=Decimal("2000.00"), currency="INR", timestamp="2026-03-12T10:00:00Z",
            status="SUCCESS", type="PAYMENT", source_row=2
        )
    ]
    bnk_records = [
        BankSettlement(
            settlement_id="STL-201", platform_trx_id="TRX-201", bank_reference="REF-2",
            settlement_date="2026-03-13", gross_amount=Decimal("2000.00"), fee_amount=Decimal("20.00"),
            net_amount=Decimal("1980.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", source_row=2
        ),
        BankSettlement(
            settlement_id="STL-201", platform_trx_id="TRX-201", bank_reference="REF-2",
            settlement_date="2026-03-13", gross_amount=Decimal("2000.00"), fee_amount=Decimal("20.00"),
            net_amount=Decimal("1980.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", source_row=3
        )
    ]
    
    res = engine.reconcile(plt_records, bnk_records)
    assert res.summary.duplicate_bank_count == 1
    assert res.summary.duplicate_bank_exposure == "2000.00"
    
    dup_bank_rows = [r for r in res.records if r.status == "DUPLICATE_BANK"]
    assert len(dup_bank_rows) == 1
    assert dup_bank_rows[0].record_id == "STL-201"

def test_multiple_legitimate_partial_settlements(engine):
    """Verify multiple distinct bank settlements for 1 platform transaction reconcile as MATCHED_PARTIAL."""
    plt_records = [
        PlatformTransaction(
            transaction_id="TRX-301", order_id="ORD-3", customer_id="C-3",
            amount=Decimal("10000.00"), currency="INR", timestamp="2026-03-15T12:00:00Z",
            status="SUCCESS", type="PAYMENT", source_row=2
        )
    ]
    bnk_records = [
        BankSettlement(
            settlement_id="STL-301-A", platform_trx_id="TRX-301", bank_reference="REF-3A",
            settlement_date="2026-03-16", gross_amount=Decimal("6000.00"), fee_amount=Decimal("60.00"),
            net_amount=Decimal("5940.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", source_row=2
        ),
        BankSettlement(
            settlement_id="STL-301-B", platform_trx_id="TRX-301", bank_reference="REF-3B",
            settlement_date="2026-03-17", gross_amount=Decimal("4000.00"), fee_amount=Decimal("40.00"),
            net_amount=Decimal("3960.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", source_row=3
        )
    ]
    
    res = engine.reconcile(plt_records, bnk_records)
    assert res.summary.matched_partial_count == 1
    partial_rows = [r for r in res.records if r.status == "MATCHED_PARTIAL"]
    # 1 platform row + 2 bank rows = 3 rows in output
    assert len(partial_rows) == 3

def test_cross_month_timing_difference(engine):
    """Verify transaction recorded on March 31 and settled on April 2 is classified as TIMING_DIFFERENCE."""
    plt_records = [
        PlatformTransaction(
            transaction_id="TRX-401", order_id="ORD-4", customer_id="C-4",
            amount=Decimal("5000.00"), currency="INR", timestamp="2026-03-31T23:30:00Z",
            status="SUCCESS", type="PAYMENT", source_row=2
        )
    ]
    bnk_records = [
        BankSettlement(
            settlement_id="STL-401", platform_trx_id="TRX-401", bank_reference="REF-4",
            settlement_date="2026-04-02", gross_amount=Decimal("5000.00"), fee_amount=Decimal("50.00"),
            net_amount=Decimal("4950.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", source_row=2
        )
    ]
    
    res = engine.reconcile(plt_records, bnk_records)
    assert res.summary.timing_difference_count == 1
    timing_rows = [r for r in res.records if r.status == "TIMING_DIFFERENCE"]
    assert len(timing_rows) == 2

def test_unmatched_old_transaction_not_timing_difference(engine):
    """Verify transaction older than settlement window without settlement is UNMATCHED_PLATFORM."""
    plt_records = [
        PlatformTransaction(
            transaction_id="TRX-501", order_id="ORD-5", customer_id="C-5",
            amount=Decimal("3000.00"), currency="INR", timestamp="2026-03-01T10:00:00Z",
            status="SUCCESS", type="PAYMENT", source_row=2
        )
    ]
    bnk_records = []
    
    res = engine.reconcile(plt_records, bnk_records)
    assert res.summary.timing_difference_count == 0
    assert res.summary.unmatched_platform_count == 1
    assert res.records[0].status == "UNMATCHED_PLATFORM"

def test_batch_level_rounding_scenario(engine):
    """Verify batch-level aggregation rounding difference with documented math."""
    # 3 platform transactions summing to 1000.00
    plt_records = [
        PlatformTransaction(
            transaction_id="TRX-B1", order_id="ORD-B1", customer_id="C-1",
            amount=Decimal("333.33"), currency="INR", timestamp="2026-03-20T10:00:00Z",
            status="SUCCESS", type="PAYMENT", batch_id="BATCH-RND", source_row=2
        ),
        PlatformTransaction(
            transaction_id="TRX-B2", order_id="ORD-B2", customer_id="C-2",
            amount=Decimal("333.33"), currency="INR", timestamp="2026-03-20T10:00:00Z",
            status="SUCCESS", type="PAYMENT", batch_id="BATCH-RND", source_row=3
        ),
        PlatformTransaction(
            transaction_id="TRX-B3", order_id="ORD-B3", customer_id="C-3",
            amount=Decimal("333.34"), currency="INR", timestamp="2026-03-20T10:00:00Z",
            status="SUCCESS", type="PAYMENT", batch_id="BATCH-RND", source_row=4
        )
    ]
    # Bank batch settles 999.98 gross
    bnk_records = [
        BankSettlement(
            settlement_id="STL-B1", platform_trx_id="TRX-B1", bank_reference="REF-B1",
            settlement_date="2026-03-21", gross_amount=Decimal("333.33"), fee_amount=Decimal("3.33"),
            net_amount=Decimal("330.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", batch_id="BATCH-RND", source_row=2
        ),
        BankSettlement(
            settlement_id="STL-B2", platform_trx_id="TRX-B2", bank_reference="REF-B2",
            settlement_date="2026-03-21", gross_amount=Decimal("333.33"), fee_amount=Decimal("3.33"),
            net_amount=Decimal("330.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", batch_id="BATCH-RND", source_row=3
        ),
        BankSettlement(
            settlement_id="STL-B3", platform_trx_id="TRX-B3", bank_reference="REF-B3",
            settlement_date="2026-03-21", gross_amount=Decimal("333.32"), fee_amount=Decimal("3.33"),
            net_amount=Decimal("329.99"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", batch_id="BATCH-RND", source_row=4
        )
    ]
    
    res = engine.reconcile(plt_records, bnk_records)
    assert res.summary.rounding_difference_count == 1
    assert res.summary.rounding_difference_net == "0.02"
    
    rnd_rows = [r for r in res.records if r.status == "ROUNDING_DIFFERENCE"]
    assert len(rnd_rows) == 6  # 3 platform + 3 bank

def test_valid_refund_with_parent_transaction(engine):
    """Verify valid refund referencing parent original payment reconciles as MATCHED_REFUND."""
    plt_records = [
        PlatformTransaction(
            transaction_id="TRX-SALE-1", order_id="ORD-S1", customer_id="C-1",
            amount=Decimal("4000.00"), currency="INR", timestamp="2026-03-10T10:00:00Z",
            status="SUCCESS", type="PAYMENT", source_row=2
        ),
        PlatformTransaction(
            transaction_id="TRX-REF-1", order_id="ORD-S1", customer_id="C-1",
            amount=Decimal("4000.00"), currency="INR", timestamp="2026-03-15T15:00:00Z",
            status="REFUNDED", type="REFUND", parent_transaction_id="TRX-SALE-1", source_row=3
        )
    ]
    bnk_records = [
        BankSettlement(
            settlement_id="STL-SALE-1", platform_trx_id="TRX-SALE-1", bank_reference="REF-S1",
            settlement_date="2026-03-11", gross_amount=Decimal("4000.00"), fee_amount=Decimal("40.00"),
            net_amount=Decimal("3960.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", source_row=2
        ),
        BankSettlement(
            settlement_id="STL-REF-1", platform_trx_id="TRX-REF-1", bank_reference="REF-R1",
            settlement_date="2026-03-16", gross_amount=Decimal("-4000.00"), fee_amount=Decimal("0.00"),
            net_amount=Decimal("-4000.00"), currency="INR", settlement_status="SETTLED",
            type="REFUND", original_payment_ref="TRX-SALE-1", source_row=3
        )
    ]
    
    res = engine.reconcile(plt_records, bnk_records)
    assert res.summary.matched_refund_count == 1
    refund_rows = [r for r in res.records if r.status == "MATCHED_REFUND"]
    assert len(refund_rows) == 2

def test_unmatched_refund_without_parent(engine):
    """Verify refund with no valid original transaction is flagged as UNMATCHED_REFUND."""
    plt_records = []
    bnk_records = [
        BankSettlement(
            settlement_id="STL-GHOST-REF", platform_trx_id="TRX-GHOST", bank_reference="REF-G",
            settlement_date="2026-03-20", gross_amount=Decimal("-1500.00"), fee_amount=Decimal("0.00"),
            net_amount=Decimal("-1500.00"), currency="INR", settlement_status="SETTLED",
            type="REFUND", original_payment_ref="TRX-NONEXISTENT", source_row=2
        )
    ]
    
    res = engine.reconcile(plt_records, bnk_records)
    assert res.summary.unmatched_refund_count == 1
    assert res.summary.unmatched_refund_exposure == "1500.00"
    assert res.records[0].status == "UNMATCHED_REFUND"

def test_currency_mismatch_prevents_matching(engine):
    """Verify cross-currency records are prevented from matching and flagged for review."""
    plt_records = [
        PlatformTransaction(
            transaction_id="TRX-FX-1", order_id="ORD-FX", customer_id="C-FX",
            amount=Decimal("100.00"), currency="USD", timestamp="2026-03-10T10:00:00Z",
            status="SUCCESS", type="PAYMENT", source_row=2
        )
    ]
    bnk_records = [
        BankSettlement(
            settlement_id="STL-FX-1", platform_trx_id="TRX-FX-1", bank_reference="REF-FX",
            settlement_date="2026-03-11", gross_amount=Decimal("100.00"), fee_amount=Decimal("1.00"),
            net_amount=Decimal("99.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", source_row=2
        )
    ]
    
    res = engine.reconcile(plt_records, bnk_records)
    assert res.summary.matched_exact_count == 0
    assert res.summary.manual_review_count == 1
    mismatch_rows = [r for r in res.records if r.status == "CURRENCY_MISMATCH"]
    assert len(mismatch_rows) == 2

def test_configurable_settlement_window_affects_timing_classification():
    """Verify that changing the settlement window dynamically affects timing classification."""
    plt_records = [
        PlatformTransaction(
            transaction_id="TRX-LAG-2D", order_id="ORD-L2", customer_id="C-L2",
            amount=Decimal("5000.00"), currency="INR", timestamp="2026-03-31T23:30:00Z",
            status="SUCCESS", type="PAYMENT", source_row=2
        )
    ]
    bnk_records = [
        BankSettlement(
            settlement_id="STL-LAG-2D", platform_trx_id="TRX-LAG-2D", bank_reference="REF-L2",
            settlement_date="2026-04-02", gross_amount=Decimal("5000.00"), fee_amount=Decimal("50.00"),
            net_amount=Decimal("4950.00"), currency="INR", settlement_status="SETTLED",
            type="SETTLEMENT", source_row=2
        )
    ]
    
    # 1. With Window = 1 Day: A 2-day lag exceeds the configured limit
    engine_w1 = ReconciliationEngine(settlement_window_days=1)
    res_w1 = engine_w1.reconcile(plt_records, bnk_records)
    assert res_w1.summary.timing_difference_count == 0
    assert res_w1.summary.manual_review_count == 1
    assert "Settlement window exceeded" in res_w1.records[0].explanation

    # 2. With Window = 2 Days: A 2-day lag is within the configured limit -> TIMING_DIFFERENCE
    engine_w2 = ReconciliationEngine(settlement_window_days=2)
    res_w2 = engine_w2.reconcile(plt_records, bnk_records)
    assert res_w2.summary.timing_difference_count == 1
    assert res_w2.summary.manual_review_count == 0
    assert res_w2.records[0].status == "TIMING_DIFFERENCE"

def test_financial_validation_fee_math():
    """Verify bank CSV validation detects net != gross - fee."""
    csv_data = (
        "settlement_id,bank_reference,settlement_date,gross_amount,fee_amount,net_amount,currency,settlement_status,type\n"
        "STL-BAD,REF-BAD,2026-03-10,1000.00,10.00,950.00,INR,SETTLED,SETTLEMENT\n"
    )
    records, errors = validate_and_parse_bank_csv(csv_data)
    assert len(errors) == 1
    assert "Financial validation failed" in errors[0]

