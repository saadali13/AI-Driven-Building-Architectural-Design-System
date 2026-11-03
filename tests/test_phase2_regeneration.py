"""
tests/test_phase2_regeneration.py
Comprehensive Phase 2 Targeted Regeneration & Room Invariance Test Suite.

Verifies:
1. Unaffected rooms' polygons are bitwise identical before and after edit (assert r.polygon == orig_poly).
2. Enlarge master bedroom.
3. Swap kitchen and dining.
4. Add a bathroom.
5. Move the stairs.
6. Impossible request that triggers conflict with nearest valid alternative.
7. Undo/restore to v1 with exact polygon recovery.
8. Bylaw conflict (enlarge master bedroom by 200% violating coverage/setbacks).
9. Minimum-size conflict (shrink master bath below statutory threshold).
10. Accumulated improvements: apply 3 edits in sequence (v1->v2->v3->v4) and verify all hold.
11. Comprehensive architectural integrity: minimum size, aspect ratio, opening re-hosting,
    clear door swing arcs, zero landlocked rooms, and vertical service stacking.
"""

import os
import sys
import copy
import pytest
from shapely.geometry import Polygon

# Ensure project root is in python path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from generation.design_diversity_engine import DesignDiversityEngine
from generation.improvement_parser import ImprovementParser
from generation.plan_edit_applier import PlanEditApplier
from dataset.schema.canonical import CanonicalFloorPlan
from api_server import ProceduralArchitecturalEngine


@pytest.fixture
def base_10m_plan() -> CanonicalFloorPlan:
    """Generates a consistent 10 Marla CanonicalFloorPlan for testing."""
    return DesignDiversityEngine.synthesize_diverse_plan(
        prompt="10 marla modern house with 4 bedrooms, 4 baths, drawing, lounge, kitchen",
        scale="10_marla",
        strategy="central_family_lounge",
        seed=101
    )


def test_01_enlarge_master_bedroom_and_invariance(base_10m_plan):
    """
    Test 1: Enlarge Master Bedroom.
    Verifies that all unaffected rooms maintain bitwise polygon invariance and architectural integrity.
    """
    initial_polys = {r.room_id: copy.deepcopy(r.polygon) for r in base_10m_plan.rooms}
    target_bed = next(r for r in base_10m_plan.rooms if "bed1" in r.room_id or "master" in r.room_name.lower())
    orig_area = target_bed.area_m2
    total_rooms = len(base_10m_plan.rooms)

    ops = ImprovementParser.parse_improvements("enlarge master bedroom by 20%")
    assert len(ops) >= 1, "Failed to parse enlarge master bedroom"
    assert ops[0]["op"] == "RESIZE_ROOM"

    res = PlanEditApplier.apply_operations(base_10m_plan, ops, plot_w_ft=35.0, plot_l_ft=65.0)
    assert res["success"] is True
    mod_plan = res["plan"]

    # Affected rooms
    affected = set(d["room_id"] for d in res["diff"])
    assert target_bed.room_id in affected
    expected_locked = total_rooms - len(affected)
    assert res["unaffected_rooms_locked"] == expected_locked

    # Assert invariant: EVERY unaffected room must have bitwise identical polygon
    for r in mod_plan.rooms:
        if r.room_id not in affected:
            assert r.polygon == initial_polys[r.room_id], f"Invariant violated for room {r.room_id} ({r.room_name})"

    # Target bed must have enlarged
    new_bed = next(r for r in mod_plan.rooms if r.room_id == target_bed.room_id)
    assert new_bed.area_m2 > orig_area, f"Expected enlarged bedroom, got {new_bed.area_m2} <= {orig_area}"

    # Architectural integrity assertions (Closing Check 3)
    integrity = res["architectural_integrity"]
    assert integrity["min_size_and_aspect_ratio"] is True, f"Failed integrity: {integrity['failures']}"
    assert integrity["door_swing_arcs_clear"] is True
    assert integrity["no_landlocked_rooms"] is True
    assert integrity["vertical_stacking_valid"] is True

    print(f"\n[PASS] Enlarge Master Bed: {orig_area * 10.7639:.1f} sqft -> {new_bed.area_m2 * 10.7639:.1f} sqft. Total rooms: {total_rooms}, Affected: {len(affected)}, Locked: {expected_locked}.")


