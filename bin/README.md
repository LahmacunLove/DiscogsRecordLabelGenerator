# Shell Scripts - DiscogsRecordLabelGenerator

This directory contains shell scripts that provide a clean interface to the Python application with automatic virtual environment handling.

## Quick Start

### First Time Setup

```bash
# Run setup to create venv, install dependencies, and configure
./bin/setup.sh
```

This will:
1. Create a Python virtual environment (`venv/`)
2. Install all required dependencies
3. Guide you through interactive configuration
4. Test your setup

### Daily Usage

```bash
# Sync your Discogs collection (dev mode - 10 releases)
./bin/sync.sh --dev

# Full sync
./bin/sync.sh

# Generate labels only
./bin/sync.sh --labels-only

# Generate labels from existing data
./bin/generate-labels.sh --max 10
```

## Available Scripts

### `setup.sh`
**Interactive setup wizard**

Creates virtual environment, installs dependencies, and guides you through configuration.

```bash
./bin/setup.sh
```

No arguments needed - it's fully interactive!

---

### `sync.sh`
**Sync and label generation CLI tool**

Modern CLI tool for syncing your Discogs library and generating labels.

```bash
# Show all options
./bin/sync.sh --help

# Configure and save settings
./bin/sync.sh --token YOUR_TOKEN --library ~/Music/Discogs --configure

# Development mode (10 releases)
./bin/sync.sh --dev

# Full sync with label generation
./bin/sync.sh

# Dry run (process existing releases only)
./bin/sync.sh --dryrun

# Generate labels only
./bin/sync.sh --labels-only --max-labels 10

# Generate specific release
./bin/sync.sh --labels-only --release 123456
```

**Key Options:**
- `--dev` - Development mode (limited releases)
- `--dryrun` - Process existing data without API calls
- `--labels` - Generate labels after sync
- `--labels-only` - Skip sync, generate labels only
- `--max N` - Limit to N releases
- `--configure` - Save configuration

---

### `generate-labels.sh`
**Label generation from existing data**

Generate printable vinyl labels without syncing.

```bash
# Generate all labels
./bin/generate-labels.sh

# Development mode (10 labels)
./bin/generate-labels.sh --dev

# Limit to N labels
./bin/generate-labels.sh --max 15

# Specific release
./bin/generate-labels.sh --release-id 123456

# Since date
./bin/generate-labels.sh --since 2024-01-01

# Custom output directory
./bin/generate-labels.sh --output /tmp/labels
```

---

## How It Works

All shell scripts use the common helper (`_common.sh`) which:

1. **Locates project root** - Works from any directory
2. **Checks virtual environment** - Ensures venv exists and is configured
3. **Activates venv automatically** - No manual activation needed
4. **Runs Python script** - Executes the correct script with arguments
5. **Cleans up** - Deactivates venv when done

### Behind the Scenes

```
bin/sync.sh --dev
    ↓
_common.sh (check & activate venv)
    ↓
scripts/sync.py --dev
    ↓
src/ (library code)
```

## Directory Structure

```
DiscogsRecordLabelGenerator/
├── bin/                    # Shell scripts (you are here)
│   ├── setup.sh           # Setup wizard
│   ├── sync.sh            # Sync tool
│   ├── generate-labels.sh # Label generator
│   └── _common.sh         # Shared functions
├── scripts/               # Python entry points
│   ├── setup.py
│   ├── sync.py
│   └── generate_labels.py
├── src/                   # Library code
│   ├── config.py
│   ├── mirror.py
│   ├── logger.py
│   └── ...
└── venv/                  # Virtual environment (created by setup)
```

## Benefits

✅ **No manual venv activation** - Scripts handle it automatically  
✅ **Clear error messages** - Helpful guidance when things go wrong  
✅ **Consistent interface** - All scripts work the same way  
✅ **Works from anywhere** - Scripts find project root automatically  
✅ **Clean separation** - Shell wrappers vs Python logic

## Troubleshooting

### "Virtual environment not found"

```bash
# Run setup first
./bin/setup.sh
```

### "Dependencies not installed"

```bash
cd /path/to/project
source venv/bin/activate
pip install -r requirements.txt
```

Or just run `setup.sh` which does this for you.

### "Script not found"

Make sure you're running from the project directory or use full paths:

```bash
# From anywhere
/path/to/DiscogsRecordLabelGenerator/bin/sync.sh --help
```

### Permission denied

```bash
chmod +x bin/*.sh
```

## Migration from Old Structure

**Before:**
```bash
source venv/bin/activate
python3 sync.py --dev
```

**After:**
```bash
./bin/sync.sh --dev
```

Much simpler! No manual venv activation needed.

## Adding New Scripts

To add a new wrapper script:

1. Create script in `bin/` directory
2. Source `_common.sh`
3. Call `run_python_script`

Example:

```bash
#!/bin/bash
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
source "$SCRIPT_DIR/_common.sh"

PROJECT_ROOT="$(get_project_root)"
display_banner "My New Tool"
run_python_script "$PROJECT_ROOT" "my_script.py" "$@"
```

That's it! The common library handles all the venv management.