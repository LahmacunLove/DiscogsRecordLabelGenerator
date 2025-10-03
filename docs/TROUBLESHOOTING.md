# Troubleshooting Guide

This guide covers common issues and their solutions when using DiscogsRecordLabelGenerator.

## Installation Issues

### Python Module Not Found

**Error:** `ModuleNotFoundError: No module named 'essentia'` (or similar)

**Cause:** Python dependencies not installed or virtual environment not activated.

**Solutions:**

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate     # Windows

# Install/reinstall dependencies
pip install -r requirements.txt
```

### PEP 668 Error (Python 3.13+)

**Error:** `error: externally-managed-environment`

**Cause:** Python 3.13+ prevents system-wide package installation.

**Solution:** Always use a virtual environment:

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### FFmpeg Not Found

**Error:** `FileNotFoundError: ffmpeg not found` or `ffmpeg: command not found`

**Solutions:**

**Verify installation:**
```bash
which ffmpeg       # Linux/macOS
where ffmpeg       # Windows
ffmpeg -version    # Any platform
```

**Install if missing:**
```bash
# Ubuntu/Debian
sudo apt install ffmpeg

# macOS
brew install ffmpeg

# Arch Linux
sudo pacman -S ffmpeg

# Fedora
sudo dnf install ffmpeg
```

**Windows:** Download from [ffmpeg.org](https://ffmpeg.org/download.html) and add to PATH.

### XeLaTeX Not Found

**Error:** `xelatex: command not found` or LaTeX compilation fails

**Solutions:**

**Verify installation:**
```bash
which xelatex      # Linux/macOS
where xelatex      # Windows
xelatex --version  # Any platform
```

**Install if missing:**
```bash
# Ubuntu/Debian
sudo apt install texlive-xetex

# macOS
brew install --cask mactex

# Arch Linux
sudo pacman -S texlive-core texlive-bin

# Fedora
sudo dnf install texlive-xetex
```

**Windows:** Install [MiKTeX](https://miktex.org/) or [TeX Live](https://tug.org/texlive/).

### Essentia Installation Fails

**Error:** Compilation errors when installing essentia

**Solutions:**

**Linux:** Install development libraries:
```bash
sudo apt install build-essential libavcodec-dev libavformat-dev \
                 libavutil-dev libswresample-dev libyaml-dev
pip install essentia
```

**macOS:**
```bash
brew install essentia
pip install essentia
```

**Windows:** Try the TensorFlow variant:
```bash
pip install essentia-tensorflow
```

## Configuration Issues

### Configuration File Not Found

**Error:** `Configuration file not found` or `FileNotFoundError`

**Solutions:**

1. **Run interactive setup:**
   ```bash
   ./bin/setup.sh
   ```

2. **Create manually:**
   ```bash
   mkdir -p ~/.config/discogsDBLabelGen
   cat > ~/.config/discogsDBLabelGen/discogs.env << 'EOF'
   {
     "DISCOGS_USER_TOKEN": "YOUR_TOKEN_HERE",
     "LIBRARY_PATH": "/path/to/library"
   }
   EOF
   ```

### Invalid JSON in Configuration

**Error:** `json.decoder.JSONDecodeError`

**Cause:** Malformed JSON in configuration file.

**Solution:** Validate JSON syntax:

```bash
python3 -c "import json; print(json.load(open('$HOME/.config/discogsDBLabelGen/discogs.env')))"
```

**Common issues:**
- Single quotes instead of double quotes
- Trailing commas
- Missing quotes around strings
- Unescaped backslashes in Windows paths (use forward slashes instead)

**Correct format:**
```json
{
  "DISCOGS_USER_TOKEN": "AbCdEf1234567890",
  "LIBRARY_PATH": "/home/user/Music/Discogs"
}
```

### Invalid Discogs Token

**Error:** `401 Unauthorized` or `Invalid authentication token`

**Solutions:**

1. **Verify token:**
   - Check for typos or extra spaces
   - Ensure no newlines in token
   - Copy-paste directly from Discogs

2. **Generate new token:**
   - Go to [Discogs Developer Settings](https://www.discogs.com/settings/developers)
   - Delete old token
   - Generate new token
   - Update configuration

3. **Test token:**
   ```bash
   ./bin/sync.sh --dev
   ```

## Runtime Issues

### Permission Denied

**Error:** `PermissionError: [Errno 13] Permission denied`

**Cause:** No write access to library directory.

**Solutions:**

```bash
# Check permissions
ls -ld /path/to/library

