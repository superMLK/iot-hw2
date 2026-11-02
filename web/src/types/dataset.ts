// 對應管線輸出的 web/public/data/<id>.json（原設計第 6 節 + design 決策 9 的延伸欄位）

export type DatasetId = "bike" | "house";

export interface Meta {
  id: DatasetId;
  name: string;
  short_name: string;
  kaggle_url: string;
  origin_url: string | null;
  license: string;
  license_url: string | null;
  citation: string | null;
  file: string;
  target: string;
  model_target: string;
  log_target: boolean;
  split: "time" | "random";
  random_state: number;
  n_train: number;
  n_test: number;
  sampled: boolean;
  n_points_total: number;
  n_points_shown: number;
  max_points: number | null;
  target_mean_train: number;
  target_mean_test: number;
  site_url: string;
  feature_labels: Record<string, string>;
  generated_at: string;
}

export interface PrepStep {
  name: string;
  reason: string;
  affected: string;
  highlight?: boolean;
}

export interface Success {
  metric: string;
  value: string;
  threshold: number;
  actual: number;
  met: boolean;
}

export interface CrispDm {
  business_understanding: { markdown: string };
  data_understanding: { markdown: string; stats_ref: string };
  data_preparation: {
    markdown: string;
    steps: PrepStep[];
    before: { rows: number; cols: number };
    after: { rows: number; cols: number; features: number };
    n_removed_rows: number;
  };
  modeling: { markdown: string };
  evaluation: { markdown: string; conclusion: string; success: Success };
  deployment: { markdown: string };
}

export interface ColumnInfo {
  name: string;
  dtype: string;
  kind: "numeric" | "categorical";
  missing: number;
  unique: number;
  role: "target" | "id" | "date" | "feature";
}

export interface Describe {
  count: number;
  mean: number;
  std: number;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
}

export interface DataUnderstanding {
  n_rows: number;
  n_cols: number;
  n_features: number;
  feature_rule: string;
  n_missing_total: number;
  n_duplicates: number;
  columns: ColumnInfo[];
  describe: Record<string, Describe>;
  correlation: { labels: string[]; matrix: (number | null)[][] };
  target_distribution: { bins: number[]; counts: number[] };
  top_corr_features: { feature: string; r: number; abs_r: number }[];
  preview: Record<string, string | number | null>[];
}

export interface FeatureSelection {
  correlation: { feature: string; abs_r: number }[];
  correlation_rule: { min_abs_r: number; high_corr_pair: number };
  high_corr_pairs: { a: string; b: string; r: number; dropped?: string }[];
  vif_threshold: number;
  vif_initial: { feature: string; vif: number | null }[];
  vif_rounds: { round: number; removed: string; vif: number | null; vif_is_inf: boolean; remaining: string[] }[];
  vif_removed: string[];
  vif_final: { feature: string; vif: number }[];
  stepwise_start_aic: number;
  stepwise_steps: { step: number; action: "add" | "remove"; feature: string; aic: number }[];
  comparison: { feature: string; corr_kept: boolean; vif_kept: boolean; stepwise_kept: boolean }[];
  final_features: string[];
  n_candidates: number;
  n_corr_kept: number;
  n_after_vif: number;
  n_final: number;
}

export interface Coefficient {
  name: string;
  coef: number;
  std_err: number;
  t: number;
  p: number;
  ci_low: number;
  ci_high: number;
}

export interface Metrics {
  r2: number;
  adj_r2: number;
  rmse: number;
  mae: number;
  pi_coverage: number;
}

export interface PredPoint {
  x: number | string;
  actual: number;
  pred: number;
  ci_low: number | null;
  ci_high: number | null;
  pi_low: number;
  pi_high: number;
}

export interface BandPoint {
  x: number;
  pred: number;
  ci_low: number;
  ci_high: number;
  pi_low: number;
  pi_high: number;
}

export interface Prediction {
  x_kind: "index" | "date" | "feature";
  x_label: string;
  y_label: string;
  n_total: number;
  points: PredPoint[];
  band?: BandPoint[];
  train_points?: { x: string; actual: number }[];
  interval_note?: string;
}

export interface Model {
  id: "slr" | "mlr_all" | "mlr_selected" | "ar";
  label: string;
  type: "slr" | "mlr" | "ar";
  is_best: boolean;
  features: string[];
  n_train: number;
  n_test: number;
  aic: number;
  ar_order?: number;
  resid_std?: number;
  train_r2?: number;
  train_adj_r2?: number;
  coefficients: Coefficient[];
  metrics: Metrics;
  metrics_note?: string;
  cv: { scores_r2: number[]; mean: number; std: number; method: string };
  prediction: Prediction;
  residuals: {
    fitted: number[];
    resid: number[];
    qq_theoretical: number[];
    qq_sample: number[];
    n_total: number;
    source: string;
    scale: string;
  };
}

export interface DatasetResult {
  meta: Meta;
  crisp_dm: CrispDm;
  data_understanding: DataUnderstanding;
  feature_selection: FeatureSelection;
  models: Model[];
}
