#!/bin/bash
# Complete build and release process

echo "🚀 Starting Complete Build Process"
echo "=================================="

# Step 1: Stop any running processes
echo "🛑 Step 1: Stopping existing processes..."
./stop_all.sh

# Step 2: Setup build environment
echo "🔧 Step 2: Setting up build environment..."
python3 setup_build_env.py

# Step 3: Build releases for all platforms
echo "🏗️  Step 3: Building releases for all platforms..."
python3 build_with_venv.py all

# Step 4: Show results
echo "📦 Step 4: Build complete!"
echo ""
echo "📁 Generated files:"
ls -la releases/ 2>/dev/null || echo "No releases folder found"

echo ""
echo "🎉 Build process finished!"
echo "📋 Next steps:"
echo "  1. Test the executable in releases/ folder"
echo "  2. Distribute to users"
echo "  3. Users double-click to run (no Python needed)"