@echo off
REM ACT Project - UI Unit Tests Runner
REM Runs UI tests sequentially (no parallel execution due to Qt threading)

cd /d "%~dp0"

echo ========================================
echo    ACT Project - Running UI Tests
echo ========================================
echo.
echo Current directory: %CD%
echo.
echo Running UI unit tests (sequential execution)...
echo This may take a few minutes...
echo.

REM Run UI tests without parallel execution (-n0 disables xdist)
python -m pytest tests/unit/ui/ -v --tb=short -n0 --durations=10 2>&1 | findstr /V /C:"QThread:" /C:"Destroyed while thread" /C:"QtWarning" > %TEMP%\ui_test_output.txt
set UI_TEST_EXIT=%ERRORLEVEL%

REM Display filtered output
type %TEMP%\ui_test_output.txt

echo.
echo ========================================
echo    UI Tests Complete
echo ========================================

if %UI_TEST_EXIT% EQU 0 (
    echo [PASS] UI Tests: ALL PASSED
    echo.
    echo UI tests completed successfully!
    echo All Qt/PySide6 components are working correctly.
) else (
    echo [FAIL] UI Tests: SOME FAILED
    echo.
    echo Some UI tests failed. Check the output above for details.
    echo This may indicate issues with Qt components or test mocking.
)

REM Cleanup
del %TEMP%\ui_test_output.txt 2>nul

echo.
pause
exit /b %UI_TEST_EXIT%