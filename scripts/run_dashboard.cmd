@echo off
setlocal

cd /d "%~dp0\.."

netstat -ano | findstr ":8501" | findstr "LISTENING" >nul
if %errorlevel%==0 (
    echo Dashboard already appears to be running at http://127.0.0.1:8501
    exit /b 0
)

set PYTHON_EXE=%CD%\.venv\Scripts\python.exe
if not exist "%PYTHON_EXE%" set PYTHON_EXE=python

"%PYTHON_EXE%" -m streamlit run dashboard\app.py --server.address 127.0.0.1 --server.port 8501 --server.headless true
