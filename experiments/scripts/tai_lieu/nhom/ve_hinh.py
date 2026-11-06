#!/usr/bin/env python3
"""Vẽ lại hình của tài liệu nhóm theo bản cuối V2. Chữ ví dụ đọc thẳng từ hyp.jsonl, số đọc từ file kết quả task3."""
import csv, json, statistics, textwrap
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Rectangle

TW = Path(__file__).resolve().parents[2]; T = TW / "task3"; OUT = TW / "tai_lieu_nhom_V2/6_hinh"
OUT.mkdir(parents=True, exist_ok=True)
plt.rcParams["font.family"] = "DejaVu Sans"
XANH, XANH2, CHU, XAM, NEN, DO, LUC, VANG = "#1f2766", "#05838f", "#1e2228", "#5a6270", "#eef1f6", "#8c2320", "#2c5f2d", "#b36b00"
J = lambda p: json.loads(Path(p).read_text(encoding="utf-8"))
vn = lambda x, d=2: f"{float(x):.{d}f}".replace(".", ",")


def hyp(v):
    return {json.loads(l)["id"].removesuffix(".wav"): json.loads(l) for l in open(T / f"runs/mt/{v}/fleurs_test_asr_pho/hyp.jsonl", encoding="utf-8")}


B, V = hyp("B0"), hyp("V2")
M = {json.loads(l)["id"].removesuffix(".wav"): json.loads(l) for l in open(T / "runs/manifests/asr_fleurs_test.jsonl", encoding="utf-8")}


def bang(fn, tieu, phu, vd, chan, mau_ket):
    fig = plt.figure(figsize=(16, 7.84)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 2000); ax.set_ylim(980, 0); ax.axis("off")
    ax.text(1000, 62, tieu, ha="center", va="center", fontsize=23, fontweight="bold", color=XANH)
    ax.text(1000, 98, phu, ha="center", va="center", fontsize=14, color=XAM)
    X = [345, 1143]; W = 796
    for x, v in zip(X, vd):
        ax.add_patch(FancyBboxPatch((x + 12, 140), W - 24, 38, boxstyle="round,pad=0,rounding_size=14", fc=XANH, ec=XANH))
        ax.text(x + W / 2, 159, v["ten"], ha="center", va="center", fontsize=15, fontweight="bold", color="white")
    H = [("Audio đầu vào", 66), ("Lời ASR (tiếng Việt)", 142), ("Tham chiếu (Anh)", 130), ("B0 – VinAI gốc", 142), ("V2 – bản đề xuất", 142)]
    y = 196
    for k, (nhan, h) in enumerate(H):
        ax.add_patch(Rectangle((50, y), 285, h, fc="#e2e6ee", ec="#c8ced8"))
        ax.text(66, y + h / 2, nhan, va="center", fontsize=13.5, fontweight="bold", color=CHU)
        for x, v in zip(X, vd):
            m = M[v["id"]]
            noi = [f"{v['id']}.wav · {str(m['duration_s']).replace('.', ',')} s · miền Giáo dục", V[v["id"]]["src"], V[v["id"]]["ref"], B[v["id"]]["hyp"], V[v["id"]]["hyp"]][k]
            ax.add_patch(Rectangle((x + 10, y), W - 20, h, fc=("#e8f1f4" if k == 4 else "#f1f4f9" if k % 2 == 0 else "white"), ec="#c8ced8"))
            ax.text(x + 26, y + 14, textwrap.fill(noi, 51 if k == 4 else 56), va="top", fontsize=14, linespacing=1.3, fontweight="bold" if k == 4 else "normal", color=XANH if k == 4 else CHU)
        y += h + 6
    for x, v in zip(X, vd):
        ax.add_patch(FancyBboxPatch((x + 12, y + 2), W - 24, 40, boxstyle="round,pad=0,rounding_size=14", fc=mau_ket, ec=mau_ket))
        ax.text(x + W / 2, y + 22, v["ket"], ha="center", va="center", fontsize=15, fontweight="bold", color="white")
    for i, c in enumerate(chan):
        ax.text(50, y + 66 + i * 26, c, va="center", fontsize=11.5, color=XAM)
    fig.savefig(OUT / fn, dpi=147.4); plt.close(fig)


