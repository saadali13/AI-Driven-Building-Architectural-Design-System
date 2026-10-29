# Master Implementation Plan V3: Architectural AI Platform

**Document:** `implementation_plan_v3.md`  
**Revision:** 3.0 (Post Independent Audit & Governance Gating)  
**Date:** September 17, 2026  
**Architecture Lead:** Antigravity AI Engineering Team  

---

## 1. Executive Principles of V3

1. **Strict Dataset Governance Before Code**: No model training proceeds without release-specific license verification and immutable provenance records in `data/dataset_manifest.json`.
2. **Golden 50 Benchmark Before Algorithm Tuning**: A 50-plan human-verified ground truth is constructed *before* tuning vision and segmentation algorithms to prevent developing against subjective visual inspection.
3. **Multi-Signal Door-Aware Segmentation**: Doorway handling does not permanently turn doors into walls; it utilizes a dual-path representation: temporary closure for seeded watershed segmentation, while permanently recording door openings in the connectivity graph.
4. **Unified Hybrid Pipeline (Raster + DXF)**: Preserves existing strong DXF CAD parsing and computational geometry engines, fusing both raster CV and CAD entities into a single canonical architectural model.
5. **Preservation of V4 Semantic Discipline**: Geometry-only enclosed areas are strictly classified as `unclassified_closed_region` unless supported by explicit text labels or specialized fixtures.
6. **Controlled Synthetic Rasterization**: Bridges the gap between vector training data (ResPlan) and messy real-world scans by rendering vector plans into diverse synthetic raster styles with pixel-perfect vector ground truth.

---

## 2. 16 Gated Implementation Phases

```
[Phase 0: Governance & Manifest] ──PASS──> [Phase 1: Dataset Cleanup] ──PASS──> [Phase 2: Golden 50 Benchmark]
                                                                                               │
┌──────────────────────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 3: Raster Preprocessing] ──PASS──> [Phase 4: OCR & Dimensions] ──PASS──> [Phase 5: Wall/Opening Detection]
                                                                                               │
┌──────────────────────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 6: Multi-Signal Room Seg] ──PASS──> [Phase 7: Semantic Fusion] ──PASS──> [Phase 8: Spatial Graph]
                                                                                               │
┌──────────────────────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 9: Canonical Model] ──PASS──> [Phase 10: RAG & Hybrid Search] ──PASS──> [Phase 11: Staged Layout Solver]
                                                                                               │
┌──────────────────────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 12: Layered DXF Export] ──PASS──> [Phase 13: Blender 3D Engine] ──PASS──> [Phase 14: Facade Synthesis]
                                                                                               │
┌──────────────────────────────────────────────────────────────────────────────────────────────┘
▼
[Phase 15: End-to-End Evaluation & CLI]
```

---

### Phase 0: Dataset Governance, Licensing & Manifest Isolation
- **Goal:** Enforce legal boundaries, verify release-specific licenses, create auditable manifests.
- **Deliverables:** `data/dataset_manifest.json`, `dataset/governance.py`.
- **Implementation:** Mechanical loader refusing to load datasets flagged `"commercial_use": false` during production training. Pinned commit tracking for ResPlan GitHub CC BY 4.0 data release.
- **Gate Criteria:**
  - `data/dataset_manifest.json` fully validated with all mandatory provenance fields.
  - Automated test verifying loader rejects non-commercial datasets when `--commercial` flag is set.
- **Status:** **READY TO EXECUTE**.

---

### Phase 1: Local Dataset Cleanup & Stress-Set Isolation
- **Goal:** Quarantine duplicates, classify image quality, establish stress categories.
- **Deliverables:** `scripts/cleanup_pilot_dataset.py`, `data/stress_set/manifest.json`.
- **Implementation:** Quarantine 2 exact duplicate pairs (`1/dc63...`, `5/5673...`) and isolate cross-folder near-duplicates (`3/7060...` $\leftrightarrow$ `10/6a0b...`). Isolate the 185 unique pilot images into `data/evaluation_only/pilot_stress_187/`.
- **Gate Criteria:**
  - Zero exact duplicates in active corpus.
  - Zero cross-split contamination.
  - Stress images categorized by failure challenge (low-res, color marketing, dense furniture, dimension-heavy).

---

