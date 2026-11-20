I want to build a complete, working software application called "SmartPay – Payment Reconciliation System" for a real-world financial reconciliation problem.

PROBLEM STATEMENT:

A payments company records every customer transaction immediately when payment occurs. However, the bank settles the funds in batches after 1–2 days. At month-end, the company's platform transaction records and bank settlement records do not match.

Build a system that identifies and explains the differences between these two datasets.

REQUIRED DISCREPANCY SCENARIOS:

1. Timing Difference:
A platform transaction is recorded in one month but settled by the bank in the following month. Identify it as a timing difference.

2. Rounding Difference:
Detect differences that emerge when individual transaction amounts are aggregated. Use accurate decimal arithmetic and explain the source of the difference.

3. Duplicate Entry:
Detect duplicate transaction entries in either dataset. Identify the affected records and their financial impact without silently deleting them.

4. Unmatched Refund:
Identify a refund record that has no corresponding original transaction and flag it for investigation.

TECHNOLOGY STACK:

- Frontend: React.js
- Styling: Tailwind CSS
- Backend: Python and FastAPI
- Data processing: Pandas
- Database: SQLite
- Charts: Recharts
- Testing: Pytest

APPLICATION REQUIREMENTS:

- Provide two CSV upload inputs: platform transactions and bank settlements.
- Generate realistic sample datasets because no test files are provided.
- Validate CSV headers, data types, missing values and invalid amounts.
- Normalize the datasets before reconciliation.
- Implement a deterministic reconciliation engine.
- Display matched transactions, unmatched transactions and discrepancies.
- Classify discrepancies into the four required categories.
- Show transaction IDs, dates, amounts, differences, status and explanations.
- Include dashboard cards showing total platform transactions, total bank settlements, matched records, unmatched records and total discrepancy amount.
- Include charts showing reconciliation status and discrepancy categories.
- Provide filters and search.
- Allow users to download the reconciliation report as CSV.

ENGINEERING REQUIREMENTS:

- Use a clean, maintainable project structure.
- Separate frontend, backend, services, models and tests.
- Use Python Decimal for financial calculations.
- Do not use an LLM to decide financial matches or calculate financial results.
- Handle invalid input and errors properly.
- Write unit tests for all four required scenarios.
- Include edge cases and document all assumptions.
- Never fabricate matching results or hide unmatched records.

IMPORTANT WORKFLOW:

Do not generate the entire application in one uncontrolled step.

First:
1. Analyze the problem.
2. Identify missing requirements and ambiguities.
3. Define explicit assumptions.
4. Propose the architecture.
5. Design the CSV schemas and sample data.
6. Design the reconciliation algorithm.
7. Present a detailed implementation plan.

Wait for my review before starting implementation.

Create a README.md and an ASSUMPTIONS.md documenting the architecture, setup instructions, business rules and limitations.

The final application must be functional, testable, demonstrable and suitable for deployment.

