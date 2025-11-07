# fileShare.app - Linux Installation Guide

Share files between your Linux computer and mobile devices with a beautiful GUI!

## 🚀 Quick Install

### GUI Version (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/realwebthings/file-share/linux/install-linux.sh | bash
```

Then run:
```bash
fileshare-gui
```

### Command Line Version
```bash
curl -sSL https://github.com/realwebthings/file-share/releases/latest/download/fileshare-gui-simple.run | bash
fileshare  # CLI version
```

## ✨ Features

- 🎛️ **GUI Control Panel** - Easy start/stop with buttons
- 📱 **Mobile-Friendly** - Responsive web interface
- 🔐 **Secure Authentication** - Admin approval required
- 📺 **Video Streaming** - Stream videos directly to mobile
- 🚀 **Zero Configuration** - Works out of the box

## 🖥️ GUI Screenshots

The GUI provides:
- Start/Stop server buttons
- Real-time status display
- Mobile URL with auto-detected IP
- Admin password display
- One-click browser opening
- Clear usage instructions

## 📱 Usage

1. **Start the GUI**: `fileshare-gui`
2. **Click "Start Server"**
3. **Note the Mobile URL** (e.g., http://192.168.1.100:8000)
4. **Connect phone to same WiFi**
5. **Open browser on phone** and go to the Mobile URL
6. **Login with admin password** shown in GUI
7. **Browse and download files!**

## 🔧 Requirements

- Python 3.6+ (usually pre-installed)
- tkinter (GUI library)

### Install tkinter if needed:
```bash
# Ubuntu/Debian
sudo apt install python3-tk

# CentOS/RHEL
sudo yum install tkinter

# Fedora
sudo dnf install python3-tkinter

# Arch Linux
sudo pacman -S tk
```

## 🗑️ Uninstall

```bash
rm -rf ~/.local/share/fileShare ~/.local/bin/fileshare* ~/.local/share/applications/fileshare*
```

## 🆘 Troubleshooting

### GUI won't start
```bash
# Check tkinter
python3 -c "import tkinter"

# If error, install tkinter (see requirements above)
```

### Can't access from phone
```bash
# Check firewall
sudo ufw allow 8000  # Ubuntu
sudo firewall-cmd --add-port=8000/tcp --permanent  # CentOS
```

### Server won't start
```bash
# Check if port is free
sudo netstat -tlnp | grep :8000
```

## 🎉 That's it!

Your Linux file sharing with GUI is ready. Enjoy secure, easy file sharing between your computer and mobile devices!