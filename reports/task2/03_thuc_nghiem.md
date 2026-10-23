# Task 2 · Phần III: Proposed Method V1 → Vn

Nguồn số liệu: `reports/task2/mt/eval_*.json`, `train_log_*.jsonl`, `train_config_*.json`, `mt_errors_*.json`,
`significance_*.json`, `phomt_dev_selection.json`, `reports/task2/ablation.md`, `NHAT_KY_THUC_NGHIEM.md`.
Mọi phiên bản chấm bằng cùng `src/mt/eval_mt.py`: FP16, beam 5, độ dài ra tối đa min(512, 2 × token nguồn + 10),
lô 16/8/4 theo độ dài, cùng tập test. Chọn epoch và chọn phiên bản cuối chỉ trên tập dev.

## 3.1. V1: LoRA cho khối dịch trên chữ máy nghe

**Ý tưởng:** VinAI Translate chỉ được dạy trên chữ sạch nên dịch kém khi gặp lỗi nghe (cascade 24,27 so với dịch chữ chuẩn 37,85).
V1 dạy thêm khối dịch bằng LoRA trên các cặp *(chữ do PhoWhisper nghe ra từ FLEURS train → câu Anh tham chiếu)*. Khối nghe giữ nguyên.

| Siêu tham số | Giá trị |
|---|---|
| Dữ liệu train / dev | 2.927 cặp (FLEURS train, chữ máy nghe, WER 11,35%) / 361 cặp (FLEURS dev, chữ máy nghe, WER 11,32%) |
| LoRA | r = 16, alpha = 32, dropout 0,05, gắn vào q/k/v/out_proj |
| Tham số train | 4.718.592 / 453.144.576 (1,04%); adapter 18 MB |
| Optimizer | AdamW, learning rate 2e-4, warmup 6%, giảm tuyến tính, weight decay 0 |
| Batch | 8 × tích lũy 2 = 16; bf16 autocast; clip gradient 1,0; seed 42 |
| Epoch | tối đa 5, giữ epoch có BLEU dev cao nhất |
| Thời gian train | khoảng 5 phút/epoch (RTX 4060 Laptop) |

| Epoch V1 | Train loss | Dev loss | Dev BLEU |
|---|---|---|---|
| 0 (chưa train = Baseline B) | – | 1,717 | 24,65 |
| **1 (chọn)** | 1,478 | **1,476** | **27,49** |
| 2 | 1,259 | 1,491 | 26,93 |
| 3 | 1,103 | 1,533 | 26,76 |
| 4 | 0,978 | 1,591 | 25,85 |

Từ epoch 2, train loss giảm tiếp nhưng dev loss tăng: **overfit** vì dữ liệu dạy nhỏ.

**Kết quả trên test:**

| | B0 | V1 |
|---|---|---|
| BLEU cascade FLEURS test (chỉ số chính) | 24,27 | **28,59** (+4,32) |
| chrF++ cascade | 50,12 | 52,82 |
| BLEU dịch chữ chuẩn FLEURS | 37,85 | 37,31 |
| BLEU PhoMT test | 40,27 | 37,90 (−2,37) |

Tín hiệu cải thiện: **có**, trên chỉ số chính. Mặt trái: quên một phần khả năng dịch văn bản sạch (PhoMT −2,37).

## 3.2. Failure cases của V1

BLEU theo nhóm câu (FLEURS test, chia theo WER của câu đầu vào):

| Nhóm | Số câu | B0 | V1 | V2 |
|---|---|---|---|---|
| Nghe đúng hoàn toàn | 183 | 30,10 | 35,72 | 33,93 |
| WER 0–10% | 283 | 26,80 | 30,82 | 29,79 |
| WER 10–30% | 306 | 21,53 | 24,64 | 23,82 |
| WER >30% | 85 | 10,55 | **19,35** | 18,07 |
| Câu có chữ số | 171 | 17,98 | **25,07** | 24,11 |
| Câu không có chữ số | 686 | 25,53 | 29,37 | 28,39 |

