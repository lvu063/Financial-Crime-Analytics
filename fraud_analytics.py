"""
fraud_analytics.py
------------------
TD Financial Crime Analytics — AML Transaction Monitoring Demo

Demonstrates core skills for TD fraud analyst roles:
  - Transaction monitoring and anomaly detection
  - AML pattern recognition (structuring, velocity, layering)
  - Customer risk scoring
  - Data quality and governance
  - Bilingual reporting (EN/FR)

Relevant to:
  - Actuarial Analyst II (Fraud) — TD Insurance DAI team
  - Business Insights Analyst II (Fraud) — TD Insurance DAI team
  - Financial Crime Risk Investigative Analyst
  - AML Financial Crime Risk Investigation Support Officer II

Context:
  TD Bank is currently executing a multi-billion dollar AML compliance
  overhaul following a 2024 regulatory settlement. This project models
  the analytical work at the heart of that effort — identifying suspicious
  transaction patterns before they become regulatory violations.

Usage:
    python python/fraud_analytics.py                    # full analysis
    python python/fraud_analytics.py --export           # save CSVs
    python python/fraud_analytics.py --report aml       # AML patterns only
    python python/fraud_analytics.py --report risk      # risk scores only
    python python/fraud_analytics.py --bilingual        # FR/EN output
"""

from __future__ import annotations

import argparse
import random
import sqlite3
from dataclasses import dataclass
from datetime import date, timedelta, datetime
from pathlib import Path

import numpy as np
import pandas as pd

# ─────────────────────────────────────────────────────────────────────────────
# Synthetic data generation
# ─────────────────────────────────────────────────────────────────────────────

CUSTOMER_SEGMENTS = ["Retail", "Small Business", "Commercial", "Wealth"]
TRANSACTION_TYPES = ["Wire Transfer", "Cash Deposit", "Cash Withdrawal",
                     "Interac e-Transfer", "ACH", "Cheque Deposit", "POS"]
CHANNELS          = ["Branch", "Online Banking", "Mobile App", "ATM", "Wire Desk"]
COUNTRIES         = ["Canada", "United States", "United Kingdom", "Mexico",
                     "Cayman Islands", "Panama", "Switzerland", "Nigeria"]
HIGH_RISK_COUNTRIES = {"Cayman Islands", "Panama", "Nigeria"}

rng = random.Random(42)
np_rng = np.random.RandomState(42)


def random_date(start: date, end: date) -> date:
    return start + timedelta(days=rng.randint(0, (end - start).days))


def generate_customers(n: int = 500) -> pd.DataFrame:
    rows = []
    for i in range(1, n + 1):
        segment  = rng.choice(CUSTOMER_SEGMENTS)
        country  = rng.choices(COUNTRIES, weights=[70, 15, 5, 3, 2, 2, 2, 1])[0]
        opened   = random_date(date(2015, 1, 1), date(2023, 12, 31))
        pep      = rng.random() < 0.02   # 2% politically exposed persons
        rows.append({
            "customer_id":      f"C{i:05d}",
            "segment":          segment,
            "country_of_origin": country,
            "account_opened":   opened.isoformat(),
            "is_pep":           pep,
            "risk_rating":      rng.choice(["Low", "Low", "Low", "Medium", "High"]),
            "monthly_income_est": rng.randint(2000, 25000),
        })
    return pd.DataFrame(rows)


def generate_transactions(customers: pd.DataFrame, n: int = 8000) -> pd.DataFrame:
    rows = []
    cust_ids = customers["customer_id"].tolist()

    for i in range(1, n + 1):
        cust_id  = rng.choice(cust_ids)
        txn_type = rng.choice(TRANSACTION_TYPES)
        channel  = rng.choice(CHANNELS)
        txn_date = random_date(date(2024, 1, 1), date(2024, 12, 31))

        # Base amount — most transactions are small
        if rng.random() < 0.85:
            amount = round(np_rng.lognormal(7, 1.2), 2)   # ~$1,000 typical
        else:
            amount = round(np_rng.lognormal(10, 0.8), 2)  # ~$22,000 large

        # Inject suspicious patterns for ~8% of transactions
        is_suspicious = False
        suspicious_flag = ""

        # Pattern 1: Structuring — amounts just below $10,000 reporting threshold
        if rng.random() < 0.03:
            amount = round(rng.uniform(9000, 9999), 2)
            is_suspicious = True
            suspicious_flag = "STRUCTURING"

        # Pattern 2: Round number large cash deposits
        if txn_type in ("Cash Deposit", "Cash Withdrawal") and rng.random() < 0.02:
            amount = float(rng.choice([5000, 10000, 15000, 20000, 25000, 50000]))
            is_suspicious = True
            suspicious_flag = "ROUND_AMOUNT_CASH"

        counterparty_country = rng.choices(
            COUNTRIES, weights=[60, 18, 6, 4, 3, 3, 3, 3])[0]
        if counterparty_country in HIGH_RISK_COUNTRIES and amount > 5000:
            is_suspicious = True
            suspicious_flag = suspicious_flag or "HIGH_RISK_JURISDICTION"

        rows.append({
            "transaction_id":        f"TXN{i:07d}",
            "customer_id":           cust_id,
            "transaction_date":      txn_date.isoformat(),
            "transaction_type":      txn_type,
            "channel":               channel,
            "amount_cad":            amount,
            "counterparty_country":  counterparty_country,
            "is_flagged":            is_suspicious,
            "flag_reason":           suspicious_flag,
        })
    return pd.DataFrame(rows)


