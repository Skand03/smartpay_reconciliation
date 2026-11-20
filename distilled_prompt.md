# SmartPay: Distilled Financial Reconciliation System Specification

Build an enterprise-grade, deterministic payment reconciliation application ("SmartPay") resolving platform ledger transactions against bank settlement statements.

## 1. Domain & Mathematical Precision
- **Currency Standard:** Standardize all financial computations and sample datasets on INR (₹). Strict currency isolation prevents cross-currency auto-matching (`CURRENCY_MISMATCH`).
- **Precision Standard:** All calculations strictly use Python's fixed-point `decimal.Decimal` with `ROUND_HALF_UP` to eliminate IEEE-754 floating-point drift.
- **Zero Hallucination:** Deterministic rules-based reconciliation only; no LLMs are used for financial matching or arithmetic.

## 2. Core Discrepancy Scenarios
1. **Timing Difference:**
   - Detect cross-month settlements where a platform transaction occurs in Month $M$ (e.g. March 31) and settles in Month $M+1$ (e.g. April 1–3) within a configurable $T+1$ to $T+3$ day clearing delay.
   - Distinguish valid timing differences from older missing platform settlements past the settlement window (`UNMATCHED_PLATFORM`).
2. **Batch-Level Aggregation Rounding Difference:**
   - Detect variances emerging from batch sum aggregation ($\sum \text{Round}(item_i) \neq \text{Round}(\sum item_i)$) where sum of rounded individual transaction amounts differs by a penny ($\le ₹0.05$) from the aggregated bank settlement batch total.
   - Accurately document the aggregation provenance and distinguish proven rounding from unexplained amount mismatches.
3. **Duplicate Entry Identification & Exposure:**
   - Detect repeated platform `transaction_id`s (`DUPLICATE_PLATFORM`) and repeated bank `settlement_id`s or identical payloads (`DUPLICATE_BANK`).
   - Quantify financial exposure ($\sum \text{duplicate amounts}$) without deleting or silently dropping any record.
4. **Refund Provenance & Unmatched Refunds:**
   - Validate refunds using `parent_transaction_id` and bank `original_payment_ref` against original payment records.
   - Reconcile valid refunds (`MATCHED_REFUND`) and flag orphaned refunds lacking original payment references as `UNMATCHED_REFUND` for operational audit.
5. **Legitimate Partial Settlements:**
   - Recognize when a single platform transaction is settled across multiple distinct bank settlements whose sum equals the original transaction amount (`MATCHED_PARTIAL`), preventing false duplicate alerts.
6. **Suggested Match (Auditable Fallback):**
   - When order ID and amount match but direct platform transaction ID is missing, flag as `MANUAL_REVIEW` for human sign-off (zero automatic fuzzy matching).

## 3. 100% Ledger Row Accounting
- Zero silent drops: Ensure every input row from both Platform ($N_P$) and Bank ($N_B$) files appears in the final reconciliation output ($N_{Output} = N_P + N_B$).

## 4. Architecture & Stack
- **Backend:** Python, FastAPI, Pydantic v2, Pandas, Decimal, Pytest.
- **Frontend:** React.js, Tailwind CSS, Lucide Icons, Recharts (Status Donut & Discrepancy Bar charts).
- **Core Features:** Dual CSV upload, pre-packaged realistic INR sample datasets, KPI summary cards, filter chips, search, dynamic settlement lag window selector, and CSV audit report export.

