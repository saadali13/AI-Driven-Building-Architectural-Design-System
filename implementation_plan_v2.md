# Master Implementation Plan V2: Architectural AI Platform

**Document:** `implementation_plan_v2.md`  
**Revision:** 2.1 (Audited Post Real-World Dataset & Engineering Challenge)  
**Date:** September 17, 2026  
**Architecture Lead:** Antigravity AI Engineering Team  

---

## Strategic Shift from V1 to V2.1

Following our comprehensive audit of the 187-image pilot collection, external datasets (ResPlan, CubiCasa5k), and real-world failure analyses:
1. **The 185 unique pilot images are designated strictly as a noisy stress-test suite**, not a training dataset.
2. **ResPlan (2025) (17,000 vector records, ~11,200 unique design families)** is our core training backbone under **CC BY 4.0**, ensuring full commercial safety.
3. **CubiCasa5k (CC BY-NC 4.0) is strictly restricted to an evaluation benchmark** to keep production weights unencumbered.
4. **Doorway Leakage Failure Solved**: Morphological room segmentation now includes **virtual door-gap bridging** before computing closed room polygons.
5. **Brittle Absolute Criteria Replaced**: Replaced unrealistic "100% closures" with a **5-layer measurable metric hierarchy** (Vision, Geometry, Semantic, Graph, End-to-End).
6. **Staged Solver Architecture**: Google OR-Tools CP-SAT starts with orthogonal room packing (Stage 1) and progresses to corridors (Stage 2), graph alignment (Stage 3), and multi-floor alignment (Stage 4).

---

## 20 Gated Implementation Phases & Measurable Engineering Criteria

```
[Phase 0: Research & Licensing] ──PASS──> [Phase 1: Deduplication & Clean] ──PASS──> [Phase 2: Preprocessing]
                                                                                              │
┌────────────────────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 3: OCR Engine] ──PASS──> [Phase 4: Symbol Detection] ──PASS──> [Phase 5: Room Segmentation]
                                                                                │
┌───────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 6: Geometry Snap] ──PASS──> [Phase 7: Classification] ──PASS──> [Phase 8: Spatial Graph]
                                                                               │
┌──────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 9: Canonical Model] ──PASS──> [Phase 10: Human Ground Truth (Golden 50)] ──PASS──> [Phase 11: ML Splits]
                                                                                                  │
┌─────────────────────────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 12: RAG Pipeline] ──PASS──> [Phase 13: Requirement Parser] ──PASS──> [Phase 14: Constraint Generator]
                                                                                    │
┌───────────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 15: Validation Engine] ──PASS──> [Phase 16: DXF / CAD Export] ──PASS──> [Phase 17: Blender 3D]
                                                                                       │
┌──────────────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 18: Exterior Facade] ──PASS──> [Phase 19: End-to-End Application & Benchmark]
```

---

### Phase 0: Dataset Research, Expansion & Licensing Audit
- **Goal:** Establish legal boundaries, identify permissive sources, document candidate datasets.
- **Deliverables:** `reports/web_dataset_sources.md`, `reports/web_dataset_research.md`.
- **Engineering Criteria:**
  - 100% legal clearance verified for core training set (ResPlan confirmed CC BY 4.0).
  - Commercial vs. Non-commercial datasets strictly segregated.
  - Paired elevation sources evaluated and documented.
- **Status:** **PASSED (Verified)**.

---

### Phase 1: Dataset Cleaning, Deduplication & Leakage Prevention
- **Goal:** Eliminate exact duplicates, detect cross-folder near-duplicates, establish strict split grouping.
- **Deliverables:** `scripts/audit_existing_dataset.py`, `reports/existing_dataset_audit.json`.
- **Implementation:** MD5 hash filter, 64-bit dHash perceptual filter, grouping by `design_family_id`.
- **Engineering Criteria:**
  - Exact duplicate count = 0 in cleaned corpus (2 exact duplicates quarantined).
  - Zero cross-split contamination (near-duplicates with Hamming distance $\le 4$ isolated to same split).
  - Cleaned directory structure with immutable raw backups.
- **Status:** **READY TO EXECUTE**.

---

### Phase 2: Image Preprocessing & Adaptive Normalization
- **Goal:** Normalization, deskewing, title block masking, multi-scale pyramid generation.
- **Deliverables:** `vision/preprocessing/normalizer.py`, `vision/preprocessing/deskew.py`.
- **Implementation:** Radon/Hough axis detection, outer border suppression, adaptive contrast enhancement, and minimum resolution gating ($<600$px flagged).
- **Engineering Criteria:**
  - Deskew accuracy $\pm 0.5^\circ$ on rotated test plans.
  - Outer border and title block suppression successful on $\ge 85\%$ of bordered plans.
  - Non-destructive processing: original images preserved byte-for-byte.

