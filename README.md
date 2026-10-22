# DPL302m · Đề tài 1: Nhận dạng giọng nói tiếng Việt và dịch sang tiếng Anh

- **Input:** âm thanh tiếng Việt (file hoặc micro)
- **Output:** chữ tiếng Việt và bản dịch tiếng Anh
- **Kiến trúc:** cascade **PhoWhisper-small** (ASR) → **VinAI Translate vi2en** (MT)
- **Vấn đề nhóm nhắm tới:** lỗi nghe của ASR lan sang khối dịch. Trên FLEURS, BLEU giảm từ 37,89 xuống 24,27 khi thay chữ chuẩn bằng chữ do máy nghe ra.
- **Hướng đề xuất (Task 2):** dạy thêm khối dịch bằng LoRA trên cặp (chữ có lỗi nghe → câu Anh đúng), để khối dịch quen với lỗi nghe.

## Thành viên

| TV | Họ tên | MSSV | Vai trò | Phần trong repo |
|---|---|---|---|---|
| 1 | Dương Gia Bảo | SE205262 | ASR, Baseline A | `src/asr/`, `data/prepare_vivos.py`, `scripts/run_asr_baseline.ps1`, `reports/task1/asr/` |
| 2 | Lê Tuấn Kiệt | SE205279 | MT, Baseline B, Proposed Method | `src/mt/`, `data/build_fleurs_eval.py`, `src/eval/`, `reports/task1/mt/` |
| 3 | Hồ Lâm Bảo Đăng | SE205148 | Hệ thống, pipeline, ghép báo cáo | (Task 2: VAD, đo tốc độ, demo) |
| 4 | Bùi Ngọc Phương Uyên | SE205253 | Dữ liệu và đánh giá | `scripts/tv4_reports.ps1`, `reports/task1/data/`, `data/README.md` |

Nhóm 4 người đã được giảng viên cho phép.

## Kết quả Task 1 (chạy lại baseline)

| Mô hình | Nguồn | Dataset | WER | CER | BLEU | chrF++ |
|---|---|---|---|---|---|---|
| PhoWhisper-small (A) | Paper [PhoWhisper, Table 2] | VIVOS test | 6,33 | – | – | – |
| PhoWhisper-small (A) | Nhóm | VIVOS test (760 câu) | **6,25** | 3,26 | – | – |
| Whisper-small (đối chứng zero-shot) | Nhóm | VIVOS test | 25,91 | 16,47 | – | – |
| VinAI Translate vi2en (B) | Paper [Interspeech 2022, Table 1] | PhoMT test | – | – | 40,42 | – |
| VinAI Translate vi2en (B) | Nhóm | PhoMT test (19.151 câu) | – | – | **40,25** | 60,30 |
| B, dịch từ chữ chuẩn | Nhóm | FLEURS test (857 bản thu) | – | – | 37,89 | 61,18 |
| PhoWhisper-small | Nhóm | FLEURS test | 12,21 | 8,58 | – | – |
| **Cascade A → B** | Nhóm | FLEURS test | – | – | **24,27** | 50,12 |

- Lỗi nghe làm BLEU giảm **13,62 điểm** (37,89 → 24,27).
- WER trên FLEURS tách theo loại lỗi: thay thế 2.058, xóa 112, chèn 1.007 trên 26.021 từ tham chiếu.
- PhoWhisper được tác giả fine-tune trên VIVOS train, nên kết quả trên VIVOS là **cùng miền**, không phải zero-shot. FLEURS là tập ngoài miền.
- Whisper-small trên VIVOS: bỏ một câu sinh lặp (`VIVOSDEV03_R193`) thì WER giảm từ 25,91 xuống 22,12.
- WER theo người nói trên VIVOS (PhoWhisper): thấp nhất 0,78% (VIVOSDEV19), cao nhất 24,93% (VIVOSDEV10).
- BLEU và chrF++ tính bằng sacreBLEU 2.6.0 (`tok:13a`). WER/CER chuẩn hóa NFC, viết thường, giữ dấu; CER bỏ khoảng trắng.
- Không dùng `vinai-translate-vi2en-v2` làm baseline: theo README của VinAI, khoảng 10 nghìn cặp train của bản này nằm trong PhoMT test (rủi ro leakage L2). Bản v2 chỉ được chạy tham khảo trên FLEURS, số nằm trong `reports/task1/mt/baseline_cascade.json`.

Mọi số ở trên kèm nguồn trong `reports/task1/so_lieu_chung.json`. Các số dẫn xuất có thể tính lại mà không cần GPU:

```
python src/eval/recompute_metrics.py
```

### Môi trường đã chạy

