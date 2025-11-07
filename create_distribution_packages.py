#!/usr/bin/env python3
"""
Create proper Linux distribution packages
"""
import os
import subprocess
import shutil
import tempfile

def create_appimage():
    """Create AppImage for universal Linux distribution"""
    print("📦 Creating AppImage...")
    
    # Create AppDir structure
    appdir = "fileShare.AppDir"
    if os.path.exists(appdir):
        shutil.rmtree(appdir)
    
    os.makedirs(f"{appdir}/usr/bin")
    os.makedirs(f"{appdir}/usr/share/fileshare")
    os.makedirs(f"{appdir}/usr/share/applications")
    os.makedirs(f"{appdir}/usr/share/icons/hicolor/256x256/apps")
    
    # Copy application files
    shutil.copy("auth_server.py", f"{appdir}/usr/share/fileshare/")
    shutil.copy("remote_control.py", f"{appdir}/usr/share/fileshare/")
    shutil.copytree("templates", f"{appdir}/usr/share/fileshare/templates")
    
    # Create AppRun script
    apprun_content = '''#!/bin/bash
HERE="$(dirname "$(readlink -f "${0}")")"
export PATH="${HERE}/usr/bin:${PATH}"
export FILESHARE_DB_PATH="$HOME/.fileshare/users.db"
mkdir -p "$HOME/.fileshare"
cd "${HERE}/usr/share/fileshare"
python3 auth_server.py "$@"
'''
    
    with open(f"{appdir}/AppRun", 'w') as f:
        f.write(apprun_content)
    os.chmod(f"{appdir}/AppRun", 0o755)
    
    # Create desktop file
    desktop_content = '''[Desktop Entry]
Type=Application
Name=fileShare.app
Comment=Share files securely over WiFi
Exec=fileshare
Icon=fileshare
Categories=Network;FileTransfer;
'''
    
    with open(f"{appdir}/fileshare.desktop", 'w') as f:
        f.write(desktop_content)
    
    with open(f"{appdir}/usr/share/applications/fileshare.desktop", 'w') as f:
        f.write(desktop_content)
    
    # Create simple icon (text-based)
    icon_content = '''<?xml version="1.0" encoding="UTF-8"?>
<svg width="256" height="256" xmlns="http://www.w3.org/2000/svg">
  <rect width="256" height="256" fill="#007bff"/>
  <text x="128" y="140" font-family="Arial" font-size="60" fill="white" text-anchor="middle">📱</text>
  <text x="128" y="200" font-family="Arial" font-size="20" fill="white" text-anchor="middle">fileShare</text>
</svg>'''
    
    with open(f"{appdir}/fileshare.svg", 'w') as f:
        f.write(icon_content)
    
    with open(f"{appdir}/usr/share/icons/hicolor/256x256/apps/fileshare.svg", 'w') as f:
        f.write(icon_content)
    
    print("✅ AppImage structure created")
    print("📝 To build AppImage, download appimagetool and run:")
    print(f"   ./appimagetool {appdir}")

def create_flatpak_manifest():
    """Create Flatpak manifest"""
    print("📦 Creating Flatpak manifest...")
    
    manifest = {
        "app-id": "com.fileshare.app",
        "runtime": "org.freedesktop.Platform",
        "runtime-version": "22.08",
        "sdk": "org.freedesktop.Sdk",
        "command": "fileshare",
        "finish-args": [
            "--share=network",
            "--filesystem=home",
            "--socket=x11",
            "--socket=wayland"
        ],
        "modules": [
            {
                "name": "python3-requests",
                "buildsystem": "simple",
                "build-commands": [
                    "pip3 install --verbose --exists-action=i --no-index --find-links=\"file://${PWD}\" --prefix=${FLATPAK_DEST} requests"
                ],
                "sources": [
                    {
                        "type": "file",
                        "url": "https://files.pythonhosted.org/packages/py3/r/requests/requests-2.31.0-py3-none-any.whl",
                        "sha256": "58cd2187c01e70e6e26505bca751777aa9f2ee0b7f4300988b709f44e013003f"
                    }
                ]
            },
            {
                "name": "fileshare",
                "buildsystem": "simple",
                "build-commands": [
                    "install -Dm755 auth_server.py ${FLATPAK_DEST}/bin/fileshare-server",
                    "install -Dm644 remote_control.py ${FLATPAK_DEST}/share/fileshare/remote_control.py",
                    "cp -r templates ${FLATPAK_DEST}/share/fileshare/",
                    "install -Dm644 fileshare.desktop ${FLATPAK_DEST}/share/applications/com.fileshare.app.desktop"
                ],
                "sources": [
                    {
                        "type": "dir",
                        "path": "."
                    }
                ]
            }
        ]
    }
    
    import json
    with open("com.fileshare.app.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print("✅ Flatpak manifest created: com.fileshare.app.json")

def create_snap_yaml():
    """Create Snap package configuration"""
    print("📦 Creating Snap configuration...")
    
    os.makedirs("snap", exist_ok=True)
    
    snapcraft_yaml = '''name: fileshare-app
base: core22
version: '1.0.0'
summary: Share files securely over WiFi
description: |
  fileShare.app allows you to easily share files between your computer
  and mobile devices over your local WiFi network. Features include secure
  authentication, mobile-friendly interface, video streaming, and rate limiting.

grade: stable
confinement: strict

apps:
  fileshare-app:
    command: bin/fileshare
    plugs:
      - network
      - network-bind
      - home

parts:
  fileshare:
    plugin: python
    source: .
    python-requirements:
      - requests
      - urllib3
    stage-packages:
      - python3
    override-build: |
      craftctl default
      mkdir -p $CRAFT_PART_INSTALL/bin
      mkdir -p $CRAFT_PART_INSTALL/share/fileshare
      cp auth_server.py $CRAFT_PART_INSTALL/bin/fileshare-server
      cp remote_control.py $CRAFT_PART_INSTALL/share/fileshare/
      cp -r templates $CRAFT_PART_INSTALL/share/fileshare/
      
      # Create launcher
      cat > $CRAFT_PART_INSTALL/bin/fileshare << 'EOF'
      #!/bin/bash
      export FILESHARE_DB_PATH="$SNAP_USER_DATA/users.db"
      cd $SNAP/share/fileshare
      python3 $SNAP/bin/fileshare-server "$@"
      EOF
      chmod +x $CRAFT_PART_INSTALL/bin/fileshare
'''
    
    with open("snap/snapcraft.yaml", 'w') as f:
        f.write(snapcraft_yaml)
    
    print("✅ Snap configuration created: snap/snapcraft.yaml")
    print("📝 To build: snapcraft")

def main():
    """Create all distribution packages"""
    print("🐧 Creating Linux Distribution Packages")
    print("=" * 50)
    
    os.makedirs("releases", exist_ok=True)
    
    create_appimage()
    print()
    create_flatpak_manifest()
    print()
    create_snap_yaml()
    
    print("\n🎉 Distribution packages configured!")
    print("\n📋 Next steps:")
    print("1. AppImage: Download appimagetool and build")
    print("2. Flatpak: Use flatpak-builder with the manifest")
    print("3. Snap: Run 'snapcraft' to build")
    print("4. Use the improved .run installer for direct distribution")

if __name__ == "__main__":
    main()