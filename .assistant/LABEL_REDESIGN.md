# Label Redesign: Unified Layout with Cover Image

**Date**: 2025-01-XX  
**Component**: `labels`  
**Impact**: Breaking change - complete label layout redesign

## Overview

Complete redesign of label layout to create a unified, professional appearance with consistent structure across all releases. The new design features a cover image header, fixed 10-row track table, and automatic multi-label support for albums with many tracks.

## Motivation

User requested a standardized label design with:
1. Visual consistency across all labels
2. Cover image integration for quick visual identification
3. QR code in a fixed position (top-right corner)
4. Fixed-height track table to ensure labels align properly
5. Proper text truncation to prevent overflow

## New Design Specification

### 1. Header Section (Top ~1.5cm)

**Layout**: Three-part horizontal structure
- **Left (1.3cm)**: Album cover image (1.2cm width, maintains aspect ratio)
- **Center (7.0cm)**: Artist name and album title
  - Artist: Normal text, left-aligned
  - Title: Bold text, left-aligned
- **Right (Top corner)**: QR code (1.2cm, positioned by combine function)

**Text Truncation**:
- Artist name: 45 characters max
- Album title: 45 characters max
- Overflow appends "..."

### 2. Track Table (Middle ~3.0cm)

**Fixed Structure**: Exactly 10 rows, regardless of track count
- Empty rows padded if album has < 10 tracks
- Additional labels created if album has > 10 tracks

**Columns**:
1. **Index** (e.g., A1, B2, C1): Left-aligned, tight spacing
2. **Track Name**: Flexible width (uses tabularx X column), truncated to 35 chars
3. **BPM**: Right-aligned, numeric
4. **Key**: Center-aligned, Camelot notation (e.g., 8A, 5B)
5. **Waveform**: Center-aligned, 1.8cm × 0.3cm image

**Column Format**: `@{}l@{\hspace{2pt}}X@{\hspace{2pt}}r@{\hspace{2pt}}c@{\hspace{2pt}}c@{}`
- Minimal spacing (2pt) to maximize usable width on 96mm labels
- X column for track name allows flexible sizing

### 3. Footer Section (Bottom ~0.5cm)

**Single Line** with comma-separated metadata:
- Record label name (max 30 chars)
- Catalog number (max 20 chars)
- Year (4 digits)
- Genres (first 2 genres, max 30 chars total)
- Release ID (always included)

**Example**: `Atlantic Records, SD 19166, 1977, Rock, Jazz, ID: 123456`

## Multi-Label Support

Albums with more than 10 tracks automatically generate multiple labels:
- `label.tex` → `label_part1.tex`, `label_part2.tex`, etc.
- Each label maintains the same header (artist, title, cover, QR)
- Track table shows chunks of 10 tracks
- Footer is identical across all parts

**Example**: 23-track album creates 3 labels:
- Part 1: Tracks 1-10
- Part 2: Tracks 11-20
- Part 3: Tracks 21-23 (with 7 empty rows)

## Technical Implementation

### File: `src/latex_generator.py`

#### Function: `_create_label_original()` (Lines ~408-665)

**Major Changes**:

1. **Cover Image Integration** (Lines ~420-429):
```python
cover_path = os.path.join(release_folder, "cover.jpg")
if not os.path.exists(cover_path):
    cover_path = os.path.join(release_folder, "cover.png")

cover_latex = ""
if os.path.exists(cover_path):
    cover_abs_path = os.path.abspath(cover_path).replace("\\", "/")
    cover_latex = f"\\includegraphics[width=1.2cm]{{{cover_abs_path}}}"
```

2. **Text Truncation** (Lines ~443-447):
```python
artist_truncated = (artist_str[:45] + "...") if len(artist_str) > 45 else artist_str
title_truncated = (title[:45] + "...") if len(title) > 45 else title
# Track titles truncated to 35 chars in loop
track_title_truncated = (track_title[:35] + "...") if len(track_title) > 35 else track_title
```

3. **Track Chunking** (Lines ~486-490):
```python
track_chunks = []
for i in range(0, len(tracklist), 10):
    chunk = tracklist[i : i + 10]
    track_chunks.append(chunk)
```

4. **10-Row Padding** (Lines ~569-577):
```python
while len(tracks_data) < 10:
    tracks_data.append({
        "pos": "",
        "title": "",
        "bpm": "",
        "key": "",
        "waveform": "",
    })
```

5. **New LaTeX Structure** (Lines ~587-626):
```latex
\begin{minipage}[t][5.08cm][t]{9.6cm}
\vspace{0pt}

% Header with cover image and text
\noindent\begin{minipage}[t]{1.3cm}
<cover image>
\end{minipage}%
\hfill%
\begin{minipage}[t]{7.0cm}
\raggedright
\small{<artist>}\\
\textbf{\small{<title>}}
\end{minipage}

\vspace{0.3cm}

% Track table (10 rows fixed)
{\scriptsize
<table>
}

\vspace{0.1cm}

% Footer
\noindent{\tiny{<metadata>}}

\end{minipage}
```

6. **Multi-Label File Handling** (Lines ~629-638):
```python
if len(track_chunks) > 1:
    chunk_label_file = label_file.replace(".tex", f"_part{chunk_idx + 1}.tex")
else:
    chunk_label_file = label_file
```

### Function: `combine_latex_labels()` (Lines ~690+)

**Changes to Support Multi-Labels**:

