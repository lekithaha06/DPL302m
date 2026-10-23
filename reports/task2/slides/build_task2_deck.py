"""Dựng bộ slide Task 2 (23 slide) từ file kết quả trong reports/task2 — không gõ tay con số nào.

Giao diện giống slide Task 1 (Swiss: mực đen, nền giấy, một màu nhấn xanh). Phân công slide theo PhanCong_Task2.docx:
Uyên 3, 4, 6, 7, 12 · Đăng 5, 19–22 (+ dẫn 1, 2, 23) · Bảo 8, 9, 11, 15, 18 · Kiệt 10, 13, 14, 16, 17.
Chạy từ thư mục repo:  python reports/task2/slides/build_task2_deck.py <out.pptx> <theme.pptx>
"""
import json, os, sys
from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from lxml import etree

OUT = sys.argv[1] if len(sys.argv) > 1 else "reports/task2/slides/Task2_DeTai1_Slide.pptx"
BASE = sys.argv[2] if len(sys.argv) > 2 else "D:/CAIDCM/done/tv3/drive-download-20261012T074908Z-1-001/SE205148_TV3_Slide.pptx"
R = "reports/task2"


def J(p):
    return json.load(open(f"{R}/{p}", encoding="utf-8"))


def has(p):
    return os.path.exists(f"{R}/{p}")


def f(x, d=2):
    s = f"{x:,.{d}f}"
    return s.replace(",", "X").replace(".", ",").replace("X", ".")


# ---------------- số liệu
DS = J("data/data_stats.json"); FL = DS["fleurs"]
A_V = J("asr/baseline_asr.json")["models"]
ERR = J("asr/asr_errors.json"); NE = J("asr/named_entities.json")
EV = {v: J(f"mt/eval_{v}.json") for v in ("B0", "V1", "V2", "V2b", "V3") if has(f"mt/eval_{v}.json")}
B0F = J("mt/eval_B0_full.json") if has("mt/eval_B0_full.json") else J("mt/eval_B0_batch32.json")
B0_PHOMT = B0F["phomt_test"]["BLEU"]
B0_PHOMT_NOTE = "" if has("mt/eval_B0_full.json") else "*"
LOG = {v: [json.loads(l) for l in open(f"{R}/mt/train_log_{v}.jsonl", encoding="utf-8")] for v in ("V1", "V2", "V2b", "V3") if has(f"mt/train_log_{v}.jsonl")}
SIG = {v: J(f"mt/significance_{v}_vs_B0.json") for v in ("V1", "V2", "V2b", "V3") if has(f"mt/significance_{v}_vs_B0.json")}
SEL = J("mt/phomt_dev_selection.json"); SEL2B = J("mt/phomt_dev_V2b.json") if has("mt/phomt_dev_V2b.json") else None
SEL3 = J("mt/phomt_dev_V3.json") if has("mt/phomt_dev_V3.json") else None
DEV = {k: J(f"mt/dev_{k}.json") for k in ("V2", "V2_itn", "V3") if has(f"mt/dev_{k}.json")}
ME2 = J("mt/mt_errors_V2.json"); ME1 = J("mt/mt_errors_V1.json")
SP0 = J("system/speed_B0.json")
FIN = "V3" if has("mt/eval_V3.json") else "V2"
SP2 = J("system/speed_V3.json") if FIN == "V3" and has("system/speed_V3.json") else J("system/speed_final.json")
SP2_NAME = "V3" if FIN == "V3" and has("system/speed_V3.json") else "V2"
SELF = (SEL3 or {}).get("V3", SEL["V2"]) if FIN == "V3" else SEL["V2"]
VR = J("system/visual_results.json")
AF = J("asr/fleurs/baseline_asr.json")["models"] if has("asr/fleurs/baseline_asr.json") and \
    J("asr/fleurs/baseline_asr.json").get("status") == "completed" else None
def phomt(v): return B0_PHOMT if v == "B0" else EV[v].get("phomt_test", {}).get("BLEU")


# ---------------- giao diện (giống Task 1)
INK, ACCENT, PAPER = RGBColor(0x0A, 0x0A, 0x0A), RGBColor(0x00, 0x2F, 0xA7), RGBColor(0xFA, 0xFA, 0xF8)
MID, HAIR, CARD, TINT, DOT = RGBColor(0x6B, 0x6B, 0x6B), RGBColor(0xBD, 0xBD, 0xB8), RGBColor(0xEE, 0xEE, 0xEA), RGBColor(0xE6, 0xEB, 0xF6), RGBColor(0x2E, 0x55, 0xC0)
WHITE, WARN = RGBColor(0xFF, 0xFF, 0xFF), RGBColor(0xB0, 0x2A, 0x1E)
FONT, FONT_NUM = "Segoe UI", "Consolas"
TOTAL = 23
A_NS = "http://schemas.openxmlformats.org/drawingml/2006/main"
prs = Presentation(BASE)
lst = prs.slides._sldIdLst
for sid in list(lst):
    prs.part.drop_rel(sid.rId); lst.remove(sid)
for lay in list(prs.slide_layouts) + [prs.slide_master]:
    for shp in list(lay.shapes):
        if shp.has_text_frame and "DPL302m - Task 1" in shp.text_frame.text:
            shp._element.getparent().remove(shp._element)
L_TITLE = next(l for l in prs.slide_layouts if l.name == "TITLE_ONLY")
COUNT = [0]


def tb(s, x, y, w, h, paras, size=13, color=INK, bold=False, align=PP_ALIGN.LEFT, anchor=MSO_ANCHOR.TOP, space=3):
    box = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    tf = box.text_frame; tf.word_wrap = True; tf.vertical_anchor = anchor
    tf.margin_left = tf.margin_right = Inches(0.03); tf.margin_top = tf.margin_bottom = Inches(0.02)
    for j, p in enumerate(paras if isinstance(paras, list) else [paras]):
        txt, o = (p, {}) if isinstance(p, str) else p
        para = tf.paragraphs[0] if j == 0 else tf.add_paragraph()
        para.alignment = o.get("align", align); para.space_after = Pt(o.get("space", space))
        r = para.add_run(); r.text = "▪ " + txt[2:] if txt.startswith("• ") else txt
        r.font.name = o.get("font", FONT); r.font.size = Pt(o.get("size", size)); r.font.bold = o.get("bold", bold)
        r.font.color.rgb = o.get("color", color)
        if o.get("spc"):
            r._r.get_or_add_rPr().set("spc", str(o["spc"]))
    return box


def rect(s, x, y, w, h, fill, line=None):
    sh = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(x), Inches(y), Inches(w), Inches(h))
    if fill is None: sh.fill.background()
    else: sh.fill.solid(); sh.fill.fore_color.rgb = fill
    if line is None: sh.line.fill.background()
    else: sh.line.color.rgb = line; sh.line.width = Pt(0.75)
    sh.shadow.inherit = False
    return sh


def hair(s, x, y, w, color=INK, weight=0.75):
    ln = s.shapes.add_connector(1, Inches(x), Inches(y), Inches(x + w), Inches(y))
    ln.line.color.rgb = color; ln.line.width = Pt(weight)


def label(s, x, y, w, h, text, fill, color=WHITE, size=11, bold=True):
    sh = rect(s, x, y, w, h, fill)
    tf = sh.text_frame; tf.margin_left = tf.margin_right = Inches(0.05); tf.vertical_anchor = MSO_ANCHOR.MIDDLE; tf.word_wrap = True
    p = tf.paragraphs[0]; p.alignment = PP_ALIGN.CENTER
    r = p.add_run(); r.text = text; r.font.name = FONT; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color
    return sh


