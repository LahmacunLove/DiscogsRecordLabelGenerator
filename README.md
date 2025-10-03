# DiscogsRecordLabelGenerator

Generate printable vinyl record labels from your Discogs collection with audio analysis, waveforms, and QR codes.

## Preview

![Label Sample](docs/assets/sample.png)

## Quick Start

### 1. Install Dependencies

**System Requirements:**
- Python 3.8+
- ffmpeg
- xelatex (TeX Live or MiKTeX)
- gnuplot (optional)

**Python Setup:**
```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

See [Installation Guide](docs/INSTALLATION.md) for platform-specific instructions.

### 2. Configure

Run the interactive setup:
```bash
./bin/setup.sh
```

This will guide you through getting your [Discogs API token](https://www.discogs.com/settings/developers) and setting up your library path.

### 3. Generate Labels

**Sync and generate labels:**
```bash
./bin/sync.sh --dev        # Test with first 10 releases
./bin/sync.sh              # Full collection
```

**Generate from existing releases:**
```bash
./bin/generate-labels.sh --max 10
```

## What It Does

1. Downloads your Discogs collection via API
2. Matches tracks to YouTube for audio analysis
3. Analyzes audio (BPM, key, waveforms) using Essentia
4. Generates QR codes with cover art
5. Creates printable PDF labels with LaTeX

## Features

### Multi-Threaded Processing with Live CLI Visualization

The sync process now features a real-time multi-threaded CLI display that shows:

- **Per-Worker Progress**: Each worker thread displayed in its own panel
- **Current Status**: Live updates showing what step each worker is processing
- **File Tracking**: See files as they're generated (metadata, covers, audio, labels)
- **Progress Indicators**: Visual progress bars and percentage completion per worker
- **Graceful Shutdown**: Press Ctrl+C to stop all threads cleanly
- **Overall Statistics**: Total progress, error count, elapsed time

**Example Display:**
```
🎵 Processing releases
Progress: 15/50 (30.0%) │ Errors: 1 │ Workers: 4 │ Time: 5m 23s

┌─ 🟢 Worker 0 │ Completed: 3 ─────────────────┐┌─ 🟢 Worker 1 │ Completed: 4 ─────────────────┐
│ Release: 123456                               ││ Release: 789012                               │
│ Title: Kind of Blue                           ││ Title: Abbey Road                             │
│ Step: Downloading audio                       ││ Step: Analyzing audio                         │
│ [████████████████░░░░] 60%                    ││ [██████████████████░] 75%                     │
│ Time: 45s                                     ││ Time: 62s                                     │
│ Files: • metadata.json                        ││ Files: • track01.opus                         │
│        • cover.jpg                            ││        • track02.opus                         │
│        • track01.opus                         ││        • waveform.png                         │
└───────────────────────────────────────────────┘└───────────────────────────────────────────────┘
```

**Test it:** Run `python3 tests/test_monitor.py` to see a demo with simulated releases.

## Commands

```bash
# Sync your collection
./bin/sync.sh [--dev|--dryrun] [--labels] [--max N]

# Process existing releases
./bin/main.sh [--dev|--dryrun] [--download-only] [--max N]

# Generate labels only
./bin/generate-labels.sh [--max N] [--output DIR]

# Interactive setup
./bin/setup.sh
```

See [Usage Guide](docs/USAGE.md) for detailed options.

## Documentation

- [Installation Guide](docs/INSTALLATION.md) - Platform-specific setup instructions
- [Usage Guide](docs/USAGE.md) - Detailed command reference
- [Configuration](docs/CONFIGURATION.md) - Advanced configuration options
- [Troubleshooting](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [File Structure](docs/FILE_STRUCTURE.md) - Output directory layout

## Output

Each release creates a directory with:
- Metadata and cover art
- Audio files (.opus format)
- Analysis data (BPM, key, waveforms)
- QR codes (plain and fancy)
- LaTeX label snippets

Labels are compiled into PDFs in `output_labels/`, formatted for 8163 shipping labels.

## License

Open source software. See LICENSE file for details.