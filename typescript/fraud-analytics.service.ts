// services/fraud-analytics.service.ts
// Angular service demonstrating: dependency injection, RxJS observables,
// HttpClient usage, data transformation, and reactive state management

import { Injectable }                   from '@angular/core';
import { HttpClient }                   from '@angular/common/http';
import { BehaviorSubject, Observable, combineLatest } from 'rxjs';
import { map, shareReplay, distinctUntilChanged }      from 'rxjs/operators';

import {
  Transaction, Customer, Alert, RiskScore,
  AlertKPIs, FilterState, RiskTier, FlagReason
} from '../models/transaction.model';

@Injectable({ providedIn: 'root' })
export class FraudAnalyticsService {

  // ── Reactive state ────────────────────────────────────────────────
  private readonly _filters$ = new BehaviorSubject<FilterState>({
    dateFrom:        null,
    dateTo:          null,
    flaggedOnly:     false,
    minAmount:       null,
    riskTier:        'All',
    transactionType: 'All',
  });

  private readonly _loading$ = new BehaviorSubject<boolean>(false);

  readonly filters$  = this._filters$.asObservable();
  readonly loading$  = this._loading$.asObservable();

  // ── Data streams (would be HttpClient calls in production) ────────
  private readonly transactions$: Observable<Transaction[]>;
  private readonly customers$:    Observable<Customer[]>;
  private readonly alerts$:       Observable<Alert[]>;

  constructor(private http: HttpClient) {
    // In production: this.http.get<Transaction[]>('/api/transactions')
    // For demo: load from assets
    this.transactions$ = this.http
      .get<Transaction[]>('assets/data/transactions.json')
      .pipe(shareReplay(1));

    this.customers$ = this.http
      .get<Customer[]>('assets/data/customers.json')
      .pipe(shareReplay(1));

    this.alerts$ = this.http
      .get<Alert[]>('assets/data/alerts.json')
      .pipe(shareReplay(1));
  }

  // ── Filtered transactions (reactive to filter state) ─────────────
  readonly filteredTransactions$: Observable<Transaction[]> = combineLatest([
    this.transactions$,
    this._filters$.pipe(distinctUntilChanged()),
  ]).pipe(
    map(([transactions, filters]) => this.applyFilters(transactions, filters)),
    shareReplay(1),
  );

  private applyFilters(
    txns: Transaction[], filters: FilterState
  ): Transaction[] {
    return txns.filter(t => {
      if (filters.flaggedOnly && !t.is_flagged) return false;
      if (filters.minAmount !== null && t.amount_cad < filters.minAmount)
        return false;
      if (filters.transactionType !== 'All' &&
          t.transaction_type !== filters.transactionType) return false;
      if (filters.dateFrom && t.transaction_date < filters.dateFrom)
        return false;
      if (filters.dateTo && t.transaction_date > filters.dateTo)
        return false;
      return true;
    });
  }

  // ── Alert KPIs ────────────────────────────────────────────────────
  readonly alertKPIs$: Observable<AlertKPIs> = this.alerts$.pipe(
    map(alerts => {
      const total = alerts.length;
      const byStatus = alerts.reduce((acc, a) => {
        acc[a.status] = (acc[a.status] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      const byReason = alerts.reduce((acc, a) => {
        acc[a.flag_reason] = (acc[a.flag_reason] || 0) + 1;
        return acc;
      }, {} as Record<string, number>);

      const escalated = byStatus['Escalated to FINTRAC'] || 0;
      const avgAmount = alerts.reduce((s, a) => s + a.amount_cad, 0) / total;

      return {
        total_alerts:          total,
        escalation_rate_pct:   Math.round(escalated / total * 1000) / 10,
        avg_alert_amount_cad:  Math.round(avgAmount * 100) / 100,
        high_value_alerts:     alerts.filter(a => a.amount_cad > 10000).length,
        by_status:             byStatus as any,
        by_flag_reason:        byReason as any,
      };
    }),
    shareReplay(1),
  );

  // ── Risk scores computed client-side ─────────────────────────────
  readonly riskScores$: Observable<RiskScore[]> = combineLatest([
    this.customers$,
    this.transactions$,
    this.alerts$,
  ]).pipe(
    map(([customers, transactions, alerts]) =>
      this.computeRiskScores(customers, transactions, alerts)
    ),
    shareReplay(1),
  );

  private computeRiskScores(
    customers: Customer[],
    transactions: Transaction[],
    alerts: Alert[],
  ): RiskScore[] {
    const riskMap: Record<string, number> = { Low: 10, Medium: 40, High: 70 };

    return customers.map(c => {
      const cTxns     = transactions.filter(t => t.customer_id === c.customer_id);
      const cAlerts   = alerts.filter(a => a.customer_id === c.customer_id);
      const flagged   = cTxns.filter(t => t.is_flagged).length;
      const escalated = cAlerts.filter(
        a => a.status === 'Escalated to FINTRAC').length;
      const hrcTxns   = cTxns.filter(t =>
        ['Cayman Islands', 'Panama', 'Nigeria'].includes(t.counterparty_country)
      ).length;

      const scoreBase         = riskMap[c.risk_rating] || 10;
      const scorePep          = c.is_pep ? 20 : 0;
      const scoreBehaviour    = Math.min(
        (flagged / Math.max(cTxns.length, 1)) * 30, 30);
      const scoreJurisdiction = Math.min(hrcTxns * 3, 15);
      const scoreEscalations  = Math.min(escalated * 10, 20);

      const total = Math.min(
        scoreBase + scorePep + scoreBehaviour +
        scoreJurisdiction + scoreEscalations, 100
      );

      const tier: RiskTier =
        total >= 75 ? 'Critical' :
        total >= 50 ? 'High'     :
        total >= 25 ? 'Medium'   : 'Low';

      return {
        customer_id:         c.customer_id,
        composite_risk_score: Math.round(total * 10) / 10,
        risk_tier:           tier,
        flagged_txns:        flagged,
        escalations:         escalated,
        score_breakdown: {
          base:         scoreBase,
          pep:          scorePep,
          behaviour:    Math.round(scoreBehaviour * 10) / 10,
          jurisdiction: scoreJurisdiction,
          escalations:  scoreEscalations,
        },
      };
    }).sort((a, b) => b.composite_risk_score - a.composite_risk_score);
  }

  // ── Filter updates ────────────────────────────────────────────────
  updateFilters(partial: Partial<FilterState>): void {
    this._filters$.next({ ...this._filters$.getValue(), ...partial });
  }

  resetFilters(): void {
    this._filters$.next({
      dateFrom: null, dateTo: null, flaggedOnly: false,
      minAmount: null, riskTier: 'All', transactionType: 'All',
    });
  }

  // ── Utility: get customer by ID ───────────────────────────────────
  getCustomer(customerId: string): Observable<Customer | undefined> {
    return this.customers$.pipe(
      map(cs => cs.find(c => c.customer_id === customerId))
    );
  }
}
