"""
mlops_monitor.py
----------------
TD Financial Crime Analytics — MLOps Model Monitoring

Implements model drift detection and performance monitoring for the
AML risk scoring pipeline — the MLOps practice the Platform Developer
and Data Services Developer roles require.

Monitors:
  - Data drift: distribution shifts in transaction amounts and patterns
  - Model drift: changes in risk score distribution over time
  - Alert rate drift: flag rate changes that may indicate false positives
  - Data quality: automated checks run on every new batch

In production this would run on a schedule (cron / Airflow) and
alert the team via Slack or PagerDuty when thresholds are breached.

Usage:
    python python/mlops_monitor.py                  # full monitoring run
    python python/mlops_monitor.py --baseline       # set new baseline
    python python/mlops_monitor.py --report         # print drift report
"""

from __future__ import annotations
import argparse
import json
import os
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Optional

import numpy as np
import pandas as pd

BASELINE_PATH = Path("data/baseline_stats.json")
DRIFT_THRESHOLD_PSI = 0.2     # Population Stability Index threshold
DRIFT_THRESHOLD_PCT = 0.15    # % change threshold for simpler metrics


# ── Data structures ────────────────────────────────────────────────────────────

@dataclass
class DriftAlert:
    metric:    str
    severity:  str   # INFO / WARNING / CRITICAL
    baseline:  float
    current:   float
    pct_change: float
    message:   str


@dataclass
class MonitoringReport:
    timestamp:     str
    total_records: int
    alerts:        list[DriftAlert] = field(default_factory=list)
    data_quality:  dict = field(default_factory=dict)
    drift_summary: dict = field(default_factory=dict)
    healthy:       bool = True


# ── Population Stability Index ─────────────────────────────────────────────────

def psi(baseline: np.ndarray, current: np.ndarray, buckets: int = 10) -> float:
    """
    Population Stability Index — standard MLOps metric for detecting
    distribution shift between baseline and current data.

    PSI < 0.1  → No significant change
    PSI < 0.2  → Moderate change, investigate
    PSI >= 0.2 → Significant change, likely drift
    """
    breakpoints = np.percentile(baseline, np.linspace(0, 100, buckets + 1))
    breakpoints[0]  = -np.inf
    breakpoints[-1] = np.inf

    baseline_pcts = np.histogram(baseline, breakpoints)[0] / len(baseline)
    current_pcts  = np.histogram(current,  breakpoints)[0] / len(current)

    # Avoid division by zero
    baseline_pcts = np.where(baseline_pcts == 0, 0.0001, baseline_pcts)
    current_pcts  = np.where(current_pcts  == 0, 0.0001, current_pcts)

    return float(np.sum((current_pcts - baseline_pcts) * np.log(current_pcts / baseline_pcts)))


# ── Baseline stats ─────────────────────────────────────────────────────────────

def compute_baseline(df: pd.DataFrame) -> dict:
    """Compute baseline statistics from a reference dataset."""
    return {
        "computed_at":        datetime.now().isoformat(),
        "n_records":          len(df),
        "amount_mean":        float(df["amount_cad"].mean()),
        "amount_std":         float(df["amount_cad"].std()),
        "amount_p50":         float(df["amount_cad"].quantile(0.50)),
        "amount_p95":         float(df["amount_cad"].quantile(0.95)),
        "amount_p99":         float(df["amount_cad"].quantile(0.99)),
        "flag_rate":          float(df["is_flagged"].mean()),
        "structuring_rate":   float((df["flag_reason"] == "STRUCTURING").mean()),
        "hrc_rate":           float((df["flag_reason"] == "HIGH_RISK_JURISDICTION").mean()),
        "amount_distribution": df["amount_cad"].tolist()[:500],  # sample for PSI
    }


def save_baseline(stats: dict):
    BASELINE_PATH.parent.mkdir(exist_ok=True)
    with open(BASELINE_PATH, "w") as f:
        json.dump(stats, f, indent=2)
    print(f"  ✓ Baseline saved to {BASELINE_PATH}")


def load_baseline() -> Optional[dict]:
    if not BASELINE_PATH.exists():
        return None
    with open(BASELINE_PATH) as f:
        return json.load(f)


# ── Drift detection ────────────────────────────────────────────────────────────

def detect_drift(baseline: dict, current_df: pd.DataFrame) -> list[DriftAlert]:
    """Compare current batch statistics against baseline and flag drift."""
    alerts = []

    current_stats = {
        "amount_mean":      float(current_df["amount_cad"].mean()),
        "flag_rate":        float(current_df["is_flagged"].mean()),
        "structuring_rate": float((current_df["flag_reason"] == "STRUCTURING").mean()),
        "hrc_rate":         float((current_df["flag_reason"] == "HIGH_RISK_JURISDICTION").mean()),
    }

    # PSI on transaction amount distribution
    baseline_amounts = np.array(baseline["amount_distribution"])
    current_amounts  = current_df["amount_cad"].values
    amount_psi = psi(baseline_amounts, current_amounts)

    if amount_psi >= DRIFT_THRESHOLD_PSI:
        alerts.append(DriftAlert(
            metric="transaction_amount_distribution",
            severity="CRITICAL" if amount_psi > 0.3 else "WARNING",
            baseline=0.0,
            current=round(amount_psi, 4),
            pct_change=0.0,
            message=f"Transaction amount distribution drift detected (PSI={amount_psi:.3f}). "
                    f"Threshold: {DRIFT_THRESHOLD_PSI}. Review for data pipeline issues or "
                    f"genuine behavioural change in customer population.",
        ))

    # Simple percentage change checks
    checks = [
        ("flag_rate", "Alert flag rate", 0.05),
        ("structuring_rate", "Structuring detection rate", 0.30),
        ("amount_mean", "Mean transaction amount", 0.20),
    ]

    for key, label, threshold in checks:
        base_val = baseline.get(key, 0)
        curr_val = current_stats.get(key, 0)
        if base_val == 0:
            continue
        pct = abs(curr_val - base_val) / base_val

        if pct >= threshold:
            severity = "CRITICAL" if pct > threshold * 2 else "WARNING"
            alerts.append(DriftAlert(
                metric=key,
                severity=severity,
                baseline=round(base_val, 4),
                current=round(curr_val, 4),
                pct_change=round(pct * 100, 1),
                message=f"{label} changed by {pct*100:.1f}% (threshold: {threshold*100:.0f}%). "
                        f"Baseline: {base_val:.4f} → Current: {curr_val:.4f}."
            ))

    return alerts


