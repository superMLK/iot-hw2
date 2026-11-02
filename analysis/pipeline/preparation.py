"""CRISP-DM ③ Data Preparation：每個資料集各自的處理規則，並逐步記錄。"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split

from .config import DatasetConfig, PipelineError


@dataclass
class Prepared:
    X_train: pd.DataFrame
    X_test: pd.DataFrame
    y_train: pd.Series          # 建模尺度（House 為 log(price)）
    y_test: pd.Series
    y_train_raw: pd.Series      # 原始尺度
    y_test_raw: pd.Series
    features: list[str]
    steps: list[dict[str, Any]]
    before: dict[str, int]
    after: dict[str, int]
    dates_train: pd.Series | None = None
    dates_test: pd.Series | None = None
    target_label: str = ""
    extra: dict[str, Any] = field(default_factory=dict)


class StepLog:
    def __init__(self) -> None:
        self.steps: list[dict[str, Any]] = []

    def add(self, name: str, reason: str, affected: str, highlight: bool = False) -> None:
        step = {"name": name, "reason": reason, "affected": affected}
        if highlight:
            step["highlight"] = True
        self.steps.append(step)


def _one_hot(df: pd.DataFrame, cols: list[str], log: StepLog, reason: str) -> pd.DataFrame:
    before_cols = df.shape[1]
    out = pd.get_dummies(df, columns=cols, prefix=cols, drop_first=True, dtype=float)
    log.add(
        f"One-hot 編碼：{'、'.join(cols)}",
        reason,
        f"{len(cols)} 個類別欄展開為 {out.shape[1] - before_cols + len(cols)} 個虛擬變數（各丟棄最小值作為基準類別）",
    )
    return out


def prepare_bike(raw: pd.DataFrame, cfg: DatasetConfig) -> Prepared:
    log = StepLog()
    df = raw.copy()
    before = {"rows": int(df.shape[0]), "cols": int(df.shape[1])}

    df["dteday"] = pd.to_datetime(df["dteday"])
    df = df.sort_values("dteday").reset_index(drop=True)
    log.add("依日期排序", "後續以時間順序切分訓練集與測試集，並作為 AR 模型的時間軸", f"{len(df):,} 筆依 dteday 由舊到新排序")

    df = df.drop(columns=["casual", "registered"])
    log.add(
        "移除 casual、registered（資料洩漏）",
        "casual（非會員租借量）＋ registered（會員租借量）＝ cnt。預測當下無法事先得知這兩個值，"
        "若放入模型等於把答案交給模型，評估結果會失真。",
        "移除 2 欄",
        highlight=True,
    )

    df = df.drop(columns=["instant"])
    log.add("移除 instant", "instant 只是流水號，沒有預測意義", "移除 1 欄")

    df = df.drop(columns=["workingday"])
    log.add(
        "移除 workingday",
        "workingday 完全由 weekday 與 holiday 決定（非週末且非假日即為 1），"
        "與 weekday 虛擬變數及 holiday 完全共線，會讓多元回歸的係數無法估計",
        "移除 1 欄",
    )

    dates = df.pop("dteday")
    log.add("dteday 不作為特徵", "日期只用於排序與繪製時間軸；季節、月份、星期等資訊已由其他欄位表示", "移出特徵 1 欄")

    df = _one_hot(
        df,
        ["season", "weathersit", "mnth", "weekday"],
        log,
        "這些欄位是類別代碼，數值大小沒有順序意義，直接當數值會誤導線性模型",
    )

    y_raw = df.pop(cfg.target).astype(float)
    X = df.astype(float)

    n_train = int(len(X) * (1 - cfg.test_size))
    log.add(
        "依時間順序切分（前 80% 訓練、後 20% 測試）",
        "資料是時間序列，隨機切分會讓模型看到「未來」的資料，高估預測能力",
        f"訓練集 {n_train:,} 筆（{dates.iloc[0].date()} ～ {dates.iloc[n_train - 1].date()}），"
        f"測試集 {len(X) - n_train:,} 筆（{dates.iloc[n_train].date()} ～ {dates.iloc[-1].date()}）",
    )

    features = list(X.columns)
    return Prepared(
        X_train=X.iloc[:n_train].reset_index(drop=True),
        X_test=X.iloc[n_train:].reset_index(drop=True),
        y_train=y_raw.iloc[:n_train].reset_index(drop=True),
        y_test=y_raw.iloc[n_train:].reset_index(drop=True),
        y_train_raw=y_raw.iloc[:n_train].reset_index(drop=True),
        y_test_raw=y_raw.iloc[n_train:].reset_index(drop=True),
        features=features,
        steps=log.steps,
        before=before,
        after={"rows": int(X.shape[0]), "cols": int(X.shape[1] + 1), "features": len(features)},
        dates_train=dates.iloc[:n_train].reset_index(drop=True),
        dates_test=dates.iloc[n_train:].reset_index(drop=True),
        target_label="cnt",
        extra={"series": y_raw, "dates": dates, "n_train": n_train},
    )


HOUSE_OUTLIER_RULES = [
    ("bedrooms ≥ 30", lambda d: d["bedrooms"] >= 30, "臥室數 30 間以上（例如 33 間）明顯是輸入錯誤，該筆的居住面積只有一般住宅大小"),
    ("bedrooms = 0", lambda d: d["bedrooms"] == 0, "臥室數為 0 不符合一般住宅交易，視為缺漏或錯誤資料"),
    ("bathrooms = 0", lambda d: d["bathrooms"] == 0, "浴室數為 0 不符合一般住宅交易，視為缺漏或錯誤資料"),
]


def prepare_house(raw: pd.DataFrame, cfg: DatasetConfig) -> Prepared:
    log = StepLog()
    df = raw.copy()
    before = {"rows": int(df.shape[0]), "cols": int(df.shape[1])}

    df = df.drop(columns=["id"])
    log.add("移除 id", "id 是房屋編號，沒有預測意義", "移除 1 欄")

    for rule, mask_fn, reason in HOUSE_OUTLIER_RULES:
        mask = mask_fn(df)
        n = int(mask.sum())
        df = df.loc[~mask]
        log.add(f"移除異常值：{rule}", reason, f"移除 {n} 筆")
    df = df.reset_index(drop=True)

    date = pd.to_datetime(df.pop("date"), format="%Y%m%dT%H%M%S")
    df["sale_year"] = date.dt.year
    df["sale_month"] = date.dt.month
    log.add("date 轉成 sale_year、sale_month", "原始日期字串無法直接放入模型；拆出年份與月份以反映市場時間與季節", "1 欄轉為 2 欄")

    pct_not_renovated = float((df["yr_renovated"] == 0).mean() * 100)
    df["is_renovated"] = (df["yr_renovated"] > 0).astype(int)
    df["house_age"] = df["sale_year"] - df["yr_built"]
    df = df.drop(columns=["yr_renovated", "yr_built"])
    log.add(
        "yr_renovated 轉成 is_renovated；新增 house_age，移除 yr_built",
        f"yr_renovated 有 {pct_not_renovated:.1f}% 是 0（未翻修），改成 0/1 較好解讀；"
        "house_age ＝ sale_year − yr_built，三者完全共線，因此保留屋齡、移除建造年",
        "2 欄轉為 2 欄",
    )

    df = df.drop(columns=["sqft_above"])
    df["has_basement"] = (df.pop("sqft_basement") > 0).astype(int)
    log.add(
        "移除 sqft_above；sqft_basement 轉成 has_basement",
        "sqft_living ＝ sqft_above ＋ sqft_basement，完全共線；地下室面積改為有無地下室（0/1）",
        "2 欄轉為 1 欄",
    )

    n_zip = int(df["zipcode"].nunique())
    df = df.drop(columns=["zipcode"])
    log.add(
        "不使用 zipcode，以 lat、long 代表位置",
        f"zipcode 有 {n_zip} 個類別，one-hot 後會增加 {n_zip - 1} 個特徵並讓模型難以解讀；經緯度已能表達地理位置",
        "移除 1 欄",
    )

    df = _one_hot(df, ["sale_month"], log, "月份是類別，對價格的影響不是線性（以 1 月為基準）")

    price = df.pop(cfg.target).astype(float)
    y = np.log(price)
    log.add(
        "目標變數取 log(price)",
        "房價右偏嚴重，取對數後分布接近常態、殘差變異較穩定；預測值與區間會以 exp 轉回原始價格顯示",
        f"{len(price):,} 筆目標值轉為對數尺度",
    )

    X = df.astype(float)
    idx_train, idx_test = train_test_split(
        np.arange(len(X)), test_size=cfg.test_size, random_state=cfg.random_state
    )
    log.add(
        "隨機切分 80/20（random_state = 42）",
        "各筆交易彼此獨立，沒有時間依賴，可以隨機切分；固定亂數種子讓結果可重現",
        f"訓練集 {len(idx_train):,} 筆，測試集 {len(idx_test):,} 筆",
    )

    def take(obj, idx):
        return obj.iloc[idx].reset_index(drop=True)

    features = list(X.columns)
    return Prepared(
        X_train=take(X, idx_train),
        X_test=take(X, idx_test),
        y_train=take(y, idx_train),
        y_test=take(y, idx_test),
        y_train_raw=take(price, idx_train),
        y_test_raw=take(price, idx_test),
        features=features,
        steps=log.steps,
        before=before,
        after={"rows": int(X.shape[0]), "cols": int(X.shape[1] + 1), "features": len(features)},
        target_label="log(price)",
    )


PREPARERS = {"bike": prepare_bike, "house": prepare_house}


def prepare(raw: pd.DataFrame, cfg: DatasetConfig) -> Prepared:
    if cfg.id not in PREPARERS:
        raise PipelineError(f"資料集「{cfg.id}」沒有對應的資料準備規則")
    return PREPARERS[cfg.id](raw, cfg)
