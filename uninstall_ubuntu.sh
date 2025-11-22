#!/bin/bash
# Uninstallation script for NIST Studio on Ubuntu

set -e  # Exit on error

echo "================================================"
echo "NIST Studio Ubuntu Uninstallation Script"
echo "================================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script needs to be run with sudo privileges."
    echo "Please run: sudo ./uninstall_ubuntu.sh"
    exit 1
fi

echo "This will remove NIST Studio from your system."
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo "Removing NIST Studio..."

# Remove installation directory (new location)
if [ -d "/opt/nist-studio" ]; then
    echo "  Removing /opt/nist-studio/..."
    rm -rf /opt/nist-studio
fi

# Remove old installation directory (legacy)
if [ -d "/opt/mynist" ]; then
    echo "  Removing legacy /opt/mynist/..."
    rm -rf /opt/mynist
fi

# Remove desktop files
if [ -f "/usr/share/applications/nist-studio.desktop" ]; then
    echo "  Removing desktop entry..."
    rm -f /usr/share/applications/nist-studio.desktop
fi

# Remove old desktop file (legacy)
if [ -f "/usr/share/applications/mynist.desktop" ]; then
    echo "  Removing legacy desktop entry..."
    rm -f /usr/share/applications/mynist.desktop
fi

# Remove symbolic links
if [ -L "/usr/local/bin/nist-studio" ]; then
    echo "  Removing symbolic link..."
    rm -f /usr/local/bin/nist-studio
fi

# Remove old symbolic link (legacy)
if [ -L "/usr/local/bin/mynist" ]; then
    echo "  Removing legacy symbolic link..."
    rm -f /usr/local/bin/mynist
fi

# Update desktop database
echo "  Updating desktop database..."
update-desktop-database /usr/share/applications/ 2>/dev/null || true

echo ""
echo "================================================"
echo "Uninstallation Complete!"
echo "================================================"
echo ""
echo "NIST Studio has been removed from your system."
echo ""
