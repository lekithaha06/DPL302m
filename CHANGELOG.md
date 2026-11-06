# Thay đổi

## 04/11/2026 — tích hợp cuối (Kiệt)

| # | Thay đổi | Ở đâu |
|---|---|---|
| 35 | Chốt quy tắc chọn bản trên DEV trước khi chạy ablation; áp cho V1–V4 + ablation → **V2** là bản cuối, mặc định của app/API/CLI/Docker | `configs/ban_chot.json`, `src/pipeline.py`, `experiments/reports/ablation/` |
| 36 | B1 Whisper Translate end-to-end: code bàn giao gốc (giữ nguyên) + bản sửa (không cắt audio > 30 s, ghim revision, seed, suppress tokens, utf-8, schema chung), chạy đủ 857 bản | `experiments/scripts/baseline2/`, `experiments/runs/b1/` |
| 37 | Ablation một yếu tố so với V2: rank 8, rank 32, augmentation; có checkpoint, log, bảng | `checkpoints/A_*`, `experiments/checkpoints/A_*`, `notebooks/03_ablation_va_chon_ban_cuoi.ipynb` |
| 38 | Đánh giá chung, prediction theo schema, workbook 3 sheet | `notebooks/06_danh_gia_tong_hop.ipynb`, `reports/bang_ket_qua.xlsx` |
| 39 | Đo lại cả hệ, tốc độ và nghiệm thu với V2 | `experiments/reports/he_thong_V2/`, `experiments/reports/toc_do/lap_V2/` |
| 40 | Ruff check + format toàn bộ `src api app tests`; README, giới hạn trong app, mốc F09 theo số V2 | README, `app/gradio_app.py`, `tests/nghiem_thu_that.py` |
| 41 | Kiểm tra 3 seed V1–V4 và ablation, đo độ bền khối nghe, notebook toàn bộ code, `src/train.py`, thêm adapter V1 và các seed | `experiments/reports/ba_seed/`, `experiments/reports/robust/`, `notebooks/00_toan_bo_code.ipynb` |

## 03/11/2026 — sửa theo demo và bảng kiểm thử F01–F12

Proposed Method giữ nguyên: PhoWhisper-small pretrained + VinAI Translate + LoRA V4, không huấn luyện thêm. Chỉ đổi tiền xử lý, hậu xử lý và cách chia đoạn.

| # | Lỗi (mã bảng kiểm) | Nguyên nhân đã kiểm | Sửa ở |
|---|---|---|---|
| 27 (F02) | Audio dài lặp chữ "có thể. có thể" | `_cat_deu` cắt đúng 15,24 s của file 30,48 s, lúc đang nói (−27,7 dB), trong khi 13,70–14,65 s là khoảng lặng thật | `src/audio.py`: điểm cắt dời tới chỗ nhỏ tiếng nhất ±3 s (file đó cắt ở 14,35 s, −50,9 dB); 5/7 file dài FLEURS đổi điểm cắt; `bo_lap_cho_noi()` bỏ cụm ≥ 2 từ lặp ở đầu đoạn sau. Test trong `test_audio.py`, `test_pipeline.py` |
| 28 (F01/F06) | Nói số thì dịch sai (1755 → 1971) | PhoWhisper viết số bằng chữ, trong khi dữ liệu dịch dùng chữ số | `src/so.py`, gọi trong `HeThong` trước khi dịch (cả upload, micro, API, CLI). `CHUAN_HOA_SO=0` để tắt. Lời gốc giữ ở `transcript_vi_goc`. `tests/test_so.py` |
| 29 (F03) | Micro cắt cứng 10 s giữa câu | `_cho_cat` chỉ cắt sớm khi có khung < 0,1 × trung vị | `src/truc_tiep.py`: cắt khi ngừng nghỉ ≥ 0,3 s sau 10 s (ngưỡng p95 − 20 dB trên năng lượng làm trơn 200 ms; trên 7 file FLEURS dài cắt ở −45 đến −52 dB ở 5 file), nói liền thì cắt ở 20 s; thêm 0,2 s đệm trước mỗi đoạn; khi Stop nhận dạng lại cả bản bằng đường của tab tải tệp; `LUU_MIC` lưu WAV thô + 16 kHz + từng đoạn |
| 30 (F05) | File rỗng/hỏng/.txt đổi đuôi hiện "AppError" | `gr.Audio` giải mã file trước khi callback chạy | tab tải tệp dùng `gr.File` + `src/audio.doc_tep()` báo lỗi tiếng Việt |
| 31 (F04) | `pip install -r requirements.txt` xung đột | gradio_client 1.3.0 cần `websockets<13`; `uvicorn[standard]==0.54.0` kéo websockets 17 | khoá `uvicorn[standard]==0.32.1`, `websockets==12.0`, `scipy==1.13.1` (bản Kiệt đã chạy); CI thêm `pip check` và job cài sạch |
| 32 (F07/F10) | Dễ hiểu nhầm V4 cải thiện ASR | LoRA chỉ gắn khối dịch | README, docstring `pipeline.py`: ghi rõ; bảng Kết quả chính có nguồn file cho từng số |
| 33 (F08) | Chưa có cách so trước/sau trên cùng tập | — | `tests/danh_gia_proposed.py` (WER/CER ASR gốc, BLEU/chrF++ cuối pipeline, nhóm audio dài); `tests/bo_cau_tu_thu/` 20 câu số/ngày/tên riêng/thuật ngữ |
| 34 (F09) | Lint | `api/main.py` import `hmac` sai thứ tự (I001) | đã sửa; vẫn cần chạy `ruff format` ở máy có ruff |

