# Detailed Audit of Existing Pilot Dataset (~187 Images)

**Document:** `reports/existing_dataset_audit.md`  
**Date:** September 17, 2026  
**Auditor:** Antigravity System Architecture Team  
**Companion File:** `reports/existing_dataset_audit.json`

---

## 1. Inventory & Directory Breakdown

An automated programmatic scan was performed on all image assets across directories `1/`, `3/`, `5/`, `7/`, and `10/`. 

| Directory | Image Count | Primary Visual Format | Average File Size |
| :--- | :--- | :--- | :--- |
| **`1/`** | 26 | JPEG / PNG (2 High-Res PNGs) | ~215 KB |
| **`3/`** | 40 | JPEG | ~128 KB |
| **`5/`** | 41 | JPEG | ~112 KB |
| **`7/`** | 42 | JPEG | ~165 KB |
| **`10/`** | 38 | JPEG | ~98 KB |
| **Total** | **187 images** | **185 JPEG, 2 PNG** | **~143 KB avg** |

---

## 2. Cryptographic & Perceptual Duplicate Audit

Using MD5 cryptographic hashing and 64-bit difference perceptual hashing (`dHash` / `aHash`), we discovered significant redundancy and cross-folder data contamination:

### Exact Duplicates (Identical MD5)
1. `1/dc63fcbef5792c11a0630cf42b1b279a (1).jpg` $\equiv$ `1/dc63fcbef5792c11a0630cf42b1b279a.jpg`  
   *Exact byte-for-byte duplicate within directory 1.*
2. `5/56734469ec2d1b6642d46f696542f158 (1).jpg` $\equiv$ `5/56734469ec2d1b6642d46f696542f158.jpg`  
   *Exact byte-for-byte duplicate within directory 5.*

### Cross-Folder Near-Duplicates & Multi-Resolution Leaks
1. **Cross-Folder Leak 1**:  
   - `3/70607f869fb7db58226ecd20e74f185d.jpg` (Resolution: $937 \times 1703$ px)  
   - `10/6a0b981cfe8407c963ab6686608d2cde.jpg` (Resolution: $564 \times 1025$ px)  
   - *Analysis:* Identical floor plan drawing downscaled and duplicated into folder 10. Perceptual Hamming distance: 2.
2. **Cross-Folder Leak 2**:  
   - `5/62d5c958516588e9756a20568ad5f365.jpg` (Resolution: $669 \times 1228$ px)  
   - `10/cb33831c86d1f16db29ad58bf9e926f3.jpg` (Resolution: $236 \times 433$ px)  
   - *Analysis:* Identical design downscaled into an extreme thumbnail. Perceptual Hamming distance: 2.

> [!WARNING]
> **Data Leakage Risk**: If folders `1`, `3`, `5`, `7`, and `10` were naively used as training vs validation splits, cross-folder duplicates would cause **direct data leakage** where the validation set evaluates designs already memorized during training.

---

## 3. Resolution, Aspect Ratio & Scale Audit

| Metric | Measured Value | Architectural Implication |
| :--- | :--- | :--- |
| **Minimum Width** | $236$ px | Extreme thumbnail (`10/cb33831c86d1f16db29ad58bf9e926f3.jpg`). Text illegible. |
| **Maximum Width** | $1,200$ px | Standard web scan (`7/0162fa659d7392157fc0854ef058f419.jpg`). |
| **Minimum Height** | $150$ px | Severely compressed thumbnail. Completely unusable for dimension OCR. |
| **Maximum Height** | $2,361$ px | High vertical resolution plan (`7/218d6139c2794cb1f417f7b3117469a4.jpg`). |
| **Average Resolution**| $751.0 \times 1205.1$ px | Moderate web marketing resolution. |
| **Low-Res Plans ($<800$px)**| **142 of 187 (75.9%)** | **Critical Vulnerability**: 76% of images lack sufficient DPI for small font OCR. |
| **High-Res Plans ($\ge 1500$px)**| **34 of 187 (18.2%)** | Only ~18% provide crisp architectural drafting line definition. |
| **Aspect Ratio Range**| $0.31$ to $1.68$ | Extreme vertical plans (row houses/townhouses) to wide bungalow plans. |

---

## 4. Visual Style & Color Distribution

