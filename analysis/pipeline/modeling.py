"""CRISP-DM ④ Modeling：OLS（SLR、MLR）與 Auto Regression，並組成 JSON 契約中的 models。"""
from __future__ import annotations

import warnings
from typing import Any

import numpy as np
import pandas as pd
import statsmodels.api as sm
from statsmodels.tsa.ar_model import AutoReg, ar_select_order

from .config import DatasetConfig, PipelineError
from .evaluation import cross_validate, even_sample_indices, regression_metrics, residual_diagnostics
from .preparation import Prepared

Z_95 = 1.959963984540054
BAND_POINTS = 100


# ---------------------------------------------------------------- OLS

def fit_ols(X: pd.DataFrame, y: pd.Series, cols: list[str]):
    return sm.OLS(y.values, sm.add_constant(X[cols], has_constant="add")).fit()


def predict_ols(res, X: pd.DataFrame, cols: list[str]) -> pd.DataFrame:
    frame = res.get_prediction(sm.add_constant(X[cols], has_constant="add")).summary_frame(alpha=0.05)
    return frame[["mean", "mean_ci_lower", "mean_ci_upper", "obs_ci_lower", "obs_ci_upper"]].reset_index(drop=True)


def coef_table(res, names: list[str]) -> list[dict[str, float]]:
    ci = np.asarray(res.conf_int(alpha=0.05))
    params, bse = np.asarray(res.params), np.asarray(res.bse)
    tvals, pvals = np.asarray(res.tvalues), np.asarray(res.pvalues)
    return [
        {
            "name": name,
            "coef": float(params[i]),
            "std_err": float(bse[i]),
            "t": float(tvals[i]),
            "p": float(pvals[i]),
            "ci_low": float(ci[i, 0]),
            "ci_high": float(ci[i, 1]),
        }
        for i, name in enumerate(names)
    ]


# ---------------------------------------------------------------- AR

def select_ar_order(series_train: pd.Series, maxlag: int) -> int:
    sel = ar_select_order(series_train.values, maxlag=maxlag, ic="aic", trend="c")
    lags = sel.ar_lags or []
    return int(max(1, max(lags) if lags else 1))


def fit_ar(series_train: np.ndarray, p: int):
    return AutoReg(np.asarray(series_train, dtype=float), lags=p, trend="c").fit()


def ar_one_step(res, full: np.ndarray, start: int, end: int, p: int) -> np.ndarray:
    """對 full[start:end] 做一步預測，每一點使用實際的前 p 期值。"""
    const, phi = res.params[0], res.params[1:]
    preds = np.empty(end - start)
    for j, t in enumerate(range(start, end)):
        lags = full[t - p:t][::-1]  # y_{t-1}, ..., y_{t-p}
        preds[j] = const + float(np.dot(phi, lags))
    return preds


def ar_resid_std(res, p: int) -> float:
    resid = np.asarray(res.resid)
    return float(np.sqrt(np.sum(resid**2) / (len(resid) - (p + 1))))


# ---------------------------------------------------------------- 組裝

def _inv(cfg: DatasetConfig):
    return np.exp if cfg.log_target else (lambda a: np.asarray(a, dtype=float))


def _points(x, actual, pred, ci_low, ci_high, pi_low, pi_high) -> list[dict[str, Any]]:
    return [
        {
            "x": x[i],
            "actual": float(actual[i]),
            "pred": float(pred[i]),
            "ci_low": None if ci_low is None else float(ci_low[i]),
            "ci_high": None if ci_high is None else float(ci_high[i]),
            "pi_low": float(pi_low[i]),
            "pi_high": float(pi_high[i]),
        }
        for i in range(len(pred))
    ]


