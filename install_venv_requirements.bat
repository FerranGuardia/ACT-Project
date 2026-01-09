@echo off
REM Install requirements in virtual environment

cd /d "%~dp0"

echo Activating virtual environment...
call .venv\Scripts\activate

echo Installing main requirements...
pip install -r requirements.txt

echo Installing dev requirements...
pip install -r requirements-dev.txt

echo Testing circuitbreaker import...
python -c "import circuitbreaker; print('circuitbreaker imported successfully from venv')"

echo.
echo Requirements installation complete!
pause
