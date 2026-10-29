
"""
Canonical Master Archetypes for 7 Marla (30'-0" x 55'-0" / 9.14m x 16.76m).
10 Distinct Archetypes v01 to v10.
"""

from typing import List
from dataset.schema.canonical import CanonicalFloorPlan, MetadataModel
from dataset.build_master_catalog import (
    make_room,
    make_door,
    make_window,
    assemble_plan
)


def build_7m_v01() -> CanonicalFloorPlan:
    """v01: Classic Dual-Bed Rear - Front porch + drawing, central lounge, side kitchen, dual rear bedrooms with central OTS and Feature Round Stairs."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    rooms.append(make_room("r_L0_porch", "garage", "Modern Car Porch (2 Cars)", 0, 0, 5.0, 5.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 7.0, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 5.0, 1.8, w, 5.0, 0, True))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 5.0, 0, 7.0, 1.8, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Feature Round Staircase", 0, 5.0, 2.6, 9.0, 0, False, {"typology": "curved"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central TV Lounge", 2.6, 5.0, w, 11.2, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Modern Working Kitchen", 0, 9.0, 2.6, 12.6, 0, True))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Bed Lobby", 2.6, 11.2, 7.8, 12.6, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 12.6, 3.20, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Attached Bath 1", 3.20, 12.6, 4.57, 14.70, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 4.57, 12.6, 5.94, 14.70, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Central Light Shaft OTS", 3.20, 14.70, 5.94, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom Suite 2", 5.94, 12.6, w, d, 0, True))

    ops.append(make_door("d_L0_01", 3.0, 5.0, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.0, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 6.5, 5.0, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_04", 7.5, 1.8, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_05", 2.6, 7.0, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_06", 2.6, 9.8, ["r_L0_kitchen", "r_L0_lounge"], 0.90, 0))
    # Open archway into rear bed lobby (no swinging door leaf in modern architecture)
    ops.append(make_door("d_L0_07", 4.57, 11.2, ["r_L0_lounge", "r_L0_lobby"], 1.20, 0))
    # Independent bedroom doors on horizontal lobby wall
    ops.append(make_door("d_L0_08", 2.90, 12.6, ["r_L0_lobby", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_11", 6.80, 12.6, ["r_L0_lobby", "r_L0_bed2"], 0.90, 0))
    # Private ensuite bathroom doors inside bedrooms
    ops.append(make_door("d_L0_09", 3.20, 13.6, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_12", 5.94, 13.6, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_10", 3.20, 15.6, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_13", 5.94, 15.6, ["r_L0_bed2", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 6.0, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 1.6, d, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_03", 7.5, d, 1.50, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Open Terrace", 0, 0, 5.0, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Attached Bath 3", 7.0, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom 3 (Front Suite)", 5.0, 1.8, w, 5.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Feature Round Staircase Landing", 0, 5.0, 2.6, 9.0, 1, False, {"typology": "curved"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family TV Lounge", 2.6, 5.0, w, 11.2, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 0, 9.0, 2.6, 11.2, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Bed Lobby", 2.6, 11.2, 7.8, 12.6, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Bedroom 4 (Rear Left Suite)", 0, 12.6, 3.20, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Attached Bath 4", 3.20, 12.6, 4.57, 14.70, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 4.57, 12.6, 5.94, 14.70, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Central Light Shaft OTS Void", 3.20, 14.70, 5.94, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Bedroom 5 (Rear Right Suite)", 5.94, 12.6, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.0, 5.0, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 6.5, 5.0, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_03", 8.0, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 2.6, 7.0, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_05", 2.6, 9.8, ["r_L1_kitchenette", "r_L1_lounge"], 0.90, 1))
    # Open archway into upper bed lobby
    ops.append(make_door("d_L1_06", 4.57, 11.2, ["r_L1_lounge", "r_L1_lobby"], 1.20, 1))
    ops.append(make_door("d_L1_07", 2.90, 12.6, ["r_L1_lobby", "r_L1_bed4"], 0.90, 1))
    ops.append(make_door("d_L1_10", 6.80, 12.6, ["r_L1_lobby", "r_L1_bed5"], 0.90, 1))
    ops.append(make_door("d_L1_08", 3.20, 13.6, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_11", 5.94, 13.6, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_09", 3.20, 15.6, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_12", 5.94, 15.6, ["r_L1_bed5", "r_L1_ots"], 0.80, 1))
    ops.append(make_window("w_L1_01", 6.0, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 1.6, d, 1.50, 0.90, 1))
    ops.append(make_window("w_L1_03", 7.5, d, 1.50, 0.90, 1))
    meta = MetadataModel(plan_id="master_7_marla_v01", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "7_marla", "stair_type": "curved", "typology": "classic_dual_bed_rear"})
    return assemble_plan(meta, env, rooms, ops)


def build_7m_v02() -> CanonicalFloorPlan:
    """v02: Central Green Courtyard - 8'x10' central open courtyard separating drawing from lounge."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (2 Cars)", 0, 0, 5.0, 4.8, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Garden", 5.0, 0, 7.0, 2.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 7.0, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 5.0, 2.0, w, 5.8, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Side Dogleg Staircase", 0, 4.8, 2.4, 8.8, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_foyer", "corridor", "Entrance Foyer Gallery", 2.4, 4.8, 4.5, 8.8, 0, False))
    rooms.append(make_room("r_L0_courtyard", "outdoor", "Central Open Green Courtyard", 4.5, 5.8, 7.0, 8.8, 0, False))
    rooms.append(make_room("r_L0_study", "study", "Side Study Room", 7.0, 5.8, w, 8.8, 0, True))
    rooms.append(make_room("r_L0_lounge", "living_room", "Wrap-Around Living Lounge", 0, 8.8, w, 12.6, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Rear Chef Kitchen", 0, 12.6, 3.2, d, 0, True))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 3.2, 12.6, 7.2, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Attached Bath 1", 7.2, 12.6, w, 14.8, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Yard OTS", 7.2, 14.8, w, d, 0, False))

    ops.append(make_door("d_L0_01", 3.6, 4.8, ["r_L0_porch", "r_L0_foyer"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.0, 3.8, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 7.5, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 5.0, 5.8, ["r_L0_foyer", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_05", 2.4, 6.8, ["r_L0_stairs", "r_L0_foyer"], 0.90, 0))
    ops.append(make_door("d_L0_06", 3.6, 8.8, ["r_L0_foyer", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_07", 5.5, 8.8, ["r_L0_courtyard", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_08", 8.0, 8.8, ["r_L0_study", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_09", 1.6, 12.6, ["r_L0_lounge", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_10", 5.0, 12.6, ["r_L0_lounge", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_11", 7.2, 13.7, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_12", 7.2, 15.7, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 6.0, 2.0, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 1.6, d, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_03", 5.0, d, 1.50, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Open Terrace", 0, 0, 5.0, 4.8, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Attached Bath 2", 7.0, 0, w, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Bedroom 2 (Front)", 5.0, 2.0, w, 5.8, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Side Dogleg Staircase Landing", 0, 4.8, 2.4, 8.8, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_gallery", "corridor", "Upper Gallery", 2.4, 4.8, 4.5, 8.8, 1, False))
    rooms.append(make_room("r_L1_courtyard", "outdoor", "Central Open Green Courtyard Void", 4.5, 5.8, 7.0, 8.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom 3 (East)", 7.0, 5.8, w, 8.8, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Lounge", 0, 8.8, w, 12.6, 1, True))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Bedroom 4 (Rear West)", 0, 12.6, 3.2, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Attached Bath 4", 3.2, 12.6, 5.0, 14.8, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Bedroom 5 (Rear Suite)", 5.0, 12.6, 7.2, d, 1, True))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 7.2, 12.6, w, 14.8, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Yard OTS Void", 7.2, 14.8, w, d, 1, False))

    ops.append(make_door("d_L1_01", 3.6, 4.8, ["r_L1_gallery", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 5.0, 3.8, ["r_L1_gallery", "r_L1_bed2"], 1.00, 1))
    ops.append(make_door("d_L1_03", 7.5, 2.0, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_04", 2.4, 6.8, ["r_L1_stairs", "r_L1_gallery"], 0.90, 1))
    ops.append(make_door("d_L1_05", 3.6, 8.8, ["r_L1_gallery", "r_L1_lounge"], 1.10, 1))
    ops.append(make_door("d_L1_06", 8.0, 8.8, ["r_L1_bed3", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_07", 1.6, 12.6, ["r_L1_lounge", "r_L1_bed4"], 0.90, 1))
    ops.append(make_door("d_L1_08", 3.2, 13.7, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_09", 6.0, 12.6, ["r_L1_lounge", "r_L1_bed5"], 0.90, 1))
    ops.append(make_door("d_L1_10", 7.2, 13.7, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_11", 7.2, 15.7, ["r_L1_bed5", "r_L1_ots"], 0.80, 1))
    ops.append(make_window("w_L1_01", 6.0, 2.0, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 1.6, d, 1.50, 0.90, 1))
    ops.append(make_window("w_L1_03", 6.0, d, 1.50, 0.90, 1))
    meta = MetadataModel(plan_id="master_7_marla_v02", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "7_marla", "stair_type": "dogleg", "typology": "central_green_courtyard"})
    return assemble_plan(meta, env, rooms, ops)


def build_7m_v03() -> CanonicalFloorPlan:
    """v03: Side-Passage Independent Stair - Dedicated side passage entry for upper tenants."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (2 Cars)", 0, 0, 4.5, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Lawn", 4.5, 0, 5.8, 1.8, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Powder Room", 5.8, 0, 6.94, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 4.5, 1.8, 6.94, 5.0, 0, True))
    rooms.append(make_room("r_L0_side_passage", "corridor", "Side Passage Entry", 6.94, 0, w, 3.5, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Independent Side Staircase", 6.94, 3.5, w, 8.0, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Family Lounge", 0, 5.0, 6.94, 11.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Ground Kitchen", 6.94, 8.0, w, 12.2, 0, True))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Bed Lobby", 2.2, 11.5, 5.8, 12.5, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 0, 11.5, 2.2, 12.5, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 12.5, 4.3, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Attached Bath 1", 4.3, 12.5, 5.8, 14.8, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Yard OTS", 4.3, 14.8, 5.8, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom 2", 5.8, 12.2, w, d, 0, True))

    ops.append(make_door("d_L0_00", 4.5, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_01", 3.0, 5.0, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.0, 5.0, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_03", 5.8, 1.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 4.5, 0.5, ["r_L0_porch", "r_L0_side_passage"], 0.90, 0)) # connection to passage
    ops.append(make_door("d_L0_05", 8.0, 3.5, ["r_L0_side_passage", "r_L0_stairs"], 0.90, 0))
    ops.append(make_door("d_L0_06", 6.94, 9.5, ["r_L0_lounge", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_07", 3.8, 11.5, ["r_L0_lounge", "r_L0_lobby"], 1.00, 0))
    ops.append(make_door("d_L0_08", 2.2, 12.5, ["r_L0_lobby", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_09", 4.3, 13.6, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_10", 4.3, 15.6, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_11", 5.8, 12.5, ["r_L0_lobby", "r_L0_bed2"], 0.90, 0))
    ops.append(make_door("d_L0_12", 1.1, 12.5, ["r_L0_bed1", "r_L0_bath2"], 0.80, 0))
    ops.append(make_window("w_L0_01", 5.0, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.0, d, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_03", 7.5, d, 1.50, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Terrace", 0, 0, 4.5, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 5.8, 0, 6.94, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom 3 (Front Suite)", 4.5, 1.8, 6.94, 5.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Independent Side Staircase Landing", 6.94, 3.5, w, 8.0, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Tenant Lounge", 0, 5.0, 6.94, 11.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Tenant Kitchenette", 6.94, 8.0, w, 12.2, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Bed Lobby", 2.2, 11.5, 5.8, 12.5, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 0, 11.5, 2.2, 12.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Bedroom 4 (Rear Suite)", 0, 12.5, 4.3, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Attached Bath 4", 4.3, 12.5, 5.8, 14.8, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Yard OTS Void", 4.3, 14.8, 5.8, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Bedroom 5 (Rear East)", 5.8, 12.2, w, d, 1, True))

    ops.append(make_door("d_L1_01", 6.94, 5.5, ["r_L1_stairs", "r_L1_lounge"], 1.10, 1))
    ops.append(make_door("d_L1_02", 3.0, 5.0, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_03", 5.0, 5.0, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_04", 5.8, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_05", 6.94, 9.5, ["r_L1_lounge", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_06", 3.8, 11.5, ["r_L1_lounge", "r_L1_lobby"], 1.00, 1))
    ops.append(make_door("d_L1_07", 2.2, 12.5, ["r_L1_lobby", "r_L1_bed4"], 0.90, 1))
    ops.append(make_door("d_L1_08", 4.3, 13.6, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_09", 4.3, 15.6, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_10", 5.8, 12.5, ["r_L1_lobby", "r_L1_bed5"], 0.90, 1))
    ops.append(make_door("d_L1_11", 1.1, 12.5, ["r_L1_bed4", "r_L1_bath5"], 0.80, 1))
    ops.append(make_window("w_L1_01", 5.0, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.0, d, 1.50, 0.90, 1))
    ops.append(make_window("w_L1_03", 7.5, d, 1.50, 0.90, 1))
    meta = MetadataModel(plan_id="master_7_marla_v03", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "7_marla", "stair_type": "dogleg", "typology": "side_passage_independent_stair"})
    return assemble_plan(meta, env, rooms, ops)


def build_7m_v04() -> CanonicalFloorPlan:
    """v04: Double Show & Dirty Kitchen - Open show kitchen + enclosed dirty kitchen."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (2 Cars)", 0, 0, 5.0, 4.8, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Lawn", 5.0, 0, 7.0, 1.8, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Powder Room", 7.0, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 5.0, 1.8, w, 4.8, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "East Dogleg Staircase", 6.94, 4.8, w, 8.8, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central TV Lounge", 0, 4.8, 6.94, 9.5, 0, True))
    rooms.append(make_room("r_L0_show_kitchen", "kitchen", "Open Show Kitchen", 0, 9.5, 2.2, 12.5, 0, True))
    rooms.append(make_room("r_L0_dining", "dining_room", "Formal Dining Room", 2.2, 9.5, 6.94, 12.5, 0, True))
    rooms.append(make_room("r_L0_dirty_kitchen", "kitchen", "Enclosed Dirty Kitchen", 6.94, 8.8, w, 12.5, 0, True))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 12.5, 3.2, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Attached Bath 1", 3.2, 12.5, 4.57, 14.8, 0, False))
    rooms.append(make_room("r_L0_ots1", "outdoor", "Rear Light Shaft OTS 1", 3.2, 14.8, 4.57, d, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 4.57, 12.5, 5.94, 14.8, 0, False))
    rooms.append(make_room("r_L0_ots2", "outdoor", "Rear Light Shaft OTS 2", 4.57, 14.8, 5.94, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom 2", 5.94, 12.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 3.0, 4.8, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.0, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 7.5, 1.8, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 6.0, 4.8, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_05", 6.94, 6.8, ["r_L0_lounge", "r_L0_stairs"], 0.90, 0))
    ops.append(make_door("d_L0_06", 1.1, 9.5, ["r_L0_lounge", "r_L0_show_kitchen"], 1.00, 0))
    ops.append(make_door("d_L0_07", 4.5, 9.5, ["r_L0_lounge", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_08", 6.94, 10.5, ["r_L0_dining", "r_L0_dirty_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_09", 2.7, 12.5, ["r_L0_dining", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_10", 3.2, 13.6, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_11", 3.2, 15.6, ["r_L0_bed1", "r_L0_ots1"], 0.80, 0))
    ops.append(make_door("d_L0_12", 6.4, 12.5, ["r_L0_dining", "r_L0_bed2"], 0.90, 0))
    ops.append(make_door("d_L0_13", 5.94, 13.6, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_14", 5.94, 15.6, ["r_L0_bed2", "r_L0_ots2"], 0.80, 0))
    ops.append(make_window("w_L0_01", 6.0, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 1.5, d, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_03", 7.5, d, 1.50, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Terrace", 0, 0, 5.0, 4.8, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 7.0, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom 3 (Front)", 5.0, 1.8, w, 4.8, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "East Dogleg Staircase Landing", 6.94, 4.8, w, 8.8, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Lounge", 0, 4.8, 6.94, 9.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 0, 9.5, 2.2, 12.5, 1, True))
    rooms.append(make_room("r_L1_gallery", "corridor", "Upper Central Gallery", 2.2, 9.5, w, 12.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Bedroom 4 (Rear West)", 0, 12.5, 3.2, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Attached Bath 4", 3.2, 12.5, 4.57, 14.8, 1, False))
    rooms.append(make_room("r_L1_ots1", "outdoor", "Upper Light Shaft OTS 1 Void", 3.2, 14.8, 4.57, d, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 4.57, 12.5, 5.94, 14.8, 1, False))
    rooms.append(make_room("r_L1_ots2", "outdoor", "Upper Light Shaft OTS 2 Void", 4.57, 14.8, 5.94, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Bedroom 5 (Rear East)", 5.94, 12.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.0, 4.8, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 6.0, 4.8, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_03", 7.5, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 6.94, 6.8, ["r_L1_lounge", "r_L1_stairs"], 0.90, 1))
    ops.append(make_door("d_L1_05", 1.1, 9.5, ["r_L1_lounge", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_06", 4.5, 9.5, ["r_L1_lounge", "r_L1_gallery"], 1.10, 1))
    ops.append(make_door("d_L1_07", 2.7, 12.5, ["r_L1_gallery", "r_L1_bed4"], 0.90, 1))
    ops.append(make_door("d_L1_08", 3.2, 13.6, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_09", 3.2, 15.6, ["r_L1_bed4", "r_L1_ots1"], 0.80, 1))
    ops.append(make_door("d_L1_10", 6.4, 12.5, ["r_L1_gallery", "r_L1_bed5"], 0.90, 1))
    ops.append(make_door("d_L1_11", 5.94, 13.6, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_12", 5.94, 15.6, ["r_L1_bed5", "r_L1_ots2"], 0.80, 1))
    ops.append(make_window("w_L1_01", 6.0, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 1.5, d, 1.50, 0.90, 1))
    ops.append(make_window("w_L1_03", 7.5, d, 1.50, 0.90, 1))
    meta = MetadataModel(plan_id="master_7_marla_v04", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "7_marla", "stair_type": "dogleg", "typology": "double_show_dirty_kitchen"})
    return assemble_plan(meta, env, rooms, ops)


def build_7m_v05() -> CanonicalFloorPlan:
    """v05: Front-Facing Master Suite - Level 1 master suite oriented forward with private balcony."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Garden Strip", 0, 0, 2.3, 2.0, 0, False))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Ground Master Bath", 2.3, 0, 4.5, 2.0, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Ground Elderly Master Suite", 0, 2.0, 4.5, 5.0, 0, True))
    rooms.append(make_room("r_L0_porch", "garage", "Front Car Porch", 4.5, 0, w, 5.0, 0, False))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Living Hall", 0, 5.0, 6.74, 11.5, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Central Dogleg Staircase Core", 6.74, 5.0, w, 9.0, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Family Kitchen", 6.74, 9.0, w, 12.5, 0, True))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Bed Lobby", 0, 11.5, 4.5, 12.5, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 4.5, 11.5, 6.74, 12.5, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom 2", 0, 12.5, 4.5, d, 0, True))
    rooms.append(make_room("r_L0_bath3", "bathroom", "Attached Bath 3", 4.5, 12.5, 5.8, 14.8, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Yard OTS", 4.5, 14.8, 5.8, d, 0, False))
    rooms.append(make_room("r_L0_garden", "outdoor", "Rear Landscaped Courtyard", 5.8, 12.5, w, d, 0, False))

    ops.append(make_door("d_L0_01", 5.5, 5.0, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 4.5, 3.5, ["r_L0_porch", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_03", 3.4, 2.0, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_04", 2.0, 5.0, ["r_L0_bed1", "r_L0_lounge"], 1.00, 0))
    ops.append(make_door("d_L0_05", 6.74, 7.0, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_06", 6.74, 10.5, ["r_L0_kitchen", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_07", 2.5, 11.5, ["r_L0_lounge", "r_L0_lobby"], 1.00, 0))
    ops.append(make_door("d_L0_08", 2.5, 12.5, ["r_L0_lobby", "r_L0_bed2"], 0.90, 0))
    ops.append(make_door("d_L0_09", 4.5, 13.6, ["r_L0_bed2", "r_L0_bath3"], 0.80, 0))
    ops.append(make_door("d_L0_10", 4.5, 15.6, ["r_L0_bed2", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_11", 5.0, 12.5, ["r_L0_bath2", "r_L0_lobby"], 0.80, 0))
    ops.append(make_door("d_L0_12", 4.5, 15.6, ["r_L0_bed2", "r_L0_garden"], 1.10, 0))
    ops.pop() # remove duplicate at same coord
    ops.append(make_door("d_L0_12", 4.5, 16.2, ["r_L0_bed2", "r_L0_garden"], 0.90, 0))
    ops.append(make_window("w_L0_01", 2.0, 2.0, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.2, d, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_03", 7.5, d, 1.50, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath", 2.3, 0, 4.5, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Front-Facing Master Suite", 0, 2.0, 4.5, 5.0, 1, True))
    rooms.append(make_room("r_L1_terrace", "balcony", "Private Front Balcony", 4.5, 0, w, 5.0, 1, False))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Living Hall", 0, 5.0, 6.74, 11.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Central Dogleg Staircase Landing", 6.74, 5.0, w, 9.0, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 6.74, 9.0, w, 12.5, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Bed Lobby", 0, 11.5, 4.5, 12.5, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Upper Bath 5", 4.5, 11.5, 6.74, 12.5, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Bedroom 5 (Rear Left)", 0, 12.5, 4.5, d, 1, True))
    rooms.append(make_room("r_L1_bath6", "bathroom", "Attached Bath 6", 4.5, 12.5, 5.8, 14.8, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Yard OTS Void", 4.5, 14.8, 5.8, d, 1, False))
    rooms.append(make_room("r_L1_terrace_rear", "balcony", "Rear Sun Terrace", 5.8, 12.5, w, d, 1, False))

    ops.append(make_door("d_L1_01", 5.5, 5.0, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 4.5, 3.5, ["r_L1_terrace", "r_L1_bed4"], 1.10, 1))
    ops.append(make_door("d_L1_03", 3.4, 2.0, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_04", 2.0, 5.0, ["r_L1_bed4", "r_L1_lounge"], 1.00, 1))
    ops.append(make_door("d_L1_05", 6.74, 7.0, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_06", 6.74, 10.5, ["r_L1_kitchenette", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_07", 2.5, 11.5, ["r_L1_lounge", "r_L1_lobby"], 1.00, 1))
    ops.append(make_door("d_L1_08", 2.5, 12.5, ["r_L1_lobby", "r_L1_bed5"], 0.90, 1))
    ops.append(make_door("d_L1_09", 4.5, 13.6, ["r_L1_bed5", "r_L1_bath6"], 0.80, 1))
    ops.append(make_door("d_L1_10", 4.5, 15.6, ["r_L1_bed5", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_11", 5.0, 12.5, ["r_L1_bath5", "r_L1_lobby"], 0.80, 1))
    ops.append(make_door("d_L1_12", 4.5, 16.2, ["r_L1_bed5", "r_L1_terrace_rear"], 0.90, 1))
    ops.append(make_window("w_L1_01", 2.0, 2.0, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.2, d, 1.50, 0.90, 1))
    ops.append(make_window("w_L1_03", 7.5, d, 1.50, 0.90, 1))
    meta = MetadataModel(plan_id="master_7_marla_v05", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "7_marla", "stair_type": "dogleg", "typology": "front_facing_master_suite"})
    return assemble_plan(meta, env, rooms, ops)


def build_7m_v06() -> CanonicalFloorPlan:
    """v06: Great Room Open Pavilion - 30-foot open living/dining/kitchen hall with floating stairs."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (2 Cars)", 0, 0, 4.8, 4.5, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Porch Lawn", 4.8, 0, 7.0, 1.8, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 7.0, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_study", "study", "Front Executive Office", 4.8, 1.8, w, 4.5, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Floating Architectural Staircase", 0, 4.5, 1.2, 8.5, 0, False, {"typology": "floating"}))
    rooms.append(make_room("r_L0_pantry", "kitchen", "Service Scullery Pantry", 0, 8.5, 1.2, 11.5, 0, True))
    rooms.append(make_room("r_L0_great_room", "living_room", "Great Room Open Pavilion Hall", 1.2, 4.5, w, 11.5, 0, True))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 11.5, 3.0, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Attached Bath 1", 3.0, 11.5, 4.5, 13.8, 0, False))
    rooms.append(make_room("r_L0_ots1", "outdoor", "Rear Light Shaft OTS 1", 3.0, 13.8, 4.5, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom 2", 4.5, 11.5, 7.5, d, 0, True))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 7.5, 11.5, w, 13.8, 0, False))
    rooms.append(make_room("r_L0_ots2", "outdoor", "Rear Light Shaft OTS 2", 7.5, 13.8, w, d, 0, False))

    ops.append(make_door("d_L0_01", 3.0, 4.5, ["r_L0_porch", "r_L0_great_room"], 1.30, 0))
    ops.append(make_door("d_L0_02", 4.8, 3.2, ["r_L0_porch", "r_L0_study"], 1.00, 0))
    ops.append(make_door("d_L0_03", 7.5, 1.8, ["r_L0_study", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 6.0, 4.5, ["r_L0_study", "r_L0_great_room"], 1.10, 0))
    ops.append(make_door("d_L0_05", 1.2, 6.5, ["r_L0_stairs", "r_L0_great_room"], 1.00, 0))
    ops.append(make_door("d_L0_06", 1.2, 10.0, ["r_L0_pantry", "r_L0_great_room"], 0.90, 0))
    ops.append(make_door("d_L0_07", 2.2, 11.5, ["r_L0_great_room", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_08", 3.0, 12.6, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_09", 3.0, 14.8, ["r_L0_bed1", "r_L0_ots1"], 0.80, 0))
    ops.append(make_door("d_L0_10", 6.0, 11.5, ["r_L0_great_room", "r_L0_bed2"], 1.00, 0))
    ops.append(make_door("d_L0_11", 7.5, 12.6, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_12", 7.5, 14.8, ["r_L0_bed2", "r_L0_ots2"], 0.80, 0))
    ops.append(make_window("w_L0_01", 6.0, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 1.5, d, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_03", 6.0, d, 1.50, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Open Terrace", 0, 0, 4.8, 4.5, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 7.0, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom 3 (Front)", 4.8, 1.8, w, 4.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Floating Architectural Staircase Landing", 0, 4.5, 1.2, 8.5, 1, False, {"typology": "floating"}))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 0, 8.5, 1.2, 11.5, 1, True))
    rooms.append(make_room("r_L1_gallery", "living_room", "Upper Mezzanine Family Lounge", 1.2, 4.5, w, 11.5, 1, True))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Bedroom 4 (Rear Left)", 0, 11.5, 3.0, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Attached Bath 4", 3.0, 11.5, 4.5, 13.8, 1, False))
    rooms.append(make_room("r_L1_ots1", "outdoor", "Upper Light Shaft OTS 1 Void", 3.0, 13.8, 4.5, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Bedroom 5 (Rear Right)", 4.5, 11.5, 7.5, d, 1, True))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 7.5, 11.5, w, 13.8, 1, False))
    rooms.append(make_room("r_L1_ots2", "outdoor", "Upper Light Shaft OTS 2 Void", 7.5, 13.8, w, d, 1, False))

    ops.append(make_door("d_L1_01", 3.0, 4.5, ["r_L1_gallery", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 6.0, 4.5, ["r_L1_gallery", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_03", 7.5, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 1.2, 6.5, ["r_L1_stairs", "r_L1_gallery"], 1.00, 1))
    ops.append(make_door("d_L1_05", 1.2, 10.0, ["r_L1_kitchenette", "r_L1_gallery"], 0.90, 1))
    ops.append(make_door("d_L1_06", 2.2, 11.5, ["r_L1_gallery", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_07", 3.0, 12.6, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_08", 3.0, 14.8, ["r_L1_bed4", "r_L1_ots1"], 0.80, 1))
    ops.append(make_door("d_L1_09", 6.0, 11.5, ["r_L1_gallery", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_10", 7.5, 12.6, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_11", 7.5, 14.8, ["r_L1_bed5", "r_L1_ots2"], 0.80, 1))
    ops.append(make_window("w_L1_01", 6.0, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 1.5, d, 1.50, 0.90, 1))
    ops.append(make_window("w_L1_03", 6.0, d, 1.50, 0.90, 1))
    meta = MetadataModel(plan_id="master_7_marla_v06", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "7_marla", "stair_type": "floating", "typology": "great_room_open_pavilion"})
    return assemble_plan(meta, env, rooms, ops)


def build_7m_v07() -> CanonicalFloorPlan:
    """v07: Executive Study & Home Office - Front office suite isolated from family living."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (2 Cars)", 0, 0, 5.0, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Office Lawn", 5.0, 0, 7.0, 1.8, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Office Guest Powder", 7.0, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_office", "study", "Executive Home Office Suite", 5.0, 1.8, w, 5.0, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Architectural Straight Staircase", 0, 5.0, 1.2, 11.5, 0, False, {"typology": "straight"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Family Living Lounge", 1.2, 5.0, w, 11.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Family Kitchen", 0, 11.5, 3.5, 14.5, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Attached Bath 1", 0, 14.5, 3.5, 15.8, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Yard OTS", 0, 15.8, 3.5, d, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 3.5, 11.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 3.0, 5.0, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.0, 3.5, ["r_L0_porch", "r_L0_office"], 1.10, 0))
    ops.append(make_door("d_L0_03", 7.5, 1.8, ["r_L0_office", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 6.0, 5.0, ["r_L0_office", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_05", 1.2, 7.0, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_06", 2.2, 11.5, ["r_L0_kitchen", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_07", 5.5, 11.5, ["r_L0_lounge", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_08", 3.5, 15.0, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_09", 3.5, 16.2, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 6.0, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 6.0, d, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_03", 1.8, d, 1.50, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Open Terrace", 0, 0, 5.0, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 7.0, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom 3 (Front Office Wing)", 5.0, 1.8, w, 5.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Architectural Straight Staircase Landing", 0, 5.0, 1.2, 11.5, 1, False, {"typology": "straight"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Lounge", 1.2, 5.0, w, 11.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 0, 11.5, 3.5, 14.5, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Attached Bath 4", 0, 14.5, 3.5, 15.8, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Central Light Shaft OTS Void", 0, 15.8, 3.5, d, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Bedroom 4 (Rear Master)", 3.5, 11.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.0, 5.0, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 6.0, 5.0, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_03", 7.5, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 1.2, 7.0, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_05", 2.2, 11.5, ["r_L1_kitchenette", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_06", 5.5, 11.5, ["r_L1_lounge", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_07", 3.5, 15.0, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_08", 3.5, 16.2, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_window("w_L1_01", 6.0, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 6.0, d, 1.50, 0.90, 1))
    ops.append(make_window("w_L1_03", 1.8, d, 1.50, 0.90, 1))
    meta = MetadataModel(plan_id="master_7_marla_v07", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "7_marla", "stair_type": "straight", "typology": "executive_study_home_office"})
    return assemble_plan(meta, env, rooms, ops)


def build_7m_v08() -> CanonicalFloorPlan:
    """v08: Dual Equal Master Wings - Equal-sized master bedrooms on Level 0 and Level 1."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Car Porch (2 Cars)", 0, 0, 4.8, 4.8, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Garden", 4.8, 0, 7.0, 1.8, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 7.0, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 4.8, 1.8, w, 4.8, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Center Dogleg Staircase", 0, 4.8, 2.4, 8.8, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central TV Lounge", 2.4, 4.8, w, 10.5, 0, True))
    # West master wing:
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Bath 1", 0, 8.8, 2.4, 10.5, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Ground Master Suite Wing", 0, 10.5, 4.5, d, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Family Kitchen", 4.5, 10.5, 7.5, 13.5, 0, True))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 7.5, 10.5, w, 12.5, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "East Light Court OTS", 7.5, 12.5, w, 13.5, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom 2", 4.5, 13.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 3.0, 4.8, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 4.8, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 7.5, 1.8, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 6.0, 4.8, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_05", 2.4, 6.8, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_06", 2.2, 10.5, ["r_L0_lounge", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_07", 1.2, 10.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_08", 6.0, 10.5, ["r_L0_lounge", "r_L0_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_09", 4.5, 14.5, ["r_L0_bed1", "r_L0_bed2"], 0.90, 0))
    ops.append(make_door("d_L0_10", 7.5, 13.0, ["r_L0_bed2", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_11", 8.0, 13.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_window("w_L0_01", 6.0, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.2, d, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_03", 7.0, d, 1.50, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Open Terrace", 0, 0, 4.8, 4.8, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 7.0, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom 3 (Front)", 4.8, 1.8, w, 4.8, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Center Dogleg Staircase Landing", 0, 4.8, 2.4, 8.8, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Lounge", 2.4, 4.8, w, 10.5, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Bath 2", 0, 8.8, 2.4, 10.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Level 1 Master Suite Wing", 0, 10.5, 4.5, d, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 4.5, 10.5, 7.5, 13.5, 1, True))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Upper Bath 5", 7.5, 10.5, w, 12.5, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "East Light Court OTS Void", 7.5, 12.5, w, 13.5, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Bedroom 5 (Rear)", 4.5, 13.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.0, 4.8, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 6.0, 4.8, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_03", 7.5, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 2.4, 6.8, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_05", 2.2, 10.5, ["r_L1_lounge", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_06", 1.2, 10.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_07", 6.0, 10.5, ["r_L1_lounge", "r_L1_kitchenette"], 0.90, 1))
    ops.append(make_door("d_L1_08", 4.5, 14.5, ["r_L1_bed4", "r_L1_bed5"], 0.90, 1))
    ops.append(make_door("d_L1_09", 7.5, 13.0, ["r_L1_bed5", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_10", 8.0, 13.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_window("w_L1_01", 6.0, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.2, d, 1.50, 0.90, 1))
    ops.append(make_window("w_L1_03", 7.0, d, 1.50, 0.90, 1))
    meta = MetadataModel(plan_id="master_7_marla_v08", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "7_marla", "stair_type": "dogleg", "typology": "dual_equal_master_wings"})
    return assemble_plan(meta, env, rooms, ops)


def build_7m_v09() -> CanonicalFloorPlan:
    """v09: Asymmetrical Corner Villa - Side driveway entrance with corner wrap-around porch."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Corner Wrap-Around Porch", 0, 0, 5.5, 4.5, 0, False))
    rooms.append(make_room("r_L0_driveway", "garage", "Side Driveway Extension", 0, 4.5, 2.2, 8.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 7.2, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Corner Drawing Room", 5.5, 2.0, w, 5.5, 0, True))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Lawn Strip", 5.5, 0, 7.2, 2.0, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Grand Curved Staircase", 2.2, 4.5, 4.6, 8.5, 0, False, {"typology": "curved"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central TV Lounge", 4.6, 5.5, w, 11.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Family Kitchen", 0, 8.0, 2.2, 12.5, 0, True))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Bed Lobby", 2.2, 11.5, 5.5, 12.5, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 5.5, 11.5, w, 12.5, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 12.5, 4.5, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Attached Bath 1", 4.5, 12.5, 5.8, 14.8, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Light Shaft OTS", 4.5, 14.8, 5.8, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom 2", 5.8, 12.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 3.0, 4.5, ["r_L0_porch", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_02", 5.5, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 7.5, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 6.5, 5.5, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_05", 4.6, 7.0, ["r_L0_stairs", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_06", 2.2, 9.5, ["r_L0_kitchen", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_07", 3.8, 11.5, ["r_L0_lounge", "r_L0_lobby"], 1.00, 0))
    ops.append(make_door("d_L0_08", 2.2, 12.5, ["r_L0_lobby", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_09", 4.5, 13.6, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_10", 4.5, 15.6, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_11", 5.8, 12.5, ["r_L0_lobby", "r_L0_bed2"], 0.90, 0))
    ops.append(make_door("d_L0_12", 7.5, 12.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_window("w_L0_01", 7.0, 2.0, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.2, d, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_03", 7.5, d, 1.50, 0.90, 0))
    # L1
    rooms.append(make_room("r_L1_terrace", "balcony", "Wrap-Around Corner Terrace", 0, 0, 5.5, 4.5, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 7.2, 0, w, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom 3 (Front)", 5.5, 2.0, w, 5.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Grand Curved Staircase Landing", 2.2, 4.5, 4.6, 8.5, 1, False, {"typology": "curved"}))
    rooms.append(make_room("r_L1_balcony", "balcony", "Side Balcony", 0, 4.5, 2.2, 8.0, 1, False))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Lounge", 4.6, 5.5, w, 11.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 0, 8.0, 2.2, 12.5, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Bed Lobby", 2.2, 11.5, 5.5, 12.5, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 5.5, 11.5, w, 12.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Bedroom 4 (Rear Left)", 0, 12.5, 4.5, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Attached Bath 4", 4.5, 12.5, 5.8, 14.8, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Light Shaft OTS Void", 4.5, 14.8, 5.8, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Bedroom 5 (Rear Right)", 5.8, 12.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.0, 4.5, ["r_L1_stairs", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 6.5, 5.5, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_03", 7.5, 2.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 4.6, 7.0, ["r_L1_stairs", "r_L1_lounge"], 1.10, 1))
    ops.append(make_door("d_L1_05", 2.2, 6.0, ["r_L1_stairs", "r_L1_balcony"], 0.90, 1))
    ops.append(make_door("d_L1_06", 2.2, 9.5, ["r_L1_kitchenette", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_07", 3.8, 11.5, ["r_L1_lounge", "r_L1_lobby"], 1.00, 1))
    ops.append(make_door("d_L1_08", 2.2, 12.5, ["r_L1_lobby", "r_L1_bed4"], 0.90, 1))
    ops.append(make_door("d_L1_09", 4.5, 13.6, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_10", 4.5, 15.6, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_11", 5.8, 12.5, ["r_L1_lobby", "r_L1_bed5"], 0.90, 1))
    ops.append(make_door("d_L1_12", 7.5, 12.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_window("w_L1_01", 7.0, 2.0, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.2, d, 1.50, 0.90, 1))
    ops.append(make_window("w_L1_03", 7.5, d, 1.50, 0.90, 1))
    meta = MetadataModel(plan_id="master_7_marla_v09", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "7_marla", "stair_type": "curved", "typology": "asymmetrical_corner_villa"})
    return assemble_plan(meta, env, rooms, ops)


def build_7m_v10() -> CanonicalFloorPlan:
    """v10: Rear-Garden Terrace Orientation - Living and master oriented to 10-foot rear garden."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Front Car Porch (2 Cars)", 0, 0, 5.0, 4.5, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Garden Strip", 5.0, 0, 7.14, 1.8, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 7.14, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 5.0, 1.8, w, 5.0, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Central Dogleg Staircase", 0, 4.5, 2.4, 8.5, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_foyer", "corridor", "Central Distribution Foyer", 2.4, 4.5, 5.0, 8.5, 0, False))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Show Kitchen", 5.0, 5.0, 7.5, 8.5, 0, True))
    rooms.append(make_room("r_L0_dirty_kitchen", "kitchen", "Dirty Scullery Kitchen", 7.5, 5.0, w, 8.5, 0, True, {"is_dirty_kitchen": True}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Garden-Facing Family Lounge", 0, 8.5, 5.0, 13.71, 0, True))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 5.0, 8.5, w, 13.71, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Attached Bath 1", 5.0, 13.71, 7.0, d, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Light Shaft OTS", 7.0, 13.71, w, d, 0, False))
    rooms.append(make_room("r_L0_garden", "outdoor", "10-Foot Wide Rear Landscaped Garden", 0, 13.71, 5.0, d, 0, False))

    ops.append(make_door("d_L0_01", 3.0, 4.5, ["r_L0_porch", "r_L0_foyer"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.0, 3.2, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 7.5, 1.8, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 5.0, 4.7, ["r_L0_drawing", "r_L0_foyer"], 1.00, 0))
    ops.append(make_door("d_L0_05", 2.4, 6.5, ["r_L0_stairs", "r_L0_foyer"], 0.90, 0))
    ops.append(make_door("d_L0_06", 5.0, 6.0, ["r_L0_foyer", "r_L0_kitchen"], 1.00, 0))
    ops.append(make_door("d_L0_07", 7.5, 6.5, ["r_L0_kitchen", "r_L0_dirty_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_08", 3.5, 8.5, ["r_L0_foyer", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_09", 5.0, 10.0, ["r_L0_lounge", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_10", 6.0, 13.71, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_11", 2.8, 13.71, ["r_L0_lounge", "r_L0_garden"], 1.40, 0))
    ops.append(make_door("d_L0_12", 7.0, 15.0, ["r_L0_bath1", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 6.0, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.5, d, 2.00, 0.90, 0))
    ops.append(make_window("w_L0_03", 8.0, d, 1.50, 0.90, 0))

    # L1: 3 Bedroom Suites (Total 4 bedrooms across house)
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Open Terrace", 0, 0, 5.0, 4.5, 1, False))
    rooms.append(make_room("r_L1_front_ots", "outdoor", "Front Light Court", 5.0, 0, 7.14, 1.8, 1, False))
    rooms.append(make_room("r_L1_bath2", "bathroom", "Upper Bath 2", 7.14, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Bedroom 2 (Front)", 5.0, 1.8, w, 5.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Central Dogleg Staircase Landing", 0, 4.5, 2.4, 8.5, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_foyer", "corridor", "Upper Central Foyer", 2.4, 4.5, 5.0, 8.5, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom 3 (Middle Suite)", 5.0, 5.0, w, 8.5, 1, True))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Attached Bath 3", 5.0, 8.5, 7.0, 10.5, 1, False))
    rooms.append(make_room("r_L1_dress3", "dressing_room", "Dressing Suite 3", 7.0, 8.5, w, 10.5, 1, False))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Garden-Facing Lounge", 0, 8.5, 5.0, 13.71, 1, True))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Bedroom 4 (Upper Master Suite)", 5.0, 10.5, w, 13.71, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Attached Bath 4", 5.0, 13.71, 7.0, d, 1, False))
    rooms.append(make_room("r_L1_garden_terrace", "balcony", "Rear Garden View Roof Terrace", 0, 13.71, 5.0, d, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Light Shaft OTS Void", 7.0, 13.71, w, d, 1, False))

    ops.append(make_door("d_L1_01", 3.0, 4.5, ["r_L1_foyer", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 5.0, 4.7, ["r_L1_foyer", "r_L1_bed2"], 1.00, 1))
    ops.append(make_door("d_L1_03", 8.0, 1.8, ["r_L1_bed2", "r_L1_bath2"], 0.80, 1))
    ops.append(make_door("d_L1_04", 2.4, 6.5, ["r_L1_stairs", "r_L1_foyer"], 0.90, 1))
    ops.append(make_door("d_L1_05", 5.0, 6.5, ["r_L1_foyer", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_06", 6.0, 8.5, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_06_dress", 8.0, 8.5, ["r_L1_bed3", "r_L1_dress3"], 0.80, 1))
    ops.append(make_door("d_L1_07", 3.5, 8.5, ["r_L1_foyer", "r_L1_lounge"], 1.10, 1))
    ops.append(make_door("d_L1_08", 5.0, 11.5, ["r_L1_lounge", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_09", 6.0, 13.71, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_10", 2.8, 13.71, ["r_L1_lounge", "r_L1_garden_terrace"], 1.40, 1))
    ops.append(make_window("w_L1_01", 6.0, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.5, d, 2.00, 0.90, 1))
    ops.append(make_window("w_L1_03", 8.0, d, 1.50, 0.90, 1))
    meta = MetadataModel(plan_id="master_7_marla_v10", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "7_marla", "stair_type": "dogleg", "typology": "rear_garden_terrace_orientation"})
    return assemble_plan(meta, env, rooms, ops)


def build_7m_triplex_6bed() -> CanonicalFloorPlan:
    """v11: Executive 3-Storey Triplex (G+2) - 6 Master Bedrooms with 6 Ensuite Baths, Round Staircase, and Zero Pass-Through Rooms."""
    w, d = 9.14, 16.76
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []

    # ------------------ LEVEL 0 (Ground Floor) ------------------
    rooms.append(make_room("r_L0_porch", "garage", "Modern Car Porch (2 Cars)", 0, 0, 5.0, 5.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 7.0, 0, w, 1.8, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Drawing Room", 5.0, 1.8, w, 5.0, 0, True))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 5.0, 0, 7.0, 1.8, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Feature Round Staircase", 0, 5.0, 2.6, 9.0, 0, False, {"typology": "curved"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central TV Lounge", 2.6, 5.0, w, 11.2, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Modern Working Kitchen", 0, 9.0, 2.6, 12.6, 0, True))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Bed Lobby", 2.6, 11.2, 7.8, 12.6, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 12.6, 3.20, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Attached Bath 1", 3.20, 12.6, 4.57, 14.70, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 4.57, 12.6, 5.94, 14.70, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Central Light Shaft OTS", 3.20, 14.70, 5.94, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom Suite 2", 5.94, 12.6, w, d, 0, True))

    ops.append(make_door("d_L0_01", 3.0, 5.0, ["r_L0_porch", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_02", 5.0, 3.5, ["r_L0_porch", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_03", 6.5, 5.0, ["r_L0_drawing", "r_L0_lounge"], 1.10, 0))
    ops.append(make_door("d_L0_04", 7.5, 1.8, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_05", 2.6, 7.0, ["r_L0_stairs", "r_L0_lounge"], 0.90, 0))
    ops.append(make_door("d_L0_06", 2.6, 9.8, ["r_L0_kitchen", "r_L0_lounge"], 0.90, 0))
    # Open archway into rear bed lobby (no swinging door leaf in modern architecture)
    ops.append(make_door("d_L0_07", 4.57, 11.2, ["r_L0_lounge", "r_L0_lobby"], 1.20, 0))
    # Independent bedroom doors on horizontal lobby wall
    ops.append(make_door("d_L0_08", 2.90, 12.6, ["r_L0_lobby", "r_L0_bed1"], 0.90, 0))
    ops.append(make_door("d_L0_11", 6.80, 12.6, ["r_L0_lobby", "r_L0_bed2"], 0.90, 0))
    # Private ensuite bathroom doors inside bedrooms
    ops.append(make_door("d_L0_09", 3.20, 13.6, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_12", 5.94, 13.6, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_10", 3.20, 15.6, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_13", 5.94, 15.6, ["r_L0_bed2", "r_L0_ots"], 0.80, 0))
    ops.append(make_window("w_L0_01", 6.0, 1.8, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_02", 1.6, d, 1.50, 0.90, 0))
    ops.append(make_window("w_L0_03", 7.5, d, 1.50, 0.90, 0))

    # ------------------ LEVEL 1 (First Floor) ------------------
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Open Terrace", 0, 0, 5.0, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Attached Bath 3", 7.0, 0, w, 1.8, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Bedroom 3 (Front Suite)", 5.0, 1.8, w, 5.0, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Feature Round Staircase Landing", 0, 5.0, 2.6, 9.0, 1, False, {"typology": "curved"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family TV Lounge", 2.6, 5.0, w, 11.2, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 0, 9.0, 2.6, 11.2, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Bed Lobby", 2.6, 11.2, 7.8, 12.6, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Bedroom 4 (Rear Left Suite)", 0, 12.6, 3.20, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Attached Bath 4", 3.20, 12.6, 4.57, 14.70, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 4.57, 12.6, 5.94, 14.70, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Central Light Shaft OTS Void", 3.20, 14.70, 5.94, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Bedroom 5 (Rear Right Suite)", 5.94, 12.6, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.0, 5.0, ["r_L1_lounge", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_02", 6.5, 5.0, ["r_L1_lounge", "r_L1_bed3"], 1.00, 1))
    ops.append(make_door("d_L1_03", 8.0, 1.8, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 2.6, 7.0, ["r_L1_stairs", "r_L1_lounge"], 0.90, 1))
    ops.append(make_door("d_L1_05", 2.6, 9.8, ["r_L1_kitchenette", "r_L1_lounge"], 0.90, 1))
    # Open archway into upper bed lobby
    ops.append(make_door("d_L1_06", 4.57, 11.2, ["r_L1_lounge", "r_L1_lobby"], 1.20, 1))
    ops.append(make_door("d_L1_07", 2.90, 12.6, ["r_L1_lobby", "r_L1_bed4"], 0.90, 1))
    ops.append(make_door("d_L1_10", 6.80, 12.6, ["r_L1_lobby", "r_L1_bed5"], 0.90, 1))
    ops.append(make_door("d_L1_08", 3.20, 13.6, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_11", 5.94, 13.6, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_09", 3.20, 15.6, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_12", 5.94, 15.6, ["r_L1_bed5", "r_L1_ots"], 0.80, 1))
    ops.append(make_window("w_L1_01", 6.0, 1.8, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_02", 1.6, d, 1.50, 0.90, 1))
    ops.append(make_window("w_L1_03", 7.5, d, 1.50, 0.90, 1))

    # ------------------ LEVEL 2 (Second Floor / Penthouse) ------------------
    rooms.append(make_room("r_L2_terrace", "balcony", "Front Rooftop BBQ Terrace", 0, 0, 5.0, 5.0, 2, False))
    rooms.append(make_room("r_L2_bath6", "bathroom", "Attached Bath 6", 7.0, 0, w, 1.8, 2, False))
    rooms.append(make_room("r_L2_bed6", "bedroom", "Master Penthouse Suite 6", 5.0, 1.8, w, 5.0, 2, True))
    rooms.append(make_room("r_L2_stairs", "corridor", "Feature Round Staircase Headroom (DN ->)", 0, 5.0, 2.6, 9.0, 2, False, {"typology": "curved"}))
    rooms.append(make_room("r_L2_lounge", "living_room", "Rooftop Distribution Gallery & Lounge", 2.6, 5.0, w, 11.2, 2, True))
    rooms.append(make_room("r_L2_utility", "utility", "Rooftop Laundry & Wash Area", 0, 9.0, 2.6, 11.2, 2, False))
    rooms.append(make_room("r_L2_lobby", "corridor", "Rooftop Gallery Lobby", 2.6, 11.2, 7.8, 12.6, 2, False))
    rooms.append(make_room("r_L2_terrace_rear", "balcony", "Rear Sky Observation Deck", 0, 12.6, 3.20, d, 2, False))
    rooms.append(make_room("r_L2_bath7", "bathroom", "Attached Bath 7", 3.20, 12.6, 4.57, 14.70, 2, False))
    rooms.append(make_room("r_L2_ots", "outdoor", "Central Light Shaft OTS Void", 3.20, 14.70, 5.94, d, 2, False))
    rooms.append(make_room("r_L2_bed7", "bedroom", "Penthouse Executive Suite 7", 5.94, 12.6, w, d, 2, True))

    ops.append(make_door("d_L2_01", 3.0, 5.0, ["r_L2_lounge", "r_L2_terrace"], 1.10, 2))
    ops.append(make_door("d_L2_02", 6.5, 5.0, ["r_L2_lounge", "r_L2_bed6"], 1.00, 2))
    ops.append(make_door("d_L2_03", 8.0, 1.8, ["r_L2_bed6", "r_L2_bath6"], 0.80, 2))
    ops.append(make_door("d_L2_04", 2.6, 7.0, ["r_L2_stairs", "r_L2_lounge"], 0.90, 2))
    ops.append(make_door("d_L2_05", 2.6, 9.8, ["r_L2_utility", "r_L2_lounge"], 0.90, 2))
    # Open archway into rooftop lobby
    ops.append(make_door("d_L2_06", 4.57, 11.2, ["r_L2_lounge", "r_L2_lobby"], 1.20, 2))
    ops.append(make_door("d_L2_07", 2.90, 12.6, ["r_L2_lobby", "r_L2_terrace_rear"], 0.90, 2))
    ops.append(make_door("d_L2_10", 6.80, 12.6, ["r_L2_lobby", "r_L2_bed7"], 0.90, 2))
    ops.append(make_door("d_L2_11", 5.94, 13.6, ["r_L2_bed7", "r_L2_bath7"], 0.80, 2))
    ops.append(make_window("w_L2_01", 6.0, 1.8, 1.80, 0.90, 2))
    ops.append(make_window("w_L2_02", 7.5, d, 1.50, 0.90, 2))

    meta = MetadataModel(
        plan_id="master_7_marla_triplex_6bed",
        source_type="synthetic_generated",
        floor_count=3,
        levels=[0, 1, 2],
        provenance={
            "scale": "7_marla",
            "stair_type": "curved",
            "typology": "triplex_executive_6bed_ensuite",
            "project_title": "7-MARLA 3-STOREY TRIPLEX 6-BEDROOM RESIDENCE"
        }
    )
    return assemble_plan(meta, env, rooms, ops)


ARCHETYPES_7_MARLA = [
    build_7m_v01, build_7m_v02, build_7m_v03, build_7m_v04, build_7m_v05,
    build_7m_v06, build_7m_v07, build_7m_v08, build_7m_v09, build_7m_v10,
    build_7m_triplex_6bed
]
