#!/bin/bash
# BAN LUU: day la hang doi Kiet DA CHAY 30-31/10 (giu de doi chieu). Co vong cho log cua buoc truoc;
# chay lai thi dung experiments/chay_lai.sh.
# Sau DEM2B: V3 (V2 + cân bằng của Uyên) → V4 (bản tốt hơn trên dev giữa V2/V3, lr 5e-5). Đánh giá đủ 5 tập.
source "$(dirname "$0")/../../env/env.sh"; cd "$T"
MTREV=ae7baa85da07dbe8e23ac26a9f5ef560c17e2138
until grep -qE "DEM2B_DONE" logs/hang_doi_dem2b.log; do sleep 20; done
ev() { local v=$1 ad=$2; shift 2; for d in "$@"; do [ -f runs/mt/$v/$d/score.json ] && continue
  $P scripts/mt/translate.py --input runs/mt_data/$d.jsonl --out_dir runs/mt/$v/$d --revision $MTREV --adapter $ad 2>&1 | grep -E "BLEU|Error|Traceback" | sed "s|^|$v $d |"; done; }
train() { local v=$1 lr=$2; shift 2; echo "$(date +%H:%M:%S) START train $v (lr $lr)"
  $P scripts/mt/train_lora.py --train "$@" --dev runs/mt_data/fleurs_dev_asr_pho.jsonl --out_dir checkpoints/$v --revision $MTREV \
     --epochs 5 --lr $lr --batch_size 4 --grad_accum 4 --lora_r 16 --lora_alpha 32 --seed 42 --resume > logs/train_$v.log 2>&1 || { echo "TRAIN_FAIL $v"; tail -15 logs/train_$v.log; exit 1; }
  grep -E "^best" logs/train_$v.log | cut -c1-200; echo "$(date +%H:%M:%S) END train $v"; }
SETS="fleurs_dev_asr_pho fleurs_test_asr_pho fleurs_test_clean fleurs_dev_clean phomt_test"
train V3 2e-4 runs/mt_data/fleurs_train_asr_pho_canbang.jsonl runs/mt_data/phomt_train_mix.jsonl
ev V3 checkpoints/V3/best $SETS
d2=$(grep -o '"BLEU": [0-9.]*' runs/mt/V2/fleurs_dev_asr_pho/score.json | cut -d' ' -f2); d3=$(grep -o '"BLEU": [0-9.]*' runs/mt/V3/fleurs_dev_asr_pho/score.json | cut -d' ' -f2)
if $P -c "import sys; sys.exit(0 if float('$d3') > float('$d2') else 1)"; then BASE=V3; DATA="runs/mt_data/fleurs_train_asr_pho_canbang.jsonl runs/mt_data/phomt_train_mix.jsonl"
else BASE=V2; DATA="runs/mt_data/fleurs_train_asr_pho.jsonl runs/mt_data/phomt_train_mix.jsonl"; fi
echo "$(date +%H:%M:%S) V4 base = $BASE (dev V2 $d2, V3 $d3)" | tee reports/tong_hop_V4_base.txt
train V4 5e-5 $DATA
ev V4 checkpoints/V4/best $SETS
echo "$(date +%H:%M:%S) DEM2C_DONE"
