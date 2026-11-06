"""Hàm chung: đọc số từ file kết quả task3 và sửa docx/pptx giữ định dạng run."""
import copy, csv, json, re, statistics, sys
from pathlib import Path

TW = Path(__file__).resolve().parents[2]; T = TW / "task3"; G = TW / "dang_test3/goc"; O = TW / "tai_lieu_nhom_V2"; H = O / "6_hinh"
sys.stdout.reconfigure(encoding="utf-8")
J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
vn = lambda x, d=2: f"{float(x):.{d}f}".replace(".", ",")
en = lambda x, d=2: f"{float(x):.{d}f}"
sc = lambda v, s: J(T / f"runs/mt/{v}/{s}/score.json")
bs = lambda f: J(T / f"reports/mt/{f}.json")


def ci(b, f=vn):
    a, c = b["ci95"]; s = (lambda x: f(x).replace("-", "−"))
    return f"[{s(a)}; {s(c)}]" if f is vn else f"[{s(a)}, {s(c)}]"


def lap(v):
    return [J(p) for p in sorted((T / "reports/toc_do/lap_V2").glob(f"toc_do_{v}_lan*.json"))]


def td(v):
    L = lap(v); m = lambda k: statistics.median(x[k] for x in L)
    return dict(rtf=m("RTF_total"), asr=m("RTF_asr"), mt=m("RTF_mt"), p50=m("latency_p50_s"), p95=m("latency_p95_s"), vram=max(x["gpu_peak_allocated_bytes"] for x in L) / 2**30,
                ram=max(x["ram_rss_peak_bytes"] for x in L) / 2**30, size=(L[0]["asr_checkpoint_bytes"] + L[0]["mt_checkpoint_bytes"] + L[0]["adapter_bytes"]) / 1e9, lan=[x["RTF_total"] for x in L])


class S:
    """Mọi số dùng chung, đọc từ file."""
    c, cl, ph = sc("V2", "fleurs_test_asr_pho"), sc("V2", "fleurs_test_clean"), sc("V2", "phomt_test")
    b0c, b0s = sc("B0", "fleurs_test_asr_pho"), sc("B0", "fleurs_test_clean")
    w = sc("V2", "fleurs_test_asr_wsp"); b1 = sc("B1_whisper-small_translate", "fleurs_test_audio")
    d = bs("bootstrap_B0_V2_cascade_test"); dw = bs("bootstrap_B0_V2_cascade_wsp_test"); db1 = bs("bootstrap_B0_fleurs_test_asr_pho_vs_B1")
    ht = J(T / "reports/he_thong_V2/ket_qua.json"); hb = J(T / "reports/he_thong_V2/bootstrap_cu_vs_moi.json")
    t0, t2 = td("B0"), td("V2")
    ab = {r["bản"].split(" ")[0]: r for r in csv.DictReader(open(T / "reports/ablation/bang_ablation.csv", encoding="utf-8-sig"))}
    mien = {r["mien"].split(" (")[0]: r for r in csv.DictReader(open(T / "reports/domain/ket_qua_theo_mien.csv", encoding="utf-8-sig")) if r["khoi"] == "MT" and r["he"] == "V2" and r["tap"] == "fleurs_test_asr_pho"}
    mien0 = {r["mien"].split(" (")[0]: r for r in csv.DictReader(open(T / "reports/domain/ket_qua_theo_mien.csv", encoding="utf-8-sig")) if r["khoi"] == "MT" and r["he"] == "B0" and r["tap"] == "fleurs_test_asr_pho"}
    tat = ht["proposed"]["tat_ca"]; dai = ht["proposed"]["dai"]
    gap = b0s["BLEU"] - c["BLEU"]; dcl = cl["BLEU"] - b0s["BLEU"]
    assert round(b0s["BLEU"] - b0c["BLEU"], 2) == 15.58
    giao = float(mien["Giáo dục"]["BLEU"]); tin = float(mien["Tin tức"]["BLEU"]); dl = float(mien["Du lịch"]["BLEU"])
    giao0 = float(mien0["Giáo dục"]["BLEU"])


