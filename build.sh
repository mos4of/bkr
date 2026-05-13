#!/bin/bash
# build.sh - Build script for Linux/macOS
# SecureWipe Pro v2.0 — NIST SP 800-88r1 / IEEE 2883-2022

echo "==============================================="
echo "  SecureWipe Pro v2.0 - Build Script"
echo "  NIST SP 800-88r1 / IEEE 2883-2022"
echo "==============================================="
echo ""

# Check Python 3.10+
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
echo "[INFO] Python version: $PYTHON_VERSION"

# Check if PyInstaller is installed
if ! pip3 show pyinstaller > /dev/null 2>&1; then
    echo "[INFO] Installing PyInstaller..."
    pip3 install pyinstaller
fi

# Check if CustomTkinter is installed
if ! pip3 show customtkinter > /dev/null 2>&1; then
    echo "[INFO] Installing CustomTkinter..."
    pip3 install customtkinter
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

# Create releases folder
mkdir -p releases
cp "dist/SecureWipePro" "releases/"
echo "[INFO] Copied to releases/SecureWipePro"
echo ""

exit 0
