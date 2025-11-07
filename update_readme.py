#!/usr/bin/env python3
"""
Update README.md with Linux GUI installation
"""

def update_readme():
    """Add Linux GUI installation section to README"""
    
    linux_section = """
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

"""
    
    try:
        with open('README.md', 'r') as f:
            content = f.read()
        
        # Insert Linux section after Quick Start
        if '## Quick Start' in content:
            parts = content.split('## Quick Start')
            if len(parts) >= 2:
                # Find the end of Quick Start section
                remaining = parts[1]
                next_section = remaining.find('\n## ')
                if next_section != -1:
                    before_next = remaining[:next_section]
                    after_next = remaining[next_section:]
                    new_content = parts[0] + '## Quick Start' + before_next + linux_section + after_next
                else:
                    new_content = parts[0] + '## Quick Start' + remaining + linux_section
                
                with open('README.md', 'w') as f:
                    f.write(new_content)
                
                print("✅ README.md updated with Linux GUI installation")
                return
        
        # If Quick Start not found, append to end
        with open('README.md', 'a') as f:
            f.write(linux_section)
        
        print("✅ Linux section added to README.md")
        
    except FileNotFoundError:
        # Create new README if it doesn't exist
        readme_content = f"""# fileShare.app

Share files between your computer and mobile devices securely over WiFi.

{linux_section}

## Features

- ✅ Cross-platform (Windows, macOS, Linux)
- ✅ Secure authentication with admin approval
- ✅ Mobile-friendly web interface
- ✅ Video streaming support
- ✅ Rate limiting protection
- ✅ GUI and CLI interfaces

## Security

- Only use on trusted networks
- Admin approval required for new users
- Automatic rate limiting
- Secure token-based authentication
"""
        
        with open('README.md', 'w') as f:
            f.write(readme_content)
        
        print("✅ Created new README.md with Linux GUI installation")

if __name__ == "__main__":
    update_readme()