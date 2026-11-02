"""產生 Word 書面報告：python reports/build_report.py

文字：analysis/content/*.yaml（經管線代入數值後存在 JSON 的 crisp_dm 中）
數值：web/public/data/*.json
圖片：reports/figures/*.png
輸出：reports/output/report.docx
需先執行 python analysis/run_pipeline.py。
"""
from __future__ import annotations

import json
import re
import sys
from datetime import date
from pathlib import Path

from docx import Document
from docx.enum.section import WD_ORIENT  # noqa: F401
from docx.enum.table import WD_TABLE_ALIGNMENT
from docx.enum.text import WD_ALIGN_PARAGRAPH, WD_BREAK
from docx.oxml import OxmlElement
from docx.oxml.ns import qn
from docx.shared import Cm, Pt, RGBColor

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "web" / "public" / "data"
FIG = ROOT / "reports" / "figures"
OUT = ROOT / "reports" / "output" / "report.docx"

FONT_CJK = "微軟正黑體"
FONT_LATIN = "Calibri"
DATASETS = ("bike", "house")
CJK = re.compile(r"[⺀-鿿豈-﫿＀-￯　-〿]")


# ------------------------------------------------------------------ 樣式

def set_run_font(run, size: float | None = None, bold: bool | None = None, mono: bool = False) -> None:
    run.font.name = "Consolas" if mono else FONT_LATIN
    rpr = run._element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    fonts.set(qn("w:eastAsia"), FONT_CJK)
    if size:
        run.font.size = Pt(size)
    if bold is not None:
        run.bold = bold


def style_fonts(style, size: float | None = None, color: RGBColor | None = None) -> None:
    style.font.name = FONT_LATIN
    rpr = style.element.get_or_add_rPr()
    fonts = rpr.find(qn("w:rFonts"))
    if fonts is None:
        fonts = OxmlElement("w:rFonts")
        rpr.append(fonts)
    fonts.set(qn("w:ascii"), FONT_LATIN)
    fonts.set(qn("w:hAnsi"), FONT_LATIN)
    fonts.set(qn("w:eastAsia"), FONT_CJK)
    if size:
        style.font.size = Pt(size)
    if color is not None:
        style.font.color.rgb = color


def setup_document() -> Document:
    doc = Document()
    sec = doc.sections[0]
    sec.page_width, sec.page_height = Cm(21), Cm(29.7)
    for side in ("left_margin", "right_margin"):
        setattr(sec, side, Cm(2.3))
    sec.top_margin = sec.bottom_margin = Cm(2.2)

    styles = doc.styles
    style_fonts(styles["Normal"], 11)
    styles["Normal"].paragraph_format.line_spacing = 1.4
    styles["Normal"].paragraph_format.space_after = Pt(6)
    black = RGBColor(0x1A, 0x1A, 0x1A)
    for name, size in (("Title", 26), ("Heading 1", 18), ("Heading 2", 15), ("Heading 3", 13), ("Heading 4", 11.5)):
        style_fonts(styles[name], size, black)
        styles[name].font.bold = True
    style_fonts(styles["Caption"], 10, RGBColor(0x44, 0x44, 0x44))
    styles["Caption"].font.italic = False
    for name in ("List Bullet", "List Number"):
        style_fonts(styles[name], 11)
    add_page_number_footer(sec)
    return doc


def add_field(paragraph, instr: str, placeholder: str = "") -> None:
    run = paragraph.add_run()
    begin = OxmlElement("w:fldChar")
    begin.set(qn("w:fldCharType"), "begin")
    text = OxmlElement("w:instrText")
    text.set(qn("xml:space"), "preserve")
    text.text = instr
    sep = OxmlElement("w:fldChar")
    sep.set(qn("w:fldCharType"), "separate")
    end = OxmlElement("w:fldChar")
    end.set(qn("w:fldCharType"), "end")
    run._r.append(begin)
    run._r.append(text)
    run._r.append(sep)
    if placeholder:
        ph = paragraph.add_run(placeholder)
        set_run_font(ph)
        ph._r.append(end)
    else:
        run._r.append(end)


