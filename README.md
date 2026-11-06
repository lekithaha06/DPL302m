# Nhận dạng giọng nói tiếng Việt và dịch sang văn bản tiếng Anh

Hệ thống nhận audio tiếng Việt, trả về transcript tiếng Việt và bản dịch tiếng Anh kèm mốc thời gian từng đoạn. Kiến trúc cascade: **PhoWhisper-small** cho khâu nghe, **VinAI Translate vi2en + adapter LoRA** cho khâu dịch.

Môn DPL302m, Đề tài 1, miền ứng dụng Giáo dục. Mã nhóm và GVHD: [nhóm điền].

| Thành viên | MSSV | Phụ trách |
|---|---|---|
| Bùi Ngọc Phương Uyên | SE205253 | Dữ liệu, EDA, pipeline làm sạch |
| Dương Gia Bảo | SE205262 | Khối ASR, protocol đánh giá WER/CER |
| Lê Tuấn Kiệt | SE205279 | Chạy toàn bộ thực nghiệm, khối dịch, LoRA |
| Hồ Lâm Bảo Đăng | SE205148 | Kiến trúc hệ thống, tiêu chí khả thi, demo, API, triển khai |

## Kết quả chính

*[Cập nhật 04/11/2026 – sinh từ file kết quả bằng `experiments/scripts/dong_goi_repo_cuoi.py`; mỗi số có nguồn ở cột cuối.]*

**Hệ cuối** = PhoWhisper-small pretrained (khối nghe, không fine-tune) → VinAI Translate vi2en + **adapter LoRA V2** (khối dịch) + tiền/hậu xử lý (chia đoạn tại chỗ ngắt nghỉ, bỏ lặp ở chỗ nối, đổi số đọc bằng chữ). **V2 được chọn theo quy tắc DEV chốt trước khi chạy ablation** (`experiments/reports/ablation/QUY_TAC_CHON.md`): bản có BLEU dev cascade cao nhất là V3 (26,71); các bản cách ≤ 0,5 coi là hoà (V2, V4, V3, V1); trong nhóm hoà chọn BLEU dev dịch sạch cao nhất → **V2** (36,93). Quy tắc này chốt sau khi đã có số test của V1–V4 (quy tắc đầu, lấy dev cascade cao nhất, cho ra V3), nên không phải lựa chọn mù với test; chỉ ba bản ablation chạy sau khi có quy tắc.

**Kiểm tra 3 seed** (seed 42, 1, 2; `experiments/reports/ba_seed/`, `notebooks/04_kiem_tra_3_seed.ipynb`): V2 test cascade 27,34 ± 0,12, test sạch 37,80 ± 0,26, hơn B0 +4,65 ± 0,12. Áp quy tắc trên trung bình dev vẫn ra V2. Seed 1 và 2 train trên Modal bằng torch 2.7.1, dịch và chấm bằng torch 2.0.1 như seed 42. Các bảng dưới là số seed 42, đúng adapter chạy trong sản phẩm.

### Baseline (FLEURS vi_vn test, 857 bản thu)

| Hệ | WER khối nghe | BLEU | chrF++ | Nguồn |
|---|---|---|---|---|
| B0 cascade: PhoWhisper-small → VinAI gốc | 13,68% | 22,69 | 49,38 | `experiments/runs/mt/B0/fleurs_test_asr_pho/score.json` |
| Cascade khối nghe thứ hai: Whisper-small → VinAI gốc | 21,24% | 18,58 | 44,62 | `experiments/runs/mt/B0/fleurs_test_asr_wsp/score.json` |
| B1 end-to-end: Whisper-small `task=translate` | không có transcript Việt | 3,80 | 25,45 | `experiments/runs/mt/B1_whisper-small_translate/fleurs_test_audio/score.json` |

