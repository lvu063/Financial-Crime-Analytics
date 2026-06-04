# TD Financial Crime Analytics

> AML transaction monitoring pipeline — Python, R, SQL, Java Spring Boot, and Angular TypeScript. Built in the context of TD Bank's ongoing Anti-Money Laundering compliance overhaul. Every component targets a specific TD role.

**Live demo:** [aml-insight-suite.lovable.app](https://aml-insight-suite.lovable.app) 

---

## Why this project exists

In 2024, TD Bank paid a multibillion-dollar regulatory penalty for AML deficiencies — the largest of its kind in Canadian banking history. The bank is now executing a mandatory overhaul of its financial crime monitoring infrastructure. The analytical work at the heart of that effort is exactly what this project models: detecting suspicious transaction patterns before they become regulatory violations.

---

## Repository structure

```
td-fraud-analytics/
│
├── python/
│   └── fraud_analytics.py          # AML pipeline — structuring, velocity, risk scoring
│
├── r/
│   └── fraud_analysis.R            # Statistical anomaly detection + ggplot2 visualisations
│
├── sql/
│   └── aml_queries.sql             # 5 production-grade AML SQL queries
│
├── java/
│   ├── pom.xml                     # Maven — Spring Boot 3, Java 17
│   └── src/main/java/com/tdfraud/
│       ├── TdFraudAnalyticsApplication.java
│       ├── controller/
│       │   └── FraudAlertController.java    # REST API — 8 endpoints
│       └── dto/
│           ├── TransactionDto.java
│           ├── AlertSummaryDto.java
│           └── RiskScoreDto.java
│
├── angular-demo/
│   └── src/app/
│       ├── models/transaction.model.ts      # TypeScript interfaces
│       ├── services/fraud-analytics.service.ts   # RxJS reactive service
│       ├── components/transaction-monitor/  # Filtered transaction table
│       └── app.module.ts
│
├── data/                           # Generated CSVs — run Python first
├── plots/                          # Generated R plots — run R script
└── docs/
    └── methodology.md              # AML framework, design decisions, production roadmap
```

---

## Quick start

```bash
# Python analytics pipeline
pip install pandas numpy
python python/fraud_analytics.py --export --sql

# R visualisations (requires R + packages)
Rscript r/fraud_analysis.R --export

# Java REST API
cd java && ./mvnw spring-boot:run
# → http://localhost:8080/api/v1/fraud/kpis

# Angular frontend
cd angular-demo && npm install && ng serve
# → http://localhost:4200
```

---

## Role mapping

| File | Language | TD role it targets |
|---|---|---|
| `python/fraud_analytics.py` | Python · pandas · SQLite | Actuarial Analyst II · Business Insights Analyst II · FCRM Investigative Analyst |
| `sql/aml_queries.sql` | SQL | All fraud/analytics roles |
| `r/fraud_analysis.R` | R · ggplot2 | Actuarial Analyst II (Shiny/Posit listed in JD) |
| `java/controller/FraudAlertController.java` | Java · Spring Boot | Associate Software Engineer L3 · Associate Engineer I |
| `java/dto/*.java` | Java records | Associate Software Engineer L3 · Associate Engineer I |
| `angular-demo/services/fraud-analytics.service.ts` | TypeScript · RxJS | Associate Engineer I · Associate Software Engineer L3 |
| `angular-demo/components/transaction-monitor/` | Angular · TypeScript | Associate Engineer I · Associate Software Engineer L3 |

---

## Demo 1 — Python AML Analytics Pipeline

```bash
python python/fraud_analytics.py              # full EN report
python python/fraud_analytics.py --bilingual  # FR/EN output (Montreal DAI team)
python python/fraud_analytics.py --sql        # run raw SQL queries
python python/fraud_analytics.py --export     # save 6 CSV files to data/
```

**Four detection patterns:**

| Pattern | Regulatory basis | Method |
|---|---|---|
| Structuring | PCMLTFA s.9 — CTR evasion | Cash txns between $9,500–$9,999 clustered per customer |
| High-risk jurisdiction | FINTRAC high-risk list | Transactions with counterparties in Cayman Islands, Panama, Nigeria |
| Round amount cash | Layering indicator | Large exact-round cash deposits/withdrawals |
| High velocity | Account takeover / smurfing | Rolling 7-day transaction frequency per customer |

**Composite customer risk score (0–100):**

| Component | Weight |
|---|---|
| Base KYC risk rating | 40% |
| Transaction behaviour (flagged ratio) | 30% |
| PEP status | 20% |
| High-risk jurisdiction exposure | 15% |
| FINTRAC escalation history | +20 additive, capped |

**Sample output:**
```
══════════════════════════════════════════════════════════════════════
  TD FINANCIAL CRIME ANALYTICS — AML MONITORING REPORT
  Transactions: 8,000  |  Customers: 500  |  Alerts: 475
══════════════════════════════════════════════════════════════════════

§1  STRUCTURING DETECTION
  2 customers with potential structuring patterns

§3  CRITICAL RISK CUSTOMERS
customer_id     segment    composite_risk_score  risk_tier
C00323       Commercial               100.0   Critical

§5  ALERT PERFORMANCE KPIs
  Total alerts:        475
  Escalation rate:     31.4%
  Avg alert amount:    $9,847.23
```

---

## Demo 2 — AML SQL Queries

Five production-grade queries in `sql/aml_queries.sql`:

| Query | SQL patterns |
|---|---|
| `structuring_suspects` | GROUP BY · HAVING · JOIN · threshold range |
| `high_risk_jurisdiction` | Multi-value IN · conditional COUNT · aggregation |
| `alert_aging` | Window: ratio over `PARTITION BY` analyst |
| `pep_exposure` | Boolean filter · multi-column JOIN · NULLIF |
| `monthly_trend` | CTE · rolling `AVG OVER` · cumulative `SUM OVER` |

BigQuery/Snowflake/PostgreSQL compatible — swap `strftime` for `DATE_TRUNC` for BigQuery.

---

## Demo 3 — R Analytics Module

```bash
Rscript r/fraud_analysis.R           # report + on-screen plot
Rscript r/fraud_analysis.R --export  # save 4 PNG plots to plots/
```

**Four visualisations (ggplot2):**
- Transaction amount distribution by type — flagged vs clear
- Monthly volume vs. flagged alerts — dual-axis trend
- Customer risk tier by segment — stacked proportional bar
- Structuring zone — cash amount band histogram with $9.5K–$9.999K highlighted

**Statistical method:** Modified IQR anomaly detection — asymmetric fences
(1.5× lower, 3.0× upper) to account for right-skewed financial data.
Symmetric fences would flag too many legitimate high-value transactions.

---

## Demo 4 — Java Spring Boot REST API

```bash
cd java
./mvnw spring-boot:run
```

**8 endpoints:**
```
GET /api/v1/fraud/kpis
GET /api/v1/fraud/transactions?page=0&size=25&flaggedOnly=true&minAmount=5000
GET /api/v1/fraud/transactions/{transactionId}
GET /api/v1/fraud/alerts?status=Under+Review
GET /api/v1/fraud/risk-scores?tier=Critical&segment=Commercial
GET /api/v1/fraud/risk-scores/{customerId}
GET /api/v1/fraud/structuring
GET /api/v1/fraud/jurisdiction-exposure
GET /api/v1/fraud/monthly-trends?year=2024
```

**Patterns demonstrated:**
- `@RestController` · `@GetMapping` · `@PathVariable` · `@RequestParam`
- `ResponseEntity` for explicit HTTP status control
- Service layer separation — controller never touches data directly
- Java 17 `record` types for immutable DTOs
- `@ExceptionHandler` for consistent error responses
- `@CrossOrigin` for Angular local dev integration

---

## Demo 5 — Angular Frontend

```bash
cd angular-demo
npm install
ng serve
```

**Key patterns:**
- `ChangeDetectionStrategy.OnPush` — prevents unnecessary re-renders on high-frequency table data
- RxJS `BehaviorSubject` + `combineLatest` — filters applied reactively without imperative logic
- `shareReplay(1)` — prevents duplicate HTTP calls on multiple subscriptions
- `FormBuilder` reactive forms with `debounceTime(300)` — smooth filter UX
- `takeUntil(destroy$)` — proper subscription cleanup in `ngOnDestroy`
- `async` pipe — no manual subscription management in templates

---

## Tech stack

| Layer | Technology |
|---|---|
| Analytics pipeline | Python · pandas · numpy · SQLite |
| Statistical modelling | R · ggplot2 · dplyr · IQR anomaly detection |
| SQL | Window functions · CTEs · CASE · BigQuery-portable |
| REST API | Java 17 · Spring Boot 3 · Maven · H2 (demo) |
| Frontend | Angular 17 · TypeScript · RxJS · Reactive Forms |
| Data | 500 customers · 8,000 transactions · 475 alerts (synthetic) |

---

## AML regulatory context

| Regulation | Relevance to this project |
|---|---|
| PCMLTFA s.9 | Structuring threshold — $10,000 CTR requirement |
| FINTRAC | Suspicious transaction reporting · high-risk jurisdiction lists |
| OSFI E-13 | AML program requirements for federally regulated institutions |
| FATF | International high-risk jurisdiction designations |

*All data is synthetically generated. Nothing in this repository represents real TD Bank customer, transaction, or operational data.*

---

## Bilingual support

French/English output for the Montreal-based TD Insurance DAI team:
```bash
python python/fraud_analytics.py --bilingual
```

---

*Background in international economics, data engineering, and bilingual communication.
Built to demonstrate production-level analytical thinking applied to real financial crime problems.*
