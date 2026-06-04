// components/transaction-monitor/transaction-monitor.component.ts
// Demonstrates: Angular component lifecycle, OnPush change detection,
// reactive forms, template-driven filtering, async pipe usage

import {
  Component, OnInit, OnDestroy, ChangeDetectionStrategy
} from '@angular/core';
import { FormBuilder, FormGroup }    from '@angular/forms';
import { Observable, Subject }       from 'rxjs';
import { takeUntil, debounceTime }   from 'rxjs/operators';

import { FraudAnalyticsService }     from '../../services/fraud-analytics.service';
import { Transaction, FilterState }  from '../../models/transaction.model';

@Component({
  selector:         'app-transaction-monitor',
  templateUrl:      './transaction-monitor.component.html',
  styleUrls:        ['./transaction-monitor.component.scss'],
  changeDetection:  ChangeDetectionStrategy.OnPush,   // performance: only re-render on input changes
})
export class TransactionMonitorComponent implements OnInit, OnDestroy {

  transactions$!: Observable<Transaction[]>;
  loading$!:      Observable<boolean>;

  filterForm!: FormGroup;
  private destroy$ = new Subject<void>();

  // Pagination
  pageSize    = 25;
  currentPage = 1;

  // Table columns
  displayedColumns = [
    'transaction_id', 'customer_id', 'transaction_date',
    'transaction_type', 'amount_cad', 'counterparty_country',
    'is_flagged', 'flag_reason',
  ];

  transactionTypes = [
    'All', 'Wire Transfer', 'Cash Deposit', 'Cash Withdrawal',
    'Interac e-Transfer', 'ACH', 'Cheque Deposit', 'POS',
  ];

  constructor(
    private fb:      FormBuilder,
    private service: FraudAnalyticsService,
  ) {}

  ngOnInit(): void {
    this.transactions$ = this.service.filteredTransactions$;
    this.loading$      = this.service.loading$;

    this.filterForm = this.fb.group({
      dateFrom:        [null],
      dateTo:          [null],
      flaggedOnly:     [false],
      minAmount:       [null],
      transactionType: ['All'],
    });

    // Reactive filter updates — debounced to avoid excessive re-computation
    this.filterForm.valueChanges.pipe(
      debounceTime(300),
      takeUntil(this.destroy$),
    ).subscribe((values: Partial<FilterState>) => {
      this.service.updateFilters(values);
      this.currentPage = 1;   // reset pagination on filter change
    });
  }

  ngOnDestroy(): void {
    this.destroy$.next();
    this.destroy$.complete();
  }

  resetFilters(): void {
    this.filterForm.reset({
      dateFrom: null, dateTo: null,
      flaggedOnly: false, minAmount: null, transactionType: 'All',
    });
    this.service.resetFilters();
  }

  // ── Helpers for template ──────────────────────────────────────────

  flagColour(reason: string | null): string {
    switch (reason) {
      case 'STRUCTURING':           return 'flag-red';
      case 'HIGH_RISK_JURISDICTION': return 'flag-orange';
      case 'ROUND_AMOUNT_CASH':     return 'flag-yellow';
      default:                      return '';
    }
  }

  formatAmount(amount: number): string {
    return new Intl.NumberFormat('en-CA', {
      style: 'currency', currency: 'CAD'
    }).format(amount);
  }

  trackById(_: number, txn: Transaction): string {
    return txn.transaction_id;
  }
}