### Phase 2: Golden 50 Ground-Truth Benchmark Protocol & Creation
- **Goal:** Construct a 50-plan human-verified evaluation dataset *before* algorithm development.
- **Deliverables:** `data/ground_truth/golden_50/`, `dataset/benchmark_validator.py`.
- **Stratification:**
  - 1–2 Bedroom: 10 plans
  - 3 Bedroom: 15 plans
  - 4+ Bedroom: 10 plans
  - Irregular / L-shaped: 5 plans
  - Duplex / Multi-storey: 5 plans
  - Unusual / Commercial residential: 5 plans
- **Ground Truth Entities:** Complete verified vectors for building boundary, walls, doors, windows, room polygons, room types, adjacency, door connectivity, and dimensions.
- **Gate Criteria:**
  - Exactly 50 plans with 100% human-verified ground truth stored in immutable JSON format.
  - Baseline evaluation harness ready to compute mIoU, Precision, Recall, and Graph Edit Distance.

---

### Phase 3: Raster Preprocessing & Resolution Gating
- **Goal:** Normalization, deskewing, title block masking, multi-scale pyramid generation.
- **Deliverables:** `vision/preprocessing/normalizer.py`, `vision/preprocessing/deskew.py`.
- **Implementation:** Automated resolution gate (images with min dimension $<600$px tagged as low-res), outer margin border suppression, and contrast enhancement.
- **Gate Criteria:**
  - Deskew accuracy $\pm 0.5^\circ$ on rotated test plans.
  - Border suppression cleans $\ge 85\%$ of bordered marketing sheets.
  - Non-destructive processing: original images preserved byte-for-byte.

---

### Phase 4: High-Fidelity OCR & Architectural Dimension Engine
- **Goal:** Extract text strings, room labels, and dimensions with architectural post-processing.
- **Deliverables:** `vision/ocr/engine.py`, `extraction/dimensions.py`.
- **Implementation:** EasyOCR CRAFT+LSTM with UTF-8 stdout configuration, multi-scale tile upscaling for small text, regex dimension parser (Imperial/Metric), and Levenshtein abbreviation corrector (`DIBATH` $\rightarrow$ `BATH`).
- **Gate Criteria:**
  - Character Error Rate (CER) $\le 8\%$ on plans $\ge 800$px.
  - Dimension parser extracts $\ge 85\%$ of visible dimension annotations.
  - Computed scale factor (pixels-to-meters) paired with confidence score.

---

### Phase 5: Architectural Wall & Opening Detection
- **Goal:** Detect walls, door swings, window segments, and structural fixtures.
- **Deliverables:** `vision/detection/walls.py`, `vision/detection/openings.py`.
- **Implementation:** Stroke-width filtering ($\ge 4$px for walls, $\le 2$px for leader lines), curvature-based door swing arc detector, and exterior wall window edge filtering.
- **Gate Criteria:**
  - Door swing detection precision $\ge 80\%$ on standard 90° swings.
  - Exterior windows associated with valid exterior wall segments.
  - Zero door swings floating in empty exterior space.

---

### Phase 6: Multi-Signal Room Segmentation & Geometry Snapping
- **Goal:** Extract watertight room polygons without doorway leakage or topology falsification.
- **Deliverables:** `vision/room_detection/segmentation.py`, `extraction/geometry.py`.
- **Implementation:** Multi-signal door-aware architecture: temporary virtual threshold bridging *strictly* during distance-transform calculation for Watershed segmentation seeded by verified OCR text centroids; permanent preservation of door openings in spatial graph. Douglas-Peucker simplification ($\epsilon=2.0$px) and collinear edge snapping.
- **Gate Criteria:**
  - Room leakage rate $<10\%$ on Golden Benchmark.
  - Room overlap area $= 0.00\text{ m}^2$.
  - $\ge 98\%$ valid closed Shapely polygons.

---

### Phase 7: Multi-Modal Semantic Fusion (Preserving V4 Discipline)
- **Goal:** Classify rooms using multimodal evidence; strictly prevent hallucination.
- **Deliverables:** `extraction/rooms.py`, `extraction/semantics.py`.
- **Implementation:** Multi-modal fusion: OCR text label (weight 0.6) + area/proportions (weight 0.2) + fixtures (weight 0.2). Enforce V4 rule: closed polygon without text/fixtures is classified as `unclassified_closed_region`.
- **Gate Criteria:**
  - Classification accuracy $\ge 90\%$ on labeled rooms.
  - 100% compliance with V4 semantic discipline (zero unlabelled regions hallucinated as bedrooms/baths).

---

### Phase 8: Computational Spatial Relationship Graph
- **Goal:** Build rich topological connectivity and circulation networks.
- **Deliverables:** `extraction/relationships.py`.
- **Implementation:** NetworkX graph construction with 4 distinct edge types: `via_door` (physical access), `adjacency` (shared wall), `direct` (open-plan connection), and `via_window` (visual connection).
- **Gate Criteria:**
  - Adjacency precision $\ge 90\%$ on Golden Benchmark.
  - Physical door access path verified for every habitable room.

