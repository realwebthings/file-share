#!/usr/bin/env python3
"""
Fix Linux .tar.gz release to work properly
"""
import tarfile
import os

def fix_linux_tarball():
    """Fix the .tar.gz to preserve executable permissions"""
    
    # Set executable permission on auth_server.py
    os.chmod('releases/linux/fileShare', 0o755)
    os.chmod('releases/linux/start-fileShare.sh', 0o755)
    
    # Recreate tarball with proper permissions
    with tarfile.open('releases/file-share-linux-fixed.tar.gz', 'w:gz') as tar:
        # Add files with explicit permissions
        for filename, arcname, mode in [
            ('releases/linux/fileShare', 'fileShare/fileShare', 0o755),
            ('releases/linux/start-fileShare.sh', 'fileShare/start-fileShare.sh', 0o755),
            ('releases/linux/fileShare.desktop', 'fileShare/fileShare.desktop', 0o644)
        ]:
            if os.path.exists(filename):
                tarinfo = tar.gettarinfo(filename, arcname)
                tarinfo.mode = mode
                with open(filename, 'rb') as f:
                    tar.addfile(tarinfo, f)
    
    print("✅ Fixed tarball created: releases/file-share-linux-fixed.tar.gz")

if __name__ == "__main__":
    fix_linux_tarball()