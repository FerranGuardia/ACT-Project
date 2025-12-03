@echo off
REM Batch file to run the Scraper Test UI
cd /d "%~dp0"
python test_scraper_ui.py
if errorlevel 1 (
    echo.
    echo Error running the test UI. Press any key to exit...
    pause >nul
)

