@echo off
echo ========================================
echo   Novel Reader - Install Dependencies
echo ========================================
echo.

echo Installing PyQt5...
pip install PyQt5

if errorlevel 1 (
    echo.
    echo Install failed, please run manually: pip install PyQt5
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Install Complete!
echo ========================================
echo.
echo Now you can run start.bat to launch the program
echo.
pause
