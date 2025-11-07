# GitHub Release Steps

## 1. Prepare Files
```bash
# Recreate release assets
python3 create_release_assets.py
```

## 2. Push to Linux Branch
```bash
git add .
git commit -m "Add Linux GUI distribution with protected source"
git push origin linux
```

## 3. Create GitHub Release
1. Go to: https://github.com/realwebthings/file-share/releases
2. Click **"Create a new release"**
3. **Choose a tag:** `v1.0.0-linux`
4. **Target:** `linux` branch
5. **Release title:** `fileShare.app v1.0.0 - Linux GUI Release`
6. **Description:** Copy from `releases/github/RELEASE_NOTES.md`

## 4. Upload Files
Upload these 4 files from `releases/github/`:
- `fileshare-linux-gui.run` (main installer)
- `install-linux.sh` (one-line installer)
- `README-LINUX.md` (documentation)
- `RELEASE_NOTES.md` (release notes)

## 5. Publish Release
Click **"Publish release"**

## 6. Test Installation
```bash
curl -sSL https://raw.githubusercontent.com/realwebthings/file-share/linux/install-linux.sh | bash
```

## 7. Update Main README
Add Linux installation section to main branch README.md