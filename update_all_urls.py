#!/usr/bin/env python3
"""
Update all URLs to use Linux branch
"""
import os
import glob

def update_urls():
    """Update all GitHub URLs to use Linux branch"""
    
    files_to_update = [
        'README.md',
        'update_readme.py',
        'publish_everywhere.py',
        'DISTRIBUTION.md'
    ]
    
    for filename in files_to_update:
        if os.path.exists(filename):
            try:
                with open(filename, 'r') as f:
                    content = f.read()
                
                # Update URLs
                content = content.replace(
                    'https://raw.githubusercontent.com/realwebthings/file-share/main',
                    'https://raw.githubusercontent.com/realwebthings/file-share/linux'
                )
                content = content.replace(
                    'https://github.com/realwebthings/file-share/releases/latest/download/fileshare-gui-simple.run',
                    'https://github.com/realwebthings/file-share/releases/latest/download/fileshare-linux-gui.run'
                )
                
                with open(filename, 'w') as f:
                    f.write(content)
                
                print(f"✅ Updated {filename}")
            except Exception as e:
                print(f"❌ Error updating {filename}: {e}")
    
    print("\n🎉 All URLs updated to use Linux branch!")

if __name__ == "__main__":
    update_urls()