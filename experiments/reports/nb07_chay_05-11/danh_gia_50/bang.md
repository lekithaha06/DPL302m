# Danh gia Proposed Method · fleurs_test

`vinai/PhoWhisper-small@a86b604c + vinai/vinai-translate-vi2en-v2@ae7baa85 + LoRA V2/best`

| Cau hinh | Nhom | n | WER_asr | CER_asr | WER_sau_doi_so | BLEU | chrF++ | RTF |
|---|---|---|---|---|---|---|---|---|
| truoc_0411 | tat_ca | 50 | 8.98 | 6.69 | 8.98 | 28.15 | 54.25 | 0.1258 |
| proposed | tat_ca | 50 | 8.98 | 6.69 | 7.71 | 28.08 | 54.25 | 0.1332 |

WER_asr: loi PhoWhisper nguyen ban (so voi Task 2: FLEURS test 13,68 khi chay tung file).
WER_sau_doi_so: tham khao, tham chieu FLEURS viet chu so nen doi so lam WER giam.
BLEU/chrF++: sacreBLEU 2.4.3, cuoi pipeline (cascade).