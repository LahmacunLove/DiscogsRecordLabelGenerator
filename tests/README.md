# Tests Directory

This directory contains test files and utilities for the DiscogsRecordLabelGenerator project.

## Test Files

### test_monitor.py

Demo/test script for the multi-threaded CLI visualization system.

**Purpose:**
- Demonstrates the ThreadMonitor visualization with simulated releases
- Tests per-worker progress tracking and display updates
- Validates graceful Ctrl+C shutdown behavior
- No actual API calls or file operations performed

**Usage:**
```bash
# Run with default settings (20 releases, 4 workers)
python3 tests/test_monitor.py

# Customize parameters
python3 tests/test_monitor.py --releases 50 --workers 8

# Test with fewer workers
python3 tests/test_monitor.py --releases 10 --workers 2
```

**Features Demonstrated:**
- Per-worker status panels with live updates
- Progress bars and percentage tracking
- Step-by-step processing simulation
- File generation tracking
- Overall statistics (completion, errors, timing)
- Graceful shutdown on Ctrl+C

**Testing Shutdown:**
Run the test and press **Ctrl+C** at any time during execution to verify:
- Workers stop gracefully
- Current operations complete cleanly
- Summary shows completed vs. total releases
- No errors or crashes occur

## Running Tests

All test scripts should be run from the project root directory:

```bash
cd /path/to/DiscogsRecordLabelGenerator
python3 tests/test_monitor.py [options]
```

## Future Tests

This directory is prepared for additional test files:

- Unit tests for individual modules
- Integration tests for full workflows
- Performance benchmarks
- API mocking tests
- Label generation tests
- Audio analysis tests

## Dependencies

Tests may require all project dependencies. Install with:

```bash
pip install -r requirements.txt
```

## Documentation

For more information about the multi-threaded visualization system, see:
- [Thread Visualization Documentation](../.assistant/THREAD_VISUALIZATION.md) (AI reference)
- [Usage Guide](../docs/USAGE.md#multi-threaded-processing)
- [Q&A Documentation](../docs/QA.md#multi-threaded-processing)

---

**Note:** This directory follows the project's file organization principle: all test files belong in `tests/`, not in the root directory.