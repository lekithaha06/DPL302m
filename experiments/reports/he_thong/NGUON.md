# Số đo hệ thống (sản phẩm) – nguồn

Chép nguyên từ gói sản phẩm cuối `fix.zip` của Đăng (giải nén `teamwork/kiem_fix/goc`), do nhóm chạy trên RTX 4060 ngày 03/11/2026
bằng `kiem_fix/goc/CHAY_TREN_GPU.ipynb`:
- `ket_qua.json`, `bang.md`, `du_doan_*.jsonl` ← `kiem_fix/goc/danh_gia/20261103_152808/` (`tests/danh_gia_proposed.py --tap test`, 857 bản FLEURS test)
- `nghiem_thu/` ← `kiem_fix/goc/nghiem_thu/20261103_161128/` (`tests/nghiem_thu_that.py`, 3 file FLEURS dev thay thế cho audio tự thu)
- `ban_chot.json` ← `kiem_fix/goc/configs/ban_chot.json` (nhóm chốt V4)
- `bootstrap_cu_vs_moi.json` ← `scripts/he_thong_bootstrap.py` (tính lại từ 2 file du_doan ở trên, không chạy model)

Hệ: PhoWhisper-small @a86b604c + VinAI Translate vi2en-v2 @ae7baa85 + LoRA V4/best (trùng hash task3/checkpoints/V4/best) +
tiền/hậu xử lý của sản phẩm. `truoc_0411` = cách xử lý cũ (cắt giữa, không bỏ lặp, không đổi số); `proposed` = bản cuối.
