$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $ProjectRoot

$Python = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $Python)) {
    $Python = "python"
}

$Existing = netstat -ano | Select-String ":8501" | Select-String "LISTENING"
if ($Existing) {
    Write-Host "Dashboard already appears to be running at http://127.0.0.1:8501"
    return
}

& $Python -m streamlit run dashboard\app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
