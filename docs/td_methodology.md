# Methodology & Design Decisions
## TD Financial Crime Analytics

> This document explains the analytical choices behind each component,
> the AML regulatory framework the project models, and how the pieces
> connect to real financial crime operations at a bank like TD.

---

## 1. Why this problem

TD Bank's 2024 regulatory settlement — including a USD $3 billion penalty
for AML deficiencies — made financial crime analytics one of the most
strategically important functions in Canadian banking. The analytical work
required to resolve those deficiencies is exactly what this project models:
detecting suspicious patterns in transaction data before they become
regulatory violations.

This isn't an abstract exercise. The TD Insurance DAI team (Actuarial Analyst II,
Business Insights Analyst II) and the Financial Crime Risk Management team
(FCRM Investigative Analyst, AML Support Officer) are building and running
these exact pipelines right now.

---

## 2. Regulatory framework

### PCMLTFA — Proceeds of Crime (Money Laundering) and Terrorist Financing Act

The primary Canadian AML legislation. Key provisions this project models:

**Section 9 — Currency Transaction Reports (CTRs)**
Financial entities must report cash transactions of $10,000+ to FINTRAC.
Structuring — breaking transactions into smaller amounts to stay below this
threshold — is a criminal offence. The structuring detection query targets
amounts in the $9,500–$9,999 range, which is the classic structuring window.

**Section 7 — Suspicious Transaction Reports (STRs)**
Entities must report transactions where there are reasonable grounds to
suspect money laundering or terrorist financing. The customer risk scoring
model produces the composite signal that would trigger an STR review.

### FINTRAC — Financial Transactions and Reports Analysis Centre of Canada

FINTRAC guidance designates certain countries as higher-risk jurisdictions
requiring enhanced scrutiny. The jurisdiction exposure query flags transactions
with counterparties in countries on FINTRAC's high-risk list (Cayman Islands,
Panama, Nigeria in this model).

### OSFI — Office of the Superintendent of Financial Institutions

OSFI Guideline E-13 requires federally regulated financial institutions to
maintain effective AML programs with documented risk assessment processes.
The customer risk scoring methodology is designed to be auditable and
documented — a direct response to E-13 requirements.

---

## 3. Detection methodology

### Structuring detection

**Approach:** Rule-based threshold analysis — transactions between
$9,500 and $9,999.99 on cash transaction types, grouped by customer,
flagging any customer with ≥2 such transactions.

**Why this works:** Most legitimate cash transactions don't cluster in this
specific band. The pattern is statistically anomalous and legally significant.

**Limitation:** High false positive rate for customers with genuinely
recurring near-threshold transactions (e.g. weekly payroll distributions).
A production system would add velocity controls and customer profile context.

### High-velocity detection

**Approach:** Rolling 7-day window count per customer. Flags customers
with ≥5 transactions in any 7-day period.

**Why this matters:** High velocity is an indicator of:
- Account takeover — fraudster rapidly draining a compromised account
- Smurfing — multiple small deposits to aggregate cash
- Layering — rapid movement to obscure source of funds

**Implementation note:** The rolling window uses pandas `rolling('7D')`
on a datetime-indexed series — the correct approach for calendar-based
windows vs. row-based windows which miss date gaps.

### Customer risk scoring

**Composite score design (0–100):**

| Component | Weight | Rationale |
|---|---|---|
| Base risk rating | 40% | KYC onboarding assessment — the established baseline |
| Transaction behaviour | 30% | Flagged ratio — behavioural signal that updates continuously |
| PEP status | 20% | Binary — politically exposed persons require EDD regardless |
| Jurisdiction exposure | 15% | High-risk counterparty countries — additive risk |
| Alert escalations | Additive (capped 20) | Historical escalation to FINTRAC — strongest signal |

**Why weighted rather than rules-based:**
A rules-based system (e.g. "flag if PEP = true AND amount > $5K") produces
discrete binary outputs. A weighted score produces a continuous risk signal
that allows prioritisation — critical for an analyst queue with finite capacity.

