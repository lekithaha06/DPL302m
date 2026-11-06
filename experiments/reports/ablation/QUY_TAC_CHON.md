# Quy tắc chọn bản cuối (chốt TRƯỚC khi chạy ablation mới) – 03/11/2026 23:38

Áp cho mọi bản khối dịch: V1, V2, V3, V4 và các bản ablation A_r8, A_r32, A_aug. Chỉ dùng tập **DEV** (FLEURS dev, 361 bản thu); test chỉ xem sau khi đã chọn.

1. Tính BLEU dev cascade (dịch lời PhoWhisper của FLEURS dev, `runs/mt/<bản>/fleurs_dev_asr_pho/score.json`). Gọi M = giá trị cao nhất.
2. Nhóm "hoà": mọi bản có BLEU dev cascade ≥ M − 0,5 (0,5 BLEU ≈ mức chênh mà bootstrap trên test không phân biệt được giữa V1–V4).
3. Trong nhóm hoà, chọn bản có **BLEU dev dịch sạch** cao nhất (`fleurs_dev_clean`) – tiêu chí Task 1 "không làm giảm chất lượng dịch văn bản chuẩn".
4. Nếu vẫn bằng nhau (chênh < 0,01): chọn bản ít tham số huấn luyện hơn, rồi bản có tên đứng trước.

Ablation (chỉ đổi 1 yếu tố so với **V2**, bản đang thắng theo quy tắc này với V1–V4):
- A_r8: LoRA rank 8 (alpha = 2·rank = 16, giữ tỉ lệ alpha/rank như V2)
- A_r32: LoRA rank 32 (alpha = 64)
- A_aug: dữ liệu V2 + 2.926 cặp transcript SẠCH FLEURS train đổi sang dạng lời ASR (chữ thường, bỏ dấu câu) – chỉ dùng TRAIN, không chạm dev/test
Mọi thứ khác giữ như V2: lr 2e-4, batch 4×4, 5 epoch, warmup 6%, dropout 0,05, 6 lớp đích, seed 42, chọn epoch theo BLEU dev cascade.
