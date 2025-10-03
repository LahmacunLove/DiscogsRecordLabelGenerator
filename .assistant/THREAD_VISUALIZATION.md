# Multi-Threaded CLI Visualization

This document explains the multi-threaded CLI visualization feature that provides real-time monitoring of parallel release processing.

## Overview

The DiscogsRecordLabelGenerator now features a sophisticated multi-threaded CLI display that visualizes parallel worker threads in real-time. Each worker is displayed in its own panel showing current progress, processing steps, and generated files.

## Features

### Real-Time Worker Monitoring

- **Per-Worker Panels**: Each worker thread has a dedicated display panel
- **Live Progress Tracking**: See progress percentage and visual bars for each worker
- **Step-by-Step Updates**: Know exactly what each worker is doing at any moment
- **File Tracking**: See files as they're generated (last 3 files per worker)
- **Status Indicators**: Visual icons show worker state (⚪ idle, 🟢 working, ✅ completed, 🔴 error)
- **Timing Information**: Elapsed time shown for each worker's current task

### Overall Statistics

The header panel displays:
- Total progress (completed/total releases)
- Overall completion percentage
- Error count with visual highlighting
- Number of active workers
- Total elapsed time

### Graceful Shutdown

Press **Ctrl+C** at any time to:
- Signal all workers to stop gracefully
- Complete current operations cleanly
- Avoid corrupted or partial files
- Display summary of completed work
- Report any errors encountered

## Display Layout

```
╭─────────────────────────────────────────────────────────────────╮
│ 🎵 Processing releases                                          │
│ Progress: 15/50 (30.0%) │ Errors: 1 │ Workers: 4 │ Time: 5m 23s │
╰─────────────────────────────────────────────────────────────────╯

┌─ 🟢 Worker 0 │ Completed: 3 ─────────────┐┌─ 🟢 Worker 1 │ Completed: 4 ─────────────┐
│ Release: 123456                           ││ Release: 789012                           │
│ Title: Kind of Blue                       ││ Title: Abbey Road                         │
│ Step: Downloading audio                   ││ Step: Analyzing audio                     │
│ [████████████████░░░░] 60%                ││ [██████████████████░] 75%                 │
│ Time: 45s                                 ││ Time: 62s                                 │
│ Files: • metadata.json                    ││ Files: • track01.opus                     │
│        • cover.jpg                        ││        • track02.opus                     │
│        • track01.opus                     ││        • waveform.png                     │
└───────────────────────────────────────────┘└───────────────────────────────────────────┘

┌─ ⚪ Worker 2 │ Completed: 4 ─────────────┐┌─ 🔴 Worker 3 │ Completed: 3 ─────────────┐
│ Waiting for work...                       ││ ❌ Error in release 456789                │
│                                           ││ Failed to download audio from YouTube     │
└───────────────────────────────────────────┘└───────────────────────────────────────────┘

╭─────────────────────────────────────────────────────────────────╮
│ Press Ctrl+C to stop gracefully                                 │
╰─────────────────────────────────────────────────────────────────╯
```

## Processing Steps Tracked

The visualization tracks progress through these key steps:

1. **Checking existing metadata** (5%)
2. **Fetching metadata from Discogs** (10%)
3. **Saving metadata** (20%)
4. **Downloading cover art** (30%)
5. **Checking for Bandcamp audio** (35%)
6. **Copying Bandcamp audio** (40%) *or*
7. **Searching YouTube** (45%)
8. **Downloading audio** (60%)
9. **Analyzing audio** (70-75%)
10. **Generating waveform** (85%)
11. **Creating QR code** (92%)
12. **Generating LaTeX label** (98%)
13. **Completed** (100%)

## Files Tracked

The display shows recently generated files including:

- `metadata.json` - Release metadata from Discogs
- `cover.jpg` / `cover.png` - Album artwork
- `*.opus` / `*.flac` / `*.mp3` - Audio files
- `waveform.png` - Audio waveform visualization
- `qr_code.png` / `qr_code_fancy.png` - QR codes
- `label.tex` - LaTeX label file

## Technical Implementation

### Architecture

**Components:**
- `src/thread_monitor.py` - Core monitoring system
  - `ThreadMonitor` class - Manages overall monitoring
  - `WorkerState` class - Tracks individual worker state
  - `WorkerProgressTracker` class - Helper for workers to report progress

- `src/mirror.py` (lines 584-679) - Integration point
  - Creates ThreadMonitor for console mode
  - Maps worker threads to IDs
  - Wraps `sync_single_release()` with monitoring

### Thread Safety

