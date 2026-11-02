"""資料集設定的載入與驗證。"""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

import yaml

ANALYSIS_DIR = Path(__file__).resolve().parent.parent
ROOT_DIR = ANALYSIS_DIR.parent
RAW_DIR = ANALYSIS_DIR / "data" / "raw"
CONTENT_DIR = ANALYSIS_DIR / "content"
DATA_OUT_DIR = ROOT_DIR / "web" / "public" / "data"
FIGURES_DIR = ROOT_DIR / "reports" / "figures"

RANDOM_STATE = 42

REQUIRED_FIELDS = ("id", "name", "kaggle_url", "license", "file", "target", "split")


class PipelineError(Exception):
    """管線中任何可預期的失敗；進入點會把它轉成非零結束狀態。"""


@dataclass
class DatasetConfig:
    id: str
    name: str
    short_name: str
    kaggle_url: str
    origin_url: str | None
    license: str
    license_url: str | None
    citation: str | None
    file: str
    target: str
    id_cols: list[str]
    date_col: str | None
    split: str
    test_size: float
    random_state: int
    log_target: bool
    slr_feature: str
    ar: bool
    ar_maxlag: int
    cv: str
    max_points: int | None
    content: str | None
    extra: dict[str, Any] = field(default_factory=dict)

    @property
    def raw_path(self) -> Path:
        return RAW_DIR / self.file


def _validate(entry: dict[str, Any], index: int) -> None:
    label = entry.get("id") or f"第 {index + 1} 筆"
    missing = [f for f in REQUIRED_FIELDS if not str(entry.get(f) or "").strip()]
    if missing:
        raise PipelineError(f"datasets.yaml 中資料集「{label}」缺少欄位：{', '.join(missing)}")
    if entry["split"] not in ("time", "random"):
        raise PipelineError(f"資料集「{label}」的 split 必須是 time 或 random")


def load_site_url(path: Path | None = None) -> str | None:
    """datasets.yaml 頂層的 site_url（GitHub Pages 網址，部署後填入）。"""
    path = path or ANALYSIS_DIR / "datasets.yaml"
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    return doc.get("site_url") or None


def load_configs(path: Path | None = None) -> list[DatasetConfig]:
    path = path or ANALYSIS_DIR / "datasets.yaml"
    try:
        doc = yaml.safe_load(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise PipelineError(f"找不到設定檔：{path}") from exc
    entries = (doc or {}).get("datasets") or []
    if not entries:
        raise PipelineError("datasets.yaml 沒有任何資料集")
    configs = []
    for i, e in enumerate(entries):
        _validate(e, i)
        configs.append(
            DatasetConfig(
                id=e["id"],
                name=e["name"],
                short_name=e.get("short_name") or e["name"],
                kaggle_url=e["kaggle_url"],
                origin_url=e.get("origin_url"),
                license=e["license"],
                license_url=e.get("license_url"),
                citation=e.get("citation"),
                file=e["file"],
                target=e["target"],
                id_cols=list(e.get("id_cols") or []),
                date_col=e.get("date_col"),
                split=e["split"],
                test_size=float(e.get("test_size", 0.2)),
                random_state=int(e.get("random_state", RANDOM_STATE)),
                log_target=bool(e.get("log_target", False)),
                slr_feature=e.get("slr_feature", "auto"),
                ar=bool(e.get("ar", False)),
                ar_maxlag=int(e.get("ar_maxlag", 14)),
                cv=e.get("cv", "kfold"),
                max_points=e.get("max_points"),
                content=e.get("content"),
                extra={k: v for k, v in e.items()},
            )
        )
    return configs
