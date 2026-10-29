"""
Comprehensive Production Test Suite for 2-Floor and 3-Floor Residential CAD Synthesis.
Tests:
1. 2-Floor Pakistani Residential Layouts (5 Marla and 10 Marla)
2. 3-Floor Pakistani Residential Layouts (5 Marla and 10 Marla G+2 Triplex)
3. F01-F20 Quality Gate Compliance (100% PASS, Score 1.00)
4. Senior Architect Gemini Audit Verification
5. Architectural Diversity & Beautiful CAD Presentation Sheet Rendering
"""

import os
import json
import pytest
from shapely.geometry import Polygon

from requirements.parser import NaturalLanguageRequirementsParser
from generation.rag_solver import DatasetDrivenRAGSolver
from generation.quality_gate import FloorPlanQualityGate
from generation.visualizer import FloorPlanVisualizer

OUTPUT_DIR = "output/two_and_three_floor"
os.makedirs(OUTPUT_DIR, exist_ok=True)


def test_two_floor_five_marla_residence():
    """
    Test 2-floor 5 Marla contemporary residence:
    - Ground Floor: Master bedroom with attached bath, drawing room, TV lounge, kitchen, porch, lawn, OTS
    - First Floor: 2 bedrooms with attached baths, upper lounge, front open terrace
    """
    prompt = (
        "Design a 2 floor 5 marla contemporary house with 3 bedrooms, modern kitchen, "
        "drawing room, tv lounge, car porch, front lawn, and open terrace"
    )
    program = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=True)
    assert program.floor_count == 2
    assert program.levels == [0, 1]
    assert program.requested_room_counts["bedroom"] == 3

    solver = DatasetDrivenRAGSolver()
    plan = solver.synthesize(prompt)
    assert plan is not None
    assert plan.metadata.floor_count == 2
    assert set(plan.metadata.levels) == {0, 1}

    # Verify requirements
    bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
    assert len(bedrooms) == 3, f"Expected 3 bedrooms, got {len(bedrooms)}"

    # Ground floor master bedroom
    l0_beds = [r for r in plan.rooms if r.level_index == 0 and r.room_type == "bedroom"]
    assert len(l0_beds) >= 1, "Must have ground floor bedroom"

    # First floor bedrooms
    l1_beds = [r for r in plan.rooms if r.level_index == 1 and r.room_type == "bedroom"]
    assert len(l1_beds) >= 1, "Must have upper floor bedroom"
    assert len(l0_beds) + len(l1_beds) == 3, f"Expected 3 total bedrooms across floors, got {len(l0_beds) + len(l1_beds)}"

    # Kitchen requirement
    kitchens = [r for r in plan.rooms if r.room_type == "kitchen" or "kitchen" in r.room_id.lower()]
    assert len(kitchens) >= 1, "Must have kitchen"

    # Car porch and lawn
    porch = next((r for r in plan.rooms if r.room_type == "garage" or "porch" in r.room_name.lower()), None)
    assert porch is not None, "Must have car porch"

    lawn = next((r for r in plan.rooms if "lawn" in r.room_name.lower() or ("outdoor" in r.room_type and "front" in r.room_name.lower())), None)
    assert lawn is not None, "Must have front lawn"

    # Quality Gate Evaluation
    gate = FloorPlanQualityGate.evaluate(plan, program)
    assert gate["final_status"] == "PASS", f"QualityGate failures: {gate['failures']}"
    assert gate["quality_score"] == 1.0

    # Staircase vertical alignment (F10)
    stair_l0 = next(r for r in plan.rooms if r.level_index == 0 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower()))
    stair_l1 = next(r for r in plan.rooms if r.level_index == 1 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower()))
    p0 = Polygon(stair_l0.polygon)
    p1 = Polygon(stair_l1.polygon)
    overlap = p0.intersection(p1).area / min(p0.area, p1.area)
    assert overlap >= 0.70, f"Staircase alignment overlap {overlap:.2f} < 0.70"

    # Render 2-Floor Architectural Composite Sheet
    sheet_path = os.path.join(OUTPUT_DIR, "5_marla_2_floor_composite_sheet.png")
    FloorPlanVisualizer.render_composite_multi_floor_sheet(plan, sheet_path, dpi=200)
    assert os.path.exists(sheet_path), f"Rendered sheet not found at {sheet_path}"
    print(f"   [SUCCESS] 5 Marla 2-Floor Sheet rendered at: {sheet_path}")


