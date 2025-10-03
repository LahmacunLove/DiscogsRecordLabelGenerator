# File Structure Documentation

This document describes the directory structure and file organization of DiscogsRecordLabelGenerator.

## Project Structure

```
DiscogsRecordLabelGenerator/
├── bin/                          # Shell wrapper scripts
│   ├── _common.sh               # Shared functions for scripts
│   ├── setup.sh                 # Interactive configuration wizard
│   ├── sync.sh                  # Sync and label generation wrapper
│   └── generate-labels.sh       # Label generation wrapper
├── scripts/                      # Python entry points
│   ├── setup.py                 # Setup script
│   ├── sync.py                  # Sync CLI tool
│   ├── generate_labels.py       # Label generation script
│   ├── cleanup_duplicates.py    # Duplicate cleanup utility
│   └── similarity_analyzer.py   # Audio similarity analyzer
├── src/                         # Core library code
│   ├── config.py                # Configuration management
│   ├── discogs_mirror.py        # Discogs API interaction
│   ├── youtube_matcher.py       # YouTube search and matching
│   ├── audio_analyzer.py        # Audio analysis (Essentia)
│   ├── label_generator.py       # LaTeX label generation
│   ├── qr_generator.py          # QR code creation
│   └── waveform_generator.py    # Waveform visualization
├── docs/                        # Documentation
│   ├── README.md                # Documentation index
│   ├── INSTALLATION.md          # Installation guide
│   ├── USAGE.md                 # Usage guide
│   ├── CONFIGURATION.md         # Configuration guide
│   ├── TROUBLESHOOTING.md       # Troubleshooting guide
│   ├── FILE_STRUCTURE.md        # This file
│   ├── DEPENDENCY_NOTES.md      # Dependency notes
│   ├── PR_SYNC_CLI.md          # PR documentation
│   └── assets/                  # Documentation assets
│       ├── sample.png           # Sample label image
│       └── sample2.png          # Additional sample
├── .github/                     # GitHub-specific files
│   └── copilot-instructions.md  # Development guidelines
├── requirements.txt             # Python dependencies
├── README.md                    # Main project README
└── LICENSE                      # License file
```

## Library Directory Structure

The library path (configured in `~/.config/discogsDBLabelGen/discogs.env`) contains release data:

```
{LIBRARY_PATH}/
├── {release_id}_{release_title}/
│   ├── metadata.json              # Discogs metadata
│   ├── cover.jpg                  # Primary album artwork
│   ├── cover_2.jpg                # Additional cover images (if any)
│   ├── cover_3.jpg                # Additional cover images (if any)
│   ├── qrcode.png                 # Plain QR code (Discogs link)
│   ├── qrcode_fancy.png           # QR code with cover art background
│   ├── yt_matches.json            # YouTube search results
│   ├── A1.opus                    # Audio files (Opus format)
│   ├── A1.json                    # Analysis data (BPM, key, etc.)
│   ├── A1_waveform.png            # Waveform visualization
│   ├── A2.opus                    # Additional tracks...
│   ├── A2.json
│   ├── A2_waveform.png
│   └── label.tex                  # LaTeX label snippet
├── {another_release_id}_{title}/
│   └── ...
└── ...
```

## Release Directory Files

### metadata.json

Complete Discogs metadata for the release, including:
- Release ID
- Artist(s)
- Title
- Label
- Catalog number
- Year
- Format
- Tracklist
- Credits
- Cover art URLs

**Example:**
```json
{
  "id": 123456,
  "title": "Album Title",
  "artists": [{"name": "Artist Name"}],
  "labels": [{"name": "Record Label", "catno": "CAT001"}],
  "year": 2024,
  "tracklist": [
    {
      "position": "A1",
      "title": "Track Title",
      "duration": "3:45"
    }
  ]
}
```

### cover.jpg, cover_2.jpg, ...

Album artwork images downloaded from Discogs:
- `cover.jpg`: Primary cover image
- `cover_2.jpg`, `cover_3.jpg`, etc.: Additional images (back cover, labels, etc.)

Format: JPEG
Typical resolution: 600x600 or larger

### qrcode.png

Plain QR code linking to the release on Discogs.

Format: PNG
Size: 200x200 pixels
Content: URL to `https://www.discogs.com/release/{release_id}`

### qrcode_fancy.png

QR code with the album cover art as background.

Format: PNG
Size: Larger than plain QR code
Features: Cover art blended with QR code for aesthetic appeal

### yt_matches.json

YouTube search results and matched videos for each track.

**Example:**
```json
{
  "A1": {
    "query": "Artist Name - Track Title",
    "video_id": "dQw4w9WgXcQ",
    "title": "Artist Name - Track Title (Official Audio)",
    "duration": 225
  }
}
```

### Track Audio Files (*.opus)

Downloaded audio files in Opus format:
- Named by track position: `A1.opus`, `B2.opus`, etc.
- Codec: Opus (efficient, high-quality)
- Source: YouTube (best available quality)

### Track Analysis Files (*.json)

Audio analysis data for each track.

**Example:**
```json
{
  "bpm": 128.5,
  "key": "C major",
  "duration": 225.6,
  "loudness": -14.2,
  "spectral_data": { ... }
}
```

