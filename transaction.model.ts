// models/transaction.model.ts
// Core TypeScript interfaces for the TD Fraud Analytics Angular app

export interface Transaction {
  transaction_id: string;
  customer_id: string;
  transaction_date: string;
  transaction_type: TransactionType;
  channel: string;
  amount_cad: number;
  counterparty_country: string;
  is_flagged: boolean;
  flag_reason: FlagReason | null;
}

export interface Customer {
  customer_id: string;
  segment: CustomerSegment;
  country_of_origin: string;
  account_opened: string;
  is_pep: boolean;
  risk_rating: RiskRating;
  monthly_income_est: number;
}

export interface Alert {
  alert_id: string;
  transaction_id: string;
  customer_id: string;
  alert_date: string;
  flag_reason: FlagReason;
  amount_cad: number;
  status: AlertStatus;
  assigned_to: string;
}

export interface RiskScore {
  customer_id: string;
  composite_risk_score: number;
  risk_tier: RiskTier;
  flagged_txns: number;
  escalations: number;
  score_breakdown: {
    base: number;
    pep: number;
    behaviour: number;
    jurisdiction: number;
    escalations: number;
  };
}

export interface AlertKPIs {
  total_alerts: number;
  escalation_rate_pct: number;
  avg_alert_amount_cad: number;
  high_value_alerts: number;
  by_status: Record<AlertStatus, number>;
  by_flag_reason: Record<FlagReason, number>;
}

export interface FilterState {
  dateFrom:       string | null;
  dateTo:         string | null;
  flaggedOnly:    boolean;
  minAmount:      number | null;
  riskTier:       RiskTier | 'All';
  transactionType: TransactionType | 'All';
}

// Enums
export type TransactionType =
  | 'Wire Transfer'
  | 'Cash Deposit'
  | 'Cash Withdrawal'
  | 'Interac e-Transfer'
  | 'ACH'
  | 'Cheque Deposit'
  | 'POS';

export type FlagReason =
  | 'STRUCTURING'
  | 'ROUND_AMOUNT_CASH'
  | 'HIGH_RISK_JURISDICTION';

export type CustomerSegment = 'Retail' | 'Small Business' | 'Commercial' | 'Wealth';
export type RiskRating      = 'Low' | 'Medium' | 'High';
export type RiskTier        = 'Low' | 'Medium' | 'High' | 'Critical';
export type AlertStatus     =
  | 'Under Review'
  | 'Closed - No Action'
  | 'Escalated to FINTRAC';
