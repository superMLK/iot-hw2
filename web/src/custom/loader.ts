// 自訂 CSV 載入：網址驗證、取得內容、解析、錯誤分類、統計彙整（除 fetch 外皆為純函式）
import Papa from "papaparse";
import {
  correlationMatrix,
  countMissing,
  describe,
  histogram,
  inferType,
  numbers,
  toNumber,
  topCategories,
  uniqueCount,
  type Cell,
  type ColumnType,
  type Describe,
} from "../lib/stats";

export const MAX_ROWS = 50_000;
export const MAX_HEATMAP_COLS = 50;
export const PREVIEW_ROWS = 10;

export type ErrorKind = "invalid_url" | "network" | "http" | "not_csv" | "empty";

export class CsvError extends Error {
  constructor(public kind: ErrorKind, public detail = "") {
    super(kind);
  }
}

export interface UserMessage {
  title: string;
  body: string;
  hint?: string;
}

/** 錯誤種類 → 中文訊息與建議 */
export function errorMessage(err: unknown): UserMessage {
  const e = err instanceof CsvError ? err : new CsvError("network", err instanceof Error ? err.message : String(err));
  switch (e.kind) {
    case "invalid_url":
      return {
        title: "網址格式錯誤",
        body: "請輸入以 http:// 或 https:// 開頭的完整網址。",
        hint: "例如：https://raw.githubusercontent.com/使用者/專案/main/data.csv",
      };
    case "network":
      return {
        title: "無法取得檔案（網路錯誤或跨來源限制）",
        body:
          "瀏覽器沒有收到回應。可能是網路中斷、網址不存在，或該網站不允許其他網站讀取它的檔案（CORS 限制）。",
        hint: "建議改用「原始檔案」網址（例如 GitHub 的 raw.githubusercontent.com），或下載後用「上傳 CSV 檔」。",
      };
    case "http":
      return {
        title: `伺服器回應錯誤（${e.detail}）`,
        body: "伺服器拒絕或找不到這個檔案，請確認網址是否正確、檔案是否公開。",
        hint: "也可以下載檔案後用「上傳 CSV 檔」。",
      };
    case "not_csv":
      return {
        title: "內容不是有效的 CSV",
        body: e.detail || "這個網址回傳的看起來不是 CSV 文字檔（例如是網頁或二進位檔）。",
        hint: "如果是 GitHub 或 Kaggle 的頁面網址，請改用檔案的「Raw」原始網址，或下載後上傳。",
      };
    case "empty":
      return { title: "檔案是空的", body: e.detail || "檔案中沒有任何資料列。", hint: "請確認檔案內容，至少需要一列標題與一列資料。" };
  }
}

export function validateUrl(input: string): URL {
  const s = input.trim();
  let url: URL;
  try {
    url = new URL(s);
  } catch {
    throw new CsvError("invalid_url");
  }
  if (url.protocol !== "http:" && url.protocol !== "https:") throw new CsvError("invalid_url");
  if (!url.hostname.includes(".") && url.hostname !== "localhost") throw new CsvError("invalid_url");
  return url;
}

export function looksLikeHtml(text: string, contentType = ""): boolean {
  if (/text\/html|application\/xhtml/i.test(contentType)) return true;
  const head = text.slice(0, 512).trimStart().toLowerCase();
  return head.startsWith("<!doctype html") || head.startsWith("<html") || /^<(head|body|div|script)[\s>]/.test(head);
}

export function looksBinary(text: string): boolean {
  const sample = text.slice(0, 2048);
  if (sample.includes("\u0000")) return true;
  const bad = (sample.match(/[\u0001-\u0008\u000E-\u001F�]/g) ?? []).length;
  return sample.length > 0 && bad / sample.length > 0.05;
}

export interface Parsed {
  fields: string[];
  rows: Record<string, Cell>[];
  truncated: boolean;
  totalSeen: number;
}