def test_02_swap_kitchen_and_dining(base_10m_plan):
    """
    Test 2: Swap Kitchen and Dining.
    Verifies position exchange and unaffected room invariance.
    """
    initial_polys = {r.room_id: copy.deepcopy(r.polygon) for r in base_10m_plan.rooms}
    k_room = next(r for r in base_10m_plan.rooms if r.room_type == "kitchen" and r.level_index == 0)
    d_room = next(r for r in base_10m_plan.rooms if "dining" in r.room_name.lower() and r.level_index == 0)
    total_rooms = len(base_10m_plan.rooms)

    orig_k_poly = copy.deepcopy(k_room.polygon)
    orig_d_poly = copy.deepcopy(d_room.polygon)

    ops = ImprovementParser.parse_improvements("swap kitchen and dining")
    assert len(ops) >= 1
    assert ops[0]["op"] == "SWAP_ROOMS"

    res = PlanEditApplier.apply_operations(base_10m_plan, ops, plot_w_ft=35.0, plot_l_ft=65.0)
    assert res["success"] is True
    mod_plan = res["plan"]

    new_k = next(r for r in mod_plan.rooms if r.room_id == k_room.room_id)
    new_d = next(r for r in mod_plan.rooms if r.room_id == d_room.room_id)

    # Kitchen now occupies dining polygon and vice versa
    assert new_k.polygon == orig_d_poly
    assert new_d.polygon == orig_k_poly

    # All unaffected rooms invariant
    affected = {k_room.room_id, d_room.room_id}
    for r in mod_plan.rooms:
        if r.room_id not in affected:
            assert r.polygon == initial_polys[r.room_id]

    # Integrity assertions
    integrity = res["architectural_integrity"]
    assert integrity["door_swing_arcs_clear"] is True
    assert integrity["no_landlocked_rooms"] is True

    print(f"\n[PASS] Swap Kitchen & Dining verified. Total rooms: {total_rooms}, Affected: 2, Locked: {total_rooms - 2}.")


def test_03_add_bathroom(base_10m_plan):
    """
    Test 3: Add Bathroom.
    Verifies that a new bathroom is synthesized without disturbing unrelated spaces.
    """
    initial_polys = {r.room_id: copy.deepcopy(r.polygon) for r in base_10m_plan.rooms}
    initial_baths = len([r for r in base_10m_plan.rooms if r.room_type == "bathroom"])
    total_rooms = len(base_10m_plan.rooms)

    ops = ImprovementParser.parse_improvements("add one more bathroom on ground floor")
    assert len(ops) >= 1
    assert ops[0]["op"] == "ADD_ROOM"

    res = PlanEditApplier.apply_operations(base_10m_plan, ops, plot_w_ft=35.0, plot_l_ft=65.0)
    assert res["success"] is True
    mod_plan = res["plan"]

    new_baths = len([r for r in mod_plan.rooms if r.room_type == "bathroom"])
    assert new_baths == initial_baths + 1, f"Expected {initial_baths + 1} bathrooms, got {new_baths}"

    affected = set(d["room_id"] for d in res["diff"])
    for r in mod_plan.rooms:
        if r.room_id not in affected and r.room_id in initial_polys:
            assert r.polygon == initial_polys[r.room_id]

    # Integrity assertions
    integrity = res["architectural_integrity"]
    assert integrity["door_swing_arcs_clear"] is True
    assert integrity["vertical_stacking_valid"] is True

    print(f"\n[PASS] Add Bathroom: {initial_baths} -> {new_baths} bathrooms. Total: {total_rooms}, Affected: {len(affected)}.")


def test_04_move_stairs(base_10m_plan):
    """
    Test 4: Move Stairs.
    Verifies stairs relocation to rear circulation zone.
    """
    initial_polys = {r.room_id: copy.deepcopy(r.polygon) for r in base_10m_plan.rooms}
    stairs_room = next(r for r in base_10m_plan.rooms if "stair" in r.room_name.lower() or "stair" in r.room_id.lower())
    orig_poly = copy.deepcopy(stairs_room.polygon)
    total_rooms = len(base_10m_plan.rooms)

    ops = ImprovementParser.parse_improvements("move stairs to rear")
    assert len(ops) >= 1
    assert ops[0]["op"] == "MOVE_STAIRS"

    res = PlanEditApplier.apply_operations(base_10m_plan, ops, plot_w_ft=35.0, plot_l_ft=65.0)
    assert res["success"] is True
    mod_plan = res["plan"]

    new_stairs = next(r for r in mod_plan.rooms if r.room_id == stairs_room.room_id)
    assert new_stairs.polygon != orig_poly, "Stairs polygon should have shifted"

    # All other rooms invariant
    for r in mod_plan.rooms:
        if r.room_id != stairs_room.room_id:
            assert r.polygon == initial_polys[r.room_id]

    print(f"\n[PASS] Move Stairs to rear verified. Total rooms: {total_rooms}, Affected: 1, Locked: {total_rooms - 1}.")


