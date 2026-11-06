# Kiểm chứng số liệu Task 1

| Mục | Số ghi ở Task 1 | Script đếm lại | Kết quả |
|---|---|---|---|
| VIVOS train: số câu | 11660 | 11660 | khớp |
| VIVOS train: số người nói | 46 | 46 | khớp |
| VIVOS test: số câu | 760 | 760 | khớp |
| VIVOS test: số người nói | 19 | 19 | khớp |
| VIVOS train: số giờ (14:55) | 14.92 | 14.921 | khớp |
| VIVOS test: số phút | 44.76 | 44.76 | khớp |
| FLEURS vi_vn test: số bản thu | 857 | 857 | khớp |
| FLEURS vi_vn test: số câu gốc | 347 | 347 | khớp |
| FLEURS vi_vn test: số giờ | 3.0 | 3.0 | khớp |
| FLEURS vi_vn test: thời lượng TB (s) | 12.62 | 12.62 | khớp |
| FLEURS vi_vn test: dài nhất (s) | 38.1 | 38.1 | khớp |
| FLEURS vi_vn test: số bản thu nhãn MALE | 857 | 857 | khớp |
| FLEURS vi_vn test: số câu có câu Anh | 347 | 347 | khớp |
| PhoMT train: số cặp | 2977999 | 2977999 | khớp |
| PhoMT dev: số cặp | 18719 | 18719 | khớp |
| PhoMT test: số cặp | 19151 | 19151 | khớp |

## Cảnh báo (đưa vào bước làm sạch / mục hạn chế)

- FLEURS vi_vn train: 4 bản thu dài hơn 30 giây (Whisper cắt 30 s)
- FLEURS vi_vn train: 33 câu không có câu Anh trong en_us
- FLEURS vi_vn dev: 2 bản thu dài hơn 30 giây (Whisper cắt 30 s)
- FLEURS vi_vn dev: 100% bản thu cùng nhãn giới tính MALE
- FLEURS vi_vn test: 7 bản thu dài hơn 30 giây (Whisper cắt 30 s)
- FLEURS vi_vn test: 100% bản thu cùng nhãn giới tính MALE
