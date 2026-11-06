#!/bin/bash
# BAN LUU: day la hang doi Kiet DA CHAY 30-31/10 (giu de doi chieu). Co vong cho log cua buoc truoc;
# chay lai thi dung experiments/chay_lai.sh.
# Đo "quên" trên PhoMT test cho V1, V2 sau khi V2 xong. Mỗi lượt ~13 phút; chỉ bắt đầu nếu trước 05:42.
# (Suy luận tất định + resume theo batch cố định → nếu bị dừng, tối mai chạy tiếp cho cùng kết quả.)
source "$(dirname "$0")/../../env/env.sh"; cd "$T"
MTREV=ae7baa85da07dbe8e23ac26a9f5ef560c17e2138
until grep -qE "V2_DONE|KHONG_DU_GIO" logs/hang_doi_v2.log; do sleep 15; done
for v in V1 V2; do
  now=$(date +%H%M); if [ "$now" -gt 0542 ] && [ "$now" -lt 1200 ]; then echo "$(date +%H:%M) KHONG_DU_GIO: $v phomt_test để tối mai"; exit 0; fi
  [ -d checkpoints/$v/best ] || continue
  echo "$(date +%H:%M:%S) START $v phomt_test"
  $P scripts/mt/translate.py --input runs/mt_data/phomt_test.jsonl --out_dir runs/mt/$v/phomt_test --revision $MTREV --adapter checkpoints/$v/best 2>&1 | grep -E "BLEU|Error|Traceback"
done
echo "$(date +%H:%M:%S) PHOMT_DONE"