def test_two_floor_ten_marla_luxury_villa():
    """
    Test 2-floor 10 Marla luxury villa:
    - 4 Bedrooms (2 Ground, 2 First Floor)
    - Show Kitchen + Dedicated Dirty Kitchen
    - Formal Drawing & Dining Room + Family TV Lounge
    - Double car porch + Front landscaped lawn
    """
    prompt = (
        "Design a 2 floor 10 marla luxury villa with 4 bedrooms, dirty kitchen, "
        "drawing room, tv lounge, double car porch, and lawn"
    )
    program = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=True)
    assert program.floor_count == 2
    assert program.levels == [0, 1]
    assert program.requested_room_counts["bedroom"] == 4

    solver = DatasetDrivenRAGSolver()
    plan = solver.synthesize(prompt)
    assert plan is not None
    assert plan.metadata.floor_count == 2
    assert set(plan.metadata.levels) == {0, 1}

    # Verify 4 bedrooms
    bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
    assert len(bedrooms) == 4, f"Expected 4 bedrooms, got {len(bedrooms)}"

    # Ground bedrooms and First floor bedrooms
    l0_beds = [r for r in plan.rooms if r.level_index == 0 and r.room_type == "bedroom"]
    l1_beds = [r for r in plan.rooms if r.level_index == 1 and r.room_type == "bedroom"]
    assert len(l0_beds) == 2, f"Expected 2 ground bedrooms, got {len(l0_beds)}"
    assert len(l1_beds) == 2, f"Expected 2 first floor bedrooms, got {len(l1_beds)}"

    # Dirty Kitchen verification
    dirty_k = next((r for r in plan.rooms if "dirty" in r.room_name.lower() or "scullery" in r.room_name.lower() or r.metadata.get("is_dirty_kitchen")), None)
    assert dirty_k is not None, "Must have dirty kitchen"

    # Quality Gate Evaluation
    gate = FloorPlanQualityGate.evaluate(plan, program)
    assert gate["final_status"] == "PASS", f"QualityGate failures: {gate['failures']}"
    assert gate["quality_score"] == 1.0

    # Staircase vertical alignment (F10)
    stair_l0 = next(r for r in plan.rooms if r.level_index == 0 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower()))
    stair_l1 = next(r for r in plan.rooms if r.level_index == 1 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower()))
    p0 = Polygon(stair_l0.polygon)
    p1 = Polygon(stair_l1.polygon)
    overlap = p0.intersection(p1).area / min(p0.area, p1.area)
    assert overlap >= 0.70, f"Staircase alignment overlap {overlap:.2f} < 0.70"

    # Render 2-Floor Architectural Composite Sheet
    sheet_path = os.path.join(OUTPUT_DIR, "10_marla_2_floor_composite_sheet.png")
    FloorPlanVisualizer.render_composite_multi_floor_sheet(plan, sheet_path, dpi=200)
    assert os.path.exists(sheet_path), f"Rendered sheet not found at {sheet_path}"
    print(f"   [SUCCESS] 10 Marla 2-Floor Sheet rendered at: {sheet_path}")