B1 kém B0 18,89 BLEU (KTC 95% [-20,65; -17,14]): Whisper-small dịch tiếng Việt yếu, nhiều câu lặp vòng khi giải mã (`notebooks/02_baseline_B1_whisper_translate.ipynb`, `notebooks/phan_tich_loi.ipynb` mục 12). Paper đối chiếu cùng dataset: PhoWhisper VIVOS 6,33 (nhóm 6,24), Whisper-small FLEURS 21,2 (nhóm 21,24), VinAI PhoMT 40,42 (nhóm 40,79).

### Proposed: LoRA khối dịch – phiên bản và ablation (BLEU)

| Bản | Thay đổi | Dev cascade | Dev sạch | Test cascade | Test sạch | PhoMT |
|---|---|---|---|---|---|---|
| B0 | VinAI gốc | 22,96 | 37,57 | 22,69 | 38,27 | 40,79 |
| V1 | + LoRA trên lời ASR | 26,47 | 35,97 | 27,49 | 36,21 | 36,96 |
| V2 ★ | V1 + PhoMT 1:1 | 26,45 | 36,93 | 27,47 | 38,09 | 40,41 |
| V3 | V2 + cân bằng câu/độ dài | 26,71 | 36,37 | 27,33 | 36,76 | 39,58 |
| V4 | V3, lr 5e-5 | 26,33 | 36,75 | 27,37 | 38,11 | 40,08 |
| A_r8 | V2, rank 8 | 25,97 | 36,74 | 27,26 | 37,96 | 40,47 |
| A_r32 | V2, rank 32 | 25,88 | 36,44 | 27,62 | 37,96 | 40,27 |
| A_aug | V2 + augmentation transcript sạch | 24,60 | 37,30 | 25,49 | 36,65 | 39,57 |

V2 so với B0 trên test cascade: +4,78 (KTC 95% [3,78; 5,83]); với khối nghe Whisper-small: 18,58 → 19,68 (+1,10 [0,43; 1,78]). Giữa V1–V4 và ablation rank, chênh lệch test nằm trong khoảng tin cậy. Nguồn: `experiments/reports/ablation/bang_ablation.csv`, `experiments/reports/mt/bootstrap_*.json`.

### Cả hệ sản phẩm và tính khả thi

| Chỉ số | Giá trị | Nguồn |
|---|---|---|
| Cả hệ (V2 + tiền/hậu xử lý), 857 bản | WER 12,26% · BLEU 28,15 · chrF++ 53,10 | `experiments/reports/he_thong_V2/ket_qua.json` |
| So với cách xử lý cũ (cắt giữa, không đổi số) | BLEU 28,01 → 28,15, Δ 0,14 [-0,20; 0,51] | `experiments/reports/he_thong_V2/bootstrap_cu_vs_moi.json` |
| Tốc độ B0 (100 bản, 3 lần xen kẽ, trung vị) | RTF 0,115 · p95 2,24 s | `experiments/reports/toc_do/lap_V2/` |
| Tốc độ V2 (100 bản, 3 lần xen kẽ, trung vị) | RTF 0,113 · p95 2,24 s | `experiments/reports/toc_do/lap_V2/` |
| VRAM đỉnh khi suy luận · kích thước | 1,57 GiB · 2,69 GB (adapter 34,7 MB) | `experiments/reports/toc_do/lap_V2/` |

Notebook có output: `notebooks/eda.ipynb`, `phan_tich_loi.ipynb`, `02_baseline_B1_whisper_translate.ipynb`, `03_ablation_va_chon_ban_cuoi.ipynb`, `06_danh_gia_tong_hop.ipynb`, `05_do_ben_khoi_nghe.ipynb`, `04_kiem_tra_3_seed.ipynb`. Toàn bộ code kèm output và phần checkpoint: `notebooks/00_toan_bo_code.ipynb`. Workbook 6 sheet: `reports/bang_ket_qua.xlsx`. Bảng PASS / FAIL / NOT RUN: `KIEM_THU_CUOI.md`.

## Cài đặt

Cần **Python 3.11**, và `ffmpeg` để đọc m4a/webm (file ghi âm điện thoại, trình duyệt).