c = J(T / "runs/mt/V2/fleurs_test_asr_pho/score.json")["BLEU"]
bang("visual_results_tot.png", "Trực quan hoá kết quả đầu ra — bản cuối V2 so với baseline B0", "Ví dụ thật trên FLEURS test, miền Giáo dục · chữ giữ nguyên như trong file kết quả, không sửa",
     [dict(id="3554584753359809648", ten="Ví dụ 1 · lỗi nghĩa của B0", ket="V2 giữ được ý “bản đồ kho báu”"), dict(id="5600578667047148114", ten="Ví dụ 2 · số đọc thành chữ", ket="V2 viết lại đúng “25 to 30 years”")],
     ["Nguồn: runs/mt/B0/fleurs_test_asr_pho/hyp.jsonl · runs/mt/V2/fleurs_test_asr_pho/hyp.jsonl · runs/manifests/asr_fleurs_test.jsonl · reports/domain/fleurs_mien.csv",
      f"Đây là ví dụ minh hoạ, không phải mức trung bình. Số tổng của cả tập: BLEU cascade FLEURS test B0 22,69 → V2 {vn(c)}."], LUC)
bang("visual_results_loi.png", "Hai ca lỗi còn lại của hệ thống", "Chọn có chủ đích để thấy giới hạn · cùng miền Giáo dục, cùng tập FLEURS test",
     [dict(id="11453833847884158456", ten="Ví dụ 3 · lỗi nghe lan truyền", ket="Cả hai đều sai tên riêng"), dict(id="10751146797584417593", ten="Ví dụ 4 · V2 kém hơn B0", ket="V2 bỏ mất thuật ngữ")],
     ["Nguồn: như hình trên. Ví dụ 3: khâu nghe đọc “Aristotle” thành “arizona”, khâu dịch không thể sửa — lỗi lan truyền trong cascade.",
      "Ví dụ 4: thuật ngữ “maria” (vùng biển trên Mặt Trăng) bị V2 dịch thành “coast”; B0 giữ được “marina”. Đây là ca bản đề xuất kém hơn baseline."], DO)

# ---- ablation
R = list(csv.DictReader(open(T / "reports/ablation/bang_ablation.csv", encoding="utf-8-sig")))
ten = ["B0", "V1", "V2 ★", "V3", "V4", "A_r8", "A_r32", "A_aug"]
fig, ax = plt.subplots(figsize=(8, 4.2), dpi=150); x = list(range(len(R)))
ax.bar(x, [float(r["test cascade"]) for r in R], color=["#4c72b0"] * 5 + ["#8fa8cf"] * 3, label="test cascade (ASR → MT)")
for i, r in zip(x, R):
    ax.text(i, float(r["test cascade"]) + .4, vn(r["test cascade"]), ha="center", fontsize=8.5)
ax.plot(x, [float(r["test sạch"]) for r in R], "o-", color="#dd8452", label="test transcript sạch")
ax.plot(x, [float(r["PhoMT test"]) for r in R], "s--", color="#55a868", label="PhoMT test")
ax.set_xticks(x, ten); ax.set_ylabel("BLEU"); ax.set_ylim(0, 48); ax.legend(loc="lower right", fontsize=8, framealpha=.9)
ax.set_title("Khối dịch: B0, V1–V4 và ablation một yếu tố so với V2 (857 bản thu)", fontsize=10.5); fig.tight_layout(); fig.savefig(OUT / "ablation_V2.png"); plt.close(fig)

# ---- kiến trúc
lap = [J(p) for p in sorted((T / "reports/toc_do/lap_V2").glob("toc_do_V2_lan*.json"))]
md = lambda k: statistics.median(x[k] for x in lap)
ht = J(T / "reports/he_thong_V2/ket_qua.json")["proposed"]
fig = plt.figure(figsize=(14.8, 8.4)); ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 2000); ax.set_ylim(1135, 0); ax.axis("off")
ax.text(1000, 62, "Kiến trúc hệ thống: tiếng Việt nói → văn bản tiếng Anh (cascade ASR → MT)", ha="center", fontsize=23, fontweight="bold", color=XANH, va="center")
ax.text(1000, 104, "Đề tài 1 · miền ứng dụng: Giáo dục · bản cuối V2", ha="center", fontsize=14, color=XAM, va="center")


