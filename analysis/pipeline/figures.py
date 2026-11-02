"""輸出報告與資訊圖表用的 PNG（matplotlib，Agg 後端）。"""
from __future__ import annotations

import logging
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402

logging.getLogger("matplotlib.font_manager").setLevel(logging.ERROR)

plt.rcParams.update(
    {
        "font.family": "sans-serif",
        "font.sans-serif": ["PingFang TC", "Heiti TC", "Noto Sans CJK TC", "Microsoft JhengHei", "Arial Unicode MS", "DejaVu Sans"],
        "axes.unicode_minus": False,
        "figure.dpi": 100,
        "savefig.dpi": 200,
        "axes.spines.top": False,
        "axes.spines.right": False,
        "axes.grid": True,
        "grid.alpha": 0.25,
        "svg.hashsalt": "crisp-dm",
    }
)

BAND = "#2a6fdb"      # 區間帶：同一色相，以透明度區分
CI_ALPHA = 0.35
PI_ALPHA = 0.15
ACTUAL = "#5f6b7a"
PRED = "#e0661b"
TRAIN = "#9aa5b1"

PNG_META = {"Software": None}


def _save(fig, path: Path) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(path, bbox_inches="tight", metadata=PNG_META)
    plt.close(fig)
    return path.name


def _xs(points, kind):
    if kind == "date":
        return np.array(points, dtype="datetime64[D]")
    return np.asarray(points, dtype=float)


def _price_axis(ax, which: str = "y") -> None:
    """House 價格跨度大，改用對數軸，刻度仍以美元顯示。"""
    from matplotlib.ticker import FuncFormatter

    fmt = FuncFormatter(lambda v, _: f"${v / 1e6:.1f}M" if v >= 1e6 else f"${v / 1e3:.0f}K")
    for w in which:
        getattr(ax, f"set_{w}scale")("log")
        getattr(ax, f"{w}axis").set_major_formatter(fmt)
        getattr(ax, f"{w}axis").set_minor_formatter(FuncFormatter(lambda v, _: ""))


def prediction_figure(model: dict[str, Any], ds_name: str, path: Path, compact: bool = False, log_axis: bool = False) -> str:
    pred = model["prediction"]
    pts = pred["points"]
    kind = pred["x_kind"]
    fig, ax = plt.subplots(figsize=(7.5, 3.2) if compact else (9, 4.8))

    if kind == "feature" and pred.get("band"):
        band = pred["band"]
        bx = np.array([b["x"] for b in band])
        ax.fill_between(bx, [b["pi_low"] for b in band], [b["pi_high"] for b in band], color=BAND, alpha=PI_ALPHA, lw=0, label="95% 預測區間")
        ax.fill_between(bx, [b["ci_low"] for b in band], [b["ci_high"] for b in band], color=BAND, alpha=CI_ALPHA, lw=0, label="95% 信賴區間")
        ax.scatter([p["x"] for p in pts], [p["actual"] for p in pts], s=10, color=ACTUAL, alpha=0.6, label="實際值（測試集）")
        ax.plot(bx, [b["pred"] for b in band], color=PRED, lw=2, label="回歸線")
    elif kind == "date":
        tr = pred.get("train_points") or []
        if tr and not compact:
            ax.plot(_xs([p["x"] for p in tr], kind), [p["actual"] for p in tr], color=TRAIN, lw=1, label="訓練期實際值")
        x = _xs([p["x"] for p in pts], kind)
        ax.fill_between(x, [p["pi_low"] for p in pts], [p["pi_high"] for p in pts], color=BAND, alpha=PI_ALPHA, lw=0, label="95% 預測區間")
        ax.plot(x, [p["actual"] for p in pts], color=ACTUAL, lw=1.2, label="測試期實際值")
        ax.plot(x, [p["pred"] for p in pts], color=PRED, lw=1.6, label="一步預測")
        fig.autofmt_xdate()
    else:
        x = _xs([p["x"] for p in pts], kind)
        ax.fill_between(x, [p["pi_low"] for p in pts], [p["pi_high"] for p in pts], color=BAND, alpha=PI_ALPHA, lw=0, label="95% 預測區間")
        ax.fill_between(x, [p["ci_low"] for p in pts], [p["ci_high"] for p in pts], color=BAND, alpha=CI_ALPHA, lw=0, label="95% 信賴區間")
        ax.scatter(x, [p["actual"] for p in pts], s=8, color=ACTUAL, alpha=0.6, label="實際值")
        ax.plot(x, [p["pred"] for p in pts], color=PRED, lw=1.8, label="預測值")

    ax.set_xlabel(pred["x_label"])
    ax.set_ylabel(pred.get("y_label", "") + ("（美元，對數軸）" if log_axis else ""))
    if log_axis:
        _price_axis(ax, "y")
    if not compact:
        ax.set_title(f"{ds_name}：{model['label']}")
    ax.legend(loc="upper left", fontsize=8, frameon=False)
    return _save(fig, path)


