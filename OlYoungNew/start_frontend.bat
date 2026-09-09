@echo off
setlocal
cd /d "%~dp0frontend"
if not exist node_modules (
  echo [OlYoungNew] Installing frontend dependencies...
  call npm install
)
call npm run dev
endlocal