class B3:
    """Số 3 seed, đọc từ reports/ba_seed."""
    R = list(csv.DictReader(open(T / "reports/ba_seed/bang_3seed.csv", encoding="utf-8-sig")))
    A = list(csv.DictReader(open(T / "reports/ba_seed/bang_ablation_3seed.csv", encoding="utf-8-sig")))
    KQ = J(T / "reports/ba_seed/ket_qua_3seed.json")

    @classmethod
    def m(cls, v, k):
        return next(float(r["trung bình"]) for r in cls.R + cls.A if r["bản"] == v and r["chỉ số"] == k)

    @classmethod
    def sd(cls, v, k):
        return next(float(r["độ lệch chuẩn"]) for r in cls.R + cls.A if r["bản"] == v and r["chỉ số"] == k)

    @classmethod
    def vi(cls, v, k):
        return f"{vn(cls.m(v, k))} ± {vn(cls.sd(v, k))}"

    @classmethod
    def eng(cls, v, k):
        return f"{en(cls.m(v, k))} ± {en(cls.sd(v, k))}"

    @classmethod
    def d(cls, v, k):
        return next(r["Δ so với V2 (cùng seed, trung bình)"].split(" (")[0] for r in cls.A if r["bản"] == v and r["chỉ số"] == k)

    @classmethod
    def seed(cls, v, k, s):
        return float(next(r[f"seed {s}"] for r in cls.R if r["bản"] == v and r["chỉ số"] == k))


D0 = [B3.seed("V2", "test cascade", s) - S.b0c["BLEU"] for s in (42, 1, 2)]
D_TB, D_SD = statistics.mean(D0), statistics.stdev(D0)
SACH_TB = B3.m("V2", "test sạch") - S.b0s["BLEU"]
DC = B3.KQ["doi_chung_phan_cung_V2_s42"]


def robust():
    """Kết quả đo độ bền; thiếu điều kiện nào trả None ở điều kiện đó."""
    ten = [("noise_snr20", "nhiễu trắng SNR 20 dB", "white noise, SNR 20 dB"), ("noise_snr10", "nhiễu trắng SNR 10 dB", "white noise, SNR 10 dB"), ("speed_0.9", "chậm lại 0,9 lần", "speed 0.9×"),
           ("speed_1.1", "nhanh lên 1,1 lần", "speed 1.1×"), ("vol_-12dB", "giảm âm lượng 12 dB", "gain −12 dB")]
    goc = J(T / "runs/asr/kiet_t2_phowhisper-small_fleurs_test/score/summary.json")
    kq = [("goc", "bản gốc", "original", goc)]
    for k, v, e in ten:
        p = T / f"runs/robust/robust_pho_{k}/score/summary.json"
        kq.append((k, v, e, J(p) if p.exists() else None))
    return kq


# ---- docx
def _gop(p):
    return "".join(r.text for r in p.runs)


def sub(p, cu, moi):
    """Thay chuỗi trong đoạn, kể cả khi vắt qua nhiều run; phần mới nhận định dạng của run đầu."""
    t = _gop(p); i = t.find(cu)
    if i < 0:
        return False
    k = 0  # bỏ phần đầu giống nhau để chữ mới giữ đúng định dạng của run chứa chỗ đổi
    while k < min(len(cu), len(moi)) - 1 and cu[k] == moi[k]:
        k += 1
    i += k; cu, moi = cu[k:], moi[k:]
    j = i + len(cu); pos = 0; dau = True
    for r in p.runs:
        a, b = pos, pos + len(r.text); pos = b
        if b <= i or a >= j:
            continue
        x, y = max(i, a) - a, min(j, b) - a
        r.text = r.text[:x] + (moi if dau else "") + r.text[y:]; dau = False
    return True


def tat_ca_doan(d):
    for p in d.paragraphs:
        yield p
    for t in d.tables:
        for r in t.rows:
            for c in r.cells:
                yield from c.paragraphs


def thay(d, cap, chi=None):
    """cap: [(cũ, mới)]; mọi cặp phải trúng ít nhất một lần."""
    for cu, moi in cap:
        n = 0
        for p in (chi if chi is not None else tat_ca_doan(d)):
            while cu in _gop(p):
                sub(p, cu, moi); n += 1
                if cu in moi:
                    break
        assert n, f"KHÔNG TRÚNG: {cu}"


