#!/usr/bin/env python3
"""Vẽ sơ đồ kiến trúc TOÀN BỘ dự án (dữ liệu → thực nghiệm → đánh giá → sản phẩm) theo code đã sửa và số đã đo.

Số đọc từ file kết quả (không gõ tay): task3/reports/..., task3/runs/..., dang_test3/kiem_thu/t3_tom_tat.json.
Đầu ra: kien_truc/kien_truc_toan_bo_du_an.png (+ .svg)
"""
import csv
import json
import statistics
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyArrowPatch, FancyBboxPatch  # noqa: E402

TW = Path(__file__).resolve().parents[1]
T3 = TW / "task3"
OUT = Path(__file__).resolve().parent


def J(p):
    return json.loads(Path(p).read_text(encoding="utf-8"))


def vn(x, d=2):
    return f"{float(x):.{d}f}".replace(".", ",")


def bleu(v, s):
    return J(T3 / "runs" / "mt" / v / s / "score.json")["BLEU"]


R = {r["run_id"]: r for r in csv.DictReader(open(T3 / "reports/asr/results_task2.csv", encoding="utf-8-sig"))}
W = lambda m, d: vn(R[f"kiet_t2_{m}_{d}_test"]["WER_percent"])
lap = [J(p) for p in sorted((T3 / "reports/toc_do/lap_V2").glob("toc_do_V2_lan*.json"))]  # bản cuối V2
rtf = vn(statistics.median(x["RTF_total"] for x in lap), 3)
p50 = vn(statistics.median(x["latency_p50_s"] for x in lap))
p95 = vn(statistics.median(x["latency_p95_s"] for x in lap))
vram = vn(max(x["gpu_peak_allocated_bytes"] for x in lap) / 2**30)
sp = J(T3 / "reports/he_thong_V2/ket_qua.json")  # cả hệ, adapter V2
bsh = J(T3 / "reports/he_thong_V2/bootstrap_cu_vs_moi.json"); nt = J(T3 / "reports/he_thong_V2/nghiem_thu/ket_qua.json")["ket_qua"]
b04 = J(T3 / "reports/mt/bootstrap_B0_V2_cascade_test.json"); b1s = J(T3 / "runs/mt/B1_whisper-small_translate/fleurs_test_audio/score.json")
dom = {(r["he"], r["mien"].split(" (")[0]): r["BLEU"] for r in csv.DictReader(open(T3 / "reports/domain/ket_qua_theo_mien.csv", encoding="utf-8-sig"))
       if r["khoi"] == "MT" and r["tap"] == "fleurs_test_asr_pho"}

NAVY, TEAL, ORANGE, GREEN, GREY = "#1F2A5C", "#0E7C86", "#B36B00", "#2E7D32", "#5A6270"
fig = plt.figure(figsize=(24, 15.5), dpi=110)
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 240); ax.set_ylim(0, 155); ax.axis("off")


def band(y, h, title, owner, color):
    ax.add_patch(FancyBboxPatch((2, y), 236, h, boxstyle="round,pad=0.3,rounding_size=1.5", fc=color + "14", ec=color, lw=1.6))
    ax.text(4, y + h - 2.3, title, fontsize=15, weight="bold", color=color, va="top")
    ax.text(236, y + h - 2.3, owner, fontsize=11.5, color=color, va="top", ha="right", style="italic")


def box(x, y, w, h, title, lines, fc="white", ec=NAVY, tc=None, dashed=False):
    tc = tc or ("white" if fc not in ("white",) else "#1A1A1A")
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.2,rounding_size=1.2", fc=fc, ec=ec, lw=1.5, ls="--" if dashed else "-"))
    ax.text(x + w / 2, y + h - 1.6, title, fontsize=11.5, weight="bold", color=tc, ha="center", va="top")
    ax.text(x + w / 2, y + h - 5.0, "\n".join(lines), fontsize=9.6, color=tc, ha="center", va="top", linespacing=1.35)


