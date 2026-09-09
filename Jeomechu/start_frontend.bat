@echo off
setlocal
cd /d %~dp0frontend
if not exist node_modules npm install
if not exist .env copy .env.example .env >nul
npm run dev -- --host 0.0.0.0
