# Usage Guide

This guide covers all commands and options available in DiscogsRecordLabelGenerator.

## Overview

The project provides several tools:

- **`sync.sh`**: Sync Discogs collection and generate labels (all-in-one)
- **`main.sh`**: Process existing releases without syncing
- **`generate-labels.sh`**: Generate labels from existing data
- **`setup.sh`**: Interactive configuration wizard

All shell scripts in `bin/` automatically manage the virtual environment.

## Multi-Threaded Processing

### Live CLI Visualization

When running sync operations in console mode, you'll see a real-time multi-threaded display showing:

- **Individual Worker Panels**: Each worker thread gets its own panel showing:
  - Current release being processed
  - Processing step (e.g., "Downloading audio", "Analyzing audio")
  - Progress percentage with visual bar
  - Files generated so far
  - Elapsed time for current task
  - Status indicator (⚪ idle, 🟢 working, ✅ completed, 🔴 error)

- **Overall Progress**: Header shows total progress, error count, worker count, and elapsed time

- **Live Updates**: Display refreshes automatically as workers progress

### Graceful Shutdown with Ctrl+C

Press **Ctrl+C** at any time to safely stop all worker threads:

1. Shutdown signal is sent to all workers
2. Workers complete their current step and stop gracefully
3. No partial or corrupted files are left behind
4. Summary shows completed vs. total releases
5. Any errors are reported

**Example:**
```
⚠️ Ctrl+C detected - shutting down workers gracefully...
⚠️ SHUTDOWN IN PROGRESS...

⚠️ Shutdown completed
Completed: 15/50
```

### Testing the Visualization

Run the test script to see a demo with simulated releases:

```bash
python3 tests/test_monitor.py --releases 20 --workers 4
```

This simulates the mirroring process and lets you test the Ctrl+C shutdown behavior.

## sync.sh - Sync and Generate Labels

The primary tool for syncing your Discogs collection and generating labels.

### Basic Usage

```bash
# Development mode (first 10 releases)
./bin/sync.sh --dev

# Full collection sync
./bin/sync.sh

# Dry run (process existing releases only, no API calls)
./bin/sync.sh --dryrun

# Sync with label generation
./bin/sync.sh --labels
```

### Common Options

```bash
--dev                 # Development mode (limit to 10 releases)
--dryrun             # Process existing releases without API calls
--labels             # Generate labels after sync
--labels-only        # Generate labels only, no sync
--max N              # Limit to N releases
--release ID         # Process specific release by Discogs ID
--since YYYY-MM-DD   # Process releases added/modified since date
--max-labels N       # Limit label generation to N releases
```

### Configuration Options

```bash
--token TOKEN        # Discogs API token
--library PATH       # Library directory path
--configure          # Save configuration for future use
```

### Examples

```bash
# Test with 5 releases and generate labels
./bin/sync.sh --dev --labels

# Sync specific release
./bin/sync.sh --release 123456 --labels

# Generate labels for releases added in 2024
./bin/sync.sh --labels-only --since 2024-01-01

# Generate up to 20 labels
./bin/sync.sh --labels-only --max-labels 20

# One-time sync with custom token
./bin/sync.sh --token YOUR_TOKEN --library ~/Music/Discogs --dev
```

### Help

```bash
./bin/sync.sh --help
```

## main.sh - Process Existing Releases

Process releases already downloaded without syncing new data.

### Basic Usage

```bash
# Process all existing releases
./bin/main.sh

# Development mode (first 10 releases)
./bin/main.sh --dev

# Dry run (verify existing data)
./bin/main.sh --dryrun
```

### Options

```bash
--dev                      # Development mode (limit to 10 releases)
--dryrun                  # Process without downloads or API calls
--download-only           # Download audio without analysis
--max N                   # Limit to N releases
--regenerate-labels       # Regenerate labels from existing data
--regenerate-waveforms    # Regenerate waveform images
```

### Examples

```bash
# Download audio for 25 releases without analysis
./bin/main.sh --download-only --max 25

# Regenerate all labels
./bin/main.sh --regenerate-labels

# Regenerate waveforms for first 50 releases
./bin/main.sh --regenerate-waveforms --max 50
```

### Help

```bash
./bin/main.sh --help
```

## generate-labels.sh - Generate Labels Only

Generate PDF labels from processed releases.

### Basic Usage

```bash
# Generate labels for all releases
./bin/generate-labels.sh

# Generate labels for first 10 releases
./bin/generate-labels.sh --max 10

# Custom output directory
./bin/generate-labels.sh --output ~/MyLabels
```

### Options

```bash
--max N           # Limit to N releases
--output DIR      # Custom output directory
```

### Examples

```bash
# Generate 5 test labels
./bin/generate-labels.sh --max 5

# Generate all labels to custom location
./bin/generate-labels.sh --output /mnt/backup/labels
```

### Help

```bash
./bin/generate-labels.sh --help
```

## setup.sh - Interactive Configuration

Interactive wizard to configure the application.

### Usage

```bash
./bin/setup.sh
```

### What It Does

1. Prompts for your Discogs API token
2. Helps you choose a library path
3. Creates the directory if it doesn't exist
4. Saves configuration to `~/.config/discogsDBLabelGen/discogs.env`
5. Tests the configuration

