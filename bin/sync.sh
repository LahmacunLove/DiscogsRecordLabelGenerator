#!/bin/bash

# DiscogsRecordLabelGenerator - Sync Script
# Syncs Discogs library and generates labels

# Get the directory where this script is located and load common functions
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

PROJECT_ROOT="$(get_project_root)"

display_banner "Sync"

# Run the sync script with all arguments
run_python_script "$PROJECT_ROOT" "sync.py" "$@"
