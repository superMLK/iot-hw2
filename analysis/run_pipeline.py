"""分析管線進入點：python analysis/run_pipeline.py

依 datasets.yaml 逐一處理資料集，輸出 web/public/data/<id>.json 與 reports/figures/*.png。
任何步驟失敗都以非零狀態結束。
"""
from __future__ import annotations

import argparse
import sys
import warnings
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

import pandas as pd

sys.path.insert(0, str(Path(__file__).resolve().parent))

from pipeline import figures  # noqa: E402
from pipeline.config import DATA_OUT_DIR, FIGURES_DIR, DatasetConfig, PipelineError, load_configs, load_site_url  # noqa: E402
from pipeline.content import load_content, render_crisp_dm  # noqa: E402
from pipeline.export import clean, write_json  # noqa: E402
from pipeline.modeling import build_models  # noqa: E402
from pipeline.preparation import prepare  # noqa: E402
from pipeline.selection import select_features  # noqa: E402
from pipeline.understanding import understand  # noqa: E402


def analyse(cfg: DatasetConfig, raw: pd.DataFrame | None = None, content: dict[str, Any] | None = None) -> dict[str, Any]:
    """對單一資料集執行完整 CRISP-DM 管線，回傳符合 JSON 契約的結果（已清理精度）。"""
    if raw is None:
        if not cfg.raw_path.exists():
            raise PipelineError(f"找不到資料檔：{cfg.raw_path}")
        raw = pd.read_csv(cfg.raw_path)
    if content is None:
        content = load_content(cfg.content)

    du = understand(raw, cfg)
    prep = prepare(raw, cfg)
    selection = select_features(prep.X_train, prep.y_train)
    models = build_models(prep, cfg, selection, content.get("feature_labels") or {})

    sampled_models = [m for m in models if len(m["prediction"]["points"]) < m["prediction"]["n_total"]]
    meta = {
        "id": cfg.id,
        "name": cfg.name,
        "short_name": cfg.short_name,
        "kaggle_url": cfg.kaggle_url,
        "origin_url": cfg.origin_url,
        "license": cfg.license,
        "license_url": cfg.license_url,
        "citation": cfg.citation,
        "file": cfg.file,
        "target": cfg.target,
        "model_target": prep.target_label,
        "log_target": cfg.log_target,
        "split": cfg.split,
        "random_state": cfg.random_state,
        "n_train": int(len(prep.X_train)),
        "n_test": int(len(prep.X_test)),
        "sampled": bool(sampled_models),
        "n_points_total": int(models[0]["prediction"]["n_total"]),
        "n_points_shown": int(len(models[0]["prediction"]["points"])),
        "max_points": cfg.max_points,
        "target_mean_train": float(prep.y_train_raw.mean()),
        "target_mean_test": float(prep.y_test_raw.mean()),
        "site_url": load_site_url() or "（部署後產生）",
        "feature_labels": content.get("feature_labels") or {},
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    result = {
        "meta": meta,
        "crisp_dm": {
            "business_understanding": {},
            "data_understanding": {"stats_ref": "data_understanding"},
            "data_preparation": {
                "steps": prep.steps,
                "before": prep.before,
                "after": prep.after,
                "n_removed_rows": prep.before["rows"] - prep.after["rows"],
            },
            "modeling": {},
            "evaluation": {},
            "deployment": {},
        },
        "data_understanding": du,
        "feature_selection": selection,
        "models": models,
    }
    # 先清理精度，讓文字中代入的數字與網站、報告讀到的 JSON 數值完全一致
    result = clean(result)
    result["crisp_dm"] = render_crisp_dm(result, content)
    return clean(result)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="CRISP-DM 線性回歸分析管線")
    parser.add_argument("--out-dir", type=Path, default=DATA_OUT_DIR)
    parser.add_argument("--figures-dir", type=Path, default=FIGURES_DIR)
    parser.add_argument("--no-figures", action="store_true")
    parser.add_argument("--only", help="只處理指定的資料集 id")
    args = parser.parse_args(argv)

    warnings.filterwarnings("ignore", category=FutureWarning)
    try:
        configs = load_configs()
        for cfg in configs:
            if args.only and cfg.id != args.only:
                continue
            print(f"▶ {cfg.id}：{cfg.name}")
            result = analyse(cfg)
            size = write_json(result, args.out_dir / f"{cfg.id}.json")
            print(f"  JSON：{args.out_dir / f'{cfg.id}.json'}（{size / 1024:.0f} KB）")
            if not args.no_figures:
                files = figures.write_all(result, args.figures_dir)
                print(f"  圖檔：{len(files)} 張 → {args.figures_dir}")
            best = next(m for m in result["models"] if m["is_best"])
            print(f"  最佳模型：{best['label']}，測試集 R² = {best['metrics']['r2']}")
    except PipelineError as exc:
        print(f"✗ 管線失敗：{exc}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
