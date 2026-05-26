@echo off
echo ========================================
echo   Building Novel Reader EXE
echo ========================================
echo.

echo Cleaning old builds...
if exist dist rmdir /s /q dist
if exist build rmdir /s /q build
if exist *.spec del *.spec

echo.
echo Building EXE...
pyinstaller --onefile --windowed --name "NovelReader" main.py

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ========================================
echo   Build Complete!
echo ========================================
echo.
echo EXE file: dist\NovelReader.exe
echo.
pause