# ── Data quality checks ────────────────────────────────────────────────────────

def run_data_quality(df: pd.DataFrame) -> dict:
    """
    Automated data quality checks on every incoming batch.
    These run before any model scoring to prevent garbage-in garbage-out.
    """
    checks = {}

    checks["no_null_amounts"] = {
        "passed": df["amount_cad"].notna().all(),
        "failed_count": int(df["amount_cad"].isna().sum()),
    }
    checks["positive_amounts"] = {
        "passed": (df["amount_cad"] > 0).all(),
        "failed_count": int((df["amount_cad"] <= 0).sum()),
    }
    checks["valid_dates"] = {
        "passed": pd.to_datetime(df["transaction_date"], errors="coerce").notna().all(),
        "failed_count": int(pd.to_datetime(df["transaction_date"], errors="coerce").isna().sum()),
    }
    checks["no_duplicate_txn_ids"] = {
        "passed": df["transaction_id"].nunique() == len(df),
        "failed_count": int(len(df) - df["transaction_id"].nunique()),
    }
    checks["valid_transaction_types"] = {
        "passed": df["transaction_type"].notna().all(),
        "failed_count": int(df["transaction_type"].isna().sum()),
    }

    all_passed = all(c["passed"] for c in checks.values())
    checks["overall_passed"] = all_passed
    checks["quality_score"]  = round(
        sum(1 for c in checks.values() if isinstance(c, dict) and c.get("passed", False))
        / (len(checks) - 2) * 100, 1
    )

    return checks


# ── Main monitoring run ────────────────────────────────────────────────────────

def run_monitoring(df: pd.DataFrame, set_baseline: bool = False) -> MonitoringReport:
    report = MonitoringReport(
        timestamp=datetime.now().isoformat(),
        total_records=len(df),
    )

    # Data quality — always runs
    report.data_quality = run_data_quality(df)
    if not report.data_quality["overall_passed"]:
        report.healthy = False

    if set_baseline:
        stats = compute_baseline(df)
        save_baseline(stats)
        print(f"  ✓ Baseline set from {len(df):,} records")
        return report

    # Load baseline
    baseline = load_baseline()
    if baseline is None:
        print("  ⚠  No baseline found. Run with --baseline to set one.")
        return report

    # Drift detection
    report.alerts = detect_drift(baseline, df)
    report.healthy = report.healthy and not any(
        a.severity == "CRITICAL" for a in report.alerts
    )

    report.drift_summary = {
        "critical_alerts": sum(1 for a in report.alerts if a.severity == "CRITICAL"),
        "warning_alerts":  sum(1 for a in report.alerts if a.severity == "WARNING"),
        "baseline_date":   baseline.get("computed_at", "unknown"),
        "baseline_records": baseline.get("n_records", 0),
    }

    return report


def print_report(report: MonitoringReport):
    status = "✅ HEALTHY" if report.healthy else "❌ NEEDS ATTENTION"

    print("\n" + "═" * 65)
    print("  AML PIPELINE — MLOps MONITORING REPORT")
    print(f"  {datetime.now().strftime('%Y-%m-%d %H:%M')}  |  {status}")
    print("═" * 65)

    print(f"\n  Records processed: {report.total_records:,}")

    print(f"\n  DATA QUALITY")
    dq = report.data_quality
    print(f"  Quality score: {dq.get('quality_score', 0)}%")
    for check, result in dq.items():
        if isinstance(result, dict):
            icon = "✓" if result["passed"] else "✗"
            print(f"  {icon} {check}: {'passed' if result['passed'] else f\"FAILED ({result['failed_count']} records)\"}")

    if report.alerts:
        print(f"\n  DRIFT ALERTS ({len(report.alerts)} total)")
        for alert in report.alerts:
            icon = "🔴" if alert.severity == "CRITICAL" else "🟡"
            print(f"\n  {icon} [{alert.severity}] {alert.metric}")
            print(f"     {alert.message}")
    else:
        print("\n  ✓ No drift detected — model performing within baseline thresholds")

    print("\n" + "═" * 65)


def main():
    parser = argparse.ArgumentParser(description="AML Pipeline MLOps Monitor")
    parser.add_argument("--baseline", action="store_true", help="Set current data as baseline")
    parser.add_argument("--report",   action="store_true", help="Print monitoring report")
    args = parser.parse_args()

    data_path = Path("data/transactions.csv")
    if not data_path.exists():
        print("  No data found. Run: python python/fraud_analytics.py --export")
        return

    df = pd.read_csv(data_path)
    print(f"  Loaded {len(df):,} transactions from {data_path}")

    report = run_monitoring(df, set_baseline=args.baseline)
    print_report(report)


if __name__ == "__main__":
    main()
