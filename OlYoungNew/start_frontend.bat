@echo off
setlocal
cd /d "%~dp0frontend"
if not exist .env (
  if exist .env.example (
    echo [OlYoungNew] Creating frontend .env from .env.example...
    copy /Y .env.example .env >nul
  )
)
if not exist node_modules (
  echo [OlYoungNew] Installing frontend dependencies...
  call npm install
)
call npm run dev
endlocal