Architectural drawings in the pilot collection fall into three distinct visual categories:
1. **Monochromatic Blueprint / Line Drawings ($69$ images, $36.9\%$)**:
   - Color variance $< 2.0$.
   - Black lines on white/cream paper.
   - Best suited for classical morphological wall extraction, but vulnerable to faint or broken scan lines.
2. **Subtle Tint / Shaded Room Plans ($52$ images, $27.8\%$)**:
   - Color variance between $2.0$ and $10.0$.
   - Rooms filled with light pastel colors (e.g., light blue for bathrooms, yellow for bedrooms).
   - Causes standard Otsu binarization to merge walls with room interiors if not processed in HSV/Lab space.
3. **Full-Color Marketing Presentations ($66$ images, $35.3\%$)**:
   - Color variance $\ge 10.0$.
   - Heavy wood textures on floors, green grass on lawn/courtyards, photographic furniture rendering.
   - **Severe CV failure mode**: Texture gradients create thousands of false wall edges under Canny or Sobel operators.

---

## 5. Architectural Element & Program Representation

| Feature | Estimated Frequency in Pilot | Observed Real-World Behavior & Failure Modes |
| :--- | :--- | :--- |
| **Text Room Labels** | Present in ~78% of plans | Mixed uppercase ("BEDROOM") and abbreviations ("MBR", "KIT", "BATH", "TOI"). Rotated 90° in corridors. |
| **Architectural Dimensions**| Present in ~62% of plans | Imperial ($12' \times 14'$, $10'\text{-}6''$) predominates over Metric ($3.5 \times 4.2\text{m}$). Dimension lines often cross wall lines, breaking wall continuity. |
| **Scale Bars / Numerical Scale**| Present in $<5\%$ of plans | Near-zero explicit graphical scale bars ($1:100$, $1/4'' = 1'$). Real-world scale must be inferred from dimension annotations. |
| **Dense Furniture** | Present in ~68% of plans | Beds, sofas, tables, dining chairs, stoves, and toilets frequently intersect wall boundaries. |
| **Door Swings** | Present in ~74% of plans | Rendered as quarter-circle arcs (some single line, some dashed, some double line). |
| **Windows** | Present in ~70% of plans | Rendered as double thin lines, empty wall gaps, or shaded rectangular inserts. |
| **Staircases** | Present in ~42% of plans | Parallel line hatched treads with directional arrows ("UP" / "DN"). Often detected erroneously as wall groupings by classical CV. |
| **Multi-Floor Plans** | Present in ~24% of images | Ground floor and first floor placed side-by-side on the same sheet. Single-image ingestion confuses this as one giant house. |
| **Title Blocks & Watermarks**| Present in ~31% of images | Real estate logos, architect credits, and social media watermarks located along borders. |

---

## 6. Real-World Stress Test Findings

During automated stress tests on representative pilot images (documented in `reports/sample_stress_test.json`):
1. **Low-Resolution Failure (`10/cb33831c...`, $236 \times 433$ px)**:
   - Extracted text items: 2 ("Ground Floor", "Plan").
   - Extracted dimensions: 0. Extracted rooms: 0.
   - *Conclusion:* Sub-800px images cannot be used for OCR-based dimension or room extraction without prior SR (super-resolution) or filtering.
2. **Wall Gap & Room Flooding Failure (`1/download.png`, $1152 \times 2048$ px)**:
   - Doorway openings create gaps in the binarized wall mask.
   - Connected-component flood fill leaked through the doors, merging 6 separate rooms into 1 giant exterior polygon.
   - *Conclusion:* Pure morphological thresholding is insufficient; topological wall completion (Hough line snapping or trained wall segmentors) is mandatory.
3. **Architectural Abbreviations & OCR Noise**:
   - OCR recognized `"DIBATH"`, `"IOXo"`, `"WASIAREA"`.
   - *Conclusion:* Hardcoded exact-string matching fails; a semantic vocabulary dictionary with Levenshtein fuzzy distance matching is required.

---

## 7. Audit Verdict

- **Pilot Sufficiency**: The 187 images are **valid for prototype pipeline development, schema hardening, and unit test fixtures**.
- **AI Training Sufficiency**: **INSUFFICIENT (P0 Critical)**. With 2 exact duplicates, cross-folder leakage, 76% low-resolution files, and absence of ground-truth vector annotations, training an ML model from scratch on these 187 images would result in severe overfitting and immediate generalization failure.
