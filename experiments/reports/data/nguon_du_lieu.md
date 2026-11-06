# Bảng nguồn dữ liệu (slide 3, mục 1.1)

| Nguồn | Loại | URL / Cách thu thập | Số lượng mẫu | Định dạng file | Dung lượng (MB) | Các trường dữ liệu | Giấy phép |
|---|---|---|---|---|---|---|---|
| VIVOS | Online (public) | https://huggingface.co/datasets/AILAB-VNUHCM/vivos (gốc: zenodo.org/record/7068130) | train 11.660 câu / 46 người nói; test 760 câu / 19 người nói; 14.921 + 0.746 giờ | WAV trong vivos.tar.gz + prompts .txt.gz (16000 Hz) | 1406.5 | speaker_id, path, audio (wav), sentence; giới tính theo người nói (genders.txt) | ['cc-by-nc-sa-4.0'] |
| FLEURS vi_vn | Online (public) | https://huggingface.co/datasets/google/fleurs (thư mục data/vi_vn) | train 2.994 bản thu / 1.482 câu, 9.076 giờ; dev 361 bản thu / 149 câu, 1.194 giờ; test 857 bản thu / 347 câu, 3.004 giờ | WAV trong audio/{split}.tar.gz + TSV (16000 Hz) | 2259.1 | id (ID câu FLoRes), file_name, raw_transcription, transcription, phonemes (trống), num_samples, gender | ['cc-by-4.0'] |
| FLEURS en_us (chỉ lấy câu Anh) | Online (public) | https://huggingface.co/datasets/google/fleurs (data/en_us/*.tsv) | train 1.476 câu; dev 150 câu; test 350 câu | TSV (không dùng audio tiếng Anh) | 1.9 | id (ghép với vi_vn), raw_transcription = câu Anh tham chiếu | ['cc-by-4.0'] |
| PhoMT | Online (gated) | https://huggingface.co/datasets/vinai/PhoMT | train 2.977.999 cặp; dev 18.719 cặp; test 19.151 cặp | Văn bản song song .vi/.en trong PhoMT.zip | 339.4 | câu tiếng Việt (.vi), câu tiếng Anh (.en), song song theo số dòng | Chỉ nghiên cứu/giáo dục, cấm phân phối lại |
| Dữ liệu tự thu | Offline | Không thu thập | 0 | - | - | Nhóm không tự thu âm/khảo sát. Dùng dataset công khai đã có nhãn chuẩn, giữ split gốc để so được với paper; tự thu cần thời gian gán nhãn và kiểm định mà Task 2 không đủ. Hạn chế: chưa có giọng nữ (theo nhãn FLEURS) và micro điện thoại. | - |

Sinh bởi viec1_tai_3_bo_du_lieu.py lúc 2026-10-29T19:06:00+00:00. Mã commit repo: {'vivos': '3cbfb2502e5e84776b4b778b020a09759f723f52', 'fleurs': '70bb2e84b976b7e960aa89f1c648e09c59f894dd', 'phomt': 'd4b9bf14888b40a88ec332cbab6bab97cf6a68a7'}.
