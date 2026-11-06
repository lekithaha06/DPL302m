#!/usr/bin/env python3
"""Sinh slide Task 2 (PowerPoint, 16:9) theo cấu trúc của Huong_dan_Task2 → tai_lieu/Slide_Task2_LeTuanKiet.pptx.

Số đọc từ file kết quả trong task3 (không gõ tay); mỗi slide có dòng nguồn ở chân trang.
"""
import csv
import json
import re
from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.util import Emu, Inches, Pt

import sys
sys.path.insert(0, str(Path(__file__).resolve().parent))
from ket_luan import he_thong, thu_muc_lap, kha_thi, nhan_xet, toc_do, toc_do_ban_cuoi  # noqa: E402

T = Path(__file__).resolve().parents[1]
OUT = T / "tai_lieu" / "Slide_Task2_LeTuanKiet.pptx"
NAVY, TEAL, GREY, LIGHT = RGBColor(0x16, 0x2B, 0x40), RGBColor(0x0E, 0x7C, 0x86), RGBColor(0x55, 0x5F, 0x6B), RGBColor(0xE9, 0xF1, 0xF5)


def J(p):
    return json.loads((T / p).read_text(encoding="utf-8"))


def vn(x, d=2):
    return "–" if x is None or x == "" else f"{float(x):.{d}f}".replace(".", ",")


def mt(v, s):
    p = T / "runs" / "mt" / v / s / "score.json"
    return J(p.relative_to(T)) if p.exists() else None


def csvr(p):
    return list(csv.DictReader(open(T / p, encoding="utf-8-sig")))


class Deck:
    def __init__(self):
        self.p = Presentation(); self.p.slide_width, self.p.slide_height = Inches(13.333), Inches(7.5)
        self.n = 0

    def slide(self, title, sub=None, src=None, tsize=30):
        s = self.p.slides.add_slide(self.p.slide_layouts[6]); self.n += 1
        self.text(s, title, 0.6, 0.35, 12.1, 0.8, tsize, True, NAVY)
        if sub:
            self.text(s, sub, 0.6, 1.1, 12.1, 0.5, 16, False, GREY)
        ln = s.shapes.add_connector(1, Inches(0.6), Inches(1.65), Inches(12.73), Inches(1.65)); ln.line.color.rgb = RGBColor(0xC8, 0xD3, 0xDB)
        if src:
            self.text(s, "Nguồn: " + src, 0.6, 7.0, 11.0, 0.35, 10, False, GREY)
        self.text(s, str(self.n), 12.3, 7.0, 0.5, 0.35, 11, True, TEAL)
        return s

    def text(self, s, t, x, y, w, h, size=16, bold=False, color=NAVY, align=None):
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
        for i, line in enumerate(t.split("\n")):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            r = para.add_run(); r.text = line; r.font.size = Pt(size); r.font.bold = bold; r.font.color.rgb = color; r.font.name = "Arial"
            if align:
                para.alignment = align
        return tb

    def bullets(self, s, items, x=0.6, y=1.85, w=12.1, h=4.9, size=17):
        tb = s.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h)); tf = tb.text_frame; tf.word_wrap = True
        for i, it in enumerate(items):
            para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
            r = para.add_run(); r.text = "• " + it; r.font.size = Pt(size); r.font.color.rgb = NAVY; r.font.name = "Arial"
            para.space_after = Pt(8)

    def table(self, s, header, rows, x=0.6, y=1.85, w=12.1, rh=0.42, size=13, col_w=None):
        shp = s.shapes.add_table(len(rows) + 1, len(header), Inches(x), Inches(y), Inches(w), Inches(rh * (len(rows) + 1)))
        tb = shp.table
        if col_w:
            for i, cw in enumerate(col_w):
                tb.columns[i].width = Inches(cw)
        for i, hd in enumerate(header):
            c = tb.cell(0, i); c.text = str(hd)
            for pp in c.text_frame.paragraphs:
                for r in pp.runs:
                    r.font.size = Pt(size); r.font.bold = True; r.font.color.rgb = RGBColor(0xFF, 0xFF, 0xFF)
            c.fill.solid(); c.fill.fore_color.rgb = NAVY
        for ri, row in enumerate(rows, 1):
            for ci, v in enumerate(row):
                c = tb.cell(ri, ci); c.text = str(v)
                for pp in c.text_frame.paragraphs:
                    for r in pp.runs:
                        r.font.size = Pt(size); r.font.color.rgb = NAVY
                c.fill.solid(); c.fill.fore_color.rgb = LIGHT if ri % 2 else RGBColor(0xFF, 0xFF, 0xFF)
        return tb

    def img(self, s, p, x, y, w=None, h=None):
        f = T / p
        if f.exists():
            s.shapes.add_picture(str(f), Inches(x), Inches(y), Inches(w) if w else None, Inches(h) if h else None)


