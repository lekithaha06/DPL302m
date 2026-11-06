# Giai đoạn C: B1 Whisper Translate - Hoàn thành

## Đã tạo

1. ✅ `inference.py` - Core inference với WhisperTranslator class
2. ✅ `run_fleurs_test.py` - Script chạy batch trên 857 mẫu
3. ✅ `evaluate_b1.py` - Đánh giá BLEU/chrF++ và so sánh B0
4. ✅ `requirements.txt` - Dependencies

## Lệnh chạy

### Test với 5 mẫu đầu tiên (CPU, kiểm tra code)

```bash
cd dang_baseline/b1_whisper_translate
pip install -r requirements.txt

python run_fleurs_test.py \
    --manifest /tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl \
    --output test_predictions_b1.jsonl \
    --device cpu \
    --dtype float32 \
    --limit 5

python evaluate_b1.py \
    --predictions test_predictions_b1.jsonl \
    --manifest /tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl \
    --output test_metrics_b1.json \
    --b0_score ../b0_summary.json
```

### Chạy đầy đủ 857 mẫu (GPU cần thiết)

```bash
python run_fleurs_test.py \
    --manifest /tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl \
    --output predictions_b1.jsonl \
    --device cuda \
    --dtype float16

python evaluate_b1.py \
    --predictions predictions_b1.jsonl \
    --manifest /tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl \
    --output metrics_b1.json \
    --b0_score ../../repo/experiments/runs/mt/B0/fleurs_test_asr_pho/score.json
```

## Lưu ý

- **Model size:** Whisper-small có 244M params, **NHỎ HƠN** giới hạn 300M của đề bài
- **Task:** `translate` (không phải `transcribe`)
- **Language:** `vi` (Vietnamese input)
- **Không có transcript tiếng Việt:** B1 dịch trực tiếp từ audio, khác với B0 cascade
- **RTF:** Real-Time Factor = latency / audio_duration. RTF < 1 là faster-than-realtime

## Môi trường hiện tại

Không có GPU, nên:
- Code đã sẵn sàng
- Có thể test 5-10 mẫu trên CPU
- Chạy đầy đủ 857 mẫu cần GPU (Google Colab hoặc máy có CUDA)

## Colab notebook

Sẽ tạo ở bước tiếp theo để dễ chạy trên GPU free.
