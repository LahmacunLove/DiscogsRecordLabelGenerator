# File Organization Guidelines

This document describes the file organization structure for the DiscogsRecordLabelGenerator project.

## Directory Structure

```
DiscogsRecordLabelGenerator/
├── .github/              # GitHub configuration (workflows, Copilot instructions)
├── bin/                  # Shell scripts and executables
├── docs/                 # Documentation files
├── scripts/              # Utility scripts (legacy/miscellaneous)
├── src/                  # Python source code modules
├── tests/                # Test files and test utilities
├── venv/                 # Virtual environment (not committed)
├── .gitignore           # Git ignore patterns
├── LICENSE              # Project license
├── README.md            # Main project documentation
└── requirements.txt     # Python dependencies
```

## Component Directories

### `/src/` - Source Code

All Python modules and core application code.

**Examples:**
- `mirror.py` - Discogs library mirroring
- `thread_monitor.py` - Multi-threaded CLI visualization
- `config.py` - Configuration management
- `logger.py` - Logging system
- `latex_generator.py` - Label generation
- `youtube_handler.py` - YouTube integration

### `/docs/` - Documentation

All markdown documentation files except the main README.

**Examples:**
- `INSTALLATION.md` - Installation instructions
- `USAGE.md` - Usage guide and command reference
- `CONFIGURATION.md` - Configuration details
- `TROUBLESHOOTING.md` - Common issues and solutions
- `THREAD_VISUALIZATION.md` - Feature-specific documentation
- `QA.md` - Code Q&A knowledge base
- `CHANGES.md` - Changelogs and feature updates
- `FILE_STRUCTURE.md` - Output directory structure

### `/bin/` - Shell Scripts

Executable wrapper scripts for easy command access.

**Examples:**
- `setup.sh` - Interactive configuration wizard
- `sync.sh` - Sync and label generation wrapper
- `generate-labels.sh` - Label generation wrapper

### `/tests/` - Test Files

Test scripts, unit tests, and testing utilities.

**Examples:**
- `test_monitor.py` - ThreadMonitor visualization demo
- (Future: unit tests, integration tests, benchmarks)

### `/.github/` - GitHub Configuration

GitHub-specific configuration files.

**Examples:**
- `copilot-instructions.md` - Development guidelines for AI assistants
- `workflows/` - CI/CD workflows (if present)

### `/scripts/` - Utility Scripts

Legacy or miscellaneous utility scripts that don't fit other categories.

## Root Directory

The root directory should remain **clean and minimal**. Only essential project-level files:

**Allowed root files:**
- `README.md` - Main project documentation
- `requirements.txt` - Python dependencies
- `LICENSE` - Project license
- `.gitignore` - Git ignore patterns
- `.env` - Environment variables (not committed)
- `setup.py` / `pyproject.toml` - Package configuration (if needed)

## File Placement Rules

### ✅ DO

- **Place Python modules in `src/`**
  ```
  ✅ src/new_feature.py
  ❌ new_feature.py
  ```

- **Place documentation in `docs/`**
  ```
  ✅ docs/NEW_FEATURE.md
  ❌ NEW_FEATURE.md
  ```

- **Place test files in `tests/`**
  ```
  ✅ tests/test_new_feature.py
  ❌ test_new_feature.py
  ```

- **Place shell scripts in `bin/`**
  ```
  ✅ bin/new-command.sh
  ❌ new-command.sh
  ```

### ❌ DON'T

- **Don't create new root-level files** unless specifically requested
- **Don't create files outside the standard directories** without justification
- **Don't mix file types** (e.g., Python code in `docs/`, documentation in `src/`)

## Special Cases

### Configuration Files

Configuration files can be in the root if they're standard project files:
- `requirements.txt` - Python dependencies
- `setup.py` / `pyproject.toml` - Package setup
- `.env` - Environment variables (gitignored)

### Generated Files

Runtime-generated files should go in appropriate output directories:
- Release data: `~/Music/Discogs/` (configurable)
- Label PDFs: `output_labels/` (configurable)
- Log files: `~/.config/discogsDBLabelGen/logs/`

## Migration Notes

### Recent Reorganization (January 2025)

Files moved from root to proper directories:
- `test_monitor.py` → `tests/test_monitor.py`
- `CHANGES.md` → `docs/CHANGES.md`

All documentation updated to reflect new paths.

## Benefits of This Structure

1. **Clarity**: Easy to find files by type/purpose
2. **Scalability**: Can add many files without cluttering root
3. **Standards**: Follows common Python project conventions
4. **Maintainability**: Clear separation of concerns
5. **Professionalism**: Clean, organized project structure

## Import Path Considerations

When files are organized in directories, adjust imports accordingly:

**From root scripts:**
```python
# If running from root directory
from src.thread_monitor import ThreadMonitor
```

**From test files:**
```python
# If running from tests/ directory
import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
from thread_monitor import ThreadMonitor
```

**From src/ modules:**
```python
# Other src modules are in the same directory
from logger import logger
from config import load_config
```

## Copilot/AI Assistant Guidelines

When creating new files, AI assistants should:

1. **Default to component directories** - Never create root-level files unless explicitly requested
2. **Ask for clarification** if unsure where a file belongs
3. **Update documentation** when files are added or moved
4. **Maintain consistency** with existing structure

See `.github/copilot-instructions.md` for complete guidelines.

## References

- [Project README](../README.md) - Main documentation
- [Copilot Instructions](../.github/copilot-instructions.md) - Development guidelines
- [Tests README](../tests/README.md) - Testing documentation

---

**Last Updated:** October 2025
**Status:** ✅ Active guideline