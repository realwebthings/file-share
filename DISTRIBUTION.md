# Distribution Guide

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