def _border(cell, side, color, w_pt):
    tcPr = cell._tc.get_or_add_tcPr(); tag = f"{{{A_NS}}}ln{side}"
    for old in tcPr.findall(tag): tcPr.remove(old)
    ln = etree.SubElement(tcPr, tag)
    if color is None:
        ln.set("w", "0"); etree.SubElement(ln, f"{{{A_NS}}}noFill")
    else:
        ln.set("w", str(int(w_pt * 12700))); sf = etree.SubElement(ln, f"{{{A_NS}}}solidFill")
        etree.SubElement(sf, f"{{{A_NS}}}srgbClr").set("val", str(color))
    order = ["lnL", "lnR", "lnT", "lnB"]
    lns = {e.tag.split("}")[1]: e for e in tcPr if e.tag.split("}")[1] in order}
    for e in lns.values(): tcPr.remove(e)
    for k, name in enumerate(n_ for n_ in order if n_ in lns): tcPr.insert(k, lns[name])


def table(s, x, y, colw, rows, size=11.5, first_bold=False, hl_rows=(), row_h=0.32):
    shp = s.shapes.add_table(len(rows), len(colw), Inches(x), Inches(y), Inches(sum(colw)), Inches(row_h * len(rows)))
    t = shp.table; t.first_row = False; t.horz_banding = False
    st = t._tbl.tblPr.find(f"{{{A_NS}}}tableStyleId")
    if st is not None: st.text = "{2D5ABB26-0587-4C30-8999-92F81FD0307C}"
    for ci, w in enumerate(colw): t.columns[ci].width = Inches(w)
    for ri, row in enumerate(rows):
        t.rows[ri].height = Inches(row_h)
        for ci, val in enumerate(row):
            c = t.cell(ri, ci); c.margin_left = c.margin_right = Inches(0.07); c.margin_top = c.margin_bottom = Inches(0.03)
            c.vertical_anchor = MSO_ANCHOR.MIDDLE; c.fill.solid()
            c.fill.fore_color.rgb = INK if ri == 0 else (TINT if ri in hl_rows else PAPER)
            tf = c.text_frame; tf.word_wrap = True
            for li, line in enumerate(val if isinstance(val, list) else [str(val)]):
                p = tf.paragraphs[0] if li == 0 else tf.add_paragraph()
                r = p.add_run(); r.text = line; r.font.name = FONT; r.font.size = Pt(size)
                r.font.bold = ri == 0 or (first_bold and ci == 0) or ri in hl_rows
                r.font.color.rgb = WHITE if ri == 0 else INK
            for side in "LRT": _border(c, side, None, 0)
            _border(c, "B", INK if ri in (0, len(rows) - 1) else HAIR, 0.75)
    return shp


def pic(s, path, x, y, w=None, h=None):
    kw = {}
    if w: kw["width"] = Inches(w)
    if h: kw["height"] = Inches(h)
    return s.shapes.add_picture(f"{R}/{path}", Inches(x), Inches(y), **kw)


def new(title, notes, dark=False):
    COUNT[0] += 1
    s = prs.slides.add_slide(L_TITLE)
    for ph in list(s.placeholders): ph._element.getparent().remove(ph._element)
    s.background.fill.solid(); s.background.fill.fore_color.rgb = ACCENT if dark else PAPER
    if not dark:
        tb(s, 0.6, 0.45, 12.1, 0.62, [(title, {"size": 26, "bold": True})], anchor=MSO_ANCHOR.MIDDLE)
        hair(s, 0.6, 1.12, 12.13, INK, 1.0)
        hair(s, 0.6, 6.95, 12.13, INK, 0.75)
        tb(s, 0.6, 7.0, 8.0, 0.3, [("DPL302M · TASK 2 · ĐỀ TÀI 1 · ASR TIẾNG VIỆT → DỊCH ANH", {"size": 8.5, "bold": True, "color": MID, "spc": 80})])
        tb(s, 10.6, 6.98, 2.13, 0.32, [(f"№ {COUNT[0]:02d} / {TOTAL}", {"size": 10.5, "bold": True, "font": FONT_NUM, "align": PP_ALIGN.RIGHT})])
    s.notes_slide.notes_text_frame.text = notes
    return s


def note(s, text, y=6.55, color=MID):
    tb(s, 0.6, y, 12.1, 0.36, [(text, {"size": 11, "color": color})])


def pending(s, x, y, w, h, text):
    label(s, x, y, w, h, text, RGBColor(0xFB, 0xEA, 0xE8), color=WARN, size=12)


def dots(s, x, y, cols, rows, step=0.22, d=0.06):
    for r_ in range(rows):
        for c_ in range(cols):
            o = s.shapes.add_shape(MSO_SHAPE.OVAL, Inches(x + c_ * step), Inches(y + r_ * step), Inches(d), Inches(d))
            o.fill.solid(); o.fill.fore_color.rgb = DOT; o.line.fill.background()


tr, dv, te = FL["train"], FL["dev"], FL["test"]
pho, wsp = A_V["PhoWhisper-small"]["metrics"], A_V["whisper-small"]["metrics"]
B0, V1, V2 = EV["B0"], EV["V1"], EV["V2"]
cas = lambda v: EV[v]["fleurs_cascade"]["BLEU"]
cln = lambda v: EV.get(v, {}).get("fleurs_clean", {}).get("BLEU", EV["V2"]["fleurs_clean"]["BLEU"] if v == "V3" else None)
fem = tr["gender"]["FEMALE"]

# 1 ----------------------------------------------------------------- Title
s = new("", "Đăng dẫn (~20 giây). Chào thầy. Nhóm báo cáo tiến độ Task 2: xử lý dữ liệu, chạy lại hai baseline trên cùng môi trường, "
        "và phát triển phương pháp đề xuất qua các phiên bản V1 đến V3.", dark=True)
dots(s, 9.85, 0.55, 13, 6)
tb(s, 0.8, 1.0, 9.0, 0.35, [("ĐỀ TÀI 1 · DPL302M · TASK 2", {"size": 12, "bold": True, "color": WHITE, "spc": 150})])
tb(s, 0.8, 1.7, 11.5, 1.9, [("Hệ thống nhận dạng giọng nói tiếng Việt\nkèm dịch sang tiếng Anh", {"size": 38, "bold": True, "color": WHITE})])
tb(s, 0.8, 3.75, 11.5, 0.9, [("Báo cáo Tiến độ Task 2: Xử lý Dữ liệu, Thực nghiệm Baseline & Mô hình Đề xuất", {"size": 18, "color": WHITE})])
tb(s, 0.8, 5.0, 11.5, 1.4, [("Dương Gia Bảo · Lê Tuấn Kiệt · Hồ Lâm Bảo Đăng · Bùi Ngọc Phương Uyên", {"size": 14, "bold": True, "color": WHITE}),
                            ("Mã nhóm: ……   ·   GVHD: ……", {"size": 13, "color": WHITE})])

# 2 ----------------------------------------------------------------- Agenda
s = new("Tổng quan nội dung", "Đăng (~20 giây). Bốn phần, theo đúng cấu trúc đề Task 2. Mỗi thành viên trình bày phần mình phụ trách.")
items = [("I", "Xử lý và phân tích dữ liệu", "Nguồn, làm sạch, gán nhãn, thống kê, mất cân bằng", "Uyên · Đăng", "3–7"),
         ("II", "Thực nghiệm hai baseline", "Môi trường, Paper và Nhóm, Gap Analysis, theo nhóm dữ liệu", "Bảo · Kiệt · Uyên", "8–12"),
         ("III", "Proposed Method V1 → V3", "Kiến trúc, kết quả, failure cases, V2/V3, ablation", "Kiệt · Bảo", "13–18"),
         ("IV", "Lỗi và tính khả thi", "Kết quả đầu ra, tốc độ, dung lượng, khả thi, kế hoạch Task 3", "Đăng", "19–22")]
for k, (n_, t_, d_, who, sl) in enumerate(items):
    y = 1.5 + k * 1.25
    label(s, 0.6, y, 0.9, 1.0, n_, ACCENT, size=22)
    tb(s, 1.7, y + 0.05, 7.4, 0.5, [(t_, {"size": 18, "bold": True})])
    tb(s, 1.7, y + 0.5, 7.4, 0.45, [(d_, {"size": 13, "color": MID})])
    tb(s, 9.3, y + 0.25, 2.3, 0.5, [(who, {"size": 13, "bold": True})])
    tb(s, 11.6, y + 0.25, 1.1, 0.5, [(f"slide {sl}", {"size": 12, "color": MID, "align": PP_ALIGN.RIGHT})])

