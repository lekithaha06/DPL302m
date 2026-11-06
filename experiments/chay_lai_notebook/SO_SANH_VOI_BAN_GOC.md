# So lần chạy lại với kết quả gốc 
## 1. Code 
Script chạy lại so với task3/scripts: 67 file, khác: ['tao_notebook_chay_lai.py']
Script chính so với repo_cuoi: 17 / 17 giống; khác: []
Ô %%tep trong notebook khớp file đã chạy: 16 / 16 
Cấu hình train V1: tham số khác: [] ; dữ liệu train: True
Cấu hình train V2: tham số khác: [] ; dữ liệu train: True
Cấu hình train V3: tham số khác: [] ; dữ liệu train: True
Cấu hình train V4: tham số khác: [] ; dữ liệu train: True
 ## 2. Dữ liệu vào khối dịch 
fleurs_dev_asr_pho.jsonl giống byte
fleurs_dev_clean.jsonl giống byte
fleurs_test_asr_pho.jsonl giống byte
fleurs_test_asr_wsp.jsonl giống byte
fleurs_test_clean.jsonl giống byte
fleurs_train_asr_pho.jsonl giống byte
fleurs_train_asr_pho_canbang.jsonl giống byte
fleurs_train_clean.jsonl giống byte
phomt_dev.jsonl giống byte
phomt_test.jsonl giống byte
phomt_train_mix.jsonl giống byte
 ## 3. Dự đoán và điểm 
ASR phowhisper-small_fleurs_dev 361 câu, khác 0
ASR phowhisper-small_fleurs_test 857 câu, khác 0
ASR phowhisper-small_fleurs_train 2926 câu, khác 0
ASR phowhisper-small_vivos_test 760 câu, khác 0
ASR whisper-small_fleurs_test 857 câu, khác 0
ASR whisper-small_vivos_test 760 câu, khác 0
MT B0 fleurs_dev_asr_pho 361 câu, khác 0 · BLEU 22.96 22.96 · chrF++ 50.4 50.4 
MT B0 fleurs_dev_clean 361 câu, khác 0 · BLEU 37.57 37.57 · chrF++ 61.63 61.63 
MT B0 fleurs_test_asr_pho 857 câu, khác 0 · BLEU 22.69 22.69 · chrF++ 49.38 49.38 
MT B0 fleurs_test_asr_wsp 857 câu, khác 0 · BLEU 18.58 18.58 · chrF++ 44.62 44.62 
MT B0 fleurs_test_clean 857 câu, khác 0 · BLEU 38.27 38.27 · chrF++ 61.54 61.54 
MT B0 phomt_test 19151 câu, khác 0 · BLEU 40.79 40.79 · chrF++ 60.73 60.73 
MT V1 fleurs_dev_asr_pho 361 câu, khác 1 · BLEU 26.48 26.47 · chrF++ 52.5 52.48 ← LỆCH
MT V1 fleurs_dev_clean 361 câu, khác 0 · BLEU 35.97 35.97 · chrF++ 59.92 59.92 
MT V1 fleurs_test_asr_pho 857 câu, khác 0 · BLEU 27.49 27.49 · chrF++ 52.5 52.5 
MT V1 fleurs_test_asr_wsp không có bản gốc để so
MT V1 fleurs_test_clean 857 câu, khác 0 · BLEU 36.21 36.21 · chrF++ 59.73 59.73 
MT V1 phomt_test 19151 câu, khác 0 · BLEU 36.96 36.96 · chrF++ 58.07 58.07 
MT V2 fleurs_dev_asr_pho 361 câu, khác 0 · BLEU 26.45 26.45 · chrF++ 52.74 52.74 
MT V2 fleurs_dev_clean 361 câu, khác 0 · BLEU 36.93 36.93 · chrF++ 61.24 61.24 
MT V2 fleurs_test_asr_pho 857 câu, khác 0 · BLEU 27.47 27.47 · chrF++ 52.98 52.98 
MT V2 fleurs_test_asr_wsp 857 câu, khác 0 · BLEU 19.68 19.68 · chrF++ 45.09 45.09 
MT V2 fleurs_test_clean 857 câu, khác 0 · BLEU 38.09 38.09 · chrF++ 61.35 61.35 
MT V2 phomt_test 19151 câu, khác 0 · BLEU 40.41 40.41 · chrF++ 60.35 60.35 
MT V3 fleurs_dev_asr_pho 361 câu, khác 0 · BLEU 26.71 26.71 · chrF++ 52.5 52.5 
MT V3 fleurs_dev_clean 361 câu, khác 0 · BLEU 36.37 36.37 · chrF++ 60.48 60.48 
MT V3 fleurs_test_asr_pho 857 câu, khác 0 · BLEU 27.33 27.33 · chrF++ 52.25 52.25 
MT V3 fleurs_test_asr_wsp 857 câu, khác 0 · BLEU 19.86 19.86 · chrF++ 44.79 44.79 
MT V3 fleurs_test_clean 857 câu, khác 0 · BLEU 36.76 36.76 · chrF++ 60.37 60.37 
MT V3 phomt_test 19151 câu, khác 4 · BLEU 39.59 39.58 · chrF++ 59.8 59.8 ← LỆCH
MT V4 fleurs_dev_asr_pho 361 câu, khác 0 · BLEU 26.33 26.33 · chrF++ 52.03 52.03 
MT V4 fleurs_dev_clean 361 câu, khác 0 · BLEU 36.75 36.75 · chrF++ 60.75 60.75 
MT V4 fleurs_test_asr_pho 857 câu, khác 1 · BLEU 27.37 27.37 · chrF++ 52.51 52.51 
MT V4 fleurs_test_asr_wsp 857 câu, khác 0 · BLEU 20.42 20.42 · chrF++ 45.25 45.25 
MT V4 fleurs_test_clean 857 câu, khác 0 · BLEU 38.11 38.11 · chrF++ 61.07 61.07 
MT V4 phomt_test 19151 câu, khác 0 · BLEU 40.08 40.08 · chrF++ 60.21 60.21 
 Tổng: 117884 câu, khác 6, tức 99.9949% giống
 ## 4. Trọng số adapter tốt nhất 
V1 giống byte · 8650752 tham số · sai khác lớn nhất 0.000e+00 · tỉ lệ so với độ lớn 0.000e+00 · tham số trùng hệt 100.00%
V2 giống byte · 8650752 tham số · sai khác lớn nhất 0.000e+00 · tỉ lệ so với độ lớn 0.000e+00 · tham số trùng hệt 100.00%
V3 giống byte · 8650752 tham số · sai khác lớn nhất 0.000e+00 · tỉ lệ so với độ lớn 0.000e+00 · tham số trùng hệt 100.00%
V4 giống byte · 8650752 tham số · sai khác lớn nhất 0.000e+00 · tỉ lệ so với độ lớn 0.000e+00 · tham số trùng hệt 100.00%
