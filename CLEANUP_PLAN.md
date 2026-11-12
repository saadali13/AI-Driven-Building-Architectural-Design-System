# ArchiCraft AI — Reversible Cleanup & Disk Reclamation Plan

## 1. Executive Summary & Disk Space Breakdown

* **Total Project Disk Space**: **4,149.0 MB (4.05 GB)**
* **Identified Reclaimable Space**: **2,501.8 MB (2.44 GB)** *(60.3% of total project size)*
* **Protected & Core Assets**: **1,647.2 MB (1.61 GB)** *(includes all source image folders, datasets, git history, core codebase)*
* **OneDrive Impact**: The project path sits at `C:\Users\m\OneDrive\Desktop\New folder`. Because it is located inside OneDrive, every file (including 1.5 GB of SketchUp models and 1.6 GB of generated outputs) continuously syncs to Microsoft cloud storage. Reclaiming 2.44 GB will significantly reduce OneDrive sync overhead and avoid storage quota exhaustion.

---

## 2. Reclaimable Space per Category & Folder

| Folder / Category | Size (MB) | Contents & Evidence | Cleanup Classification | Action |
|:---|:---|:---|:---|:---|
| **`3d/*.zip` Duplicate Archives** | 605.2 MB | 16 `.zip` files (e.g. `120x80-classical-spanish-bungalow-design-1.snapshot.2.zip` 38.6MB). Exactly identical `.skp` files exist in `3d/_Organized_Designs/`. | **DUPLICATE** | Quarantine to `_cleanup_quarantine/` |
| **`3d/` Unpacked Raw Snapshots** | 556.5 MB | Unpacked snapshot folders duplicating files already curated into `3d/_Organized_Designs/`. | **DUPLICATE** | Quarantine to `_cleanup_quarantine/` |
| **`output/web_generated/`** | 387.2 MB | Transient web server preview renders from previous user UI test sessions. | **GENERATED OUTPUT** | Quarantine to `_cleanup_quarantine/` |
| **`output/*/difference_maps/`** | 297.0 MB | Visual difference heatmaps generated during earlier CV test attempts in `output/5/`, `output/7/`, and `output/10/`. | **GENERATED OUTPUT** | Quarantine to `_cleanup_quarantine/` |
| **`variation_experiments/`** | 211.2 MB | Thousands of generated variation PNGs and SVGs from old parameter sweep tests. | **GENERATED OUTPUT** | **ASK ME** (User approval required) |
| **`outputs/comparisons/`** | 154.7 MB | Side-by-side benchmark comparison renders from past testing. | **GENERATED OUTPUT** | Quarantine to `_cleanup_quarantine/` |
| **`frontend/node_modules/`** | 164.4 MB | Node.js package dependencies for secondary frontend; 100% regenerable at any time via `npm install`. | **REGENERABLE** | **ASK ME** (Delete only if space needed) |
| **`output/manual_test/` & `experiments/`** | 124.8 MB | Ad-hoc manual design test runs and stress tests. | **GENERATED OUTPUT** | Quarantine to `_cleanup_quarantine/` |
| **Root One-Off Utility Scripts** | 0.1 MB | Standalone developer scripts (`render_4_styles.py`, `insert_compliance.py`, `generate_contact_sheet.py`, `debug_synthesis.py`, `benchmark_stages.py`, `patch_new_design_page.py`, `test_exports.py`). | **ONE-OFF SCRIPT** | Quarantine to `_cleanup_quarantine/` |
| **`scratch/`** | 3.5 MB | Temporary debugging scripts and intermediate logs. | **ONE-OFF SCRIPT** | Quarantine to `_cleanup_quarantine/` |

---

## 3. Protected Asset Inventory (NEVER Move or Delete)

The following assets are strictly protected under project guardrails and must never be moved or deleted, regardless of references:

