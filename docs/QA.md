# Code Q&A Documentation

This document contains questions and answers about the codebase behavior and implementation details. It serves as a knowledge base for understanding how different parts of the system work.

---

## Table of Contents

- [General Architecture](#general-architecture)
- [Data Processing](#data-processing)
- [Label Generation](#label-generation)
- [Configuration](#configuration)
- [API Integration](#api-integration)
- [Audio Analysis](#audio-analysis)
- [Multi-Threaded Processing](#multi-threaded-processing)

---

## General Architecture

*Questions about overall system design and structure will be documented here.*

---

## Data Processing

*Questions about how data is processed, transformed, and stored will be documented here.*

---

## Label Generation

### Q: What label format is used for printing?

**A:** The system uses **Avery Zweckform L4744REV-65** labels:
- **Label size**: 96 x 50.8 mm (3.78" x 2")
- **Paper format**: A4 (210 x 297 mm)
- **Layout**: 2 columns x 5 rows = 10 labels per sheet
- **Form**: Rectangular with rounded corners
- **Compatibility**: Inkjet, Laser B&W, Color Laser

**Implementation locations**:
- LaTeX templates: `src/templates/xelatexTemplate.tex` and `src/templates/latexTemplate.tex`
  - Geometry package settings define A4 paper with appropriate margins
  - Left/right margins: 0.276 inches (7mm)
  - Top/bottom margins: 0.846 inches (21.5mm)
- Label generation: `src/latex_generator.py`
  - Line ~408: Label generation function `_create_label_original()`
  - Line ~587: Minipage dimensions set to 9.6cm x 5.08cm (96mm x 50.8mm)
  - Line ~873: TikZ rectangle dimensions set to 3.78in x 2in
  - Line ~876: Column spacing set to 3.937 inches (3.78" label + 0.157" gap)
  - Line ~644: Tabularx width set to 9.2cm for track table

**Note**: The system previously used US Letter paper with 4" x 2" labels. The change to Avery L4744REV-65 maintains the same height (50.8mm = 2") but reduces width from 101.6mm to 96mm to match standard European label sheets.

---

### Q: What is the layout of each label?

**A:** Each label follows a unified design structure:

**1. Header Section**:
- **Left**: Cover image (1.2cm width) spanning 2 text rows
- **Center**: Artist name (normal text) and album title (bold text)
- **Top-right corner**: QR code (1.2cm, positioned by combine function)

**2. Track Table** (10 rows fixed):
- **Columns**: Index (e.g., A1, B2) | Track Name | BPM | Key | Waveform
- Track names are truncated to 35 characters to prevent overflow
- Empty rows are padded if album has fewer than 10 tracks
- Albums with more than 10 tracks create multiple labels (label_part1.tex, label_part2.tex, etc.)

**3. Footer Section**:
- Record label name (max 30 chars)
- Catalog number (max 20 chars)
- Year
- Genres (max 2, max 30 chars total)
- Release ID

**Text Truncation**:
- Artist name: 45 characters max
- Album title: 45 characters max
- Track names: 35 characters max
- All truncated text appends "..."

**Implementation**: `src/latex_generator.py` lines ~408-665

---

## Configuration

*Questions about configuration handling and environment setup will be documented here.*

---

## API Integration

*Questions about Discogs API integration and data fetching will be documented here.*

---

## Audio Analysis

*Questions about audio feature extraction and similarity analysis will be documented here.*

---

## Multi-Threaded Processing

### Q: How does the multi-threaded CLI visualization work during sync operations?

**A:** The sync process displays real-time progress for each worker thread in separate panels.

**What you see:**
- Per-worker panels showing current release, processing step, and progress bar
- Files being generated in real-time
- Overall statistics (completion %, errors, elapsed time)
- Status indicators (⚪ idle, 🟢 working, ✅ completed, 🔴 error)

**Graceful shutdown:** Press Ctrl+C at any time to stop all workers cleanly without corrupting files.

**Try it:** Run `python3 tests/test_monitor.py` to see a demo with simulated releases.

**Implementation:** Uses `ThreadMonitor` class in `src/thread_monitor.py`, integrated in `src/mirror.py`. See [detailed implementation notes](../.assistant/QA_DETAILED.md) for technical details.

### Q: How does Ctrl+C work during sync operations?

**Asked:** 2025-01-XX

**Question:** When I press Ctrl+C during sync, does it stop immediately or wait for workers to finish their current tasks?

**Answer:** 

The sync process implements **immediate termination** that responds to Ctrl+C by forcefully exiting the entire process, terminating all worker threads/processes instantly.

**How it works:**

1. **Signal Handler Setup** (`src/thread_monitor.py`, line 135):
   - `ThreadMonitor.__init__()` registers a SIGINT handler
   - When Ctrl+C is pressed, `_signal_handler()` immediately calls `sys.exit(130)`

2. **Immediate Process Exit**:
   - All worker threads are terminated immediately (Python kills threads on process exit)
   - No cleanup, no checkpoints, no waiting for operations to complete
   - Process exits with status code 130 (standard for SIGINT)

**Behavior:**

- **Instant termination**: Process exits immediately when Ctrl+C is pressed
- **All workers killed**: No waiting for any operations to complete
- **Warning message**: UI shows "⚠️ Ctrl+C detected - terminating immediately..." before exit
- **Potential partial files**: Any files being written may be incomplete or corrupted
- **No cleanup**: Temporary files may be left behind

**Trade-offs:**

✅ **Advantages:**
- Immediate response to user request
- No waiting for long operations
- Simple implementation

⚠️ **Considerations:**
- Files currently being written may be incomplete
- Temporary files may not be cleaned up
- Audio downloads may be partial
- Next sync will need to reprocess interrupted releases

**Relevant Files:**
- `src/thread_monitor.py` (lines 137-143) - Signal handler with immediate exit
- `scripts/sync.py` (lines 324-328) - Top-level KeyboardInterrupt handler

**Testing:**
```bash
# Start a sync and press Ctrl+C during processing
python3 scripts/sync.py --dev

# Press Ctrl+C while workers are active
# You should see: "⚠️ Ctrl+C detected - terminating immediately..."
# Process exits instantly
```

**Related Topics:** Multi-threaded processing, signal handling, immediate termination, SIGINT handling

---

## Contributing to this Document

When adding new Q&A entries:
1. Place the entry in the most appropriate section
2. Use the following format:

### Q: [Brief question summary]

**Asked:** YYYY-MM-DD

**Question:** Full question as asked by the user.

**Answer:** Detailed answer with code references.

**Relevant Files:**
- `path/to/file.py` (lines X-Y) - Brief description
- `path/to/another_file.py` (lines A-B) - Brief description

**Related Topics:** Links to other Q&A entries or documentation sections if applicable.

---

*Last updated: 2025-10-03*

---

## Q&A Entries

### Q: When are waveforms generated in the application lifecycle?

**Asked:** 2025-10-03

**Question:** Where in the lifecycle do we generate waveforms? If it's done at print time, could we move the logic to the processing sync step and store waveform files along with all other assets?

**Answer:** 

Waveforms are **already designed to be generated during the sync/processing step**, not at print/label generation time. They are stored as asset files (`*_waveform.png`) alongside audio files and analysis data.

**However, upon investigation of an actual library, waveforms were NOT being generated.**

**Root Causes Identified and Fixed:**

1. **Opus Codec Incompatibility**: Essentia's `MusicExtractor` doesn't support Opus codec directly
   - **Solution**: Added automatic Opus-to-WAV conversion using FFmpeg before Essentia analysis
   - Temporary WAV file is created, analyzed, then cleaned up
   - Original Opus files remain unchanged

2. **FFmpeg Not Enabled**: Code had `ffmpegUsage=False` hardcoded in multiple locations
   - **Solution**: Changed to `ffmpegUsage=True` throughout the codebase
   - Affects: `youtube_handler.py`, `mirror.py` (4 locations total)

**After Fix**: Waveforms now generate successfully during sync!

**Generation Design (when dependencies are met):**

1. **YouTube download flow** (`src/youtube_handler.py`):
   - After downloading and analyzing a track from YouTube
   - Method: `YouTubeMatcher._parallel_audio_analysis()` → `_analyze_track_standalone()` (lines 497-570)
   - Calls `analyzer.generate_waveform_gnuplot()` after Essentia analysis

2. **Bandcamp audio analysis** (`src/mirror.py`):
   - Method: `DiscogsLibraryMirror.analyze_bandcamp_audio()` (line ~246)
   - Calls `analyzer.generate_waveform_gnuplot()` after loading audio

3. **Offline processing** (`src/mirror.py`):
   - Method: `DiscogsLibraryMirror._process_audio_analysis_offline()` (line ~1059)
   - Processes existing audio files and generates missing waveforms

**Regeneration capability:**

The system supports regenerating waveforms independently via:
- CLI flag: `--regenerate-waveforms`
- Method: `DiscogsLibraryMirror.regenerate_waveforms()` (line 1064-1138)
- This allows rebuilding all waveforms without re-downloading audio

**Storage location:**

Waveforms should be stored in each release folder as: `{track_position}_waveform.png`
Example: `A1_waveform.png`, `B2_waveform.png`

**Technical implementation:**

- Core logic: `analyzeAudioFileOrStream.generate_waveform_gnuplot()` in `src/analyzeSoundFile.py` (line 157-270)
- Uses `gnuplot` with FFmpeg PCM data for fast generation
- Checks for existing files to avoid regeneration
- Waveform script template: `src/waveform.gnuplot`

**Critical Dependencies:**
- **NumPy** - Required by Essentia (ImportError if missing)
- **Essentia** - Audio analysis library
- **gnuplot** - Waveform visualization
- **FFmpeg** - Audio decoding for both Essentia and gnuplot

**Testing the Fix:**
```bash
# Test on a specific release
./bin/sync.sh --release 116013

# Check results
ls ~/Music/DiscogsLibrary/116013_*/
# Should see: A1_waveform.png, A1.json, etc.
```

**Troubleshooting:**
If waveforms are not being generated:
1. **Check FFmpeg**: `which ffmpeg` - Required for Opus file handling
2. **Check gnuplot**: `which gnuplot` - Required for waveform visualization
3. **Check NumPy**: `python3 -c "import numpy; print(numpy.__version__)"`
4. **Check Essentia**: `python3 -c "import essentia; print(essentia.__version__)"`
5. **Check virtual environment**: Scripts use `venv/` - ensure it's activated
6. **Look for analysis JSON files** (`A1.json`, etc.) - if missing, analysis failed
7. **Check file format**: If not Opus, the conversion logic won't trigger
8. **Review error messages**: Look for "Unsupported codec!" or FFmpeg errors

**Relevant Files (Modified in Fix):**
- `src/analyzeSoundFile.py` (lines 46-160) - Added Opus-to-WAV conversion in `analyzeMusicExtractor()`
- `src/youtube_handler.py` (line 57, 76) - Changed `ffmpegUsage=False` to `True`
- `src/mirror.py` (lines 228, 246, 1043, 1059) - Changed `ffmpegUsage=False` to `True`
- `src/analyzeSoundFile.py` (lines 235-395) - Core waveform generation logic using gnuplot
- `src/youtube_handler.py` (lines 15-90) - Standalone analysis function
- `src/youtube_handler.py` (lines 497-650) - Parallel audio analysis orchestration
- `src/waveform.gnuplot` - Gnuplot script template
- `scripts/sync.py` - CLI tool for syncing and processing releases

**Related Topics:** Audio analysis workflow, Opus codec handling, FFmpeg integration, dependency validation, error handling, asset storage structure

---

*Last updated: 2025-10-03*