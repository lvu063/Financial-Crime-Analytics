-- aml_queries.sql
-- TD Financial Crime Analytics — AML Pattern Detection Queries
-- ─────────────────────────────────────────────────────────────────────────────
-- Production-grade SQL for financial crime analytics.
-- Compatible with: SQLite (demo) · PostgreSQL · BigQuery · Snowflake
--
-- Schema:
--   customers    (customer_id, segment, country_of_origin, is_pep, risk_rating)
--   transactions (transaction_id, customer_id, transaction_date, transaction_type,
--                 channel, amount_cad, counterparty_country, is_flagged, flag_reason)
--   alerts       (alert_id, transaction_id, customer_id, alert_date,
--                 flag_reason, amount_cad, status, assigned_to)
-- ─────────────────────────────────────────────────────────────────────────────


-- ── Query 1: Structuring Suspects ─────────────────────────────────────────────
-- Identifies customers with multiple cash transactions clustered just below
-- the $10,000 Currency Transaction Report (CTR) threshold — a key indicator
-- of structuring under PCMLTFA s.9.
--
-- Pattern demonstrated: GROUP BY + HAVING, JOIN, threshold range logic

SELECT
    t.customer_id,
    c.segment,
    c.risk_rating,
    COUNT(*)                    AS near_threshold_txns,
    SUM(t.amount_cad)           AS total_amount,
    ROUND(AVG(t.amount_cad), 2) AS avg_amount,
    MIN(t.transaction_date)     AS first_txn,
    MAX(t.transaction_date)     AS last_txn
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.amount_cad BETWEEN 9500 AND 9999.99
  AND t.transaction_type IN ('Cash Deposit', 'Cash Withdrawal')
GROUP BY t.customer_id, c.segment, c.risk_rating
HAVING COUNT(*) >= 2
ORDER BY near_threshold_txns DESC, total_amount DESC;


-- ── Query 2: High-Risk Jurisdiction Exposure ──────────────────────────────────
-- Customers sending or receiving funds from FINTRAC-designated high-risk
-- jurisdictions (Cayman Islands, Panama, Nigeria) above $5,000 CAD.
--
-- Pattern demonstrated: Multi-value IN, aggregation, conditional COUNT

SELECT
    t.customer_id,
    c.risk_rating,
    c.is_pep,
    t.counterparty_country,
    COUNT(*)                AS txn_count,
    ROUND(SUM(t.amount_cad), 2)  AS total_exposure_cad,
    ROUND(MAX(t.amount_cad), 2)  AS largest_single_txn,
    COUNT(CASE WHEN t.is_flagged = 1 THEN 1 END) AS already_flagged,
    COUNT(CASE WHEN t.is_flagged = 0 THEN 1 END) AS unflagged_exposure
FROM transactions t
JOIN customers c ON t.customer_id = c.customer_id
WHERE t.counterparty_country IN ('Cayman Islands', 'Panama', 'Nigeria')
  AND t.amount_cad > 5000
GROUP BY t.customer_id, c.risk_rating, c.is_pep, t.counterparty_country
ORDER BY total_exposure_cad DESC;


-- ── Query 3: Alert Queue Aging by Analyst ─────────────────────────────────────
-- Operational KPI: how alerts are distributed across analysts and statuses.
-- Window function calculates each analyst's workload as a % of their total queue.
-- Used by fraud operations managers to identify bottlenecks.
--
-- Pattern demonstrated: Window function (SUM OVER PARTITION BY), ratio calculation

SELECT
    assigned_to,
    status,
    COUNT(*)                                    AS alert_count,
    ROUND(AVG(amount_cad), 2)                   AS avg_amount,
    ROUND(SUM(amount_cad), 2)                   AS total_amount,
    ROUND(
        COUNT(*) * 100.0
        / SUM(COUNT(*)) OVER (PARTITION BY assigned_to),
        1
    )                                           AS pct_of_analyst_queue
FROM alerts
GROUP BY assigned_to, status
ORDER BY assigned_to, alert_count DESC;


-- ── Query 4: PEP Customer Exposure ────────────────────────────────────────────
-- Politically Exposed Persons (PEPs) require Enhanced Due Diligence under
-- FINTRAC guidance. This query surfaces PEP customers with significant
-- transaction activity for priority review.
--
-- Pattern demonstrated: Boolean filter, multi-column aggregation, JOIN

SELECT
    c.customer_id,
    c.segment,
    c.country_of_origin,
    c.risk_rating,
    COUNT(t.transaction_id)                     AS total_transactions,
    ROUND(SUM(t.amount_cad), 2)                 AS total_volume_cad,
    ROUND(AVG(t.amount_cad), 2)                 AS avg_transaction_cad,
    SUM(CASE WHEN t.is_flagged = 1 THEN 1 ELSE 0 END) AS flagged_count,
    ROUND(MAX(t.amount_cad), 2)                 AS largest_single_txn,
    COUNT(DISTINCT t.counterparty_country)      AS distinct_countries
FROM customers c
JOIN transactions t ON c.customer_id = t.customer_id
WHERE c.is_pep = 1
GROUP BY
    c.customer_id, c.segment, c.country_of_origin, c.risk_rating
ORDER BY total_volume_cad DESC;


-- ── Query 5: Monthly Transaction Trends with Flag Rate ────────────────────────
-- Month-over-month transaction volume and flag rate by transaction type.
-- Surfaces seasonal patterns and anomalous spikes for management reporting.
--
-- Pattern demonstrated: CTE, strftime date truncation, window function
-- (cumulative SUM OVER ORDER BY), flag rate calculation

WITH monthly AS (
    SELECT
        strftime('%Y-%m', transaction_date)     AS month,
        transaction_type,
        COUNT(*)                                AS txn_count,
        ROUND(SUM(amount_cad), 2)               AS total_amount,
        SUM(is_flagged)                         AS flagged_count,
        ROUND(
            SUM(amount_cad) / NULLIF(COUNT(*), 0),
            2
        )                                       AS avg_amount
    FROM transactions
    GROUP BY month, transaction_type
),
with_rates AS (
    SELECT
        *,
        ROUND(flagged_count * 100.0 / NULLIF(txn_count, 0), 2) AS flag_rate_pct
    FROM monthly
)
SELECT
    month,
    transaction_type,
    txn_count,
    total_amount,
    flagged_count,
    flag_rate_pct,
    -- Cumulative transaction count per type — tracks growth over time
    SUM(txn_count) OVER (
        PARTITION BY transaction_type
        ORDER BY month
        ROWS BETWEEN UNBOUNDED PRECEDING AND CURRENT ROW
    )                                           AS cumulative_count,
    -- 3-month rolling average flag rate — smooths noise
    ROUND(
        AVG(flag_rate_pct) OVER (
            PARTITION BY transaction_type
            ORDER BY month
            ROWS BETWEEN 2 PRECEDING AND CURRENT ROW
        ),
        2
    )                                           AS rolling_3m_flag_rate
FROM with_rates
ORDER BY month, total_amount DESC;
