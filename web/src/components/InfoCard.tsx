import type { DatasetResult } from "../types/dataset";
import { fmtInt } from "../lib/format";

export default function InfoCard({ data }: { data: DatasetResult }) {
  const { meta, data_understanding: du } = data;
  return (
    <section className="card info-card" aria-labelledby="ds-title">
      <h2 id="ds-title">{meta.name}</h2>
      <div className="info-links">
        <a href={meta.kaggle_url} target="_blank" rel="noreferrer">
          Kaggle 資料來源 ↗
        </a>
        {meta.origin_url && (
          <a href={meta.origin_url} target="_blank" rel="noreferrer">
            原始出處 ↗
          </a>
        )}
        <span>
          授權：
          {meta.license_url ? (
            <a href={meta.license_url} target="_blank" rel="noreferrer">
              {meta.license}
            </a>
          ) : (
            meta.license
          )}
        </span>
        <span>
          檔案：<code>{meta.file}</code>
        </span>
      </div>
      <div className="stat-row">
        <div className="stat">
          <div className="label">筆數</div>
          <div className="value">{fmtInt(du.n_rows)}</div>
        </div>
        <div className="stat">
          <div className="label">特徵數</div>
          <div className="value">{du.n_features}</div>
        </div>
        <div className="stat">
          <div className="label">目標變數</div>
          <div className="value small">
            <code>{meta.target}</code>
            {meta.log_target && <span className="note">（以 log 建模）</span>}
          </div>
        </div>
        <div className="stat">
          <div className="label">資料切分</div>
          <div className="value small">{meta.split === "time" ? "依時間 80/20" : "隨機 80/20"}</div>
        </div>
      </div>
    </section>
  );
}