So từng câu với B0 (chrF++ chênh trên 1 điểm): V1 tốt lên 444 câu, kém đi 244, như cũ 169.

Nguyên nhân lỗi chính của V1:
1. **Số đọc thành chữ gây sinh lặp:** câu "chuẩn tám không hai chấm một một … hai chấm bốn đi ra hệ" (đúng: *The 802.11n standard operates on both the 2.4Ghz and 5.0Ghz frequencies*). V1 sinh lặp "one, one, two, one…" tới giới hạn độ dài. Đây là lý do thêm giới hạn độ dài ra khi chấm, áp dụng như nhau cho mọi phiên bản.
2. **Bỏ sót, đơn giản hóa ý:** "không nhất thiết phải cần" → V1 bỏ *necessarily*; "quần đảo" → *islands* thay vì *archipelagos*.
3. **Quên văn bản sạch:** BLEU PhoMT giảm 2,37 vì chỉ dạy trên FLEURS.
4. **Một phần cải thiện là thích nghi miền:** câu nghe đúng hoàn toàn cũng tăng 5,62 BLEU, tức V1 còn quen văn phong FLEURS và kiểu chữ PhoWhisper xuất ra, không chỉ chịu được lỗi nghe.

## 3.3. V2 và bảng tiến trình

**V2** (từ lỗi 3 và overfit): chỉ đổi dữ liệu dạy. Thêm 1.449 cặp chữ chuẩn FLEURS train và 3.000 cặp PhoMT train (lấy ngẫu nhiên, seed 42), tổng 7.376 cặp; giữ nguyên mọi siêu tham số, tối đa 3 epoch.

| Epoch V2 | Train loss | Dev loss | Dev BLEU |
|---|---|---|---|
| 0 | – | 1,717 | 24,65 |
| **1 (chọn)** | 1,160 | **1,491** | **27,17** |
| 2 | 0,983 | 1,524 | 26,98 |
| 3 | 0,860 | 1,584 | 27,04 |

| Phiên bản | Thay đổi so với bản trước | Lý do (từ phân tích lỗi) | BLEU cascade | BLEU PhoMT | Nhận xét |
|---|---|---|---|---|---|
| B0 | – | Baseline A → B | 24,27 | 40,27 | Mốc so sánh |
| V1 | LoRA trên 2.927 cặp chữ máy nghe | Khối dịch chưa từng thấy lỗi nghe | **28,59** | 37,90 | Cải thiện mạnh nhất nhưng quên văn bản sạch |
| V2 | + 1.449 cặp chữ chuẩn + 3.000 cặp PhoMT | V1 overfit và quên (PhoMT −2,37) | 27,57 | 39,80 | Giữ +3,30 BLEU, PhoMT chỉ −0,47 |
| V2b | V2 + lấy mẫu cân bằng theo câu (trọng số 1/k cho câu có k bản thu) | Mất cân bằng số bản thu mỗi câu (mục 1.3) | 26,85 | – (PhoMT dev 40,93) | Không hơn V2 trên dev (26,98 so với 27,17) nên không nhận |
| V3a | V2 + chuẩn hóa số (`src/text/itn_vi.py`) chỉ ở lúc dịch, không train lại | Lỗi lặp và sai số ở câu nhiều số | không chấm test | – | FLEURS dev giảm 27,29 → 27,17 nên không nhận |
| **V3** | Chuẩn hóa số **cả khi dạy lẫn khi dịch** (train lại với dữ liệu như V2) | V3a: đầu vào lúc dịch lệch so với lúc dạy | **27,75** | **39,86** (−0,41) | FLEURS dev 27,29 → 27,56, PhoMT dev 41,16: **nhận, bản cuối** |

