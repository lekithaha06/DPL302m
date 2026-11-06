# Gap Analysis: So sánh Proposal Task 1 với Kết quả Thực tế

## 1. Tổng quan Proposal Task 1

### Đề tài
Hệ thống nhận dạng giọng nói tiếng Việt và dịch sang tiếng Anh, kiến trúc cascade ASR → MT, đánh giá lỗi lan truyền và độ trễ.

### Baselines trong Proposal

**Baseline A (ASR):** PhoWhisper-small
- Dataset: VIVOS test (760 bản thu)
- Kết quả tham khảo từ paper: WER 6,33%
- Hardware: RTX 3050 Laptop 4GB

**Baseline B (MT):** VinAI Translate vi2en pretrained
- Dataset: PhoMT test (19.151 câu)
- Kết quả tham khảo từ paper: BLEU 40,42 (mBART)
- Hardware: RTX 4060 Laptop 8GB

**Cascade:** PhoWhisper-small → VinAI Translate
- Dataset: FLEURS vi_vn test (857 bản thu / 347 câu gốc)
- Kết quả dự kiến trong proposal:
  - Văn bản sạch: BLEU 37,89, chrF++ 61,18
  - Cascade (ASR output): BLEU 24,27, chrF++ 50,12
  - **Mất 13,62 BLEU do lỗi ASR** (35,9% tương đối)

### Research Questions

1. **RQ1:** Thay Whisper-small → PhoWhisper-small, WER/CER thay đổi bao nhiêu và ảnh hưởng đến BLEU cascade?
2. **RQ2:** VAD, chia đoạn có ngữ cảnh, chuẩn hóa dấu câu cải thiện balance giữa quality và latency?
3. **RQ3:** Fine-tune MT với dữ liệu mô phỏng lỗi ASR có thu hẹp mất BLEU mà không giảm chất lượng trên văn bản sạch?

## 2. Kết quả Thực tế của Nhóm (B0 - Baseline Cascade)

### Từ file kiểm chứng (`b0_summary.json`)

**Kiến trúc:**
```
Audio VI → PhoWhisper-small → Text VI → VinAI Translate (pretrained) → Text EN
```

**Cấu hình:**
- ASR model: `vinai/PhoWhisper-small`
- MT model: `vinai/vinai-translate-vi2en-v2`
- MT revision: `ae7baa85da07dbe8e23ac26a9f5ef560c17e2138`
- MT dtype: `float16`
- Decode: `num_beams=5, max_new_tokens=256, early_stopping=True`
- Adapter: `None` (B0 = pretrained, không có LoRA)

**Kết quả trên FLEURS test (857 mẫu):**
- **BLEU: 22.69**
- **chrF++: 49.38**
- Samples: 857

### Từ repo experiments

**ASR (PhoWhisper-small) trên FLEURS test:**
- WER: 13.68%
- CER: 9.88%
- Run fingerprint: `0f61cac456e885df9ba785757bf8c5ace9925a3663c46c81cd31526230ee2233`

**ASR (PhoWhisper-small) trên VIVOS test:**
- WER: 6.24%
- CER: 3.25%
- Samples: 760

## 3. Gap Analysis Chi tiết

### 3.1. ASR Performance

| Dataset | Metric | Proposal (paper) | Thực tế (nhóm) | Δ |
|---------|--------|------------------|----------------|---|
| VIVOS test | WER | 6.33% | **6.24%** | **-0.09%** ✅ |
| VIVOS test | CER | — | 3.25% | — |
| FLEURS test | WER | — | 13.68% | — |
| FLEURS test | CER | — | 9.88% | — |

**Phân tích:**
- ✅ **VIVOS WER nhóm thấp hơn paper** (6.24% vs 6.33%), chứng minh tái lập tốt
- ⚠️ **FLEURS WER cao hơn VIVOS** (13.68% vs 6.24%):
  - FLEURS có audio dài hơn (avg 12.62s vs VIVOS ~3.5s)
  - FLEURS có 7 bản thu > 30s gây lỗi lặp từ (WER > 100% trên mẫu dài)
  - FLEURS có tên riêng, số, thuật ngữ khó hơn

