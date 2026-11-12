# Architectural Testing Ledger & Verification Evidence

**Date**: 2026-10-29  
**Execution Environment**: Python 3.14.4 on Windows 64-bit  
**Total Tests Run**: 44  
**Passing Rate**: 100% (44 Passed, 0 Failed)  

---

## 1. Baseline Test Execution Evidence

### 1.1 Architectural Geometry & Collision Suite
- **Command**: `python -m pytest tests/test_architectural_correction.py tests/test_door_stair_furniture_clearances.py -v`
- **Results**: 27 Passed in 7.91s
- **Verified Capabilities**:
  - Scenario 1: Door-vehicle collision resolution in compact garages (`test_scenario_1_door_vehicle_collision_resolution`) — **PASSED**.
  - Scenario 2: Bedroom door misaligned snapping to host wall (`test_scenario_2_bedroom_door_misaligned_snapped`) — **PASSED**.
  - Scenario 3: Adjacent doors swing conflict avoidance (`test_scenario_3_adjacent_doors_swing_conflict`) — **PASSED**.
  - Scenario 4: Door-furniture obstruction resolution (`test_scenario_4_door_furniture_obstruction`) — **PASSED**.
  - Scenario 5: Front bedroom window 1:1 facade matching (`test_scenario_5_front_bedroom_window_matching`) — **PASSED**.
  - Scenario 6-9: Facade depth occlusion, garage facade bay, main entrance positioning, zero invented openings — **PASSED**.
  - Staircase boundary containment across straight, curved, spiral, bifurcated typologies — **PASSED**.
  - 90-degree door swing quadrant containment across rotations ($0^\circ, 90^\circ, 180^\circ, 270^\circ$) — **PASSED**.
  - Furniture containment: nightstands, showers, kitchen islands, and water closets — **PASSED**.

### 1.2 Master Regression Suite
- **Command**: `python -m pytest tests/test_master_regression.py -v`
- **Results**: 12 Passed in 8.32s
- **Verified Capabilities**:
  - Baseline JSON snapshot integrity & quality gate scoring — **PASSED**.
  - 9 stair typologies swappability & circulation reachability: straight, L-shaped, U-shaped, winder, spiral, curved, ladder, floating, bifurcated — **PASSED**.
  - Vector presentation sheet & AutoCAD DXF layer generation — **PASSED**.

### 1.3 Computer Vision Extraction Verification Suite
- **Command**: `python -m pytest output/experiments/poc_single_plan_extraction/phase_5d/test_phase_5d.py -v`
- **Results**: 5 Passed in 0.34s
- **Verified Capabilities**:
  - Independent ground truth annotations integrity across 3, 7, and 1 Kanal plots — **PASSED**.
  - Penalized IoU mathematical formulation — **PASSED**.
  - Production code non-modification guardrails — **PASSED**.

---

## 2. Regression Instructions for Ongoing Development

To run the complete architectural test battery at any point during development:

```bash
# Run core architectural geometry and collision verification
python -m pytest tests/test_architectural_correction.py tests/test_door_stair_furniture_clearances.py -v

# Run master regression and CAD export validation
python -m pytest tests/test_master_regression.py -v

# Run complete test suite
python -m pytest tests/ -v
```

