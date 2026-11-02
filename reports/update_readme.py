"""從管線輸出的 JSON 產生 README 的主要結果表，與資料集表，寫入 README 中對應的標記區塊之間。

用法：python reports/update_readme.py（需先執行 python analysis/run_pipeline.py）
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "public" / "data"
README = ROOT / "README.md"



def load(ds: str) -> dict:
    path = DATA / f"{ds}.json"
    if not path.exists():
        sys.exit(f"找不到 {path}，請先執行 python analysis/run_pipeline.py")
    return json.loads(path.read_text(encoding="utf-8"))


def datasets_table() -> str:
    rows = ["| 資料集 | 來源 | 授權 | 筆數 | 特徵數 | 目標變數 |", "|---|---|---|---:|---:|---|"]
    for ds in ("bike", "house"):
        m, du = load(ds)["meta"], load(ds)["data_understanding"]
        src = f"[Kaggle]({m['kaggle_url']})" + (f"／原始出處 [UCI]({m['origin_url']})" if m.get("origin_url") else "")
        rows.append(f"| {m['name']} | {src} | {m['license']} | {du['n_rows']:,} | {du['n_features']} | `{m['target']}` |")
    return "\n".join(rows) + "\n"


def table() -> str:
    lines = []
    for ds in ("bike", "house"):
        d = load(ds)
        meta, fs = d["meta"], d["feature_selection"]
        money = "（美元）" if meta["log_target"] else ""
        lines.append(f"**{meta['name']}**（目標：`{meta['target']}`；特徵選擇 {fs['n_candidates']} → {fs['n_final']} 個）\n")
        lines.append(f"| 模型 | 測試集 R² | Adjusted R² | RMSE{money} | MAE{money} | 95% 預測區間覆蓋率 | 5 折 CV R² |")
        lines.append("|---|---:|---:|---:|---:|---:|---:|")
        for m in d["models"]:
            x = m["metrics"]
            best = " ⭐ 最佳" if m["is_best"] else ""
            lines.append(
                f"| {m['label']}{best} | {x['r2']:.3f} | {x['adj_r2']:.3f} | {x['rmse']:,.0f} | {x['mae']:,.0f} "
                f"| {x['pi_coverage'] * 100:.1f}% | {m['cv']['mean']:.3f} ± {m['cv']['std']:.3f} |"
            )
        s = d["crisp_dm"]["evaluation"]["success"]
        note = f"成功標準：{s['metric']} ≥ {s['threshold']:.2f}，{'已達標' if s['met'] else '未達標'}。"
        if m.get("metrics_note"):
            note += m["metrics_note"] + "。"
        lines.append(f"\n{note}\n")
    return "\n".join(lines).rstrip() + "\n"


def main() -> None:
    text = README.read_text(encoding="utf-8")
    for name, build in (("DATASETS", datasets_table), ("RESULTS", table)):
        start, end = f"<!-- {name}:START -->", f"<!-- {name}:END -->"
        pattern = re.compile(re.escape(start) + r".*?" + re.escape(end), re.S)
        if not pattern.search(text):
            sys.exit(f"README.md 中找不到 {name} 標記")
        body = build()
        text = pattern.sub(lambda _m: f"{start}\n{body}{end}", text)
    README.write_text(text, encoding="utf-8")
    print("README 資料集表與結果表已更新")


if __name__ == "__main__":
    main()