### 3.2. Cascade Performance

| Metric | Proposal (dự kiến) | Thực tế (B0) | Δ |
|--------|-------------------|--------------|---|
| BLEU cascade | 24.27 | **22.69** | **-1.58** ⚠️ |
| chrF++ cascade | 50.12 | **49.38** | **-0.74** ⚠️ |
| BLEU văn bản sạch | 37.89 | — | — |
| chrF++ văn bản sạch | 61.18 | — | — |

**Phân tích:**
- ⚠️ **BLEU thực tế thấp hơn proposal 1.58 điểm**
- Nguyên nhân có thể:
  1. **WER FLEURS cao hơn dự kiến** (13.68% vs ~6-7% ước tính)
  2. **Không có số văn bản sạch để đối chiếu**
  3. Proposal dùng số "dự kiến", không phải kết quả chạy thật
  4. Có thể khác biệt về preprocessing/decoding config

### 3.3. Error Propagation

| Metric | Proposal | Thực tế | Cách tính |
|--------|----------|---------|-----------|
| Mất BLEU do lỗi ASR | 13.62 (35.9% tương đối) | **Chưa có số văn bản sạch** | clean_BLEU - cascade_BLEU |

**Vấn đề:**
- ❌ **Không tính được mất bao nhiêu BLEU do lỗi ASR** vì thiếu baseline văn bản sạch
- Cần: chạy VinAI Translate trên `reference_vi` (văn bản chuẩn) để có BLEU sạch
- Chỉ khi đó mới so sánh: BLEU_sạch - BLEU_cascade = mất bao nhiêu

### 3.4. Proposed Method (V1-V4 LoRA)

**Trong repo có:**
- V1, V2, V3, V4: các adapter LoRA của VinAI Translate
- V4 được chọn làm bản cuối: BLEU 26.33 (dev), 38.11 (clean test)
- V4 cải thiện so với B0: +3.64 BLEU trên dev

**Gap:**
- ✅ RQ3 đã được trả lời một phần: LoRA V4 có cải thiện
- ⚠️ Chưa rõ V4 có "không làm giảm chất lượng trên văn bản sạch" hay không
- Cần: BLEU của B0 và V4 trên cùng reference sạch để so sánh

### 3.5. B1 (Whisper Translate) - Baseline Bổ sung

**Trong Proposal:**
- Không đề cập Whisper Translate làm baseline chính
- Chỉ nói "Whisper task translate sẽ được chạy làm đối chứng"

**Việc của Đăng:**
- ✅ Đã tạo code B1 (Whisper-small multilingual, task=translate)
- ⚠️ **Chưa chạy được do không có GPU**
- B1 là baseline bổ sung, không phải trong proposal gốc

**So sánh B1 vs B0 (dự kiến):**
- B0: 2 bước (ASR → MT) → có transcript VI
- B1: 1 bước (Audio → EN trực tiếp) → không có transcript VI
- B1 dùng Whisper-small (244M params) < 300M limit
- Nếu B1 BLEU cao hơn B0 → end-to-end tốt hơn cascade
- Nếu B1 BLEU thấp hơn B0 → cascade có lợi thế

## 4. Thiếu gì để hoàn thiện Gap Analysis

### 4.1. PHẢI CÓ (Priority 1)

1. **BLEU văn bản sạch** (B0 clean):
   - Chạy VinAI Translate trên `reference_vi` của FLEURS test
   - So sánh với 22.69 để tính mất bao nhiêu do ASR
   - Script: `dang_baseline/compute_b0_clean.py`

2. **Kết quả B1** (Whisper Translate):
   - Chạy 857 mẫu trên GPU
   - So sánh BLEU B1 vs B0
   - Trả lời: cascade hay end-to-end tốt hơn?

