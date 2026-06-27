@echo off
setlocal

cd /d "%~dp0\.."

netstat -ano | findstr ":8000" | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo API already appears to be running at http://127.0.0.1:8000
    echo Open docs at http://127.0.0.1:8000/docs
    exit /b 0
)

set PYTHON_EXE=%CD%\.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=python

"%PYTHON_EXE%" -m uvicorn api.main:app --host 127.0.0.1 --port 8000
