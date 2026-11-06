# Bộ 20 câu tự thu: số, ngày tháng, tên riêng, thuật ngữ

Mỗi người trong nhóm đọc 20 câu trong `cau.jsonl` (đọc số như nói bình thường, ví dụ "ngày mười một tháng ba năm hai nghìn không trăm hai mươi sáu"), lưu thành `01.wav` … `20.wav` trong thư mục này hoặc thư mục con theo tên người. Sau đó chạy:

```
python tests/danh_gia_proposed.py --tu_thu tests/bo_cau_tu_thu
```

Bảng ra tách WER/CER theo nhóm (`so_ngay`, `so_luong`, `ten_rieng`, `thuat_ngu`) cho cả hai cấu hình, cách xử lý cũ và Proposed. Bản dịch tham chiếu tiếng Anh là do nhóm tự viết, nên BLEU trên bộ này chỉ để tham khảo.
