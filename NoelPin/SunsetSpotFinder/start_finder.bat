@echo off
setlocal
cd /d "%~dp0"
if not exist .venv (
  echo [SunsetSpotFinder] Creating virtual environment...
  py -3.10 -m venv .venv 2>nul || py -3 -m venv .venv
)
call .venv\Scripts\activate.bat
python -m pip install --upgrade pip
pip install -r requirements.txt
python run_finder.py --stage v5
if errorlevel 1 pause
endlocal
