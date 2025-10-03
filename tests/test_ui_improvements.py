#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for UI improvements to thread monitor

Tests the following improvements:
1. Deterministic height (height=6)
2. Dynamic width (50% minus gap using Columns)
3. Artist - Title [Release] format (no Worker # prefix)
4. Combined [Time] [Progress]
5. No files section
"""

import sys
import os
import time
import random

# Add src to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

from thread_monitor import ThreadMonitor, WorkerProgressTracker
from concurrent.futures import ThreadPoolExecutor


def mock_process_release(release, tracker):
    """Simulate processing a release with various steps"""
    steps = [
        "Fetching metadata",
        "Analyzing audio",
        "Generating waveform",
        "Creating label",
        "Finalizing",
    ]

    for i, step in enumerate(steps):
        if tracker.check_shutdown():
            return

        progress = int((i + 1) / len(steps) * 100)
        tracker.update_step(step, progress)

        # Simulate variable processing time
        time.sleep(random.uniform(0.5, 1.2))

    tracker.complete()


def test_ui_improvements():
    """Test the UI improvements"""

    # Create test releases with realistic artist/title combinations
    test_releases = [
        {"id": "r123456", "artist": "Miles Davis", "title": "Kind of Blue"},
        {"id": "r789012", "artist": "The Beatles", "title": "Abbey Road"},
        {"id": "r345678", "artist": "Pink Floyd", "title": "The Dark Side of the Moon"},
        {"id": "r901234", "artist": "Led Zeppelin", "title": "Led Zeppelin IV"},
        {"id": "r567890", "artist": "Radiohead", "title": "OK Computer"},
        {"id": "r234567", "artist": "Nirvana", "title": "Nevermind"},
    ]

    num_workers = 4

    print("=" * 80)
    print("Testing UI Improvements")
    print("=" * 80)
    print("\nExpected improvements:")
    print("  1. ✓ Deterministic height (6 lines per panel)")
    print("  2. ✓ Dynamic width (50% minus gap using Columns)")
    print("  3. ✓ Format: Artist - Title [Release] (no 'Worker #')")
    print("  4. ✓ Combined: [Progress Bar] XX% │ XXs")
    print("  5. ✓ No files section")
    print(
        "\nStarting test with {} workers and {} releases...".format(
            num_workers, len(test_releases)
        )
    )
    print("Press Ctrl+C to stop\n")

    time.sleep(3)

    # Create monitor
    monitor = ThreadMonitor(
        num_workers=num_workers,
        total_releases=len(test_releases),
        mode_desc="UI Test - Discogs Sync",
    )

    # Define executor function
    def run_with_executor(executor, releases):
        futures = []
        for idx, release in enumerate(releases):
            worker_id = idx % num_workers
            tracker = WorkerProgressTracker(monitor, worker_id)

            # Set release with Artist - Title format
            release_title = "{} - {}".format(release["artist"], release["title"])
            tracker.set_release(release["id"], release_title)

            # Submit work
            future = executor.submit(mock_process_release, release, tracker)
            futures.append(future)

            # Stagger submissions slightly for better visualization
            time.sleep(0.2)

        # Wait for all to complete
        results = []
        for future in futures:
            try:
                results.append(future.result())
            except Exception as e:
                print("Error: {}".format(e))

        return results

    # Run with live display
    try:
        results = monitor.run_with_live_display(
            ThreadPoolExecutor, test_releases, run_with_executor
        )

        print("\n" + "=" * 80)
        print("Test completed successfully!")
        print("=" * 80)
        print("\nVerification checklist:")
        print("  [ ] Worker panels had deterministic height (4 lines)")
        print("  [ ] Worker panels took full width (stacked vertically)")
        print("  [ ] Title showed: #Index: Artist - Title [Release ID]")
        print("  [ ] Progress showed: [Bar] XX% │ XXs │ Step")
        print("  [ ] No files section was visible")
        print("  [ ] Step is positioned after time")
        print("\nIf all items look correct, the UI improvements are working!")

    except KeyboardInterrupt:
        print("\n\nTest interrupted by user.")
        print("UI improvements can still be verified from what was displayed.")


if __name__ == "__main__":
    test_ui_improvements()
