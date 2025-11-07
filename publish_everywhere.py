#!/usr/bin/env python3
"""
Publish Linux package everywhere with hidden source
"""
import os
import json

def create_flatpak():
    """Create Flatpak manifest for Flathub"""
    manifest = {
        "app-id": "com.realwebthings.fileshare",
        "runtime": "org.freedesktop.Platform",
        "runtime-version": "22.08",
        "sdk": "org.freedesktop.Sdk",
        "command": "fileshare",
        "finish-args": [
            "--share=network",
            "--filesystem=home",
            "--socket=x11"
        ],
        "modules": [{
            "name": "fileshare",
            "buildsystem": "simple",
            "build-commands": [
                "install -Dm755 fileshare ${FLATPAK_DEST}/bin/fileshare"
            ],
            "sources": [{
                "type": "file",
                "path": "releases/linux/fileshare"
            }]
        }]
    }
    
    with open("com.realwebthings.fileshare.json", 'w') as f:
        json.dump(manifest, f, indent=2)
    
    print("✅ Flatpak manifest: com.realwebthings.fileshare.json")

def create_snap():
    """Create Snap package config"""
    os.makedirs("snap", exist_ok=True)
    
    with open("snap/snapcraft.yaml", 'w') as f:
        f.write('''name: fileshare-app
base: core22
version: '1.0.0'
summary: Share files over WiFi
description: |
  Share files between your computer and mobile devices securely over WiFi.

grade: stable
confinement: strict

apps:
  fileshare-app:
    command: bin/fileshare
    plugs: [network, network-bind, home]

parts:
  fileshare:
    plugin: dump
    source: releases/linux/
    organize:
      fileshare: bin/fileshare
''')
    
    print("✅ Snap config: snap/snapcraft.yaml")

def create_aur_pkgbuild():
    """Create Arch Linux AUR package"""
    pkgbuild = '''# Maintainer: FileShare <support@fileshare.com>
pkgname=fileshare-bin
pkgver=1.0.0
pkgrel=1
pkgdesc="Share files over WiFi"
arch=('x86_64')
url="https://github.com/realwebthings/file-share"
license=('MIT')
depends=('python')
source=("https://github.com/realwebthings/file-share/releases/download/v${pkgver}/fileshare-universal.run")
sha256sums=('SKIP')

package() {
    install -Dm755 "$srcdir/fileshare-universal.run" "$pkgdir/usr/bin/fileshare-installer"
    
    # Create wrapper
    cat > "$pkgdir/usr/bin/fileshare" << 'EOF'
#!/bin/bash
if [ ! -f "$HOME/.local/share/fileShare/fileshare" ]; then
    echo "Installing fileShare.app..."
    /usr/bin/fileshare-installer
fi
exec "$HOME/.local/share/fileShare/fileshare" "$@"
EOF
    chmod +x "$pkgdir/usr/bin/fileshare"
}
'''
    
    with open("PKGBUILD", 'w') as f:
        f.write(pkgbuild)
    
    print("✅ AUR package: PKGBUILD")

def create_homebrew_formula():
    """Create Homebrew formula for macOS/Linux"""
    formula = '''class Fileshare < Formula
  desc "Share files over WiFi"
  homepage "https://github.com/realwebthings/file-share"
  url "https://github.com/realwebthings/file-share/releases/download/v1.0.0/fileshare-universal.run"
  version "1.0.0"
  sha256 "REPLACE_WITH_ACTUAL_SHA256"

  def install
    bin.install "fileshare-universal.run" => "fileshare-installer"
    
    (bin/"fileshare").write <<~EOS
      #!/bin/bash
      if [ ! -f "$HOME/.local/share/fileShare/fileshare" ]; then
        echo "Installing fileShare.app..."
        #{bin}/fileshare-installer
      fi
      exec "$HOME/.local/share/fileShare/fileshare" "$@"
    EOS
  end

  test do
    system "#{bin}/fileshare", "--help"
  end
end
'''
    
    with open("fileshare.rb", 'w') as f:
        f.write(formula)
    
    print("✅ Homebrew formula: fileshare.rb")

def create_distribution_guide():
    """Create guide for publishing everywhere"""
    guide = '''# Distribution Guide

## 1. GitHub Releases
Upload these files:
- fileshare-universal.run (main installer)
- fileshare-linux.deb (Debian/Ubuntu)
- fileShare.AppDir.tar.gz (AppImage source)

## 2. Package Repositories

### Flathub (Flatpak)
1. Fork https://github.com/flathub/flathub
2. Submit com.realwebthings.fileshare.json
3. Follow Flathub submission process

### Snap Store
```bash
snapcraft login
snapcraft upload fileshare-app_1.0.0_amd64.snap
snapcraft release fileshare-app 1 stable
```

### AUR (Arch Linux)
1. Create AUR account
2. Submit PKGBUILD
3. Maintain package

### Homebrew
1. Fork homebrew-core
2. Submit fileshare.rb formula
3. Create PR

## 3. One-line installers

### Linux
```bash
curl -sSL https://github.com/realwebthings/file-share/releases/latest/download/fileshare-universal.run | bash
```

### Universal
```bash
curl -sSL https://raw.githubusercontent.com/realwebthings/file-share/linux/install-linux.sh | bash
```

## 4. Distribution channels
- ✅ GitHub Releases (primary)
- ✅ Flathub (Flatpak)
- ✅ Snap Store
- ✅ AUR (Arch)
- ✅ Homebrew
- ✅ Direct download
'''
    
    with open("DISTRIBUTION.md", 'w') as f:
        f.write(guide)
    
    print("✅ Distribution guide: DISTRIBUTION.md")

if __name__ == "__main__":
    print("📦 Creating distribution packages...")
    
    create_flatpak()
    create_snap()
    create_aur_pkgbuild()
    create_homebrew_formula()
    create_distribution_guide()
    
    print("\n🎉 Ready to publish everywhere!")
    print("📋 Next steps:")
    print("1. Run: python3 create_compiled_release.py")
    print("2. Upload to GitHub Releases")
    print("3. Submit to package repositories")
    print("4. Update README with install instructions")