def generate_alerts(transactions: pd.DataFrame) -> pd.DataFrame:
    """Escalated alerts from flagged transactions."""
    flagged = transactions[transactions["is_flagged"]].copy()
    flagged["alert_id"]     = [f"ALT{i:05d}" for i in range(1, len(flagged) + 1)]
    flagged["alert_date"]   = flagged["transaction_date"]
    flagged["status"]       = np.where(
        np.random.RandomState(99).random(len(flagged)) < 0.3,
        "Closed - No Action",
        np.where(
            np.random.RandomState(99).random(len(flagged)) < 0.5,
            "Under Review",
            "Escalated to FINTRAC"
        )
    )
    flagged["assigned_to"]  = np.random.choice(
        ["Analyst A", "Analyst B", "Analyst C"], len(flagged))
    return flagged[["alert_id", "transaction_id", "customer_id",
                    "alert_date", "flag_reason", "amount_cad",
                    "status", "assigned_to"]]


# ─────────────────────────────────────────────────────────────────────────────
# Analytics
# ─────────────────────────────────────────────────────────────────────────────

class FraudAnalytics:
    """
    Core AML/fraud analytics — mirrors TD Insurance DAI team workflows.

    Methods map directly to job description requirements:
      - detect_structuring()     → "identify fraud patterns, emerging risks"
      - velocity_analysis()      → "analyze trends in retail collections"
      - customer_risk_score()    → "develop new strategies to drive business performance"
      - data_quality_report()    → "ensure data quality through validation"
      - jurisdiction_exposure()  → "AML operations, standards, procedures"
    """

    def __init__(self, customers, transactions, alerts):
        self.customers    = customers
        self.transactions = transactions
        self.alerts       = alerts

    # ------------------------------------------------------------------
    # 1. Structuring detection — amounts clustered just below $10K
    # ------------------------------------------------------------------
    def detect_structuring(self, threshold: float = 10000,
                           window: float = 500) -> pd.DataFrame:
        """
        Structuring: breaking large transactions into smaller amounts
        to evade currency transaction reporting requirements (PCMLTFA s.9).

        SQL equivalent:
            SELECT customer_id, COUNT(*) as txn_count,
                   SUM(amount_cad) as total_amount,
                   AVG(amount_cad) as avg_amount
            FROM transactions
            WHERE amount_cad BETWEEN 9500 AND 9999.99
              AND transaction_type IN ('Cash Deposit', 'Cash Withdrawal')
            GROUP BY customer_id
            HAVING COUNT(*) >= 2
            ORDER BY txn_count DESC
        """
        window_low  = threshold - window
        window_high = threshold - 0.01
        cash_types  = ["Cash Deposit", "Cash Withdrawal"]

        near_threshold = self.transactions[
            (self.transactions["amount_cad"].between(window_low, window_high)) &
            (self.transactions["transaction_type"].isin(cash_types))
        ]

        return (
            near_threshold
            .groupby("customer_id")
            .agg(
                txn_count    = ("transaction_id", "count"),
                total_amount = ("amount_cad", "sum"),
                avg_amount   = ("amount_cad", "mean"),
            )
            .query("txn_count >= 2")
            .sort_values("txn_count", ascending=False)
            .round(2)
            .reset_index()
        )

    # ------------------------------------------------------------------
    # 2. Velocity analysis — unusual transaction frequency
    # ------------------------------------------------------------------
    def velocity_analysis(self, window_days: int = 7,
                          threshold_count: int = 5) -> pd.DataFrame:
        """
        Velocity check: customers with unusually high transaction frequency
        in a rolling window — a key indicator of account takeover or layering.

        SQL equivalent:
            SELECT customer_id, transaction_date,
                   COUNT(*) OVER (
                       PARTITION BY customer_id
                       ORDER BY transaction_date
                       ROWS BETWEEN 6 PRECEDING AND CURRENT ROW
                   ) as rolling_7day_count
            FROM transactions
        """
        df = self.transactions.copy()
        df["transaction_date"] = pd.to_datetime(df["transaction_date"])
        df = df.sort_values(["customer_id", "transaction_date"])

        rolling = (
            df.groupby("customer_id")
            .apply(lambda x: x.set_index("transaction_date")["transaction_id"]
                   .rolling(f"{window_days}D").count())
            .reset_index()
        )
        rolling.columns = ["customer_id", "transaction_date", "rolling_count"]

        high_velocity = (
            rolling[rolling["rolling_count"] >= threshold_count]
            .groupby("customer_id")
            .agg(max_daily_burst=("rolling_count", "max"),
                 high_velocity_days=("rolling_count", "count"))
            .sort_values("max_daily_burst", ascending=False)
            .reset_index()
        )
        return high_velocity

    # ------------------------------------------------------------------
    # 3. Customer risk scoring — composite AML risk model
    # ------------------------------------------------------------------
    def customer_risk_score(self) -> pd.DataFrame:
        """
        Composite customer risk score combining:
          - Base risk rating (from onboarding KYC)
          - PEP status (politically exposed person)
          - Transaction behaviour (flagged ratio)
          - Jurisdiction risk (high-risk country exposure)
          - Alert history (escalations)

        This is the "risk strategy" the TD fraud JD references.
        """
        # Base score from risk rating
        risk_map = {"Low": 10, "Medium": 40, "High": 70}
        df = self.customers.copy()
        df["score_base"] = df["risk_rating"].map(risk_map)

        # PEP premium
        df["score_pep"] = df["is_pep"].astype(int) * 20

        # Flagged transaction ratio
        txn_stats = (
            self.transactions
            .groupby("customer_id")
            .agg(
                total_txns   = ("transaction_id", "count"),
                flagged_txns = ("is_flagged", "sum"),
                total_amount = ("amount_cad", "sum"),
            )
        )
        txn_stats["flag_ratio"] = (
            txn_stats["flagged_txns"] / txn_stats["total_txns"].clip(lower=1)
        )
        txn_stats["score_behaviour"] = (txn_stats["flag_ratio"] * 30).clip(upper=30)

        # High-risk jurisdiction exposure
        jurisdiction_risk = (
            self.transactions[
                self.transactions["counterparty_country"].isin(HIGH_RISK_COUNTRIES)
            ]
            .groupby("customer_id")
            .size()
            .rename("hrc_txn_count")
        )

        # Alert escalations
        alert_score = (
            self.alerts[self.alerts["status"] == "Escalated to FINTRAC"]
            .groupby("customer_id")
            .size()
            .rename("escalations")
        )

        df = (
            df.merge(txn_stats[["score_behaviour", "total_txns",
                                 "flagged_txns", "total_amount"]],
                     on="customer_id", how="left")
              .merge(jurisdiction_risk, on="customer_id", how="left")
              .merge(alert_score, on="customer_id", how="left")
              .fillna({"score_behaviour": 0, "hrc_txn_count": 0,
                       "escalations": 0, "total_txns": 0,
                       "flagged_txns": 0, "total_amount": 0})
        )

        df["score_jurisdiction"] = (df["hrc_txn_count"] * 3).clip(upper=15)
        df["score_escalations"]  = (df["escalations"] * 10).clip(upper=20)
        df["composite_risk_score"] = (
            df["score_base"] + df["score_pep"] + df["score_behaviour"] +
            df["score_jurisdiction"] + df["score_escalations"]
        ).clip(upper=100).round(1)

        df["risk_tier"] = pd.cut(
            df["composite_risk_score"],
            bins=[0, 25, 50, 75, 100],
            labels=["Low", "Medium", "High", "Critical"]
        )

        return df.sort_values("composite_risk_score", ascending=False)

    # ------------------------------------------------------------------
    # 4. Jurisdiction exposure heatmap
    # ------------------------------------------------------------------
    def jurisdiction_exposure(self) -> pd.DataFrame:
        """
        Transaction volume and value by counterparty country.
        Flags high-risk jurisdictions per FINTRAC guidance.
        """
        exp = (
            self.transactions
            .groupby("counterparty_country")
            .agg(
                txn_count    = ("transaction_id", "count"),
                total_cad    = ("amount_cad", "sum"),
                avg_amount   = ("amount_cad", "mean"),
                flagged      = ("is_flagged", "sum"),
            )
            .round(2)
            .sort_values("total_cad", ascending=False)
            .reset_index()
        )
        exp["is_high_risk"] = exp["counterparty_country"].isin(HIGH_RISK_COUNTRIES)
        exp["flag_rate_pct"] = (exp["flagged"] / exp["txn_count"] * 100).round(1)
        return exp

    # ------------------------------------------------------------------
    # 5. Alert performance dashboard
    # ------------------------------------------------------------------
    def alert_performance(self) -> dict:
        """
        Operational KPIs for the AML alert queue —
        the kind of metrics a fraud analyst tracks daily.
        """
        total     = len(self.alerts)
        by_status = self.alerts["status"].value_counts().to_dict()
        by_reason = self.alerts["flag_reason"].value_counts().to_dict()
        by_analyst = self.alerts["assigned_to"].value_counts().to_dict()

        escalation_rate = round(
            by_status.get("Escalated to FINTRAC", 0) / max(total, 1) * 100, 1
        )
        avg_alert_amount = round(self.alerts["amount_cad"].mean(), 2)

        return {
            "total_alerts":       total,
            "by_status":          by_status,
            "by_flag_reason":     by_reason,
            "by_analyst":         by_analyst,
            "escalation_rate_pct": escalation_rate,
            "avg_alert_amount_cad": avg_alert_amount,
            "high_value_alerts":  int((self.alerts["amount_cad"] > 10000).sum()),
        }

    # ------------------------------------------------------------------
    # 6. Data quality report
    # ------------------------------------------------------------------
    def data_quality_report(self) -> dict:
        """
        Data quality checks — a core responsibility in both fraud analyst JDs.
        Identifies issues that would corrupt monitoring models.
        """
        issues = []

        # Missing transaction types
        missing_type = self.transactions["transaction_type"].isna().sum()
        if missing_type:
            issues.append({"check": "Missing transaction_type",
                           "count": int(missing_type), "severity": "High"})

        # Negative amounts
        neg_amounts = (self.transactions["amount_cad"] <= 0).sum()
        if neg_amounts:
            issues.append({"check": "Non-positive transaction amounts",
                           "count": int(neg_amounts), "severity": "High"})

        # Future-dated transactions
        today = date.today()
        future = (
            pd.to_datetime(self.transactions["transaction_date"]).dt.date > today
        ).sum()
        if future:
            issues.append({"check": "Future-dated transactions",
                           "count": int(future), "severity": "Medium"})

        # Customers with no transactions
        no_txn = set(self.customers["customer_id"]) - set(
            self.transactions["customer_id"])
        if no_txn:
            issues.append({"check": "Customers with zero transactions",
                           "count": len(no_txn), "severity": "Low"})

        return {
            "total_issues":      len(issues),
            "high_severity":     sum(1 for i in issues if i["severity"] == "High"),
            "issues":            issues,
            "data_quality_score": round((1 - len(issues) / 8) * 100, 1),
        }

    def print_report(self, bilingual: bool = False):
        """Print formatted analytics report."""
        lang = "fr" if bilingual else "en"
        labels = {
            "en": {
                "title": "TD FINANCIAL CRIME ANALYTICS — AML MONITORING REPORT",
                "structuring": "STRUCTURING DETECTION",
                "velocity": "HIGH VELOCITY ACCOUNTS (TOP 10)",
                "risk": "CRITICAL RISK CUSTOMERS (TOP 10)",
                "jurisdiction": "JURISDICTION EXPOSURE",
                "alerts": "ALERT PERFORMANCE KPIs",
                "quality": "DATA QUALITY REPORT",
            },
            "fr": {
                "title": "ANALYTIQUE CRIMINALITÉ FINANCIÈRE TD — RAPPORT SURVEILLANCE LBC",
                "structuring": "DÉTECTION DE FRACTIONNEMENT",
                "velocity": "COMPTES À HAUTE VÉLOCITÉ (TOP 10)",
                "risk": "CLIENTS À RISQUE CRITIQUE (TOP 10)",
                "jurisdiction": "EXPOSITION AUX JURIDICTIONS",
                "alerts": "KPIs DE PERFORMANCE DES ALERTES",
                "quality": "RAPPORT DE QUALITÉ DES DONNÉES",
            },
        }[lang]

        print("\n" + "═" * 70)
        print(f"  {labels['title']}")
        print(f"  Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  "
              f"Transactions: {len(self.transactions):,}  |  "
              f"Customers: {len(self.customers):,}")
        print("═" * 70)

        print(f"\n§1  {labels['structuring']}")
        struct = self.detect_structuring()
        print(f"  {len(struct)} customers with potential structuring patterns")
        if len(struct):
            print(struct.head(5).to_string(index=False))

        print(f"\n§2  {labels['velocity']}")
        vel = self.velocity_analysis()
        print(vel.head(10).to_string(index=False))

        print(f"\n§3  {labels['risk']}")
        risk = self.customer_risk_score()
        cols = ["customer_id", "segment", "composite_risk_score",
                "risk_tier", "flagged_txns", "escalations"]
        print(risk[risk["risk_tier"] == "Critical"][cols].head(10).to_string(
            index=False))

        print(f"\n§4  {labels['jurisdiction']}")
        jur = self.jurisdiction_exposure()
        print(jur.to_string(index=False))

        print(f"\n§5  {labels['alerts']}")
        perf = self.alert_performance()
        print(f"  Total alerts:        {perf['total_alerts']}")
        print(f"  Escalation rate:     {perf['escalation_rate_pct']}%")
        print(f"  Avg alert amount:    ${perf['avg_alert_amount_cad']:,.2f}")
        print(f"  High value (>$10K):  {perf['high_value_alerts']}")
        for status, count in perf["by_status"].items():
            print(f"  {status:<30} {count}")

        print(f"\n§6  {labels['quality']}")
        dq = self.data_quality_report()
        print(f"  Data quality score: {dq['data_quality_score']}%")
        print(f"  Issues found: {dq['total_issues']}  |  "
              f"High severity: {dq['high_severity']}")
        for issue in dq["issues"]:
            print(f"  [{issue['severity']:6}] {issue['check']} — "
                  f"{issue['count']} records")

        print("\n" + "═" * 70)


