# Architectural Dataset Growth Plan & AI Scaling Strategy

**Document:** `reports/dataset_growth_plan.md`  
**Date:** September 17, 2026  
**Auditor:** Antigravity System Architecture Team  

---

## 1. Why 186 Images Are Insufficient for AI Training

Training production-grade computer vision, spatial reasoning, and layout generation models requires statistical generalization across an immense combinatorial space of architectural variables. 186 images fail for the following fundamental mathematical and architectural reasons:

1. **Statistical Power & Sample Size**:
   - Modern deep vision models (YOLOv11, Mask R-CNN, SegFormer, SAM2 adapters) have 20M–100M parameters. Training or fine-tuning them on 186 unannotated images leads to immediate catastrophic overfitting or memorization of noise.
2. **Long-Tail Architectural Diversity**:
   - Architecture exhibits enormous long-tail variation: L-shaped courtyards, split-level living rooms, spiral staircases, pocket doors, Jack-and-Jill ensuite bathrooms, duplex double-height voids, and semi-detached townhomes. A sample of 186 images captures at most 10–15 common 2BHK/3BHK archetypes, missing 90%+ of architectural typologies.
3. **Symbol & Graphical Representation Entropy**:
   - Architectural drafting conventions differ dramatically by country, firm, and software. Doors can be single lines with arcs, double-line swings, bi-fold zig-zags, or sliding arrows. In 186 images, an AI model learns only the specific CAD block library of a few designers.
4. **Resolution & Scan Degradation Disparity**:
   - 75.9% of the pilot images are low-resolution web thumbnails ($<800$px). Models trained on this distribution fail on crisp 4000px architectural blueprints or high-DPI scanned PDF construction drawings.
5. **Absence of Vector Ground Truth**:
   - The pilot images are raw unannotated raster rasters. Without ground-truth polygons, line vectors, and metric scales, they cannot supervise a neural network.

---

## 2. What the Current 186 Images Are Useful For

The 186 pilot images remain highly valuable for the development process:
- **Pipeline Edge-Case Hardening**: They provide an authentic stress-test battery of noisy scans, JPEG compression artifacts, rotated labels, and low DPI.
- **Algorithm Prototyping**: Ideal for developing classical CV filters, Otsu adaptive thresholding, morphological kernels, and Hough line detection.
- **OCR Post-Processing Dictionary**: Useful for building the architectural abbreviation lexicon (`MBR`, `DIBATH`, `KIT`, `WASIAREA`).
- **Schema & RAG Validation**: Serves as test inputs for verifying that the Canonical Schema and RAG text generators handle uncertain or missing fields gracefully.
- **Unit Test Regression Fixtures**: 10–15 representative images will be integrated into CI/CD regression tests.

---

## 3. Staged Expansion Targets by AI Task

Dataset volume requirements are **not uniform** across tasks. Below is the empirically justified dataset scale needed for each architectural capability:

| Architectural AI Task | Pilot Size | Stage 1 Target (Prototype) | Stage 2 Target (Production) | Recommended Data Source | Annotation Format |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **OCR & Text Extraction** | 186 images | 2,000 cropped text patches | 20,000 architectural patches | Pretrained EasyOCR + synthetic architectural text | Bounding box + text string + angle |
| **Wall Segmentation** | 186 images | 500 vector plans | 5,000 diverse plans | ResPlan (2025) + CubiCasa5k | Binary/multiclass polygon masks |
| **Door/Window Detection** | 186 images | 1,000 plans (~8k instances) | 5,000 plans (~40k instances) | ResPlan + SESYD (synthetic) | Oriented bounding box (OBB) / Arcs |
| **Room Semantic Classification**| 186 images | 3,000 room crops | 30,000 room crops | ResPlan + CubiCasa5k | Categorical class + aspect ratio + area |
| **Spatial Relationship Graph**| 0 graphs | 1,000 verified graphs | 17,000 graphs | ResPlan (17k vector graphs) | NetworkX Graph JSON (nodes & edges) |
| **Constraint Layout Generation**| 0 samples | 2,000 vector layouts | 20,000 vector layouts | ResPlan + Synthetic OR-Tools generator | Metric coordinate polygons + constraints |
| **Facade & Exterior Understanding**| 0 images | 500 rectified facades | 5,000 facades + 1,500 paired | CMP Facades + CorbuAI paired set | Semantic facade segmentation + elevation |
| **Procedural 3D Generation** | 0 models | 50 parametric test cases | 1,000 multi-level house plans | Procedural Blender script + Structured3D | Watertight 3D mesh (GLTF/OBJ) |

