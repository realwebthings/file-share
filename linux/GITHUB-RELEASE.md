# 🚀 fileShare.app v2.0.0 - Universal Linux Distribution

**Share files between devices over WiFi with secure authentication and modern GUI control panel.**

## ✨ What's New in v2.0.0

- 🔒 **Enhanced Security** - Removed plain text password storage
- 🎛️ **Improved Control Panel** - Better web-based management interface  
- 📦 **Multiple Package Formats** - .deb, .rpm, .run, Snap, Flatpak support
- 🐧 **Universal Compatibility** - Works on ALL Linux distributions
- ⚡ **Performance Optimizations** - Faster file streaming and caching
- 🔧 **Better Error Handling** - More robust database and network operations

## 📥 Quick Installation

### 🎯 Universal Installer (All Linux Distributions)
```bash
wget https://github.com/yourusername/file-share/releases/latest/download/fileshare-installer.run
chmod +x fileshare-installer.run
./fileshare-installer.run
```

### 📦 Distribution-Specific Packages

#### Debian/Ubuntu
```bash
wget https://github.com/yourusername/file-share/releases/latest/download/fileshare_2.0.0.deb
sudo dpkg -i fileshare_2.0.0.deb
```

#### Red Hat/Fedora/CentOS
```bash
wget https://github.com/yourusername/file-share/releases/latest/download/fileshare-2.0.0-1.noarch.rpm
sudo rpm -i fileshare-2.0.0-1.noarch.rpm
```

## 🚀 Usage

```bash
# GUI Control Panel (Recommended)
fileshare-gui

# Terminal Mode
fileshare

# Uninstall
fileshare-uninstall
```

## 🎯 Features

- ✅ **Secure Authentication** - Token-based login system
- ✅ **Admin Panel** - User management and file sharing controls
- ✅ **Mobile Optimized** - Perfect interface for phones/tablets
- ✅ **Video Streaming** - Stream videos directly to mobile devices
- ✅ **Rate Limiting** - Protection against brute force attacks
- ✅ **Cross-Platform** - Works on any device with a web browser

## 📱 How to Use

1. **Start the server**: Run `fileshare-gui`
2. **Note the admin password** displayed in the GUI
3. **Connect devices** to the same WiFi network
4. **Open browser** on your phone/tablet
5. **Visit the URL** shown in the control panel
6. **Login** with username `admin` and the displayed password
7. **Share files** by adding folders in the admin panel

## 🔧 System Requirements

- **Python**: 3.6 or higher
- **GUI**: tkinter (for control panel)
- **Network**: WiFi connection
- **OS**: Any Linux distribution

## 📋 Package Details

| Package | Size | Description |
|---------|------|-------------|
| `fileshare-installer.run` | ~45KB | Universal self-extracting installer |
| `fileshare_2.0.0.deb` | ~25KB | Debian/Ubuntu package |
| `fileshare-2.0.0-1.noarch.rpm` | ~30KB | Red Hat/Fedora package |

## 🛡️ Security Notes

- 🔒 **Local Network Only** - Designed for trusted WiFi networks
- 🔑 **Auto-Generated Passwords** - New admin password on each startup
- 🚫 **Rate Limited** - Automatic protection against failed login attempts
- 📁 **Selective Sharing** - Only admin-approved folders are accessible

## 🆘 Troubleshooting

**GUI won't start?**
```bash
# Install tkinter
sudo apt install python3-tk  # Debian/Ubuntu
sudo dnf install python3-tkinter  # Fedora
```

**Can't access from phone?**
- Ensure both devices are on the same WiFi
- Check firewall settings
- Try the IP address shown in the control panel

## 📚 Documentation

- [Linux Distribution Guide](https://github.com/yourusername/file-share/tree/main/linux)
- [Installation Troubleshooting](https://github.com/yourusername/file-share/blob/main/linux/README.md)
- [Security Best Practices](https://github.com/yourusername/file-share/blob/main/README.md)

---

**⭐ Star this repo if fileShare.app helped you!**
**🐛 Report issues on [GitHub Issues](https://github.com/yourusername/file-share/issues)**