// 網址 hash 狀態：#<dataset>-<step>（例如 #bike-modeling），自訂 CSV 為 #custom
import type { DatasetId } from "./types/dataset";

export const STEPS = [
  { id: "business", label: "業務理解", en: "Business Understanding" },
  { id: "data", label: "資料理解", en: "Data Understanding" },
  { id: "preparation", label: "資料準備", en: "Data Preparation" },
  { id: "modeling", label: "建模", en: "Modeling" },
  { id: "evaluation", label: "評估", en: "Evaluation" },
  { id: "deployment", label: "部署", en: "Deployment" },
] as const;

export type StepId = (typeof STEPS)[number]["id"];
export type View = DatasetId | "custom";

export const DATASET_OPTIONS: { value: View; label: string }[] = [
  { value: "bike", label: "Bike Sharing（每日租借量）" },
  { value: "house", label: "King County 房價" },
  { value: "custom", label: "自訂 CSV URL" },
];

export type Route = { view: DatasetId; step: StepId } | { view: "custom"; step: StepId };

export const DEFAULT_ROUTE: Route = { view: "bike", step: "business" };

const STEP_IDS = new Set<string>(STEPS.map((s) => s.id));
const DATASETS = new Set<string>(["bike", "house"]);

export function isStep(s: string): s is StepId {
  return STEP_IDS.has(s);
}

/** 解析 hash；無法辨識時回到預設（Bike 業務理解）。custom 的 step 記住上一次的步驟。 */
export function parseHash(hash: string, lastStep: StepId = "business"): Route {
  const h = decodeURIComponent(hash.replace(/^#/, "")).trim().toLowerCase();
  if (h === "custom") return { view: "custom", step: lastStep };
  const m = /^([a-z]+)-([a-z]+)$/.exec(h);
  if (m && DATASETS.has(m[1]) && isStep(m[2])) return { view: m[1] as DatasetId, step: m[2] };
  if (DATASETS.has(h)) return { view: h as DatasetId, step: "business" };
  return DEFAULT_ROUTE;
}

export function toHash(route: Route): string {
  return route.view === "custom" ? "#custom" : `#${route.view}-${route.step}`;
}

/** 切換下拉選單：內建資料集之間（或從自訂回來）保留目前的步驟。 */
export function switchView(route: Route, view: View): Route {
  return { view, step: route.step } as Route;
}

export function switchStep(route: Route, step: StepId): Route {
  return route.view === "custom" ? route : { view: route.view, step };
}