def actual_vs_pred_figure(model: dict[str, Any], ds_name: str, path: Path, log_axis: bool = False) -> str:
    pts = model["prediction"]["points"]
    a = np.array([p["actual"] for p in pts])
    p_ = np.array([p["pred"] for p in pts])
    lo, hi = float(min(a.min(), p_.min())), float(max(a.max(), p_.max()))
    fig, ax = plt.subplots(figsize=(5.2, 5))
    ax.scatter(p_, a, s=10, color=ACTUAL, alpha=0.6, label="測試集樣本")
    ax.plot([lo, hi], [lo, hi], color=PRED, lw=1.5, ls="--", label="y = x")
    ax.set_xlabel("預測值" + ("（對數軸）" if log_axis else ""))
    ax.set_ylabel("實際值" + ("（對數軸）" if log_axis else ""))
    if log_axis:
        _price_axis(ax, "xy")
    ax.set_title(f"{ds_name}：實際值 vs 預測值（{model['label']}）", fontsize=10)
    ax.legend(frameon=False, fontsize=8)
    return _save(fig, path)


def residual_figure(model: dict[str, Any], ds_name: str, path: Path) -> str:
    r = model["residuals"]
    fig, axes = plt.subplots(1, 3, figsize=(12, 3.6))
    axes[0].scatter(r["fitted"], r["resid"], s=8, color=ACTUAL, alpha=0.6)
    axes[0].axhline(0, color=PRED, lw=1)
    axes[0].set_xlabel("預測值（訓練集）")
    axes[0].set_ylabel("殘差")
    axes[0].set_title("殘差 vs 預測值")
    axes[1].scatter(r["qq_theoretical"], r["qq_sample"], s=8, color=ACTUAL, alpha=0.6)
    lim = [min(r["qq_theoretical"]), max(r["qq_theoretical"])]
    axes[1].plot(lim, lim, color=PRED, lw=1)
    axes[1].set_xlabel("理論分位數")
    axes[1].set_ylabel("標準化殘差分位數")
    axes[1].set_title("常態 Q-Q 圖")
    axes[2].hist(r["resid"], bins=30, color=BAND, alpha=0.6)
    axes[2].set_xlabel("殘差")
    axes[2].set_title("殘差分布")
    fig.suptitle(f"{ds_name}：{model['label']} 殘差診斷", fontsize=11)
    fig.tight_layout()
    return _save(fig, path)


def correlation_figure(du: dict[str, Any], ds_name: str, path: Path) -> str:
    labels = du["correlation"]["labels"]
    m = np.array(du["correlation"]["matrix"], dtype=float)
    n = len(labels)
    fig, ax = plt.subplots(figsize=(0.45 * n + 2, 0.45 * n + 1.5))
    im = ax.imshow(m, cmap="RdBu_r", vmin=-1, vmax=1)
    ax.set_xticks(range(n), labels, rotation=90, fontsize=8)
    ax.set_yticks(range(n), labels, fontsize=8)
    ax.grid(False)
    fig.colorbar(im, ax=ax, shrink=0.8, label="相關係數 r")
    ax.set_title(f"{ds_name}：數值欄相關係數矩陣")
    return _save(fig, path)


def target_figure(du: dict[str, Any], target: str, ds_name: str, path: Path) -> str:
    td = du["target_distribution"]
    edges = np.array(td["bins"])
    fig, ax = plt.subplots(figsize=(7, 3.4))
    ax.bar(edges[:-1], td["counts"], width=np.diff(edges), align="edge", color=BAND, alpha=0.7)
    ax.set_xlabel(target)
    ax.set_ylabel("筆數")
    ax.set_title(f"{ds_name}：目標變數 {target} 分布")
    return _save(fig, path)


def write_all(result: dict[str, Any], out_dir: Path) -> list[str]:
    ds = result["meta"]["id"]
    log_axis = bool(result["meta"].get("log_target"))
    name = result["meta"]["name"]
    files = [
        correlation_figure(result["data_understanding"], name, out_dir / f"{ds}_correlation.png"),
        target_figure(result["data_understanding"], result["meta"]["target"], name, out_dir / f"{ds}_target_distribution.png"),
    ]
    for m in result["models"]:
        files.append(prediction_figure(m, name, out_dir / f"{ds}_pred_{m['id']}.png", log_axis=log_axis))
        files.append(residual_figure(m, name, out_dir / f"{ds}_residuals_{m['id']}.png"))
        if m["type"] == "mlr":
            files.append(actual_vs_pred_figure(m, name, out_dir / f"{ds}_actual_vs_pred_{m['id']}.png", log_axis=log_axis))
        if m["is_best"]:
            files.append(prediction_figure(m, name, out_dir / f"{ds}_infographic_pred.png", compact=True, log_axis=log_axis))
    return files
