#!/usr/bin/env python3
"""Sinh BAN_GIAO_KIET.md (bàn giao cho Đăng ghép + cả nhóm) từ kết quả trong task3 – số đọc từ file, không gõ tay."""
import csv
import json
import sys
from pathlib import Path

T = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(T / "scripts"))
from ket_luan import bleu, he_thong, kha_thi, quy_tac_chon, toc_do, toc_do_ban_cuoi, vn  # noqa: E402


def main():
    final = (T / "reports" / "tong_hop" / "ban_cuoi.txt").read_text(encoding="utf-8").split()[-1]
    vers = [v for v in ("B0", "V1", "V2", "V3", "V4") if bleu(v, "fleurs_test_asr_pho") is not None]
    R = {r["run_id"]: r for r in csv.DictReader(open(T / "reports" / "asr" / "results_task2.csv", encoding="utf-8-sig"))}
    L = ["# Bàn giao Task 2 – Lê Tuấn Kiệt (SE205279)", "",
         "Toàn bộ chạy mới trong `teamwork/task3` (30–31/10/2026, RTX 4060 Laptop 8 GB). Nhật ký từng bước: `NHAT_KY.md`; trạng thái: `TRANG_THAI.md`.",
         "Mọi số dưới đây sinh tự động từ file kết quả (`scripts/tao_ban_giao.py`).", "",
         "## 1. Tài liệu đã làm", "",
         "| File | Nội dung |", "|---|---|",
         "| `tai_lieu/BaoCao_Task2_LeTuanKiet.docx` | Báo cáo Task 2 phần của Kiệt (dữ liệu đã chạy, baseline, V1→V4, ablation, miền Giáo dục, khả thi) |",
         "| `tai_lieu/Slide_Task2_LeTuanKiet.pptx` | 19 slide theo cấu trúc Huong_dan_Task2 |",
         "| `tai_lieu/BaoCao_ASR_Task2_DA_DIEN.docx`, `Slide_ASR_Task2_DA_DIEN.pptx` | BẢN CHÉP tài liệu của Bảo đã điền ô [CHỜ KIỆT] (bản gốc trong task2 không sửa) |",
         "| `tai_lieu/NGUON_SO_DA_DIEN.csv` | Ô nào ← file kết quả nào (để Đăng kiểm khi ghép) |",
         "| `reports/asr/` | results_task2.csv, paper_comparison.csv, strata.csv, long_form_audit.csv, error_audit.csv, run_metadata_*.json, tone_confusion_* |",
         "| `reports/tong_hop/` | ablation.csv/.md/.png, mien_giao_duc.png, asr_baseline.png, flowchart_lam_sach.png |",
         "| `nghe_kiem/` | Bộ nghe kiểm 10 audio – **chưa có người nghe** |", "",
         "## 2. Baseline ASR (protocol bao_asr_v1_20261027)", "", "| Model | VIVOS WER/CER | FLEURS WER/CER | Paper |", "|---|---|---|---|"]
    for m, n, pp in (("phowhisper-small", "PhoWhisper-small", "VIVOS 6,33"), ("whisper-small", "Whisper-small", "FLEURS 21,2")):
        v, f = R[f"kiet_t2_{m}_vivos_test"], R[f"kiet_t2_{m}_fleurs_test"]
        L.append(f"| {n} | {vn(v['WER_percent'])} / {vn(v['CER_percent'])} | {vn(f['WER_percent'])} / {vn(f['CER_percent'])} | {pp} |")
    L += ["", "## 3. Khối dịch: B0 → V1 … (BLEU, sacreBLEU 2.4.3)", "", "| Hệ | dev cascade | test cascade | test sạch | PhoMT test | Whisper → dịch |", "|---|---|---|---|---|---|"]
    for v in vers:
        w = bleu(v, "fleurs_test_asr_wsp")
        L.append(f"| {v}{' ★' if v == final else ''} | {vn(bleu(v, 'fleurs_dev_asr_pho'))} | {vn(bleu(v, 'fleurs_test_asr_pho'))} | {vn(bleu(v, 'fleurs_test_clean'))} | "
                 f"{vn(bleu(v, 'phomt_test'))} | {vn(w) if w is not None else '–'} |")
    L += ["", f"★ bản cuối = **{final}**. {quy_tac_chon(final)}", "", "Paper VinAI Translate VI-EN PhoMT test 40,42 (Interspeech 2022, Table 1).", ""]
    rows, verdict = kha_thi(final)
    L += ["## 4. Tốc độ & khả thi (trung vị các lần đo xen kẽ)", "", "| Tiêu chí | Giá trị | Đạt? |", "|---|---|---|"]
    L += [f"| {a} | {b} | {'–' if c is None else ('Đạt' if c else 'Chưa đạt')} |" for a, b, c in rows]
    t0, (tf, ten_td, _) = toc_do("B0"), toc_do_ban_cuoi(final)
    if t0 and tf:
        L += ["", f"B0: RTF {vn(t0['RTF_total'], 3)}, p50 {vn(t0['latency_p50_s'])} s; {final}{'' if ten_td == final else ' (số đo của ' + ten_td + ')'}: RTF {vn(tf['RTF_total'], 3)}, p50 {vn(tf['latency_p50_s'])} s "
              f"({tf.get('n_lan_do', 1)} lần đo mỗi hệ)."]
    kq, bsh, thu_muc_ht = he_thong()
    if kq:  # số cả hệ của sản phẩm cuối (fix.zip)
        L += ["", f"## 4b. Cả hệ trong sản phẩm (repo cuối, chạy GPU) – `reports/{thu_muc_ht}/`", "",
              "| Cấu hình | n | WER (%) | BLEU | chrF++ | RTF |", "|---|---|---|---|---|---|"]
        for ten, k in (("xử lý cũ", "truoc_0411"), ("bản cuối", "proposed")):
            for nhom in ("tat_ca", "dai"):
                q = kq[k][nhom]
                L.append(f"| {ten} · {'toàn bộ' if nhom == 'tat_ca' else 'audio dài'} | {q['n']} | {vn(q['WER_asr'])} | {vn(q['BLEU'])} | {vn(q['chrF++'])} | {vn(q['RTF'], 3)} |")
        if bsh:
            L += ["", f"Δ BLEU bản cuối – xử lý cũ: " + f"{bsh['delta']:+.2f}".replace(".", ",") + f" [{vn(bsh['ci95'][0])}; {vn(bsh['ci95'][1])}], p = {vn(bsh['p_one_sided_delta_le_0'], 3)} → không có ý nghĩa thống kê."]
    L += ["", f"**Kết luận:** {verdict}.", "",
          "## 5. Việc còn cần người trong nhóm", "",
          "- Nghe 10 audio trong `nghe_kiem/` và điền CSV → chạy lại `scripts/dien_tai_lieu_bao.py` để cập nhật ô \"đã nghe audio\".",
          "- Mã nhóm, GVHD cho slide 1 (đang để [nhóm điền]).",
          "- Đăng: ghép số từ bản chép đã điền (đối chiếu `NGUON_SO_DA_DIEN.csv`). Báo cáo của Bảo ghi \"Đăng mới thay [CHỜ KIỆT]\" nên bản gốc để Đăng thay.",
          "- Nhóm đã thống nhất (03/11/2026): miền Giáo dục; bản cuối và sản phẩm dùng " + final + " (configs/ban_chot.json của sản phẩm). Tốc độ và Whisper → " + final + " đo bổ sung 03/11.", ""]
    (T / "BAN_GIAO_KIET.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
