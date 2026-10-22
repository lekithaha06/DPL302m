# Task 2 · Phần IV: Hệ thống, tính khả thi và kế hoạch Task 3

Code: `src/system/cascade.py` (hệ thống đầu cuối), `src/system/measure_speed.py` (đo tốc độ, bộ nhớ, dung lượng).

## Kiến trúc hệ thống

```
Âm thanh (file wav/mp3/flac hoặc micro)
  → đọc, trộn mono, đổi về 16 kHz
  → Silero VAD: cắt đoạn có tiếng nói, gộp thành khối ≤ 25 giây (âm thanh dài)
  → PhoWhisper-small (ASR, FP16)          → chữ tiếng Việt + mốc thời gian từng khối
  → VinAI Translate vi2en + LoRA (MT, FP16) → câu tiếng Anh
  → hiển thị song song Việt | Anh theo từng đoạn
```

## Tiêu chí khả thi (đặt trước khi đo)

| Tiêu chí | Ngưỡng nhóm đặt ra | Lý do |
|---|---|---|
| Chất lượng dịch | Phiên bản cuối có BLEU cascade trên FLEURS test **cao hơn B0 (24,21)**, và BLEU PhoMT không giảm quá 1 điểm so với 40,25 | Cải tiến phải thật và không làm hỏng khả năng dịch văn bản sạch |
| Tốc độ | RTF toàn hệ thống **< 1** trên RTX 4060 | Xử lý nhanh hơn thời gian thực, đủ cho chế độ micro hiển thị theo đoạn |
| Độ trễ | Độ trễ trung vị một câu ngắn **< 3 giây** | Người dùng chờ chấp nhận được trong demo |
| Bộ nhớ | VRAM đỉnh **< 8 GB** (vừa GPU laptop phổ biến) | Chạy được trên máy giảng viên hoặc máy cá nhân có GPU |
| Âm thanh dài | Có VAD, xử lý được âm thanh vài phút | Yêu cầu chức năng của đề tài |

## Kết quả đo (RTX 4060 Laptop, FP16, máy không chạy việc khác; `system/speed_B0.json`, `system/speed_final.json`)

100 bản thu FLEURS test (tổng 1.279,8 giây, trung bình 12,8 giây/câu), chạy từng câu một, không VAD:

| | B0 | V2 (bản cuối) |
|---|---|---|
| RTF toàn hệ thống | 0,315 | 0,340 |
| RTF khối nghe / khối dịch | 0,215 / 0,100 | 0,229 / 0,111 |
| Độ trễ một câu: trung vị / p95 | 3,73 s / 6,67 s | 4,10 s / 7,06 s |
| VRAM đỉnh | 1.791 MB | 1.777 MB |
| Dung lượng trọng số | ASR 922 MB + MT 1.711 MB | như B0 + adapter LoRA 18 MB |
| Số tham số | ASR 241,7 triệu + MT 448,4 triệu | như B0 (LoRA gộp vào trọng số khi chạy) |

Âm thanh dài: ghép 20 bản thu thành 249 giây.

| | Có VAD | Không VAD |
|---|---|---|
| B0 | 11 đoạn, 76,5 s, RTF 0,307 | 1 khối, 109,4 s, RTF 0,439 |
| V2 | 11 đoạn, 71,5 s, RTF 0,287 | 1 khối, 100,7 s, RTF 0,404 |

V2 và B0 có cùng kiến trúc khi chạy (LoRA đã gộp vào trọng số), nên chênh lệch tốc độ giữa hai bản là dao động đo, không phải chi phí của LoRA.

## Đối chiếu tiêu chí khả thi

| Tiêu chí | Ngưỡng | V2 | Đạt? |
|---|---|---|---|
| Chất lượng dịch | Cao hơn B0 trên cascade, PhoMT giảm ≤ 1 | 27,57 so với 24,27; PhoMT −0,45 | ✅ |
| Tốc độ | RTF < 1 | 0,340 (âm thanh dài có VAD: 0,287) | ✅ |
| Độ trễ | Trung vị < 3 s/câu | 4,10 s cho câu trung bình 12,8 s | ❌ |
| Bộ nhớ | VRAM < 8 GB | 1,78 GB | ✅ |
| Âm thanh dài | Có VAD, xử lý vài phút | 249 s, 11 đoạn | ✅ |

**Kết luận: KHẢ THI** để làm demo ở Task 3 (web Gradio trên máy có GPU). Riêng độ trễ chưa đạt ngưỡng nhóm đặt ra;
vì độ trễ tỉ lệ với độ dài câu, ở chế độ micro cần cắt đoạn ngắn hơn bằng VAD và hiển thị kết quả theo từng đoạn.
Đây là việc cần giải quyết ở Task 3.

## Hạn chế đã biết

- Chưa thử micro điện thoại thật và chưa có tập test giọng nữ (FLEURS test 100% nam, VIVOS thu sạch).
- Số viết bằng chữ số thường bị ASR đọc thành chữ ("802" → "tám trăm linh hai").

## Kế hoạch Task 3

| Hạng mục | Nội dung |
|---|---|
| Demo (bắt buộc) | Gradio: tab tải file và tab micro; hiển thị song song chữ Việt và câu Anh kèm mốc thời gian; tự đổi tần số lấy mẫu |
| Real-time | Ghi âm theo đoạn, VAD cắt câu, hiển thị kết quả từng đoạn |
| API (điểm cộng) | FastAPI `/transcribe`, `/translate`, `/speech-translate`, có schema và xử lý lỗi |
| Đóng gói (điểm cộng) | Dockerfile, GitHub Actions (lint, test), deploy Hugging Face Spaces |
| Kiểm thử | Âm thanh dài, âm thanh có nhiễu, file sai định dạng, im lặng |
| Báo cáo cuối | 15–25 trang theo mục 6 projectdpl; video demo 2–5 phút |
