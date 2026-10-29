"""
10-Marla Canonical Blueprint Catalog (10.67m x 19.81m / 35'-0" x 65'-0").
Defines 10 distinct, production-grade architectural archetypes (v01 to v10).
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


def build_10m_v01() -> CanonicalFloorPlan:
    """v01: Executive Dual-Suite Classical with Dressing Buffers & Service Exit (Authentic Pakistani DHA/LDA 10 Marla)."""
    w, d = 10.67, 19.81
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []

    # =========================================================================
    # LEVEL 0 (GROUND FLOOR)
    # =========================================================================
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (2 Cars)", 0, 0, 5.8, 5.5, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 5.8, 0, 8.5, 2.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 8.5, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 5.8, 2.0, w, 5.5, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Classical Dogleg Staircase", 0, 5.5, 2.6, 9.8, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_dining", "dining_room", "Formal Dining Room", 6.8, 5.5, w, 9.0, 0, True))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Family TV Lounge", 2.6, 5.5, 6.8, 12.5, 0, True))
    rooms.append(make_room("r_L0_show_kitchen", "kitchen", "Open Show Kitchen", 6.8, 9.0, w, 12.5, 0, True))
    rooms.append(make_room("r_L0_dirty_kitchen", "kitchen", "Enclosed Scullery Dirty Kitchen", 0, 9.8, 2.6, 13.5, 0, True, {"is_dirty_kitchen": True}))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Suite Distribution Lobby", 2.6, 12.5, 6.8, 13.5, 0, False))

    # Bed 1 with Dress 1 and Bath 1
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 13.5, 5.2, 17.5, 0, True))
    rooms.append(make_room("r_L0_dress1", "closet", "Master Walk-in Dressing 1", 0, 17.5, 2.6, d, 0, False))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 2.6, 17.5, 5.2, d, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Central Ventilation Light Shaft", 5.2, 16.5, 6.8, d, 0, False))

    # Bed 2 with Dress 2 and Bath 2
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 6.8, 12.5, 8.6, 14.5, 0, False))
    rooms.append(make_room("r_L0_dress2", "closet", "Bed 2 Walk-in Dressing", 8.6, 12.5, w, 14.5, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Ground Bedroom Suite 2", 6.8, 14.5, w, d, 0, True))

    # Doors L0
    ops.append(make_door("d_L0_01", 3.0, 5.5, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.8, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 8.5, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 7.5, 5.5, ["r_L0_drawing", "r_L0_dining"], 1.10, 0))
    ops.append(make_door("d_L0_05", 2.6, 7.5, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_06", 6.8, 7.5, ["r_L0_lounge", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_07", 6.8, 10.5, ["r_L0_lounge", "r_L0_show_kitchen"], 1.00, 0))
    # Dirty kitchen connects to lobby and exterior service exit
    ops.append(make_door("d_L0_08", 2.6, 12.5, ["r_L0_dirty_kitchen", "r_L0_lobby"], 0.90, 0))
    ops.append(make_door("d_L0_08_ext", 0, 11.5, ["r_L0_dirty_kitchen", "r_L0_porch"], 0.85, 0)) # exterior service door!
    ops.append(make_door("d_L0_09", 4.5, 12.5, ["r_L0_lounge", "r_L0_lobby"], 1.10, 0))
    # Lobby to Bed 1
    ops.append(make_door("d_L0_10", 2.6, 13.5, ["r_L0_lobby", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_11", 1.3, 17.5, ["r_L0_bed1", "r_L0_dress1"], 0.85, 0))
    ops.append(make_door("d_L0_12", 2.6, 18.5, ["r_L0_dress1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_13_ots", 5.2, 17.0, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    # Lobby to Bed 2
    ops.append(make_door("d_L0_13", 6.8, 13.5, ["r_L0_lobby", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_14", 7.5, 14.5, ["r_L0_bath2", "r_L0_bed2"], 0.80, 0))
    ops.append(make_door("d_L0_15", 9.2, 14.5, ["r_L0_bed2", "r_L0_dress2"], 0.80, 0))

    # Windows
    ops.append(make_window("w_L0_01", 7.5, 2.0, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.5, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", 8.5, d, 1.80, 0.90, 0))

    # =========================================================================
    # LEVEL 1 (FIRST FLOOR)
    # =========================================================================
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Promenade Terrace", 0, 0, 5.8, 5.5, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 8.5, 0, w, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom Suite 3 (Front)", 5.8, 2.0, w, 5.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Classical Dogleg Staircase Landing", 0, 5.5, 2.6, 9.8, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_media", "living_room", "Executive Media Lounge", 6.8, 5.5, w, 9.0, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Lounge", 2.6, 5.5, 6.8, 12.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Pantry Kitchenette", 6.8, 9.0, w, 12.5, 1, True))
    rooms.append(make_room("r_L1_linen", "closet", "Linen & Utility Storage", 0, 9.8, 2.6, 13.5, 1, False))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Suite Distribution Lobby", 2.6, 12.5, 6.8, 13.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 13.5, 5.2, 17.5, 1, True))
    rooms.append(make_room("r_L1_dress4", "closet", "Upper Master Dressing 4", 0, 17.5, 2.6, d, 1, False))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 2.6, 17.5, 5.2, d, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Central Ventilation Light Shaft Void", 5.2, 16.5, 6.8, d, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 6.8, 12.5, 8.6, 14.5, 1, False))
    rooms.append(make_room("r_L1_dress5", "closet", "Bed 5 Walk-in Dressing", 8.6, 12.5, w, 14.5, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Bedroom Suite 5", 6.8, 14.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.0, 5.5, ["r_L1_lounge", "r_L1_terrace"], 1.20, 1))
    ops.append(make_door("d_L1_02", 5.8, 3.5, ["r_L1_terrace", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 8.5, 2.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 6.8, 7.5, ["r_L1_lounge", "r_L1_media"], 1.10, 1))
    ops.append(make_door("d_L1_05", 2.6, 7.5, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_06", 6.8, 10.5, ["r_L1_lounge", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_07", 2.6, 11.5, ["r_L1_lounge", "r_L1_linen"], 0.80, 1))
    ops.append(make_door("d_L1_08", 4.5, 12.5, ["r_L1_lounge", "r_L1_lobby"], 1.10, 1))
    ops.append(make_door("d_L1_09", 2.6, 13.5, ["r_L1_lobby", "r_L1_bed4"], 0.90, 1))
    ops.append(make_door("d_L1_10", 1.3, 17.5, ["r_L1_bed4", "r_L1_dress4"], 0.85, 1))
    ops.append(make_door("d_L1_11", 2.6, 18.5, ["r_L1_dress4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_12", 6.8, 13.5, ["r_L1_lobby", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_13", 7.5, 14.5, ["r_L1_bath5", "r_L1_bed5"], 0.80, 1))
    ops.append(make_door("d_L1_14", 9.2, 14.5, ["r_L1_bed5", "r_L1_dress5"], 0.80, 1))

    ops.append(make_window("w_L1_01", 7.5, 2.0, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.5, d, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", 8.5, d, 1.80, 0.90, 1))

    meta = MetadataModel(
        plan_id="master_10_marla_v01",
        source_type="synthetic_generated",
        floor_count=2,
        levels=[0, 1],
        provenance={"scale": "10_marla", "stair_type": "dogleg", "typology": "executive_dual_suite_classical"}
    )
    return assemble_plan(meta, env, rooms, ops)


def build_10m_v02() -> CanonicalFloorPlan:
    """v02: Grand Central Atrium - Double-height central atrium skylight with bridge corridor."""
    w, d = 10.67, 19.81
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Front Garage (2 Cars)", 0, 0, 6.0, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Lawn Garden", 6.0, 0, 8.5, 1.8, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 8.5, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 6.0, 1.8, w, 5.5, 0, True))
    rooms.append(make_room("r_L0_foyer", "corridor", "Grand Entrance Foyer", 0, 5.0, 6.0, 7.5, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Straight Flight Atrium Stairs", 0, 7.5, 1.6, 12.0, 0, False, {"typology": "straight"}))
    rooms.append(make_room("r_L0_atrium", "living_room", "Double-Height Central Atrium Court", 1.6, 7.5, 6.0, 12.0, 0, True))
    rooms.append(make_room("r_L0_dining", "dining_room", "Formal Dining Hall", 6.0, 5.5, w, 8.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Executive Island Kitchen", 6.0, 8.5, w, 12.0, 0, True))
    rooms.append(make_room("r_L0_lounge", "living_room", "Family Entertainment Lounge", 0, 12.0, 6.0, 15.5, 0, True))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 6.0, 12.0, w, 16.5, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 6.0, 16.5, 8.5, d, 0, False))
    rooms.append(make_room("r_L0_dress1", "dressing_room", "Master Walk-in Wardrobe", 8.5, 16.5, w, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom 2", 0, 15.5, 4.0, d, 0, True))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 4.0, 15.5, 6.0, 17.5, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Light Shaft OTS", 4.0, 17.5, 6.0, d, 0, False))

    ops.append(make_door("d_L0_01", 2.5, 5.0, ["r_L0_porch", "r_L0_foyer"], 1.30, 0))
    ops.append(make_door("d_L0_02", 6.0, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 8.5, 1.8, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 7.5, 5.5, ["r_L0_drawing", "r_L0_dining"], 1.10, 0))
    ops.append(make_door("d_L0_05", 3.0, 7.5, ["r_L0_foyer", "r_L0_atrium"], 1.40, 0))
    ops.append(make_door("d_L0_06", 1.6, 9.5, ["r_L0_stairs", "r_L0_atrium"], 0.90, 0))
    ops.append(make_door("d_L0_07", 6.0, 7.5, ["r_L0_atrium", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_08", 6.0, 10.0, ["r_L0_atrium", "r_L0_kitchen"], 1.00, 0))
    ops.append(make_door("d_L0_09", 3.0, 12.0, ["r_L0_atrium", "r_L0_lounge"], 1.30, 0))
    ops.append(make_door("d_L0_10", 6.0, 14.0, ["r_L0_lounge", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_11", 7.2, 16.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_12", 9.2, 16.5, ["r_L0_bed1", "r_L0_dress1"], 0.80, 0))
    ops.append(make_door("d_L0_13", 2.0, 15.5, ["r_L0_lounge", "r_L0_bed2"], 0.90, 0))
    ops.append(make_door("d_L0_14", 4.0, 16.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_15", 4.0, 18.5, ["r_L0_bed2", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 7.0, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.0, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", 7.2, d, 1.80, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Promenade Terrace", 0, 0, 6.0, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 8.5, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Front Bedroom Suite 3", 6.0, 1.8, w, 5.5, 1, True))
    rooms.append(make_room("r_L1_study", "study", "Upper Gallery Study", 0, 5.0, 6.0, 7.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Straight Flight Atrium Stairs Landing", 0, 7.5, 1.6, 12.0, 1, False, {"typology": "straight"}))
    rooms.append(make_room("r_L1_bridge", "corridor", "Suspended Atrium Glass Bridge", 1.6, 7.5, 6.0, 12.0, 1, False))
    rooms.append(make_room("r_L1_media", "living_room", "Upper Media Room", 6.0, 5.5, w, 8.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Bar Kitchenette", 6.0, 8.5, w, 12.0, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Gallery Lounge", 0, 12.0, 6.0, 15.5, 1, True))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 6.0, 12.0, w, 16.5, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 6.0, 16.5, 8.5, d, 1, False))
    rooms.append(make_room("r_L1_dress4", "dressing_room", "Upper Master Walk-in", 8.5, 16.5, w, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Rear Bedroom 5", 0, 15.5, 4.0, d, 1, True))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 4.0, 15.5, 6.0, 17.5, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Light Shaft OTS Void", 4.0, 17.5, 6.0, d, 1, False))

    ops.append(make_door("d_L1_01", 2.5, 5.0, ["r_L1_study", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 6.0, 3.5, ["r_L1_terrace", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 8.5, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 3.0, 7.5, ["r_L1_study", "r_L1_bridge"], 1.10, 1))
    ops.append(make_door("d_L1_05", 1.6, 9.5, ["r_L1_stairs", "r_L1_bridge"], 0.90, 1))
    ops.append(make_door("d_L1_06", 6.0, 7.5, ["r_L1_bridge", "r_L1_media"], 1.10, 1))
    ops.append(make_door("d_L1_07", 6.0, 10.0, ["r_L1_bridge", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_08", 3.0, 12.0, ["r_L1_bridge", "r_L1_lounge"], 1.20, 1))
    ops.append(make_door("d_L1_09", 6.0, 14.0, ["r_L1_lounge", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_10", 7.2, 16.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_11", 9.2, 16.5, ["r_L1_bed4", "r_L1_dress4"], 0.80, 1))
    ops.append(make_door("d_L1_12", 2.0, 15.5, ["r_L1_lounge", "r_L1_bed5"], 0.90, 1))
    ops.append(make_door("d_L1_13", 4.0, 16.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_14", 4.0, 18.5, ["r_L1_bed5", "r_L1_ots"], 0.80, 1))
    ops.append(make_window("w_L1_01", 7.0, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.0, d, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", 7.2, d, 1.80, 0.90, 1))
    meta = MetadataModel(plan_id="master_10_marla_v02", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "10_marla", "stair_type": "straight", "typology": "grand_central_atrium"})
    return assemble_plan(meta, env, rooms, ops)


def build_10m_v03() -> CanonicalFloorPlan:
    """v03: Linear Gallery & Side Courtyard - West gallery hallway, linear courtyard, straight steel stair."""
    w, d = 10.67, 19.81
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (2 Cars)", 2.0, 0, 7.5, 5.0, 0, False))
    rooms.append(make_room("r_L0_gallery", "corridor", "West Gallery Hallway", 0, 0, 2.0, 13.5, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Corner Lawn", 7.5, 0, 9.2, 1.8, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 9.2, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 7.5, 1.8, w, 5.0, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Linear Steel Staircase", 2.0, 5.0, 3.4, 10.5, 0, False, {"typology": "straight"}))
    rooms.append(make_room("r_L0_court", "outdoor", "Linear Side Courtyard", 3.4, 5.0, 5.5, 10.5, 0, False))
    rooms.append(make_room("r_L0_lounge", "living_room", "Courtyard-Facing Great Lounge", 5.5, 5.0, w, 10.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Designer Open Kitchen", 2.0, 10.5, 6.0, 13.5, 0, True))
    rooms.append(make_room("r_L0_dining", "dining_room", "Garden Dining Room", 6.0, 10.5, w, 12.3, 0, True))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Suite Foyer", 6.0, 12.3, w, 13.5, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 13.5, 5.5, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 5.5, 13.5, 7.5, 16.5, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Green Light Shaft", 5.5, 16.5, 7.5, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom Suite 2", 7.5, 13.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 2.0, 2.5, ["r_L0_porch", "r_L0_gallery"], 1.20, 0))
    ops.append(make_door("d_L0_02", 7.5, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 9.2, 1.8, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 7.5, 5.0, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_05", 2.0, 7.5, ["r_L0_gallery", "r_L0_stairs"], 0.90, 0))
    ops.append(make_door("d_L0_06", 5.5, 7.5, ["r_L0_court", "r_L0_lounge"], 1.40, 0))
    ops.append(make_door("d_L0_07", 2.0, 12.0, ["r_L0_gallery", "r_L0_kitchen"], 1.00, 0))
    ops.append(make_door("d_L0_08", 6.0, 11.5, ["r_L0_kitchen", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_09", 7.5, 10.5, ["r_L0_lounge", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_10", 1.0, 13.5, ["r_L0_gallery", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_11", 5.5, 14.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_12", 5.5, 17.5, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_12b", 8.0, 12.3, ["r_L0_dining", "r_L0_lobby"], 1.00, 0))
    ops.append(make_door("d_L0_13", 8.5, 13.5, ["r_L0_lobby", "r_L0_bed2"], 1.00, 0))
    ops.append(make_door("d_L0_14", 7.5, 15.0, ["r_L0_bed2", "r_L0_bath1"], 0.80, 0))
    ops.append(make_window("w_L0_01", 8.5, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.5, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", 8.5, d, 1.80, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Covered Balcony", 2.0, 0, 7.5, 5.0, 1, False))
    rooms.append(make_room("r_L1_gallery", "corridor", "Upper West Gallery Hallway", 0, 0, 2.0, 13.5, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 9.2, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Front Bedroom 3", 7.5, 1.8, w, 5.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Linear Steel Staircase Landing", 2.0, 5.0, 3.4, 10.5, 1, False, {"typology": "straight"}))
    rooms.append(make_room("r_L1_court_void", "outdoor", "Courtyard Void", 3.4, 5.0, 5.5, 10.5, 1, False))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Courtyard-Facing Lounge", 5.5, 5.0, w, 10.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Pantry Kitchenette", 2.0, 10.5, 6.0, 13.5, 1, True))
    rooms.append(make_room("r_L1_study", "study", "Quiet Library Study", 6.0, 10.5, w, 13.5, 1, True))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 13.5, 5.5, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 5.5, 13.5, 7.5, 16.5, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Green Light Shaft Void", 5.5, 16.5, 7.5, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Rear Bedroom Suite 5", 7.5, 13.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 2.0, 2.5, ["r_L1_gallery", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 7.5, 3.5, ["r_L1_terrace", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 9.2, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 7.5, 5.0, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_05", 2.0, 7.5, ["r_L1_gallery", "r_L1_stairs"], 0.90, 1))
    ops.append(make_door("d_L1_06", 5.5, 7.5, ["r_L1_lounge", "r_L1_court_void"], 1.20, 1))
    ops.append(make_door("d_L1_07", 2.0, 12.0, ["r_L1_gallery", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_08", 6.0, 12.0, ["r_L1_kitchenette", "r_L1_study"], 0.90, 1))
    ops.append(make_door("d_L1_09", 7.5, 10.5, ["r_L1_lounge", "r_L1_study"], 1.10, 1))
    ops.append(make_door("d_L1_10", 1.0, 13.5, ["r_L1_gallery", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_11", 5.5, 14.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_12", 5.5, 17.5, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_13", 8.5, 13.5, ["r_L1_study", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_14", 7.5, 15.0, ["r_L1_bed5", "r_L1_bath4"], 0.80, 1))
    ops.append(make_window("w_L1_01", 8.5, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.5, d, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", 8.5, d, 1.80, 0.90, 1))
    meta = MetadataModel(plan_id="master_10_marla_v03", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "10_marla", "stair_type": "straight", "typology": "linear_gallery_side_courtyard"})
    return assemble_plan(meta, env, rooms, ops)


def build_10m_v04() -> CanonicalFloorPlan:
    """v04: Curved Rotunda Staircase - Curved front staircase lobby, kitchen with side patio court, and dual rear suites with walk-in dressing buffers (Authentic CAD 10 Marla)."""
    w, d = 10.67, 19.81
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # =========================================================================
    # LEVEL 0 (GROUND FLOOR): Curved Stair Hall + Side Patio + Twin Dressing Suites
    # =========================================================================
    rooms.append(make_room("r_L0_porch", "garage", "Double Car Porch", 0, 0, 5.8, 5.5, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 5.8, 0, 8.5, 2.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 8.5, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Guest Drawing Room", 5.8, 2.0, w, 5.5, 0, True))

    rooms.append(make_room("r_L0_stairs", "corridor", "Curved Rotunda Staircase Hall", 0, 5.5, 3.6, 9.5, 0, False, {"typology": "curved"}))
    rooms.append(make_room("r_L0_foyer", "corridor", "Entrance Stair Lobby", 3.6, 5.5, 5.8, 9.5, 0, False))
    rooms.append(make_room("r_L0_dining", "dining_room", "Formal Dining Wing", 5.8, 5.5, w, 9.5, 0, True))

    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Family Kitchen", 0, 9.5, 3.6, 13.5, 0, True))
    rooms.append(make_room("r_L0_patio_side", "outdoor", "Kitchen Side Patio Garden Court", 0, 13.5, 3.6, 15.5, 0, False))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Family TV Lounge", 3.6, 9.5, w, 14.5, 0, True))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Distribution Lobby", 3.6, 14.5, w, 15.5, 0, False))

    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 15.5, 5.2, 18.0, 0, True))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Garden Light Shaft OTS", 5.2, 15.5, 6.8, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Ground Bedroom Suite 2", 6.8, 15.5, w, 18.0, 0, True))

    rooms.append(make_room("r_L0_dress1", "closet", "Master Walk-in Dressing 1", 0, 18.0, 2.6, d, 0, False))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 2.6, 18.0, 5.2, d, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 6.8, 18.0, 8.8, d, 0, False))
    rooms.append(make_room("r_L0_dress2", "closet", "Bed 2 Walk-in Dressing", 8.8, 18.0, w, d, 0, False))

    # Doors L0
    ops.append(make_door("d_L0_01", 4.7, 5.5, ["r_L0_porch", "r_L0_foyer"], 1.30, 0))
    ops.append(make_door("d_L0_02", 5.8, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 9.5, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 7.5, 5.5, ["r_L0_drawing", "r_L0_dining"], 1.10, 0))
    ops.append(make_door("d_L0_05", 3.6, 7.5, ["r_L0_foyer", "r_L0_stairs"], 1.20, 0))
    ops.append(make_door("d_L0_06", 5.8, 7.5, ["r_L0_foyer", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_07", 4.7, 9.5, ["r_L0_foyer", "r_L0_lounge"], 1.30, 0))
    ops.append(make_door("d_L0_08", 8.0, 9.5, ["r_L0_dining", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_09", 3.6, 11.5, ["r_L0_lounge", "r_L0_kitchen"], 1.00, 0))
    ops.append(make_door("d_L0_10", 1.8, 13.5, ["r_L0_kitchen", "r_L0_patio_side"], 0.90, 0))
    ops.append(make_door("d_L0_11", 5.3, 14.5, ["r_L0_lounge", "r_L0_lobby"], 1.10, 0))
    ops.append(make_door("d_L0_12", 4.4, 15.5, ["r_L0_lobby", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_13", 8.5, 15.5, ["r_L0_lobby", "r_L0_bed2"], 1.00, 0))
    ops.append(make_door("d_L0_14", 1.3, 18.0, ["r_L0_bed1", "r_L0_dress1"], 0.85, 0))
    ops.append(make_door("d_L0_15", 2.6, 18.9, ["r_L0_dress1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_16", 5.2, 16.5, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_17", 9.7, 18.0, ["r_L0_bed2", "r_L0_dress2"], 0.85, 0))
    ops.append(make_door("d_L0_18", 8.8, 18.9, ["r_L0_dress2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_19", 6.8, 16.5, ["r_L0_bed2", "r_L0_ots"], 0.80, 0))

    # Windows L0
    ops.append(make_window("w_L0_01", 7.5, 2.0, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.6, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", 8.8, d, 1.80, 0.90, 0))

    # =========================================================================
    # LEVEL 1 (FIRST FLOOR): Upper Curved Stair Landing + Upper Dressing Suites
    # =========================================================================
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Curved Sun Terrace", 0, 0, 5.8, 5.5, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 8.5, 0, w, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Front Suite 3", 5.8, 2.0, w, 5.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Curved Staircase Landing", 0, 5.5, 3.6, 9.5, 1, False, {"typology": "curved"}))
    rooms.append(make_room("r_L1_foyer", "corridor", "Upper Rotunda Landing", 3.6, 5.5, 5.8, 9.5, 1, False))
    rooms.append(make_room("r_L1_media", "living_room", "Upper Media Hall", 5.8, 5.5, w, 9.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette & Bar", 0, 9.5, 3.6, 13.5, 1, True))
    rooms.append(make_room("r_L1_patio_void", "outdoor", "Patio Open Void", 0, 13.5, 3.6, 15.5, 1, False))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Lounge", 3.6, 9.5, w, 14.5, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Distribution Lobby", 3.6, 14.5, w, 15.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 15.5, 5.2, 18.0, 1, True))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Garden Light Shaft Void", 5.2, 15.5, 6.8, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Bedroom Suite 5", 6.8, 15.5, w, 18.0, 1, True))
    rooms.append(make_room("r_L1_dress4", "closet", "Upper Master Dressing 4", 0, 18.0, 2.6, d, 1, False))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 2.6, 18.0, 5.2, d, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 6.8, 18.0, 8.8, d, 1, False))
    rooms.append(make_room("r_L1_dress5", "closet", "Bed 5 Walk-in Dressing", 8.8, 18.0, w, d, 1, False))

    # Doors L1
    ops.append(make_door("d_L1_01", 4.7, 5.5, ["r_L1_foyer", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 5.8, 3.5, ["r_L1_terrace", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 9.5, 2.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 3.6, 7.5, ["r_L1_foyer", "r_L1_stairs"], 1.20, 1))
    ops.append(make_door("d_L1_05", 5.8, 7.5, ["r_L1_foyer", "r_L1_media"], 1.10, 1))
    ops.append(make_door("d_L1_06", 4.7, 9.5, ["r_L1_foyer", "r_L1_lounge"], 1.20, 1))
    ops.append(make_door("d_L1_07", 8.0, 9.5, ["r_L1_media", "r_L1_lounge"], 1.10, 1))
    ops.append(make_door("d_L1_08", 3.6, 11.5, ["r_L1_lounge", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_09", 5.3, 14.5, ["r_L1_lounge", "r_L1_lobby"], 1.10, 1))
    ops.append(make_door("d_L1_10", 4.4, 15.5, ["r_L1_lobby", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_11", 8.5, 15.5, ["r_L1_lobby", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_12", 1.3, 18.0, ["r_L1_bed4", "r_L1_dress4"], 0.85, 1))
    ops.append(make_door("d_L1_13", 2.6, 18.9, ["r_L1_dress4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_14", 9.7, 18.0, ["r_L1_bed5", "r_L1_dress5"], 0.85, 1))
    ops.append(make_door("d_L1_15", 8.8, 18.9, ["r_L1_dress5", "r_L1_bath5"], 0.80, 1))

    # Windows L1
    ops.append(make_window("w_L1_01", 7.5, 2.0, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.6, d, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", 8.8, d, 1.80, 0.90, 1))

    meta = MetadataModel(
        plan_id="master_10_marla_v04",
        source_type="synthetic_generated",
        floor_count=2,
        levels=[0, 1],
        provenance={"scale": "10_marla", "stair_type": "curved", "typology": "curved_rotunda_staircase"}
    )
    return assemble_plan(meta, env, rooms, ops)


def build_10m_v05() -> CanonicalFloorPlan:
    """v05: Bifurcated Grand Foyer - Split-flight grand imperial stair branching to master suites."""
    w, d = 10.67, 19.81
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Imperial Car Porch", 2.5, 0, 8.2, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn_w", "outdoor", "West Lawn", 0, 0, 2.5, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn_e", "outdoor", "East Lawn", 8.2, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Foyer Powder Room", 8.2, 2.0, w, 3.5, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Guest Drawing", 8.2, 3.5, w, 7.5, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Bifurcated Grand Stairs", 3.8, 5.0, 7.0, 8.5, 0, False, {"typology": "bifurcated"}))
    rooms.append(make_room("r_L0_foyer", "corridor", "Central Grand Foyer", 2.5, 5.0, 3.8, 8.5, 0, False))
    rooms.append(make_room("r_L0_study", "study", "Private Ground Study", 0, 5.0, 2.5, 8.5, 0, True))
    rooms.append(make_room("r_L0_lounge", "living_room", "Palatial Family Living Hall", 0, 8.5, 7.5, 14.0, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Chef's Kitchen & Pantry", 7.5, 8.5, w, 14.0, 0, True))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 14.0, 5.2, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 5.2, 14.0, 6.8, 16.8, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Yard OTS Light Shaft", 5.2, 16.8, 6.8, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Secondary Bedroom Suite 2", 6.8, 14.0, w, d, 0, True))

    ops.append(make_door("d_L0_01", 3.2, 5.0, ["r_L0_porch", "r_L0_foyer"], 1.30, 0))
    ops.append(make_door("d_L0_02", 8.2, 4.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 9.0, 3.5, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 2.5, 6.5, ["r_L0_foyer", "r_L0_study"], 0.90, 0))
    ops.append(make_door("d_L0_05", 3.8, 6.5, ["r_L0_foyer", "r_L0_stairs"], 1.20, 0))
    ops.append(make_door("d_L0_06", 3.2, 8.5, ["r_L0_foyer", "r_L0_lounge"], 1.30, 0))
    ops.append(make_door("d_L0_07", 7.5, 10.5, ["r_L0_lounge", "r_L0_kitchen"], 1.10, 0))
    ops.append(make_door("d_L0_08", 2.6, 14.0, ["r_L0_lounge", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_09", 5.2, 15.0, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_10", 5.2, 17.5, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_11", 6.8, 14.0, ["r_L0_lounge", "r_L0_bed2"], 1.00, 0))
    ops.append(make_door("d_L0_12", 6.8, 15.0, ["r_L0_bed2", "r_L0_bath1"], 0.80, 0))
    ops.append(make_window("w_L0_01", w, 5.5, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.6, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", 8.5, d, 1.80, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Imperial Front Balcony", 2.5, 0, 8.2, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 8.2, 2.0, w, 3.5, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Front Suite 3", 8.2, 3.5, w, 7.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Bifurcated Grand Stairs Landing", 3.8, 5.0, 7.0, 8.5, 1, False, {"typology": "bifurcated"}))
    rooms.append(make_room("r_L1_foyer", "corridor", "Upper Central Foyer", 2.5, 5.0, 3.8, 8.5, 1, False))
    rooms.append(make_room("r_L1_gym", "study", "Private Fitness Studio", 0, 5.0, 2.5, 8.5, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Living Hall", 0, 8.5, 7.5, 14.0, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 7.5, 8.5, w, 14.0, 1, True))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 14.0, 5.2, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 5.2, 14.0, 6.8, 16.8, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Yard OTS Light Shaft Void", 5.2, 16.8, 6.8, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Bedroom Suite 5", 6.8, 14.0, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.2, 5.0, ["r_L1_foyer", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 8.2, 4.5, ["r_L1_terrace", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 9.0, 3.5, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 2.5, 6.5, ["r_L1_foyer", "r_L1_gym"], 0.90, 1))
    ops.append(make_door("d_L1_05", 3.8, 6.5, ["r_L1_foyer", "r_L1_stairs"], 1.20, 1))
    ops.append(make_door("d_L1_06", 3.2, 8.5, ["r_L1_foyer", "r_L1_lounge"], 1.30, 1))
    ops.append(make_door("d_L1_07", 7.5, 10.5, ["r_L1_lounge", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_08", 2.6, 14.0, ["r_L1_lounge", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_09", 5.2, 15.0, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_10", 5.2, 17.5, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_11", 6.8, 14.0, ["r_L1_lounge", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_12", 6.8, 15.0, ["r_L1_bed5", "r_L1_bath4"], 0.80, 1))
    ops.append(make_window("w_L1_01", w, 5.5, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.6, d, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", 8.5, d, 1.80, 0.90, 1))
    meta = MetadataModel(plan_id="master_10_marla_v05", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "10_marla", "stair_type": "bifurcated", "typology": "bifurcated_grand_foyer"})
    return assemble_plan(meta, env, rooms, ops)


def build_10m_v06() -> CanonicalFloorPlan:
    """v06: Integrated Patio Plunge Pool - Sunken patio pool court between lounge and master bed."""
    w, d = 10.67, 19.81
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (2 Cars)", 0, 0, 5.5, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Lawn", 5.5, 0, 8.5, 1.8, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 8.5, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 5.5, 1.8, w, 5.0, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Central Dogleg Staircase", 0, 5.0, 2.6, 10.5, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Pool-Facing Living Hall", 2.6, 5.0, w, 10.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Designer Island Kitchen", 0, 10.5, 3.5, 14.5, 0, True))
    rooms.append(make_room("r_L0_pool_patio", "outdoor", "Sunken Patio Plunge Pool Court", 3.5, 10.5, 7.0, 14.5, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 7.0, 10.5, w, 15.5, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 7.0, 15.5, w, 17.8, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Light Shaft OTS", 7.0, 17.8, w, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Garden Bedroom Suite 2", 0, 14.5, 5.0, d, 0, True))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 5.0, 14.5, 7.0, d, 0, False))

    ops.append(make_door("d_L0_01", 3.0, 5.0, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.5, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 8.5, 1.8, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 6.8, 5.0, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_05", 2.6, 7.0, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_06", 1.8, 10.5, ["r_L0_stairs", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_07", 5.2, 10.5, ["r_L0_lounge", "r_L0_pool_patio"], 1.40, 0))
    ops.append(make_door("d_L0_08", 7.0, 12.0, ["r_L0_bed1", "r_L0_pool_patio"], 1.20, 0))
    ops.append(make_door("d_L0_09", 8.5, 10.5, ["r_L0_lounge", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_10", 8.5, 15.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_11", 8.5, 17.8, ["r_L0_bath1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_12", 4.2, 14.5, ["r_L0_pool_patio", "r_L0_bed2"], 1.00, 0))
    ops.append(make_door("d_L0_13", 5.0, 16.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_window("w_L0_01", 7.0, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.5, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", 8.5, d, 1.80, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Sun Terrace", 0, 0, 5.5, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 8.5, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Front Suite 3", 5.5, 1.8, w, 5.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Central Dogleg Staircase Landing", 0, 5.0, 2.6, 10.5, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Lounge", 2.6, 5.0, w, 10.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 0, 10.5, 3.5, 14.5, 1, True))
    rooms.append(make_room("r_L1_patio_void", "outdoor", "Pool Patio Open Void", 3.5, 10.5, 7.0, 14.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 7.0, 10.5, w, 15.5, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 7.0, 15.5, w, 17.8, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Light Shaft OTS Void", 7.0, 17.8, w, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Bedroom Suite 5", 0, 14.5, 5.0, d, 1, True))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 5.0, 14.5, 7.0, d, 1, False))

    ops.append(make_door("d_L1_01", 3.0, 5.0, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 5.5, 3.5, ["r_L1_terrace", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 8.5, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 6.8, 5.0, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_05", 2.6, 7.0, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_06", 1.8, 10.5, ["r_L1_stairs", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_07", 5.2, 10.5, ["r_L1_lounge", "r_L1_patio_void"], 1.20, 1))
    ops.append(make_door("d_L1_08", 8.5, 10.5, ["r_L1_lounge", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_09", 8.5, 15.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_10", 8.5, 17.8, ["r_L1_bath4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_11", 4.2, 14.5, ["r_L1_patio_void", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_12", 5.0, 16.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_window("w_L1_01", 7.0, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.5, d, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", 8.5, d, 1.80, 0.90, 1))
    meta = MetadataModel(plan_id="master_10_marla_v06", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "10_marla", "stair_type": "dogleg", "typology": "integrated_patio_plunge_pool"})
    return assemble_plan(meta, env, rooms, ops)


def build_10m_v07() -> CanonicalFloorPlan:
    """v07: Multi-Family Dual Kitchenette - Full ground kitchen + upper kitchenette & bar pantry."""
    w, d = 10.67, 19.81
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Ground Porch (2 Cars)", 4.8, 0, w, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Garden Strip", 0, 0, 2.5, 2.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 2.5, 0, 4.8, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 0, 2.0, 4.8, 5.5, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Side Independent Dogleg Stair", 8.27, 5.0, w, 9.5, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Ground Lounge", 0, 5.5, 8.27, 12.0, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Full Commercial Ground Kitchen", 4.8, 12.0, w, 15.5, 0, True))
    rooms.append(make_room("r_L0_dining", "dining_room", "Family Dining Room", 0, 12.0, 4.8, 15.5, 0, True))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Distribution Lobby", 4.8, 15.5, 6.2, 17.5, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 15.5, 4.8, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 4.8, 17.5, 6.2, d, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Yard OTS Light Shaft", 6.2, 17.5, 7.5, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom Suite 2", 6.2, 15.5, w, 17.5, 0, True))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 7.5, 17.5, w, d, 0, False))

    ops.append(make_door("d_L0_01", 6.0, 5.0, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 4.8, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 3.5, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 2.5, 5.5, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_05", 8.27, 7.0, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_06", 2.5, 12.0, ["r_L0_lounge", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_07", 6.0, 12.0, ["r_L0_lounge", "r_L0_kitchen"], 1.10, 0))
    ops.append(make_door("d_L0_08", 4.8, 14.0, ["r_L0_dining", "r_L0_lobby"], 1.00, 0))
    ops.append(make_door("d_L0_09", 4.8, 16.5, ["r_L0_lobby", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_10", 4.8, 18.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_11", 6.2, 16.5, ["r_L0_lobby", "r_L0_bed2"], 0.90, 0))
    ops.append(make_door("d_L0_12", 7.5, 17.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_13", 6.2, 17.5, ["r_L0_bed2", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 2.0, 2.0, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.0, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", 8.5, d, 1.80, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Upper Terrace", 4.8, 0, w, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 2.5, 0, 4.8, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom Suite 3 (Front)", 0, 2.0, 4.8, 5.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Side Independent Stair Landing", 8.27, 5.0, w, 9.5, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Lounge", 0, 5.5, 8.27, 12.0, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette & Bar Pantry", 4.8, 12.0, w, 15.5, 1, True))
    rooms.append(make_room("r_L1_media", "living_room", "Upper Media Lounge", 0, 12.0, 4.8, 15.5, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Distribution Lobby", 4.8, 15.5, 6.2, 17.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 15.5, 4.8, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 4.8, 17.5, 6.2, d, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Yard OTS Void", 6.2, 17.5, 7.5, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Bedroom Suite 5", 6.2, 15.5, w, 17.5, 1, True))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 7.5, 17.5, w, d, 1, False))

    ops.append(make_door("d_L1_01", 6.0, 5.0, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 4.8, 3.5, ["r_L1_terrace", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 3.5, 2.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 2.5, 5.5, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_05", 8.27, 7.0, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_06", 2.5, 12.0, ["r_L1_lounge", "r_L1_media"], 1.10, 1))
    ops.append(make_door("d_L1_07", 6.0, 12.0, ["r_L1_lounge", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_08", 4.8, 14.0, ["r_L1_media", "r_L1_lobby"], 1.00, 1))
    ops.append(make_door("d_L1_09", 4.8, 16.5, ["r_L1_lobby", "r_L1_bed4"], 0.90, 1))
    ops.append(make_door("d_L1_10", 4.8, 18.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_11", 6.2, 16.5, ["r_L1_lobby", "r_L1_bed5"], 0.90, 1))
    ops.append(make_door("d_L1_12", 7.5, 17.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_13", 6.2, 17.5, ["r_L1_bed5", "r_L1_ots"], 0.80, 1))
    ops.append(make_window("w_L1_01", 2.0, 2.0, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.0, d, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", 8.5, d, 1.80, 0.90, 1))
    meta = MetadataModel(plan_id="master_10_marla_v07", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "10_marla", "stair_type": "dogleg", "typology": "multi_family_dual_kitchenette"})
    return assemble_plan(meta, env, rooms, ops)


def build_10m_v08() -> CanonicalFloorPlan:
    """v08: Rear Master Pavilion - Master suite spanning full 35-foot rear width with dual walk-ins."""
    w, d = 10.67, 19.81
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Front Garage (2 Cars)", 0, 0, 5.5, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Garden Lawn", 5.5, 0, 8.5, 2.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 8.5, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Guest Drawing", 5.5, 2.0, w, 5.0, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Floating Open Staircase", 0, 5.0, 1.4, 10.5, 0, False, {"typology": "floating"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Pavilion Living Hall", 1.4, 5.0, 7.5, 10.5, 0, True))
    rooms.append(make_room("r_L0_dining", "dining_room", "Formal Dining Room", 7.5, 5.0, w, 8.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Show Kitchen", 7.5, 8.5, w, 10.5, 0, True))
    rooms.append(make_room("r_L0_dirty_kitchen", "kitchen", "Enclosed Scullery Kitchen", 7.5, 10.5, w, 12.0, 0, True, {"is_dirty_kitchen": True}))
    rooms.append(make_room("r_L0_lobby", "corridor", "Master Suite Vestibule", 0, 10.5, 7.5, 12.0, 0, False))
    # Full 35-foot rear master suite:
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 12.0, w, 16.5, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master 5-Fixture Luxury Bath", 0, 16.5, 4.5, d, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Private Master Garden OTS", 4.5, 16.5, 6.5, d, 0, False))
    rooms.append(make_room("r_L0_dress1", "dressing_room", "Dual Walk-in Dressing Suite", 6.5, 16.5, w, d, 0, False))

    ops.append(make_door("d_L0_01", 3.0, 5.0, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.5, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 8.5, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 8.5, 5.0, ["r_L0_drawing", "r_L0_dining"], 1.10, 0))
    ops.append(make_door("d_L0_05", 1.4, 7.5, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_06", 7.5, 7.0, ["r_L0_lounge", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_07", 7.5, 9.5, ["r_L0_lounge", "r_L0_kitchen"], 1.00, 0))
    ops.append(make_door("d_L0_07_dk", 9.0, 10.5, ["r_L0_kitchen", "r_L0_dirty_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_08", 4.0, 10.5, ["r_L0_lounge", "r_L0_lobby"], 1.20, 0))
    ops.append(make_door("d_L0_09", 4.0, 12.0, ["r_L0_lobby", "r_L0_bed1"], 1.20, 0))
    ops.append(make_door("d_L0_10", 2.2, 16.5, ["r_L0_bed1", "r_L0_bath1"], 0.90, 0))
    ops.append(make_door("d_L0_11", 5.5, 16.5, ["r_L0_bed1", "r_L0_ots"], 0.90, 0))
    ops.append(make_door("d_L0_12", 8.5, 16.5, ["r_L0_bed1", "r_L0_dress1"], 0.90, 0))
    ops.append(make_window("w_L0_01", 7.0, 2.0, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.2, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", 8.5, d, 1.80, 0.90, 0))
    # L1: 3 Bedrooms on Upper Level (Total 4 bedrooms across house)
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Open Terrace", 0, 0, 5.5, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 8.5, 0, w, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom Suite 3 (Front)", 5.5, 2.0, w, 5.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Floating Open Staircase Landing", 0, 5.0, 1.4, 10.5, 1, False, {"typology": "floating"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Living Hall", 1.4, 5.0, 7.5, 10.5, 1, True))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Executive Suite 5", 7.5, 5.0, w, 8.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 7.5, 8.5, w, 12.0, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Suite Vestibule", 0, 10.5, 7.5, 12.0, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 12.0, w, 16.5, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master 5-Fixture Luxury Bath 4", 0, 16.5, 4.5, d, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Private Master Garden OTS Void", 4.5, 16.5, 6.5, d, 1, False))
    rooms.append(make_room("r_L1_dress4", "dressing_room", "Upper Walk-in Dressing Suite", 6.5, 16.5, w, d, 1, False))

    ops.append(make_door("d_L1_01", 3.0, 5.0, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 5.5, 3.5, ["r_L1_terrace", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 8.5, 2.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 7.5, 7.0, ["r_L1_lounge", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_05", 1.4, 7.5, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_06", 7.5, 9.5, ["r_L1_lounge", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_07", 4.0, 10.5, ["r_L1_lounge", "r_L1_lobby"], 1.10, 1))
    ops.append(make_door("d_L1_08", 4.0, 12.0, ["r_L1_lobby", "r_L1_bed4"], 1.20, 1))
    ops.append(make_door("d_L1_09", 2.2, 16.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_10", 5.5, 16.5, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_11", 8.5, 16.5, ["r_L1_bed4", "r_L1_dress4"], 0.80, 1))
    ops.append(make_window("w_L1_01", 7.0, 2.0, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.2, d, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", 8.5, d, 1.80, 0.90, 1))
    meta = MetadataModel(plan_id="master_10_marla_v08", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "10_marla", "stair_type": "floating", "typology": "rear_master_pavilion"})
    return assemble_plan(meta, env, rooms, ops)


def build_10m_v09() -> CanonicalFloorPlan:
    """v09: Corner Splayed Entrance - 45-degree corner entrance with dual frontage lawns."""
    w, d = 10.67, 19.81
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Corner Wrap-Around Porch", 3.0, 0, 8.5, 4.5, 0, False))
    rooms.append(make_room("r_L0_lawn_w", "outdoor", "West Front Lawn", 0, 0, 3.0, 4.5, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Corner Guest Powder", 8.5, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Corner Drawing Room", 8.5, 2.0, w, 5.5, 0, True))
    rooms.append(make_room("r_L0_foyer", "corridor", "Splayed Corner Entrance Vestibule", 0, 4.5, 3.0, 9.0, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Corner Dogleg Staircase", 0, 9.0, 2.6, 13.5, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Family Living Hall", 3.0, 4.5, 7.5, 13.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Designer Family Kitchen", 7.5, 5.5, w, 11.0, 0, True))
    rooms.append(make_room("r_L0_dining", "dining_room", "Dining Room", 7.5, 11.0, w, 14.5, 0, True))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Suite Lobby", 2.6, 13.5, 7.5, 14.5, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 14.5, 5.2, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 5.2, 14.5, 7.0, 17.0, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Light Shaft OTS", 5.2, 17.0, 7.0, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom Suite 2", 7.0, 14.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 3.0, 3.5, ["r_L0_porch", "r_L0_foyer"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.5, 4.5, ["r_L0_porch", "r_L0_lounge"], 1.30, 0))
    ops.append(make_door("d_L0_03", 8.5, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_04", 9.2, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_05", 8.5, 5.0, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_06", 3.0, 7.0, ["r_L0_foyer", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_07", 2.6, 11.0, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_08", 7.5, 8.5, ["r_L0_lounge", "r_L0_kitchen"], 1.10, 0))
    ops.append(make_door("d_L0_09", 7.5, 12.5, ["r_L0_lounge", "r_L0_dining"], 1.10, 0))
    ops.append(make_door("d_L0_10", 5.5, 13.5, ["r_L0_lounge", "r_L0_lobby"], 1.20, 0))
    ops.append(make_door("d_L0_11", 2.6, 14.5, ["r_L0_lobby", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_12", 5.2, 15.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_13", 5.2, 18.0, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_14", 7.0, 14.5, ["r_L0_lobby", "r_L0_bed2"], 1.00, 0))
    ops.append(make_door("d_L0_15", 7.0, 15.5, ["r_L0_bed2", "r_L0_bath1"], 0.80, 0))
    ops.append(make_window("w_L0_01", w, 3.5, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.5, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", 8.5, d, 1.80, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Corner Wrap-Around Balcony", 3.0, 0, 8.5, 4.5, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 8.5, 0, w, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Corner Bedroom 3", 8.5, 2.0, w, 5.5, 1, True))
    rooms.append(make_room("r_L1_foyer", "corridor", "Upper Corner Vestibule", 0, 4.5, 3.0, 9.0, 1, False))
    rooms.append(make_room("r_L1_stairs", "corridor", "Corner Dogleg Staircase Landing", 0, 9.0, 2.6, 13.5, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Living Hall", 3.0, 4.5, 7.5, 13.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 7.5, 5.5, w, 11.0, 1, True))
    rooms.append(make_room("r_L1_study", "study", "Upper Study Room", 7.5, 11.0, w, 14.5, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Suite Lobby", 2.6, 13.5, 7.5, 14.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 14.5, 5.2, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 5.2, 14.5, 7.0, 17.0, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Light Shaft OTS Void", 5.2, 17.0, 7.0, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Rear Bedroom Suite 5", 7.0, 14.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.0, 3.5, ["r_L1_foyer", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 5.5, 4.5, ["r_L1_lounge", "r_L1_terrace"], 1.20, 1))
    ops.append(make_door("d_L1_03", 8.5, 3.5, ["r_L1_terrace", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_04", 9.2, 2.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_05", 8.5, 5.0, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_06", 3.0, 7.0, ["r_L1_foyer", "r_L1_lounge"], 1.10, 1))
    ops.append(make_door("d_L1_07", 2.6, 11.0, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_08", 7.5, 8.5, ["r_L1_lounge", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_09", 7.5, 12.5, ["r_L1_lounge", "r_L1_study"], 1.00, 1))
    ops.append(make_door("d_L1_10", 5.5, 13.5, ["r_L1_lounge", "r_L1_lobby"], 1.10, 1))
    ops.append(make_door("d_L1_11", 2.6, 14.5, ["r_L1_lobby", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_12", 5.2, 15.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_13", 5.2, 18.0, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_14", 7.0, 14.5, ["r_L1_lobby", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_15", 7.0, 15.5, ["r_L1_bed5", "r_L1_bath4"], 0.80, 1))
    ops.append(make_window("w_L1_01", w, 3.5, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.5, d, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", 8.5, d, 1.80, 0.90, 1))
    meta = MetadataModel(plan_id="master_10_marla_v09", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "10_marla", "stair_type": "dogleg", "typology": "corner_splayed_entrance"})
    return assemble_plan(meta, env, rooms, ops)


def build_10m_v10() -> CanonicalFloorPlan:
    """v10: Concealed Core Minimalist - Flush cabinetry, open floating stair with glass balustrade."""
    w, d = 10.67, 19.81
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Minimalist Garage (2 Cars)", 0, 0, 5.0, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Minimalist Lawn", 5.0, 0, 7.5, 1.8, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Concealed Powder Room", 7.5, 0, 9.2, 1.8, 0, False))
    rooms.append(make_room("r_L0_store", "dressing_room", "Entrance Mudroom Store", 9.2, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Minimalist Living", 5.0, 1.8, w, 5.0, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Open Floating Glass Stair", 0, 5.0, 1.2, 10.5, 0, False, {"typology": "floating"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Open Concept Great Room", 1.2, 5.0, 7.5, 10.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Concealed Minimalist Kitchen", 7.5, 5.0, w, 12.0, 0, True))
    rooms.append(make_room("r_L0_pantry", "kitchen", "Concealed Dirty Scullery", 7.5, 12.0, w, 14.5, 0, True))
    rooms.append(make_room("r_L0_corridor", "corridor", "Minimalist Rear Corridor", 0, 10.5, 7.5, 12.0, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 12.0, 5.2, 17.5, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 0, 17.5, 5.2, d, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Yard OTS Light Court", 5.2, 14.5, 7.5, 17.5, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 5.2, 17.5, 7.5, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom Suite 2", 7.5, 14.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 2.5, 5.0, ["r_L0_porch", "r_L0_lounge"], 1.30, 0))
    ops.append(make_door("d_L0_02", 5.0, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 8.2, 1.8, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 6.2, 5.0, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_05", 1.2, 7.5, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_06", 7.5, 8.5, ["r_L0_lounge", "r_L0_kitchen"], 1.20, 0))
    ops.append(make_door("d_L0_07", 8.5, 12.0, ["r_L0_kitchen", "r_L0_pantry"], 0.90, 0))
    ops.append(make_door("d_L0_08", 4.0, 10.5, ["r_L0_lounge", "r_L0_corridor"], 1.20, 0))
    ops.append(make_door("d_L0_09", 2.5, 12.0, ["r_L0_corridor", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_10", 2.5, 17.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_11", 5.2, 16.0, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_12", 7.5, 13.0, ["r_L0_corridor", "r_L0_bed2"], 1.00, 0))
    ops.append(make_door("d_L0_13", 7.5, 18.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_window("w_L0_01", 6.2, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.5, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", 9.0, d, 1.80, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Open Terrace", 0, 0, 5.0, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 7.5, 0, 9.2, 1.8, 1, False))
    rooms.append(make_room("r_L1_store", "dressing_room", "Upper Store", 9.2, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom Suite 3 (Front)", 5.0, 1.8, w, 5.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Open Floating Glass Stair Landing", 0, 5.0, 1.2, 10.5, 1, False, {"typology": "floating"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Minimalist Lounge", 1.2, 5.0, 7.5, 10.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 7.5, 5.0, w, 12.0, 1, True))
    rooms.append(make_room("r_L1_study", "study", "Quiet Library Nook", 7.5, 12.0, w, 14.5, 1, True))
    rooms.append(make_room("r_L1_corridor", "corridor", "Upper Rear Corridor", 0, 10.5, 7.5, 12.0, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 12.0, 5.2, 17.5, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 0, 17.5, 5.2, d, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Yard OTS Light Court Void", 5.2, 14.5, 7.5, 17.5, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 5.2, 17.5, 7.5, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Bedroom Suite 5", 7.5, 14.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 2.5, 5.0, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 6.2, 5.0, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_03", 8.2, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 1.2, 7.5, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_05", 7.5, 8.5, ["r_L1_lounge", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_06", 8.5, 12.0, ["r_L1_kitchenette", "r_L1_study"], 0.90, 1))
    ops.append(make_door("d_L1_07", 4.0, 10.5, ["r_L1_lounge", "r_L1_corridor"], 1.10, 1))
    ops.append(make_door("d_L1_08", 2.5, 12.0, ["r_L1_corridor", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_09", 2.5, 17.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_10", 5.2, 16.0, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_11", 7.5, 13.0, ["r_L1_corridor", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_12", 7.5, 18.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_window("w_L1_01", 6.2, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.5, d, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", 9.0, d, 1.80, 0.90, 1))
    meta = MetadataModel(plan_id="master_10_marla_v10", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "10_marla", "stair_type": "floating", "typology": "concealed_core_minimalist"})
    return assemble_plan(meta, env, rooms, ops)


ARCHETYPES_10_MARLA = [
    build_10m_v01, build_10m_v02, build_10m_v03, build_10m_v04, build_10m_v05,
    build_10m_v06, build_10m_v07, build_10m_v08, build_10m_v09, build_10m_v10
]
