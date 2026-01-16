@echo off
REM ACT Project - Deterministic E2E Tests Runner (local fixture site)

cd /d "%~dp0"

set ACT_TEST_MODE=1
set ACT_ALLOW_LOCALHOST_URLS=1
set ACT_TTS_MAX_CHARS=600

echo ========================================
echo    ACT Project - Running Deterministic E2E Tests
echo    (Local fixture HTTP server)
echo ========================================
echo.
echo Running: pytest tests/integration/e2e/ (no xdist)
echo.

python -m pytest tests/integration/e2e/ -v --tb=short -n 0
set TEST_EXIT=%ERRORLEVEL%

echo.
echo ========================================
if %TEST_EXIT% EQU 0 (
    echo    Deterministic E2E Tests PASSED
) else (
    echo    Deterministic E2E Tests FAILED
)
echo ========================================
echo.

pause
exit /b %TEST_EXIT%
