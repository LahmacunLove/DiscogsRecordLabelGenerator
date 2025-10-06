# YouTube Bot Detection Fix Guide

**Problem:** YouTube is blocking your requests with "Sign in to confirm you're not a bot"

**Solution:** Configure the tool to use your browser's cookies for authentication

---

## Quick Fix (5 minutes)

### Option A: Use Setup Script (Easiest)

If you're setting up for the first time or want to reconfigure:

```bash
./bin/setup.sh
```

The setup script will ask you about YouTube authentication and automatically configure browser cookies.

### Option B: Manual Configuration

### Step 1: Update yt-dlp

```bash
pip install -U yt-dlp
```

### Step 2: Edit your configuration file

```bash
nano ~/.config/discogsDBLabelGen/discogs.env
```

Add the `YOUTUBE_COOKIES_BROWSER` setting:

```json
{
  "DISCOGS_USER_TOKEN": "your_discogs_token",
  "LIBRARY_PATH": "/home/user/Music/DiscogsLibrary",
  "YOUTUBE_COOKIES_BROWSER": "firefox"
}
```

**Choose your browser:**
- `"firefox"` - Mozilla Firefox
- `"chrome"` - Google Chrome  
- `"chromium"` - Chromium
- `"edge"` - Microsoft Edge
- `"safari"` - Safari (macOS only)
- `"brave"` - Brave Browser
- `"opera"` - Opera

### Step 3: Sign into YouTube

Open your chosen browser and make sure you're **signed into YouTube.com**.

The tool will automatically use your browser's YouTube cookies.

### Step 4: Run sync

```bash
./bin/sync.sh --dev
```

You should see in the logs:
```
Using firefox cookies for YouTube authentication
```

### Step 5: Verify it's working

Check the error summary after sync completes:

```bash
# Find the latest error summary
ls -t ~/.config/discogsDBLabelGen/logs/sync_error_summary_*.log | head -1

# View it
cat $(ls -t ~/.config/discogsDBLabelGen/logs/sync_error_summary_*.log | head -1)
```

If bot detection errors are gone, you're all set! ✅

---

## Testing Individual Videos

Before running a full sync, test if the cookie method works:

```bash
# Get a YouTube URL from one of your releases
cat ~/Music/DiscogsLibrary/*/metadata.json | grep -o '"https://www.youtube.com/watch?v=[^"]*' | head -1

# Test downloading with cookies (replace VIDEO_ID)
yt-dlp --cookies-from-browser firefox "https://www.youtube.com/watch?v=VIDEO_ID"
```

If this works, your sync will work too.

---

## Troubleshooting

### "secretstorage" errors (Chrome/Chromium on Linux)

**Problem:** Error messages about `secretstorage`, `keyring`, or `DBus` when using Chrome/Chromium.

**This happens because:** Chrome/Chromium stores cookies encrypted in the system keyring on Linux, and yt-dlp needs `secretstorage` to decrypt them.

**Solution 1: Install secretstorage (Recommended)**
```bash
# Install Python package
pip install secretstorage

# If that doesn't work, install system dependencies first:
# Ubuntu/Debian:
sudo apt-get install libsecret-1-dev python3-secretstorage
pip install secretstorage keyring

# Fedora/RHEL:
sudo dnf install libsecret-devel python3-secretstorage
pip install secretstorage keyring
```

**Solution 2: Switch to Firefox (Easier)**

Firefox doesn't need `secretstorage`:
```bash
# Edit config file
nano ~/.config/discogsDBLabelGen/discogs.env

# Change to:
"YOUTUBE_COOKIES_BROWSER": "firefox"
```

Make sure you're signed into YouTube in Firefox, then run sync again.

### "Cookies not found" error

**Problem:** yt-dlp can't find your browser's cookies.

**Solutions:**
1. Make sure you're signed into YouTube in that browser
2. Close and reopen the browser
3. Try a different browser
4. Check that your browser profile is the default one

### Still getting bot detection

**Try these:**

1. **Clear YouTube cookies and sign in again**
   - Go to YouTube.com in your browser
   - Sign out completely
   - Clear cookies for youtube.com
   - Sign back in
   - Try sync again

2. **Use a different browser**
   - Some browser profiles work better than others
   - Try Chrome if Firefox doesn't work, or vice versa

3. **Wait before retrying**
   - If you made many requests, YouTube may have temporarily blocked your IP
   - Wait 10-15 minutes before trying again

4. **Check browser installation**
   ```bash
   # Make sure your browser is installed
   which firefox
   which google-chrome
   ```

### Permission errors accessing cookies

**Linux/macOS:**
```bash
# Make sure your user can access browser profile
ls -la ~/.mozilla/firefox/  # Firefox
ls -la ~/.config/google-chrome/  # Chrome
```

If you see permission errors, the browser profile may be owned by a different user.

### Manual cookie export (Advanced)

If automatic cookie extraction fails, you can manually export cookies:

1. **Install browser extension:**
   - Firefox: "cookies.txt" extension
   - Chrome: "Get cookies.txt" extension

2. **Export cookies:**
   - Visit youtube.com
   - Click the extension icon
   - Export cookies.txt

3. **Tell yt-dlp to use the file:**
   ```bash
   yt-dlp --cookies /path/to/cookies.txt "https://youtube.com/watch?v=VIDEO_ID"
   ```

4. **Configure in discogs.env:**
   ```json
   {
     "YOUTUBE_COOKIES_FILE": "/home/user/youtube_cookies.txt"
   }
   ```
   
   (Note: This requires additional code changes - contact maintainer if needed)

