# Debian/Ubuntu Distribution Guide

## 📦 Building .deb Package

```bash
python3 build-deb.py
```

## 📋 Requirements

- `dpkg-dev` package for building
- Python 3.6+ and tkinter

```bash
# Install build tools
sudo apt install dpkg-dev

# Install dependencies  
sudo apt install python3 python3-tk
```

## 🚀 Installation

### For Users
```bash
# Download and install
wget https://github.com/yourusername/file-share/releases/latest/download/fileshare_1.0.0.deb
sudo dpkg -i fileshare_1.0.0.deb

# Fix dependencies if needed
sudo apt install -f
```

### Usage
```bash
fileshare          # Terminal mode
fileshare-gui      # GUI control panel
```

## 📤 Publishing to Repository

### 1. Personal PPA (Ubuntu)
```bash
# Create PPA on Launchpad
# Upload source package
dput ppa:yourusername/fileshare fileshare_1.0.0_source.changes
```

### 2. Debian Repository
```bash
# Submit to Debian mentors
# Follow Debian packaging guidelines
# Create ITP (Intent to Package) bug
```

### 3. Third-party Repository
```bash
# Create repository structure
mkdir -p repo/dists/stable/main/binary-amd64
cp fileshare_1.0.0.deb repo/dists/stable/main/binary-amd64/

# Generate Packages file
cd repo
dpkg-scanpackages dists/stable/main/binary-amd64 /dev/null | gzip -9c > dists/stable/main/binary-amd64/Packages.gz

# Create Release file
cd dists/stable
apt-ftparchive release . > Release
```

## 🎯 Supported Distributions

- ✅ Ubuntu 18.04+
- ✅ Debian 10+
- ✅ Linux Mint 19+
- ✅ Pop!_OS 20.04+
- ✅ Elementary OS 6+

## 🔧 Package Details

- **Package name:** `fileshare`
- **Dependencies:** `python3 (>= 3.6), python3-tk`
- **Install location:** `/usr/share/fileshare`
- **Executables:** `/usr/bin/fileshare`, `/usr/bin/fileshare-gui`
- **Desktop entry:** `/usr/share/applications/fileshare.desktop`