```bash
git clone <url-repo> && cd <ten-repo>
python -m venv .venv && source .venv/bin/activate     # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

Ba điều hay gặp lỗi:

- **Phải cài vào venv mới.** Mọi thư viện đều khoá phiên bản. Nếu venv đã có Gradio 5/6 hoặc pydantic ≥ 2.11, huggingface_hub ≥ 1.0 từ trước thì giao diện crash. Kiểm tra: `python -c "import gradio; print(gradio.__version__)"` phải ra `4.44.1`.
- **torch bản CUDA.** `requirements.txt` đã có dòng `--extra-index-url https://download.pytorch.org/whl/cu117`. Kiểm tra: `python -c "import torch; print(torch.cuda.is_available())"` phải ra `True`. Ra `False` thì đang chạy CPU, rất chậm.
- **Xung đột `websockets`.** Gradio 4.44.1 (gradio_client 1.3.0) cần `websockets<13`, còn `uvicorn[standard]` bản mới kéo websockets 14 trở lên. Repo khoá `uvicorn[standard]==0.32.1` và `websockets==12.0`. Sau khi cài, chạy `python -m pip check` và kết quả phải là `No broken requirements found`. Nếu vẫn báo lỗi, gửi lại **toàn bộ** log `pip install` (CI job `cai-sach` lưu log này thành artifact).
- **Lần chạy đầu tải khoảng 2,7 GB trọng số** từ Hugging Face, cần mạng. Nếu nạp model lỗi thì chương trình dừng và in lý do, không chạy tiếp với kết quả giả.

Trên Ubuntu, nếu thiếu thư viện hệ thống: `sudo apt-get install -y ffmpeg libsndfile1`.

Suy luận trên CPU chạy được nhưng chậm; các con số tốc độ ở trên đo trên GPU.

## Chạy demo

```bash
python app/gradio_app.py                  # mở http://localhost:7860
GRADIO_SHARE=1 python app/gradio_app.py   # tạo link public tạm thời
```

Giao diện có hai tab: tải tệp lên, và thu âm trực tiếp từ micro. Ở tab micro, kết quả hiện **theo từng đoạn ngay trong lúc đang nói**: sau khoảng 10 giây (`CUA_SO_TRUC_TIEP_S`), hệ cắt ở chỗ bạn ngừng nghỉ (≥ 0,3 s); nói liền thì cắt bắt buộc ở 20 giây. Khi bấm Stop, **cả bản thu được nhận dạng lại** bằng đúng đường xử lý của tab tải tệp (`CHAY_LAI_KHI_DUNG=1`, mặc định), nên kết quả cuối của micro và của upload cùng một file là như nhau. Đặt `LUU_MIC=mic_luu` để lưu WAV thô từ trình duyệt, WAV 16 kHz, từng đoạn và `ket_qua.json` của mỗi lượt thu, dùng để truy lỗi. Đoạn im lặng bị bỏ, không sinh chữ giả. File rỗng, hỏng hoặc không phải audio được báo bằng tiếng Việt, không còn "AppError". Kết quả hiện transcript tiếng Việt và bản dịch tiếng Anh song song, kèm bảng chi tiết theo từng đoạn với mốc thời gian.

**Adapter LoRA có sẵn trong repo** (`checkpoints/V2/best` là bản chốt; `V3`, `V4`, ablation `A_r8`, `A_r32`, `A_aug` để so sánh; r=16, α=32 trừ bản rank). App, API và CLI **mặc định dùng V2**, không cần đặt gì thêm. Đổi bản:

```bash
ADAPTER_PATH=checkpoints/V3/best python app/gradio_app.py   # bản để so sánh, bản cuối là V2
ADAPTER_PATH=none python app/gradio_app.py                  # VinAI gốc, baseline B0
```

Kiểm tra adapter còn nguyên vẹn: `cd checkpoints && sha256sum -c SHA256SUMS`.

**Chạy thử không cần GPU và không cần tải trọng số** — hữu ích khi kiểm tra giao diện:

