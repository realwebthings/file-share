# 📱 File Share Server - User Guide

Share files between your computer and phone easily!

## 🚀 Quick Setup (Non-Developers)

### Option 1: One-Click Installer
1. **Download** all files to a folder on your computer
2. **Double-click** `install.py` 
3. **Follow** the prompts - it creates a desktop shortcut
4. **Done!** Click the desktop shortcut to start

### Option 2: Manual Setup
1. **Install Python** from [python.org](https://python.org) (if not installed)
2. **Download** all files to a folder
3. **Open Terminal/Command Prompt** in that folder
4. **Type**: `python auth_server.py` (or `python3 auth_server.py` on Mac/Linux)

## 📱 Using the Server

### Starting the Server
1. **Run** the server (desktop shortcut or command)
2. **Save** the admin password shown (you'll need it!)
3. **Note** the IP address displayed (like `192.168.1.100:8000`)

### On Your Phone
1. **Connect** to same WiFi as your computer
2. **Open browser** and go to the IP address shown
3. **Register** a new account or login as admin
4. **Browse** and download files from your computer!

## 🔐 First Time Setup

### Admin Login
- **Username**: `admin`
- **Password**: The random code shown when server starts (save it!)

### Adding Users
1. **Others register** accounts on the welcome page
2. **You approve** them in the Admin Panel
3. **They can then** access files

## 📋 Features

- ✅ **Browse** computer files from phone
- ✅ **Download** files to phone
- ✅ **Upload** files from phone to computer
- ✅ **Secure** with passwords and user approval
- ✅ **Works** on same WiFi network

## 🛡️ Security Tips

- **Only use** on trusted home/office WiFi
- **Stop server** when not needed
- **Don't share** admin password
- **Approve** only known users

## 📞 Troubleshooting

### Can't Connect from Phone?
- ✅ Both devices on same WiFi?
- ✅ Firewall blocking port 8000?
- ✅ Try different port: `python auth_server.py --port 8080`

### Forgot Admin Password?
- ✅ Delete `users.db` file
- ✅ Restart server (new password will be shown)

### Server Won't Start?
- ✅ Python installed correctly?
- ✅ All template files present?
- ✅ Port 8000 already in use?

## 🎯 Common Use Cases

### Share Photos to Phone
1. Start server on computer
2. Browse to Photos folder on phone
3. Tap photos to download

### Get Files from Phone
1. Use upload feature on phone browser
2. Select files from phone
3. Files appear in server folder

### Family File Sharing
1. Set up server on main computer
2. Family members register accounts
3. Admin approves family members
4. Everyone can access shared files

## 🔧 Advanced Options

### Change Port
```bash
python auth_server.py --port 8080
```

### Custom Directory
```bash
cd /path/to/share
python auth_server.py
```

### View Database
```bash
sqlite3 users.db
.tables
SELECT * FROM users;
```

---

**Need Help?** Check the terminal/command prompt for error messages and IP addresses.