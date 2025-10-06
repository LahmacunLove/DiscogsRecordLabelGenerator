# Error Logging and Diagnostics

This document explains how to use the error logging and diagnostic features to troubleshoot issues during sync operations, particularly YouTube download problems.

## Overview

Every time you run `./bin/sync.sh`, the system automatically:
1. Tracks all errors that occur during the sync
2. Generates a detailed error summary report at the end
3. Saves logs to `~/.config/discogsDBLabelGen/logs/`

This helps you understand what went wrong and why certain downloads or operations failed.

## Log File Locations

### Daily Log File
**Location:** `~/.config/discogsDBLabelGen/logs/discogs_YYYYMMDD.log`

This file contains all log messages from the entire day, including:
- INFO messages about what the system is doing
- DEBUG messages with detailed technical information
- WARNING messages about potential issues
- ERROR messages about failures

**Example:** `discogs_20251003.log`

### Error Summary Reports
**Location:** `~/.config/discogsDBLabelGen/logs/sync_error_summary_YYYYMMDD_HHMMSS.log`

Generated after each sync operation completes (or is interrupted). Contains:
- Summary of all errors that occurred
- Categorized YouTube download errors
- Automatic diagnostics and analysis
- Recommended troubleshooting steps

**Example:** `sync_error_summary_20251003_154708.log`

## Understanding the Error Summary Report

### Report Structure

```
================================================================================
SYNC ERROR SUMMARY REPORT
================================================================================

Sync Start Time: 2025-10-03 15:47:08
Sync End Time:   2025-10-03 15:47:08
Duration:        0:00:00.291904

--------------------------------------------------------------------------------
SUMMARY
--------------------------------------------------------------------------------
Total YouTube Errors:  5
Total General Errors:  2
Total Errors:          7

--------------------------------------------------------------------------------
YOUTUBE DOWNLOAD ERRORS
--------------------------------------------------------------------------------

Error #1:
  Time:    2025-10-03T15:47:08.123456
  Message: Download failed for track A1 - no file found
  Release: 12345678
  Track:   A1
  URL:     https://www.youtube.com/watch?v=...

Error #2:
  Time:    2025-10-03T15:47:15.654321
  Message: Download error for track B2: HTTP Error 403: Forbidden
  Release: 87654321
  Track:   B2
  URL:     https://www.youtube.com/watch?v=...
  Exception: HTTP Error 403: Forbidden

--------------------------------------------------------------------------------
DIAGNOSTICS
--------------------------------------------------------------------------------

YouTube Error Analysis:
  - HTTP/Network errors:     2
  - No match found:          1
  - Download failed:         2
  - Other errors:            0

⚠️  HTTP/Network errors detected - possible causes:
   - Network connectivity issues
   - YouTube API rate limiting
   - Firewall/proxy blocking
   - yt-dlp needs updating: pip install -U yt-dlp

ℹ️  No YouTube matches found - possible causes:
   - Obscure/rare releases not on YouTube
   - Track titles don't match YouTube metadata
   - Region-restricted content

--------------------------------------------------------------------------------
RECOMMENDATIONS
--------------------------------------------------------------------------------

To investigate YouTube download issues:
  1. Check network connectivity: ping youtube.com
  2. Update yt-dlp: pip install -U yt-dlp
  3. Test yt-dlp directly: yt-dlp --verbose <youtube_url>
  4. Check if ffmpeg is installed: ffmpeg -version
  5. Review detailed logs at: /home/user/.config/discogsDBLabelGen/logs

================================================================================
Full logs available at: /home/user/.config/discogsDBLabelGen/logs/discogs_20251003.log
================================================================================
```

## Common YouTube Error Types

### 1. HTTP/Network Errors & Bot Detection

**Symptoms:**
- `HTTP Error 403: Forbidden`
- `HTTP Error 429: Too Many Requests`
- `Sign in to confirm you're not a bot`
- `Unable to download webpage`
- Network timeout errors

**Possible Causes:**
- **Bot Detection**: YouTube detects automated access (most common)
- **Rate Limiting**: YouTube is limiting your requests (too many downloads in short time)
- **Network Issues**: Internet connectivity problems or firewall blocking
- **Outdated yt-dlp**: YouTube changed their API and yt-dlp needs updating
- **Region Restrictions**: Content not available in your country