# Fix ownership (Linux/macOS)
sudo chown -R $USER:$USER /path/to/library

# Fix permissions
chmod -R u+w /path/to/library

# Or choose a different location
./bin/setup.sh  # Run setup again with different path
```

### Disk Space Issues

**Error:** `OSError: [Errno 28] No space left on device`

**Cause:** Insufficient disk space.

**Solutions:**

```bash
# Check disk usage
df -h
du -sh ~/Music/DiscogsLibrary

# Clean up space
# Option 1: Remove audio files (keep metadata and analysis)
find ~/Music/DiscogsLibrary -name "*.opus" -delete

# Option 2: Move library to larger disk
mv ~/Music/DiscogsLibrary /mnt/external/
# Update configuration with new path
```

### YouTube Download Fails

**Error:** `yt-dlp error` or download timeouts

**Solutions:**

1. **Update yt-dlp:**
   ```bash
   pip install --upgrade yt-dlp
   ```

2. **Check internet connection:**
   ```bash
   ping youtube.com
   ```

3. **Retry with specific release:**
   ```bash
   ./bin/sync.sh --release 123456
   ```

4. **Skip problematic releases:**
   - The tool continues with next release after failures
   - Check logs for specific error messages

### LaTeX Compilation Errors

**Error:** LaTeX compilation fails or produces incomplete PDF

**Common causes and solutions:**

**1. Special characters in titles:**
```
Error: Undefined control sequence
```

**Solution:** The application should escape special characters, but if issues persist, check release titles for: `&`, `%`, `$`, `#`, `_`, `{`, `}`, `~`, `^`, `\`

**2. Missing fonts:**
```
Error: Font not found
```

**Solution:** Install additional fonts:
```bash
# Ubuntu/Debian
sudo apt install texlive-fonts-extra

# macOS
brew install --cask font-computer-modern

# Or use system fonts (application should handle this)
```

**3. Long file paths:**

**Solution:** Use shorter library path or move library closer to root.

**4. Unicode issues:**

**Solution:** Ensure XeLaTeX is installed (not just pdflatex):
```bash
xelatex --version
```

### Rate Limiting

**Error:** `429 Too Many Requests` from Discogs API

**Cause:** Exceeded API rate limit.

**Solutions:**

1. **Wait and retry:**
   - Discogs allows 60 requests/minute for authenticated users
   - Script includes delays, but rapid repeated runs can trigger limits

2. **Use authenticated requests:**
   - Ensure your token is configured (increases rate limit)

3. **Process in smaller batches:**
   ```bash
   ./bin/sync.sh --max 50
   # Wait a few minutes
   ./bin/sync.sh --max 50
   ```

## Processing Issues

### No Audio Downloaded

**Symptom:** Sync completes but no `.opus` files in release directories

**Causes and solutions:**

1. **No YouTube matches found:**
   - Check `yt_matches.json` in release directory
   - Manual matching may be needed for obscure releases

2. **YouTube download blocked:**
   - Update yt-dlp: `pip install --upgrade yt-dlp`
   - Check network/firewall settings

3. **Download-only mode:**
   - If using `--download-only`, audio is downloaded but not analyzed
   - Run `./bin/main.sh` to complete processing

### Analysis Data Missing

**Symptom:** Audio files exist but no `.json` analysis files

**Solutions:**

```bash
# Rerun analysis
./bin/main.sh --max 10  # Test with small batch first

# Check for errors
./bin/main.sh --dev 2>&1 | tee error.log
```

**If Essentia errors occur:**
- Reinstall essentia: `pip install --force-reinstall essentia`
- Check audio file integrity: `ffmpeg -i release_dir/A1.opus -f null -`

### Waveform Generation Fails

**Symptom:** No `*_waveform.png` files

**Cause:** gnuplot not installed or audio files missing.

**Solutions:**

```bash
# Install gnuplot
sudo apt install gnuplot  # Ubuntu/Debian
brew install gnuplot      # macOS

# Regenerate waveforms
./bin/main.sh --regenerate-waveforms
```

### Labels Not Generated

**Symptom:** No PDF output after running label generation

**Solutions:**

1. **Check for LaTeX errors:**
   ```bash
   # Look in output_labels/temp/ for .log files
   cat output_labels/temp/label_combined.log
   ```

2. **Verify label.tex files exist:**
   ```bash
   find ~/Music/DiscogsLibrary -name "label.tex"
   ```

