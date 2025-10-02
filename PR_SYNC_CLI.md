# PR: Replace GUI with CLI Sync Tool

## Overview

This PR removes the tkinter-based GUI (`gui.py`) and replaces it with a comprehensive command-line tool (`sync.py`) that provides all the same functionality through CLI options with sensible defaults.

## Motivation

- **Reduce Dependencies**: Eliminates tkinter dependency, which is a system package that can be problematic across different Python installations (Homebrew, system Python, venv, etc.)
- **Better CI/CD**: CLI-only tools are easier to automate and integrate into scripts
- **Simpler Installation**: One less dependency for users to troubleshoot
- **More Flexible**: CLI arguments are easier to script and chain with other tools
- **Maintains Accessibility**: Users who preferred the GUI can use the new `sync.py` with clear help text and examples

## Changes

### Added
- **`sync.py`**: New CLI tool with comprehensive options for:
  - Configuration management (`--token`, `--library`, `--configure`)
  - Sync modes (`--sync`, `--dev`, `--max`, `--dryrun`)
  - Label generation (`--labels`, `--labels-only`, `--output`, `--max-labels`, `--release`, `--since`)
  - Built-in help with examples (`--help`)
  - Sensible defaults (syncs and generates labels by default)

### Removed
- **`gui.py`**: Tkinter-based GUI application (474 lines)
- **`run-gui.sh`**: Convenience script for launching GUI
- **Tkinter references**: Removed from README, setup.py, and copilot instructions

### Modified
- **`README.md`**: 
  - Replaced GUI usage with `sync.py` examples
  - Removed tkinter installation instructions
  - Updated quick start guide
  - Added comprehensive `sync.py` usage examples
- **`setup.py`**: Updated next steps to reference `sync.py` instead of GUI
- **`.github/copilot-instructions.md`**: Updated testing instructions to use `sync.py`

## Usage Examples

### Basic Usage
```bash
# Full sync with label generation (default behavior)
python3 sync.py

# Development mode (limited releases)
python3 sync.py --dev

# Dry run (process existing releases only)
python3 sync.py --dryrun
```

### Configuration
```bash
# Save configuration for future use
python3 sync.py --token YOUR_TOKEN --library ~/Music/Discogs --configure

# Then run without specifying token/library
python3 sync.py --dev
```

### Label Generation
```bash
# Generate labels only (no sync)
python3 sync.py --labels-only

# Generate specific release
python3 sync.py --labels-only --release 123456

# Generate labels since date
python3 sync.py --labels-only --since 2024-01-01

# Limit number of labels
python3 sync.py --labels-only --max-labels 10
```

## Testing

Tested with:
```bash
# Verify help text
python3 sync.py --help

# Test dry run mode
python3 sync.py --dryrun

# Test label generation only
python3 sync.py --labels-only --max-labels 1
```

All tests passed successfully.

## Migration Guide

### For GUI Users

**Before (GUI):**
```bash
./run-gui.sh
# Then click buttons in GUI
```

**After (CLI):**
```bash
# Configure once
python3 sync.py --token YOUR_TOKEN --library ~/Music/Discogs --configure

# Run sync
python3 sync.py --dev  # or just: python3 sync.py
```

### For Script Users

The new `sync.py` is actually better for scripting:

```bash
# Old way (GUI couldn't be scripted)
python3 main.py --dev

# New way (more options)
python3 sync.py --dev --labels
python3 sync.py --labels-only --since 2024-01-01
python3 sync.py --dryrun
```

## Benefits

1. **Simpler Dependencies**: No more tkinter troubleshooting
2. **Better for Automation**: Can be easily scripted and integrated into workflows
3. **More Maintainable**: Less code to maintain (removed 474 lines)
4. **Better UX**: Clear help text and examples built into the tool
5. **More Flexible**: Easier to add new features as CLI options

## Backward Compatibility

- **`main.py`**: Still works exactly as before
- **`setup.py`**: Still works for interactive configuration
- **Configuration**: Same config file format and location
- **`run.sh`**: Still works as before

Users who relied on `gui.py` or `run-gui.sh` should switch to `sync.py`, which provides equivalent functionality with better scriptability.

## Related Issues

This PR is part of a series of improvements to make the project more accessible and easier to maintain.

## Checklist

- [x] Code follows project style guidelines
- [x] Tested with `--dryrun` flag
- [x] Updated README.md
- [x] Updated copilot instructions
- [x] Removed deprecated files (gui.py, run-gui.sh)
- [x] All tests pass
- [x] Help text is clear and includes examples
- [x] Migration path documented