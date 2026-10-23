"""Task 2 · sơ đồ kiến trúc hệ thống (phần Đăng): baseline B0 và Proposed Method V2 → reports/task2/figures/architecture.png."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch
import json, os
R = "reports/task2"
FIN = "V3" if os.path.exists(f"{R}/mt/eval_V3.json") else "V2"
E = {v: json.load(open(f"{R}/mt/eval_{v}.json", encoding="utf-8")) for v in ("B0", FIN)}
B0P = json.load(open(f"{R}/mt/eval_B0_full.json" if os.path.exists(f"{R}/mt/eval_B0_full.json") else f"{R}/mt/eval_B0_batch32.json", encoding="utf-8"))["phomt_test"]["BLEU"]
SPF = f"{R}/system/speed_V3.json" if FIN == "V3" and os.path.exists(f"{R}/system/speed_V3.json") else f"{R}/system/speed_final.json"
SP = json.load(open(SPF, encoding="utf-8"))
fmt = lambda x, d=2: f"{x:.{d}f}".replace(".", ",")
VRAM = f"{int(round(SP['size']['gpu_peak_allocated_mb'])):,}".replace(",", ".")

fig, ax = plt.subplots(figsize=(13, 5.2))
ax.set_xlim(0, 13); ax.set_ylim(0, 5.2); ax.axis("off")
NAVY, BLUE, GREEN, GREY, ORANGE = "#0b2a6f", "#dbe6f8", "#dff3e4", "#f1f1f1", "#fde7d6"


def box(x, y, w, h, title, sub, fill, edge=NAVY):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12", fc=fill, ec=edge, lw=1.6))
    ax.text(x + w / 2, y + h * 0.64, title, ha="center", va="center", fontsize=11, weight="bold", color=NAVY)
    ax.text(x + w / 2, y + h * 0.30, sub, ha="center", va="center", fontsize=8.6, color="#333")


def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=14, lw=1.4, color=NAVY))


y = 2.7
box(0.2, y, 1.9, 1.3, "Âm thanh", "file / micro\nmono, 16 kHz", GREY)
box(2.5, y, 1.9, 1.3, "Silero VAD", "cắt đoạn ≤ 25 s\n(âm thanh dài)", GREY)
box(4.8, y, 2.2, 1.3, "PhoWhisper-small", "ASR, 242 triệu tham số\nFP16, giữ nguyên", BLUE)
box(7.4, y, 2.6, 1.3, "VinAI Translate vi2en", f"MT, 448 triệu tham số\n+ LoRA {FIN} (18 MB)", GREEN, edge="#2e7d32")
box(10.4, y, 2.4, 1.3, "Kết quả", "chữ Việt | câu Anh\nkèm mốc thời gian", GREY)
for a, b in ((2.1, 2.5), (4.4, 4.8), (7.0, 7.4), (10.0, 10.4)):
    arrow(a, y + 0.65, b, y + 0.65)

box(6.0, 0.35, 5.2, 1.45, "Proposed Method: LoRA trên chữ máy nghe",
    "2.927 cặp (chữ PhoWhisper nghe FLEURS train → câu Anh)\n+ 1.449 cặp chữ chuẩn + 3.000 cặp PhoMT; r = 16, 1,04% tham số",
    ORANGE, edge="#c75b12")
arrow(8.7, 1.8, 8.7, 2.7)
ax.text(0.2, 4.75, f"Cascade ASR → MT: B0 = PhoWhisper-small → VinAI Translate gốc; {FIN} = cùng hệ thống, khối dịch được dạy thêm bằng LoRA" + (" + chuẩn hóa số" if FIN == "V3" else ""),
        fontsize=11, color=NAVY, weight="bold")
ax.text(0.2, 0.9, f"FLEURS test (cascade):\nB0 BLEU {fmt(E['B0']['fleurs_cascade']['BLEU'])} → {FIN} {fmt(E[FIN]['fleurs_cascade']['BLEU'])}\nPhoMT test: {fmt(B0P)} → {fmt(E[FIN].get('phomt_test', {}).get('BLEU', float('nan')))}\nRTF {fmt(SP['short_utterances']['rtf_total'])} · VRAM {VRAM} MB",
        fontsize=9.5, color="#222", va="center")
fig.tight_layout()
fig.savefig("reports/task2/figures/architecture.png", dpi=170)
print("saved reports/task2/figures/architecture.png")
