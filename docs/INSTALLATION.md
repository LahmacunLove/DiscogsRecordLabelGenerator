# Installation Guide

This guide provides detailed installation instructions for DiscogsRecordLabelGenerator across different platforms.

## System Requirements

- **Python**: 3.8 or higher (3.9+ recommended)
- **ffmpeg**: Audio processing and conversion
- **xelatex**: PDF generation with Unicode support (part of TeX Live or MiKTeX)
- **gnuplot**: Waveform visualization (optional but recommended)

## Platform-Specific Instructions

### Ubuntu/Debian

```bash
# Update package lists
sudo apt update

# Install system dependencies
sudo apt install ffmpeg texlive-xetex gnuplot python3-pip python3-venv

# Clone the repository (if not already done)
git clone <repository-url>
cd DiscogsRecordLabelGenerator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### macOS

**Using Homebrew:**

```bash
# Install Homebrew if not already installed
/bin/bash -c "$(curl -fsSL https://raw.githubusercontent.com/Homebrew/install/HEAD/install.sh)"

# Install system dependencies
brew install ffmpeg mactex gnuplot python@3.11

# Add LaTeX to PATH (if needed)
echo 'export PATH="/Library/TeX/texbin:$PATH"' >> ~/.zshrc
source ~/.zshrc

# Clone the repository (if not already done)
git clone <repository-url>
cd DiscogsRecordLabelGenerator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

**Note**: You may need to install Xcode command line tools first:
```bash
xcode-select --install
```

### Arch Linux

```bash
# Install system dependencies
sudo pacman -S ffmpeg texlive-core texlive-bin gnuplot python-pip

# Clone the repository (if not already done)
git clone <repository-url>
cd DiscogsRecordLabelGenerator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Fedora/RHEL/CentOS

```bash
# Enable EPEL repository (RHEL/CentOS only)
sudo dnf install epel-release

# Install system dependencies
sudo dnf install ffmpeg texlive-xetex gnuplot python3-pip

# Clone the repository (if not already done)
git clone <repository-url>
cd DiscogsRecordLabelGenerator

# Create and activate virtual environment
python3 -m venv venv
source venv/bin/activate

# Install Python dependencies
pip install -r requirements.txt
```

### Windows

#### Step 1: Install Python

1. Download Python 3.8+ from [python.org](https://python.org/downloads)
2. Run the installer
3. **Important**: Check "Add Python to PATH" during installation

#### Step 2: Install FFmpeg

1. Download FFmpeg from [ffmpeg.org](https://ffmpeg.org/download.html)
2. Extract the archive to `C:\ffmpeg`
3. Add `C:\ffmpeg\bin` to your system PATH:
   - Open System Properties → Environment Variables
   - Edit the "Path" variable
   - Add new entry: `C:\ffmpeg\bin`
   - Click OK to save

#### Step 3: Install LaTeX

Choose one of these distributions:

**Option A: MiKTeX** (Recommended for Windows)
1. Download from [miktex.org](https://miktex.org/download)
2. Run the installer with default settings
3. MiKTeX will automatically download required packages

**Option B: TeX Live**
1. Download from [tug.org/texlive](https://tug.org/texlive/)
2. Run the installer (large download, ~4GB)

#### Step 4: Install gnuplot (Optional)

1. Download from [gnuplot.info](http://www.gnuplot.info/download.html)
2. Run the installer
3. Add gnuplot to PATH (usually `C:\Program Files\gnuplot\bin`)

#### Step 5: Install Python Dependencies

Open Command Prompt or PowerShell:

```powershell
# Navigate to project directory
cd path\to\DiscogsRecordLabelGenerator

# Create virtual environment
python -m venv venv

# Activate virtual environment
venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
```

**Note**: On Windows, use forward slashes (`/`) in configuration paths, not backslashes (`\`).

## Python Virtual Environment

### Why Use a Virtual Environment?

- Isolates project dependencies from system Python
- Prevents version conflicts between projects
- **Required for Python 3.13+** due to PEP 668

### Creating and Using Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate it
# Linux/macOS:
source venv/bin/activate

# Windows (Command Prompt):
venv\Scripts\activate.bat

# Windows (PowerShell):
venv\Scripts\Activate.ps1

# Install dependencies
pip install -r requirements.txt

# Deactivate when done
deactivate
```

### Automatic Activation with Shell Scripts

The `bin/` scripts automatically activate the virtual environment:

```bash
./bin/sync.sh --dev        # venv activated automatically
./bin/sync.sh --help       # see all options
```

## Python Dependencies

The project requires these Python packages (installed via `requirements.txt`):

- **python3-discogs-client**: Discogs API client
- **yt-dlp**: YouTube audio downloading
- **essentia**: Audio analysis (BPM, key detection)
- **pandas**: Data processing
- **rapidfuzz**: Fuzzy string matching
- **scipy**: Scientific computing
- **matplotlib**: Plotting and visualization
- **tqdm**: Progress bars
- **segno**: QR code generation
- **numpy**: Numerical computing
- **scikit-learn**: Machine learning utilities
- **librosa**: Audio analysis
- **python-dateutil**: Date parsing

### Manual Installation (Alternative)

If you prefer not to use `requirements.txt`:

```bash
pip install python3-discogs-client yt-dlp essentia pandas rapidfuzz scipy matplotlib tqdm segno numpy scikit-learn librosa python-dateutil
```

## Verification

Test your installation:

```bash
# Activate virtual environment
source venv/bin/activate  # or venv\Scripts\activate on Windows

# Check Python
python3 --version

# Check system tools
ffmpeg -version
xelatex --version
gnuplot --version

# Test Python imports
python3 -c "import essentia, discogs_client, yt_dlp; print('Python dependencies OK')"
```

## Troubleshooting Installation

### Python 3.13+ PEP 668 Errors

**Error**: `error: externally-managed-environment`

**Solution**: Always use a virtual environment (see above).

### Essentia Installation Issues

**Linux**: Essentia may require additional dependencies:
```bash
sudo apt install libavcodec-dev libavformat-dev libavutil-dev libswresample-dev
```

**macOS**: Install via Homebrew:
```bash
brew install essentia
```

**Windows**: Essentia can be challenging. Try:
```bash
pip install essentia-tensorflow  # Lighter alternative
```

### FFmpeg Not Found

**Verify installation**:
```bash
which ffmpeg       # Linux/macOS
where ffmpeg       # Windows
```

**If not found**:
- Linux: Ensure package is installed and PATH is updated
- macOS: Run `brew link ffmpeg`
- Windows: Verify PATH environment variable includes FFmpeg bin directory

### XeLaTeX Not Found

**Linux**: Install full TeX Live distribution:
```bash
sudo apt install texlive-full  # Large but comprehensive
```

**macOS**: 
```bash
brew install --cask mactex
# Then restart terminal or run:
export PATH="/Library/TeX/texbin:$PATH"
```

**Windows**: Reinstall MiKTeX or TeX Live, ensuring it's added to PATH.

### Permission Errors

**Linux/macOS**: Ensure library directory is writable:
```bash
chmod -R u+w ~/Music/DiscogsLibrary
```

**Windows**: Run terminal as Administrator or choose a user-writable directory.

## Next Steps

After successful installation:

1. [Configure the application](CONFIGURATION.md)
2. [Read the usage guide](USAGE.md)
3. Run `./bin/setup.sh` for interactive setup