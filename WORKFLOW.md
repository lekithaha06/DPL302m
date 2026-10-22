# WORKFLOW: tiến độ dự án

**Đề tài 1:** nhận dạng giọng nói tiếng Việt và dịch sang tiếng Anh (cascade PhoWhisper-small → VinAI Translate vi2en).
Cập nhật: 22/10/2026. Tick `[x]` khi xong và có file minh chứng trong repo.

| Giai đoạn | Nội dung | Trạng thái |
|---|---|---|
| Task 1 | Proposal: bài toán, related work, 2 baseline, phương pháp đề xuất, dữ liệu, đánh giá | ✅ Đã nộp 13/10/2026 |
| **Task 2** | Xử lý dữ liệu, chạy lại 2 baseline, Proposed Method V1 → Vn, kết luận khả thi | 🔄 **Đang làm** |
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

**Còn tồn từ Task 1, xử lý đầu Task 2:**
- [ ] Hai baseline chạy trên 2 máy khác nhau (RTX 3050 4 GB và RTX 4060 8 GB). Task 2 yêu cầu môi trường đồng nhất, nên chạy lại cả hai trên **RTX 4060**.
- [ ] Mời Bảo, Đăng, Uyên làm collaborator. Từ Task 2 mỗi người tự commit phần mình.

---

## Task 2: đang làm

### Giai đoạn 1: dữ liệu (TV4 chính, TV3 hỗ trợ)
- [ ] Tải **FLEURS vi_vn + en_us train/dev** (hiện mới có test). Chia theo ID câu, kiểm không trùng câu với test. TV4
- [ ] 1.1 Bảng nguồn dữ liệu online/offline: URL, số mẫu, định dạng, dung lượng, các trường. TV4
- [ ] **Dữ liệu offline:** tự thu âm một tập test nhỏ (giọng nữ, micro điện thoại, nhiều miền), có phiếu đồng ý của người được thu. Đây cũng là điểm cộng "tự build". TV3 + TV4
- [ ] 1.2 Flowchart làm sạch, có số mẫu bị loại ở mỗi bước (trùng, lỗi, thiếu, đổi về 16 kHz, chuẩn hóa chữ). TV4
- [ ] 1.2 Gán nhãn tập tự thu bằng Label Studio. Hai người gán chung một phần để tính Cohen's Kappa. TV3 + TV4
- [ ] 1.3 Biểu đồ mất cân bằng **có %**: theo người nói, giới tính, độ dài âm thanh, miền văn bản PhoMT. Bảng tỉ lệ train/val/test. TV4
- [ ] 1.4 Xử lý mất cân bằng (augmentation nhiễu/tốc độ, cân bằng miền khi trộn PhoMT), có biểu đồ trước/sau. TV4

### Giai đoạn 2: hai baseline trên cùng môi trường (TV1, TV2)
- [ ] Chạy lại Baseline A trên RTX 4060, cùng seed 42 và cùng chuẩn hóa. Báo WER, CER, S/D/I trên VIVOS, FLEURS và tập tự thu. TV1
- [ ] Chạy lại Baseline B và cascade trên cùng máy. TV2
- [ ] **PhoWhisper nghe FLEURS train/dev/test, xuất chữ kèm ID câu, giao cho TV2.** Việc này chặn V1, nên làm sớm nhất. TV1
- [ ] 2.2 Bảng Paper và Nhóm cho từng baseline. 2.3 Gap Analysis: cùng miền (VIVOS) và ngoài miền (FLEURS), giải mã, chuẩn hóa. TV1 + TV2
- [ ] Ghi rõ: baseline là suy luận zero-shot nên learning rate/optimizer/epoch không áp dụng.

### Giai đoạn 3: Proposed Method (TV2 chính)
- [ ] **V1:** LoRA cho VinAI Translate trên cặp (chữ do PhoWhisper nghe ra từ FLEURS train → câu Anh). Chọn cấu hình trên dev, test chỉ để chấm. TV2
- [ ] Log loss/BLEU theo epoch, bảng siêu tham số, thời gian train, lưu checkpoint (không commit). TV2
- [ ] So V1 với cả 2 baseline: BLEU, chrF++ của cascade trên FLEURS test. Kiểm PhoMT test để chắc khối dịch không kém đi. TV2
- [ ] 3.2 Failure cases của V1: ma trận nhầm dấu thanh (TV1), câu dịch sai phân theo nguyên nhân (TV2)
- [ ] 3.3 V2, V3 dựa trên lỗi của V1, ví dụ trộn câu PhoMT sạch hoặc tạo lỗi nghe giả. Bảng tiến trình và ablation. TV2 + TV4
- [ ] 3.4 Khả thi: VAD cho âm thanh dài, RTF/latency cả hệ thống, dung lượng mô hình, thử gần real-time. Kết luận có hay không đủ điều kiện làm Task 3. TV3

### Slide Task 2 (18–25 slide)
- [ ] Slide 3–6: TV4 · 7–9: TV1 + TV2 · 10–14: TV2 (+ TV1 slide 12) · 15–17: TV3 · ghép deck, slide 1–2, 18: TV3

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
