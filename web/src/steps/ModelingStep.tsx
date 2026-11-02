import { useState } from "react";
import Markdown from "../components/Markdown";
import Table from "../components/Table";
import { fmtAuto, fmtNum, fmtP } from "../lib/format";
import type { DatasetResult } from "../types/dataset";

const Kept = ({ v }: { v: boolean }) => (v ? <span className="yes">✓ 保留</span> : <span className="no">✗ 移除</span>);

export default function ModelingStep({ data }: { data: DatasetResult }) {
  const fs = data.feature_selection;
  const labels = data.meta.feature_labels;
  const [modelId, setModelId] = useState(data.models.find((m) => m.id === "mlr_selected")?.id ?? data.models[0].id);
  const model = data.models.find((m) => m.id === modelId)!;
  const label = (f: string) => labels[f] ?? "";

  return (
    <>
      <section className="card">
        <h2>④ 建模（Modeling）</h2>
        <div className="stat-row">
          <div className="stat">
            <div className="label">候選特徵</div>
            <div className="value">{fs.n_candidates}</div>
          </div>
          <div className="stat">
            <div className="label">相關係數篩選保留</div>
            <div className="value">{fs.n_corr_kept}</div>
          </div>
          <div className="stat">
            <div className="label">VIF 後</div>
            <div className="value">{fs.n_after_vif}</div>
          </div>
          <div className="stat">
            <div className="label">逐步回歸最終</div>
            <div className="value">
              {fs.n_candidates} → {fs.n_final}
            </div>
          </div>
        </div>
        <Markdown text={data.crisp_dm.modeling.markdown} />
      </section>

      <section className="card">
        <h3>方法 1：相關係數篩選（訓練集）</h3>
        <p className="note">
          保留規則：與目標的 |r| ≥ {fs.correlation_rule.min_abs_r}；兩特徵彼此 |r| &gt; {fs.correlation_rule.high_corr_pair} 時保留與目標較相關者。
        </p>
        <div className="grid-2">
          <Table
            caption="特徵與目標的相關係數"
            tall
            rows={fs.correlation}
            columns={[
              { key: "f", header: "特徵", render: (r) => <code>{r.feature}</code> },
              { key: "l", header: "說明", render: (r) => label(r.feature) },
              { key: "r", header: "|r|", num: true, render: (r) => r.abs_r.toFixed(3) },
              { key: "k", header: "結果", render: (r) => <Kept v={fs.comparison.find((c) => c.feature === r.feature)!.corr_kept} /> },
            ]}
          />
          <div>
            <h4 style={{ marginTop: 0 }}>彼此高度相關（|r| &gt; {fs.correlation_rule.high_corr_pair}）的特徵對</h4>
            {fs.high_corr_pairs.length === 0 ? (
              <p className="note">沒有任何特徵對超過門檻。</p>
            ) : (
              <Table
                caption="高相關特徵對"
                rows={fs.high_corr_pairs}
                columns={[
                  { key: "a", header: "特徵 A", render: (p) => <code>{p.a}</code> },
                  { key: "b", header: "特徵 B", render: (p) => <code>{p.b}</code> },
                  { key: "r", header: "r", num: true, render: (p) => p.r.toFixed(3) },
                  { key: "d", header: "移除", render: (p) => (p.dropped ? <code>{p.dropped}</code> : "—") },
                ]}
              />
            )}
          </div>
        </div>

        <h3>方法 2：VIF 迭代移除（門檻 {fs.vif_threshold}）</h3>
        {fs.vif_rounds.length === 0 ? (
          <p className="note">所有特徵的 VIF 都不大於 {fs.vif_threshold}，不需移除。</p>
        ) : (
          <Table
            caption="VIF 各輪移除紀錄"
            rows={fs.vif_rounds}
            columns={[
              { key: "r", header: "輪次", num: true, render: (r) => r.round },
              { key: "f", header: "移除特徵", render: (r) => <code>{r.removed}</code> },
              { key: "v", header: "當下 VIF", num: true, render: (r) => (r.vif_is_inf ? "∞" : fmtNum(r.vif, 2)) },
              { key: "n", header: "剩餘特徵數", num: true, render: (r) => r.remaining.length },
            ]}
          />
        )}
        <details>
          <summary>VIF 篩選後各特徵的 VIF</summary>
          <Table
            caption="最終 VIF"
            tall
            rows={[...fs.vif_final].sort((a, b) => b.vif - a.vif)}
            columns={[
              { key: "f", header: "特徵", render: (r) => <code>{r.feature}</code> },
              { key: "v", header: "VIF", num: true, render: (r) => fmtNum(r.vif, 2) },
            ]}
          />
        </details>

        <h3>方法 3：雙向逐步回歸（AIC）</h3>
        <p className="note">起點為只有截距的模型（AIC = {fmtNum(fs.stepwise_start_aic, 1)}），候選為 VIF 篩選後的 {fs.n_after_vif} 個特徵。</p>
        <Table
          caption="逐步回歸紀錄"
          tall
          rows={fs.stepwise_steps}
          columns={[
            { key: "s", header: "步驟", num: true, render: (r) => r.step },
            { key: "a", header: "動作", render: (r) => (r.action === "add" ? "加入" : "移除") },
            { key: "f", header: "特徵", render: (r) => <code>{r.feature}</code> },
            { key: "l", header: "說明", render: (r) => label(r.feature) },
            { key: "aic", header: "AIC", num: true, render: (r) => fmtNum(r.aic, 1) },
          ]}
        />

        <h3>三種方法比較</h3>
        <Table
          caption="特徵選擇方法比較"
          tall
          rows={fs.comparison}
          rowClass={(r) => (r.stepwise_kept ? "best" : undefined)}
          columns={[
            { key: "f", header: "特徵", render: (r) => <code>{r.feature}</code> },
            { key: "l", header: "說明", render: (r) => label(r.feature) },
            { key: "c", header: "相關係數", render: (r) => <Kept v={r.corr_kept} /> },
            { key: "v", header: "VIF", render: (r) => <Kept v={r.vif_kept} /> },
            { key: "s", header: "逐步回歸（最終）", render: (r) => <Kept v={r.stepwise_kept} /> },
          ]}
        />
        <p>
          <strong>最終特徵（{fs.n_final} 個）：</strong>
          {fs.final_features.map((f) => (
            <code key={f} style={{ marginRight: 6, display: "inline-block" }}>
              {f}
            </code>
          ))}
        </p>
      </section>

      <section className="card">
        <h3>模型與係數表</h3>
        <div className="toggle-group" role="group" aria-label="選擇模型">
          {data.models.map((m) => (
            <button key={m.id} type="button" aria-pressed={m.id === modelId} onClick={() => setModelId(m.id)}>
              {m.label}
            </button>
          ))}
        </div>
        <p className="note">
          訓練集 {model.n_train} 筆；
          {model.type === "ar" ? `AR(${model.ar_order}) 以前 ${model.ar_order} 期的 ${data.meta.target} 預測當期` : `特徵 ${model.features.length} 個`}
          {model.train_r2 !== undefined && `；訓練集 R² = ${model.train_r2.toFixed(3)}`}；AIC = {fmtNum(model.aic, 1)}。
          底色標示 p &lt; 0.05 的係數。
          {data.meta.log_target && " 目標為 log(price)，係數為對數尺度。"}
        </p>
        <Table
          caption={`${model.label} 係數表`}
          rows={model.coefficients}
          columns={[
            { key: "n", header: "變數", render: (c) => (c.name === "const" ? "截距" : <code>{c.name}</code>) },
            { key: "l", header: "說明", render: (c) => label(c.name) },
            { key: "coef", header: "係數", num: true, render: (c) => fmtAuto(c.coef) },
            { key: "se", header: "標準誤", num: true, render: (c) => fmtAuto(c.std_err) },
            { key: "t", header: "t 值", num: true, render: (c) => fmtNum(c.t, 2) },
            {
              key: "p",
              header: "p 值",
              num: true,
              cellClass: (c) => (c.p < 0.05 ? "sig" : undefined),
              render: (c) => (
                <>
                  {fmtP(c.p)}
                  {c.p < 0.05 && <span aria-label="顯著"> ＊</span>}
                </>
              ),
            },
            { key: "ci", header: "95% 信賴區間", num: true, render: (c) => `[${fmtAuto(c.ci_low)}, ${fmtAuto(c.ci_high)}]` },
          ]}
        />
      </section>
    </>
  );
}
