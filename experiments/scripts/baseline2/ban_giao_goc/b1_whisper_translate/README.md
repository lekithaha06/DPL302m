# B1: Whisper Translate (Speech-to-Speech Translation)

## Kiến trúc

```
Vietnamese Audio → Whisper-small (multilingual) → English Text
```

**Khác với B0:**
- B0: Audio → ASR (tiếng Việt) → MT (Việt→Anh)
- B1: Audio → Direct Translation (Việt→Anh, không qua transcript tiếng Việt)

## Model

- **openai/whisper-small** (multilingual)
- Task: `translate` (không phải `transcribe`)
- Language: `vi` (Vietnamese)

## Yêu cầu

```bash
pip install transformers torch torchaudio accelerate
```

## Cấu trúc

```
b1_whisper_translate/
├── inference.py          # Chạy inference 1 file hoặc batch
├── run_fleurs_test.py    # Chạy toàn bộ 857 mẫu FLEURS test
├── evaluate_b1.py        # Đánh giá BLEU/chrF++
├── requirements.txt
└── README.md
```

## Chạy

### Inference đơn lẻ

```bash
python inference.py --audio path/to/audio.wav --output result.json
```

### Chạy toàn bộ FLEURS test

```bash
python run_fleurs_test.py \
    --manifest /tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl \
    --output predictions_b1.jsonl \
    --device cuda
```

### Đánh giá

```bash
python evaluate_b1.py \
    --predictions predictions_b1.jsonl \
    --manifest /tmp/dang_fleurs/GUI_DANG_FLEURS_TEST/manifest_fleurs_test.jsonl \
    --output metrics_b1.json
```

## Google Colab

Notebook: `b1_whisper_translate_colab.ipynb`

## Kết quả

Sẽ được ghi vào `b1_results/`:
- `predictions_b1.jsonl`: Dự đoán cho từng mẫu
- `metrics_b1.json`: BLEU, chrF++, latency, RTF
- `b1_summary.json`: Tổng hợp cấu hình và kết quả
