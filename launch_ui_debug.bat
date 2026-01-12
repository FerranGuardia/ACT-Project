@echo off
REM Debug UI Launcher - Runs the UI with verbose event logging enabled
REM This will show all UI interactions in the console

echo.
echo ========================================
echo    ACT - Debug UI Launcher
echo ========================================
echo.
echo Starting UI with VERBOSE logging...
echo All button clicks, input changes, and navigation will be shown in console.
echo.

cd /d "%~dp0"

REM Activate virtual environment
call .venv\Scripts\activate.bat

REM Run with verbose logging
python launch_ui.py

pause
