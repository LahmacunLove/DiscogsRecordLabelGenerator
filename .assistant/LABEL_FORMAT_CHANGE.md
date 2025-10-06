# Label Format Change: Avery Zweckform L4744REV-65

**Date**: 2025-01-XX  
**Component**: `labels`  
**Impact**: Breaking change - label dimensions updated

## Overview

The label template has been updated from US Letter paper (4" x 2" labels) to **Avery Zweckform L4744REV-65** format (96mm x 50.8mm labels on A4 paper).

## Motivation

User request to match a specific, widely available label sheet format suitable for European markets. The Avery Zweckform L4744REV-65 is:
- Standard A4 paper size (more common internationally)
- Removable adhesive labels (perfect for temporary labeling)
- Compatible with inkjet and laser printers
- TÜV-certified for laser printers
- FSC-certified paper

## Product Specifications

**Avery Zweckform L4744REV-65**:
- **Label size**: 96 x 50.8 mm (3.78" x 2")
- **Paper format**: A4 (210 x 297 mm / 8.27" x 11.69")
- **Labels per sheet**: 10 (2 columns x 5 rows)
- **Form**: Rectangular with rounded corners
- **Adhesive**: Removable (ablösbar)
- **Material**: White paper
- **Compatibility**: Inkjet, Laser B&W, Color Laser
- **Product URL**: https://www.avery-zweckform.com/produkt/universal-etiketten-l4744rev-65

## Technical Changes

### 1. LaTeX Templates

**Files Modified**:
- `src/templates/xelatexTemplate.tex`
- `src/templates/latexTemplate.tex`

**Changes**:
```latex
% Before:
\usepackage[letterpaper,margin=0.1562in,top=0.6in]{geometry}

% After:
\usepackage[a4paper,left=0.276in,right=0.276in,top=0.846in,bottom=0.846in]{geometry}
```

**Margin Calculations**:
- **Left/Right**: 7mm = 0.276" each side
  - A4 width: 210mm = 8.268"
  - 2 labels: 2 × 96mm = 192mm = 7.559"
  - Gap between labels: ~4mm = 0.157"
  - Margins accommodate proper alignment
  
- **Top/Bottom**: 21.5mm = 0.846" each side
  - A4 height: 297mm = 11.693"
  - 5 labels: 5 × 50.8mm = 254mm = 10"
  - Remaining space: 43mm = 1.693" distributed to margins

### 2. Label Generation Code

**File Modified**: `src/latex_generator.py`

#### Minipage Dimensions (Line ~616-617)
```python
# Before:
latex_content = f"""\\begin{{minipage}}[t][4.4cm][t]{{9.5cm}}

# After:
latex_content = f"""\\begin{{minipage}}[t][5.08cm][t]{{9.6cm}}
```
- Height: 4.4cm → 5.08cm (matches 50.8mm label height)
- Width: 9.5cm → 9.6cm (matches 96mm label width)

#### Adjustbox Widths (Line ~619, 622)
```python
# Before:
\\begin{{adjustbox}}{{max width=8cm}}

# After:
\\begin{{adjustbox}}{{max width=9cm}}
```
- Increased to utilize more of the 96mm label width

#### Tabularx Width (Line ~646-647)
```python
# Before:
inplace_change(label_file, "\\begin{tabular}", "\\begin{tabularx}{3.74in}")

# After:
inplace_change(label_file, "\\begin{tabular}", "\\begin{tabularx}{3.78in}")
```
- 3.74" → 3.78" (exact 96mm conversion)

#### TikZ Label Frame (Line ~871-873)
```python
# Before:
f"\t\\draw[rounded corners=0.5cm] ({x_pos} in, {y_pos} in) rectangle +(4in,2in);\n"

# After:
f"\t\\draw[rounded corners=0.5cm] ({x_pos} in, {y_pos} in) rectangle +(3.78in,2in);\n"
```
- Width: 4" → 3.78" (96mm)
- Height: 2" unchanged (50.8mm matches both formats)