# 3 ----------------------------------------------------------------- Data sources (Uyên)
s = new("Thu thập và tổng quan dữ liệu", "Uyên (~50 giây). Ba bộ dữ liệu công khai, tải mới từ nguồn gốc. FLEURS là bộ duy nhất có cả âm thanh tiếng Việt "
        "và câu tiếng Anh, nên dùng để dạy và chấm cả hệ thống. Nhóm không tự thu dữ liệu offline; đề cho phép, hạn chế là chưa thử micro điện thoại.")
table(s, 0.6, 1.35, [2.0, 1.25, 3.35, 2.05, 1.35, 2.13], [
    ["Nguồn", "Loại", "Số mẫu dùng", "Định dạng", "Dung lượng", "License"],
    ["FLEURS vi_vn + en_us", "Online", f"{tr['utterances'] + 67:,} / {dv['utterances']} / {te['utterances']} bản thu (train/dev/test)".replace(",", "."), "WAV 16 kHz + TSV", "2,9 GB", "CC BY 4.0"],
    ["VIVOS (test)", "Online", f"{DS['vivos_test']['utterances']} câu, {DS['vivos_test']['speakers']} người nói", "WAV 16 kHz + TXT", "82 MB", "CC BY-NC-SA 4.0"],
    ["PhoMT", "Online (gated)", "2.977.999 / 18.719 / 19.151 cặp câu", "TXT song song", "501 MB", "Chỉ nghiên cứu"],
    ["Tự thu", "Offline", "Không thu thập", "–", "–", "–"]], size=12, first_bold=True, row_h=0.45)
tb(s, 0.6, 3.85, 12.1, 0.35, [("Các trường dữ liệu FLEURS: ID câu FLoRes · tên file · transcript gốc · transcript chuẩn hóa · số mẫu âm thanh · giới tính", {"size": 12, "color": MID})])
ex = json.load(open("data/processed/fleurs_vi_en_train.json", encoding="utf-8"))[0] if os.path.exists("data/processed/fleurs_vi_en_train.json") else None
label(s, 0.6, 4.4, 2.0, 0.4, "VÍ DỤ MẪU FLEURS", INK, size=11)
if ex:
    tb(s, 0.6, 4.9, 12.1, 1.5, [(f"Âm thanh: {os.path.basename(ex['audio'])}  ·  ID câu {ex['id']}", {"size": 12, "color": MID}),
                                (f"Tiếng Việt: {ex['vi_raw']}", {"size": 13}), (f"Tiếng Anh: {ex['en_ref']}", {"size": 13})])

# 4 ----------------------------------------------------------------- Cleaning (Uyên)
s = new("Làm sạch dữ liệu", "Uyên (~50 giây). Mỗi bước đếm số mẫu còn lại. Chỉ train mất mẫu: 67 bản thu không có câu tiếng Anh cùng ID. "
        "Không có transcript rỗng, file lỗi hay trùng file. Mẫu khó và câu dài trên 30 giây được giữ lại để phân tích lỗi.")
steps = [("Dữ liệu gốc", "vi_vn TSV"), ("Có câu Anh", "ghép theo ID"), ("Transcript", "không rỗng"), ("Âm thanh", "đọc được"), ("Không trùng", "hash SHA-1")]
cnt = [s_[1] for s_ in tr["cleaning_steps"]]
for k, (t_, d_) in enumerate(steps):
    x = 0.6 + k * 2.47
    label(s, x, 1.45, 2.1, 0.55, t_, ACCENT, size=13)
    tb(s, x, 2.05, 2.1, 0.35, [(d_, {"size": 11, "color": MID, "align": PP_ALIGN.CENTER})])
    tb(s, x, 2.4, 2.1, 0.5, [(f"{cnt[k]:,}".replace(",", "."), {"size": 22, "bold": True, "font": FONT_NUM, "align": PP_ALIGN.CENTER})])
    if k < 4:
        a = s.shapes.add_shape(MSO_SHAPE.RIGHT_ARROW, Inches(x + 2.13), Inches(1.6), Inches(0.3), Inches(0.28))
        a.fill.solid(); a.fill.fore_color.rgb = INK; a.line.fill.background()
tb(s, 0.6, 2.95, 12.1, 0.3, [("Số bản thu còn lại của tập train sau mỗi bước (dev 361 và test 857 không mất mẫu nào)", {"size": 11, "color": MID})])
table(s, 0.6, 3.5, [3.2, 8.93], [
    ["Bước", "Cách làm"],
    ["Missing values", "Bỏ bản thu không có câu tiếng Anh cùng ID FLoRes: train loại 67 (2,2%)"],
    ["Duplicate", "So hash từng file âm thanh: 0 file trùng. Một câu có nhiều bản thu là thiết kế của FLEURS, không phải trùng"],
    ["Noise / outlier", f"Giữ lại để phân tích: {tr['over_30s']} bản thu train và {dv['over_30s']} dev dài hơn 30 giây"],
    ["Chuẩn hóa", "100% âm thanh 16 kHz; chữ: NFC, viết thường, ký hiệu thành khoảng trắng, giữ dấu tiếng Việt"],
    ["Chống leakage", "Chia theo ID câu; train–dev, train–test, dev–test: 0 ID trùng, 0 câu trùng nội dung"]], size=12, first_bold=True, row_h=0.47)

# 5 ----------------------------------------------------------------- Labeling (Đăng)
s = new("Gán nhãn và độ đồng nhất", "Đăng (~45 giây). Ba bộ dữ liệu đều có nhãn gốc, nhóm dùng nhãn gốc để train và chấm. "
        "Để phân tích lỗi, 100 câu dev baseline làm sai được gán loại lỗi tự động theo quy tắc cố định: tên riêng là lỗi phổ biến nhất (43%). "
        "Vì chỉ có một quy trình gán, không có hai người gán độc lập, nên không tính Cohen's Kappa; đề Task 2 chỉ yêu cầu Kappa nếu có nhiều người gán.")
table(s, 0.6, 1.35, [2.6, 9.53], [
    ["Dataset", "Nhãn dùng"],
    ["FLEURS", "Transcript tiếng Việt gốc + câu tiếng Anh FLoRes cùng ID (bản dịch chuyên nghiệp)"],
    ["VIVOS", "Transcript gốc của bộ dữ liệu, chia theo người nói"],
    ["PhoMT", "Cặp câu song ngữ gốc"]], size=12, first_bold=True, row_h=0.42)
tb(s, 0.6, 3.25, 12.1, 0.4, [("Gán nhãn loại lỗi cho 100 câu FLEURS dev mà baseline nghe hoặc dịch sai (chọn tự động, seed 42)", {"size": 15, "bold": True})])
cats = ["Sai dấu thanh", "Tên riêng", "Số", "Thiếu / thừa từ", "Sai nghĩa"]
for k, c in enumerate(cats):
    label(s, 0.6 + k * 2.47, 3.8, 2.3, 0.5, c, TINT, color=INK, size=12)
if has("labeling/kappa.json"):
    K = J("labeling/kappa.json")
    names = {"sai_dau_thanh": "Dấu thanh", "ten_rieng": "Tên riêng", "so": "Số", "thieu_thua_tu": "Thiếu/thừa từ", "sai_nghia_dich": "Sai nghĩa"}
    table(s, 0.6, 4.55, [2.6] + [1.9] * 5, [["Cohen's Kappa"] + [names[c] for c in K["per_category"]],
          ["Kappa"] + [f(v["kappa"], 2) if v["kappa"] is not None else "–" for v in K["per_category"].values()],
          ["Đồng ý thô"] + [f"{f(100 * v['agreement'], 0)}%" for v in K["per_category"].values()]], size=12, first_bold=True, row_h=0.4)
    tb(s, 0.6, 5.85, 12.1, 0.4, [(f"{K['n_sentences']} câu · Kappa trung bình {f(K['mean_kappa'], 2)} · hai người gán độc lập (Đăng, Uyên)", {"size": 12, "bold": True})])
