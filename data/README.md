# Dữ liệu

Repo **không chứa dữ liệu**. Mọi bộ dữ liệu được tải mới từ nguồn gốc bằng script dưới đây.

| Bộ | Vai trò ở Task 1 | Quy mô đã dùng | License | Nguồn |
|---|---|---|---|---|
| VIVOS | Đo khối nghe (Baseline A) | Test 760 câu, 19 người nói (bản chính thức) | CC BY-NC-SA 4.0 | [AILAB-VNUHCM/vivos](https://huggingface.co/datasets/AILAB-VNUHCM/vivos) |
| FLEURS vi_vn + en_us | Đo cả hệ thống (âm thanh Việt → câu Anh) | Test 857 bản thu, 347 câu gốc, 3,0 giờ | CC BY 4.0 | [google/fleurs](https://huggingface.co/datasets/google/fleurs) |
| PhoMT | Đo khối dịch (Baseline B) | 2.977.999 / 18.719 / 19.151 cặp (train/dev/test) | Chỉ nghiên cứu, **cấm phân phối lại** | [vinai/PhoMT](https://huggingface.co/datasets/vinai/PhoMT) (gated) |

## Cách tải

**VIVOS test** (TV1): tải đúng revision đã dùng, tạo `data/vivos_test/manifest.jsonl`.

```
python data/prepare_vivos.py
```

**FLEURS test** (TV2): tải từ trang Hugging Face các file `data/vi_vn/test.tsv`, `data/en_us/test.tsv`,
`data/vi_vn/audio/test.tar.gz` vào `data/fleurs/`, giải nén âm thanh vào `data/fleurs_audio_test/`, rồi ghép câu Việt và câu Anh theo ID FLoRes:

```
python data/build_fleurs_eval.py
```

**PhoMT**: đăng nhập Hugging Face, đồng ý điều khoản, tải `PhoMT.zip` và giải nén sao cho có `data/phomt/PhoMT/detokenization/`.

**FLEURS train/dev/test (Task 2)**: tải cả ba tập (âm thanh vi_vn, chữ vi_vn và en_us) rồi ghép theo ID câu:

```
python data/download_fleurs.py --splits train,dev,test
python data/build_fleurs_eval.py --split train --audio-dir data/fleurs_audio/train --output data/processed/fleurs_vi_en_train.json
```

## Sơ đồ thư mục dữ liệu trên máy chạy (không commit; Task 2 chạy trên RTX 4060)

| Thư mục | Nội dung | Tạo bởi |
|---|---|---|
| `data/fleurs/` | TSV vi_vn, en_us và file nén âm thanh gốc (train/dev/test) | `download_fleurs.py` |
| `data/fleurs_audio/{train,dev,test}/` | WAV 16 kHz đã giải nén: 2.994 / 361 / 857 file | `download_fleurs.py` |
| `data/vivos_test/` | 760 WAV VIVOS test + `manifest.jsonl` | `prepare_vivos.py` |
| `data/phomt/PhoMT/` | PhoMT (`detokenization/`, `tokenization/`) | tải tay (gated) |
| `data/processed/` | Cặp Việt–Anh FLEURS theo ID câu; danh sách mẫu sau làm sạch | `build_fleurs_eval.py`, `src/data/clean_eda.py` |
| `data/asr/` | Chữ PhoWhisper nghe FLEURS train/dev (dữ liệu dạy V1) | `src/asr/transcribe_fleurs.py` |
| `data/mt/` | 1.449 cặp chữ chuẩn FLEURS train, 3.000 cặp PhoMT train (V2) | `src/mt/build_mix_data.py` |
| `data/phomt_hyp/` | Bản dịch của từng phiên bản trên PhoMT test (không chia sẻ: license) | `src/mt/eval_mt.py` |
| `checkpoints/pretrained/` | PhoWhisper-small, VinAI Translate vi2en (đúng revision) | `src/mt/download_models.py` |
| `checkpoints/v1/`, `checkpoints/v2/` | Adapter LoRA V1, V2 (`best_adapter/`), log và trạng thái train | `src/mt/train_lora.py` |
| `.work/source_models/` | PhoWhisper-small, Whisper-small cho Baseline A | `src/asr/download_checkpoints.py` |

Mã hash SHA-256 của dữ liệu đã xử lý và checkpoint: `reports/task2/evidence/manifest.json`. Log tải dữ liệu: `reports/task2/logs/download/`.

## Quy tắc

- Giữ nguyên cách chia train/dev/test gốc của từng bộ. VIVOS chia theo người nói. Một câu FLEURS có nhiều bản thu, nên khi dùng train/dev phải chia theo ID câu.
- Tập test chỉ dùng để chấm, không dùng để huấn luyện hay chọn siêu tham số.
- **Không commit** dữ liệu PhoMT, bản dịch trên tập test PhoMT, hay câu trích từ PhoMT. `scripts/tv4_reports.ps1` in ra một cặp câu giống nhất. Bản trong `reports/task1/data/` đã bỏ câu đó, chỉ giữ số dòng.

## Kiểm tra leakage (Task 1)

`reports/task1/data/leakcheck_fleurs_phomt.json` (TV4): so 347 câu FLEURS test với toàn bộ PhoMT.
Kết quả: **0 câu trùng tuyệt đối**. Ở mức cụm 8 âm tiết, Jaccard cao nhất chỉ 0,045, tức chỉ trùng cụm từ thông dụng.
