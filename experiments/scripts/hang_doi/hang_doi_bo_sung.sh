#!/bin/bash
# BAN LUU: day la hang doi Kiet DA CHAY 30-31/10 (giu de doi chieu). Co vong cho log cua buoc truoc;
# chay lai thi dung experiments/chay_lai.sh.
# Bổ sung sau CHAY_MAY_XONG: cascade với Baseline 2 (Whisper-small → B0, Whisper-small → bản cuối) để V1..Vn so được với CẢ 2 baseline.
source "$(dirname "$0")/../../env/env.sh"; cd "$T"
MTREV=ae7baa85da07dbe8e23ac26a9f5ef560c17e2138
until grep -qE "CHAY_MAY_XONG" logs/hang_doi_ket_thuc.log 2>/dev/null; do sleep 20; done
FINAL=$(cat reports/tong_hop/ban_cuoi.txt | awk '{print $NF}')
$P scripts/mt/make_mt_data.py --asr test:wsp:runs/asr/kiet_t2_whisper-small_fleurs_test/predictions.jsonl | grep wsp
for v in B0 $FINAL; do
  ad=""; [ $v != B0 ] && ad="--adapter checkpoints/$v/best"
  [ -f runs/mt/$v/fleurs_test_asr_wsp/score.json ] || $P scripts/mt/translate.py --input runs/mt_data/fleurs_test_asr_wsp.jsonl --out_dir runs/mt/$v/fleurs_test_asr_wsp --revision $MTREV $ad 2>&1 | grep -E "BLEU|Error|Traceback" | sed "s|^|$v wsp |"
done
$P scripts/mt/bootstrap.py --a runs/mt/B0/fleurs_test_asr_wsp/hyp.jsonl --b runs/mt/$FINAL/fleurs_test_asr_wsp/hyp.jsonl --data runs/mt_data/fleurs_test_asr_wsp.jsonl --out reports/mt/bootstrap_B0_${FINAL}_cascade_wsp_test.json --n 1000 | grep -o '"delta.*"p_one_sided_delta_le_0": [0-9.]*'
$P scripts/cham_theo_mien.py > /dev/null; $P scripts/ve_bieu_do.py > /dev/null
touch logs/DUNG_THEO_DOI
echo "$(date +%H:%M:%S) BO_SUNG_XONG"
