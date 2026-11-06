#!/bin/bash
# BAN LUU: day la hang doi Kiet DA CHAY 30-31/10 (giu de doi chieu). Co vong cho log cua buoc truoc;
# chay lai thi dung experiments/chay_lai.sh.
# Hàng đợi đêm 1 sau S4: S5 (ASR FLEURS dev/train bằng PhoWhisper) → S6 (B0 + cascade) → S7 (V1 LoRA).
# Mỗi bước kiểm "đã xong" trước khi chạy để chạy lại an toàn; train chỉ bắt đầu nếu còn đủ giờ trước hạn dừng.
source "$(dirname "$0")/../../env/env.sh"; cd "$T"
MTREV=ae7baa85da07dbe8e23ac26a9f5ef560c17e2138
PHO="vinai/PhoWhisper-small --revision a86b604c346caf7148c37512eafe783a16420adb"
until grep -q ALL_DONE logs/s4_asr_baseline.log; do sleep 20; done
for sp in dev train; do
  RID=kiet_t2_phowhisper-small_fleurs_${sp}
  echo "$(date +%H:%M:%S) START S5 $RID"
  $P scripts/asr/run_asr.py --model $PHO --manifest runs/manifests/asr_fleurs_${sp}.jsonl --out_dir runs/asr/$RID --run_id $RID 2>&1 | grep -v "forced_decoder_ids\|attention mask is not set\|fget.__get__"
  [ -d runs/asr/$RID/score ] || $P scripts/asr/score_asr.py --predictions runs/asr/$RID/predictions.jsonl --manifest runs/manifests/asr_fleurs_${sp}.jsonl --out runs/asr/$RID/score --run-id $RID | grep -E '"(n|WER_percent|CER_percent)"'
  echo "$(date +%H:%M:%S) END S5 $RID"
done
$P scripts/mt/make_mt_data.py --asr test:pho:runs/asr/kiet_t2_phowhisper-small_fleurs_test/predictions.jsonl \
  dev:pho:runs/asr/kiet_t2_phowhisper-small_fleurs_dev/predictions.jsonl train:pho:runs/asr/kiet_t2_phowhisper-small_fleurs_train/predictions.jsonl
for d in fleurs_test_clean fleurs_test_asr_pho fleurs_dev_clean fleurs_dev_asr_pho; do
  echo "$(date +%H:%M:%S) START S6 B0 $d"
  $P scripts/mt/translate.py --input runs/mt_data/$d.jsonl --out_dir runs/mt/B0/$d --revision $MTREV 2>&1 | grep -E "BLEU|Error|Traceback"
done
echo "$(date +%H:%M:%S) S6_DONE"
