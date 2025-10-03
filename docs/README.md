# Documentation

This directory contains comprehensive documentation for DiscogsRecordLabelGenerator.

## User Documentation

Essential guides for using the application:

- **[INSTALLATION.md](INSTALLATION.md)** - Platform-specific installation instructions
- **[CONFIGURATION.md](CONFIGURATION.md)** - Configuration guide and setup options
- **[USAGE.md](USAGE.md)** - Detailed command reference and usage examples
- **[TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Common issues and solutions
- **[FILE_STRUCTURE.md](FILE_STRUCTURE.md)** - Project and output directory structure

## Quick Links

- **[Main README](../README.md)** - Quick start and project overview
- **[Requirements](../requirements.txt)** - Python dependencies
- **[Shell Scripts](../bin/)** - Wrapper scripts for easy execution

## Developer Documentation

Technical documentation and development notes:

- **[DEPENDENCY_NOTES.md](DEPENDENCY_NOTES.md)** - Dependency resolution and migration notes
- **[PR_SYNC_CLI.md](PR_SYNC_CLI.md)** - CLI sync tool PR documentation
- **[Copilot Instructions](../.github/copilot-instructions.md)** - Development guidelines and testing workflows

## Assets

Sample outputs and images:

- **[assets/sample.png](assets/sample.png)** - Primary label example
- **[assets/sample2.png](assets/sample2.png)** - Secondary label example

## Documentation Overview

### For New Users

1. Start with [INSTALLATION.md](INSTALLATION.md) to set up your system
2. Follow [CONFIGURATION.md](CONFIGURATION.md) to configure the application
3. Use [USAGE.md](USAGE.md) to learn the commands
4. Refer to [TROUBLESHOOTING.md](TROUBLESHOOTING.md) if you encounter issues

### For Existing Users

- **Upgrading?** Check [DEPENDENCY_NOTES.md](DEPENDENCY_NOTES.md) for migration info
- **Commands?** See [USAGE.md](USAGE.md) for full reference
- **Errors?** Check [TROUBLESHOOTING.md](TROUBLESHOOTING.md)
- **File locations?** See [FILE_STRUCTURE.md](FILE_STRUCTURE.md)

### For Developers

- Review [Copilot Instructions](../.github/copilot-instructions.md) before contributing
- Check [DEPENDENCY_NOTES.md](DEPENDENCY_NOTES.md) for dependency context
- See [PR_SYNC_CLI.md](PR_SYNC_CLI.md) for CLI migration details

## Contributing

When contributing to documentation:

1. Keep user docs (INSTALLATION, USAGE, etc.) beginner-friendly
2. Put technical details in developer docs (DEPENDENCY_NOTES, etc.)
3. Update this README when adding new documentation
4. Use clear examples and avoid jargon where possible
5. Test all commands before documenting them

## Structure

```
docs/
├── README.md                 # This file - documentation index
├── INSTALLATION.md           # Installation guide (all platforms)
├── CONFIGURATION.md          # Configuration reference
├── USAGE.md                  # Complete usage guide
├── TROUBLESHOOTING.md        # Common problems and solutions
├── FILE_STRUCTURE.md         # Directory structure documentation
├── DEPENDENCY_NOTES.md       # Technical dependency notes
├── PR_SYNC_CLI.md           # CLI tool PR documentation
└── assets/                   # Images and samples
    ├── sample.png
    ├── sample2.png
    ├── sample.jpg
    └── output.jpg
```