**Solutions:**

#### Best Solution: Use Browser Cookies (Bypasses Bot Detection)

This makes yt-dlp use your browser's authentication, so YouTube sees requests as coming from a legitimate logged-in user.

**Step 1: Update yt-dlp**
```bash
pip install -U yt-dlp
```

**Step 2: Configure browser cookies in your config file**

Edit `~/.config/discogsDBLabelGen/discogs.env` and add:

```json
{
  "DISCOGS_USER_TOKEN": "your_token_here",
  "LIBRARY_PATH": "/path/to/library",
  "YOUTUBE_COOKIES_BROWSER": "firefox"
}
```

Replace `"firefox"` with your browser:
- `"firefox"` - Mozilla Firefox
- `"chrome"` - Google Chrome
- `"chromium"` - Chromium
- `"edge"` - Microsoft Edge
- `"safari"` - Safari (macOS only)
- `"brave"` - Brave Browser
- `"opera"` - Opera

**Step 3: Make sure you're logged into YouTube in that browser**

Open your chosen browser and sign into YouTube.com. The sync tool will use those cookies automatically.

**Step 4: Run sync**
```bash
./bin/sync.sh --dev
```

You should see in the logs:
```
Using firefox cookies for YouTube authentication
```

#### Alternative Solutions (if cookies don't work)

1. **Wait and retry**: Rate limiting is often temporary (wait 5-10 minutes)
2. **Check internet connectivity**: `ping youtube.com`
3. **Try accessing YouTube URL in your browser**: Verify it's not a network issue
4. **Check VPN/proxy settings**: Some VPNs trigger bot detection
5. **Manual cookie export**: If auto-extraction fails, manually export cookies (advanced)

### 2. No YouTube Match Found

**Symptoms:**
- `No YouTube match for track A1`

**Possible Causes:**
- Track is not available on YouTube
- Track title doesn't match YouTube video metadata
- Very obscure or rare recordings
- Region-restricted content

**Solutions:**
1. Manually search YouTube for the track
2. Check if Bandcamp audio is available (preferred alternative)
3. Accept that some tracks won't have YouTube audio
4. The system will continue processing other tracks

### 3. Download Failed - No File Found

**Symptoms:**
- `Download failed for track A1 - no file found`

**Possible Causes:**
- Download appeared successful but file wasn't created
- FFmpeg postprocessing failed
- Disk space issues
- File permissions problems

**Solutions:**
1. Check disk space: `df -h`
2. Verify FFmpeg is installed: `ffmpeg -version`
3. Check file permissions in library directory
4. Try downloading the specific URL manually with yt-dlp

### 4. FFmpeg/Codec Issues

**Symptoms:**
- `Failed to extract audio`
- `Postprocessing failed`
- Errors mentioning Opus or codec conversion

**Possible Causes:**
- FFmpeg not installed or not in PATH
- FFmpeg version too old
- Audio codec not supported

**Solutions:**
1. Install/update FFmpeg:
   - Ubuntu/Debian: `sudo apt install ffmpeg`
   - macOS: `brew install ffmpeg`
2. Verify installation: `ffmpeg -version`
3. Ensure FFmpeg is in your PATH

### 5. secretstorage/Keyring Errors (Chrome/Chromium on Linux)

**Symptoms:**
- `ModuleNotFoundError: No module named 'secretstorage'`
- `Error accessing keyring`
- `DBus error` when using Chrome/Chromium
- Cookies extraction fails

**Possible Causes:**
- Chrome/Chromium stores cookies encrypted in system keyring
- yt-dlp needs `secretstorage` to decrypt them
- Missing system dependencies

**Solutions:**
1. Install secretstorage package:
   ```bash
   pip install secretstorage
   ```

2. If that fails, install system dependencies first:
   ```bash
   # Ubuntu/Debian
   sudo apt-get install libsecret-1-dev python3-secretstorage
   pip install secretstorage keyring
   
   # Fedora/RHEL
   sudo dnf install libsecret-devel python3-secretstorage
   pip install secretstorage keyring
   ```

