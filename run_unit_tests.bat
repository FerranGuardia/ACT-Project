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

REM Run pytest and capture output (filter QThread warnings)
python -m pytest tests/unit/ -v --tb=short 2>&1 | findstr /V /C:"QThread:" /C:"Destroyed while thread" > %TEMP%\pytest_output.txt
set TEST_EXIT=%ERRORLEVEL%

REM Display filtered output
type %TEMP%\pytest_output.txt

REM Parse and display summary
python tests\unit\get_test_summary.py %TEMP%\pytest_output.txt

echo.
echo ========================================
echo    Unit Tests Complete
echo ========================================

REM Cleanup
del %TEMP%\pytest_output.txt 2>nul

echo.
pause
exit /b %TEST_EXIT%



