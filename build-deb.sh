#!/bin/bash
# Build Debian package for FileShare Server

set -e

PACKAGE_NAME="fileshare-server"
VERSION="1.0.0"
ARCH="all"

echo "🔧 Building Debian package: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

# Create package directory structure
PKG_DIR="debian-package"
rm -rf "$PKG_DIR"
mkdir -p "$PKG_DIR/DEBIAN"
mkdir -p "$PKG_DIR/usr/share/fileshare"
mkdir -p "$PKG_DIR/usr/bin"
mkdir -p "$PKG_DIR/usr/share/doc/fileshare-server"

# Copy control file
cp debian/control "$PKG_DIR/DEBIAN/"

# Copy application files
cp auth_server.py "$PKG_DIR/usr/share/fileshare/"
cp remote_control.py "$PKG_DIR/usr/share/fileshare/"
cp -r templates "$PKG_DIR/usr/share/fileshare/"

# Create executable wrapper
cat > "$PKG_DIR/usr/bin/fileshare" << 'EOF'
#!/bin/bash
cd /usr/share/fileshare
python3 auth_server.py "$@"
EOF

chmod +x "$PKG_DIR/usr/bin/fileshare"

# Copy documentation
cp README.md "$PKG_DIR/usr/share/doc/fileshare-server/"
cp LICENSE "$PKG_DIR/usr/share/doc/fileshare-server/"

# Build the package
dpkg-deb --build "$PKG_DIR" "${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"

echo "✅ Package built: ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "📦 To install:"
echo "   sudo dpkg -i ${PACKAGE_NAME}_${VERSION}_${ARCH}.deb"
echo ""
echo "🚀 To run after installation:"
echo "   fileshare"