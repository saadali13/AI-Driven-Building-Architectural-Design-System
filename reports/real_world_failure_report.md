# Real-World Failure Audit Report: Stress Testing the Vision & Geometry Pipeline

**Document:** `reports/real_world_failure_report.md`  
**Date:** September 17, 2026  
**Auditor:** Lead AI/ML & Computational Geometry Engineer (Antigravity)  
**Scope:** Deep diagnostic stress test on 10 representative pilot images covering low-resolution thumbnails, multi-room layouts, color fills, dense furniture, dimension lines, and border noise.

---

## 1. Executive Summary of Failure Modes

Local empirical execution of classical computer vision (Otsu binarization, morphological filtering, connected components, contour finding) and deep OCR on representative floor plans from directories `1/`, `3/`, `5/`, `7/`, and `10/` exposed **five fundamental, reproducible architectural failure modes**.

Crucially, **a 100% failure rate was observed on the 10 adversarial floor plans tested with the current naive morphology/flood-fill implementation**. This is an expected failure mode of naive pixel-level wall binarization and demonstrates why pure morphological thresholding cannot solve architectural floor plans without a higher-level door-aware representation.

---

## 2. Detailed Diagnostic Failure Records

### Failure Case 1: Doorway Leakage via Naive Morphological Flood-Fill
* **Image:** `1/download.png` ($1152 \times 2048$ px) & `1/00770eba...` ($877 \times 1584$ px)
* **Component:** `vision/room_detection/segmentation.py`
* **Expected:** 6 to 8 discrete, watertight room polygons (Bedrooms, Bathrooms, Kitchen, Living Room).
* **Actual:** In the 10 tested plans, a single massive connected component leaked through door openings, covering **60.9% to 99.8%** of the entire image canvas.
* **Root Cause:** Architectural doorways are physical openings in walls. Inverted binary wall masks have holes at every door swing and threshold. A naive flood-fill travels through these door openings, merging interior rooms with circulation corridors and the outer sheet background.
* **Severity:** **HIGH (Algorithmic Flaw of Naive Morphology)**
* **Engineering Fix (Multi-Signal Architectural Wall/Door Graph):** 
  Do NOT simply turn every doorway into an artificial permanent wall (which destroys door semantics and falsifies topology if door detection misfires). Instead, implement a **multi-signal door-aware architecture**:
  ```
  INPUT IMAGE
       │
  ┌────┴────────────┐
  │                 │
  Wall Evidence     Door Evidence
  │                 │
  └────┬────────────┘
       ▼
  Architectural Wall/Door Graph
       │
  ┌────┴──────────────────────────┐
  ▼                               ▼
  Temporary Boundary Closure      Door Opening Preservation
  (for Seeded Watershed only)    (preserved for connectivity graph)
  │                               │
  ▼                               ▼
  Watertight Room Polygons        Room-to-Room Adjacency & Access
  │                               │
  └────┬──────────────────────────┘
       ▼
  Canonical Geometry Model
  ```
  1. Detect wall segments and door openings concurrently as separate architectural entities.
  2. Maintain a formal door opening entity `{ "id": "door_1", "connects": ["room_a", "room_b"], "wall_id": "wall_3" }`.
  3. Apply temporary closure barriers *strictly* during watershed distance-transform calculation (seeded from verified OCR room text centroids), while permanently preserving the door opening in the spatial connectivity graph.

---

### Failure Case 2: Sub-800px Severe Character & Dimension Atrophy
* **Image:** `10/cb33831c86d1f16db29ad58bf9e926f3.jpg` ($236 \times 433$ px) & `10/052da936...` ($474 \times 800$ px)
* **Component:** `vision/ocr/engine.py` & `extraction/dimensions.py`
* **Expected:** Extraction of 4 room labels and 6 dimension strings ($12'\times 14'$, $3.5\text{m}$, etc.).
* **Actual:** OCR detected only 2 generic words ("Ground Floor", "Plan"); extracted **0 dimensions** and **0 room names**.
* **Root Cause:** In sub-800px plans, character stroke height drops below 8–10 pixels. Neural text detectors (CRAFT) and CTC decoders fail when resolution drops below the Nyquist sampling limit for typography. 75.9% of the pilot images fall into this low-resolution regime.
* **Severity:** **HIGH (P1)**
* **Engineering Fix:**
  1. Automated Resolution Gate: Ingested images with min dimension $< 600$px are flagged as `insufficient_resolution_for_ocr`.
  2. Multi-scale bicubic / super-resolution tiling ($2\times$ or $4\times$ Real-ESRGAN / LapSRN) applied specifically to text-dense bounding regions prior to OCR inference.