def main():
    D = Deck()
    vers = [v for v in ("V1", "V2", "V3", "V4") if mt(v, "fleurs_test_asr_pho")]
    bc = T / "reports" / "tong_hop" / "ban_cuoi.txt"
    final = bc.read_text(encoding="utf-8").split()[-1] if bc.exists() else (vers[-1] if vers else "B0")
    R = {r["run_id"]: r for r in csvr("reports/asr/results_task2.csv")}
    b0 = {s: mt("B0", s) for s in ("fleurs_test_asr_pho", "fleurs_test_clean", "fleurs_dev_asr_pho", "phomt_test")}

    s = D.slide("Dịch tiếng nói tiếng Việt → văn bản tiếng Anh (cascade ASR → MT)", tsize=26)
    D.text(s, "Báo cáo Tiến độ Task 2: Xử lý Dữ liệu, Thực nghiệm Baseline & Mô hình Đề xuất\nMiền ứng dụng: Giáo dục", 0.6, 2.0, 12, 1.2, 22, True, TEAL)
    D.text(s, "Đề tài 1 · Mã nhóm: [nhóm điền] · GVHD: [nhóm điền]\nDương Gia Bảo (SE205262) · Lê Tuấn Kiệt (SE205279) · Hồ Lâm Bảo Đăng (SE205148) · Bùi Ngọc Phương Uyên (SE205253)\n"
              "Phần trình bày: Lê Tuấn Kiệt – chạy thực nghiệm, khối dịch và phương pháp đề xuất", 0.6, 3.6, 12, 2, 16)

    s = D.slide("Tổng quan nội dung")
    D.bullets(s, ["I. Xử lý & phân tích dữ liệu (Dataset Pipeline)", "II. Kết quả thực nghiệm 2 mô hình Baseline (+ baseline khối dịch B0)",
                  "III. Phát triển & đánh giá mô hình đề xuất V1 → " + (vers[-1] if vers else "Vn"), "IV. Phân tích lỗi & đánh giá tính khả thi sản phẩm"], size=22)

    s = D.slide("Thu thập & tổng quan dữ liệu", "Toàn bộ là dữ liệu Online công khai, tải mới 30/10/2026, revision cố định", "reports/data/nguon_du_lieu.md, kiem_chung.md")
    D.table(s, ["Nguồn", "Loại", "Số mẫu", "Định dạng", "Dung lượng"], [
        ["VIVOS", "Online", "train 11.660 / test 760 câu", "WAV 16 kHz + text", "1.406,5 MB"],
        ["FLEURS vi_vn + en_us", "Online", "2.994 / 361 / 857 bản thu", "WAV + TSV", "2.259,1 MB"],
        ["PhoMT (gated)", "Online", "2.977.999 / 18.719 / 19.151 cặp", "TXT song song", "339,4 MB"],
        ["FLoRes+ (gated)", "Online", "nhãn miền 1.945 câu FLEURS", "JSONL", "< 1 MB"],
        ["Tự thu", "Offline", "0", "–", "–"]], col_w=[3.2, 1.3, 3.8, 2.3, 1.5])
    D.text(s, "Ví dụ (FLEURS test, miền Giáo dục): “Về cơ bản, hợp kim là hỗn hợp của hai kim loại trở lên.”", 0.6, 4.6, 12, 0.5, 15, False, TEAL)

    s = D.slide("Phương pháp làm sạch & gán nhãn", "Thiếu dữ liệu → trùng lặp → hỏng/nhiễu → 16 kHz mono → chuẩn hoá chữ (script của Uyên)", "reports/data/lam_sach_dem_tung_buoc.csv, reports/domain/")
    D.img(s, "reports/tong_hop/flowchart_lam_sach.png", 0.6, 1.8, w=12.1)
    D.bullets(s, ["Gán nhãn: dùng nhãn gốc của dataset; nhãn miền từ FLoRes+ (ghép câu Anh, 100% ghép được) → không gán tay, không tính Kappa",
                  "Chống leakage: 0 ID câu chung giữa các tập; 0 câu FLEURS test trùng PhoMT"], y=5.85, h=1.1, size=14)

    s = D.slide("Thống kê mô tả & mất cân bằng", "FLEURS giữ split gốc 70,61 / 8,71 / 20,68 để so được với paper", "reports/data/eda/eda_nhan_xet.md")
    D.img(s, "reports/data/eda/eda_05_ban_thu_moi_cau.png", 0.6, 1.8, h=3.6)
    D.img(s, "reports/data/eda/eda_03_gioi_tinh.png", 6.8, 1.8, h=3.6)
    D.bullets(s, ["Train: câu 2 bản thu chiếm 58,59%, câu 1 bản thu 19,74% → số lần dạy mỗi câu chênh 3 lần",
                  "Giới tính: train 74,3% nữ; dev/test 100% nam", "FLEURS test dài TB 12,62 s, gấp 3,6 lần VIVOS (3,53 s); 0,82% > 30 s"], y=5.5, h=1.5, size=14)

    s = D.slide("Xử lý mất cân bằng", "Lấy mẫu lại theo câu + độ dài (V3) và trộn PhoMT 1:1 (V2) – thiết kế của Uyên", "reports/data/can_bang/can_bang_tom_tat.json")
    D.img(s, "reports/data/can_bang/can_bang_01_theo_cau.png", 0.6, 1.8, h=3.7)
    D.img(s, "reports/data/can_bang/can_bang_02_do_dai.png", 6.8, 1.8, h=3.7)
    D.bullets(s, ["FLEURS train 2.926 → 4.468 mẫu; chênh số lần dạy trong cùng nhóm độ dài 3,0× → 1,5×",
                  "Trộn PhoMT: FLEURS chiếm 0,15% nếu gộp nguyên 3 triệu cặp → 50% khi lấy 4.468 cặp"], y=5.6, h=1.3, size=14)

    env = J("env/moi_truong.json")
    s = D.slide("Cấu hình môi trường thực nghiệm", "Một máy, một môi trường cho mọi số so sánh", "env/moi_truong.json, configs/")
    D.table(s, ["Thành phần", "Giá trị"], [
        ["Hardware", f"{env['gpu']} 8 GB, RAM 16 GB"], ["Framework", f"PyTorch {env['torch']}, Transformers {env['transformers']}, PEFT 0.12.0"],
        ["Seed", "42"], ["Baseline (ASR, MT)", "Checkpoint công bố, suy luận fp16, beam 5, batch 1 → LR/optimizer/epoch: không áp dụng"],
        ["Proposed (LoRA)", "r 16, α 32; AdamW; lr 2e-4 (V4: 5e-5); batch 16; 5 epoch; chọn epoch theo BLEU dev"]], col_w=[3.0, 9.1])

    s = D.slide("Kết quả 2 baseline: Paper vs Nhóm", None, "reports/asr/paper_comparison.csv; runs/mt/B0/*/score.json")
    rows = []
    for m, mn, pv, pf in (("phowhisper-small", "Baseline 1 · PhoWhisper-small", "6,33", "NR"), ("whisper-small", "Baseline 2 · Whisper-small", "NR", "21,2")):
        rv, rf = R[f"kiet_t2_{m}_vivos_test"], R[f"kiet_t2_{m}_fleurs_test"]
        rows.append([mn, "Paper", pv, pf, "–"]); rows.append([mn, "Nhóm", vn(rv["WER_percent"]), vn(rf["WER_percent"]), "–"])
    rows.append(["Khối dịch B0 · VinAI Translate", "Paper", "–", "–", "40,42"]); rows.append(["Khối dịch B0 · VinAI Translate", "Nhóm", "–", "–", vn(b0["phomt_test"]["BLEU"])])
    D.table(s, ["Mô hình", "Nguồn", "WER VIVOS (%)", "WER FLEURS (%)", "BLEU PhoMT"], rows, col_w=[4.3, 1.6, 2.1, 2.1, 2.0])
    D.text(s, f"Cascade PhoWhisper → B0 trên FLEURS test: BLEU {vn(b0['fleurs_test_asr_pho']['BLEU'])} (dịch transcript sạch: {vn(b0['fleurs_test_clean']['BLEU'])})", 0.6, 5.7, 12, 0.5, 16, True, TEAL)

    strata = {(r["run_id"], r["group_type"], r["group_value"]): r for r in csvr("reports/asr/strata.csv")}
    lf = strata[("kiet_t2_phowhisper-small_fleurs_test", "duration_s", ">30")]
    s = D.slide("Gap Analysis", "Kết quả khớp công bố trên cùng dataset (chênh ≤ 0,37 điểm)", "reports/asr/strata.csv, long_form_audit.csv; paper VinAI Translate Table 1")
    D.bullets(s, ["Khớp: PhoWhisper VIVOS −0,09; Whisper FLEURS +0,04; VinAI PhoMT +0,37",
                  "Domain gap: PhoWhisper fine-tune trên VIVOS → VIVOS 6,24% nhưng FLEURS 13,68%; lợi thế so với Whisper co từ 19,75 xuống 7,56 điểm",
                  f"Audio > 30 s: PhoWhisper không có timestamp → đoạn sau 30 s giải mã sai, WER {vn(lf['WER_percent'])}% ({lf['I']} từ chèn); Whisper 28,6%. Đã nghe: người đọc nói đến gần hết file",
                  "Tiền xử lý: không đổi số ↔ chữ khi chấm → câu có chữ số WER cao. Đã nghe: người đọc nói “tám không hai” cho “802”, model ghi đúng âm",
                  "Siêu tham số (H4, dev): beam 5 tốt hơn beam 1 ở audio ≤ 30 s (10,70 vs 10,91)",
                  f"Cascade mất {vn(b0['fleurs_test_clean']['BLEU'] - b0['fleurs_test_asr_pho']['BLEU'])} BLEU so với dịch sạch → mục tiêu của phương pháp đề xuất"], size=16)

    cf = J("checkpoints/V1/config.json")
    s = D.slide("Kiến trúc Proposed Method V1", "Thích nghi khối dịch với lời ASR thật bằng LoRA", "configs/mt/V1.json, checkpoints/V1/config.json")
    for i, (t, c) in enumerate((("Audio tiếng Việt", LIGHT), ("PhoWhisper-small\n(giữ nguyên)", LIGHT), ("Lời ASR\n(chữ thường, lỗi nghe)", LIGHT),
                                ("VinAI Translate\n+ LoRA (2,0% tham số)", RGBColor(0xFC, 0xE9, 0xD9)), ("Câu tiếng Anh", LIGHT))):
        box = s.shapes.add_shape(1, Inches(0.6 + i * 2.5), Inches(2.4), Inches(2.1), Inches(1.3)); box.fill.solid(); box.fill.fore_color.rgb = c
        box.line.color.rgb = TEAL; tf = box.text_frame; tf.text = t
        for pp in tf.paragraphs:
            pp.alignment = PP_ALIGN.CENTER
            for r in pp.runs:
                r.font.size = Pt(14); r.font.color.rgb = NAVY
    D.bullets(s, [f"Điểm mới so với baseline: dạy khối dịch bằng lời ASR THẬT của FLEURS train (2.926 bản thu → câu Anh), thay vì chỉ viết thường + bỏ dấu câu như VinAI",
                  f"LoRA trên q, k, v, out_proj, fc1, fc2: {cf['trainable_params']:,} tham số huấn luyện".replace(",", ".") + "; adapter 34,7 MB",
                  "Chọn epoch theo BLEU dev cascade (361 bản thu), checkpoint mỗi epoch"], y=4.2, h=2.6, size=16)

    s = D.slide("Kết quả V1 & tín hiệu cải thiện", None, "runs/mt/*/score.json; reports/mt/bootstrap_B0_V1_cascade_test.json")
    bs = J("reports/mt/bootstrap_B0_V1_cascade_test.json")
    D.table(s, ["Hệ", "Khâu nghe", "BLEU cascade test", "BLEU dịch sạch", "BLEU PhoMT"], [
        ["Baseline 1 + B0", "PhoWhisper", vn(b0["fleurs_test_asr_pho"]["BLEU"]), vn(b0["fleurs_test_clean"]["BLEU"]), vn(b0["phomt_test"]["BLEU"])],
        ["Baseline 2 + B0", "Whisper-small", vn((mt("B0", "fleurs_test_asr_wsp") or {}).get("BLEU")), vn(b0["fleurs_test_clean"]["BLEU"]), vn(b0["phomt_test"]["BLEU"])],
        *([["B1 (end-to-end)", "Whisper-small translate", vn(mt("B1_whisper-small_translate", "fleurs_test_audio")["BLEU"]), "–", "–"]] if mt("B1_whisper-small_translate", "fleurs_test_audio") else []),
        ["V1", "PhoWhisper", vn(mt("V1", "fleurs_test_asr_pho")["BLEU"]), vn(mt("V1", "fleurs_test_clean")["BLEU"]), vn(mt("V1", "phomt_test")["BLEU"])]], y=1.8, rh=0.34, size=12, col_w=[2.6, 2.2, 2.5, 2.4, 2.4])
    D.img(s, "checkpoints/V1/curves.png", 0.6, 3.95, h=2.8)
    d_sach = b0["fleurs_test_clean"]["BLEU"] - mt("V1", "fleurs_test_clean")["BLEU"]
    d_phomt = b0["phomt_test"]["BLEU"] - mt("V1", "phomt_test")["BLEU"]
    D.text(s, f"Tín hiệu cải thiện: +{vn(bs['delta'])} BLEU cascade\nKTC 95% [{vn(bs['ci95'][0])}; {vn(bs['ci95'][1])}], p < 0,001\n\n"
              f"Đánh đổi: dịch sạch −{vn(d_sach)}, PhoMT −{vn(d_phomt)}\nĐỉnh ở epoch 1 rồi giảm → overfit",
           8.6, 4.1, 4.2, 2.6, 15, True, TEAL)

    fa = J("reports/mt/failure_V1_dev.json")["groups"]
    s = D.slide("Phân tích lỗi V1 (trên dev)", "Confusion matrix dấu thanh của khâu nghe + BLEU theo nhóm câu", "reports/mt/failure_V1_dev.md; reports/asr/tone_confusion_*.png")
    D.img(s, "reports/asr/tone_confusion_kiet_t2_phowhisper-small_fleurs_test.png", 0.5, 1.75, h=3.9)
    D.table(s, ["Nhóm câu", "n", "B0", "V1"], [[{"so": "Có chữ số", "ten": "Có tên riêng", "dai": "Lời ASR > 40 từ", "asr_xau": "ASR sai ≥ 30%", "con_lai": "Còn lại", "all": "Tất cả"}[k], v["n"], vn(v["B0"][0]), vn(v["V1"][0])] for k, v in fa.items()],
            x=5.6, y=1.8, w=7.1, rh=0.38, size=12, col_w=[2.9, 1.0, 1.6, 1.6])
    D.bullets(s, ["Lỗi chính: rút gọn/diễn giải mất ý – 8/361 bản dịch ngắn < 0,7 tham chiếu (B0: 0)",
                  "“…colonization period which lasted for three centuries” → V1 “…a three-century period of colonialism”",
                  "Nguyên nhân: 2.926 câu dạy, lr cao → mô hình học kiểu câu FLEURS, quên miền gốc"], x=5.6, y=4.65, w=7.1, h=2.3, size=13)

    s = D.slide("Đề xuất cải tiến V2 và các phiên bản tiếp theo", "Mỗi phiên bản chỉ đổi 1 yếu tố, lý do lấy từ phân tích lỗi trên dev", "configs/mt/V2.json, V3.json, V4.json")
    rows13 = [["V2", "+ 4.468 cặp PhoMT (trộn 1:1)", "V1 quên miền gốc (dịch sạch, PhoMT giảm), rút gọn câu", nhan_xet("V2", "V1") if "V2" in vers else "–"],
              ["V3", "Phần FLEURS cân bằng theo câu + độ dài (4.468)", "Đo hiệu quả xử lý mất cân bằng; câu dài, tên riêng còn yếu", nhan_xet("V3", "V2") if "V3" in vers else "–"],
              ["V4", "lr 2e-4 → 5e-5 (gốc: bản tốt hơn trên dev giữa V2/V3)", "Mọi lần train đều đỉnh ở epoch 1 rồi giảm → học quá nhanh", nhan_xet("V4", "V3") if "V4" in vers else "đang chạy"]]
    D.table(s, ["Phiên bản", "Thay đổi so với bản trước", "Lý do (phân tích lỗi trên dev)", "Kết quả (BLEU)"], rows13, rh=0.9, size=12, col_w=[1.2, 3.2, 3.6, 4.1])

    rows = [["B0", vn(b0["fleurs_dev_asr_pho"]["BLEU"]), vn(b0["fleurs_test_asr_pho"]["BLEU"]), vn(b0["fleurs_test_clean"]["BLEU"]), vn(b0["phomt_test"]["BLEU"])]]
    for v in vers + [a for a in ("A_r8", "A_r32", "A_aug") if mt(a, "fleurs_test_asr_pho")]:
        rows.append([v + (" ★" if v == final else ""), vn(mt(v, "fleurs_dev_asr_pho")["BLEU"]), vn(mt(v, "fleurs_test_asr_pho")["BLEU"]),
                     vn((mt(v, "fleurs_test_clean") or {}).get("BLEU")), vn((mt(v, "phomt_test") or {}).get("BLEU"))])
    s = D.slide("Bảng tổng hợp (Ablation Study)", f"★ = bản cuối {final} (quy tắc DEV chốt trước ablation) · A_* = ablation một yếu tố so với V2", "reports/tong_hop/ablation.csv; reports/ablation/bang_ablation.csv")
    D.table(s, ["Phiên bản", "Dev cascade", "Test cascade", "Test dịch sạch", "PhoMT test"], rows, w=6.4, rh=0.36, size=12, col_w=[1.4, 1.25, 1.25, 1.25, 1.25])
    D.img(s, "reports/tong_hop/ablation.png", 7.1, 1.85, w=5.8)
    devs = {v: mt(v, "fleurs_dev_asr_pho")["BLEU"] for v in vers}
    ds = {v: mt(v, "fleurs_dev_clean")["BLEU"] for v in vers}
    ch_ = J("reports/ablation/chon_ban_cuoi.json") if (T / "reports/ablation/chon_ban_cuoi.json").exists() else None
    D.text(s, (f"Quy tắc DEV (chốt trước ablation): hoà = dev cascade ≥ {vn(ch_['M_dev_cascade'])} − 0,5 → {', '.join(ch_['nhom_hoa'])}; chọn dev sạch cao nhất → {ch_['ban_chon']}.\n"
               "Rank 8/32 không khác V2 có ý nghĩa; augmentation làm giảm cascade.") if ch_ else "",
           0.6, 5.6, 6.4, 1.3, 12, True, TEAL)

    dm = [r for r in csvr("reports/domain/ket_qua_theo_mien.csv") if r["khoi"] == "MT" and r["tap"] == "fleurs_test_asr_pho" and r["he"] in ["B0"] + vers]
    miens = sorted({r["mien"] for r in dm}, key=lambda m: (not m.startswith("Giáo dục"), m))
    s = D.slide("Kết quả theo miền – trọng tâm Giáo dục", "Miền theo nguồn câu FLoRes+: Giáo dục = Wikibooks (sách giáo khoa mở)", "reports/domain/ket_qua_theo_mien.csv")
    D.table(s, ["Miền", "n"] + ["B0"] + vers, [[m.split(" (")[0], next(r["n_ban_thu"] for r in dm if r["mien"] == m)] +
                                               [next((vn(r["BLEU"]) for r in dm if r["mien"] == m and r["he"] == h), "–") for h in ["B0"] + vers] for m in miens], w=6.6, size=13)
    D.img(s, "reports/tong_hop/mien_giao_duc.png", 7.3, 1.85, w=5.6)

    s = D.slide("Trực quan hoá kết quả đầu ra", f"Ví dụ thật trên FLEURS test (miền Giáo dục) – B0 so với {final}", f"runs/mt/B0, runs/mt/{final}/fleurs_test_asr_pho/hyp.jsonl")
    mien = {(r["split"], r["sent_id"]): r["domain"] for r in csvr("reports/domain/fleurs_mien.csv")}
    data = {json.loads(l)["id"]: json.loads(l) for l in open(T / "runs" / "mt_data" / "fleurs_test_asr_pho.jsonl", encoding="utf-8")}
    A = {json.loads(l)["id"]: json.loads(l) for l in open(T / "runs" / "mt" / "B0" / "fleurs_test_asr_pho" / "hyp.jsonl", encoding="utf-8")}
    B = {json.loads(l)["id"]: json.loads(l) for l in open(T / "runs" / "mt" / final / "fleurs_test_asr_pho" / "hyp.jsonl", encoding="utf-8")} if final != "B0" else A
    import sacrebleu
    ch = sacrebleu.CHRF(word_order=2)
    cand = sorted((ch.sentence_score(B[i]["hyp"], [B[i]["ref"]]).score - ch.sentence_score(A[i]["hyp"], [A[i]["ref"]]).score, i) for i in A
                  if mien.get(("test", data[i]["sent_id"])) == "wikibooks" and 12 <= len(A[i]["ref"].split()) <= 22
                  # không chọn câu mà bản dịch sai số (vd 1920s -> 1990s)
                  and set(re.findall(r"\d+", B[i]["ref"])) <= set(re.findall(r"\d+", B[i]["hyp"])))
    seen, ex = set(), []
    for d_, i in reversed(cand):
        if data[i]["sent_id"] not in seen:
            seen.add(data[i]["sent_id"]); ex.append(i)
        if len(ex) == 2:
            break
    rows = []
    for i in ex:
        rows += [["Lời ASR", A[i]["src"]], ["Tham chiếu", A[i]["ref"]], ["B0", A[i]["hyp"]], [final, B[i]["hyp"]]]
    D.table(s, ["", "Nội dung"], rows, rh=0.5, size=11, col_w=[1.6, 10.5])
    D.text(s, "Chọn tự động: 2 câu Giáo dục (12–22 từ) có chrF++ tăng nhiều nhất, bản dịch giữ đúng số; không phải trung bình – xem bảng ablation.", 0.6, 6.6, 12, 0.4, 11, False, GREY)

    s = D.slide("Đánh giá tính khả thi", "Tiêu chí lấy từ đề cương Task 1: real-time (RTF < 1), đo latency median/p95, không giảm BLEU dịch chuẩn", f"reports/toc_do/{thu_muc_lap().name}/*.json – trung vị 3 lần đo xen kẽ cùng phiên, 100 bản thu, batch 1")
    rows = []
    for v in dict.fromkeys(["B0", final, "V4"]):
        q = toc_do(v) if v != final else toc_do_ban_cuoi(v)[0]
        if q:
            rows.append([v if v == "B0" or toc_do(v) else f"{v} (số V3)", vn(q["RTF_total"], 3), vn(q["latency_p50_s"]), vn(q["latency_p95_s"]), vn(q["gpu_peak_allocated_bytes"] / 2**30), vn(q["ram_rss_peak_bytes"] / 2**30),
                         vn((q["asr_checkpoint_bytes"] + q["mt_checkpoint_bytes"] + q["adapter_bytes"]) / 1e9)])
    D.table(s, ["Hệ", "RTF", "p50 (s)", "p95 (s)", "VRAM (GiB)", "RAM (GiB)", "Model (GB)"], rows or [["chưa đo"] + [""] * 6], y=1.75, size=11, rh=0.3)
    kt, verdict = kha_thi(final)
    D.table(s, ["Tiêu chí", "Giá trị", "Đạt?"], [[a, b, "–" if c is None else ("Đạt" if c else "Chưa đạt")] for a, b, c in kt],
            y=3.15, rh=0.3, size=10, col_w=[6.6, 3.8, 1.7])
    D.text(s, "Kết luận: " + verdict, 0.6, 6.2, 12.1, 0.7, 14, True, TEAL)

    kq, bsh, thu_muc_ht = he_thong()
    if kq:
        # slide số đo cả hệ của sản phẩm cuối (fix.zip)
        s = D.slide("Sản phẩm: đo cả hệ trên GPU", f"LoRA {final} + tiền/hậu xử lý (chia đoạn tại chỗ ngắt, bỏ lặp, đổi số) – không huấn luyện thêm",
                    f"reports/{thu_muc_ht}/ket_qua.json, bootstrap_cu_vs_moi.json (tests/danh_gia_proposed.py của sản phẩm)")
        rr = []
        for ten, k in (("Xử lý cũ", "truoc_0411"), ("Bản cuối", "proposed")):
            for nhom, nn in (("tat_ca", "toàn bộ"), ("dai", "audio dài")):
                q = kq[k][nhom]
                rr.append([ten, f"{nn} ({q['n']})", vn(q["WER_asr"]), vn(q["BLEU"]), vn(q["chrF++"]), vn(q["RTF"], 3)])
        D.table(s, ["Cấu hình", "Nhóm (n)", "WER (%)", "BLEU", "chrF++", "RTF"], rr, size=14, rh=0.45)
        if bsh:
            D.text(s, f"BLEU cả hệ {vn(bsh['BLEU_A'])} → {vn(bsh['BLEU_B'])}, Δ " + f"{bsh['delta']:+.2f}".replace(".", ",") +
                   f" [{vn(bsh['ci95'][0])}; {vn(bsh['ci95'][1])}] → không có ý nghĩa thống kê, không làm giảm chất lượng.\n"
                   f"Câu có chữ số ({bsh['cau_co_chu_so']['n']}): {vn(bsh['cau_co_chu_so']['BLEU_A'])} → {vn(bsh['cau_co_chu_so']['BLEU_B'])} · audio dài: "
                   f"{vn(kq['truoc_0411']['dai']['BLEU'])} → {vn(kq['proposed']['dai']['BLEU'])} (10 bản, tham khảo).\n"
                   "Số cả hệ đo bằng sản phẩm, khác bối cảnh với bảng ablation (từng khối).", 0.6, 4.4, 12.1, 2.2, 15, True, TEAL)

    s = D.slide("Kế hoạch Task 3 – tình trạng", "Theo repo cuối", "repo_cuoi/CHANGELOG.md; KIEM_THU_CUOI.md")
    D.table(s, ["Việc", "Tình trạng"], [
        [f"Đóng gói model (ASR + MT + adapter {final}), API FastAPI, giao diện Gradio, Docker, CI", "Đã có"],
        ["Audio > 30 s: chia đoạn tại chỗ ngắt nghỉ; đổi số đọc bằng chữ → chữ số", "Đã có, đã đo trên 857 bản (slide trước)"],
        ["Thu âm trực tiếp (micro), hiện kết quả khi đang nói", "Đã có; còn thử bằng micro thật 45–60 s"],
        ["Đọc m4a/webm (file điện thoại)", "Cần ffmpeg trên máy chạy"],
        ["Kiểm thử với audio tự thu (bộ 20 câu tests/bo_cau_tu_thu)", "Cả nhóm thu"],
        ["Báo cáo tốt nghiệp", "Cả nhóm"]], col_w=[8.0, 4.1])

    s = D.slide("Cảm ơn và Q&A")
    D.text(s, "Toàn bộ script, log, checkpoint và bảng số: teamwork/task3 (NHAT_KY.md ghi từng bước)", 0.6, 3.2, 12, 1, 18, False, TEAL)
    D.p.save(OUT)
    print(OUT, D.n, "slide")


if __name__ == "__main__":
    main()
