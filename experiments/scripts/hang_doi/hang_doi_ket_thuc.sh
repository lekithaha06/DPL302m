#!/bin/bash
# BAN LUU: day la hang doi Kiet DA CHAY 30-31/10 (giu de doi chieu). Co vong cho log cua buoc truoc;
# chay lai thi dung experiments/chay_lai.sh.
# Bước cuối phần chạy máy: chọn bản cuối theo BLEU dev cascade (translate.py) trong V1..V4, đo tốc độ bản cuối (nếu chưa đo),
# bootstrap so với B0 và với V-trước, chấm theo miền, tổng hợp bảng/biểu đồ, bảng ASR; rồi dừng theo dõi tài nguyên.
source "$(dirname "$0")/../../env/env.sh"; cd "$T"
until grep -qE "DEM2C_DONE|TRAIN_FAIL" logs/hang_doi_dem2c.log; do sleep 20; done
FINAL=$($P - <<'PY'
import json, pathlib
s = {v: json.loads(pathlib.Path(f"runs/mt/{v}/fleurs_dev_asr_pho/score.json").read_text(encoding="utf-8"))["BLEU"]
     for v in ("V1", "V2", "V3", "V4") if pathlib.Path(f"runs/mt/{v}/fleurs_dev_asr_pho/score.json").exists()}
print(max(sorted(s), key=lambda v: s[v]))
PY
)
echo "$(date +%H:%M:%S) BAN_CUOI theo dev = $FINAL" | tee reports/tong_hop/ban_cuoi.txt
[ -f reports/toc_do/toc_do_$FINAL.json ] || $P scripts/mt/do_toc_do.py --n 100 --out reports/toc_do/toc_do_$FINAL.json --adapter checkpoints/$FINAL/best 2>&1 | tail -1 | cut -c1-300
prev=B0; for v in V1 V2 V3 V4; do [ -f runs/mt/$v/fleurs_test_asr_pho/hyp.jsonl ] || continue
  for a in B0 $prev; do [ $a = $v ] && continue; o=reports/mt/bootstrap_${a}_${v}_cascade_test.json
    $P scripts/mt/bootstrap.py --a runs/mt/$a/fleurs_test_asr_pho/hyp.jsonl --b runs/mt/$v/fleurs_test_asr_pho/hyp.jsonl --data runs/mt_data/fleurs_test_asr_pho.jsonl --out $o --n 1000 | grep -o '"delta.*"p_one_sided_delta_le_0": [0-9.]*' | sed "s|^|$a→$v |"; done
  prev=$v; done
for v in V2 V3 V4; do [ -f runs/mt/$v/fleurs_dev_asr_pho/hyp.jsonl ] && $P scripts/mt/failure_analysis.py --a runs/mt/B0/fleurs_dev_asr_pho/hyp.jsonl --b runs/mt/$v/fleurs_dev_asr_pho/hyp.jsonl --b_name $v --asr_score runs/asr/kiet_t2_phowhisper-small_fleurs_dev/score/per_utterance.csv --out reports/mt/failure_${v}_dev.md > /dev/null; done
$P scripts/cham_theo_mien.py > /dev/null && echo "cham theo mien xong"
$P scripts/asr/tong_hop_asr.py; $P scripts/asr/error_audit.py
$P scripts/ve_bieu_do.py
touch logs/DUNG_THEO_DOI
echo "$(date +%H:%M:%S) CHAY_MAY_XONG"
