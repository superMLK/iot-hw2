import Markdown from "../components/Markdown";
import type { DatasetResult } from "../types/dataset";

const FLOW = ["推送到 main", "Python 分析管線", "產生 JSON 與圖檔", "前端單元測試", "Vite 建置", "GitHub Pages"];

export default function DeploymentStep({ data }: { data: DatasetResult }) {
  return (
    <section className="card">
      <h2>⑥ 部署（Deployment）</h2>
      <ol className="steps" aria-label="部署流程" style={{ marginTop: 8 }}>
        {FLOW.map((f, i) => (
          <li key={f}>
            <div className="stat" style={{ textAlign: "center", height: "100%" }}>
              <div className="label">步驟 {i + 1}</div>
              <div style={{ fontWeight: 600, fontSize: "0.9rem" }}>{f}</div>
            </div>
          </li>
        ))}
      </ol>
      <Markdown text={data.crisp_dm.deployment.markdown} />
      <p className="note">本頁資料產生時間：{new Date(data.meta.generated_at).toLocaleString("zh-TW", { hour12: false })}</p>
    </section>
  );
}