1. **Find All Label Files** (Lines ~693-701):
```python
label_files = []
if os.path.exists(label_file):
    label_files.append("label.tex")

for item in os.listdir(release_path):
    if item.startswith("label_part") and item.endswith(".tex"):
        label_files.append(item)
```

2. **QR Code Positioning** (Lines ~916-925):
```python
# Position QR code in top-right corner
qr_x = x_pos + 3.15
qr_y = y_pos - 0.25 + 1.975
# Reduced QR size to 1.2cm to match design
f.write(f"\\includegraphics[width=1.2cm]{{{qr_path}}}")
```

3. **Multi-Label Scanning** (Lines ~779-827):
- Scans for both `label.tex` and `label_part*.tex` files
- Each part is treated as a separate label in the combined PDF
- Maintains proper ordering (part1, part2, part3, etc.)

## Comparison: Old vs New Design

### Old Design
```
┌─────────────────────────────────────┐
│ Artist Name (adjustbox)             │
│ Album Title (adjustbox)             │
│                                     │
│ [Track Table - Variable Height]    │
│                                     │
│ Footer (label, year, genre, ID)    │
└─────────────────────────────────────┘
```

### New Design
```
┌─────────────────────────────────────┐
│ [Cover] Artist Name            [QR] │
│         Album Title (Bold)          │
├─────────────────────────────────────┤
│ A1 │ Track Name    │ 120│ 5A│ [~~~]│
│ A2 │ Track Name    │ 125│ 8B│ [~~~]│
│ ... (8 more rows, always 10 total) │
├─────────────────────────────────────┤
│ Label, Cat#, Year, Genre, ID       │
└─────────────────────────────────────┘
```

## Key Improvements

1. **Visual Consistency**: All labels have identical structure
2. **Quick Recognition**: Cover image enables visual scanning
3. **Better Organization**: Fixed row count ensures alignment
4. **No Overflow**: Aggressive text truncation prevents layout breaks
5. **Scalability**: Automatic multi-label generation for long albums
6. **Professional Look**: Clean grid layout with proper spacing

## Text Truncation Strategy

**Why Truncation?**
- Avery L4744REV-65 labels are only 96mm wide
- LaTeX `adjustbox` and `fitbox` can over-shrink text, making it unreadable
- Fixed truncation ensures minimum legible font size

**Truncation Limits**:
- **Artist**: 45 chars (2-3 artist names with full names)
- **Album Title**: 45 chars (most album titles fit)
- **Track Names**: 35 chars (ensures minimum font size in table)
- **Footer Elements**: 20-30 chars each (prevents footer overflow)

**Visual Indicator**: All truncated text appends "..." to show truncation

## Migration Path

### For Existing Libraries

1. **Regenerate All Labels**: 
   ```bash
   python3 scripts/generate_labels.py
   ```
   - Old `label.tex` files will be overwritten
   - Multi-track albums will create `label_part*.tex` files

2. **Combined PDF Generation**:
   ```bash
   python3 scripts/generate_labels.py --max 10
   ```
   - Automatically includes all label parts
   - Each part gets its own sticker position

3. **Print Test**:
   - Print one sheet with various releases
   - Verify cover images align properly
   - Check QR code position (top-right corner)
   - Confirm text is legible at all truncation points

### Backwards Compatibility

**Breaking Change**: No compatibility with old label format
- Different minipage dimensions
- Different internal structure
- Cover image requirement (gracefully handles missing covers)

**Action Required**: Full label regeneration for all releases

## Testing Checklist

- [ ] Single-page label (< 10 tracks) renders correctly
- [ ] Multi-page label (> 10 tracks) splits properly
- [ ] Cover image displays at correct size
- [ ] QR code positioned in top-right corner
- [ ] Text truncation works for long names
- [ ] Empty rows pad correctly for short albums
- [ ] Footer metadata fits in one line
- [ ] BPM and Key columns align properly
- [ ] Waveforms display at correct size
- [ ] Labels align on printed Avery L4744REV-65 sheets

## Known Issues & Considerations

1. **Missing Cover Images**: 
   - Layout still works, just no cover shown
   - Could add placeholder image in future

2. **Very Long Track Names**: 
   - 35-char truncation may cut important info
   - Consider abbreviations in metadata

3. **QR Code Overlap**: 
   - Very long artist names might overlap QR
   - Truncation at 45 chars prevents this in most cases

4. **Multi-Part Confusion**: 
   - No visual indicator on label which part it is
   - Could add "(Part 1 of 3)" to footer in future

5. **Waveform Quality**: 
   - 1.8cm × 0.3cm is quite small
   - Ensure waveform generation uses appropriate resolution

## Future Enhancements

1. **Part Numbering**: Add "(1/3)" indicator for multi-part labels
2. **Placeholder Cover**: Generate placeholder for releases without covers
3. **Custom Truncation**: Allow user-configurable truncation limits
4. **Font Scaling**: Smarter font scaling within truncation limits
5. **Color Themes**: Optional color schemes for different genres
6. **Barcode Support**: Alternative to QR codes for some use cases

## References

- Original Request: User specification for unified label design
- Label Format: Avery Zweckform L4744REV-65 (96 × 50.8 mm)
- Implementation: `src/latex_generator.py`
- Documentation: `docs/QA.md`

---

**Status**: ✅ Implemented  
**Testing**: ⚠️ Requires testing with real release data  
**Breaking Change**: Yes - complete redesign, requires full regeneration