Máy sửa khi đó không có GPU; các bước đo lại đã làm ở mục 04/11 (trừ micro thật, xem `KIEM_THU_CUOI.md`).

## 03/11/2026 — sửa theo kiểm thử với model thật

Kiệt chạy gói với model thật ngày 01/11/2026 (RTX 4060, Windows, Python 3.11) và tìm ra các lỗi dưới đây. Unit test dùng backend giả nên không thể phát hiện chúng.

| # | Lỗi | Sửa ở |
|---|---|---|
| 1 | Thiếu `protobuf` → tokenizer VinAI Translate không nạp được → hệ **tự chuyển sang backend giả**, trả chữ giả mà không ai biết | `requirements.txt`; `src/pipeline.py`: nạp lỗi thì báo lỗi và dừng |
| 2 | Không khoá phiên bản → pip cài Gradio 6 → giao diện crash (`show_copy_button`) | khoá `gradio==4.44.1`, `fastapi==0.115.6`, `pydantic==2.10.6` ở `requirements.txt` và `docker/requirements-app.txt`; app báo rõ nếu sai phiên bản |
| 3 | VAD bật mặc định, cắt cả audio ngắn, ngưỡng tuyệt đối −45 dBFS → 28,9% file FLEURS bị coi là nhỏ tiếng, WER 34,79% thay vì 15,05% | `src/audio.py`: audio ≤ 28 s giữ nguyên; audio dài mặc định chia đều; VAD là tuỳ chọn, ngưỡng tương đối, gom vùng nói thành đoạn dài |
| 4 | Gộp adapter LoRA ở fp16 → BLEU thấp hơn khoảng 0,3 | `src/pipeline.py`: nạp fp32, gộp, rồi mới đổi fp16 (giống `translate.py` Task 2) |
| 5 | Không áp danh sách suppress tokens của protocol | `configs/common_suppression_from_task1.json`, nạp trong `ThatBackend` |
| 6 | `evaluate.py --metric bleu` crash | dùng `sacrebleu.BLEU()` / `CHRF()`, thêm test |
| 7 | `torch` không chỉ bản CUDA → Windows cài bản CPU | `--extra-index-url .../cu117` trong `requirements.txt` |
| 8 | Không đọc được m4a/webm | `doc_audio_bytes()` lùi về ffmpeg |
| 9 | Thông báo lỗi 400 lộ `<_io.BytesIO object at 0x…>` | `api/main.py`: chi tiết chỉ ghi log |
| 10 | `chuan_hoa()` kiểm kiểu int sau khi đã đổi sang float | kiểm trước khi đổi, thêm test |
| 11 | Gradio gửi analytics ra ngoài | `GRADIO_ANALYTICS_ENABLED=False` |
| 12 | `/dich` là `async def` nhưng chạy suy luận chặn | đổi sang `def` + khoá, request xử lý lần lượt |
| 13 | Lint: B904, E741, B905, F401, I001, SIM108 | đã sửa tay; **cần chạy `ruff format` một lần** (máy sửa không có mạng để cài ruff) |
| 14 | Trích dẫn VinAI Translate sai tên bài | README, báo cáo, paper |
| 15 | README ghi 57 test, VRAM huấn luyện 5,99 GiB | 66 test; 5,58 GiB (theo `chon.json`) |
| 16 | Gradio 4.44.1 crash với `huggingface_hub` ≥ 1.0 (bỏ `HfFolder`) | khoá `huggingface_hub==0.36.2` |
| 17 | README chỉ có lệnh bash, `ASR_BACKEND=gia python …` không chạy trên Windows | thêm lệnh PowerShell/cmd |
| 18 | Adapter LoRA (kết quả chính của đề tài) không có trong repo vì `.gitignore` loại cả `checkpoints/` → demo chỉ chạy được B0 | đưa `checkpoints/V3/best`, `V4/best` + `SHA256SUMS` vào repo; mặc định dùng V4, `ADAPTER_PATH=none` cho B0; thêm `tests/test_adapter.py` |
| 19 (F05) | Audio toàn im lặng vẫn gọi model, backend giả trả chữ, `test_audio_toan_im_lang` fail; Whisper thật gặp im lặng cũng bịa chữ | `la_im_lang()`: bỏ đoạn có khung 30 ms to nhất < −60 dBFS **trước** khi gọi model; giọng −50 dBFS vẫn giữ. `tests/test_pipeline.py` |
| 20 (F02) | Tab micro phải thu xong mới bấm xử lý | `src/truc_tiep.py`: `gr.Audio(streaming=True)` + `gr.State`, cắt mỗi 10 s tại chỗ nhỏ tiếng nhất, hiện từng đoạn khi đang thu, flush khi Stop. `tests/test_truc_tiep.py` |
| 21 (F03/F08) | Chưa có test audio 1/3/5 phút, nhiều sample rate, m4a/webm/ogg, file rỗng/hỏng | thêm vào `test_pipeline.py`, `test_audio.py` |
| 22 (F04) | Script data/train/eval chỉ trỏ tới gói ngoài | `experiments/`: toàn bộ script, config, manifest, dự đoán, điểm; `chay_lai.sh cham|nho|day_du`; đường dẫn cứng `D:/CAIDCM` bỏ khỏi `env.sh` |
| 23 (F06) | Mặc định V4 nhưng BLEU dev cascade V3 cao hơn, chưa ghi lý do | nhóm chốt V4; lý do theo số dev ở `configs/ban_chot.json`, có test khớp số. App/API/CLI/Docker dùng chung `ADAPTER_MAC_DINH` |
| 24 (F10) | GUI không báo đang xử lý, kết quả cũ còn lại khi tải tệp mới, bấm nhiều lần chạy chồng | hiện "Đang xử lý", xoá kết quả cũ, hàng đợi 1 lượt, lỗi API/mạng báo rõ và cho thử lại; kết quả ghi `mo_hinh` (model + adapter) |
| 25 (F11) | API không xác thực | `API_KEY` → header `X-API-Key`, so sánh hằng thời gian; app tự gửi; log cảnh báo khi chưa đặt |
| 26 (F01/F09) | Chưa có cách nghiệm thu model thật lặp lại được | `tests/nghiem_thu_that.py` tự kiểm T01, T03–T09, F09, xuất `bang.md` |

Đổi giao diện dòng lệnh: `inference.py --khong_vad` bỏ, thay bằng `--vad` (mặc định đã là chia đều).

Số đo 01/11 sau khi sửa 1–3: WER 12,27%, BLEU 27,63 (V4). Đã đo lại sau các sửa đổi: xem `experiments/reports/he_thong_V2/`.
