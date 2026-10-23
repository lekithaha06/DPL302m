# Task 2 · kiểm chứng độ ổn định theo seed: train lại V3 với seed 13 và 7 (mọi thứ khác giữ nguyên), chấm trên FLEURS test.
# Chỉ để báo độ dao động (trung bình ± độ lệch chuẩn); không dùng để chọn mô hình, bản cuối vẫn là V3 seed 42 chọn trên dev.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$py = if ($env:TASK2_PY) { $env:TASK2_PY } else { 'python' }
$deadline = if ($env:TASK2_DEADLINE) { [datetime]::ParseExact($env:TASK2_DEADLINE, 'HH:mm', $null) } else { [datetime]::MaxValue }
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -FilePath reports\task2\logs\queue.log -Append }
foreach ($seed in 13, 7) {
    $out = "checkpoints/v3_s$seed"; $name = "V3_s$seed"
    if ((Get-Date) -gt $deadline) { Log "SKIP seed $seed (deadline)"; break }
    if (-not (Test-Path "$out\best.json")) {
        Log "START train $name"
        & $py -X utf8 -u src\mt\train_lora.py --train data/asr/fleurs_train_asr_itn.jsonl data/mt/fleurs_train_clean.jsonl `
            --extra-train data/mt/phomt_train_subset.jsonl --dev data/asr/fleurs_dev_asr_itn.jsonl --out $out --epochs 3 --seed $seed *>> "reports\task2\logs\train_$name.log"
        if ($LASTEXITCODE -ne 0) { Log "FAIL train $name"; exit 1 }
        Log "DONE train $name"
        Copy-Item "$out\log.jsonl" "reports\task2\mt\train_log_$name.jsonl" -Force
    }
    if (-not (Test-Path "reports\task2\mt\eval_$name.json")) {
        Log "START eval $name"
        & $py -X utf8 -u src\mt\eval_mt.py --name $name --adapter "$out/best_adapter" --itn *>> "reports\task2\logs\eval_$name.log"
        if ($LASTEXITCODE -ne 0) { Log "FAIL eval $name"; exit 1 }
        Log "DONE eval $name"
    }
}
Log 'SEEDS QUEUE COMPLETE'
