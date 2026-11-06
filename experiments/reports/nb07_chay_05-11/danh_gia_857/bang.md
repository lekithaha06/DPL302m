# Danh gia Proposed Method · fleurs_test

`vinai/PhoWhisper-small@a86b604c + vinai/vinai-translate-vi2en-v2@ae7baa85 + LoRA V2/best`

| Cau hinh | Nhom | n | WER_asr | CER_asr | WER_sau_doi_so | BLEU | chrF++ | RTF |
|---|---|---|---|---|---|---|---|---|
| truoc_0411 | tat_ca | 857 | 12.27 | 8.6 | 12.27 | 28.01 | 53.03 | 0.1249 |
| truoc_0411 | dai | 10 | 16.03 | 12.04 | 16.03 | 15.51 | 49.61 | 0.1004 |
| proposed | tat_ca | 857 | 12.26 | 8.57 | 10.12 | 28.15 | 53.1 | 0.1192 |
| proposed | dai | 10 | 15.59 | 10.99 | 12.94 | 18.74 | 51.34 | 0.1082 |

WER_asr: loi PhoWhisper nguyen ban (so voi Task 2: FLEURS test 13,68 khi chay tung file).
WER_sau_doi_so: tham khao, tham chieu FLEURS viet chu so nen doi so lam WER giam.
BLEU/chrF++: sacreBLEU 2.4.3, cuoi pipeline (cascade).