### Getting Your Discogs Token

1. Go to [Discogs Developer Settings](https://www.discogs.com/settings/developers)
2. Click "Generate new token"
3. Copy the token
4. Paste it when prompted by `setup.sh`

## Manual Python Execution

If you prefer to run Python scripts directly:

```bash
# Activate virtual environment first
source venv/bin/activate

# Then run any script
python3 scripts/sync.py --dev
python3 scripts/main.py --dryrun
python3 scripts/generate_labels.py --max 10
```

## Workflow Examples

### First-Time Setup

```bash
# 1. Install dependencies
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# 2. Configure
./bin/setup.sh

# 3. Test with small dataset
./bin/sync.sh --dev

# 4. Generate test labels
./bin/generate-labels.sh --max 5
```

### Regular Usage

```bash
# Sync new releases and generate labels
./bin/sync.sh --labels

# Or sync separately from label generation
./bin/sync.sh
./bin/generate-labels.sh
```

### Batch Processing

```bash
# Download audio for entire collection (no analysis yet)
./bin/main.sh --download-only

# Then analyze in batches
./bin/main.sh --max 50
./bin/main.sh --max 100
# etc.
```

### Regeneration

```bash
# Regenerate labels after template changes
./bin/main.sh --regenerate-labels

# Regenerate waveforms with new settings
./bin/main.sh --regenerate-waveforms
```

## Understanding Modes

### Development Mode (`--dev`)

- Limits processing to first 10 releases
- Useful for testing
- Doesn't affect saved configuration

### Dry Run Mode (`--dryrun`)

- Processes existing releases only
- No API calls to Discogs
- No downloads from YouTube
- Useful for:
  - Testing after code changes
  - Regenerating outputs
  - Verifying installation

### Download-Only Mode (`--download-only`)

- Downloads audio files
- Skips analysis (BPM, key detection, waveforms)
- Faster for bulk downloads
- Can analyze later with `./bin/main.sh`

### Labels-Only Mode (`--labels-only`)

- Generates labels from existing data
- No syncing with Discogs
- No audio processing
- Use with `--since` or `--max-labels` to control scope

## Output Structure

### Library Directory

Each release creates a subdirectory:

```
{LIBRARY_PATH}/
├── {release_id}_{release_title}/
│   ├── metadata.json              # Discogs metadata
│   ├── cover.jpg                  # Primary cover art
│   ├── cover_2.jpg                # Additional images (if any)
│   ├── qrcode.png                 # Plain QR code
│   ├── qrcode_fancy.png           # QR code with cover background
│   ├── yt_matches.json            # YouTube search results
│   ├── A1.opus                    # Audio files
│   ├── A1.json                    # Analysis data
│   ├── A1_waveform.png            # Waveform image
│   └── label.tex                  # LaTeX snippet
```

### Label Output Directory

```
output_labels/
├── label_combined.tex             # Combined LaTeX document
├── label_combined.pdf             # Generated PDF
└── temp/                          # Temporary build files
```

## Performance Tips

### Incremental Syncing

```bash
# Only process releases added this month
./bin/sync.sh --since 2024-12-01 --labels
```

### Parallel Processing

The scripts don't support parallel execution, but you can process batches:

```bash
# Terminal 1
./bin/main.sh --max 100

# Terminal 2
./bin/generate-labels.sh --max 50
```

### Storage Management

```bash
# Monitor disk usage
du -sh ~/Music/DiscogsLibrary

# Remove audio files but keep metadata and analysis
find ~/Music/DiscogsLibrary -name "*.opus" -delete
```

## Advanced Usage

### Custom Python Scripts

You can import the library modules:

```python
from src.config import load_config
from src.discogs_mirror import DiscogsLibraryMirror

config = load_config()
mirror = DiscogsLibraryMirror(config)
# Your custom logic here
```

### Environment Variables

Override configuration temporarily:

```bash
DISCOGS_USER_TOKEN=abc123 LIBRARY_PATH=/tmp/test ./bin/sync.sh --dev
```

### Scripting and Automation

```bash
#!/bin/bash
# Daily sync script

cd /path/to/DiscogsRecordLabelGenerator

# Sync new releases
./bin/sync.sh --since $(date -d '1 day ago' +%Y-%m-%d)

# Generate labels
./bin/generate-labels.sh

# Backup
rsync -av output_labels/ /backup/labels/
```

## Common Workflows

### Testing Template Changes

```bash
# 1. Modify LaTeX template in src/
# 2. Regenerate labels
./bin/main.sh --regenerate-labels --max 5
# 3. Check output_labels/label_combined.pdf
```

### Processing New Acquisitions

```bash
# After adding releases to Discogs collection
./bin/sync.sh --since $(date +%Y-%m-%d) --labels
```

### Rebuilding Everything

```bash
# Full reprocessing (caution: time-consuming)
./bin/sync.sh --dryrun
./bin/main.sh --regenerate-waveforms
./bin/main.sh --regenerate-labels
```

## See Also

- [Configuration Guide](CONFIGURATION.md)
- [Troubleshooting](TROUBLESHOOTING.md)
- [File Structure](FILE_STRUCTURE.md)