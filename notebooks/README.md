# Notebook (đã chạy, có output)

| Notebook | Nội dung |
|---|---|
| `eda.ipynb` | Thống kê mô tả dữ liệu: split, giới tính, số bản thu mỗi câu, độ dài audio/câu, miền, cân bằng |
| `phan_tich_loi.ipynb` | Phân tích lỗi: nhầm dấu thanh, WER theo nhóm, BLEU theo nhóm/miền, ca lỗi có ID, lan truyền ASR → MT, B1, ablation |
| `02_baseline_B1_whisper_translate.ipynb` | Kiểm gói baseline, chạy B1 Whisper Translate (857 bản), chấm, bootstrap với B0 |
| `03_ablation_va_chon_ban_cuoi.ipynb` | Kiểm toán V1–V4, ablation một yếu tố (rank 8/32, augmentation), áp quy tắc chọn trên DEV |
| `06_danh_gia_tong_hop.ipynb` | Prediction theo schema chung, bảng so sánh, workbook 3 sheet gốc; `04_kiem_tra_3_seed.ipynb` thêm 2 sheet, tổng 6 sheet |
| `05_do_ben_khoi_nghe.ipynb` | Độ bền PhoWhisper-small khi thêm nhiễu, đổi tốc độ, đổi âm lượng (chỉ đo, không fine-tune) |
| `04_kiem_tra_3_seed.ipynb` | Kiểm tra 3 seed cho V1–V4 và ablation, đối chứng môi trường |
| `00_toan_bo_code.ipynb` | Toàn bộ code của project, log và output thật, phần checkpoint, chạy thử model thật |
| `01_chay_lai_thuc_nghiem.ipynb` | Chạy lại thật seed 42: dữ liệu, 4 baseline ASR, B0, train V1–V4 đủ 5 epoch, đánh giá, tốc độ. So sánh với kết quả gốc ở `experiments/chay_lai_notebook/SO_SANH_VOI_BAN_GOC.md` |
| `07_chay_san_pham_tren_gpu.ipynb` | Chạy thật sản phẩm V2 trên GPU: kiểm adapter, test, đánh giá cũ/mới 857 bản, nghiệm thu, demo |

`eda` và `phan_tich_loi` chỉ đọc `experiments/`, chạy được không cần GPU. 03–05 gọi script thực nghiệm và cần thư mục làm việc có `data/` (không đẩy lên Git, xem `data/README.md`);
output đã lưu trong file, mở ra đọc được ngay. Phần đã có checkpoint/score sẽ tự bỏ qua khi chạy lại.