```bash
ASR_BACKEND=gia python app/gradio_app.py
```

**Trên Windows** cú pháp `BIEN=gia_tri lenh` không chạy được (đây là cú pháp của bash). Dùng:

```powershell
# PowerShell
$env:ASR_BACKEND="gia"; python app/gradio_app.py
$env:ADAPTER_PATH="checkpoints/V2/best"; python app/gradio_app.py
```

```bat
:: cmd
set ASR_BACKEND=gia && python app\gradio_app.py
```

Backend giả trả chuỗi cố định, giao diện sẽ hiện cảnh báo. Không dùng kết quả từ backend giả để báo cáo bất kỳ con số nào.

## Chạy API

```bash
uvicorn api.main:app --host 0.0.0.0 --port 8000
```

Tài liệu endpoint tự sinh ở `http://localhost:8000/docs`.

| Endpoint | Method | Mô tả |
|---|---|---|
| `/health` | GET | Kiểm tra service còn sống và model đã nạp chưa |
| `/dich` | POST | Nhận file audio, trả transcript và bản dịch |
| `/docs` | GET | Tài liệu OpenAPI tương tác |

```bash
curl -X POST "http://localhost:8000/dich" -F "file=@bai_giang.wav"
curl -X POST "http://localhost:8000/dich?dung_vad=true&max_doan_s=20" -F "file=@bai_giang.wav"
```

Tham số truy vấn: `max_doan_s` (mặc định 28, phải ≤ 30) và `dung_vad` (mặc định `false`). Audio không quá `max_doan_s` giây luôn là 1 đoạn. Audio dài hơn thì mặc định chia thành các phần gần bằng nhau, mỗi điểm cắt dời tới chỗ nhỏ tiếng nhất trong ±3 s; `dung_vad=true` thì gom theo vùng nói (chưa đo với model thật). Kết quả có thêm `transcript_vi_goc` (lời ASR trước khi đổi số).

**Xác thực:** đặt biến `API_KEY` thì `/dich` bắt buộc header `X-API-Key` (sai hoặc thiếu trả `401`), app Gradio tự gửi kèm. Không đặt thì API mở cho mọi người, log sẽ cảnh báo, chỉ nên dùng trên máy mình. Khi deploy public vẫn cần HTTPS (reverse proxy) và giới hạn tần suất; repo chưa có hai phần này. Mỗi lần chỉ xử lý một request, các request khác chờ.

Phản hồi gồm `transcript_vi`, `ban_dich_en`, `cac_doan` (mỗi đoạn có `moc_thoi_gian`, `bat_dau_s`, `ket_thuc_s`, transcript và bản dịch riêng), cùng `rtf` và thời gian xử lý từng khâu.

Mã lỗi: `400` file rỗng hoặc sai định dạng hoặc không đọc được, `401` sai API key, `413` file quá giới hạn (mặc định 50 MB), `422` thiếu file hoặc tham số sai, `503` model chưa nạp xong.

## Suy luận từ dòng lệnh

```bash
python src/inference.py --audio bai_giang.wav
python src/inference.py --thu_muc audio/ --json ket_qua.jsonl
python src/inference.py --audio a.wav --adapter checkpoints/V2/best --json ra.json
python src/inference.py --audio bai_giang_dai.wav --vad    # cắt audio dài tại khoảng lặng
```

## Chấm điểm và kiểm hồi quy

```bash
# WER/CER cho khối nghe
python src/evaluate.py --hyp runs/asr/<run>/predictions.jsonl --metric wer \
       --truong_ref reference --truong_hyp prediction --moc wer_phowhisper_fleurs

# BLEU và chrF++ cho khối dịch
python src/evaluate.py --hyp runs/mt/V3/fleurs_test_asr_pho/hyp.jsonl --metric bleu \
       --moc bleu_v3_cascade
```

