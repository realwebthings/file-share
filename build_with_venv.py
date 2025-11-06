#!/usr/bin/env python3
import subprocess
import sys
import os

# Use virtual environment Python
venv_python = "build_env/bin/python"

print("🏗️  Building with virtual environment...")
subprocess.run([venv_python, "create_releases.py"] + sys.argv[1:])