---

### Failure Case 3: Wood Flooring & Hatch Texture False Wall Edges
* **Image:** `7/0162fa659d7392157fc0854ef058f419.jpg` & `10/cb33831...`
* **Component:** `extraction/walls.py`
* **Expected:** Clean binary separation between structural walls and interior room space.
* **Actual:** Laplacian texture variance exceeded **8,743.2**. Floorboards, tile hatching, and furniture outlines produced thousands of fragmented edge contours, shattering room boundaries into 66–303 micro-noise regions.
* **Root Cause:** Standard Canny and Sobel edge detectors cannot differentiate between an architectural structural wall boundary (a 200mm load-bearing element) and decorative floor surface hatching (a 2D texture).
* **Severity:** **HIGH (P1)**
* **Engineering Fix:**
  1. Structural Wall Thickness Filter: Enforce minimum wall stroke thickness ($>4$px at standard DPI) via directional morphological opening kernels (`MORPH_RECT` $5\times 1$ and $1\times 5$).
  2. HSV / Lab color space decomposition: Remove decorative floor textures by color thresholding before binarization.
  3. Pretrained wall segmentation model (e.g. from ResPlan / CubiCasa5k) which learns semantic wall features rather than low-level gradient edges.

---

### Failure Case 4: Title Blocks, Logos & Border Contamination
* **Image:** `3/0adf5f25feca052f9968d0a9f42bd8eb.jpg` & `5/1dfd85587a24...`
* **Component:** `vision/preprocessing/normalizer.py`
* **Expected:** Isolated architectural floor plan boundary.
* **Actual:** Outer drawing borders, legal disclaimers, real estate logos, and north arrows are fused with exterior walls, distorting the building envelope polygon.
* **Root Cause:** Many scanned drawings have a decorative solid black border 10–20px from the image boundary (`border_darkness > 0.3`).
* **Severity:** **MEDIUM (P1)**
* **Engineering Fix:**
  1. Convex Hull / Outer Contour Isolation: Identify the outermost closed rectangular frame and crop inward by 2% of image dimensions.
  2. Margin edge-density suppression: Zero out connected components that touch the image outer perimeter.

---

### Failure Case 5: Dimension Line Wall Intersection & Occlusion
* **Image:** `7/0162fa659d7392157fc0854ef058f419.jpg` ($1200 \times 1697$ px)
* **Component:** `extraction/dimensions.py` & `extraction/walls.py`
* **Expected:** Dimension leader lines ($|\longleftrightarrow|$) read independently from wall geometry.
* **Actual:** Dimension witness lines cut directly across exterior walls, creating artificial gaps in exterior wall contours and producing false wall junctions.
* **Root Cause:** In architectural presentation drawings, dimension lines are drawn with the same line weight and black color as interior partition walls.
* **Severity:** **MEDIUM (P2)**
* **Engineering Fix:**
  1. Dimension Line Inpainting: Once dimension text and arrowheads are spotted by OCR, inpaint thin leader lines ($<2$px stroke) before extracting structural walls.
  2. Stroke width transform (SWT): Separate thick structural walls ($\ge 4$px) from thin dimension leader lines ($\le 2$px).

---

## 3. Summary Diagnostic Table

| Case | Image ID | Component | Severity | Root Cause | Engineering Solution |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **F-01** | `1/download.png` | `room_segmentation` | **P0 (Critical)** | Doorway openings leak room interiors into exterior | Door threshold virtual bridging + Seeded Watershed |
| **F-02** | `10/cb3383...` | `ocr_dimension` | **P1 (High)** | Character stroke $<8$px in low-res thumbnail | Super-resolution / Min-resolution ingestion gate |
| **F-03** | `7/0162fa...` | `wall_extraction` | **P1 (High)** | Floor texture hatching creates thousands of false walls | Stroke-width transform + HSV color decomposition |
| **F-04** | `3/0adf5f...` | `preprocessing` | **P1 (High)** | Title block & outer sheet borders fused to walls | Border suppression & outermost contour cropping |
| **F-05** | `7/0162fa...` | `dimensions` | **P2 (Med)** | Dimension leader lines cross and break wall masks | Thin-line inpainting prior to wall vectorization |