Tham số `--moc` lấy ngưỡng từ các con số đã báo cáo ở Task 2 và trả mã thoát khác 0 nếu lệch quá `--sai_so` (mặc định 0,5). Dùng để phát hiện khi một thay đổi code làm lệch kết quả.

Scorer trong `src/evaluate.py` được viết độc lập theo protocol `vi_nfc_ps_space_v1` và đã tái lập đúng từng con số của thực nghiệm: WER VIVOS 6,24 với S/D/I/N = 448/21/13/7722, CER VIVOS 3,25 với 544/167/129/25809, WER FLEURS 13,68 với 2057/113/1389/26021.

## Huấn luyện

Toàn bộ pipeline thực nghiệm (tải và làm sạch dữ liệu, chia train/dev/test, ASR baseline, train LoRA V1–V4 + ablation, B1, chọn checkpoint, đánh giá, bootstrap, đo tốc độ) nằm ở `experiments/`, kèm dự đoán và điểm số đã chạy. Xem `experiments/README.md`.

```bash
bash experiments/chay_lai.sh cham     # không cần GPU: chấm lại từ dự đoán có sẵn, ra đúng số báo cáo
bash experiments/chay_lai.sh nho      # GPU: chạy cả pipeline trên 20 câu, 1 epoch
bash experiments/chay_lai.sh day_du   # GPU: chạy lại toàn bộ
```

Cấu hình từng phiên bản ở `experiments/configs/mt/`. Siêu tham số của bản cuối V2: LoRA r=16, α=32, dropout 0,05 trên q, k, v, out_proj, fc1, fc2; AdamW; lr 2e-4; warmup 6% rồi giảm tuyến tính; batch 4 × tích luỹ 4 = 16; 5 epoch, chọn epoch theo BLEU dev cascade. Thời gian huấn luyện khoảng 10 đến 13 phút mỗi epoch trên RTX 4060, VRAM đỉnh 5,58 GiB.

## Dữ liệu

Không đẩy dữ liệu lên Git. Xem `data/README.md` cho nguồn và giấy phép; script tải lại ở `experiments/scripts/data/`. Tổng khoảng 12 GB; PhoMT và FLoRes+ là dataset gated, cần xin quyền truy cập trên Hugging Face.

## Đánh giá Proposed Method

Cùng trọng số, so hai cấu hình trên cùng tập, cùng chuẩn hoá. `truoc_0411` là cắt đúng giữa, không bỏ lặp, không đổi số (cách cũ). `proposed` là cắt tại chỗ ngắt nghỉ, bỏ lặp ở chỗ nối, đổi số trước khi dịch.

```powershell
$env:FLEURS_AUDIO_DIR="D:/.../audio_16k/fleurs/test"
python tests/danh_gia_proposed.py --tap test                  # 857 bản, ra danh_gia/<ngày_giờ>/bang.md
python tests/danh_gia_proposed.py --tu_thu tests/bo_cau_tu_thu # 20 câu số/ngày/tên riêng/thuật ngữ tự thu
```

Bảng tách 3 tầng để không nhầm module: `WER_asr`/`CER_asr` chấm trên lời PhoWhisper nguyên bản, `WER_sau_doi_so` chỉ để tham khảo, còn `BLEU`/`chrF++` là điểm cuối pipeline. Có thêm nhóm `dai` (7 bản > 28 s) để thấy tác dụng của cách cắt mới. Mỗi mẫu được ghi vào `du_doan_<cấu_hình>.jsonl` cùng mốc cắt. Chưa chạy với model thật: số trong bảng Kết quả chính chưa gồm các thay đổi ngày 04/11.

## Kiểm thử

```bash
pip install -r requirements-dev.txt
pytest                                    # chạy toàn bộ
pytest --cov=src --cov=api                # kèm coverage
ruff check src api app tests              # lint
ruff format --check src api app tests     # kiểm định dạng (CI chạy cả hai)
```

