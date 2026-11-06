#!/bin/bash
# BAN LUU: day la hang doi Kiet DA CHAY 30-31/10 (giu de doi chieu). Co vong cho log cua buoc truoc;
# chay lai thi dung experiments/chay_lai.sh.
# Đo lặp tốc độ xen kẽ B0 / bản cuối (cùng khoảng thời gian, cùng 100 bản thu) để so công bằng; báo cáo trung vị 3 lần.
source "$(dirname "$0")/../../env/env.sh"; cd "$T"
until grep -qE "BO_SUNG_XONG" logs/hang_doi_bo_sung.log 2>/dev/null; do sleep 15; done
FINAL=$(awk '{print $NF}' reports/tong_hop/ban_cuoi.txt)
for k in 1 2 3; do for v in B0 $FINAL; do
  ad=""; [ $v != B0 ] && ad="--adapter checkpoints/$v/best"
  echo "$(date +%H:%M:%S) lan $k $v"
  $P scripts/mt/do_toc_do.py --n 100 --out reports/toc_do/lap/toc_do_${v}_lan$k.json $ad 2>&1 | tail -1 | grep -o '"RTF_total": [0-9.]*, "RTF_asr": [0-9.]*, "RTF_mt": [0-9.]*, "latency_p50_s": [0-9.]*, "latency_p95_s": [0-9.]*'
done; done
echo "$(date +%H:%M:%S) LAP_XONG"
