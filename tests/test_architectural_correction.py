"""
Comprehensive Test Suite for Architectural Corrections:
Interior Floor Plan Door Placement, Swing Clearance, Vehicle Safety,
and Floor-Plan-Accurate Front Elevation Mapping.

Covers all 10 Mandatory Scenarios:
1. Door opening toward a parked vehicle (detected and resolved).
2. Bedroom door positioned away from intended wall (detected and auto-snapped).
3. Two adjacent doors with conflicting swing areas (detected and resolved).
4. Door obstructed by furniture (detected and resolved).
5. Front-facing bedroom window (1:1 coordinate and host-room matching).
6. Living room and kitchen with different exterior-wall positions (facade depth occlusion).
7. Garage occupying one side of the front facade (accurate bay mapping).
8. Main entrance positioned between garage and living area (accurate placement).
9. Layout with no front-facing window for a particular room (zero invented openings).
10. User modifying a room or moving a window (dynamic facade invalidation & re-synchronization).
"""

import os
import sys
import pytest
from shapely.geometry import Polygon, box, Point

# Ensure project root is on path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dataset.schema.canonical import (
    CanonicalFloorPlan,
    MetadataModel,
    RoomModel,
    OpeningModel,
    WallModel
)
from dataset.build_master_catalog import rect_poly, assemble_plan
from generation.door_clearance_engine import DoorClearanceEngine
from generation.floor_plan_to_elevation_mapper import FloorPlanToElevationMapper
from generation.architectural_validator_engine import ArchitecturalValidatorEngine


def _create_base_plan() -> CanonicalFloorPlan:
    """Creates a clean canonical test plan for unit test scenarios."""
    meta = MetadataModel(
        plan_id="test_plan_001",
        source_type="synthetic_generated",
        floor_count=2,
        levels=[0, 1],
        provenance={"scale": "10_marla", "architectural_style": "modern_contemporary"}
    )
    env = rect_poly(0.0, 0.0, 10.67, 19.81)

    rooms = [
        # Level 0
        RoomModel(
            room_id="r_L0_porch", room_name="Car Porch", room_type="garage",
            polygon=rect_poly(0.0, 0.0, 5.49, 5.49), area_m2=30.14,
            centroid=[2.75, 2.75], level_index=0, is_habitable=False
        ),
        RoomModel(
            room_id="r_L0_foyer", room_name="Entrance Foyer", room_type="corridor",
            polygon=rect_poly(2.44, 5.49, 5.49, 7.32), area_m2=5.58,
            centroid=[3.96, 6.40], level_index=0, is_habitable=False
        ),
        RoomModel(
            room_id="r_L0_powder", room_name="Powder Room", room_type="bathroom",
            polygon=rect_poly(0.0, 5.49, 2.44, 7.32), area_m2=4.46,
            centroid=[1.22, 6.40], level_index=0, is_habitable=False
        ),
        RoomModel(
            room_id="r_L0_drawing", room_name="Formal Drawing", room_type="living_room",
            polygon=rect_poly(5.49, 1.83, 10.67, 6.10), area_m2=22.12,
            centroid=[8.08, 3.96], level_index=0, is_habitable=True
        ),
        RoomModel(
            room_id="r_L0_lounge", room_name="TV Lounge", room_type="living_room",
            polygon=rect_poly(2.44, 7.32, 10.67, 12.80), area_m2=45.10,
            centroid=[6.55, 10.06], level_index=0, is_habitable=True
        ),
        RoomModel(
            room_id="r_L0_lobby", room_name="Vestibule Lobby", room_type="corridor",
            polygon=rect_poly(0.0, 10.50, 2.44, 12.80), area_m2=5.61,
            centroid=[1.22, 11.65], level_index=0, is_habitable=False
        ),
        RoomModel(
            room_id="r_L0_bed1", room_name="Master Suite", room_type="bedroom",
            polygon=rect_poly(0.0, 12.80, 5.49, 18.29), area_m2=30.14,
            centroid=[2.75, 15.54], level_index=0, is_habitable=True
        ),
        # Level 1
        RoomModel(
            room_id="r_L1_terrace", room_name="Front Sky Terrace", room_type="balcony",
            polygon=rect_poly(0.0, 0.0, 5.49, 5.49), area_m2=30.14,
            centroid=[2.75, 2.75], level_index=1, is_habitable=False
        ),
        RoomModel(
            room_id="r_L1_bed3", room_name="Front Master Suite 3", room_type="bedroom",
            polygon=rect_poly(5.49, 1.83, 10.67, 6.10), area_m2=22.12,
            centroid=[8.08, 3.96], level_index=1, is_habitable=True
        )
    ]

    openings = [
        # Main Entry Door
        OpeningModel(
            opening_id="d_L0_main_entry", opening_type="door", position=[3.96, 5.49],
            width_m=1.20, height_m=2.10, connects_rooms=["r_L0_porch", "r_L0_foyer"], level_index=0,
            metadata={"is_double": True, "swing_dir": 1, "hinge_side": 0}
        ),
        # Drawing Room Front Window
        OpeningModel(
            opening_id="w_L0_drawing_front", opening_type="window", position=[8.08, 1.83],
            width_m=2.40, height_m=1.80, connects_rooms=["r_L0_drawing"], level_index=0
        ),
        # Level 1 Bedroom 3 Front Window
        OpeningModel(
            opening_id="w_L1_bed3_front", opening_type="window", position=[8.08, 1.83],
            width_m=2.40, height_m=1.80, connects_rooms=["r_L1_bed3"], level_index=1
        )
    ]

    return assemble_plan(meta, env, rooms, openings)


