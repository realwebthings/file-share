# 🎛️ Remote Control Guide

## How to Control Software Remotely

### 🚨 **Kill Switch (Emergency Stop)**

1. **Create GitHub Release** with these settings:
   - ✅ Mark as "Pre-release"
   - 📝 Title: `KILL_SWITCH - Emergency Stop`
   - 📄 Description: Your message to users

2. **What happens:**
   - All running software will show your message
   - Users must press Enter to exit
   - Software stops completely

### 🔄 **Force Update**

1. **Create GitHub Release** with:
   - ✅ Mark as "Latest release" 
   - 📝 Version: Higher than current (e.g., `v1.1.0`)
   - 📄 Include download links

2. **What happens:**
   - Software detects newer version
   - Shows update required message
   - Forces users to download new version

## 📋 **Setup Instructions**

### Step 1: Update Control URL
Edit `remote_control.py` line 11:
```python
self.control_url = "https://api.github.com/repos/YOUR_USERNAME/YOUR_REPO/releases/latest"
```

### Step 2: Set Current Version
Edit `remote_control.py` line 12:
```python
self.current_version = "1.0.0"  # Your current version
```

### Step 3: Adjust Check Interval (Optional)
```python
self.check_interval = 300  # Seconds (300 = 5 minutes)
```

## 🎯 **Usage Examples**

### Emergency Stop All Users:
1. Go to GitHub → Releases → Create Release
2. Title: `KILL_SWITCH - Security Update Required`
3. Check "Pre-release"
4. Description: `Please update immediately for security reasons.`
5. Publish

### Force Update:
1. Create new release: `v1.1.0`
2. Upload new executable files
3. Description: `Critical update - please download new version`
4. Publish as latest release

## ⚙️ **Technical Details**

- **Check Frequency**: Every 5 minutes
- **Timeout**: 10 seconds per check
- **Fallback**: Silent failure (doesn't interrupt user)
- **Background**: Runs in separate thread
- **No Internet**: Software works normally

## 🔒 **Security Notes**

- Uses GitHub API (public, read-only)
- No personal data transmitted
- Only version checking
- Users can block internet access to disable

## 📱 **User Experience**

- **Normal**: No interruption
- **Kill Switch**: Clear message + graceful exit
- **Update Required**: Download link + forced exit
- **No Internet**: Works normally offline