def build_ols_model(
    model_id: str, label: str, mtype: str, cols: list[str], prep: Prepared, cfg: DatasetConfig,
    feature_labels: dict[str, str],
) -> dict[str, Any]:
    inv = _inv(cfg)
    res = fit_ols(prep.X_train, prep.y_train, cols)
    frame = predict_ols(res, prep.X_test, cols)

    pred_m = frame["mean"].values
    pred_raw = inv(pred_m)
    ci_low, ci_high = inv(frame["mean_ci_lower"].values), inv(frame["mean_ci_upper"].values)
    pi_low, pi_high = inv(frame["obs_ci_lower"].values), inv(frame["obs_ci_upper"].values)
    actual_raw = prep.y_test_raw.values

    metrics = regression_metrics(prep.y_test.values, pred_m, actual_raw, pred_raw, pi_low, pi_high, k=len(cols))

    def fit_predict(tr, te):
        # 時間序列交叉驗證的前幾折可能缺少部分月份，虛擬變數全為 0 會造成 rank-deficient，屬預期情況
        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            r = fit_ols(prep.X_train.iloc[tr], prep.y_train.iloc[tr], cols)
        p = r.predict(sm.add_constant(prep.X_train.iloc[te][cols], has_constant="add"))
        return prep.y_train.iloc[te].values, np.asarray(p)

    cv = cross_validate(len(prep.X_train), cfg.cv, fit_predict)

    # 預測點：SLR 依特徵值排序，MLR 依預測值排序；House 均勻抽樣至 max_points
    if mtype == "slr":
        f = cols[0]
        order = np.argsort(prep.X_test[f].values, kind="mergesort")
        x_kind, x_label = "feature", feature_labels.get(f, f)
    else:
        order = np.argsort(pred_m, kind="mergesort")
        x_kind, x_label = "index", "測試集樣本（依預測值由小到大排序）"
    order = order[even_sample_indices(len(order), cfg.max_points)]

    if mtype == "slr":
        xs = prep.X_test[cols[0]].values[order].tolist()
    else:
        # x 為該點在完整測試集中依預測值排序的名次（抽樣後仍保留原名次）
        rank = np.empty(len(pred_m), dtype=int)
        rank[np.argsort(pred_m, kind="mergesort")] = np.arange(1, len(pred_m) + 1)
        xs = rank[order].tolist()

    prediction: dict[str, Any] = {
        "x_kind": x_kind,
        "x_label": x_label,
        "y_label": cfg.target,
        "n_total": int(len(pred_m)),
        "points": _points(
            xs, actual_raw[order], pred_raw[order], ci_low[order], ci_high[order], pi_low[order], pi_high[order]
        ),
    }

    if mtype == "slr":
        f = cols[0]
        lo, hi = float(prep.X_test[f].min()), float(prep.X_test[f].max())
        grid = pd.DataFrame({f: np.linspace(lo, hi, BAND_POINTS)})
        g = predict_ols(res, grid, cols)
        prediction["band"] = [
            {
                "x": float(grid[f].iloc[i]),
                "pred": float(inv(g["mean"].iloc[i])),
                "ci_low": float(inv(g["mean_ci_lower"].iloc[i])),
                "ci_high": float(inv(g["mean_ci_upper"].iloc[i])),
                "pi_low": float(inv(g["obs_ci_lower"].iloc[i])),
                "pi_high": float(inv(g["obs_ci_upper"].iloc[i])),
            }
            for i in range(BAND_POINTS)
        ]

    residuals = residual_diagnostics(res.fittedvalues, res.resid, cfg.max_points)
    residuals["source"] = "train"
    residuals["scale"] = prep.target_label

    return {
        "id": model_id,
        "label": label,
        "type": mtype,
        "is_best": False,
        "features": list(cols),
        "n_train": int(len(prep.X_train)),
        "n_test": int(len(prep.X_test)),
        "train_r2": float(res.rsquared),
        "train_adj_r2": float(res.rsquared_adj),
        "aic": float(res.aic),
        "coefficients": coef_table(res, ["const"] + list(cols)),
        "metrics": metrics,
        "cv": cv,
        "prediction": prediction,
        "residuals": residuals,
    }