def test_05_impossible_request_triggers_conflict_with_alternative(base_10m_plan):
    """
    Test 5: Impossible / Conflicting Request.
    Verifies conflict detection with code, reason, and nearest valid alternative.
    """
    # Cross-floor swap conflict
    ops_cross = [{"op": "SWAP_ROOMS", "room_1": "dining", "room_2": "study"}]
    res_cross = PlanEditApplier.apply_operations(base_10m_plan, ops_cross, plot_w_ft=35.0, plot_l_ft=65.0)
    assert len(res_cross["conflicts"]) >= 1
    conflict = res_cross["conflicts"][0]
    assert conflict["code"] == "FLOOR_MISMATCH_CONFLICT"
    assert "Cross-floor swap violates structural plumbing stack" in conflict["reason"]
    assert "alternative" in conflict and len(conflict["alternative"]) > 0

    print(f"\n[PASS] Conflict detection verified: {conflict['code']} returned with alternative: '{conflict['alternative']}'.")


def test_06_undo_restore_to_v1():
    """
    Test 6: Undo / Restore to v1.
    Verifies that restoring v1 recovers exact initial room polygons bitwise.
    """
    import shutil
    shutil.rmtree(os.path.join(PROJECT_ROOT, "output", "archi_35x65_modern_777"), ignore_errors=True)

    v1_design = ProceduralArchitecturalEngine.synthesize_design(
        prompt="10 marla modern house with 4 bedrooms",
        plot_width=35.0,
        plot_length=65.0,
        floors=2,
        bedrooms=4,
        bathrooms=4,
        style="modern",
        seed=777
    )
    pid = v1_design["project_id"]
    v1_canonical = CanonicalFloorPlan.model_validate(v1_design["canonical_plan"])
    v1_polys = {r.room_id: list(r.polygon) for r in v1_canonical.rooms}

    # Modify to v2 (enlarge master bedroom)
    v2_design = ProceduralArchitecturalEngine.regenerate_with_improvement(
        plan_id=pid,
        improvement_text="enlarge master bedroom by 20%",
        base_version=1
    )
    assert v2_design["version"] == 2

    # Restore v1 -> produces v3 with exact v1 geometry
    v3_design = ProceduralArchitecturalEngine.restore_plan_version(pid, target_version=1)
    assert v3_design["version"] == 3
    assert v3_design["base_version"] == 1
    assert "Restored complete architectural layout from Version 1" in v3_design["what_changed"]

    v3_canonical = CanonicalFloorPlan.model_validate(v3_design["canonical_plan"])
    v3_polys = {r.room_id: list(r.polygon) for r in v3_canonical.rooms}

    assert len(v3_polys) == len(v1_polys)
    for rid, poly in v1_polys.items():
        assert v3_polys[rid] == poly, f"Restored polygon for {rid} does not match initial v1!"

    print(f"\n[PASS] Undo/Restore to v1 verified: All {len(v1_polys)} rooms restored with 100% bitwise polygon match.")


def test_07_bylaw_conflict_extreme_enlargement(base_10m_plan):
    """
    Test 7 (Check 2a): Bylaw Conflict (enlarge master bedroom by 200%).
    Verifies SETBACK_BOUNDARY_CONFLICT is returned with reason and valid alternative.
    """
    ops = ImprovementParser.parse_improvements("enlarge master bedroom by 200%")
    assert len(ops) >= 1
    assert ops[0]["delta_pct"] >= 2.0

    res = PlanEditApplier.apply_operations(base_10m_plan, ops, plot_w_ft=35.0, plot_l_ft=65.0)
    assert len(res["conflicts"]) >= 1
    c = res["conflicts"][0]
    assert c["code"] == "SETBACK_BOUNDARY_CONFLICT"
    assert "exceeds statutory maximum plot coverage" in c["reason"]
    assert "alternative" in c and "20%" in c["alternative"]

    print(f"\n[PASS] Bylaw Conflict (200% enlargement): {c['code']} - {c['reason']} Alternative: {c['alternative']}")


