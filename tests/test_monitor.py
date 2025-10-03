#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script for ThreadMonitor visualization

Simulates the mirroring process to test the multi-threaded CLI display.

@author: ffx
"""

import sys
import os

# Add src to path (we're in tests/, so go up one level)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

import time
import random
import concurrent.futures
from thread_monitor import ThreadMonitor, WorkerProgressTracker


def mock_sync_release(release_id, tracker):
    """
    Mock function that simulates syncing a release with progress tracking
    """
    # Simulate different album titles
    titles = [
        "Kind of Blue",
        "The Dark Side of the Moon",
        "Abbey Road",
        "Thriller",
        "Rumours",
        "The Wall",
        "Led Zeppelin IV",
        "Back in Black",
        "Hotel California",
        "Nevermind",
    ]
    title = titles[release_id % len(titles)] + f" ({release_id})"

    # Set the release being processed
    tracker.set_release(release_id, title)

    # Simulate processing steps with varying durations
    steps = [
        ("Checking existing metadata", 5, 0.3),
        ("Fetching metadata from Discogs", 15, 0.8),
        ("Saving metadata", 25, 0.2),
        ("Downloading cover art", 35, 0.5),
        ("Searching YouTube", 45, 1.0),
        ("Downloading audio", 60, 1.5),
        ("Analyzing audio", 75, 1.2),
        ("Generating waveform", 85, 0.8),
        ("Creating QR code", 92, 0.4),
        ("Generating LaTeX label", 98, 0.3),
    ]

    for step_name, progress, duration in steps:
        # Check for shutdown
        if tracker.check_shutdown():
            tracker.error("Interrupted by user")
            return None

        tracker.update_step(step_name, progress)
        time.sleep(duration * random.uniform(0.7, 1.3))

        # Simulate file generation
        if progress >= 25:
            if "metadata" in step_name.lower():
                tracker.add_file(f"releases/{release_id}/metadata.json")
            elif "cover" in step_name.lower():
                tracker.add_file(f"releases/{release_id}/cover.jpg")
            elif "audio" in step_name.lower() and progress == 60:
                tracker.add_file(f"releases/{release_id}/track01.opus")
                tracker.add_file(f"releases/{release_id}/track02.opus")
            elif "waveform" in step_name.lower():
                tracker.add_file(f"releases/{release_id}/waveform.png")
            elif "qr" in step_name.lower():
                tracker.add_file(f"releases/{release_id}/qr_code.png")
            elif "label" in step_name.lower():
                tracker.add_file(f"releases/{release_id}/label.tex")

    # Simulate occasional errors
    if random.random() < 0.1:  # 10% chance of error
        tracker.error("Failed to download audio from YouTube")
        return None

    tracker.update_step("Completed", 100)
    return release_id


def test_thread_monitor(num_releases=20, num_workers=4):
    """
    Test the ThreadMonitor with simulated release processing
    """
    print(
        f"🎵 Testing ThreadMonitor with {num_releases} releases and {num_workers} workers"
    )
    print("Press Ctrl+C at any time to test graceful shutdown\n")

    # Create monitor
    monitor = ThreadMonitor(
        total_releases=num_releases, num_workers=num_workers, mode_desc="Test Sync Mode"
    )

    # Worker ID mapping (simulating thread-to-worker mapping)
    import threading

    worker_id_map = {}
    worker_id_lock = threading.Lock()
    next_worker_id = [0]

    def sync_with_monitoring(release_id):
        """Wrapper to add monitoring"""
        thread_id = threading.current_thread().ident
        with worker_id_lock:
            if thread_id not in worker_id_map:
                worker_id_map[thread_id] = next_worker_id[0]
                next_worker_id[0] += 1
            worker_id = worker_id_map[thread_id]

        tracker = WorkerProgressTracker(monitor, worker_id)

        try:
            if tracker.check_shutdown():
                return None

            result = mock_sync_release(release_id, tracker)

            if not tracker.check_shutdown():
                tracker.complete()
            return result

        except Exception as e:
            tracker.error(str(e))
            raise

    # Use Live display
    from rich.live import Live
    from rich.console import Console

    console = Console()
    releases = list(range(1, num_releases + 1))

    try:
        with Live(
            monitor._build_display(), console=console, refresh_per_second=2
        ) as live:
            with concurrent.futures.ThreadPoolExecutor(
                max_workers=num_workers
            ) as executor:
                futures = [
                    executor.submit(sync_with_monitoring, release_id)
                    for release_id in releases
                ]

                for future in concurrent.futures.as_completed(futures):
                    if monitor.is_shutdown_requested():
                        # Cancel remaining futures
                        for f in futures:
                            f.cancel()
                        break

                    try:
                        result = future.result()
                    except Exception as e:
                        pass  # Error already tracked

                    # Update display
                    live.update(monitor._build_display())

                # Final update
                time.sleep(0.5)
                live.update(monitor._build_display())

        # Print summary
        if monitor.is_shutdown_requested():
            console.print("\n[bold yellow]⚠️  Test shutdown completed[/]")
        else:
            console.print(f"\n[bold green]✅ Test completed successfully![/]")

        console.print(
            f"[bold]Completed:[/] {monitor.completed_count}/{monitor.total_releases}"
        )
        if monitor.error_count > 0:
            console.print(f"[bold red]Errors:[/] {monitor.error_count}")

    except KeyboardInterrupt:
        monitor._signal_handler(None, None)
        console.print("\n[bold yellow]⚠️  Test interrupted by user[/]")


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="Test ThreadMonitor visualization")
    parser.add_argument(
        "--releases",
        type=int,
        default=20,
        help="Number of releases to simulate (default: 20)",
    )
    parser.add_argument(
        "--workers", type=int, default=4, help="Number of worker threads (default: 4)"
    )

    args = parser.parse_args()

    test_thread_monitor(num_releases=args.releases, num_workers=args.workers)
