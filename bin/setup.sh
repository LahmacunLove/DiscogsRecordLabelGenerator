#!/bin/bash

# DiscogsRecordLabelGenerator - Setup Script
# Interactive setup wizard with automatic venv handling

# Get the directory where this script is located and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

PROJECT_ROOT="$(get_project_root)"

display_banner "Setup"

# Check if venv exists, if not create it
VENV_PATH="$PROJECT_ROOT/venv"

if [ ! -d "$VENV_PATH" ]; then
    echo "📦 Creating virtual environment..."
    python3 -m venv "$VENV_PATH"

    if [ $? -ne 0 ]; then
        echo "❌ Failed to create virtual environment"
        exit 1
    fi

    echo "✅ Virtual environment created"
    echo ""
fi

# Activate venv
echo "🔄 Activating virtual environment..."
if ! activate_venv "$PROJECT_ROOT"; then
    exit 1
fi

echo "✅ Virtual environment activated"
echo ""

# Install/upgrade dependencies
echo "📦 Installing dependencies from requirements.txt..."
pip install --upgrade pip -q
pip install -r "$PROJECT_ROOT/requirements.txt"

if [ $? -ne 0 ]; then
    echo "❌ Failed to install dependencies"
    deactivate
    exit 1
fi

echo "✅ Dependencies installed"
echo ""

# Run the interactive setup script
echo "🚀 Starting interactive configuration..."
echo ""
python3 "$PROJECT_ROOT/scripts/setup.py"

EXIT_CODE=$?

# Deactivate venv
deactivate

if [ $EXIT_CODE -eq 0 ]; then
    echo ""
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo "  🎉 Setup completed successfully!"
    echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
    echo ""
    echo "Next steps:"
    echo "  • Run a test sync:     $PROJECT_ROOT/bin/sync.sh --dev"
    echo "  • Full sync:           $PROJECT_ROOT/bin/sync.sh"
    echo "  • Generate labels:     $PROJECT_ROOT/bin/generate-labels.sh"
    echo "  • Main application:    $PROJECT_ROOT/bin/main.sh"
    echo ""
fi

exit $EXIT_CODE
