@echo off
setlocal
cd /d "%~dp0frontend"
if not exist .env (
  if exist .env.example (
    echo [NoelPin] Creating frontend .env from .env.example...
    copy /Y .env.example .env >nul
  )
)
if not exist node_modules (
  echo [NoelPin] Installing frontend dependencies...
  call npm install
  if errorlevel 1 exit /b 1
)
echo [NoelPin] Starting frontend on http://localhost:5176
call npm run dev