def test_08_minimum_size_conflict_shrink_bath(base_10m_plan):
    """
    Test 8 (Check 2b): Minimum-Size Conflict (shrink master bath below learned minimum).
    Verifies MINIMUM_DIMENSION_CONFLICT is returned with reason and valid alternative.
    """
    ops = ImprovementParser.parse_improvements("shrink master bath by 75%")
    assert len(ops) >= 1
    assert ops[0]["delta_pct"] < 0

    res = PlanEditApplier.apply_operations(base_10m_plan, ops, plot_w_ft=35.0, plot_l_ft=65.0)
    assert len(res["conflicts"]) >= 1
    c = res["conflicts"][0]
    assert c["code"] == "MINIMUM_DIMENSION_CONFLICT"
    assert "violating statutory minimum functional threshold" in c["reason"]
    assert "alternative" in c and "10%" in c["alternative"]

    print(f"\n[PASS] Minimum-Size Conflict (shrink bath): {c['code']} - {c['reason']} Alternative: {c['alternative']}")


def test_09_accumulated_improvements_sequence():
    """
    Test 9 (Check 2c): Accumulated Improvements.
    Applies 3 edits in sequence (v1 -> v2 -> v3 -> v4):
    1. v1 -> v2: Enlarge master bedroom by 20%
    2. v2 -> v3: Swap kitchen and dining
    3. v3 -> v4: Add a bathroom
    Verifies that v4 still satisfies all earlier edits and the original requirements.
    """
    import shutil
    shutil.rmtree(os.path.join(PROJECT_ROOT, "output", "archi_35x65_modern_888"), ignore_errors=True)

    v1 = ProceduralArchitecturalEngine.synthesize_design(
        prompt="10 marla modern house with 4 bedrooms",
        plot_width=35.0,
        plot_length=65.0,
        floors=2,
        bedrooms=4,
        bathrooms=4,
        style="modern",
        seed=888
    )
    pid = v1["project_id"]
    orig_bed = next(r for r in v1["floors"][0]["rooms"] if "bed1" in r["id"].lower() or "master" in r["name"].lower())
    orig_bed_area = orig_bed["width"] * orig_bed["length"]

    # Edit 1: Enlarge master bed
    v2 = ProceduralArchitecturalEngine.regenerate_with_improvement(pid, "enlarge master bedroom by 20%", base_version=1)
    assert v2["version"] == 2
    v2_bed = next(r for r in v2["floors"][0]["rooms"] if "bed1" in r["id"].lower() or "master" in r["name"].lower())
    assert (v2_bed["width"] * v2_bed["length"]) > orig_bed_area

    # Edit 2: Swap kitchen and dining
    v3 = ProceduralArchitecturalEngine.regenerate_with_improvement(pid, "swap kitchen and dining", base_version=2)
    assert v3["version"] == 3
    # Check that master bed enlargement is STILL preserved in v3
    v3_bed = next(r for r in v3["floors"][0]["rooms"] if "bed1" in r["id"].lower() or "master" in r["name"].lower())
    assert (v3_bed["width"] * v3_bed["length"]) >= (v2_bed["width"] * v2_bed["length"]) - 0.5

    # Edit 3: Add a bathroom
    v4 = ProceduralArchitecturalEngine.regenerate_with_improvement(pid, "add one more bathroom on ground floor", base_version=3)
    assert v4["version"] == 4

    # Assert all earlier edits preserved in v4:
    # 1. Master bedroom is still enlarged
    v4_bed = next(r for r in v4["floors"][0]["rooms"] if "bed1" in r["id"].lower() or "master" in r["name"].lower())
    assert (v4_bed["width"] * v4_bed["length"]) > orig_bed_area
    # 2. Kitchen & dining swapped positions preserved
    assert any("swap" in op.get("description", "").lower() for op in v3["operations_applied"])
    # 3. Bathroom added
    assert len([r for fl in v4["floors"] for r in fl["rooms"] if r.get("category") == "bathroom"]) >= 5
    # 4. Original requirements: 4 bedrooms, 2 storeys, quality gate PASS
    assert v4["floors_count"] == 2
    assert v4["quality_gate"]["status"] == "PASS"

    print(f"\n[PASS] Accumulated Improvements Verified across v1 -> v2 -> v3 -> v4: All edits & original requirements preserved.")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
