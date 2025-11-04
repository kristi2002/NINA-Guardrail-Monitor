@echo off
echo Starting Guardrail-Strategy...
echo.

REM Check if venv exists
if not exist "venv" (
    echo ERROR: Virtual environment not found!
    echo Please run setup.bat first.
    pause
    exit /b 1
)

REM Run using venv python directly
venv\Scripts\python.exe app.py

pause