def add_page_number_footer(section) -> None:
    p = section.footer.paragraphs[0]
    p.alignment = WD_ALIGN_PARAGRAPH.CENTER
    add_field(p, "PAGE", "1")


def shade(cell, hex_fill: str) -> None:
    tcpr = cell._element.get_or_add_tcPr()
    shd = OxmlElement("w:shd")
    shd.set(qn("w:val"), "clear")
    shd.set(qn("w:color"), "auto")
    shd.set(qn("w:fill"), hex_fill)
    tcpr.append(shd)


# ------------------------------------------------------------------ Markdown → Word（與網站相同的子集）

def join_lines(lines: list[str]) -> str:
    out = ""
    for raw in lines:
        line = raw.strip()
        if not line:
            continue
        if not out:
            out = line
        elif CJK.search(out[-1]) or CJK.search(line[0]):
            out += line
        else:
            out += " " + line
    return out


INLINE = re.compile(r"\*\*(.+?)\*\*|`([^`]+)`|\[([^\]]+)\]\(([^)\s]+)\)")


def add_inline(paragraph, text: str, bold: bool = False) -> None:
    pos = 0
    for m in INLINE.finditer(text):
        if m.start() > pos:
            set_run_font(paragraph.add_run(text[pos:m.start()]), bold=bold or None)
        if m.group(1) is not None:
            add_inline(paragraph, m.group(1), bold=True)
        elif m.group(2) is not None:
            r = paragraph.add_run(m.group(2))
            set_run_font(r, mono=True, bold=bold or None)
            r.font.size = Pt(10)
        else:
            set_run_font(paragraph.add_run(f"{m.group(3)}（{m.group(4)}）"), bold=bold or None)
        pos = m.end()
    if pos < len(text):
        set_run_font(paragraph.add_run(text[pos:]), bold=bold or None)


UL = re.compile(r"^\s*[-*]\s+(.*)$")
OL = re.compile(r"^\s*\d+[.)]\s+(.*)$")
HEAD = re.compile(r"^(#{1,6})\s+(.*)$")


def add_markdown(doc: Document, text: str, base_level: int = 3) -> None:
    lines = text.replace("\r\n", "\n").split("\n")
    i = 0
    while i < len(lines):
        line = lines[i]
        if not line.strip():
            i += 1
            continue
        h = HEAD.match(line.strip())
        if h:
            level = min(base_level + max(0, len(h.group(1)) - 3), 4)
            add_inline(doc.add_heading(level=level), h.group(2).strip())
            i += 1
            continue
        if line.lstrip().startswith(">"):
            inner = []
            while i < len(lines) and lines[i].lstrip().startswith(">"):
                inner.append(re.sub(r"^\s*>\s?", "", lines[i]))
                i += 1
            table = doc.add_table(rows=1, cols=1)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            cell = table.cell(0, 0)
            shade(cell, "FFF3E6")
            add_inline(cell.paragraphs[0], join_lines(inner))
            doc.add_paragraph()
            continue
        list_re = UL if UL.match(line) else OL if OL.match(line) else None
        if list_re:
            style = "List Bullet" if list_re is UL else "List Number"
            items: list[list[str]] = []
            while i < len(lines) and lines[i].strip():
                m = list_re.match(lines[i])
                if m:
                    items.append([m.group(1)])
                elif re.match(r"^\s+\S", lines[i]) and items:
                    items[-1].append(lines[i])
                else:
                    break
                i += 1
            for it in items:
                add_inline(doc.add_paragraph(style=style), join_lines(it))
            continue
        para = []
        while i < len(lines) and lines[i].strip() and not HEAD.match(lines[i].strip()) and not lines[i].lstrip().startswith(">") \
                and not UL.match(lines[i]) and not OL.match(lines[i]):
            para.append(lines[i])
            i += 1
        add_inline(doc.add_paragraph(), join_lines(para))


