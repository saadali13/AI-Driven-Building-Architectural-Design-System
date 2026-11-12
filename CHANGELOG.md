# CHANGELOG

## Layout-Driven RAG Generator & Real Plan Adaptation Engine

### Date: 2026-11-10

### Scope of Changes:
- **No changes to `generation/rag_solver.py` or `generation/quality_gate.py`** (preserved strict read-only integrity).
- **Source images**: Strictly read-only.
- **Slicing Layout Reconstruction & Blind Subagent Gate (Step 0)**:
  - Created `layout_engine/slicing_reconstructor.py` implementing non-overlapping slicing partitions across normalized building envelopes (front/middle/back x left/centre/right).
  - Wired Pilot `1_00770eba` to load real Run D extracted vector geometry.
  - Added Urdu & Roman-Urdu synonyms (`بیڈروم`, `فیملی ہال`, `کچن`, `baithak`, `dera`, etc.).
  - Executed blind vision validation across 12 plans with 12 subagents: achieved **85.71% agreement** (174/203 rooms, exceeding the 70.0% threshold).
- **Corpus & Retrieval Tuning (Step 1)**:
  - Removed `indian_squat_wc` from foreign exclusions (authentic Pakistani fixture). Reclassified 81 Pakistan, 9 possible_foreign, 2 foreign.
  - Rebuilt `corpus/plans.jsonl` (92 records, 32 strict slicing usable) and `retrieval/feature_index.json`.
  - Added lawn scoring and single-floor stair penalty in `retrieval/search.py`.
- **Layout Adaptation Engine (Step 2)**:
  - Created `layout_engine/adapt.py`:
    - Scales reference slicing layout to target plot dimensions with statutory CDA/LDA/DHA setbacks.
    - Applies logged edit rules (bedroom allocation, en-suite bathroom attachment, powder room placement).
    - Non-overlapping slicing repack guaranteeing 0 room collisions.
    - Generates 9" exterior / 4.5" interior walls, hosted doors (90° swept arcs), and exterior windows.
    - Achieves high spatial fidelity metric (up to 0.857).
    - Outputs `CanonicalFloorPlan` and renders publication-quality blueprints via `FloorPlanVisualizer`.
- **Pipeline Integration & 6 Test Runs (Step 3 & 4)**:
  - Updated `pipeline/generate_from_requirements.py` to prioritize usable references and adapt them with `fallback_used = False`.
  - Executed all 6 test requests:
    - req_1 (5 Marla 3-bed): PASS (Fallback: False, Score: 0.96)
    - req_2 (7 Marla 3-bed double storey with lawn): PASS (Fallback: False, Score: 0.96)
    - req_3 (Single floor 3-bed): PASS (Fallback: False, Score: 0.96)
    - req_4 (10 Marla luxury with lawn & servant): PASS (Fallback: False, Score: 0.96)
    - req_5 (1 Kanal 4-bed double storey): PASS (Fallback: True, Score: 1.00)
    - req_6 (3-bed with drawing & car porch): PASS (Fallback: False, Score: 0.96)
  - 100% verification checklist pass rate across all 6 requests.
- **Controlled Ablation Study**:
  - Implemented `pipeline/run_ablation_study.py` comparing Condition A (Rank-1 Reference), Condition B (Rank-3 Reference), and Condition C (Procedural Catalog Fallback) across 2 benchmark cases.
  - Published findings in `results/ablation_study.md`.
- **API Server Endpoint**:
  - Endpoint `POST /generate_from_reference` / `/api/generate_from_reference` in `api_server.py` verified with complete payload and response assertions.

---

## End-to-End System Integration: Retrieval -> Adaptation -> Synthesis -> Verification

### Date: 2026-11-09 / 2026-11-10

### Scope of Changes:
- **No changes to `generation/rag_solver.py` or `generation/quality_gate.py`** (preserved read-only integrity).
- **Source images**: Strictly read-only.
- **Records sync (Step 0)**:
  - Cleaned & rebuilt `extraction_v2/records/` and `extraction_v2/records_index.json` using vision-primary rules with flat OCR confirmation and plausibility checks.
  - Corpus tier breakdown: Tier A (36), Tier B (17), needs_review (41), unverified (65), unsupported_format (43).
- **Engine Interface (Step 1)**:
  - Created `ENGINE_INTERFACE.md` documenting `ProceduralArchitecturalEngine.synthesize_design`, exact input schemas, output schemas, and QualityGate checks.
- **Retrieval Engine (Step 2)**:
  - Created `retrieval/feature_index.py` (indexes 94 plans: 36 Tier A, 17 Tier B, 41 needs_review with penalty).
  - Created `retrieval/search.py` implementing hard marla filtering, weighted feature distance, Tier A boost, and explanation generation.
  - Evaluated 5 diverse queries in `results/retrieval_tests.md`.
- **Adapter Layer (Step 3)**:
  - Created `adapter/record_to_constraints.py` mapping retrieved plans and user requirements into engine synthesis arguments, enforcing user-wins precedence and tracking kept/changed/dropped guidance.
- **Generation & Verification Pipeline (Step 4)**:
  - Created `pipeline/generate_from_requirements.py` executing end-to-end synthesis and deterministic requirements verification.
  - Generated and verified 5 sample requests; archived output plans and reference CAD images in `results/generation_tests/`.
- **API & Frontend Integration (Step 5)**:
  - Added `POST /generate_from_reference` to `api_server.py`.
  - Verified live endpoint with 2 requests (`results/server_response_1.json`, `results/server_response_2.json`).
  - Updated `RequirementsGenerator.jsx` to display retrieved reference plan image, similarity badge, and requirements compliance checklist side-by-side with generated CAD output.

