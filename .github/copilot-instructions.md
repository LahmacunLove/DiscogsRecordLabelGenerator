# GitHub Copilot Instructions for DiscogsRecordLabelGenerator

This document provides guidelines for making changes to the DiscogsRecordLabelGenerator project.

## Core Principles

1. **Maintain Functionality**: All changes must preserve existing functionality
2. **Test Before Commit**: Always verify changes don't break the application
3. **Document Dependencies**: Keep dependency lists accurate and up-to-date
4. **Follow Python Best Practices**: Write clean, maintainable Python code
5. **Document Code Analysis**: When analyzing code behavior or location, document findings in Q&A format
6. **Commit Often with Component Prefixes**: Make frequent, focused commits with component-based prefixes to enable easy squashing later
7. **File Organization**: Do not add new files in the root directory unless specifically requested. Place all new files in corresponding component directories (e.g., `src/`, `docs/`, `bin/`, `tests/`)
8. **Keep README.md Focused**: The main README.md should be minimal and user-focused. It should help users understand what the tool does and how to get started. Everything else (detailed features, technical documentation, advanced usage) belongs in `docs/`
9. **AI-Generated Summaries**: Lengthy AI-generated summaries, changelogs, and implementation notes should be stored in `.assistant/` directory, not in user-facing documentation. If it's more than a few lines and primarily for AI reference, it belongs in `.assistant/`

## Pre-Commit Checklist

Before committing any changes, you MUST:

### 1. Run Integrity Test
```bash
python3 sync.py --dryrun
```
This command processes existing releases offline without making API calls or downloads. It verifies that:
- All imports resolve correctly
- Core functionality works
- No runtime errors occur
- File operations execute properly

### 2. Verify All Entry Points
If you modified core functionality, test all main entry points:
```bash
# Test sync tool
python3 sync.py --dryrun

# Test label generation
python3 generate_labels.py --max 1

# Test similarity analyzer (if applicable)
python3 similarity_analyzer.py
```

### 3. Check Dependencies
If you added new imports:
- Update `README.md` with any new Python packages
- Verify the package is available via `pip`
- Test installation: `pip install <package_name>`

## Code Style Guidelines

### Python Code
- Use Python 3.8+ features
- Follow PEP 8 style guidelines
- Use meaningful variable and function names
- Add docstrings for non-obvious functions
- Handle errors gracefully with try/except blocks

### Documentation
- **README.md**: Keep minimal and focused on first impressions
  - What the tool does (brief overview)
  - Quick start guide (installation, basic usage)
  - Links to detailed documentation in `docs/`
  - Avoid: lengthy feature lists, technical details, advanced usage