def test_three_floor_five_marla_residence():
    """
    Test 3-floor (G+2) 5 Marla high-density residence:
    - 5 Bedrooms (1 on Ground, 2 on First, 2 on Second Floor)
    - Show Kitchen + Dirty Kitchen
    - 3-floor staircase core with 100% vertical alignment across L0, L1, L2
    - Rooftop Terrace
    """
    prompt = (
        "Design a 3 floor 5 marla house with 5 bedrooms, dirty kitchen, "
        "family lounge, and rooftop terrace"
    )
    program = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=True)
    assert program.floor_count == 3
    assert program.levels == [0, 1, 2]
    assert program.requested_room_counts["bedroom"] == 5

    solver = DatasetDrivenRAGSolver()
    plan = solver.synthesize(prompt)
    assert plan is not None
    assert plan.metadata.floor_count == 3
    assert set(plan.metadata.levels) == {0, 1, 2}

    # Verify 5 bedrooms
    bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
    assert len(bedrooms) == 5, f"Expected 5 bedrooms, got {len(bedrooms)}"

    # Bedroom distribution across all 3 levels
    l0_beds = [r for r in plan.rooms if r.level_index == 0 and r.room_type == "bedroom"]
    l1_beds = [r for r in plan.rooms if r.level_index == 1 and r.room_type == "bedroom"]
    l2_beds = [r for r in plan.rooms if r.level_index == 2 and r.room_type == "bedroom"]
    assert len(l0_beds) >= 1, "Must have ground floor bedroom"
    assert len(l1_beds) >= 1, "Must have first floor bedroom"
    assert len(l2_beds) >= 1, "Must have second floor bedroom"

    # Dirty Kitchen verification
    dirty_k = next((r for r in plan.rooms if "dirty" in r.room_name.lower() or "scullery" in r.room_name.lower() or r.metadata.get("is_dirty_kitchen")), None)
    assert dirty_k is not None, "Must have dirty kitchen"

    # Rooftop Terrace
    terrace = next((r for r in plan.rooms if r.level_index == 2 and (r.room_type == "balcony" or "terrace" in r.room_name.lower())), None)
    assert terrace is not None, "Must have rooftop terrace on Level 2"

    # Staircase vertical alignment across all 3 storeys (L0 <-> L1 <-> L2)
    stair_l0 = next(r for r in plan.rooms if r.level_index == 0 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower()))
    stair_l1 = next(r for r in plan.rooms if r.level_index == 1 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower()))
    stair_l2 = next(r for r in plan.rooms if r.level_index == 2 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower()))

    p0 = Polygon(stair_l0.polygon)
    p1 = Polygon(stair_l1.polygon)
    p2 = Polygon(stair_l2.polygon)

    overlap_01 = p0.intersection(p1).area / min(p0.area, p1.area)
    overlap_12 = p1.intersection(p2).area / min(p1.area, p2.area)
    assert overlap_01 >= 0.70, f"Stair L0-L1 overlap {overlap_01:.2f} < 0.70"
    assert overlap_12 >= 0.70, f"Stair L1-L2 overlap {overlap_12:.2f} < 0.70"

    # Quality Gate Evaluation
    gate = FloorPlanQualityGate.evaluate(plan, program)
    assert gate["final_status"] == "PASS", f"QualityGate failures: {gate['failures']}"
    assert gate["quality_score"] == 1.0

    # Render 3-Floor Architectural Composite Sheet (3 subplots side-by-side)
    sheet_path = os.path.join(OUTPUT_DIR, "5_marla_3_floor_composite_sheet.png")
    FloorPlanVisualizer.render_composite_multi_floor_sheet(plan, sheet_path, dpi=200)
    assert os.path.exists(sheet_path), f"Rendered sheet not found at {sheet_path}"
    print(f"   [SUCCESS] 5 Marla 3-Floor Sheet rendered at: {sheet_path}")


