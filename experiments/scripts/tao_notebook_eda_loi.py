#!/usr/bin/env python3
"""Sinh notebooks/eda.ipynb và notebooks/phan_tich_loi.ipynb (03/11/2026).

Notebook CHỈ đọc kết quả đã có (reports/, runs/), không chạy model, không gõ tay số. Tự tìm thư mục gốc:
  - task3/notebooks/   → dữ liệu ở task3/
  - <repo>/notebooks/  → dữ liệu ở <repo>/experiments/ (gói sản phẩm)
Chạy: env/.venv/Scripts/python.exe scripts/tao_notebook_eda_loi.py   (sinh + chạy để lưu kết quả trong file)
"""
import sys
from pathlib import Path

import nbformat as nbf

T = Path(__file__).resolve().parents[1]
OUT = T / "notebooks"

SETUP = r'''
import json, csv, re
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
from IPython.display import Image, Markdown, display

# Tìm thư mục gốc chứa reports/ (task3/ hoặc experiments/ của repo sản phẩm)
ung_vien = [Path.cwd().parent / "experiments", Path.cwd().parent, Path.cwd(), Path(r"D:\CAIDCM\teamwork\task3")]
BASE = next(c for c in ung_vien if (c / "reports" / "data" / "eda").exists())
R = BASE / "reports"
print("Đọc kết quả từ:", BASE)
pd.set_option("display.max_colwidth", 120); pd.set_option("display.width", 200)
plt.rcParams.update({"figure.dpi": 110, "axes.grid": True, "grid.alpha": .3, "axes.spines.top": False, "axes.spines.right": False})
XANH, CAM, XAM, LUC = "#0E7C86", "#B36B00", "#8A939C", "#2E7D32"
doc = lambda p: pd.read_csv(p, encoding="utf-8-sig")
J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
'''


def nb(cells):
    out = []
    for kind, src in cells:
        out.append(nbf.v4.new_markdown_cell(src.strip()) if kind == "md" else nbf.v4.new_code_cell(src.strip()))
    return nbf.v4.new_notebook(cells=out, metadata={
        "kernelspec": {"name": "task3-dpl302m", "display_name": "Python (task3 DPL302m)", "language": "python"},
        "language_info": {"name": "python"}})


