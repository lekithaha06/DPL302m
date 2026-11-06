#!/bin/bash
# BAN LUU: day la hang doi Kiet DA CHAY 30-31/10 (giu de doi chieu). Co vong cho log cua buoc truoc;
# chay lai thi dung experiments/chay_lai.sh.
# Buổi 2 (30/10 chiều): kiểm B0 với translate.py mới → train lại V1, V2 bằng train_lora.py đã sửa → đánh giá đủ 4 tập.
# Chạy lại an toàn: mỗi bước bỏ qua phần đã xong (resume).
source "$(dirname "$0")/../../env/env.sh"; cd "$T"
MTREV=ae7baa85da07dbe8e23ac26a9f5ef560c17e2138
ev() {  # ev <hệ> <adapter|""> <tập...>
  local v=$1 ad=$2; shift 2
  for d in "$@"; do
    [ -f runs/mt/$v/$d/score.json ] && { echo "$(date +%H:%M:%S) bo qua $v/$d (da co)"; continue; }
    $P scripts/mt/translate.py --input runs/mt_data/$d.jsonl --out_dir runs/mt/$v/$d --revision $MTREV ${ad:+--adapter $ad} 2>&1 | grep -E "BLEU|Error|Traceback" | sed "s|^|$v $d |"
  done
}
echo "$(date +%H:%M:%S) START kiem B0 voi translate.py moi (dev cascade)"
ev B0_kiemtra "" fleurs_dev_asr_pho
$P - <<'PY'
import json
a=[json.loads(l) for l in open("runs/mt/B0/fleurs_dev_asr_pho/hyp.jsonl",encoding="utf-8")]; b={json.loads(l)["id"]:json.loads(l)["hyp"] for l in open("runs/mt/B0_kiemtra/fleurs_dev_asr_pho/hyp.jsonl",encoding="utf-8")}
print("B0 cu vs moi: giong", sum(r["hyp"]==b[r["id"]] for r in a), "/", len(a))
PY
train() {  # train <V> <file train...>
  local v=$1; shift
  echo "$(date +%H:%M:%S) START train $v"
  $P scripts/mt/train_lora.py --train "$@" --dev runs/mt_data/fleurs_dev_asr_pho.jsonl --out_dir checkpoints/$v --revision $MTREV \
     --epochs 5 --lr 2e-4 --batch_size 4 --grad_accum 4 --lora_r 16 --lora_alpha 32 --seed 42 --resume > logs/train_$v.log 2>&1 || { echo "TRAIN_FAIL $v"; tail -15 logs/train_$v.log; exit 1; }
  grep -E "^best" logs/train_$v.log | cut -c1-300
  echo "$(date +%H:%M:%S) END train $v"
}
train V1 runs/mt_data/fleurs_train_asr_pho.jsonl
ev V1 checkpoints/V1/best fleurs_dev_asr_pho fleurs_test_asr_pho fleurs_test_clean fleurs_dev_clean phomt_test
train V2 runs/mt_data/fleurs_train_asr_pho.jsonl runs/mt_data/phomt_train_mix.jsonl
ev V2 checkpoints/V2/best fleurs_dev_asr_pho fleurs_test_asr_pho fleurs_test_clean fleurs_dev_clean phomt_test
ev B0 "" fleurs_dev_clean
echo "$(date +%H:%M:%S) DEM2_DONE"
