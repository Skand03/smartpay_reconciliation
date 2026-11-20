# SmartPay – Payment Reconciliation System (Specification & Plan)

SmartPay is a deterministic, enterprise-grade financial reconciliation application designed to ingest, validate, normalize, and reconcile **Platform Transaction Ledgers** against **Bank Settlement Ledgers**. 

It deterministically identifies, categorizes, and explains discrepancies such as timing differences, batch-level rounding errors, duplicate entries, legitimate partial settlements, and orphaned/unmatched refunds, operating with full financial precision in **INR (₹)**.

---

## Key Revisions & Highlights

1. **Explicit Currency Handling (INR - ₹):**
   - All sample datasets and financial computations are standardized on INR (₹).
   - Strict currency validation ensures records with differing currencies are never matched, preventing cross-currency contamination.

2. **Accurate Duplicate & Partial Settlement Handling:**
   - Platform duplicates are identified by repeated `transaction_id`.
   - Bank duplicates are identified by repeated `settlement_id` or identical settlement payloads.
   - Legitimate **partial settlements** (multiple bank settlement records for one platform transaction whose sum equals the original amount) are recognized and matched as `MATCHED_PARTIAL`, not misclassified as duplicates.
   - All duplicate records are preserved with their financial impact quantified without dropping data.

3. **Batch-Level Sum Aggregation Rounding:**
   - Rounding differences are demonstrated at the batch aggregation level ($\sum \text{Round}(item) \neq \text{Round}(\sum item)$) where the sum of rounded individual transaction amounts differs by a penny or two ($\le ₹0.05$) from the aggregated bank settlement batch total.
   - Distinguishes mathematically proven aggregation differences from unexplained amount mismatches.

4. **Rigorous Refund Integrity:**
   - Uses `parent_transaction_id` to validate refunds against original platform payments.
   - Legitimate refunds are reconciled as `MATCHED_REFUND`.
   - Orphaned refunds (no matching parent transaction) are flagged as `UNMATCHED_REFUND` for risk and fraud review.

5. **Configurable Settlement Window & Timing Differences:**
   - Configurable settlement delay window (default 1–2 days, reflecting typical banking clearing cycles).
   - Real-world cross-month example: A platform transaction recorded on March 31, 2026, settled by the bank on April 2, 2026, is classified as `TIMING_DIFFERENCE`.
   - Genuinely unsettled transactions past the settlement window are classified as `UNMATCHED_PLATFORM`.

6. **Auditable Matching & Suggested Matches:**
   - Zero automatic fuzzy matching.
   - Potential matches on order ID and amount without a direct transaction ID reference are flagged as `MANUAL_REVIEW` for human operator decision.

7. **Strict 100% Row Accounting:**
   - Every single row in both datasets is accounted for in the output report, categorized into transparent audit buckets.

---

## CSV Schemas

### 1. Platform Transactions (`platform_transactions.csv`)
| Column | Type | Example | Validation Rules |
| :--- | :--- | :--- | :--- |
| `transaction_id` | String | `TRX-1001` | Platform unique ID (duplicates flagged in engine) |
| `order_id` | String | `ORD-5001` | Merchant internal order identifier |
| `customer_id` | String | `CUST-901` | Customer account identifier |
| `amount` | Decimal(12,2) | `2499.50` | Transaction amount in INR |
| `currency` | String | `INR` | Required currency code (e.g., `INR`) |
| `timestamp` | ISO-8601 | `2026-03-31T21:30:00Z` | Transaction timestamp |
| `status` | String | `SUCCESS` | `SUCCESS`, `PENDING`, `REFUNDED` |
| `type` | String | `PAYMENT` | `PAYMENT` or `REFUND` |
| `parent_transaction_id` | String (Opt) | `TRX-0992` | Required if `type == REFUND` |

### 2. Bank Settlements (`bank_settlements.csv`)
| Column | Type | Example | Validation Rules |
| :--- | :--- | :--- | :--- |
| `settlement_id` | String | `STL-7001` | Bank settlement ID (duplicates flagged in engine) |
| `platform_trx_id` | String | `TRX-1001` | Cross-reference identifier |
| `order_id` | String (Opt) | `ORD-5001` | Secondary reference |
| `bank_reference` | String | `BNK-REF-10492` | Bank internal clearing reference |
| `settlement_date` | Date | `2026-04-02` | ISO date `YYYY-MM-DD` |
| `gross_amount` | Decimal(12,2) | `2499.50` | Gross funds settled |
| `fee_amount` | Decimal(12,2) | `15.00` | Gateway/Interchange fee |
| `net_amount` | Decimal(12,2) | `2484.50` | Must equal `gross_amount - fee_amount` |
| `currency` | String | `INR` | Settlement currency |
| `settlement_status` | String | `SETTLED` | `SETTLED`, `PENDING`, `REVERSED` |
| `type` | String | `SETTLEMENT` | `SETTLEMENT` or `REFUND` |
| `batch_id` | String | `BATCH-2026-04-A` | Bank settlement batch identifier |

