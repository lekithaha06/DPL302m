#!/bin/bash
# BAN LUU: day la hang doi Kiet DA CHAY 30-31/10 (giu de doi chieu). Co vong cho log cua buoc truoc;
# chay lai thi dung experiments/chay_lai.sh.
# S8a: V2 sau khi B0 PhoMT test xong. Chỉ bắt đầu nếu trước 05:15 (ước ~25 phút train + ~5 phút đánh giá; hạn 06:00).
source "$(dirname "$0")/../../env/env.sh"; cd "$T"
MTREV=ae7baa85da07dbe8e23ac26a9f5ef560c17e2138
until grep -q B0_PHOMT_DONE logs/hang_doi_v1.log; do sleep 15; done
now=$(date +%H%M); if [ "$now" -gt 0515 ] && [ "$now" -lt 1200 ]; then echo "$(date +%H:%M) KHONG_DU_GIO: để V2 sang tối mai"; exit 0; fi
echo "$(date +%H:%M:%S) START S8 V2"
$P scripts/mt/train_lora.py --train runs/mt_data/fleurs_train_asr_pho.jsonl runs/mt_data/phomt_train_mix.jsonl --dev runs/mt_data/fleurs_dev_asr_pho.jsonl \
  --out_dir checkpoints/V2 --revision $MTREV --epochs 5 --lr 2e-4 --batch_size 8 --grad_accum 2 --lora_r 16 --lora_alpha 32 --seed 42 --resume 2>&1 | grep -E "epoch|best|Error|Traceback"
echo "$(date +%H:%M:%S) END S8 V2 train"
for d in fleurs_dev_asr_pho fleurs_test_asr_pho fleurs_test_clean; do
  $P scripts/mt/translate.py --input runs/mt_data/$d.jsonl --out_dir runs/mt/V2/$d --revision $MTREV --adapter checkpoints/V2/best 2>&1 | grep -E "BLEU|Error|Traceback"
done
echo "$(date +%H:%M:%S) V2_DONE"
