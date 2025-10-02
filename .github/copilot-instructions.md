# GitHub Copilot Instructions for DiscogsRecordLabelGenerator

This document provides guidelines for making changes to the DiscogsRecordLabelGenerator project.

## Core Principles

1. **Maintain Functionality**: All changes must preserve existing functionality
2. **Test Before Commit**: Always verify changes don't break the application
3. **Document Dependencies**: Keep dependency lists accurate and up-to-date
4. **Follow Python Best Practices**: Write clean, maintainable Python code

## Pre-Commit Checklist

Before committing any changes, you MUST:

### 1. Run Integrity Test
```bash
python3 main.py --dryrun
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
- Keep README.md up-to-date with any new features or requirements
- Use clear, concise language
- Provide examples for complex operations
- Update troubleshooting section if you encounter common issues

## Common Tasks

### Adding a New Python Dependency
1. Add the import to your code
2. Test locally: `pip install <package>`
3. Run integrity test: `python3 main.py --dryrun`
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
python3 main.py --dryrun
```

### Standard Testing (Recommended)
```bash
# Test with limited scope
python3 main.py --dev

# Generate labels from test data
python3 generate_labels.py --max 5
```

### Full Testing (Before Major Changes)
```bash
# Test all modes
python3 main.py --dryrun
python3 main.py --dev
python3 sync.py --dryrun
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

Follow this format:
```
<Short summary (50 chars or less)>

- Bullet point describing change 1
- Bullet point describing change 2
- Note about testing performed
```

Example:
```
Add support for multi-disc releases

- Modified track parser to handle disc numbers
- Updated LaTeX template for disc grouping
- Tested with --dryrun and --dev modes
```

## Pull Request Guidelines

1. Create a descriptive branch name (e.g., `feature/add-spotify-integration`, `fix/unicode-labels`)
2. Test thoroughly before pushing
3. Update README.md with any user-facing changes
4. Include "Tested with `python3 main.py --dryrun`" in PR description
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
python3 main.py --dryrun --verbose  # (if verbose flag exists)

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

**Remember**: Always run `python3 main.py --dryrun` before committing changes!