- **docs/**: All detailed documentation goes here
  - Feature explanations
  - Advanced usage guides
  - Technical implementation details
  - Troubleshooting guides
  - API references
- Use clear, concise language
- Provide examples for complex operations

### File Organization
- **Root Directory**: Keep clean - only essential files (README.md, requirements.txt, etc.)
- **README.md**: Keep focused and concise
  - Brief "What It Does" section
  - Quick Start guide
  - Basic commands overview
  - Links to `docs/` for everything else
  - Remove lengthy feature explanations → move to `docs/FEATURES.md` or specific feature docs
  - Remove detailed usage → move to `docs/USAGE.md`
  - Remove technical details → move to appropriate `docs/` files
- **New Files**: Place in appropriate component directories:
  - `src/` - Python source code modules
  - `docs/` - Documentation files (all detailed docs belong here)
  - `bin/` - Shell scripts and executables
  - `tests/` - Test files and test utilities
  - `scripts/` - Utility scripts (if exists)
- **Exception**: Only add root-level files when specifically requested by the user

### Code Analysis and Q&A Documentation
When a user asks about code behavior or where functionality is implemented:
1. Perform thorough analysis of the codebase
2. Provide a clear, detailed answer to the user
3. Document the Q&A in `docs/QA.md` for future reference (keep entries concise)
4. Include:
   - The question asked
   - File paths and line numbers where relevant code exists
   - Brief explanation of how the functionality works
   - Any relevant context or related features

### Project History Documentation
- **User-Facing Docs** (`docs/`): Keep concise and focused on what users need to know
- **Project History** (`.assistant/`): Store detailed implementation notes, comprehensive changelogs, and technical evolution
  - `CHANGES_*.md` - Detailed feature implementation histories
  - `*_DETAILED.md` - Technical deep-dives with code references
  - `IMPLEMENTATION_*.md` - Architecture explanations and design decisions
- **Version Control**: `.assistant/` is committed to git as it documents project evolution
- **Rule of Thumb**: If it explains "how we built it" rather than "how to use it", put it in `.assistant/`
- **Purpose**: Creates a knowledge base showing how the project evolved, helping future developers understand context and decisions

## Common Tasks

### Adding a New Python Dependency
1. Add the import to your code
2. Test locally: `pip install <package>`
3. Run integrity test: `python3 sync.py --dryrun`
4. Update both pip install commands in README.md:
   - Under "Requirements > Python Libraries"
   - Under "Setup > 1. Install Python Dependencies"
5. Commit with descriptive message

### Modifying Configuration
1. Update `src/config.py` if needed
2. Update configuration examples in README.md
3. Test with both sync.py and manual configuration methods
4. Verify backward compatibility with existing config files

### Changing File Structure
1. Update "File Structure" section in README.md
2. Ensure existing releases still work (test with `--dryrun`)
3. Consider migration path for users with existing data

### Updating LaTeX Templates
1. Test PDF generation: `python3 generate_labels.py --max 1`
2. Verify special characters render correctly
3. Check Unicode support (XeLaTeX requirement)

## Testing Scenarios

### Minimal Testing (Quick Check)
```bash
python3 sync.py --dryrun
```

### Standard Testing (Recommended)
```bash
# Test with limited scope
python3 sync.py --dev

# Generate labels from test data
python3 generate_labels.py --max 5
```

### Full Testing (Before Major Changes)
```bash
# Test all modes
python3 sync.py --dryrun
python3 sync.py --dev
python3 sync.py --dev --labels
python3 generate_labels.py --max 10
```

## Error Handling

When encountering errors:
1. Check the error message and stack trace
2. Verify all dependencies are installed
3. Confirm external tools (ffmpeg, xelatex, gnuplot) are in PATH
4. Test with `--dryrun` to isolate the issue
5. Add error to "Troubleshooting" section in README.md if it's common

## Git Commit Messages

### Commit Convention

**Commit often** with focused, atomic changes. Prefix each commit subject with a component name to enable easy identification and squashing of related commits later.

**Important:** Focus on describing the **intent and impact** for reviewers, not specific code-level changes (e.g., avoid "Modified line 42 in foo.py"). Describe *what* and *why*, not *where*.

**Format:**
```
component: Short summary (50 chars or less including prefix)

- Describe the intent or user-facing impact
- Explain why the change was needed
- Note about testing performed (if applicable)
```

**Common Component Prefixes:**
- `audio:` - Audio analysis, waveform generation, Essentia integration
- `sync:` - Sync tool, data processing, release mirroring
- `labels:` - Label generation, LaTeX templates, PDF output
- `config:` - Configuration files, environment setup
- `api:` - Discogs API integration, external API calls
- `docs:` - Documentation updates, README changes
- `tests:` - Test files, test utilities, CI
- `deps:` - Dependency updates, requirements changes
- `fix:` - Bug fixes (can be combined with component, e.g., `audio/fix:`)
- `refactor:` - Code refactoring without functional changes
- `build:` - Build scripts, deployment, packaging

**Examples:**
```
audio: Add Opus-to-WAV conversion for Essentia

- Enable analysis of Opus-encoded audio files
- Essentia requires WAV format, so convert temporarily
- Tested with --dryrun
```

```
sync: Enable FFmpeg usage in track analysis

- Allow decoding of modern audio codecs during sync
- Fixes failure to analyze Opus and other formats
```

```
docs: Document waveform generation lifecycle

- Clarify when and where waveforms are created
- Help users troubleshoot missing waveform files
```

```
labels: Fix Unicode rendering in track titles

- Correctly display international characters in labels
- Resolves garbled text for non-ASCII titles
- Tested with --max 5
```

**Squashing Related Commits:**

When you have multiple related commits, they can be easily squashed during PR or rebase:
```bash
# Example: Squashing multiple audio-related commits
git rebase -i HEAD~5

# In the editor, you'll see:
pick abc1234 audio: Add Opus detection
pick def5678 audio: Implement WAV conversion
pick ghi9012 audio: Add cleanup for temp files
pick jkl3456 docs: Update audio analysis docs

# Change to:
pick abc1234 audio: Add Opus detection
squash def5678 audio: Implement WAV conversion
squash ghi9012 audio: Add cleanup for temp files
pick jkl3456 docs: Update audio analysis docs
```

This convention makes it easy to:
- Find all commits related to a specific component
- Review changes by functional area
- Squash related work into cohesive commits
- Generate meaningful changelogs

## Pull Request Guidelines

1. Create a descriptive branch name (e.g., `feature/add-spotify-integration`, `fix/unicode-labels`)
2. Test thoroughly before pushing
3. Update README.md with any user-facing changes
4. Include "Tested with `python3 sync.py --dryrun`" in PR description
5. List all modified functionality
6. Note any breaking changes

## Troubleshooting Development Issues

### Import Errors
```bash
# Verify Python path
python3 -c "import sys; print(sys.path)"

# Check if package is installed
pip list | grep <package-name>
```

### Configuration Issues
```bash
# Check config file location
ls -la ~/.config/discogsDBLabelGen/

# Validate JSON syntax
python3 -m json.tool ~/.config/discogsDBLabelGen/discogs.env
```

### Runtime Issues
```bash
# Run with verbose logging
python3 sync.py --dryrun --verbose  # (if verbose flag exists)

# Check system dependencies
which ffmpeg
which xelatex
which gnuplot
```

## Resources

- [Discogs API Documentation](https://www.discogs.com/developers/)
- [Essentia Documentation](https://essentia.upf.edu/documentation/)
- [LaTeX/XeLaTeX Documentation](https://www.latex-project.org/help/documentation/)
- [Project README](../README.md)

---

**Remember**: Always run `python3 sync.py --dryrun` before committing changes!