1. **Source Blueprint Folders**: `1/` (5.76 MB), `3/` (6.18 MB), `5/` (4.51 MB), `7/` (8.59 MB), `10/` (4.95 MB).
2. **Paired Elevation Source Folder**: `elevationwithfloorplan/` (8.42 MB).
3. **Primary Vector Knowledge Base**: `dataset/` (20.70 MB, including `dataset/extracted_vector_knowledge/`, `dataset/synthetic_knowledge_base/floorplan_rag_dataset.jsonl`, `dataset/catalog_*.py`, and `dataset/schema/`).
4. **Active User Saved Projects**: `output/saved_projects.json` (2.39 MB).
5. **Git Version History**: `.git/` (209.31 MB).
6. **Core Python Pipeline**: `api_server.py`, `generation/`, `requirements/`, `cad/`.
7. **Frontend Source Code**: `archai_frontend/archai_frontend/src/` and `frontend/src/`.
8. **Passed Dataset Destination**: `output/dataset/` and `dataset_index.json`.
9. **Environment Secrets & Credentials**: `.env.example`, `frontend/.env` (contains Supabase keys, untracked by Git).

---

## 4. Extraction Work Scripts: HOLD Policy

All extraction scripts located in `output/code/` (`run_attempt8_final_master.py`, `run_attempt9_correction_pipeline.py`, etc.) and earlier pilot plan outputs in `output/1/00770eba64db20501bbd30bb21ce6aa5/` are explicitly marked:

$$\mathbf{HOLD}$$

*They must remain intact and accessible as reference benchmarks until the PART B clean extraction pilot (`extraction_v2/1/00770eba64db20501bbd30bb21ce6aa5/`) has been formally reviewed and approved by the user.*

---

## 5. Reversible Step-by-Step Quarantine Procedure (When Approved)

*No files will be moved during Part A. When the user approves cleanup execution, the following zero-risk, reversible procedure will be followed:*

### Step 5.1: Create Timestamped Quarantine Directory
```powershell
$Quarantine = "_cleanup_quarantine\20261106_reclamation"
New-Item -ItemType Directory -Path $Quarantine -Force
```

### Step 5.2: Move with Preserved Relative Paths
Files are never deleted outright. They are relocated into `$Quarantine` preserving their original folder structure. For example:
* `3d\120x80-classical-spanish-bungalow-design-1.snapshot.2.zip` $\to$ `_cleanup_quarantine\20261106_reclamation\3d\120x80-...zip`
* `output\web_generated\*` $\to$ `_cleanup_quarantine\20261106_reclamation\output\web_generated\*`
* `render_4_styles.py` $\to$ `_cleanup_quarantine\20261106_reclamation\render_4_styles.py`

### Step 5.3: Post-Move System Verification Protocol
Immediately after moving any files, four automated verification gates must pass:
1. **Backend Server Startup**:
   Execute `python api_server.py --help` or test-mode health check to confirm server launches without missing module errors.
2. **Geometric Design Pipeline Generation**:
   Execute `python -c "from generation.design_diversity_engine import DesignDiversityEngine; print('Engine loaded successfully')"` to verify core solver integrity.
3. **Frontend Build / Dev Verification**:
   Execute `cd archai_frontend/archai_frontend && npm run build` (or `npx vite build --dry-run`) to confirm primary UI compiles cleanly.
4. **Automated Regression Suite**:
   Execute `pytest tests/test_generation.py tests/test_refactored_quality_gate.py` to prove zero functional regression.

*If any check fails, files are instantly restored by moving the contents of `$Quarantine` back to root.*

---

## 6. OneDrive Optimization Recommendations

1. **Pause Syncing of Generated Caches**:
   Add a `.git/info/exclude` and configure OneDrive "Always keep on this device / Free up space" for `3d/` and `output/web_generated/` to stop uploading hundreds of temporary test images.
2. **Preserve SketchUp Master Library in `3d/_Organized_Designs`**:
   The 10 organized SketchUp models in `3d/_Organized_Designs/` represent 422 MB of clean architectural reference assets. Deleting the redundant 1,162 MB of duplicate `.zip` archives and unorganized snapshot folders frees massive OneDrive bandwidth while preserving 100% of the 3D assets.

