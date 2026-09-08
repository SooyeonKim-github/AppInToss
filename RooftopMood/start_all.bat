@echo off
cd /d "%~dp0"
start "RooftopMood Backend" cmd /k call "%~dp0start_backend.bat"
timeout /t 2 /nobreak >nul
start "RooftopMood Frontend" cmd /k call "%~dp0start_frontend.bat"
