@echo off
setlocal
cd /d %~dp0backend
if not exist .venv (
  py -m venv .venv
)
call .venv\Scripts\activate
python -m pip install -r requirements.txt
if not exist .env copy .env.example .env >nul
python -m uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