3. **Regenerate labels:**
   ```bash
   ./bin/main.sh --regenerate-labels --max 5
   ```

4. **Test with single release:**
   ```bash
   ./bin/sync.sh --release 123456 --labels
   ```

## Performance Issues

### Slow Processing

**Symptom:** Processing takes extremely long

**Solutions:**

1. **Use dev mode for testing:**
   ```bash
   ./bin/sync.sh --dev  # Limits to 10 releases
   ```

2. **Process in batches:**
   ```bash
   ./bin/sync.sh --max 50
   ```

3. **Skip analysis temporarily:**
   ```bash
   ./bin/main.sh --download-only
   ```

4. **Check system resources:**
   ```bash
   top         # Linux/macOS
   htop        # Better alternative
   ```

### High Memory Usage

**Symptom:** System becomes slow or crashes

**Solutions:**

1. **Process smaller batches:**
   ```bash
   ./bin/sync.sh --max 25
   ```

2. **Close other applications**

3. **Monitor memory:**
   ```bash
   free -h     # Linux
   vm_stat     # macOS
   ```

## Platform-Specific Issues

### Windows Path Issues

**Error:** Path-related errors on Windows

**Solutions:**

1. **Use forward slashes:**
   ```json
   {
     "LIBRARY_PATH": "C:/Users/John/Music/Discogs"
   }
   ```
   NOT: `"C:\\Users\\John\\Music\\Discogs"`

2. **Avoid spaces in paths** or ensure proper escaping

3. **Use short paths** (Windows has 260 character limit in some contexts)

### macOS Permission Prompts

**Issue:** Repeated permission prompts for Terminal

**Solution:**

Grant Full Disk Access to Terminal:
1. System Preferences → Security & Privacy
2. Privacy tab → Full Disk Access
3. Add Terminal.app

### Linux Snap/Flatpak Issues

**Issue:** Applications can't access files

**Solution:**

Install system packages directly (not via snap/flatpak):
```bash
sudo apt remove --purge ffmpeg-snap
sudo apt install ffmpeg
```

## Debugging Tips

### Enable Verbose Output

```bash
# Run scripts with error output visible
./bin/sync.sh --dev 2>&1 | tee debug.log
```

### Check Individual Components

```bash
# Test Discogs API access
python3 -c "import discogs_client; d = discogs_client.Client('test', user_token='YOUR_TOKEN'); print(d.identity())"

# Test FFmpeg
ffmpeg -version

# Test XeLaTeX
xelatex --version

# Test gnuplot
gnuplot --version

# Test Python imports
python3 -c "import essentia, yt_dlp, segno; print('All imports OK')"
```

### Validate Release Directory

```bash
# Check what's in a release directory
ls -la ~/Music/DiscogsLibrary/12345_Release_Name/

# Verify JSON files
python3 -c "import json; print(json.load(open('path/to/metadata.json')))"
```

### Test Individual Scripts

```bash
# Activate venv first
source venv/bin/activate

# Run with Python directly for better error messages
python3 scripts/sync.py --dev
python3 scripts/main.py --dryrun
python3 scripts/generate_labels.py --max 1
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs:**
   - Look for error messages in terminal output
   - Check LaTeX logs in `output_labels/temp/`

2. **Verify installation:**
   ```bash
   ./bin/sync.sh --dryrun
   ```

3. **Create a minimal test case:**
   ```bash
   ./bin/sync.sh --dev --release 123456
   ```

4. **Gather information:**
   - Operating system and version
   - Python version: `python3 --version`
   - Error messages (full stack trace)
   - Steps to reproduce

5. **Check existing issues:**
   - Look for similar problems in project documentation
   - Search issue tracker (if available)

## Preventive Measures

### Regular Maintenance

```bash
# Keep dependencies updated
pip install --upgrade -r requirements.txt

# Update yt-dlp regularly (changes frequently)
pip install --upgrade yt-dlp

# Clean up old temporary files
rm -rf output_labels/temp/*
```

### Backup Configuration

```bash
# Backup configuration
cp ~/.config/discogsDBLabelGen/discogs.env ~/discogs.env.backup

# Backup generated labels
cp -r output_labels ~/labels_backup_$(date +%Y%m%d)
```

### Test After Updates

```bash
# After any code changes
./bin/sync.sh --dryrun
./bin/sync.sh --dev --max 5
```

## See Also

- [Installation Guide](INSTALLATION.md)
- [Configuration Guide](CONFIGURATION.md)
- [Usage Guide](USAGE.md)