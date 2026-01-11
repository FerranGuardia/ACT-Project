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
echo Checking for slow tests and performance issues...
echo.

echo ========================================
echo    Running Unit Tests (Non-UI)
echo ========================================
echo.
echo Running unit tests with coverage (excluding UI tests)...
echo UI tests run separately due to Qt threading constraints.
echo This may take a few minutes...
echo.

python -m pytest tests/unit/ -v --tb=short -m "not ui"
set UNIT_TEST_EXIT=%ERRORLEVEL%

echo.
echo ========================================
echo    Running UI Tests (Sequential)
echo ========================================
echo.
echo Running UI tests sequentially (Qt components)...
echo.

python -m pytest tests/unit/ui/ -v --tb=short -n0
set UI_TEST_EXIT=%ERRORLEVEL%

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

if %UI_TEST_EXIT% EQU 0 (
    echo [OK] UI Tests: PASSED
) else (
    echo [FAIL] UI Tests: FAILED
)

if %INTEGRATION_TEST_EXIT% EQU 0 (
    echo [OK] Integration Tests: PASSED
) else (
    echo [FAIL] Integration Tests: FAILED
)
echo.

REM Check for any failures
set OVERALL_EXIT=0
if %UNIT_TEST_EXIT% NEQ 0 set OVERALL_EXIT=1
if %UI_TEST_EXIT% NEQ 0 set OVERALL_EXIT=1
if %INTEGRATION_TEST_EXIT% NEQ 0 set OVERALL_EXIT=1

if %OVERALL_EXIT% NEQ 0 (
    echo ========================================
    echo    Some tests FAILED
    echo ========================================
    echo.
    echo Failed test suites:
    if %UNIT_TEST_EXIT% NEQ 0 echo - Unit Tests (Non-UI)
    if %UI_TEST_EXIT% NEQ 0 echo - UI Tests
    if %INTEGRATION_TEST_EXIT% NEQ 0 echo - Integration Tests
    echo.
    echo Check the output above for failure details.
    pause
    exit /b 1
)

echo ========================================
echo    All Tests PASSED
echo ========================================
pause

