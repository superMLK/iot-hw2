import Chart, { type Layout, type Trace } from "./Chart";
import { alpha, bandAlpha, useChartTheme, type ChartTheme } from "./theme";
import type { Meta, Model } from "../types/dataset";

const CI_NAME = "95% 信賴區間";
const PI_NAME = "95% 預測區間";

/** 以兩條線（下緣、上緣 + fill: tonexty）畫區間帶 */
function band(x: (number | string)[], lo: number[], hi: number[], color: string, a: number, name: string, group: string): Trace[] {
  return [
    { type: "scatter", mode: "lines", x, y: lo, line: { width: 0, color }, hoverinfo: "skip", showlegend: false, legendgroup: group },
    {
      type: "scatter",
      mode: "lines",
      x,
      y: hi,
      fill: "tonexty",
      fillcolor: alpha(color, a),
      line: { width: 0, color },
      name,
      legendgroup: group,
      hoverinfo: "skip",
    },
  ];
}

// 對數價格軸：固定 1-2-5 刻度，避免次刻度擠在一起
const PRICE_TICKS = [5e4, 1e5, 2e5, 5e5, 1e6, 2e6, 5e6, 1e7, 2e7];
const priceText = (v: number) => (v >= 1e6 ? `$${v / 1e6}M` : `$${v / 1e3}K`);

export function priceAxis(title: string): Layout {
  return { title: { text: `${title}（美元，對數軸）` }, type: "log", tickvals: PRICE_TICKS, ticktext: PRICE_TICKS.map(priceText) };
}

function yAxis(meta: Meta, title: string): Layout {
  return meta.log_target ? priceAxis(title) : { title: { text: title } };
}

function valueFmt(meta: Meta): string {
  return meta.log_target ? "$%{y:,.0f}" : "%{y:,.0f}";
}

function slrTraces(m: Model, meta: Meta, t: ChartTheme): Trace[] {
  const b = m.prediction.band ?? [];
  const bx = b.map((p) => p.x);
  const pts = m.prediction.points;
  return [
    ...band(bx, b.map((p) => p.pi_low), b.map((p) => p.pi_high), t.series1, bandAlpha(t).pi, PI_NAME, "pi"),
    ...band(bx, b.map((p) => p.ci_low), b.map((p) => p.ci_high), t.series1, bandAlpha(t).ci, CI_NAME, "ci"),
    {
      type: "scatter",
      mode: "markers",
      x: pts.map((p) => p.x),
      y: pts.map((p) => p.actual),
      marker: { size: 7, color: alpha(t.neutral, 0.7), line: { color: t.surface, width: 1 } },
      name: "實際值（測試集）",
      hovertemplate: `x = %{x:.4g}<br>實際值 ${valueFmt(meta)}<extra></extra>`,
    },
    {
      type: "scatter",
      mode: "lines",
      x: bx,
      y: b.map((p) => p.pred),
      line: { color: t.series2, width: 2.5 },
      name: "回歸線",
      customdata: b.map((p) => [p.ci_low, p.ci_high, p.pi_low, p.pi_high]),
      hovertemplate:
        `x = %{x:.4g}<br>預測 ${valueFmt(meta)}<br>信賴區間 [%{customdata[0]:,.0f}, %{customdata[1]:,.0f}]` +
        `<br>預測區間 [%{customdata[2]:,.0f}, %{customdata[3]:,.0f}]<extra></extra>`,
    },
  ];
}

function mlrTraces(m: Model, meta: Meta, t: ChartTheme): Trace[] {
  const pts = m.prediction.points;
  const x = pts.map((p) => p.x);
  return [
    ...band(x, pts.map((p) => p.pi_low), pts.map((p) => p.pi_high), t.series1, bandAlpha(t).pi, PI_NAME, "pi"),
    ...band(x, pts.map((p) => p.ci_low as number), pts.map((p) => p.ci_high as number), t.series1, bandAlpha(t).ci, CI_NAME, "ci"),
    {
      type: "scatter",
      mode: "markers",
      x,
      y: pts.map((p) => p.actual),
      marker: { size: 6, color: alpha(t.neutral, 0.65) },
      name: "實際值",
      hovertemplate: `第 %{x} 名<br>實際值 ${valueFmt(meta)}<extra></extra>`,
    },
    {
      type: "scatter",
      mode: "lines",
      x,
      y: pts.map((p) => p.pred),
      line: { color: t.series2, width: 2.5 },
      name: "預測值",
      customdata: pts.map((p) => [p.ci_low, p.ci_high, p.pi_low, p.pi_high]),
      hovertemplate:
        `第 %{x} 名<br>預測 ${valueFmt(meta)}<br>信賴區間 [%{customdata[0]:,.0f}, %{customdata[1]:,.0f}]` +
        `<br>預測區間 [%{customdata[2]:,.0f}, %{customdata[3]:,.0f}]<extra></extra>`,
    },
  ];
}

function arTraces(m: Model, t: ChartTheme): Trace[] {
  const pts = m.prediction.points;
  const x = pts.map((p) => p.x);
  const train = m.prediction.train_points ?? [];
  return [
    {
      type: "scatter",
      mode: "lines",
      x: train.map((p) => p.x),
      y: train.map((p) => p.actual),
      line: { color: alpha(t.neutral, 0.55), width: 1.2 },
      name: "訓練期實際值",
      hovertemplate: "%{x}<br>實際值 %{y:,.0f}<extra></extra>",
    },
    ...band(x, pts.map((p) => p.pi_low), pts.map((p) => p.pi_high), t.series1, bandAlpha(t).pi, PI_NAME, "pi"),
    {
      type: "scatter",
      mode: "lines+markers",
      x,
      y: pts.map((p) => p.actual),
      line: { color: t.neutral, width: 1.5 },
      marker: { size: 4, color: t.neutral },
      name: "測試期實際值",
      hovertemplate: "%{x}<br>實際值 %{y:,.0f}<extra></extra>",
    },
    {
      type: "scatter",
      mode: "lines",
      x,
      y: pts.map((p) => p.pred),
      line: { color: t.series2, width: 2.2 },
      name: "一步預測",
      customdata: pts.map((p) => [p.pi_low, p.pi_high]),
      hovertemplate: "%{x}<br>預測 %{y:,.0f}<br>預測區間 [%{customdata[0]:,.0f}, %{customdata[1]:,.0f}]<extra></extra>",
    },
  ];
}