def build_ar_model(prep: Prepared, cfg: DatasetConfig) -> dict[str, Any]:
    series = prep.extra["series"].values.astype(float)
    dates = prep.extra["dates"]
    n_train = prep.extra["n_train"]
    train = series[:n_train]

    p = select_ar_order(pd.Series(train), cfg.ar_maxlag)
    if not (1 <= p <= cfg.ar_maxlag):
        raise PipelineError(f"AR 階數 {p} 超出 1–{cfg.ar_maxlag}")
    res = fit_ar(train, p)
    s = ar_resid_std(res, p)

    pred = ar_one_step(res, series, n_train, len(series), p)
    actual = series[n_train:]
    pi_low, pi_high = pred - Z_95 * s, pred + Z_95 * s
    metrics = regression_metrics(actual, pred, actual, pred, pi_low, pi_high, k=p)

    def fit_predict(tr, te):
        r = fit_ar(train[: tr[-1] + 1], p)
        return train[te], ar_one_step(r, train, te[0], te[-1] + 1, p)

    cv = cross_validate(n_train, "timeseries", fit_predict)

    names = ["const"] + [f"cnt(t−{i})" for i in range(1, p + 1)]
    ci = np.asarray(res.conf_int(alpha=0.05))
    coefficients = [
        {
            "name": names[i],
            "coef": float(res.params[i]),
            "std_err": float(res.bse[i]),
            "t": float(res.tvalues[i]),
            "p": float(res.pvalues[i]),
            "ci_low": float(ci[i, 0]),
            "ci_high": float(ci[i, 1]),
        }
        for i in range(len(names))
    ]

    date_str = dates.dt.strftime("%Y-%m-%d").tolist()
    fitted = np.asarray(res.fittedvalues)
    residuals = residual_diagnostics(fitted, np.asarray(res.resid), cfg.max_points)
    residuals["source"] = "train"
    residuals["scale"] = cfg.target

    return {
        "id": "ar",
        "label": f"Auto Regression AR({p})",
        "type": "ar",
        "is_best": False,
        "features": names[1:],
        "ar_order": p,
        "resid_std": s,
        "n_train": int(n_train),
        "n_test": int(len(actual)),
        "aic": float(res.aic),
        "coefficients": coefficients,
        "metrics": metrics,
        "cv": cv,
        "prediction": {
            "x_kind": "date",
            "x_label": "日期",
            "y_label": cfg.target,
            "n_total": int(len(actual)),
            "interval_note": "AR 只提供預測區間：一步預測 ± 1.96 × 訓練殘差標準差",
            "train_points": [{"x": date_str[i], "actual": float(series[i])} for i in range(n_train)],
            "points": _points(date_str[n_train:], actual, pred, None, None, pi_low, pi_high),
        },
        "residuals": residuals,
    }


def build_models(prep: Prepared, cfg: DatasetConfig, selection: dict[str, Any], feature_labels: dict[str, str]) -> list[dict[str, Any]]:
    if cfg.slr_feature == "auto":
        slr_feature = selection["correlation"][0]["feature"]
    else:
        slr_feature = cfg.slr_feature
    if slr_feature not in prep.features:
        raise PipelineError(f"SLR 特徵 {slr_feature} 不在準備後的特徵中")

    final = selection["final_features"]
    models = [
        build_ols_model("slr", f"單純線性回歸（{slr_feature}）", "slr", [slr_feature], prep, cfg, feature_labels),
        build_ols_model("mlr_all", f"多元線性回歸（全部 {len(prep.features)} 個特徵）", "mlr", prep.features, prep, cfg, feature_labels),
        build_ols_model("mlr_selected", f"多元線性回歸（選擇後 {len(final)} 個特徵）", "mlr", final, prep, cfg, feature_labels),
    ]
    if cfg.ar:
        models.append(build_ar_model(prep, cfg))

    best = max(models, key=lambda m: m["metrics"]["r2"])
    best["is_best"] = True
    if cfg.log_target:
        for m in models:
            m["metrics_note"] = "R²、Adjusted R² 與交叉驗證 R² 以 log(price) 計算；RMSE、MAE 以原始價格（美元）計算"
    return models
