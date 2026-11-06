# Kiểm thử cuối – PASS / FAIL / NOT RUN (Lê Tuấn Kiệt, 04/11/2026)

Theo mục 04 và 08 của file phân công. Mọi mục PASS đều có file bằng chứng; mục chưa làm ghi NOT RUN kèm lý do.
Máy: RTX 4060 Laptop 8 GB, Windows 11, Python 3.11.1, torch 2.0.1+cu117. Bản chạy: repo cuối, adapter mặc định **V2**.

| Hạng mục | Kết quả | Chi tiết | Bằng chứng |
|---|---|---|---|
| B0 / B1 / Proposed cùng manifest test, cùng metric | PASS | 857 bản FLEURS test, sacreBLEU 2.4.3, dự đoán riêng từng hệ theo schema chung | `experiments/reports/danh_gia/`, `notebooks/06_danh_gia_tong_hop.ipynb` |
| B1 Whisper Translate chạy thật | PASS | `openai/whisper-small` @973afd24, `task=translate`; 857/857 mẫu ok; BLEU 3,80, chrF++ 25,45 | `experiments/runs/b1/`, `notebooks/02_baseline_B1_whisper_translate.ipynb` |
| B1 so với paper | NOT RUN | Chưa tra bảng dịch FLEURS của paper Whisper; B1 ghi là baseline đối chứng theo proposal Task 1, không nhận là tái lập paper | – |
| Kiểm toán V1–V4 | PASS | Config, seed 42, checkpoint mỗi epoch, 0 câu train trùng dev/test | `notebooks/03_ablation_va_chon_ban_cuoi.ipynb` mục 1 |
| Ablation một yếu tố | PASS | Rank 8, rank 32, augmentation so với V2; có checkpoint, log, bootstrap | `experiments/reports/ablation/`, `checkpoints/A_*` |
| Quy tắc chọn dùng số DEV | PASS, có ghi chú | Ghi file 03/11 23:38, trước ablation; kết quả V2. Quy tắc chốt sau khi đã có số test của V1–V4 nên không phải lựa chọn mù với test | `experiments/reports/ablation/QUY_TAC_CHON.md`, `chon_ban_cuoi.json` |
| EDA, phân tích lỗi | PASS | 2 notebook chạy lại từ đầu, có output; phân tích lỗi gồm B1, ablation, lan truyền ASR → MT | `notebooks/eda.ipynb`, `notebooks/phan_tich_loi.ipynb` |
| Workbook ≥ 3 sheet | PASS | Baseline Comparison · Proposed & Ablation · Error & Feasibility, thêm bảng so sánh chung và 2 sheet 3 seed | `reports/bang_ket_qua.xlsx` |
| Đo cả hệ sau khi đổi tiền/hậu xử lý | PASS | V2, 857 bản: WER 12,26%, BLEU 28,15, chrF++ 53,10; so xử lý cũ +0,14 [−0,20; 0,51], không có ý nghĩa thống kê | `experiments/reports/he_thong_V2/` |
| Chia đoạn, không lặp ở chỗ nối | PASS | File blog (`1988769089134997232.wav`) hết "có thể. có thể"; 10 file > 28 s không còn cụm lặp | `experiments/reports/he_thong_V2/du_doan_proposed.jsonl`, `tests/test_audio.py` |
| Audio 1/3/5 phút | PASS | Đoạn liền nhau, phủ hết (T03) | `experiments/reports/he_thong_V2/nghiem_thu/` |
| Demo thật: upload, audio dài, im lặng, file hỏng, nhiều lượt | PASS | Gradio model thật V2: file rỗng/hỏng báo lỗi tiếng Việt; im lặng không sinh chữ; 5 lượt giống nhau; 3 người cùng lúc không lẫn | `experiments/reports/he_thong_V2/thu_gradio/ket_qua_gradio.json` |
| API thật | PASS | 200; rỗng/hỏng/sai đuôi 400; quá dung lượng 413; 5 request giống nhau | `experiments/reports/he_thong_V2/thu_gradio/ket_qua_api.json` |
| Micro thật, câu "Hôm nay là ngày 11 tháng 3 năm 2026" | NOT RUN | Cần người nói trên Chrome (khung trình duyệt của công cụ chặn micro). Mô phỏng micro 57 s qua `PhienTrucTiep` trên bản 03/11 đạt, nhưng không thay được bài này | – |
| Bộ 20 câu tự thu | NOT RUN | Cần nhóm thu âm (`tests/bo_cau_tu_thu/`) | – |
| m4a / webm | FAIL | T05 trượt: máy không có ffmpeg. wav, mp3, flac, ogg không phụ thuộc | `experiments/reports/he_thong_V2/nghiem_thu/bang.md` |
| Kiểm tra 3 seed V1–V4 và ablation | PASS | Seed 42, 1, 2; V2 test cascade 27,34 ± 0,12; quy tắc trên trung bình dev vẫn ra V2. Quy tắc xử lý ghi trước khi train seed mới | `experiments/reports/ba_seed/`, `notebooks/04_kiem_tra_3_seed.ipynb` |
| Độ bền PhoWhisper-small (chỉ đo, không fine-tune) | PASS | 857 bản FLEURS test, WER: gốc 13,68%, nhiễu 20 dB 15,32%, nhiễu 10 dB 17,02%, tốc độ 0,9 15,50%, tốc độ 1,1 14,30%, giảm 12 dB 16,38% | `experiments/reports/robust/`, `notebooks/05_do_ben_khoi_nghe.ipynb` |
| Notebook toàn bộ code | PASS | `notebooks/00_toan_bo_code.ipynb`: 134 file code, 145/145 ô có output, 0 lỗi. Chạy thật trong notebook: train ngắn 40 câu và lưu checkpoint, ASR, dịch, chấm 857 bản, bootstrap, CLI, pytest, nạp V2. Không chạy lại trọn huấn luyện và pipeline dữ liệu; các ô đó hiện log thật của lần chạy gốc | `notebooks/00_toan_bo_code.ipynb`, `DANH_MUC_CODE.md` |
| Chạy lại thực nghiệm trong notebook, seed 42 | PASS | `notebooks/01_chay_lai_thuc_nghiem.ipynb` 36/36 ô, 0 lỗi. 117.884 câu dự đoán, khác 6; adapter V1–V4 giống từng byte; số đã báo cáo không đổi. Không gồm B1, ablation, seed 1 và 2 | `experiments/chay_lai_notebook/SO_SANH_VOI_BAN_GOC.md` |
| Notebook sản phẩm V2 | PASS | `notebooks/07_chay_san_pham_tren_gpu.ipynb` 10/10 ô có output, 0 lỗi; kiểm SHA256 adapter V2 và log demo. Chạy lại 857 bản: WER 12,26%, BLEU 28,15, chrF++ 53,10, khớp số đã báo cáo; nghiệm thu 6/7 | `experiments/reports/nb07_chay_05-11/` |
| Unit test | PASS | 151 test: 145 qua, 6 bỏ qua (cần ffmpeg), 0 trượt | `pytest` |
| Ruff | PASS | `ruff check`, `ruff format --check` (0.5.7, đúng phiên bản CI) | `experiments/scripts/dong_goi_repo_cuoi.py` |
| Cài `requirements.txt` | PASS (dry-run) | pip giải phụ thuộc thành công, hết xung đột uvicorn. Chưa cài thật vào venv mới | – |
| GitHub Actions | NOT RUN | Repo chưa push lên GitHub | – |
| Docker | NOT RUN | Docker Desktop đang tắt; là điểm cộng | – |

## Hạn chế còn lại
- `bo_lap_cho_noi` bỏ cụm ≥ 2 từ lặp y hệt ở chỗ nối, nên cụm người nói cố ý lặp đúng tại điểm cắt sẽ bị xoá. Lặp 1 từ được giữ. Trên 857 bản test không có ca này.
- B1 giữ đúng cấu hình giải mã protocol (không temperature fallback), 86/857 câu lặp vòng. Đây là số của cấu hình này, không phải giới hạn tuyệt đối của Whisper.
- Seed 42 và seed 1, 2 train ở hai môi trường khác nhau; train lại V2 seed 42 trên Modal làm dev cascade 26,45 → 25,66, test cascade 27,47 → 27,32. Chỉ 3 seed nên chỉ cho biết mức dao động.
- Mục Whisper → dịch của V1 và ablation chỉ có 2 seed.
- Dev/test FLEURS 100% giọng nam.