# ─────────────────────────────────────────────────────────────────────────────
# SQLite demo — raw SQL competency
# ─────────────────────────────────────────────────────────────────────────────

AML_SQL_QUERIES = {
    "structuring_suspects": """
        -- Customers with multiple cash transactions just below $10K threshold
        -- Potential structuring under PCMLTFA s.9
        SELECT
            t.customer_id,
            c.segment,
            c.risk_rating,
            COUNT(*)                    AS near_threshold_txns,
            SUM(t.amount_cad)           AS total_amount,
            AVG(t.amount_cad)           AS avg_amount,
            MIN(t.transaction_date)     AS first_txn,
            MAX(t.transaction_date)     AS last_txn
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE t.amount_cad BETWEEN 9500 AND 9999.99
          AND t.transaction_type IN ('Cash Deposit', 'Cash Withdrawal')
        GROUP BY t.customer_id, c.segment, c.risk_rating
        HAVING COUNT(*) >= 2
        ORDER BY near_threshold_txns DESC, total_amount DESC
    """,

    "high_risk_jurisdiction": """
        -- Transactions with high-risk jurisdiction counterparties over $5K
        SELECT
            t.customer_id,
            c.risk_rating,
            t.counterparty_country,
            COUNT(*)                AS txn_count,
            SUM(t.amount_cad)       AS total_exposure,
            MAX(t.amount_cad)       AS largest_txn,
            COUNT(CASE WHEN t.is_flagged = 1 THEN 1 END) AS already_flagged
        FROM transactions t
        JOIN customers c ON t.customer_id = c.customer_id
        WHERE t.counterparty_country IN ('Cayman Islands','Panama','Nigeria')
          AND t.amount_cad > 5000
        GROUP BY t.customer_id, c.risk_rating, t.counterparty_country
        ORDER BY total_exposure DESC
    """,

    "alert_aging": """
        -- Alert aging analysis — how long are alerts sitting in queue?
        -- Window function: running count by analyst and status
        SELECT
            assigned_to,
            status,
            COUNT(*)                AS alert_count,
            AVG(amount_cad)         AS avg_amount,
            SUM(amount_cad)         AS total_amount,
            COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (PARTITION BY assigned_to)
                                    AS pct_of_analyst_queue
        FROM alerts
        GROUP BY assigned_to, status
        ORDER BY assigned_to, alert_count DESC
    """,

    "pep_exposure": """
        -- PEP customers with significant transaction activity
        -- PEPs require enhanced due diligence under FINTRAC guidance
        SELECT
            c.customer_id,
            c.segment,
            c.country_of_origin,
            c.risk_rating,
            COUNT(t.transaction_id)     AS total_transactions,
            SUM(t.amount_cad)           AS total_volume_cad,
            SUM(CASE WHEN t.is_flagged = 1 THEN 1 ELSE 0 END) AS flagged_count,
            MAX(t.amount_cad)           AS largest_single_txn
        FROM customers c
        JOIN transactions t ON c.customer_id = t.customer_id
        WHERE c.is_pep = 1
        GROUP BY c.customer_id, c.segment, c.country_of_origin, c.risk_rating
        ORDER BY total_volume_cad DESC
    """,

    "monthly_trend": """
        -- Monthly transaction trends — identify volume anomalies
        -- CTE pattern for clean staging
        WITH monthly AS (
            SELECT
                strftime('%Y-%m', transaction_date) AS month,
                transaction_type,
                COUNT(*)            AS txn_count,
                SUM(amount_cad)     AS total_amount,
                SUM(is_flagged)     AS flagged_count
            FROM transactions
            GROUP BY month, transaction_type
        )
        SELECT
            month,
            transaction_type,
            txn_count,
            ROUND(total_amount, 2)          AS total_amount,
            flagged_count,
            ROUND(flagged_count * 100.0 / txn_count, 2) AS flag_rate_pct,
            SUM(txn_count) OVER (PARTITION BY transaction_type
                                 ORDER BY month)        AS cumulative_count
        FROM monthly
        ORDER BY month, total_amount DESC
    """,
}


