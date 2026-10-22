param([int]$Threads = 8, [int]$Limit = 0, [switch]$CPU)
# Baseline A (TV1): PhoWhisper-small vs Whisper-small on the official VIVOS test split (760 utterances).
# Task 1 run: RTX 3050 Laptop 4 GB, torch 2.0.1+cu117, CUDA FP16, batch 1, beam 5 -> PhoWhisper-small WER 6.25%, CER 3.26%.
# Uses its own Python 3.11 environment in .work/ (pinned in src/asr/requirements-asr-gpu.txt), separate from the MT environment.
$ErrorActionPreference = 'Stop'
$repoRoot = Split-Path -Parent $PSScriptRoot
Set-Location -LiteralPath $repoRoot
New-Item -ItemType Directory -Path '.work\tmp' -Force | Out-Null
$env:TEMP = Join-Path $repoRoot '.work\tmp'
$env:TMP = $env:TEMP
$env:HF_HOME = Join-Path $repoRoot '.work\hf_cache'
$envFolder = if ($CPU) { '.work\asr_env' } else { '.work\asr_gpu_env' }
if (-not (Test-Path -LiteralPath (Join-Path $envFolder 'Scripts\python.exe'))) {
    py -3.11 -m venv --system-site-packages $envFolder
    if ($LASTEXITCODE -ne 0) { throw 'Cannot create Python 3.11 environment' }
}
$asrPython = Join-Path $repoRoot (Join-Path $envFolder 'Scripts\python.exe')
if ($CPU) {
    & $asrPython -m pip --disable-pip-version-check --no-cache-dir install -r src\asr\requirements-asr.txt
} else {
    & $asrPython -m pip --disable-pip-version-check --no-cache-dir install --extra-index-url 'https://download.pytorch.org/whl/cu117' 'torch==2.0.1+cu117' 'torchvision==0.15.2+cu117'
    if ($LASTEXITCODE -ne 0) { throw 'CUDA PyTorch installation failed' }
    & $asrPython -m pip --disable-pip-version-check --no-cache-dir install -r src\asr\requirements-asr-gpu.txt
}
if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed' }
& $asrPython -X utf8 data\prepare_vivos.py
if ($LASTEXITCODE -ne 0) { throw 'Dataset download failed' }
& $asrPython -X utf8 src\asr\download_checkpoints.py
if ($LASTEXITCODE -ne 0) { throw 'Checkpoint download failed' }
if ($CPU) {
    & $asrPython -X utf8 src\asr\prepare_models.py --source-dir .work\source_models
    if ($LASTEXITCODE -ne 0) { throw 'Model conversion failed' }
    $outputPath = if ($Limit -gt 0) { "reports/task1/asr/cpu_subset_$Limit/baseline_asr.json" } else { 'reports/task1/asr/cpu_int8/baseline_asr.json' }
    & $asrPython -X utf8 -u src\asr\evaluate_asr.py --threads $Threads --limit $Limit --output $outputPath
} else {
    $outputPath = if ($Limit -gt 0) { "reports/task1/asr/gpu_subset_$Limit/baseline_asr.json" } else { 'reports/task1/asr/baseline_asr.json' }
    & $asrPython -X utf8 -u src\asr\evaluate_asr_gpu.py --limit $Limit --output $outputPath
}
if ($LASTEXITCODE -ne 0) { throw 'ASR evaluation failed' }
Write-Output "Completed: $outputPath"