# ===========================================================================
# SCENARIO 1: Door opening toward a parked vehicle (detected and resolved)
# ===========================================================================
def test_scenario_1_door_vehicle_collision_resolution():
    plan = _create_base_plan()
    # Add a door connecting Powder Room into Car Porch directly behind parked SUV (x=1.30, y=5.49)
    # swinging South (-1) into the porch
    door = OpeningModel(
        opening_id="d_test_porch_entry", opening_type="door", position=[1.30, 5.49],
        width_m=0.90, height_m=2.10, connects_rooms=["r_L0_powder", "r_L0_porch"], level_index=0,
        metadata={"swing_dir": -1, "hinge_side": 0}  # -1 swings into porch!
    )
    plan.openings.append(door)

    # Validate before correction: swept arc must intersect the SUV in the porch
    initial_poly = DoorClearanceEngine.compute_door_swing_polygon(door, plan, override_swing_dir=-1)
    porch = plan.get_room_by_id("r_L0_porch")
    porch_obs = DoorClearanceEngine.extract_room_fixed_obstacles(porch, plan)
    vehicle_hit = any(initial_poly.intersects(obs_poly) for _, obs_poly in porch_obs)
    assert vehicle_hit, "Pre-condition: Door swing must conflict with vehicle footprint."

    # Run automated resolution
    validated_plan, report = DoorClearanceEngine.validate_and_correct_doors(plan)

    # Verify conflict was detected and resolved
    assert report["door_swing_conflicts_detected"] >= 1
    assert report["vehicle_conflicts_prevented"] >= 1

    # Verify door swing was flipped away from vehicle (swing_dir changed to +1 into powder room)
    corrected_door = next(op for op in validated_plan.openings if op.opening_id == "d_test_porch_entry")
    final_poly = DoorClearanceEngine.compute_door_swing_polygon(corrected_door, validated_plan)
    final_hit = any(final_poly.intersects(obs_poly) for _, obs_poly in porch_obs)
    assert not final_hit, "Post-condition: Door must not swing into parked vehicle."


