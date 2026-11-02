import { Component, lazy, Suspense, type ReactNode } from "react";
import { useChartTheme } from "./theme";

export type Trace = Record<string, unknown>;
export type Layout = Record<string, unknown>;

// Plotly 體積大，延遲載入（cartesian 精簡版涵蓋 scatter、bar、histogram、heatmap）
const Plot = lazy(async () => {
  const [{ default: factory }, plotly] = await Promise.all([
    import("react-plotly.js/factory"),
    import("plotly.js-cartesian-dist-min"),
  ]);
  return { default: factory((plotly as { default?: unknown }).default ?? plotly) };
});

class ChartBoundary extends Component<{ children: ReactNode }, { failed: boolean }> {
  state = { failed: false };
  static getDerivedStateFromError() {
    return { failed: true };
  }
  render() {
    return this.state.failed ? <p className="error">圖表載入失敗，請重新整理頁面。</p> : this.props.children;
  }
}

interface Props {
  data: Trace[];
  layout?: Layout;
  height?: number;
  /** 手機上圖表最小寬度；容器較窄時在容器內橫向捲動 */
  minWidth?: number;
  label: string;
}

function deepMerge(a: Layout, b: Layout): Layout {
  const out: Layout = { ...a };
  for (const [k, v] of Object.entries(b)) {
    const av = out[k];
    out[k] =
      v && typeof v === "object" && !Array.isArray(v) && av && typeof av === "object" && !Array.isArray(av)
        ? deepMerge(av as Layout, v as Layout)
        : v;
  }
  return out;
}

export default function Chart({ data, layout = {}, height = 380, minWidth = 520, label }: Props) {
  const t = useChartTheme();
  const axis = {
    gridcolor: t.border,
    zerolinecolor: t.border,
    linecolor: t.border,
    tickfont: { color: t.text2 },
    title: { font: { color: t.text2 } },
    automargin: true,
  };
  const base: Layout = {
    autosize: true,
    height,
    margin: { l: 56, r: 16, t: layout.showlegend === false ? 44 : 76, b: 48 },
    title: { x: 0, xanchor: "left", xref: "paper", y: 0.985, yanchor: "top", yref: "container" },
    paper_bgcolor: "rgba(0,0,0,0)",
    plot_bgcolor: "rgba(0,0,0,0)",
    font: { family: getComputedStyle(document.body).fontFamily, color: t.text, size: 12 },
    xaxis: axis,
    yaxis: axis,
    legend: { orientation: "h", x: 0, y: 1.02, yanchor: "bottom", font: { color: t.text2 }, bgcolor: "rgba(0,0,0,0)" },
    hoverlabel: { bgcolor: t.surface, bordercolor: t.border, font: { color: t.text } },
    hovermode: "closest",
  };
  return (
    <div className="chart-scroll" role="figure" aria-label={label}>
      <div className="chart-box" style={{ minWidth }}>
        <ChartBoundary>
          <Suspense fallback={<div className="chart-placeholder" style={{ height }}>圖表載入中…</div>}>
            <Plot
              data={data}
              layout={deepMerge(base, layout)}
              config={{ displaylogo: false, responsive: true, modeBarButtonsToRemove: ["lasso2d", "select2d"] }}
              style={{ width: "100%", height }}
              useResizeHandler
            />
          </Suspense>
        </ChartBoundary>
      </div>
    </div>
  );
}
