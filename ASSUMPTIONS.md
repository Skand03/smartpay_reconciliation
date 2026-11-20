# SmartPay: System Assumptions, Business Rules & Financial Reconciliation Specification (Revised)

This document formalizes the updated domain rules, mathematical specifications, CSV schemas, discrepancy definitions, edge cases, and architectural rules for the **SmartPay Payment Reconciliation System**.

---

## 1. Domain Overview & Problem Statement

Financial reconciliation between an internal payment platform ledger and bank settlement records must handle real-world payment acquiring mechanics:
1. **Asynchronous Settlement Delays:** Platform transactions are recorded instantly, while acquiring banks settle funds in batches with a standard delay of 1–2 banking days.
2. **Month-End Cut-offs:** Transactions occurring at the end of Month $M$ (e.g., March 31) settle in Month $M+1$ (e.g., April 1 or April 2).
3. **Multi-Part & Batch Settlements:** A single platform transaction may have multiple legitimate partial settlements (e.g., split shipments, milestone releases, or partial authorizations), whereas duplicate settlements represent accidental duplicate processing.
4. **Batch Sum Aggregation Rounding:** Individual transactions calculated with micro-fees, taxes, or multi-currency conversions lead to variances between the sum of rounded individual transaction amounts and the batch-level settled total ($\sum \text{Round}(x_i) \neq \text{Round}(\sum x_i)$).
5. **Refund Integrity:** Customer refunds must link to an authenticated original sale (`parent_transaction_id`). Orphaned refunds without an originating transaction signal potential fraud or ledger corruption.

---

## 2. Explicit Business Rules & Assumptions

### 2.1 Currency Rule
- **Currency Standard:** The primary operational currency for sample data and validation is **INR (₹)**.
- **Strict Currency Isolation:** Platform and Bank records **MUST** share the identical currency code (e.g., `INR == INR`). 
- **Rule:** A record will **never** be reconciled or matched against a record with a different currency. Any cross-currency attempt is immediately flagged as a `CURRENCY_MISMATCH` requiring manual review.

### 2.2 CSV Validation Rules (Preserving Evaluation Targets)
- **Non-Rejection of Duplicates:** CSV validation checks headers, data type formats (ISO date strings, valid decimal numbers), and required structural columns. **It strictly does NOT reject duplicate IDs**, because identifying duplicate platform records and duplicate bank settlements is an explicit reconciliation goal.
- **Financial Equation Validation:** For every bank record:
  $$\text{net\_amount} = \text{gross\_amount} - \text{fee\_amount}$$
  (with proper sign handling for refunds/reversals). Records failing this equation are flagged as `FINANCIAL_VALIDATION_ERROR` for audit review.

### 2.3 Duplicate Detection Rules
- **Platform Duplicates (`DUPLICATE_PLATFORM`):**
  - Identified by repeated `transaction_id` in the platform dataset.
  - The first encountered instance is preserved as the primary operational record; all subsequent occurrences are flagged as `DUPLICATE_PLATFORM`.
  - Financial impact = $\sum \text{amount of duplicate instances}$.
- **Bank Duplicates (`DUPLICATE_BANK`):**
  - Identified by repeated `settlement_id` or identical settlement records (same `settlement_id` or identical composite key `(platform_trx_id, bank_reference, settlement_date, gross_amount, net_amount)`).
  - The primary record is processed for settlement matching; duplicate rows are preserved and flagged as `DUPLICATE_BANK`.
  - Financial impact = $\sum \text{gross\_amount of duplicate instances}$.
- **Legitimate Partial Settlements:**
  - Multiple bank settlement rows with different `settlement_id` referencing the **same** `platform_trx_id` are **NOT** automatically duplicates.
  - When the sum of these settlements $\sum \text{gross\_amount}_{settlements} = \text{amount}_{platform}$, they are recognized as legitimate `MATCHED_PARTIAL_SETTLEMENT`.

### 2.4 Rounding Difference (Batch Sum Aggregation vs. Mismatch)
- **Batch Aggregation Context:**
  When aggregating $N$ transactions into a bank settlement batch, two rounding methodologies often collide:
  1. **Itemized Sum:** $\sum_{i=1}^N \text{Round}_2(Amount_i)$
  2. **Batch Aggregate:** $\text{Round}_2\left(\sum_{i=1}^N Amount_i\right)$ or sum of items with sub-cent fee allocations.