# =====================================================================  EDA
EDA = [
    ("md", """
# EDA – Thống kê mô tả dữ liệu (Đề tài 1, miền Giáo dục)

Dữ liệu: **VIVOS** (ASR), **FLEURS vi_vn + en_us** (ASR + câu Anh song song), **PhoMT** (song ngữ), nhãn miền **FLoRes+**.
Pipeline dữ liệu `scripts/data/viec1`–`viec4`, chạy trên dữ liệu tải mới 29–30/10/2026 (tái lập đúng hash).
Notebook chỉ **đọc bảng kết quả** trong `reports/data/` và `reports/domain/` rồi vẽ – không tải hay xử lý lại dữ liệu.
Văn bản PhoMT không được phân phối lại (giấy phép) nên chỉ có số đếm.
"""),
    ("code", SETUP),
    ("md", "## 1. Nguồn dữ liệu"),
    ("code", r'''
display(doc(R / "data/nguon_du_lieu.csv"))
'''),
    ("md", "## 2. Làm sạch – số mẫu sau từng bước"),
    ("code", r'''
ls = doc(R / "data/lam_sach_dem_tung_buoc.csv")
display(ls[["dataset", "split", "buoc", "ten_buoc", "truoc", "bi_loai", "sau"]])
kq = ls[ls.buoc == "KET_QUA"].assign(tap=lambda d: d.dataset + " " + d.split)
print("Tổng bị loại:", int(ls[ls.buoc != "KET_QUA"].bi_loai.sum()), "mẫu")
buoc = ls[ls.buoc != "KET_QUA"].assign(tap=lambda d: d.dataset + " " + d.split)
tap_co_loai = buoc.groupby("tap").bi_loai.sum().loc[lambda x: x > 0].index
fig, ax = plt.subplots(1, len(tap_co_loai), figsize=(5 * len(tap_co_loai), 3.4), squeeze=False)
for a_, t in zip(ax[0], tap_co_loai):
    d = buoc[buoc.tap == t]; a_.plot(range(len(d)), d.sau, "o-", color=XANH)
    for k, (x, y, l) in enumerate(zip(range(len(d)), d.sau, d.bi_loai)):
        if l: a_.annotate(f"−{l}", (x, y), textcoords="offset points", xytext=(0, 8), ha="center", color=CAM)
    a_.set_xticks(range(len(d))); a_.set_xticklabels(d.buoc.str.split("_").str[0], fontsize=8); a_.set_title(f"{t}: số mẫu sau từng bước")
plt.tight_layout(); plt.show()
'''),
    ("md", "## 3. Tỉ lệ train / dev / test"),
    ("code", r'''
tl = doc(R / "data/eda/eda_bang_ti_le_tap.csv"); display(tl)
fl = tl[tl.dataset == "fleurs"]
fig, ax = plt.subplots(1, 2, figsize=(11, 3.6))
ax[0].bar(fl.split, fl.so_mau, color=XANH); ax[0].set_title("FLEURS – số bản thu")
for x, y, p in zip(fl.split, fl.so_mau, fl.pct_mau): ax[0].text(x, y, f"{y:,}\n({p:.1f}%)".replace(",", "."), ha="center", va="bottom")
ax[1].bar(fl.split, fl.gio, color=CAM); ax[1].set_title("FLEURS – số giờ audio")
for x, y in zip(fl.split, fl.gio): ax[1].text(x, y, f"{y:.2f} h".replace(".", ","), ha="center", va="bottom")
plt.tight_layout(); plt.show()
print("Giữ split gốc của FLEURS (≈ 70,6 / 8,7 / 20,7) để so được với paper và tránh rò rỉ; không ép về 80/10/10.")
'''),
    ("md", "## 4. Giới tính người nói"),
    ("code", r'''
gt = doc(R / "data/eda/eda_bang_gioi_tinh.csv"); display(gt)
g = gt.assign(tap=gt.dataset + " " + gt.split)
fig, ax = plt.subplots(figsize=(9, 3.6))
ax.barh(g.tap, g.pct_Nam, color=XANH, label="Nam"); ax.barh(g.tap, g["pct_Nữ"], left=g.pct_Nam, color=CAM, label="Nữ")
ax.barh(g.tap, g["pct_Không rõ"], left=g.pct_Nam + g["pct_Nữ"], color=XAM, label="Không rõ")
ax.set_xlabel("%"); ax.legend(loc="lower right"); ax.set_title("Tỉ lệ giới tính theo tập"); plt.tight_layout(); plt.show()
print("Lệch lớn nhất: FLEURS train phần lớn giọng nữ nhưng dev/test toàn giọng nam → kết quả test chưa nói được gì về giọng nữ.")
'''),
    ("md", "## 5. Số bản thu mỗi câu (FLEURS) – nguồn mất cân bằng chính"),
    ("code", r'''
bt = doc(R / "data/eda/eda_bang_ban_thu_moi_cau.csv"); display(bt.pivot(index="so_ban_thu", columns="split", values="pct"))
fig, ax = plt.subplots(figsize=(8, 3.6)); w = .27
for i, sp in enumerate(["train", "dev", "test"]):
    d = bt[bt.split == sp]; ax.bar(d.so_ban_thu + (i - 1) * w, d.pct, w, label=sp)
ax.set_xlabel("số bản thu của một câu"); ax.set_ylabel("% số câu"); ax.set_xticks(sorted(bt.so_ban_thu.unique())); ax.legend()
ax.set_title("Phân bố số bản thu mỗi câu"); plt.tight_layout(); plt.show()
'''),
    ("md", "## 6. Thời lượng audio và độ dài câu"),
    ("code", r'''
th = doc(R / "data/eda/eda_bang_thoi_luong.csv"); display(th)
fig, ax = plt.subplots(figsize=(9, 3.6))
y = range(len(th)); ax.hlines(y, th.p5, th.p95, color=XANH, lw=6, alpha=.5, label="p5–p95")
ax.plot(th["median"], y, "o", color=CAM, label="trung vị"); ax.plot(th["max"], y, "x", color="k", label="max")
ax.axvline(30, color="red", ls="--", lw=1); ax.text(30.3, len(th) - .6, "30 s (giới hạn 1 lượt Whisper)", color="red", fontsize=9)
ax.set_yticks(list(y)); ax.set_yticklabels(th.bo_tap); ax.set_xlabel("giây"); ax.legend(loc="lower right"); ax.set_title("Thời lượng bản thu")
plt.tight_layout(); plt.show()
dd = doc(R / "data/eda/eda_bang_do_dai_cau.csv"); display(dd)
print("FLEURS test có", int(th[th.bo_tap == "fleurs_test"].so_tren_30s.iloc[0]), "bản > 30 s – nhóm này PhoWhisper giải mã sai khi đưa thẳng vào model (xem phan_tich_loi.ipynb).")
'''),
    ("md", "## 7. VIVOS – số câu mỗi người nói"),
    ("code", r'''
vn_ = doc(R / "data/eda/eda_bang_nguoi_noi_vivos.csv")
display(vn_.groupby("split").so_cau.describe())
fig, ax = plt.subplots(figsize=(8, 3.2))
for sp, c in (("train", XANH), ("test", CAM)):
    ax.hist(vn_[vn_.split == sp].so_cau, bins=15, alpha=.7, color=c, label=sp)
ax.set_xlabel("số câu / người nói"); ax.set_ylabel("số người nói"); ax.legend(); ax.set_title("VIVOS: phân bố số câu theo người nói"); plt.tight_layout(); plt.show()
'''),
    ("md", "## 8. Miền văn bản – PhoMT và FLEURS (FLoRes+)"),
    ("code", r'''
pm = doc(R / "data/eda/eda_bang_mien_phomt.csv")
fig, ax = plt.subplots(1, 2, figsize=(12, 3.8))
d = pm[pm.split == "train"].sort_values("pct"); ax[0].barh(d.mien, d.pct, color=XANH); ax[0].set_title("PhoMT train – % cặp câu theo miền"); ax[0].set_xlabel("%")
mt = J(R / "domain/mien_tom_tat.json")["so_cau_theo_mien"]
ten = {"wikibooks": "Giáo dục (Wikibooks)", "wikinews": "Tin tức (Wikinews)", "wikivoyage": "Du lịch (Wikivoyage)"}
df = pd.DataFrame(mt).T.rename(columns=ten); df.plot.bar(ax=ax[1], color=[CAM, XANH, LUC]); ax[1].set_title("FLEURS – số câu gốc theo miền FLoRes+")
ax[1].set_xlabel(""); ax[1].tick_params(axis="x", rotation=0); plt.tight_layout(); plt.show()
display(df.assign(tong=df.sum(axis=1)))
print("PhoMT chủ yếu là phụ đề phim (OpenSubtitles) – khác xa câu Wikipedia/Wikibooks của FLEURS → lý do dạy LoRA trên lời ASR của FLEURS.")
'''),
    ("md", "## 9. Xử lý mất cân bằng"),
    ("code", r'''
cb = J(R / "data/can_bang/can_bang_tom_tat.json")
print(json.dumps({k: v for k, v in cb.items() if not isinstance(v, (list, dict)) or len(str(v)) < 400}, ensure_ascii=False, indent=1)[:2500])
for f in ("can_bang_01_theo_cau.png", "can_bang_02_do_dai.png", "can_bang_03_nguon_v2.png"):
    p = R / "data/can_bang" / f
    if p.exists(): display(Image(filename=str(p), width=780))
'''),
    ("md", "## 10. Nhận xét EDA (định lượng)"),
    ("code", r'''
display(Markdown((R / "data/eda/eda_nhan_xet.md").read_text(encoding="utf-8")))
'''),
]

