"""JSON 輸出：統一數值精度、處理 NaN/inf、決定性序列化。"""
from __future__ import annotations

import json
import math
from datetime import date, datetime
from pathlib import Path
from typing import Any

import numpy as np

SIG_DIGITS = 6
MAX_JSON_BYTES = 2 * 1024 * 1024


def _round_sig(x: float) -> float | int | None:
    if x is None or not math.isfinite(x):
        return None
    if x == 0:
        return 0
    v = float(f"{x:.{SIG_DIGITS}g}")
    return int(v) if v.is_integer() and abs(v) < 1e15 else v


def clean(obj: Any) -> Any:
    """遞迴轉成可 JSON 序列化的型別，浮點數四捨五入到 6 位有效數字。"""
    if isinstance(obj, dict):
        return {str(k): clean(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean(v) for v in obj]
    if isinstance(obj, np.ndarray):
        return [clean(v) for v in obj.tolist()]
    if isinstance(obj, (bool, np.bool_)):
        return bool(obj)
    if isinstance(obj, (int, np.integer)):
        return int(obj)
    if isinstance(obj, (float, np.floating)):
        return _round_sig(float(obj))
    if isinstance(obj, (datetime, date)):
        return obj.isoformat()
    if obj is None or isinstance(obj, str):
        return obj
    if hasattr(obj, "isoformat"):
        return obj.isoformat()
    if obj != obj:  # pandas NA 類
        return None
    return str(obj)


def dumps(doc: dict[str, Any]) -> str:
    return json.dumps(clean(doc), ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False)


def write_json(doc: dict[str, Any], path: Path) -> int:
    text = dumps(doc)
    data = text.encode("utf-8")
    if len(data) >= MAX_JSON_BYTES:
        from .config import PipelineError

        raise PipelineError(f"{path.name} 大小 {len(data)} bytes，超過 2 MB 上限")
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    return len(data)
