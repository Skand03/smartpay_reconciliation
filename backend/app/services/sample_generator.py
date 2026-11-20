"""Sample dataset generator for SmartPay (INR ₹ Currency)."""
import csv
import io
import os
from decimal import Decimal
from typing import Tuple

def generate_sample_datasets() -> Tuple[str, str]:
    """Generates realistic Platform and Bank CSV strings containing all required discrepancy scenarios.
    
    Scenarios covered:
    1. Exact Match (3 normal transactions)
    2. Timing Difference (cross-month March 31 -> April 2)
    3. Batch-Level Rounding Difference (3-item batch, ₹0.02 variance)
    4. Duplicate Platform Entry (TRX-IN-1020 appears twice)
    5. Duplicate Bank Settlement (STL-IN-7025 appears twice)
    6. Legitimate Partial Settlements (₹10,000 -> ₹6,000 + ₹4,000)
    7. Valid Refund with Parent Transaction
    8. Unmatched Refund (orphaned bank refund)
    9. Currency Mismatch (USD vs INR)
    10. Suggested Match (order_id match, missing platform_trx_id)
    11. Unmatched Platform (unsettled old transaction)
    12. Unmatched Bank (unclaimed deposit)
    """
    
    platform_rows = [
        # --- 3 Normal Exact Matches (March 2026) ---
        {"transaction_id": "TRX-IN-1001", "order_id": "ORD-2026-101", "customer_id": "CUST-501",
         "amount": "1499.00", "currency": "INR", "timestamp": "2026-03-15T10:15:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},
        {"transaction_id": "TRX-IN-1002", "order_id": "ORD-2026-102", "customer_id": "CUST-502",
         "amount": "2999.00", "currency": "INR", "timestamp": "2026-03-16T14:20:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},
        {"transaction_id": "TRX-IN-1003", "order_id": "ORD-2026-103", "customer_id": "CUST-503",
         "amount": "850.50", "currency": "INR", "timestamp": "2026-03-18T18:05:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},

        # --- Scenario 1: Timing Differences (1-day, 2-day, 3-day delays) ---
        # 1-day cross-month lag (March 31 -> April 1)
        {"transaction_id": "TRX-IN-1004", "order_id": "ORD-2026-104", "customer_id": "CUST-504",
         "amount": "3499.00", "currency": "INR", "timestamp": "2026-03-31T21:00:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},
        # 2-day cross-month lag (March 31 -> April 2)
        {"transaction_id": "TRX-IN-1005", "order_id": "ORD-2026-105", "customer_id": "CUST-505",
         "amount": "7499.00", "currency": "INR", "timestamp": "2026-03-31T22:30:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},
        # 3-day cross-month lag (March 31 -> April 3)
        {"transaction_id": "TRX-IN-1006", "order_id": "ORD-2026-106", "customer_id": "CUST-506",
         "amount": "5200.00", "currency": "INR", "timestamp": "2026-03-31T23:15:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},

        # --- Scenario 2: Batch-Level Aggregation Rounding ---
        # 3 items in BATCH-2026-03-RND: 333.33 + 333.33 + 333.34 = 1000.00
        # Bank settles same batch as 333.33 + 333.33 + 333.32 = 999.98 (Δ = ₹0.02)
        {"transaction_id": "TRX-IN-1010", "order_id": "ORD-2026-110", "customer_id": "CUST-510",
         "amount": "333.33", "currency": "INR", "timestamp": "2026-03-20T11:00:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": "BATCH-2026-03-RND"},
        {"transaction_id": "TRX-IN-1011", "order_id": "ORD-2026-111", "customer_id": "CUST-511",
         "amount": "333.33", "currency": "INR", "timestamp": "2026-03-20T11:05:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": "BATCH-2026-03-RND"},
        {"transaction_id": "TRX-IN-1012", "order_id": "ORD-2026-112", "customer_id": "CUST-512",
         "amount": "333.34", "currency": "INR", "timestamp": "2026-03-20T11:10:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": "BATCH-2026-03-RND"},

        # --- Scenario 3: Duplicate Platform Entry ---
        # TRX-IN-1020 entered twice (accidental double-entry)
        {"transaction_id": "TRX-IN-1020", "order_id": "ORD-2026-120", "customer_id": "CUST-520",
         "amount": "2499.00", "currency": "INR", "timestamp": "2026-03-22T09:15:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},
        {"transaction_id": "TRX-IN-1020", "order_id": "ORD-2026-120", "customer_id": "CUST-520",
         "amount": "2499.00", "currency": "INR", "timestamp": "2026-03-22T09:15:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},

        # --- Scenario 4: Legitimate Partial Settlements ---
        # ₹10,000 platform transaction settled in two bank tranches (₹6,000 + ₹4,000)
        {"transaction_id": "TRX-IN-1030", "order_id": "ORD-2026-130", "customer_id": "CUST-530",
         "amount": "10000.00", "currency": "INR", "timestamp": "2026-03-23T15:30:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},

        # --- Scenario 5: Valid Refund with Parent ---
        # Original payment
        {"transaction_id": "TRX-IN-1040", "order_id": "ORD-2026-140", "customer_id": "CUST-540",
         "amount": "4500.00", "currency": "INR", "timestamp": "2026-03-12T12:00:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},
        # Refund linked to parent
        {"transaction_id": "TRX-IN-1041", "order_id": "ORD-2026-140", "customer_id": "CUST-540",
         "amount": "4500.00", "currency": "INR", "timestamp": "2026-03-18T16:00:00Z",
         "status": "REFUNDED", "type": "REFUND", "parent_transaction_id": "TRX-IN-1040", "batch_id": ""},

        # --- Scenario 6: Unsettled Platform Transaction ---
        {"transaction_id": "TRX-IN-1060", "order_id": "ORD-2026-160", "customer_id": "CUST-560",
         "amount": "3200.00", "currency": "INR", "timestamp": "2026-03-05T08:30:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},

        # --- Scenario 7: Currency Mismatch ---
        {"transaction_id": "TRX-IN-1070", "order_id": "ORD-2026-170", "customer_id": "CUST-570",
         "amount": "100.00", "currency": "USD", "timestamp": "2026-03-25T14:00:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},

        # --- Scenario 8: Suggested Match ---
        # Bank has this order_id but no platform_trx_id
        {"transaction_id": "TRX-IN-1080", "order_id": "ORD-2026-180", "customer_id": "CUST-580",
         "amount": "5500.00", "currency": "INR", "timestamp": "2026-03-26T17:45:00Z",
         "status": "SUCCESS", "type": "PAYMENT", "parent_transaction_id": "", "batch_id": ""},
    ]

    bank_rows = [
        # --- Exact Matches for TRX-IN-1001, 1002, 1003 ---
        {"settlement_id": "STL-IN-7001", "platform_trx_id": "TRX-IN-1001", "order_id": "ORD-2026-101",
         "bank_reference": "UTR-HDFC-99101", "settlement_date": "2026-03-16",
         "gross_amount": "1499.00", "fee_amount": "14.99", "net_amount": "1484.01",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},
        {"settlement_id": "STL-IN-7002", "platform_trx_id": "TRX-IN-1002", "order_id": "ORD-2026-102",
         "bank_reference": "UTR-HDFC-99102", "settlement_date": "2026-03-17",
         "gross_amount": "2999.00", "fee_amount": "29.99", "net_amount": "2969.01",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},
        {"settlement_id": "STL-IN-7003", "platform_trx_id": "TRX-IN-1003", "order_id": "ORD-2026-103",
         "bank_reference": "UTR-HDFC-99103", "settlement_date": "2026-03-19",
         "gross_amount": "850.50", "fee_amount": "8.50", "net_amount": "842.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},

        # --- Timing Difference settlements (April 1, April 2, April 3) ---
        {"settlement_id": "STL-IN-7004", "platform_trx_id": "TRX-IN-1004", "order_id": "ORD-2026-104",
         "bank_reference": "UTR-ICICI-44104", "settlement_date": "2026-04-01",
         "gross_amount": "3499.00", "fee_amount": "34.99", "net_amount": "3464.01",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},
        {"settlement_id": "STL-IN-7005", "platform_trx_id": "TRX-IN-1005", "order_id": "ORD-2026-105",
         "bank_reference": "UTR-ICICI-44105", "settlement_date": "2026-04-02",
         "gross_amount": "7499.00", "fee_amount": "74.99", "net_amount": "7424.01",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},
        {"settlement_id": "STL-IN-7006", "platform_trx_id": "TRX-IN-1006", "order_id": "ORD-2026-106",
         "bank_reference": "UTR-ICICI-44106", "settlement_date": "2026-04-03",
         "gross_amount": "5200.00", "fee_amount": "52.00", "net_amount": "5148.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},

        # --- Batch Rounding (bank settles 333.32 for the third item) ---
        {"settlement_id": "STL-IN-7010", "platform_trx_id": "TRX-IN-1010", "order_id": "ORD-2026-110",
         "bank_reference": "UTR-AXIS-33110", "settlement_date": "2026-03-21",
         "gross_amount": "333.33", "fee_amount": "3.33", "net_amount": "330.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "BATCH-2026-03-RND", "original_payment_ref": ""},
        {"settlement_id": "STL-IN-7011", "platform_trx_id": "TRX-IN-1011", "order_id": "ORD-2026-111",
         "bank_reference": "UTR-AXIS-33111", "settlement_date": "2026-03-21",
         "gross_amount": "333.33", "fee_amount": "3.33", "net_amount": "330.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "BATCH-2026-03-RND", "original_payment_ref": ""},
        {"settlement_id": "STL-IN-7012", "platform_trx_id": "TRX-IN-1012", "order_id": "ORD-2026-112",
         "bank_reference": "UTR-AXIS-33112", "settlement_date": "2026-03-21",
         "gross_amount": "333.32", "fee_amount": "3.33", "net_amount": "329.99",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "BATCH-2026-03-RND", "original_payment_ref": ""},

        # --- Bank settlement for TRX-IN-1020 (primary of the duplicate) ---
        {"settlement_id": "STL-IN-7020", "platform_trx_id": "TRX-IN-1020", "order_id": "ORD-2026-120",
         "bank_reference": "UTR-SBI-55120", "settlement_date": "2026-03-23",
         "gross_amount": "2499.00", "fee_amount": "24.99", "net_amount": "2474.01",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},

        # --- Duplicate Bank Settlement: STL-IN-7025 appears twice ---
        {"settlement_id": "STL-IN-7025", "platform_trx_id": "TRX-IN-1001", "order_id": "ORD-2026-101",
         "bank_reference": "UTR-HDFC-DUP", "settlement_date": "2026-03-17",
         "gross_amount": "1499.00", "fee_amount": "14.99", "net_amount": "1484.01",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},
        {"settlement_id": "STL-IN-7025", "platform_trx_id": "TRX-IN-1001", "order_id": "ORD-2026-101",
         "bank_reference": "UTR-HDFC-DUP", "settlement_date": "2026-03-17",
         "gross_amount": "1499.00", "fee_amount": "14.99", "net_amount": "1484.01",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},

        # --- Partial Settlements for TRX-IN-1030 (₹6,000 + ₹4,000 = ₹10,000) ---
        {"settlement_id": "STL-IN-7031", "platform_trx_id": "TRX-IN-1030", "order_id": "ORD-2026-130",
         "bank_reference": "UTR-KOTAK-77131", "settlement_date": "2026-03-24",
         "gross_amount": "6000.00", "fee_amount": "60.00", "net_amount": "5940.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},
        {"settlement_id": "STL-IN-7032", "platform_trx_id": "TRX-IN-1030", "order_id": "ORD-2026-130",
         "bank_reference": "UTR-KOTAK-77132", "settlement_date": "2026-03-25",
         "gross_amount": "4000.00", "fee_amount": "40.00", "net_amount": "3960.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},

        # --- Original payment settlement for TRX-IN-1040 ---
        {"settlement_id": "STL-IN-7040", "platform_trx_id": "TRX-IN-1040", "order_id": "ORD-2026-140",
         "bank_reference": "UTR-AXIS-88140", "settlement_date": "2026-03-13",
         "gross_amount": "4500.00", "fee_amount": "45.00", "net_amount": "4455.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},
        # --- Valid Bank Refund (linked to TRX-IN-1040) ---
        {"settlement_id": "STL-IN-7041", "platform_trx_id": "TRX-IN-1041", "order_id": "ORD-2026-140",
         "bank_reference": "UTR-AXIS-88141", "settlement_date": "2026-03-19",
         "gross_amount": "-4500.00", "fee_amount": "0.00", "net_amount": "-4500.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "REFUND",
         "batch_id": "", "original_payment_ref": "TRX-IN-1040"},

        # --- Unmatched Refund (orphaned, no original sale) ---
        {"settlement_id": "STL-IN-7099", "platform_trx_id": "TRX-IN-NONE-999", "order_id": "ORD-UNKNOWN",
         "bank_reference": "UTR-PNB-00199", "settlement_date": "2026-03-28",
         "gross_amount": "-1200.00", "fee_amount": "0.00", "net_amount": "-1200.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "REFUND",
         "batch_id": "", "original_payment_ref": "TRX-IN-UNKNOWN"},

        # --- Currency Mismatch bank record (INR vs platform's USD) ---
        {"settlement_id": "STL-IN-7070-FX", "platform_trx_id": "TRX-IN-1070", "order_id": "ORD-2026-170",
         "bank_reference": "UTR-BOI-FX170", "settlement_date": "2026-03-26",
         "gross_amount": "100.00", "fee_amount": "1.00", "net_amount": "99.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},

        # --- Unmatched Bank (no platform transaction exists) ---
        {"settlement_id": "STL-IN-7070", "platform_trx_id": "TRX-IN-GHOST", "order_id": "ORD-2026-777",
         "bank_reference": "UTR-SBI-77070", "settlement_date": "2026-03-27",
         "gross_amount": "3750.00", "fee_amount": "37.50", "net_amount": "3712.50",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},

        # --- Suggested Match (missing platform_trx_id, order_id matches) ---
        {"settlement_id": "STL-IN-7080", "platform_trx_id": "", "order_id": "ORD-2026-180",
         "bank_reference": "UTR-YES-88180", "settlement_date": "2026-03-27",
         "gross_amount": "5500.00", "fee_amount": "55.00", "net_amount": "5445.00",
         "currency": "INR", "settlement_status": "SETTLED", "type": "SETTLEMENT",
         "batch_id": "", "original_payment_ref": ""},
    ]

    # Write Platform CSV
    plt_out = io.StringIO()
    plt_writer = csv.DictWriter(plt_out, fieldnames=[
        "transaction_id", "order_id", "customer_id", "amount",
        "currency", "timestamp", "status", "type", "parent_transaction_id", "batch_id"
    ])
    plt_writer.writeheader()
    for row in platform_rows:
        plt_writer.writerow(row)

    # Write Bank CSV
    bnk_out = io.StringIO()
    bnk_writer = csv.DictWriter(bnk_out, fieldnames=[
        "settlement_id", "platform_trx_id", "order_id", "bank_reference",
        "settlement_date", "gross_amount", "fee_amount", "net_amount",
        "currency", "settlement_status", "type", "batch_id", "original_payment_ref"
    ])
    bnk_writer.writeheader()
    for row in bank_rows:
        bnk_writer.writerow(row)

    return plt_out.getvalue(), bnk_out.getvalue()

def save_sample_csv_files(dest_dir: str):
    os.makedirs(dest_dir, exist_ok=True)
    plt_csv, bnk_csv = generate_sample_datasets()

    plt_path = os.path.join(dest_dir, "sample_platform_transactions.csv")
    bnk_path = os.path.join(dest_dir, "sample_bank_settlements.csv")

    with open(plt_path, "w", encoding="utf-8") as f:
        f.write(plt_csv)
    with open(bnk_path, "w", encoding="utf-8") as f:
        f.write(bnk_csv)

    return plt_path, bnk_path
