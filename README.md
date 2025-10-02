# DiscogsRecordLabelGenerator

A Python application that syncs your Discogs collection, analyzes tracks, and generates printable vinyl record labels.

### Preview

![Label Sample 1](sample.png)

![Label Sample 2](sample2.png)

## What it does

1. **Downloads your Discogs collection** via the Discogs API
2. **Matches tracks to YouTube videos** for audio analysis  
3. **Analyzes audio files** using Essentia (BPM, key detection, spectrograms)
4. **Generates waveform images** with gnuplot
5. **Creates QR codes** (both plain and fancy with cover art backgrounds)
6. **Creates printable labels** in PDF format using LaTeX

## Quick Start

### Step 1: Setup (First Time Only)
```bash
python3 setup.py
```
This interactive script will guide you through:
- Getting your Discogs API token
- Choosing where to store your music library
- Creating your configuration file

<details>
<summary>Example setup session (click to expand)</summary>

```
============================================================
  DiscogsRecordLabelGenerator - Setup
============================================================

── Discogs API Token ───────────────────────────────────────

You need a personal access token from Discogs.

To get your token:
  1. Go to: https://www.discogs.com/settings/developers
  2. Click 'Generate new token'
  3. Copy the token

Enter your Discogs token: njBUrxYhPyKiBWZctlFhYXXmHFNjhybHXBByTyPS

── Library Path ────────────────────────────────────────────

This is where the application will store:
  • Downloaded metadata
  • Audio files
  • Analysis data
  • Generated labels

Each release will have its own subdirectory.

Suggested path: /home/user/Music/DiscogsLibrary

Enter library path [/home/user/Music/DiscogsLibrary]: 

📁 Directory does not exist: /home/user/Music/DiscogsLibrary
Create it now? [Y/n]: y
✅ Created directory: /home/user/Music/DiscogsLibrary

── Creating Configuration ──────────────────────────────────

✅ Config directory ready: /home/user/.config/discogsDBLabelGen
✅ Configuration saved: /home/user/.config/discogsDBLabelGen/discogs.env

── Testing Configuration ───────────────────────────────────

✅ Configuration loaded successfully!
   Library path: /home/user/Music/DiscogsLibrary
   Token: ********************yTyPS

── Next Steps ──────────────────────────────────────────────

Configuration complete! Here's what to do next:

1. Install dependencies (if not done yet):
   python3 -m venv venv
   source venv/bin/activate
   pip install -r requirements.txt

2. Run the application:
   ./run.sh --dev          # Test with first 10 releases
   ./run.sh                # Full collection sync
   python3 sync.py --help  # See all CLI options

3. For help:
   ./run.sh --help
   python3 sync.py --help

============================================================
  Setup completed successfully! 🎉
============================================================
```
</details>

### Step 2: Run the Application

**Option A: Quick Sync (Command Line)**
```bash
./run.sh --dev  # Process first 10 releases (automatically uses virtual environment)
```

**Option B: Advanced Sync (CLI Tool)**
```bash
python3 sync.py --dev --labels  # Dev mode with label generation
python3 sync.py --help          # See all options
```

> **Note**: The `run.sh` convenience script automatically activates the virtual environment for you. If you prefer to manually activate it, use: `source venv/bin/activate`
</parameter>

<old_text line=151>
> **Note**: The `run.sh` convenience script automatically handles the virtual environment for you after this initial setup.

## Requirements

### External Tools (must be in $PATH)
- `ffmpeg` - Audio processing
- `xelatex` - PDF generation (XeLaTeX for Unicode support)
- `gnuplot` - Waveform generation (optional but recommended)

### Python Libraries

**Recommended: Use a virtual environment** (especially for Python 3.13+)
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

**Alternative: Direct installation**
```bash
pip install discogs_client yt-dlp essentia pandas rapidfuzz scipy matplotlib tqdm segno numpy scikit-learn librosa python-dateutil
```

## Setup

### Step 1: Install Python Dependencies

**Recommended: Using requirements.txt**
```bash
# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install all dependencies
pip install -r requirements.txt
```

> **Note**: The `run.sh` convenience script automatically handles the virtual environment for you after this initial setup.

> **Note for Python 3.13+**: Due to PEP 668, using a virtual environment is strongly recommended to avoid conflicts with system packages.

### Step 2: Install External Dependencies

