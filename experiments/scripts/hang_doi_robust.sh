#!/bin/bash
# Đo độ bền PhoWhisper-small trên FLEURS test (5 điều kiện). Xoá wav sau khi chấm vì sinh lại được, tất định.
source /d/CAIDCM/teamwork/task3/env/env.sh; cd $T
for dk in noise_snr20 noise_snr10 speed_0.9 speed_1.1 vol_-12dB; do
  RID=robust_pho_$dk; O=runs/robust/$RID
  [ -f $O/score/summary.json ] && continue
  $P scripts/asr/tao_audio_robust.py $dk
  $P scripts/asr/run_asr.py --model vinai/PhoWhisper-small --revision a86b604c346caf7148c37512eafe783a16420adb --manifest runs/robust/manifests/$dk.jsonl --out_dir $O --run_id $RID 2>&1 | grep -v "forced_decoder_ids\|attention mask is not set\|fget.__get__"
  [ -d $O/score ] || $P scripts/asr/score_asr.py --predictions $O/predictions.jsonl --manifest runs/robust/manifests/$dk.jsonl --out $O/score --run-id $RID | grep -E '"(n|WER_percent|CER_percent)"'
  rm -rf runs/robust/audio/$dk
  echo "$(date +%H:%M:%S) END $dk"
done
echo ROBUST_DONE
