#!/usr/bin/env python3
"""
Build all Linux distribution packages
"""
import os
import sys
import subprocess

def build_all_packages():
    """Build all available package formats"""
    
    print("🚀 Building all Linux packages...")
    
    builders = [
        ("build-run.py", ".run installer"),
        ("build-deb.py", ".deb package"),
        ("build-rpm.py", ".rpm package"), 
        ("build-snap.py", "Snap package"),
        ("build-flatpak.py", "Flatpak package")
    ]
    
    results = []
    
    for script, description in builders:
        print(f"\n📦 Building {description}...")
        try:
            result = subprocess.run([sys.executable, script], 
                                  capture_output=True, text=True, check=True)
            print(f"✅ {description} - SUCCESS")
            results.append((description, "SUCCESS", ""))
        except subprocess.CalledProcessError as e:
            print(f"❌ {description} - FAILED")
            print(f"Error: {e.stderr}")
            results.append((description, "FAILED", e.stderr))
        except FileNotFoundError:
            print(f"❌ {description} - SCRIPT NOT FOUND")
            results.append((description, "NOT FOUND", ""))
    
    # Summary
    print("\n" + "="*50)
    print("📋 BUILD SUMMARY")
    print("="*50)
    
    for desc, status, error in results:
        status_icon = "✅" if status == "SUCCESS" else "❌"
        print(f"{status_icon} {desc:<20} - {status}")
    
    print("\n🎯 Distribution ready packages created!")
    print("📁 Check build/ directory for output files")

if __name__ == "__main__":
    build_all_packages()