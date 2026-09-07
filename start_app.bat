@echo off
setlocal

cd /d "%~dp0"

echo ========================================
echo   AppInToss - 오를까? 개발 서버 실행
echo ========================================
echo.

if not exist "backend\.venv\Scripts\python.exe" (
    echo [Backend] 가상환경이 없어 생성합니다...
    python -m venv backend\.venv
    if errorlevel 1 goto :error
)

if not exist "backend\.venv\.deps_installed" (
    echo [Backend] 패키지를 설치합니다...
    backend\.venv\Scripts\python.exe -m pip install -r backend\requirements.txt
    if errorlevel 1 goto :error
    type nul > backend\.venv\.deps_installed
)

if not exist "frontend\node_modules" (
    echo [Frontend] npm 패키지를 설치합니다...
    pushd frontend
    call npm install
    if errorlevel 1 (
        popd
        goto :error
    )
    popd
)

if not exist "frontend\.env" (
    echo [Warning] frontend\.env 파일이 없습니다.
    echo 모바일 테스트라면 아래 형식으로 생성하세요.
    echo VITE_API_BASE_URL=http://PC_IP:8000
    echo.
)

echo [Backend] http://localhost:8000
echo [Frontend] http://localhost:5173
echo.

echo 백엔드와 프론트엔드를 새 창에서 실행합니다...

start "AppInToss Backend" cmd /k "cd /d "%~dp0backend" && .venv\Scripts\python.exe -m uvicorn app.main:app --host 0.0.0.0 --port 8000"
start "AppInToss Frontend" cmd /k "cd /d "%~dp0frontend" && npm run dev -- --host 0.0.0.0"

echo.
echo 실행 완료.
echo 서버를 종료하려면 열린 Backend / Frontend 창에서 Ctrl+C를 누르세요.
exit /b 0

:error
echo.
echo [ERROR] 초기화 또는 실행 준비 중 오류가 발생했습니다.
pause
exit /b 1
