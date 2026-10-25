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
