// 自訂 CSV 的統計純函式（不依賴 DOM，可單獨測試）

export type ColumnType = "numeric" | "categorical" | "date";
export type Cell = string | number | boolean | null | undefined | Date;

const TYPE_THRESHOLD = 0.95;
// 日期：YYYY-MM-DD、YYYY/MM/DD、可帶時間；或 MM/DD/YYYY。純數字不視為日期
const DATE_RE = /^(\d{4}[-/.]\d{1,2}[-/.]\d{1,2}([ T]\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(Z|[+-]\d{2}:?\d{2})?)?|\d{1,2}\/\d{1,2}\/\d{4})$/;

export function isMissing(v: Cell): boolean {
  if (v === null || v === undefined) return true;
  if (typeof v === "number") return Number.isNaN(v);
  if (typeof v === "string") {
    const s = v.trim();
    return s === "" || /^(na|n\/a|nan|null|none)$/i.test(s);
  }
  return false;
}

export function toNumber(v: Cell): number | null {
  if (isMissing(v)) return null;
  if (typeof v === "number") return Number.isFinite(v) ? v : null;
  if (typeof v === "boolean") return null;
  if (typeof v === "string") {
    const s = v.trim().replace(/,/g, "");
    if (!/^[-+]?(\d+\.?\d*|\.\d+)([eE][-+]?\d+)?$/.test(s)) return null;
    const n = Number(s);
    return Number.isFinite(n) ? n : null;
  }
  return null;
}

export function isDateLike(v: Cell): boolean {
  if (v instanceof Date) return !Number.isNaN(v.getTime());
  if (typeof v !== "string") return false;
  const s = v.trim();
  if (!DATE_RE.test(s)) return false;
  return !Number.isNaN(Date.parse(s)) || !Number.isNaN(Date.parse(s.replace(/\//g, "-")));
}

export function countMissing(values: Cell[]): number {
  return values.reduce<number>((n, v) => n + (isMissing(v) ? 1 : 0), 0);
}

export function inferType(values: Cell[]): ColumnType {
  const present = values.filter((v) => !isMissing(v));
  if (present.length === 0) return "categorical";
  const nNum = present.filter((v) => toNumber(v) !== null).length;
  if (nNum / present.length >= TYPE_THRESHOLD) return "numeric";
  const nDate = present.filter(isDateLike).length;
  if (nDate / present.length >= TYPE_THRESHOLD) return "date";
  return "categorical";
}

export function numbers(values: Cell[]): number[] {
  const out: number[] = [];
  for (const v of values) {
    const n = toNumber(v);
    if (n !== null) out.push(n);
  }
  return out;
}

/** 線性內插分位數（與 pandas 預設相同）；sorted 必須已排序 */
export function quantile(sorted: number[], q: number): number {
  if (sorted.length === 0) return NaN;
  const pos = (sorted.length - 1) * q;
  const lo = Math.floor(pos);
  const hi = Math.ceil(pos);
  return sorted[lo] + (sorted[hi] - sorted[lo]) * (pos - lo);
}

export interface Describe {
  count: number;
  mean: number;
  std: number;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
}

export function describe(nums: number[]): Describe {
  const n = nums.length;
  if (n === 0) return { count: 0, mean: NaN, std: NaN, min: NaN, q1: NaN, median: NaN, q3: NaN, max: NaN };
  const sorted = [...nums].sort((a, b) => a - b);
  const mean = nums.reduce((s, x) => s + x, 0) / n;
  const variance = n > 1 ? nums.reduce((s, x) => s + (x - mean) ** 2, 0) / (n - 1) : NaN;
  return {
    count: n,
    mean,
    std: Math.sqrt(variance),
    min: sorted[0],
    q1: quantile(sorted, 0.25),
    median: quantile(sorted, 0.5),
    q3: quantile(sorted, 0.75),
    max: sorted[n - 1],
  };
}

/** Pearson 相關係數（成對完整觀測）；觀測不足或變異為 0 時回傳 null */
export function pearson(a: (number | null)[], b: (number | null)[]): number | null {
  let n = 0, sa = 0, sb = 0;
  for (let i = 0; i < a.length; i++) {
    const x = a[i], y = b[i];
    if (x === null || y === null) continue;
    n++; sa += x; sb += y;
  }
  if (n < 2) return null;
  const ma = sa / n, mb = sb / n;
  let cov = 0, va = 0, vb = 0;
  for (let i = 0; i < a.length; i++) {
    const x = a[i], y = b[i];
    if (x === null || y === null) continue;
    cov += (x - ma) * (y - mb); va += (x - ma) ** 2; vb += (y - mb) ** 2;
  }
  if (va === 0 || vb === 0) return null;
  return Math.max(-1, Math.min(1, cov / Math.sqrt(va * vb)));
}

export function correlationMatrix(columns: (number | null)[][]): (number | null)[][] {
  const k = columns.length;
  const m: (number | null)[][] = Array.from({ length: k }, () => Array<number | null>(k).fill(null));
  for (let i = 0; i < k; i++) {
    for (let j = i; j < k; j++) {
      const r = i === j ? (pearson(columns[i], columns[i]) === null ? null : 1) : pearson(columns[i], columns[j]);
      m[i][j] = r;
      m[j][i] = r;
    }
  }
  return m;
}

export function histogram(nums: number[], bins = 20): { bins: number[]; counts: number[] } {
  if (nums.length === 0) return { bins: [], counts: [] };
  let lo = Infinity, hi = -Infinity;
  for (const x of nums) { if (x < lo) lo = x; if (x > hi) hi = x; }
  if (lo === hi) { lo -= 0.5; hi += 0.5; bins = 1; }
  const width = (hi - lo) / bins;
  const edges = Array.from({ length: bins + 1 }, (_, i) => lo + i * width);
  const counts = Array<number>(bins).fill(0);
  for (const x of nums) counts[Math.min(bins - 1, Math.floor((x - lo) / width))]++;
  return { bins: edges, counts };
}

export function topCategories(values: Cell[], k = 10): { value: string; count: number }[] {
  const map = new Map<string, number>();
  for (const v of values) {
    if (isMissing(v)) continue;
    const key = v instanceof Date ? v.toISOString() : String(v).trim();
    map.set(key, (map.get(key) ?? 0) + 1);
  }
  return [...map.entries()]
    .sort((a, b) => b[1] - a[1] || (a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0))
    .slice(0, k)
    .map(([value, count]) => ({ value, count }));
}

export function uniqueCount(values: Cell[]): number {
  const s = new Set<string>();
  for (const v of values) if (!isMissing(v)) s.add(String(v).trim());
  return s.size;
}