- **Rule:**
  - If a batch of platform transactions mapped to a bank settlement batch has an aggregate difference $|\sum Amount_{platform} - \sum Gross_{bank}| \le ₹0.05 \times N$ (or up to ₹0.05 for individual/batch pairings) with documented per-item penny differences, it is classified as `ROUNDING_DIFFERENCE` (Batch Aggregation).
  - Any variance exceeding tolerance or lacking batch aggregation provenance is classified as an unexplained `AMOUNT_MISMATCH` (requiring manual review), **never** masked as a rounding difference.

### 2.5 Refund Validation Rules
- **Valid Refund (`MATCHED_REFUND`):**
  - Platform refund record must reference a valid `parent_transaction_id`.
  - The parent transaction must exist in the platform ledger as a successful `PAYMENT`.
  - Refund amount must be $\le$ parent transaction amount.
  - Direction/sign must be consistent (negative in net flow, or designated by `type = 'REFUND'`).
  - Matches the corresponding bank refund settlement.
- **Unmatched Refund (`UNMATCHED_REFUND`):**
  - Any refund record in the bank settlements (or platform) that has no valid original sale transaction (`parent_transaction_id` is missing, invalid, or does not exist in the ledger).
  - Flagged for operational risk and fraud investigation.

### 2.6 Timing Difference Rules
- **Settlement Delay Window:** Default configurable window is $T+1$ to $T+2$ banking days (assessment specification).
- **Rule:**
  - A transaction is a `TIMING_DIFFERENCE` if and only if:
    1. Transaction ID and Amount match.
    2. Platform transaction date is in Month $M$ (e.g., 2026-03-31), and Bank settlement date is in Month $M+1$ (e.g., 2026-04-02).
    3. The settlement lag $\Delta t = \text{settlement\_date} - \text{platform\_date}$ is within the allowable window ($1 \le \Delta t \le 2$ business days, configurable up to 3 days).
  - If a platform transaction has no matching settlement and its age $> 3$ days, it is classified as `UNMATCHED_PLATFORM` (Missing Settlement / Pending Deposit), **not** a timing difference.

### 2.7 Deterministic vs. Manual Review (Zero Automatic Fuzzy Matching)
- **Deterministic Requirement:** Automated reconciliation matches only on exact keys: `currency`, `platform_trx_id` $\leftrightarrow$ `transaction_id`, and exact (or proven partial/batch) amounts.
- **Suggested Match (`MANUAL_REVIEW_SUGGESTED`):**
  - If a bank record lacks a `platform_trx_id` but shares an `order_id` and exact amount with an unsettled platform transaction, the system **does not** automatically reconcile it.
  - It surfaces the pair as `MANUAL_REVIEW_SUGGESTED` with high confidence score for human operator confirmation.

---

## 3. Reconciliation Classification Categories (100% Row Accounting)

Every row from both input files is mapped to one and only one classification:

| Status Code | Classification | Description |
| :--- | :--- | :--- |
| `MATCHED_EXACT` | Exact Match | Same ID, identical amount, same currency, settled within normal period. |
| `MATCHED_PARTIAL` | Partial Settlement | Multiple bank settlements summing up to one platform transaction. |
| `MATCHED_REFUND` | Reconciled Refund | Valid refund linked to original parent sale and settled by bank. |
| `TIMING_DIFFERENCE` | Timing Difference | Valid match, cross-month cut-off within 1–2 day settlement lag. |
| `ROUNDING_DIFFERENCE` | Batch Rounding | Aggregate variance ($\le ₹0.05$) due to batch sum rounding. |
| `DUPLICATE_PLATFORM` | Duplicate Platform | Redundant platform record with financial exposure calculated. |
| `DUPLICATE_BANK` | Duplicate Bank | Redundant bank settlement record with financial exposure calculated. |
| `UNMATCHED_REFUND` | Orphaned Refund | Refund with no valid parent transaction; flagged for investigation. |
| `MANUAL_REVIEW` | Suggested Match / Mismatch | Order ID match or amount mismatch requiring human sign-off. |
| `UNMATCHED_PLATFORM` | Missing Settlement | Platform transaction recorded but never settled by the bank. |
| `UNMATCHED_BANK` | Unclaimed Deposit | Bank settlement with no corresponding platform transaction. |

---

## 4. Financial Precision Standard

- All calculation pipelines utilize Python's standard `decimal.Decimal`.
- String representations from CSVs are directly converted: `Decimal(str(val).strip())`.
- Aggregations and differences use exact decimal math:
  $$\Delta = Amount_{platform} - Gross_{bank}$$
- Rounding strategy: `ROUND_HALF_UP` strictly applied when formatting to 2 decimal places. Floating-point conversions are barred from reconciliation logic.
