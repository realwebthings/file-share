# Linux Distribution Guide

This directory contains build scripts for creating fileShare.app packages for all major Linux distributions.

## 🚀 Quick Build

```bash
# Build all packages at once
python3 build-all.py

# Or build specific format
python3 build-run.py      # Universal .run installer
python3 build-deb.py      # Debian/Ubuntu package
python3 build-rpm.py      # Red Hat/Fedora package
python3 build-snap.py     # Snap package
python3 build-flatpak.py  # Flatpak package
```

## 📦 Package Formats

| Format | Distributions | Command |
|--------|---------------|---------|
| `.run` | **All Linux** | `python3 build-run.py` |
| `.deb` | Debian, Ubuntu, Mint | `python3 build-deb.py` |
| `.rpm` | Fedora, CentOS, RHEL | `python3 build-rpm.py` |
| `snap` | Universal | `python3 build-snap.py` |
| `flatpak` | Universal | `python3 build-flatpak.py` |

## 📁 Output Structure

```
build/
├── run/        # Universal .run installer
├── deb/        # Debian packages
├── rpm/        # RPM packages  
├── snap/       # Snap configuration
└── flatpak/    # Flatpak configuration
```

## 🎯 Distribution Ready

All packages are ready for:
- GitHub Releases
- Official repositories
- Snap Store
- Flathub
- Direct distribution