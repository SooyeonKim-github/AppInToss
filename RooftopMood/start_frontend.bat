@echo off
cd /d "%~dp0frontend"
if not exist .env (
  copy .env.example .env >nul
)
if not exist node_modules (
  npm install
)
npm run dev
