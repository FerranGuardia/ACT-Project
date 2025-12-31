@echo off
REM ACT Project - Unit Tests Runner

cd /d "%~dp0"

echo ========================================
echo    ACT Project - Running Unit Tests
echo ========================================
echo.
echo Current directory: %CD%
echo.
echo Running unit tests...
echo This may take a few minutes...
echo.

python -m pytest tests/unit/ -v --tb=short
set TEST_EXIT=%ERRORLEVEL%

echo.
echo ========================================
if %TEST_EXIT% EQU 0 (
    echo    Unit Tests PASSED
) else (
    echo    Unit Tests FAILED
)
echo ========================================
echo.

pause
exit /b %TEST_EXIT%


