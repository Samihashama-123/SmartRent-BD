@echo off
setlocal
cd /d "%~dp0"
echo.
echo ===========================================
echo       SmartRent BD - Local Development
echo ===========================================
echo.
if not exist ".venv\Scripts\python.exe" (
  echo Creating Python environment...
  py -m venv .venv
  if errorlevel 1 python -m venv .venv
)
if not exist ".venv\Scripts\python.exe" (
  echo Could not create Python environment. Install Python 3.11 or newer.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" -c "import fastapi, uvicorn, jinja2, multipart, dotenv" >nul 2>&1
if errorlevel 1 (
  echo Installing project dependencies...
  ".venv\Scripts\python.exe" -m pip install -r requirements.txt
  if errorlevel 1 (
    echo Dependencies could not be installed.
    pause
    exit /b 1
  )
)
echo Starting http://127.0.0.1:8000
".venv\Scripts\python.exe" -m uvicorn main:app --reload --port 8000
pause