- All worker state updates are protected by locks
- Thread-to-worker ID mapping ensures consistent display
- Signal handlers are registered for graceful Ctrl+C

### Display Technology

Uses the `rich` Python library for:
- Live updating displays
- Formatted panels and tables
- Progress bars and status icons
- Color-coded text

## Usage

### Normal Sync Operation

The visualization activates automatically when running sync operations:

```bash
./bin/sync.sh              # Full sync with visualization
./bin/sync.sh --dev        # Dev mode (10 releases)
./bin/sync.sh --max 20     # Process 20 releases
```

### Testing

Test the visualization without processing real releases:

```bash
# Run demo with default settings (20 releases, 4 workers)
python3 tests/test_monitor.py

# Customize test parameters
python3 tests/test_monitor.py --releases 50 --workers 8

# Test Ctrl+C handling (press Ctrl+C during execution)
python3 tests/test_monitor.py --releases 100 --workers 4
```

The test script simulates realistic processing times and file generation.

### Disabling Visualization

The visualization is used in console mode. If you need the old behavior, you can:

1. Use a progress callback (for GUI integration)
2. Redirect output: `./bin/sync.sh > output.log 2>&1`
3. Modify `mirror.py` to use tqdm instead

## Shutdown Behavior

### Normal Completion

```
✅ All releases processed!
Completed: 50/50
```

### User Interruption (Ctrl+C)

```
⚠️ Ctrl+C detected - shutting down workers gracefully...
⚠️ SHUTDOWN IN PROGRESS...

⚠️ Shutdown completed
Completed: 23/50
Errors: 1
```

### Error Handling

- Errors don't stop other workers
- Error count is displayed in the header
- Failed releases are marked with 🔴 status
- Error messages are shown in worker panels

## Performance Impact

The visualization has minimal performance impact:

- Display refreshes at 2 Hz (twice per second)
- Worker state updates are lock-protected but very fast
- File path tracking only stores last 3 files per worker
- Live display runs in separate thread from workers

## Dependencies

**New Dependency:**
- `rich` - Terminal UI library for live displays

Added to `requirements.txt`:
```
rich
```

Install with:
```bash
pip install rich
```

## Troubleshooting

### Display Issues

**Problem:** Weird characters or broken display
**Solution:** Ensure terminal supports Unicode and ANSI colors

**Problem:** Display doesn't update
**Solution:** Try a different terminal or disable rich animations

### Performance Issues

**Problem:** Slow processing with visualization
**Solution:** The visualization should have minimal impact. Check system resources.

**Problem:** Too many workers shown
**Solution:** Adjust worker count with CPU optimization settings in `cpu_utils.py`

### Shutdown Issues

**Problem:** Ctrl+C doesn't stop workers
**Solution:** Press Ctrl+C again to force termination (second press forces immediate exit)

**Problem:** Workers don't finish gracefully
**Solution:** Shutdown checks happen between processing steps; long-running operations may delay shutdown

## Future Enhancements

Potential improvements for future versions:

- Configurable refresh rate
- Export progress to log file
- Network bandwidth monitoring
- Disk I/O statistics
- Memory usage per worker
- Estimated time remaining
- Worker performance comparison
- Historical statistics dashboard

## Code Examples

### Integrating Monitoring in Custom Code

```python
from thread_monitor import ThreadMonitor, WorkerProgressTracker
import concurrent.futures

# Create monitor
monitor = ThreadMonitor(
    total_releases=100,
    num_workers=4,
    mode_desc="Custom Processing"
)

def process_with_tracking(item_id, worker_id):
    tracker = WorkerProgressTracker(monitor, worker_id)
    
    # Set what you're processing
    tracker.set_release(item_id, "Item Title")
    
    # Update progress through steps
    tracker.update_step("Step 1", 25)
    # ... do work ...
    
    tracker.update_step("Step 2", 50)
    # ... do work ...
    
    # Track generated files
    tracker.add_file("/path/to/generated/file.txt")
    
    # Check for shutdown
    if tracker.check_shutdown():
        return None
    
    # Mark complete
    tracker.complete()
    return item_id

# Use with executor
with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
    # Submit jobs and process...
    pass
```

## Related Documentation

- [Q&A Documentation](QA.md#multi-threaded-processing) - Implementation details
- [Usage Guide](USAGE.md#multi-threaded-processing) - Usage instructions
- [Main README](../README.md#features) - Feature overview
- [Changelog](CHANGES.md) - Complete changelog for this feature

## Credits

Implemented to provide better visibility into parallel processing operations and enable graceful shutdown of long-running sync operations.

---

**Last Updated:** October 2025