def arrow(x1, y1, x2, y2, color=GREY, text=None, rad=0.0):
    ax.add_patch(FancyArrowPatch((x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=16, color=color, lw=1.6, connectionstyle=f"arc3,rad={rad}"))
    if text:
        ax.text((x1 + x2) / 2 + 0.8, (y1 + y2) / 2, text, fontsize=9, color=color, style="italic", va="center")


ax.text(120, 152.5, "Kiến trúc toàn bộ dự án – Dịch tiếng nói tiếng Việt → văn bản tiếng Anh (cascade ASR → MT), miền Giáo dục",
        fontsize=19, weight="bold", color=NAVY, ha="center", va="top")
ax.text(120, 148.6, "Đề tài 1 · DPL302m · Uyên (dữ liệu) · Bảo (ASR) · Kiệt (thực nghiệm, khối dịch) · Đăng (hệ thống, triển khai)  ·  số liệu đo trên RTX 4060 Laptop 8 GB",
        fontsize=11.5, color=GREY, ha="center", va="top")

# ---- 1. Dữ liệu ----
band(116, 29, "① DỮ LIỆU", "Uyên thiết kế pipeline · Kiệt chạy (tái lập đúng hash)", GREEN)
box(5, 118.5, 33, 21, "VIVOS", ["train 11.656 / test 760 câu", "46 + 19 người nói", "CC BY-NC-SA 4.0"], ec=GREEN)
box(41, 118.5, 36, 21, "FLEURS vi_vn + en_us", ["train 2.926 / dev 361 /", "test 857 bản thu (347 câu)", "audio Việt ↔ câu Anh"], ec=GREEN)
box(80, 118.5, 33, 21, "PhoMT", ["2.977.170 cặp sạch", "(bỏ 829 cặp trùng)", "dev 18.719 / test 19.151"], ec=GREEN)
box(116, 118.5, 31, 21, "FLoRes+", ["nhãn miền từng câu", "Giáo dục = Wikibooks", "(test 336 bản thu)"], ec=GREEN)
box(152, 118.5, 83, 21, "Pipeline dữ liệu (5 script)", ["tải → ghép vi–en + chống leakage → làm sạch (thiếu / trùng / hỏng / 16 kHz / chuẩn hoá chữ)",
    "→ EDA (tỉ lệ tập, giới tính, độ dài) → cân bằng (lặp mẫu theo câu + độ dài; trộn PhoMT 1:1)",
    "0 ID câu trùng giữa các tập · 0 câu FLEURS test trùng PhoMT"], fc=GREEN)
for x in (21.5, 59, 96.5, 131.5):
    pass
arrow(147, 129, 152, 129, GREEN)

# ---- 2. Thực nghiệm ----
band(68, 45, "② THỰC NGHIỆM (Task 2)", "Bảo: protocol ASR · Kiệt: chạy toàn bộ, khối dịch, LoRA", NAVY)
box(5, 88, 52, 20, "Khối nghe – 2 baseline ASR", [f"PhoWhisper-small: VIVOS {W('phowhisper-small', 'vivos')}% · FLEURS {W('phowhisper-small', 'fleurs')}%",
    f"Whisper-small: VIVOS {W('whisper-small', 'vivos')}% · FLEURS {W('whisper-small', 'fleurs')}%", "fp16 · beam 5 · protocol bao_asr_v1"], fc=NAVY)
box(5, 70.5, 52, 14.5, "Lời ASR (PhoWhisper)", ["FLEURS train 2.926 → dữ liệu dạy", "FLEURS dev 361 → chọn epoch"], ec=NAVY)
box(62, 88, 40, 20, "Khối dịch – baseline B0", ["VinAI Translate vi2en-v2", f"PhoMT test {vn(bleu('B0', 'phomt_test'))} (paper 40,42)",
    f"dịch sạch {vn(bleu('B0', 'fleurs_test_clean'))} → cascade {vn(bleu('B0', 'fleurs_test_asr_pho'))}"], fc=TEAL)
box(107, 70.5, 128, 37.5, "Phương pháp đề xuất: LoRA cho khối dịch, dạy trên lời ASR thật (r 16, α 32, 2,0% tham số, adapter 34,7 MB)", [""], ec=TEAL)
vx = [("V1", "+ LoRA trên lời ASR", "V1"), ("V2", "+ trộn 4.468 cặp PhoMT", "V2"), ("V3", "+ cân bằng câu/độ dài", "V3"), ("V4", "lr 2e-4 → 5e-5", "V4")]
for i, (v, ch, k) in enumerate(vx):
    x = 110 + i * 31.5
    fc = TEAL if v != "V2" else "#0A5C63"
    box(x, 74, 28.5, 26, v + (" ★ bản cuối" if v == "V2" else ""),
        [ch, f"dev {vn(bleu(k, 'fleurs_dev_asr_pho'))}", f"cascade {vn(bleu(k, 'fleurs_test_asr_pho'))}", f"dịch sạch {vn(bleu(k, 'fleurs_test_clean'))}",
         f"PhoMT {vn(bleu(k, 'phomt_test'))}"], fc=fc)
    if i:
        arrow(x - 3, 87, x, 87, TEAL)
arrow(31, 88, 31, 85, NAVY)
arrow(57, 72.5, 107, 72.5, NAVY, "dữ liệu dạy / dev")
box(62, 74.5, 40, 11, "B1 · Whisper translate (end-to-end)", [f"audio → tiếng Anh: BLEU {vn(b1s['BLEU'])}"], ec=ORANGE)
ax.text(171, 102.2, f"Ablation so với V2 (dev cascade {vn(bleu('V2', 'fleurs_dev_asr_pho'))}): rank 8 {vn(bleu('A_r8', 'fleurs_dev_asr_pho'))} · rank 32 {vn(bleu('A_r32', 'fleurs_dev_asr_pho'))} · augmentation {vn(bleu('A_aug', 'fleurs_dev_asr_pho'))}", fontsize=9.6, color=TEAL, ha="center", weight="bold")
arrow(102, 98, 110, 95, TEAL, "base")
ax.text(158, 72.0, "checkpoint mỗi epoch, resume được · chọn bản: dev cascade, hoà ≤ 0,5 thì dev sạch", fontsize=9.1, color=TEAL, ha="left")
arrow(205, 118.5, 205, 108.3, GREEN, "dữ liệu dạy (cân bằng, PhoMT)")
arrow(160, 118.5, 40, 108.3, GREEN, "audio + nhãn sạch", rad=0.04)

# ---- 3. Đánh giá ----
band(44, 21, "③ ĐÁNH GIÁ", "score_asr.py của Bảo · sacreBLEU 2.4.3 · bootstrap cụm theo câu", ORANGE)
items = [("WER / CER", ["chuẩn hoá vi_nfc_ps_space_v1", "phân tầng độ dài, tên, số", "H1–H5 Gap Analysis"]),
         ("BLEU / chrF++", ["cascade · dịch sạch · PhoMT", f"Whisper → B0 {vn(bleu('B0', 'fleurs_test_asr_wsp'))} → V2 {vn(bleu('V2', 'fleurs_test_asr_wsp'))}", f"bootstrap B0→V2 +{vn(b04['delta'])}"]),
         ("Theo miền (B0 → V2)", [f"Giáo dục: {vn(dom[('B0', 'Giáo dục')])} → {vn(dom[('V2', 'Giáo dục')])}", f"Tin tức: {vn(dom[('B0', 'Tin tức')])} → {vn(dom[('V2', 'Tin tức')])}", f"Du lịch: {vn(dom[('B0', 'Du lịch')])} → {vn(dom[('V2', 'Du lịch')])}"]),
         ("Tốc độ (V2)", [f"RTF {rtf} · p50 {p50} s · p95 {p95} s", f"VRAM {vram} GiB · model 2,69 GB", "3 lần đo xen kẽ B0/V2/V4 (04/11)"]),
         ("Nghe kiểm + lỗi", ["10 audio do Kiệt nghe", "ma trận nhầm dấu thanh", "phân tích lỗi trên dev"])]
for i, (t, ls) in enumerate(items):
    box(5 + i * 46.5, 46, 43.5, 15, t, ls, ec=ORANGE)
arrow(171, 70.5, 171, 61.5, ORANGE)

# ---- 4. Sản phẩm ----
band(3, 38, "④ SẢN PHẨM (Task 3)", "Đăng: kiến trúc hệ thống, API, demo, Docker/CI · Kiệt: kiểm thử với model thật", "#6A1B9A")
P = "#6A1B9A"
box(5, 15, 22, 19, "Người dùng", ["thu âm micro", "hoặc tải tệp", "wav/mp3/flac/ogg", "(m4a/webm qua ffmpeg)"], ec=P)
box(31, 15, 26, 19, "Giao diện Gradio", [":7860 · tải tệp + thu âm", "hiện từng đoạn khi đang nói", "bảng theo đoạn", "lỗi tệp báo tiếng Việt"], ec=P)
box(61, 15, 26, 19, "API FastAPI", [":8000 · POST /dich", "GET /health", "400 / 413 / 422 / 503", "báo lỗi nếu model không nạp"], ec=P)
box(91, 6, 112, 30, "Pipeline suy luận (src/pipeline.py)", [""], fc="#F3E5F5", ec=P, tc=P)
steps = [("Chuẩn hoá", ["mono · 16 kHz", "im lặng → rỗng"]), ("Chia đoạn", ["≤ 28 s, cắt ở", "chỗ ngắt; bỏ lặp"]),
         ("PhoWhisper-small", ["fp16 · beam 5", "giữ nguyên"]), ("Đổi số", ["chữ → chữ số", "trước khi dịch"]), ("VinAI + LoRA V2", ["merge ở fp32", "→ fp16 · beam 5"])]
for i, (t, ls) in enumerate(steps):
    x = 93 + i * 22
    box(x, 9, 19.5, 18, t, ls, fc=P if i in (2, 4) else "white", ec=P)
    if i:
        arrow(x - 2.5, 18, x, 18, P)
pr = sp["proposed"]
box(207, 6, 29, 30, "Đo cả hệ (GPU)", [f"857 bản FLEURS test", f"WER {vn(pr['tat_ca']['WER_asr'])}% · BLEU {vn(pr['tat_ca']['BLEU'])}", f"chrF++ {vn(pr['tat_ca']['chrF++'], 1)} · RTF {vn(pr['tat_ca']['RTF'], 3)}",
    "so xử lý cũ: " + f"{bsh['delta']:+.2f}".replace(".", ",") + " (không ý nghĩa TK)", f"nghiệm thu {sum(m['dat'] for m in nt)}/{len(nt)} mục"], fc=GREEN)
arrow(27, 24.5, 31, 24.5, P); arrow(57, 24.5, 61, 24.5, P); arrow(87, 24.5, 91, 24.5, P); arrow(203, 21, 207, 21, GREEN)
ax.text(46, 8.3, "Docker: 2 service (api + app) · CI: lint → test → cài sạch → build → deploy (chưa chạy trên GitHub)", fontsize=9.3, color=P, ha="center")
ax.plot([155, 155, 189.6, 189.6], [74, 66.8, 66.8, 42], color="#0A5C63", lw=1.8)
arrow(189.6, 42, 189.6, 27.3, "#0A5C63")
ax.text(191, 39.5, "adapter V2/best", fontsize=9.5, color="#0A5C63", style="italic", weight="bold")

ax.text(238, 0.8, "Nguồn số: task3/reports/asr/results_task2.csv · task3/runs/mt/*/score.json · task3/reports/toc_do/lap_V2 · task3/reports/domain · task3/reports/he_thong_V2 · task3/reports/ablation",
        fontsize=8.6, color=GREY, ha="right")
OUT.mkdir(exist_ok=True)
fig.savefig(OUT / "kien_truc_toan_bo_du_an.png", dpi=110)
fig.savefig(OUT / "kien_truc_toan_bo_du_an.svg")
print(OUT / "kien_truc_toan_bo_du_an.png")
