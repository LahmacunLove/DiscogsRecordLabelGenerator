#!/bin/bash

# DiscogsRecordLabelGenerator - Convenience Runner Script
# This script automatically activates the virtual environment and runs the application

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
echo ""

# Run the Python script with all passed arguments
python3 "$SCRIPT_DIR/main.py" "$@"

# Capture exit code
EXIT_CODE=$?

# Deactivate virtual environment
deactivate

exit $EXIT_CODE