---

## Understanding What This Does

### Why does YouTube block bots?

YouTube uses bot detection to prevent:
- Automated scraping
- Mass downloading
- API abuse
- Copyright circumvention

Your legitimate use case (downloading audio for personal vinyl label generation) triggers these protections.

### How do cookies help?

When you sign into YouTube in your browser:
- Browser stores authentication cookies
- These cookies prove you're a real person
- yt-dlp uses these same cookies
- YouTube sees requests as coming from your logged-in browser session

**Security note:** Your cookies are only used locally. They're never sent anywhere except to YouTube.

### Why not use YouTube API?

YouTube's official API:
- Requires application registration
- Has strict rate limits
- Doesn't allow audio downloads
- More complex to set up

Browser cookies are simpler and work better for this use case.

---

## Configuration File Examples

**Note:** You can use `./bin/setup.sh` to configure these interactively instead of editing manually.

### Minimal configuration (just Discogs + cookies)
```json
{
  "DISCOGS_USER_TOKEN": "your_token_here",
  "LIBRARY_PATH": "~/Music/DiscogsLibrary",
  "YOUTUBE_COOKIES_BROWSER": "firefox"
}
```

### Full configuration (with Bandcamp + cookies)
```json
{
  "DISCOGS_USER_TOKEN": "your_token_here",
  "LIBRARY_PATH": "~/Music/DiscogsLibrary",
  "BANDCAMP_PATH": "~/Music/Bandcamp",
  "YOUTUBE_COOKIES_BROWSER": "chrome"
}
```

### Multiple browser attempt (tries Firefox, falls back to Chrome)
```json
{
  "DISCOGS_USER_TOKEN": "your_token_here",
  "LIBRARY_PATH": "~/Music/DiscogsLibrary",
  "YOUTUBE_COOKIES_BROWSER": "firefox"
}
```

If Firefox cookies don't work, manually change to `"chrome"` and retry.

---

## Checking if Cookies Are Working

After configuring cookies, run a test sync:

```bash
./bin/sync.sh --dev --max 3
```

Check the logs for these indicators:

**✅ Success indicators:**
```
Using firefox cookies for YouTube authentication
✓ Metadata fetched: Track Name
Downloaded: A1.opus
```

**❌ Still failing:**
```
Sign in to confirm you're not a bot
Failed to fetch metadata for all X YouTube videos
```

If still failing, try:
1. Different browser
2. Sign out and back into YouTube
3. Wait 10 minutes and retry

---

## Rate Limiting vs. Bot Detection

### Bot Detection (what you're seeing)
- Happens immediately on first request
- Error: "Sign in to confirm you're not a bot"
- **Fix:** Use browser cookies

### Rate Limiting (different issue)
- Happens after many successful requests
- Error: "HTTP Error 429: Too Many Requests"
- **Fix:** Wait and retry, or add delays between requests

If you're seeing **both** issues, fix bot detection first with cookies, then handle rate limiting by:
- Processing fewer releases at once (`--max 10`)
- Running sync less frequently
- Adding delays (requires code modification)

---

## Privacy & Security

### Is this safe?

**Yes.** Here's what happens:

1. yt-dlp reads cookies from your browser's local storage
2. Cookies are used only to authenticate with YouTube
3. No cookies are sent to third parties
4. No passwords are accessed or stored
5. Works exactly like using your browser manually

### What cookies are accessed?

Only YouTube authentication cookies:
- Session tokens
- Login state
- Preference settings

**Not accessed:**
- Passwords (stored separately, encrypted)
- Payment information
- Personal data from other sites

### Can I revoke access?

Yes, at any time:

1. Sign out of YouTube in your browser
2. Remove `YOUTUBE_COOKIES_BROWSER` from config
3. Clear browser cookies

---

## FAQ

### Q: Do I need to be logged into YouTube?
**A:** Yes, you must be signed into YouTube in the browser you specified.

### Q: Which browser should I use?
**A:** Firefox and Chrome work best. **Firefox is recommended on Linux** because it doesn't require `secretstorage`. Use whichever you normally use for YouTube.

### Q: What's the error about secretstorage?
**A:** Chrome/Chromium on Linux need the `secretstorage` Python package to decrypt cookies. Either install it (`pip install secretstorage`) or switch to Firefox which doesn't need it.

### Q: Do I need YouTube Premium?
**A:** No, a free YouTube account works fine.

### Q: How often do I need to re-configure?
**A:** Once configured, it works until you sign out of YouTube or clear browser cookies.

### Q: Does this violate YouTube's Terms of Service?
**A:** You're using yt-dlp for personal, non-commercial use of content you have legal access to. This is generally considered fair use, but check YouTube's current TOS.

### Q: Can I use multiple browsers?
**A:** Only one browser at a time. If one doesn't work, edit the config to try another.

### Q: What if I don't want to use cookies?
**A:** Without cookies, YouTube will block most requests. Alternatives:
- Accept that many downloads will fail
- Manually download audio and place in release folders
- Use Bandcamp audio instead (preferred when available)

---

## Related Documentation

- [ERROR_LOGGING.md](ERROR_LOGGING.md) - Understanding error reports
- [CONFIGURATION.md](CONFIGURATION.md) - Full configuration options
- [TROUBLESHOOTING.md](TROUBLESHOOTING.md) - General troubleshooting

---

**Still having issues?** Check the error summary after each sync run:
```bash
cat ~/.config/discogsDBLabelGen/logs/sync_error_summary_*.log | tail -100
```

The diagnostics section will tell you exactly what's wrong and how to fix it.