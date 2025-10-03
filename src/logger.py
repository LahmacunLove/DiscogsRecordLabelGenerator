#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Unified logging system for DiscogsRecordLabelGenerator

@author: ffx
"""

import logging
import sys
from pathlib import Path
from datetime import datetime
import json


class DiscogsLogger:
    def __init__(self, name="DiscogsRecordLabelGenerator", level=logging.INFO):
        self.logger = logging.getLogger(name)
        self.logger.setLevel(level)

        # Error tracking for summary reports
        self.youtube_errors = []
        self.general_errors = []
        self.sync_start_time = None

        # Verhindere doppelte Handler
        if not self.logger.handlers:
            self._setup_handlers()

    def _setup_handlers(self):
        """Setup console und file handlers"""

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)

        # File Handler (optional)
        log_dir = Path.home() / ".config" / "discogsDBLabelGen" / "logs"
        log_dir.mkdir(parents=True, exist_ok=True)

        self.log_dir = log_dir
        self.current_log_file = (
            log_dir / f"discogs_{datetime.now().strftime('%Y%m%d')}.log"
        )

        file_handler = logging.FileHandler(self.current_log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)

        # Formatter
        console_formatter = logging.Formatter("%(levelname)s │ %(message)s")
        file_formatter = logging.Formatter(
            "%(asctime)s │ %(name)s │ %(levelname)s │ %(message)s"
        )

        console_handler.setFormatter(console_formatter)
        file_handler.setFormatter(file_formatter)

        self.logger.addHandler(console_handler)
        self.logger.addHandler(file_handler)

    def info(self, message):
        self.logger.info(message)

    def debug(self, message):
        self.logger.debug(message)

    def warning(self, message):
        self.logger.warning(message)

    def error(self, message, error_type="general", context=None):
        """Log error and track it for summary report"""
        self.logger.error(message)

        # Track error for summary
        error_entry = {
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "context": context or {},
        }

        if error_type == "youtube":
            self.youtube_errors.append(error_entry)
        else:
            self.general_errors.append(error_entry)

    def success(self, message):
        self.logger.info(f"✅ {message}")

    def process(self, message):
        self.logger.info(f"🔄 {message}")

    def download(self, message):
        self.logger.info(f"⬇️  {message}")

    def analyze(self, message):
        self.logger.info(f"🎵 {message}")

    def match(self, message):
        self.logger.info(f"🔗 {message}")

    def separator(self, title=None):
        if title:
            self.logger.info(f"\n{'─' * 50}")
            self.logger.info(f"  {title}")
            self.logger.info(f"{'─' * 50}")
        else:
            self.logger.info(f"{'─' * 50}")

    def start_sync(self):
        """Mark the start of a sync operation"""
        self.sync_start_time = datetime.now()
        self.youtube_errors = []
        self.general_errors = []
        self.logger.info(
            f"Sync started at {self.sync_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def youtube_error(
        self, message, release_id=None, track_position=None, url=None, exception=None
    ):
        """Track YouTube-specific errors with context"""
        context = {}
        if release_id:
            context["release_id"] = release_id
        if track_position:
            context["track_position"] = track_position
        if url:
            context["url"] = url
        if exception:
            context["exception"] = str(exception)

        self.error(message, error_type="youtube", context=context)

    def generate_error_summary(self, output_file=None):
        """Generate error summary report and save to .log file"""
        if not output_file:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = self.log_dir / f"sync_error_summary_{timestamp}.log"

        summary_lines = []
        summary_lines.append("=" * 80)
        summary_lines.append("SYNC ERROR SUMMARY REPORT")
        summary_lines.append("=" * 80)
        summary_lines.append("")

        if self.sync_start_time:
            sync_duration = datetime.now() - self.sync_start_time
            summary_lines.append(
                f"Sync Start Time: {self.sync_start_time.strftime('%Y-%m-%d %H:%M:%S')}"
            )
            summary_lines.append(
                f"Sync End Time:   {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )
            summary_lines.append(f"Duration:        {sync_duration}")
        else:
            summary_lines.append(
                f"Report Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
            )

        summary_lines.append("")
        summary_lines.append("-" * 80)
        summary_lines.append("SUMMARY")
        summary_lines.append("-" * 80)
        summary_lines.append(f"Total YouTube Errors:  {len(self.youtube_errors)}")
        summary_lines.append(f"Total General Errors:  {len(self.general_errors)}")
        summary_lines.append(
            f"Total Errors:          {len(self.youtube_errors) + len(self.general_errors)}"
        )
        summary_lines.append("")

        # YouTube Errors Section
        if self.youtube_errors:
            summary_lines.append("-" * 80)
            summary_lines.append("YOUTUBE DOWNLOAD ERRORS")
            summary_lines.append("-" * 80)
            summary_lines.append("")

            for i, error in enumerate(self.youtube_errors, 1):
                summary_lines.append(f"Error #{i}:")
                summary_lines.append(f"  Time:    {error['timestamp']}")
                summary_lines.append(f"  Message: {error['message']}")

                if error.get("context"):
                    ctx = error["context"]
                    if ctx.get("release_id"):
                        summary_lines.append(f"  Release: {ctx['release_id']}")
                    if ctx.get("track_position"):
                        summary_lines.append(f"  Track:   {ctx['track_position']}")
                    if ctx.get("url"):
                        summary_lines.append(f"  URL:     {ctx['url']}")
                    if ctx.get("exception"):
                        summary_lines.append(f"  Exception: {ctx['exception']}")

                summary_lines.append("")
        else:
            summary_lines.append("-" * 80)
            summary_lines.append("YOUTUBE DOWNLOAD ERRORS: None")
            summary_lines.append("-" * 80)
            summary_lines.append("")

        # General Errors Section
        if self.general_errors:
            summary_lines.append("-" * 80)
            summary_lines.append("GENERAL ERRORS")
            summary_lines.append("-" * 80)
            summary_lines.append("")

            for i, error in enumerate(self.general_errors, 1):
                summary_lines.append(f"Error #{i}:")
                summary_lines.append(f"  Time:    {error['timestamp']}")
                summary_lines.append(f"  Message: {error['message']}")

                if error.get("context"):
                    summary_lines.append(
                        f"  Context: {json.dumps(error['context'], indent=4)}"
                    )

                summary_lines.append("")

        # Diagnostics Section
        summary_lines.append("-" * 80)
        summary_lines.append("DIAGNOSTICS")
        summary_lines.append("-" * 80)
        summary_lines.append("")

        if self.youtube_errors:
            # Analyze YouTube errors
            http_errors = [
                e
                for e in self.youtube_errors
                if "HTTP" in e["message"] or "network" in e["message"].lower()
            ]
            no_match_errors = [
                e for e in self.youtube_errors if "No YouTube match" in e["message"]
            ]
            download_failed = [
                e
                for e in self.youtube_errors
                if "Download failed" in e["message"] or "Download error" in e["message"]
            ]

            summary_lines.append("YouTube Error Analysis:")
            summary_lines.append(f"  - HTTP/Network errors:     {len(http_errors)}")
            summary_lines.append(f"  - No match found:          {len(no_match_errors)}")
            summary_lines.append(f"  - Download failed:         {len(download_failed)}")
            summary_lines.append(
                f"  - Other errors:            {len(self.youtube_errors) - len(http_errors) - len(no_match_errors) - len(download_failed)}"
            )
            summary_lines.append("")

            if http_errors:
                summary_lines.append(
                    "⚠️  HTTP/Network errors detected - possible causes:"
                )
                summary_lines.append("   - Network connectivity issues")
                summary_lines.append("   - YouTube API rate limiting")
                summary_lines.append("   - Firewall/proxy blocking")
                summary_lines.append(
                    "   - yt-dlp needs updating: pip install -U yt-dlp"
                )
                summary_lines.append("")

            if no_match_errors:
                summary_lines.append("ℹ️  No YouTube matches found - possible causes:")
                summary_lines.append("   - Obscure/rare releases not on YouTube")
                summary_lines.append("   - Track titles don't match YouTube metadata")
                summary_lines.append("   - Region-restricted content")
                summary_lines.append("")
        else:
            summary_lines.append("✅ No YouTube errors detected")
            summary_lines.append("")

        summary_lines.append("-" * 80)
        summary_lines.append("RECOMMENDATIONS")
        summary_lines.append("-" * 80)
        summary_lines.append("")

        if self.youtube_errors:
            summary_lines.append("To investigate YouTube download issues:")
            summary_lines.append("  1. Check network connectivity: ping youtube.com")
            summary_lines.append("  2. Update yt-dlp: pip install -U yt-dlp")
            summary_lines.append(
                "  3. Test yt-dlp directly: yt-dlp --verbose <youtube_url>"
            )
            summary_lines.append("  4. Check if ffmpeg is installed: ffmpeg -version")
            summary_lines.append("  5. Review detailed logs at: " + str(self.log_dir))
        else:
            summary_lines.append("✅ No issues detected")

        summary_lines.append("")
        summary_lines.append("=" * 80)
        summary_lines.append(f"Full logs available at: {self.current_log_file}")
        summary_lines.append("=" * 80)

        # Write to file
        output_content = "\n".join(summary_lines)
        with open(output_file, "w", encoding="utf-8") as f:
            f.write(output_content)

        # Also print summary to console
        self.logger.info("")
        self.logger.info("=" * 80)
        self.logger.info("ERROR SUMMARY REPORT GENERATED")
        self.logger.info("=" * 80)
        self.logger.info(f"Total YouTube Errors: {len(self.youtube_errors)}")
        self.logger.info(f"Total General Errors: {len(self.general_errors)}")
        self.logger.info(f"")
        self.logger.info(f"📄 Error summary saved to: {output_file}")
        self.logger.info(f"📋 Full logs available at: {self.current_log_file}")
        self.logger.info("=" * 80)

        return output_file


# Global logger instance
logger = DiscogsLogger()
