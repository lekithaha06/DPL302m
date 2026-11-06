#!/bin/bash
# BAN LUU: day la hang doi Kiet DA CHAY 30-31/10 (giu de doi chieu). Co vong cho log cua buoc truoc;
# chay lai thi dung experiments/chay_lai.sh.
# S7: train V1 sau khi S6 xong. Chỉ bắt đầu nếu trước 05:10 (ước tính train + đánh giá ~35 phút, hạn dừng 06:00).
source "$(dirname "$0")/../../env/env.sh"; cd "$T"
MTREV=ae7baa85da07dbe8e23ac26a9f5ef560c17e2138
until grep -q S6_DONE logs/hang_doi_dem1.log; do sleep 20; done
now=$(date +%H%M); if [ "$now" -gt 0510 ] && [ "$now" -lt 1200 ]; then echo "$(date +%H:%M) KHONG_DU_GIO: để V1 sang tối mai"; exit 0; fi
echo "$(date +%H:%M:%S) SMOKE train_lora (32 mẫu, 1 epoch, ra checkpoints/_smoke, không dùng kết quả)"
head -32 runs/mt_data/fleurs_train_asr_pho.jsonl > runs/smoke/lora_train32.jsonl; head -16 runs/mt_data/fleurs_dev_asr_pho.jsonl > runs/smoke/lora_dev16.jsonl
$P scripts/mt/train_lora.py --train runs/smoke/lora_train32.jsonl --dev runs/smoke/lora_dev16.jsonl --out_dir checkpoints/_smoke --revision $MTREV --epochs 1 > logs/s7_smoke_lora.log 2>&1 || { echo SMOKE_FAIL; tail -20 logs/s7_smoke_lora.log; exit 1; }
echo "$(date +%H:%M:%S) START S7 V1"
$P scripts/mt/train_lora.py --train runs/mt_data/fleurs_train_asr_pho.jsonl --dev runs/mt_data/fleurs_dev_asr_pho.jsonl \
  --out_dir checkpoints/V1 --revision $MTREV --epochs 5 --lr 2e-4 --batch_size 8 --grad_accum 2 --lora_r 16 --lora_alpha 32 --seed 42 --resume 2>&1 | grep -v "Warn\|warn("
echo "$(date +%H:%M:%S) END S7 V1 train"
for d in fleurs_test_asr_pho fleurs_test_clean fleurs_dev_asr_pho; do
  $P scripts/mt/translate.py --input runs/mt_data/$d.jsonl --out_dir runs/mt/V1/$d --revision $MTREV --adapter checkpoints/V1/best 2>&1 | grep -E "BLEU|Error|Traceback"
done
echo "$(date +%H:%M:%S) V1_DONE"
echo "$(date +%H:%M:%S) START B0 phomt_test (sau V1 để V1 kịp xong trước 06:00)"
$P scripts/mt/translate.py --input runs/mt_data/phomt_test.jsonl --out_dir runs/mt/B0/phomt_test --revision $MTREV 2>&1 | grep -E "BLEU|Error|Traceback"
echo "$(date +%H:%M:%S) B0_PHOMT_DONE"
