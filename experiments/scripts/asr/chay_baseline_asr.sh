#!/bin/bash
# S4: 4 lượt ASR baseline theo protocol bao_asr_v1_20261027, rồi chấm bằng score_asr.py của Bảo.
source /d/CAIDCM/teamwork/task3/env/env.sh; cd $T
PHO="vinai/PhoWhisper-small a86b604c346caf7148c37512eafe783a16420adb phowhisper-small"
WSP="openai/whisper-small 973afd24965f72e36ca33b3055d56a652f456b4d whisper-small"
for m in "$PHO" "$WSP"; do set -- $m
  for ds in vivos fleurs; do
    RID=kiet_t2_${3}_${ds}_test
    echo "$(date +%H:%M:%S) START $RID"
    $P scripts/asr/run_asr.py --model $1 --revision $2 --manifest runs/manifests/asr_${ds}_test.jsonl --out_dir runs/asr/$RID --run_id $RID 2>&1 | grep -v "forced_decoder_ids\|attention mask is not set\|fget.__get__"
    [ -d runs/asr/$RID/score ] || $P scripts/asr/score_asr.py --predictions runs/asr/$RID/predictions.jsonl --manifest runs/manifests/asr_${ds}_test.jsonl --out runs/asr/$RID/score --run-id $RID | grep -E '"(n|WER_percent|CER_percent)"'
    echo "$(date +%H:%M:%S) END $RID"
  done
done
echo ALL_DONE
