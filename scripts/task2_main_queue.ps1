# Task 2 · hàng đợi chính sau khi có chữ máy nghe train/dev: V1 eval → V2 train → B0 rescore → V2 eval → tổng hợp → đo tốc độ.
# Mọi phiên bản (B0, V1, V2) chấm bằng cùng src/mt/eval_mt.py, cùng cấu hình giải mã và cùng tập test.
# Bước nào xong (có file kết quả) thì bỏ qua; không bắt đầu bước mới sau giờ $env:TASK2_DEADLINE (HH:mm).
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$py = if ($env:TASK2_PY) { $env:TASK2_PY } else { 'python' }
$phomt = if ($env:PHOMT_ROOT) { $env:PHOMT_ROOT } else { 'data\phomt\PhoMT' }
$deadline = if ($env:TASK2_DEADLINE) { [datetime]::ParseExact($env:TASK2_DEADLINE, 'HH:mm', $null) } else { [datetime]::MaxValue }
if ($deadline -lt (Get-Date).AddHours(-12)) { $deadline = $deadline.AddDays(1) }
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -FilePath reports\task2\logs\queue.log -Append }
function Step($name, $done, [scriptblock]$run) {
    if (& $done) { return }
    if ((Get-Date) -gt $deadline) { Log "SKIP $name (deadline)"; exit 0 }
    Log "START $name"; & $run
    if ($LASTEXITCODE -ne 0) { Log "FAIL $name"; exit 1 }
    Log "DONE $name"
}

Step 'eval V1' { Test-Path reports\task2\mt\eval_V1.json } {
    & $py -X utf8 -u src\mt\eval_mt.py --name V1 --adapter checkpoints/v1/best_adapter --phomt $phomt *>> reports\task2\logs\eval_V1.log }
Copy-Item checkpoints\v1\log.jsonl reports\task2\mt\train_log_V1.jsonl -Force
Copy-Item checkpoints\v1\config.json reports\task2\mt\train_config_V1.json -Force

Step 'train V2' { Test-Path checkpoints\v2\best.json } {
    & $py -X utf8 -u src\mt\train_lora.py --train data/asr/fleurs_train_asr.jsonl data/mt/fleurs_train_clean.jsonl `
        --extra-train data/mt/phomt_train_subset.jsonl --dev data/asr/fleurs_dev_asr.jsonl --out checkpoints/v2 --epochs 3 *>> reports\task2\logs\train_V2.log }
Copy-Item checkpoints\v2\log.jsonl reports\task2\mt\train_log_V2.jsonl -Force
Copy-Item checkpoints\v2\config.json reports\task2\mt\train_config_V2.json -Force

# B0 rescored on FLEURS only here (4 min); its PhoMT rescore (~29 min) runs last if time allows (eval_B0_full.json),
# otherwise the PhoMT number of B0 comes from the Task 2 run with the earlier batching (eval_B0_batch32.json).
Step 'eval B0' { Test-Path reports\task2\mt\eval_B0.json } {
    & $py -X utf8 -u src\mt\eval_mt.py --name B0 *>> reports\task2\logs\eval_B0.log }
Step 'eval V2' { Test-Path reports\task2\mt\eval_V2.json } {
    & $py -X utf8 -u src\mt\eval_mt.py --name V2 --adapter checkpoints/v2/best_adapter --phomt $phomt *>> reports\task2\logs\eval_V2.log }

& $py -X utf8 src\eval\summarize.py --versions B0,V1,V2 *>> reports\task2\logs\summarize.log
foreach ($v in 'V1', 'V2') {
    & $py -X utf8 src\eval\mt_errors.py --new $v *>> "reports\task2\logs\mt_errors_$v.log"
    & $py -X utf8 src\eval\significance.py --new $v *>> reports\task2\logs\significance.log
}
Log 'ANALYSIS COMPLETE'

# phiên bản cuối chọn theo dev BLEU (không nhìn test)
$b1 = (Get-Content checkpoints\v1\best.json -Raw | ConvertFrom-Json).dev_bleu
$b2 = (Get-Content checkpoints\v2\best.json -Raw | ConvertFrom-Json).dev_bleu
$final = if ($b2 -gt $b1) { 'v2' } else { 'v1' }
Log "FINAL by dev BLEU: $final (V1 dev $b1, V2 dev $b2)"
$env:PYTHONPATH = 'src\system'
Step 'speed B0' { Test-Path reports\task2\system\speed_B0.json } {
    & $py -X utf8 -u src\system\measure_speed.py --name B0 *>> reports\task2\logs\speed.log }
Step "speed $final" { Test-Path "reports\task2\system\speed_final.json" } {
    & $py -X utf8 -u src\system\measure_speed.py --name final --adapter "checkpoints/$final/best_adapter" *>> reports\task2\logs\speed.log }
Step 'eval B0 PhoMT rescore' { Test-Path reports\task2\mt\eval_B0_full.json } {
    & $py -X utf8 -u src\mt\eval_mt.py --name B0_full --phomt $phomt *>> reports\task2\logs\eval_B0_full.log }
& $py -X utf8 src\eval\summarize.py --versions B0,V1,V2 *>> reports\task2\logs\summarize.log
Log 'MAIN QUEUE COMPLETE'