# ===========================================================================
# SCENARIO 2: Bedroom door positioned away from intended wall (auto-snapped)
# ===========================================================================
def test_scenario_2_bedroom_door_misaligned_snapped():
    plan = _create_base_plan()
    # Add a door with position y=13.05 (away from actual wall y=12.80) and x=5.60 (past wall corner 5.49)
    door = OpeningModel(
        opening_id="d_test_bed_misaligned", opening_type="door", position=[5.60, 13.05],
        width_m=0.90, height_m=2.10, connects_rooms=["r_L0_lounge", "r_L0_bed1"], level_index=0
    )
    plan.openings.append(door)

    validated_plan, report = DoorClearanceEngine.validate_and_correct_doors(plan)

    # Verify misalignment was corrected
    assert report["doors_with_misalignment_fixed"] >= 1
    corrected_door = next(op for op in validated_plan.openings if op.opening_id == "d_test_bed_misaligned")
    # Position must be snapped to wall line y=12.80
    assert abs(corrected_door.position[1] - 12.80) <= 0.05
    # Position must be clamped within wall segment [0.0, 5.49] with corner margin
    assert corrected_door.position[0] <= 5.49 - DoorClearanceEngine.MIN_CORNER_SETBACK_M


# ===========================================================================
# SCENARIO 3: Two adjacent doors with conflicting swing areas
# ===========================================================================
def test_scenario_3_adjacent_doors_swing_conflict():
    plan = _create_base_plan()
    # Place two adjacent doors on the same wall segment swinging into the same space
    d1 = OpeningModel(
        opening_id="d_adj_1", opening_type="door", position=[3.20, 12.80],
        width_m=0.90, height_m=2.10, connects_rooms=["r_L0_lounge", "r_L0_bed1"], level_index=0,
        metadata={"swing_dir": -1, "hinge_side": 1}  # hinge on right
    )
    d2 = OpeningModel(
        opening_id="d_adj_2", opening_type="door", position=[3.80, 12.80],
        width_m=0.90, height_m=2.10, connects_rooms=["r_L0_lounge", "r_L0_bed1"], level_index=0,
        metadata={"swing_dir": -1, "hinge_side": 0}  # hinge on left, swings into d1
    )
    plan.openings.extend([d1, d2])

    # Pre-check: initial sweeps intersect
    p1 = DoorClearanceEngine.compute_door_swing_polygon(d1, plan)
    p2 = DoorClearanceEngine.compute_door_swing_polygon(d2, plan)
    assert p1.intersects(p2), "Pre-condition: Adjacent door sweeps must collide."

    # Validate and resolve
    validated_plan, report = DoorClearanceEngine.validate_and_correct_doors(plan)
    assert report["door_swing_conflicts_detected"] >= 1
    assert report["door_to_door_conflicts_resolved"] >= 1


# ===========================================================================
# SCENARIO 4: Door obstructed by furniture (wardrobe/bed)
# ===========================================================================
def test_scenario_4_door_furniture_obstruction():
    plan = _create_base_plan()
    # Place a door connecting lobby into bed1 at x=0.85, swinging into bed1 (+1) right into the wardrobe (x=0.05 to 0.65)
    door = OpeningModel(
        opening_id="d_bed_wardrobe_clash", opening_type="door", position=[0.85, 12.80],
        width_m=0.90, height_m=2.10, connects_rooms=["r_L0_lobby", "r_L0_bed1"], level_index=0,
        metadata={"swing_dir": 1, "hinge_side": 0}
    )
    plan.openings.append(door)

    validated_plan, report = DoorClearanceEngine.validate_and_correct_doors(plan)
    assert report["furniture_conflicts_resolved"] >= 1


# ===========================================================================
# SCENARIO 5: Front-facing bedroom window (1:1 plan matching)
# ===========================================================================
def test_scenario_5_front_bedroom_window_matching():
    plan = _create_base_plan()
    facade_data = FloorPlanToElevationMapper.extract_facade_data_model(plan)

    # Verify Level 1 front openings include the bedroom window at exact X=8.08, width=2.40m
    w_l1 = next((op for op in facade_data["front_openings_l1"] if op["opening_id"] == "w_L1_bed3_front"), None)
    assert w_l1 is not None, "Elevation mapper must detect Level 1 front bedroom window."
    assert abs(w_l1["x"] - 8.08) < 0.05
    assert abs(w_l1["width"] - 2.40) < 0.05
    assert "Master Suite" in w_l1["host_room"]


