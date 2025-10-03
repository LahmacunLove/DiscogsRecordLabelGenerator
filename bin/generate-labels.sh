#!/bin/bash

# DiscogsRecordLabelGenerator - Generate Labels Script
# Generates printable vinyl labels from synced library

# Get the directory where this script is located and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

PROJECT_ROOT="$(get_project_root)"

display_banner "Generate Labels"

# Run the generate_labels script with all arguments
run_python_script "$PROJECT_ROOT" "generate_labels.py" "$@"
