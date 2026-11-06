#!/bin/bash
# 03/11/2026 – nhóm chốt V4: đo 2 số V4 còn thiếu (trước đây chỉ đo cho V3 = bản cuối theo quy tắc cũ).
# (1) Whisper-small → V4 + bootstrap so với B0 (cùng cách hang_doi_bo_sung.sh);
# (2) tốc độ B0 / V3 / V4 xen kẽ 3 lần trong CÙNG một phiên (thư mục riêng lap_V4/, không ghi đè lap/ của 30–31/10).
source /d/CAIDCM/teamwork/task3/env/env.sh; cd $T
MTREV=ae7baa85da07dbe8e23ac26a9f5ef560c17e2138
echo "$(date +%H:%M:%S) BAT_DAU"
[ -f runs/mt/V4/fleurs_test_asr_wsp/score.json ] || $P scripts/mt/translate.py --input runs/mt_data/fleurs_test_asr_wsp.jsonl --out_dir runs/mt/V4/fleurs_test_asr_wsp --revision $MTREV --adapter checkpoints/V4/best 2>&1 | grep -E "BLEU|Error|Traceback" | sed "s|^|V4 wsp |"
$P scripts/mt/bootstrap.py --a runs/mt/B0/fleurs_test_asr_wsp/hyp.jsonl --b runs/mt/V4/fleurs_test_asr_wsp/hyp.jsonl --data runs/mt_data/fleurs_test_asr_wsp.jsonl --out reports/mt/bootstrap_B0_V4_cascade_wsp_test.json --n 1000 | grep -o '"delta.*"p_one_sided_delta_le_0": [0-9.]*' | sed "s|^|B0→V4 wsp |"
for k in 1 2 3; do for v in B0 V3 V4; do
  ad=""; [ $v != B0 ] && ad="--adapter checkpoints/$v/best"
  echo "$(date +%H:%M:%S) toc do lan $k $v"
  $P scripts/mt/do_toc_do.py --n 100 --out reports/toc_do/lap_V4/toc_do_${v}_lan$k.json $ad 2>&1 | tail -1 | grep -o '"RTF_total": [0-9.]*, "RTF_asr": [0-9.]*, "RTF_mt": [0-9.]*, "latency_p50_s": [0-9.]*, "latency_p95_s": [0-9.]*'
done; done
echo "$(date +%H:%M:%S) DO_V4_XONG"
