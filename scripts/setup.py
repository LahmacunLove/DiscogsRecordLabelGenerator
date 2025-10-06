#!/usr/bin/env python3
"""
DiscogsRecordLabelGenerator - Interactive Setup Script

This script helps users set up their configuration by:
1. Asking for their Discogs API token
2. Asking for their library path
3. Creating the configuration file
"""

import os
import sys
import json
from pathlib import Path


def print_header():
    """Print welcome header."""
    print("=" * 60)
    print("  DiscogsRecordLabelGenerator - Setup")
    print("=" * 60)
    print()


def print_section(title):
    """Print section divider."""
    print()
    print(f"── {title} " + "─" * (58 - len(title)))
    print()


def get_config_path():
    """Get the configuration file path."""
    return Path.home() / ".config" / "discogsDBLabelGen" / "discogs.env"


def check_existing_config():
    """Check if configuration already exists."""
    config_path = get_config_path()
    if config_path.exists():
        print(f"⚠️  Configuration file already exists at:")
        print(f"   {config_path}")
        print()
        response = input("Do you want to overwrite it? [y/N]: ").strip().lower()
        if response not in ["y", "yes"]:
            print()
            print("Setup cancelled. Existing configuration preserved.")
            return False
        print()
    return True


def get_discogs_token():
    """Prompt user for Discogs API token."""
    print_section("Discogs API Token")
    print("You need a personal access token from Discogs.")
    print()
    print("To get your token:")
    print("  1. Go to: https://www.discogs.com/settings/developers")
    print("  2. Click 'Generate new token'")
    print("  3. Copy the token")
    print()

    while True:
        token = input("Enter your Discogs token: ").strip()
        if not token:
            print("❌ Token cannot be empty. Please try again.")
            print()
            continue

        if len(token) < 20:
            print("⚠️  Warning: Token seems too short. Are you sure this is correct?")
            response = input("Continue anyway? [y/N]: ").strip().lower()
            if response not in ["y", "yes"]:
                print()
                continue

        return token


def get_library_path():
    """Prompt user for library path."""
    print_section("Library Path")
    print("This is where the application will store:")
    print("  • Downloaded metadata")
    print("  • Audio files")
    print("  • Analysis data")
    print("  • Generated labels")
    print()
    print("Each release will have its own subdirectory.")
    print()

    # Suggest a default path
    default_path = str(Path.home() / "Music" / "DiscogsLibrary")
    print(f"Suggested path: {default_path}")
    print()

    while True:
        path_input = input(f"Enter library path [{default_path}]: ").strip()

        # Use default if empty
        if not path_input:
            path_input = default_path

        # Expand ~ to home directory
        path = Path(path_input).expanduser()

        # Check if path exists
        if path.exists():
            if not path.is_dir():
                print(f"❌ Error: {path} exists but is not a directory.")
                print()
                continue
            print(f"✅ Directory exists: {path}")
        else:
            print(f"📁 Directory does not exist: {path}")
            response = input("Create it now? [Y/n]: ").strip().lower()
            if response in ["n", "no"]:
                print()
                continue

            try:
                path.mkdir(parents=True, exist_ok=True)
                print(f"✅ Created directory: {path}")
            except Exception as e:
                print(f"❌ Error creating directory: {e}")
                print()
                continue

        # Check if directory is writable
        if not os.access(path, os.W_OK):
            print(f"❌ Error: No write permission for {path}")
            print()
            continue

        return str(path)


