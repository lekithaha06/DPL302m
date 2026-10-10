# WORKFLOW — DPL302m Project

**Đề tài 1:** Hệ thống nhận dạng giọng nói (ASR) tiếng Việt kèm dịch sang tiếng Anh
**Input:** file audio (wav/mp3/flac) hoặc micro real-time → **Output:** transcript tiếng Việt + bản dịch tiếng Anh (kèm timestamp)
**Tài nguyên:** RTX 4060 Laptop 8 GB (local) + Colab/Kaggle (T4/P100) cho các lần train dài

> File này là "bản đồ" của cả dự án. Mỗi phase có đầu ra cụ thể, map với rubric (Mục 7 của projectdpl).
> Tick `[x]` khi xong. Cập nhật cột "Ai làm" sau khi nhóm phân công.

---

## Tổng quan các phase

| Phase | Nội dung | Đầu ra | Rubric | Trạng thái |
|---|---|---|---|---|
| **0** | Setup repo, môi trường, phân công | Repo Git + README khung + `requirements.txt` | Code & tái lập (5) | ⏳ |
| **1** | **TASK 1 — Proposal** | Slide thuyết trình 9 phần | (Kiểm tra giữa kỳ) | 🔄 **Đang làm** |
| 2 | Dữ liệu (Bước 1) | Script tải, EDA notebook, split không leak | Dữ liệu (15) | ⏳ |
| 3 | Xử lý dữ liệu (Bước 2) | Dataset/DataLoader, augmentation | Dữ liệu (15) | ⏳ |
| 4 | Baseline (Bước 3) | Whisper zero-shot + MT zero-shot, bảng kết quả | Baseline (10) | ⏳ |
| 5 | Đề xuất + huấn luyện (Bước 4–5) | Checkpoint, log, ablation | Đề xuất (25) | ⏳ |
| 6 | Đánh giá (Bước 6) | Bảng metric, error analysis, RTF | Đánh giá (15) | ⏳ |
| 7 | Demo (Bước 7) | Gradio app (upload + mic), video dự phòng | Demo (10) | ⏳ |
| 8 | Bonus | FastAPI (+3), Docker + CI/CD + HF Spaces (+5), tự build data (+2) | Điểm cộng | ⏳ |
| 9 | Báo cáo + slide cuối | PDF 15–25 trang, 12–20 slide | Báo cáo (10) + Vấn đáp (10) | ⏳ |

---

## Phase 0 — Setup
- [ ] Tạo repo GitHub, mời đủ thành viên; mỗi người commit bằng tài khoản của mình (điểm cá nhân dựa trên git log)
- [x] Cấu trúc thư mục theo gợi ý của đề (`data/ notebooks/ src/ configs/ app/ api/ docker/ reports/`)
- [x] `requirements.txt` (ghim `==` các thư viện đã cài trên máy; còn lại `>=`, chạy `pip freeze` sau khi cài đủ)
- [x] Cố định seed (`src/utils/seed.py`), ghi môi trường vào README, test pytest
- [ ] Cài thư viện còn thiếu: `peft datasets jiwer faster-whisper silero-vad librosa soundfile`
- [ ] Cài git, `git init`, tạo repo GitHub và push
- [ ] Điền tên, MSSV, vai trò từng thành viên → cập nhật slide 1–2 Task 1

## Phase 1 — TASK 1 (Proposal) ← ĐANG LÀM
- [x] Đọc đề, chọn đề tài
- [x] Tìm Related Work/SOTA, số liệu đã kiểm chứng từ paper/model card
- [x] Xác định Research Question + Research Gap
- [x] Chọn baseline, phương pháp đề xuất, dataset, metric
- [x] Dựng slide 9 phần theo checklist Task 1
- [ ] Nhóm điền tên/MSSV/mã nhóm, review lại nội dung
- [ ] Tập thuyết trình, chuẩn bị câu hỏi vấn đáp (xem cuối file)

## Phase 2 — Dữ liệu
- [ ] Script tải: VIVOS, Common Voice vi, FLEURS vi_vn, PhoMT (cần đăng ký, chỉ dùng học thuật)
- [ ] Ghi license từng nguồn vào `data/README.md`
- [ ] EDA: tổng giờ audio, phân bố độ dài, số speaker, giới tính, sample rate, độ dài câu (số âm tiết), từ vựng OOV
- [ ] Split **theo speaker** (VIVOS đã tách sẵn speaker train/test); kiểm tra không trùng câu giữa train và test
- [ ] Dedup PhoMT train với FLEURS/FLoRes test (tránh leak khi đánh giá end-to-end)
- [ ] (Bonus +2) Tự thu âm tập test riêng: 3 miền Bắc/Trung/Nam, có nhiễu và không nhiễu, transcript + bản dịch tham chiếu; có phiếu đồng ý của người được thu âm