def khoi(y, nen, bien, tieu, hop):
    ax.add_patch(Rectangle((68, y), 1864, 462 if y < 400 else 405, fc=nen, ec=bien, lw=1.6)); ax.text(98, y + 36, tieu, fontsize=14.5, fontweight="bold", color=XANH if y < 400 else VANG, va="center")
    X = [(70, 345), (448, 365), (843, 415), (1288, 415), (1714, 232)]
    for (x, w), (t, d, m) in zip(X, hop):
        ax.add_patch(FancyBboxPatch((x + 22, y + 80), w - 44, 236, boxstyle="round,pad=0,rounding_size=34", fc=m, ec="#5a6270" if m == "white" else m, lw=2.2))
        c_ = CHU if m == "white" else "white"
        ax.text(x + w / 2, y + 120, t, ha="center", va="center", fontsize=14, fontweight="bold", color=c_)
        ax.text(x + w / 2, y + 222, d, ha="center", va="center", fontsize=12, color=c_, linespacing=1.75)
    for x in (393, 791, 1236, 1681):
        ax.annotate("", (x + 40, y + 198), (x, y + 198), arrowprops=dict(arrowstyle="-|>", lw=2.4, color="#5a6270"))


khoi(140, NEN, "#c8ced8", "LUỒNG ĐO THỰC NGHIỆM  ·  tệp WAV 16 kHz có sẵn, không chia đoạn (theo protocol ASR)", [
    ("Đầu vào: tệp audio", "FLEURS / VIVOS test\nWAV 16 kHz mono,\nPCM 16-bit, batch 1", "white"), ("Tiền xử lý", "resample 16 kHz, mono\n(bước B4 của pipeline\nlàm sạch)", "white"),
    ("Khối nghe (ASR)", "PhoWhisper-small\nfp16 · beam 5\nWER 13,68% (FLEURS)", XANH), ("Khối dịch (MT)", f"VinAI vi2en-v2\n+ LoRA V2 34,7 MB\nBLEU cascade {vn(c)}", XANH2), ("Đầu ra", "câu tiếng\nAnh", "white")])
ax.text(1000, 512, f"RTF toàn hệ {vn(md('RTF_total'),3)}  ·  độ trễ p50 {vn(md('latency_p50_s'))} s / p95 {vn(md('latency_p95_s'))} s  ·  VRAM đỉnh 1,57 GiB  ·  model 2,69 GB", ha="center", fontsize=14, fontweight="bold", color=XANH, va="center")
ax.text(1000, 552, f"RTF khâu nghe {vn(md('RTF_asr'),3)} + khâu dịch {vn(md('RTF_mt'),3)}  ·  trung bình mỗi bản thu: nghe {vn(md('asr_mean_s'))} s, dịch {vn(md('mt_mean_s'))} s", ha="center", fontsize=12, color=XAM, va="center")
khoi(622, "#fff7ea", "#e3c588", "LUỒNG SẢN PHẨM  ·  demo và API chạy với model thật, đo trên 857 bản FLEURS test", [
    ("Người dùng", "tải tệp lên\nhoặc thu âm từ micro\nđổi về 16 kHz mono", "white"), ("Chia đoạn", "audio > 28 s: cắt ≤ 28 s\ntại chỗ ngắt nghỉ (±3 s)\nVAD là tuỳ chọn", VANG),
    ("Khối nghe (giữ nguyên)", "PhoWhisper-small\nmỗi đoạn ≤ 28 s\nbỏ lặp ở chỗ nối", XANH), ("Khối dịch (bản cuối V2)", "đổi số đọc thành chữ số\n→ VinAI + LoRA V2\ndịch từng đoạn", XANH2), ("Giao diện", "lời Việt\n+ bản dịch\n+ mốc thời gian", "white")])
ax.text(1000, 985, f"Cả hệ: WER {vn(ht['tat_ca']['WER_asr'])}%  ·  BLEU {vn(ht['tat_ca']['BLEU'])}  ·  chrF++ {vn(ht['tat_ca']['chrF++'])}  ·  10 bản thu dài hơn 28 s: WER {vn(ht['dai']['WER_asr'])}%, BLEU {vn(ht['dai']['BLEU'])}", ha="center", fontsize=13.5, fontweight="bold", color="#7a4a00", va="center")
ax.text(1000, 1062, "Nguồn: reports/asr/results_task2.csv · runs/mt/V2/fleurs_test_asr_pho/score.json · reports/toc_do/lap_V2/ · reports/he_thong_V2/ket_qua.json", ha="center", fontsize=11, color=XAM, va="center")
fig.savefig(OUT / "kien_truc_he_thong.png", dpi=147.3); plt.close(fig)
print("XONG")
