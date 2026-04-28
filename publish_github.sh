#!/bin/bash
# publish_github.sh - Publish SecureWipe Pro to GitHub
# This script initializes git repo and creates a release

set -e  # Exit on error

echo "==============================================="
echo "  SecureWipe Pro - GitHub Publisher"
echo "==============================================="
echo ""

# Check if git is installed
if ! command -v git &> /dev/null; then
    echo "[ERROR] Git is not installed!"
    exit 1
fi

# Check if gh CLI is installed (for release creation)
HAS_GH=false
if command -v gh &> /dev/null; then
    HAS_GH=true
    echo "[INFO] GitHub CLI (gh) found - will create release"
else
    echo "[INFO] GitHub CLI (gh) not found - skipping release creation"
    echo "       Install gh from: https://cli.github.com/"
fi

# Get repository URL from user
read -p "Enter GitHub repository URL (e.g., https://github.com/USERNAME/SecureWipePro.git): " REPO_URL

if [ -z "$REPO_URL" ]; then
    echo "[ERROR] Repository URL cannot be empty!"
    exit 1
fi

# Extract repo name from URL
REPO_NAME=$(basename "$REPO_URL" .git)
echo ""
echo "[INFO] Repository name: $REPO_NAME"

# Initialize git if not already initialized
if [ ! -d ".git" ]; then
    echo ""
    echo "[SETUP] Initializing git repository..."
    git init
    git branch -M main
    echo "[SUCCESS] Git repository initialized"
else
    echo "[INFO] Git repository already exists"
fi

# Add remote origin
echo ""
echo "[SETUP] Adding remote origin..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REPO_URL"
echo "[SUCCESS] Remote origin added"

# Create proper directory structure
echo ""
echo "[SETUP] Creating directory structure..."

mkdir -p releases
touch releases/.gitkeep

# Create .gitignore if not exists
if [ ! -f ".gitignore" ]; then
    cat > .gitignore << 'EOF'
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
ENV/
*.egg-info/
dist/
build/

# Logs
logs/
*.log

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
Thumbs.db
Desktop.ini
.DS_Store

# Temporary files
test_data.bin
create_*.py

# Executables (keep in releases only)
*.exe
!releases/*.exe
EOF
    echo "[SUCCESS] .gitignore created"
fi

# Create LICENSE if not exists
if [ ! -f "LICENSE" ]; then
    cat > LICENSE << 'EOF'
MIT License

Copyright (c) 2026 SecureWipe Pro

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.
EOF
    echo "[SUCCESS] LICENSE created (MIT)"
fi

# Add all files
echo ""
echo "[COMMIT] Adding files to git..."
git add .

# Create initial commit
echo ""
echo "[COMMIT] Creating initial commit..."
git commit -m "🔒 Initial release: SecureWipe Pro v1.0.0

Features:
- Modern CustomTkinter GUI
- Wiping methods: Zeros, DoD 5220.22-M, Gutmann
- Verification and logging
- Test mode for safe demonstration
- Progress tracking with speed and ETA
- Splash screen and animations
- Cross-platform support (Windows/Linux/macOS)" || echo "[INFO] Commit may already exist"

# Push to GitHub
echo ""
echo "[PUSH] Pushing to GitHub..."
git push -u origin main

if [ $? -eq 0 ]; then
    echo ""
    echo "[SUCCESS] Code pushed to GitHub!"
    echo "Repository: $REPO_URL"
else
    echo ""
    echo "[ERROR] Failed to push to GitHub"
    echo "Make sure you have the correct permissions and the repository exists."
    exit 1
fi

# Create GitHub release if gh CLI is available
if [ "$HAS_GH" = true ]; then
    echo ""
    echo "[RELEASE] Creating GitHub release..."
    
    # Check if executable exists
    if [ -f "releases/SecureWipePro.exe" ]; then
        gh release create v1.0.0 \
            "releases/SecureWipePro.exe#SecureWipePro.exe" \
            --title "SecureWipe Pro v1.0.0" \
            --notes "First release of SecureWipe Pro.

## Features
- 🔒 Secure data wiping with multiple methods
- 🎨 Modern dark-themed GUI with CustomTkinter
- 📊 Real-time progress with speed and ETA
- ✅ Verification after wiping
- 🧪 Test mode for safe demonstration
- 📋 Export reports (TXT/PDF)

## Wiping Methods
- Zeros (1 pass)
- DoD 5220.22-M (3 passes)
- Gutmann simplified (7 passes)
- Verify only

## Installation
Download SecureWipePro.exe from releases - no Python required!"
        
        echo "[SUCCESS] GitHub release created!"
        echo "Release: https://github.com/$REPO_NAME/releases/tag/v1.0.0"
    else
        echo "[INFO] No executable found in releases/"
        echo "       Build the executable first with build.bat or build.sh"
        echo "       Then run this script again to create the release."
    fi
else
    echo ""
    echo "[INFO] To create a release manually:"
    echo "       1. Go to your repository on GitHub"
    echo "       2. Click 'Releases' -> 'Create a new release'"
    echo "       3. Tag version: v1.0.0"
    echo "       4. Upload SecureWipePro.exe from releases/ folder"
fi

echo ""
echo "==============================================="
echo "  ✅ All done!"
echo "==============================================="
echo ""
echo "Next steps:"
echo "  1. Build executable: ./build.sh (Linux) or build.bat (Windows)"
echo "  2. Place executable in releases/ folder"
echo "  3. Create GitHub release with the executable"
echo ""