## Phase 3 — Xử lý dữ liệu
- [ ] Resample 16 kHz mono, chuẩn hoá biên độ, loại file lỗi/rỗng/quá dài
- [ ] Chuẩn hoá transcript: Unicode NFC, viết thường, bỏ ký tự lạ, số → chữ (thống nhất 1 quy tắc cho cả train và eval)
- [ ] Augmentation: SpecAugment, thêm nhiễu (SNR 5–20 dB), speed perturb 0.9/1.0/1.1; giải thích lý do từng loại
- [ ] Tạo nguồn MT "nhiễu kiểu ASR": bỏ dấu câu, viết thường, chèn lỗi thay thế/xoá âm tiết
- [ ] `src/dataset/` — Dataset/collator dùng lại được cho cả train và eval

## Phase 4 — Baseline
- [ ] B1: Whisper-small zero-shot (vi) → WER/CER trên VIVOS test, CV test, FLEURS test
- [ ] B2: Whisper dịch trực tiếp (task=translate) → BLEU trên FLEURS vi→en
- [ ] B3: cascade Whisper zero-shot → MT pretrained zero-shot (vinai-translate-vi2en-v2) → BLEU, chrF++
- [ ] Đo RTF, latency, kích thước model trên RTX 4060
- [ ] Error analysis của baseline (ví dụ minh hoạ) → làm động cơ cho Phase 5

## Phase 5 — Đề xuất + huấn luyện
- [ ] ASR: fine-tune Whisper-small/PhoWhisper-small (LoRA hoặc full) + augmentation nhiễu
- [ ] Phân đoạn audio dài bằng Silero VAD; streaming theo đoạn cho chế độ mic
- [ ] Punctuation & casing restoration trước MT (hoặc MT học trực tiếp trên input không dấu câu)
- [ ] MT: fine-tune mô hình vi→en trên PhoMT subset + nguồn nhiễu kiểu ASR (noise-robust MT)
- [ ] Tối ưu suy luận: faster-whisper (CTranslate2, int8/fp16)
- [ ] Log bằng TensorBoard/W&B: loss, WER/BLEU theo epoch; bảng siêu tham số; thời gian train; lưu checkpoint
- [ ] **Ablation:** bật/tắt từng thành phần (FT ASR, noise aug, VAD, punct restoration, noise-robust MT)

## Phase 6 — Đánh giá
- [ ] Bảng baseline vs đề xuất trên **cùng** tập test + **cùng** metric
- [ ] WER tách riêng lỗi thay thế/chèn/xoá; CER
- [ ] BLEU (sacreBLEU), chrF++, COMET (bonus)
- [ ] Error analysis theo nhóm: vùng miền, SNR, độ dài câu, tên riêng/số, từ mượn
- [ ] RTF, latency real-time, số tham số, VRAM

## Phase 7 — Demo
- [ ] Gradio: tab Upload file + tab Microphone (streaming), hiển thị song song VI | EN kèm timestamp
- [ ] Video demo dự phòng 2–5 phút

## Phase 8 — Bonus
- [ ] FastAPI `/transcribe`, `/translate`, `/speech-translate` + schema + xử lý lỗi (+3)
- [ ] Dockerfile + GitHub Actions (lint/test/build) + deploy HF Spaces (+5)

## Phase 9 — Báo cáo & slide cuối
- [ ] Báo cáo theo Mục 6 (15–25 trang, trích dẫn IEEE)
- [ ] Bảng phân công + tỷ lệ đóng góp
- [ ] Ghi rõ phần nào có dùng công cụ AI hỗ trợ (yêu cầu liêm chính học thuật)

---

## Phân công gợi ý (3 người)

| Vai trò | Phụ trách chính |
|---|---|
| Thành viên 1 — ASR lead | Dữ liệu speech, fine-tune Whisper, VAD/streaming, WER/RTF |
| Thành viên 2 — MT lead | PhoMT, noise-robust MT, punctuation restoration, BLEU/COMET |
| Thành viên 3 — System/Demo lead | Pipeline cascade, Gradio, FastAPI, Docker/CI, tự build tập test |

Cả nhóm cùng làm: EDA, error analysis, báo cáo, slide.

---

## Câu hỏi vấn đáp nên chuẩn bị cho Task 1
1. Tại sao chọn cascade thay vì end-to-end? (PhoST 2022: cascade vẫn tốt hơn E2E; ít dữ liệu vi-audio→en-text)
2. Tại sao chọn Whisper-small chứ không phải large? (real-time trên GPU 8 GB, RTF)
3. Dữ liệu test end-to-end lấy ở đâu khi không có corpus ST vi→en lớn? (FLEURS vi_vn song song với tiếng Anh qua FLoRes + tập tự build)
4. Làm sao chống data leakage? (split theo speaker, dedup câu, không dùng test để chọn siêu tham số)
5. License: VIVOS CC BY-NC-SA 4.0, PhoMT chỉ dùng nghiên cứu/giáo dục, VinAI Translate AGPL-3.0
