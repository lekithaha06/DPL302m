#!/usr/bin/env python3
"""Sinh CHECKLIST_YEU_CAU.md: mỗi yêu cầu (phân công Kiệt, KIỆT CẦN LÀM của Bảo, checklist Huong_dan_Task2) → file bằng chứng trong gói.
Kiểm tự động từng file có tồn tại trong task3 (và trong zip nếu truyền --zip). Thiếu file nào thì báo THIẾU."""
import sys
import zipfile
from pathlib import Path

T = Path(__file__).resolve().parents[1]
REQ = [
    ("A. Phân công Task 2 của Kiệt", [
        ("1. Môi trường, tải dữ liệu, làm sạch, chia tập, EDA theo đặc tả", "Đã làm",
         ["env/requirements.txt", "env/pip_freeze.txt", "env/moi_truong.json", "reports/data/kiem_chung.md", "reports/data/nguon_du_lieu.md",
          "reports/data/lam_sach_dem_tung_buoc.csv", "reports/data/fleurs_split_ids.csv", "reports/data/eda/eda_nhan_xet.md", "reports/data/can_bang/can_bang_tom_tat.json"]),
        ("2. Chạy lại PhoWhisper, Whisper, VinAI và cascade", "Đã làm",
         ["reports/asr/results_task2.csv", "runs/asr/kiet_t2_phowhisper-small_fleurs_test/predictions.jsonl", "runs/asr/kiet_t2_whisper-small_vivos_test/predictions.jsonl",
          "runs/mt/B0/phomt_test/score.json", "runs/mt/B0/fleurs_test_asr_pho/score.json", "runs/mt/B0/fleurs_test_asr_wsp/score.json"]),
        ("3. LoRA V1 trên lời ASR train, chọn theo dev, curves, failure cases", "Đã làm",
         ["configs/mt/V1.json", "checkpoints/V1/best/adapter_model.safetensors", "checkpoints/V1/best/chon.json", "checkpoints/V1/curves.png", "reports/mt/failure_V1_dev.md"]),
        ("4. V2/V3 (+V4) và ablation B0→V1→V2→V3→V4, không bịa số", "Đã làm",
         ["configs/mt/V2.json", "configs/mt/V3.json", "configs/mt/V4.json", "reports/tong_hop/ablation.csv", "reports/tong_hop/ablation.png",
          "reports/mt/bootstrap_B0_V2_cascade_test.json", "reports/mt/failure_V3_vs_V2_dev.md", "reports/mt/failure_V2_dev.md", "reports/tong_hop/ban_cuoi.txt", "reports/ablation/QUY_TAC_CHON.md", "reports/ablation/chon_ban_cuoi.json", "reports/ablation/bang_ablation.csv", "reports/he_thong_V2/ban_chot.json"]),
        ("5. RTF, latency, VRAM, model size cùng máy; gói script, log, bảng, báo cáo, slide", "Đã làm",
         ["reports/toc_do/lap_V2/toc_do_B0_lan1.json", "reports/toc_do/lap_V2/toc_do_V2_lan3.json", "logs/tai_nguyen.csv", "scripts/mt/do_toc_do.py",
          "tai_lieu/BaoCao_Task2_LeTuanKiet.docx", "tai_lieu/BaoCao_Task2_LeTuanKiet.pdf", "tai_lieu/Slide_Task2_LeTuanKiet.pptx", "NHAT_KY.md", "reports/he_thong_V2/ket_qua.json", "reports/danh_gia/bang_ket_qua.xlsx"]),
    ]),
    ("B. Bàn giao của Bảo – KIỆT CẦN LÀM", [
        ("1. Kiểm manifest thật theo protocol; manifest cascade tách riêng", "Đã làm", ["runs/manifests/manifests_sha256.json", "runs/manifests/asr_fleurs_test.jsonl", "runs/mt_data/fleurs_test_asr_pho.jsonl"]),
        ("2. Chạy 2 checkpoint trên VIVOS 760 + FLEURS 857; 7 bản > 30 s không cắt", "Đã làm", ["reports/asr/long_form_audit.csv", "runs/asr/kiet_t2_phowhisper-small_vivos_test/segments.jsonl"]),
        ("3. Xuất dự đoán thô + metadata; chấm bằng score_asr.py, kiểm ID", "Đã làm",
         ["runs/asr/kiet_t2_phowhisper-small_fleurs_test/score/summary.json", "reports/asr/run_metadata_kiet_t2_phowhisper-small_fleurs_test.json", "scripts/asr/score_asr.py"]),
        ("4. Điền results_task2, paper_comparison; phân tích lỗi có nghe audio; tốc độ cùng máy", "Đã làm (mục 9 nghe chưa ghi cách phát âm)",
         ["reports/asr/paper_comparison.csv", "reports/asr/strata.csv", "reports/asr/error_audit.csv", "reports/asr/gap_hypotheses.csv", "nghe_kiem/danh_sach_nghe_kiem.csv"]),
        ("5. Điền ô [CHỜ KIỆT] trong báo cáo + slide của Bảo (NR ≠ 0)", "Đã làm trên bản chép",
         ["tai_lieu/BaoCao_ASR_Task2_DA_DIEN.docx", "tai_lieu/Slide_ASR_Task2_DA_DIEN.pptx", "tai_lieu/NGUON_SO_DA_DIEN.csv"]),
    ]),
    ("C. Checklist Huong_dan_Task2", [
        ("Bảng nguồn dữ liệu Online/Offline (số lượng, định dạng, dung lượng)", "Có", ["reports/data/nguon_du_lieu.md"]),
        ("Flowchart làm sạch + công cụ/tiêu chí gán nhãn (Kappa nếu có)", "Có (không gán tay → không Kappa, có ghi lý do)", ["reports/tong_hop/flowchart_lam_sach.png", "reports/domain/fleurs_mien.csv"]),
        ("Biểu đồ class distribution + nhận xét định lượng (%)", "Có", ["reports/data/eda/eda_05_ban_thu_moi_cau.png", "reports/data/eda/eda_03_gioi_tinh.png"]),
        ("Tỉ lệ Train/Val/Test rõ ràng", "Có (giữ split gốc 70,6/8,7/20,7 – có lý do)", ["reports/data/eda/eda_bang_ti_le_tap.csv"]),
        ("Biểu đồ phân bố trước/sau xử lý mất cân bằng", "Có", ["reports/data/can_bang/can_bang_01_theo_cau.png", "reports/data/can_bang/can_bang_02_do_dai.png"]),
        ("2 baseline cùng môi trường (hardware, seed, LR, optimizer, epochs)", "Có", ["env/moi_truong.json", "configs/asr_protocol.json"]),
        ("Bảng Paper vs Thực nghiệm cho từng baseline", "Có", ["reports/asr/paper_comparison.csv", "tai_lieu/paper/nguyen22e_interspeech_VinAI_Translate.pdf"]),
        ("Gap Analysis (domain / hyperparameter / tiền xử lý)", "Có", ["reports/asr/gap_hypotheses.csv", "reports/asr/strata.csv"]),
        ("V1 so với CẢ 2 baseline, chỉ rõ tín hiệu cải thiện", "Có", ["reports/mt/bootstrap_B0_V1_cascade_test.json", "reports/mt/bootstrap_B0_V2_cascade_wsp_test.json", "runs/mt/B1_whisper-small_translate/fleurs_test_audio/score.json"]),
        ("Confusion Matrix, Loss/Metric curves", "Có (ma trận nhầm dấu thanh; curves V1–V4)", ["reports/asr/tone_confusion_kiet_t2_phowhisper-small_fleurs_test.png", "checkpoints/V4/curves.png"]),
        ("Failure cases có ví dụ trực quan", "Có", ["reports/mt/failure_V1_dev.md", "reports/asr/error_audit.csv"]),
        ("V2, V3… đề xuất từ phân tích lỗi; bảng tiến trình/ablation", "Có", ["reports/tong_hop/ablation.md", "configs/mt/V3.json"]),
        ("Số liệu Accuracy, Latency/FPS, Model size + kết luận khả thi", "Có", ["reports/toc_do/lap_V2/toc_do_V2_lan1.json", "BAN_GIAO_KIET.md"]),
        ("Slide 18–25 trang", "Có (19 slide)", ["tai_lieu/Slide_Task2_LeTuanKiet.pptx"]),
    ]),
]
TODO = ["Điền mã nhóm + GVHD (slide 1 của Kiệt; báo cáo trang đầu).",
        "Nhóm chốt miền Giáo dục cho cả deck (Bảo, Uyên thêm 1 câu ở phần của mình).",
        "Đã chốt 04/11/2026: bản cuối = V2 theo quy tắc DEV chốt trước ablation (reports/ablation/QUY_TAC_CHON.md); sản phẩm = teamwork/repo_cuoi (số cả hệ: reports/he_thong_V2/). Đăng cập nhật báo cáo nhóm/slide/paper theo kien_truc/DONG_BO_V2_CHO_DANG.md.",
        "Đăng ghép: dùng bản chép đã điền của Bảo + `NGUON_SO_DA_DIEN.csv`; bản gốc của Bảo do Đăng thay [CHỜ KIỆT] theo quy trình của Bảo.",
        "(Tuỳ chọn) Mục 9 nghe kiểm: ghi cách người đọc phát âm tên riêng Ấn Độ.",
        "(Tuỳ chọn, cải thiện) H2 chấm lại với mapping số; chia đoạn audio > 30 s cho PhoWhisper; chuẩn hoá số trước khi dịch."]