/** 解析 CSV 文字；超過 MAX_ROWS 只取前 MAX_ROWS 筆 */
export function parseCsvText(text: string, contentType = ""): Parsed {
  if (!text || !text.trim()) throw new CsvError("empty");
  if (looksLikeHtml(text, contentType)) throw new CsvError("not_csv", "這個網址回傳的是 HTML 網頁，不是 CSV 檔。");
  if (looksBinary(text)) throw new CsvError("not_csv", "檔案看起來是二進位格式（例如 Excel 或壓縮檔），請先另存為 CSV。");

  const res = Papa.parse<Record<string, Cell>>(text.replace(/^﻿/, ""), {
    header: true,
    dynamicTyping: true,
    skipEmptyLines: "greedy",
    preview: MAX_ROWS + 1,
    transformHeader: (h, i) => (h.trim() === "" ? `（未命名欄 ${i + 1}）` : h.trim()),
  });
  const fields = (res.meta.fields ?? []).filter((f) => f !== "__parsed_extra");
  if (fields.length === 0) throw new CsvError("empty");
  if (res.data.length === 0) throw new CsvError("empty", "檔案只有標題列，沒有任何資料列。");
  const fatal = res.errors.filter((e) => e.type === "Delimiter" || e.code === "UndetectableDelimiter");
  if (fields.length === 1 && fatal.length > 0 && res.data.length < 2) throw new CsvError("not_csv", "無法判斷欄位分隔符號，內容可能不是 CSV。");

  const truncated = res.data.length > MAX_ROWS;
  return { fields, rows: truncated ? res.data.slice(0, MAX_ROWS) : res.data, truncated, totalSeen: res.data.length };
}

export interface ColumnSummary {
  name: string;
  type: ColumnType;
  missing: number;
  unique: number;
}

export interface Summary {
  nRows: number;
  nCols: number;
  truncated: boolean;
  columns: ColumnSummary[];
  describe: (Describe & { name: string })[];
  corr: { labels: string[]; matrix: (number | null)[][]; limited: boolean; nNumeric: number };
  distributions: (
    | { name: string; kind: "hist"; bins: number[]; counts: number[] }
    | { name: string; kind: "top"; items: { value: string; count: number }[]; nUnique: number }
  )[];
  preview: Record<string, Cell>[];
  fields: string[];
}

export function summarize(p: Parsed): Summary {
  const columns: ColumnSummary[] = p.fields.map((f) => {
    const vals = p.rows.map((r) => r[f]);
    return { name: f, type: inferType(vals), missing: countMissing(vals), unique: uniqueCount(vals) };
  });
  const numericCols = columns.filter((c) => c.type === "numeric");
  const heatCols = numericCols.slice(0, MAX_HEATMAP_COLS);
  const colValues = (f: string) => p.rows.map((r) => r[f]);
  return {
    nRows: p.rows.length,
    nCols: p.fields.length,
    truncated: p.truncated,
    columns,
    describe: numericCols.map((c) => ({ name: c.name, ...describe(numbers(colValues(c.name))) })),
    corr: {
      labels: heatCols.map((c) => c.name),
      matrix: correlationMatrix(heatCols.map((c) => colValues(c.name).map(toNumber))),
      limited: numericCols.length > MAX_HEATMAP_COLS,
      nNumeric: numericCols.length,
    },
    distributions: columns.map((c) =>
      c.type === "numeric"
        ? { name: c.name, kind: "hist" as const, ...histogram(numbers(colValues(c.name))) }
        : { name: c.name, kind: "top" as const, items: topCategories(colValues(c.name), 10), nUnique: c.unique },
    ),
    preview: p.rows.slice(0, PREVIEW_ROWS),
    fields: p.fields,
  };
}

/** 從網址載入（只有這一步會連網） */
export async function loadFromUrl(input: string, signal?: AbortSignal): Promise<Summary> {
  const url = validateUrl(input);
  let res: Response;
  try {
    res = await fetch(url.toString(), { signal, mode: "cors", credentials: "omit" });
  } catch (e) {
    if ((e as Error)?.name === "AbortError") throw e;
    throw new CsvError("network", (e as Error)?.message);
  }
  if (!res.ok) throw new CsvError("http", `HTTP ${res.status}`);
  const text = await res.text();
  return summarize(parseCsvText(text, res.headers.get("content-type") ?? ""));
}

export async function loadFromFile(file: File): Promise<Summary> {
  if (file.size === 0) throw new CsvError("empty");
  const text = await file.text();
  return summarize(parseCsvText(text, file.type));
}
