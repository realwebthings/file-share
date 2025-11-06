#!/bin/bash
# Stop all file server processes and deactivate virtual environments

echo "🛑 Stopping all file server processes..."

# Kill Python file server processes
pkill -f "python.*auth_server" 2>/dev/null && echo "✅ Stopped auth_server processes"
pkill -f "FileShareServer" 2>/dev/null && echo "✅ Stopped FileShareServer processes"
pkill -f "fileshare-server" 2>/dev/null && echo "✅ Stopped fileshare-server processes"

# Kill any Python processes on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null && echo "✅ Freed port 8000"

# Deactivate virtual environment if active
if [[ "$VIRTUAL_ENV" != "" ]]; then
    deactivate 2>/dev/null && echo "✅ Deactivated virtual environment"
fi

# Clear environment variables
unset VIRTUAL_ENV 2>/dev/null
unset PYTHONPATH 2>/dev/null

echo "🎯 All processes stopped and environments cleared"