"""CRISP-DM 文字內容：讀取內容檔並以管線結果代入佔位符。

佔位符語法：{{path.to.value}} 或 {{path.to.value|fmt}}
fmt：Python 格式（例如 .3f、,.0f）、pct（百分比一位小數）、pct0、int（千分位整數）、list（以「、」串接）
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

import yaml

from .config import CONTENT_DIR, PipelineError

PLACEHOLDER = re.compile(r"\{\{\s*([^{}|]+?)\s*(?:\|\s*([^{}]+?)\s*)?\}\}")
STEP_KEYS = (
    "business_understanding",
    "data_understanding",
    "data_preparation",
    "modeling",
    "evaluation",
    "deployment",
)


def load_content(filename: str | None, content_dir: Path = CONTENT_DIR) -> dict[str, Any]:
    if not filename:
        raise PipelineError("資料集設定缺少 content 檔名")
    path = content_dir / filename
    if not path.exists():
        raise PipelineError(f"找不到內容檔：{path}")
    doc = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    missing = [k for k in STEP_KEYS if not str((doc.get("crisp_dm") or {}).get(k) or "").strip()]
    if missing:
        raise PipelineError(f"內容檔 {filename} 缺少 CRISP-DM 步驟：{', '.join(missing)}")
    return doc


def resolve(ctx: Any, path: str) -> Any:
    cur = ctx
    for part in path.split("."):
        if isinstance(cur, dict) and part in cur:
            cur = cur[part]
        elif isinstance(cur, list) and part.lstrip("-").isdigit() and -len(cur) <= int(part) < len(cur):
            cur = cur[int(part)]
        else:
            raise PipelineError(f"無法解析佔位符：{{{{{path}}}}}")
    return cur


def fmt_value(value: Any, fmt: str | None) -> str:
    if isinstance(value, bool):
        return "是" if value else "否"
    if fmt == "pct":
        return f"{float(value) * 100:.1f}%"
    if fmt == "pct0":
        return f"{float(value) * 100:.0f}%"
    if fmt == "int":
        return f"{int(round(float(value))):,}"
    if fmt == "list" or isinstance(value, (list, tuple)):
        return "、".join(str(v) for v in value)
    if fmt:
        try:
            return format(value, fmt)
        except (ValueError, TypeError) as exc:
            raise PipelineError(f"佔位符格式 {fmt} 無法套用在 {value!r}") from exc
    if isinstance(value, float):
        return f"{value:.3f}"
    if value is None:
        raise PipelineError("佔位符的值是空的")
    return str(value)


def render(template: str, ctx: dict[str, Any]) -> str:
    def sub(m: re.Match) -> str:
        return fmt_value(resolve(ctx, m.group(1)), m.group(2))

    out = PLACEHOLDER.sub(sub, template)
    if "{{" in out or "}}" in out:
        raise PipelineError(f"內容中有無法辨識的佔位符：{out[max(0, out.find('{{') - 20): out.find('{{') + 40]}")
    return out


def build_context(result: dict[str, Any], content: dict[str, Any]) -> dict[str, Any]:
    models = {m["id"]: m for m in result["models"]}
    best = next(m for m in result["models"] if m["is_best"])
    success = dict(content.get("success") or {})
    if success:
        actual = resolve({"best": best, "model": models}, success.get("value", "best.metrics.r2"))
        success["actual"] = actual
        success["met"] = bool(actual >= float(success["threshold"]))
    fs = result["feature_selection"]
    return {
        **result,
        "model": models,
        "best": best,
        "metrics": {"test": best["metrics"], "cv": best["cv"]},
        "fs": fs,
        "prep": result["crisp_dm"]["data_preparation"],
        "du": result["data_understanding"],
        "success": success,
        "labels": content.get("feature_labels") or {},
    }


def render_crisp_dm(result: dict[str, Any], content: dict[str, Any]) -> dict[str, Any]:
    """回傳代入完成的 crisp_dm 區塊（保留管線產生的結構化欄位）。"""
    ctx = build_context(result, content)
    crisp = {k: dict(v) for k, v in result["crisp_dm"].items()}
    success = ctx["success"]
    if success:
        tmpl = (content.get("conclusion") or {}).get("met" if success["met"] else "not_met")
        if not tmpl:
            raise PipelineError("內容檔缺少 conclusion.met 或 conclusion.not_met")
        conclusion = render(tmpl, ctx)
        ctx["conclusion"] = conclusion
        crisp["evaluation"]["conclusion"] = conclusion
        crisp["evaluation"]["success"] = success
    for key in STEP_KEYS:
        crisp.setdefault(key, {})
        crisp[key]["markdown"] = render(content["crisp_dm"][key], ctx).strip()
    return crisp
