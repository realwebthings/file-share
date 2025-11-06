#!/usr/bin/env python3
"""
Professional installer builder for all platforms
"""
import os
import sys
import platform
import subprocess
import shutil

def install_requirements():
    """Install required packages"""
    packages = ['pyinstaller', 'cx_freeze']
    for package in packages:
        try:
            __import__(package)
        except ImportError:
            print(f"Installing {package}...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", package])

def build_windows_installer():
    """Build Windows .exe and .msi installer"""
    print("🪟 Building Windows installer...")
    
    # PyInstaller spec for Windows
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-
import sys
sys.setrecursionlimit(5000)

a = Analysis(
    ['auth_server.py'],
    pathex=[],
    binaries=[],
    datas=[('templates', 'templates')],
    hiddenimports=['sqlite3', 'hashlib', 'secrets'],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=None,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

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
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,
)
'''
    
    with open('windows_build.spec', 'w') as f:
        f.write(spec_content)
    
    # Build executable
    subprocess.run(['pyinstaller', 'windows_build.spec', '--clean', '--onefile'])
    
    # Create NSIS installer script
    nsis_script = '''
!define APPNAME "File Share Server"
!define COMPANYNAME "FileShare"
!define DESCRIPTION "Secure file sharing between devices"
!define VERSIONMAJOR 1
!define VERSIONMINOR 0
!define VERSIONBUILD 0

!define HELPURL "https://github.com/fileshare/help"
!define UPDATEURL "https://github.com/fileshare/updates"
!define ABOUTURL "https://github.com/fileshare/about"

!define INSTALLSIZE 50000

RequestExecutionLevel admin

InstallDir "$PROGRAMFILES\\${COMPANYNAME}\\${APPNAME}"

Name "${APPNAME}"
Icon "icon.ico"
outFile "FileShareServer-Setup.exe"

!include LogicLib.nsh

page components
page directory
page instfiles

!macro VerifyUserIsAdmin
UserInfo::GetAccountType
pop $0
${If} $0 != "admin"
    messageBox mb_iconstop "Administrator rights required!"
    setErrorLevel 740
    quit
${EndIf}
!macroend

function .onInit
    setShellVarContext all
    !insertmacro VerifyUserIsAdmin
functionEnd

