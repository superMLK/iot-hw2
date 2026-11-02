import { DescribeTable, Heatmap, Histogram, PreviewTable } from "../components/DataViews";
import Markdown from "../components/Markdown";
import Table from "../components/Table";
import { fmtInt } from "../lib/format";
import type { ColumnInfo, DatasetResult } from "../types/dataset";

const ROLE: Record<ColumnInfo["role"], string> = { target: "目標變數", id: "ID（不計入特徵）", date: "日期", feature: "特徵" };

export default function DataStep({ data }: { data: DatasetResult }) {
  const du = data.data_understanding;
  const target = data.meta.target;
  return (
    <>
      <section className="card">
        <h2>② 資料理解（Data Understanding）</h2>
        <div className="stat-row">
          <div className="stat">
            <div className="label">筆數</div>
            <div className="value">{fmtInt(du.n_rows)}</div>
          </div>
          <div className="stat">
            <div className="label">欄數</div>
            <div className="value">{du.n_cols}</div>
          </div>
          <div className="stat">
            <div className="label">特徵數（{du.feature_rule}）</div>
            <div className="value">
              {du.n_features}
              {du.n_features > 13 && du.n_features < 40 && <span className="badge">符合 13–40</span>}
            </div>
          </div>
          <div className="stat">
            <div className="label">缺失值／重複列</div>
            <div className="value small">
              {fmtInt(du.n_missing_total)} ／ {fmtInt(du.n_duplicates)}
            </div>
          </div>
        </div>
        <Markdown text={data.crisp_dm.data_understanding.markdown} />
      </section>

      <section className="card">
        <h3>欄位資訊</h3>
        <Table
          caption="欄位資訊"
          rows={du.columns}
          rowClass={(c) => (c.role === "target" ? "best" : undefined)}
          columns={[
            { key: "name", header: "欄位", render: (c) => <code>{c.name}</code> },
            { key: "role", header: "角色", render: (c) => ROLE[c.role] },
            { key: "dtype", header: "型別", render: (c) => (c.kind === "numeric" ? `數值（${c.dtype}）` : `文字（${c.dtype}）`) },
            { key: "missing", header: "缺失值", num: true, render: (c) => fmtInt(c.missing) },
            { key: "unique", header: "唯一值", num: true, render: (c) => fmtInt(c.unique) },
            { key: "label", header: "說明", render: (c) => data.meta.feature_labels[c.name] ?? "" },
          ]}
        />
        <h3>數值欄敘述統計</h3>
        <DescribeTable rows={Object.entries(du.describe).map(([name, d]) => ({ name, ...d }))} />
      </section>

      <section className="card">
        <div className="grid-2">
          <div>
            <Histogram
              title={`目標變數 ${target} 的分布`}
              xLabel={target}
              bins={du.target_distribution.bins}
              counts={du.target_distribution.counts}
            />
            <h3>與 {target} 相關性最高的 5 個欄位</h3>
            <Table
              caption="相關性最高的欄位"
              rows={du.top_corr_features}
              columns={[
                { key: "f", header: "欄位", render: (r) => <code>{r.feature}</code> },
                { key: "r", header: "相關係數 r", num: true, render: (r) => r.r.toFixed(3) },
              ]}
            />
          </div>
          <div>
            <Heatmap title="數值欄相關係數矩陣（原始資料）" labels={du.correlation.labels} matrix={du.correlation.matrix} />
          </div>
        </div>
      </section>

      <section className="card">
        <h3>資料預覽（前 10 筆）</h3>
        <PreviewTable rows={du.preview} columns={du.columns.map((c) => c.name)} />
      </section>
    </>
  );
}
