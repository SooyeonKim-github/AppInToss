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

echo [OlYoungNew] Collecting newest serum/ampoule products from OliveYoung...
python -m app.jobs.collect_oliveyoung --pages 3
pause
endlocal