elif has("labeling/auto_labels_summary.json"):
    AL = J("labeling/auto_labels_summary.json")
    names = {"sai_dau_thanh": "Dấu thanh", "ten_rieng": "Tên riêng", "so": "Số", "thieu_thua_tu": "Thiếu/thừa từ", "sai_nghia_dich": "Sai nghĩa"}
    table(s, 0.6, 4.55, [2.6] + [1.9] * 5, [["Gán tự động (100 câu)"] + [names[k] for k in AL["counts"]],
          ["Số câu có lỗi"] + [f"{v} ({f(AL['percent'][k], 0)}%)" for k, v in AL["counts"].items()]], size=12, first_bold=True, row_h=0.42)
    tb(s, 0.6, 5.5, 12.1, 0.7, [(f"{AL['sentences_with_any_error']}/{AL['n']} câu có ít nhất một lỗi. Nhãn gán tự động theo quy tắc cố định (chạy lại ra đúng kết quả); "
                                "chỉ một quy trình gán nên không tính Cohen's Kappa.", {"size": 12.5})])
else:
    pending(s, 0.6, 4.6, 12.13, 1.0, "CHỜ KẾT QUẢ gán nhãn loại lỗi")
note(s, "Đề Task 2 mục 1.2: Kappa chỉ bắt buộc nếu có quy trình nhiều người gán nhãn. Tiêu chí: reports/task2/labeling/TIEU_CHI_GAN_NHAN.md", y=6.35)

# 6 ----------------------------------------------------------------- Stats & imbalance (Uyên)
s = new("Thống kê mô tả và mất cân bằng", "Uyên (~55 giây). Bài nghe và dịch không có lớp, nên mất cân bằng xét theo giới tính, số bản thu mỗi câu, độ dài. "
        f"Lệch lớn nhất: train có {f(100 * fem / tr['utterances'], 1)}% giọng nữ nhưng dev và test toàn giọng nam. Nhóm giữ cách chia gốc để so được với công bố.")
table(s, 0.6, 1.35, [2.1, 1.35, 1.35, 1.35], [
    ["", "Train", "Dev", "Test"],
    ["Bản thu", f"{tr['utterances']:,}".replace(",", "."), str(dv["utterances"]), str(te["utterances"])],
    ["Câu gốc", f"{tr['unique_sentences']:,}".replace(",", "."), str(dv["unique_sentences"]), str(te["unique_sentences"])],
    ["Giờ", f(tr["hours"], 2), f(dv["hours"], 2), f(te["hours"], 2)],
    ["TB giây/câu", f(tr["mean_sec"], 1), f(dv["mean_sec"], 1), f(te["mean_sec"], 1)],
    ["Tỉ lệ", f"{f(DS['split_ratio_percent']['train'], 1)}%", f"{f(DS['split_ratio_percent']['dev'], 1)}%", f"{f(DS['split_ratio_percent']['test'], 1)}%"]],
    size=12, first_bold=True, row_h=0.42)
pic(s, "data/figures/fleurs_gender.png", 6.95, 1.3, w=5.8)
rp = tr["recordings_per_sentence"]
tb(s, 0.6, 4.1, 6.1, 2.4, [("Nhận xét định lượng", {"size": 14, "bold": True}),
    (f"• Giới tính: train {fem:,} giọng nữ ({f(100 * fem / tr['utterances'], 1)}%), dev và test 100% giọng nam".replace(",", "."), {"size": 12.5}),
    (f"• Số bản thu mỗi câu (train): {rp['1']} câu có 1, {rp['2']} câu có 2, {rp['3']} câu có 3", {"size": 12.5}),
    (f"• Độ dài: 52,4% bản thu train dài 10–20 giây, chỉ {tr['length_buckets']['<5 s']} bản dưới 5 giây", {"size": 12.5}),
    ("• PhoMT: 51,4% train là phụ đề phim (paper PhoMT)", {"size": 12.5})])
pic(s, "data/figures/fleurs_split.png", 6.95, 4.15, w=4.6)

# 7 ----------------------------------------------------------------- Imbalance handling (Uyên)
v2b_txt = (f"V2b (V2 + cân bằng theo câu): dev {f(LOG['V2b'][max(range(len(LOG['V2b'])), key=lambda i: LOG['V2b'][i]['dev_bleu'])]['dev_bleu'], 2)} "
           f"so với V2 {f(max(r['dev_bleu'] for r in LOG['V2']), 2)}; test cascade {f(cas('V2b'), 2)} so với {f(cas('V2'), 2)}") if "V2b" in LOG and "V2b" in EV else ""
s = new("Xử lý mất cân bằng", "Uyên (~50 giây). Kỹ thuật: lấy mẫu lại theo câu, trọng số 1 chia số bản thu, để mỗi câu gốc đóng góp như nhau. "
        "Không dùng augmentation âm thanh vì nhóm không train khối nghe. Kết quả đo thật: cân bằng theo câu không giúp, nên không đưa vào bản cuối. "
        "Lý do: các bản thu khác nhau của cùng câu cho lỗi nghe khác nhau, là dữ liệu có ích.")
pic(s, "data/figures/fleurs_sentence_balance.png", 0.6, 1.35, w=7.0)
tb(s, 7.9, 1.4, 4.85, 3.0, [("Kỹ thuật áp dụng", {"size": 14, "bold": True}),
    ("• Resampling theo câu: bản thu của câu có k bản được lấy với trọng số 1/k", {"size": 12.5}),
    ("• Cân bằng miền khi trộn dữ liệu (V2): thêm 1.449 cặp chữ chuẩn và 3.000 cặp PhoMT", {"size": 12.5}),
    ("• Không augmentation âm thanh: không train khối nghe", {"size": 12.5}),
    ("• Lệch giới tính: test không có giọng nữ, ghi là hạn chế", {"size": 12.5})])
label(s, 7.9, 4.5, 4.85, 0.45, "KẾT QUẢ ĐO", INK, size=12)
tb(s, 7.9, 5.0, 4.85, 1.4, [(v2b_txt, {"size": 12.5}), ("→ Không cải thiện, không dùng trong bản cuối", {"size": 12.5, "bold": True, "color": ACCENT})])
note(s, "Hình trái: trước (số bản thu theo nhóm câu) và sau cân bằng (tổng trọng số); FLEURS train.", y=6.2)

# 8 ----------------------------------------------------------------- Environment (Bảo)
cfg2 = J("mt/train_config_V2.json")
s = new("Cấu hình môi trường thực nghiệm", "Bảo (~45 giây). Mọi số so sánh chạy trên một máy RTX 4060, cùng thư viện, seed 42. Hai baseline là mô hình công bố chạy zero-shot, "
        "nên learning rate, optimizer, epoch không áp dụng; các thông số đó chỉ có ở V1 đến V3.")
table(s, 0.6, 1.35, [3.3, 8.83], [
    ["Thành phần", "Giá trị"],
    ["Phần cứng", f"{SP2['gpu']} (8 GB) — một máy cho mọi số so sánh và đo tốc độ"],
    ["Framework", f"Python {SP2['python']} · PyTorch {SP2['torch']} · Transformers 5.17.0 · PEFT 0.21.2 · sacreBLEU 2.6.0"],
    ["Seed / độ chính xác", "42 · suy luận FP16, train bf16"],
    ["Baseline A (ASR)", "PhoWhisper-small, Whisper-small · beam 5 · batch 1 · tiếng Việt"],
    ["Baseline B (MT)", "VinAI Translate vi2en (bản của paper) · beam 5"],
    ["LR · optimizer · epoch", "Baseline: không áp dụng (zero-shot, không train)"],
    ["V1 → V3 (LoRA)", f"AdamW · lr {cfg2['lr']:.0e} · warmup {int(cfg2['warmup'] * 100)}% · batch {cfg2['batch']}×{cfg2['grad_accum']} · r {cfg2['r']} · alpha {cfg2['alpha']} · tối đa {cfg2['epochs']}–5 epoch, chọn theo dev"]],
    size=12, first_bold=True, row_h=0.5)

