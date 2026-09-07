@echo off
setlocal
cd /d "%~dp0"

set "CHART_EXPERT_ROOT=%~dp0..\ChartExpertAnalyzer"

if not exist "%CHART_EXPERT_ROOT%\MarketData" (
  echo [ERROR] ChartExpertAnalyzer\MarketData not found:
  echo         %CHART_EXPERT_ROOT%
  echo.
  echo AppInToss and ChartExpertAnalyzer should be sibling folders,
  echo or run scripts\sync_market_data.py with --chart-expert-root manually.
  pause
  exit /b 1
)

echo [1/2] Installing question generator dependencies...
python -m pip install -r question_generator\requirements.txt
if errorlevel 1 goto :error

echo.
echo [2/2] Syncing KOSPI/KOSDAQ liquidity TOP 300 and OHLCV...
python scripts\sync_market_data.py ^
  --chart-expert-root "%CHART_EXPERT_ROOT%" ^
  --markets KOSPI KOSDAQ ^
  --top-n 300 ^
  --lookback 20 ^
  --start 20230101 ^
  --end 20260831

if errorlevel 1 (
  echo.
  echo [WARN] Sync finished with failed tickers. Check:
  echo        data\universe\market_data_sync_report.csv
  pause
  exit /b 2
)

echo.
echo [DONE] Market data sync complete.
echo Next command:
echo   python scripts\generate_questions.py
pause
exit /b 0

:error
echo.
echo [ERROR] Dependency installation failed.
pause
exit /b 1
