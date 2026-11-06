# Dữ liệu

Không đẩy dữ liệu lên Git: tổng khoảng 12 GB. Thư mục này chỉ chứa script tải và tiền xử lý.

## Nguồn

| Bộ | Dùng cho | Số mẫu (train / dev / test) | Dung lượng | Giấy phép |
|---|---|---|---|---|
| VIVOS | đánh giá khối nghe | 11.660 / – / 760 câu | 1.406,5 MB | CC BY-NC-SA 4.0 |
| FLEURS vi_vn + en_us | huấn luyện và đánh giá cả hệ | 2.994 / 361 / 857 bản thu | 2.259,1 MB | CC BY 4.0 |
| PhoMT | khối dịch | 2.977.999 / 18.719 / 19.151 cặp câu | 339,4 MB | chỉ nghiên cứu, cấm phân phối lại |
| FLoRes+ | nhãn miền cho từng câu FLEURS | metadata 1.945 câu | < 1 MB | CC BY-SA 4.0 |

PhoMT và FLoRes+ là dataset gated: cần đăng nhập Hugging Face và xin quyền truy cập trước khi tải.

Revision cố định: VIVOS `3cbfb25`, FLEURS `70bb2e8`, PhoMT `d4b9bf1`. Phải giữ đúng revision để tái lập được kết quả.

## Tải lại

Script tải và làm sạch nằm trong gói thực nghiệm (`scripts/data/viec1` đến `viec4`). Chạy theo thứ tự: tải ba bộ dữ liệu, ghép và chia FLEURS kèm chống rò rỉ, làm sạch, rồi EDA và cân bằng.

Sau khi chạy xong, cấu trúc mong đợi:

```
data/
├── raw/              dữ liệu tải về, không sửa
├── clean/
│   ├── audio_16k/    audio đã resample 16 kHz PCM 16-bit
│   └── *.jsonl       manifest có id, đường dẫn, nhãn, duration
└── mt/               cặp câu cho khối dịch
```

## Lưu ý về giấy phép

- VIVOS là CC BY-NC-SA 4.0, không dùng cho mục đích thương mại.
- PhoMT không được phân phối lại. Gói nộp chỉ giữ `score.json`, không giữ văn bản.
- Nếu nhóm tự thu thêm audio, phải có sự đồng ý của người được thu và che thông tin nhạy cảm khi công bố.
