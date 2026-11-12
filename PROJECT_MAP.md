# ArchiCraft AI — Comprehensive Project Map & Architecture

## 1. System Overview & High-Level Architecture
**ArchiCraft AI** is an AI-assisted residential architectural CAD system designed specifically for the Pakistani residential typology (5 Marla, 7 Marla, 10 Marla, 1 Kanal / 20 Marla, and custom executive dimensions). It automates the generation of compliant 2D floor plans, front elevations, 3D parametric massing, and Bill of Quantities (BOQ).

* **Technology Stack**:
  * **Backend**: Python 3.10+, FastAPI / Python `http.server` on port 8000, Shapely (spatial polygon geometry), Matplotlib Agg (vector floor plan visualization), ezdxf (AutoCAD DXF export), Google Gemini API (architectural audit & refinement).
  * **Primary Active Frontend**: `archai_frontend/archai_frontend` — React 19, Vite (port 5173), Three.js (interactive 3D massing and elevation viewport), Tailwind CSS v4.
  * **Secondary Legacy Frontend**: `frontend` — React 19, TypeScript, React Router, Vite (preserved management dashboard).

---

## 2. System Entry Points

### 2.1 Backend Entry Points
1. [`api_server.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/api_server.py): Primary HTTP backend server running on `http://localhost:8000`. Exposes `/generate`, `/health`, `/export_dxf`, `/refine_design`, `/projects`, and serving static visualizer renders.
2. [`pipeline_runner.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/pipeline_runner.py): Command-line batch execution engine for generating designs directly to disk without running the web server.
3. [`run_app.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/run_app.py): Convenience bootstrap runner to start both backend and frontend processes.
4. [`start_system.bat`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/start_system.bat): Windows batch script initializing the backend server and frontend dev server simultaneously.

### 2.2 Frontend Entry Points
1. **Primary Frontend (`archai_frontend/archai_frontend`)**:
   * `index.html` $\to$ `src/main.jsx` $\to$ `src/App.jsx`.
   * Houses the active ArchiCraft Studio: 2D plan viewer, interactive Three.js 3D viewport, architectural parameter inputs, and real-time generation controls.
2. **Secondary Frontend (`frontend`)**:
   * `index.html` $\to$ `src/main.tsx` $\to$ `src/App.tsx` $\to$ `src/pages/designs/NewDesignPage.tsx`.
   * Preserved architectural management dashboard.

### 2.3 Automated Test Suites & Benchmarks
* **Unit & Integration Tests**: Executed via `pytest tests/` (covers spatial solvers, door clearance, diversity engine, quality gate, DXF generation).
* **End-to-End & Playwright**: [`run_playwright_test_suite.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/run_playwright_test_suite.py), [`benchmark_stages.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/benchmark_stages.py), [`test_system_diversity_multi_scale.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/test_system_diversity_multi_scale.py).

---

## 3. Reachable Core Python Module Graph

Tracing all imports originating from `api_server.py` and `pipeline_runner.py` yields **46 reachable core modules**. Each module's specific responsibility is documented below:

### 3.1 Requirements & Site Geometry
* [`requirements/parser.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/requirements/parser.py): Parses raw client requirements (plot dimensions, bedroom count, luxury tier) into normalized design constraints.
* [`requirements/site_geometry.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/requirements/site_geometry.py): Constructs Shapely plot boundary polygons, computes party lines, and validates overall site aspect ratio.

### 3.2 Geometric Spatial Solvers & Diversity Engines
* [`generation/setback_engine.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/setback_engine.py): Enforces mandatory municipal setbacks (front, rear, side) per Pakistani bylaws (LDA, CDA, DHA) to produce the valid buildable footprint.
* [`generation/strategy_selector.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/strategy_selector.py): Selects spatial zoning strategies (central courtyard, side corridor, split duplex, rear lawn) based on plot category.
* [`generation/rag_matcher.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/rag_matcher.py): Retrieves nearest-neighbor reference floor plans from vector knowledge base using topological graphs.
* [`generation/rag_similarity_matcher.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/rag_similarity_matcher.py): Mathematical graph-similarity matcher ranking archetypes by room adjacency and setback overlap.
* [`generation/rag_solver.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/rag_solver.py): Adapts retrieved catalog archetypes to exact requested plot boundaries while maintaining room aspect ratios.
* [`generation/solver.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/solver.py): Core geometric constraint solver placing room rectangles with zero overlaps inside buildable envelope.
* [`generation/irregular_solver.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/irregular_solver.py): Specialized geometric solver handling non-orthogonal, chamfered, and trapezoidal plots.
* [`generation/design_diversity_engine.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/design_diversity_engine.py): Primary orchestrator coordinating RAG retrieval, parametric variations, and multi-floor synthesis.
* [`generation/structural_signature.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/structural_signature.py): Generates topological hash signatures for plans to guarantee distinct layout variations.
* [`generation/duplicate_detector.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/duplicate_detector.py): Calculates IoU and topological similarity to prevent delivering redundant plan variations.

### 3.3 Architectural Validation, Clearance & Quality Gate
* [`generation/door_clearance_engine.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/door_clearance_engine.py): Hosts doors on physical wall segments, punches cutouts, and verifies 90-degree swept arcs with zero furniture collisions.
* [`generation/compliance_engine.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/compliance_engine.py): Validates minimum room dimensions, mandatory setbacks, natural lighting, and stair mumty heights.
* [`generation/architectural_validator_engine.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/architectural_validator_engine.py): High-level architectural sanity auditor ensuring vertical plumbing alignment and eliminating landlocked rooms.
* [`generation/quality_gate.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/quality_gate.py): Hard gating engine scoring floor plans; blocks any invalid design from reaching UI or DXF export.
* [`generation/fidelity_guard.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/fidelity_guard.py): Prevents geometric drift between floor plan revisions and user edits.
* [`generation/plan_quality_scorer.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/plan_quality_scorer.py): Composite scoring engine evaluating circulation efficiency, natural ventilation, and privacy zoning.
* [`generation/plan_edit_applier.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/plan_edit_applier.py): Applies user-requested modifications (resizing rooms, flipping orientation, adding powder room).
* [`generation/improvement_parser.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/improvement_parser.py): Translates natural language refinement requests into geometric modification parameters.

### 3.4 Elevation & 3D Synthesis
* [`generation/floor_plan_to_elevation_mapper.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/floor_plan_to_elevation_mapper.py): Extracts 1:1 front-facing coordinates (porch plinth, front window bays, entrance door, balcony) for elevation generation.
* [`generation/dynamic_elevation_generator.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/dynamic_elevation_generator.py): Parametric 2D front elevation generator producing SVG/PNG facades strictly coherent with ground floor coordinates.
* [`generation/elevation_engine.py`](file:///C:/Users/m/OneDrive/Desktop/New%20floor/generation/elevation_engine.py): Orchestrates front elevation rendering across Pakistani styles (Modern, Neoclassical, Spanish, Contemporary).
* [`generation/elevation_engine/elevation_builder.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/elevation_engine/elevation_builder.py): Builds parametric elevation masses, floor plinths, lintels, and parapet walls.
* [`generation/elevation_engine/elevation_svg_renderer.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/elevation_engine/elevation_svg_renderer.py): Renders vector SVG elevation with architectural hatching, shadows, and window mullions.
* [`generation/elevation_engine/elevation_dxf_exporter.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/elevation_engine/elevation_dxf_exporter.py): Exports layered CAD DXF elevations with industry-standard lineweights.
* [`three_d/blender_generator.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/three_d/blender_generator.py): Extrudes 2D floor plan polygons into 3D parametric massing models (OBJ/GLTF/SKP).

### 3.5 Visualization, CAD Export & AI Auditor
* [`generation/visualizer.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/visualizer.py): Generates 2D blueprint renders (Matplotlib Agg / SVG) with Pakistani architectural room styling and dimension strings.
* [`cad/dxf_generator.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/cad/dxf_generator.py): Produces production-ready AutoCAD DXF blueprints with dedicated layers (WALLS, DOORS, WINDOWS, TEXT, DIMS).
* [`cad/parser.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/cad/parser.py): Reads existing DXF files into Shapely geometric entities.
* [`cad/asset_loader.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/cad/asset_loader.py): Loads reusable CAD furniture blocks (car, beds, sanitary ware) into DXF blueprints.
* [`generation/gemini_service.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/gemini_service.py): Client wrapper connecting to Google Gemini API for architectural suggestions.
* [`generation/gemini_architectural_auditor.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/generation/gemini_architectural_auditor.py): AI audit engine reviewing plan layouts against aesthetic guidelines.
* [`config/gemini_config.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/config/gemini_config.py): API key configuration and rate-limiting thresholds.

### 3.6 Catalogs & Schema Specifications
* [`dataset/schema/canonical.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/dataset/schema/canonical.py): Canonical JSON schema definition for all floor plan dataset entries.
* [`dataset/catalog_3_marla.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/dataset/catalog_3_marla.py): Hand-crafted archetypes for 3 Marla ($18'\text{-}0'' \times 38'\text{-}0''$) plots.
* [`dataset/catalog_5_marla.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/dataset/catalog_5_marla.py): Verified archetypes for 5 Marla ($25'\text{-}0'' \times 45'\text{-}0''$) plots.
* [`dataset/catalog_7_marla.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/dataset/catalog_7_marla.py): Verified archetypes for 7 Marla ($30'\text{-}0'' \times 52'\text{-}6''$) plots.
* [`dataset/catalog_10_marla.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/dataset/catalog_10_marla.py): Verified archetypes for 10 Marla ($35'\text{-}0'' \times 65'\text{-}0''$) plots.
* [`dataset/catalog_1_kanal.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/dataset/catalog_1_kanal.py): Verified archetypes for 1 Kanal ($50'\text{-}0'' \times 90'\text{-}0''$) plots.
* [`dataset/build_master_catalog.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/dataset/build_master_catalog.py): Aggregates individual Marla catalogs into `dataset/master_catalog.json`.
* [`dataset/rag_generator.py`](file:///C:/Users/m/OneDrive/Desktop/New%20folder/dataset/rag_generator.py): Ingests extracted vector plans into the active RAG retrieval index.

---

## 4. Standalone & Specialized Python Modules (Non-Entry-Point)

Out of 618 Python files in the workspace, 572 are standalone, categorized below:

1. **Automated Test Suite (`tests/`, 54 files)**:
   * Test suites verifying multi-scale diversity, door clearance, vertical plumbing stacking, irregular plots, and regression benchmarks. All are active and kept.
2. **Benchmark & Evaluation Suite (`benchmark/`, `scripts/`, 38 files)**:
   * Batch generation testing and benchmark suites (`scripts/run_variation_matrix.py`, `benchmark/benchmark_20_archetypes.py`).
3. **Legacy CV Agent Pipeline (`cv_agent/`, 14 files)**:
   * Earlier experimental computer vision scanner and dimension extractor. Kept for historical reference.
4. **Legacy Extraction Pipeline (`extraction/`, 7 files)**:
   * Pre-Attempt-8 batch extraction scripts (`extraction/gemini_dataset_extractor.py`, `extraction/batch_dataset_extractor.py`).
5. **Blender Headless Workers (`three_d/`, 3 files)**:
   * Worker scripts executing headless Blender mesh generation (`blender_headless_worker.py`).
6. **One-Off Root Investigation Scripts (8 files)**:
   * Developer utilities (`render_4_styles.py`, `insert_compliance.py`, `generate_contact_sheet.py`, `debug_synthesis.py`, `benchmark_stages.py`, `patch_new_design_page.py`, `test_exports.py`, `scratch_test_multi_scale.py`). Candidates for archiving into `_cleanup_quarantine/`.
7. **Pilot Extraction Iteration Scripts (`output/code/`, 40+ files)**:
   * Scripts created during Attempts 1 through 9 for pilot plan `00770eba64db20501bbd30bb21ce6aa5`. Marked `HOLD` until Part B extraction is approved.

---

## 5. Main Design Pipeline Data Flow

```
[User Web UI / API Request]
         │
         ▼
[1. Requirements Parser & Site Geometry]
  - Normalizes dimensions (e.g. 50x90, 1 Kanal)
  - Computes plot polygon & party walls
         │
         ▼
[2. Setback Engine & Strategy Selector]
  - Calculates mandatory front (15'), rear (7'), side (5') setbacks
  - Establishes buildable footprint & circulation zoning
         │
         ▼
[3. RAG Retrieval & Similarity Matcher]
  - Queries dataset/extracted_vector_knowledge/ & master catalogs
  - Computes graph-topological similarity score
         │
         ▼
[4. Spatial Geometric Solver / RAG Solver]
  - Places room bounding boxes inside buildable boundary
  - Eliminates room overlap; snaps walls to grid
         │
         ▼
[5. Door Clearance & Furniture Placement]
  - Hosts doors on physical wall segments
  - Verifies 90° swept arc clearance & punches cutouts
         │
         ▼
[6. Compliance Engine & Architectural Validator]
  - Verifies natural ventilation for all habitable bedrooms
  - Checks vertical bathroom/stair mumty stacking
         │
         ▼
[7. Quality Gate (Scorer & Hard Checks)]
  - Evaluates plan score (0-100); blocks non-compliant plans
         │
         ▼
[8. 2D Visualizer, DXF Generator & Elevation Mapper]
  - Renders blueprint SVG & PNG (visualizer.py)
  - Exports production AutoCAD DXF (cad/dxf_generator.py)
  - Extracts 1:1 front facade coordinates (floor_plan_to_elevation_mapper.py)
         │
         ▼
[9. Dynamic Elevation Generator & 3D Extruder]
  - Renders coherent front elevation in chosen style (Modern/Spanish/Classical)
  - Extrudes parametric 3D massing model (three_d/)
  - Computes Bill of Quantities (BOQ) cost estimate
         │
         ▼
[JSON Payload & Visual Renders Returned to Web UI]
```

---

## 6. Datasets, Catalogs & Output Locations

| Asset Type | Storage Location | Size | Description | Policy |
|:---|:---|:---|:---|:---|
| **Raw Real Plan Images** | `1/`, `3/`, `5/`, `7/`, `10/` | 30.0 MB | Primary real Pakistani residential blueprint images | **PROTECTED — READ ONLY** |
| **Elevation + Plan Images**| `elevationwithfloorplan/` | 8.42 MB | Paired floor plan and front elevation drawings | **PROTECTED — READ ONLY** |
| **Vector CAD Knowledge** | `dataset/extracted_vector_knowledge/` | 2.5 MB | High-value ground truth JSON vector layouts | **PROTECTED — NEVER TOUCH** |
| **Synthetic Knowledge Base**| `dataset/synthetic_knowledge_base/` | 9.94 MB | Pre-computed RAG knowledge graph (`.jsonl`) | **PROTECTED — NEVER TOUCH** |
| **Master Catalogs** | `dataset/catalog_*.py` | 0.8 MB | Hand-curated Pakistani archetypes | **PROTECTED — NEVER TOUCH** |
| **3D Model Archive** | `3d/` | 1,584.5 MB | SketchUp (`.skp`) models and duplicate `.zip` files | **ASK ME / QUARANTINE DUPLICATES** |
| **Batch Generated Outputs** | `output/web_generated/` | 387.2 MB | Web preview images and temporary test plans | **RECLAIMABLE** |
| **Difference Maps** | `output/*/difference_maps/` | 297.0 MB | Visual diff images from earlier extraction attempts | **RECLAIMABLE** |
| **Variation Experiments** | `variation_experiments/` | 211.2 MB | Historical test variations (SVG/PNG) | **ASK ME** |
| **Evaluation Outputs** | `outputs/comparisons/` | 154.7 MB | Test run image comparisons | **RECLAIMABLE** |
| **Frontend Dependencies** | `frontend/node_modules/` | 164.4 MB | Node package manager cache (regenerable) | **DELETE-CANDIDATE** |

