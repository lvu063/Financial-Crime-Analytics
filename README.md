# TD Financial Crime Analytics

> AML transaction monitoring pipeline — Python, R, SQL, Java Spring Boot, Angular TypeScript, MLOps monitoring. Structuring detection, velocity analysis, customer risk scoring. Deployed on AWS EC2. CI/CD via GitHub Actions.

**Live demo:** [aml-insight-suite.lovable.app](https://aml-insight-suite.lovable.app) 


**Deployed:** AWS EC2 (t2.micro, Amazon Linux 2023) · Docker containerised

---

## Why this project exists

In 2024, TD Bank paid a multibillion-dollar regulatory penalty for AML deficiencies — the largest of its kind in Canadian banking history. The bank is now executing a mandatory overhaul of its financial crime monitoring infrastructure. The analytical work at the heart of that effort is exactly what this project models: detecting suspicious transaction patterns before they become regulatory violations.

---

## Repository structure

```
td-fraud-analytics/
├── python/
│   ├── fraud_analytics.py              # AML pipeline — structuring, velocity, risk scoring
│   └── mlops_monitor.py                # Model drift detection + data quality monitoring
├── r/
│   └── fraud_analysis.R                # Statistical anomaly detection + ggplot2 visualisations
├── sql/
│   └── aml_queries.sql                 # 5 production-grade AML SQL queries
├── java/
│   ├── pom.xml                         # Maven — Spring Boot 3, Java 17
│   └── src/main/java/com/tdfraud/
│       ├── TdFraudAnalyticsApplication.java
│       ├── controller/
│       │   └── FraudAlertController.java    # REST API — 8 endpoints
│       └── dto/
│           ├── TransactionDto.java
│           ├── AlertSummaryDto.java
│           └── RiskScoreDto.java
├── angular-demo/
│   └── src/app/
│       ├── models/transaction.model.ts      # TypeScript interfaces
│       ├── services/fraud-analytics.service.ts   # RxJS reactive service
│       ├── components/transaction-monitor/  # Filtered transaction table
│       └── app.module.ts
├── .github/
│   └── workflows/ci-cd.yml             # GitHub Actions: test → lint → build → deploy
├── docs/
│   ├── methodology.md                  # AML framework, design decisions, production roadmap
│   └── agile/
│       └── PROJECT_MANAGEMENT.md       # Sprint plan, WBS, risk register
├── data/                               # Generated CSVs (gitignored)
└── plots/                              # Generated R plots (gitignored)
```

---

## Quick start

```bash
pip install pandas numpy
python python/fraud_analytics.py --export --sql
```

```bash
Rscript r/fraud_analysis.R --export
```

```bash
cd java && ./mvnw spring-boot:run
# → http://localhost:8080/api/v1/fraud/kpis
```

```bash
cd angular-demo && npm install && ng serve
# → http://localhost:4200
```

---

## Role mapping

| File | Language | Role it targets |
|---|---|---|
| `python/fraud_analytics.py` | Python · pandas · SQLite | Actuarial Analyst II · Business Insights Analyst II · FCRM Investigative Analyst |
| `python/mlops_monitor.py` | Python · numpy | Data Services Developer · Platform Developer · DevOps roles |
| `sql/aml_queries.sql` | SQL | All fraud/analytics/data engineering roles |
| `r/fraud_analysis.R` | R · ggplot2 | Actuarial Analyst II (Shiny/Posit listed in JD) |
| `java/controller/` | Java · Spring Boot | Associate Software Engineer L3 · Associate Engineer I |
| `java/dto/*.java` | Java 17 records | Associate Software Engineer L3 · Associate Engineer I |
| `angular-demo/services/` | TypeScript · RxJS | Associate Engineer I · Associate Software Engineer L3 |
| `angular-demo/components/` | Angular · TypeScript | Associate Engineer I · Associate Software Engineer L3 |
| `.github/workflows/ci-cd.yml` | GitHub Actions | CI/CD · DevOps · Data Services Developer |
| `docs/agile/` | Markdown | Agile · Scrum · project management |

---

## Demo 1 — Python AML Analytics Pipeline
*Targets: Actuarial Analyst II · Business Insights Analyst II · FCRM Investigative Analyst*

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
| High velocity | Account takeover / smurfing | Rolling 7-day transaction frequency per customer |
| High-risk jurisdiction | FINTRAC high-risk list | Counterparties in Cayman Islands, Panama, Nigeria |
| Round amount cash | Layering indicator | Large exact-round cash deposits/withdrawals |

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

## Demo 2 — MLOps Model Monitoring
*Targets: Data Services Developer · Platform Developer · DevOps/MLOps roles*

```bash
python python/fraud_analytics.py --export     # generate data first
python python/mlops_monitor.py --baseline     # set baseline
python python/mlops_monitor.py --report       # check for drift
```

**What it monitors:**

| Check | Method |
|---|---|
| Transaction amount drift | Population Stability Index (PSI) — industry standard MLOps metric |
| Alert flag rate drift | % change vs baseline threshold |
| Structuring detection rate | % change vs baseline |
| Data quality | 5 automated rules on every batch |

PSI thresholds: < 0.1 (stable) · < 0.2 (investigate) · ≥ 0.2 (model drift)

In production this would run on a schedule via Airflow and alert via Slack when thresholds are breached.

---

## Demo 3 — AML SQL Queries
*Targets: All fraud/analytics/data engineering roles*

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

## Demo 4 — R Analytics Module
*Targets: Actuarial Analyst II (Shiny/Posit listed in JD)*

```bash
Rscript r/fraud_analysis.R           # report + on-screen plot
Rscript r/fraud_analysis.R --export  # save 4 PNG plots to plots/
```

Four ggplot2 visualisations:
- Transaction amount distribution by type — flagged vs clear
- Monthly volume vs. flagged alerts — dual-axis trend
- Customer risk tier by segment — stacked proportional bar
- Structuring zone — cash amount band histogram with $9.5K–$9.999K highlighted

**Statistical method:** Modified IQR anomaly detection — asymmetric fences (1.5× lower, 3.0× upper) to account for right-skewed financial data. Symmetric fences would flag too many legitimate high-value transactions.

---

## Demo 5 — Java Spring Boot REST API
*Targets: Associate Software Engineer L3 · Associate Engineer I*

```bash
cd java && ./mvnw spring-boot:run
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

Patterns demonstrated: `@RestController` · `ResponseEntity` · service layer separation · Java 17 `record` DTOs · `@ExceptionHandler` · `@CrossOrigin`

---

## Demo 6 — Angular Frontend
*Targets: Associate Engineer I · Associate Software Engineer L3*

```bash
cd angular-demo && npm install && ng serve
```

`ChangeDetectionStrategy.OnPush` · RxJS `BehaviorSubject` + `combineLatest` · `shareReplay(1)` · `FormBuilder` reactive forms with `debounceTime(300)` · `takeUntil(destroy$)` · `async` pipe

---

## CI/CD Pipeline

```
push to main
    │
    ├── 1. Test     → pytest + data quality validation
    ├── 2. Lint     → flake8 code quality
    ├── 3. Build    → Docker image → Docker Hub
    └── 4. Deploy   → SSH to AWS EC2
```

See `.github/workflows/ci-cd.yml`.

**Required GitHub secrets:** `DOCKERHUB_USERNAME` · `DOCKERHUB_TOKEN` · `EC2_HOST` · `EC2_SSH_KEY`

---

## AWS EC2 Deployment

```bash
docker pull [YOUR_DOCKERHUB]/td-fraud-analytics:latest
docker run -d -p 8000:8000 --name td-fraud-analytics \
  --restart unless-stopped \
  [YOUR_DOCKERHUB]/td-fraud-analytics:latest
```

---

## Agile documentation

Sprint plan, WBS, risk register, and definition of done in `docs/agile/PROJECT_MANAGEMENT.md`.

3 sprints · 63 story points · 100% velocity

---

## Complete tech stack

| Layer | Technology |
|---|---|
| Analytics pipeline | Python · pandas · numpy · SQLite |
| MLOps monitoring | PSI drift detection · data quality checks |
| Statistical modelling | R · ggplot2 · dplyr · IQR anomaly detection |
| SQL | Window functions · CTEs · CASE · BigQuery-portable |
| REST API | Java 17 · Spring Boot 3 · Maven |
| Frontend | Angular 17 · TypeScript · RxJS · Reactive Forms |
| CI/CD | GitHub Actions (test → lint → build → deploy) |
| Cloud | AWS EC2 · Docker · Docker Hub |
| Agile | Scrum · user stories · sprint backlog · retrospective |
| Data | 500 customers · 8,000 transactions · 475 alerts (synthetic) |

---

## AML regulatory context

| Regulation | Relevance |
|---|---|
| PCMLTFA s.9 | Structuring threshold — $10,000 CTR requirement |
| FINTRAC | Suspicious transaction reporting · high-risk jurisdiction lists |
| OSFI E-13 | AML program requirements for federally regulated institutions |
| FATF | International high-risk jurisdiction designations |

---

## Bilingual support

French/English output for the Montreal-based TD Insurance DAI team:
```bash
python python/fraud_analytics.py --bilingual
```

---

*Background in international economics, data engineering, and bilingual communication. Built to demonstrate production-level analytical thinking applied to real financial crime problems. Nothing in this repository represents real TD Bank customer or operational data.*
```

---

*Background in international economics, data engineering, and bilingual communication.
Built to demonstrate production-level analytical thinking applied to real financial crime problems.*
