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

*Questions about the label generation process and LaTeX template system will be documented here.*

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
./bin/main.sh --release-id 116013

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
- `scripts/main.py` (lines 91-95, 151-187) - CLI argument handling for `--regenerate-waveforms`

**Related Topics:** Audio analysis workflow, Opus codec handling, FFmpeg integration, dependency validation, error handling, asset storage structure

---

*Last updated: 2025-10-03*