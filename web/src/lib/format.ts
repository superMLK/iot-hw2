// 數值顯示格式（與管線內容檔的格式一致：R² 三位小數、金額千分位、百分比一位小數）

export function fmtNum(v: number | null | undefined, digits = 3): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  if (!Number.isFinite(v)) return v > 0 ? "∞" : "−∞";
  return v.toLocaleString("en-US", { minimumFractionDigits: digits, maximumFractionDigits: digits });
}

export function fmtInt(v: number | null | undefined): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return Math.round(v).toLocaleString("en-US");
}

export function fmtPct(v: number | null | undefined, digits = 1): string {
  if (v === null || v === undefined || Number.isNaN(v)) return "—";
  return `${(v * 100).toFixed(digits)}%`;
}

/** 自動選擇有效位數：大數用千分位整數，小數用 3–4 位 */
export function fmtAuto(v: number | string | null | undefined): string {
  if (v === null || v === undefined) return "—";
  if (typeof v === "string") return v;
  if (Number.isNaN(v)) return "—";
  if (!Number.isFinite(v)) return v > 0 ? "∞" : "−∞";
  const a = Math.abs(v);
  if (Number.isInteger(v)) return v.toLocaleString("en-US");
  if (a >= 1000) return fmtInt(v);
  if (a >= 1) return fmtNum(v, 2);
  if (a === 0) return "0";
  if (a < 0.001) return v.toExponential(2);
  return fmtNum(v, 4);
}

export function fmtP(p: number): string {
  if (p < 0.001) return "< 0.001";
  return p.toFixed(3);
}

export function fmtMoney(v: number): string {
  return `$${fmtInt(v)}`;
}
