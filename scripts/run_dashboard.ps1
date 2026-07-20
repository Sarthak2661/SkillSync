$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
$Frontend = Join-Path $ProjectRoot "frontend"
Set-Location $Frontend

$Existing = netstat -ano | Select-String ":3000" | Select-String "LISTENING"
if ($Existing) {
    Write-Host "SkillSync already appears to be running at http://127.0.0.1:3000"
    return
}

if (-not (Test-Path (Join-Path $Frontend "node_modules"))) {
    & npm.cmd install
}

$env:SKILLSYNC_API_URL = if ($env:SKILLSYNC_API_URL) { $env:SKILLSYNC_API_URL } else { "http://127.0.0.1:8000" }
& npm.cmd run dev -- --hostname 127.0.0.1 --port 3000
