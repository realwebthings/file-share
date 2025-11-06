#!/usr/bin/env python3
"""
Build script to create standalone executable for non-developers
"""
import os
import subprocess
import sys

def build_executable():
    """Build standalone executable using PyInstaller"""
    
    # Install PyInstaller if not present
    try:
        import PyInstaller
    except ImportError:
        print("Installing PyInstaller...")
        subprocess.check_call([sys.executable, "-m", "pip", "install", "pyinstaller"])
    
    # Create spec file for better control
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['auth_server.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates')],
    hiddenimports=[],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
    a.datas,
    [],
    name='FileShareServer',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)
'''
    
    with open('FileShareServer.spec', 'w') as f:
        f.write(spec_content)
    
    # Build the executable
    print("Building executable...")
    subprocess.check_call(['pyinstaller', 'FileShareServer.spec', '--clean'])
    
    print("\n✅ Build complete!")
    print("📁 Executable location: dist/FileShareServer")
    print("\n📋 To distribute:")
    print("1. Copy the entire 'dist' folder to user's computer")
    print("2. User double-clicks 'FileShareServer' to run")
    print("3. Server starts automatically with GUI instructions")

if __name__ == "__main__":
    build_executable()