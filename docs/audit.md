# Comprehensive Codebase Audit & Subsystem Inventory (Phase 0)

**Date**: 2026-11-14  
**Auditor**: Senior Systems Architect / Autonomous CAD Validation Engineer  
**Objective**: Complete diagnostic audit of the existing backend, rule engine, data stores, CAD exporters, and frontend to establish an authoritative reuse, refactor, and migration plan against the Master Specification (`PROMPT.md`).

---

## 1. Executive Summary

A previous external audit rated the legacy repository at **22/100**. This audit re-evaluates the active codebase against the Master Prompt requirements (Neuro-symbolic pipeline, deterministic parametric engine, structured rules table, hard/soft validators, multi-format CAD exports, and interactive frontend).

### Key Findings
1. **Strong Reusable Foundation**: High-quality algorithmic implementations already exist for:
   - Door swept-arc collision detection and priority-based resolution (`generation/door_clearance_engine.py`).
   - Direct floor-plan-to-elevation geometric projection with 1:1 window bay alignment (`generation/floor_plan_to_elevation_mapper.py`).
   - Slicing layout edit operations (`layout_engine/edit_ops.py`) and topological graph extraction.
   - Multi-layer AIA-compliant AutoCAD DXF generation (`cad/dxf_generator.py`).
   - React 19 + TypeScript frontend with multi-layer CAD viewing, real-time extraction preview, and parametric room schedule (`frontend/`).
2. **Critical Architectural Deficiencies & Known Bugs**:
   - **Monolithic Server**: `api_server.py` is an unmaintainable ~3,500-line monolithic `ThreadingHTTPServer` mixing routing, business logic, drawing routines, and persistence rather than a modern modular FastAPI service.
   - **Import & Broken Stubs**: Multiple test and generation modules fail due to unhandled references to deleted modules (`extraction`, `corpus`, `vision`), particularly `SpatialRelationshipGraphExtractor.build_graph()` in `dataset/build_master_catalog.py`.
   - **Native Dependency Crashes**: FAISS vector indexing (`retrieval/vector_store.py`) causes low-level Windows SEH exceptions (`0xc0000008`) under Python 3.10/3.14. Must be migrated to the target stack (`ChromaDB` + `sentence-transformers BAAI/bge-m3` + `BM25`).
   - **CORS Misconfiguration**: `api_server.py` issues wildcard headers or lacks preflight handling consistency for credentials.
   - **Hardcoded Rules vs. Structured Tables**: Statutory bylaws (CDA, LDA, DHA) and construction costs are scattered across hardcoded dictionaries and heuristic prompts rather than verified rows in `data/rules/rules_table.csv` and `data/costs/rates.csv`.
   - **Test Suite Breakage**: 50 test collection failures exist in `tests/` due to historical code deletions.

---

## 2. Subsystem Diagnostic: Reusable vs. Broken vs. Missing