Test dùng backend giả nên không cần GPU và không tải trọng số. Chúng kiểm tra tiền xử lý audio, chia đoạn và đọc 6 định dạng (`test_audio.py`), im lặng và giọng nhỏ, audio 1/3/5 phút, sample rate 8–48 kHz (`test_pipeline.py`), thu âm trực tiếp theo đoạn và chạy lại cả bản khi dừng (`test_truc_tiep.py`), đổi số đọc bằng chữ (`test_so.py`), scorer (`test_evaluate.py`), API kể cả API key và 10 request liên tiếp (`test_api.py`), cùng adapter LoRA và bản chốt (`test_adapter.py`).

Nghiệm thu với model thật (cần GPU): `python tests/nghiem_thu_that.py --audio a.wav b.wav c.wav`. Xem mục **Nghiệm thu** bên dưới. Backend giả chỉ kiểm được phần code hệ thống. Các lỗi về thư viện, model thật và chất lượng chỉ lộ ra khi chạy với model thật, xem `CHANGELOG.md`.

## Nghiệm thu với model thật

Unit test chỉ kiểm code. Trước khi chốt demo, chạy một lần trên máy GPU với 3–5 file tiếng Việt **chưa dùng trong test** (tự thu, 10–20 s):

```powershell
$env:ASR_BACKEND="that"
python tests/nghiem_thu_that.py --audio a.wav b.wav c.wav
# thêm hồi quy toàn bộ FLEURS test (khoảng 15 phút):
$env:FLEURS_AUDIO_DIR="D:/.../audio_16k/fleurs/test"; python tests/nghiem_thu_that.py --audio a.wav --hoi_quy 857
# thêm kiểm API (chạy uvicorn ở cửa sổ khác trước):
python tests/nghiem_thu_that.py --audio a.wav --api http://localhost:8000
```

Script tự kiểm và ghi `nghiem_thu/<ngày_giờ>/bang.md`:

| Mã | Kiểm | Tự động |
|---|---|---|
| T01/F01 | transcript + bản dịch thật, `backend=that`, không có chuỗi giả | có (người kiểm vẫn phải đọc nội dung) |
| T03/F03 | audio 1/3/5 phút: đoạn < 30 s, liền nhau, phủ hết | có |
| T04/F05 | im lặng 3 s không sinh chữ; giọng −50 dBFS vẫn nhận | có |
| T05/F08 | wav, mp3, flac, ogg, m4a, webm; 8 kHz; 44,1 kHz stereo | có (cần ffmpeg) |
| T06/F10 | API: file rỗng, hỏng, sai đuôi, quá dung lượng, 10 request | có, khi có `--api` |
| T07 | adapter sai đường dẫn thì báo lỗi, không chạy giả | có |
| T08/F06 | V2 (mặc định), V4, B0 nạp đúng adapter, log có model ID | có |
| T09/F10 | 10 lượt liên tiếp không lẫn kết quả | có |
| F09 | WER/BLEU FLEURS test so với mốc 04/11 – bản V2 (WER 12,26, BLEU 28,15, sai số 1,0) | có, khi có `--hoi_quy` |
| T02 | micro nói 45–60 s, có đoạn hiện ra trước khi bấm Stop; câu ngày tháng nói 3 lần; so `ca_ban_16k.wav` qua tab tải tệp và CLI | **tay**: `LUU_MIC=mic_luu`, mở app, tab Thu âm trực tiếp |
| T09 | 2 tab trình duyệt cùng lúc, lần bấm sau xếp hàng | **tay** |
| T10 | `pytest`, `ruff check`, `ruff format --check`, `docker compose up` | **tay** |

## Triển khai bằng Docker

Hai service tách riêng: `api` nạp model và suy luận, `app` chỉ là giao diện và gọi `api` qua HTTP. Tách ra để ảnh giao diện không phải kéo theo torch, và để hai phần scale độc lập.

```bash
docker compose -f docker/docker-compose.yml up --build
# giao diện: http://localhost:7860    API: http://localhost:8000/docs
```

Chạy thử nhanh không cần trọng số:

