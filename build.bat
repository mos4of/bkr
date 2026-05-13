@echo off
REM build.bat - Build script for Windows
REM SecureWipe Pro v2.0 — NIST SP 800-88r1 / IEEE 2883-2022

echo ================================================
echo   SecureWipe Pro v2.0 - Build Script
echo   NIST SP 800-88r1 / IEEE 2883-2022
echo ================================================
echo.

REM Check if Python 3.10+
python -c "import sys; assert sys.version_info >= (3, 10), 'Python 3.10+ required'"
if errorlevel 1 (
    echo [ERROR] Python 3.10 or higher is required!
    pause
    exit /b 1
)

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
          --hidden-import "crypt" ^
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

REM Create releases folder
if not exist "releases" mkdir releases
copy "dist\SecureWipePro.exe" "releases\" >nul
echo [INFO] Copied to releases\SecureWipePro.exe
echo.

pause
