# Documentation

This directory contains project documentation, development notes, and assets.

## Contents

### Documentation Files

- **[DEPENDENCY_NOTES.md](DEPENDENCY_NOTES.md)** - Detailed explanation of the `six` dependency issue and how it was resolved by upgrading to `python3-discogs-client`
- **[PR_SYNC_CLI.md](PR_SYNC_CLI.md)** - Pull request documentation for the CLI sync tool that replaced the GUI

### Assets

The `assets/` directory contains images and sample outputs:

- **sample.png** - Example of generated vinyl label (shown in main README)
- **sample2.png** - Another label example (shown in main README)
- **sample.jpg** - Additional label sample
- **output.jpg** - Sample output artifact

## For Users

If you're looking for user-facing documentation, please see:

- **[Main README](../README.md)** - Setup instructions, usage guide, and feature overview
- **[bin/README.md](../bin/README.md)** - Shell scripts documentation and usage examples
- **[Copilot Instructions](../.github/copilot-instructions.md)** - Development guidelines and testing workflows

## For Developers

The documentation in this directory is primarily for:

- Understanding the technical decisions made during development
- Reviewing pull request rationale and migration guides
- Learning about dependency management and project history
- Contributing to the project with context about past changes

## Structure

```
docs/
├── README.md                 # This file
├── DEPENDENCY_NOTES.md       # Technical notes on dependency resolution
├── PR_SYNC_CLI.md           # CLI tool PR documentation
└── assets/                   # Images, screenshots, and samples
    ├── sample.png
    ├── sample2.png
    ├── sample.jpg
    └── output.jpg
```
