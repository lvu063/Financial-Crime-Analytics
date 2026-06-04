# TD Financial Crime Analytics

> AML transaction monitoring pipeline and fraud detection framework — built in the context of TD Bank's ongoing Anti-Money Laundering compliance overhaul. Demonstrates production-level Python analytics, SQL pattern detection, and Angular frontend development.

**Live demo:** [aml-insight-suite.lovable.app](https://aml-insight-suite.lovable.app) 

---

## Why this project

TD Bank is currently executing one of the largest AML compliance overhauls in Canadian banking history — a multibillion-dollar program to remediate Anti-Money Laundering deficiencies. The analytical work at the heart of that effort is exactly what this project models: detecting suspicious patterns in transaction data before they become regulatory violations.

This project targets three TD roles:
- **Actuarial Analyst II (Fraud)** — TD Insurance DAI team
- **Business Insights Analyst II (Fraud)** — TD Insurance DAI team
- **Financial Crime Risk Investigative Analyst** — TD Financial Crime Risk Management

---

## Repository Structure

```
td-fraud-analytics/
├── python/
│   └── fraud_analytics.py          # AML monitoring pipeline — Python + pandas + SQL
├── sql/
│   └── aml_queries.sql             # 5 production-grade AML SQL queries
├── angular-demo/
│   └── src/app/
│       ├── models/                 # TypeScript interfaces
│       ├── services/               # Reactive Angular service (RxJS)
│       └── components/             # Transaction monitor + risk dashboard
├── data/                           # Generated CSVs (run python first)
└── docs/
    └── methodology.md              # AML framework and design decisions
```

---

## Quick Start

```bash
pip install pandas numpy
python python/fraud_analytics.py --export --sql
```

---

## Demo 1 — Python AML Analytics Pipeline
*Targets: Actuarial Analyst II, Business Insights Analyst II*

```bash
python python/fraud_analytics.py              # full report
python python/fraud_analytics.py --sql        # raw AML SQL queries
python python/fraud_analytics.py --bilingual  # French/English output
python python/fraud_analytics.py --export     # save 6 CSVs
```

**What it detects:**

| Pattern | Method | Regulatory relevance |
|---|---|---|
| Structuring | Amounts clustered $9,500–$9,999 | PCMLTFA s.9 — CTR evasion |
| High-risk jurisdiction | Counterparty in Cayman Islands, Panama, Nigeria | FINTRAC guidance |
| Round amount cash | Large round number cash transactions | Layering indicator |
| High velocity | Rolling 7-day transaction frequency | Account takeover / smurfing |

**Customer risk scoring:**

| Component | Weight | Source |
|---|---|---|
| Base risk rating | 40% | KYC onboarding |
| Transaction behaviour | 30% | Flagged ratio |
| PEP status | 20% | Enhanced due diligence |
| Jurisdiction exposure | 15% | FINTRAC high-risk list |
| Alert escalations | Additive | Investigation history |

**Sample output:**
```
§1  STRUCTURING DETECTION
  2 customers with potential structuring patterns

§3  CRITICAL RISK CUSTOMERS
customer_id     segment    composite_risk_score  risk_tier
C00323       Commercial               100.0   Critical
C00108       Commercial               100.0   Critical

§5  ALERT PERFORMANCE KPIs
  Total alerts:        475
  Escalation rate:     31.4%
  Avg alert amount:    $9,847.23
```

---

## Demo 2 — AML SQL Queries
*Production-grade patterns for BigQuery/Snowflake/PostgreSQL*

Five queries demonstrating the SQL skills both fraud analyst JDs require:

| Query | Pattern demonstrated |
|---|---|
| `structuring_suspects` | GROUP BY + HAVING, JOIN, threshold logic |
| `high_risk_jurisdiction` | Multi-value IN, aggregation, conditional COUNT |
| `alert_aging` | Window function: ratio over PARTITION BY analyst |
| `pep_exposure` | Enhanced due diligence — PEP customer deep-dive |
| `monthly_trend` | CTE, window function cumulative count, flag rate |

**SQL highlight — structuring detection:**
```sql
SELECT customer_id, COUNT(*) AS near_threshold_txns,
       SUM(amount_cad) AS total_amount
FROM transactions
WHERE amount_cad BETWEEN 9500 AND 9999.99
  AND transaction_type IN ('Cash Deposit', 'Cash Withdrawal')
GROUP BY customer_id
HAVING COUNT(*) >= 2
ORDER BY near_threshold_txns DESC
```

---

## Demo 3 — Angular Frontend
*Targets: Associate Engineer I, Associate Software Engineer L3*

TypeScript + Angular 17 transaction monitoring dashboard demonstrating:

- **Reactive service** with RxJS BehaviorSubject, combineLatest, shareReplay
- **OnPush change detection** for performance
- **Reactive forms** with debounced filter updates
- **TypeScript interfaces** with strict typing across all models
- **Angular pipes** for data transformation
- **Async pipe** for subscription management

```bash
cd angular-demo
npm install
ng serve
```

**Key Angular patterns shown:**
- Dependency injection via `@Injectable({ providedIn: 'root' })`
- Component lifecycle: `ngOnInit` / `ngOnDestroy` with `takeUntil`
- Template syntax: `*ngFor`, `*ngIf`, `[ngClass]`, `(click)`, `| async`
- Reactive forms: `FormBuilder`, `formGroup`, `formControlName`

---

## Tech Stack

| Layer | Technology |
|---|---|
| Analytics | Python · pandas · numpy · SQLite |
| SQL | Window functions · CTEs · CASE · BigQuery-portable |
| Frontend | Angular 17 · TypeScript · RxJS · Reactive Forms |
| Deployment | Lovable (React demo) · GitHub |
| Data | 500 customers · 8,000 transactions · 475 alerts (synthetic) |

---

## Bilingual support

The analytics report runs in both English and French:
```bash
python python/fraud_analytics.py --bilingual
```

Output headings, labels, and KPIs render in French — relevant for TD Insurance's Montreal-based DAI team.

---

## AML Regulatory Context

This project models patterns covered by:
- **PCMLTFA** — Proceeds of Crime (Money Laundering) and Terrorist Financing Act
- **FINTRAC** guidance on suspicious transaction reporting
- **OSFI** guidelines on AML risk management for federally regulated institutions
- **FATF** high-risk jurisdiction lists

*All data is synthetically generated. Nothing in this project represents real TD Bank customer or transaction data.*

---

*Built as a portfolio project targeting financial crime analytics roles at TD Bank. Background in international economics, data engineering, and bilingual communication — strong on analytical rigour and building systems that surface the right signal from noisy data.*

---

## Demo 4 — R Analytics Module
*Targets: Actuarial Analyst II (TD Insurance DAI team)*

```bash
Rscript r/fraud_analysis.R            # full report + plot
Rscript r/fraud_analysis.R --export   # save 4 PNG plots
```

**What it produces:**

| Analysis | Method |
|---|---|
| Statistical anomaly detection | IQR method — 1.5× lower, 3× upper fence (right-skewed financial data) |
| Monthly trend analysis | ggplot2 dual-axis: volume bars + flagged line |
| Risk tier distribution | Stacked bar by customer segment |
| Structuring zone detection | Amount band histogram with $9.5K–$9.999K highlight |

Bilingual labels (EN/FR) throughout — relevant for Montreal-based DAI team.

---

## Demo 5 — Java Spring Boot REST API
*Targets: Associate Software Engineer L3, Associate Engineer I*

A production-style REST API exposing the analytics pipeline as endpoints consumable by the Angular frontend.

```
GET /api/v1/fraud/kpis
GET /api/v1/fraud/transactions?page=0&size=25&flaggedOnly=true
GET /api/v1/fraud/transactions/{transactionId}
GET /api/v1/fraud/alerts?status=Under+Review
GET /api/v1/fraud/risk-scores?tier=Critical
GET /api/v1/fraud/structuring
GET /api/v1/fraud/jurisdiction-exposure
GET /api/v1/fraud/monthly-trends?year=2024
```

```bash
cd java
./mvnw spring-boot:run
# API available at http://localhost:8080
```

**Patterns demonstrated:**
- `@RestController` with proper HTTP verb mapping
- `ResponseEntity` for HTTP status control
- Service layer separation — controller never touches data
- Java records (Java 16+) for immutable DTOs
- `@ExceptionHandler` for consistent error responses
- `@CrossOrigin` for Angular local dev integration

---

## Complete Tech Stack

| Layer | Technology |
|---|---|
| Analytics | Python · pandas · numpy · SQLite |
| Statistical modelling | R · ggplot2 · dplyr · IQR anomaly detection |
| REST API | Java 17 · Spring Boot 3 · Maven |
| Frontend | Angular 17 · TypeScript · RxJS · Reactive Forms |
| SQL | Window functions · CTEs · CASE · BigQuery-portable |
| Deployment | Lovable demo · GitHub |
