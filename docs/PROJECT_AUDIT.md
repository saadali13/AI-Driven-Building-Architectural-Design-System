# Comprehensive Project Audit & Baseline Diagnostics

**Date**: 2026-10-29  
**Status**: Verified Working Tree Baseline  
**Recovery Checkpoint**: Git commit `e03d6d5` on branch `recovery-checkpoint-20261029-1835`  

---

## 1. Verified Technology Stack

| Layer | Component | Version / Runtime | Health Status |
| :--- | :--- | :--- | :---: |
| **Backend Runtime** | Python Standard HTTP Server | Python 3.14.4 (Windows 64-bit) | Healthy |
| **Geometry & CAD** | Shapely, Matplotlib (Agg), ezdxf | Shapely 2.0.7, ezdxf 1.3.4 | Healthy |
| **Computer Vision** | OpenCV, EasyOCR, PyTorch | OpenCV 4.10, PyTorch 2.6 (CPU) | Healthy |
| **Primary Frontend** | React 19, Vite, Three.js, Tailwind v4 | `archai_frontend/archai_frontend` | Healthy |
| **Secondary Frontend**| React 19, TypeScript, React Router | `frontend` | Preserved Intact |
| **Project Storage** | Local JSON Store | `output/saved_projects.json` | Protected |

---

## 2. Feature Inventory: Functional vs Defective Modules

### Functional Subsystems
- **DatasetDrivenRAGSolver (`generation/rag_solver.py`)**: Successfully retrieves catalog archetypes and adapts room envelopes to plot constraints.
- **AutoCAD DXF Exporter (`cad/dxf_generator.py`)**: Emits valid layered DXF files conforming to AIA standards (`A-WALL-EXTR`, `A-DOOR`, `A-GLAZ`).
- **Blender 5.1 Procedural Scripting (`api_server.py`)**: Emits executable `.blend` generation Python scripts.
- **Three.js 3D Viewport (`BuildingViewport3D.jsx`)**: Extrudes room boundaries into real-time 3D models with orbit controls.

### Diagnosed Architectural Defects & Limitations

1. **DEFECT-01: Hardcoded Door Clearances in `_convert_canonical_to_floors`**:
   - *Symptom*: When converting canonical plans to frontend JSON, `api_server.py` emits a default placeholder:
     `{"hinge": "left", "swing": "inward", "clearance": 0.9}`.
   - *Impact*: In `FloorPlanEditor2D.jsx`, doors are drawn without authentic wall cutouts or 90-degree swept arc collision verification, allowing door arcs to slice through perpendicular walls or furniture.
2. **DEFECT-02: Elevation-to-Plan Disconnection in Generative Fallbacks**:
   - *Symptom*: If the RAG solver fails, fallback elevation generation defaults to template facades rather than projecting the actual exterior window bays from the floor plan.
3. **DEFECT-03: Multi-Floor Stair Mumty Alignment**:
   - *Symptom*: In two-floor configurations ($G+1$), staircase footprints on the ground floor must stack vertically under the upper floor landing and mumty roof tower. Minor 0.5m offsets were observed in certain plot aspect ratios.
4. **DEFECT-04: Raster Reference Extraction Over-Generalization**:
   - *Symptom*: Phase 5B/5C/5D proved that while computer vision extracts genuine room voids, raster blueprints with watermarks or dense annotations fragment continuous walls, making direct raster extraction unsuitable as a primary real-time CAD generator.

---

## 3. Baseline Test Suite Verification

Baseline tests executed directly against the active codebase:

1. **`tests/test_architectural_correction.py` & `test_door_stair_furniture_clearances.py`**:
   - **27 tests executed**: **27 PASSED (100%)** in 7.91s.
   - Verified door-vehicle collision resolution, curved/spiral stair boundary containment, nightstand/shower clearances, and G+1 metadata export.
2. **`tests/test_master_regression.py`**:
   - **12 tests executed**: **12 PASSED (100%)** in 8.32s.
   - Verified quality gate scoring, stair typology swappability (straight, L-shaped, U-shaped, winder, spiral, curved, ladder, floating, bifurcated), and DXF export.
3. **`output/experiments/poc_single_plan_extraction/phase_5d/test_phase_5d.py`**:
   - **5 tests executed**: **5 PASSED (100%)** in 0.34s.
   - Verified independent ground truth evaluation, penalized IoU logic, and protection of production code.

---

## 4. Protected Asset Checkpoints

- **Local Git Recovery Branch**: `recovery-checkpoint-20261029-1835` (Commit `e03d6d56b81de1801b30e17ce7ae8968729ccf83`).
- **External ZIP Backup**: `C:\Users\m\Desktop_Backups\archaicraft_backup_20261029_183120.zip`.
- **Protected User Storage**: `output/saved_projects.json`.

