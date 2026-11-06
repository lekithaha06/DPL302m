# DANG_BASELINE_HANDOFF

Bàn giao hoàn chỉnh phần việc của **Hồ Lâm Bảo Đăng (SE205148)** - TV3  
Vai trò: Hệ thống, điều phối, **Baseline và Dataset** (hoàn thành 100% trước khi Kiệt làm Proposed Method)

## Nội dung bàn giao

### 1. Dataset (✅ Hoàn thành)
- `check_data.py` - Kiểm tra FLEURS test (857 mẫu)
- Kết quả: ✅ 857/857 mẫu hợp lệ, không trùng, khớp với repo manifest

### 2. B0 - Cascade Baseline (✅ Hoàn thành)
- `verify_b0.py` - Kiểm chứng B0 (PhoWhisper → VinAI pretrained)
- `b0_summary.json` - Tổng hợp cấu hình và kết quả B0
- Kết quả: BLEU 22.69, chrF++ 49.38 (857 mẫu FLEURS test)

### 3. B1 - Whisper Translate (✅ Code hoàn thành, ⚠️ chưa chạy GPU)
- `b1_whisper_translate/` - Baseline bổ sung (end-to-end translation)
  - `inference.py` - Core translation class
  - `run_fleurs_test.py` - Batch inference 857 mẫu
  - `evaluate_b1.py` - Đánh giá BLEU/chrF++, so sánh B0
  - `requirements.txt` - Dependencies
  - `README.md` và `STATUS.md` - Hướng dẫn

**Trạng thái:** Code sẵn sàng, test được trên CPU (5 mẫu), cần GPU để chạy đầy đủ 857 mẫu

### 4. Notebooks (✅ Đã có sẵn trong repo)
- `../../repo/notebooks/eda.ipynb` - EDA đầy đủ với output
- `../../repo/notebooks/phan_tich_loi.ipynb` - Error analysis với output
- Cả hai notebook chạy được, có hình và kết quả

### 5. Gap Analysis (✅ Hoàn thành)
- `GAP_ANALYSIS.md` - So sánh proposal Task 1 với kết quả thực tế
- Phân tích: B0 đạt được, thiếu BLEU clean và B1 GPU results

## Cấu trúc thư mục

```
DANG_BASELINE_HANDOFF/
├── README.md                    (file này)
├── check_data.py                Kiểm tra dataset FLEURS
├── verify_b0.py                 Kiểm chứng B0 cascade
├── b0_summary.json              Tổng hợp B0
├── GAP_ANALYSIS.md              So sánh proposal vs thực tế
├── b1_whisper_translate/        Baseline B1 (code hoàn chỉnh)
│   ├── README.md
│   ├── STATUS.md
│   ├── inference.py
│   ├── run_fleurs_test.py
│   ├── evaluate_b1.py
│   └── requirements.txt
└── HANDOFF_CHECKLIST.md         Danh sách kiểm tra bàn giao
```

## Yêu cầu môi trường

### Dataset
- FLEURS test 857 mẫu: `/tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/`
- Repo V2: `../repo/`

### Phần mềm
- Python 3.11
- PyTorch 2.0+ (CPU để test, GPU để chạy đầy đủ)
- transformers, torchaudio, sacrebleu (xem requirements.txt)

## Cách sử dụng

### Kiểm tra dataset
```bash
python check_data.py
```

### Kiểm chứng B0
```bash
python verify_b0.py
```

### Test B1 (CPU, 5 mẫu)
```bash
cd b1_whisper_translate
pip install -r requirements.txt
python run_fleurs_test.py \
    --manifest /tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl \
    --output test_predictions_b1.jsonl \
    --device cpu --dtype float32 --limit 5
```

### Chạy đầy đủ B1 (GPU)
```bash
cd b1_whisper_translate
python run_fleurs_test.py \
    --manifest /tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl \
    --output predictions_b1.jsonl \
    --device cuda --dtype float16

python evaluate_b1.py \
    --predictions predictions_b1.jsonl \
    --manifest /tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl \
    --output metrics_b1.json \
    --b0_score ../../repo/experiments/runs/mt/B0/fleurs_test_asr_pho/score.json
```

## Kết quả đạt được

### ✅ Hoàn thành 100%
1. Dataset FLEURS test 857 mẫu hợp lệ
2. B0 (cascade) kiểm chứng: BLEU 22.69, chrF++ 49.38
3. Code B1 (Whisper Translate) hoàn chỉnh
4. Notebooks EDA và Error Analysis có sẵn
5. Gap Analysis chi tiết

### ⚠️ Cần GPU để hoàn thiện
1. Chạy B1 trên 857 mẫu → BLEU B1
2. So sánh B0 vs B1 → kết luận cascade vs end-to-end
3. Chạy B0 clean (VinAI trên reference_vi) → tính error propagation

### ❌ Không làm (không phải phần của Đăng)
- Proposed Method V1-V4 (Kiệt đã làm)
- GUI/FastAPI (Kiệt đã làm)
- Training/fine-tuning (không phải baseline)

## Bàn giao cho Kiệt

Kiệt có thể:
1. ✅ Sử dụng B0 làm baseline so sánh với V1-V4
2. ✅ Chạy B1 trên GPU để có baseline end-to-end
3. ✅ Dùng notebooks EDA/Error Analysis cho báo cáo
4. ✅ Tham khảo Gap Analysis để viết Discussion

## Liên hệ

- Người bàn giao: Hồ Lâm Bảo Đăng (SE205148)
- Vai trò: TV3 - Hệ thống và điều phối
- Ngày bàn giao: 2026-11-03
