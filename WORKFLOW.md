# WORKFLOW: tiến độ dự án

**Đề tài 1:** nhận dạng giọng nói tiếng Việt và dịch sang tiếng Anh (cascade PhoWhisper-small → VinAI Translate vi2en).
Cập nhật: 23/10/2026. Tick `[x]` khi xong và có file minh chứng trong repo.

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| Task 1 | Proposal: bài toán, related work, 2 baseline, phương pháp đề xuất, dữ liệu, đánh giá | ✅ Đã nộp 13/10/2026 |
| **Task 2** | Xử lý dữ liệu, chạy lại 2 baseline, Proposed Method V1 → V3, kết luận khả thi | ✅ Thực nghiệm xong · chờ Kappa, thuyết trình |
| Task 3 | Demo Gradio, đóng gói (FastAPI, Docker: điểm cộng), báo cáo cuối | ⏳ |

Phân công giữ theo vai trò Task 1: **TV1 Bảo** (ASR), **TV2 Kiệt** (MT, Proposed Method), **TV3 Đăng** (hệ thống, demo), **TV4 Uyên** (dữ liệu, đánh giá).

---

## Task 1: đã xong

- [x] Chạy lại Baseline A: PhoWhisper-small trên VIVOS test, WER 6,25% (paper 6,33%). TV1, `reports/task1/asr/`
- [x] Chạy lại Baseline B: VinAI Translate trên PhoMT test, BLEU 40,25 (paper 40,42). TV2, `reports/task1/mt/`
- [x] Đo lỗi lan truyền trên FLEURS: BLEU 37,89 (chữ chuẩn) → 24,27 (cascade). TV2
- [x] Kiểm leakage FLEURS ↔ PhoMT: 0 câu trùng. Loại `vi2en-v2` khỏi baseline (L2). TV4, `reports/task1/data/`
- [x] Thống kê FLEURS test: 857 bản thu, 347 câu, 3,0 giờ, nhãn giới tính 100% MALE. TV4
- [x] Bảng số liệu có nguồn: `reports/task1/so_lieu_chung.json`. Script tính lại không cần GPU: `src/eval/recompute_metrics.py`
- [x] WER tách thay thế/xóa/chèn (FLEURS: S 2.058, D 112, I 1.007)

**Tồn từ Task 1:** [x] chạy lại hai baseline trên cùng RTX 4060 · [ ] mời Bảo, Đăng, Uyên làm collaborator

---

## Task 2: thực nghiệm xong (23/10/2026), chờ gán nhãn Kappa và thuyết trình

Kết quả chính (FLEURS test, cascade, cùng script và cấu hình): B0 24,27 → V1 28,59 → V2 27,57 → **V3 27,75 (bản cuối, chọn trên dev)**;
PhoMT test B0 40,27 → V3 39,86; V3 so với B0 +3,49 BLEU, khoảng tin cậy 95% [+2,34; +4,70], p < 0,001. Chi tiết: `reports/task2/`.

### Giai đoạn 1: dữ liệu
- [x] Tải FLEURS train/dev/test; ghép theo ID câu; 0 câu trùng giữa các tập (`data/download_fleurs.py`, `data/build_fleurs_eval.py`)
- [x] 1.1 Bảng nguồn online/offline (offline: không thu thập, có lý do)
- [x] 1.2 Làm sạch có số mẫu từng bước: train loại 67 bản thu thiếu câu Anh (`src/data/clean_eda.py`)
- [ ] 1.2 Gán nhãn loại lỗi 100 câu dev và Cohen's Kappa: **cần 2 người gán độc lập (Đăng, Uyên)**
- [x] 1.3 Thống kê và mất cân bằng có %: train 74,3% giọng nữ, dev/test 100% nam; tỉ lệ 70,6/8,7/20,7
- [x] 1.4 Xử lý mất cân bằng (cân bằng theo câu, V2b) có biểu đồ trước/sau và kết quả đo: không cải thiện

### Giai đoạn 2: hai baseline cùng môi trường
- [x] Baseline A trên RTX 4060: PhoWhisper VIVOS 6,25 (760/760 câu giống Task 1), FLEURS 12,29; Whisper-small 22,26 / 21,42
- [x] Baseline B và cascade cùng máy: PhoMT 40,27, FLEURS chữ chuẩn 37,85, cascade 24,27
- [x] PhoWhisper nghe FLEURS train/dev (WER 11,35 / 11,32) làm dữ liệu dạy
- [x] Paper và Nhóm, Gap Analysis (domain gap, cách viết số, môi trường, gom câu)

### Giai đoạn 3: Proposed Method
- [x] V1 (LoRA): cascade 28,59; overfit từ epoch 2; PhoMT −2,37
- [x] Failure cases: ma trận nhầm dấu thanh, tên riêng (65,2% nghe đúng; tên nước ngoài 43,8%), số đọc thành chữ, lỗi dịch
- [x] V2 (thêm dữ liệu sạch): 27,57, PhoMT −0,47 · V2b (cân bằng theo câu): không nhận · V3a (chuẩn hóa số khi dịch): không nhận
- [x] V3 (chuẩn hóa số cả khi dạy và khi dịch): 27,75; câu có chữ số +1,06 so với V2; chọn trên FLEURS dev và PhoMT dev
- [x] Ablation, kiểm định bootstrap cho V1, V2, V2b, V3
- [x] 3.4 Khả thi: RTF 0,358, VRAM 1.775 MB, âm thanh dài có VAD RTF 0,274; độ trễ trung vị 4,29 s chưa đạt ngưỡng 3 s → KHẢ THI

### Slide và báo cáo
- [x] 23 slide `reports/task2/slides/` (dựng từ file kết quả) · báo cáo `reports/task2/BaoCao_Task2_DeTai1.pdf`
- [ ] Điền mã nhóm, GVHD (slide 1) và Kappa (slide 5)

---
## Task 3: sau Task 2
- [ ] Demo Gradio: tab upload file và tab micro, hiện song song chữ Việt và câu Anh kèm mốc thời gian. TV3
- [ ] Video demo dự phòng 2–5 phút
- [ ] (Điểm cộng) FastAPI +3, Docker + CI/CD + deploy +5
- [ ] Báo cáo PDF 15–25 trang, bảng phân công và tỉ lệ đóng góp, ghi chú phần dùng công cụ AI

---

## Quy tắc chung
- Mọi con số phải lấy từ kết quả chạy thật và ghi kèm nguồn. Số kỳ vọng ghi rõ là "mục tiêu".
- Test chỉ dùng để chấm. Chọn cấu hình trên validation.
- Không commit dữ liệu, checkpoint, âm thanh, hay bất cứ nội dung nào của PhoMT.
- Commit bằng tài khoản của chính mình. Message dạng `task2: <việc đã làm>`.
