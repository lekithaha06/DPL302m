#!/bin/bash
# 04/11/2026 – quy tắc DEV (reports/ablation/QUY_TAC_CHON.md) chọn V2 → đo các số V2 còn thiếu, cùng cách đã đo V3/V4:
# (1) Whisper-small → V2 + bootstrap so với B0; (2) tốc độ B0 / V2 / V4 xen kẽ 3 lần trong CÙNG một phiên (lap_V2/, không ghi đè lap/, lap_V4/).
source /d/CAIDCM/teamwork/task3/env/env.sh; cd $T
MTREV=ae7baa85da07dbe8e23ac26a9f5ef560c17e2138
echo "$(date +%H:%M:%S) BAT_DAU"
[ -f runs/mt/V2/fleurs_test_asr_wsp/score.json ] || $P scripts/mt/translate.py --input runs/mt_data/fleurs_test_asr_wsp.jsonl --out_dir runs/mt/V2/fleurs_test_asr_wsp --revision $MTREV --adapter checkpoints/V2/best 2>&1 | grep -E "BLEU|Error|Traceback" | sed "s|^|V2 wsp |"
$P scripts/mt/bootstrap.py --a runs/mt/B0/fleurs_test_asr_wsp/hyp.jsonl --b runs/mt/V2/fleurs_test_asr_wsp/hyp.jsonl --data runs/mt_data/fleurs_test_asr_wsp.jsonl --out reports/mt/bootstrap_B0_V2_cascade_wsp_test.json --n 1000 | grep -o '"delta.*"p_one_sided_delta_le_0": [0-9.]*' | sed "s|^|B0→V2 wsp |"
for k in 1 2 3; do for v in B0 V2 V4; do
  ad=""; [ $v != B0 ] && ad="--adapter checkpoints/$v/best"
  echo "$(date +%H:%M:%S) toc do lan $k $v"
  $P scripts/mt/do_toc_do.py --n 100 --out reports/toc_do/lap_V2/toc_do_${v}_lan$k.json $ad 2>&1 | tail -1 | grep -o '"RTF_total": [0-9.]*, "RTF_asr": [0-9.]*, "RTF_mt": [0-9.]*, "latency_p50_s": [0-9.]*, "latency_p95_s": [0-9.]*'
done; done
echo "$(date +%H:%M:%S) DO_V2_XONG"
