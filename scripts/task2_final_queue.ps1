# Task 2 · bước cuối: chọn bản cuối trên PhoMT dev (validation) → đo tốc độ B0 và bản cuối (GPU rảnh)
# → chấm lại B0 trên PhoMT test cùng cấu hình (nếu còn trước giờ chốt).
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$py = if ($env:TASK2_PY) { $env:TASK2_PY } else { 'python' }
$phomt = if ($env:PHOMT_ROOT) { $env:PHOMT_ROOT } else { 'data\phomt\PhoMT' }
$deadline = [datetime]::ParseExact($env:TASK2_DEADLINE, 'HH:mm', $null)
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -FilePath reports\task2\logs\queue.log -Append }

if (-not (Test-Path reports\task2\mt\phomt_dev_selection.json)) {
    Log 'START select final on PhoMT dev'
    & $py -X utf8 -u src\mt\eval_phomt_dev.py --phomt $phomt *>> reports\task2\logs\select_final.log
    if ($LASTEXITCODE -ne 0) { Log 'FAIL select final'; exit 1 }
    Log 'DONE select final'
}
$final = (Get-Content reports\task2\mt\phomt_dev_selection.json -Raw | ConvertFrom-Json).final.ToLower()
Log "FINAL = $final"
$env:PYTHONPATH = 'src\system'
foreach ($s in @(@('B0', ''), @('final', "checkpoints/$final/best_adapter"))) {
    if (Test-Path "reports\task2\system\speed_$($s[0]).json") { continue }
    Log "START speed $($s[0])"
    if ($s[1]) { & $py -X utf8 -u src\system\measure_speed.py --name $s[0] --adapter $s[1] *>> reports\task2\logs\speed.log }
    else { & $py -X utf8 -u src\system\measure_speed.py --name $s[0] *>> reports\task2\logs\speed.log }
    if ($LASTEXITCODE -ne 0) { Log "FAIL speed $($s[0])"; exit 1 }
    Log "DONE speed $($s[0])"
}
Log 'SPEED COMPLETE'
if ((Get-Date) -lt $deadline -and -not (Test-Path reports\task2\mt\eval_B0_full.json)) {
    Log 'START eval B0 PhoMT rescore'
    & $py -X utf8 -u src\mt\eval_mt.py --name B0_full --phomt $phomt *>> reports\task2\logs\eval_B0_full.log
    if ($LASTEXITCODE -ne 0) { Log 'FAIL B0 rescore'; exit 1 }
    Log 'DONE eval B0 PhoMT rescore'
}
Log 'FINAL QUEUE COMPLETE'