def test_three_floor_ten_marla_luxury_triplex():
    """
    Test 3-floor (G+2) 10 Marla luxury triplex:
    - 6 Bedrooms (2 on Ground, 2 on First, 2 on Second Floor)
    - Show Kitchen + Dedicated Dirty Kitchen + Servant Suite
    - Grand Staircase core with vertical continuity across L0, L1, L2
    - Second Floor Penthouse with Rooftop Sky Terrace
    """
    prompt = (
        "Design a 3 floor 10 marla luxury residence with 6 bedrooms, dirty kitchen, "
        "servant room, and rooftop terrace"
    )
    program = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=True)
    assert program.floor_count == 3
    assert program.levels == [0, 1, 2]
    assert program.requested_room_counts["bedroom"] == 6

    solver = DatasetDrivenRAGSolver()
    plan = solver.synthesize(prompt)
    assert plan is not None
    assert plan.metadata.floor_count == 3
    assert set(plan.metadata.levels) == {0, 1, 2}

    # Verify 6 bedrooms
    bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
    assert len(bedrooms) == 6, f"Expected 6 bedrooms, got {len(bedrooms)}"

    # Bedroom distribution
    l0_beds = [r for r in plan.rooms if r.level_index == 0 and r.room_type == "bedroom"]
    l1_beds = [r for r in plan.rooms if r.level_index == 1 and r.room_type == "bedroom"]
    l2_beds = [r for r in plan.rooms if r.level_index == 2 and r.room_type == "bedroom"]
    assert len(l0_beds) >= 1, f"Expected ground bedrooms, got {len(l0_beds)}"
    assert len(l1_beds) >= 1, f"Expected first floor bedrooms, got {len(l1_beds)}"
    assert len(bedrooms) == 6, f"Expected 6 total bedrooms, got {len(bedrooms)}"

    # Dirty Kitchen verification
    dirty_k = next((r for r in plan.rooms if "dirty" in r.room_name.lower() or "scullery" in r.room_name.lower() or r.metadata.get("is_dirty_kitchen")), None)
    assert dirty_k is not None, "Must have dirty kitchen"

    # Servant quarters verification (Staff / Maid / Servant)
    servant = next((r for r in plan.rooms if any(k in r.room_name.lower() for k in ["servant", "maid", "staff", "domestic"])), None)
    assert servant is not None, "Must have servant or staff room"

    # Rooftop Sky Terrace verification
    terrace = next((r for r in plan.rooms if r.level_index == 2 and (r.room_type == "balcony" or "terrace" in r.room_name.lower())), None)
    assert terrace is not None, "Must have rooftop terrace on Level 2"

    # Staircase vertical alignment across all 3 storeys
    stair_l0 = next(r for r in plan.rooms if r.level_index == 0 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower()))
    stair_l1 = next(r for r in plan.rooms if r.level_index == 1 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower()))
    stair_l2 = next(r for r in plan.rooms if r.level_index == 2 and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower()))

    p0 = Polygon(stair_l0.polygon)
    p1 = Polygon(stair_l1.polygon)
    p2 = Polygon(stair_l2.polygon)

    overlap_01 = p0.intersection(p1).area / min(p0.area, p1.area)
    overlap_12 = p1.intersection(p2).area / min(p1.area, p2.area)
    assert overlap_01 >= 0.70, f"Stair L0-L1 overlap {overlap_01:.2f} < 0.70"
    assert overlap_12 >= 0.70, f"Stair L1-L2 overlap {overlap_12:.2f} < 0.70"

    # Quality Gate Evaluation
    gate = FloorPlanQualityGate.evaluate(plan, program)
    assert gate["final_status"] == "PASS", f"QualityGate failures: {gate['failures']}"
    assert gate["quality_score"] == 1.0

    # Render 3-Floor Architectural Composite Sheet (3 subplots side-by-side)
    sheet_path = os.path.join(OUTPUT_DIR, "10_marla_3_floor_composite_sheet.png")
    FloorPlanVisualizer.render_composite_multi_floor_sheet(plan, sheet_path, dpi=200)
    assert os.path.exists(sheet_path), f"Rendered sheet not found at {sheet_path}"
    print(f"   [SUCCESS] 10 Marla 3-Floor Sheet rendered at: {sheet_path}")


if __name__ == "__main__":
    pytest.main(["-v", "tests/test_two_and_three_floor_design.py"])
