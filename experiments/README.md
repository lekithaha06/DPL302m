# Thực nghiệm: dữ liệu → ASR baseline → LoRA V1–V4 → đánh giá

Toàn bộ code, cấu hình, dự đoán và bảng số Kiệt đã chạy ngày 30–31/10/2026 trên RTX 4060 Laptop 8 GB. Mọi số trong báo cáo truy được về một file ở đây.

## Chạy lại

```bash
pip install -r experiments/env/requirements.txt     # torch 2.0.1+cu117, transformers 4.44.2, peft 0.12.0
export P=python                                       # Windows venv: export P=.venv/Scripts/python.exe
bash experiments/chay_lai.sh cham      # không cần GPU: chấm lại từ dự đoán có sẵn, ra đúng số báo cáo
bash experiments/chay_lai.sh nho       # cần GPU: chạy cả pipeline trên 20 câu, 1 epoch (chỉ để kiểm lệnh chạy được)
bash experiments/chay_lai.sh day_du    # cần GPU: tải dữ liệu, train V1–V4, đánh giá, bootstrap, đo tốc độ
```

Chế độ `cham` đã chạy thử ngày 03/11: WER/CER PhoWhisper VIVOS 6,24/3,25, FLEURS 13,68/9,88; Whisper 25,99/16,49 và 21,24/12,26, khớp `reports/asr/results_task2.csv`.

Trên Windows, chạy bằng Git Bash. PhoMT và FLoRes+ là dataset gated: `huggingface-cli login` và xin quyền trước khi chạy `day_du`.

## Tái lập được nhờ gì

| Thứ | Ở đâu |
|---|---|
| Revision model | `env/env.sh`: PhoWhisper `a86b604`, Whisper `973afd2`, VinAI Translate `ae7baa8` |
| Revision dữ liệu | `env/env.sh`: FLEURS `70bb2e8`, VIVOS `3cbfb25` |
| Thư viện | `env/requirements.txt` (bản khoá), `env/pip_freeze.txt` (bản thật trên máy chạy), `env/moi_truong.json` (GPU, CUDA) |
| Seed | 42 cho mọi lần train và bootstrap |
| Protocol ASR | `configs/asr_protocol.json`, `configs/common_suppression_from_task1.json` |
| Siêu tham số LoRA | `configs/mt/V1.json` … `V4.json`; lệnh thật trong `scripts/hang_doi/` |
| Danh sách mẫu | `runs/manifests/*.jsonl` + `manifests_sha256.json` (857 bản FLEURS test, 361 dev, 2.926 train, 760 VIVOS test) |
| Đầu vào khối dịch | `runs/mt_data/*.jsonl` (sạch, lời ASR, bản cân bằng) |
| Dự đoán | `runs/asr/*/predictions.jsonl`, `runs/mt/*/*/hyp.jsonl` |
| Điểm | `runs/mt/*/*/score.json` (kèm signature sacreBLEU, sha256 đầu vào, adapter) |
| Đường cong huấn luyện | `checkpoints/V*/epochs.json`, `train_log.jsonl`, `curves.png` |
| Adapter | V1–V4 và ablation, đủ 3 seed: `../checkpoints/*/best` (có SHA256) |

## Thứ tự các bước

| Bước | Script | Người viết |
|---|---|---|
| Tải 3 bộ dữ liệu, kiểm chứng số mẫu | `scripts/data/viec1_tai_3_bo_du_lieu.py` | Uyên |
| Ghép, chia FLEURS chống rò rỉ theo câu | `scripts/data/viec2_ghep_chia_fleurs_chong_trung.py` | Uyên |
| Làm sạch (B1–B6) | `scripts/data/viec2_lam_sach_du_lieu.py` | Uyên |
| EDA, cân bằng | `scripts/data/viec3_eda.py`, `viec4_can_bang_du_lieu.py` | Uyên |
| Nhãn miền FLoRes+ | `scripts/data/gan_mien_flores.py` | Kiệt |
| Manifest + ASR baseline | `scripts/asr/make_asr_manifest.py`, `run_asr.py` | Bảo (protocol), Kiệt |
| Chấm WER/CER | `scripts/asr/score_asr.py` (test: `test_score_asr.py`) | Bảo |
| Dữ liệu dịch, train LoRA, dịch | `scripts/mt/make_mt_data.py`, `make_balanced_data.py`, `train_lora.py`, `translate.py` | Kiệt |
| Bootstrap, phân tích lỗi, tốc độ | `scripts/mt/bootstrap.py`, `failure_analysis.py`, `do_toc_do.py` | Kiệt |
| Theo miền, tổng hợp, biểu đồ | `scripts/cham_theo_mien.py`, `asr/tong_hop_asr.py`, `ve_bieu_do.py` | Kiệt |

## Không có ở đây

- `data/` (~12 GB) và trọng số gốc (~4 GB): bước 0–4 của `chay_lai.sh day_du` tải lại đúng revision.
- Văn bản PhoMT: giấy phép không cho phân phối lại, nên chỉ giữ `runs/mt/*/phomt_test/score.json`. `phomt_train_mix.jsonl` được tạo lại từ PhoMT gốc bằng `make_balanced_data.py` và `reports/data/can_bang/can_bang_v2_phomt_idx.txt`.
- Audio của manifest: đường dẫn trong `runs/manifests/*.jsonl` là máy Kiệt (`D:\CAIDCM\...`). Bước 4 của `chay_lai.sh` tạo lại manifest với đường dẫn trên máy bạn.
- Script sinh tài liệu (`tao_bao_cao.py`, `tao_slide.py`, ...) không phải thực nghiệm, vẫn ở gói `task3.zip`.

`scripts/hang_doi/*.sh` là bản lưu đúng lệnh đã chạy, có vòng chờ log của bước trước. Muốn chạy lại thì dùng `chay_lai.sh`.

## Chạy lại 3 seed và đo độ bền

Seed 42 chạy theo `chay_lai.sh`. Seed 1 và 2 của V1–V4, ablation chạy bằng `scripts/modal_3seed.py` (cần `pip install modal` và tài khoản Modal; đưa file trong `runs/mt_data/` lên Volume `dpl302m-3seed`, riêng `phomt_train_mix.jsonl` phải tự tạo lại vì không phân phối). Train trên RTX PRO 6000 với torch 2.7.1, dịch và chấm trên T4 với torch 2.0.1. Tổng hợp: `scripts/tong_hop_3seed.py`, kết quả ở `reports/ba_seed/` và `runs/ba_seed/mt/`.

Đo độ bền khối nghe: `bash scripts/hang_doi_robust.sh` (cần GPU và `data/`), kết quả ở `reports/robust/`, `runs/robust/`.

Toàn bộ log của các lần chạy thật ở `logs/`.
