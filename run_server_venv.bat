@echo off
echo Activating Python 3.11 virtual environment...
call venv311\Scripts\activate.bat

echo.
echo Virtual environment activated!
echo Python version:
python --version

echo.
echo Starting Flask API server...
python api_server.py

pause
