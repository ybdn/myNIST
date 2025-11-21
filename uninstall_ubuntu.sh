#!/bin/bash
# Uninstallation script for myNIST on Ubuntu

set -e  # Exit on error

echo "================================================"
echo "myNIST Ubuntu Uninstallation Script"
echo "================================================"
echo ""

# Check if running with sudo
if [ "$EUID" -ne 0 ]; then
    echo "This script needs to be run with sudo privileges."
    echo "Please run: sudo ./uninstall_ubuntu.sh"
    exit 1
fi

echo "This will remove myNIST from your system."
read -p "Are you sure you want to continue? (y/N) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "Uninstallation cancelled."
    exit 0
fi

echo ""
echo "Removing myNIST..."

# Remove installation directory
if [ -d "/opt/mynist" ]; then
    echo "  Removing /opt/mynist/..."
    rm -rf /opt/mynist
fi

# Remove desktop file
if [ -f "/usr/share/applications/mynist.desktop" ]; then
    echo "  Removing desktop entry..."
    rm -f /usr/share/applications/mynist.desktop
fi

# Remove symbolic link
if [ -L "/usr/local/bin/mynist" ]; then
    echo "  Removing symbolic link..."
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
echo "myNIST has been removed from your system."
echo ""
