#!/bin/bash
# Chay lai thuc nghiem Task 2 theo dung thu tu, dung lenh va sieu tham so Kiet da chay 30-31/10/2026.
#   bash experiments/chay_lai.sh nho       # mau nho: 20 cau, 1 epoch, ~10 phut tren GPU 8 GB, KHONG dung de bao cao
#   bash experiments/chay_lai.sh day_du    # toan bo: tai ~12 GB du lieu + ~4 GB model, train V1-V4 (~1 gio)
#   bash experiments/chay_lai.sh cham      # chi cham lai tu du doan co san (khong can GPU) -> so khop bao cao
# Moi buoc bo qua phan da co, nen chay lai sau khi dung giua chung an toan.
set -euo pipefail
source "$(dirname "$0")/env/env.sh"; cd "$T"
CHE_DO=${1:-cham}

if [ "$CHE_DO" = cham ]; then
  # WER/CER 4 baseline ASR + BLEU/chrF++ moi he dich, tu file du doan trong runs/
  for rid in phowhisper-small_vivos phowhisper-small_fleurs whisper-small_vivos whisper-small_fleurs; do
    ds=${rid##*_}; out=runs/cham_lai/asr_$rid; rm -rf "$out"
    $P scripts/asr/score_asr.py --predictions runs/asr/kiet_t2_${rid}_test/predictions.jsonl \
      --manifest runs/manifests/asr_${ds}_test.jsonl --out "$out" --run-id cham_lai_$rid > /dev/null
    $P -c "import json;d=json.load(open('$out/summary.json'));print('ASR $rid', round(d['WER_percent'],2), round(d['CER_percent'],2))"
  done
  for v in B0 V1 V2 V3 V4; do for d in fleurs_dev_asr_pho fleurs_test_asr_pho fleurs_test_clean; do
    f=runs/mt/$v/$d/hyp.jsonl; [ -f "$f" ] || continue
    $P "$REPO/src/evaluate.py" --hyp "$f" --metric bleu | $P -c "import json,sys;d=json.load(sys.stdin);print('MT $v $d', d['gia_tri'], d['chrF++'])"
  done; done
  exit 0
fi

LIM=""; EP=5; TAG=""
if [ "$CHE_DO" = nho ]; then LIM="--limit 20"; EP=1; TAG="_nho"; fi

# 0. model (revision co dinh) va kiem moi truong
$P scripts/tai_model.py
$P env/check_env.py

# 1-4. du lieu: tai, ghep/chia FLEURS chong ro ri, lam sach, EDA, can bang (script cua Uyen)
#      PhoMT va FLoRes+ la dataset gated: can `huggingface-cli login` va xin quyen truoc
$P scripts/data/viec1_tai_3_bo_du_lieu.py --data_dir data --report_dir reports/data \
   --fleurs_revision $FLEURS_REV --vivos_revision $VIVOS_REV
$P scripts/data/viec2_ghep_chia_fleurs_chong_trung.py --data_dir data --report_dir reports/data --revision $FLEURS_REV --with_test_audio ${LIM}
$P scripts/data/viec2_lam_sach_du_lieu.py --data_dir data --report_dir reports/data ${LIM}
$P scripts/data/viec3_eda.py --data_dir data --report_dir reports/data
$P scripts/data/viec4_can_bang_du_lieu.py --data_dir data --report_dir reports/data --seed 42
$P scripts/asr/make_asr_manifest.py --clean_dir data/clean --out_dir runs/manifests
$P scripts/data/gan_mien_flores.py          # can manifest o buoc tren

# 5. ASR baseline (protocol bao_asr_v1_20261027: beam 5, suppress tokens chung)
for m in "vinai/PhoWhisper-small $ASR_REV phowhisper-small" "openai/whisper-small $WSP_REV whisper-small"; do
  set -- $m
  for ds in vivos_test fleurs_test fleurs_dev fleurs_train; do
    rid=kiet_t2_${3}_${ds}${TAG}
    $P scripts/asr/run_asr.py --model $1 --revision $2 --manifest runs/manifests/asr_${ds}.jsonl \
       --out_dir runs/asr/$rid --run_id $rid ${LIM}
  done
done

# 6. du lieu dich: cap sach + loi ASR cua PhoWhisper
$P scripts/mt/make_mt_data.py --phomt --asr \
   test:pho:runs/asr/kiet_t2_phowhisper-small_fleurs_test${TAG}/predictions.jsonl \
   dev:pho:runs/asr/kiet_t2_phowhisper-small_fleurs_dev${TAG}/predictions.jsonl \
   train:pho:runs/asr/kiet_t2_phowhisper-small_fleurs_train${TAG}/predictions.jsonl
$P scripts/mt/make_balanced_data.py

# 7. B0 + LoRA V1-V4 (sieu tham so: configs/mt/V*.json; seed 42)
D=runs/mt_data
ev() { local v=$1 ad=$2; for d in fleurs_dev_asr_pho fleurs_test_asr_pho fleurs_test_clean fleurs_dev_clean; do
  $P scripts/mt/translate.py --input $D/$d.jsonl --out_dir runs/mt/$v$TAG/$d --revision $MTREV ${ad:+--adapter $ad} ${LIM}; done; }
tr() { local v=$1 lr=$2; shift 2
  $P scripts/mt/train_lora.py --train "$@" --dev $D/fleurs_dev_asr_pho.jsonl --out_dir checkpoints/$v$TAG \
     --revision $MTREV --epochs $EP --lr $lr --batch_size 4 --grad_accum 4 --lora_r 16 --lora_alpha 32 --seed 42 --resume; }
ev B0 ""
tr V1 2e-4 $D/fleurs_train_asr_pho.jsonl;                                   ev V1 checkpoints/V1$TAG/best
tr V2 2e-4 $D/fleurs_train_asr_pho.jsonl $D/phomt_train_mix.jsonl;         ev V2 checkpoints/V2$TAG/best
tr V3 2e-4 $D/fleurs_train_asr_pho_canbang.jsonl $D/phomt_train_mix.jsonl; ev V3 checkpoints/V3$TAG/best
tr V4 5e-5 $D/fleurs_train_asr_pho_canbang.jsonl $D/phomt_train_mix.jsonl; ev V4 checkpoints/V4$TAG/best

# 8. kiem dinh + toc do (chi y nghia khi day_du)
if [ "$CHE_DO" = day_du ]; then
  $P scripts/mt/bootstrap.py --a runs/mt/B0/fleurs_test_asr_pho/hyp.jsonl --b runs/mt/V4/fleurs_test_asr_pho/hyp.jsonl \
     --data $D/fleurs_test_asr_pho.jsonl --out reports/mt/bootstrap_B0_V4_cascade_test.json --n 1000
  $P scripts/mt/do_toc_do.py --n 100 --out reports/toc_do/toc_do_V4.json --adapter checkpoints/V4/best
  $P scripts/cham_theo_mien.py
fi
echo XONG $CHE_DO
