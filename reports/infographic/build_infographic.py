"""產生 A4 直式資訊圖表：python reports/infographic/build_infographic.py

數值取自 web/public/data/*.json，圖片取自 reports/figures/*_infographic_pred.png。
以 Playwright（使用本機 Google Chrome）匯出：
  reports/output/infographic.pdf（A4 單頁）
  reports/output/infographic.png（300 dpi，2480 × 3508）
"""
from __future__ import annotations

import io
import json
import re
import sys
from pathlib import Path

import qrcode
import qrcode.image.svg
from PIL import Image
from playwright.sync_api import sync_playwright

HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
DATA = ROOT / "web" / "public" / "data"
FIG = ROOT / "reports" / "figures"
OUT = ROOT / "reports" / "output"
A4_PX = (2480, 3508)  # 210 × 297 mm @ 300 dpi
CSS_PX = (794, 1123)  # 210 × 297 mm @ 96 dpi


def load(ds: str) -> dict:
    p = DATA / f"{ds}.json"
    if not p.exists():
        sys.exit(f"找不到 {p}，請先執行 python analysis/run_pipeline.py")
    return json.loads(p.read_text(encoding="utf-8"))


def values(ds: str, d: dict) -> dict[str, str]:
    m, du, fs = d["meta"], d["data_understanding"], d["feature_selection"]
    best = next(x for x in d["models"] if x["is_best"])
    chart = FIG / f"{ds}_infographic_pred.png"
    if not chart.exists():
        sys.exit(f"找不到 {chart}，請先執行 python analysis/run_pipeline.py")
    rmse = best["metrics"]["rmse"]
    return {
        f"{ds}.name": m["name"],
        f"{ds}.license": m["license"].split("（")[0],
        f"{ds}.rows": f"{du['n_rows']:,}",
        f"{ds}.features": str(du["n_features"]),
        f"{ds}.target": m["target"],
        f"{ds}.best_label": best["label"],
        f"{ds}.r2": f"{best['metrics']['r2']:.3f}",
        f"{ds}.rmse": f"${rmse:,.0f}" if m["log_target"] else f"{rmse:,.0f}",
        f"{ds}.chart": chart.as_uri(),
        f"{ds}.n_candidates": str(fs["n_candidates"]),
        f"{ds}.n_final": str(fs["n_final"]),
        f"{ds}.vif_removed": "、".join(fs["vif_removed"]) or "無",
    }


def qr_svg(url: str) -> str:
    img = qrcode.make(url, image_factory=qrcode.image.svg.SvgPathImage, box_size=10, border=2)
    buf = io.BytesIO()
    img.save(buf)
    svg = buf.getvalue().decode("utf-8")
    return re.sub(r"<\?xml[^>]*\?>", "", svg).strip()


def render() -> str:
    bike, house = load("bike"), load("house")
    site = bike["meta"]["site_url"]
    if not site.startswith("http"):
        sys.exit("datasets.yaml 尚未設定 site_url，無法產生 QR code")
    v = {**values("bike", bike), **values("house", house), "site_url": site, "qr_svg": qr_svg(site)}
    html = (HERE / "template.html").read_text(encoding="utf-8")

    def sub(mt: re.Match) -> str:
        key = mt.group(1).strip()
        if key not in v:
            sys.exit(f"模板中的 {{{{{key}}}}} 沒有對應的值")
        return v[key]

    out = re.sub(r"\{\{([^{}]+)\}\}", sub, html)
    if "{{" in out:
        sys.exit("模板仍有未代入的佔位符")
    return out


def main() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    rendered = HERE / "_rendered.html"
    rendered.write_text(render(), encoding="utf-8")
    try:
        with sync_playwright() as p:
            browser = p.chromium.launch(channel="chrome")
            page = browser.new_page(viewport={"width": CSS_PX[0], "height": CSS_PX[1]}, device_scale_factor=A4_PX[0] / CSS_PX[0])
            page.goto(rendered.as_uri())
            page.wait_for_load_state("networkidle")
            page.evaluate("document.fonts.ready")
            overflow = page.evaluate("document.querySelector('.page').scrollHeight - document.querySelector('.page').clientHeight")
            if overflow > 1:
                print(f"警告：內容超出 A4 高度 {overflow}px", file=sys.stderr)
            page.pdf(path=str(OUT / "infographic.pdf"), width="210mm", height="297mm", print_background=True,
                     margin={"top": "0", "right": "0", "bottom": "0", "left": "0"}, prefer_css_page_size=True)
            png = page.screenshot(full_page=False, type="png")
            browser.close()
    finally:
        rendered.unlink(missing_ok=True)

    img = Image.open(io.BytesIO(png)).convert("RGB")
    if img.size != A4_PX:
        img = img.resize(A4_PX, Image.LANCZOS)
    img.save(OUT / "infographic.png", dpi=(300, 300), optimize=True)
    print(f"已產生 {OUT / 'infographic.pdf'} 與 {OUT / 'infographic.png'}（{img.size[0]} × {img.size[1]}）")


if __name__ == "__main__":
    main()
