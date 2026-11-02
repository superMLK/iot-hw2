"""CRISP-DM ⑤ Evaluation：指標、交叉驗證、殘差診斷、抽樣。"""
from __future__ import annotations

from typing import Callable

import numpy as np
from scipy import stats
from sklearn.model_selection import KFold, TimeSeriesSplit

from .config import RANDOM_STATE

N_SPLITS = 5


def r2_score(y_true, y_pred) -> float:
    y_true = np.asarray(y_true, dtype=float)
    y_pred = np.asarray(y_pred, dtype=float)
    ss_res = float(np.sum((y_true - y_pred) ** 2))
    ss_tot = float(np.sum((y_true - y_true.mean()) ** 2))
    return 1.0 - ss_res / ss_tot


def adjusted_r2(r2: float, n: int, k: int) -> float:
    return 1.0 - (1.0 - r2) * (n - 1) / (n - k - 1)


def regression_metrics(
    y_model, pred_model, y_raw, pred_raw, pi_low_raw, pi_high_raw, k: int
) -> dict[str, float]:
    """R² 與 Adjusted R² 用建模尺度；RMSE、MAE、覆蓋率用原始尺度。"""
    y_raw = np.asarray(y_raw, dtype=float)
    pred_raw = np.asarray(pred_raw, dtype=float)
    r2 = r2_score(y_model, pred_model)
    err = y_raw - pred_raw
    inside = (y_raw >= np.asarray(pi_low_raw)) & (y_raw <= np.asarray(pi_high_raw))
    return {
        "r2": r2,
        "adj_r2": adjusted_r2(r2, len(y_raw), k),
        "rmse": float(np.sqrt(np.mean(err**2))),
        "mae": float(np.mean(np.abs(err))),
        "pi_coverage": float(inside.mean()),
    }


def make_splitter(kind: str):
    if kind == "timeseries":
        return TimeSeriesSplit(n_splits=N_SPLITS), "TimeSeriesSplit（5 折，依時間順序，只用訓練集）"
    return KFold(n_splits=N_SPLITS, shuffle=True, random_state=RANDOM_STATE), "KFold（5 折，shuffle，random_state = 42，只用訓練集）"


def cross_validate(n: int, kind: str, fit_predict: Callable[[np.ndarray, np.ndarray], tuple[np.ndarray, np.ndarray]]) -> dict:
    """fit_predict(train_idx, test_idx) 回傳 (y_true, y_pred)，皆為建模尺度。"""
    splitter, method = make_splitter(kind)
    scores = []
    for train_idx, test_idx in splitter.split(np.arange(n)):
        y_true, y_pred = fit_predict(train_idx, test_idx)
        scores.append(r2_score(y_true, y_pred))
    arr = np.asarray(scores)
    return {"scores_r2": arr.tolist(), "mean": float(arr.mean()), "std": float(arr.std(ddof=1)), "method": method}


def even_sample_indices(n: int, max_points: int | None) -> np.ndarray:
    if not max_points or n <= max_points:
        return np.arange(n)
    return np.unique(np.linspace(0, n - 1, max_points).round().astype(int))


def residual_diagnostics(fitted, resid, max_points: int | None) -> dict:
    fitted = np.asarray(fitted, dtype=float)
    resid = np.asarray(resid, dtype=float)
    order = np.argsort(fitted, kind="mergesort")
    idx = order[even_sample_indices(len(order), max_points)]

    std = resid.std(ddof=1)
    z = np.sort(resid / std) if std > 0 else np.sort(resid)
    n = len(z)
    theo = stats.norm.ppf((np.arange(1, n + 1) - 0.5) / n)
    qidx = even_sample_indices(n, max_points)
    return {
        "fitted": fitted[idx].tolist(),
        "resid": resid[idx].tolist(),
        "qq_theoretical": theo[qidx].tolist(),
        "qq_sample": z[qidx].tolist(),
        "n_total": int(len(resid)),
    }