def run_sql_demo(customers_df, transactions_df, alerts_df):
    conn = sqlite3.connect(":memory:")
    customers_df.to_sql("customers",    conn, index=False, if_exists="replace")
    transactions_df.to_sql("transactions", conn, index=False, if_exists="replace")
    alerts_df.to_sql("alerts",          conn, index=False, if_exists="replace")

    print("\n" + "═" * 70)
    print("  AML SQL QUERIES — SQLite Demo")
    print("═" * 70)
    for name, sql in AML_SQL_QUERIES.items():
        print(f"\n─── {name} ───")
        result = pd.read_sql_query(sql, conn)
        print(result.head(8).to_string(index=False))

    conn.close()


# ─────────────────────────────────────────────────────────────────────────────
# Main
# ─────────────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="TD Financial Crime Analytics — AML Monitoring Demo")
    parser.add_argument("--export",   action="store_true",
                        help="Export all datasets to CSV")
    parser.add_argument("--sql",      action="store_true",
                        help="Run raw SQL queries via SQLite")
    parser.add_argument("--bilingual", action="store_true",
                        help="Print report in French")
    parser.add_argument("--report",   choices=["aml", "risk", "all"],
                        default="all", help="Which report section to run")
    args = parser.parse_args()

    print("\n━" * 35)
    print("  TD FINANCIAL CRIME ANALYTICS")
    print("  AML Transaction Monitoring Pipeline")
    print("━" * 35)

    print("\nGenerating synthetic transaction data...")
    customers    = generate_customers(500)
    transactions = generate_transactions(customers, 8000)
    alerts       = generate_alerts(transactions)
    print(f"  {len(customers):,} customers · {len(transactions):,} transactions · "
          f"{len(alerts):,} alerts")

    analytics = FraudAnalytics(customers, transactions, alerts)
    analytics.print_report(bilingual=args.bilingual)

    if args.sql:
        run_sql_demo(customers, transactions, alerts)

    if args.export:
        out = Path("data")
        out.mkdir(exist_ok=True)
        customers.to_csv(out / "customers.csv", index=False)
        transactions.to_csv(out / "transactions.csv", index=False)
        alerts.to_csv(out / "alerts.csv", index=False)
        analytics.detect_structuring().to_csv(out / "structuring_suspects.csv",
                                               index=False)
        analytics.customer_risk_score().to_csv(out / "customer_risk_scores.csv",
                                                index=False)
        analytics.jurisdiction_exposure().to_csv(out / "jurisdiction_exposure.csv",
                                                  index=False)
        print(f"\n  Exported 6 files to data/")


if __name__ == "__main__":
    main()