---

### Phase 9: Canonical Architectural Model Integration (Raster + DXF)
- **Goal:** Unified data format representing building, site, levels, walls, openings, and graph.
- **Deliverables:** `dataset/schema/canonical.py`, `cad/parser.py`.
- **Implementation:** Strict Pydantic models supporting both raster extraction and CAD DXF parser outputs. Multi-floor vertical alignment parameters included.
- **Gate Criteria:**
  - 100% JSON schema validation compliance.
  - Both Raster pipeline and DXF parser deserialize into identical Canonical Architectural Model.

---

### Phase 10: Architectural RAG & Hybrid Vector Retrieval
- **Goal:** Natural-language architectural document synthesis and semantic search.
- **Deliverables:** `dataset/rag_generator.py`, `retrieval/vector_store.py`.
- **Implementation:** Architectural summary generator + FAISS dense embeddings (`all-MiniLM-L6-v2`) + structured SQL metadata filtering (plot size, room count, area).
- **Gate Criteria:**
  - Hybrid search query returns relevant plans with semantic similarity $>0.75$ and 100% metadata filter compliance.

---

### Phase 11: Constraint-Based Layout Generation (5-Stage Staged Solver)
- **Goal:** Generate valid 2D floor plans from natural-language requirements.
- **Deliverables:** `requirements/parser.py`, `generation/solver.py`, `generation/validation.py`.
- **Implementation:** 
  - Requirement parser classifying Hard vs Soft vs Ambiguous vs Unsupported requirements.
  - Google OR-Tools CP-SAT solver executed in 5 stages: Stage 1 (Orthogonal room packing) $\rightarrow$ Stage 2 (Circulation spine) $\rightarrow$ Stage 3 (Graph adjacency) $\rightarrow$ Stage 4 (L-shape decomposition) $\rightarrow$ Stage 5 (Multi-floor alignment).
  - Validation engine checking `geometrically_valid`, `architecturally_valid`, and circulation connectivity.
- **Gate Criteria:**
  - Generates 3 distinct candidates satisfying $\ge 90\%$ of requested constraints.
  - 100% rejection of plans with room overlaps or orphan rooms. Hard solver timeout $\le 15$ seconds.

---

### Phase 12: Layered AutoCAD DXF Generation
- **Goal:** Production CAD files derived directly from canonical geometry.
- **Deliverables:** `cad/dxf_generator.py`.
- **Implementation:** `ezdxf` layered drafting engine (`WALL`, `DOOR`, `WINDOW`, `ROOM_LABEL`, `DIMENSION`) producing clean 2D polylines, arcs, and text.
- **Gate Criteria:**
  - DXF files open cleanly in AutoCAD / FreeCAD without geometry corruption.
  - Real-world metric/imperial scale matches canonical dimensions.

---

### Phase 13: Procedural 3D Blender Generation
- **Goal:** Extrude 2D plans into watertight 3D building models.
- **Deliverables:** `three_d/blender_generator.py`.
- **Implementation:** Headless Blender 5.1 Python script extruding walls, cutting window/door openings with boolean modifiers, creating floors/ceilings, and generating roof geometry.
- **Gate Criteria:**
  - Headless Blender execution exits with code 0.
  - Exports clean GLTF/GLB models and perspective renders.

---

### Phase 14: Exterior Facade Synthesis & Multi-View Rendering
- **Goal:** Generate authentic exterior representations aligned with 2D plan perimeters.
- **Deliverables:** `three_d/facade_generator.py`.
- **Implementation:** Parametric facade grammar applying exterior materials (brick, stucco, timber), window trims, and roof eaves to 3D extruded geometry.
- **Gate Criteria:**
  - Horizontal window/door openings 100% collinear with 2D floor plan exterior perimeters.
  - Perspective, front elevation, and rear elevation rendered images produced.

---

### Phase 15: End-to-End System Integration & Evaluation
- **Goal:** Complete end-to-end pipeline execution from user prompt to CAD and 3D.
- **Deliverables:** `run_pipeline.py`, `api/server.py`, `reports/final_evaluation.html`.
- **Gate Criteria:**
  - Full end-to-end flow executes in $<45$s on GPU / $<90$s on CPU.
  - Complete report detailing extraction metrics, layout generation scores, CAD export validity, and 3D render outputs.