# 9 ----------------------------------------------------------------- Baseline A (Bảo)
rows = [["Mô hình", "Nguồn", "Dataset", "WER", "CER"],
        ["PhoWhisper-small", "Paper (Table 2)", "VIVOS test", "6,33", "–"],
        ["PhoWhisper-small", "Nhóm", "VIVOS test (760)", f(pho["wer_percent"]), f(pho["cer_percent"])],
        ["Whisper-small", "Nhóm (zero-shot)", "VIVOS test (760)", f(wsp["wer_percent"]), f(wsp["cer_percent"])]]
if AF:
    rows += [["PhoWhisper-small", "Nhóm", "FLEURS test (857)", f(AF["PhoWhisper-small"]["metrics"]["wer_percent"]), f(AF["PhoWhisper-small"]["metrics"]["cer_percent"])],
             ["Whisper-small", "Nhóm (zero-shot)", "FLEURS test (857)", f(AF["whisper-small"]["metrics"]["wer_percent"]), f(AF["whisper-small"]["metrics"]["cer_percent"])]]
else:
    rows += [["PhoWhisper-small", "Nhóm (cascade)", "FLEURS test (857)", f(ERR["FLEURS"]["WER"]), "8,58"]]
s = new("Baseline A: Paper và thực nghiệm của nhóm", "Bảo (~50 giây). PhoWhisper-small chạy lại ra 6,25% so với 6,33% của paper. "
        "Chạy lại trên máy và thư viện mới, 760 trên 760 câu giống hệt Task 1. Whisper-small chưa fine-tune tiếng Việt nên sai nhiều hơn.")
table(s, 0.6, 1.35, [2.6, 2.4, 2.6, 1.6, 1.6], rows, size=12.5, hl_rows=(2,), row_h=0.48)
sv, sf_ = ERR["VIVOS"], ERR["FLEURS"]
if AF:  # cùng nguồn với bảng: script đánh giá ASR trên FLEURS
    wc = AF["PhoWhisper-small"]["metrics"]["word_counts"]
    sf_ = {"substitutions": wc["substitutions"], "deletions": wc["deletions"], "insertions": wc["insertions"], "ref_words": wc["reference_units"]}
tb(s, 0.6, 4.6, 12.1, 1.8, [("Tách lỗi WER của PhoWhisper-small (thay thế / xóa / chèn)", {"size": 14, "bold": True}),
    (f"• VIVOS: {sv['substitutions']} / {sv['deletions']} / {sv['insertions']} trên {sv['ref_words']:,} từ".replace(",", "."), {"size": 13}),
    (f"• FLEURS: {sf_['substitutions']:,} / {sf_['deletions']} / {sf_['insertions']:,} trên {sf_['ref_words']:,} từ — lỗi chèn nhiều bất thường (xem slide 11)".replace(",", "."), {"size": 13})])

# 10 ---------------------------------------------------------------- Baseline B (Kiệt)
s = new("Baseline B: Paper và thực nghiệm của nhóm", "Kiệt (~50 giây). VinAI Translate chạy lại trên PhoMT test ra " + f(B0_PHOMT) + " so với 40,42 của paper. "
        "Trên FLEURS, dịch chữ chuẩn được 37,85 nhưng nối sau khối nghe chỉ còn 24,27: mất 13,58 điểm vì lỗi nghe. "
        "Không dùng bản v2 của VinAI vì dữ liệu train của nó trùng tập test PhoMT.")
table(s, 0.6, 1.35, [3.3, 2.2, 3.0, 1.7, 1.7], [
    ["Mô hình", "Nguồn", "Dataset", "BLEU", "chrF++"],
    ["VinAI Translate vi2en", "Paper (Table 1)", "PhoMT test", "40,42", "–"],
    ["VinAI Translate vi2en", "Nhóm", "PhoMT test (19.151)", f(B0_PHOMT) + B0_PHOMT_NOTE, f(B0F["phomt_test"]["chrF++"])],
    ["Dịch chữ chuẩn", "Nhóm", "FLEURS test (857)", f(cln("B0")), f(B0["fleurs_clean"]["chrF++"])],
    ["Cascade A → B (B0)", "Nhóm", "FLEURS test (857)", f(cas("B0")), f(B0["fleurs_cascade"]["chrF++"])]], size=12.5, hl_rows=(4,), row_h=0.5)
label(s, 0.6, 4.4, 3.6, 1.3, f"−{f(cln('B0') - cas('B0'))}", ACCENT, size=36)
tb(s, 4.45, 4.45, 8.3, 1.3, [("BLEU mất đi khi thay chữ chuẩn bằng chữ máy nghe", {"size": 15, "bold": True}),
    ("Đây là vấn đề Proposed Method nhắm tới. Không dùng vinai-translate-vi2en-v2: khoảng 10 nghìn cặp train của bản này nằm trong PhoMT test.", {"size": 12.5})])
if B0_PHOMT_NOTE:
    note(s, "* B0 trên PhoMT chấm với batch 32 / max_length 512; các phiên bản V dùng batch 16/8/4 và giới hạn độ dài ra.", y=6.2)

# 11 ---------------------------------------------------------------- Gap analysis (Bảo)
s = new("Gap Analysis", "Bảo (~55 giây). Kết quả khớp công bố. Bốn nguồn chênh lệch: domain gap giữa VIVOS và FLEURS; cách viết số khi chấm; "
        "môi trường và cấu hình giải mã; và cách gom câu khi dịch. Mỗi nguồn đều có số chứng minh.")
table(s, 0.6, 1.35, [2.55, 4.6, 4.98], [
    ["Nguyên nhân", "Bằng chứng", "Ảnh hưởng"],
    ["Khớp công bố", f"PhoWhisper {f(pho['wer_percent'])} so với 6,33 · VinAI {f(B0_PHOMT)} so với 40,42", "Chênh dưới 0,2 điểm: tái lập thành công"],
    ["Domain gap", f"VIVOS {f(pho['wer_percent'])}% (cùng miền, PhoWhisper đã học VIVOS train) so với FLEURS {f(ERR['FLEURS']['WER'])}%",
     "FLEURS câu dài hơn (12,6 s so với 3,5 s), đọc văn bản Wikipedia"],
    ["Tiền xử lý / chuẩn hóa", "Từ bị chèn nhiều nhất trên FLEURS là số: một, hai, trăm, mươi (\"802\" → \"tám trăm linh hai\")",
     "WER FLEURS bị đội lên vì khác cách viết số, không hoàn toàn do nghe sai"],
    ["Môi trường / giải mã", "Whisper-small 25,91% (Task 1) → 22,26%: 750/760 câu giống hệt; câu R193 hết sinh lặp (293 → 4 từ)",
     "PhoWhisper 760/760 câu giống hệt: kết quả ổn định"],
    ["Cách gom câu khi dịch", "B0 cascade 24,21 → 24,27 khi đổi batch để tránh tràn bộ nhớ", "Mọi phiên bản chấm cùng một script và cấu hình"]],
    size=12.5, first_bold=True, row_h=0.8)

# 12 ---------------------------------------------------------------- Results by data group (Uyên)
wl = ERR["VIVOS"]["wer_by_length"]
bw = ME2["by_asr_wer"]; bd = ME2["by_digits"]
s = new("Kết quả baseline theo nhóm dữ liệu", "Uyên (~50 giây). Chia kết quả theo nhóm dữ liệu: người nói, độ dài, và mức lỗi nghe của câu. "
        "Lỗi nghe càng nhiều thì bản dịch càng kém: câu nghe đúng hoàn toàn được 30 BLEU, câu nghe sai trên 30% chỉ còn khoảng 10. Câu có số kém nhất.")