| Phần | Máy | Thư viện chính |
|---|---|---|
| Baseline A (TV1) | RTX 3050 Laptop 4 GB, CUDA FP16, batch 1, beam 5 | torch 2.0.1+cu117, transformers 4.44.2 (`src/asr/requirements-asr-gpu.txt`) |
| Baseline B và cascade (TV2) | RTX 4060 Laptop 8 GB, FP16, beam 5 | torch 2.6.0+cu124, transformers 5.17.0, sacrebleu 2.6.0 (`requirements.txt`) |

Hai baseline đều là **suy luận zero-shot** từ checkpoint công bố (không train), nên không có learning rate, optimizer hay epoch. Seed cố định 42. Task 2 sẽ chạy lại cả hai trên **cùng một máy**.

## Cấu trúc repo

```
├── WORKFLOW.md                # tiến độ Task 1–3, checklist, người phụ trách
├── configs/base.yaml          # seed, chuẩn hóa văn bản, cấu hình giải mã đã dùng
├── data/                      # chỉ chứa script tải dữ liệu và README (dữ liệu không commit)
├── src/
│   ├── asr/                   # Baseline A: đánh giá PhoWhisper-small / Whisper-small trên VIVOS
│   ├── mt/                    # Baseline B: VinAI Translate trên PhoMT; cascade trên FLEURS
│   ├── eval/                  # tính lại WER/CER/S-D-I từ file dự đoán
│   └── utils/seed.py          # cố định seed, in thông tin môi trường
├── scripts/                   # run_asr_baseline.ps1 (TV1), tv4_reports.ps1 (TV4)
├── reports/task1/             # kết quả Task 1: asr/, mt/, data/, so_lieu_chung.json
├── tests/
├── notebooks/  app/  checkpoints/   # dùng từ Task 2
```

## Chạy lại

```
python -m venv .venv
.venv\Scripts\activate
pip install torch==2.6.0 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
python src/mt/download_models.py
```

1. **Baseline A (VIVOS):** `powershell -ExecutionPolicy Bypass -File scripts\run_asr_baseline.ps1`. Script tự tạo môi trường riêng, tải VIVOS test và checkpoint đúng revision.
2. **Baseline B (PhoMT):** tải PhoMT (xem `data/README.md`), rồi chạy `python src/mt/run_phomt.py test`.
3. **Cascade (FLEURS):** `python data/build_fleurs_eval.py`, rồi `python src/mt/run_cascade.py`.
4. **Thống kê và kiểm leakage (TV4):** `powershell -ExecutionPolicy Bypass -File scripts\tv4_reports.ps1 -FleursViTsv data\fleurs\data\vi_vn\test.tsv -FleursJson data\processed\fleurs_vi_en_test.json -PhoMTZip <PhoMT.zip> -OutDir reports\task1\data`
5. **Kiểm tra:** `pytest`

## Không có trong repo

- Dữ liệu âm thanh và văn bản: tải bằng script ở trên.
- Trọng số mô hình: tải từ Hugging Face đúng revision trong `src/mt/download_models.py` và `src/asr/download_checkpoints.py`.
- Mọi nội dung của PhoMT, kể cả bản dịch trên tập test, vì license cấm phân phối lại.

## License và trích dẫn

- Dữ liệu: VIVOS CC BY-NC-SA 4.0 (dự đoán VIVOS trong `reports/task1/asr/` giữ license này, xem `LICENSE_DATA.txt`), FLEURS CC BY 4.0, PhoMT chỉ dùng nghiên cứu.
- Mô hình: PhoWhisper BSD-3-Clause, Whisper MIT, VinAI Translate AGPL-3.0.
- Tài liệu tham khảo đầy đủ (IEEE) nằm trong slide và proposal Task 1.

## Tiến độ

- [x] **Task 1** (nộp 13/10/2026): proposal, chạy lại 2 baseline, đo lỗi lan truyền, kiểm leakage
- [ ] **Task 2** (đang làm): xử lý dữ liệu, chạy lại 2 baseline trên cùng máy, Proposed Method V1 → Vn
- [ ] **Task 3:** demo Gradio, đóng gói, báo cáo cuối

Checklist chi tiết và người phụ trách: [WORKFLOW.md](WORKFLOW.md).

## Quy ước làm việc

- Mỗi người commit bằng tài khoản GitHub của mình (điểm cá nhân tính theo lịch sử commit).
- Không commit dữ liệu, checkpoint, âm thanh hay tài liệu môn học (`.gitignore` đã chặn).
- Ghi nhận: có dùng công cụ AI hỗ trợ viết script và kiểm tra số liệu. Thành viên phụ trách từng phần phải hiểu và giải thích được phần đó.
