@echo off
REM build.bat - Build script for Windows
REM SecureWipe Pro v1.0 - PyInstaller build

echo ================================================
echo   SecureWipe Pro v1.0 - Build Script
echo ================================================
echo.

REM Check if PyInstaller is installed
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing PyInstaller...
    pip install pyinstaller
)

REM Check if CustomTkinter is installed
pip show customtkinter >nul 2>&1
if errorlevel 1 (
    echo [INFO] Installing CustomTkinter...
    pip install customtkinter
)

echo.
echo [BUILD] Creating executable...
echo.

REM Build with PyInstaller
pyinstaller --onefile ^
          --windowed ^
          --name "SecureWipePro" ^
          --icon=NONE ^
          --add-data "wipe_engine.py;." ^
          --hidden-import "customtkinter" ^
          --hidden-import "tkinter" ^
          secure_wipe_pro.py

if errorlevel 1 (
    echo.
    echo [ERROR] Build failed!
    pause
    exit /b 1
)

echo.
echo [SUCCESS] Build completed!
echo Executable: dist\SecureWipePro.exe
echo.

REM Optional: Create releases folder
if not exist "releases" mkdir releases
copy "dist\SecureWipePro.exe" "releases\" >nul
echo [INFO] Copied to releases\SecureWipePro.exe
echo.

pause
