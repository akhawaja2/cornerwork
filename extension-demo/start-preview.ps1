$pythonExe = Join-Path $PSScriptRoot '..\.venv\Scripts\python.exe'
& $pythonExe -m http.server 8766 --bind 127.0.0.1 --directory $PSScriptRoot
