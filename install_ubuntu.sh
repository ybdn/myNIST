#!/bin/bash
# Installation script for myNIST on Ubuntu
#
# This script installs myNIST in /opt/mynist/ and creates
# desktop menu entries for easy access.

set -e  # Exit on error

echo "================================================"
echo "myNIST Ubuntu Installation Script"
echo "================================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script needs to be run with sudo privileges."
    echo "Please run: sudo ./install_ubuntu.sh"
    exit 1
fi

# Get the real user (not root)
REAL_USER=${SUDO_USER:-$USER}
REAL_HOME=$(getent passwd "$REAL_USER" | cut -d: -f6)

echo "Installing for user: $REAL_USER"
echo "User home directory: $REAL_HOME"
echo ""

# Check if executable exists
if [ ! -f "dist/mynist" ]; then
    echo "ERROR: Executable not found!"
    echo "Please build the application first with: ./build.sh"
    exit 1
fi

# Create installation directory
echo "Creating installation directory..."
INSTALL_DIR="/opt/mynist"
mkdir -p "$INSTALL_DIR"

# Copy executable
echo "Copying executable..."
cp dist/mynist "$INSTALL_DIR/"
chmod +x "$INSTALL_DIR/mynist"

# Copy icon
echo "Copying icon..."
if [ -f "mynist/resources/icons/mynist.png" ]; then
    cp mynist/resources/icons/mynist.png "$INSTALL_DIR/"
else
    echo "WARNING: Icon file not found, skipping..."
fi

# Create desktop file for system-wide installation
echo "Creating desktop entry..."
DESKTOP_FILE="/usr/share/applications/mynist.desktop"

cat > "$DESKTOP_FILE" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=myNIST
GenericName=NIST File Viewer
Comment=View and edit ANSI/NIST-ITL biometric files
Exec=/opt/mynist/mynist
Icon=/opt/mynist/mynist.png
Terminal=false
Categories=Utility;FileTools;Graphics;Science;
Keywords=NIST;biometric;fingerprint;viewer;forensic;
StartupWMClass=mynist
StartupNotify=true
MimeType=application/x-nist;application/x-eft;application/x-an2;
EOF

# Create symbolic link in /usr/local/bin
echo "Creating symbolic link..."
ln -sf "$INSTALL_DIR/mynist" /usr/local/bin/mynist

# Update desktop database
echo "Updating desktop database..."
update-desktop-database /usr/share/applications/ 2>/dev/null || true

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "myNIST has been installed to: $INSTALL_DIR"
echo ""
echo "You can now launch myNIST by:"
echo "  1. Searching for 'myNIST' in your applications menu"
echo "  2. Running 'mynist' from the terminal"
echo "  3. Running '/opt/mynist/mynist' directly"
echo ""
echo "To uninstall, run: sudo ./uninstall_ubuntu.sh"
echo ""