def tim(d, dau):
    k = [p for p in d.paragraphs if p.text.startswith(dau)]
    assert len(k) == 1, f"{dau}: {len(k)} đoạn"
    return k[0]


def dat(p, text):
    """Đặt lại nội dung đoạn; run đầu đậm là tiêu đề chạy thì giữ nếu text bắt đầu bằng nó."""
    R = p.runs; r0 = R[0]
    if len(R) > 1 and r0.text and text.startswith(r0.text) and r0.bold:
        tu = R[1]; tu.text = text[len(r0.text):]; bo = R[2:]
    else:
        r0.text = text; bo = R[1:]
    for r in bo:
        r._r.getparent().remove(r._r)


def chen_sau(anchor, text, kieu=None):
    """Chèn đoạn mới sau anchor (paragraph hoặc table), chép định dạng từ kieu."""
    goc = kieu or anchor
    el = copy.deepcopy(goc._p)
    (anchor._p if hasattr(anchor, "_p") else anchor._tbl).addnext(el)
    from docx.text.paragraph import Paragraph
    q = Paragraph(el, goc._parent); da_dam = bool(q.runs and q.runs[0].bold); dat(q, text)
    for r in q.runs[1:]:
        r._r.getparent().remove(r._r)
    r0 = q.runs[0]; r0.text = text; r0.bold = None
    m = re.match(r"^[^.]{3,45}\.\s", text)
    if da_dam and m:  # giữ kiểu tiêu đề chạy: câu ngắn đầu đoạn in đậm
        r2 = copy.deepcopy(r0._r); r0._r.addnext(r2)
        q.runs[1].text = text[m.end(0) - 1:]; q.runs[1].bold = None
        r0.text = text[:m.end(0) - 1]; r0.bold = True
    return q


def xoa(x):
    el = x._p if hasattr(x, "_p") else x._tbl
    el.getparent().remove(el)


def o(cell, text):
    p = cell.paragraphs[0]
    if p.runs:
        dat(p, text)
    else:
        p.add_run(text)
    for q in cell.paragraphs[1:]:
        q._p.getparent().remove(q._p)


def hang(t, i, *gt):
    for c, v in zip(t.rows[i].cells, gt):
        if v is not None:
            o(c, v)


def them_hang(t, sau, *gt):
    tr = copy.deepcopy(t.rows[sau]._tr); t.rows[sau]._tr.addnext(tr)
    hang(t, sau + 1, *gt)


def chep_bang(t, sau, hangs):
    """Tạo bảng mới chép từ t, đặt sau phần tử `sau`, đủ số hàng trong hangs."""
    from docx.table import Table
    el = copy.deepcopy(t._tbl); (sau._p if hasattr(sau, "_p") else sau._tbl).addnext(el)
    n = Table(el, t._parent)
    while len(n.rows) > len(hangs):
        el.remove(n.rows[-1]._tr)
    while len(n.rows) < len(hangs):
        them_hang(n, len(n.rows) - 1, *hangs[0])
    for i, h in enumerate(hangs):
        hang(n, i, *h)
    for rw in n.rows[1:]:  # bảng chép có thể mang theo ô in đậm của bảng gốc
        for c in rw.cells:
            for r in c.paragraphs[0].runs:
                r.bold = None
    return n


def doi_hinh(d, thu_tu, tep):
    """Thay ảnh thứ thu_tu (theo inline_shapes), giữ chiều rộng, tính lại chiều cao."""
    from PIL import Image
    s = d.inline_shapes[thu_tu]
    rid = s._inline.graphic.graphicData.pic.blipFill.blip.embed
    d.part.related_parts[rid]._blob = Path(tep).read_bytes()
    w, h = Image.open(tep).size
    s.height = int(s.width * h / w)


def tach_dam(d, dau, lead):
    """Đoạn bị đậm cả đoạn: chỉ giữ đậm phần lead."""
    p = tim(d, dau); t = p.text; assert t.startswith(lead)
    R = p.runs
    for r in R[1:]:
        r._r.getparent().remove(r._r)
    r0 = p.runs[0]; r2 = copy.deepcopy(r0._r); r0._r.addnext(r2)
    r0.text = lead; p.runs[1].text = t[len(lead):]; p.runs[1].bold = None
