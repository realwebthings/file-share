#!/usr/bin/env python3
"""
Create uninstaller for Windows builds
"""
import os

def create_windows_uninstaller():
    """Create Windows uninstaller script"""
    
    uninstaller_content = '''@echo off
title File Share Server - Uninstaller
echo.
echo ========================================
echo   File Share Server Uninstaller
echo ========================================
echo.
echo This will remove File Share Server from your computer.
echo.
set /p confirm="Are you sure? (y/N): "
if /i "%confirm%" NEQ "y" (
    echo Uninstall cancelled.
    pause
    exit /b
)

echo.
echo Removing files...

:: Stop any running processes
taskkill /f /im FileShareServer.exe 2>nul

:: Remove files
del /q "%~dp0FileShareServer.exe" 2>nul
del /q "%~dp0Start FileShare Server.bat" 2>nul
del /q "%~dp0README.txt" 2>nul
del /q "%~dp0users.db" 2>nul

:: Remove desktop shortcut if exists
del /q "%USERPROFILE%\\Desktop\\File Share Server.lnk" 2>nul

:: Remove start menu shortcut if exists
del /q "%APPDATA%\\Microsoft\\Windows\\Start Menu\\Programs\\File Share Server.lnk" 2>nul

echo.
echo ✅ File Share Server has been removed.
echo You can now delete this folder.
echo.
pause
'''
    
    return uninstaller_content

if __name__ == "__main__":
    print("Uninstaller script created for Windows builds")