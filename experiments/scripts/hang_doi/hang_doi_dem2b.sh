#!/bin/bash
# BAN LUU: day la hang doi Kiet DA CHAY 30-31/10 (giu de doi chieu). Co vong cho log cua buoc truoc;
# chay lai thi dung experiments/chay_lai.sh.
# Sau DEM2_DONE: H4 cho whisper-small (dev beam 5 và beam 1), rồi đo tốc độ cascade (S9) cho B0 và V2 trên 100 bản thu test.
source "$(dirname "$0")/../../env/env.sh"; cd "$T"
until grep -qE "DEM2_DONE|TRAIN_FAIL" logs/hang_doi_dem2.log; do sleep 20; done
WSP="openai/whisper-small --revision 973afd24965f72e36ca33b3055d56a652f456b4d"
for nb in 5 1; do
  RID=kiet_t2_whisper-small_fleurs_dev; [ $nb = 1 ] && RID=${RID}_beam1
  echo "$(date +%H:%M:%S) START H4 $RID"
  $P scripts/asr/run_asr.py --model $WSP --manifest runs/manifests/asr_fleurs_dev.jsonl --out_dir runs/asr/$RID --run_id $RID --num_beams $nb 2>&1 | grep -E "xong|Error|Traceback"
  [ -d runs/asr/$RID/score ] || $P scripts/asr/score_asr.py --predictions runs/asr/$RID/predictions.jsonl --manifest runs/manifests/asr_fleurs_dev.jsonl --out runs/asr/$RID/score --run-id $RID | grep -E '"(WER_percent|CER_percent)"'
done
for v in B0 V2; do
  [ -f reports/toc_do/toc_do_$v.json ] && continue
  ad=""; [ $v != B0 ] && ad="--adapter checkpoints/$v/best"
  echo "$(date +%H:%M:%S) START S9 toc do $v"
  $P scripts/mt/do_toc_do.py --n 100 --out reports/toc_do/toc_do_$v.json $ad 2>&1 | tail -1 | cut -c1-400
done
echo "$(date +%H:%M:%S) DEM2B_DONE"
