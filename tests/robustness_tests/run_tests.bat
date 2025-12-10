@echo off
REM Robustness Test Suite - Batch Launcher
REM Runs the full pipeline robustness tests
REM Can be run from project root or from tests\robustness_tests directory

echo ========================================
echo Robustness Test Suite - Full Pipeline
echo ========================================
echo.

REM Get the directory where this batch file is located
set SCRIPT_DIR=%~dp0

REM Change to script directory (works whether run from project root or test directory)
cd /d "%SCRIPT_DIR%"

REM Run the test script
python run_tests.py

REM Check exit code
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo Test suite completed with errors.
) else (
    echo.
    echo Test suite completed successfully!
)

echo.
pause