---

## Deterministic Reconciliation Algorithm

The engine processes data in sequential, deterministic passes:

```
Pass 1: Data Parsing & Normalization
  ├── Decimal conversion with standard ROUND_HALF_UP.
  └── Validate net_amount == gross_amount - fee_amount for bank records.

Pass 2: Currency Check
  └── Ensure currency equivalence. Records with mismatched currencies are isolated for MANUAL_REVIEW.

Pass 3: Duplicate Detection (Platform & Bank)
  ├── Group platform rows by transaction_id; all occurrences > 1 flagged as DUPLICATE_PLATFORM.
  └── Group bank rows by settlement_id / identical payload; all occurrences > 1 flagged as DUPLICATE_BANK.

Pass 4: Refund Validation & Reconciliation
  ├── Identify REFUND records in platform and bank.
  ├── Verify parent_transaction_id exists in platform ledger.
  ├── If parent missing or amount > parent, flag as UNMATCHED_REFUND.
  └── If valid parent exists and bank refund matches, status: MATCHED_REFUND.

Pass 5: Legitimate Partial Settlement Matching
  ├── Find platform transactions with multiple bank settlement rows referencing platform_trx_id.
  └── If sum(bank_gross) == platform_amount, reconcile as MATCHED_PARTIAL.

Pass 6: Batch Aggregation Rounding Identification
  ├── Group settlements by batch_id and compare with corresponding platform transactions.
  └── If sum(platform_amount) - sum(bank_gross) is within proven rounding threshold (<= ₹0.05),
      mark as ROUNDING_DIFFERENCE (Batch Aggregation) with exact breakdown.

Pass 7: Exact Matching & Timing Difference Matching
  ├── For remaining single 1:1 matches:
  │   ├── If platform_amount == bank_gross:
  │   │   ├── If settlement within 1–2 days and cross-month (e.g., March 31 -> April 2):
  │   │   │   Status: TIMING_DIFFERENCE.
  │   │   └── Else within same month or standard window:
  │   │       Status: MATCHED_EXACT.
  │   └── If amount difference <= ₹0.05 on 1:1: ROUNDING_DIFFERENCE.
  │   └── Else: AMOUNT_MISMATCH (requires MANUAL_REVIEW).

Pass 8: Suggested Match Identification (Order ID Fallback)
  └── For unmatched records having identical order_id and amount:
      Flag as MANUAL_REVIEW (Suggested Match) for human approval.

Pass 9: Unmatched Ledger Accounting
  ├── Remaining platform records: UNMATCHED_PLATFORM (Unsettled Platform Transaction).
  └── Remaining bank records: UNMATCHED_BANK (Unclaimed Settlement Deposit).
```

---

## Test Plan Suite (Pytest)

The test suite will verify all 10 target scenarios:
1. `test_duplicate_platform_transaction`: Repeated platform `transaction_id`, verify all copies preserved, primary matched, duplicate flagged with financial exposure.
2. `test_duplicate_bank_settlement`: Repeated `settlement_id` or identical settlement record, duplicate preserved and flagged with financial exposure.
3. `test_multiple_partial_settlements`: A single ₹5,000 platform transaction settled in two ₹2,500 bank records, successfully reconciled as `MATCHED_PARTIAL`.
4. `test_cross_month_timing_difference`: Platform transaction on `2026-03-31` settled on `2026-04-02` (within 2 days), classified as `TIMING_DIFFERENCE`.
5. `test_batch_level_rounding`: Batch of transactions where sum of rounded individual amounts differs by ₹0.02 from the batch settlement total, verified with `Decimal`.
6. `test_valid_refund_with_parent`: Refund linked to valid parent payment, verified and reconciled as `MATCHED_REFUND`.
7. `test_unmatched_refund_without_parent`: Bank refund referencing non-existent parent, correctly flagged as `UNMATCHED_REFUND`.
8. `test_currency_mismatch`: Platform in INR, bank in USD, prevented from matching and flagged for review.
9. `test_financial_validation_fee_math`: Validation error when `gross - fee != net`.
10. `test_exact_match_and_unmatched`: Full coverage of clean matches and truly unsettled residual items.
