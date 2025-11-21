#!/bin/bash
# Script to install WSQ (Wavelet Scalar Quantization) support for fingerprint images

echo "======================================"
echo "Installing WSQ Support for myNIST"
echo "======================================"
echo ""

echo "WSQ is a compression format for fingerprint images used by FBI and law enforcement."
echo ""

# Check if virtual environment exists
if [ -d "venv" ]; then
    echo "Activating virtual environment..."
    source venv/bin/activate
fi

echo "Installing WSQ decoder library..."
echo ""

# Try to install wsq library
pip install wsq 2>&1 | tee /tmp/wsq_install.log

if [ $? -eq 0 ]; then
    echo ""
    echo "======================================"
    echo "✓ WSQ Support Installed Successfully!"
    echo "======================================"
    echo ""
    echo "You can now view WSQ fingerprint images in myNIST."
    echo ""
else
    echo ""
    echo "======================================"
    echo "⚠️  WSQ Installation Note"
    echo "======================================"
    echo ""
    echo "The 'wsq' Python library may not be available on PyPI."
    echo ""
    echo "Alternative solutions:"
    echo ""
    echo "1. Try NBIS (NIST Biometric Image Software):"
    echo "   - Download from: https://www.nist.gov/itl/iad/image-group/products-and-services/image-group-open-source-server-nigos"
    echo "   - Compile and install cwsq/dwsq utilities"
    echo ""
    echo "2. Use pillow-jpls (if images are JPEG-LS):"
    echo "   pip install pillow-jpls"
    echo ""
    echo "3. Convert WSQ to PNG externally and re-import"
    echo ""
    echo "For now, myNIST will show an information message when"
    echo "WSQ images are detected, with format details."
    echo ""
fi

echo "Installation complete."
