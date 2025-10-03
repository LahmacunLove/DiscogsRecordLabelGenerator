# Configuration Guide

This guide covers all configuration options for DiscogsRecordLabelGenerator.

## Quick Configuration

The easiest way to configure the application is using the interactive setup:

```bash
./bin/setup.sh
```

This wizard will guide you through all required settings.

## Configuration File

Configuration is stored in JSON format at:

```
~/.config/discogsDBLabelGen/discogs.env
```

### Required Fields

```json
{
  "DISCOGS_USER_TOKEN": "YOUR_DISCOGS_API_TOKEN",
  "LIBRARY_PATH": "/path/to/your/music/library"
}
```

#### DISCOGS_USER_TOKEN

Your personal access token from Discogs.

**How to get it:**
1. Log in to [Discogs](https://www.discogs.com)
2. Go to [Developer Settings](https://www.discogs.com/settings/developers)
3. Click "Generate new token"
4. Copy the token (it looks like: `AbCdEf1234567890...`)
5. Keep it secure - treat it like a password

**Security note:** Never commit this token to version control or share it publicly.

#### LIBRARY_PATH

The directory where the application stores all data:
- Downloaded metadata from Discogs
- Audio files from YouTube
- Analysis results (BPM, key, spectrograms)
- Generated waveforms
- QR codes
- LaTeX label snippets

Each release gets its own subdirectory.

**Example paths:**
- Linux/macOS: `/home/username/Music/DiscogsLibrary`
- Windows: `C:/Users/username/Music/DiscogsLibrary`

**Note:** Use forward slashes (`/`) in paths, even on Windows.

## Configuration Methods

### Method 1: Interactive Setup (Recommended)

```bash
./bin/setup.sh
```

Advantages:
- Step-by-step guidance
- Validates your token
- Creates directories automatically
- Tests configuration before saving

### Method 2: CLI Configuration

```bash
./bin/sync.sh --token YOUR_TOKEN --library ~/Music/Discogs --configure
```

This saves the configuration for future use.

### Method 3: Manual Configuration

Create the configuration file manually:

```bash
# Create directory
mkdir -p ~/.config/discogsDBLabelGen

# Create configuration file
cat > ~/.config/discogsDBLabelGen/discogs.env << 'EOF'
{
  "DISCOGS_USER_TOKEN": "YOUR_ACTUAL_TOKEN_HERE",
  "LIBRARY_PATH": "/home/username/Music/DiscogsLibrary"
}
EOF
```

Replace the placeholder values with your actual token and desired path.

## Configuration Location

### Linux/macOS

Default: `~/.config/discogsDBLabelGen/discogs.env`

Full path: `/home/username/.config/discogsDBLabelGen/discogs.env`

### Windows

Default: `%USERPROFILE%\.config\discogsDBLabelGen\discogs.env`

Full path: `C:\Users\username\.config\discogsDBLabelGen\discogs.env`

## Environment Variables

You can override configuration temporarily using environment variables:

```bash
DISCOGS_USER_TOKEN=xyz789 LIBRARY_PATH=/tmp/test ./bin/sync.sh --dev
```

This doesn't modify your saved configuration.

## Verifying Configuration

### Test with Dry Run

```bash
./bin/sync.sh --dryrun
```

This verifies:
- Configuration file exists and is valid
- Token is readable (doesn't test API access)
- Library path is accessible

### Test API Access

```bash
./bin/sync.sh --dev
```

This makes actual API calls and verifies your token works.

## Configuration File Format

The configuration file must be valid JSON:

```json
{
  "DISCOGS_USER_TOKEN": "AbCdEf1234567890ABCDEFGH",
  "LIBRARY_PATH": "/home/user/Music/DiscogsLibrary"
}
```

**Important:**
- Use double quotes, not single quotes
- No trailing commas
- Paths can use `$HOME` or `~` for home directory (expanded at runtime)

## Advanced Configuration

### Path Expansion

The library path supports these expansions:

```json
{
  "LIBRARY_PATH": "~/Music/Discogs"           // Expands ~ to home directory
}
```

```json
{
  "LIBRARY_PATH": "$HOME/Music/Discogs"       // Expands $HOME variable
}
```

```json
{
  "LIBRARY_PATH": "/absolute/path/to/library" // Absolute path (no expansion)
}
```

### Multiple Configurations

You can maintain multiple configurations for different use cases:

```bash
# Production configuration
cp ~/.config/discogsDBLabelGen/discogs.env ~/.config/discogsDBLabelGen/discogs.env.prod

# Test configuration
cat > ~/.config/discogsDBLabelGen/discogs.env << 'EOF'
{
  "DISCOGS_USER_TOKEN": "TEST_TOKEN",
  "LIBRARY_PATH": "/tmp/test_library"
}
EOF

# Run tests
./bin/sync.sh --dev

# Restore production
cp ~/.config/discogsDBLabelGen/discogs.env.prod ~/.config/discogsDBLabelGen/discogs.env
```

### Per-Project Configuration

While the default location is in your home directory, you can specify configuration via environment:

```bash
# Set custom config path
export DISCOGS_CONFIG_PATH=/path/to/custom/config.json
./bin/sync.sh --dev
```

(Note: This requires modifying the scripts to read `DISCOGS_CONFIG_PATH`)

## Security Best Practices

### Token Security

1. **Never commit tokens to git:**
   ```bash
   # Already in .gitignore, but verify:
   git check-ignore ~/.config/discogsDBLabelGen/discogs.env
   ```

2. **Use restrictive file permissions:**
   ```bash
   chmod 600 ~/.config/discogsDBLabelGen/discogs.env
   ```

3. **Revoke compromised tokens immediately:**
   - Go to [Discogs Developer Settings](https://www.discogs.com/settings/developers)
   - Delete the compromised token
   - Generate a new one
   - Update your configuration

### Shared Systems

On shared systems, ensure your configuration directory is private:

```bash
chmod 700 ~/.config/discogsDBLabelGen
chmod 600 ~/.config/discogsDBLabelGen/discogs.env
```

## Troubleshooting Configuration

### Configuration File Not Found

**Error:** `Configuration file not found`

**Solution:** Run `./bin/setup.sh` or create the file manually.

### Invalid JSON

**Error:** `JSON decode error`

**Solution:** Validate your JSON:
```bash
python3 -c "import json; print(json.load(open('~/.config/discogsDBLabelGen/discogs.env')))"
```

Common issues:
- Missing quotes around strings
- Trailing commas
- Single quotes instead of double quotes

### Invalid Token

**Error:** `401 Unauthorized` or `Invalid token`

**Solutions:**
1. Verify token is correct (copy-paste from Discogs)
2. Check for extra spaces or newlines
3. Ensure token hasn't been revoked
4. Generate a new token if needed

### Library Path Issues

**Error:** `Permission denied` or `Directory not found`

**Solutions:**
```bash
# Check if directory exists
ls -la /path/to/library

# Create if missing
mkdir -p /path/to/library

# Check permissions
ls -ld /path/to/library

# Fix permissions
chmod u+w /path/to/library
```

### Path with Spaces

Paths with spaces should work but be careful with shell escaping:

```json
{
  "LIBRARY_PATH": "/home/user/My Music/Discogs Library"
}
```

No special escaping needed in JSON.

## Configuration Examples

### Minimal Configuration

```json
{
  "DISCOGS_USER_TOKEN": "AbCdEf1234567890",
  "LIBRARY_PATH": "/home/user/Music/Discogs"
}
```

### Windows Configuration

```json
{
  "DISCOGS_USER_TOKEN": "AbCdEf1234567890",
  "LIBRARY_PATH": "C:/Users/John/Music/DiscogsLibrary"
}
```

### macOS Configuration

```json
{
  "DISCOGS_USER_TOKEN": "AbCdEf1234567890",
  "LIBRARY_PATH": "/Users/john/Music/Discogs"
}
```

### Linux Configuration

```json
{
  "DISCOGS_USER_TOKEN": "AbCdEf1234567890",
  "LIBRARY_PATH": "/home/john/Music/Discogs"
}
```

### Network Storage

```json
{
  "DISCOGS_USER_TOKEN": "AbCdEf1234567890",
  "LIBRARY_PATH": "/mnt/nas/Music/Discogs"
}
```

## Migrating Configuration

### From Old Location

If you have configuration in an old location:

```bash
# Copy to new location
mkdir -p ~/.config/discogsDBLabelGen
cp /old/path/config.json ~/.config/discogsDBLabelGen/discogs.env
```

### Changing Library Path

To move your library to a new location:

```bash
# 1. Copy/move library data
mv /old/library/path /new/library/path

# 2. Update configuration
# Edit ~/.config/discogsDBLabelGen/discogs.env
# Change LIBRARY_PATH to new location

# 3. Verify
./bin/sync.sh --dryrun
```

## See Also

- [Installation Guide](INSTALLATION.md)
- [Usage Guide](USAGE.md)
- [Troubleshooting](TROUBLESHOOTING.md)