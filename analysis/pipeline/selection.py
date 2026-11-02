"""特徵選擇：相關係數篩選、VIF、雙向逐步回歸（只用訓練集）。"""
from __future__ import annotations

import math
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.stats.outliers_influence import variance_inflation_factor

CORR_MIN_ABS_R = 0.1
HIGH_CORR_PAIR = 0.8
VIF_THRESHOLD = 10.0


def correlation_filter(X: pd.DataFrame, y: pd.Series) -> dict[str, Any]:
    abs_r = X.apply(lambda c: abs(np.corrcoef(c, y)[0, 1]) if c.std() > 0 else 0.0)
    abs_r = abs_r.fillna(0.0)
    corr = X.corr().fillna(0.0)

    pairs = []
    cols = list(X.columns)
    for i, a in enumerate(cols):
        for b in cols[i + 1:]:
            r = float(corr.loc[a, b])
            if abs(r) > HIGH_CORR_PAIR:
                pairs.append({"a": a, "b": b, "r": r})
    pairs.sort(key=lambda p: -abs(p["r"]))

    kept = {f: bool(abs_r[f] >= CORR_MIN_ABS_R) for f in cols}
    for p in pairs:
        a, b = p["a"], p["b"]
        if kept[a] and kept[b]:
            weaker = a if abs_r[a] < abs_r[b] else b
            kept[weaker] = False
            p["dropped"] = weaker

    table = [
        {"feature": f, "abs_r": float(abs_r[f]), "kept": kept[f]}
        for f in sorted(cols, key=lambda f: -abs_r[f])
    ]
    return {"table": table, "pairs": pairs, "kept": kept}


def _vif_table(X: pd.DataFrame) -> dict[str, float]:
    Xc = sm.add_constant(X, has_constant="add").values
    out = {}
    with np.errstate(divide="ignore", invalid="ignore"):
        for i, col in enumerate(X.columns, start=1):
            v = variance_inflation_factor(Xc, i)
            out[col] = math.inf if (v is None or not np.isfinite(v)) else float(v)
    return out


def vif_filter(X: pd.DataFrame) -> dict[str, Any]:
    remaining = list(X.columns)
    initial = _vif_table(X[remaining])
    rounds = []
    current = initial
    while remaining:
        worst = max(remaining, key=lambda c: current[c])
        if current[worst] <= VIF_THRESHOLD:
            break
        remaining = [c for c in remaining if c != worst]
        rounds.append(
            {
                "round": len(rounds) + 1,
                "removed": worst,
                "vif": None if math.isinf(current[worst]) else current[worst],
                "vif_is_inf": math.isinf(current[worst]),
                "remaining": list(remaining),
            }
        )
        current = _vif_table(X[remaining]) if remaining else {}
    return {
        "initial": [{"feature": f, "vif": None if math.isinf(v) else v} for f, v in initial.items()],
        "rounds": rounds,
        "final": [{"feature": f, "vif": current[f]} for f in remaining],
        "kept": remaining,
    }


def _aic(X: pd.DataFrame, y: pd.Series, cols: list[str]) -> float:
    design = sm.add_constant(X[cols], has_constant="add") if cols else np.ones((len(y), 1))
    return float(sm.OLS(y.values, design).fit().aic)


def stepwise(X: pd.DataFrame, y: pd.Series, candidates: list[str], max_steps: int = 200) -> dict[str, Any]:
    """從只有常數項的模型開始，每一步選擇讓 AIC 下降最多的加入或移除動作。"""
    selected: list[str] = []
    current_aic = _aic(X, y, selected)
    start_aic = current_aic
    steps = []
    for _ in range(max_steps):
        best = None  # (aic, action, feature)
        for f in candidates:
            if f in selected:
                continue
            a = _aic(X, y, selected + [f])
            if best is None or a < best[0] - 1e-9:
                best = (a, "add", f)
        for f in selected:
            a = _aic(X, y, [c for c in selected if c != f])
            if best is None or a < best[0] - 1e-9:
                best = (a, "remove", f)
        if best is None or best[0] >= current_aic - 1e-9:
            break
        current_aic, action, feat = best
        if action == "add":
            selected.append(feat)
        else:
            selected.remove(feat)
        steps.append({"step": len(steps) + 1, "action": action, "feature": feat, "aic": current_aic})
    order = {f: i for i, f in enumerate(candidates)}
    return {"start_aic": start_aic, "steps": steps, "kept": sorted(selected, key=lambda f: order[f])}


def select_features(X_train: pd.DataFrame, y_train: pd.Series) -> dict[str, Any]:
    corr = correlation_filter(X_train, y_train)
    vif = vif_filter(X_train)
    step = stepwise(X_train, y_train, vif["kept"])
    vif_kept = set(vif["kept"])
    step_kept = set(step["kept"])
    comparison = [
        {
            "feature": f,
            "corr_kept": corr["kept"][f],
            "vif_kept": f in vif_kept,
            "stepwise_kept": f in step_kept,
        }
        for f in X_train.columns
    ]
    return {
        "correlation": [{"feature": r["feature"], "abs_r": r["abs_r"]} for r in corr["table"]],
        "correlation_rule": {"min_abs_r": CORR_MIN_ABS_R, "high_corr_pair": HIGH_CORR_PAIR},
        "high_corr_pairs": corr["pairs"],
        "vif_threshold": VIF_THRESHOLD,
        "vif_initial": vif["initial"],
        "vif_rounds": vif["rounds"],
        "vif_removed": [r["removed"] for r in vif["rounds"]],
        "vif_final": vif["final"],
        "stepwise_start_aic": step["start_aic"],
        "stepwise_steps": step["steps"],
        "comparison": comparison,
        "final_features": step["kept"],
        "n_candidates": int(X_train.shape[1]),
        "n_corr_kept": int(sum(corr["kept"].values())),
        "n_after_vif": len(vif["kept"]),
        "n_final": len(step["kept"]),
    }
