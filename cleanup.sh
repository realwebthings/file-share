#!/bin/bash
# Clean up unnecessary files for final project

echo "🧹 Cleaning up project files..."

# Remove old/unused server files
rm -f file_server.py
rm -f simple_server.py
rm -f secure_server.py
rm -f mobile_server.py

# Remove redundant build files
rm -f build_app.py
rm -f build_installer.py
rm -f build_all.sh
rm -f install.py

# Remove documentation files (keep only essential ones)
rm -f MOBILE_ALTERNATIVES.md
rm -f BUILD_INSTRUCTIONS.txt

echo "✅ Cleanup complete!"
echo ""
echo "📁 Essential files remaining:"
echo "  - auth_server.py (main server)"
echo "  - templates/ (HTML files)"
echo "  - build_release.sh (one-click build)"
echo "  - setup_build_env.py (environment setup)"
echo "  - create_releases.py (release builder)"
echo "  - stop_all.sh (process killer)"
echo "  - README.md (project info)"
echo "  - USER_GUIDE.md (user instructions)"