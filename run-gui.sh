#!/bin/bash

# DiscogsRecordLabelGenerator - GUI Convenience Runner Script
# This script automatically activates the virtual environment and runs the GUI

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_PATH="$SCRIPT_DIR/venv"

# Check if virtual environment exists
if [ ! -d "$VENV_PATH" ]; then
    echo "❌ Virtual environment not found!"
    echo ""
    echo "Please create it first by running:"
    echo "  cd $SCRIPT_DIR"
    echo "  python3 -m venv venv"
    echo "  source venv/bin/activate"
    echo "  pip install -r requirements.txt"
    exit 1
fi

# Activate virtual environment
source "$VENV_PATH/bin/activate"

# Check if activation was successful
if [ -z "$VIRTUAL_ENV" ]; then
    echo "❌ Failed to activate virtual environment"
    exit 1
fi

echo "✅ Virtual environment activated: $VIRTUAL_ENV"
echo "🖥️  Starting GUI..."
echo ""

# Check if tkinter is available
python3 -c "import tkinter" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "❌ Error: tkinter is not installed!"
    echo ""
    echo "Tkinter is required for the GUI but cannot be installed via pip."
    echo "Please install it for your system:"
    echo ""
    echo "  Fedora/RHEL:    sudo dnf install python3-tkinter"
    echo "  Ubuntu/Debian:  sudo apt install python3-tk"
    echo "  Homebrew:       brew install python-tk@3.13"
    echo "                  or: brew reinstall python@3.13"
    echo ""
    deactivate
    exit 1
fi

# Run the GUI script
python3 "$SCRIPT_DIR/gui.py" "$@"

# Capture exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

exit $EXIT_CODE
