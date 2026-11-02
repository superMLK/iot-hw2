import { readFileSync } from "node:fs";
import { describe, expect, test } from "vitest";
import type { DatasetResult } from "./dataset";

// 管線輸出必須先產生（CI 會先執行 python analysis/run_pipeline.py）
function load(id: string): DatasetResult {
  return JSON.parse(readFileSync(new URL(`../../public/data/${id}.json`, import.meta.url), "utf-8"));
}

const META_KEYS = ["id", "name", "kaggle_url", "license", "file", "target", "model_target", "n_train", "n_test", "sampled", "site_url"];
const STEPS = ["business_understanding", "data_understanding", "data_preparation", "modeling", "evaluation", "deployment"];

describe.each(["bike", "house"])("%s.json 符合前端型別", (id) => {
  const d = load(id);

  test("meta 與 CRISP-DM 區塊", () => {
    for (const k of META_KEYS) expect(d.meta).toHaveProperty(k);
    expect(d.meta.id).toBe(id);
    for (const s of STEPS) expect(typeof (d.crisp_dm as unknown as Record<string, { markdown: string }>)[s].markdown).toBe("string");
    expect(d.crisp_dm.data_preparation.steps.length).toBeGreaterThan(0);
    expect(d.crisp_dm.evaluation.success).toHaveProperty("threshold");
  });

  test("資料理解與特徵選擇", () => {
    const du = d.data_understanding;
    expect(du.n_features).toBeGreaterThan(13);
    expect(du.n_features).toBeLessThan(40);
    expect(du.correlation.matrix.length).toBe(du.correlation.labels.length);
    const fs = d.feature_selection;
    for (const k of ["correlation", "high_corr_pairs", "vif_rounds", "stepwise_steps", "comparison", "final_features"]) expect(fs).toHaveProperty(k);
  });

  test("模型結構", () => {
    for (const m of d.models) {
      expect(["slr", "mlr", "ar"]).toContain(m.type);
      for (const k of ["r2", "adj_r2", "rmse", "mae", "pi_coverage"]) expect(m.metrics).toHaveProperty(k);
      expect(m.cv.scores_r2).toHaveLength(5);
      const p = m.prediction.points[0];
      for (const k of ["x", "actual", "pred", "ci_low", "ci_high", "pi_low", "pi_high"]) expect(p).toHaveProperty(k);
      if (m.type === "slr") expect(m.prediction.band?.length).toBeGreaterThan(0);
      if (m.type === "ar") expect(m.prediction.train_points?.length).toBeGreaterThan(0);
    }
    expect(d.models.filter((m) => m.is_best)).toHaveLength(1);
  });
});