---

### Phase 3: High-Fidelity OCR & Dimension Normalization
- **Goal:** Extract text, labels, and dimensions with architectural post-processing.
- **Deliverables:** `vision/ocr/engine.py`, `extraction/dimensions.py`.
- **Implementation:** EasyOCR with UTF-8 stdout fix, multi-scale tile recognition for small fonts, regex parsing for imperial/metric strings, and Levenshtein dictionary correction (`DIBATH` $\rightarrow$ `BATH`).
- **Engineering Criteria:**
  - Character Error Rate (CER) $\le 8\%$ on plans $\ge 800$px.
  - Dimension parser extracts $\ge 85\%$ of visible dimension annotations.
  - Scale factor (pixels-to-meters) computed with explicit confidence score.

---

### Phase 4: Architectural Element Detection (Doors, Windows, Fixtures)
- **Goal:** Detect openings and symbols across varied graphical conventions.
- **Deliverables:** `vision/detection/doors.py`, `vision/detection/windows.py`.
- **Implementation:** Curvature-based swing arc detection, exterior wall window edge filtering, and pre-trained SESYD symbol templates.
- **Engineering Criteria:**
  - Door swing detection precision $\ge 80\%$ on standard 90° swings.
  - Exterior windows associated with valid exterior wall segments.
  - Zero door swings detected floating in open exterior space.

---

### Phase 5: Topological Wall & Room Segmentation (With Doorway Virtual Bridging)
- **Goal:** Extract closed room boundaries without doorway leakage.
- **Deliverables:** `vision/room_detection/segmentation.py`, `extraction/walls.py`.
- **Implementation:** Structural wall isolation + **virtual doorway threshold bridging** (drawing line segments across detected door gaps to seal rooms) + Watershed seeded by confirmed OCR room text centroids.
- **Engineering Criteria:**
  - Room leakage rate $<10\%$ (doors do not cause rooms to merge into exterior flood-fill).
  - Topological polygon validity $\ge 98\%$ on Golden Benchmark.

---

### Phase 6: Canonical Geometry Reconstruction & Centerline Snapping
- **Goal:** Construct shared-wall topological geometry.
- **Deliverables:** `extraction/geometry.py`.
- **Implementation:** Polygon orthogonalization, Douglas-Peucker simplification ($\epsilon = 2.0$px), shared wall edge snapping.
- **Engineering Criteria:**
  - Room overlap area $= 0.00\text{ m}^2$ (no self-intersecting or overlapping room polygons).
  - Interior room corners snapped to orthogonal grid ($| \theta - 90^\circ | \le 5^\circ$ or documented angle).

---

### Phase 7: Multi-Modal Room Semantic Classification
- **Goal:** Categorize rooms even when OCR text is missing or blurred.
- **Deliverables:** `extraction/rooms.py`.
- **Implementation:** Multi-modal fusion: OCR text label (weight 0.6) + area/aspect ratio (weight 0.2) + detected fixtures (bed, toilet, stove) (weight 0.2).
- **Engineering Criteria:**
  - Classification accuracy $\ge 90\%$ on labeled rooms; $\ge 70\%$ plausible assignment on unlabeled rooms.
  - Master bedroom / ensuite bathroom relationships correctly flagged.

---

### Phase 8: Computational Spatial Relationship Graph
- **Goal:** Build rich topological connectivity and adjacency networks.
- **Deliverables:** `extraction/relationships.py`.
- **Implementation:** Shapely geometric predicates (`touches`, `distance < threshold`, door intersections) + NetworkX graph generation.
- **Engineering Criteria:**
  - Adjacency precision $\ge 90\%$ on verified ground truth.
  - Direct door connectivity correctly identified as `connected_to` and `opens_into`.

---

### Phase 9: Canonical Architectural Model Integration
- **Goal:** Unify all extractions into the canonical v1.0 data format.
- **Deliverables:** `dataset/schema/canonical.py`.
- **Implementation:** Strict Pydantic models supporting building, site, levels, walls, rooms, openings, fixtures, scale, and spatial graph.
- **Engineering Criteria:**
  - 100% JSON schema validation compliance.
  - Zero missing mandatory fields; provenance and confidence recorded on every entity.

---

### Phase 10: Human Verification & Golden 50 Benchmark
- **Goal:** Create a 50-plan ground-truth benchmark and review workflow.
- **Deliverables:** `dataset/human_review.py`, `data/ground_truth/golden_50/`.
- **Implementation:** Review tool supporting tri-state immutability: `raw_prediction`, `human_correction`, and `final_ground_truth`.
- **Engineering Criteria:**
  - Exactly 50 diverse floor plans 100% human-verified (geometry, labels, dimensions, graph).
  - Ground truth used as immutable regression test set.

---