# ===========================================================================
# SCENARIO 6: Living room and kitchen with different exterior-wall positions
# ===========================================================================
def test_scenario_6_facade_depth_occlusion():
    plan = _create_base_plan()
    # Add a recessed kitchen at y=9.0m (behind front drawing room y=1.83m)
    kitchen = RoomModel(
        room_id="r_L0_kitchen", room_name="Gourmet Kitchen", room_type="kitchen",
        polygon=rect_poly(5.49, 9.00, 10.67, 13.00), area_m2=20.72,
        centroid=[8.08, 11.00], level_index=0, is_habitable=True
    )
    plan.rooms.append(kitchen)

    facade_data = FloorPlanToElevationMapper.extract_facade_data_model(plan)
    front_room_ids = [r["room_id"] for r in facade_data["l0_front_rooms"]]

    # Front rooms must include Drawing Room (y=1.83), NOT the recessed kitchen (y=9.00)
    assert "r_L0_drawing" in front_room_ids
    assert "r_L0_kitchen" not in front_room_ids


# ===========================================================================
# SCENARIO 7: Garage occupying one side of front facade
# ===========================================================================
def test_scenario_7_garage_facade_bay():
    plan = _create_base_plan()
    facade_data = FloorPlanToElevationMapper.extract_facade_data_model(plan)

    porch = facade_data["porch_info"]
    assert porch is not None, "Garage/Porch must be detected on front facade."
    assert porch["x1"] == 0.0
    assert abs(porch["x2"] - 5.49) < 0.05
    assert abs(porch["width"] - 5.49) < 0.05


# ===========================================================================
# SCENARIO 8: Main entrance positioned between garage and living area
# ===========================================================================
def test_scenario_8_main_entrance_positioning():
    plan = _create_base_plan()
    facade_data = FloorPlanToElevationMapper.extract_facade_data_model(plan)

    main_entry = facade_data["main_entrance_door"]
    assert main_entry is not None, "Main entrance must be identified."
    # Placed at x=3.96m inside the porch foyer access
    assert abs(main_entry["x"] - 3.96) < 0.05
    assert main_entry["is_double"] is True


# ===========================================================================
# SCENARIO 9: Layout with no front-facing window for a particular room
# ===========================================================================
def test_scenario_9_zero_invented_openings():
    plan = _create_base_plan()
    # The Car Porch and Foyer have no front window in plan.openings
    facade_data = FloorPlanToElevationMapper.extract_facade_data_model(plan)
    consistency = FloorPlanToElevationMapper.verify_consistency(plan)

    assert consistency["missing_openings"] == 0
    assert consistency["invented_openings"] == 0
    assert consistency["overall_status"] == "PASS"


# ===========================================================================
# SCENARIO 10: Dynamic re-synchronization when floor plan window moves
# ===========================================================================
def test_scenario_10_dynamic_synchronization_on_plan_change():
    plan = _create_base_plan()
    initial_data = FloorPlanToElevationMapper.extract_facade_data_model(plan)
    w_initial = next(op for op in initial_data["front_openings_l0"] if op["opening_id"] == "w_L0_drawing_front")
    assert abs(w_initial["x"] - 8.08) < 0.05

    # User modifies window: moves it from x=8.08m to x=7.20m and changes width to 3.00m
    plan_window = next(op for op in plan.openings if op.opening_id == "w_L0_drawing_front")
    plan_window.position = [7.20, 1.83]
    plan_window.width_m = 3.00

    # Invalidate and re-extract facade model
    updated_data = FloorPlanToElevationMapper.extract_facade_data_model(plan)
    w_updated = next(op for op in updated_data["front_openings_l0"] if op["opening_id"] == "w_L0_drawing_front")

    assert abs(w_updated["x"] - 7.20) < 0.05, "Facade window position must update to x=7.20m."
    assert abs(w_updated["width"] - 3.00) < 0.05, "Facade window width must update to 3.00m."
