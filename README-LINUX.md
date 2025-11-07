# FileShare Server - Linux Installation Guide

Share files between your Linux computer and mobile devices instantly!

## 🚀 Quick Install (Recommended)

### Method 1: One-Line Install Script
```bash
curl -sSL https://raw.githubusercontent.com/yourusername/fileshare-server/main/install.sh | bash
```

### Method 2: Manual Installation
```bash
# Download and extract
git clone https://github.com/yourusername/fileshare-server.git
cd fileshare-server
chmod +x install.sh
./install.sh
```

## 📦 Package Installation

### Ubuntu/Debian (.deb)
```bash
# Build package
chmod +x build-deb.sh
./build-deb.sh

# Install
sudo dpkg -i fileshare-server_1.0.0_all.deb
```

### CentOS/RHEL/Fedora (.rpm)
```bash
# Install build tools
sudo yum install rpm-build

# Build package
chmod +x build-rpm.sh
./build-rpm.sh

# Install
sudo rpm -i ~/rpmbuild/RPMS/noarch/fileshare-server-1.0.0-1.*.rpm
```

## 🎯 Usage

1. **Start the server:**
   ```bash
   fileshare
   ```

2. **Access from your phone:**
   - Connect phone to same WiFi as your Linux computer
   - Open browser and go to: `http://YOUR_COMPUTER_IP:8000`
   - Register an account or login as admin

3. **Admin login:**
   - Username: `admin`
   - Password: Shown in terminal when server starts

## ✨ Features

- ✅ **Zero Dependencies** - Uses only Python standard library
- ✅ **Secure Authentication** - Token-based with admin approval
- ✅ **Mobile-Friendly** - Responsive web interface
- ✅ **Video Streaming** - Stream videos directly to mobile
- ✅ **Rate Limiting** - Protection against brute force attacks
- ✅ **File Upload/Download** - Bidirectional file transfer

## 🔧 Requirements

- Python 3.8 or higher
- Linux (Ubuntu, Debian, CentOS, RHEL, Fedora, Arch, etc.)

## 🛡️ Security

- Only use on trusted networks (home WiFi)
- Admin approval required for new users
- Automatic rate limiting after failed login attempts
- Secure token-based authentication

## 📱 Use Cases

- **Share photos** from Linux to phone
- **Transfer documents** between devices
- **Stream videos** to mobile without copying
- **Quick file exchange** without cloud services
- **Access Linux files** remotely on same network

## 🆘 Troubleshooting

### Server won't start
```bash
# Check Python version
python3 --version

# Check if port 8000 is free
sudo netstat -tlnp | grep :8000
```

### Can't access from phone
```bash
# Check your computer's IP
ip addr show | grep inet

# Check firewall (Ubuntu/Debian)
sudo ufw allow 8000

# Check firewall (CentOS/RHEL)
sudo firewall-cmd --add-port=8000/tcp --permanent
sudo firewall-cmd --reload
```

### Permission denied
```bash
# Make sure install script is executable
chmod +x install.sh

# Check if ~/.local/bin is in PATH
echo $PATH | grep -o ~/.local/bin
```

## 🔄 Uninstall

### Script Installation
```bash
rm -rf ~/.local/share/fileshare
rm ~/.local/bin/fileshare
```

### Package Installation
```bash
# Debian/Ubuntu
sudo dpkg -r fileshare-server

# CentOS/RHEL/Fedora
sudo rpm -e fileshare-server
```

## 📞 Support

- Report issues: [GitHub Issues](https://github.com/yourusername/fileshare-server/issues)
- Documentation: [GitHub Wiki](https://github.com/yourusername/fileshare-server/wiki)

---

**Made with ❤️ for Linux users who want simple, secure file sharing!**