# ------------------------------------------------------------------ 圖表編號

class Numbering:
    def __init__(self, doc: Document) -> None:
        self.doc = doc
        self.fig = 0
        self.tab = 0

    def figure(self, path: Path, caption: str, width_cm: float = 15.5) -> None:
        if not path.exists():
            sys.exit(f"找不到圖檔 {path}，請先執行 python analysis/run_pipeline.py")
        self.fig += 1
        p = self.doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        p.add_run().add_picture(str(path), width=Cm(width_cm))
        cap = self.doc.add_paragraph(style="Caption")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(cap.add_run(f"圖 {self.fig}：{caption}"))

    def table(self, caption: str, header: list[str], rows: list[list[str]], widths: list[float] | None = None,
              highlight: set[int] | None = None, font_size: float = 9.5) -> None:
        self.tab += 1
        cap = self.doc.add_paragraph(style="Caption")
        cap.alignment = WD_ALIGN_PARAGRAPH.CENTER
        cap.paragraph_format.keep_with_next = True
        set_run_font(cap.add_run(f"表 {self.tab}：{caption}"))
        t = self.doc.add_table(rows=1 + len(rows), cols=len(header))
        t.style = "Table Grid"
        t.alignment = WD_TABLE_ALIGNMENT.CENTER
        for j, h in enumerate(header):
            c = t.cell(0, j)
            shade(c, "E3EEFB")
            set_run_font(c.paragraphs[0].add_run(h), size=font_size, bold=True)
        for i, row in enumerate(rows, start=1):
            for j, v in enumerate(row):
                c = t.cell(i, j)
                if highlight and (i - 1) in highlight:
                    shade(c, "FFF3E6")
                add_inline_sized(c.paragraphs[0], str(v), font_size)
        apply_widths(t, widths)
        for row in t.rows:
            for c in row.cells:
                for para in c.paragraphs:
                    para.paragraph_format.line_spacing = 1.0
                    para.paragraph_format.space_after = Pt(1)
                    para.paragraph_format.space_before = Pt(1)
        self.doc.add_paragraph()


TEXT_WIDTH_CM = 16.4


def apply_widths(table, widths: list[float] | None) -> None:
    """固定欄寬：關閉自動調整，並同時寫入 tblGrid 與每個儲存格的寬度（Word 以兩者為準）。"""
    n = len(table.columns)
    if not widths:
        widths = [TEXT_WIDTH_CM / n] * n
    scale = min(1.0, TEXT_WIDTH_CM / sum(widths))
    widths = [w * scale for w in widths]
    table.autofit = False
    tbl_pr = table._tbl.tblPr
    layout = OxmlElement("w:tblLayout")
    layout.set(qn("w:type"), "fixed")
    tbl_pr.append(layout)
    grid = table._tbl.tblGrid
    for j, col in enumerate(grid.findall(qn("w:gridCol"))):
        col.set(qn("w:w"), str(int(Cm(widths[j]).twips)))
    for row in table.rows:
        for j, cell in enumerate(row.cells):
            cell.width = Cm(widths[j])


def add_inline_sized(paragraph, text: str, size: float) -> None:
    add_inline(paragraph, text)
    for r in paragraph.runs:
        r.font.size = Pt(size)


# ------------------------------------------------------------------ 格式

def f3(v: float) -> str:
    return f"{v:.3f}"


def f0(v: float) -> str:
    return f"{v:,.0f}"


def pct(v: float) -> str:
    return f"{v * 100:.1f}%"


def p_fmt(p: float) -> str:
    return "< 0.001" if p < 0.001 else f"{p:.3f}"


def g4(v: float) -> str:
    a = abs(v)
    if a >= 1000:
        return f"{v:,.0f}"
    if a >= 1:
        return f"{v:.3f}"
    if a == 0:
        return "0"
    return f"{v:.4g}"


