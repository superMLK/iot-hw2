import Markdown from "../components/Markdown";
import Table from "../components/Table";
import { fmtInt } from "../lib/format";
import type { DatasetResult } from "../types/dataset";

export default function PreparationStep({ data }: { data: DatasetResult }) {
  const p = data.crisp_dm.data_preparation;
  return (
    <>
      <section className="card">
        <h2>③ 資料準備（Data Preparation）</h2>
        <Markdown text={p.markdown} />
        <div className="stat-row" style={{ marginTop: 12 }}>
          <div className="stat">
            <div className="label">處理前</div>
            <div className="value small">
              {fmtInt(p.before.rows)} 筆 × {p.before.cols} 欄
            </div>
          </div>
          <div className="stat">
            <div className="label">處理後</div>
            <div className="value small">
              {fmtInt(p.after.rows)} 筆 × {p.after.cols} 欄
            </div>
          </div>
          <div className="stat">
            <div className="label">候選特徵</div>
            <div className="value">{p.after.features}</div>
          </div>
          <div className="stat">
            <div className="label">移除筆數</div>
            <div className="value">{fmtInt(p.n_removed_rows)}</div>
          </div>
        </div>
      </section>
      <section className="card">
        <h3>處理步驟</h3>
        <Table
          caption="資料準備步驟"
          rows={p.steps}
          rowClass={(s) => (s.highlight ? "highlight" : undefined)}
          columns={[
            { key: "i", header: "#", num: true, render: (_s, i) => i + 1 },
            {
              key: "name",
              header: "步驟",
              wrap: true,
              render: (s) => (
                <>
                  <strong>{s.name}</strong>
                  {s.highlight && <span className="badge" style={{ background: "var(--callout-border)" }}>⚠ 資料洩漏</span>}
                </>
              ),
            },
            { key: "reason", header: "原因", wrap: true, render: (s) => s.reason },
            { key: "affected", header: "影響", wrap: true, render: (s) => s.affected },
          ]}
        />
      </section>
    </>
  );
}
