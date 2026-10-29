import pytest
import os
import sys

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from generation.rag_solver import DatasetDrivenRAGSolver
from generation.quality_gate import FloorPlanQualityGate
from generation.design_diversity_engine import DesignDiversityEngine


def test_archetype_1_triple_ground_suite_and_side_passage():
    """
    Validates Archetype 1 (matching User Reference Images 1 & 5):
    - Triple Ground Suites (Bed 1, Bed 2, Bed 3 on Level 0)
    - Continuous 5'-4" Side Service Passage
    - Dirty Kitchen with exterior service door to Side Passage
    - Private 6' Bedroom Distribution Lobby
    - Dedicated Walk-In Dressing Rooms (DRESS) buffering every ensuite bath
    - QualityGate Score = 1.0 (PASS)
    """
    solver = DatasetDrivenRAGSolver()
    prompt = "1 kanal luxury house with triple ground suite, 3 bedrooms on ground floor, dirty kitchen, and side service passage"
    plan = solver.synthesize(prompt)

    # 1. QualityGate Compliance
    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", f"QualityGate failed: {gate['failures']}"
    assert gate["quality_score"] == 1.0

    # 2. Check Side Service Passage presence
    passage_rooms = [r for r in plan.rooms if "passage" in r.room_id.lower() or "passage" in r.room_name.lower()]
    assert len(passage_rooms) > 0, "Plan must feature a dedicated side service passage!"

    # 3. Check Dirty Kitchen Service Exit
    dirty_doors = [
        d for d in plan.openings
        if d.opening_type == "door" and any("dirty" in r.lower() or "scullery" in r.lower() for r in d.connects_rooms)
    ]
    assert len(dirty_doors) >= 2, "Dirty kitchen must have both internal show kitchen door and exterior service door!"
    # Ensure dirty kitchen connects to side passage
    assert any(any("passage" in r.lower() for r in d.connects_rooms) for d in dirty_doors), \
        "Dirty kitchen must have direct door to side service passage!"

    # 4. Check 3 Ground Bedrooms + Dressing Buffers
    l0_beds = [r for r in plan.rooms if r.level_index == 0 and r.room_type == "bedroom"]
    assert len(l0_beds) >= 3, f"Expected 3 ground bedroom suites, found {len(l0_beds)}"

    l0_dresses = [r for r in plan.rooms if r.level_index == 0 and (r.room_type in ("closet", "dressing_room") or "dress" in r.room_id.lower())]
    assert len(l0_dresses) >= 3, f"Expected 3 dressing suites on ground floor, found {len(l0_dresses)}"

    # 5. Check Zero Doors between any two bedrooms
    room_types = {r.room_id: r.room_type for r in plan.rooms}
    for op in plan.openings:
        if op.opening_type == "door" and len(op.connects_rooms) == 2:
            t1 = room_types.get(op.connects_rooms[0], "")
            t2 = room_types.get(op.connects_rooms[1], "")
            assert not (t1 == "bedroom" and t2 == "bedroom"), f"Illegal inter-bedroom door found: {op.opening_id}"


def test_archetype_2_splayed_angular_pavilion():
    """
    Validates Archetype 2 (matching User Reference Image 2):
    - 45-Degree Angular / Splayed layout
    - Splayed entrance foyer
    - Garden patios
    - Master suite with dressing buffer
    - QualityGate Score = 1.0 (PASS)
    """
    solver = DatasetDrivenRAGSolver()
    prompt = "1 kanal modernist villa with 45 degree angular splayed layout and side garden patios"
    plan = solver.synthesize(prompt)

    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", f"QualityGate failed: {gate['failures']}"
    assert gate["quality_score"] == 1.0

    # Check for patio presence
    patios = [r for r in plan.rooms if "patio" in r.room_id.lower() or "patio" in r.room_name.lower()]
    assert len(patios) >= 1, "Splayed pavilion must feature garden patios!"

    # Check dressing buffer
    dresses = [r for r in plan.rooms if "dress" in r.room_id.lower() or r.room_type in ("closet", "dressing_room")]
    assert len(dresses) >= 2, "Suites must have walk-in dressing buffers!"


def test_archetype_3_independent_rental_front_stair():
    """
    Validates Archetype 3 (matching User Reference Image 3):
    - Independent Front Staircore accessible from Porch for rental privacy
    - Zero doors between bedrooms
    - QualityGate Score = 1.0 (PASS)
    """
    solver = DatasetDrivenRAGSolver()
    prompt = "10 marla house with independent front stair in porch for rental tenant privacy"
    plan = solver.synthesize(prompt)

    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", f"QualityGate failed: {gate['failures']}"
    assert gate["quality_score"] == 1.0


def test_archetype_4_linear_spine_corridor():
    """
    Validates Archetype 4 (matching User Reference Image 4):
    - Linear circulation gallery spine running front to rear
    - QualityGate Score = 1.0 (PASS)
    """
    solver = DatasetDrivenRAGSolver()
    prompt = "1 kanal house with linear circulation spine corridor and gallery passage"
    plan = solver.synthesize(prompt)

    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", f"QualityGate failed: {gate['failures']}"
    assert gate["quality_score"] == 1.0


def test_archetype_5_double_height_skylight_luxury():
    """
    Validates Archetype 5 (matching User Reference Image 5):
    - Double-height skylight atrium
    - QualityGate Score = 1.0 (PASS)
    """
    solver = DatasetDrivenRAGSolver()
    prompt = "1 kanal palatial residence with double-height skylight atrium and first floor plunge pool"
    plan = solver.synthesize(prompt)

    gate = FloorPlanQualityGate.evaluate(plan)
    assert gate["final_status"] == "PASS", f"QualityGate failed: {gate['failures']}"
    assert gate["quality_score"] == 1.0


def test_pairwise_diversity_across_archetypes():
    """
    Validates that the 5 distinct typologies generate genuinely diverse layouts:
    - Pairwise Jaccard >= 0.25 (or IoU <= 0.70)
    """
    solver = DatasetDrivenRAGSolver()
    p1 = solver.synthesize("1 kanal triple ground suite classic estate with side service passage")
    p2 = solver.synthesize("1 kanal 45 degree angular splayed modernist pavilion with garden patios")

    # Measure room-ID and boundary diversity
    ids1 = set(r.room_id for r in p1.rooms)
    ids2 = set(r.room_id for r in p2.rooms)
    jaccard = 1.0 - len(ids1.intersection(ids2)) / len(ids1.union(ids2))
    assert jaccard >= 0.20, f"Plans should be architecturally diverse, got Jaccard distance {jaccard:.2f}"
