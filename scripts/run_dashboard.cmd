@echo off
setlocal

cd /d "%~dp0\..\frontend"

netstat -ano | findstr ":3000" | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo SkillSync already appears to be running at http://127.0.0.1:3000
    exit /b 0
)

if not exist "node_modules" call npm.cmd install
if not defined SKILLSYNC_API_URL set SKILLSYNC_API_URL=http://127.0.0.1:8000
call npm.cmd run dev -- --hostname 127.0.0.1 --port 3000
