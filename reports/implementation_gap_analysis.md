# Architectural System Implementation Gap Analysis

**Document:** `reports/implementation_gap_analysis.md`  
**Standard:** Antigravity AI Engineering Architecture Audit  
**Classification Values:** `EXISTS`, `PARTIAL`, `MISSING`, `INCORRECT`, `NEEDS_REFACTOR`  

---

## 1. System Component Gap Matrix

| Architectural Subsystem | File / Module | Current Status | Audit Findings & Deficiencies | Remediation Action |
| :--- | :--- | :--- | :--- | :--- |
| **Requirements Parsing** | `requirements/parser.py` | `NEEDS_REFACTOR` | Parses text into `ArchitecturalProgram`, but room count generation is heuristic. Storey count defaults to 1 unless explicit strings match, which causes infeasible spatial packing for multi-bedroom requests on compact plots. Hard vs soft constraints are not partitioned. | Enforce deterministic room node creation: requested $N$ bedrooms $\rightarrow$ exactly $N$ nodes. Partition Hard constraints from Soft preferences. Infer multi-storey feasibility or return `INFEASIBLE_PROGRAM`. |
| **Canonical Schema** | `dataset/schema/canonical.py` | `EXISTS` | Strong single source of truth (`CanonicalFloorPlan`, `RoomModel`, `WallModel`, `OpeningModel`, `GraphEdgeModel`). Already supports level indices and confidence scores. | Preserve schema. Enrich `RoomModel` with `attached_to_room_id` and `calculated_dimensions`. Add site setback metadata. |
| **V4 Semantic Discipline** | `extraction/rooms.py` | `EXISTS` | Correctly implements V4 rule: polygons without verified text or fixtures are strictly designated `unclassified_closed_region`. Prevents hallucinated bedrooms from geometry alone. | **PRESERVE UNMODIFIED**. Ensure downstream generators do not violate this rule by creating "fake" rooms via floating labels. |
| **Geometric & Structural Validation** | `generation/validation.py` | `PARTIAL` | Checks geometric room overlap, minimum room area, daylight proximity, and graph connectivity. Missing: master-bath attachment check, door-on-shared-wall check, window-on-exterior check, dimension consistency check. | Refactor and expand. Integrate deep geometric tests (1D boundary intersection $\ge 0.80\,\text{m}$, exterior wall window hosting). |
| **Floor Plan Quality Gate** | `generation/quality_gate.py` | `MISSING` | No standalone machine-readable validation engine outputting formal pass/fail verdicts mapped to standardized failure codes F01–F20. | **CREATE NEW** `generation/quality_gate.py` generating standardized `quality_report.json` with severity levels (`CRITICAL`, `MAJOR`, `MINOR`). |
| **Constraint Solver** | `generation/solver.py` | `PARTIAL` | CP-SAT solver packs rectangles orthogonally and minimizes perimeter. Lacks hard constraints for master bedroom $\leftrightarrow$ attached bathroom pairing and rigid circulation corridors. | Add explicit hard constraints for master bath adjacency and circulation reachability. |
| **Parametric Templates** | `generation/architectural_templates.py` | `NEEDS_REFACTOR` | 10M, 5M, and 3M templates generate realistic layouts, but 1 Kanal and 7 Marla need full template parity. Need support for grand helical stairs and $45^\circ$ chamfered entrance foyers. | Add `Luxury1KanalArchitecturalEngine` and `Contemporary7MarlaArchitecturalEngine`. Enforce strict private en-suite doors. |
| **Architectural Visualizer** | `generation/visualizer.py` | `NEEDS_REFACTOR` | Produces detailed furniture and orientation-aware windows, but visual styling currently has high contrast colors and large callout boxes that resemble marketing infographics rather than authentic CAD drawings. | Refactor to CAD architectural drafting conventions: solid wall fills ($0.30\,\text{mm}$ exterior, $0.15\,\text{mm}$ interior), clean dimension strings calculated from polygon geometry, restrained architectural symbols, north arrow. |
| **AutoCAD DXF Pipeline** | `cad/dxf_generator.py` | `EXISTS` | Generates compliant AIA layered DXFs (`WALL`, `DOOR`, `WINDOW`, `ROOM_LABEL`, `DIMENSION`). | **PRESERVE**. Update layer definitions to include setback lines and plot boundaries. |
| **Blender 3D Engine** | `three_d/blender_generator.py` | `EXISTS` | Successfully executes headless Blender Python scripts to extrude walls, carve openings with boolean modifiers, and render multi-storey perspectives. | **PRESERVE**. |
| **Reference Dataset Annotations** | `reference_floorplans/annotations/` | `MISSING` | Real reference plans in folders 1, 3, 5, 7, 10 are cataloged in `dataset_manifest.json`, but structured per-image annotation JSON files are not yet formalized. | **CREATE** annotation builder and produce structured JSON files for benchmark exemplars. |
| **Benchmark Regression Suite** | `reference_floorplan_benchmark.json` | `MISSING` | No formal regression benchmark file tracking room count distributions, adjacency statistics, and proportion ranges across the 187 real plans. | **CREATE** `reference_floorplan_benchmark.json` and regression test harness. |
| **End-to-End Pipeline Orchestration** | `pipeline_runner.py` | `NEEDS_REFACTOR` | Pipeline generates and validates, but does not enforce a bounded iterative regeneration loop if the Quality Gate fails, nor does it handle `INFEASIBLE_PROGRAM` gracefully. | Integrate requirement-first pre-render gate, Quality Gate (F01–F20), bounded retry loop (`max_attempts=5`), and `quality_report.json` emission. |

---

## 2. Core Architectural Engineering Principles to Preserve
1. **Architecture Semantics First, Rendering Second**: No image or 2D drawing is generated until the canonical architectural model passes all critical quality gates.
2. **Deterministic Room Counts**: Requested room counts in the user prompt are non-negotiable hard constraints.
3. **Master Suite Integrity**: An attached bathroom must be geometrically adjacent and connected by an internal private door.
4. **Authentic Drafting Standards**: Visual representation must communicate true construction geometry without decorative obfuscation.
