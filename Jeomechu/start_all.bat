@echo off
setlocal
cd /d %~dp0
start "Jeomechu Backend" cmd /k "%~dp0start_backend.bat"
timeout /t 2 /nobreak >nul
start "Jeomechu Frontend" cmd /k "%~dp0start_frontend.bat"
