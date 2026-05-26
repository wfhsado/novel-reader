@echo off
echo Starting Novel Reader...
echo.

python --version >nul 2>&1
if errorlevel 1 (
    echo Error: Python not found
    pause
    exit /b 1
)

python -c "import PyQt5" >nul 2>&1
if errorlevel 1 (
    echo PyQt5 not installed. Please run install.bat first.
    pause
    exit /b 1
)

if "%~1"=="" (
    python main.py
) else (
    python main.py "%~1"
)
