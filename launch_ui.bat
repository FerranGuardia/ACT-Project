@echo off
REM ACT UI Launcher - Quick launch for UI development
cd /d "%~dp0"
echo ========================================
echo ACT UI Builder
echo ========================================
echo.
echo Python version:
python --version
echo.
echo Python path:
python -c "import sys; print(sys.executable)"
echo.
echo Checking PySide6...
python -c "import PySide6; print('PySide6 version:', PySide6.__version__)" 2>nul
if errorlevel 1 (
    echo.
    echo PySide6 not found. Installing now...
    python -m pip install PySide6 --user
    if errorlevel 1 (
        echo.
        echo ERROR: Installation failed!
        echo Please install manually: pip install PySide6
        pause
        exit /b 1
    )
    echo.
    echo PySide6 installed successfully!
    echo.
)
echo.
echo Launching UI...
echo.
python launch_ui.py
if errorlevel 1 (
    echo.
    echo ERROR: Failed to launch UI
    pause
)

