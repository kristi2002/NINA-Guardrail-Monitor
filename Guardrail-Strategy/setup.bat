@echo off
echo Setting up Guardrail-Strategy environment...
echo.

REM Check if venv exists
if not exist "venv" (
    echo Creating virtual environment with Python 3.12...
    py -3.12 -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment
        pause
        exit /b 1
    )
    echo Virtual environment created successfully!
) else (
    echo Virtual environment already exists.
)

echo.
echo Activating virtual environment...
call venv\Scripts\activate.bat

echo.
echo Installing dependencies...
pip install -r requirements.txt
if errorlevel 1 (
    echo ERROR: Failed to install dependencies
    pause
    exit /b 1
)

echo.
echo.
echo ========================================
echo Setup complete!
echo ========================================
echo.
echo To run the service:
echo   1. Activate: venv\Scripts\activate.bat
echo   2. Run: python app.py
echo.
pause

