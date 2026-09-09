@echo off
setlocal
cd /d "%~dp0backend"
if not exist .venv (
  echo [OlYoungNew] Creating backend virtual environment...
  python -m venv .venv
  call .venv\Scripts\activate.bat
  python -m pip install --upgrade pip
  pip install -r requirements.txt
) else (
  call .venv\Scripts\activate.bat
)
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8010
endlocal
