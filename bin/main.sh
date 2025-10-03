#!/bin/bash

# DiscogsRecordLabelGenerator - Main Script
# Runs the main application with all sync and analysis features

# Get the directory where this script is located and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

PROJECT_ROOT="$(get_project_root)"

display_banner "Main Application"

# Run the main script with all arguments
run_python_script "$PROJECT_ROOT" "main.py" "$@"
