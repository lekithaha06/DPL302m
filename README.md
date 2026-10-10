# Vietnamese ASR + Vietnamese→English Translation

DPL302m project — **Đề tài 1**: nhận dạng giọng nói tiếng Việt kèm dịch sang tiếng Anh.

- **Input:** file audio (wav/mp3/flac) hoặc micro real-time
- **Output:** transcript tiếng Việt + bản dịch tiếng Anh (kèm timestamp)
- **Hướng tiếp cận:** cascade `VAD → Whisper-small (fine-tune) → dấu câu → mBART vi→en (chống nhiễu ASR)`, so sánh với Whisper dịch trực tiếp (end-to-end)

Kế hoạch chi tiết các phase: [WORKFLOW.md](WORKFLOW.md).

## Team

| Thành viên | MSSV | Vai trò | GitHub |
|---|---|---|---|
| [Họ tên 1] | [MSSV] | ASR lead | [@user] |
| [Họ tên 2] | [MSSV] | MT lead | [@user] |
| [Họ tên 3] | [MSSV] | System / Demo lead | [@user] |

## Cấu trúc thư mục

```
├── README.md
├── WORKFLOW.md          # kế hoạch & checklist
├── requirements.txt
├── configs/             # yaml cấu hình (base.yaml + cấu hình từng thí nghiệm)
├── data/                # script tải/tiền xử lý (KHÔNG commit dữ liệu nặng)
├── notebooks/           # EDA, phân tích lỗi
├── src/
│   ├── dataset/         # Dataset/DataLoader
│   ├── models/          # ASR, MT, punctuation
│   ├── utils/           # seed, môi trường, chuẩn hoá văn bản
│   ├── train.py
│   ├── evaluate.py
│   └── inference.py
├── app/                 # gradio_app.py
├── api/                 # (bonus) FastAPI
├── docker/              # (bonus) Dockerfile
├── .github/workflows/   # (bonus) CI/CD
├── tests/
├── checkpoints/         # trọng số (không commit)
└── reports/             # báo cáo, hình
```

## Cài đặt

Yêu cầu: Python 3.11, GPU NVIDIA (dev: RTX 4060 Laptop 8 GB, CUDA 12.4).

```bash
python -m venv .venv
.venv\Scripts\activate
pip install torch==2.6.0 torchaudio==2.6.0 --index-url https://download.pytorch.org/whl/cu124
pip install -r requirements.txt
```

Kiểm tra môi trường (in ra phiên bản thư viện, GPU, VRAM để ghi vào báo cáo):

```bash
python -m src.utils.seed
```

## Tái lập kết quả

- Seed mặc định `42`, cấu hình trong `configs/base.yaml`, gọi `set_seed()` ở đầu mọi script train/eval.
- Mọi siêu tham số nằm trong `configs/*.yaml`, không hard-code.
- Chạy `python -m src.utils.seed` rồi dán kết quả vào mục **Môi trường** bên dưới.

### Môi trường đã dùng

| Thành phần | Giá trị |
|---|---|
| OS | Windows 11 |
| GPU | NVIDIA GeForce RTX 4060 Laptop, 8 GB |
| Python | 3.11 |
| torch | 2.6.0+cu124 |
| transformers | 5.17.0 |

## Dữ liệu

Chi tiết nguồn, license và cách tải: xem `data/README.md` (sẽ bổ sung ở Phase 2).

## Quy ước làm việc nhóm

- Mỗi người commit bằng tài khoản GitHub của mình, commit nhỏ và đều đặn (điểm cá nhân dựa vào lịch sử commit).
- Nhánh: `main` ổn định; làm việc trên `feat/<tên>-<nội dung>`, merge qua Pull Request.
- Commit message: `<phase>: <việc đã làm>`, ví dụ `p2: add VIVOS download script`.
- Không đẩy dữ liệu, checkpoint, file âm thanh lên Git (đã có trong `.gitignore`).
- Không dùng tập test để huấn luyện hoặc chọn siêu tham số.
- Ghi rõ phần nào có dùng công cụ AI hỗ trợ trong báo cáo.

## Trích dẫn

Danh sách tài liệu tham khảo: xem slide Task 1 và `reports/`.
