CẤU HÌNH ASR DỰ KIẾN
Đọc asr_protocol.json và mục 3 của báo cáo. Đây là đặc tả; không phải config đã chạy Task2.

Tải model/processor/tokenizer/generation_config cùng revision. Dùng model.eval(), torch.inference_mode(). Kiệt ghi tất cả generation kwargs và giá trị resolved; không chỉ ghi tên checkpoint.
Transformers dùng num_beams, không phải beam_size của faster-whisper. Tên chính xác cho long-form là condition_on_prev_tokens, không dùng condition_on_previous_text của backend khác.
Audio <=30s: processor truncation=False, padding=max_length, sampling_rate=16000, return_attention_mask=True; generate return_timestamps=False, language=vi, task=transcribe, num_beams=5, do_sample=False.
Audio >30s: processor truncation=False, padding=longest, sampling_rate=16000, return_attention_mask=True; generate return_timestamps=True, condition_on_prev_tokens=False và các giá trị chung. Không ép prompt no_timestamps cho nhánh này. Ghép text toàn bộ segment, lưu coverage để kiểm 7 FLEURS test dài.
Đây là thiết kế dựa API Transformers4.44.2; Kiệt phải smoke test trên dev và xuất code thực chạy. Nếu thay version/backend, dùng run_id và config riêng.
Common suppression: dùng hai mảng trong common_suppression_from_task1.json cho cả hai model; ghi hash. Không bổ sung tên riêng hoặc số từ test vào prompt.
Token cap440 tính từng segment. Log số token và mọi mẫu chạm cap. Không bỏ output dài hoặc prediction rỗng vì làm metric đẹp.
LR, optimizer, epochs là N/A cho baseline inference. Không gán các thông số huấn luyện của paper thành cấu hình inference của nhóm.