### Phase 11: ML Training Dataset Generation
- **Goal:** Export model-specific formats from canonical architecture.
- **Deliverables:** `dataset/exporter.py`.
- **Implementation:** Exporters for COCO object detection, YOLO OBB, semantic segmentation masks, and PyTorch Geometric graph datasets.
- **Engineering Criteria:**
  - Automated export runs without data corruption.
  - Train/Val/Test splits strictly respect project and design-family groupings.

---

### Phase 12: Architectural RAG Dataset & Vector Store
- **Goal:** Synthesize natural-language architectural profiles and semantic indices.
- **Deliverables:** `dataset/rag_generator.py`, `retrieval/vector_store.py`.
- **Implementation:** Architectural summary builder + FAISS index + `all-MiniLM-L6-v2` dense embeddings + structured SQL metadata filters.
- **Engineering Criteria:**
  - Hybrid retrieval query (e.g. "3 bedroom plan with open kitchen under 120m2") returns valid matches with similarity score $>0.75$.

---

### Phase 13: Natural-Language Requirement Parser
- **Goal:** Translate user natural language into structured geometric constraints.
- **Deliverables:** `requirements/parser.py`.
- **Implementation:** Regex heuristic parser + LLM prompt mapping user prompt to plot dimensions, room program, and classifying hard vs soft vs ambiguous constraints.
- **Engineering Criteria:**
  - 100% valid Pydantic constraint JSON.
  - Subjective adjectives ("spacious", "modern") classified into bounded target ranges or soft preferences rather than false precision.

---

### Phase 14: Constraint-Based Layout Generation Engine (Staged Architecture)
- **Goal:** Generate valid 2D floor plans from structured requirements.
- **Deliverables:** `generation/layout.py`, `generation/solver.py`.
- **Implementation:** Staged Google OR-Tools CP-SAT solver: Stage 1 (Orthogonal room packing) $\rightarrow$ Stage 2 (Corridor allocation) $\rightarrow$ Stage 3 (Graph adjacency alignment).
- **Engineering Criteria:**
  - Generates 3 distinct candidate layouts satisfying $\ge 90\%$ of requested constraints.
  - Plot boundary containment $= 100\%$. Hard solver timeout bounded at 15 seconds.

---

### Phase 15: Geometric & Architectural Validation Engine
- **Goal:** Gate all generated plans before CAD/3D export.
- **Deliverables:** `generation/validation.py`.
- **Implementation:** Multi-tier validator checking `geometrically_valid`, `architecturally_valid`, and circulation connectivity.
- **Engineering Criteria:**
  - 100% rejection of plans with room overlaps ($>0.001\text{m}^2$) or orphan rooms disconnected from entrance.
  - Produces detailed validation scorecard for each candidate.

---

### Phase 16: Layered AutoCAD DXF Export
- **Goal:** Generate production CAD files directly from canonical geometry.
- **Deliverables:** `cad/dxf_generator.py`.
- **Implementation:** `ezdxf` layered drafting engine (`WALL`, `DOOR`, `WINDOW`, `ROOM_LABEL`, `DIMENSION`).
- **Engineering Criteria:**
  - DXF files open cleanly in AutoCAD / FreeCAD without geometry corruption.
  - Real-world metric/imperial scale matches canonical dimensions.

---

### Phase 17: Procedural 3D Blender House Generation
- **Goal:** Extrude 2D plans into watertight 3D building models.
- **Deliverables:** `three_d/blender_generator.py`.
- **Implementation:** Headless Blender 5.1 Python script extruding walls, cutting window/door openings with boolean modifiers, creating floors/ceilings, and generating roof geometry.
- **Engineering Criteria:**
  - Headless Blender execution exits with code 0.
  - Exports clean GLTF/GLB models and perspective renders.

---

### Phase 18: Exterior Facade & Elevation Synthesis
- **Goal:** Generate authentic exterior representations aligned with 2D plan perimeters.
- **Deliverables:** `three_d/facade_generator.py`.
- **Implementation:** Parametric facade grammar applying exterior materials (brick, stucco, timber), window trims, and roof eaves to 3D extruded geometry.
- **Engineering Criteria:**
  - Horizontal window/door openings 100% collinear with 2D floor plan exterior perimeters.
  - Perspective, front elevation, and rear elevation rendered images produced.

---

### Phase 19: End-to-End System Integration & Evaluation
- **Goal:** Complete end-to-end pipeline execution from natural language to CAD and 3D.
- **Deliverables:** `run_pipeline.py`, `api/server.py`, `reports/final_evaluation.html`.
- **Engineering Criteria:**
  - Full end-to-end flow executes in $<45$s on GPU / $<90$s on CPU.
  - Complete report detailing extraction metrics, layout generation scores, CAD export validity, and 3D render outputs.
