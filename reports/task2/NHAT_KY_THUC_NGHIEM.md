# Nhật ký thực nghiệm Task 2

Máy: xem `evidence/gpu.txt`; thư viện: `evidence/pip_freeze.txt`; mã hash mọi file: `evidence/manifest.json`.

## Dòng thời gian (trích `logs/queue.log`)

```
2026-10-22 21:16:07 START baseline A (VIVOS)
2026-10-22 21:46:02 DONE baseline A
2026-10-22 21:46:02 START B0 eval
2026-10-22 22:05:22 DONE B0 eval
2026-10-22 22:05:22 START transcribe dev (361)
2026-10-22 22:23:10 DONE transcribe dev
2026-10-22 22:23:10 START transcribe train (2927)
2026-10-23 00:46:36 DONE transcribe train
2026-10-23 00:46:36 QUEUE STAGE 1-3 COMPLETE
2026-10-23 00:46:45 START train V1
2026-10-23 01:16:07 DONE train V1
2026-10-23 01:16:07 START eval V1
2026-10-23 01:26:23 FAIL eval V1
2026-10-23 01:38:16 START eval V1
2026-10-23 01:45:30 START eval V1
2026-10-23 02:19:24 DONE eval V1
2026-10-23 02:19:24 START train V2
2026-10-23 02:20:07 START train V2
2026-10-23 02:50:59 DONE train V2
2026-10-23 02:50:59 START eval B0
2026-10-23 02:54:29 DONE eval B0
2026-10-23 02:54:29 START eval V2
2026-10-23 03:28:56 DONE eval V2
2026-10-23 03:39:28 STOP queue (significance moved after speed; GPU was idle)
2026-10-23 03:39:40 START select final on PhoMT dev
2026-10-23 03:49:21 DONE select final
2026-10-23 03:49:21 FINAL = v2
2026-10-23 03:49:21 START speed B0
2026-10-23 03:59:49 DONE speed B0
2026-10-23 03:59:49 START speed final
2026-10-23 04:10:25 DONE speed final
2026-10-23 04:10:25 SPEED COMPLETE
2026-10-23 04:10:25 FINAL QUEUE COMPLETE
2026-10-23 09:41:24 START train V2b (V2 + sentence balancing)
2026-10-23 09:41:43 DONE train V2b (exit 1)
2026-10-23 09:43:39 FAIL train V2b: lỗi import thư viện khi khởi động (chưa train bước nào); cố định lại phiên bản thư viện như evidence/pip_freeze.txt rồi chạy lại
2026-10-23 09:43:39 START train V2b (V2 + sentence balancing)
2026-10-23 10:10:35 DONE train V2b (exit 0)
2026-10-23 10:10:51 START dev V2
2026-10-23 10:12:05 DONE dev V2
2026-10-23 10:12:05 START dev V2+ITN
2026-10-23 10:13:16 DONE dev V2+ITN
2026-10-23 10:13:16 START eval V2b
2026-10-23 10:16:38 DONE eval V2b
2026-10-23 10:16:38 START PhoMT dev V2b
2026-10-23 10:21:16 DONE PhoMT dev V2b
2026-10-23 10:21:16 BASE for V3 = V2 (FLEURS dev V2 27.1655242467345, V2b 26.9796055725761; PhoMT dev B0 40.96, V2b 40.93)
2026-10-23 10:21:16 ITN on FLEURS dev (V2): 27.29 -> 27.17
2026-10-23 10:21:16 V3 not adopted: ITN did not improve FLEURS dev
2026-10-23 10:21:27 V3 QUEUE COMPLETE
2026-10-23 10:27:20 ENV: kiểm tra pip freeze giống hệt evidence/pip_freeze.txt
2026-10-23 12:44:34 START train V3
2026-10-23 13:12:24 DONE train V3
2026-10-23 13:12:24 START dev V3
2026-10-23 13:13:08 DONE dev V3
2026-10-23 13:13:08 START PhoMT dev V3
2026-10-23 13:16:54 DONE PhoMT dev V3
2026-10-23 13:16:54 V3 decision on dev: FLEURS dev V2 27.29 vs V3 27.56; PhoMT dev B0 40.96 vs V3 41.16 -> adopt=True
2026-10-23 13:16:54 START eval V3
2026-10-23 13:38:19 DONE eval V3
2026-10-23 13:38:19 START eval B0 PhoMT rescore
2026-10-23 14:06:26 DONE eval B0 PhoMT rescore
2026-10-23 14:06:26 START baseline A on FLEURS
2026-10-23 15:34:45 DONE baseline A on FLEURS
2026-10-23 15:34:57 SESSION 3 QUEUE COMPLETE
2026-10-23 15:35:17 START speed V3 (final, with number normalisation)
2026-10-23 15:46:27 DONE speed V3 (exit 0)
2026-10-23 15:49:49 DONE session 3: slides, report, docs updated
2026-10-23 15:50:10 START train V3_s13
2026-10-23 16:21:31 DONE train V3_s13
2026-10-23 16:21:31 START eval V3_s13
2026-10-23 16:25:33 DONE eval V3_s13
2026-10-23 16:25:33 START train V3_s7
2026-10-23 16:56:53 DONE train V3_s7
2026-10-23 16:56:53 START eval V3_s7
2026-10-23 17:02:28 DONE eval V3_s7
2026-10-23 17:02:28 SEEDS QUEUE COMPLETE
2026-10-23 17:03:46 DONE seed robustness write-up
```

## Kết quả train từng phiên bản

### V1

| Epoch | Train loss | Dev loss | Dev BLEU | Dev chrF++ | Giây |
|---|---|---|---|---|---|
| 0 | – | 1.7174 | 24.65 | 51.19 | 0 |
| 1 | 1.4778 | 1.4757 | 27.49 | 52.86 | 313.2 |
| 2 | 1.2592 | 1.4907 | 26.93 | 52.58 | 304.3 |
| 3 | 1.1028 | 1.5332 | 26.76 | 52.78 | 294.3 |
| 4 | 0.9775 | 1.5908 | 25.85 | 51.73 | 307.2 |
| 5 | 0.9056 | 1.6287 | 26.22 | 52.22 | 305.9 |

### V2

| Epoch | Train loss | Dev loss | Dev BLEU | Dev chrF++ | Giây |
|---|---|---|---|---|---|
| 0 | – | 1.7174 | 24.65 | 51.19 | 0 |
| 1 | 1.1596 | 1.4905 | 27.17 | 53.13 | 587.2 |
| 2 | 0.9831 | 1.5244 | 26.98 | 53.05 | 569.6 |
| 3 | 0.8604 | 1.5842 | 27.04 | 52.63 | 541.7 |

## Mã hash checkpoint (adapter LoRA)

- `checkpoints/v1/best_adapter/adapter_model.safetensors`: `83ca179b1713ded2…` (18,915,448 byte)
- `checkpoints/v2/best_adapter/adapter_model.safetensors`: `d7186a19355b1bc3…` (18,915,448 byte)
- `checkpoints/v2b/best_adapter/adapter_model.safetensors`: `07199d4715a73b94…` (18,915,448 byte)
- `checkpoints/v3/best_adapter/adapter_model.safetensors`: `4235dfa267f26ac4…` (18,915,448 byte)
- `checkpoints/v3_s13/best_adapter/adapter_model.safetensors`: `47ec97387712ed65…` (18,915,448 byte)
- `checkpoints/v3_s7/best_adapter/adapter_model.safetensors`: `c3608cb68d05af21…` (18,915,448 byte)