```bash
ASR_BACKEND=gia docker compose -f docker/docker-compose.yml up --build
```

Trên máy có GPU NVIDIA, bỏ comment khối `deploy.resources` trong `docker/docker-compose.yml` (thư mục `checkpoints/` đã được mount sẵn, mặc định dùng V2).

Biến môi trường: `ASR_BACKEND` (`that` hoặc `gia`), `ADAPTER_PATH`, `API_KEY`, `MAX_UPLOAD_MB`, `API_PORT`, `APP_PORT`, `GRADIO_SHARE`, `CUA_SO_TRUC_TIEP_S`, `CHAY_LAI_KHI_DUNG`, `LUU_MIC`, `CHUAN_HOA_SO` (mặc định 1).

## CI/CD

`.github/workflows/ci.yml` chạy năm job: lint bằng ruff, test trên Python 3.10 và 3.11, cài sạch `requirements.txt`, build hai ảnh Docker rồi khởi động container và gọi thử `/health` cùng `/dich`, và deploy lên Hugging Face Spaces khi đẩy lên `main`. Job deploy tự bỏ qua nếu repo chưa đặt secret `HF_TOKEN`.

CI đặt `ASR_BACKEND=gia` vì runner không có GPU và không tải 2,69 GB trọng số.

## Cấu trúc repo

```
├── README.md
├── requirements.txt / requirements-dev.txt
├── pyproject.toml            cấu hình ruff
├── data/                     script tải và tiền xử lý, không chứa dữ liệu
├── notebooks/                EDA và phân tích lỗi
├── src/
│   ├── audio.py              chuẩn hoá sample rate, chia đoạn, đọc file
│   ├── pipeline.py           ghép khối nghe và khối dịch
│   ├── evaluate.py           WER, CER, BLEU, chrF++, kiểm hồi quy
│   ├── inference.py          suy luận từ dòng lệnh
│   ├── truc_tiep.py          gom audio micro theo đoạn khi đang thu
│   ├── so.py                 đổi số đọc bằng chữ sang chữ số trước khi dịch
│   ├── dataset/ models/      chỉ trỏ tới experiments/ (code thật ở đó)
├── checkpoints/              adapter LoRA V2 (chốt), V3, V4, ablation A_* + SHA256SUMS
├── configs/                  protocol ASR, suppress tokens, bản chốt (ban_chot.json)
├── experiments/              pipeline thực nghiệm: script, cấu hình, dự đoán, điểm
├── app/gradio_app.py         demo
├── api/main.py               FastAPI
├── docker/                   Dockerfile và docker-compose
├── .github/workflows/ci.yml  CI/CD
├── tests/                    unit test + nghiem_thu_that.py, danh_gia_proposed.py (chạy với model thật)
│   └── bo_cau_tu_thu/        20 câu số/ngày/tên riêng/thuật ngữ để tự thu
└── reports/                  bảng số liệu và hình
```

## Giới hạn đã biết

Những điều này đo được, nên cần biết trước khi dùng:

