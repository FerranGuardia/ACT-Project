@echo off
REM ACT Project - Integration Tests Runner

cd /d "%~dp0"

echo ========================================
echo    ACT Project - Running Integration Tests
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




