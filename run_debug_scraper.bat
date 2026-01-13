@echo off
REM Unified scraper debug harness runner
REM Usage (examples):
REM   run_debug_scraper.bat --site novelfull --verbose
REM   run_debug_scraper.bat --site fanmtl --max-chapters 120 --verbose
REM   run_debug_scraper.bat --site custom --base-url https://example.com --toc-url https://example.com/toc

cd /d "%~dp0"
python scripts\debug_scraper.py %*

echo.
echo Debug run finished. Artifacts are under debug_runs\<site>_<timestamp>\.
echo.
pause