def best(d: dict) -> dict:
    return next(m for m in d["models"] if m["is_best"])


def model(d: dict, mid: str) -> dict | None:
    return next((m for m in d["models"] if m["id"] == mid), None)


# ------------------------------------------------------------------ 章節

def cover(doc: Document, data: dict) -> None:
    for _ in range(5):
        doc.add_paragraph()
    t = doc.add_paragraph(style="Title")
    t.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(t.add_run("以 CRISP-DM 流程進行線性回歸分析"), size=26, bold=True)
    sub = doc.add_paragraph()
    sub.alignment = WD_ALIGN_PARAGRAPH.CENTER
    set_run_font(sub.add_run("Bike Sharing 每日租借量與 King County 房價"), size=15)
    for _ in range(4):
        doc.add_paragraph()
    site = data["bike"]["meta"]["site_url"]
    for label, value in (("課程", "物聯網應用與資料分析"), ("作業", "HW2"), ("姓名", "＿＿＿＿＿＿＿＿"), ("學號", "＿＿＿＿＿＿＿＿"),
                         ("日期", date.today().strftime("%Y 年 %m 月 %d 日")), ("網站", site)):
        p = doc.add_paragraph()
        p.alignment = WD_ALIGN_PARAGRAPH.CENTER
        set_run_font(p.add_run(f"{label}："), size=13, bold=True)
        set_run_font(p.add_run(value), size=13)
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)

    h = doc.add_paragraph()
    set_run_font(h.add_run("目錄"), size=16, bold=True)
    p = doc.add_paragraph()
    add_field(p, 'TOC \\o "1-2" \\h \\z \\u', "（在 Word 中於此按右鍵 →「更新功能變數」即可產生目錄）")
    doc.add_paragraph().add_run().add_break(WD_BREAK.PAGE)


def abstract(doc: Document, data: dict) -> None:
    doc.add_heading("摘要", level=1)
    b, h = data["bike"], data["house"]
    bb, hb = best(b), best(h)
    text = (
        f"本報告依 CRISP-DM 六個步驟，以線性回歸分析兩個 Kaggle 公開資料集。"
        f"Bike Sharing 資料共 {b['data_understanding']['n_rows']:,} 天、{b['data_understanding']['n_features']} 個特徵，"
        f"目標是預測每日總租借量；King County 房價資料共 {h['data_understanding']['n_rows']:,} 筆、"
        f"{h['data_understanding']['n_features']} 個特徵，目標是估算房屋成交價。"
        f"資料準備階段移除了會造成資料洩漏與完全共線的欄位，並以相關係數、VIF 與 AIC 雙向逐步回歸進行特徵選擇，"
        f"Bike 由 {b['feature_selection']['n_candidates']} 個候選特徵選出 {b['feature_selection']['n_final']} 個，"
        f"House 由 {h['feature_selection']['n_candidates']} 個選出 {h['feature_selection']['n_final']} 個。"
        f"模型涵蓋單純線性回歸、多元線性回歸與 Auto Regression，所有預測都附 95% 信賴區間與預測區間。"
    )
    add_inline(doc.add_paragraph(), text)
    text2 = (
        f"評估結果：Bike 的最佳模型為「{bb['label']}」，測試集 R² = {f3(bb['metrics']['r2'])}、RMSE = {f0(bb['metrics']['rmse'])}；"
        f"House 的最佳模型為「{hb['label']}」，測試集 R²（log 尺度）= {f3(hb['metrics']['r2'])}、RMSE = {f0(hb['metrics']['rmse'])} 美元。"
        f"分析結果以靜態網站呈現並部署於 GitHub Pages（{b['meta']['site_url']}），網站另提供自訂 CSV 網址的資料檢視功能。"
    )
    add_inline(doc.add_paragraph(), text2)


