import Markdown from "../components/Markdown";
import type { DatasetResult } from "../types/dataset";

export default function BusinessStep({ data }: { data: DatasetResult }) {
  const s = data.crisp_dm.evaluation.success;
  return (
    <section className="card">
      <h2>① 業務理解（Business Understanding）</h2>
      <Markdown text={data.crisp_dm.business_understanding.markdown} />
      <div className="stat-row" style={{ marginTop: 12 }}>
        <div className="stat">
          <div className="label">成功標準</div>
          <div className="value small">
            {s.metric} ≥ {s.threshold.toFixed(2)}
          </div>
        </div>
        <div className="stat">
          <div className="label">最佳模型實際值</div>
          <div className="value small">
            {s.actual.toFixed(3)} {s.met ? <span className="yes">✓ 達標</span> : <span className="warning-text">✗ 未達標</span>}
          </div>
        </div>
      </div>
    </section>
  );
}