---

## 4. Missing Categories & Required Diversity Ingestion

The expanded dataset must systematically fill the demographic and architectural voids identified in the pilot audit:

1. **Typologies**:
   - Narrow-lot urban townhouses (width $< 6$m, length $> 18$m).
   - Courtyard houses (central open-to-sky voids).
   - Multi-generation homes (attached granny flats, dual master bedrooms).
   - Luxury villas with swimming pools, porticos, and double-height living areas.
   - Studio and micro-apartments ($< 40\text{m}^2$).
2. **Floor Count**:
   - Single-storey bungalows (60%).
   - Two-storey duplexes with vertical stair alignment (30%).
   - Three-storey / split-level houses (10%).
3. **Room Program Completeness**:
   - Powder rooms (half-baths), walk-in closets (WIC), pantries, mudrooms, utility/laundry rooms, home offices/studies, mechanical rooms.
4. **Symbolic Conventions**:
   - Pocket sliding doors, bi-fold doors, double casement windows, bay windows.
   - U-shaped, dog-legged, and spiral staircases.
   - Kitchen islands, corner sinks, walk-in showers vs bathtubs.

---

## 5. Legally Usable Dataset Ingestion Sources

To ensure complete legal compliance and commercial safety:
1. **Primary Production Training Set (Commercial Safe)**:
   - **ResPlan (2025)**: 17,000 residential plans under Apache 2.0 / Open-Source license. Provides vector walls, room polygons, doors, windows, and connectivity graphs.
   - **Procedurally Synthesized Generator**: In-house constraint solver producing 10,000+ mathematically flawless plans with full DXF and 3D ground truth.
2. **Benchmark & Evaluation Set (Non-Commercial Research Safe)**:
   - **CubiCasa5k (5,000 plans)**: Used strictly for zero-shot testing of the raster vision pipeline on noisy scans.
   - **Structured3D (3,500 3D houses)**: Used to benchmark 2D-to-3D wall extrusion accuracy.
   - **CMP Facades (606 images)**: Used to evaluate facade parsing rules.
3. **Paired Elevation Anchor**:
   - **CorbuAI / C3Po (1,570 paired sets)**: Used to benchmark the alignment between 2D floor plans and 2D building elevations.

---

## 6. Pre-Annotation & Human-in-the-Loop Workflow

Scaling to thousands of annotated plans cannot rely purely on manual CAD drafting. We implement an **Active Learning & Pre-Annotation Pipeline**:

```
Raw Ingested Images / Vectors
               ↓
    Heuristic / Model Pre-Annotation
    (Walls, Rooms, Doors, Windows, OCR)
               ↓
    Automated Topological Validator
    (Geometry sanity, closure, intersections)
       ┌───────┴───────┐
  PASS (Confidence > 0.85)   FLAGGED (Confidence <= 0.85 or Rule Violation)
       ↓                       ↓
Auto-Accepted Dataset     Human Review & Correction Interface
(90% volume)              (10% volume: Room splits, label fixes)
                               ↓
                      Golden Ground Truth Dataset
```

### Golden Benchmark Set
We will construct a curated **Golden Benchmark of 50 Floor Plans** representing:
- 10 clean single-family plans (1, 2, 3, 4, 5 BHK).
- 10 multi-storey duplexes with staircases.
- 10 low-resolution noisy web scans (stress cases).
- 10 textured full-color marketing presentations.
- 10 irregular/L-shaped courtyard villas.
Every single wall centerline, door swing, window, room polygon, and dimension in this Golden 50 will be 100% human-verified.

---

## 7. Preventing Duplicates and Data Leakage

To prevent the cross-folder duplicate contamination uncovered during our pilot audit:
1. **Deduplication Engine**:
   - **MD5 Check**: Eliminate exact file duplicates immediately.
   - **Perceptual dHash / pHash**: Filter out near-duplicates (Hamming distance $\le 4$).
   - **Vector Topology Hash**: Compute graph isomorphism hashes on room adjacency graphs to eliminate identical floor plans drawn in different visual rendering themes.
2. **Grouped Train / Validation / Test Splitting**:
   - Never split images randomly.
   - Group records by `source_id`, `project_id`, and `design_family_id`.
   - If a building has multiple floors (Ground + First) or multiple rendering styles (2D CAD + Color 3D top-down), all variants are assigned strictly to the **same split**.
   - Ensure the Test Set comprises 100% unseen architectural sources.