table(s, 0.6, 1.35, [3.4, 1.4, 1.4], [
    ["VIVOS (PhoWhisper)", "Số câu", "WER"],
    ["Câu < 3 giây", str(wl["<3 s"]["n"]), f(wl["<3 s"]["WER"])],
    ["Câu 3–5 giây", str(wl["3–5 s"]["n"]), f(wl["3–5 s"]["WER"])],
    ["Câu ≥ 5 giây", str(wl["≥5 s"]["n"]), f(wl["≥5 s"]["WER"])],
    ["Người nói tốt nhất", "VIVOSDEV19", "0,78"],
    ["Người nói kém nhất", "VIVOSDEV10", "24,93"]], size=12, first_bold=True, row_h=0.45)
table(s, 7.0, 1.35, [3.35, 1.1, 1.3], [
    ["FLEURS, cascade B0", "Số câu", "BLEU"],
    ["Nghe đúng hoàn toàn", str(bw["WER 0"]["n"]), f(bw["WER 0"]["BLEU_B0"])],
    ["WER 0–10%", str(bw["WER 0–10"]["n"]), f(bw["WER 0–10"]["BLEU_B0"])],
    ["WER 10–30%", str(bw["WER 10–30"]["n"]), f(bw["WER 10–30"]["BLEU_B0"])],
    ["WER > 30%", str(bw["WER >30"]["n"]), f(bw["WER >30"]["BLEU_B0"])],
    ["Câu có chữ số", str(bd["có số"]["n"]), f(bd["có số"]["BLEU_B0"])]], size=12, first_bold=True, row_h=0.45)
note(s, "Câu ngắn dưới 3 giây sai nhiều hơn (ít ngữ cảnh). Độ khó giữa người nói chênh 30 lần — số trung bình che mất người nói khó.", y=4.4, color=INK)

# 13 ---------------------------------------------------------------- V1 architecture (Kiệt)
c1 = J("mt/train_config_V1.json")
s = new("Proposed Method: kiến trúc (V1 → V3)", "Kiệt (~55 giây). Khối nghe giữ nguyên. Khối dịch được dạy thêm bằng LoRA trên cặp chữ do PhoWhisper nghe ra từ FLEURS train và câu Anh đúng, "
        "để khối dịch quen với lỗi nghe thật. LoRA chỉ train khoảng 1% tham số, adapter 18 MB.")
pic(s, "figures/architecture.png", 0.6, 1.3, w=12.1)
tb(s, 0.6, 6.25, 12.1, 0.6, [(f"LoRA r {c1['r']}, alpha {c1['alpha']}, gắn vào q/k/v/out_proj · {c1['trainable_params']:,} / {c1['total_params']:,} tham số ({f(100 * c1['trainable_params'] / c1['total_params'], 2)}%) · "
                              f"V1: {c1['train_pairs']:,} cặp chữ máy nghe (WER 11,35%), chọn epoch trên {c1['dev_pairs']} câu dev".replace(",", "."), {"size": 12})])

# 14 ---------------------------------------------------------------- V1 results (Kiệt)
s1 = SIG["V1"]["sentence_cluster"]
s = new("Kết quả V1 và tín hiệu cải thiện", "Kiệt (~55 giây). V1 tăng 4,32 BLEU trên chỉ số chính, kiểm định bootstrap p nhỏ hơn 0,001. "
        "Đường cong cho thấy overfit từ epoch 2, nên chọn epoch 1 theo dev. Mặt trái: PhoMT giảm 2,37, tức V1 quên một phần cách dịch văn bản sạch.")
table(s, 0.6, 1.35, [3.1, 1.45, 1.45], [
    ["Chỉ số (test)", "B0", "V1"],
    ["BLEU cascade FLEURS", f(cas("B0")), f(cas("V1"))],
    ["chrF++ cascade", f(B0["fleurs_cascade"]["chrF++"]), f(V1["fleurs_cascade"]["chrF++"])],
    ["BLEU chữ chuẩn", f(cln("B0")), f(cln("V1"))],
    ["BLEU PhoMT", f(B0_PHOMT) + B0_PHOMT_NOTE, f(phomt("V1"))]], size=12.5, first_bold=True, hl_rows=(1,), row_h=0.48)
tb(s, 0.6, 4.0, 6.0, 2.4, [("Tín hiệu cải thiện: CÓ", {"size": 15, "bold": True, "color": ACCENT}),
    (f"• ΔBLEU {f(s1['delta_BLEU_mean'])}, khoảng tin cậy 95% [{f(s1['delta_BLEU_CI95'][0])}; {f(s1['delta_BLEU_CI95'][1])}], p < 0,001", {"size": 12.5}),
    ("• Bootstrap 1.000 lần, lấy mẫu theo cụm câu gốc", {"size": 12.5}),
    ("• Mặt trái: PhoMT giảm, V1 quên văn bản sạch", {"size": 12.5})])
pic(s, "figures/curves_V1.png", 6.85, 1.3, w=5.9)

# 15 ---------------------------------------------------------------- ASR failures (Bảo)
s = new("Lỗi nghe mà V1 chưa sửa được", "Bảo (~55 giây). V1 không đổi khối nghe, nên các lỗi nghe vẫn còn. Ba loại lỗi chính: tên riêng, nhất là tên nước ngoài; "
        "số bị đọc thành chữ; và nhầm dấu thanh, nhiều nhất là thanh ngang thành thanh sắc. V1 dịch lại đúng được một phần, phần còn lại vẫn sai.")
pic(s, "asr/tone_confusion_FLEURS.png", 0.6, 1.3, h=4.4)
table(s, 6.6, 1.35, [3.6, 1.2, 1.33], [
    ["Loại từ (FLEURS test)", "Số từ", "Nghe đúng"],
    ["Từ thường", f"{NE['common_word_tokens']:,}".replace(",", "."), f"{f(NE['common_word_recall_percent'], 1)}%"],
    ["Tên riêng", f"{NE['named_entity_tokens']:,}".replace(",", "."), f"{f(NE['named_entity_recall_percent'], 1)}%"],
    ["Tên nước ngoài", str(NE["foreign_name_tokens"]), f"{f(NE['foreign_name_recall_percent'], 1)}%"]], size=12, first_bold=True, hl_rows=(3,), row_h=0.45)
tb(s, 6.6, 3.4, 6.1, 2.4, [("Ví dụ lỗi nghe còn lại", {"size": 14, "bold": True}),
    ("• \"Aristotle\" → \"erik stone\" (V1, V2 dịch theo tên sai)", {"size": 12.5}),
    ("• \"802.11n\" → \"tám không hai chấm một một in\": số đọc thành chữ", {"size": 12.5}),
    (f"• Nhầm dấu thanh chỉ chiếm {f(ERR['FLEURS']['tone_only_share_of_substitutions_percent'], 1)}% lỗi thay thế trên FLEURS ({f(ERR['VIVOS']['tone_only_share_of_substitutions_percent'], 1)}% trên VIVOS)", {"size": 12.5})])
note(s, "Ma trận nhầm dấu thanh (bỏ đường chéo) thay cho Confusion Matrix của bài phân loại.", y=5.85)

# 16 ---------------------------------------------------------------- MT failures (Kiệt)
s = new("Failure cases V1: lỗi dịch", "Kiệt (~50 giây). Bốn nguyên nhân lỗi dịch của V1: số đọc thành chữ gây sinh lặp; bỏ sót ý; quên văn bản sạch; "
        "và một phần cải thiện là do quen văn phong FLEURS chứ không chỉ do chịu lỗi nghe.")
