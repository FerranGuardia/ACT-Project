@echo off
REM ACT Project - Integration Tests Runner

cd /d "%~dp0"

REM Set test mode to use temp directories instead of user Documents
set ACT_TEST_MODE=1

echo ========================================
echo    ACT Project - Running Integration Tests
echo    Test Mode: %ACT_TEST_MODE% (Isolated directories)
echo ========================================
echo.
echo Current directory: %CD%
echo.
echo Running integration tests...
echo This may take a few minutes...
echo.

python -m pytest tests/integration/ -v --tb=short
set TEST_EXIT=%ERRORLEVEL%

echo.
echo ========================================
if %TEST_EXIT% EQU 0 (
    echo    Integration Tests PASSED
) else (
    echo    Integration Tests FAILED
)
echo ========================================
echo.

pause
exit /b %TEST_EXIT%







