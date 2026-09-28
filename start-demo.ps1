$ErrorActionPreference = 'Stop'
$projectDir = $PSScriptRoot
$pythonExe = Join-Path $projectDir '.venv\Scripts\python.exe'
if (-not (Test-Path -LiteralPath $pythonExe)) {
    python -m venv (Join-Path $projectDir '.venv')
    if ($LASTEXITCODE -ne 0) { throw 'Python 3.12+ is required.' }
}
& $pythonExe -c "import fastapi, uvicorn, tzdata" 2>$null
if ($LASTEXITCODE -ne 0) {
    & $pythonExe -m pip install -r (Join-Path $projectDir 'demo\requirements.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Dependency installation failed.' }
}
Write-Host 'Cornerwork demo: http://127.0.0.1:8765 — Ctrl+C to stop.'
& $pythonExe (Join-Path $projectDir 'demo\server.py')
