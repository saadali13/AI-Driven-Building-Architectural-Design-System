"""
5-Marla Canonical Blueprint Catalog (7.62m x 13.72m / 25'-0" x 45'-0").
Defines 10 distinct, production-grade architectural archetypes (v01 to v10).
Achieves 1.0 FloorPlanQualityGate compliance and zero room overlaps.
"""
import sys
import os
from typing import List

PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dataset.schema.canonical import CanonicalFloorPlan, MetadataModel
from dataset.build_master_catalog import (
    rect_poly,
    make_room,
    make_door,
    make_window,
    assemble_plan
)


def _assemble_5m(plan_id: str, w: float, d: float, rooms: List, ops: List, desc: str, typology: str, stair_type: str = "dogleg") -> CanonicalFloorPlan:
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    meta = MetadataModel(
        plan_id=plan_id,
        source_type="synthetic_generated",
        floor_count=2,
        levels=[0, 1],
        provenance={
            "scale": "5_marla",
            "archetype_name": desc,
            "typology": typology,
            "stair_type": stair_type,
            "target_scale": "5_marla"
        }
    )
    return assemble_plan(meta, env, rooms, ops)


def build_5m_v01() -> CanonicalFloorPlan:
    """v01: Classical Segregated Family Residence - Porch, drawing, central lounge, kitchen, rear suite."""
    w, d = 7.62, 13.72
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (1 Car)", 0, 0, 3.8, 4.2, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 3.8, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 3.8, 1.8, w, 4.2, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Central Dogleg Staircase", 0, 4.2, 2.4, 7.5, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Family TV Lounge", 2.4, 4.2, w, 8.8, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Kitchen", 0, 7.5, 2.4, 10.5, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Attached Bath", 0, 10.5, 2.4, 12.2, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Light Shaft & OTS", 0, 12.2, 2.4, d, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 2.4, 8.8, w, d, 0, True))

    ops.append(make_door("d_L0_01", 1.8, 4.2, ["r_L0_porch", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_02", 3.8, 3.0, ["r_L0_porch", "r_L0_drawing"], 1.00, 0))
    ops.append(make_door("d_L0_03", 2.4, 5.5, ["r_L0_stairs", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_04", 4.5, 4.2, ["r_L0_drawing", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_05", 2.4, 8.0, ["r_L0_lounge", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_06", 3.5, 8.8, ["r_L0_lounge", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_07", 2.4, 11.2, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_08", 2.4, 12.8, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 5.5, 1.8, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_02", 5.5, d, 1.50, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Open Terrace", 0, 0, 3.8, 4.2, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Upper Bath 2", 3.8, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Front Bedroom Suite 2", 3.8, 1.8, w, 4.2, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Staircase Landing", 0, 4.2, 2.4, 7.5, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family TV Lounge", 2.4, 4.2, w, 8.8, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Pantry Kitchenette", 0, 7.5, 2.4, 10.5, 1, True))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Master Bath 3", 0, 10.5, 2.4, 12.2, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper Light Shaft", 0, 12.2, 2.4, d, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Master Suite 3", 2.4, 8.8, w, d, 1, True))

    ops.append(make_door("d_L1_01", 2.4, 5.5, ["r_L1_stairs", "r_L1_lounge"], 1.00, 1))
    ops.append(make_door("d_L1_02", 1.8, 4.2, ["r_L1_stairs", "r_L1_terrace"], 0.90, 1))
    ops.append(make_door("d_L1_03", 4.5, 4.2, ["r_L1_lounge", "r_L1_bed2"], 0.90, 1))
    ops.append(make_door("d_L1_04", 5.5, 1.8, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_05", 2.4, 8.0, ["r_L1_lounge", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_06", 3.5, 8.8, ["r_L1_lounge", "r_L1_bed3"], 0.90, 1))
    ops.append(make_door("d_L1_07", 2.4, 11.2, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_08", 2.4, 12.8, ["r_L1_bed3", "r_L1_ots"], 0.80, 1))
    ops.append(make_window("w_L1_01", 5.5, d, 1.50, 0.90, 1))

    return _assemble_5m("master_5_marla_v01", w, d, rooms, ops, "v01: Classical Segregated Family Residence", "central_lounge")


def build_5m_v02() -> CanonicalFloorPlan:
    """v02: Central Courtyard Lightwell - Internal open-to-sky court separating public from private."""
    w, d = 7.62, 13.72
    rooms, ops = [], []
    # L0: Clean non-overlapping tessellation
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (1 Car)", 0, 0, 4.0, 4.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 4.0, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Guest Salon", 4.0, 1.8, w, 4.0, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Side Straight Staircase", 0, 4.0, 1.8, 8.5, 0, False, {"typology": "straight"}))
    rooms.append(make_room("r_L0_courtyard", "outdoor", "Central Open-to-Sky Courtyard", 1.8, 4.0, 4.2, 6.0, 0, False))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Central Courtyard Kitchen", 1.8, 6.0, 4.2, 8.5, 0, True))
    rooms.append(make_room("r_L0_lounge", "living_room", "Courtyard Family Lounge", 4.2, 4.0, w, 8.5, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Attached Bath 1", 0, 8.5, 2.4, 10.8, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Light Shaft", 0, 10.8, 2.4, d, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 2.4, 8.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 1.0, 4.0, ["r_L0_porch", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_02", 4.0, 3.0, ["r_L0_porch", "r_L0_drawing"], 1.00, 0))
    ops.append(make_door("d_L0_03", 4.2, 5.0, ["r_L0_courtyard", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_04", 1.8, 5.0, ["r_L0_stairs", "r_L0_courtyard"], 0.90, 0))
    ops.append(make_door("d_L0_05", 4.2, 7.5, ["r_L0_lounge", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_06", 3.5, 8.5, ["r_L0_lounge", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_07", 2.4, 9.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_08", 2.4, 11.5, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 5.5, 1.8, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_02", 5.0, d, 1.50, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Promenade Terrace", 0, 0, 4.0, 4.0, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Upper Bath 2", 4.0, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Upper Bedroom Suite 2", 4.0, 1.8, w, 4.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Straight Staircase Landing", 0, 4.0, 1.8, 8.5, 1, False, {"typology": "straight"}))
    rooms.append(make_room("r_L1_bridge", "corridor", "Courtyard Overlook Bridge", 1.8, 4.0, 4.2, 6.0, 1, False))
    rooms.append(make_room("r_L1_study", "office", "Executive Study & Office", 1.8, 6.0, 4.2, 8.5, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Skylight Lounge", 4.2, 4.0, w, 8.5, 1, True))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 0, 8.5, 2.4, 10.8, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper Light Shaft", 0, 10.8, 2.4, d, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Master Bedroom 3", 2.4, 8.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 1.8, 5.0, ["r_L1_stairs", "r_L1_bridge"], 0.90, 1))
    ops.append(make_door("d_L1_02", 4.2, 5.0, ["r_L1_bridge", "r_L1_lounge"], 1.00, 1))
    ops.append(make_door("d_L1_03", 5.5, 4.0, ["r_L1_lounge", "r_L1_bed2"], 0.90, 1))
    ops.append(make_door("d_L1_04", 5.5, 1.8, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_05", 4.2, 7.5, ["r_L1_lounge", "r_L1_study"], 0.80, 1))
    ops.append(make_door("d_L1_06", 4.5, 8.5, ["r_L1_lounge", "r_L1_bed3"], 0.90, 1))
    ops.append(make_door("d_L1_07", 2.4, 9.5, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))

    return _assemble_5m("master_5_marla_v02", w, d, rooms, ops, "v02: Central Courtyard Lightwell", "courtyard_planning", "straight")


def build_5m_v03() -> CanonicalFloorPlan:
    """v03: Side Gallery Linear Spine - Straight linear steel stair along boundary, open continuous living."""
    w, d = 7.62, 13.72
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (1 Car)", 0, 0, 4.0, 4.5, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 4.0, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Front Salon", 4.0, 2.0, w, 4.5, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Side Linear Gallery & Stairs", 0, 4.5, 1.8, 10.0, 0, False, {"typology": "straight"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Continuous Great Living Hall", 1.8, 4.5, w, 9.2, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Side Linear Kitchen", 0, 10.0, 3.2, 12.0, 0, True))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Service Lightwell", 0, 12.0, 3.2, d, 0, False))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Ensuite Luxury Bath 1", 3.2, 9.2, 5.2, 11.2, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Rear Master Suite 1", 3.2, 11.2, w, d, 0, True))

    ops.append(make_door("d_L0_01", 1.0, 4.5, ["r_L0_porch", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_02", 4.0, 3.2, ["r_L0_porch", "r_L0_drawing"], 1.00, 0))
    ops.append(make_door("d_L0_03", 1.8, 6.0, ["r_L0_stairs", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_04", 4.5, 4.5, ["r_L0_drawing", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_05", 2.0, 9.2, ["r_L0_lounge", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_06", 4.0, 9.2, ["r_L0_lounge", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_07", 4.0, 11.2, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_08", 2.0, 12.0, ["r_L0_kitchen", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 5.5, 2.0, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_02", 5.5, d, 1.50, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Linear Terrace", 0, 0, 4.0, 4.5, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Upper Bath 2", 4.0, 0, w, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Front Bedroom Suite 2", 4.0, 2.0, w, 4.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Linear Gallery", 0, 4.5, 1.8, 10.0, 1, False, {"typology": "straight"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Media Lounge", 1.8, 4.5, w, 9.2, 1, True))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 0, 10.0, 3.2, 12.0, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper Lightwell", 0, 12.0, 3.2, d, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Master Suite 3", 3.2, 9.2, w, d, 1, True))

    # Connecting door from gallery to lounge and terrace on L1
    ops.append(make_door("d_L1_01", 1.8, 6.0, ["r_L1_stairs", "r_L1_lounge"], 1.10, 1))
    ops.append(make_door("d_L1_02", 1.0, 4.5, ["r_L1_stairs", "r_L1_terrace"], 1.00, 1))
    ops.append(make_door("d_L1_03", 4.5, 4.5, ["r_L1_lounge", "r_L1_bed2"], 0.90, 1))
    ops.append(make_door("d_L1_04", 5.5, 2.0, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_05", 4.0, 9.2, ["r_L1_lounge", "r_L1_bed3"], 0.90, 1))
    ops.append(make_door("d_L1_06", 3.2, 10.5, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))

    return _assemble_5m("master_5_marla_v03", w, d, rooms, ops, "v03: Side Gallery Linear Spine", "side_corridor", "straight")


def build_5m_v04() -> CanonicalFloorPlan:
    """v04: Double Show & Dirty Kitchen Scullery - Open show kitchen + enclosed rear wet kitchen."""
    w, d = 7.62, 13.72
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (1 Car)", 0, 0, 3.8, 4.2, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 3.8, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Guest Drawing", 3.8, 1.8, w, 4.2, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Enclosed Dogleg Staircase", 0, 4.2, 2.4, 7.5, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Family Lounge", 2.4, 4.2, w, 8.5, 0, True))
    rooms.append(make_room("r_L0_show_kitchen", "kitchen", "Open Show Kitchen", 0, 7.5, 2.4, 10.2, 0, True))
    rooms.append(make_room("r_L0_dirty_kitchen", "kitchen", "Enclosed Scullery Kitchen", 0, 10.2, 2.4, 12.2, 0, True, {"is_dirty_kitchen": True}))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Service Shaft", 0, 12.2, 2.4, d, 0, False))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Ensuite Bath 1", 2.4, 8.5, 4.5, 10.5, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 4.5, 8.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 1.8, 4.2, ["r_L0_porch", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_02", 3.8, 3.0, ["r_L0_porch", "r_L0_drawing"], 1.00, 0))
    ops.append(make_door("d_L0_03", 2.4, 5.5, ["r_L0_stairs", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_04", 4.5, 4.2, ["r_L0_drawing", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_05", 2.4, 8.0, ["r_L0_lounge", "r_L0_show_kitchen"], 1.00, 0))
    ops.append(make_door("d_L0_06", 1.2, 10.2, ["r_L0_show_kitchen", "r_L0_dirty_kitchen"], 0.85, 0))
    ops.append(make_door("d_L0_07", 1.2, 12.2, ["r_L0_dirty_kitchen", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_08", 4.5, 9.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_09", 5.5, 8.5, ["r_L0_lounge", "r_L0_bed1"], 0.90, 0))
    ops.append(make_window("w_L0_01", 5.5, 1.8, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_02", 6.0, d, 1.50, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Balcony Terrace", 0, 0, 3.8, 4.2, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Upper Bath 2", 3.8, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Upper Front Bedroom 2", 3.8, 1.8, w, 4.2, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Dogleg Landing", 0, 4.2, 2.4, 7.5, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Living", 2.4, 4.2, w, 8.5, 1, True))
    rooms.append(make_room("r_L1_linen", "dressing_room", "Linen & Utility Store", 0, 7.5, 2.4, 10.2, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Master Bath 3", 0, 10.2, 2.4, 12.2, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper Service Shaft", 0, 12.2, 2.4, d, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Master Suite 3", 2.4, 8.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 2.4, 5.5, ["r_L1_stairs", "r_L1_lounge"], 1.00, 1))
    ops.append(make_door("d_L1_02", 4.5, 4.2, ["r_L1_lounge", "r_L1_bed2"], 0.90, 1))
    ops.append(make_door("d_L1_03", 5.5, 1.8, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_04", 4.5, 8.5, ["r_L1_lounge", "r_L1_bed3"], 0.90, 1))
    ops.append(make_door("d_L1_05", 2.4, 10.5, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))

    return _assemble_5m("master_5_marla_v04", w, d, rooms, ops, "v04: Double Show & Dirty Kitchen Scullery", "double_kitchen")


def build_5m_v05() -> CanonicalFloorPlan:
    """v05: Split Guest-Family Zoning - Ground floor guest suite forward, family zone secluded rear."""
    w, d = 7.62, 13.72
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (1 Car)", 0, 0, 3.6, 4.5, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 3.6, 0, w, 1.6, 0, False))
    rooms.append(make_room("r_L0_guest_bath", "bathroom", "Guest Powder & Bath", 3.6, 1.6, 5.4, 3.2, 0, False))
    rooms.append(make_room("r_L0_guest_bed", "bedroom", "Ground Guest Suite", 3.6, 3.2, w, 6.2, 0, True))
    rooms.append(make_room("r_L0_foyer", "corridor", "Central Distribution Foyer", 0, 4.5, 3.6, 6.2, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Central Feature Staircase", 0, 6.2, 2.2, 9.5, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Secluded Family Lounge", 2.2, 6.2, w, 9.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Rear Island Kitchen", 0, 9.5, 3.0, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Attached Bath 1", 3.0, 9.5, 4.8, 11.5, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Light Shaft", 3.0, 11.5, 4.8, d, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 4.8, 9.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 1.8, 4.5, ["r_L0_porch", "r_L0_foyer"], 1.10, 0))
    ops.append(make_door("d_L0_02", 3.6, 4.5, ["r_L0_foyer", "r_L0_guest_bed"], 0.90, 0))
    ops.append(make_door("d_L0_03", 4.5, 3.2, ["r_L0_guest_bed", "r_L0_guest_bath"], 0.80, 0))
    ops.append(make_door("d_L0_04", 1.5, 6.2, ["r_L0_foyer", "r_L0_stairs"], 1.00, 0))
    ops.append(make_door("d_L0_05", 2.2, 7.5, ["r_L0_stairs", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_06", 1.5, 9.5, ["r_L0_foyer", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_07", 5.5, 9.5, ["r_L0_lounge", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_08", 4.8, 10.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_09", 4.8, 12.5, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", w, 4.5, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_02", 6.0, d, 1.50, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Terrace", 0, 0, 3.6, 4.5, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Upper Bath 2", 3.6, 0, 5.4, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Upper Front Bedroom 2", 3.6, 2.0, w, 6.2, 1, True))
    rooms.append(make_room("r_L1_foyer", "corridor", "Upper Foyer", 0, 4.5, 3.6, 6.2, 1, False))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Staircase", 0, 6.2, 2.2, 9.5, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Lounge", 2.2, 6.2, w, 9.5, 1, True))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Master Bath 3", 3.0, 9.5, 4.8, 11.5, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper Light Shaft", 3.0, 11.5, 4.8, d, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Master Suite 3", 4.8, 9.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 1.8, 4.5, ["r_L1_foyer", "r_L1_terrace"], 0.90, 1))
    ops.append(make_door("d_L1_02", 3.6, 4.5, ["r_L1_foyer", "r_L1_bed2"], 0.90, 1))
    ops.append(make_door("d_L1_03", 4.5, 2.0, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_04", 1.5, 6.2, ["r_L1_foyer", "r_L1_stairs"], 1.00, 1))
    ops.append(make_door("d_L1_05", 2.2, 7.5, ["r_L1_stairs", "r_L1_lounge"], 1.00, 1))
    ops.append(make_door("d_L1_06", 5.5, 9.5, ["r_L1_lounge", "r_L1_bed3"], 0.90, 1))
    ops.append(make_door("d_L1_07", 4.8, 10.5, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))

    return _assemble_5m("master_5_marla_v05", w, d, rooms, ops, "v05: Split Guest-Family Zoning", "split_guest_family")


def build_5m_v06() -> CanonicalFloorPlan:
    """v06: Open-Concept Great Room Pavilion - Integrated living, dining, kitchen hall to rear court."""
    w, d = 7.62, 13.72
    rooms, ops = [], []
    # L0: Clean non-overlapping layout with feature stair along right flank and proportional kitchen
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (1 Car)", 3.42, 0, w, 4.2, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 0, 0, 3.42, 2.2, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 0, 2.2, 2.0, 4.2, 0, False))
    rooms.append(make_room("r_L0_foyer", "corridor", "Entrance Foyer", 2.0, 2.2, 3.42, 4.2, 0, False))
    rooms.append(make_room("r_L0_great_room", "living_room", "Open Concept Great Room", 0, 4.2, 5.62, 8.5, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Open Floating Steel Stair", 5.62, 4.2, w, 8.5, 0, False, {"typology": "straight"}))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 8.5, 4.42, d, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Island Kitchen", 4.42, 8.5, w, 11.5, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Attached Bath 1", 4.42, 11.5, 5.92, d, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Garden Patio Lightwell", 5.92, 11.5, w, d, 0, False))

    ops.append(make_door("d_L0_01", 3.42, 3.2, ["r_L0_porch", "r_L0_foyer"], 1.00, 0))
    ops.append(make_door("d_L0_02", 4.5, 4.2, ["r_L0_porch", "r_L0_great_room"], 1.20, 0))
    ops.append(make_door("d_L0_03", 2.0, 3.2, ["r_L0_foyer", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 2.7, 4.2, ["r_L0_foyer", "r_L0_great_room"], 1.00, 0))
    ops.append(make_door("d_L0_05", 5.62, 6.0, ["r_L0_great_room", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_06", 5.5, 8.5, ["r_L0_great_room", "r_L0_kitchen"], 1.10, 0))
    ops.append(make_door("d_L0_07", 2.5, 8.5, ["r_L0_great_room", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_08", 4.42, 12.2, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_09", 6.5, 11.5, ["r_L0_kitchen", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 2.2, d, 1.80, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Garden Terrace", 3.42, 0, w, 4.2, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Upper Bath 2", 0, 0, 3.42, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Upper Front Bedroom 2", 0, 1.8, 3.42, 4.2, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Gallery Lounge", 0, 4.2, 5.62, 8.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Floating Landing", 5.62, 4.2, w, 8.5, 1, False, {"typology": "straight"}))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Master Suite 3", 0, 8.5, 4.42, d, 1, True))
    rooms.append(make_room("r_L1_linen", "dressing_room", "Linen & Utility Store", 4.42, 8.5, w, 11.5, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 4.42, 11.5, 5.92, d, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper Patio Lightwell", 5.92, 11.5, w, d, 1, False))

    ops.append(make_door("d_L1_01", 5.62, 6.0, ["r_L1_stairs", "r_L1_lounge"], 1.10, 1))
    ops.append(make_door("d_L1_02", 4.0, 4.2, ["r_L1_lounge", "r_L1_terrace"], 1.00, 1))
    ops.append(make_door("d_L1_03", 2.0, 4.2, ["r_L1_lounge", "r_L1_bed2"], 0.90, 1))
    ops.append(make_door("d_L1_04", 1.7, 1.8, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_05", 2.5, 8.5, ["r_L1_lounge", "r_L1_bed3"], 0.90, 1))
    ops.append(make_door("d_L1_06", 4.42, 12.2, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_07", 5.5, 8.5, ["r_L1_lounge", "r_L1_linen"], 0.80, 1))

    return _assemble_5m("master_5_marla_v06", w, d, rooms, ops, "v06: Open-Concept Great Room Pavilion", "open_living", "straight")


def build_5m_v07() -> CanonicalFloorPlan:
    """v07: Executive Study & Home Office - Dedicated professional work-from-home suite."""
    w, d = 7.62, 13.72
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (1 Car)", 0, 0, 3.8, 4.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 3.8, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_study", "office", "Executive Home Office & Study", 3.8, 1.8, w, 4.0, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Central Staircase", 0, 4.0, 2.4, 7.2, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Family TV Lounge", 2.4, 4.0, w, 8.8, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Kitchen", 0, 7.2, 2.4, 10.2, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Attached Bath 1", 0, 10.2, 2.4, 12.0, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear OTS Ventilation", 0, 12.0, 2.4, d, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 2.4, 8.8, w, d, 0, True))

    ops.append(make_door("d_L0_01", 1.8, 4.0, ["r_L0_porch", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_02", 3.8, 2.8, ["r_L0_porch", "r_L0_study"], 1.00, 0))
    ops.append(make_door("d_L0_03", 2.4, 5.5, ["r_L0_stairs", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_04", 4.5, 4.0, ["r_L0_study", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_05", 2.4, 8.0, ["r_L0_lounge", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_06", 3.5, 8.8, ["r_L0_lounge", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_07", 2.4, 11.0, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_08", 2.4, 12.8, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 5.5, 1.8, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_02", 5.5, d, 1.50, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Terrace", 0, 0, 3.8, 4.0, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Upper Bath 2", 3.8, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Upper Front Bedroom 2", 3.8, 1.8, w, 4.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Landing", 0, 4.0, 2.4, 7.2, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Living", 2.4, 4.0, w, 8.8, 1, True))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 0, 10.2, 2.4, 12.0, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper Ventilation Shaft", 0, 12.0, 2.4, d, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Master Suite 3", 2.4, 8.8, w, d, 1, True))

    ops.append(make_door("d_L1_01", 2.4, 5.5, ["r_L1_stairs", "r_L1_lounge"], 1.00, 1))
    ops.append(make_door("d_L1_02", 4.5, 4.0, ["r_L1_lounge", "r_L1_bed2"], 0.90, 1))
    ops.append(make_door("d_L1_03", 5.5, 1.8, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_04", 3.5, 8.8, ["r_L1_lounge", "r_L1_bed3"], 0.90, 1))
    ops.append(make_door("d_L1_05", 2.4, 11.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))

    return _assemble_5m("master_5_marla_v07", w, d, rooms, ops, "v07: Executive Study & Home Office", "executive_study")


def build_5m_v08() -> CanonicalFloorPlan:
    """v08: Dual Ground Master Suites (4-Bed High-Density Family)."""
    w, d = 7.62, 13.72
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (1 Car)", 0, 0, 3.8, 4.2, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 3.8, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Ground Suite 1 (Front)", 3.8, 1.8, w, 4.2, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Central Compact Staircase", 0, 4.2, 2.4, 7.5, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Family Lounge", 2.4, 4.2, 5.0, 8.8, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Ensuite Bath 1", 5.0, 4.2, w, 6.2, 0, False))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Central Kitchen", 5.0, 6.2, w, 8.8, 0, True))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Master Attached Bath 2", 0, 7.5, 2.4, 9.5, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Light Shaft", 0, 9.5, 2.4, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Master Bedroom Suite 2 (Rear)", 2.4, 8.8, w, d, 0, True))

    ops.append(make_door("d_L0_01", 1.8, 4.2, ["r_L0_porch", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_02", 3.8, 3.0, ["r_L0_porch", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_03", 5.8, 4.2, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_04", 2.4, 5.5, ["r_L0_stairs", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_05", 5.0, 7.5, ["r_L0_lounge", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_06", 3.5, 8.8, ["r_L0_lounge", "r_L0_bed2"], 0.90, 0))
    ops.append(make_door("d_L0_07", 2.4, 9.0, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_08", 2.4, 11.0, ["r_L0_bed2", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 5.5, 1.8, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_02", 5.5, d, 1.50, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Balcony", 0, 0, 3.8, 4.2, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 3.8, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Bedroom Suite 3", 3.8, 1.8, w, 4.2, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Staircase", 0, 4.2, 2.4, 7.5, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Lounge", 2.4, 4.2, 5.0, 8.8, 1, True))
    rooms.append(make_room("r_L1_study", "office", "Upper Study", 5.0, 4.2, w, 8.8, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Upper Bath 4", 0, 7.5, 2.4, 9.5, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper Light Shaft", 0, 9.5, 2.4, d, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Upper Master Bedroom 4", 2.4, 8.8, w, d, 1, True))

    ops.append(make_door("d_L1_01", 2.4, 5.5, ["r_L1_stairs", "r_L1_lounge"], 1.00, 1))
    ops.append(make_door("d_L1_02", 4.5, 4.2, ["r_L1_lounge", "r_L1_bed3"], 0.90, 1))
    ops.append(make_door("d_L1_03", 5.5, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 5.0, 6.5, ["r_L1_lounge", "r_L1_study"], 0.90, 1))
    ops.append(make_door("d_L1_05", 3.5, 8.8, ["r_L1_lounge", "r_L1_bed4"], 0.90, 1))
    ops.append(make_door("d_L1_06", 2.4, 9.0, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))

    return _assemble_5m("master_5_marla_v08", w, d, rooms, ops, "v08: Dual Ground Master Suites", "dual_suites")


def build_5m_v09() -> CanonicalFloorPlan:
    """v09: Corner Splayed Porch - Dual frontage aspect with diagonal sightlines."""
    w, d = 7.62, 13.72
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Corner Splayed Porch", 0, 0, 4.5, 4.5, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Wrap Landscaped Garden", 4.5, 0, w, 2.2, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Corner Drawing Salon", 4.5, 2.2, w, 5.0, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Rotunda Curved Staircase", 0, 4.5, 2.4, 7.8, 0, False, {"typology": "rotunda"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Family Lounge", 2.4, 5.0, w, 9.2, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Side Kitchen", 0, 7.8, 2.4, 10.5, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Attached Bath 1", 0, 10.5, 2.4, 12.2, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear OTS Lightwell", 0, 12.2, 2.4, d, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 2.4, 9.2, w, d, 0, True))

    ops.append(make_door("d_L0_01", 1.8, 4.5, ["r_L0_porch", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_02", 4.5, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.00, 0))
    ops.append(make_door("d_L0_03", 2.4, 6.0, ["r_L0_stairs", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_04", 4.5, 5.0, ["r_L0_drawing", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_05", 2.4, 8.5, ["r_L0_lounge", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_06", 3.5, 9.2, ["r_L0_lounge", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_07", 2.4, 11.2, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_08", 2.4, 12.8, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 5.5, 2.2, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_02", 5.5, d, 1.50, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Corner Splayed Terrace", 0, 0, 4.5, 4.5, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Upper Bath 2", 4.5, 0, w, 2.2, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Upper Front Bedroom 2", 4.5, 2.2, w, 5.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Rotunda Landing", 0, 4.5, 2.4, 7.8, 1, False, {"typology": "rotunda"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Lounge", 2.4, 5.0, w, 9.2, 1, True))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 0, 10.5, 2.4, 12.2, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper OTS", 0, 12.2, 2.4, d, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Master Suite 3", 2.4, 9.2, w, d, 1, True))

    ops.append(make_door("d_L1_01", 2.4, 6.0, ["r_L1_stairs", "r_L1_lounge"], 1.00, 1))
    ops.append(make_door("d_L1_02", 4.5, 4.0, ["r_L1_lounge", "r_L1_bed2"], 0.90, 1))
    ops.append(make_door("d_L1_03", 5.5, 2.2, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_04", 3.5, 9.2, ["r_L1_lounge", "r_L1_bed3"], 0.90, 1))
    ops.append(make_door("d_L1_05", 2.4, 11.2, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))

    return _assemble_5m("master_5_marla_v09", w, d, rooms, ops, "v09: Corner Splayed Porch", "corner_entrance", "rotunda")


def build_5m_v10() -> CanonicalFloorPlan:
    """v10: Minimalist Concealed Core - Floating central stair, concealed service core, dual light shafts."""
    w, d = 7.62, 13.72
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (1 Car)", 0, 0, 3.8, 4.2, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Zen Lawn", 3.8, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Minimalist Living Salon", 3.8, 1.8, w, 4.2, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Central Floating Spine Stair", 2.5, 4.2, 4.5, 6.8, 0, False, {"typology": "floating"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Open Concept Family Lounge", 0, 4.2, 2.5, 8.8, 0, True))
    rooms.append(make_room("r_L0_dining", "dining_room", "Minimalist Dining Pavilion", 4.5, 4.2, w, 6.8, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Flush Kitchen Core", 4.5, 6.8, w, 8.8, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 0, 8.8, 2.5, 11.0, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Daylight Shaft", 0, 11.0, 2.5, d, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 2.5, 8.8, w, d, 0, True))

    ops.append(make_door("d_L0_01", 1.8, 4.2, ["r_L0_porch", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_02", 3.8, 3.0, ["r_L0_porch", "r_L0_drawing"], 1.00, 0))
    ops.append(make_door("d_L0_03", 2.5, 5.5, ["r_L0_lounge", "r_L0_stairs"], 1.00, 0))
    ops.append(make_door("d_L0_04", 4.5, 5.5, ["r_L0_stairs", "r_L0_dining"], 1.00, 0))
    ops.append(make_door("d_L0_05", 5.5, 6.8, ["r_L0_dining", "r_L0_kitchen"], 1.00, 0))
    ops.append(make_door("d_L0_06", 3.5, 8.8, ["r_L0_lounge", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_07", 2.5, 9.8, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_08", 2.5, 12.0, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 5.5, 1.8, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_02", 5.5, d, 1.50, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Minimalist Terrace", 0, 0, 3.8, 4.2, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Upper Bath 2", 3.8, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Upper Front Bedroom 2", 3.8, 1.8, w, 4.2, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Floating Landing", 2.5, 4.2, 4.5, 6.8, 1, False, {"typology": "floating"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Gallery", 0, 4.2, 2.5, 8.8, 1, True))
    rooms.append(make_room("r_L1_study", "office", "Upper Studio Office", 4.5, 4.2, w, 8.8, 1, True))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Master Bath 3", 0, 8.8, 2.5, 11.0, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper Daylight Shaft", 0, 11.0, 2.5, d, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Master Suite 3", 2.5, 8.8, w, d, 1, True))

    ops.append(make_door("d_L1_01", 2.5, 5.5, ["r_L1_lounge", "r_L1_stairs"], 1.00, 1))
    ops.append(make_door("d_L1_02", 4.5, 5.5, ["r_L1_stairs", "r_L1_study"], 0.90, 1))
    ops.append(make_door("d_L1_03", 2.0, 4.2, ["r_L1_lounge", "r_L1_terrace"], 0.90, 1))
    ops.append(make_door("d_L1_04", 4.5, 4.2, ["r_L1_study", "r_L1_bed2"], 0.90, 1))
    ops.append(make_door("d_L1_05", 5.5, 1.8, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_06", 3.5, 8.8, ["r_L1_lounge", "r_L1_bed3"], 0.90, 1))
    ops.append(make_door("d_L1_07", 2.5, 9.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))

    return _assemble_5m("master_5_marla_v10", w, d, rooms, ops, "v10: Minimalist Concealed Core", "minimalist_core", "floating")