table(s, 0.6, 1.35, [2.7, 9.43], [
    ["Nguyên nhân", "Ví dụ / bằng chứng"],
    ["Số đọc thành chữ → sinh lặp", "Máy nghe \"chuẩn tám không hai chấm một một … hai chấm bốn đi ra hệ\" (đúng: 802.11n … 2.4GHz) → V1 lặp \"one, one, two, one…\" tới giới hạn độ dài"],
    ["Bỏ sót, đơn giản hóa", "\"không nhất thiết phải cần\" → V1 bỏ \"necessarily\"; \"quần đảo\" → \"islands\" thay vì \"archipelagos\""],
    ["Quên văn bản sạch", f"BLEU PhoMT {f(B0_PHOMT)} → {f(phomt('V1'))} vì chỉ dạy trên FLEURS"],
    ["Thích nghi miền", f"Câu nghe đúng hoàn toàn cũng tăng {f(ME1['by_asr_wer']['WER 0']['BLEU_V1'] - ME1['by_asr_wer']['WER 0']['BLEU_B0'])} BLEU: V1 còn quen văn phong FLEURS"]],
    size=12, first_bold=True, row_h=0.72)
tb(s, 0.6, 5.2, 12.1, 1.0, [(f"So từng câu với B0 (chênh chrF++ trên 1 điểm): V1 tốt lên {J('mt/mt_errors_V1.json')['sentences_better']} câu, "
                             f"kém đi {J('mt/mt_errors_V1.json')['sentences_worse']} câu, như cũ {J('mt/mt_errors_V1.json')['sentences_same']} câu", {"size": 13})])

# 17 ---------------------------------------------------------------- V2/V3 (Kiệt)
def best(v): return max(r["dev_bleu"] for r in LOG[v]) if v in LOG else None
rows = [["Phiên bản", "Thay đổi", "Lý do (từ phân tích lỗi)", "Dev BLEU", "Quyết định"],
        ["V2", "+ 1.449 cặp chữ chuẩn + 3.000 cặp PhoMT", "V1 overfit, quên văn bản sạch", f(best("V2")), "Nhận"],
        ["V2b", "V2 + cân bằng theo câu", "Mất cân bằng số bản thu mỗi câu", f(best("V2b")) if best("V2b") else "–", "Không: kém V2"]]
if "V2_itn" in DEV:
    rows.append(["V3a", "V2 + chuẩn hóa số khi dịch", "Lỗi số đọc thành chữ", f"{f(DEV['V2']['BLEU'])} → {f(DEV['V2_itn']['BLEU'])}", "Không: dev giảm"])
if "V3" in DEV:
    rows.append(["V3", "Chuẩn hóa số cả khi dạy lẫn khi dịch", "V3a lệch dữ liệu dạy và dịch", f(DEV["V3"]["BLEU"]) + " (so V2 " + f(DEV["V2"]["BLEU"]) + ")",
                 "Nhận" if "V3" in EV else "Không"])
s = new("Đề xuất cải tiến V2, V3", "Kiệt (~55 giây). Mỗi phiên bản sửa một lỗi tìm thấy ở bản trước và chỉ đổi một thứ. Mọi quyết định nhận hay bỏ đều dựa trên tập dev, "
        "không nhìn tập test. Bản cuối cũng được chọn trên PhoMT dev: phiên bản giảm quá 1 điểm so với B0 bị loại.")
table(s, 0.6, 1.35, [1.2, 3.7, 3.3, 2.1, 1.83], rows, size=11.5, first_bold=True, row_h=0.62)
sel = SEL
tb(s, 0.6, 1.5 + 0.62 * len(rows), 12.1, 1.2, [("Chọn bản cuối trên validation", {"size": 14, "bold": True}),
    (f"PhoMT dev (2.000 câu): B0 {f(sel['B0']['BLEU'])} · V1 {f(sel['V1']['BLEU'])} (giảm {f(sel['B0']['BLEU'] - sel['V1']['BLEU'])}, loại) · "
     f"V2 {f(sel['V2']['BLEU'])} (giảm {f(sel['B0']['BLEU'] - sel['V2']['BLEU'])}, đạt)" + (f" · V3 {f(SEL3['V3']['BLEU'])}" if SEL3 else ""), {"size": 13})])

# 18 ---------------------------------------------------------------- Ablation (Bảo)
abl = J("ablation.json")
rows = [["Phiên bản", "BLEU cascade", "chrF++", "Δ so với B0", "BLEU chữ chuẩn", "BLEU PhoMT"]]
for r in abl:
    rows.append([r["version"], f(r["fleurs_cascade_BLEU"]), f(r["fleurs_cascade_chrF++"]), ("+" if r["delta_vs_B0"] > 0 else "") + f(r["delta_vs_B0"]),
                 f(r["fleurs_clean_BLEU"]) if r["fleurs_clean_BLEU"] is not None else "–",
                 (f(r["phomt_BLEU"]) + (B0_PHOMT_NOTE if r["version"] == "B0" else "")) if r["phomt_BLEU"] is not None else "–"])
final_row = [i for i, r in enumerate(abl, 1) if r["version"] == ("V3" if "V3" in EV else "V2")]
s = new("Ablation Study", "Bảo (~55 giây). Cùng tập test, cùng metric, cùng script chấm. Mỗi dòng chỉ thêm một thay đổi. V1 cao nhất trên cascade nhưng quên văn bản sạch; "
        "bản cuối giữ được cải thiện có ý nghĩa thống kê mà PhoMT gần như không giảm.")
table(s, 0.6, 1.35, [1.4, 1.6, 1.2, 1.5, 1.6, 1.5], rows, size=12, first_bold=True, hl_rows=tuple(final_row), row_h=0.48)
pic(s, "figures/ablation_bleu.png", 9.35, 1.3, w=3.4)
sig_rows = [["So với B0", "ΔBLEU", "KTC 95%", "p"]]
for v in ("V1", "V2", "V2b", "V3"):
    if v in SIG:
        g = SIG[v]["sentence_cluster"]
        sig_rows.append([v, f(g["delta_BLEU_mean"]), f"[{f(g['delta_BLEU_CI95'][0])}; {f(g['delta_BLEU_CI95'][1])}]", "< 0,001" if g["p_value_BLEU"] == 0 else f(g["p_value_BLEU"], 3)])
table(s, 0.6, 1.5 + 0.48 * len(rows), [1.6, 1.4, 2.6, 1.4], sig_rows, size=11.5, first_bold=True, row_h=0.4)
if has("mt/seed_robustness_V3.json"):
    SR = J("mt/seed_robustness_V3.json")
    tb(s, 7.85, 1.65 + 0.48 * len(rows), 4.9, 2.2, [("Độ ổn định theo seed (V3)", {"size": 13, "bold": True}),
        (f"• Seed 42 / 13 / 7: " + " / ".join(f(v["cascade_BLEU"]) for v in SR["runs"].values()), {"size": 12}),
        (f"• Trung bình {f(SR['cascade_mean'])} ± {f(SR['cascade_std'])}; kém nhất vẫn hơn B0 {f(SR['min_gain_vs_B0'])}", {"size": 12}),
        ("• V3 hơn V2 trên toàn tập nhỏ hơn dao động seed; đóng góp rõ ở câu có chữ số (+1,06)", {"size": 12})])

# 19 ---------------------------------------------------------------- Visual results (Đăng)
s = new("Kết quả đầu ra tiêu biểu", "Đăng (~50 giây). Ví dụ được chọn tự động theo chrF++ từng câu, không chọn tay. "
        "Hai câu đầu là câu bản cuối tốt lên nhiều nhất so với B0; câu cuối là câu bản cuối vẫn sai nặng, thường do khối nghe sai tên riêng nên khối dịch không cứu được.")
ex = VR["tốt lên"][:2] + VR["vẫn sai"][:1]
y = 1.3
for k, r in enumerate(ex):
    tag = f"{FIN} TỐT LÊN" if k < 2 else f"{FIN} VẪN SAI"
    label(s, 0.6, y, 1.6, 0.35, tag, ACCENT if k < 2 else WARN, size=10)
    tb(s, 2.35, y - 0.03, 10.4, 1.75, [(f"Máy nghe: {r['asr']}", {"size": 11, "color": MID}),
        (f"Tham chiếu: {r['en_ref']}", {"size": 11.5}),
        (f"B0: {r['B0']}", {"size": 11.5}),
        (f"{FIN}: {r['final']}", {"size": 11.5, "bold": True})], space=1)
    y += 1.85