- Hệ chỉ được đo trên audio đọc rõ, một người nói, phòng yên tĩnh. Chưa đo với hội thoại tự nhiên, nhiều người nói chồng tiếng hay môi trường ồn.
- Tập đánh giá FLEURS dev và test đều 100% giọng nam, nên chưa có cơ sở kết luận hệ hoạt động như nhau với giọng nữ.
- Hệ làm tốt nhất ở miền Giáo dục (BLEU 31,45, WER khối nghe 10,76%) và kém nhất ở miền Tin tức (BLEU 22,51, WER 19,18%), nguyên nhân chính là tên riêng nước ngoài.
- Lỗi khâu nghe lan truyền sang khâu dịch và khâu dịch không sửa được. Ví dụ "Aristotle" bị nghe thành "arizona" thì bản dịch sai theo.
- Bản dịch có thể rút gọn làm mất chi tiết: 4 trên 361 câu dev có bản dịch ngắn hơn 0,7 lần tham chiếu (V2).
- Audio dài hơn 30 giây phải chia đoạn trước khi nhận dạng. Nếu đưa trực tiếp vào khối nghe thì WER lên tới 94,70% vì phần sau 30 giây bị giải mã sai. Cắt đúng giữa (cách cũ) đo trên 7 bản dài của FLEURS test còn WER 16,31%, nhưng có thể cắt ngang một từ và sinh chữ lặp ("học sinh có thể. có thể xác định", file 30,48 s cắt ở 15,24 s). Từ 04/11 điểm cắt được dời tới chỗ ngắt nghỉ gần nhất (file đó cắt ở 14,35 s, −51 dB) và cụm từ lặp ở chỗ nối được bỏ. Đo lại 04/11 với V2: 10 bản thu dài hơn 28 s của FLEURS test: WER 15,59%, BLEU 18,74 (đưa thẳng audio > 30 s vào khối nghe thì WER lên tới 94,70%).
- Khối nghe không fine-tune nên lỗi nghe vẫn còn: tên riêng ("Oravec" thành "ozil david"), và có thể nghe sai cả từ thường ("hôm nay" thành "có may"). Các bước tiền/hậu xử lý không sửa được loại lỗi này.
- Đổi số đọc bằng chữ dựa trên luật: chỉ đổi cụm từ 2 từ trở lên hoặc sau "ngày/tháng", giữ "thứ hai", "một số". Đo trên lời ASR dev: 72/88 số khớp tham chiếu, thừa 29 số (thường là số mà tham chiếu cũng viết bằng chữ).
- Chưa đo ở chế độ nghe liên tục theo thời gian thực và chưa đo với nhiều người dùng cùng lúc.

Đây là công cụ hỗ trợ, không dùng cho mục đích cần độ chính xác cao như dịch văn bản pháp lý hay y tế.

## Nguồn và giấy phép

**Mô hình**

- PhoWhisper-small: Le, T.-T., Nguyen, L. T., Nguyen, D. Q. (2024). *PhoWhisper: Automatic Speech Recognition for Vietnamese*. ICLR 2024 Tiny Papers. [arXiv](https://arxiv.org/pdf/2406.02555) · [checkpoint](https://huggingface.co/vinai/PhoWhisper-small) @a86b604c
- Whisper-small: Radford, A. et al. (2023). *Robust Speech Recognition via Large-Scale Weak Supervision*. ICML 2023. [PMLR](https://proceedings.mlr.press/v202/radford23a/radford23a.pdf) · [checkpoint](https://huggingface.co/openai/whisper-small) @973afd24
- VinAI Translate: Nguyen, T. H. et al. (2022). *A Vietnamese-English Neural Machine Translation System*. Interspeech 2022, pp. 5543–5544. [checkpoint](https://huggingface.co/vinai/vinai-translate-vi2en-v2) @ae7baa85

**Dữ liệu**

- VIVOS — CC BY-NC-SA 4.0 — [dataset card](https://huggingface.co/datasets/AILAB-VNUHCM/vivos) @3cbfb25
- FLEURS — CC BY 4.0 — [dataset card](https://huggingface.co/datasets/google/fleurs) @70bb2e8
- PhoMT — chỉ nghiên cứu, cấm phân phối lại — Doan, L. et al. (2021), EMNLP 2021. [arXiv](https://arxiv.org/abs/2110.12199) · [dataset](https://huggingface.co/datasets/vinai/PhoMT) @d4b9bf1
- FLoRes+ — CC BY-SA 4.0 — [dataset](https://huggingface.co/datasets/openlanguagedata/flores_plus)

**Thư viện** — PyTorch, Transformers 4.44.2, PEFT 0.12.0, sacreBLEU 2.4.3, Gradio, FastAPI.

Mã nguồn của nhóm phát hành theo MIT. Trọng số mô hình và dữ liệu giữ nguyên giấy phép gốc; đặc biệt PhoMT không được phân phối lại và VIVOS không dùng cho mục đích thương mại.