### Statistical anomaly detection (R module)

**Approach:** Modified IQR method — 1.5× lower fence, 3.0× upper fence.

The asymmetric fences (standard IQR uses 1.5× for both) are intentional.
Financial transaction data is heavily right-skewed — large legitimate transactions
exist at the high end. A symmetric upper fence would flag too many legitimate
high-value transactions as anomalies. The 3.0× upper fence captures only
extreme outliers while the 1.5× lower fence maintains sensitivity to
unusually small transactions (which can indicate fee fraud or test transactions).

---

## 4. Technical design decisions

### Python: pandas over raw SQL for analytics

The analytics pipeline uses pandas for the primary computations rather than
doing everything in SQL. This is deliberate:

- **Composability:** pandas operations chain cleanly for multi-step analyses
  (e.g. rolling velocity → join → composite score in one pipeline)
- **Testability:** each method returns a DataFrame that can be unit-tested
- **Flexibility:** easier to add new detection patterns without schema changes

The raw SQL module (`aml_queries.sql`) demonstrates SQL competency separately,
using BigQuery/Snowflake-compatible patterns that would run in a production
data warehouse.

### Angular: OnPush change detection

The transaction monitor component uses `ChangeDetectionStrategy.OnPush`.
This is the correct choice for a high-frequency data table — default change
detection would re-render on every user interaction anywhere in the app.
OnPush only re-renders when `@Input()` references change or observables emit,
which is the right behaviour for a reactive service-driven component.

### Angular: RxJS reactive service pattern

The `FraudAnalyticsService` exposes data as `Observable` streams rather than
returning raw arrays. This is the production Angular pattern because:
- The UI automatically updates when data changes (no manual refresh)
- `combineLatest` applies filters reactively without imperative logic
- `shareReplay(1)` prevents duplicate HTTP calls on multiple subscriptions
- `distinctUntilChanged()` prevents unnecessary recomputation on filter changes

### Java: Records for DTOs

The data transfer objects use Java 16+ `record` types rather than traditional
POJOs with getters/setters. Records are:
- Immutable by default — correct for DTOs that shouldn't be mutated after construction
- Concise — no boilerplate
- Value-based equality — correct semantics for data objects

### Bilingual output (EN/FR)

The Python report prints in French when `--bilingual` is passed.
This is not cosmetic — the TD Insurance DAI team is based in Montreal and
operates bilingually. A fraud analyst presenting findings to a French-speaking
operations team needs French-language KPI labels. The bilingual flag makes the
output usable for both Toronto and Montreal stakeholders without code changes.

---

## 5. What a production version would add

This demo uses synthetic data and an in-memory SQLite database.
A production implementation at TD would include:

**Data layer**
- Real-time feed from TD's core banking system (Temenos / FIS)
- Snowflake or BigQuery as the analytical warehouse
- dbt models for data transformation and lineage
- Airflow for pipeline orchestration

**Detection enhancements**
- Machine learning: XGBoost anomaly scorer trained on historical confirmed
  STRs — higher precision than rule-based detection
- Network analysis: graph-based detection of coordinated fraud rings
  (e.g. NetworkX or Neo4j for relationship mapping)
- Real-time scoring: streaming pipeline (Kafka + Flink) for sub-second
  alert generation on high-value transactions

**Compliance & audit**
- Full audit trail: every model decision logged with feature values
- Model governance: documented model cards per OSFI E-23 requirements
- FINTRAC integration: automated STR submission pipeline

**Operational**
- Docker + Kubernetes deployment
- Power BI dashboards connected to Snowflake for management reporting
- Automated model performance monitoring (drift detection)

---

*This methodology document exists because documentation is how analysts
communicate intent — not just what the code does, but why it was built
this way. That distinction matters in regulated environments where
every analytical decision is subject to audit.*