3. **BLEU V4 trên văn bản sạch:**
   - V4 vs B0 trên cùng reference sạch
   - Kiểm tra V4 có làm giảm chất lượng dịch sạch không

### 4.2. NÊN CÓ (Priority 2)

4. **Ablation VAD/segmentation:**
   - Đã có trong repo (audio dài, chia đoạn)
   - Cần tổng hợp thành bảng ablation rõ ràng

5. **Latency và RTF:**
   - Proposal nhắc "độ trễ" nhưng chưa có số cụ thể
   - B0 và B1 đều cần đo RTF

6. **Error analysis theo nhóm lỗi:**
   - Đã có trong `phan_tich_loi.ipynb`
   - Cần trích xuất thành bảng tóm tắt

## 5. Kết luận Gap Analysis

### 5.1. Những gì ĐÃ ĐẠT so với Proposal

✅ **ASR Baseline (B0):**
- VIVOS WER 6.24% khớp với paper (6.33%)
- Tái lập được checkpoint và config

✅ **Cascade Baseline (B0):**
- Có kết quả BLEU 22.69 trên FLEURS test
- Có đủ file predictions để phân tích

✅ **Proposed Method (V1-V4):**
- Đã có LoRA adapter và kết quả
- V4 cải thiện so với B0

✅ **Dataset:**
- FLEURS test 857 mẫu đầy đủ và hợp lệ
- Có reference VI và EN

### 5.2. Những gì CHƯA ĐẠT / CẦN BỔ SUNG

❌ **BLEU văn bản sạch:**
- Không tính được "mất 13.62 BLEU do lỗi ASR"
- Cần chạy B0 clean baseline

⚠️ **B1 Whisper Translate:**
- Code đã có, chưa chạy do không có GPU
- Không so sánh được cascade vs end-to-end

⚠️ **Ablation rõ ràng:**
- Có data nhưng chưa tổng hợp thành bảng ablation đầy đủ

⚠️ **Latency/RTF:**
- Proposal nhắc nhưng chưa có số đo đầy đủ

### 5.3. Giải thích Chênh lệch

**Tại sao BLEU B0 thấp hơn proposal 1.58 điểm?**

1. **WER FLEURS cao hơn VIVOS** (13.68% vs 6.24%):
   - Audio dài, lỗi lặp từ, tên riêng, số
   - Proposal có thể ước tính WER thấp hơn thực tế

2. **Không rõ proposal chạy thật hay ước tính:**
   - Proposal ghi "dự kiến": 24.27, 50.12
   - B0 thực tế: 22.69, 49.38
   - Có thể proposal dựa trên ước tính lý thuyết

3. **Khác biệt config:**
   - Proposal không ghi rõ beam size, max_tokens
   - B0 dùng beam=5, max_tokens=256

### 5.4. Đánh giá Tổng thể

**Baseline (B0) CASCADE đã hoàn thành và tái lập được.**

**Điểm mạnh:**
- Code rõ ràng, có checkpoint SHA256
- Kết quả truy xuất được nguồn
- ASR VIVOS khớp với paper

**Điểm yếu:**
- Thiếu BLEU clean để tính error propagation
- B1 chưa chạy được
- BLEU thấp hơn proposal (cần giải thích rõ hơn)

**Khuyến nghị:**
1. Chạy B0 clean ngay (ưu tiên 1)
2. Chạy B1 trên GPU (ưu tiên 1)
3. Tổng hợp ablation table (ưu tiên 2)
4. Ghi rõ trong báo cáo: "BLEU proposal là ước tính, BLEU thực tế thấp hơn do WER FLEURS cao hơn dự kiến"

---

**Ngày tạo:** 2026-11-03
**Người phân tích:** Hồ Lâm Bảo Đăng (SE205148)
**Vai trò:** TV3 - Hệ thống và điều phối, Baseline và Dataset
