# Nguon chung cho moi lenh thuc nghiem:  source experiments/env/env.sh
# Ban goc cua Kiet ghi duong dan cung D:/CAIDCM/...; ban nay tu tinh tu vi tri file.
export T="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
export REPO="$(cd "$T/.." && pwd)"
export P="${P:-python}"                      # Windows venv: export P=.venv/Scripts/python.exe
export HF_HUB_CACHE="${HF_HUB_CACHE:-$T/hf_home/hub}"
export HF_HUB_DISABLE_TELEMETRY=1
export PYTHONIOENCODING=utf-8
export PYTHONUTF8=1
export FLEURS_REV=70bb2e84b976b7e960aa89f1c648e09c59f894dd
export VIVOS_REV=3cbfb2502e5e84776b4b778b020a09759f723f52
export ASR_REV=a86b604c346caf7148c37512eafe783a16420adb
export WSP_REV=973afd24965f72e36ca33b3055d56a652f456b4d
export MTREV=ae7baa85da07dbe8e23ac26a9f5ef560c17e2138
# adapter V3/V4 nam o checkpoints/ cua repo; V1/V2 trong goi task3 cua Kiet
export AD="$REPO/checkpoints"
