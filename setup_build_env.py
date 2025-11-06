#!/usr/bin/env python3
"""
Setup build environment with virtual environment
"""
import os
import sys
import subprocess
import venv

def setup_venv():
    """Create virtual environment and install dependencies"""
    venv_path = "build_env"
    
    print("🔧 Setting up build environment...")
    
    # Create virtual environment
    if not os.path.exists(venv_path):
        print("📦 Creating virtual environment...")
        venv.create(venv_path, with_pip=True)
    
    # Determine activation script path
    if sys.platform == "win32":
        activate_script = os.path.join(venv_path, "Scripts", "activate")
        pip_path = os.path.join(venv_path, "Scripts", "pip")
        python_path = os.path.join(venv_path, "Scripts", "python")
    else:
        activate_script = os.path.join(venv_path, "bin", "activate")
        pip_path = os.path.join(venv_path, "bin", "pip")
        python_path = os.path.join(venv_path, "bin", "python")
    
    # Install PyInstaller and dependencies in virtual environment
    print("📥 Installing PyInstaller and dependencies...")
    subprocess.check_call([python_path, "-m", "pip", "install", "pyinstaller", "requests"])
    
    print("✅ Build environment ready!")
    print(f"📁 Virtual environment: {venv_path}")
    
    # Create build script that uses the venv
    build_script = f'''#!/usr/bin/env python3
import subprocess
import sys
import os

# Use virtual environment Python
venv_python = "{python_path}"

print("🏗️  Building with virtual environment...")
subprocess.run([venv_python, "create_releases.py"] + sys.argv[1:])
'''
    
    with open("build_with_venv.py", "w") as f:
        f.write(build_script)
    
    # Create activation instructions
    if sys.platform == "win32":
        instructions = f'''
🎯 Build Instructions:

Option 1 - Use build script:
  python build_with_venv.py

Option 2 - Manual activation:
  {venv_path}\\Scripts\\activate
  python create_releases.py

Option 3 - Direct build:
  {python_path} create_releases.py
'''
    else:
        instructions = f'''
🎯 Build Instructions:

Option 1 - Use build script:
  python3 build_with_venv.py

Option 2 - Manual activation:
  source {venv_path}/bin/activate
  python create_releases.py

Option 3 - Direct build:
  {python_path} create_releases.py
'''
    
    print(instructions)
    
    # Save instructions to file
    with open("BUILD_INSTRUCTIONS.txt", "w") as f:
        f.write(instructions)

if __name__ == "__main__":
    setup_venv()