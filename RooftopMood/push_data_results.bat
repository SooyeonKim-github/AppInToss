@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0.."

echo ====================================================
echo        RooftopMood DataCollector 결과 Push
echo ====================================================
echo.
echo 대상: RooftopMood\DataCollector\output\*.csv
echo .env / API Key / 가상환경은 포함하지 않습니다.
echo.

if not exist "RooftopMood\DataCollector\output\*.csv" (
    echo [안내] push할 CSV 결과 파일이 없습니다.
    echo 먼저 run_data_collector.bat를 실행해주세요.
    pause
    exit /b 1
)

rem output CSV는 기본적으로 gitignore 되어 있으므로 결과 공유 시에만 강제 stage 합니다.
git add -f RooftopMood/DataCollector/output/*.csv
if errorlevel 1 goto :error

echo.
echo [Stage된 결과 파일]
git status --short -- RooftopMood/DataCollector/output

echo.
set /p CONFIRM=위 결과 파일을 GitHub main에 commit/push 할까요? (YES 입력): 
if /I not "%CONFIRM%"=="YES" (
    echo 취소했습니다. Stage 상태는 유지됩니다.
    pause
    exit /b 0
)

git diff --cached --quiet -- RooftopMood/DataCollector/output
if not errorlevel 1 (
    echo.
    echo [안내] 변경된 결과 파일이 없습니다.
    pause
    exit /b 0
)

git commit -m "data: update RooftopMood collector results"
if errorlevel 1 goto :error

git push origin main
if errorlevel 1 goto :push_error

echo.
echo [완료] DataCollector 결과를 GitHub에 push했습니다.
echo 이제 ChatGPT에 "결과 push했어. 분석해줘"라고 말하면 됩니다.
echo.
pause
exit /b 0

:push_error
echo.
echo [실패] git push에 실패했습니다.
echo 원격 main이 더 최신이면 먼저 git pull origin main 후 다시 실행해주세요.
pause
exit /b 1

:error
echo.
echo [실패] Git 명령 실행 중 오류가 발생했습니다.
pause
exit /b 1