def datasets_chapter(doc: Document, data: dict, num: Numbering) -> None:
    doc.add_heading("資料集介紹與來源", level=1)
    add_inline(doc.add_paragraph(), "兩個資料集都存放在專案的 `analysis/data/raw/` 中，授權已查閱 Kaggle 與原始出處頁面確認。特徵數的計算方式為「原始欄數 − 目標變數 − ID 欄」。")
    rows = []
    for ds in DATASETS:
        m, du = data[ds]["meta"], data[ds]["data_understanding"]
        rows.append([m["name"], m["kaggle_url"], m["license"], f"{du['n_rows']:,}", str(du["n_features"]), f"`{m['target']}`"])
    num.table("資料集基本資訊", ["資料集", "Kaggle 連結", "授權", "筆數", "特徵數", "目標變數"], rows,
              widths=[2.8, 6.0, 3.2, 1.6, 1.4, 1.4], font_size=8.5)
    for ds in DATASETS:
        m = data[ds]["meta"]
        doc.add_heading(m["name"], level=2)
        p = doc.add_paragraph()
        add_inline(p, f"檔案 `{m['file']}`，Kaggle：{m['kaggle_url']}")
        if m.get("origin_url"):
            add_inline(doc.add_paragraph(), f"原始出處：{m['origin_url']}")
        add_inline(doc.add_paragraph(), f"授權：{m['license']}")
        cols = [c for c in data[ds]["data_understanding"]["columns"]]
        labels = m.get("feature_labels") or {}
        role = {"target": "目標變數", "id": "ID", "date": "日期", "feature": "特徵"}
        num.table(f"{m['short_name']} 欄位說明", ["欄位", "角色", "型別", "說明"],
                  [[f"`{c['name']}`", role[c["role"]], "數值" if c["kind"] == "numeric" else "文字", labels.get(c["name"], "")] for c in cols],
                  widths=[4.0, 2.4, 1.6, 8.4], font_size=9)


def per_dataset(doc: Document, data: dict, title: str, body) -> None:
    doc.add_heading(title, level=1)
    for ds in DATASETS:
        doc.add_heading(data[ds]["meta"]["name"], level=2)
        body(ds, data[ds])


