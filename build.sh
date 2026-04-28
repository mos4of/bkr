#!/bin/bash
# build.sh - Build script for Linux/macOS
# SecureWipe Pro v1.0 - PyInstaller build

echo "==============================================="
echo "  SecureWipe Pro v1.0 - Build Script"
echo "==============================================="
echo ""

# Check if PyInstaller is installed
if ! pip show pyinstaller > /dev/null 2>&1; then
    echo "[INFO] Installing PyInstaller..."
    pip install pyinstaller
fi

# Check if CustomTkinter is installed
if ! pip show customtkinter > /dev/null 2>&1; then
    echo "[INFO] Installing CustomTkinter..."
    pip install customtkinter
fi

echo ""
echo "[BUILD] Creating executable..."
echo ""

# Build with PyInstaller
pyinstaller --onefile \
          --windowed \
          --name "SecureWipePro" \
          --add-data "wipe_engine.py:." \
          --hidden-import "customtkinter" \
          --hidden-import "tkinter" \
          secure_wipe_pro.py

if [ $? -ne 0 ]; then
    echo ""
    echo "[ERROR] Build failed!"
    exit 1
fi

echo ""
echo "[SUCCESS] Build completed!"
echo "Executable: dist/SecureWipePro"
echo ""

# Optional: Create releases folder
mkdir -p releases
cp "dist/SecureWipePro" "releases/"
echo "[INFO] Copied to releases/SecureWipePro"
echo ""

exit 0
