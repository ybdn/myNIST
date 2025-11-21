#!/bin/bash
# Run script for myNIST application (development mode)

set -e  # Exit on error

echo "======================================"
echo "Running myNIST (Development Mode)"
echo "======================================"
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo "Virtual environment not found. Creating..."
    python3 -m venv venv
    source venv/bin/activate
    echo "Installing dependencies..."
    pip install --upgrade pip
    pip install -r requirements.txt
else
    # Activate virtual environment
    source venv/bin/activate
fi

# Run the application
echo "Starting myNIST..."
python -m mynist
