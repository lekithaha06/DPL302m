# Task 2 · V1: chờ có đủ chữ máy nghe FLEURS train/dev, rồi train LoRA V1, chấm trên test, lập bảng và phân tích lỗi.
# Chạy lại cùng lệnh sau khi tắt máy: train_lora.py tự tiếp tục từ epoch đã lưu; bước nào xong rồi thì bỏ qua.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$py = if ($env:TASK2_PY) { $env:TASK2_PY } else { 'python' }
$phomt = $env:PHOMT_ROOT
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -FilePath reports\task2\logs\queue.log -Append }
$need = (Get-Content data\processed\fleurs_vi_en_train.json -Raw | ConvertFrom-Json).Count
while (((Get-Content data\asr\fleurs_train_asr.jsonl -ErrorAction SilentlyContinue | Measure-Object -Line).Lines) -lt $need) { Start-Sleep 60 }
while (Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*transcribe_fleurs*' }) { Start-Sleep 10 }

if (-not (Test-Path checkpoints\v1\best.json)) {
    Log 'START train V1'
    & $py -X utf8 -u src\mt\train_lora.py --train data/asr/fleurs_train_asr.jsonl --dev data/asr/fleurs_dev_asr.jsonl --out checkpoints/v1 --epochs 5 *>> reports\task2\logs\train_V1.log
    if ($LASTEXITCODE -ne 0) { Log 'FAIL train V1'; exit 1 }
    Log 'DONE train V1'
}
if (-not (Test-Path reports\task2\mt\eval_V1.json)) {
    Log 'START eval V1'
    & $py -X utf8 -u src\mt\eval_mt.py --name V1 --adapter checkpoints/v1/best_adapter --phomt $phomt *>> reports\task2\logs\eval_V1.log
    if ($LASTEXITCODE -ne 0) { Log 'FAIL eval V1'; exit 1 }
    Log 'DONE eval V1'
}
Copy-Item checkpoints\v1\log.jsonl reports\task2\mt\train_log_V1.jsonl -Force
Copy-Item checkpoints\v1\config.json reports\task2\mt\train_config_V1.json -Force
& $py -X utf8 src\eval\summarize.py --versions B0,V1 *>> reports\task2\logs\summarize.log
& $py -X utf8 src\eval\mt_errors.py --new V1 *>> reports\task2\logs\mt_errors_V1.log
Log 'V1 QUEUE COMPLETE'