export function PredictionChart({ model, meta }: { model: Model; meta: Meta }) {
  const t = useChartTheme();
  const pred = model.prediction;
  const traces = model.type === "slr" ? slrTraces(model, meta, t) : model.type === "ar" ? arTraces(model, t) : mlrTraces(model, meta, t);
  const xaxis: Layout =
    pred.x_kind === "date" ? { title: { text: "日期" }, type: "date" } : { title: { text: pred.x_label } };
  return (
    <Chart
      label={`${model.label} 預測圖`}
      height={440}
      minWidth={560}
      data={traces}
      layout={{
        title: { text: `${model.label}：測試集預測`, font: { size: 14 } },
        xaxis,
        yaxis: yAxis(meta, pred.y_label),
        hovermode: pred.x_kind === "feature" ? "closest" : "x unified",
      }}
    />
  );
}

export function ActualVsPredicted({ model, meta }: { model: Model; meta: Meta }) {
  const t = useChartTheme();
  const pts = model.prediction.points;
  const all = pts.flatMap((p) => [p.actual, p.pred]);
  const lo = Math.min(...all);
  const hi = Math.max(...all);
  const axis = (title: string): Layout => (meta.log_target ? priceAxis(title) : { title: { text: title } });
  return (
    <Chart
      label={`${model.label} 實際值與預測值散佈圖`}
      height={420}
      minWidth={380}
      data={[
        {
          type: "scatter",
          mode: "markers",
          x: pts.map((p) => p.pred),
          y: pts.map((p) => p.actual),
          marker: { size: 6, color: alpha(t.neutral, 0.65) },
          name: "測試集樣本",
          hovertemplate: "預測 %{x:,.0f}<br>實際 %{y:,.0f}<extra></extra>",
        },
        {
          type: "scatter",
          mode: "lines",
          x: [lo, hi],
          y: [lo, hi],
          line: { color: t.series2, width: 2, dash: "dash" },
          name: "y = x（完美預測）",
          hoverinfo: "skip",
        },
      ]}
      layout={{
        title: { text: "實際值 vs 預測值", font: { size: 14 } },
        xaxis: axis("預測值"),
        yaxis: axis("實際值"),
      }}
    />
  );
}

export function ResidualCharts({ model }: { model: Model }) {
  const t = useChartTheme();
  const r = model.residuals;
  const qlo = Math.min(...r.qq_theoretical);
  const qhi = Math.max(...r.qq_theoretical);
  const note = `殘差來源：訓練集（${r.scale} 尺度）${r.fitted.length < r.n_total ? `，共 ${r.n_total} 筆、均勻抽樣顯示 ${r.fitted.length} 筆` : ""}`;
  return (
    <>
      <p className="note">{note}</p>
      <div className="grid-2">
        <Chart
          label="殘差對預測值"
          height={320}
          minWidth={320}
          data={[
            {
              type: "scatter",
              mode: "markers",
              x: r.fitted,
              y: r.resid,
              marker: { size: 5, color: alpha(t.neutral, 0.6) },
              name: "殘差",
              hovertemplate: "預測值 %{x:.4g}<br>殘差 %{y:.4g}<extra></extra>",
            },
          ]}
          layout={{
            title: { text: "殘差 vs 預測值", font: { size: 14 } },
            xaxis: { title: { text: "預測值" } },
            yaxis: { title: { text: "殘差" }, zeroline: true, zerolinecolor: t.series2, zerolinewidth: 1.5 },
            showlegend: false,
          }}
        />
        <Chart
          label="Q-Q 圖"
          height={320}
          minWidth={320}
          data={[
            {
              type: "scatter",
              mode: "markers",
              x: r.qq_theoretical,
              y: r.qq_sample,
              marker: { size: 5, color: alpha(t.neutral, 0.6) },
              name: "標準化殘差",
              hovertemplate: "理論 %{x:.2f}<br>樣本 %{y:.2f}<extra></extra>",
            },
            { type: "scatter", mode: "lines", x: [qlo, qhi], y: [qlo, qhi], line: { color: t.series2, width: 1.5 }, name: "常態參考線", hoverinfo: "skip" },
          ]}
          layout={{
            title: { text: "常態 Q-Q 圖", font: { size: 14 } },
            xaxis: { title: { text: "理論分位數" } },
            yaxis: { title: { text: "標準化殘差分位數" } },
            showlegend: false,
          }}
        />
        <Chart
          label="殘差直方圖"
          height={320}
          minWidth={320}
          data={[
            {
              type: "histogram",
              x: r.resid,
              nbinsx: 30,
              marker: { color: t.series1, line: { color: t.surface, width: 1 } },
              hovertemplate: "%{x}<br>%{y} 筆<extra></extra>",
            },
          ]}
          layout={{
            title: { text: "殘差分布", font: { size: 14 } },
            xaxis: { title: { text: "殘差" } },
            yaxis: { title: { text: "筆數" } },
            showlegend: false,
            bargap: 0.02,
          }}
        />
      </div>
    </>
  );
}
