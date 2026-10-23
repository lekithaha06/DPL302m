# Task 2 · Phần II: Thực nghiệm hai Baseline

Nguồn số liệu: `reports/task2/asr/baseline_asr.json`, `reports/task2/asr/asr_errors.json`, `reports/task2/mt/eval_B0.json`.

## 2.1. Môi trường thực nghiệm (đồng nhất cho cả hai baseline và V1 → Vn)

| Thành phần | Giá trị |
|---|---|
| Phần cứng | NVIDIA GeForce RTX 4060 Laptop GPU 8 GB (một máy cho mọi số so sánh) |
| Phần mềm | Python 3.11, PyTorch 2.6.0+cu124, Transformers 5.17.0, PEFT 0.21.2, sacreBLEU 2.6.0, jiwer 4.0.0 |
| Seed | 42 |
| Độ chính xác | FP16 khi suy luận |
| Baseline A (ASR) | PhoWhisper-small, Whisper-small; beam 5, batch 1, ngôn ngữ vi, max_new_tokens 440 |
| Baseline B (MT) | VinAI Translate vi2en (bản của paper); beam 5, max_length 512 |
| Learning rate / optimizer / epochs | **Không áp dụng cho baseline**: cả hai là mô hình công bố chạy zero-shot, không train thêm. Siêu tham số train nằm ở bảng V1 → Vn |

So với Task 1, Baseline A chuyển từ RTX 3050 (torch 2.0.1, transformers 4.44) sang **cùng máy và cùng thư viện với Baseline B**.

## 2.2. Paper và thực nghiệm của nhóm

| Mô hình | Nguồn | Dataset | WER | CER | BLEU | chrF++ |
|---|---|---|---|---|---|---|
| PhoWhisper-small (A) | Paper (PhoWhisper, Table 2) | VIVOS test | 6,33 | – | – | – |
| PhoWhisper-small (A) | Nhóm | VIVOS test (760) | **6,25** | 3,26 | – | – |
| PhoWhisper-small (A) | Nhóm | FLEURS test (857) | 12,29 | 8,68 | – | – |
| Whisper-small (đối chứng zero-shot) | Nhóm | VIVOS test | 22,26 | 13,15 | – | – |
| Whisper-small (đối chứng zero-shot) | Nhóm | FLEURS test (857) | 21,42 | 12,56 | – | – |
| VinAI Translate (B) | Paper (Interspeech 2022, Table 1) | PhoMT test | – | – | 40,42 | – |
| VinAI Translate (B) | Nhóm | PhoMT test (19.151) | – | – | **40,27** | 60,32 |
| B, dịch chữ chuẩn | Nhóm | FLEURS test | – | – | 37,85 | 61,16 |
| **Cascade A → B (B0)** | Nhóm | FLEURS test | – | – | **24,27** | 50,12 |

Tách lỗi WER (PhoWhisper-small, cùng script đánh giá): VIVOS: thay thế 447, xóa 22, chèn 14 trên 7.722 từ; FLEURS: thay thế 2.057, xóa 136, chèn 1.006. Whisper-small trên FLEURS: thay thế 4.645, xóa 399, chèn 529.

Hai số FLEURS của PhoWhisper: 12,29 / 8,68 từ script đánh giá ASR (beam 5, giống VIVOS) và 12,21 / 8,58 từ chữ máy nghe dùng trong cascade (pipeline Transformers, cấu hình mặc định). Bảng baseline dùng số của script đánh giá; cascade dùng đúng chữ máy nghe của pipeline. Lưu ý: 7 bản thu FLEURS test dài hơn 30 giây bị cắt ở 30 giây khi chấm bằng script đánh giá (giới hạn đầu vào của Whisper).

## 2.3. Gap Analysis

**Kết quả có khớp công bố không?** Có.
- PhoWhisper-small: 6,25% so với 6,33% (chênh 0,08). Chạy lại trên máy và thư viện mới, **760/760 câu cho kết quả giống hệt Task 1**.
- VinAI Translate: 40,27 so với 40,42 (chênh 0,15). Task 1 ra 40,25 với cách gom câu cũ; chênh 0,02 chỉ do gom câu.

**Nguyên nhân các chênh lệch:**
1. **Domain gap (dataset):** PhoWhisper được tác giả fine-tune trên VIVOS train nên VIVOS là cùng miền (6,25%). Trên FLEURS (ngoài miền, câu dài 12,62 giây so với 3,53 giây, đọc văn bản Wikipedia) WER tăng lên 12,29%. Bằng chứng thêm: trên VIVOS PhoWhisper hơn Whisper-small 16,0 điểm WER (6,25 so với 22,26), trên FLEURS chỉ hơn 9,1 điểm (12,29 so với 21,42), tức một phần lợi thế của PhoWhisper trên VIVOS là lợi thế cùng miền.
2. **Tiền xử lý / chuẩn hóa:** phần lớn 1.007 lỗi chèn trên FLEURS là **số bị đọc thành chữ**. Ví dụ câu đúng "802.11a", máy nghe "tám trăm linh hai chấm mười một a"; các từ bị chèn nhiều nhất là "một" (75), "hai" (61), "trăm" (57), "mươi" (39). Nhóm không đổi số thành chữ khi chấm, nên WER FLEURS bị đội lên một phần do khác cách viết.
3. **Cấu hình giải mã và môi trường:** Whisper-small đổi từ 25,91% (Task 1) sang 22,26%. Kiểm tra cho thấy 750/760 câu giống hệt nhau; khác biệt chính đến từ câu `VIVOSDEV03_R193` (câu đúng 2 từ): Task 1 sinh lặp 293 từ, lần này 4 từ. Bỏ câu này, hai lần chạy là 22,12% và 22,22%.
4. **Cách gom câu khi dịch:** Task 1 ra 24,27 / 37,89 (cascade / chữ chuẩn). Lần chấm đầu của Task 2 (lô 32 câu) ra 24,21 / 37,82; khi đổi sang lô 16/8/4 và giới hạn độ dài ra (để tránh tràn bộ nhớ ở V1) ra 24,27 / 37,85. Chênh dưới 0,1 điểm do padding trong beam search. Mọi phiên bản V được chấm bằng đúng cấu hình cuối, với B0 = 24,27.

## Phân tích lỗi ASR (dùng cho failure cases)

| | VIVOS | FLEURS |
|---|---|---|
| Lỗi thay thế chỉ sai dấu thanh | 54 (12,1% số lỗi thay thế) | 118 (5,7%) |
| Cặp nhầm dấu nhiều nhất | huyền → nặng (15), nặng → hỏi (14), ngã → hỏi (14) | ngang → sắc (133), ngang → huyền (61) |
| WER theo độ dài (VIVOS) | <3 s: 8,60% · 3–5 s: 5,23% · ≥5 s: 8,56% | – |
| WER theo người nói (VIVOS) | thấp nhất 0,78% (VIVOSDEV19), cao nhất 24,93% (VIVOSDEV10) | – |

Hình: `asr/tone_confusion_VIVOS.png`, `asr/tone_confusion_FLEURS.png`.

Ảnh hưởng của lỗi nghe lên bản dịch (B0, FLEURS test, chia theo WER từng câu): câu nghe đúng hoàn toàn BLEU 29,89; WER 0–10%: 26,75; WER 10–30%: 21,50; WER >30%: 10,57. Câu có chữ số: 18,03.
