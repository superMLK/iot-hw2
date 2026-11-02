import { useState } from "react";
import Markdown from "../components/Markdown";
import { ActualVsPredicted, PredictionChart, ResidualCharts } from "../components/PredictionChart";
import Table from "../components/Table";
import { fmtNum, fmtPct } from "../lib/format";
import type { DatasetResult, Model } from "../types/dataset";

export default function EvaluationStep({ data }: { data: DatasetResult }) {
  const { meta, models } = data;
  const [modelId, setModelId] = useState<Model["id"]>(models.find((m) => m.is_best)!.id);
  const model = models.find((m) => m.id === modelId)!;
  const money = meta.log_target ? "（美元）" : "";
  const note = models[0].metrics_note;

  return (
    <>
      <section className="card">
        <h2>⑤ 評估（Evaluation）</h2>
        <h3>模型比較（測試集）</h3>
        {note && <p className="note">{note}</p>}
        <Table
          caption="模型比較表"
          rows={models}
          rowClass={(m) => (m.is_best ? "best" : undefined)}
          columns={[
            {
              key: "label",
              header: "模型",
              render: (m) => (
                <>
                  {m.label}
                  {m.is_best && <span className="badge">最佳</span>}
                </>
              ),
            },
            { key: "r2", header: "R²", num: true, render: (m) => fmtNum(m.metrics.r2) },
            { key: "adj", header: "Adjusted R²", num: true, render: (m) => fmtNum(m.metrics.adj_r2) },
            { key: "rmse", header: `RMSE${money}`, num: true, render: (m) => fmtNum(m.metrics.rmse, 0) },
            { key: "mae", header: `MAE${money}`, num: true, render: (m) => fmtNum(m.metrics.mae, 0) },
            { key: "cov", header: "95% 預測區間覆蓋率", num: true, render: (m) => fmtPct(m.metrics.pi_coverage) },
            { key: "cv", header: "5 折 CV R²（平均 ± 標準差）", num: true, render: (m) => `${fmtNum(m.cv.mean)} ± ${fmtNum(m.cv.std)}` },
          ]}
        />
        <p className="note">
          最佳模型以測試集 R² 判定。預測區間覆蓋率是測試集實際值落在 95% 預測區間內的比例，理想值接近 95%。
          測試集共 {meta.n_test} 筆。
        </p>
      </section>

      <section className="card">
        <h3>預測圖</h3>
        <div className="toggle-group" role="group" aria-label="選擇要顯示的模型">
          {models.map((m) => (
            <button key={m.id} type="button" aria-pressed={m.id === modelId} onClick={() => setModelId(m.id)}>
              {m.label}
            </button>
          ))}
        </div>
        <PredictionChart model={model} meta={meta} />
        <p className="chart-caption">
          <span className="legend-swatch" style={{ opacity: 0.35 }} />
          95% 信賴區間（較深）：平均預測值的不確定性。
          <span className="legend-swatch" style={{ opacity: 0.15, marginLeft: 12 }} />
          95% 預測區間（較淺）：單筆新觀測值可能落在的範圍。
          {model.type === "ar" && <> AR 模型只提供預測區間（一步預測 ± 1.96 × 訓練殘差標準差），沒有信賴區間。</>}
          {meta.log_target && <> 區間在 log 尺度計算後轉回美元，因此上緣離預測值較遠、下緣較近，這是對數轉換的正常現象。</>}
          {meta.sampled && model.prediction.points.length < model.prediction.n_total && (
            <> 測試集共 {model.prediction.n_total} 筆，依預測值排序後均勻抽樣顯示 {model.prediction.points.length} 筆；指標以完整測試集計算。</>
          )}
        </p>
        {model.type === "mlr" && <ActualVsPredicted model={model} meta={meta} />}
      </section>

      <section className="card">
        <h3>殘差診斷：{model.label}</h3>
        <ResidualCharts model={model} />
      </section>

      <section className="card">
        <h3>交叉驗證（{models[0].cv.method}）</h3>
        <Table
          caption="交叉驗證每折 R²"
          rows={models}
          rowClass={(m) => (m.is_best ? "best" : undefined)}
          columns={[
            { key: "m", header: "模型", render: (m) => m.label },
            ...[0, 1, 2, 3, 4].map((i) => ({
              key: `f${i}`,
              header: `第 ${i + 1} 折`,
              num: true,
              render: (m: Model) => fmtNum(m.cv.scores_r2[i]),
            })),
            { key: "mean", header: "平均", num: true, render: (m) => fmtNum(m.cv.mean) },
            { key: "std", header: "標準差", num: true, render: (m) => fmtNum(m.cv.std) },
          ]}
        />
      </section>

      <section className="card">
        <h3>分析與結論</h3>
        <Markdown text={data.crisp_dm.evaluation.markdown} />
      </section>
    </>
  );
}
