# Task 2 GPU queue (one job at a time so timings are clean). Each stage is skipped when its output is complete,
# so the queue can be stopped (machine shut down) and started again with the same command.
$ErrorActionPreference = 'Stop'
$repo = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repo
$py = if ($env:TASK2_PY) { $env:TASK2_PY } else { 'python' }
$phomt = $env:PHOMT_ROOT   # e.g. ...\PhoMT\PhoMT (gated data, kept outside Git)
New-Item -ItemType Directory -Force reports\task2\logs, reports\task2\asr, reports\task2\mt, data\asr | Out-Null
function Log($m) { "$(Get-Date -Format 'yyyy-MM-dd HH:mm:ss') $m" | Tee-Object -FilePath reports\task2\logs\queue.log -Append }
function Lines($f) { if (Test-Path $f) { (Get-Content $f | Measure-Object -Line).Lines } else { 0 } }

# 1. Baseline A: PhoWhisper-small and Whisper-small on VIVOS test (760), same environment as Baseline B
$a = 'reports\task2\asr\baseline_asr.json'
if (-not ((Test-Path $a) -and ((Get-Content $a -Raw) -match '"status": "completed"'))) {
    Log 'START baseline A (VIVOS)'
    & $py -X utf8 -u src\asr\evaluate_asr_gpu.py --output reports/task2/asr/baseline_asr.json *>> reports\task2\logs\baseline_a.log
    if ($LASTEXITCODE -ne 0) { Log 'FAIL baseline A'; exit 1 }
    Log 'DONE baseline A'
}

# 2. Baseline B / B0 cascade, scored by the same script that scores V1..Vn
if (-not (Test-Path reports\task2\mt\eval_B0.json)) {
    Log 'START B0 eval'
    & $py -X utf8 -u src\mt\eval_mt.py --name B0 --phomt $phomt *>> reports\task2\logs\eval_B0.log
    if ($LASTEXITCODE -ne 0) { Log 'FAIL B0'; exit 1 }
    Log 'DONE B0 eval'
}

# 3. PhoWhisper transcripts of FLEURS dev and train = training data for V1 (resumable per utterance)
foreach ($s in 'dev', 'train') {
    $n = (Get-Content "data\processed\fleurs_vi_en_$s.json" -Raw | ConvertFrom-Json).Count
    if ((Lines "data\asr\fleurs_${s}_asr.jsonl") -lt $n) {
        Log "START transcribe $s ($n)"
        & $py -X utf8 -u src\asr\transcribe_fleurs.py --eval-set "data/processed/fleurs_vi_en_$s.json" --output "data/asr/fleurs_${s}_asr.jsonl" *>> "reports\task2\logs\transcribe_$s.log"
        if ($LASTEXITCODE -ne 0) { Log "FAIL transcribe $s"; exit 1 }
        Log "DONE transcribe $s"
    }
}
Log 'QUEUE STAGE 1-3 COMPLETE'
