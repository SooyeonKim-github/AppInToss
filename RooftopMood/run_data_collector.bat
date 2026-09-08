@echo off
setlocal EnableExtensions
chcp 65001 >nul
cd /d "%~dp0DataCollector"

if not exist .venv (
    echo [RooftopMood] DataCollector 가상환경을 생성합니다...
    py -m venv .venv
    if errorlevel 1 goto :error

    call .venv\Scripts\activate.bat
    python -m pip install --upgrade pip
    python -m pip install -r requirements.txt
    if errorlevel 1 goto :error
) else (
    call .venv\Scripts\activate.bat
)

if not exist .env (
    copy .env.example .env >nul
    echo.
    echo [RooftopMood] DataCollector\.env 파일을 생성했습니다.
    echo KAKAO_REST_API_KEY 값을 입력한 뒤 다시 실행해주세요.
    echo.
    pause
    exit /b 1
)

rem 인자가 있으면 기존 방식 그대로 실행합니다.
if not "%~1"=="" (
    python main.py %*
    set EXIT_CODE=%ERRORLEVEL%
    if not "%EXIT_CODE%"=="0" goto :error_code
    goto :done
)

:menu
cls
echo ====================================================
echo          RooftopMood DataCollector - Kakao Only
echo ====================================================
echo.
echo  [1] 후보 카페 수집              discover
echo  [2] 루프탑/뷰 분류               classify
echo  [3] 설명 및 DB-ready 생성        describe
echo  [4] 전체 파이프라인              all
echo  [5] Supabase 적재 미리보기       publish --dry-run
echo  [6] Supabase 실제 적재           publish
echo  [O] output 폴더 열기
echo  [Q] 종료
echo.
set /p CHOICE=선택: 

if /I "%CHOICE%"=="1" set CMD=discover& goto :run
if /I "%CHOICE%"=="2" set CMD=classify& goto :run
if /I "%CHOICE%"=="3" set CMD=describe& goto :run
if /I "%CHOICE%"=="4" set CMD=all& goto :run
if /I "%CHOICE%"=="5" set CMD=publish --dry-run& goto :run
if /I "%CHOICE%"=="6" set CMD=publish& goto :confirm_publish
if /I "%CHOICE%"=="O" start "" "%CD%\output"& goto :menu
if /I "%CHOICE%"=="Q" goto :done

echo.
echo 잘못된 선택입니다.
timeout /t 2 /nobreak >nul
goto :menu

:confirm_publish
echo.
echo [주의] 실제 Supabase DB에 데이터를 반영합니다.
set /p CONFIRM=계속하려면 YES 입력: 
if /I not "%CONFIRM%"=="YES" goto :menu
goto :run

:run
echo.
echo ----------------------------------------------------
echo 실행: python main.py %CMD%
echo ----------------------------------------------------
echo.
python main.py %CMD%
if errorlevel 1 goto :error

echo.
echo [완료] %CMD%
echo 결과 위치: %CD%\output
echo.
pause
goto :menu

:error
echo.
echo [실패] DataCollector 실행 중 오류가 발생했습니다.
pause
exit /b 1

:error_code
echo.
echo [실패] 종료 코드: %EXIT_CODE%
pause
exit /b %EXIT_CODE%

:done
endlocal
