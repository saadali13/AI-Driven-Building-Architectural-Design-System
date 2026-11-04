# Autonomous Architectural AI Implementation Roadmap

**Document Standard**: Production Master Roadmap  
**Scope**: 9-Phase Engineering Architecture  
**Active Working Tree**: `recovery-checkpoint-20261029-1835`  

---

## Roadmap Overview

```
Phase 1: Baseline & Diagnosis (DONE)
   │
   ▼
Phase 2: Canonical Architectural Foundation (IN PROGRESS)
   │
   ▼
Phase 3: Floor-Plan Generation & Authentic Door Clearances (DEFECT-01) (NEXT)
   │
   ▼
Phase 4: Coordinated Front & Side Elevation Generation
   │
   ▼
Phase 5: Complete 3D Architectural Modeling & Rooftop Structures
   │
   ▼
Phase 6: Parametric Regeneration & Project Persistence
   │
   ▼
Phase 7: Full-Stack UI/UX & Studio Controls Audit
   │
   ▼
Phase 8: Authentic Architectural Reference Benchmarking
   │
   ▼
Phase 9: Continuous Quality Monitoring & Final Certification
```

---

## Detailed Phase Breakdown

### Phase 1: Baseline & Repository Diagnosis
- [x] Full codebase mapping and technology stack audit.
- [x] Verification of protected recovery checkpoints (Commit `e03d6d5`, ZIP backup).
- [x] Baseline execution of existing test suites (44/44 tests passed).
- [x] Creation of core architectural documentation in `docs/`.

### Phase 2: Architectural Data Foundation (Single Source of Truth)
- [x] Audit canonical plan schemas in `generation/canonical_plan.py` and `api_server.py`.
- [ ] Ensure all wall objects have explicit host IDs, thickness specifications ($0.2286\text{m}$ exterior, $0.1143\text{m}$ interior), and opening arrays.
- [ ] Standardize coordinate transformation matrices across 2D canvas, 3D viewport, and DXF exporter.

### Phase 3: Floor-Plan Generation & Door Opening Cutouts (DEFECT-01)
- [ ] Eliminate hardcoded door placeholders in `_convert_canonical_to_floors`.
- [ ] Implement true punch-through wall cutouts hosting doors and windows.
- [ ] Integrate 90-degree swept arc geometry calculation with collision detection against furniture and vehicles.
- [ ] Connect `FloorPlanEditor2D.jsx` to render verified swept arcs and punched wall openings.

### Phase 4: Elevation Generation Coherence
- [ ] Derive front elevation directly from exterior front wall coordinates of the floor plan.
- [ ] Enforce 1:1 window bay alignment and entrance/porch placement between ground/upper plans and elevation.
- [ ] Prevent invented or omitted facade openings.

### Phase 5: Complete 3D Modeling (Exterior, Interior & Rooftop)
- [ ] Synchronize Three.js `BuildingViewport3D.jsx` with canonical wall openings.
- [ ] Model interior partitions with door leaves and window frames.
- [ ] Extrude parapet walls and rooftop mumty tower aligned with vertical stair shaft.

### Phase 6: Regeneration & Persistence
- [ ] Audit `/api/regenerate` endpoint for room-specific mutation without envelope corruption.
- [ ] Test project persistence in `output/saved_projects.json` across page reloads.
- [ ] Establish rollback mechanisms on regeneration failures.

### Phase 7: Full-Stack UI/UX Quality Gate
- [ ] Audit all visible studio controls in `archai_frontend`.
- [ ] Verify export workflows (DXF, SVG, OBJ, Blender script).
- [ ] Remove misleading placeholder buttons or bind them to active functionality.

### Phase 8: Authentic Reference Benchmarking
- [ ] Benchmark spatial graphs extracted in Phase 5 against canonical generator archetypes.
- [ ] Catalog dimensioned reference case studies across 3, 5, 7, 10 Marla and 1 Kanal plots.

### Phase 9: Continuous Monitoring & Final Acceptance
- [ ] Implement automated telemetry and architectural validation scorecard.
- [ ] Verify all 17 criteria in Section 17 of the Master Prompt.

