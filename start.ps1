#Requires -Version 5.1
<#
Cornerwork one-command startup.
  .\start.ps1            start the backend on port 8765, print + copy the token, open the dashboard
  .\start.ps1 -Stop      stop whatever listens on the port
  .\start.ps1 -Port 8777 use another port
  .\start.ps1 -NoBrowser do not open the browser
#>
param([int]$Port = 8765, [switch]$Stop, [switch]$NoBrowser)
$ErrorActionPreference = 'Stop'
Set-Location $PSScriptRoot
$python = Join-Path $PSScriptRoot '.venv\Scripts\python.exe'

function Stop-Port([int]$p) {
    $pids = Get-NetTCPConnection -LocalPort $p -State Listen -ErrorAction SilentlyContinue | Select-Object -ExpandProperty OwningProcess -Unique
    foreach ($id in $pids) { Write-Host "Stopping process $id on port $p"; Stop-Process -Id $id -Force -ErrorAction SilentlyContinue }
}

if ($Stop) { Stop-Port $Port; Write-Host "Stopped."; exit 0 }

# 1. Environment
if (-not (Test-Path $python)) {
    Write-Host "Creating .venv and installing requirements (first run only)..."
    python -m venv .venv
    & $python -m pip install -q -r requirements.txt
}
if (-not (Test-Path '.env')) { Copy-Item '.env.example' '.env'; Write-Host "Created .env from .env.example (fakes until you add keys)." }
New-Item -ItemType Directory -Force -Path 'data' | Out-Null

# 2. Backend (background process, logs to data\backend.log)
Stop-Port $Port
$env:PORT = "$Port"
$proc = Start-Process -FilePath $python -ArgumentList '-m', 'app.main' -WorkingDirectory $PSScriptRoot -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput 'data\backend.log' -RedirectStandardError 'data\backend.err.log'
$base = "http://127.0.0.1:$Port"
$up = $false
for ($i = 0; $i -lt 40; $i++) {
    Start-Sleep -Milliseconds 250
    try { if ((Invoke-RestMethod "$base/health" -TimeoutSec 2).ok) { $up = $true; break } } catch {}
    if ($proc.HasExited) { break }
}
if (-not $up) { Write-Host "Backend did not start. See data\backend.err.log:"; Get-Content 'data\backend.err.log' -Tail 20; exit 1 }

# 3. Token: print, copy to clipboard
$token = (& $python 'scripts\issue_token.py').Trim()
try { Set-Clipboard -Value $token; $copied = ' (copied to clipboard)' } catch { $copied = '' }

Write-Host ""
Write-Host "Cornerwork backend running on $base  (pid $($proc.Id), log data\backend.log)"
Write-Host "Gym API token$copied :"
Write-Host "  $token"
Write-Host ""
Write-Host "Extension: click the Cornerwork icon > Settings > Backend URL $base > paste the token > Save and test."
Write-Host "Phone/web: $base/c/$token"
Write-Host "Stop:      .\start.ps1 -Stop -Port $Port"

if (-not $NoBrowser) { Start-Process "$base/c/$token" }
