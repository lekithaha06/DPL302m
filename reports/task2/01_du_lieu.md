# Task 2 · Phần I: Xử lý và phân tích dữ liệu

Nguồn số liệu: `reports/task2/data/data_stats.json` (sinh bởi `src/data/clean_eda.py`), `data/fleurs/…/*.tsv`, PhoMT detokenization.
Mọi số dưới đây là số đếm trực tiếp từ dữ liệu đã tải ngày 22/10/2026.

## 1.1. Thống kê nguồn dữ liệu

| Nguồn | Loại | URL / cách thu thập | Số mẫu dùng | Định dạng | Dung lượng (trên đĩa) | Các trường dữ liệu | License |
|---|---|---|---|---|---|---|---|
| FLEURS vi_vn + en_us | Online (dataset công khai) | huggingface.co/datasets/google/fleurs, `data/download_fleurs.py` | train 2.994 / dev 361 / test 857 bản thu | WAV 16 kHz mono + TSV | 1.994,5 / 262,4 / 660,1 MB (WAV) | id câu FLoRes, tên file, transcript gốc, transcript chuẩn hóa, ký tự, số mẫu âm thanh, giới tính | CC BY 4.0 |
| VIVOS (test) | Online | huggingface.co/datasets/AILAB-VNUHCM/vivos, `data/prepare_vivos.py` | 760 câu, 19 người nói | WAV 16 kHz + văn bản | 82,0 MB | mã câu, mã người nói, transcript | CC BY-NC-SA 4.0 |
| PhoMT | Online (gated) | huggingface.co/datasets/vinai/PhoMT (xin quyền) | 2.977.999 / 18.719 / 19.151 cặp | TXT song song .vi/.en | 501,4 MB (detokenization) | câu Việt, câu Anh (theo dòng) | Chỉ nghiên cứu, cấm phân phối lại |
| Dữ liệu tự thu | Offline | **Không thu thập** | 0 | — | — | — | — |

Lý do không thu offline: projectdpl cho phép dùng dataset công khai, tự build tập test chỉ là khuyến khích. Hạn chế đi kèm: chưa thử micro điện thoại thật.

## 1.2. Làm sạch và gán nhãn

Quy trình (áp dụng cho từng tập FLEURS, đếm số mẫu còn lại sau mỗi bước):

| Bước | Train | Dev | Test |
|---|---|---|---|
| Dữ liệu gốc (vi_vn TSV) | 2.994 | 361 | 857 |
| Có câu tiếng Anh tham chiếu cùng ID (en_us) | **2.927** (loại 67) | 361 | 857 |
| Transcript không rỗng (missing) | 2.927 | 361 | 857 |
| Âm thanh đọc được, không rỗng (lỗi file) | 2.927 | 361 | 857 |
| Không trùng file âm thanh (hash SHA-1, duplicate) | 2.927 | 361 | 857 |
| Tần số lấy mẫu | 100% 16 kHz | 100% 16 kHz | 100% 16 kHz |

- Chuẩn hóa văn bản khi chấm WER/CER: NFC, viết thường, dấu câu và ký hiệu → khoảng trắng, **giữ dấu tiếng Việt**, không đổi số thành chữ.
- Nhiễu và mẫu khó **không bị loại** mà giữ lại để phân tích lỗi (4 bản thu train và 2 dev dài hơn 30 giây vẫn giữ).
- Gán nhãn: dùng **nhãn gốc** của dataset (transcript tiếng Việt, câu tiếng Anh FLoRes) để train và chấm.
- Gán nhãn loại lỗi cho phân tích lỗi: 100 câu FLEURS dev (chọn tự động, seed 42) mà B0 nghe sai hoặc dịch kém, gán **tự động theo quy tắc cố định**
  (`src/data/auto_label_errors.py`, tiêu chí trong `reports/task2/labeling/TIEU_CHI_GAN_NHAN.md`): tên riêng sai 43 câu, bản dịch sai nghĩa
  (chrF++ < 40) 31, thiếu/thừa từ 26, sai dấu thanh 21, số sai 17; 73/100 câu có ít nhất một lỗi. Chỉ có một quy trình gán nên **không tính
  Cohen's Kappa** (đề: "nếu có sử dụng"). Bộ file để hai người gán tay và script tính Kappa vẫn có sẵn nếu nhóm muốn bổ sung.
- Chống leakage: chia theo **ID câu**; đã kiểm train–dev, train–test, dev–test: **0 ID trùng, 0 câu trùng nội dung**. Task 1 đã kiểm FLEURS test với toàn bộ PhoMT: 0 câu trùng.

## 1.3. Thống kê mô tả và mất cân bằng

| | Train | Dev | Test |
|---|---|---|---|
| Bản thu | 2.927 | 361 | 857 |
| Câu gốc | 1.449 | 149 | 347 |
| Tổng giờ | 8,86 | 1,19 | 3,00 |
| Độ dài trung bình / trung vị (giây) | 10,90 / 10,38 | 11,91 / 11,16 | 12,62 |
| Tỉ lệ bản thu | **70,6%** | **8,7%** | **20,7%** |

Nhận xét định lượng:
- **Giới tính lệch giữa các tập:** train có **2.175 bản thu nữ (74,3%)** và 752 nam (25,7%); dev và test **100% nam**. Mô hình dạy trên dữ liệu đa số giọng nữ nhưng được chấm trên toàn giọng nam.
- **Số bản thu mỗi câu không đều (train):** 285 câu có 1 bản thu, 850 câu có 2, 314 câu có 3. Câu có 2–3 bản thu chiếm **90,3%** số bản thu (2.642/2.927).
- **Độ dài:** 1.533 bản thu train (52,4%) dài 10–20 giây, chỉ 63 (2,2%) dưới 5 giây.
- **VIVOS test:** 19 người nói, mỗi người đúng 40 câu, cân bằng; trung bình 3,53 giây/câu.
- **PhoMT:** 51,4% train là phụ đề phim OpenSubtitles (theo paper PhoMT, Table 1).
- Tỉ lệ chia FLEURS là 70,6/8,7/20,7 theo cách chia gốc của dataset; nhóm giữ nguyên để kết quả so được với công bố và tránh leakage, không ép về 80/10/10.

Hình: `data/figures/fleurs_split.png`, `fleurs_gender.png`, `fleurs_duration.png`.

## 1.4. Xử lý mất cân bằng

- **Cân bằng theo câu:** gán trọng số 1/k cho mỗi bản thu của câu có k bản thu, để mỗi câu gốc đóng góp như nhau. Trước: nhóm câu 2 bản thu chiếm 1.700 bản thu; sau: tổng trọng số 850 (hình `fleurs_sentence_balance.png`).
- Không dùng augmentation âm thanh vì nhóm không train khối nghe.
- Lệch giới tính train/test: không sửa được bằng lấy mẫu vì test không có giọng nữ; ghi là hạn chế.
- **Kết quả đo (V2b = V2 + cân bằng theo câu, mọi thứ khác giữ nguyên):** FLEURS dev BLEU 26,98 so với V2 27,17;
  cascade FLEURS test 26,85 so với V2 27,57; PhoMT dev 40,93 so với V2 40,80. **Cân bằng theo câu không cải thiện khối dịch**
  nên không được dùng trong bản cuối. Lý do hợp lý: các bản thu khác nhau của cùng một câu cho ra lỗi nghe khác nhau,
  nên chúng là dữ liệu bổ sung có ích, không phải dữ liệu trùng; hạ trọng số chúng làm mất bớt sự đa dạng của lỗi nghe.