def build(data: dict) -> Document:
    doc = setup_document()
    num = Numbering(doc)
    cover(doc, data)
    abstract(doc, data)
    datasets_chapter(doc, data, num)

    # 4. Business Understanding
    def bu(ds, d):
        add_markdown(doc, d["crisp_dm"]["business_understanding"]["markdown"])
    per_dataset(doc, data, "Business Understanding（業務理解）", bu)

    # 5. Data Understanding
    def du(ds, d):
        add_markdown(doc, d["crisp_dm"]["data_understanding"]["markdown"])
        u = d["data_understanding"]
        rows = [[f"`{k}`", f"{v['count']:,}", g4(v["mean"]), g4(v["std"]), g4(v["min"]), g4(v["median"]), g4(v["max"])]
                for k, v in u["describe"].items()]
        num.table(f"{d['meta']['short_name']} 數值欄敘述統計", ["欄位", "筆數", "平均", "標準差", "最小值", "中位數", "最大值"], rows,
                  widths=[3.4, 1.6, 2.4, 2.3, 2.2, 2.3, 2.2], font_size=8.5)
        num.figure(FIG / f"{ds}_target_distribution.png", f"{d['meta']['short_name']} 目標變數 {d['meta']['target']} 分布", 13)
        num.figure(FIG / f"{ds}_correlation.png", f"{d['meta']['short_name']} 數值欄相關係數矩陣", 14)
    per_dataset(doc, data, "Data Understanding（資料理解）", du)

    # 6. Data Preparation
    def dp(ds, d):
        p = d["crisp_dm"]["data_preparation"]
        add_markdown(doc, p["markdown"])
        num.table(f"{d['meta']['short_name']} 資料準備步驟", ["#", "步驟", "原因", "影響"],
                  [[str(i + 1), s["name"], s["reason"], s["affected"]] for i, s in enumerate(p["steps"])],
                  widths=[0.8, 4.2, 7.2, 3.6], highlight={i for i, s in enumerate(p["steps"]) if s.get("highlight")}, font_size=9)
        add_inline(doc.add_paragraph(), f"處理前 {p['before']['rows']:,} 筆 × {p['before']['cols']} 欄；處理後 {p['after']['rows']:,} 筆，候選特徵 {p['after']['features']} 個。")
    per_dataset(doc, data, "Data Preparation（資料準備）", dp)

    # 7. Modeling
    def mo(ds, d):
        fs = d["feature_selection"]
        add_markdown(doc, d["crisp_dm"]["modeling"]["markdown"])
        if fs["vif_rounds"]:
            num.table(f"{d['meta']['short_name']} VIF 迭代移除紀錄", ["輪次", "移除特徵", "當下 VIF", "剩餘特徵數"], widths=[2, 6, 4, 4], rows=
                      [[str(r["round"]), f"`{r['removed']}`", "∞" if r["vif_is_inf"] else f"{r['vif']:.2f}", str(len(r["remaining"]))] for r in fs["vif_rounds"]])
        num.table(f"{d['meta']['short_name']} 逐步回歸紀錄（起點 AIC = {fs['stepwise_start_aic']:.1f}）", ["步驟", "動作", "特徵", "AIC"], widths=[2, 2.4, 7, 5], rows=
                  [[str(s["step"]), "加入" if s["action"] == "add" else "移除", f"`{s['feature']}`", f"{s['aic']:.1f}"] for s in fs["stepwise_steps"]], font_size=9)
        yn = lambda v: "✓" if v else "✗"  # noqa: E731
        num.table(f"{d['meta']['short_name']} 三種特徵選擇方法比較（✓ 保留／✗ 移除）", ["特徵", "相關係數", "VIF", "逐步回歸（最終）"], widths=[6.4, 3.2, 3.2, 3.6], rows=
                  [[f"`{c['feature']}`", yn(c["corr_kept"]), yn(c["vif_kept"]), yn(c["stepwise_kept"])] for c in fs["comparison"]],
                  highlight={i for i, c in enumerate(fs["comparison"]) if c["stepwise_kept"]}, font_size=9)
        for mid in ("mlr_selected", "ar"):
            m = model(d, mid)
            if not m:
                continue
            num.table(f"{d['meta']['short_name']}「{m['label']}」係數表（p < 0.05 以底色標示）",
                      ["變數", "係數", "標準誤", "t 值", "p 值", "95% 信賴區間"], widths=[3.6, 2.3, 2.3, 1.6, 1.8, 4.8], rows=
                      [["截距" if c["name"] == "const" else f"`{c['name']}`", g4(c["coef"]), g4(c["std_err"]), f"{c['t']:.2f}", p_fmt(c["p"]),
                        f"[{g4(c['ci_low'])}, {g4(c['ci_high'])}]"] for c in m["coefficients"]],
                      highlight={i for i, c in enumerate(m["coefficients"]) if c["p"] < 0.05}, font_size=8.5)
    per_dataset(doc, data, "Modeling（建模，含特徵選擇）", mo)

    # 8. Evaluation
    def ev(ds, d):
        money = "（美元）" if d["meta"]["log_target"] else ""
        models = d["models"]
        num.table(f"{d['meta']['short_name']} 模型比較（測試集，★ 為最佳模型）",
                  ["模型", "R²", "Adj. R²", f"RMSE{money}", f"MAE{money}", "PI 覆蓋率", "5 折 CV R²"],
                  [[("★ " if m["is_best"] else "") + m["label"], f3(m["metrics"]["r2"]), f3(m["metrics"]["adj_r2"]), f0(m["metrics"]["rmse"]),
                    f0(m["metrics"]["mae"]), pct(m["metrics"]["pi_coverage"]), f"{f3(m['cv']['mean'])} ± {f3(m['cv']['std'])}"] for m in models],
                  highlight={i for i, m in enumerate(models) if m["is_best"]}, widths=[5.2, 1.4, 1.5, 2.1, 2.0, 1.7, 2.6], font_size=8.5)
        if models[0].get("metrics_note"):
            add_inline(doc.add_paragraph(), models[0]["metrics_note"] + "。")
        num.table(f"{d['meta']['short_name']} 交叉驗證每折 R²（{models[0]['cv']['method']}）",
                  ["模型", "第 1 折", "第 2 折", "第 3 折", "第 4 折", "第 5 折"], widths=[6.4, 2, 2, 2, 2, 2], rows=
                  [[m["label"], *[f3(s) for s in m["cv"]["scores_r2"]]] for m in models], font_size=8.5)
        for m in models:
            num.figure(FIG / f"{ds}_pred_{m['id']}.png", f"{d['meta']['short_name']} {m['label']}預測圖（含 95% 區間帶）")
            if m["type"] == "mlr" and m["id"] == "mlr_selected":
                num.figure(FIG / f"{ds}_actual_vs_pred_{m['id']}.png", f"{d['meta']['short_name']} {m['label']}實際值 vs 預測值", 10)
        b = best(d)
        num.figure(FIG / f"{ds}_residuals_{b['id']}.png", f"{d['meta']['short_name']} 最佳模型（{b['label']}）殘差診斷")
        add_markdown(doc, d["crisp_dm"]["evaluation"]["markdown"])
    per_dataset(doc, data, "Evaluation（評估）", ev)

    # 9. Deployment
    def de(ds, d):
        add_markdown(doc, d["crisp_dm"]["deployment"]["markdown"])
    per_dataset(doc, data, "Deployment（部署）", de)

    # 10. 結論與限制
    doc.add_heading("結論與限制", level=1)
    for ds in DATASETS:
        doc.add_heading(data[ds]["meta"]["name"], level=2)
        add_markdown(doc, data[ds]["crisp_dm"]["evaluation"]["conclusion"])
    doc.add_heading("共同限制", level=2)
    for t in (
        "線性回歸假設特徵與目標之間是線性關係，無法自動表達非線性與交互作用。",
        "逐步回歸在同一份訓練集上選擇特徵並估計係數，p 值有選擇偏誤，解讀時應保守。",
        "交叉驗證使用已在完整訓練集選好的特徵，對選擇後模型的評估會略為樂觀。",
        "預測區間假設殘差近似常態且變異固定；殘差圖與 Q-Q 圖顯示的偏離，會影響區間的實際覆蓋率。",
    ):
        add_inline(doc.add_paragraph(style="List Bullet"), t)

    # 11. 參考資料
    doc.add_heading("參考資料", level=1)
    refs = [data[ds]["meta"]["citation"] for ds in DATASETS if data[ds]["meta"].get("citation")]
    refs += [
        "Chapman, P., Clinton, J., Kerber, R., Khabaza, T., Reinartz, T., Shearer, C., & Wirth, R. (2000). CRISP-DM 1.0: Step-by-step data mining guide. SPSS Inc.",
        "Seabold, S., & Perktold, J. (2010). statsmodels: Econometric and statistical modeling with Python. Proceedings of the 9th Python in Science Conference.",
        "Pedregosa, F., et al. (2011). Scikit-learn: Machine learning in Python. Journal of Machine Learning Research, 12, 2825–2830.",
        f"本專案網站：{data['bike']['meta']['site_url']}",
    ]
    for r in refs:
        add_inline(doc.add_paragraph(style="List Number"), " ".join(r.split()))
    return doc


def main() -> None:
    data = {}
    for ds in DATASETS:
        path = DATA / f"{ds}.json"
        if not path.exists():
            sys.exit(f"找不到 {path}，請先執行 python analysis/run_pipeline.py")
        data[ds] = json.loads(path.read_text(encoding="utf-8"))
    doc = build(data)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    doc.save(OUT)
    print(f"已產生 {OUT}")


if __name__ == "__main__":
    main()
