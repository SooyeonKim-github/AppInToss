@echo off
setlocal
cd /d "%~dp0DataCollector"

if not exist .venv (
    echo [RooftopMood] DataCollector virtual environment creating...
    py -m venv .venv
)

call .venv\Scripts\activate.bat
python -m pip install -r requirements.txt

if not exist .env (
    copy .env.example .env >nul
    echo.
    echo [RooftopMood] DataCollector\.env was created.
    echo Please enter KAKAO_REST_API_KEY / NAVER_CLIENT_ID / NAVER_CLIENT_SECRET and run again.
    pause
    exit /b 1
)

python main.py %*
endlocal