#### Column Spacing (Line ~868)
```python
# Before:
x_pos = 4.1 * col  # 4" label + 0.1" gap

# After:
x_pos = 3.937 * col  # 3.78" label + 0.157" gap
```
- Spacing: 4.1" → 3.937" per column
- Calculated as: 96mm label + 4mm gap = 100mm = 3.937"

### 3. Documentation Updates

**Files Modified**:
- `README.md` - Updated output format description
- `docs/FILE_STRUCTURE.md` - Updated label specifications
- `docs/QA.md` - Added detailed Q&A entry with implementation locations

## Layout Comparison

### Before (US Letter, 8163 format)
- Paper: 8.5" × 11" (215.9mm × 279.4mm)
- Label: 4" × 2" (101.6mm × 50.8mm)
- Layout: 2 × 5 = 10 labels per page
- Margins: Varied

### After (A4, Avery L4744REV-65)
- Paper: 8.27" × 11.69" (210mm × 297mm)
- Label: 3.78" × 2" (96mm × 50.8mm)
- Layout: 2 × 5 = 10 labels per page
- Margins: Symmetric (7mm left/right, 21.5mm top/bottom)

## Key Observations

1. **Height unchanged**: Both formats use 50.8mm (2") label height - perfect match!
2. **Width reduced**: 101.6mm → 96mm (5.6mm narrower per label)
3. **Same layout**: Both formats have 10 labels per page in 2×5 grid
4. **Better symmetry**: A4 format allows for more balanced margins

## Testing Recommendations

1. **Visual Check**: Generate a test PDF with `--max 1` to verify single label
2. **Full Page Test**: Generate 10 labels to verify complete page layout
3. **Print Test**: Print on actual Avery L4744REV-65 sheets to verify alignment
4. **Content Check**: Ensure all content (artist, title, tracks, QR code) fits properly in narrower format

## Potential Issues

1. **Content Overflow**: Narrower labels (96mm vs 101.6mm) may cause text wrapping for very long artist/title names
   - Solution: The `adjustbox` and `fitbox` environments automatically scale content to fit
   
2. **QR Code Position**: QR code positioning may need fine-tuning
   - Current position: Line ~892-900 in `latex_generator.py`
   - Positioned at `x_pos + 3.25` (may need adjustment to `x_pos + 3.0` for narrower labels)

3. **Existing Labels**: Users with existing `.tex` label files will need to regenerate them
   - The minipage dimensions are embedded in individual label files
   - Re-run label generation to update all labels to new format

## Migration Path

For users upgrading from the old format:

1. **Regenerate Labels**: Run label generation to create new `.tex` files with updated dimensions
   ```bash
   python3 scripts/generate_labels.py
   ```

2. **Update Output**: The combined PDF will automatically use the new A4 format

3. **Order New Sheets**: Purchase Avery Zweckform L4744REV-65 label sheets for printing

## Rollback Instructions

If needed, revert these commits to return to US Letter format:
- Revert `src/templates/*.tex` geometry settings
- Revert `src/latex_generator.py` dimension changes
- Regenerate all label files

## References

- Product Page: https://www.avery-zweckform.com/produkt/universal-etiketten-l4744rev-65
- A4 Paper Standard: ISO 216 (210mm × 297mm)
- Original Implementation: Based on 8163 shipping label format (US Letter)

## Related Files

- `src/templates/xelatexTemplate.tex` - XeLaTeX template with geometry
- `src/templates/latexTemplate.tex` - pdfLaTeX template with geometry  
- `src/latex_generator.py` - Label generation logic
- `README.md` - User-facing documentation
- `docs/FILE_STRUCTURE.md` - Output format documentation
- `docs/QA.md` - Implementation Q&A

---

**Status**: ✅ Implemented  
**Testing**: ⚠️ Requires print test on actual label sheets  
**Breaking Change**: Yes - requires label regeneration for existing libraries