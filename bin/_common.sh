#!/bin/bash

# Common functions for DiscogsRecordLabelGenerator shell scripts
# This file should be sourced by other scripts, not executed directly

# Get the project root directory (parent of bin/)
get_project_root() {
    echo "$(cd "$(dirname "${BASH_SOURCE[1]}")" && cd .. && pwd)"
}

# Check if virtual environment exists and is set up
check_venv() {
    local PROJECT_ROOT="$1"
    local VENV_PATH="$PROJECT_ROOT/venv"

    if [ ! -d "$VENV_PATH" ]; then
        echo "❌ Virtual environment not found at: $VENV_PATH"
        echo ""
        echo "Please create it first by running:"
        echo "  cd $PROJECT_ROOT"
        echo "  python3 -m venv venv"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        echo ""
        echo "Or use the setup script:"
        echo "  $PROJECT_ROOT/bin/setup.sh"
        return 1
    fi

    # Check if requirements are installed
    if [ ! -f "$VENV_PATH/lib/python"*/site-packages/discogs_client/__init__.py ]; then
        echo "⚠️  Virtual environment exists but dependencies may not be installed"
        echo ""
        echo "Please install dependencies:"
        echo "  cd $PROJECT_ROOT"
        echo "  source venv/bin/activate"
        echo "  pip install -r requirements.txt"
        echo ""
        return 1
    fi

    return 0
}

# Activate virtual environment
activate_venv() {
    local PROJECT_ROOT="$1"
    local VENV_PATH="$PROJECT_ROOT/venv"

    # Source the activation script
    source "$VENV_PATH/bin/activate"

    # Verify activation was successful
    if [ -z "$VIRTUAL_ENV" ]; then
        echo "❌ Failed to activate virtual environment"
        return 1
    fi

    return 0
}

# Run a Python script from the scripts/ directory with venv activated
run_python_script() {
    local PROJECT_ROOT="$1"
    local SCRIPT_NAME="$2"
    shift 2  # Remove first two arguments, leaving only script arguments

    # Check and activate venv
    if ! check_venv "$PROJECT_ROOT"; then
        exit 1
    fi

    if ! activate_venv "$PROJECT_ROOT"; then
        exit 1
    fi

    local SCRIPT_PATH="$PROJECT_ROOT/scripts/$SCRIPT_NAME"

    # Verify script exists
    if [ ! -f "$SCRIPT_PATH" ]; then
        echo "❌ Script not found: $SCRIPT_PATH"
        deactivate
        exit 1
    fi

    # Run the script with all remaining arguments
    python3 "$SCRIPT_PATH" "$@"

    # Capture exit code
    local EXIT_CODE=$?

    # Deactivate virtual environment
    deactivate

    return $EXIT_CODE
}

# Display a banner for the script
display_banner() {
    local SCRIPT_NAME="$1"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  DiscogsRecordLabelGenerator - $SCRIPT_NAME"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
}
