// 資料理解頁與自訂 CSV 共用的檢視元件
import Chart from "./Chart";
import Table from "./Table";
import { useChartTheme } from "./theme";
import { fmtAuto, fmtInt } from "../lib/format";

export interface DescribeRow {
  name: string;
  count: number;
  mean: number;
  std: number;
  min: number;
  q1: number;
  median: number;
  q3: number;
  max: number;
}

export function DescribeTable({ rows }: { rows: DescribeRow[] }) {
  const cols = ["count", "mean", "std", "min", "q1", "median", "q3", "max"] as const;
  const head: Record<(typeof cols)[number], string> = {
    count: "筆數",
    mean: "平均",
    std: "標準差",
    min: "最小值",
    q1: "Q1",
    median: "中位數",
    q3: "Q3",
    max: "最大值",
  };
  return (
    <Table
      caption="數值欄敘述統計"
      rows={rows}
      columns={[
        { key: "name", header: "欄位", render: (r) => <code>{r.name}</code> },
        ...cols.map((c) => ({
          key: c,
          header: head[c],
          num: true,
          render: (r: DescribeRow) => (c === "count" ? fmtInt(r[c]) : fmtAuto(r[c])),
        })),
      ]}
    />
  );
}

export function Heatmap({ labels, matrix, title }: { labels: string[]; matrix: (number | null)[][]; title: string }) {
  const t = useChartTheme();
  const n = labels.length;
  const size = Math.max(360, Math.min(900, 26 * n + 160));
  return (
    <Chart
      label={title}
      height={size}
      minWidth={Math.max(420, 22 * n + 160)}
      data={[
        {
          type: "heatmap",
          z: matrix,
          x: labels,
          y: labels,
          zmin: -1,
          zmax: 1,
          colorscale: [
            [0, t.divLow],
            [0.5, t.divMid],
            [1, t.divHigh],
          ],
          colorbar: { title: { text: "r" }, thickness: 12, tickfont: { color: t.text2 } },
          hovertemplate: "%{y} × %{x}<br>r = %{z:.3f}<extra></extra>",
          xgap: 1,
          ygap: 1,
          ...(n <= 12 ? { texttemplate: "%{z:.2f}", textfont: { size: 11, color: t.text } } : {}),
        },
      ]}
      layout={{
        title: { text: title, font: { size: 14 } },
        xaxis: { tickangle: -60, showgrid: false, tickfont: { size: 10 } },
        yaxis: { autorange: "reversed", showgrid: false, tickfont: { size: 10 } },
        margin: { l: 110, r: 10, t: 44, b: 110 },
      }}
    />
  );
}

export function Histogram({ bins, counts, title, xLabel }: { bins: number[]; counts: number[]; title: string; xLabel: string }) {
  const t = useChartTheme();
  const centers = counts.map((_, i) => (bins[i] + bins[i + 1]) / 2);
  const widths = counts.map((_, i) => bins[i + 1] - bins[i]);
  return (
    <Chart
      label={title}
      height={300}
      minWidth={320}
      data={[
        {
          type: "bar",
          x: centers,
          y: counts,
          width: widths,
          marker: { color: t.series1, line: { color: t.surface, width: 1 } },
          customdata: counts.map((_, i) => [bins[i], bins[i + 1]]),
          hovertemplate: "%{customdata[0]:,.4g} – %{customdata[1]:,.4g}<br>%{y} 筆<extra></extra>",
        },
      ]}
      layout={{
        title: { text: title, font: { size: 14 } },
        xaxis: { title: { text: xLabel } },
        yaxis: { title: { text: "筆數" } },
        bargap: 0,
        showlegend: false,
      }}
    />
  );
}

export function TopBar({ items, title }: { items: { value: string; count: number }[]; title: string }) {
  const t = useChartTheme();
  const rev = [...items].reverse();
  return (
    <Chart
      label={title}
      height={Math.max(220, 28 * items.length + 90)}
      minWidth={320}
      data={[
        {
          type: "bar",
          orientation: "h",
          x: rev.map((d) => d.count),
          y: rev.map((d) => (d.value.length > 24 ? d.value.slice(0, 23) + "…" : d.value)),
          marker: { color: t.series1 },
          hovertemplate: "%{y}：%{x} 筆<extra></extra>",
        },
      ]}
      layout={{
        title: { text: title, font: { size: 14 } },
        xaxis: { title: { text: "筆數" } },
        yaxis: { automargin: true, type: "category" },
        showlegend: false,
        margin: { l: 120 },
      }}
    />
  );
}

export function PreviewTable({ rows, columns }: { rows: Record<string, unknown>[]; columns: string[] }) {
  return (
    <Table
      caption="資料預覽"
      rows={rows}
      columns={[
        { key: "#", header: "#", num: true, render: (_r, i) => i + 1 },
        ...columns.map((c) => ({
          key: c,
          header: c,
          render: (r: Record<string, unknown>) => {
            const v = r[c];
            if (v === null || v === undefined || v === "") return <span className="no">（空）</span>;
            return typeof v === "number" ? fmtAuto(v) : String(v);
          },
        })),
      ]}
    />
  );
}