3. **Easier alternative - Switch to Firefox:**
   ```bash
   # Edit config file
   nano ~/.config/discogsDBLabelGen/discogs.env
   
   # Change to:
   "YOUTUBE_COOKIES_BROWSER": "firefox"
   ```
   Firefox doesn't require secretstorage and is simpler to use on Linux.

## Viewing Error Logs

### View Latest Error Summary
```bash
cat ~/.config/discogsDBLabelGen/logs/sync_error_summary_*.log | tail -100
```

### View All Error Summaries
```bash
ls -lt ~/.config/discogsDBLabelGen/logs/sync_error_summary_*.log
```

### View Today's Full Log
```bash
cat ~/.config/discogsDBLabelGen/logs/discogs_$(date +%Y%m%d).log
```

### Search for Specific Errors
```bash
# Find all YouTube errors
grep -i "youtube" ~/.config/discogsDBLabelGen/logs/discogs_$(date +%Y%m%d).log

# Find all HTTP errors
grep -i "http error" ~/.config/discogsDBLabelGen/logs/discogs_$(date +%Y%m%d).log

# Find errors for specific release
grep "12345678" ~/.config/discogsDBLabelGen/logs/sync_error_summary_*.log
```

### Troubleshooting Workflow

When YouTube downloads aren't working:

1. **Configure browser cookies (if you see bot detection errors)**:
   ```bash
   # Edit config file
   nano ~/.config/discogsDBLabelGen/discogs.env
   
   # Add this line (choose your browser):
   "YOUTUBE_COOKIES_BROWSER": "firefox"
   
   # Make sure you're logged into YouTube in that browser
   ```

2. **Run sync and check the summary**:
   ```bash
   ./bin/sync.sh --dev
   # Check the error summary path printed at the end
   ```

3. **Review the error summary report**:
   - Look at the DIAGNOSTICS section to understand error patterns
   - Check the RECOMMENDATIONS for specific troubleshooting steps

4. **Test individual components**:
   ```bash
   # Test YouTube connectivity
   ping youtube.com
   
   # Test yt-dlp with browser cookies
   yt-dlp --cookies-from-browser firefox --verbose "https://www.youtube.com/watch?v=VIDEO_ID"
   
   # Test FFmpeg
   ffmpeg -version
   ```

5. **Update dependencies if needed**:
   ```bash
   pip install -U yt-dlp
   ```

6. **Check specific release details**:
   - Error summary includes Release ID and Track Position
   - Navigate to release folder: `~/Music/DiscogsLibrary/{release_id}_{title}/`
   - Check `yt_matches.json` for YouTube search results
   - Check `metadata.json` for track information

7. **Review full logs for context**:
   ```bash
   cat ~/.config/discogsDBLabelGen/logs/discogs_$(date +%Y%m%d).log | grep -A 5 -B 5 "ERROR"
   ```

## No Errors?

If the error summary shows:
```
Total YouTube Errors:  0
Total General Errors:  0
```

Then all operations completed successfully! The summary is generated for every sync to confirm everything worked.

## Technical Details

### Error Tracking Implementation

The error tracking system:
- Captures errors in real-time during sync operations
- Stores context (release ID, track position, URL, exception details)
- Automatically categorizes error types
- Generates summary report even if sync is interrupted (Ctrl+C)

### Log File Rotation

- Daily log files are created automatically
- Error summary files are created per sync operation
- Old log files are not automatically deleted (manual cleanup if needed)

### Privacy Note

Log files contain:
- Discogs release IDs (public data)
- YouTube URLs (public data)
- Error messages and timestamps
- **No personal information or API tokens are logged**

## Getting Help

If you're stuck after reviewing error logs:

1. Check the error summary DIAGNOSTICS section
2. Follow RECOMMENDATIONS in the report
3. Search GitHub issues for similar errors
4. Create a new issue with:
   - Error summary report content
   - Steps to reproduce
   - Your environment (OS, Python version)

---

**Related Documentation:**
- [QA.md](QA.md#error-logging-and-diagnostics) - Technical Q&A about error logging
- [INSTALLATION.md](INSTALLATION.md) - Dependency setup
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General troubleshooting guide