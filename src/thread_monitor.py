#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Multi-threaded CLI Monitor for Discogs Library Sync

Provides real-time visualization of parallel worker threads with:
- Per-worker progress tracking
- Current step display
- Generated files list
- Graceful Ctrl+C handling

@author: ffx
"""

import sys
import os
import time
import threading
import logging
from collections import defaultdict, deque
from datetime import datetime
from rich.console import Console
from rich.live import Live
from rich.table import Table
from rich.panel import Panel
from rich.layout import Layout
from rich.text import Text
from rich.columns import Columns
from rich.console import Group
from rich.progress import (
    Progress,
    SpinnerColumn,
    BarColumn,
    TextColumn,
    TimeElapsedColumn,
)
import signal


class WorkerState:
    """Tracks state of a single worker thread"""

    def __init__(self, worker_id):
        self.worker_id = worker_id
        self.release_id = None
        self.release_title = "Idle"
        self.current_step = "Waiting..."
        self.progress_percent = 0
        self.files_generated = []
        self.start_time = None
        self.status = "idle"  # idle, working, completed, error
        self.error_message = None
        self.total_processed = 0
        self.overall_index = None  # Overall position in import order

    def update(
        self,
        release_id=None,
        release_title=None,
        step=None,
        progress=None,
        file_generated=None,
        status=None,
        error=None,
        overall_index=None,
    ):
        """Update worker state"""
        if release_id is not None:
            self.release_id = release_id
            if self.start_time is None:
                self.start_time = time.time()
        if release_title is not None:
            self.release_title = release_title
        if overall_index is not None:
            self.overall_index = overall_index
        if step is not None:
            self.current_step = step
        if progress is not None:
            self.progress_percent = min(100, max(0, progress))
        if file_generated is not None:
            self.files_generated.append(file_generated)
        if status is not None:
            self.status = status
            if status == "completed":
                self.total_processed += 1
                self.files_generated.clear()
                self.progress_percent = 0
                self.current_step = "Waiting..."
                self.release_title = "Idle"
                self.start_time = None
                # Keep overall_index for display until next release starts
        if error is not None:
            self.error_message = error
            self.status = "error"

    def get_elapsed_time(self):
        """Get elapsed time for current task"""
        if self.start_time:
            return time.time() - self.start_time
        return 0


class ThreadMonitor:
    """Monitors and visualizes parallel worker threads"""

    def __init__(self, total_releases, num_workers, mode_desc="Processing"):
        self.console = Console()
        self.total_releases = total_releases
        self.num_workers = num_workers
        self.mode_desc = mode_desc

        # Worker state tracking
        self.workers = {i: WorkerState(i) for i in range(num_workers)}
        self.lock = threading.Lock()

        # Overall progress
        self.completed_count = 0
        self.error_count = 0
        self.start_time = time.time()
        self.next_overall_index = 1  # Track next index for releases

        # Log buffer for capturing messages (last 6 messages)
        self.log_buffer = deque(maxlen=6)
        self.log_handler = None

        # Stderr redirection to suppress Essentia C++ output
        self.stderr_fd_backup = None
        self.devnull_fd = None

        # Shutdown handling
        self.shutdown_requested = False
        self.shutdown_event = threading.Event()

        # Setup signal handler for Ctrl+C
        signal.signal(signal.SIGINT, self._signal_handler)

    def _signal_handler(self, signum, frame):
        """Handle Ctrl+C gracefully"""
        self.console.print(
            "\n[bold yellow]⚠️  Ctrl+C detected - shutting down workers gracefully...[/]"
        )
        self.shutdown_requested = True
        self.shutdown_event.set()

    def is_shutdown_requested(self):
        """Check if shutdown has been requested"""
        return self.shutdown_requested

    def update_worker(self, worker_id, **kwargs):
        """Update state for a specific worker"""
        with self.lock:
            if worker_id in self.workers:
                # Assign overall index when starting new work (new release_id)
                if kwargs.get("release_id") is not None:
                    current_release = self.workers[worker_id].release_id
                    new_release = kwargs.get("release_id")
                    # Only assign new index if this is a different release
                    if current_release != new_release:
                        kwargs["overall_index"] = self.next_overall_index
                        self.next_overall_index += 1

                self.workers[worker_id].update(**kwargs)

                # Update overall counters
                if kwargs.get("status") == "completed":
                    self.completed_count += 1
                elif kwargs.get("status") == "error":
                    self.error_count += 1

    def add_log_message(self, message):
        """Add a log message to the buffer"""
        with self.lock:
            timestamp = datetime.now().strftime("%H:%M:%S")
            self.log_buffer.append(f"[dim]{timestamp}[/dim] {message}")

    def install_log_handler(self):
        """Install a custom log handler to capture messages from all loggers"""
        from logger import logger as discogs_logger

        class BufferHandler(logging.Handler):
            def __init__(self, monitor):
                super().__init__()
                self.monitor = monitor

            def emit(self, record):
                try:
                    msg = self.format(record)
                    # Strip various logger prefixes
                    if " │ " in msg:
                        msg = msg.split(" │ ", 1)[1]
                    elif msg.startswith("["):
                        # Handle [   INFO   ] style prefixes from Essentia
                        parts = msg.split("]", 1)
                        if len(parts) > 1:
                            msg = parts[1].strip()
                    self.monitor.add_log_message(msg)
                except Exception:
                    pass

        self.log_handler = BufferHandler(self)
        self.log_handler.setLevel(logging.INFO)

        # Add to BOTH the discogs logger AND the root logger to catch all messages
        discogs_logger.logger.addHandler(self.log_handler)
        logging.root.addHandler(self.log_handler)

        # Suppress console output by removing console handlers temporarily
        self.original_handlers = []
        self.original_root_handlers = []

        # Remove console handlers from discogs logger
        for handler in discogs_logger.logger.handlers[:]:
            if (
                isinstance(handler, logging.StreamHandler)
                and handler.stream == sys.stdout
            ):
                self.original_handlers.append(handler)
                discogs_logger.logger.removeHandler(handler)

        # Remove console handlers from root logger
        for handler in logging.root.handlers[:]:
            if isinstance(handler, logging.StreamHandler):
                self.original_root_handlers.append(handler)
                logging.root.removeHandler(handler)

        # Redirect stderr at the file descriptor level to suppress Essentia C++ output
        # This prevents [   INFO   ] messages from breaking the UI
        try:
            sys.stderr.flush()
            self.stderr_fd_backup = os.dup(2)  # Backup stderr file descriptor
            self.devnull_fd = os.open(os.devnull, os.O_WRONLY)
            os.dup2(self.devnull_fd, 2)  # Redirect stderr to /dev/null
        except Exception as e:
            # If redirection fails, continue without it
            pass

    def remove_log_handler(self):
        """Remove the custom log handler and restore original handlers"""
        from logger import logger as discogs_logger

        # Restore stderr at the file descriptor level
        if self.stderr_fd_backup is not None:
            try:
                sys.stderr.flush()
                os.dup2(self.stderr_fd_backup, 2)  # Restore original stderr
                os.close(self.stderr_fd_backup)
                if self.devnull_fd is not None:
                    os.close(self.devnull_fd)
            except Exception:
                pass
            self.stderr_fd_backup = None
            self.devnull_fd = None

        if self.log_handler:
            # Remove from both loggers
            discogs_logger.logger.removeHandler(self.log_handler)
            logging.root.removeHandler(self.log_handler)
            self.log_handler = None

        # Restore original console handlers to discogs logger
        for handler in self.original_handlers:
            discogs_logger.logger.addHandler(handler)
        self.original_handlers = []

        # Restore original console handlers to root logger
        for handler in self.original_root_handlers:
            logging.root.addHandler(handler)
        self.original_root_handlers = []

    def _build_display(self):
        """Build the display layout"""
        layout = Layout()

        # Header with overall progress, workers, logs, and footer
        layout.split_column(
            Layout(name="header", size=5),
            Layout(name="workers", ratio=1),
            Layout(name="logs", size=6),
            Layout(name="footer", size=3),
        )

        # Header panel
        elapsed = time.time() - self.start_time
        elapsed_str = f"{int(elapsed // 60)}m {int(elapsed % 60)}s"

        with self.lock:
            progress_pct = (
                (self.completed_count / self.total_releases * 100)
                if self.total_releases > 0
                else 0
            )

            header_text = Text()
            header_text.append(f"🎵 {self.mode_desc}\n", style="bold cyan")
            header_text.append(
                f"Progress: {self.completed_count}/{self.total_releases} ", style="bold"
            )
            header_text.append(f"({progress_pct:.1f}%) ", style="bold green")
            header_text.append(
                f"│ Errors: {self.error_count} ",
                style="bold red" if self.error_count > 0 else "dim",
            )
            header_text.append(f"│ Workers: {self.num_workers} ", style="bold blue")
            header_text.append(f"│ Time: {elapsed_str}", style="bold yellow")

            if self.shutdown_requested:
                header_text.append(
                    "\n⚠️  SHUTDOWN IN PROGRESS...", style="bold yellow blink"
                )

        layout["header"].update(Panel(header_text, border_style="cyan"))

        # Worker table with all workers as rows
        worker_table = Table(
            show_header=True,
            header_style="bold cyan",
            border_style="dim",
            expand=True,
        )
        worker_table.add_column("", width=2, no_wrap=True)  # Status icon
        worker_table.add_column("#", width=4, style="yellow", no_wrap=True)
        worker_table.add_column("Release", width=35, style="white", no_wrap=True)
        worker_table.add_column("Progress", width=15, style="green", no_wrap=True)
        worker_table.add_column("Time", width=5, style="yellow", no_wrap=True)
        worker_table.add_column("Step", width=18, style="cyan", no_wrap=True)

        with self.lock:
            for worker_id in sorted(self.workers.keys()):
                worker = self.workers[worker_id]
                self._add_worker_row(worker_table, worker)

        layout["workers"].update(worker_table)

        # Log panel with recent messages
        with self.lock:
            log_text = Text()
            if self.log_buffer:
                log_text.append("📋 Recent Activity:\n", style="bold cyan")
                for log_msg in self.log_buffer:
                    log_text.append(log_msg + "\n")
            else:
                log_text.append("📋 Recent Activity:\n", style="bold cyan")
                log_text.append("Waiting for activity...", style="dim")

        layout["logs"].update(Panel(log_text, border_style="blue"))

        # Footer with instructions
        footer_text = Text()
        footer_text.append("Press ", style="dim")
        footer_text.append("Ctrl+C", style="bold red")
        footer_text.append(" to stop gracefully", style="dim")
        layout["footer"].update(Panel(footer_text, border_style="dim"))

        return layout

    def _add_worker_row(self, table, worker):
        """Add a worker row to the table"""
        # Status indicator
        status_icons = {"idle": "⚪", "working": "🟢", "completed": "✅", "error": "🔴"}
        status_icon = status_icons.get(worker.status, "⚪")

        # Index column - show overall index if working, otherwise worker ID
        if worker.status == "working" and worker.overall_index is not None:
            index_text = f"#{worker.overall_index}"
        else:
            index_text = f"#{worker.worker_id}"

        # Release column
        if worker.status == "working":
            title_display = (
                worker.release_title[:32] + ".."
                if len(worker.release_title) > 32
                else worker.release_title
            )
            release_text = f"{title_display} [{worker.release_id}]"
        elif worker.status == "error":
            release_text = f"Error: {worker.release_id}"
        else:
            release_text = "Idle"

        # Progress column (bar with percentage)
        if worker.status == "working":
            bar_width = 10
            filled = int(worker.progress_percent / 100 * bar_width)
            bar = "█" * filled + "░" * (bar_width - filled)
            progress_text = f"[{bar}] {worker.progress_percent:3.0f}%"
        elif worker.status == "error":
            progress_text = "Error"
        else:
            progress_text = "—"

        # Time column
        if worker.status == "working":
            elapsed = worker.get_elapsed_time()
            time_text = f"{int(elapsed)}s"
        else:
            time_text = "—"

        # Step column
        if worker.status == "working":
            step_display = (
                worker.current_step[:16] + ".."
                if len(worker.current_step) > 16
                else worker.current_step
            )
            step_text = step_display
        elif worker.status == "error" and worker.error_message:
            error_display = (
                worker.error_message[:16] + ".."
                if len(worker.error_message) > 16
                else worker.error_message
            )
            step_text = f"❌ {error_display}"
        else:
            step_text = "Waiting..."

        # Add the row
        table.add_row(
            status_icon, index_text, release_text, progress_text, time_text, step_text
        )

    def run_with_live_display(
        self, executor_func, releases, process_func, *process_args
    ):
        """
        Run the executor with live display updates

        Args:
            executor_func: Executor class (ThreadPoolExecutor or ProcessPoolExecutor)
            releases: List of release IDs to process
            process_func: Function to process each release
            *process_args: Additional args for process_func
        """
        try:
            with Live(
                self._build_display(), console=self.console, refresh_per_second=2
            ) as live:
                with executor_func(max_workers=self.num_workers) as executor:
                    # Submit all tasks
                    future_to_release = {}
                    for release_id in releases:
                        if self.shutdown_requested:
                            break
                        future = executor.submit(
                            process_func, release_id, *process_args
                        )
                        future_to_release[future] = release_id

                    # Process completed tasks
                    import concurrent.futures

                    for future in concurrent.futures.as_completed(future_to_release):
                        if self.shutdown_requested:
                            # Cancel remaining futures
                            for f in future_to_release:
                                f.cancel()
                            break

                        release_id = future_to_release[future]
                        try:
                            result = future.result()
                            # Worker already updated via callbacks
                        except Exception as e:
                            # Update error status
                            # Note: worker_id needs to be tracked differently in real implementation
                            pass

                        # Update display
                        live.update(self._build_display())

                # Final display update
                time.sleep(0.5)
                live.update(self._build_display())

        except KeyboardInterrupt:
            self._signal_handler(None, None)
            raise

        # Summary
        if self.shutdown_requested:
            self.console.print("\n[bold yellow]⚠️  Shutdown completed[/]")
        else:
            self.console.print(f"\n[bold green]✅ All releases processed![/]")

        self.console.print(
            f"[bold]Completed:[/] {self.completed_count}/{self.total_releases}"
        )
        if self.error_count > 0:
            self.console.print(f"[bold red]Errors:[/] {self.error_count}")


# Progress tracking helper for use within worker functions
class WorkerProgressTracker:
    """Helper to track progress within worker functions"""

    def __init__(self, monitor, worker_id):
        self.monitor = monitor
        self.worker_id = worker_id

    def update_step(self, step, progress=None):
        """Update current processing step"""
        kwargs = {"step": step}
        if progress is not None:
            kwargs["progress"] = progress
        self.monitor.update_worker(self.worker_id, **kwargs)

    def add_file(self, filepath):
        """Register a generated file"""
        self.monitor.update_worker(self.worker_id, file_generated=filepath)

    def set_release(self, release_id, title):
        """Set current release being processed"""
        self.monitor.update_worker(
            self.worker_id, release_id=release_id, release_title=title, status="working"
        )

    def complete(self):
        """Mark work as completed"""
        self.monitor.update_worker(self.worker_id, status="completed")

    def error(self, message):
        """Mark work as errored"""
        self.monitor.update_worker(self.worker_id, status="error", error=message)

    def check_shutdown(self):
        """Check if shutdown has been requested"""
        return self.monitor.is_shutdown_requested()


if __name__ == "__main__":
    # Demo/test of the monitor
    import concurrent.futures
    import random

    def mock_worker(release_id, monitor, worker_id):
        """Mock worker for testing"""
        tracker = WorkerProgressTracker(monitor, worker_id)

        # Simulate processing
        title = f"Test Album {release_id}"
        tracker.set_release(release_id, title)

        steps = [
            ("Fetching metadata", 20),
            ("Downloading cover art", 40),
            ("Processing audio", 60),
            ("Generating waveform", 80),
            ("Creating label", 100),
        ]

        for step, progress in steps:
            if tracker.check_shutdown():
                return None

            tracker.update_step(step, progress)
            time.sleep(random.uniform(0.5, 2.0))

            # Simulate file generation
            if progress > 40:
                tracker.add_file(f"release_{release_id}/file_{progress}.txt")

        tracker.complete()
        return release_id

    # Run test
    num_releases = 20
    num_workers = 4

    monitor = ThreadMonitor(num_releases, num_workers, "Test Sync")

    releases = list(range(1, num_releases + 1))

    try:
        monitor.run_with_live_display(
            concurrent.futures.ThreadPoolExecutor,
            releases,
            mock_worker,
            monitor,
            0,  # worker_id placeholder
        )
    except KeyboardInterrupt:
        print("\nTest interrupted")
