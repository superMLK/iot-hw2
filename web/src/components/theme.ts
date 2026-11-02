import { useEffect, useState } from "react";

export interface ChartTheme {
  dark: boolean;
  text: string;
  text2: string;
  muted: string;
  border: string;
  surface: string;
  series1: string;
  series2: string;
  neutral: string;
  divLow: string;
  divMid: string;
  divHigh: string;
}

function read(): ChartTheme {
  const s = getComputedStyle(document.documentElement);
  const v = (n: string) => s.getPropertyValue(n).trim();
  return {
    dark: window.matchMedia?.("(prefers-color-scheme: dark)").matches ?? false,
    text: v("--text"),
    text2: v("--text-2"),
    muted: v("--muted"),
    border: v("--border"),
    surface: v("--surface"),
    series1: v("--series-1"),
    series2: v("--series-2"),
    neutral: v("--neutral-mark"),
    divLow: v("--div-low"),
    divMid: v("--div-mid"),
    divHigh: v("--div-high"),
  };
}

/** 讀取 CSS 變數作為圖表配色，系統深淺色切換時自動更新 */
export function useChartTheme(): ChartTheme {
  const [theme, setTheme] = useState<ChartTheme>(read);
  useEffect(() => {
    const mq = window.matchMedia?.("(prefers-color-scheme: dark)");
    if (!mq) return;
    const on = () => setTheme(read());
    mq.addEventListener("change", on);
    return () => mq.removeEventListener("change", on);
  }, []);
  return theme;
}

/** 十六進位色碼轉 rgba（區間帶用同一色相、不同透明度） */
export function alpha(hex: string, a: number): string {
  const h = hex.replace("#", "");
  const n = parseInt(h.length === 3 ? h.split("").map((c) => c + c).join("") : h, 16);
  return `rgba(${(n >> 16) & 255}, ${(n >> 8) & 255}, ${n & 255}, ${a})`;
}

// 信賴區間較深、預測區間較淺；深色背景上整體調高以維持可見度
export const bandAlpha = (t: ChartTheme) => (t.dark ? { ci: 0.45, pi: 0.22 } : { ci: 0.35, pi: 0.15 });