section "install"
    setOutPath $INSTDIR
    file "dist\\FileShareServer.exe"
    
    writeUninstaller "$INSTDIR\\uninstall.exe"
    
    createDirectory "$SMPROGRAMS\\${COMPANYNAME}"
    createShortCut "$SMPROGRAMS\\${COMPANYNAME}\\${APPNAME}.lnk" "$INSTDIR\\FileShareServer.exe"
    createShortCut "$DESKTOP\\${APPNAME}.lnk" "$INSTDIR\\FileShareServer.exe"
    
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "DisplayName" "${APPNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "UninstallString" "$INSTDIR\\uninstall.exe"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "InstallLocation" "$INSTDIR"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "Publisher" "${COMPANYNAME}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "HelpLink" "${HELPURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "URLUpdateInfo" "${UPDATEURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "URLInfoAbout" "${ABOUTURL}"
    WriteRegStr HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "DisplayVersion" "${VERSIONMAJOR}.${VERSIONMINOR}.${VERSIONBUILD}"
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "VersionMajor" ${VERSIONMAJOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "VersionMinor" ${VERSIONMINOR}
    WriteRegDWORD HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}" "EstimatedSize" ${INSTALLSIZE}
sectionEnd

section "uninstall"
    delete "$INSTDIR\\FileShareServer.exe"
    delete "$INSTDIR\\uninstall.exe"
    rmDir "$INSTDIR"
    
    delete "$SMPROGRAMS\\${COMPANYNAME}\\${APPNAME}.lnk"
    rmDir "$SMPROGRAMS\\${COMPANYNAME}"
    delete "$DESKTOP\\${APPNAME}.lnk"
    
    DeleteRegKey HKLM "Software\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\${COMPANYNAME} ${APPNAME}"
sectionEnd
'''
    
    with open('installer.nsi', 'w') as f:
        f.write(nsis_script)
    
    print("✅ Windows executable built: dist/FileShareServer.exe")
    print("📦 To create installer: Install NSIS and run 'makensis installer.nsi'")

def build_macos_app():
    """Build macOS .app bundle and .dmg installer"""
    print("🍎 Building macOS app...")
    
    # Build with PyInstaller
    subprocess.run([
        'pyinstaller', 
        '--onefile',
        '--windowed',
        '--name=FileShareServer',
        '--add-data=templates:templates',
        'auth_server.py'
    ])
    
    # Create proper .app structure
    app_name = "FileShareServer.app"
    app_path = f"dist/{app_name}"
    
    if os.path.exists(app_path):
        shutil.rmtree(app_path)
    
    os.makedirs(f"{app_path}/Contents/MacOS")
    os.makedirs(f"{app_path}/Contents/Resources")
    
    # Copy executable
    shutil.copy("dist/FileShareServer", f"{app_path}/Contents/MacOS/")
    
    # Create Info.plist
    plist_content = '''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>CFBundleExecutable</key>
    <string>FileShareServer</string>
    <key>CFBundleIdentifier</key>
    <string>com.fileshare.server</string>
    <key>CFBundleName</key>
    <string>File Share Server</string>
    <key>CFBundleDisplayName</key>
    <string>File Share Server</string>
    <key>CFBundleVersion</key>
    <string>1.0.0</string>
    <key>CFBundleShortVersionString</key>
    <string>1.0</string>
    <key>CFBundlePackageType</key>
    <string>APPL</string>
    <key>LSMinimumSystemVersion</key>
    <string>10.13</string>
    <key>NSHighResolutionCapable</key>
    <true/>
</dict>
</plist>'''
    
    with open(f"{app_path}/Contents/Info.plist", 'w') as f:
        f.write(plist_content)
    
    # Make executable
    os.chmod(f"{app_path}/Contents/MacOS/FileShareServer", 0o755)
    
    print(f"✅ macOS app built: {app_path}")
    print("📦 To create DMG: Use 'create-dmg' tool or Disk Utility")

def build_linux_package():
    """Build Linux .deb and .rpm packages"""
    print("🐧 Building Linux packages...")
    
    # Build executable
    subprocess.run([
        'pyinstaller', 
        '--onefile',
        '--name=fileshare-server',
        '--add-data=templates:templates',
        'auth_server.py'
    ])
    
    # Create .deb package structure
    deb_dir = "fileshare-server_1.0-1_amd64"
    os.makedirs(f"{deb_dir}/usr/bin", exist_ok=True)
    os.makedirs(f"{deb_dir}/usr/share/applications", exist_ok=True)
    os.makedirs(f"{deb_dir}/DEBIAN", exist_ok=True)
    
    # Copy executable
    shutil.copy("dist/fileshare-server", f"{deb_dir}/usr/bin/")
    os.chmod(f"{deb_dir}/usr/bin/fileshare-server", 0o755)
    
    # Create control file
    control_content = '''Package: fileshare-server
Version: 1.0-1
Section: net
Priority: optional
Architecture: amd64
Maintainer: FileShare <support@fileshare.com>
Description: Secure file sharing server
 Share files between devices on local network with authentication.
'''
    
    with open(f"{deb_dir}/DEBIAN/control", 'w') as f:
        f.write(control_content)
    
    # Create desktop entry
    desktop_content = '''[Desktop Entry]
Version=1.0
Type=Application
Name=File Share Server
Comment=Share files between devices
Exec=/usr/bin/fileshare-server
Icon=folder
Terminal=true
Categories=Network;FileTransfer;
'''
    
    with open(f"{deb_dir}/usr/share/applications/fileshare-server.desktop", 'w') as f:
        f.write(desktop_content)
    
    # Build .deb package
    subprocess.run(['dpkg-deb', '--build', deb_dir])
    
    print(f"✅ Linux .deb package built: {deb_dir}.deb")

def main():
    """Main build function"""
    print("🏗️  Professional Installer Builder")
    print("=" * 50)
    
    install_requirements()
    
    system = platform.system()
    
    if system == "Windows":
        build_windows_installer()
    elif system == "Darwin":
        build_macos_app()
    elif system == "Linux":
        build_linux_package()
    else:
        print(f"❌ Unsupported platform: {system}")
        return
    
    print("\n🎉 Build completed!")
    print("\n📋 Distribution files created:")
    print("- Windows: .exe executable + NSIS installer script")
    print("- macOS: .app bundle (ready for DMG creation)")
    print("- Linux: .deb package")

if __name__ == "__main__":
    main()