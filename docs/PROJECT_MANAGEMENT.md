# docs/agile/PROJECT_MANAGEMENT.md
# TD Financial Crime Analytics — Project Management Documentation
#
# Demonstrates: project planning, sprint methodology, stakeholder management,
# risk tracking, and delivery governance.
# Closes gaps: Agile/JIRA/Confluence, project management basics.

---

## Project Charter

**Project name:** TD Financial Crime Analytics — AML Monitoring Pipeline  
**Objective:** Build a production-inspired AML transaction monitoring system demonstrating Python analytics, SQL pattern detection, R statistical modelling, Java REST API, and Angular frontend  
**Stakeholders:** TD Financial Crime Risk Management (FCRM), TD Insurance DAI team  
**Timeline:** 6 weeks  
**Success criteria:** End-to-end pipeline operational with live demo, GitHub documentation complete, MLOps monitoring in place

---

## Work Breakdown Structure (WBS)

```
TD Financial Crime Analytics
├── 1.0 Data Layer
│   ├── 1.1 Synthetic data generation (GBM-based, 8,000 transactions)
│   ├── 1.2 ETL pipeline (validate → transform → load → verify)
│   └── 1.3 Data quality checks (4 automated rules)
├── 2.0 Analytics Engine
│   ├── 2.1 Structuring detection (PCMLTFA s.9)
│   ├── 2.2 Velocity analysis (rolling 7-day window)
│   ├── 2.3 Jurisdiction screening (FINTRAC high-risk list)
│   └── 2.4 Composite risk scoring (0–100 weighted model)
├── 3.0 SQL Layer
│   └── 3.1 Five production-grade AML queries (BigQuery-portable)
├── 4.0 R Analytics Module
│   ├── 4.1 IQR anomaly detection
│   └── 4.2 ggplot2 visualisations (bilingual)
├── 5.0 Java REST API
│   ├── 5.1 Spring Boot setup
│   └── 5.2 Eight endpoints with DTOs and error handling
├── 6.0 Angular Frontend
│   ├── 6.1 Reactive data service (RxJS)
│   └── 6.2 Transaction monitor component
├── 7.0 MLOps Monitoring
│   ├── 7.1 PSI drift detection
│   └── 7.2 Data quality validation
├── 8.0 CI/CD Pipeline
│   ├── 8.1 GitHub Actions workflow
│   └── 8.2 AWS EC2 deployment
└── 9.0 Documentation
    ├── 9.1 README
    ├── 9.2 Methodology doc
    └── 9.3 Agile artifacts
```

---

## Sprint Plan

### Sprint 1 — Core Analytics (Week 1–2)
**Goal:** Working Python pipeline with AML detection and risk scoring

| Task | Story Points | Status |
|---|---|---|
| Synthetic data generator | 3 | ✅ Done |
| ETL pipeline with validation | 5 | ✅ Done |
| Structuring detection | 3 | ✅ Done |
| Velocity analysis | 3 | ✅ Done |
| Risk scoring model | 5 | ✅ Done |
| Unit tests | 3 | ✅ Done |

**Sprint 1 velocity:** 22 points

### Sprint 2 — SQL + R + API (Week 3–4)
**Goal:** SQL queries, R module, Java REST API

| Task | Story Points | Status |
|---|---|---|
| 5 AML SQL queries | 5 | ✅ Done |
| R IQR anomaly detection | 3 | ✅ Done |
| ggplot2 visualisations | 2 | ✅ Done |
| Java Spring Boot setup | 3 | ✅ Done |
| 8 REST endpoints | 5 | ✅ Done |

**Sprint 2 velocity:** 18 points

### Sprint 3 — Frontend + MLOps + CI/CD (Week 5–6)
**Goal:** Angular UI, monitoring, and cloud deployment

| Task | Story Points | Status |
|---|---|---|
| Angular reactive service | 5 | ✅ Done |
| Transaction monitor component | 5 | ✅ Done |
| MLOps monitoring (PSI + drift) | 5 | ✅ Done |
| GitHub Actions CI/CD pipeline | 3 | ✅ Done |
| AWS EC2 deployment | 5 | ✅ Done |

**Sprint 3 velocity:** 23 points

---

## Risk Register

| Risk | Probability | Impact | Mitigation |
|---|---|---|---|
| AWS EC2 free tier limits exceeded | Low | Medium | Stop instance when not demoing; monitor usage |
| API key expiry breaks live demo | Medium | High | Mock mode available — demo works without any key |
| Dependency version conflicts | Medium | Low | Pin versions in requirements.txt |
| Regulatory inaccuracy in AML logic | Low | High | Cross-reference PCMLTFA and FINTRAC guidance; document limitations |

---

## Definition of Done

A feature is done when:
- [ ] Code is merged to `main` via pull request
- [ ] Unit tests written and passing in CI
- [ ] No new Flake8 warnings introduced
- [ ] README updated to reflect the change
- [ ] Mock mode works without external dependencies
