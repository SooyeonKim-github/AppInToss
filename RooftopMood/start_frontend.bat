@echo off
cd /d "%~dp0frontend"
if not exist .env (
  copy .env.example .env >nul
)
if not exist node_modules (
  call npm install
  if errorlevel 1 exit /b %errorlevel%
)
call npm run dev
