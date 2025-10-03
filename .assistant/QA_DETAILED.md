# Detailed Q&A Documentation (AI Reference)

This document contains verbose technical Q&A entries with implementation details, line numbers, and code-level information. This is primarily for AI assistant reference.

For user-facing Q&A, see `docs/QA.md`.

---

## Multi-Threaded Processing

### Q: How does the multi-threaded CLI visualization work during sync operations?

**A: The system uses a `ThreadMonitor` class to provide real-time visualization of parallel worker threads.**

**Location:** `src/thread_monitor.py` (primary implementation), integrated in `src/mirror.py` (lines 584-679)

**How it works:**

1. **ThreadMonitor Setup** - When `sync_releases()` runs in console mode (no progress_callback), it creates a `ThreadMonitor` instance with:
   - Total number of releases to process
   - Number of worker threads/processes
   - Mode description (e.g., "Processing releases", "Syncing Discogs metadata")

2. **Worker State Tracking** - Each worker thread is tracked individually with:
   - Current release ID and title
   - Current processing step (e.g., "Downloading cover art", "Analyzing audio")
   - Progress percentage (0-100%)
   - List of generated files
   - Status (idle, working, completed, error)
   - Elapsed time for current task

3. **Live Display** - Uses the `rich` library's Live display to show:
   - **Header Panel**: Overall progress, error count, worker count, elapsed time
   - **Worker Panels**: Grid layout (2 columns) showing each worker's:
     - Status indicator (⚪ idle, 🟢 working, ✅ completed, 🔴 error)
     - Current release being processed
     - Processing step and progress bar
     - Last 3 files generated
   - **Footer**: Instructions for graceful shutdown (Ctrl+C)

4. **Progress Tracking Integration** - The `sync_single_release_monitored()` method receives a `WorkerProgressTracker` that updates the monitor at key points:
   - Line 667: Checking existing metadata (5%)
   - Line 699: Fetching from Discogs (10%)
   - Line 778: Saving metadata (20%)
   - Line 788: Downloading cover art (30%)
   - Line 805: Checking Bandcamp audio (35%)
   - Line 810: Copying Bandcamp audio (40%)
   - Line 824: Analyzing Bandcamp audio (70%)
   - Line 837: Searching YouTube (45%)
   - Line 848: Downloading YouTube audio (60%)
   - Line 874: Generating QR code (85%)
   - Line 883: Creating LaTeX label (95%)

5. **File Tracking** - As files are generated, they're registered with the tracker:
   - metadata.json (line 784)
   - cover.jpg/png (line 793)
   - Audio files (lines 816-819, 856-859, 868-871)
   - QR code (lines 877-879)
   - label.tex (line 887)

6. **Graceful Shutdown** - Ctrl+C handling (line 115-122 in thread_monitor.py):
   - Signal handler sets shutdown flag
   - Workers check `tracker.check_shutdown()` between steps
   - Remaining futures are cancelled
   - Display shows "SHUTDOWN IN PROGRESS" warning
   - Summary shows completed vs total releases

**Testing:** Run `python3 tests/test_monitor.py` to see a demo with simulated releases.

**Key Features:**
- Real-time progress visualization for each worker thread
- Per-worker file generation tracking
- Graceful Ctrl+C shutdown that terminates all threads
- Visual separation of idle, working, completed, and errored workers
- Overall progress statistics and timing

**Dependencies:**
- `rich` library for terminal UI (added to requirements.txt)
- Works with both ThreadPoolExecutor (Discogs-only mode) and ProcessPoolExecutor (full processing)

**Implementation Classes:**

- `ThreadMonitor` (thread_monitor.py):
  - `__init__()` - Initialize with total releases, workers, mode description
  - `update_worker()` - Update state for specific worker
  - `_build_display()` - Build rich Layout with header, worker panels, footer
  - `_build_worker_panel()` - Build individual worker display panel
  - `_signal_handler()` - Handle Ctrl+C gracefully
  - `is_shutdown_requested()` - Check shutdown flag

- `WorkerState` (thread_monitor.py):
  - Tracks: worker_id, release_id, release_title, current_step, progress_percent
  - Tracks: files_generated (list), start_time, status, error_message, total_processed
  - `update()` - Update any tracked field
  - `get_elapsed_time()` - Calculate elapsed time for current task

- `WorkerProgressTracker` (thread_monitor.py):
  - Helper class for workers to report progress
  - `update_step()` - Update current processing step and progress
  - `add_file()` - Register generated file
  - `set_release()` - Set current release being processed
  - `complete()` - Mark work completed
  - `error()` - Mark work errored
  - `check_shutdown()` - Check if shutdown requested

**Integration in mirror.py:**

Lines 584-679 in `sync_releases()` method:
1. Create ThreadMonitor instance
2. Create worker ID mapping (thread ID → worker ID)
3. Define `sync_with_monitoring()` wrapper function
4. Wrap executor in Live display context
5. Submit all jobs to executor
6. Process completed futures with display updates
7. Handle shutdown signals
8. Display final summary

Lines 658-887 in `sync_single_release_monitored()`:
- Progress tracking calls at each major step
- File tracking as files are generated
- Shutdown checks between operations
- Tracker.complete() called at end

**Signal Flow:**

1. User presses Ctrl+C
2. `_signal_handler()` called → sets `shutdown_requested = True`
3. Display shows "SHUTDOWN IN PROGRESS"
4. Workers check `tracker.check_shutdown()` between steps
5. Workers return early if shutdown requested
6. Main loop cancels remaining futures
7. Live display updates one final time
8. Summary printed to console

---

## Future Q&A Entries

Additional detailed Q&A entries will be added here as needed.