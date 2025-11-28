# File Share Server

A simple HTTP server to share files between your Mac and mobile device.

## Quick Start

1. **Run the server on your Mac:**
   ```bash
   python3 file_server.py
   ```

2. **Access from your phone:**
   - Connect your phone to the same WiFi network as your Mac
   - Open browser on phone and go to the IP address shown (e.g., `http://192.168.1.100:8000`)

## 🐧 Linux Installation

### GUI Version (Recommended)
```bash
curl -sSL https://raw.githubusercontent.com/realwebthings/file-share/linux/install-linux.sh | bash
fileshare-gui
```

### Command Line Version
```bash
curl -sSL https://github.com/realwebthings/file-share/releases/latest/download/fileshare-linux-gui.run | bash
fileshare
```

### Features
- 🎛️ GUI Control Panel with start/stop buttons
- 📱 Auto-detected mobile URL display
- 🔐 Admin password shown in GUI
- 🌐 One-click browser opening
- 📋 Clear usage instructions


## Features

- ✅ Browse directories on your Mac from mobile
- ✅ Download files from Mac to mobile
- ✅ Upload files from mobile to Mac
- ✅ Mobile-friendly interface
- ✅ Works on same WiFi network

## Usage Scenarios

### Mac → Mobile (Download files to phone)
1. Run server on Mac
2. Browse to files on phone browser
3. Tap files to download them

### Mobile → Mac (Upload files from phone)
1. Run server on Mac
2. Use upload form on phone browser
3. Select files from phone to upload to Mac

## Security Notes

- Only use on trusted networks
- Server is accessible to anyone on the same network
- Stop server when not needed

## Alternative: Mobile → Mac Server

If you want to access mobile files from Mac, you'll need a mobile app that creates a server. Consider:
- **Android**: Use apps like "HTTP Server" or "WiFi File Transfer"
- **iOS**: Use apps like "Documents by Readdle" with WiFi transfer feature

## Troubleshooting

- Ensure both devices are on same WiFi
- Check firewall settings on Mac
- Try different port if 8000 is busy: `python3 file_server.py --port 8080`