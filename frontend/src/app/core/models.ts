// Kiểu dữ liệu theo docs/04-api-contract.md

export type Segment = 'S1' | 'S2' | 'S3' | 'S4' | 'S5' | 'S6';
export type Level = 'High' | 'Mid' | 'Low';

export interface Thresholds {
  tau: number;
  clv_p33: number;
  clv_p67: number;
}

export interface SegmentSummary {
  segment: Segment;
  name: string;
  risk: 'High' | 'Low';
  tier: Level;
  count: number;
  share: number;
  value_at_risk: number;
}

export interface DashboardSummary {
  total_customers: number;
  high_risk_rate: number;
  total_clv_expected: number;
  total_value_at_risk: number;
  model: { version: string; scored_at: string | null };
  thresholds: Thresholds;
  segments: SegmentSummary[];
  p_churn_histogram: { bin: string; count: number }[];
  by_country: { country: string; count: number; value_at_risk: number }[];
}

export interface FeatureImportance {
  feature: string;
  label: string;
  mean_abs_shap: number;
}

export interface ModelInfo {
  version: string;
  algorithm: string;
  trained_at: string;
  metrics: { roc_auc: number; recall: number; precision: number };
  plain_text: string[];
  thresholds: Thresholds;
  global_importance: FeatureImportance[];
  limitations: string[];
}

export interface Page<T> {
  count: number;
  next: string | null;
  previous: string | null;
  results: T[];
}

export interface CustomerRow {
  customer_id: string;
  country: string;
  city: string;
  p_churn: number;
  risk_label: 'High' | 'Low';
  clv_pred: number;
  clv_potential: number;
  clv_tier: Level;
  value_at_risk: number;
  segment: Segment;
}

export interface Reason {
  feature: string;
  label: string;
  value: number | string | null;
  avg: number | null;
  shap: number;
}

export interface JourneyStep {
  day: number;
  channel: string;
  action: string;
  offer: string | null;
}

export interface CustomerDetail {
  customer_id: string;
  attributes: Record<'profile' | 'behavior' | 'purchase' | 'engagement', Record<string, number | string | null>>;
  prediction: Omit<CustomerRow, 'customer_id' | 'country' | 'city'> & {
    channel: string;
    top_reasons: Reason[];
    model_version: string;
    scored_at: string;
  };
  journey: JourneyInfo | null;
}

export interface JourneyInfo {
  journey_id: string;
  name: string;
  goal: string;
  steps: JourneyStep[];
  kpi: string;
  max_spend_pct: number;
}

export interface Journey extends JourneyInfo {
  segment: Segment;
  risk: 'High' | 'Low';
  tier: Level;
  count: number;
  value_at_risk: number;
  research: string[];
}

export interface JourneysResponse {
  thresholds: Thresholds;
  journeys: Journey[];
}

export interface PredictResult {
  p_churn: number;
  risk_label: 'High' | 'Low';
  clv_pred: number;
  clv_potential: number;
  clv_tier: Level;
  value_at_risk: number;
  segment: Segment;
  channel: string;
  journey: JourneyInfo | null;
  top_reasons: Reason[];
  imputed_fields: string[];
  model_version: string;
  saved: boolean;
  customer_id: string | null;
}
