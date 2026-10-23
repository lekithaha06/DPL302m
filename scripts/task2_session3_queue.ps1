# Task 2 · buổi 3:
#  1. V3 = V2 nhưng chữ máy nghe được chuẩn hóa số (src/text/itn_vi.py) cả khi dạy lẫn khi dịch (V3 ở buổi 2 chỉ chuẩn hóa khi dịch
#     và làm dev giảm). Nhận V3 khi BLEU FLEURS dev (cùng script eval_dev.py) cao hơn V2 và PhoMT dev không giảm quá 1 so với B0.
#  2. Chấm lại B0 trên PhoMT test cùng cấu hình giải mã với các phiên bản V.
#  3. Baseline A trên FLEURS test cho PhoWhisper-small và Whisper-small bằng cùng script với VIVOS.
# Bước nào xong thì bỏ qua; không bắt đầu bước mới sau $env:TASK2_DEADLINE (HH:mm).
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$py = if ($env:TASK2_PY) { $env:TASK2_PY } else { 'python' }
$phomt = if ($env:PHOMT_ROOT) { $env:PHOMT_ROOT } else { 'data\phomt\PhoMT' }
$deadline = if ($env:TASK2_DEADLINE) { [datetime]::ParseExact($env:TASK2_DEADLINE, 'HH:mm', $null) } else { [datetime]::MaxValue }
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -FilePath reports\task2\logs\queue.log -Append }
function Step($name, $done, [scriptblock]$run) {
    if (& $done) { return }
    if ((Get-Date) -gt $deadline) { Log "SKIP $name (deadline)"; return }
    Log "START $name"; & $run
    if ($LASTEXITCODE -ne 0) { Log "FAIL $name"; exit 1 }
    Log "DONE $name"
}

# ---- 1. V3
Step 'train V3' { Test-Path checkpoints\v3\best.json } {
    & $py -X utf8 -u src\mt\train_lora.py --train data/asr/fleurs_train_asr_itn.jsonl data/mt/fleurs_train_clean.jsonl `
        --extra-train data/mt/phomt_train_subset.jsonl --dev data/asr/fleurs_dev_asr_itn.jsonl --out checkpoints/v3 --epochs 3 *>> reports\task2\logs\train_V3.log }
if (Test-Path checkpoints\v3\best.json) {
    Copy-Item checkpoints\v3\log.jsonl reports\task2\mt\train_log_V3.jsonl -Force
    Copy-Item checkpoints\v3\config.json reports\task2\mt\train_config_V3.json -Force
}
Step 'dev V3' { Test-Path reports\task2\mt\dev_V3.json } {
    & $py -X utf8 -u src\mt\eval_dev.py --name V3 --adapter checkpoints/v3/best_adapter --itn *>> reports\task2\logs\dev_eval.log }
Step 'PhoMT dev V3' { Test-Path reports\task2\mt\phomt_dev_V3.json } {
    & $py -X utf8 -u src\mt\eval_phomt_dev.py --versions B0,V3 --out reports/task2/mt/phomt_dev_V3.json *>> reports\task2\logs\select_final.log }
$adopt = $false
if ((Test-Path reports\task2\mt\dev_V3.json) -and (Test-Path reports\task2\mt\phomt_dev_V3.json)) {
    $dv2 = (Get-Content reports\task2\mt\dev_V2.json -Raw | ConvertFrom-Json).BLEU
    $dv3 = (Get-Content reports\task2\mt\dev_V3.json -Raw | ConvertFrom-Json).BLEU
    $pd = Get-Content reports\task2\mt\phomt_dev_V3.json -Raw | ConvertFrom-Json
    $adopt = ($dv3 -gt $dv2) -and ($pd.V3.BLEU -ge ($pd.B0.BLEU - 1.0))
    Log "V3 decision on dev: FLEURS dev V2 $dv2 vs V3 $dv3; PhoMT dev B0 $($pd.B0.BLEU) vs V3 $($pd.V3.BLEU) -> adopt=$adopt"
}
if ($adopt) {
    Step 'eval V3' { Test-Path reports\task2\mt\eval_V3.json } {
        & $py -X utf8 -u src\mt\eval_mt.py --name V3 --adapter checkpoints/v3/best_adapter --itn --phomt $phomt *>> reports\task2\logs\eval_V3.log }
}

# ---- 2. B0 trên PhoMT test, cùng cấu hình giải mã
Step 'eval B0 PhoMT rescore' { Test-Path reports\task2\mt\eval_B0_full.json } {
    & $py -X utf8 -u src\mt\eval_mt.py --name B0_full --phomt $phomt *>> reports\task2\logs\eval_B0_full.log }

# ---- 3. Baseline A trên FLEURS test
Step 'baseline A on FLEURS' { (Test-Path reports\task2\asr\fleurs\baseline_asr.json) -and ((Get-Content reports\task2\asr\fleurs\baseline_asr.json -Raw) -match '"status": "completed"') } {
    & $py -X utf8 -u src\asr\evaluate_asr_gpu.py --manifest data/fleurs_test_asr/manifest.jsonl --output reports/task2/asr/fleurs/baseline_asr.json *>> reports\task2\logs\baseline_a_fleurs.log }

# ---- tổng hợp
$vers = if (Test-Path reports\task2\mt\eval_V3.json) { 'B0,V1,V2,V2b,V3' } else { 'B0,V1,V2,V2b' }
& $py -X utf8 src\eval\summarize.py --versions $vers *>> reports\task2\logs\summarize.log
if (Test-Path reports\task2\mt\eval_V3.json) {
    & $py -X utf8 src\eval\mt_errors.py --new V3 *>> reports\task2\logs\mt_errors_V3.log
    & $py -X utf8 src\eval\significance.py --new V3 *>> reports\task2\logs\significance_V3.log
}
& $py -X utf8 src\utils\evidence.py *>> reports\task2\logs\evidence.log
Log 'SESSION 3 QUEUE COMPLETE'
