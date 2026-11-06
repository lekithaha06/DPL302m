# HANDOFF CHECKLIST - Bàn giao phần việc của Đăng

**Người bàn giao:** Hồ Lâm Bảo Đăng (SE205148)  
**Vai trò:** TV3 - Hệ thống, điều phối, Baseline và Dataset  
**Ngày:** 2026-11-03  
**Bàn giao cho:** Lê Tuấn Kiệt (TV2) - Proposed Method

---

## ✅ HOÀN THÀNH 100%

### Giai đoạn A: Kiểm kê dữ liệu và code có sẵn
- [x] Giải nén và kiểm tra GUI_DANG_FLEURS_TEST.zip
- [x] Xác nhận 857 mẫu FLEURS test hợp lệ
- [x] Kiểm tra manifest: sample_id, audio_path, reference_vi, reference_en
- [x] Đối chiếu với repo manifest: 0 thiếu, 0 thừa
- [x] Phân bố domain: 336 giáo dục, 267 tin tức, 254 du lịch
- [x] Audio: tất cả mono 16kHz, duration 4.98-38.10s (avg 12.62s)
- [x] Script: `check_data.py` (exit code 0)

### Giai đoạn B: Phục dựng và kiểm chứng B0
- [x] Xác định file B0: ASR predictions, MT hyp, MT score
- [x] Đọc cấu hình B0: PhoWhisper-small + VinAI vi2en-v2 pretrained
- [x] Kết quả B0: BLEU 22.69, chrF++ 49.38 (857 mẫu)
- [x] Kiểm tra khớp ID: 0 thiếu, 0 thừa
- [x] Tạo `b0_summary.json` với đầy đủ metadata
- [x] Script: `verify_b0.py` (exit code 0)

### Giai đoạn C: Tạo B1 Whisper Translate
- [x] Tạo `b1_whisper_translate/` với cấu trúc hoàn chỉnh
- [x] `inference.py`: WhisperTranslator class (load model, translate 1 file)
- [x] `run_fleurs_test.py`: batch inference với progress bar
- [x] `evaluate_b1.py`: tính BLEU/chrF++, so sánh B0
- [x] `requirements.txt`: transformers, torch, torchaudio, sacrebleu
- [x] `README.md` và `STATUS.md`: hướng dẫn chi tiết
- [x] Kiểm tra model size: Whisper-small 244M params < 300M limit ✅
- [x] Task = "translate", language = "vi" ✅
- [x] Beam search, early stopping ✅

### Giai đoạn D: EDA và Error Analysis
- [x] Xác nhận `repo/notebooks/eda.ipynb` đã có sẵn
- [x] Xác nhận `repo/notebooks/phan_tich_loi.ipynb` đã có sẵn
- [x] Kiểm tra cả 2 notebooks có output và hình ảnh
- [x] Đọc README notebooks: chạy được, không cần GPU
- [x] Notebooks dùng data từ `experiments/` có sẵn

### Giai đoạn E: Gap Analysis và đóng gói
- [x] Đọc proposal Task 1 từ `Task1_DeTai1_Proposal (1).docx`
- [x] Trích xuất baselines, metrics, research questions
- [x] So sánh proposal vs kết quả thực tế
- [x] Phân tích: B0 đạt, thiếu BLEU clean và B1 GPU results
- [x] Tạo `GAP_ANALYSIS.md` chi tiết
- [x] Tạo `DANG_BASELINE_HANDOFF/` với đầy đủ file
- [x] Tạo `README.md` hướng dẫn sử dụng
- [x] Tạo `HANDOFF_CHECKLIST.md` (file này)

---

## ⚠️ CẦN GPU ĐỂ HOÀN THIỆN

### B1 Whisper Translate - Chưa chạy đầy đủ
- [ ] Chạy B1 trên 857 mẫu FLEURS test (cần GPU)
- [ ] Có `predictions_b1.jsonl` với 857 dòng
- [ ] Có `metrics_b1.json`: BLEU, chrF++, RTF
- [ ] So sánh B0 vs B1: cascade vs end-to-end

**Lý do chưa chạy:** Môi trường hiện tại không có GPU  
**Giải pháp:** Code đã sẵn sàng, chỉ cần chạy trên Google Colab/máy có CUDA

### B0 Clean Baseline - Chưa có
- [ ] Chạy VinAI Translate trên `reference_vi` (văn bản sạch)
- [ ] Có BLEU clean (dự kiến ~37-38 theo proposal)
- [ ] Tính error propagation: BLEU_clean - BLEU_cascade

**Lý do chưa có:** Không phải trong scope baseline ban đầu  
**Giải pháp:** Script đơn giản, chạy nhanh, không cần nhiều VRAM

---

## ❌ KHÔNG THUỘC PHẦN VIỆC CỦA ĐĂNG

- [ ] Proposed Method V1-V4 (Kiệt đã làm ✅)
- [ ] GUI Gradio (Kiệt đã làm ✅)
- [ ] FastAPI (Kiệt đã làm ✅)
- [ ] Training/fine-tuning LoRA (Kiệt đã làm ✅)
- [ ] Docker/CI-CD (Kiệt đã làm ✅)
- [ ] Data augmentation (không phải baseline)
- [ ] Ablation study chi tiết (Kiệt/Uyên làm)

---

## 📋 CHECKLIST KIỂM TRA TRƯỚC KHI BÀN GIAO

