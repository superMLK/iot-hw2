import { useRef, useState, type FormEvent } from "react";
import { DescribeTable, Heatmap, Histogram, PreviewTable, TopBar } from "../components/DataViews";
import Table from "../components/Table";
import { fmtInt } from "../lib/format";
import { errorMessage, loadFromFile, loadFromUrl, MAX_HEATMAP_COLS, MAX_ROWS, type Summary, type UserMessage } from "./loader";

export const SAMPLE_URL = "https://raw.githubusercontent.com/Avik-Jain/100-Days-Of-ML-Code/master/datasets/50_Startups.csv";

const TYPE_LABEL = { numeric: "數值", categorical: "類別", date: "日期" } as const;

type State =
  | { status: "idle" }
  | { status: "loading"; source: string }
  | { status: "error"; message: UserMessage }
  | { status: "ready"; summary: Summary; source: string };

export default function CustomCsv() {
  const [url, setUrl] = useState(SAMPLE_URL);
  const [state, setState] = useState<State>({ status: "idle" });
  const abortRef = useRef<AbortController | null>(null);
  const fileRef = useRef<HTMLInputElement>(null);

  async function run(source: string, load: (signal: AbortSignal) => Promise<Summary>) {
    abortRef.current?.abort();
    const ctrl = new AbortController();
    abortRef.current = ctrl;
    setState({ status: "loading", source });
    try {
      const summary = await load(ctrl.signal);
      if (!ctrl.signal.aborted) setState({ status: "ready", summary, source });
    } catch (e) {
      if ((e as Error)?.name === "AbortError") return;
      setState({ status: "error", message: errorMessage(e) });
    }
  }

  function onSubmit(e: FormEvent) {
    e.preventDefault();
    run(url.trim(), (signal) => loadFromUrl(url, signal));
  }

  function onFile(files: FileList | null) {
    const f = files?.[0];
    if (!f) return;
    run(`上傳檔案：${f.name}`, () => loadFromFile(f));
    if (fileRef.current) fileRef.current.value = "";
  }

  return (
    <>
      <section className="card">
        <h2 style={{ marginTop: 0 }}>自訂 CSV 資料檢視</h2>
        <p className="note">
          輸入 CSV 檔的網址，或上傳本機 CSV 檔，即可檢視欄位、型別、缺失值、敘述統計、相關係數與分布。
          資料只在你的瀏覽器中處理，不會上傳到任何伺服器。此模式只顯示資料資訊，不進行建模。
        </p>
        <form className="custom-input" onSubmit={onSubmit} noValidate>
          <label htmlFor="csv-url" className="visually-hidden">
            CSV 網址
          </label>
          <input id="csv-url" type="url" inputMode="url" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://…/data.csv" />
          <button type="submit" disabled={state.status === "loading"}>
            {state.status === "loading" ? "載入中…" : "載入網址"}
          </button>
          <label className="button secondary file-label">
            上傳 CSV 檔
            <input ref={fileRef} type="file" accept=".csv,text/csv,text/plain" onChange={(e) => onFile(e.target.files)} aria-label="上傳 CSV 檔" />
          </label>
        </form>
        <p className="note" style={{ marginBottom: 0 }}>
          提示：GitHub 檔案請使用 Raw 原始網址（raw.githubusercontent.com）。超過 {fmtInt(MAX_ROWS)} 筆時只取前 {fmtInt(MAX_ROWS)} 筆。
        </p>
      </section>

      {state.status === "loading" && <p className="note">正在讀取 {state.source} …</p>}

      {state.status === "error" && (
        <div className="error card" role="alert">
          <strong>{state.message.title}</strong>
          <p style={{ margin: "6px 0" }}>{state.message.body}</p>
          {state.message.hint && <p className="note" style={{ margin: 0 }}>{state.message.hint}</p>}
        </div>
      )}

      {state.status === "ready" && <SummaryView summary={state.summary} source={state.source} />}
    </>
  );
}

function SummaryView({ summary: s, source }: { summary: Summary; source: string }) {
  const nNum = s.columns.filter((c) => c.type === "numeric").length;
  const totalMissing = s.columns.reduce((n, c) => n + c.missing, 0);
  return (
    <>
      <section className="card">
        <h3 style={{ marginTop: 0 }}>資料概況</h3>
        <p className="note" style={{ overflowWrap: "anywhere" }}>來源：{source}</p>
        {s.truncated && (
          <p className="warning-text" role="status">
            ⚠ 資料超過 {fmtInt(MAX_ROWS)} 筆，只取前 {fmtInt(MAX_ROWS)} 筆進行分析。
          </p>
        )}
        <div className="stat-row">
          <div className="stat">
            <div className="label">筆數</div>
            <div className="value">{fmtInt(s.nRows)}</div>
          </div>
          <div className="stat">
            <div className="label">欄數</div>
            <div className="value">{s.nCols}</div>
          </div>
          <div className="stat">
            <div className="label">數值欄</div>
            <div className="value">{nNum}</div>
          </div>
          <div className="stat">
            <div className="label">缺失值總數</div>
            <div className="value">{fmtInt(totalMissing)}</div>
          </div>
        </div>
        <h3>欄位資訊</h3>
        <Table
          caption="欄位資訊"
          rows={s.columns}
          columns={[
            { key: "n", header: "欄位", render: (c) => <code>{c.name}</code> },
            { key: "t", header: "型別", render: (c) => TYPE_LABEL[c.type] },
            { key: "m", header: "缺失值", num: true, render: (c) => fmtInt(c.missing) },
            { key: "u", header: "唯一值", num: true, render: (c) => fmtInt(c.unique) },
          ]}
        />
        {s.describe.length > 0 ? (
          <>
            <h3>數值欄敘述統計</h3>
            <DescribeTable rows={s.describe} />
          </>
        ) : (
          <p className="note">沒有數值欄，因此不顯示敘述統計與相關係數。</p>
        )}
      </section>

      {s.corr.labels.length >= 2 && (
        <section className="card">
          {s.corr.limited && (
            <p className="warning-text" role="status">
              數值欄共 {s.corr.nNumeric} 欄，熱圖只顯示前 {MAX_HEATMAP_COLS} 欄。
            </p>
          )}
          <Heatmap title="數值欄相關係數矩陣" labels={s.corr.labels} matrix={s.corr.matrix} />
        </section>
      )}

      <section className="card">
        <h3 style={{ marginTop: 0 }}>各欄分布</h3>
        <p className="note">數值欄以直方圖呈現；類別與日期欄顯示出現次數最多的前 10 個值。</p>
        <div className="grid-2">
          {s.distributions.map((d) =>
            d.kind === "hist" ? (
              d.counts.length > 0 ? (
                <Histogram key={d.name} title={d.name} xLabel={d.name} bins={d.bins} counts={d.counts} />
              ) : (
                <p key={d.name} className="note">{d.name}：沒有可用的數值。</p>
              )
            ) : d.items.length > 0 ? (
              <TopBar key={d.name} title={`${d.name}（前 ${d.items.length} 名，共 ${fmtInt(d.nUnique)} 種）`} items={d.items} />
            ) : (
              <p key={d.name} className="note">{d.name}：全部為缺失值。</p>
            ),
          )}
        </div>
      </section>

      <section className="card">
        <h3 style={{ marginTop: 0 }}>資料預覽（前 {s.preview.length} 筆）</h3>
        <PreviewTable rows={s.preview} columns={s.fields} />
      </section>
    </>
  );
}
