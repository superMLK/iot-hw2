import { lazy, Suspense, useCallback, useEffect, useState } from "react";
import InfoCard from "./components/InfoCard";
import StepNav from "./components/StepNav";
import { DATASET_OPTIONS, parseHash, switchStep, switchView, toHash, type Route, type StepId, type View } from "./route";
import StepContent from "./steps/StepContent";
import type { DatasetId } from "./types/dataset";
import { useDataset } from "./useDataset";

const CustomCsv = lazy(() => import("./custom/CustomCsv"));

function useRoute(): [Route, (r: Route) => void] {
  const [route, setRoute] = useState<Route>(() => parseHash(window.location.hash));

  useEffect(() => {
    // 無效或空的 hash 正規化成預設網址，但不新增歷史紀錄
    const canonical = toHash(route);
    if (window.location.hash !== canonical) history.replaceState(null, "", canonical);
    const onHash = () => setRoute((prev) => parseHash(window.location.hash, prev.step));
    window.addEventListener("hashchange", onHash);
    return () => window.removeEventListener("hashchange", onHash);
  }, []);

  const navigate = useCallback((r: Route) => {
    setRoute(r);
    const h = toHash(r);
    if (window.location.hash !== h) history.pushState(null, "", h);
  }, []);

  return [route, navigate];
}

function DatasetView({ id, step, onStep }: { id: DatasetId; step: StepId; onStep: (s: StepId) => void }) {
  const state = useDataset(id);
  if (state.status === "loading") return <p className="note">資料載入中…</p>;
  if (state.status === "error")
    return (
      <div className="error" role="alert">
        <strong>載入失敗：</strong>
        {state.message}
      </div>
    );
  return (
    <>
      <InfoCard data={state.data} />
      <StepNav current={step} onChange={onStep} />
      <StepContent key={`${id}-${step}`} data={state.data} step={step} />
    </>
  );
}

export default function App() {
  const [route, navigate] = useRoute();

  useEffect(() => {
    window.scrollTo?.({ top: 0 });
  }, [route.view]);

  return (
    <>
      <header className="site-header">
        <div className="container">
          <h1 className="site-title">
            CRISP-DM 線性回歸分析
            <small>單純線性回歸 · 多元線性回歸 · Auto Regression</small>
          </h1>
          <label className="select-label">
            資料集：
            <select value={route.view} onChange={(e) => navigate(switchView(route, e.target.value as View))}>
              {DATASET_OPTIONS.map((o) => (
                <option key={o.value} value={o.value}>
                  {o.label}
                </option>
              ))}
            </select>
          </label>
        </div>
      </header>
      <main>
        <div className="container">
          {route.view === "custom" ? (
            <Suspense fallback={<p className="note">載入中…</p>}>
              <CustomCsv />
            </Suspense>
          ) : (
            <DatasetView id={route.view} step={route.step} onStep={(s) => navigate(switchStep(route, s))} />
          )}
        </div>
      </main>
      <footer className="site-footer">
        <div className="container">
          物聯網應用與資料分析 HW2 · 內建資料集的分析結果由 Python 管線在建置時產生，自訂 CSV 只在你的瀏覽器中處理、不會上傳。
        </div>
      </footer>
    </>
  );
}
