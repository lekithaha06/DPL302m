CHẤM OFFLINE ASR
Yêu cầu Python >=3.9, không cần cài thư viện bên ngoài. Script không huấn luyện, tải checkpoint hay suy luận.

Manifest JSONL độc lập do Kiệt xuất từ dữ liệu thật, mỗi dòng:
{"id":"recording_unique_id","reference":"nhãn raw gốc","sent_id":"ID câu nếu là FLEURS"}
Predictions JSONL, mỗi dòng:
{"id":"recording_unique_id","reference":"nhãn raw gốc","prediction":"text raw model", "run_fingerprint":"hash của cùng run", "sent_id":"ID câu"}
id phải là ID bản thu (file_name ở FLEURS), không phải sent_id vì nhiều bản thu dùng cùng câu.

Lệnh tại thư mục 01_BAO_ASR:
python scripts/score_asr.py --predictions DUONG_DAN_predictions.jsonl --manifest DUONG_DAN_manifest.jsonl --out ket_qua_moi --run-id KIET_RUN_THAT
Thư mục --out phải chưa tồn tại. Script xuất summary.json, per_utterance.csv, alignments.jsonl. Chặn thiếu/thừa/trùng ID, reference sai manifest, reference rỗng và nhiều run_fingerprint. Dự đoán rỗng tính deletion.

Kiểm tra scorer bằng fixture toán học (không phải kết quả model):
python -m unittest discover -s scripts -p test_score_asr.py -v

Chuẩn hóa NFC, lower, mọi ký tự Unicode loại P/S đổi thành space rồi collapse whitespace. Giữ dấu thanh và chữ số. CER dùng code point sau NFC, bỏ khoảng trắng. Không đổi hòa/hoà về cùng kiểu gõ. Whitespace WER gần đơn vị âm tiết, không tách từ ngôn ngữ học.
Corpus metric cộng edit và N, không lấy trung bình WER câu. WER có thể >100%. Tie-breaking H>S>D>I xác định; S/D/I có thể khác JiWER 3.0.5 khi có nhiều alignment tối ưu dù tổng edit và WER/CER giống. Chọn một scorer làm chính và ghi hash, không trộn counts từ các scorer.
Tone-only chỉ xét cặp substitution, bỏ đúng dấu thanh nhưng giữ ă â ê ô ơ ư đ; là gợi ý, không thay kiểm âm thanh. Proper name và number span do người đọc nhãn xác nhận. Script không tự kết luận các lỗi này.
Để chốt kết quả Task2 còn phải kiểm audio, model revision, resolved config, full audio coverage, environment và đo thời gian bằng code Kiệt. Đây là scorer tham chiếu, không thay inference pipeline.