**V3a thất bại cho ra hướng đúng.** V2 được dạy trên chữ máy nghe, trong đó số vẫn viết bằng chữ, nên đổi sang chữ số chỉ ở lúc dịch
làm đầu vào lệch so với lúc dạy. V3 chuẩn hóa số cả dữ liệu dạy (622/2.927 câu train, 64/361 câu dev bị đổi) lẫn đầu vào lúc dịch
(174/857 câu test). Bộ chuẩn hóa không đổi nhầm từ thường ("một hệ thống", "năm nay", "hàng trăm người").
Ngay ở epoch 0 (chưa train), mô hình gốc đã dịch chữ đã chuẩn hóa tốt hơn (dev BLEU 25,55 so với 24,65).

| Epoch V3 | Train loss | Dev loss | Dev BLEU |
|---|---|---|---|
| 0 | – | 1,695 | 25,55 |
| **1 (chọn)** | 1,150 | **1,485** | **27,61** |
| 2 | 0,980 | 1,520 | 26,98 |
| 3 | 0,859 | 1,579 | 26,49 |

**V3 cải thiện đúng chỗ nó nhắm tới** (FLEURS test, so với V2): câu có chữ số 24,11 → **25,17** (+1,06); câu không có chữ số
28,39 → 28,45 (gần như không đổi); câu nghe sai nặng (WER >30%) 18,07 → 19,14. Từng câu: V3 tốt lên 249, kém đi 196, như cũ 412
(`mt/mt_errors_V3_vs_V2.json`).

**Failure case của V1 được V3 sửa** (chọn tự động trong `system/visual_results.md`):
máy nghe "chuẩn tám không hai chấm một một n hoạt động trên cả hai tần số hai chấm bốn …";
B0 "standard eight zeros two dots one one one n works on both frequencies two dots four …";
V1 sinh lặp "one, one, two, one…"; **V3 "The 802.11 n standard operates on both 2.4 GHz and 5.0 GHz frequencies."**
(tham chiếu: "The 802.11n standard operates on both the 2.4Ghz and 5.0Ghz frequencies.").

**Chọn phiên bản cuối trên validation (không dùng test):** quy tắc đặt trước là BLEU dev FLEURS cao nhất trong các phiên bản
có BLEU PhoMT dev không giảm quá 1 điểm so với B0. Trên 2.000 câu PhoMT dev (seed 42): B0 40,96; V1 38,98 (−1,98, loại);
V2 40,80 (−0,16, đạt); V3 41,16 (+0,20, đạt). Trên FLEURS dev (cùng script `eval_dev.py`): V2 27,29, V3 27,56.
**Phiên bản cuối: V3.** Kết luận này trùng với kết quả trên test.

**Cải thiện có thật hay do may?** Paired bootstrap (Koehn, 2004), 1.000 lần lấy mẫu lại theo cụm câu gốc
(857 bản thu thuộc 347 câu nên lấy cả cụm cho chặt), seed 42, trên cascade FLEURS test:

| So sánh | ΔBLEU trung bình | Khoảng tin cậy 95% | p | ΔchrF++ | Khoảng tin cậy 95% | p |
|---|---|---|---|---|---|---|
| V1 so với B0 | +4,36 | [+3,19; +5,48] | < 0,001 | +2,71 | [+2,02; +3,43] | < 0,001 |
| V2 so với B0 | +3,28 | [+2,11; +4,49] | < 0,001 | +2,33 | [+1,57; +3,04] | < 0,001 |
| V2b so với B0 | +2,59 | [+1,61; +3,64] | < 0,001 | +2,01 | [+1,38; +2,68] | < 0,001 |
| **V3 so với B0** | **+3,49** | **[+2,34; +4,70]** | < 0,001 | +2,47 | [+1,69; +3,22] | < 0,001 |

Không lần lấy mẫu nào V1, V2, V2b hay V3 thua B0, nên cải thiện là có ý nghĩa thống kê.
File: `mt/significance_V1_vs_B0.json`, `mt/significance_V2_vs_B0.json`.