# =====================================================================  PHÂN TÍCH LỖI
LOI = [
    ("md", """
# Phân tích lỗi – khối nghe (ASR) và khối dịch (MT)

Hệ cascade: **PhoWhisper-small** (khối nghe, giữ nguyên) → **VinAI Translate vi2en-v2 + LoRA** (khối dịch; bản cuối **V2**, chọn theo quy tắc DEV – `reports/ablation/QUY_TAC_CHON.md`).
Notebook chỉ đọc kết quả đã chạy (`reports/asr`, `reports/mt`, `reports/domain`, `runs/`) – không chạy model.
Mỗi ca lỗi có **ID bản thu** để nghe lại (`data/clean/audio_16k/fleurs/test/<id>`).
"""),
    ("code", SETUP),
    ("md", "## 1. WER hai baseline khối nghe"),
    ("code", r'''
rs = doc(R / "asr/results_task2.csv")[["model", "dataset", "n_scored", "WER_percent", "CER_percent", "S", "D", "I", "N", "rtf"]]
display(rs)
fig, ax = plt.subplots(figsize=(7, 3.4))
p = rs.pivot(index="dataset", columns="model", values="WER_percent"); p.plot.bar(ax=ax, color=[XANH, CAM]); ax.set_ylabel("WER (%)")
ax.tick_params(axis="x", rotation=0); ax.set_title("WER theo bộ test"); plt.tight_layout(); plt.show()
'''),
    ("md", "## 2. WER theo nhóm câu (phân tầng) – lỗi tập trung ở đâu"),
    ("code", r'''
st = doc(R / "asr/strata.csv")
st = st[st.run_id.str.contains("fleurs_test")].assign(model=lambda d: d.run_id.str.extract(r"t2_(.*)_fleurs")[0])
display(st[["model", "group_type", "group_value", "n_recordings", "S", "D", "I", "WER_percent"]])
fig, ax = plt.subplots(1, 2, figsize=(12, 3.6))
for a, gt_ in zip(ax, ("duration_s", "name_or_number")):
    d = st[st.group_type == gt_].pivot(index="group_value", columns="model", values="WER_percent"); d.plot.bar(ax=a, color=[XANH, CAM])
    a.set_title(f"FLEURS test – WER theo {gt_}"); a.set_xlabel(""); a.tick_params(axis="x", rotation=0)
plt.tight_layout(); plt.show()
print("Câu có chữ số: phần lớn lỗi là CHÈN từ (số đọc thành chữ: '802' → 'tám không hai') – lỗi do cách viết tham chiếu, không hẳn do nghe sai.")
'''),
    ("md", "## 3. Ma trận nhầm dấu thanh"),
    ("code", r'''
import numpy as np
fig, ax = plt.subplots(1, 2, figsize=(11, 4.2))
for a, (ten, f) in zip(ax, (("FLEURS test", "tone_confusion_kiet_t2_phowhisper-small_fleurs_test.csv"), ("VIVOS test", "tone_confusion_kiet_t2_phowhisper-small_vivos_test.csv"))):
    m = doc(R / "asr" / f).set_index("ref\\hyp"); a.imshow(m.values, cmap="Oranges")
    a.set_xticks(range(len(m.columns))); a.set_xticklabels(m.columns); a.set_yticks(range(len(m.index))); a.set_yticklabels(m.index)
    for i in range(m.shape[0]):
        for j in range(m.shape[1]): a.text(j, i, m.values[i, j], ha="center", va="center", fontsize=9)
    a.set_title(f"PhoWhisper – {ten}\n(hàng: thanh đúng · cột: thanh model ghi)"); a.grid(False)
plt.tight_layout(); plt.show()
'''),
    ("md", "## 4. Audio dài hơn 30 giây (long-form)"),
    ("code", r'''
lf = doc(R / "asr/long_form_audit.csv"); lf["model"] = lf.run_id.str.extract(r"t2_(.*)_fleurs")[0]
display(lf[["model", "id", "duration_s", "n_segments", "hit_cap_440", "n_output_tokens", "S", "D", "I", "N", "WER_percent"]])
print("PhoWhisper đưa thẳng cả file > 30 s: chèn rất nhiều từ (lặp 'a. a. a.', 'từng từng…') → sản phẩm chia đoạn ≤ 28 s trước khi nhận dạng.")
he = next((R / d / "ket_qua.json" for d in ("he_thong_V2", "he_thong") if (R / d / "ket_qua.json").exists()), R / "x")
if he.exists():
    k = J(he); print("Sản phẩm (chia đoạn) – nhóm audio dài:", {c: k[c]["dai"] for c in ("truoc_0411", "proposed")})
'''),
    ("md", "## 5. Giả thuyết Gap Analysis"),
    ("code", r'''
gh = doc(R / "asr/gap_hypotheses.csv"); display(gh[["id", "hypothesis", "status", "ket_qua_kiet"]].rename(columns={"ket_qua_kiet": "ket_qua"}))
'''),
    ("md", "## 6. Ca lỗi khối nghe có ID để nghe lại"),
    ("code", r'''
ea = doc(R / "asr/error_audit.csv")
cot = ["recording_id", "duration_s", "WER_percent", "tone_only", "omission", "proper_name", "number", "repetition", "audio_checked", "reference_raw", "hypothesis_raw"]
ea_p = ea[ea.run_id.str.contains("phowhisper") & ea.run_id.str.contains("fleurs")]
display(ea_p.sort_values("WER_percent", ascending=False)[cot].head(12))
loai = ["tone_only", "omission", "proper_name", "number", "repetition"]
dem = {c: int(ea_p[c].astype(str).str.lower().isin(["1", "true", "yes", "co"]).sum()) for c in loai}
print("Số ca được gắn nhãn theo loại lỗi (trong", len(ea_p), "ca audit):", dem)
nk = BASE / "nghe_kiem/danh_sach_nghe_kiem.csv"
if nk.exists():
    print("\nNghe kiểm bằng tai:"); display(doc(nk).iloc[:, :8])
'''),
    ("md", "## 7. Khối dịch – BLEU theo nhóm câu trên dev (B0 → V1…V4)"),
    ("code", r'''
nhom = {"all": "tất cả", "so": "có chữ số", "ten": "có tên riêng", "dai": "lời ASR > 40 từ", "asr_xau": "ASR sai nhiều (WER ≥ 30%)", "con_lai": "còn lại"}
rows = []
for v in ("V1", "V2", "V3", "V4"):
    f = R / f"mt/failure_{v}_dev.json"
    if f.exists():
        g = J(f)["groups"]
        for k, ten in nhom.items():
            if k in g:
                if v == "V1": rows.append({"nhóm": ten, "n": g[k]["n"], "hệ": "B0", "BLEU": g[k]["B0"][0]})
                rows.append({"nhóm": ten, "n": g[k]["n"], "hệ": v, "BLEU": g[k][v][0]})
bd = pd.DataFrame(rows).pivot_table(index=["nhóm", "n"], columns="hệ", values="BLEU").reset_index(); display(bd)
fig, ax = plt.subplots(figsize=(11, 3.8)); bd.set_index("nhóm")[["B0", "V1", "V2", "V3", "V4"]].plot.bar(ax=ax)
ax.set_ylabel("BLEU (dev)"); ax.tick_params(axis="x", rotation=15); ax.set_title("BLEU dev theo nhóm câu"); plt.tight_layout(); plt.show()
print("LoRA tăng mạnh nhất ở nhóm khối nghe làm sai (có số, ASR sai nhiều, câu dài); nhóm 'còn lại' gần như không đổi.")
'''),
    ("md", "## 8. Kết quả theo miền (FLoRes+) – trọng tâm Giáo dục"),
    ("code", r'''
dm = doc(R / "domain/ket_qua_theo_mien.csv")
mt_ = dm[(dm.khoi == "MT") & (dm.tap == "fleurs_test_asr_pho")].assign(mien=lambda d: d.mien.str.split(" \\(").str[0])
p = mt_.pivot(index="mien", columns="he", values="BLEU")[["B0", "V1", "V2", "V3", "V4"]]; display(p)
asr = dm[(dm.khoi == "ASR") & (dm.he == "phowhisper-small_fleurs_test")][["mien", "n_ban_thu", "WER", "CER"]]; display(asr)
fig, ax = plt.subplots(figsize=(8, 3.6)); p.plot.bar(ax=ax); ax.set_ylabel("BLEU cascade (test)"); ax.tick_params(axis="x", rotation=0)
ax.set_title("BLEU cả hệ theo miền"); plt.tight_layout(); plt.show()
'''),
    ("md", "## 9. Ca dịch có ID: bản cuối tốt hơn / kém hơn B0 nhiều nhất (FLEURS test, chrF++ từng câu)"),
    ("code", r'''
import sacrebleu
L = lambda v: {(r := json.loads(l))["id"]: r for l in open(BASE / f"runs/mt/{v}/fleurs_test_asr_pho/hyp.jsonl", encoding="utf-8")}
BC = J(R / "ablation/chon_ban_cuoi.json")["ban_chon"]; print("Bản cuối:", BC)
A, B = L("B0"), L(BC); ch = sacrebleu.CHRF(word_order=2)
d = pd.DataFrame([{"id": i, "chrF_B0": ch.sentence_score(A[i]["hyp"], [A[i]["ref"]]).score, "chrF_cuoi": ch.sentence_score(B[i]["hyp"], [B[i]["ref"]]).score,
                   "loi_ASR": A[i]["src"], "tham_chieu": A[i]["ref"], "B0": A[i]["hyp"], "ban_cuoi": B[i]["hyp"]} for i in A])
d["delta"] = d.chrF_cuoi - d.chrF_B0
print(f"{BC} tốt hơn B0 ở {(d.delta > 0).sum()} câu, kém hơn ở {(d.delta < 0).sum()} câu, bằng nhau {(d.delta == 0).sum()} (trên {len(d)} bản thu).")
display(Markdown(f"**{BC} tốt hơn nhiều nhất**")); display(d.sort_values("delta", ascending=False).head(5).round(1))
display(Markdown(f"**{BC} kém hơn nhiều nhất** – không phải câu nào phương pháp cũng thắng")); display(d.sort_values("delta").head(5).round(1))
'''),
    ("md", "## 10. Lỗi giữ số: tham chiếu có chữ số mà bản dịch không giữ đúng"),
    ("code", r'''
so = lambda s: set(re.findall(r"\d+", s))
co = d[d.tham_chieu.map(lambda s: bool(so(s)))]
mat = {h: int((~co.apply(lambda r: so(r.tham_chieu) <= so(r[h]), axis=1)).sum()) for h in ("B0", "ban_cuoi")}
print(f"{len(co)} bản thu có chữ số trong tham chiếu; số bản dịch thiếu/sai số: B0 {mat['B0']}, {BC} {mat['ban_cuoi']}")
vd = co[~co.apply(lambda r: so(r.tham_chieu) <= so(r.ban_cuoi), axis=1)].head(6)[["id", "loi_ASR", "tham_chieu", "ban_cuoi"]]; display(vd)
print("Khối nghe đọc số bằng chữ nên khối dịch phải đoán lại chữ số; sản phẩm thêm bước đổi số trước khi dịch (src/so.py) – đo ở reports/he_thong_V2.")
'''),
    ("md", "## 11. Lỗi lan truyền từ khối nghe sang khối dịch"),
    ("code", r'''
pr = {json.loads(l)["id"]: json.loads(l) for l in open(BASE / "runs/asr/kiet_t2_phowhisper-small_fleurs_test/predictions.jsonl", encoding="utf-8")}
from collections import Counter
sys_path = BASE / "scripts" / "asr"
import sys; sys.path.insert(0, str(sys_path))
from score_asr import score
d["WER_cau"] = [100 * (lambda c: (c["S"] + c["D"] + c["I"]) / max(c["N"], 1))(score(pr[i]["reference"], pr[i]["prediction"])["word_counts"]) for i in d.id]
d["nhom_WER"] = pd.cut(d.WER_cau, [-.1, 0, 10, 30, 1e9], labels=["0%", "0–10%", "10–30%", "> 30%"])
t = d.groupby("nhom_WER", observed=True).agg(n=("id", "size"), chrF_B0=("chrF_B0", "mean"), chrF_cuoi=("chrF_cuoi", "mean")).round(2); display(t)
fig, ax = plt.subplots(figsize=(7, 3.4)); t[["chrF_B0", "chrF_cuoi"]].plot.bar(ax=ax, color=[XAM, XANH]); ax.set_xlabel("WER của câu (khối nghe)")
ax.set_ylabel("chrF++ trung bình"); ax.tick_params(axis="x", rotation=0); ax.set_title("Khối nghe sai càng nhiều → bản dịch càng kém"); plt.tight_layout(); plt.show()
print("LoRA lấy lại được một phần, nhưng lỗi nghe nặng vẫn kéo bản dịch xuống – nhược điểm cố hữu của cascade.")
'''),
    ("md", "## 12. Baseline B1 – Whisper Translate end-to-end (không có transcript tiếng Việt → không tính WER)"),
    ("code", r'''
pb = BASE / "runs/b1/predictions_b1.jsonl"
if not pb.exists():
    print("NOT RUN: chưa có runs/b1/predictions_b1.jsonl (chạy notebooks/02_baseline_B1_whisper_translate.ipynb)")
else:
    b1 = pd.read_json(pb, lines=True, dtype={"sample_id": str, "sent_id": str})
    sc = J(BASE / "runs/mt/B1_whisper-small_translate/fleurs_test_audio/score.json")
    print(f"B1: BLEU {sc['BLEU']} · chrF++ {sc['chrF++']} · RTF {sc['RTF_tong']} (n = {sc['n']}) | B0 cascade: BLEU {J(BASE / 'runs/mt/B0/fleurs_test_asr_pho/score.json')['BLEU']}")
    b1["tu_du_doan"] = b1.pred_en.str.split().str.len(); b1["tu_tham_chieu"] = b1.reference_en.str.split().str.len()
    b1["lap_vong"] = b1.tu_du_doan > 2 * b1.tu_tham_chieu
    bl = lambda g: round(sacrebleu.corpus_bleu(list(g.pred_en), [list(g.reference_en)]).score, 2)
    t = pd.DataFrame([{"nhóm": k, "n": len(g), "BLEU": bl(g), "câu lặp vòng": int(g.lap_vong.sum())} for k, g in
                      [("toàn bộ", b1)] + [(f"miền {k}", g) for k, g in b1.groupby("domain")] + [("≤ 30 s", b1[~b1.long_form]), ("> 30 s", b1[b1.long_form])]])
    display(t)
    print(f"{int(b1.lap_vong.sum())} câu dài hơn 2 lần câu tham chiếu (giải mã lặp vòng, vd 'network network network…'); "
          f"bỏ các câu này BLEU = {bl(b1[~b1.lap_vong])} – chỉ để chẩn đoán, số báo cáo vẫn là {sc['BLEU']}.")
    display(b1[b1.lap_vong].nlargest(3, "tu_du_doan")[["sample_id", "audio_duration_s", "tu_du_doan", "pred_en"]].assign(pred_en=lambda x: x.pred_en.str[:160]))
    for f in sorted((BASE / "reports/mt").glob("bootstrap_*_vs_B1.json")):
        r = J(f); print(f"{f.stem}: {r['BLEU_A']} → B1 {r['BLEU_B']}, Δ {r['delta']:+.2f} [{r['ci95'][0]}; {r['ci95'][1]}]")
    so_ = lambda s: set(re.findall(r"\d+", s))
    co_ = b1[b1.reference_en.map(lambda s: bool(so_(s)))]
    print(f"Giữ đúng chữ số: {len(co_)} câu có số trong tham chiếu → B1 sai/thiếu {int((~co_.apply(lambda r: so_(r.reference_en) <= so_(r.pred_en), axis=1)).sum())} câu")
'''),
    ("md", "## 13. Ablation khối dịch (đổi một yếu tố so với V2) và bản chọn theo DEV"),
    ("code", r'''
fa = BASE / "reports/ablation/bang_ablation.csv"
if not fa.exists():
    print("NOT RUN: chưa có reports/ablation/bang_ablation.csv (chạy notebooks/03_ablation_va_chon_ban_cuoi.ipynb)")
else:
    display(doc(fa))
    ch_ = J(BASE / "reports/ablation/chon_ban_cuoi.json")
    print("Quy tắc:", ch_["quy_tac"], "| M dev cascade =", ch_["M_dev_cascade"], "| nhóm hoà:", ch_["nhom_hoa"], "| CHỌN:", ch_["ban_chon"])
    fig, ax = plt.subplots(1, 3, figsize=(13, 3.2), sharey=True)
    for a_, k in zip(ax, ("A_r8", "A_r32", "A_aug")):
        e = pd.DataFrame(J(BASE / f"checkpoints/{k}/epochs.json")); v2 = pd.DataFrame(J(BASE / "checkpoints/V2/epochs.json"))
        a_.plot(v2.epoch, v2.dev_BLEU_translate, "o--", color=XAM, label="V2"); a_.plot(e.epoch, e.dev_BLEU_translate, "s-", color=XANH, label=k)
        a_.set_title(f"{k}: BLEU dev theo epoch"); a_.set_xlabel("epoch"); a_.legend()
    plt.tight_layout(); plt.show()
'''),
]


def main():
    OUT.mkdir(exist_ok=True)
    for ten, cells in (("eda.ipynb", EDA), ("phan_tich_loi.ipynb", LOI)):
        nbf.write(nb(cells), OUT / ten)
        print("sinh", OUT / ten)
    if "--khong_chay" in sys.argv:
        return
    import asyncio
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
    from nbclient import NotebookClient
    for ten in ("eda.ipynb", "phan_tich_loi.ipynb"):
        p = OUT / ten
        n = nbf.read(p, as_version=4)
        NotebookClient(n, timeout=600, kernel_name="task3-dpl302m", resources={"metadata": {"path": str(OUT)}}, allow_errors=True).execute()
        loi = [(i, o["ename"], o["evalue"][:200]) for i, c in enumerate(n.cells) if c.cell_type == "code" for o in c.outputs if o.get("output_type") == "error"]
        for c in n.cells:  # bỏ nhiễu stderr của kernel khi chạy nền trên Windows
            if c.cell_type == "code":
                c.outputs = [o for o in c.outputs if not (o.get("output_type") == "stream" and o.get("name") == "stderr")]
        nbf.write(n, p)
        print(ten, "lỗi:", loi or "không")


if __name__ == "__main__":
    main()
