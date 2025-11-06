#!/bin/bash
# Build script for creating professional installers

echo "🏗️  Building Professional Installers"
echo "====================================="

# Install required tools
echo "📦 Installing build tools..."
pip install pyinstaller cx_freeze

# Create releases for current platform
echo "🔨 Building for current platform..."
python create_releases.py

echo ""
echo "🎯 Platform-specific instructions:"
echo ""

case "$(uname -s)" in
    Darwin*)
        echo "🍎 macOS:"
        echo "  - Install create-dmg: brew install create-dmg"
        echo "  - Sign app: codesign -s 'Developer ID' FileShareServer.app"
        echo "  - Notarize: xcrun altool --notarize-app"
        ;;
    Linux*)
        echo "🐧 Linux:"
        echo "  - Create .deb: dpkg-deb --build package"
        echo "  - Create .rpm: rpmbuild -bb package.spec"
        echo "  - Create AppImage: appimagetool FileShareServer.AppDir"
        ;;
    CYGWIN*|MINGW32*|MSYS*|MINGW*)
        echo "🪟 Windows:"
        echo "  - Install NSIS: https://nsis.sourceforge.io/"
        echo "  - Build installer: makensis installer.nsi"
        echo "  - Sign exe: signtool sign /f cert.pfx FileShareServer.exe"
        ;;
esac

echo ""
echo "✅ Build complete! Check 'releases/' folder"
echo ""
echo "📋 For distribution:"
echo "  1. Test on clean system"
echo "  2. Sign executables (recommended)"
echo "  3. Upload to GitHub Releases or website"
echo "  4. Users download and double-click to install"