# 20 ---------------------------------------------------------------- Speed (Đăng)
a0, a2 = SP0["short_utterances"], SP2["short_utterances"]
l0, l2 = SP0["long_audio"], SP2["long_audio"]
z = SP2["size"]
s = new("Tốc độ và dung lượng", "Đăng (~50 giây). Đo trên máy rảnh, 100 bản thu FLEURS test, câu trung bình 12,8 giây. RTF khoảng 0,34: xử lý nhanh gấp khoảng 3 lần thời gian thực. "
        "LoRA gộp vào trọng số nên V2 chạy như B0. Âm thanh dài có VAD nhanh hơn không VAD khoảng 30%.")
table(s, 0.6, 1.35, [3.6, 2.1, 2.1], [
    ["Chỉ số", "B0", f"{SP2_NAME} (bản cuối)"],
    ["RTF toàn hệ thống", f(a0["rtf_total"], 3), f(a2["rtf_total"], 3)],
    ["RTF nghe / dịch", f"{f(a0['rtf_asr'], 3)} / {f(a0['rtf_mt'], 3)}", f"{f(a2['rtf_asr'], 3)} / {f(a2['rtf_mt'], 3)}"],
    ["Độ trễ trung vị / p95 (giây)", f"{f(a0['latency_median_s'])} / {f(a0['latency_p95_s'])}", f"{f(a2['latency_median_s'])} / {f(a2['latency_p95_s'])}"],
    ["VRAM đỉnh", f"{SP0['size']['gpu_peak_allocated_mb']:,.0f} MB".replace(",", "."), f"{z['gpu_peak_allocated_mb']:,.0f} MB".replace(",", ".")],
    ["Âm thanh dài 249 s: có VAD", f"RTF {f(l0['vad']['rtf'], 3)}", f"RTF {f(l2['vad']['rtf'], 3)}"],
    ["Âm thanh dài 249 s: không VAD", f"RTF {f(l0['no_vad']['rtf'], 3)}", f"RTF {f(l2['no_vad']['rtf'], 3)}"]], size=12, first_bold=True, hl_rows=(1,), row_h=0.48)
table(s, 8.6, 1.35, [2.2, 1.93], [
    ["Dung lượng", "Giá trị"],
    ["ASR", f"{z['asr_weights_mb']:,.0f} MB".replace(",", ".")],
    ["MT", f"{z['mt_weights_mb']:,.0f} MB".replace(",", ".")],
    ["Adapter LoRA", f"{f(z['adapter_mb'], 0)} MB"],
    ["Tham số ASR", f"{f(z['asr_params'] / 1e6, 1)} triệu"],
    ["Tham số MT", f"{f(z['mt_params'] / 1e6, 1)} triệu"]], size=12, first_bold=True, row_h=0.48)
note(s, f"{SP2['gpu']} · FP16 · từng câu một · không tính thời gian nạp mô hình.", y=5.0)

# 21 ---------------------------------------------------------------- Feasibility (Đăng)
s = new("Đánh giá tính khả thi", "Đăng (~55 giây). Tiêu chí đặt trước khi đo. Đạt bốn trên năm: chất lượng, tốc độ, bộ nhớ, âm thanh dài. "
        "Chưa đạt độ trễ dưới 3 giây cho câu khoảng 13 giây; Task 3 sẽ cắt đoạn ngắn hơn ở chế độ micro. Kết luận: khả thi để làm demo.")
fin = FIN
table(s, 0.6, 1.35, [2.5, 4.2, 3.9, 1.53], [
    ["Tiêu chí", "Ngưỡng (đặt trước)", f"Bản cuối {fin}", "Đạt?"],
    ["Chất lượng", "Hơn B0 trên cascade; PhoMT giảm ≤ 1 điểm", f"{f(cas(fin))} so với {f(cas('B0'))}; PhoMT dev {f(SELF['BLEU'])} (B0 {f(SEL['B0']['BLEU'])})", "Đạt"],
    ["Tốc độ", "RTF < 1", f"{f(a2['rtf_total'], 3)} (âm thanh dài, VAD: {f(l2['vad']['rtf'], 3)})", "Đạt"],
    ["Độ trễ", "Trung vị < 3 giây / câu", f"{f(a2['latency_median_s'])} giây (câu TB 12,8 giây)", "Chưa"],
    ["Bộ nhớ", "VRAM < 8 GB", f"{z['gpu_peak_allocated_mb']:,.0f} MB".replace(",", "."), "Đạt"],
    ["Âm thanh dài", "Có VAD, xử lý vài phút", f"249 giây, {l2['vad']['segments']} đoạn", "Đạt"]], size=12, first_bold=True, row_h=0.52)
label(s, 0.6, 4.75, 3.0, 1.1, "KHẢ THI", ACCENT, size=28)
tb(s, 3.85, 4.75, 8.9, 1.5, [("Triển khai dự kiến ở Task 3: web Gradio trên máy có GPU (laptop RTX 4060 hoặc Hugging Face Spaces có GPU)", {"size": 13}),
    ("Hạn chế: chưa thử micro điện thoại và giọng nữ ở tập test; tên nước ngoài và số đọc thành chữ vẫn là điểm yếu", {"size": 13})])

# 22 ---------------------------------------------------------------- Task 3 plan (Đăng)
s = new("Kế hoạch thực hiện Task 3", "Đăng (~45 giây). Task 3 đóng gói bản cuối thành demo Gradio có tải file và micro, thêm API, Docker và báo cáo cuối. "
        "Phân công giữ theo chuyên môn ở Task 1 và Task 2.")
table(s, 0.6, 1.35, [3.0, 6.6, 2.53], [
    ["Hạng mục", "Nội dung", "Phụ trách"],
    ["Demo Gradio (bắt buộc)", "Tab tải file và tab micro; hiển thị song song Việt | Anh kèm mốc thời gian", "Đăng"],
    ["Real-time, âm thanh dài", "VAD cắt đoạn ngắn để giảm độ trễ; hiển thị theo từng đoạn", "Đăng, Bảo"],
    ["API (điểm cộng)", "FastAPI /transcribe, /translate, /speech-translate; schema, xử lý lỗi", "Kiệt"],
    ["Docker, CI/CD (điểm cộng)", "Dockerfile, GitHub Actions, deploy Hugging Face Spaces", "Kiệt"],
    ["Cải tiến mô hình", "Tên riêng, số đọc thành chữ; thử giọng nữ, micro điện thoại", "Bảo, Kiệt"],
    ["Báo cáo cuối, video", "Báo cáo 15–25 trang; video demo 2–5 phút; bảng đóng góp", "Uyên, cả nhóm"]], size=12, first_bold=True, row_h=0.6)

# 23 ---------------------------------------------------------------- Thanks
s = new("", "Cả nhóm (~20 giây). Cảm ơn thầy đã lắng nghe. Nhóm sẵn sàng trả lời câu hỏi.", dark=True)
dots(s, 9.85, 0.55, 13, 6)
tb(s, 0.8, 2.3, 11.5, 1.2, [("Cảm ơn thầy và các bạn", {"size": 40, "bold": True, "color": WHITE})])
tb(s, 0.8, 3.6, 11.5, 0.8, [("Q&A", {"size": 26, "color": WHITE})])
tb(s, 0.8, 5.2, 11.5, 0.8, [("Code, số liệu và nhật ký thực nghiệm: github.com/lekithaha06/DPL302m", {"size": 14, "color": WHITE})])

assert COUNT[0] == TOTAL, COUNT[0]
os.makedirs(os.path.dirname(OUT), exist_ok=True)
prs.save(OUT)
print("saved", OUT, COUNT[0], "slides")
