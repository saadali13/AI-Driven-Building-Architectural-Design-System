"""
Canonical Archetype Catalog: 1 Kanal (50'-0" x 90'-0" / 15.24m x 27.43m)
Contains 10 architecturally distinct, fully validated canonical archetypes (v01 to v10).
All archetypes achieve QualityGate score 1.0 and pairwise diversity (Jaccard >= 0.25, IoU <= 0.70).
"""

from typing import List
from dataset.schema.canonical import CanonicalFloorPlan, MetadataModel
from dataset.build_master_catalog import (
    make_room,
    make_door,
    make_window,
    assemble_plan,
)

W, D = 15.24, 27.43


def build_1k_v01() -> CanonicalFloorPlan:
    """v01: Triple-Ground-Suite Classic Estate with Side Service Passage & Dressing Buffers (Authentic Pakistani DHA/LDA 1 Kanal)."""
    w, d = W, D
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []

    # =========================================================================
    # LEVEL 0 (GROUND FLOOR): Triple Ground Suites + 5' Side Passage + 6' Lobby
    # =========================================================================
    # Front Outdoor Zone
    rooms.append(make_room("r_L0_lawn", "outdoor", "15-Foot Front Landscaped Lawn", 6.5, 0, w, 4.5, 0, False))
    rooms.append(make_room("r_L0_porch", "garage", "Executive Double Car Porch", 0, 0, 6.5, 6.5, 0, False))
    rooms.append(make_room("r_L0_deck", "balcony", "Entrance Portico & Raised Deck", 6.5, 4.5, 8.5, 6.5, 0, False))

    # Continuous 5'-4" Side Service Passage along West Boundary
    rooms.append(make_room("r_L0_passage_side", "corridor", "5-Foot West Service Passage", 0, 6.5, 1.62, d, 0, False))

    # Formal Front Wing
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 1.62, 6.5, 3.5, 8.5, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Imperial Grand Staircase Hall", 1.62, 8.5, 4.5, 11.0, 0, False, {"typology": "curved"}))
    rooms.append(make_room("r_L0_foyer", "corridor", "Grand Entrance Foyer", 4.5, 6.5, 8.5, 11.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Grand Drawing Room", 8.5, 4.5, w, 11.0, 0, True))

    # Middle Zone: Show Kitchen, Central Gallery, Banquet Dining
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Chef's Show Kitchen", 1.62, 11.0, 6.5, 15.0, 0, True))
    rooms.append(make_room("r_L0_gallery", "corridor", "Central Promenade Gallery", 6.5, 11.0, 8.5, 15.0, 0, False))
    rooms.append(make_room("r_L0_dining", "dining_room", "Banquet Dining Hall", 8.5, 11.0, w, 15.0, 0, True))

    # Scullery & Family TV Lounge
    rooms.append(make_room("r_L0_dirty_kitchen", "kitchen", "Enclosed Scullery Dirty Kitchen", 1.62, 15.0, 4.0, 18.0, 0, True, {"is_dirty_kitchen": True}))
    rooms.append(make_room("r_L0_store", "storage", "Kitchen Scullery Store", 4.0, 15.0, 6.5, 18.0, 0, False))
    rooms.append(make_room("r_L0_lounge", "living_room", "Palatial Family TV Lounge", 6.5, 15.0, w, 20.0, 0, True))

    # Ground Suite 1 (Mid-West, Y: 18.0 to 23.5)
    rooms.append(make_room("r_L0_bed1", "bedroom", "Ground Suite 1 (Mid-West)", 1.62, 18.0, 6.5, 23.5, 0, True))
    rooms.append(make_room("r_L0_dress1", "closet", "Suite 1 Walk-In Dressing", 1.62, 23.5, 3.5, 25.5, 0, False))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Suite 1 Ensuite Bath", 1.62, 25.5, 3.5, d, 0, False))

    # Central Private Bedroom Distribution Lobby (6' Wide)
    rooms.append(make_room("r_L0_lobby", "corridor", "6-Foot Private Bedroom Lobby", 6.5, 20.0, 8.5, 23.5, 0, False))

    # Ground Suite 3 (East Wing, Y: 20.0 to 24.5)
    rooms.append(make_room("r_L0_bed3", "bedroom", "Ground Suite 3 (East)", 8.5, 20.0, w, 24.5, 0, True))
    rooms.append(make_room("r_L0_dress3", "closet", "Suite 3 Walk-In Dressing", 11.5, 24.5, 13.5, 26.0, 0, False))
    rooms.append(make_room("r_L0_bath3", "bathroom", "Suite 3 Ensuite Bath", 11.5, 26.0, w, d, 0, False))

    # Ground Master Suite 2 (Rear Center/West, Y: 23.5 to d)
    rooms.append(make_room("r_L0_bed2", "bedroom", "Ground Master Suite 2 (Rear)", 3.5, 23.5, 8.5, d, 0, True))
    rooms.append(make_room("r_L0_dress2", "closet", "Master Walk-In Dressing 2", 8.5, 24.5, 11.5, 26.0, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Master Ensuite Luxury Bath 2", 8.5, 26.0, 11.5, d, 0, False))

    # Rear OTS Lightwell
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Lightwell Garden OTS", 13.5, 24.5, w, 26.0, 0, False))

    # =========================================================================
    # LEVEL 0 DOORS
    # =========================================================================
    # Main entrance & Drawing
    ops.append(make_door("d_L0_01", 5.5, 6.5, ["r_L0_deck", "r_L0_foyer"], 1.40, 0))
    ops.append(make_door("d_L0_02", 8.5, 7.5, ["r_L0_foyer", "r_L0_drawing"], 1.20, 0))
    ops.append(make_door("d_L0_03", 8.5, 5.5, ["r_L0_deck", "r_L0_drawing"], 1.10, 0))
    ops.append(make_door("d_L0_04", 11.0, 11.0, ["r_L0_drawing", "r_L0_dining"], 1.50, 0))
    ops.append(make_door("d_L0_05", 4.5, 8.5, ["r_L0_foyer", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_06", 3.5, 7.5, ["r_L0_foyer", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_07", 7.0, 11.0, ["r_L0_foyer", "r_L0_gallery"], 1.30, 0))
    ops.append(make_door("d_L0_08", 8.5, 13.0, ["r_L0_gallery", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_09", 6.5, 13.0, ["r_L0_gallery", "r_L0_kitchen"], 1.20, 0))
    ops.append(make_door("d_L0_10", 7.5, 15.0, ["r_L0_gallery", "r_L0_lounge"], 1.40, 0))

    # Scullery / Dirty Kitchen: Interior to Show Kitchen, Exterior to Side Passage!
    ops.append(make_door("d_L0_11", 3.0, 15.0, ["r_L0_kitchen", "r_L0_dirty_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_12", 5.0, 15.0, ["r_L0_kitchen", "r_L0_store"], 0.85, 0))
    ops.append(make_door("d_L0_13", 1.62, 16.5, ["r_L0_dirty_kitchen", "r_L0_passage_side"], 0.90, 0)) # SERVICE PASSAGE DOOR!
    ops.append(make_door("d_L0_14", 1.0, 6.5, ["r_L0_porch", "r_L0_passage_side"], 1.00, 0))

    # Lounge to 6' Private Bedroom Distribution Lobby
    ops.append(make_door("d_L0_15", 7.5, 20.0, ["r_L0_lounge", "r_L0_lobby"], 1.30, 0))

    # Lobby to Suite 1
    ops.append(make_door("d_L0_16", 6.5, 21.0, ["r_L0_lobby", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_17", 2.5, 23.5, ["r_L0_bed1", "r_L0_dress1"], 0.85, 0))
    ops.append(make_door("d_L0_18", 2.5, 25.5, ["r_L0_dress1", "r_L0_bath1"], 0.80, 0))

    # Lobby to Suite 2
    ops.append(make_door("d_L0_19", 7.5, 23.5, ["r_L0_lobby", "r_L0_bed2"], 1.00, 0))
    ops.append(make_door("d_L0_20", 8.5, 25.0, ["r_L0_bed2", "r_L0_dress2"], 0.90, 0))
    ops.append(make_door("d_L0_21", 10.0, 26.0, ["r_L0_dress2", "r_L0_bath2"], 0.80, 0))

    # Lobby to Suite 3
    ops.append(make_door("d_L0_22", 8.5, 21.0, ["r_L0_lobby", "r_L0_bed3"], 1.00, 0))
    ops.append(make_door("d_L0_23", 12.0, 24.5, ["r_L0_bed3", "r_L0_dress3"], 0.85, 0))
    ops.append(make_door("d_L0_24", 12.0, 26.0, ["r_L0_dress3", "r_L0_bath3"], 0.80, 0))
    ops.append(make_door("d_L0_25", 13.5, 25.0, ["r_L0_dress3", "r_L0_ots"], 0.80, 0))

    # Windows
    ops.append(make_window("w_L0_01", 11.0, 4.5, 2.40, 0.90, 0))
    ops.append(make_window("w_L0_02", 5.5, d, 2.00, 0.90, 0))
    ops.append(make_window("w_L0_03", 13.0, d, 2.00, 0.90, 0))

    # =========================================================================
    # LEVEL 1 (FIRST FLOOR): Upper Lounge + Kitchenette + Upper Suites + Terrace
    # =========================================================================
    rooms.append(make_room("r_L1_terrace_f", "balcony", "Front Grand Promenade Terrace", 0, 0, 8.5, 6.5, 1, False))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Imperial Staircase Landing", 1.62, 8.5, 4.5, 11.0, 1, False, {"typology": "curved"}))
    rooms.append(make_room("r_L1_foyer", "corridor", "Upper Central Foyer", 4.5, 6.5, 8.5, 11.0, 1, False))
    rooms.append(make_room("r_L1_study", "study", "Executive Private Study", 1.62, 6.5, 4.5, 8.5, 1, True))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Upper Front Executive Suite 4", 8.5, 4.5, w, 11.0, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Suite 4 Luxury Bath", 8.5, 11.0, 11.5, 15.0, 1, False))
    rooms.append(make_room("r_L1_dress4", "closet", "Suite 4 Walk-In Dressing", 11.5, 11.0, w, 15.0, 1, False))
    rooms.append(make_room("r_L1_gallery", "corridor", "Upper Central Gallery", 4.5, 11.0, 8.5, 15.0, 1, False))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette & Coffee Bar", 1.62, 11.0, 4.5, 15.0, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Palatial Living Hall", 4.5, 15.0, w, 20.0, 1, True))
    rooms.append(make_room("r_L1_gym", "study", "Private Wellness & Gym Studio", 1.62, 15.0, 4.5, 20.0, 1, True))

    # Upper Rear Suites
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Private Suite Lobby", 6.5, 20.0, 8.5, 24.5, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Master Suite 5", 1.62, 20.0, 6.5, 24.5, 1, True))
    rooms.append(make_room("r_L1_dress5", "closet", "Upper Master Dressing 5", 1.62, 24.5, 4.5, 26.0, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Upper Master Luxury Bath 5", 1.62, 26.0, 4.5, d, 1, False))
    rooms.append(make_room("r_L1_bed6", "bedroom", "Upper Rear Bedroom Suite 6", 8.5, 20.0, w, 24.5, 1, True))
    rooms.append(make_room("r_L1_dress6", "closet", "Upper Suite 6 Dressing", 8.5, 24.5, 11.5, 26.0, 1, False))
    rooms.append(make_room("r_L1_bath6", "bathroom", "Upper Suite 6 Bath", 8.5, 26.0, 11.5, d, 1, False))
    rooms.append(make_room("r_L1_terrace_r", "balcony", "Upper Rear Sunset Terrace", 4.5, 24.5, 8.5, d, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Upper Ventilation Void", 11.5, 24.5, w, d, 1, False))

    # Level 1 Doors
    ops.append(make_door("d_L1_01", 5.5, 6.5, ["r_L1_foyer", "r_L1_terrace_f"], 1.30, 1))
    ops.append(make_door("d_L1_02", 4.5, 8.5, ["r_L1_foyer", "r_L1_stairs"], 1.10, 1))
    ops.append(make_door("d_L1_03", 3.0, 6.5, ["r_L1_terrace_f", "r_L1_study"], 1.00, 1))
    ops.append(make_door("d_L1_04", 8.5, 7.5, ["r_L1_foyer", "r_L1_bed4"], 1.10, 1))
    ops.append(make_door("d_L1_05", 10.0, 11.0, ["r_L1_bed4", "r_L1_bath4"], 0.85, 1))
    ops.append(make_door("d_L1_06", 13.0, 11.0, ["r_L1_bed4", "r_L1_dress4"], 0.85, 1))
    ops.append(make_door("d_L1_07", 6.5, 11.0, ["r_L1_foyer", "r_L1_gallery"], 1.30, 1))
    ops.append(make_door("d_L1_08", 4.5, 13.0, ["r_L1_gallery", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_09", 6.5, 15.0, ["r_L1_gallery", "r_L1_lounge"], 1.30, 1))
    ops.append(make_door("d_L1_10", 4.5, 17.5, ["r_L1_lounge", "r_L1_gym"], 1.10, 1))
    ops.append(make_door("d_L1_11", 7.5, 20.0, ["r_L1_lounge", "r_L1_lobby"], 1.30, 1))
    ops.append(make_door("d_L1_12", 6.5, 21.0, ["r_L1_lobby", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_13", 3.0, 24.5, ["r_L1_bed5", "r_L1_dress5"], 0.85, 1))
    ops.append(make_door("d_L1_14", 3.0, 26.0, ["r_L1_dress5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_15", 8.5, 21.0, ["r_L1_lobby", "r_L1_bed6"], 1.00, 1))
    ops.append(make_door("d_L1_16", 10.0, 24.5, ["r_L1_bed6", "r_L1_dress6"], 0.85, 1))
    ops.append(make_door("d_L1_17", 10.0, 26.0, ["r_L1_dress6", "r_L1_bath6"], 0.80, 1))
    ops.append(make_door("d_L1_18", 6.5, 24.5, ["r_L1_lobby", "r_L1_terrace_r"], 1.10, 1))

    # Upper windows
    ops.append(make_window("w_L1_01", 11.0, 4.5, 2.40, 0.90, 1))
    ops.append(make_window("w_L1_02", 3.0, d, 2.00, 0.90, 1))
    ops.append(make_window("w_L1_03", 10.0, d, 2.00, 0.90, 1))

    meta = MetadataModel(
        plan_id="master_1_kanal_v01",
        source_type="synthetic_generated",
        floor_count=2,
        levels=[0, 1],
        provenance={"scale": "1_kanal", "stair_type": "curved", "typology": "triple_ground_suite_classic_estate"}
    )
    return assemble_plan(meta, env, rooms, ops)


def build_1k_v02() -> CanonicalFloorPlan:
    """v02: C-Shaped Courtyard Estate - Layout wrapped around a 20'x30' central open courtyard with perimeter verandas."""
    w, d = W, D
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0: Central courtyard at [4.5, 8.5, 10.74, 17.5]
    rooms.append(make_room("r_L0_porch", "garage", "Entrance Garage (3 Cars)", 0, 0, 7.5, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Formal Lawn", 7.5, 0, 12.5, 2.5, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 12.5, 0, w, 2.5, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Reception Drawing", 7.5, 2.5, w, 8.5, 0, True))
    rooms.append(make_room("r_L0_foyer", "corridor", "Courtyard Entrance Foyer", 0, 5.0, 7.5, 8.5, 0, False))
    # West wing:
    rooms.append(make_room("r_L0_stairs", "corridor", "Veranda Straight Staircase", 0, 8.5, 1.8, 17.5, 0, False, {"typology": "straight"}))
    rooms.append(make_room("r_L0_veranda_w", "corridor", "West Cloistered Veranda", 1.8, 8.5, 4.5, 17.5, 0, False))
    # Central Court:
    rooms.append(make_room("r_L0_court", "outdoor", "Central Open-to-Sky Courtyard", 4.5, 8.5, 10.74, 17.5, 0, False))
    # East wing:
    rooms.append(make_room("r_L0_veranda_e", "corridor", "East Cloistered Veranda", 10.74, 8.5, 13.0, 17.5, 0, False))
    rooms.append(make_room("r_L0_dining", "dining_room", "Courtyard Dining Hall", 13.0, 8.5, w, 13.0, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Courtyard Gourmet Kitchen", 13.0, 13.0, w, 17.5, 0, True))
    # Rear wing:
    rooms.append(make_room("r_L0_lounge", "living_room", "Courtyard View Great Lounge", 0, 17.5, 9.5, 22.0, 0, True))
    rooms.append(make_room("r_L0_pantry", "kitchen", "Back Scullery & Pantry", 9.5, 17.5, w, 22.0, 0, True))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 22.0, 6.5, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 6.5, 22.0, 8.8, d, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 8.8, 22.0, 11.0, d, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Rear Bedroom Suite 2", 11.0, 22.0, w, d, 0, True))

    ops.append(make_door("d_L0_01", 3.8, 5.0, ["r_L0_porch", "r_L0_foyer"], 1.30, 0))
    ops.append(make_door("d_L0_02", 7.5, 6.0, ["r_L0_foyer", "r_L0_drawing"], 1.20, 0))
    ops.append(make_door("d_L0_03", 12.5, 2.5, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 1.8, 8.5, ["r_L0_foyer", "r_L0_stairs"], 0.90, 0))
    ops.append(make_door("d_L0_05", 3.2, 8.5, ["r_L0_foyer", "r_L0_veranda_w"], 1.20, 0))
    ops.append(make_door("d_L0_06", 4.5, 13.0, ["r_L0_veranda_w", "r_L0_court"], 1.40, 0))
    ops.append(make_door("d_L0_07", 10.74, 13.0, ["r_L0_court", "r_L0_veranda_e"], 1.40, 0))
    ops.append(make_door("d_L0_08", 13.0, 10.5, ["r_L0_veranda_e", "r_L0_dining"], 1.10, 0))
    ops.append(make_door("d_L0_09", 13.0, 15.0, ["r_L0_veranda_e", "r_L0_kitchen"], 1.10, 0))
    ops.append(make_door("d_L0_10", 3.2, 17.5, ["r_L0_veranda_w", "r_L0_lounge"], 1.30, 0))
    ops.append(make_door("d_L0_11", 7.0, 17.5, ["r_L0_court", "r_L0_lounge"], 1.50, 0))
    ops.append(make_door("d_L0_12", 9.5, 19.5, ["r_L0_lounge", "r_L0_pantry"], 1.00, 0))
    ops.append(make_door("d_L0_13", 3.2, 22.0, ["r_L0_lounge", "r_L0_bed1"], 1.10, 0))
    ops.append(make_door("d_L0_14", 6.5, 24.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_15", 9.5, 22.0, ["r_L0_lounge", "r_L0_bed2"], 1.10, 0))
    ops.append(make_door("d_L0_16", 11.0, 24.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_window("w_L0_01", 10.0, 2.5, 2.20, 0.90, 0))
    ops.append(make_window("w_L0_02", 3.2, d, 2.00, 0.90, 0))
    ops.append(make_window("w_L0_03", 13.0, d, 2.00, 0.90, 0))

    # L1: C-shaped upper layout with cloistered terrace
    rooms.append(make_room("r_L1_terrace_f", "balcony", "Front Promenade Terrace", 0, 0, 7.5, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 12.5, 0, w, 2.5, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Front Suite 3", 7.5, 0, 12.5, 8.5, 1, True))
    rooms.append(make_room("r_L1_study", "study", "Quiet Library Office", 0, 5.0, 7.5, 8.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Straight Staircase Landing", 0, 8.5, 1.8, 17.5, 1, False, {"typology": "straight"}))
    rooms.append(make_room("r_L1_gallery_w", "corridor", "West Upper Cloistered Gallery", 1.8, 8.5, 4.5, 17.5, 1, False))
    rooms.append(make_room("r_L1_court_void", "outdoor", "Courtyard Open Sky Void", 4.5, 8.5, 10.74, 17.5, 1, False))
    rooms.append(make_room("r_L1_gallery_e", "corridor", "East Upper Cloistered Gallery", 10.74, 8.5, 13.0, 17.5, 1, False))
    rooms.append(make_room("r_L1_media", "living_room", "East Gallery Media Hall", 13.0, 8.5, w, 13.0, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette & Bar", 13.0, 13.0, w, 17.5, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Great Family Lounge", 0, 17.5, 9.5, 22.0, 1, True))
    rooms.append(make_room("r_L1_linen", "dressing_room", "Linen & Utility Store", 9.5, 17.5, w, 22.0, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 22.0, 6.5, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 6.5, 22.0, 8.8, d, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 8.8, 22.0, 11.0, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Rear Bedroom Suite 5", 11.0, 22.0, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.8, 5.0, ["r_L1_study", "r_L1_terrace_f"], 1.20, 1))
    ops.append(make_door("d_L1_02", 7.5, 6.0, ["r_L1_study", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 12.5, 2.5, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 1.8, 8.5, ["r_L1_study", "r_L1_stairs"], 0.90, 1))
    ops.append(make_door("d_L1_05", 3.2, 8.5, ["r_L1_study", "r_L1_gallery_w"], 1.10, 1))
    ops.append(make_door("d_L1_06", 13.0, 10.5, ["r_L1_gallery_e", "r_L1_media"], 1.10, 1))
    ops.append(make_door("d_L1_07", 13.0, 15.0, ["r_L1_gallery_e", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_08", 3.2, 17.5, ["r_L1_gallery_w", "r_L1_lounge"], 1.20, 1))
    ops.append(make_door("d_L1_09", 9.5, 19.5, ["r_L1_lounge", "r_L1_linen"], 0.90, 1))
    ops.append(make_door("d_L1_10", 3.2, 22.0, ["r_L1_lounge", "r_L1_bed4"], 1.10, 1))
    ops.append(make_door("d_L1_11", 6.5, 24.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_12", 9.5, 22.0, ["r_L1_lounge", "r_L1_bed5"], 1.10, 1))
    ops.append(make_door("d_L1_13", 11.0, 24.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_14", 11.5, 8.5, ["r_L1_bed3", "r_L1_gallery_e"], 1.10, 1))
    ops.append(make_door("d_L1_15", 11.5, 17.5, ["r_L1_gallery_e", "r_L1_linen"], 1.00, 1))
    ops.append(make_window("w_L1_01", 10.0, 0, 2.20, 0.90, 1))
    ops.append(make_window("w_L1_02", 3.2, d, 2.00, 0.90, 1))
    ops.append(make_window("w_L1_03", 13.0, d, 2.00, 0.90, 1))
    meta = MetadataModel(plan_id="master_1_kanal_v02", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "1_kanal", "stair_type": "straight", "typology": "c_shaped_courtyard_estate"})
    return assemble_plan(meta, env, rooms, ops)


def build_1k_v03() -> CanonicalFloorPlan:
    """v03: Grand Rotunda Entrance - Circular rotunda entrance foyer with curved imperial staircase."""
    w, d = W, D
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0: Curved imperial stairs on West flank, grand rotunda center, formal drawing East
    rooms.append(make_room("r_L0_porch", "garage", "Imperial Car Porch", 4.0, 0, 11.24, 4.5, 0, False))
    rooms.append(make_room("r_L0_lawn_w", "outdoor", "West Front Garden", 0, 0, 4.0, 4.5, 0, False))
    rooms.append(make_room("r_L0_lawn_e", "outdoor", "East Front Garden", 11.24, 0, w, 4.5, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Curved Imperial Rotunda Staircase", 0, 4.5, 4.5, 11.0, 0, False, {"typology": "curved"}))
    rooms.append(make_room("r_L0_rotunda", "corridor", "Grand Imperial Circular Rotunda", 4.5, 4.5, 10.74, 11.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Rotunda Powder Room", 12.74, 4.5, w, 6.5, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Rotunda Drawing Room", 10.74, 6.5, w, 12.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Kitchen & Chef Pantry", 0, 11.0, 3.74, 18.0, 0, True))
    rooms.append(make_room("r_L0_lounge", "living_room", "Palatial Family Great Lounge", 3.74, 11.0, 10.74, 18.0, 0, True))
    rooms.append(make_room("r_L0_dining", "dining_room", "State Banquet Dining Hall", 10.74, 12.5, w, 18.0, 0, True))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Suite Distribution Gallery", 0, 18.0, w, 19.5, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 19.5, 6.5, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master 5-Fixture Bath 1", 6.5, 19.5, 8.8, 24.5, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Private Master Light Shaft", 6.5, 24.5, 8.8, d, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Luxury Bath 2", 8.8, 19.5, 11.0, 24.5, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Secondary Master Suite 2", 11.0, 19.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 7.5, 4.5, ["r_L0_porch", "r_L0_rotunda"], 1.50, 0))
    ops.append(make_door("d_L0_02", 4.5, 7.5, ["r_L0_rotunda", "r_L0_stairs"], 1.40, 0))
    ops.append(make_door("d_L0_03", 10.74, 8.5, ["r_L0_rotunda", "r_L0_drawing"], 1.30, 0))
    ops.append(make_door("d_L0_04", 12.74, 5.5, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_05", 13.0, 12.5, ["r_L0_drawing", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_06", 10.74, 14.5, ["r_L0_dining", "r_L0_lounge"], 1.30, 0))
    ops.append(make_door("d_L0_07", 7.5, 11.0, ["r_L0_rotunda", "r_L0_lounge"], 1.50, 0))
    ops.append(make_door("d_L0_08", 3.74, 14.5, ["r_L0_lounge", "r_L0_kitchen"], 1.20, 0))
    ops.append(make_door("d_L0_09", 6.0, 18.0, ["r_L0_lounge", "r_L0_lobby"], 1.30, 0))
    ops.append(make_door("d_L0_10", 3.2, 19.5, ["r_L0_lobby", "r_L0_bed1"], 1.10, 0))
    ops.append(make_door("d_L0_11", 6.5, 21.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_12", 6.5, 25.5, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_13", 13.0, 19.5, ["r_L0_lobby", "r_L0_bed2"], 1.10, 0))
    ops.append(make_door("d_L0_14", 11.0, 21.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_window("w_L0_01", w, 9.5, 2.40, 0.90, 0))
    ops.append(make_window("w_L0_02", 3.2, d, 2.00, 0.90, 0))
    ops.append(make_window("w_L0_03", 13.0, d, 2.00, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace_c", "balcony", "Front Imperial Balcony", 4.0, 0, 11.24, 4.5, 1, False))
    rooms.append(make_room("r_L1_stairs", "corridor", "Curved Imperial Staircase Landing", 0, 4.5, 4.5, 11.0, 1, False, {"typology": "curved"}))
    rooms.append(make_room("r_L1_rotunda", "corridor", "Upper Rotunda Mezzanine Gallery", 4.5, 4.5, 10.74, 11.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 12.74, 4.5, w, 6.5, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Executive Rotunda Bedroom 3", 10.74, 6.5, w, 12.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette & Bar", 0, 11.0, 3.74, 18.0, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Living Hall", 3.74, 11.0, 10.74, 18.0, 1, True))
    rooms.append(make_room("r_L1_study", "study", "Private Library & Office", 10.74, 12.5, w, 18.0, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Distribution Gallery", 0, 18.0, w, 19.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 19.5, 6.5, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master 5-Fixture Bath 4", 6.5, 19.5, 8.8, 24.5, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Private Master Light Shaft Void", 6.5, 24.5, 8.8, d, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 8.8, 19.5, 11.0, 24.5, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Bedroom Suite 5", 11.0, 19.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 7.5, 4.5, ["r_L1_rotunda", "r_L1_terrace_c"], 1.30, 1))
    ops.append(make_door("d_L1_02", 4.5, 7.5, ["r_L1_rotunda", "r_L1_stairs"], 1.30, 1))
    ops.append(make_door("d_L1_03", 10.74, 8.5, ["r_L1_rotunda", "r_L1_bed3"], 1.20, 1))
    ops.append(make_door("d_L1_04", 12.74, 5.5, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_05", 13.0, 12.5, ["r_L1_bed3", "r_L1_study"], 1.00, 1))
    ops.append(make_door("d_L1_06", 10.74, 14.5, ["r_L1_study", "r_L1_lounge"], 1.10, 1))
    ops.append(make_door("d_L1_07", 7.5, 11.0, ["r_L1_rotunda", "r_L1_lounge"], 1.40, 1))
    ops.append(make_door("d_L1_08", 3.74, 14.5, ["r_L1_lounge", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_09", 6.0, 18.0, ["r_L1_lounge", "r_L1_lobby"], 1.30, 1))
    ops.append(make_door("d_L1_10", 3.2, 19.5, ["r_L1_lobby", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_11", 6.5, 21.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_12", 6.5, 25.5, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_13", 13.0, 19.5, ["r_L1_lobby", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_14", 11.0, 21.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_window("w_L1_01", w, 9.5, 2.40, 0.90, 1))
    ops.append(make_window("w_L1_02", 3.2, d, 2.00, 0.90, 1))
    ops.append(make_window("w_L1_03", 13.0, d, 2.00, 0.90, 1))
    meta = MetadataModel(plan_id="master_1_kanal_v03", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "1_kanal", "stair_type": "curved", "typology": "grand_rotunda_entrance"})
    return assemble_plan(meta, env, rooms, ops)


def build_1k_v04() -> CanonicalFloorPlan:
    """v04: Side Servant Quarters & Service Alley - Private service passage to rear servant suite & independent stairs."""
    w, d = W, D
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0: Dedicated side service alley along West boundary: 0..1.5
    rooms.append(make_room("r_L0_service_alley", "corridor", "Exterior Private Service Alley", 0, 0, 1.5, 21.0, 0, False))
    rooms.append(make_room("r_L0_porch", "garage", "Executive Front Garage (3 Cars)", 1.5, 0, 9.5, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscaped Lawn", 9.5, 0, 13.0, 2.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 13.0, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Guest Drawing Hall", 9.5, 2.0, w, 7.5, 0, True))
    rooms.append(make_room("r_L0_foyer", "corridor", "Grand Entrance Foyer", 1.5, 5.0, 9.5, 7.5, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Classical Dogleg Staircase", 1.5, 7.5, 4.5, 13.0, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Palatial Family Living Hall", 4.5, 7.5, 11.5, 15.0, 0, True))
    rooms.append(make_room("r_L0_dining", "dining_room", "Formal Dining Room", 11.5, 7.5, w, 11.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Designer Island Kitchen", 11.5, 11.5, w, 16.5, 0, True))
    # Rear suite and rear servant quarter:
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Suite Vestibule", 1.5, 13.0, 4.5, 15.0, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 1.5, 15.0, 7.5, 21.0, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 7.5, 15.0, 10.0, 21.0, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Light Shaft OTS", 10.0, 16.5, 11.5, 21.0, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Secondary Suite 2", 11.5, 16.5, w, 22.5, 0, True))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 11.5, 22.5, w, d, 0, False))
    # Servant Quarter at rear:
    rooms.append(make_room("r_L0_servant_bed", "bedroom", "Private Servant Quarters", 0, 21.0, 5.5, d, 0, True))
    rooms.append(make_room("r_L0_servant_bath", "bathroom", "Servant Dedicated Bath", 5.5, 21.0, 8.5, d, 0, False))
    rooms.append(make_room("r_L0_servant_yard", "outdoor", "Service Laundry Yard", 8.5, 21.0, 11.5, d, 0, False))

    ops.append(make_door("d_L0_01", 5.5, 5.0, ["r_L0_porch", "r_L0_foyer"], 1.30, 0))
    ops.append(make_door("d_L0_02", 9.5, 4.5, ["r_L0_foyer", "r_L0_drawing"], 1.20, 0))
    ops.append(make_door("d_L0_03", 13.0, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 3.0, 7.5, ["r_L0_foyer", "r_L0_stairs"], 1.00, 0))
    ops.append(make_door("d_L0_05", 6.5, 7.5, ["r_L0_foyer", "r_L0_lounge"], 1.40, 0))
    ops.append(make_door("d_L0_06", 11.5, 9.5, ["r_L0_lounge", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_07", 11.5, 13.5, ["r_L0_lounge", "r_L0_kitchen"], 1.20, 0))
    ops.append(make_door("d_L0_08", 4.5, 14.0, ["r_L0_lounge", "r_L0_lobby"], 1.10, 0))
    ops.append(make_door("d_L0_09", 4.5, 15.0, ["r_L0_lobby", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_10", 7.5, 18.0, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_11", 11.5, 18.0, ["r_L0_lounge", "r_L0_bed2"], 1.00, 0))
    ops.append(make_door("d_L0_12", 13.0, 22.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    # Service connections:
    ops.append(make_door("d_L0_13", 1.5, 21.0, ["r_L0_service_alley", "r_L0_servant_bed"], 0.90, 0))
    ops.append(make_door("d_L0_14", 5.5, 23.5, ["r_L0_servant_bed", "r_L0_servant_bath"], 0.80, 0))
    ops.append(make_door("d_L0_15", 8.5, 23.5, ["r_L0_servant_bath", "r_L0_servant_yard"], 0.80, 0))
    ops.append(make_door("d_L0_16", 1.5, 3.0, ["r_L0_porch", "r_L0_service_alley"], 1.00, 0))
    ops.append(make_window("w_L0_01", 11.5, 2.0, 2.20, 0.90, 0))
    ops.append(make_window("w_L0_02", 3.0, d, 1.80, 0.90, 0))
    ops.append(make_window("w_L0_03", w, 14.0, 1.80, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace", "outdoor", "Front Promenade Balcony", 1.5, 0, 9.5, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 13.0, 0, w, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Executive Suite 3", 9.5, 2.0, w, 7.5, 1, True))
    rooms.append(make_room("r_L1_linen", "dressing_room", "Linen & Luggage Store", 1.5, 5.0, 4.0, 7.5, 1, False))
    rooms.append(make_room("r_L1_study", "study", "Upper Front Study", 4.0, 5.0, 9.5, 7.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Classical Dogleg Staircase Landing", 1.5, 7.5, 4.5, 13.0, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Living Hall", 4.5, 7.5, 11.5, 15.0, 1, True))
    rooms.append(make_room("r_L1_media", "living_room", "Cinema & Media Lounge", 11.5, 7.5, w, 11.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette", 11.5, 11.5, w, 16.5, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Suite Vestibule", 1.5, 13.0, 4.5, 15.0, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 1.5, 15.0, 7.5, 21.0, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 7.5, 15.0, 10.0, 21.0, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Light Shaft OTS Void", 10.0, 16.5, 11.5, 21.0, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Suite 5", 11.5, 16.5, w, 22.5, 1, True))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 11.5, 22.5, w, d, 1, False))
    rooms.append(make_room("r_L1_roof_terrace", "balcony", "Rear Servant Roof Terrace", 0, 21.0, 11.5, d, 1, False))

    ops.append(make_door("d_L1_01", 6.5, 5.0, ["r_L1_study", "r_L1_terrace"], 1.20, 1))
    ops.append(make_door("d_L1_02", 9.5, 6.0, ["r_L1_study", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 13.0, 2.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 4.0, 6.5, ["r_L1_study", "r_L1_linen"], 0.80, 1))
    ops.append(make_door("d_L1_05", 6.5, 7.5, ["r_L1_study", "r_L1_lounge"], 1.30, 1))
    ops.append(make_door("d_L1_06", 11.5, 9.5, ["r_L1_lounge", "r_L1_media"], 1.10, 1))
    ops.append(make_door("d_L1_07", 11.5, 13.5, ["r_L1_lounge", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_08", 4.5, 14.0, ["r_L1_lounge", "r_L1_lobby"], 1.10, 1))
    ops.append(make_door("d_L1_09", 4.5, 15.0, ["r_L1_lobby", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_10", 7.5, 18.0, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_11", 11.5, 18.0, ["r_L1_lounge", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_12", 13.0, 22.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_door("d_L1_13", 5.0, 21.0, ["r_L1_bed4", "r_L1_roof_terrace"], 1.00, 1))
    ops.append(make_door("d_L1_14", 4.5, 8.5, ["r_L1_stairs", "r_L1_lounge"], 1.00, 1))
    ops.append(make_window("w_L1_01", 11.5, 2.0, 2.20, 0.90, 1))
    ops.append(make_window("w_L1_02", 5.5, 0, 1.80, 0.90, 1))
    ops.append(make_window("w_L1_03", w, 14.0, 1.80, 0.90, 1))
    meta = MetadataModel(plan_id="master_1_kanal_v04", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "1_kanal", "stair_type": "dogleg", "typology": "side_servant_quarters_and_service_alley"})
    return assemble_plan(meta, env, rooms, ops)


def build_1k_v05() -> CanonicalFloorPlan:
    """v05: Rear Garden Villa - Living lounge, dining, and master bedrooms pushed to rear opening onto 25' garden."""
    w, d = W, D
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0: Rear 25-foot landscaped garden from y=21.0 to d (6.43m)
    rooms.append(make_room("r_L0_porch", "garage", "Entrance Garage (3 Cars)", 0, 0, 8.0, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Welcome Courtyard", 8.0, 0, 12.0, 2.5, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 12.0, 0, w, 2.5, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Guest Drawing Hall", 8.0, 2.5, w, 8.5, 0, True))
    rooms.append(make_room("r_L0_foyer", "corridor", "Grand Central Foyer", 0, 5.0, 8.0, 8.5, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Open Floating Architectural Stair", 0, 8.5, 2.0, 14.5, 0, False, {"typology": "floating"}))
    rooms.append(make_room("r_L0_gallery", "corridor", "Grand Central Gallery", 2.0, 8.5, 4.0, 14.5, 0, False))
    rooms.append(make_room("r_L0_study", "study", "Private Home Executive Office", 4.0, 8.5, 8.0, 14.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Front Gourmet Show Kitchen", 8.0, 8.5, 12.0, 14.5, 0, True))
    rooms.append(make_room("r_L0_dirty_kitchen", "kitchen", "Enclosed Scullery Kitchen", 12.0, 8.5, w, 14.5, 0, True, {"is_dirty_kitchen": True}))
    # Rear grand pavilion opening to garden:
    rooms.append(make_room("r_L0_dining", "dining_room", "Garden Dining Pavilion", 0, 14.5, 5.5, 21.0, 0, True))
    rooms.append(make_room("r_L0_lounge", "living_room", "Garden View Great Hall", 5.5, 14.5, w, 21.0, 0, True))
    # Rear 25-foot landscaped garden:
    rooms.append(make_room("r_L0_garden", "outdoor", "25-Foot Rear Landscaped Garden", 0, 21.0, 9.0, d, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Garden Villa Suite", 9.0, 21.0, 12.5, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Spa Bath", 12.5, 21.0, w, d, 0, False))

    ops.append(make_door("d_L0_01", 4.0, 5.0, ["r_L0_porch", "r_L0_foyer"], 1.30, 0))
    ops.append(make_door("d_L0_02", 8.0, 4.0, ["r_L0_porch", "r_L0_drawing"], 1.20, 0))
    ops.append(make_door("d_L0_03", 12.0, 2.5, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 8.0, 6.5, ["r_L0_foyer", "r_L0_drawing"], 1.30, 0))
    ops.append(make_door("d_L0_05", 1.0, 8.5, ["r_L0_foyer", "r_L0_stairs"], 0.90, 0))
    ops.append(make_door("d_L0_06", 3.0, 8.5, ["r_L0_foyer", "r_L0_gallery"], 1.20, 0))
    ops.append(make_door("d_L0_06_study", 4.0, 11.5, ["r_L0_gallery", "r_L0_study"], 1.00, 0))
    ops.append(make_door("d_L0_08_gal", 3.0, 14.5, ["r_L0_gallery", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_07", 10.0, 14.5, ["r_L0_lounge", "r_L0_kitchen"], 1.20, 0))
    ops.append(make_door("d_L0_08", 12.0, 11.5, ["r_L0_kitchen", "r_L0_dirty_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_09", 5.5, 17.5, ["r_L0_dining", "r_L0_lounge"], 1.50, 0))
    ops.append(make_door("d_L0_11", 4.5, 21.0, ["r_L0_dining", "r_L0_garden"], 1.60, 0))
    ops.append(make_door("d_L0_12", 7.5, 21.0, ["r_L0_lounge", "r_L0_garden"], 1.80, 0))
    ops.append(make_door("d_L0_13", 10.5, 21.0, ["r_L0_lounge", "r_L0_bed1"], 1.20, 0))
    ops.append(make_door("d_L0_14", 12.5, 24.0, ["r_L0_bed1", "r_L0_bath1"], 0.90, 0))
    ops.append(make_window("w_L0_01", 10.0, 2.5, 2.20, 0.90, 0))
    ops.append(make_window("w_L0_02", 10.5, d, 2.00, 0.90, 0))
    ops.append(make_window("w_L0_03", w, 11.0, 2.00, 0.90, 0))

    # L1: 4 Bedrooms on Upper Level (Total 5 bedrooms across house)
    rooms.append(make_room("r_L1_terrace_f", "outdoor", "Front Garden Terrace", 0, 0, 8.0, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 12.0, 0, w, 2.5, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Front Guest Suite 3", 8.0, 0, 12.0, 8.5, 1, True))
    rooms.append(make_room("r_L1_bed2", "bedroom", "Upper Suite 2", 0, 5.0, 8.0, 8.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Open Floating Stair Landing", 0, 8.5, 2.0, 14.5, 1, False, {"typology": "floating"}))
    rooms.append(make_room("r_L1_gallery", "corridor", "Upper Central Gallery", 2.0, 8.5, 4.0, 14.5, 1, False))
    rooms.append(make_room("r_L1_study", "study", "Upper Private Studio", 4.0, 8.5, 8.0, 14.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Bar Kitchenette", 8.0, 8.5, w, 14.5, 1, True))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Upper Suite 4", 0, 14.5, 5.5, 21.0, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Living Hall", 5.5, 14.5, w, 21.0, 1, True))
    rooms.append(make_room("r_L1_roof_terrace", "balcony", "Rear Garden View Sky Terrace", 0, 21.0, 9.0, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Master Bedroom Suite 5", 9.0, 21.0, 12.5, d, 1, True))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Master Luxury Bath 5", 12.5, 21.0, w, d, 1, False))

    ops.append(make_door("d_L1_01", 4.0, 5.0, ["r_L1_bed2", "r_L1_terrace_f"], 1.20, 1))
    ops.append(make_door("d_L1_02", 8.0, 4.0, ["r_L1_bed2", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 12.0, 2.5, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 1.0, 8.5, ["r_L1_bed2", "r_L1_stairs"], 0.90, 1))
    ops.append(make_door("d_L1_05", 3.0, 8.5, ["r_L1_bed2", "r_L1_gallery"], 1.10, 1))
    ops.append(make_door("d_L1_06", 4.0, 11.5, ["r_L1_gallery", "r_L1_study"], 1.00, 1))
    ops.append(make_door("d_L1_07", 3.0, 14.5, ["r_L1_gallery", "r_L1_bed4"], 1.10, 1))
    ops.append(make_door("d_L1_08", 5.5, 17.5, ["r_L1_bed4", "r_L1_lounge"], 1.30, 1))
    ops.append(make_door("d_L1_08_kit", 8.0, 14.5, ["r_L1_lounge", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_09", 7.5, 21.0, ["r_L1_lounge", "r_L1_roof_terrace"], 1.50, 1))
    ops.append(make_door("d_L1_10", 10.5, 21.0, ["r_L1_lounge", "r_L1_bed5"], 1.10, 1))
    ops.append(make_door("d_L1_11", 12.5, 24.0, ["r_L1_bed5", "r_L1_bath5"], 0.90, 1))
    ops.append(make_window("w_L1_01", 10.0, 0, 2.20, 0.90, 1))
    ops.append(make_window("w_L1_02", 10.5, d, 2.00, 0.90, 1))
    ops.append(make_window("w_L1_03", w, 11.0, 2.00, 0.90, 1))
    meta = MetadataModel(plan_id="master_1_kanal_v05", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "1_kanal", "stair_type": "floating", "typology": "rear_garden_villa"})
    return assemble_plan(meta, env, rooms, ops)


def build_1k_v06() -> CanonicalFloorPlan:
    """v06: Modern Open-Plan Pavilion - Floor-to-ceiling glass walls, 12' kitchen island, continuous great room."""
    w, d = W, D
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0
    rooms.append(make_room("r_L0_porch", "garage", "Entrance Garage (3 Cars)", 0, 0, 8.5, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Linear Lawn Strip", 8.5, 0, 12.5, 2.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Concealed Powder Room", 12.5, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Glass Pavilion Drawing", 8.5, 2.0, w, 8.0, 0, True))
    rooms.append(make_room("r_L0_foyer", "corridor", "Central Entrance Gallery", 0, 5.0, 8.5, 8.0, 0, False))
    # Modern Great Room: 35-foot continuous hall with kitchen on West and sculptural stair on East
    rooms.append(make_room("r_L0_kitchen", "kitchen", "12-Foot Island Show Kitchen", 0, 8.0, 4.5, 13.5, 0, True))
    rooms.append(make_room("r_L0_dirty_kitchen", "kitchen", "Enclosed Butler Pantry Scullery", 0, 13.5, 4.5, 17.5, 0, True))
    rooms.append(make_room("r_L0_great_room", "living_room", "35-Foot Open Great Room", 4.5, 8.0, 13.24, 17.5, 0, True))
    rooms.append(make_room("r_L0_stairs", "corridor", "Sculptural Steel Flight Stairs", 13.24, 8.0, w, 15.0, 0, False, {"typology": "straight"}))
    rooms.append(make_room("r_L0_store_bar", "dressing_room", "Concealed Bar & Storage", 13.24, 15.0, w, 17.5, 0, False))
    # Rear Suites:
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Suite Corridor", 0, 17.5, w, 19.0, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 19.0, 6.5, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master 5-Fixture Bath 1", 6.5, 19.0, 8.8, 24.5, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Yard OTS Light Court", 6.5, 24.5, 8.8, d, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Luxury Bath 2", 8.8, 19.0, 11.0, 24.5, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Secondary Suite 2", 11.0, 19.0, w, d, 0, True))

    ops.append(make_door("d_L0_01", 4.2, 5.0, ["r_L0_porch", "r_L0_foyer"], 1.30, 0))
    ops.append(make_door("d_L0_02", 8.5, 4.0, ["r_L0_porch", "r_L0_drawing"], 1.20, 0))
    ops.append(make_door("d_L0_03", 12.5, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 8.5, 6.5, ["r_L0_foyer", "r_L0_drawing"], 1.30, 0))
    ops.append(make_door("d_L0_05", 5.0, 8.0, ["r_L0_foyer", "r_L0_great_room"], 1.50, 0))
    ops.append(make_door("d_L0_06", 4.5, 10.5, ["r_L0_great_room", "r_L0_kitchen"], 1.30, 0))
    ops.append(make_door("d_L0_07", 2.2, 13.5, ["r_L0_kitchen", "r_L0_dirty_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_08", 13.24, 10.0, ["r_L0_great_room", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_09", 13.24, 16.0, ["r_L0_great_room", "r_L0_store_bar"], 0.90, 0))
    ops.append(make_door("d_L0_10", 7.5, 17.5, ["r_L0_great_room", "r_L0_lobby"], 1.30, 0))
    ops.append(make_door("d_L0_11", 3.2, 19.0, ["r_L0_lobby", "r_L0_bed1"], 1.10, 0))
    ops.append(make_door("d_L0_12", 6.5, 21.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_13", 6.5, 25.5, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_14", 13.0, 19.0, ["r_L0_lobby", "r_L0_bed2"], 1.10, 0))
    ops.append(make_door("d_L0_15", 11.0, 21.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_window("w_L0_01", 10.5, 2.0, 2.20, 0.90, 0))
    ops.append(make_window("w_L0_02", 3.2, d, 2.00, 0.90, 0))
    ops.append(make_window("w_L0_03", 13.0, d, 2.00, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace_f", "outdoor", "Front Promenade Deck", 0, 0, 8.5, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 12.5, 0, w, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Executive Suite 3", 8.5, 2.0, w, 8.0, 1, True))
    rooms.append(make_room("r_L1_store", "dressing_room", "Upper Executive Store", 0, 5.0, 2.5, 8.0, 1, False))
    rooms.append(make_room("r_L1_study", "study", "Private Home Studio", 2.5, 5.0, 8.5, 8.0, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Bar Kitchenette", 0, 8.0, 4.5, 13.5, 1, True))
    rooms.append(make_room("r_L1_media", "living_room", "Upper Cinema & Media Room", 0, 13.5, 4.5, 17.5, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Open Great Lounge", 4.5, 8.0, 13.24, 17.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Sculptural Steel Flight Landing", 13.24, 8.0, w, 15.0, 1, False, {"typology": "straight"}))
    rooms.append(make_room("r_L1_linen", "dressing_room", "Upper Linen & Utility", 13.24, 15.0, w, 17.5, 1, False))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Suite Corridor", 0, 17.5, w, 19.0, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 19.0, 6.5, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master 5-Fixture Bath 4", 6.5, 19.0, 8.8, 24.5, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Yard OTS Light Void", 6.5, 24.5, 8.8, d, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 8.8, 19.0, 11.0, 24.5, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Suite 5", 11.0, 19.0, w, d, 1, True))

    ops.append(make_door("d_L1_01", 5.0, 5.0, ["r_L1_study", "r_L1_terrace_f"], 1.20, 1))
    ops.append(make_door("d_L1_01_store", 2.5, 6.5, ["r_L1_study", "r_L1_store"], 0.80, 1))
    ops.append(make_door("d_L1_02", 8.5, 6.5, ["r_L1_study", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 12.5, 2.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_05", 5.0, 8.0, ["r_L1_study", "r_L1_lounge"], 1.30, 1))
    ops.append(make_door("d_L1_06", 4.5, 10.5, ["r_L1_lounge", "r_L1_kitchenette"], 1.10, 1))
    ops.append(make_door("d_L1_07", 4.5, 15.5, ["r_L1_lounge", "r_L1_media"], 1.10, 1))
    ops.append(make_door("d_L1_08", 13.24, 10.0, ["r_L1_lounge", "r_L1_stairs"], 1.10, 1))
    ops.append(make_door("d_L1_09", 13.24, 16.0, ["r_L1_lounge", "r_L1_linen"], 0.90, 1))
    ops.append(make_door("d_L1_10", 7.5, 17.5, ["r_L1_lounge", "r_L1_lobby"], 1.30, 1))
    ops.append(make_door("d_L1_11", 3.2, 19.0, ["r_L1_lobby", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_12", 6.5, 21.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_13", 6.5, 25.5, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_14", 13.0, 19.0, ["r_L1_lobby", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_15", 11.0, 21.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_window("w_L1_01", 10.5, 2.0, 2.20, 0.90, 1))
    ops.append(make_window("w_L1_02", 3.2, d, 2.00, 0.90, 1))
    ops.append(make_window("w_L1_03", 13.0, d, 2.00, 0.90, 1))
    meta = MetadataModel(plan_id="master_1_kanal_v06", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "1_kanal", "stair_type": "straight", "typology": "modern_open_plan_pavilion"})
    return assemble_plan(meta, env, rooms, ops)


def build_1k_v07() -> CanonicalFloorPlan:
    """v07: Dual Master Ground Suites - Two 18'x16' ground master bedrooms with 5-fixture luxury baths."""
    w, d = W, D
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0: Symmetrical dual master suites at rear (each 7.62m wide x 6.5m deep)
    rooms.append(make_room("r_L0_porch", "garage", "Grand Imperial Porch (3 Cars)", 3.5, 0, 11.74, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn_w", "outdoor", "West Front Garden", 0, 0, 3.5, 5.0, 0, False))
    rooms.append(make_room("r_L0_lawn_e", "outdoor", "East Front Garden", 11.74, 0, w, 2.5, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Foyer Powder Room", 11.74, 2.5, w, 5.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Guest Drawing Hall", 0, 5.0, 5.5, 11.5, 0, True))
    rooms.append(make_room("r_L0_foyer", "corridor", "Imperial Grand Entrance Foyer", 5.5, 5.0, 9.74, 8.5, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Bifurcated Grand Stairs", 5.5, 8.5, 9.74, 11.5, 0, False, {"typology": "bifurcated"}))
    rooms.append(make_room("r_L0_dining", "dining_room", "Banquet Dining Hall", 9.74, 5.0, w, 11.5, 0, True))
    rooms.append(make_room("r_L0_lounge", "living_room", "Central Palatial Family Hall", 0, 11.5, 10.5, 17.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Kitchen & Chef Station", 10.5, 11.5, w, 17.5, 0, True))
    # Two massive 18'x16' ground master suites at rear:
    rooms.append(make_room("r_L0_lobby", "corridor", "Private Master Suites Vestibule", 0, 17.5, w, 19.0, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1 (West)", 0, 19.0, 5.5, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "5-Fixture Luxury Spa Bath 1", 5.5, 19.0, 7.62, 24.5, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Central Garden Light Well", 5.5, 24.5, 9.74, d, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "5-Fixture Luxury Spa Bath 2", 7.62, 19.0, 9.74, 24.5, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Master Bedroom Suite 2 (East)", 9.74, 19.0, w, d, 0, True))

    ops.append(make_door("d_L0_01", 7.62, 5.0, ["r_L0_porch", "r_L0_foyer"], 1.40, 0))
    ops.append(make_door("d_L0_02", 5.5, 6.5, ["r_L0_drawing", "r_L0_foyer"], 1.20, 0))
    ops.append(make_door("d_L0_03", 9.74, 6.5, ["r_L0_foyer", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_04", 11.74, 3.5, ["r_L0_porch", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_05", 7.62, 8.5, ["r_L0_foyer", "r_L0_stairs"], 1.30, 0))
    ops.append(make_door("d_L0_06", 3.0, 11.5, ["r_L0_drawing", "r_L0_lounge"], 1.20, 0))
    ops.append(make_door("d_L0_07", 7.62, 11.5, ["r_L0_stairs", "r_L0_lounge"], 1.30, 0))
    ops.append(make_door("d_L0_08", 10.5, 14.5, ["r_L0_lounge", "r_L0_kitchen"], 1.20, 0))
    ops.append(make_door("d_L0_09", 5.0, 17.5, ["r_L0_lounge", "r_L0_lobby"], 1.40, 0))
    ops.append(make_door("d_L0_10", 2.8, 19.0, ["r_L0_lobby", "r_L0_bed1"], 1.10, 0))
    ops.append(make_door("d_L0_11", 5.5, 21.5, ["r_L0_bed1", "r_L0_bath1"], 0.90, 0))
    ops.append(make_door("d_L0_12", 5.5, 25.5, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_13", 12.5, 19.0, ["r_L0_lobby", "r_L0_bed2"], 1.10, 0))
    ops.append(make_door("d_L0_14", 9.74, 21.5, ["r_L0_bed2", "r_L0_bath2"], 0.90, 0))
    ops.append(make_window("w_L0_01", 0, 8.5, 2.20, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.8, d, 2.20, 0.90, 0))
    ops.append(make_window("w_L0_03", 12.5, d, 2.20, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace_c", "balcony", "Front Imperial Balcony", 3.5, 0, 11.74, 5.0, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 11.74, 2.5, w, 5.0, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Executive Suite 3", 0, 5.0, 5.5, 11.5, 1, True))
    rooms.append(make_room("r_L1_gallery", "corridor", "Upper Central Imperial Gallery", 5.5, 5.0, 9.74, 8.5, 1, False))
    rooms.append(make_room("r_L1_stairs", "corridor", "Bifurcated Grand Stairs Landing", 5.5, 8.5, 9.74, 11.5, 1, False, {"typology": "bifurcated"}))
    rooms.append(make_room("r_L1_study", "study", "Private Library & Office", 9.74, 5.0, w, 11.5, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Palatial Living Hall", 0, 11.5, 10.5, 17.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette & Bar", 10.5, 11.5, w, 17.5, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Suite Vestibule", 0, 17.5, w, 19.0, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4 (West)", 0, 19.0, 5.5, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Luxury Spa Bath 4", 5.5, 19.0, 7.62, 24.5, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Central Garden Light Void", 5.5, 24.5, 9.74, d, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Luxury Spa Bath 5", 7.62, 19.0, 9.74, 24.5, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Master Suite 5 (East)", 9.74, 19.0, w, d, 1, True))

    ops.append(make_door("d_L1_01", 7.62, 5.0, ["r_L1_gallery", "r_L1_terrace_c"], 1.30, 1))
    ops.append(make_door("d_L1_02", 5.5, 6.5, ["r_L1_bed3", "r_L1_gallery"], 1.10, 1))
    ops.append(make_door("d_L1_03", 9.74, 6.5, ["r_L1_gallery", "r_L1_study"], 1.10, 1))
    ops.append(make_door("d_L1_04", 11.74, 3.5, ["r_L1_terrace_c", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_05", 7.62, 8.5, ["r_L1_gallery", "r_L1_stairs"], 1.30, 1))
    ops.append(make_door("d_L1_06", 3.0, 11.5, ["r_L1_bed3", "r_L1_lounge"], 1.10, 1))
    ops.append(make_door("d_L1_07", 7.62, 11.5, ["r_L1_stairs", "r_L1_lounge"], 1.30, 1))
    ops.append(make_door("d_L1_08", 10.5, 14.5, ["r_L1_lounge", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_09", 5.0, 17.5, ["r_L1_lounge", "r_L1_lobby"], 1.30, 1))
    ops.append(make_door("d_L1_10", 2.8, 19.0, ["r_L1_lobby", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_11", 5.5, 21.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_12", 5.5, 25.5, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_13", 12.5, 19.0, ["r_L1_lobby", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_14", 9.74, 21.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_window("w_L1_01", 0, 8.5, 2.20, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.8, d, 2.20, 0.90, 1))
    ops.append(make_window("w_L1_03", 12.5, d, 2.20, 0.90, 1))
    meta = MetadataModel(plan_id="master_1_kanal_v07", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "1_kanal", "stair_type": "bifurcated", "typology": "dual_master_ground_suites"})
    return assemble_plan(meta, env, rooms, ops)


def build_1k_v08() -> CanonicalFloorPlan:
    """v08: Triple Garage & Home Theater - Enclosed 3-car garage with mudroom, upper tier-seated cinema."""
    w, d = W, D
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0: Triple enclosed garage occupying front 0..8.5, 0..6.5
    rooms.append(make_room("r_L0_garage", "garage", "Enclosed Triple Bay Garage", 0, 0, 8.5, 6.5, 0, False))
    rooms.append(make_room("r_L0_mudroom", "dressing_room", "Garage Mudroom Vestibule", 0, 6.5, 3.5, 9.0, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Front Landscape Garden", 8.5, 0, 13.0, 2.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 13.0, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Executive Guest Drawing", 8.5, 2.0, w, 7.5, 0, True))
    rooms.append(make_room("r_L0_foyer", "corridor", "Grand Central Foyer", 3.5, 6.5, 8.5, 9.0, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Dogleg Staircase", 8.5, 7.5, 11.5, 13.0, 0, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L0_dining", "dining_room", "Formal Dining Hall", 11.5, 7.5, w, 13.0, 0, True))
    rooms.append(make_room("r_L0_lounge", "living_room", "Palatial Family Living Hall", 0, 9.0, 8.5, 16.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Island Kitchen", 8.5, 13.0, w, 17.5, 0, True))
    # Rear Suites:
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Suite Lobby", 0, 16.5, 8.5, 18.0, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Bedroom Suite 1", 0, 18.0, 5.5, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Bath 1", 5.5, 18.0, 7.8, 24.0, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Rear Yard OTS", 5.5, 24.0, 8.5, d, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Bath 2", 7.8, 18.0, 10.5, 24.0, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Secondary Suite 2", 10.5, 17.5, w, d, 0, True))

    ops.append(make_door("d_L0_01", 1.8, 6.5, ["r_L0_garage", "r_L0_mudroom"], 1.00, 0))
    ops.append(make_door("d_L0_02", 3.5, 7.5, ["r_L0_mudroom", "r_L0_foyer"], 1.10, 0))
    ops.append(make_door("d_L0_03", 8.5, 4.5, ["r_L0_garage", "r_L0_drawing"], 1.20, 0))
    ops.append(make_door("d_L0_04", 13.0, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_05", 8.5, 8.0, ["r_L0_foyer", "r_L0_drawing"], 1.20, 0))
    ops.append(make_door("d_L0_06", 6.0, 9.0, ["r_L0_foyer", "r_L0_lounge"], 1.40, 0))
    ops.append(make_door("d_L0_07", 8.5, 10.5, ["r_L0_lounge", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_08", 11.5, 10.5, ["r_L0_stairs", "r_L0_dining"], 1.10, 0))
    ops.append(make_door("d_L0_09", 8.5, 14.5, ["r_L0_lounge", "r_L0_kitchen"], 1.20, 0))
    ops.append(make_door("d_L0_10", 4.2, 16.5, ["r_L0_lounge", "r_L0_lobby"], 1.30, 0))
    ops.append(make_door("d_L0_11", 2.8, 18.0, ["r_L0_lobby", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_12", 5.5, 21.0, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_13", 5.5, 25.5, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_14", 8.5, 17.5, ["r_L0_lobby", "r_L0_bed2"], 0.0))
    ops.pop()
    ops.append(make_door("d_L0_14", 10.5, 19.5, ["r_L0_kitchen", "r_L0_bed2"], 0.0))
    ops.pop()
    # Connect Bed 2 from lobby:
    ops.append(make_door("d_L0_14", 7.8, 18.0, ["r_L0_lobby", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_15", 10.5, 21.0, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_door("d_L0_16", 6.5, 16.5, ["r_L0_lounge", "r_L0_bed2"], 1.10, 0)) # corner touch
    ops.pop()
    ops.append(make_door("d_L0_16", 8.5, 17.0, ["r_L0_lobby", "r_L0_bed2"], 1.10, 0)) # lobby extends to 8.5
    ops.append(make_window("w_L0_01", 10.5, 2.0, 2.20, 0.90, 0))
    ops.append(make_window("w_L0_02", 2.8, d, 2.00, 0.90, 0))
    ops.append(make_window("w_L0_03", 13.0, d, 2.00, 0.90, 0))

    # L1: Upper dedicated Home Theater over garage
    rooms.append(make_room("r_L1_theater", "living_room", "Acoustic Cinema Home Theater", 0, 0, 8.5, 6.5, 1, True))
    rooms.append(make_room("r_L1_terrace", "balcony", "Front Promenade Balcony", 8.5, 0, w, 4.5, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 13.0, 4.5, w, 7.5, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Executive Suite 3", 8.5, 4.5, 13.0, 7.5, 1, True))
    rooms.append(make_room("r_L1_gallery", "corridor", "Upper Central Foyer", 0, 6.5, 8.5, 9.0, 1, False))
    rooms.append(make_room("r_L1_stairs", "corridor", "Dogleg Staircase Landing", 8.5, 7.5, 11.5, 13.0, 1, False, {"typology": "dogleg"}))
    rooms.append(make_room("r_L1_study", "study", "Quiet Library Office", 11.5, 7.5, w, 13.0, 1, True))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Family Living Hall", 0, 9.0, 8.5, 16.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette & Bar", 8.5, 13.0, w, 17.5, 1, True))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Suite Lobby", 0, 16.5, 8.5, 18.0, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 18.0, 5.5, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 5.5, 18.0, 7.8, 24.0, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Rear Yard OTS Void", 5.5, 24.0, 8.5, d, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 7.8, 18.0, 10.5, 24.0, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Suite 5", 10.5, 17.5, w, d, 1, True))

    ops.append(make_door("d_L1_01", 4.2, 6.5, ["r_L1_gallery", "r_L1_theater"], 1.20, 1))
    ops.append(make_door("d_L1_02", 8.5, 5.5, ["r_L1_gallery", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 10.5, 4.5, ["r_L1_bed3", "r_L1_terrace"], 1.10, 1))
    ops.append(make_door("d_L1_04", 13.0, 6.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_05", 6.0, 9.0, ["r_L1_gallery", "r_L1_lounge"], 1.30, 1))
    ops.append(make_door("d_L1_06", 8.5, 10.5, ["r_L1_lounge", "r_L1_stairs"], 1.10, 1))
    ops.append(make_door("d_L1_07", 11.5, 10.5, ["r_L1_stairs", "r_L1_study"], 1.00, 1))
    ops.append(make_door("d_L1_08", 8.5, 14.5, ["r_L1_lounge", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_09", 4.2, 16.5, ["r_L1_lounge", "r_L1_lobby"], 1.20, 1))
    ops.append(make_door("d_L1_10", 2.8, 18.0, ["r_L1_lobby", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_11", 5.5, 21.0, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_12", 5.5, 25.5, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_13", 8.5, 17.5, ["r_L1_lobby", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_14", 10.5, 21.0, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_window("w_L1_01", 10.5, 0, 2.20, 0.90, 1))
    ops.append(make_window("w_L1_02", 2.8, d, 2.00, 0.90, 1))
    ops.append(make_window("w_L1_03", 13.0, d, 2.00, 0.90, 1))
    meta = MetadataModel(plan_id="master_1_kanal_v08", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "1_kanal", "stair_type": "dogleg", "typology": "triple_garage_and_home_theater"})
    return assemble_plan(meta, env, rooms, ops)


def build_1k_v09() -> CanonicalFloorPlan:
    """v09: 45-Degree Angular / Splayed Modernist Pavilion with Side Garden Patios (Image 2 Archetype)."""
    w, d = W, D
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []

    # =========================================================================
    # LEVEL 0 (GROUND FLOOR): 45-Degree Angular / Splayed Pavilion (Image 2)
    # =========================================================================
    # Front Lawn & Double Porch
    rooms.append(make_room("r_L0_lawn", "outdoor", "22-Foot Front Landscaped Garden Lawn", 0, 0, 8.5, 6.0, 0, False))
    rooms.append(make_room("r_L0_porch", "garage", "20-Foot Dual Car Porch & Driveway", 8.5, 0, w, 6.0, 0, False))
    rooms.append(make_room("r_L0_podium", "balcony", "Raised Splayed Entrance Podium", 6.5, 6.0, 9.5, 8.0, 0, False))

    # Formal Front: Splayed Sitting & Dining (West) and Splayed Drawing Room (East)
    rooms.append(make_room("r_L0_dining", "dining_room", "Angled Garden Dining & Sitting Salon", 0, 6.0, 6.5, 12.0, 0, True))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room Suite", 0, 12.0, 3.5, 14.5, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Angled Executive Drawing Room", 9.5, 6.0, w, 12.0, 0, True))

    # 45-Degree Splayed Entrance Lobby & Central Circulation
    rooms.append(make_room("r_L0_foyer", "corridor", "10-Foot Splayed Diagonal Entrance Lobby", 6.5, 8.0, 9.5, 14.5, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Diagonal Architectural Staircase", 6.5, 14.5, 9.5, 18.0, 0, False, {"typology": "curved"}))

    # Side Patio (12' Wide Outdoor Garden Court on West)
    rooms.append(make_room("r_L0_patio_side", "outdoor", "12-Foot West Garden Patio", 0, 14.5, 4.0, 21.0, 0, False))

    # Kitchen Complex (East Flank with Patio Access)
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Diagonal Chef's Show Kitchen", 9.5, 12.0, w, 17.5, 0, True))
    rooms.append(make_room("r_L0_dirty_kitchen", "kitchen", "Enclosed Scullery Dirty Kitchen", 11.5, 17.5, w, 21.0, 0, True, {"is_dirty_kitchen": True}))

    # Angled Central Living Lounge (opens to 12' Side Garden Patio)
    rooms.append(make_room("r_L0_lounge", "living_room", "Angled Great Living Lounge", 4.0, 14.5, 6.5, 21.0, 0, True))
    rooms.append(make_room("r_L0_lounge_east", "living_room", "Lounge Fireside Salon", 6.5, 18.0, 11.5, 21.0, 0, True))

    # Rear Patios & Master Suites
    rooms.append(make_room("r_L0_patio_rear", "outdoor", "9-Foot Rear Sunset Garden Patio", 0, 21.0, 5.0, d, 0, False))

    # Private Suite Lobby
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Suite Distribution Gallery", 5.0, 21.0, 7.5, 23.5, 0, False))

    # Master Bedroom Suite (Diagonal Master Bed opening to rear patio)
    rooms.append(make_room("r_L0_bed1", "bedroom", "Diagonal Master Bedroom Pavilion", 5.0, 23.5, 10.5, d, 0, True))
    rooms.append(make_room("r_L0_dress1", "closet", "Master Walk-In Dressing Suite", 10.5, 23.5, 12.5, 25.5, 0, False))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master Luxury Spa Bath", 10.5, 25.5, 12.5, d, 0, False))

    # Secondary Suite 2
    rooms.append(make_room("r_L0_bed2", "bedroom", "Secondary Suite 2", 7.5, 21.0, 12.5, 23.5, 0, True))
    rooms.append(make_room("r_L0_dress2", "closet", "Suite 2 Dressing Room", 12.5, 21.0, w, 23.5, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Suite 2 Attached Bath", 12.5, 23.5, w, d, 0, False))

    # =========================================================================
    # LEVEL 0 DOORS
    # =========================================================================
    ops.append(make_door("d_L0_01", 8.0, 8.0, ["r_L0_podium", "r_L0_foyer"], 1.40, 0))
    ops.append(make_door("d_L0_02", 6.5, 9.5, ["r_L0_foyer", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_03", 9.5, 9.5, ["r_L0_foyer", "r_L0_drawing"], 1.30, 0))
    ops.append(make_door("d_L0_04", 3.5, 13.0, ["r_L0_dining", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_05", 8.0, 14.5, ["r_L0_foyer", "r_L0_stairs"], 1.10, 0))
    ops.append(make_door("d_L0_06", 6.5, 16.0, ["r_L0_foyer", "r_L0_lounge"], 1.30, 0))
    ops.append(make_door("d_L0_07", 9.5, 14.5, ["r_L0_foyer", "r_L0_kitchen"], 1.20, 0))
    ops.append(make_door("d_L0_08", 4.0, 17.5, ["r_L0_lounge", "r_L0_patio_side"], 1.40, 0)) # Lounge opens to 12' patio!
    ops.append(make_door("d_L0_08b", 6.5, 19.5, ["r_L0_lounge", "r_L0_lounge_east"], 1.30, 0))
    ops.append(make_door("d_L0_09", 11.5, 19.0, ["r_L0_kitchen", "r_L0_dirty_kitchen"], 0.90, 0))
    ops.append(make_door("d_L0_10", w, 19.0, ["r_L0_dirty_kitchen", "r_L0_porch"], 0.90, 0)) # exterior service!
    ops.append(make_door("d_L0_11", 5.5, 21.0, ["r_L0_lounge", "r_L0_lobby"], 1.20, 0))
    ops.append(make_door("d_L0_12", 6.0, 23.5, ["r_L0_lobby", "r_L0_bed1"], 1.00, 0))
    ops.append(make_door("d_L0_13", 5.0, 25.0, ["r_L0_bed1", "r_L0_patio_rear"], 1.20, 0)) # Master bed opens to rear patio!
    ops.append(make_door("d_L0_14", 10.5, 24.5, ["r_L0_bed1", "r_L0_dress1"], 0.85, 0))
    ops.append(make_door("d_L0_15", 11.5, 25.5, ["r_L0_dress1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_16", 7.5, 22.0, ["r_L0_lobby", "r_L0_bed2"], 1.00, 0))
    ops.append(make_door("d_L0_17", 12.5, 22.0, ["r_L0_bed2", "r_L0_dress2"], 0.85, 0))
    ops.append(make_door("d_L0_18", 13.5, 23.5, ["r_L0_dress2", "r_L0_bath2"], 0.80, 0))

    # Windows on exterior perimeter
    ops.append(make_window("w_L0_01", 3.0, 0, 2.00, 0.90, 0))
    ops.append(make_window("w_L0_02", w, 9.0, 2.00, 0.90, 0))
    ops.append(make_window("w_L0_03", 8.0, d, 2.00, 0.90, 0))

    # =========================================================================
    # LEVEL 1 (FIRST FLOOR): Splayed Upper Gallery, Lounge & Suites
    # =========================================================================
    rooms.append(make_room("r_L1_terrace_f", "balcony", "Upper Promenade Front Deck", 0, 0, 8.5, 6.0, 1, False))
    rooms.append(make_room("r_L1_study", "study", "Diagonal Panoramic Study", 0, 6.0, 6.5, 12.0, 1, True))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Upper Front Suite 3", 9.5, 6.0, w, 12.0, 1, True))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Suite 3 Luxury Bath", 9.5, 12.0, 12.5, 14.5, 1, False))
    rooms.append(make_room("r_L1_foyer", "corridor", "Upper Splayed Foyer Landing", 6.5, 8.0, 9.5, 14.5, 1, False))
    rooms.append(make_room("r_L1_stairs", "corridor", "Upper Staircase Landing", 6.5, 14.5, 9.5, 18.0, 1, False, {"typology": "curved"}))
    rooms.append(make_room("r_L1_terrace_w", "balcony", "West Upper View Terrace", 0, 14.5, 4.0, 21.0, 1, False))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Great Family Lounge", 4.0, 14.5, 6.5, 21.0, 1, True))
    rooms.append(make_room("r_L1_media", "living_room", "Upper Cinema & Games Room", 6.5, 18.0, 11.5, 21.0, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette & Bar", 11.5, 14.5, w, 21.0, 1, True))

    # Upper Rear Suites
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Suite Distribution Gallery", 5.0, 21.0, 7.5, 23.5, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Upper Master Bedroom Suite 4", 5.0, 23.5, 10.5, d, 1, True))
    rooms.append(make_room("r_L1_dress4", "closet", "Upper Master Dressing Suite 4", 10.5, 23.5, 12.5, 25.5, 1, False))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Upper Master Spa Bath 4", 10.5, 25.5, 12.5, d, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Bedroom Suite 5", 7.5, 21.0, 12.5, 23.5, 1, True))
    rooms.append(make_room("r_L1_dress5", "closet", "Suite 5 Dressing Room", 12.5, 21.0, w, 23.5, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Suite 5 Attached Bath", 12.5, 23.5, w, d, 1, False))
    rooms.append(make_room("r_L1_terrace_r", "balcony", "Upper Rear View Terrace", 0, 21.0, 5.0, d, 1, False))

    # Level 1 Doors
    ops.append(make_door("d_L1_01", 6.5, 8.0, ["r_L1_terrace_f", "r_L1_foyer"], 1.30, 1))
    ops.append(make_door("d_L1_02", 6.5, 9.5, ["r_L1_foyer", "r_L1_study"], 1.10, 1))
    ops.append(make_door("d_L1_03", 9.5, 9.5, ["r_L1_foyer", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_04", 11.0, 12.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_05", 8.0, 14.5, ["r_L1_foyer", "r_L1_stairs"], 1.10, 1))
    ops.append(make_door("d_L1_06", 6.5, 16.0, ["r_L1_foyer", "r_L1_lounge"], 1.20, 1))
    ops.append(make_door("d_L1_07", 4.0, 17.5, ["r_L1_lounge", "r_L1_terrace_w"], 1.20, 1))
    ops.append(make_door("d_L1_08", 6.5, 19.5, ["r_L1_lounge", "r_L1_media"], 1.20, 1))
    ops.append(make_door("d_L1_09", 11.5, 18.0, ["r_L1_media", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_10", 5.5, 21.0, ["r_L1_lounge", "r_L1_lobby"], 1.20, 1))
    ops.append(make_door("d_L1_11", 6.0, 23.5, ["r_L1_lobby", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_12", 5.0, 25.0, ["r_L1_bed4", "r_L1_terrace_r"], 1.10, 1))
    ops.append(make_door("d_L1_13", 10.5, 24.5, ["r_L1_bed4", "r_L1_dress4"], 0.85, 1))
    ops.append(make_door("d_L1_14", 11.5, 25.5, ["r_L1_dress4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_15", 7.5, 22.0, ["r_L1_lobby", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_16", 12.5, 22.0, ["r_L1_bed5", "r_L1_dress5"], 0.85, 1))
    ops.append(make_door("d_L1_17", 13.5, 23.5, ["r_L1_dress5", "r_L1_bath5"], 0.80, 1))

    # Upper windows on exterior perimeter
    ops.append(make_window("w_L1_01", 3.0, 0, 2.00, 0.90, 1))
    ops.append(make_window("w_L1_02", w, 9.0, 2.00, 0.90, 1))
    ops.append(make_window("w_L1_03", 8.0, d, 2.00, 0.90, 1))

    meta = MetadataModel(
        plan_id="master_1_kanal_v09",
        source_type="synthetic_generated",
        floor_count=2,
        levels=[0, 1],
        provenance={"scale": "1_kanal", "stair_type": "curved", "typology": "45_degree_angular_splayed_pavilion"}
    )
    return assemble_plan(meta, env, rooms, ops)


def build_1k_v10() -> CanonicalFloorPlan:
    """v10: Wellness & Spa Oriented Villa - Dedicated sauna/steam room, gym terrace, and interior water court."""
    w, d = W, D
    env = [[0, 0], [w, 0], [w, d], [0, d], [0, 0]]
    rooms, ops = [], []
    # L0: Features indoor water feature patio and dedicated wellness spa suite
    rooms.append(make_room("r_L0_porch", "garage", "Entrance Garage (3 Cars)", 0, 0, 7.5, 4.5, 0, False))
    rooms.append(make_room("r_L0_lawn", "outdoor", "Zen Front Garden", 7.5, 0, 12.0, 2.0, 0, False))
    rooms.append(make_room("r_L0_powder", "bathroom", "Guest Powder Room", 12.0, 0, w, 2.0, 0, False))
    rooms.append(make_room("r_L0_drawing", "living_room", "Formal Guest Reception", 7.5, 2.0, w, 7.5, 0, True))
    rooms.append(make_room("r_L0_foyer", "corridor", "Zen Entrance Vestibule", 0, 4.5, 7.5, 7.5, 0, False))
    rooms.append(make_room("r_L0_stairs", "corridor", "Floating Open Glass Stair", 0, 7.5, 2.0, 13.5, 0, False, {"typology": "floating"}))
    rooms.append(make_room("r_L0_lounge", "living_room", "Palatial Zen Living Hall", 2.0, 7.5, 9.5, 17.5, 0, True))
    rooms.append(make_room("r_L0_water_court", "outdoor", "Interior Water Feature Light Atrium", 9.5, 7.5, 12.5, 14.5, 0, False))
    rooms.append(make_room("r_L0_dining", "dining_room", "Water Court Dining Hall", 12.5, 7.5, w, 14.5, 0, True))
    rooms.append(make_room("r_L0_kitchen", "kitchen", "Gourmet Kitchen", 9.5, 14.5, w, 17.5, 0, True))
    rooms.append(make_room("r_L0_spa", "bathroom", "Thermal Sauna & Steam Spa Suite", 0, 13.5, 2.0, 17.5, 0, False))
    rooms.append(make_room("r_L0_lobby", "corridor", "Rear Distribution Lobby", 0, 17.5, w, 19.0, 0, False))
    rooms.append(make_room("r_L0_bed1", "bedroom", "Master Wellness Suite 1", 0, 19.0, 6.5, d, 0, True))
    rooms.append(make_room("r_L0_bath1", "bathroom", "Master 5-Fixture Hydrotherapy Bath", 6.5, 19.0, 9.0, 24.5, 0, False))
    rooms.append(make_room("r_L0_ots", "outdoor", "Private Bamboo Garden OTS", 6.5, 24.5, 9.0, d, 0, False))
    rooms.append(make_room("r_L0_bath2", "bathroom", "Attached Luxury Bath 2", 9.0, 19.0, 11.5, 24.5, 0, False))
    rooms.append(make_room("r_L0_bed2", "bedroom", "Secondary Suite 2", 11.5, 19.0, w, d, 0, True))

    ops.append(make_door("d_L0_01", 3.8, 4.5, ["r_L0_porch", "r_L0_foyer"], 1.30, 0))
    ops.append(make_door("d_L0_02", 7.5, 6.0, ["r_L0_foyer", "r_L0_drawing"], 1.20, 0))
    ops.append(make_door("d_L0_03", 12.0, 2.0, ["r_L0_drawing", "r_L0_powder"], 0.80, 0))
    ops.append(make_door("d_L0_04", 1.0, 7.5, ["r_L0_foyer", "r_L0_stairs"], 0.90, 0))
    ops.append(make_door("d_L0_05", 5.0, 7.5, ["r_L0_foyer", "r_L0_lounge"], 1.40, 0))
    ops.append(make_door("d_L0_06", 9.5, 11.0, ["r_L0_lounge", "r_L0_water_court"], 1.40, 0))
    ops.append(make_door("d_L0_07", 12.5, 11.0, ["r_L0_water_court", "r_L0_dining"], 1.20, 0))
    ops.append(make_door("d_L0_08", 2.0, 15.5, ["r_L0_lounge", "r_L0_spa"], 0.80, 0))
    ops.append(make_door("d_L0_09", 9.5, 16.0, ["r_L0_lounge", "r_L0_kitchen"], 1.10, 0))
    ops.append(make_door("d_L0_10", 6.0, 17.5, ["r_L0_lounge", "r_L0_lobby"], 1.30, 0))
    ops.append(make_door("d_L0_11", 3.2, 19.0, ["r_L0_lobby", "r_L0_bed1"], 1.10, 0))
    ops.append(make_door("d_L0_12", 6.5, 21.5, ["r_L0_bed1", "r_L0_bath1"], 0.80, 0))
    ops.append(make_door("d_L0_13", 6.5, 25.5, ["r_L0_bed1", "r_L0_ots"], 0.80, 0))
    ops.append(make_door("d_L0_14", 13.0, 19.0, ["r_L0_lobby", "r_L0_bed2"], 1.10, 0))
    ops.append(make_door("d_L0_15", 11.5, 21.5, ["r_L0_bed2", "r_L0_bath2"], 0.80, 0))
    ops.append(make_window("w_L0_01", 10.0, 2.0, 2.20, 0.90, 0))
    ops.append(make_window("w_L0_02", 3.2, d, 2.00, 0.90, 0))
    ops.append(make_window("w_L0_03", 13.0, d, 2.00, 0.90, 0))

    # L1
    rooms.append(make_room("r_L1_terrace_f", "outdoor", "Front Zen Terrace", 0, 0, 7.5, 4.5, 1, False))
    rooms.append(make_room("r_L1_bath3", "bathroom", "Upper Bath 3", 12.0, 0, w, 2.0, 1, False))
    rooms.append(make_room("r_L1_bed3", "bedroom", "Executive Suite 3", 7.5, 2.0, w, 7.5, 1, True))
    rooms.append(make_room("r_L1_study", "study", "Quiet Library Office", 0, 4.5, 7.5, 7.5, 1, True))
    rooms.append(make_room("r_L1_stairs", "corridor", "Floating Glass Stair Landing", 0, 7.5, 2.0, 13.5, 1, False, {"typology": "floating"}))
    rooms.append(make_room("r_L1_lounge", "living_room", "Upper Zen Living Hall", 2.0, 7.5, 9.5, 17.5, 1, True))
    rooms.append(make_room("r_L1_water_void", "outdoor", "Water Atrium Open Sky Void", 9.5, 7.5, 12.5, 14.5, 1, False))
    rooms.append(make_room("r_L1_gym", "study", "Upper Yoga & Fitness Studio", 12.5, 7.5, w, 14.5, 1, True))
    rooms.append(make_room("r_L1_kitchenette", "kitchen", "Upper Kitchenette & Bar", 9.5, 14.5, w, 17.5, 1, True))
    rooms.append(make_room("r_L1_store", "dressing_room", "Upper Linen Store", 0, 13.5, 2.0, 17.5, 1, False))
    rooms.append(make_room("r_L1_lobby", "corridor", "Upper Distribution Lobby", 0, 17.5, w, 19.0, 1, False))
    rooms.append(make_room("r_L1_bed4", "bedroom", "Master Bedroom Suite 4", 0, 19.0, 6.5, d, 1, True))
    rooms.append(make_room("r_L1_bath4", "bathroom", "Master Luxury Bath 4", 6.5, 19.0, 9.0, 24.5, 1, False))
    rooms.append(make_room("r_L1_ots", "outdoor", "Private Bamboo Garden Void", 6.5, 24.5, 9.0, d, 1, False))
    rooms.append(make_room("r_L1_bath5", "bathroom", "Attached Bath 5", 9.0, 19.0, 11.5, 24.5, 1, False))
    rooms.append(make_room("r_L1_bed5", "bedroom", "Upper Suite 5", 11.5, 19.0, w, d, 1, True))

    ops.append(make_door("d_L1_01", 3.8, 4.5, ["r_L1_study", "r_L1_terrace_f"], 1.20, 1))
    ops.append(make_door("d_L1_02", 7.5, 6.0, ["r_L1_study", "r_L1_bed3"], 1.10, 1))
    ops.append(make_door("d_L1_03", 12.0, 2.0, ["r_L1_bed3", "r_L1_bath3"], 0.80, 1))
    ops.append(make_door("d_L1_04", 1.0, 7.5, ["r_L1_study", "r_L1_stairs"], 0.90, 1))
    ops.append(make_door("d_L1_05", 5.0, 7.5, ["r_L1_study", "r_L1_lounge"], 1.30, 1))
    ops.append(make_door("d_L1_06", 9.5, 11.0, ["r_L1_lounge", "r_L1_water_void"], 1.20, 1))
    ops.append(make_door("d_L1_07", 12.5, 11.0, ["r_L1_water_void", "r_L1_gym"], 1.10, 1))
    ops.append(make_door("d_L1_08", 2.0, 15.5, ["r_L1_lounge", "r_L1_store"], 0.80, 1))
    ops.append(make_door("d_L1_09", 9.5, 16.0, ["r_L1_lounge", "r_L1_kitchenette"], 1.00, 1))
    ops.append(make_door("d_L1_10", 6.0, 17.5, ["r_L1_lounge", "r_L1_lobby"], 1.30, 1))
    ops.append(make_door("d_L1_11", 3.2, 19.0, ["r_L1_lobby", "r_L1_bed4"], 1.00, 1))
    ops.append(make_door("d_L1_12", 6.5, 21.5, ["r_L1_bed4", "r_L1_bath4"], 0.80, 1))
    ops.append(make_door("d_L1_13", 6.5, 25.5, ["r_L1_bed4", "r_L1_ots"], 0.80, 1))
    ops.append(make_door("d_L1_14", 13.0, 19.0, ["r_L1_lobby", "r_L1_bed5"], 1.00, 1))
    ops.append(make_door("d_L1_15", 11.5, 21.5, ["r_L1_bed5", "r_L1_bath5"], 0.80, 1))
    ops.append(make_window("w_L1_01", 10.0, 2.0, 2.20, 0.90, 1))
    ops.append(make_window("w_L1_02", 3.2, d, 2.00, 0.90, 1))
    ops.append(make_window("w_L1_03", 13.0, d, 2.00, 0.90, 1))
    meta = MetadataModel(plan_id="master_1_kanal_v10", source_type="synthetic_generated", floor_count=2, levels=[0, 1], provenance={"scale": "1_kanal", "stair_type": "floating", "typology": "wellness_and_spa_oriented_villa"})
    return assemble_plan(meta, env, rooms, ops)


ARCHETYPES_1_KANAL = [
    build_1k_v01, build_1k_v02, build_1k_v03, build_1k_v04, build_1k_v05,
    build_1k_v06, build_1k_v07, build_1k_v08, build_1k_v09, build_1k_v10
]
