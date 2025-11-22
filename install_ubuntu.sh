#!/bin/bash
# Installation script for NIST Studio on Ubuntu
#
# This script installs NIST Studio in /opt/nist-studio/ and creates
# desktop menu entries for easy access.
#
# Usage: Download the release binary, then run:
#   sudo ./install_ubuntu.sh

set -e  # Exit on error

echo "================================================"
echo "NIST Studio Ubuntu Installation Script"
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

# Check if executable exists (from GitHub release)
BINARY_NAME="nist-studio-linux"
if [ ! -f "$BINARY_NAME" ]; then
    # Try alternative name
    BINARY_NAME="nist-studio"
    if [ ! -f "$BINARY_NAME" ]; then
        echo "ERROR: Executable not found!"
        echo "Please download the Linux binary from GitHub releases:"
        echo "  https://github.com/ybdn/NIST-Studio/releases"
        echo ""
        echo "Expected file: nist-studio-linux"
        exit 1
    fi
fi

# Create installation directory
echo "Creating installation directory..."
INSTALL_DIR="/opt/nist-studio"
mkdir -p "$INSTALL_DIR"

# Copy executable
echo "Copying executable..."
cp "$BINARY_NAME" "$INSTALL_DIR/nist-studio"
chmod +x "$INSTALL_DIR/nist-studio"

# Copy icon if available
echo "Copying icon..."
ICON_SOURCE=""
if [ -f "mynist/resources/icons/appicon-nist-studio-256.png" ]; then
    ICON_SOURCE="mynist/resources/icons/appicon-nist-studio-256.png"
elif [ -f "appicon-nist-studio-256.png" ]; then
    ICON_SOURCE="appicon-nist-studio-256.png"
fi

if [ -n "$ICON_SOURCE" ]; then
    cp "$ICON_SOURCE" "$INSTALL_DIR/nist-studio.png"
else
    echo "WARNING: Icon file not found, skipping..."
fi

# Create desktop file for system-wide installation
echo "Creating desktop entry..."
DESKTOP_FILE="/usr/share/applications/nist-studio.desktop"

cat > "$DESKTOP_FILE" << 'EOF'
[Desktop Entry]
Version=1.0
Type=Application
Name=NIST Studio
GenericName=NIST File Viewer
Comment=View and edit ANSI/NIST-ITL biometric files
Exec=/opt/nist-studio/nist-studio
Icon=/opt/nist-studio/nist-studio.png
Terminal=false
Categories=Utility;FileTools;Graphics;Science;
Keywords=NIST;biometric;fingerprint;viewer;forensic;
StartupWMClass=nist-studio
StartupNotify=true
MimeType=application/x-nist;application/x-eft;application/x-an2;
EOF

# Create symbolic link in /usr/local/bin
echo "Creating symbolic link..."
ln -sf "$INSTALL_DIR/nist-studio" /usr/local/bin/nist-studio

# Update desktop database
echo "Updating desktop database..."
update-desktop-database /usr/share/applications/ 2>/dev/null || true

echo ""
echo "================================================"
echo "Installation Complete!"
echo "================================================"
echo ""
echo "NIST Studio has been installed to: $INSTALL_DIR"
echo ""
echo "You can now launch NIST Studio by:"
echo "  1. Searching for 'NIST Studio' in your applications menu"
echo "  2. Running 'nist-studio' from the terminal"
echo "  3. Running '/opt/nist-studio/nist-studio' directly"
echo ""
echo "To uninstall, run: sudo ./uninstall_ubuntu.sh"
echo ""
