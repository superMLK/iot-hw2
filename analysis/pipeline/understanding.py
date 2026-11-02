"""CRISP-DM ② Data Understanding：在原始資料上計算基本資訊。"""
from __future__ import annotations

from typing import Any

import numpy as np
import pandas as pd

from .config import DatasetConfig, PipelineError

FEATURE_MIN_EXCLUSIVE = 13
FEATURE_MAX_EXCLUSIVE = 40


def count_features(df: pd.DataFrame, cfg: DatasetConfig) -> int:
    """特徵數 = 原始欄數 − 目標變數 − ID 欄（design 決策 2）。"""
    return df.shape[1] - 1 - len([c for c in cfg.id_cols if c in df.columns])


def check_feature_count(n_features: int, cfg: DatasetConfig) -> None:
    if not (FEATURE_MIN_EXCLUSIVE < n_features < FEATURE_MAX_EXCLUSIVE):
        raise PipelineError(
            f"資料集「{cfg.id}」的特徵數為 {n_features}，不符合作業要求（必須大於 13 且小於 40）"
        )


def _kind(series: pd.Series) -> str:
    if pd.api.types.is_numeric_dtype(series):
        return "numeric"
    return "categorical"


def _describe(series: pd.Series) -> dict[str, float]:
    s = series.dropna().astype(float)
    return {
        "count": int(s.count()),
        "mean": float(s.mean()),
        "std": float(s.std()),
        "min": float(s.min()),
        "q1": float(s.quantile(0.25)),
        "median": float(s.quantile(0.5)),
        "q3": float(s.quantile(0.75)),
        "max": float(s.max()),
    }


def _histogram(values: pd.Series, bins: int = 30) -> dict[str, list]:
    counts, edges = np.histogram(values.dropna().astype(float), bins=bins)
    return {"bins": edges.tolist(), "counts": counts.astype(int).tolist()}


def understand(df: pd.DataFrame, cfg: DatasetConfig) -> dict[str, Any]:
    n_features = count_features(df, cfg)
    check_feature_count(n_features, cfg)

    columns = [
        {
            "name": c,
            "dtype": str(df[c].dtype),
            "kind": _kind(df[c]),
            "missing": int(df[c].isna().sum()),
            "unique": int(df[c].nunique(dropna=True)),
            "role": "target" if c == cfg.target else ("id" if c in cfg.id_cols else ("date" if c == cfg.date_col else "feature")),
        }
        for c in df.columns
    ]

    numeric_cols = [c for c in df.columns if _kind(df[c]) == "numeric" and c not in cfg.id_cols]
    describe = {c: _describe(df[c]) for c in numeric_cols}

    corr = df[numeric_cols].corr()
    target_corr = (
        corr[cfg.target].drop(labels=[cfg.target]).abs().sort_values(ascending=False)
    )
    top_corr = [
        {"feature": f, "r": float(corr.loc[f, cfg.target]), "abs_r": float(v)}
        for f, v in target_corr.head(5).items()
    ]

    preview = df.head(10).astype(object).where(df.head(10).notna(), None).to_dict(orient="records")

    return {
        "n_rows": int(df.shape[0]),
        "n_cols": int(df.shape[1]),
        "n_features": int(n_features),
        "feature_rule": "原始欄數 − 目標變數 − ID 欄",
        "n_missing_total": int(df.isna().sum().sum()),
        "n_duplicates": int(df.duplicated().sum()),
        "columns": columns,
        "describe": describe,
        "correlation": {"labels": numeric_cols, "matrix": corr.values.tolist()},
        "target_distribution": _histogram(df[cfg.target]),
        "top_corr_features": top_corr,
        "preview": preview,
    }
