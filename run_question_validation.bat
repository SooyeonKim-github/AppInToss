@echo off
setlocal
cd /d "%~dp0"

echo ============================================================
echo [AppInToss] Feature Question Validation Pipeline
echo ============================================================
echo.

where python >nul 2>nul
if errorlevel 1 (
    echo [ERROR] python command not found.
    echo         Please install Python or add it to PATH.
    goto :fail
)

echo [1/3] Testing 15 chart features...
python scripts\test_chart_features.py
if errorlevel 1 (
    echo.
    echo [FAILED] Feature smoke test failed.
    goto :fail
)
echo [OK] Feature smoke test passed.
echo.

echo [2/3] Generating feature-based question bank...
python scripts\generate_questions.py
if errorlevel 1 (
    echo.
    echo [FAILED] Question generation failed.
    goto :fail
)
echo [OK] Question bank generated.
echo.

echo [3/3] Validating question bank...
python scripts\validate_question_bank.py
if errorlevel 1 (
    echo.
    echo [FAILED] Question bank validation failed.
    goto :fail
)
echo [OK] Question bank validation passed.
echo.

echo ============================================================
echo [DONE] All validation steps completed successfully.
echo Output: data\question_bank.csv
echo ============================================================
pause
exit /b 0

:fail
echo.
echo ============================================================
echo [STOPPED] Pipeline stopped because a step failed.
echo Check the error message above.
echo ============================================================
pause
exit /b 1
