# Task 2 · buổi 2: V2b (V2 + cân bằng theo câu, mục 1.4) và V3 (chuẩn hóa số trước khi dịch).
# Mọi quyết định dựa trên dev: dùng V3 chỉ khi chuẩn hóa số tăng BLEU trên FLEURS dev; V2b được nhận chỉ khi
# hơn V2 trên FLEURS dev và PhoMT dev không giảm quá 1 điểm so với B0 (cùng quy tắc với buổi 1).
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$py = if ($env:TASK2_PY) { $env:TASK2_PY } else { 'python' }
$phomt = if ($env:PHOMT_ROOT) { $env:PHOMT_ROOT } else { 'data\phomt\PhoMT' }
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -FilePath reports\task2\logs\queue.log -Append }
function Run($name, [scriptblock]$b) { Log "START $name"; & $b; if ($LASTEXITCODE -ne 0) { Log "FAIL $name"; exit 1 }; Log "DONE $name" }
while (-not (Test-Path checkpoints\v2b\best.json)) { Start-Sleep 20 }
while (Get-Process python -ErrorAction SilentlyContinue | Where-Object { $_.CommandLine -like '*train_lora*' }) { Start-Sleep 5 }
Copy-Item checkpoints\v2b\log.jsonl reports\task2\mt\train_log_V2b.jsonl -Force
Copy-Item checkpoints\v2b\config.json reports\task2\mt\train_config_V2b.json -Force

# 1. V3 có giúp không? (FLEURS dev, bản V2)
Run 'dev V2' { & $py -X utf8 -u src\mt\eval_dev.py --name V2 --adapter checkpoints/v2/best_adapter *>> reports\task2\logs\dev_eval.log }
Run 'dev V2+ITN' { & $py -X utf8 -u src\mt\eval_dev.py --name V2_itn --adapter checkpoints/v2/best_adapter --itn *>> reports\task2\logs\dev_eval.log }

# 2. V2b: test + PhoMT dev cho quy tắc chọn bản cuối
Run 'eval V2b' { & $py -X utf8 -u src\mt\eval_mt.py --name V2b --adapter checkpoints/v2b/best_adapter *>> reports\task2\logs\eval_V2b.log }
Run 'PhoMT dev V2b' { & $py -X utf8 -u src\mt\eval_phomt_dev.py --versions B0,V2b --out reports/task2/mt/phomt_dev_V2b.json *>> reports\task2\logs\select_final.log }

# 3. bản nền cho V3 = bản cuối theo dev (V2, hoặc V2b nếu V2b đạt quy tắc và hơn V2 trên FLEURS dev)
$sel = Get-Content reports\task2\mt\phomt_dev_V2b.json -Raw | ConvertFrom-Json
$v2dev = (Get-Content checkpoints\v2\best.json -Raw | ConvertFrom-Json).dev_bleu
$v2bdev = (Get-Content checkpoints\v2b\best.json -Raw | ConvertFrom-Json).dev_bleu
$v2bok = ($sel.V2b.BLEU -ge ($sel.B0.BLEU - 1.0)) -and ($v2bdev -gt $v2dev)
$base = if ($v2bok) { 'V2b' } else { 'V2' }
Log "BASE for V3 = $base (FLEURS dev V2 $v2dev, V2b $v2bdev; PhoMT dev B0 $($sel.B0.BLEU), V2b $($sel.V2b.BLEU))"
$d0 = (Get-Content reports\task2\mt\dev_V2.json -Raw | ConvertFrom-Json).BLEU
$d1 = (Get-Content reports\task2\mt\dev_V2_itn.json -Raw | ConvertFrom-Json).BLEU
Log "ITN on FLEURS dev (V2): $d0 -> $d1"
if ($d1 -gt $d0) {
    Run 'eval V3' { & $py -X utf8 -u src\mt\eval_mt.py --name V3 --adapter "checkpoints/$($base.ToLower())/best_adapter" --itn --skip-clean --base-version $base *>> reports\task2\logs\eval_V3.log }
    $vers = 'B0,V1,V2,V2b,V3'
} else { Log 'V3 not adopted: ITN did not improve FLEURS dev'; $vers = 'B0,V1,V2,V2b' }

& $py -X utf8 src\eval\summarize.py --versions $vers *>> reports\task2\logs\summarize.log
foreach ($v in ($vers.Split(',') | Where-Object { $_ -in 'V2b', 'V3' })) {
    & $py -X utf8 src\eval\mt_errors.py --new $v *>> "reports\task2\logs\mt_errors_$v.log"
    & $py -X utf8 src\eval\significance.py --new $v *>> "reports\task2\logs\significance_$v.log"
}
& $py -X utf8 src\utils\evidence.py *>> reports\task2\logs\evidence.log
Log 'V3 QUEUE COMPLETE'
