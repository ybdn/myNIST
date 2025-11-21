#!/bin/bash
# Build script for myNIST application

set -e  # Exit on error

echo "======================================"
echo "myNIST Build Script"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Clean previous build
if [ -d "dist" ]; then
    echo "Cleaning previous build..."
    rm -rf dist
fi

if [ -d "build" ]; then
    rm -rf build
fi

# Build with PyInstaller
echo "Building executable with PyInstaller..."
pyinstaller mynist.spec

# Check if build succeeded
if [ -f "dist/mynist" ]; then
    echo ""
    echo "======================================"
    echo "Build successful!"
    echo "======================================"
    echo "Executable location: dist/mynist"
    echo ""
    echo "Run with: ./dist/mynist"
    echo ""

    # Make executable
    chmod +x dist/mynist

    # Get file size
    size=$(du -h dist/mynist | cut -f1)
    echo "Executable size: $size"
else
    echo ""
    echo "======================================"
    echo "Build failed!"
    echo "======================================"
    exit 1
fi
