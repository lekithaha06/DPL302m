#!/bin/bash
# 04/11/2026 – đo cả hệ sản phẩm (repo cuối, adapter mặc định V2) trên 857 bản FLEURS test + nghiệm thu model thật.
# Kết quả chép vào task3/reports/he_thong_V2/ (giống reports/he_thong/ của lần đo V4 ngày 03/11).
T=/d/CAIDCM/teamwork/task3; R=/d/CAIDCM/teamwork/repo_cuoi; PY=/d/CAIDCM/teamwork/kiem_repo_asr/.venv/Scripts/python.exe
export HF_HUB_CACHE=$T/hf_home/hub HF_HUB_OFFLINE=1 ASR_BACKEND=that PYTHONIOENCODING=utf-8 PYTHONDONTWRITEBYTECODE=1
export FLEURS_AUDIO_DIR=$T/data/clean/audio_16k/fleurs/test
unset ADAPTER_PATH
cd $R
echo "$(date +%H:%M:%S) BAT_DAU danh_gia_proposed (V2 mặc định)"
$PY -X utf8 tests/danh_gia_proposed.py --tap test 2>&1 | grep -v -E "Warning|warn\(|forced_decoder|attention mask|fget" | tail -25
D=$(ls -td danh_gia/*/ | head -1); echo "thư mục: $D"
mkdir -p $T/reports/he_thong_V2 && cp -p $D/ket_qua.json $D/bang.md $D/du_doan_*.jsonl $T/reports/he_thong_V2/
cp -p configs/ban_chot.json $T/reports/he_thong_V2/
$T/env/.venv/Scripts/python.exe -X utf8 $T/scripts/he_thong_bootstrap.py he_thong_V2
echo "$(date +%H:%M:%S) BAT_DAU nghiem_thu_that (V2)"
A=/d/CAIDCM/teamwork/kiem_repo_asr2/audio_thay_the
$PY -X utf8 tests/nghiem_thu_that.py --audio $A/dev1_16525570830762756295.wav $A/dev2_13754775770768255557.wav $A/dev3_15730294784062856962.wav 2>&1 | grep -E "^\[|DAT|bang" | tail -12
N=$(ls -td nghiem_thu/*/ | head -1); mkdir -p $T/reports/he_thong_V2/nghiem_thu && cp -p $N/* $T/reports/he_thong_V2/nghiem_thu/
echo "$(date +%H:%M:%S) HE_THONG_V2_XONG"
