# Quy tắc xử lý 3 seed (ghi TRƯỚC khi train seed mới) – 04/11/2026

Seed: 42 (đã có, chạy trên RTX 4060), 1 và 2 (mới, chạy trên Modal). Phạm vi: V1, V2, V3, V4. Ablation A_r8, A_r32, A_aug giữ 1 seed và ghi rõ.
Cấu hình mỗi bản giữ nguyên như seed 42: 5 epoch, batch 4 × 4, chọn epoch theo BLEU dev cascade. Chỉ đổi seed huấn luyện; dữ liệu train giữ nguyên.
V4 dùng dữ liệu của V3 như seed 42, không xét lại nhánh chọn gốc V2/V3.

1. Báo cáo trung bình ± độ lệch chuẩn (mẫu, n = 3) của dev cascade, dev sạch, test cascade, test sạch, Whisper → dịch. PhoMT test không chạy lại, giữ 1 seed.
2. Bản cuối và demo vẫn là V2 seed 42 (quyết định đã chốt, không đổi theo kết quả 3 seed).
3. Áp lại quy tắc DEV trên trung bình 3 seed như phân tích độ nhạy. Nếu ra bản khác V2 thì ghi rõ trong tài liệu, không đổi bản cuối.
4. Không bỏ seed nào, không chọn seed đẹp. Seed lỗi kỹ thuật thì chạy lại đúng seed đó và ghi lại.
5. Khác phần cứng: thêm 1 job V2 seed 42 trên Modal để đo chênh lệch do máy; job này không tính vào trung bình.
6. Môi trường: train trên RTX PRO 6000 với torch 2.7.1 (GPU này không chạy được torch 2.0.1). Dịch và chấm trên T4 với torch 2.0.1, đúng môi trường seed 42: adapter V2 seed 42 dịch dev ra 26,45, khớp máy nhóm; cùng adapter trên torch 2.7.1 ra 26,24 nên không chấm bằng torch 2.7.1. Chọn epoch trong lúc train vẫn chạy trên torch 2.7.1.
7. Bổ sung 04/11 sau khi đã có số V1–V4: ablation A_r8, A_r32, A_aug cũng chạy seed 1 và 2 theo yêu cầu, cùng cách train và chấm như trên. Thay cho câu "giữ 1 seed" ở đầu file. Bản cuối vẫn là V2, ablation không tham gia chọn lại.