def main():
    zp = Path(sys.argv[sys.argv.index("--zip") + 1]) if "--zip" in sys.argv else None
    names = set(zipfile.ZipFile(zp).namelist()) if zp else None
    L = ["# Checklist yêu cầu ↔ bằng chứng trong gói (Lê Tuấn Kiệt, Task 2)", "",
         "Mỗi dòng: yêu cầu, trạng thái, file bằng chứng (đường dẫn trong thư mục `task3/`). ✔ = file có trong gói (kiểm tự động bởi `scripts/tao_checklist.py`).", ""]
    missing = []
    for sec, items in REQ:
        L += [f"## {sec}", "", "| Yêu cầu | Trạng thái | Bằng chứng |", "|---|---|---|"]
        for req, st, files in items:
            ev = []
            for f in files:
                ok = (T / f).exists() and (names is None or ("task3/" + f) in names)
                ev.append(("✔ " if ok else "✘ THIẾU ") + f"`{f}`")
                if not ok:
                    missing.append(f)
            L.append(f"| {req} | {st} | {'<br>'.join(ev)} |")
        L.append("")
    L += ["## D. Việc còn lại cho nhóm / Đăng", ""] + [f"- {t}" for t in TODO] + [""]
    (T / "CHECKLIST_YEU_CAU.md").write_text("\n".join(L), encoding="utf-8")
    print("thieu:", missing or "khong")


if __name__ == "__main__":
    main()
