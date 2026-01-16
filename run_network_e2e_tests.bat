@echo off
REM ACT Project - Network E2E Tests Runner (real external sites)
REM WARNING: These tests are subject to rate limiting, site changes, and network flakiness.

cd /d "%~dp0"

set ACT_TEST_MODE=1
set ACT_RUN_NETWORK_E2E=1
set ACT_TTS_MAX_CHARS=600

echo ========================================
echo    ACT Project - Running Network E2E Tests
echo    ACT_RUN_NETWORK_E2E=%ACT_RUN_NETWORK_E2E%
echo ========================================
echo.
echo Running: pytest tests/e2e/ (no xdist)
echo.

python -m pytest tests/e2e/ -v --tb=short -n 0
set TEST_EXIT=%ERRORLEVEL%

echo.
echo ========================================
if %TEST_EXIT% EQU 0 (
    echo    Network E2E Tests PASSED
) else (
    echo    Network E2E Tests FAILED
)
echo ========================================
echo.

pause
exit /b %TEST_EXIT%
