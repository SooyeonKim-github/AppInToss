@echo off
cd /d "%~dp0"
start "OlYoungNew Backend" cmd /k call start_backend.bat
start "OlYoungNew Frontend" cmd /k call start_frontend.bat
