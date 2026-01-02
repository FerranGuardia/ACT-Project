@echo off
REM ACT Project - Test Runner
REM Runs both unit and integration tests with clear separation

cd /d "%~dp0"

echo ========================================
echo    ACT Project - Running All Tests
echo ========================================
echo.
echo Current directory: %CD%
echo.

echo ========================================
echo    Running Unit Tests
echo ========================================
echo.
echo Running unit tests...
echo This may take a few minutes...
echo.

python -m pytest tests/unit/ -v --tb=short
set UNIT_TEST_EXIT=%ERRORLEVEL%

echo.
echo ========================================
echo    Unit Tests Complete
echo ========================================
if %UNIT_TEST_EXIT% EQU 0 (
    echo [PASS] Unit Tests: ALL PASSED
) else (
    echo [FAIL] Unit Tests: SOME FAILED
)
echo.

echo ========================================
echo    Running Integration Tests
echo ========================================
echo.
echo Running integration tests...
echo This may take a few minutes...
echo.

python -m pytest tests/integration/ -v --tb=short
set INTEGRATION_TEST_EXIT=%ERRORLEVEL%

echo.
echo ========================================
echo    Integration Tests Complete
echo ========================================
if %INTEGRATION_TEST_EXIT% EQU 0 (
    echo [PASS] Integration Tests: ALL PASSED
) else (
    echo [FAIL] Integration Tests: SOME FAILED
)
echo.

echo ========================================
echo    Final Test Summary
echo ========================================
if %UNIT_TEST_EXIT% EQU 0 (
    echo [OK] Unit Tests: PASSED
) else (
    echo [FAIL] Unit Tests: FAILED
)

if %INTEGRATION_TEST_EXIT% EQU 0 (
    echo [OK] Integration Tests: PASSED
) else (
    echo [FAIL] Integration Tests: FAILED
)
echo.

if %UNIT_TEST_EXIT% NEQ 0 (
    echo ========================================
    echo    Some tests FAILED
    echo ========================================
    pause
    exit /b %UNIT_TEST_EXIT%
)

if %INTEGRATION_TEST_EXIT% NEQ 0 (
    echo ========================================
    echo    Some tests FAILED
    echo ========================================
    pause
    exit /b %INTEGRATION_TEST_EXIT%
)

echo ========================================
echo    All Tests PASSED
echo ========================================
pause