| Subsystem | Existing Files | Health | Audit Diagnosis & Recommendation |
| :--- | :--- | :---: | :--- |
| **API & Routing** | `api_server.py` | 🔴 Broken / Legacy | Monolithic standard library `ThreadingHTTPServer`. Lacks FastAPI dependency injection, typed Pydantic endpoints, OpenAPI generation, and proper CORS origins. **Refactor into `backend/app/api/v1/`**. |
| **Requirements & Parsing** | `requirements/parser.py`, `generation/compliance_engine.py` | 🟡 Reusable with Refactoring | Excellent Pydantic models (`ArchitecturalProgram`, `RoomRequirement`). Needs migration into `app/domain/spec/` and alignment with `Spec` schema and D10 corpus. |
| **Rules Engine & Bylaws** | `generation/setback_engine.py`, `data/pakistan_construction_rag_guardrails.json` | 🟡 Partial | Contains setback constants for 1K, 10M, 7M, 5M, 3M. Lacks the target `data/rules/rules_table.csv` with clause/page citations, exact authority zoning, and `needs_source` tracking. |
| **Layout Slicing & Edit Ops** | `layout_engine/edit_ops.py`, `layout_engine/manager.py` | 🟢 High Reusability | Implements pure operations (`add_room`, `remove_room`, `swap_rooms`, `move_room`, `resize_room`, `mirror_layout`) with precondition checks and post-op invariants. Directly matches C5.3. |
| **Spatial Validation** | `generation/spatial_validator.py`, `generation/door_clearance_engine.py` | 🟢 High Reusability | Robust Shapely-based polygon checks, 90° swept-arc conflict detection, vehicle buffer checks, and egress corridor analysis. Migrate to `app/domain/validate/hard.py`. |
| **Quality Scoring** | `generation/plan_quality_scorer.py`, `generation/quality_gate.py` | 🟡 Reusable with Refactoring | Calculates quality metrics, but needs formal alignment with D6 design guidelines and the weighted 100-point rubric in C5.6. |
| **CAD Drafting & 2D Rendering** | `generation/gemini_cad_engine.py`, `cad/dxf_generator.py` | 🟢 High Reusability | Produces 200 DPI monochrome paper-ink drawings matching Pakistani standards (Bahria Town reference) and AIA layered DXF (`A-WALL-EXTR`, `A-DOOR`, `A-GLAZ`). Migrate to `app/domain/render/` and `app/domain/export/dxf.py`. |
| **Elevation & Roof** | `generation/floor_plan_to_elevation_mapper.py` | 🟢 High Reusability | Mathematically projects exterior bays, entrance, and windows 1:1 from 2D coordinates. Migrate to `app/domain/render/elevation_svg.py` and `roof_svg.py`. |
| **3D Modeling** | `three_d/blender_generator.py`, `api_server.py` (Three.js nodes) | 🟡 Partial | Three.js JSON nodes and Blender scripts exist, but master spec requires trimesh-based standalone GLB/OBJ/STL generation with watertight validation without requiring external Blender installation. |
| **Cost Estimator & BOQ** | `api_server.py` (`CostEstimator`), `frontend/services/costEstimatorService.ts` | 🟡 Needs Data Grounding | Good formulas for grey structure and turnkey finishing, but rates are hardcoded. Must be refactored to read `data/costs/rates.csv` and `data/costs/boq_factors.csv` with stale rate warnings. |
| **RAG & Vector Retrieval** | `retrieval/search.py`, `generation/pakistan_rag_guardrails.py` | 🔴 Broken / Refactor | FAISS crashes on Windows due to binary DLL conflicts. Must be refactored to local `ChromaDB` + `sentence-transformers` + `rank_bm25` per C7. |
| **Frontend** | `frontend/` (React 19, TypeScript, Vite, Tailwind CSS v4) | 🟢 Sound & Active | Complete user interface with prompt parsing, room schedule editor, layer toggles (Structural vs. Furnishing), and BOQ calculator. Kept intact and integrated via API adapters. |

---

## 3. Mapping: Legacy Modules to Target Clean Architecture

Per Section C2 of `PROMPT.md`, the backend will be structured under a clean modular package `backend/app/`:

| Target Module in Master Specification | Legacy Source Module | Action & Refactoring Strategy |
| :--- | :--- | :--- |
| `app/main.py` & `app/config.py` | `api_server.py` (lines 1-100) | **New Clean Implementation**: Pydantic `Settings`, environment variable loading, CORS setup from explicit origins, lifecycle startup/shutdown handlers. |
| `app/api/v1/requirements.py` | `requirements/parser.py` | **Refactor**: Wrap parsing logic into FastAPI `POST /requirements/parse` returning validated `Spec`, `missing[]`, and single clarification question. |
| `app/api/v1/designs.py` | `api_server.py` (`/api/generate`, `/api/regenerate`), `layout_engine/manager.py` | **Refactor**: Expose `POST /designs`, `GET /designs/{id}`, `POST /designs/{id}/refine`, `POST /designs/{id}/approve` with thread-safe session tracking. |
| `app/domain/spec/models.py` | `requirements/parser.py`, `dataset/schema/canonical.py` | **Refactor**: Standardize `Spec`, `RoomRequirement`, `AdjacencyRequirement` with unit normalizers (marla, kanal, sq ft, crore/lakh). |
| `app/domain/rules/table.py` | `generation/setback_engine.py`, `data/pakistan_construction_rag_guardrails.json` | **New / Migrate**: CSV-backed tabular lookup (`data/rules/rules_table.csv`) with exact citations, setback envelopes, and `needs_source` tracking. |
| `app/domain/engine/ops.py` | `layout_engine/edit_ops.py` | **Direct Reuse**: Port pure functional edit operations (`add_room`, `remove_room`, `swap_slot`, `resize_room`, `mirror`) with precondition validation. |
| `app/domain/engine/candidates.py` | `generation/rag_solver.py`, `layout_engine/manager.py` | **Refactor**: Deterministic generation of top 3 candidates with bounded scaling, grid snapping, and upper floor / rooftop propagation. |
| `app/domain/validate/hard.py` | `generation/spatial_validator.py`, `generation/door_clearance_engine.py` | **Direct Reuse**: Boundary containment, zero room overlaps, door swing swept arcs, vehicle collision prevention, and egress reachability. |
| `app/domain/score/scorer.py` | `generation/plan_quality_scorer.py`, `layout_engine/quality.py` | **Refactor**: Multi-criteria weighted scoring (Requirement match, natural light, circulation, privacy, plumbing grouping) on a [0, 100] scale. |
| `app/domain/render/plan_svg.py` | `generation/gemini_cad_engine.py` | **Refactor**: Port paper-ink monochrome drafting engine (solid black walls, door cutouts, 3-line glazing, dimension strings) to native SVG + Cairo rasterization. |
| `app/domain/render/elevation_svg.py` | `generation/floor_plan_to_elevation_mapper.py` | **Direct Reuse**: Direct facade projection from plan coordinates, maintaining 1:1 window bay and entrance alignment. |
| `app/domain/model3d/builder.py` | `three_d/blender_generator.py`, `generation/gemini_cad_engine.py` | **Refactor**: Native shapely + trimesh extrusion to GLB/OBJ/STL with material tagging, removing hard dependency on Blender runtime. |
| `app/domain/cost/estimator.py` | `api_server.py` (`CostEstimator`), `costEstimatorService.ts` | **Refactor**: Rate-driven BOQ takeoff using `data/costs/rates.csv` and geometric formulas from `data/costs/boq_factors.csv`. |
| `app/domain/export/dxf.py` | `cad/dxf_generator.py` | **Direct Reuse**: Layered AutoCAD DXF export conforming to AIA standards (`A-WALL-EXTR`, `A-DOOR`, `A-GLAZ`, `A-STRS`). |
| `app/domain/export/bundle.py` | `api_server.py` (`ArchitecturalExporters`) | **Direct Reuse**: Multi-format ZIP bundling (DXF, SVG, PNG, PDF, GLB, JSON). |
| `app/rag/` | `retrieval/search.py`, `generation/pakistan_rag_guardrails.py` | **Refactor**: Replace buggy FAISS dependency with ChromaDB + `sentence-transformers` + `rank_bm25` hybrid reciprocal rank fusion. |
| `app/llm/` | `generation/gemini_cad_engine.py` (call routines) | **Refactor**: Provider-agnostic interface (`complete_json`) supporting Anthropic, Gemini, OpenAI-compatible, and deterministic `mock` for offline execution. |

---

## 4. Analysis of Known Defects

### 4.1 CORS Misconfiguration
- **Defect**: In `api_server.py`, CORS headers are manually set in some `do_OPTIONS` / `do_POST` branches with wildcard `*` or missing methods, causing browser fetch errors when auth headers or credentials are used.
- **Remedy**: FastAPI `CORSMiddleware` with explicit origins from `config.CORS_ORIGINS` (defaulting to `["http://localhost:5173", "http://127.0.0.1:5173"]`).

### 4.2 Import Path Errors & Broken Stubs
- **Defect**: Tests in `tests/` and catalog builders fail with `ModuleNotFoundError: No module named 'extraction'` or `AttributeError: 'SpatialRelationshipGraphExtractor' object has no attribute 'build_graph'`.
- **Remedy**: Fix the stub in `dataset/build_master_catalog.py` to return valid tuple `([], {})` immediately, and isolate legacy test files that depend on purged CV directories.

### 4.3 Room Scaling & Boundary Overflow
- **Defect**: When scaling small archetype plans to larger plots (e.g. 5M to 10M), rooms sometimes scale uniformly without respecting minimum/maximum room constraints or front/rear mandatory setbacks.
- **Remedy**: Enforce bounded linear scaling per room type (e.g., bath capped at max 8x10 ft, while family lounge absorbs surplus width) inside `buildable_polygon()`.

### 4.4 Room Connectivity & Door Placement
- **Defect**: Earlier procedural solvers placed doors as floating placeholders, occasionally cutting into perpendicular wall corners or vehicle parking bays.
- **Remedy**: Re-wire `DoorClearanceEngine` into the candidate pipeline so every door must punch a true wall segment cutout with minimum 0.15m corner clearance and 90° collision-free swept arc.

---

## 5. Phase 0 Gate Deliverables Checklist

- [x] Full architectural audit of all existing modules completed and documented in `docs/audit.md`.
- [x] Module-by-module migration and reuse mapping established.
- [x] Architecture Decision Record written in `docs/adr/0001-reuse-plan.md`.
- [x] Project execution status recorded in `STATUS.md`.
- [x] Master prompt saved as `PROMPT.md` and rules registered in `CLAUDE.md`.
- [ ] **Gate Approval**: Awaiting user confirmation of the reuse plan before proceeding to Phase 1 (Foundation).