Fields may include:
- **bpm**: Beats per minute (tempo)
- **key**: Musical key
- **duration**: Track length in seconds
- **loudness**: Average loudness (LUFS)
- **spectral_data**: Frequency analysis data

### Waveform Images (*_waveform.png)

Waveform visualization for use in labels:
- Named by track position: `A1_waveform.png`
- Generated with gnuplot
- Shows amplitude over time
- Optimized for label printing

Format: PNG
Dimensions: Optimized for label layout

### label.tex

LaTeX snippet containing the formatted label content for this release.

Includes:
- Track listing with positions, titles, and durations
- BPM and key information
- Waveform images
- Release metadata
- QR code

This file is included in the combined label document.

## Output Directory Structure

Generated labels are placed in the output directory:

```
output_labels/
├── label_combined.tex             # Combined LaTeX document
├── label_combined.pdf             # Generated PDF with all labels
├── label_combined.aux             # LaTeX auxiliary files
├── label_combined.log             # LaTeX compilation log
└── temp/                          # Temporary build files
    ├── *.aux
    ├── *.log
    └── *.out
```

### label_combined.tex

Master LaTeX document that includes all individual `label.tex` files.

Structure:
```latex
\documentclass{...}
% Preamble with packages and settings
\begin{document}
\input{/path/to/release1/label.tex}
\input{/path/to/release2/label.tex}
% ...
\end{document}
```

### label_combined.pdf

Final output: Printable PDF with all labels.

Features:
- Formatted for Avery Zweckform L4744REV-65 labels (96 x 50.8 mm on A4 paper)
- 10 labels per page (2 columns x 5 rows)
- Ready to print

## Configuration Directory

User configuration is stored in the standard config location:

```
~/.config/discogsDBLabelGen/
└── discogs.env                    # JSON configuration file
```

**Linux/macOS:** `~/.config/discogsDBLabelGen/discogs.env`
**Windows:** `%USERPROFILE%\.config\discogsDBLabelGen\discogs.env`

## Virtual Environment

Python virtual environment (not tracked in git):

```
venv/
├── bin/                           # Executables (Linux/macOS)
│   ├── python
│   ├── pip
│   └── activate
├── Scripts/                       # Executables (Windows)
│   ├── python.exe
│   ├── pip.exe
│   └── activate.bat
└── lib/                          # Installed packages
    └── python3.x/
        └── site-packages/
```

## File Naming Conventions

### Track Positions

Tracks are named by their vinyl position:
- **Side A**: A1, A2, A3, ...
- **Side B**: B1, B2, B3, ...
- **Side C**: C1, C2, C3, ... (for multi-disc releases)
- **Side D**: D1, D2, D3, ...

**Digital tracks** (no side designation): 1, 2, 3, ...

### Release Directories

Format: `{release_id}_{sanitized_title}`

Example: `123456_Artist_Name_Album_Title`

Special characters are sanitized:
- Spaces become underscores
- Special characters removed or replaced
- Maximum length enforced (filesystem limits)

## File Formats

### Audio
- **Opus** (.opus): Primary audio format (efficient, high-quality)

### Images
- **JPEG** (.jpg): Cover art
- **PNG** (.png): QR codes, waveforms (lossless for graphics)

### Data
- **JSON** (.json): Metadata and analysis data (human-readable)

### Documents
- **LaTeX** (.tex): Label templates and snippets
- **PDF** (.pdf): Final printable labels

## Storage Considerations

### Typical Space Usage

Per release (approximate):
- Metadata: < 1 MB
- Cover art: 0.5-2 MB
- Audio files: 3-8 MB per track (depends on length)
- Analysis data: < 100 KB per track
- Waveforms: < 500 KB per track
- QR codes: < 100 KB

**Example:**
- 10-track album: ~50-100 MB
- 100 releases: ~5-10 GB
- 1000 releases: ~50-100 GB

### Optimization

To reduce storage:
```bash
# Remove audio files (keep metadata and analysis)
find ~/Music/DiscogsLibrary -name "*.opus" -delete

# Remove waveforms (can be regenerated)
find ~/Music/DiscogsLibrary -name "*_waveform.png" -delete

# Remove extra cover images (keep cover.jpg)
find ~/Music/DiscogsLibrary -name "cover_[2-9].jpg" -delete
```

## Backup Strategy

### Essential Files

Minimum backup for recovery:
- Configuration: `~/.config/discogsDBLabelGen/discogs.env`
- Metadata: All `metadata.json` files
- Analysis: All `*.json` files (optional but time-consuming to regenerate)

### Full Backup

Complete backup includes:
- Entire library directory
- Configuration directory
- Generated labels (output_labels/)

**Backup command:**
```bash
tar -czf discogs_backup_$(date +%Y%m%d).tar.gz \
  ~/.config/discogsDBLabelGen \
  ~/Music/DiscogsLibrary \
  output_labels
```

## See Also

- [Installation Guide](INSTALLATION.md)
- [Configuration Guide](CONFIGURATION.md)
- [Usage Guide](USAGE.md)
- [Troubleshooting](TROUBLESHOOTING.md)