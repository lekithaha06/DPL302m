# Task 2 · V2 (sau phân tích V1): V1 overfit từ epoch 2 vì chỉ có 2.927 cặp. V2 chỉ đổi dữ liệu dạy:
# thêm cặp chữ chuẩn FLEURS train (1.449) + 3.000 cặp PhoMT train (seed 42) để giảm overfit và giữ khả năng dịch văn bản sạch.
# Giữ nguyên LoRA, learning rate, batch, seed; chọn epoch trên cùng tập dev (chữ máy nghe FLEURS dev).
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$py = if ($env:TASK2_PY) { $env:TASK2_PY } else { 'python' }
$phomt = $env:PHOMT_ROOT
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -FilePath reports\task2\logs\queue.log -Append }
while (-not ((Get-Content reports\task2\logs\queue.log -Raw) -match 'V1 QUEUE COMPLETE')) { Start-Sleep 30 }

if (-not (Test-Path checkpoints\v2\best.json)) {
    Log 'START train V2'
    & $py -X utf8 -u src\mt\train_lora.py --train data/asr/fleurs_train_asr.jsonl data/mt/fleurs_train_clean.jsonl `
        --extra-train data/mt/phomt_train_subset.jsonl --dev data/asr/fleurs_dev_asr.jsonl --out checkpoints/v2 --epochs 3 *>> reports\task2\logs\train_V2.log
    if ($LASTEXITCODE -ne 0) { Log 'FAIL train V2'; exit 1 }
    Log 'DONE train V2'
}
if (-not (Test-Path reports\task2\mt\eval_V2.json)) {
    Log 'START eval V2'
    & $py -X utf8 -u src\mt\eval_mt.py --name V2 --adapter checkpoints/v2/best_adapter --phomt $phomt *>> reports\task2\logs\eval_V2.log
    if ($LASTEXITCODE -ne 0) { Log 'FAIL eval V2'; exit 1 }
    Log 'DONE eval V2'
}
Copy-Item checkpoints\v2\log.jsonl reports\task2\mt\train_log_V2.jsonl -Force
Copy-Item checkpoints\v2\config.json reports\task2\mt\train_config_V2.json -Force
& $py -X utf8 src\eval\summarize.py --versions B0,V1,V2 *>> reports\task2\logs\summarize.log
& $py -X utf8 src\eval\mt_errors.py --new V2 *>> reports\task2\logs\mt_errors_V2.log
& $py -X utf8 src\eval\significance.py --new V2 *>> reports\task2\logs\significance.log
Log 'V2 QUEUE COMPLETE'