def get_youtube_cookies_browser():
    """Prompt user for YouTube cookies browser configuration."""
    print_section("YouTube Authentication (Optional)")
    print(
        "YouTube often blocks automated requests with 'Sign in to confirm you're not a bot'."
    )
    print()
    print(
        "To bypass this, we can use cookies from your browser where you're signed into YouTube."
    )
    print()
    print("Supported browsers:")
    print("  • firefox")
    print("  • chrome")
    print("  • chromium")
    print("  • edge")
    print("  • brave")
    print("  • opera")
    print("  • safari (macOS only)")
    print()
    print("⚠️  Requirements:")
    print("  1. You must be signed into YouTube in the browser you choose")
    print("  2. yt-dlp must be up to date: pip install -U yt-dlp")
    print()

    while True:
        browser = input("Enter browser name (or press Enter to skip): ").strip().lower()

        # Allow skipping
        if not browser:
            print(
                "⏭️  Skipping YouTube authentication (you may see bot detection errors)"
            )
            return None

        # Validate browser choice
        valid_browsers = [
            "firefox",
            "chrome",
            "chromium",
            "edge",
            "brave",
            "opera",
            "safari",
        ]
        if browser not in valid_browsers:
            print(
                f"❌ Invalid browser. Please choose from: {', '.join(valid_browsers)}"
            )
            print()
            continue

        # Confirm
        print(f"✅ Will use cookies from: {browser}")
        print()
        print(f"⚠️  Make sure you're signed into YouTube in {browser.title()}!")
        response = input("Is this correct? [Y/n]: ").strip().lower()
        if response in ["n", "no"]:
            print()
            continue

        return browser


def create_config_file(token, library_path, youtube_cookies_browser=None):
    """Create the configuration file."""
    print_section("Creating Configuration")

    config_path = get_config_path()
    config_dir = config_path.parent

    # Create config directory if it doesn't exist
    try:
        config_dir.mkdir(parents=True, exist_ok=True)
        print(f"✅ Config directory ready: {config_dir}")
    except Exception as e:
        print(f"❌ Error creating config directory: {e}")
        return False

    # Create configuration data
    config_data = {"DISCOGS_USER_TOKEN": token, "LIBRARY_PATH": library_path}

    # Add YouTube cookies browser if configured
    if youtube_cookies_browser:
        config_data["YOUTUBE_COOKIES_BROWSER"] = youtube_cookies_browser

    # Write configuration file
    try:
        with open(config_path, "w") as f:
            json.dump(config_data, f, indent=2)
        print(f"✅ Configuration saved: {config_path}")
        return True
    except Exception as e:
        print(f"❌ Error writing config file: {e}")
        return False


def test_configuration():
    """Test if the configuration can be loaded."""
    print_section("Testing Configuration")

    try:
        # Try to import and load config
        sys.path.insert(0, os.path.join(os.path.dirname(__file__), "src"))
        from config import load_config

        config = load_config()
        print("✅ Configuration loaded successfully!")
        print(f"   Library path: {config['LIBRARY_PATH']}")
        print(f"   Token: {'*' * 20}{config['DISCOGS_USER_TOKEN'][-10:]}")
        return True
    except Exception as e:
        print(f"⚠️  Warning: Could not test configuration: {e}")
        print("   This might be okay if dependencies aren't installed yet.")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print_section("Next Steps")
    print("Configuration complete! Here's what to do next:")
    print()
    print("1. Install dependencies (if not done yet):")
    print("   python3 -m venv venv")
    print("   source venv/bin/activate")
    print("   pip install -r requirements.txt")
    print()
    print("2. Run the application:")
    print("   ./run.sh --dev          # Test with first 10 releases")
    print("   ./run.sh                # Full collection sync")
    print("   python3 sync.py --help  # See all CLI options")
    print()
    print("3. For help:")
    print("   ./run.sh --help")
    print()


def main():
    """Main setup function."""
    try:
        print_header()

        # Check for existing config
        if not check_existing_config():
            sys.exit(0)

        # Get configuration from user
        token = get_discogs_token()
        library_path = get_library_path()
        youtube_cookies_browser = get_youtube_cookies_browser()

        # Create configuration file
        if not create_config_file(token, library_path, youtube_cookies_browser):
            print()
            print("❌ Setup failed. Please try again.")
            sys.exit(1)

        # Test configuration
        test_configuration()

        # Show next steps
        print_next_steps()

        print("=" * 60)
        print("  Setup completed successfully! 🎉")
        print("=" * 60)
        print()

    except KeyboardInterrupt:
        print()
        print()
        print("Setup cancelled by user.")
        sys.exit(1)
    except Exception as e:
        print()
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
