# Gán nhãn loại lỗi: tiêu chí và cách làm (Task 2, mục 1.2)

**Người gán:** Hồ Lâm Bảo Đăng và Bùi Ngọc Phương Uyên, **mỗi người làm độc lập**, không xem hay bàn kết quả của nhau trước khi cả hai gán xong.
**Dữ liệu:** 100 câu FLEURS dev (`items.csv`), chọn tự động: mỗi câu gốc một bản thu, chỉ câu mà baseline B0 nghe sai hoặc dịch kém, seed 42 (`selection.json`).
Không dùng tập test.

## Mỗi dòng có

| Cột | Nội dung |
|---|---|
| `cau_dung_vi` | Câu tiếng Việt đúng (nhãn gốc FLEURS) |
| `may_nghe_vi` | Chữ PhoWhisper-small nghe ra |
| `tham_chieu_en` | Câu tiếng Anh tham chiếu |
| `ban_dich_B0` | Bản dịch của B0 (dịch chữ máy nghe) |

Có thể nghe lại âm thanh: `data/fleurs_audio/dev/<audio>`.

## Năm loại lỗi (một câu có thể có nhiều loại; ghi **1** vào cột nếu có, để trống nếu không)

| Cột | Ghi 1 khi | Ví dụ |
|---|---|---|
| `sai_dau_thanh` | Máy nghe đúng âm tiết nhưng sai dấu thanh, ít nhất một chỗ | "bảo" → "báo"; "kho báu" → "kho báo" |
| `ten_rieng` | Tên người, địa danh, tổ chức bị nghe sai hoặc dịch sai | "Aristotle" → "erik stone" |
| `so` | Số, năm, đơn vị bị nghe sai, đọc thành chữ, hoặc bản dịch sai số | "802.11" → "tám trăm linh hai chấm mười một"; "1966" dịch thành "1600" |
| `thieu_thua_tu` | Máy nghe thiếu hoặc thừa từ có nghĩa (không tính dấu câu) | bỏ mất "nhất thiết" |
| `sai_nghia_dich` | Bản dịch B0 sai nghĩa chính của câu so với tham chiếu (không tính khác từ đồng nghĩa) | "treasure map" thành "newspaper inventory map" |

**Quy tắc chung**
- Chỉ so với `cau_dung_vi` và `tham_chieu_en`; không đoán ý người nói.
- Viết hoa/thường, dấu câu, cách viết số khác nhau nhưng **cùng giá trị** ("2,4" và "2.4") không tính là lỗi.
- Không chắc thì để trống và ghi lý do vào `ghi_chu`.

## Cách làm

**Cách 1 (Excel):** Đăng mở `annotator_Dang.csv`, Uyên mở `annotator_Uyen.csv`, điền 1 vào các cột lỗi, lưu lại dạng CSV UTF-8.

**Cách 2 (Label Studio):** tạo project, dán cấu hình `label_studio_config.xml`, import `label_studio_tasks.json`, gán xong thì export JSON.

**Tính Kappa** (sau khi cả hai xong):

```
python src/data/compute_kappa.py reports/task2/labeling/annotator_Dang.csv reports/task2/labeling/annotator_Uyen.csv
```

Kết quả ghi vào `kappa.json`: Cohen's Kappa cho từng loại lỗi, Kappa trung bình, tỉ lệ đồng ý.
Dựng lại slide thì slide 5 tự điền số. Sau đó hai người **thống nhất lại các câu lệch** để có bộ nhãn cuối dùng cho phân tích lỗi.

Thang đọc Kappa (Landis & Koch, 1977): dưới 0,2 thấp · 0,21–0,4 khá · 0,41–0,6 trung bình · 0,61–0,8 tốt · trên 0,8 rất tốt.
