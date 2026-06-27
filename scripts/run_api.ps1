$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Existing = netstat -ano | Select-String ":8000" | Select-String "LISTENING"
if ($Existing) {
    Write-Host "API already appears to be running at http://127.0.0.1:8000"
    Write-Host "Open docs at http://127.0.0.1:8000/docs"
    return
}

& $Python -m uvicorn api.main:app --host 127.0.0.1 --port 8000