**Windows:**
1. Install [Python 3.8+](https://python.org/downloads)
2. Install [FFmpeg](https://ffmpeg.org/download.html) and add to PATH
3. Install [MiKTeX](https://miktex.org/) or [TeX Live](https://tug.org/texlive/) for XeLaTeX
4. Install [gnuplot](http://www.gnuplot.info/) (optional)

**macOS:**
```bash
brew install ffmpeg mactex gnuplot
```

**Ubuntu/Debian:**
```bash
sudo apt update
sudo apt install ffmpeg texlive-xetex gnuplot python3-pip
```

**Arch Linux:**
```bash
sudo pacman -S ffmpeg texlive-core texlive-bin gnuplot python-pip
```

**CentOS/RHEL/Fedora:**
```bash
sudo dnf install ffmpeg texlive-xetex gnuplot python3-pip
```

### Step 3: Configure the Application

The application requires two configuration values:

- **`DISCOGS_USER_TOKEN`**: Your personal Discogs API token from https://www.discogs.com/settings/developers
- **`LIBRARY_PATH`**: Local filesystem path where the program will store all downloaded metadata, audio files, analysis data, and generated labels. Each release will have its own subdirectory here.

**Option A: Interactive Setup (Easiest)** ⭐
```bash
python3 setup.py
```
This interactive script will:
- Guide you step-by-step to get your Discogs API token
- Help you choose a library path
- Create the directory if it doesn't exist
- Automatically create the configuration file
- Test that everything works

See the expandable example above for what the setup process looks like.

**Option B: CLI Sync Tool Configuration**
```bash
python3 sync.py --token YOUR_TOKEN --library ~/Music/Discogs --configure
```
This saves your configuration for future use.

**Option C: Manual Configuration**
Run this command to create and edit the config file:
```bash
mkdir -p ~/.config/discogsDBLabelGen && cat > ~/.config/discogsDBLabelGen/discogs.env << 'EOF'
{
  "DISCOGS_USER_TOKEN": "your_discogs_token_here",
  "LIBRARY_PATH": "/path/to/your/music/library"
}
EOF
```
Replace `your_discogs_token_here` and `/path/to/your/music/library` with your actual values.

## Usage

### CLI Sync Tool (sync.py)

The `sync.py` tool provides a comprehensive command-line interface:

```bash
# Full sync with label generation
python3 sync.py

# Development mode (limited releases)
python3 sync.py --dev

# Dry run (process existing releases only)
python3 sync.py --dryrun

# Configure and save settings
python3 sync.py --token YOUR_TOKEN --library ~/Music/Discogs --configure

# Generate labels only (no sync)
python3 sync.py --labels-only

# Generate specific release
python3 sync.py --labels-only --release 123456

# Generate labels since date
python3 sync.py --labels-only --since 2024-01-01

# Limit number of labels
python3 sync.py --labels-only --max-labels 10
```

### Main Script (main.py)

**Using convenience script (recommended):**
```bash
# Full collection sync
./run.sh

# Development mode (first 10 releases only)
./run.sh --dev

# Dry run (offline processing of existing releases)
./run.sh --dryrun

# Download-only mode (sync and download without analysis)
./run.sh --download-only

# Custom limit (e.g., first 25 releases)  
./run.sh --max 25

# Regenerate labels only
./run.sh --regenerate-labels
```

**Or activate venv manually:**
```bash
source venv/bin/activate

python3 main.py                      # Full collection sync
python3 main.py --dev                # Development mode
python3 main.py --dryrun             # Dry run
python3 main.py --download-only      # Download-only mode
python3 main.py --max 25             # Custom limit
python3 main.py --regenerate-labels  # Regenerate labels only
python3 main.py --regenerate-waveforms  # Regenerate waveforms only
```

### Generate Printable Labels
```bash
# With virtual environment (activate first):
source venv/bin/activate

# Generate labels for all releases
python3 generate_labels.py

# Generate first 10 releases for testing
python3 generate_labels.py --max 10

# Custom output directory
python3 generate_labels.py --output ~/my_labels
```

## File Structure

Each release creates a folder:
```
{release_id}_{release_title}/
├── metadata.json              # Discogs metadata
├── cover.jpg                  # Primary album artwork
├── cover_2.jpg, cover_3.jpg...# Additional cover images (if available)
├── qrcode.png                 # Plain QR code linking to Discogs
├── qrcode_fancy.png          # Fancy QR code with cover art background
├── yt_matches.json           # YouTube matches
├── A1.opus, A2.opus...       # Audio files
├── A1.json, A2.json...       # Analysis data (BPM, key, etc.)
├── A1_waveform.png...        # Waveform images for labels
└── label.tex                 # LaTeX label snippet
```

## Configuration Template

Save this as `~/.config/discogsDBLabelGen/discogs.env`:
```json
{
  "DISCOGS_USER_TOKEN": "AbCdEfGhIjKlMnOpQrStUvWxYz1234567890",
  "LIBRARY_PATH": "$HOME/Music/DiscogsLibrary"
}
```

Replace `AbCdEfGhIjKlMnOpQrStUvWxYz1234567890` with your actual Discogs token and adjust the library path as needed.

## Label Output

The generated labels include:
- Track listing with BPM and musical key
- Waveform visualizations
- Release information (artist, title, label, year)
- Format optimized for 8163 shipping labels

## Troubleshooting

**Common Issues:**
- **"No module named 'essentia'" or similar**: Activate virtual environment (`source venv/bin/activate`) or run `pip install -r requirements.txt`
- **"No module named 'six'"**: Use the convenience script (`./run.sh`) or manually activate venv first
- **"ffmpeg not found"**: Install ffmpeg and ensure it's in your PATH
- **"xelatex not found"**: Install a LaTeX distribution with XeLaTeX support (texlive/miktex)
- **LaTeX compilation errors**: Check for special characters in track titles
- **Permission errors**: Make sure the library path is writable
- **PEP 668 errors (Python 3.13+)**: Use a virtual environment instead of system-wide installation

**Platform-Specific:**
- **Windows**: Use forward slashes `/` in paths, not backslashes `\`
- **macOS**: May need to install Xcode command line tools: `xcode-select --install`


## License

Open source software. See LICENSE file for details.