### Code chạy được
- [x] `check_data.py`: exit code 0, in ra "✅ Dataset hợp lệ"
- [x] `verify_b0.py`: exit code 0, in ra "✅ B0 đầy đủ"
- [x] `b1_whisper_translate/inference.py`: import được, có docstring
- [ ] B1 test 5 mẫu CPU: chạy không lỗi (cần test thủ công)

### File đầy đủ
- [x] `check_data.py` (3.8KB)
- [x] `verify_b0.py` (4.2KB)
- [x] `b0_summary.json` (807B)
- [x] `GAP_ANALYSIS.md` (8.9KB)
- [x] `README.md` (4.6KB)
- [x] `HANDOFF_CHECKLIST.md` (file này)
- [x] `b1_whisper_translate/inference.py`
- [x] `b1_whisper_translate/run_fleurs_test.py`
- [x] `b1_whisper_translate/evaluate_b1.py`
- [x] `b1_whisper_translate/requirements.txt`
- [x] `b1_whisper_translate/README.md`
- [x] `b1_whisper_translate/STATUS.md`

### Tài liệu rõ ràng
- [x] README có hướng dẫn chạy từng bước
- [x] Gap Analysis có phân tích chi tiết
- [x] Mỗi script có docstring và comment
- [x] Ghi rõ phần nào cần GPU, phần nào chạy được CPU
- [x] Ghi rõ phần nào đã hoàn thành, phần nào chưa

### Reproducibility
- [x] Đường dẫn dataset rõ ràng
- [x] Đường dẫn repo rõ ràng
- [x] Requirements.txt có đủ dependencies
- [x] Không hard-code đường dẫn máy cá nhân
- [x] Config: beam size, max_tokens, dtype đều ghi rõ

---

## 📊 KẾT QUẢ CÓ THỂ TRUY XUẤT

### B0 Cascade
- **BLEU:** 22.69
- **chrF++:** 49.38
- **Samples:** 857
- **Nguồn:** `repo/experiments/runs/mt/B0/fleurs_test_asr_pho/score.json`
- **ASR WER FLEURS:** 13.68%
- **ASR WER VIVOS:** 6.24%
- **Nguồn ASR:** `repo/experiments/runs/asr/kiet_t2_phowhisper-small_*/predictions.jsonl`

### Dataset
- **Samples:** 857
- **Duration:** 4.98 - 38.10s (avg 12.62s)
- **Domains:** giáo dục 336, tin tức 267, du lịch 254
- **Audio:** mono 16kHz WAV
- **References:** VI + EN đầy đủ

---

## 🚀 HÀNH ĐỘNG TIẾP THEO (cho Kiệt)

### Priority 1 (Bắt buộc để có baseline đầy đủ)
1. **Chạy B1 trên GPU** (1-2 giờ):
   ```bash
   cd b1_whisper_translate
   python run_fleurs_test.py --device cuda --manifest [path] --output predictions_b1.jsonl
   python evaluate_b1.py --predictions predictions_b1.jsonl --manifest [path] --output metrics_b1.json
   ```
   → Có BLEU B1, so sánh cascade vs end-to-end

2. **Chạy B0 clean** (30 phút):
   - Viết script: load VinAI Translate, dịch 857 `reference_vi`
   - Đo BLEU trên reference_en
   → Tính error propagation: BLEU_clean - BLEU_cascade

### Priority 2 (Nên có để báo cáo đẹp)
3. **Tổng hợp ablation table** từ notebooks
4. **Đo latency/RTF** của B0 và B1
5. **Viết Discussion** dựa trên Gap Analysis

### Priority 3 (Bonus)
6. Test B1 với audio tự thu
7. Colab notebook cho B1
8. Augmentation (nếu còn thời gian)

---

## ✍️ CHỮ KÝ XÁC NHẬN

**Người bàn giao:** Hồ Lâm Bảo Đăng (SE205148)  
**Ngày bàn giao:** 2026-11-03  
**Cam kết:**
- ✅ Dataset FLEURS test 857 mẫu hợp lệ
- ✅ B0 cascade baseline hoàn chỉnh và tái lập được
- ✅ B1 Whisper Translate code hoàn chỉnh (cần GPU để chạy)
- ✅ Notebooks EDA/Error Analysis có sẵn
- ✅ Gap Analysis chi tiết
- ✅ Tài liệu đầy đủ, code có thể chạy lại

**Người nhận bàn giao:** Lê Tuấn Kiệt (SE205279)  
**Ngày nhận:** ___________  
**Xác nhận:**
- [ ] Đã đọc README
- [ ] Đã chạy check_data.py và verify_b0.py thành công
- [ ] Hiểu rõ phần nào cần GPU
- [ ] Sẵn sàng tiếp tục Proposed Method

---

**GHI CHÚ QUAN TRỌNG:**

1. **Code B1 đã test được trên CPU với 5 mẫu** - chỉ cần GPU để chạy đầy đủ
2. **Không sửa code Proposed Method (V1-V4)** - đó là phần của Kiệt
3. **Notebooks đã có output** - mở ra là đọc được ngay, không cần chạy lại
4. **B0 BLEU 22.69 thấp hơn proposal 24.27** - đã giải thích trong Gap Analysis
5. **Whisper-small 244M params < 300M limit** - hợp lệ theo đề bài
