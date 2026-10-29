"""
Architectural Archetype Builders for 20 Benchmark Plans.
Part 1: Batch A (3 Marla) & Batch B (5 Marla).
"""

from typing import List, Dict, Any
from dataset.schema.canonical import CanonicalFloorPlan
from benchmark.test_and_perfect_20 import (
    FT, make_room, make_door, make_window, assemble_plan
)

# ===========================================================================
# BATCH A: 3 MARLA (Plots: 20ft x 33.75ft = 6.10m x 10.29m / 18ft x 37.5ft = 5.49m x 11.43m)
# Zero Side Setback, 3ft Rear OTS (0.91m)
# ===========================================================================

def build_3m_d1_central_courtyard() -> CanonicalFloorPlan:
    """3M-D1: Compact single car porch; entry past internal 5x5ft OTS glass courtyard; open kitchen-dining-lounge; rear master suite."""
    W = 6.10
    D = 10.29
    y_ots = 9.38

    rooms = [
        make_room("room_L0_porch", "parking", "Compact Car Porch", 0.0, 0.0, 3.20, 3.80, hab=False),
        make_room("room_L0_foyer", "foyer", "Entrance Foyer", 3.20, 0.0, 6.10, 2.00, hab=True),
        make_room("room_L0_courtyard", "outdoor", "5ft x 5ft OTS Glass Courtyard", 3.20, 2.00, 4.70, 3.80, hab=False),
        make_room("room_L0_powder", "bathroom", "Guest Powder Room", 4.70, 2.00, 6.10, 3.80, hab=False),

        make_room("room_L0_stairs", "corridor", "Lateral Floating Stair", 0.0, 3.80, 0.95, 6.80, hab=False, meta={"typology": "floating", "headroom_m": 2.20, "lateral": True}),
        make_room("room_L0_kitchen", "kitchen", "Gourmet Show Kitchen", 0.95, 3.80, 3.20, 6.80, hab=True, meta={"open_concept": True, "waterfall_island": True}),
        make_room("room_L0_lounge", "living_room", "Open TV Lounge & Dining", 3.20, 3.80, 6.10, 6.80, hab=True, meta={"open_concept": True}),

        make_room("room_L0_master_bed", "bedroom", "Master Bedroom Suite", 0.0, 6.80, 4.00, y_ots, hab=True, meta={"master": True, "garden_view": True}),
        make_room("room_L0_master_bath", "bathroom", "Ensuite Master Bath", 4.00, 6.80, 6.10, y_ots, hab=False),
        make_room("room_L0_ots_rear", "outdoor", "3ft Rear OTS Green Court", 0.0, y_ots, 6.10, D, hab=False),
    ]

    openings = [
        make_door("d_porch_foyer", 3.20, 1.00, ["room_L0_porch", "room_L0_foyer"], 1.05),
        make_door("d_foyer_powder", 5.40, 2.00, ["room_L0_foyer", "room_L0_powder"], 0.75),
        make_door("d_foyer_lounge", 3.90, 2.00, ["room_L0_foyer", "room_L0_lounge"], 1.10),
        make_door("d_lounge_bed", 3.60, 6.80, ["room_L0_lounge", "room_L0_master_bed"], 0.95),
        make_door("d_bed_bath", 4.00, 7.80, ["room_L0_master_bed", "room_L0_master_bath"], 0.85),
        make_door("d_bed_ots", 1.80, y_ots, ["room_L0_master_bed", "room_L0_ots_rear"], 1.40, is_pocket=True),
        make_door("d_bath_ots", 5.00, y_ots, ["room_L0_master_bath", "room_L0_ots_rear"], 0.75),

        make_window("w_front_foyer", 4.60, 0.0, 1.40),
        make_window("w_court_lounge", 3.95, 3.80, 1.20)
    ]

    return assemble_plan("3M-D1", "3M-D1 (Central Courtyard)", W, D, rooms, openings)


def build_3m_d2_split_level_studio() -> CanonicalFloorPlan:
    """3M-D2: Sunken car porch & powder; elevated Great Room triad; lateral single-flight floating stair; rear bedroom & bath."""
    W = 5.49
    D = 11.43
    y_ots = 10.52

    rooms = [
        make_room("room_L0_porch", "parking", "Sunken Car Porch", 0.0, 0.0, 3.20, 4.00, hab=False),
        make_room("room_L0_powder", "bathroom", "Screened Powder Room", 3.20, 0.0, 5.49, 1.80, hab=False),
        make_room("room_L0_foyer", "foyer", "Entrance Landing Foyer", 3.20, 1.80, 5.49, 4.00, hab=True),

        make_room("room_L0_stairs", "corridor", "Lateral Single-Flight Floating Stair", 0.0, 4.00, 0.95, 7.20, hab=False, meta={"typology": "floating", "headroom_m": 2.20, "lateral": True}),
        make_room("room_L0_kitchen", "kitchen", "Gourmet Studio Kitchen", 0.95, 4.00, 2.50, 7.20, hab=True, meta={"open_concept": True, "waterfall_island": True}),
        make_room("room_L0_lounge", "living_room", "Elevated Great Lounge & Dining", 2.50, 4.00, 5.49, 7.20, hab=True, meta={"open_concept": True}),

        make_room("room_L0_master_bed", "bedroom", "Rear Bedroom Suite", 0.0, 7.20, 3.50, y_ots, hab=True, meta={"master": True, "garden_view": True}),
        make_room("room_L0_master_bath", "bathroom", "Attached Luxury Bath", 3.50, 7.20, 5.49, y_ots, hab=False),
        make_room("room_L0_ots_rear", "outdoor", "3ft Rear OTS Lightwell", 0.0, y_ots, 5.49, D, hab=False),
    ]

    openings = [
        make_door("d_porch_foyer", 3.20, 2.80, ["room_L0_porch", "room_L0_foyer"], 1.05),
        make_door("d_foyer_powder", 4.30, 1.80, ["room_L0_foyer", "room_L0_powder"], 0.75),
        make_door("d_foyer_lounge", 4.00, 4.00, ["room_L0_foyer", "room_L0_lounge"], 1.10),
        make_door("d_lounge_bed", 3.00, 7.20, ["room_L0_lounge", "room_L0_master_bed"], 0.95),
        make_door("d_bed_bath", 3.50, 8.50, ["room_L0_master_bed", "room_L0_master_bath"], 0.85),
        make_door("d_bed_ots", 1.60, y_ots, ["room_L0_master_bed", "room_L0_ots_rear"], 1.30, is_pocket=True),
        make_door("d_bath_ots", 4.50, y_ots, ["room_L0_master_bath", "room_L0_ots_rear"], 0.75),

        make_window("w_front_powder", 4.30, 0.0, 0.80),
        make_window("w_lounge_side", 5.49, 5.60, 1.40)
    ]

    return assemble_plan("3M-D2", "3M-D2 (Split-Level Open Studio)", W, D, rooms, openings)


def build_3m_d3_rear_lightwell_loft() -> CanonicalFloorPlan:
    """3M-D3: Linear living-dining on left, kitchen island on right; full-width rear master suite opening onto 3ft rear green court."""
    W = 6.10
    D = 10.29
    y_ots = 9.38

    rooms = [
        make_room("room_L0_porch", "parking", "Compact Front Porch", 0.0, 0.0, 3.20, 3.80, hab=False),
        make_room("room_L0_powder", "bathroom", "Front Powder Room", 3.20, 0.0, 4.60, 1.80, hab=False),
        make_room("room_L0_foyer", "foyer", "Entrance Foyer", 4.60, 0.0, 6.10, 3.80, hab=True),
        make_room("room_L0_foyer_alcove", "foyer", "Screened Foyer Alcove", 3.20, 1.80, 4.60, 3.80, hab=False),

        make_room("room_L0_stairs", "corridor", "Lateral Cantilevered Stair", 0.0, 3.80, 0.95, 6.80, hab=False, meta={"typology": "floating", "headroom_m": 2.20, "lateral": True}),
        make_room("room_L0_lounge", "living_room", "Linear Living & Dining", 0.95, 3.80, 3.80, 6.80, hab=True, meta={"open_concept": True}),
        make_room("room_L0_kitchen", "kitchen", "Gourmet Kitchen Island Suite", 3.80, 3.80, 6.10, 6.80, hab=True, meta={"open_concept": True, "waterfall_island": True}),

        make_room("room_L0_master_bed", "bedroom", "Full-Width Master Suite", 0.0, 6.80, 4.10, y_ots, hab=True, meta={"master": True, "garden_view": True}),
        make_room("room_L0_master_bath", "bathroom", "Designer Ensuite Bath", 4.10, 6.80, 6.10, y_ots, hab=False),
        make_room("room_L0_ots_rear", "outdoor", "3ft Rear Green Court", 0.0, y_ots, 6.10, D, hab=False),
    ]

    openings = [
        make_door("d_porch_foyer", 4.60, 0.90, ["room_L0_porch", "room_L0_foyer"], 1.05),
        make_door("d_foyer_alcove", 4.60, 2.80, ["room_L0_foyer", "room_L0_foyer_alcove"], 0.90),
        make_door("d_alcove_powder", 3.90, 1.80, ["room_L0_foyer_alcove", "room_L0_powder"], 0.75),
        make_door("d_foyer_kitchen", 5.20, 3.80, ["room_L0_foyer", "room_L0_kitchen"], 1.10),
        make_door("d_lounge_bed", 2.20, 6.80, ["room_L0_lounge", "room_L0_master_bed"], 0.95),
        make_door("d_bed_bath", 4.10, 7.80, ["room_L0_master_bed", "room_L0_master_bath"], 0.85),
        make_door("d_bed_ots", 1.80, y_ots, ["room_L0_master_bed", "room_L0_ots_rear"], 1.60, is_pocket=True),
        make_door("d_bath_ots", 5.10, y_ots, ["room_L0_master_bath", "room_L0_ots_rear"], 0.75),

        make_window("w_front_powder", 3.90, 0.0, 0.80),
        make_window("w_front_foyer", 5.35, 0.0, 1.20)
    ]

    return assemble_plan("3M-D3", "3M-D3 (Rear-Lightwell Loft)", W, D, rooms, openings)


def build_3m_d4_wide_frontage() -> CanonicalFloorPlan:
    """3M-D4: Front drawing alcove with sliding wood screen; open central TV lounge and L-kitchen; rear corner bedroom and bath sharing OTS."""
    W = 6.10
    D = 10.29
    y_ots = 9.38

    rooms = [
        make_room("room_L0_porch", "parking", "Compact Front Porch", 0.0, 0.0, 2.90, 3.80, hab=False),
        make_room("room_L0_drawing", "living_room", "Front Drawing Alcove", 2.90, 0.0, 6.10, 3.80, hab=True, meta={"drawing_room": True}),

        make_room("room_L0_stairs", "corridor", "Lateral Floating Stair", 0.0, 3.80, 0.95, 6.80, hab=False, meta={"typology": "floating", "headroom_m": 2.20, "lateral": True}),
        make_room("room_L0_lounge", "living_room", "Open Central TV Lounge", 0.95, 3.80, 3.80, 6.80, hab=True, meta={"open_concept": True}),
        make_room("room_L0_kitchen", "kitchen", "Gourmet L-Kitchen & Dining", 3.80, 3.80, 6.10, 6.80, hab=True, meta={"open_concept": True, "waterfall_island": True}),

        make_room("room_L0_master_bed", "bedroom", "Rear Corner Master Suite", 0.0, 6.80, 3.90, y_ots, hab=True, meta={"master": True, "garden_view": True}),
        make_room("room_L0_master_bath", "bathroom", "Corner Attached Bath", 3.90, 6.80, 6.10, 8.50, hab=False),
        make_room("room_L0_ots_rear", "outdoor", "Shared OTS Shaft & Lightwell", 3.90, 8.50, 6.10, D, hab=False),
        make_room("room_L0_ots_patio", "outdoor", "Master Garden Patio", 0.0, y_ots, 3.90, D, hab=False),
    ]

    openings = [
        make_door("d_draw_a_entry", 2.90, 1.20, ["room_L0_porch", "room_L0_drawing"], 1.05),
        make_door("d_draw_b_sliding", 4.20, 3.80, ["room_L0_drawing", "room_L0_kitchen"], 1.50, is_pocket=True),
        make_door("d_porch_lounge", 1.80, 3.80, ["room_L0_porch", "room_L0_lounge"], 1.00),
        make_door("d_lounge_bed", 2.20, 6.80, ["room_L0_lounge", "room_L0_master_bed"], 0.95),
        make_door("d_bed_bath", 3.90, 7.60, ["room_L0_master_bed", "room_L0_master_bath"], 0.85),
        make_door("d_bed_patio", 1.80, y_ots, ["room_L0_master_bed", "room_L0_ots_patio"], 1.40, is_pocket=True),
        make_door("d_bath_ots", 5.00, 8.50, ["room_L0_master_bath", "room_L0_ots_rear"], 0.75),

        make_window("w_front_drawing", 4.50, 0.0, 1.60),
        make_window("w_ots_patio", 1.95, y_ots, 1.20)
    ]

    return assemble_plan("3M-D4", "3M-D4 (Wide-Frontage Urban Plan)", W, D, rooms, openings)


# ===========================================================================
# BATCH B: 5 MARLA (25ft x 45ft = 7.62m x 13.72m)
# 5ft Front, 3ft Rear Setback, Zero Side Setback
# ===========================================================================

def build_5m_d1_linear_great_room() -> CanonicalFloorPlan:
    """5M-D1: 14ft x 13.5ft porch; foyer with powder; dual-access drawing room; open dining and TV lounge with 8ft island; rear master suite."""
    W = 7.62
    D = 13.72
    y_rear = 12.81

    rooms = [
        make_room("room_L0_porch", "parking", "Spacious Car Porch", 0.0, 0.0, 4.20, 4.80, hab=False),
        make_room("room_L0_foyer", "foyer", "Grand Entrance Foyer", 4.20, 0.0, 5.70, 2.20, hab=True),
        make_room("room_L0_powder", "bathroom", "Screened Powder Room", 4.20, 2.20, 5.70, 3.60, hab=False),
        make_room("room_L0_drawing", "living_room", "Formal Drawing Room", 5.70, 0.0, 7.62, 4.80, hab=True, meta={"drawing_room": True}),

        make_room("room_L0_stairs", "corridor", "Lateral Floating Staircase", 0.0, 4.80, 1.05, 8.20, hab=False, meta={"typology": "floating", "headroom_m": 2.20, "lateral": True}),
        make_room("room_L0_lounge", "living_room", "Open TV Lounge", 1.05, 4.80, 4.50, 8.80, hab=True, meta={"open_concept": True}),
        make_room("room_L0_dining", "dining_room", "Family Dining Space", 4.50, 4.80, 7.62, 6.80, hab=True, meta={"open_concept": True}),
        make_room("room_L0_kitchen", "kitchen", "Gourmet Show Kitchen & 8ft Island", 4.50, 6.80, 7.62, 8.80, hab=True, meta={"open_concept": True, "waterfall_island": True}),

        make_room("room_L0_master_bed", "bedroom", "Master Bedroom Suite", 0.0, 8.80, 4.60, y_rear, hab=True, meta={"master": True, "garden_view": True}),
        make_room("room_L0_dressing", "closet", "Walk-in Dressing Room", 4.60, 8.80, 6.00, 10.60, hab=False),
        make_room("room_L0_master_bath", "bathroom", "5-Fixture Luxury Ensuite Bath", 4.60, 10.60, 6.00, y_rear, hab=False),
        make_room("room_L0_guest_bed", "bedroom", "Secondary Bedroom", 6.00, 8.80, 7.62, y_rear, hab=True),
        make_room("room_L0_rear_lawn", "outdoor", "3ft Rear Landscaped Lawn", 0.0, y_rear, 7.62, D, hab=False),
    ]

    openings = [
        make_door("d_porch_foyer", 4.20, 1.10, ["room_L0_porch", "room_L0_foyer"], 1.10),
        make_door("d_foyer_powder", 4.95, 2.20, ["room_L0_foyer", "room_L0_powder"], 0.75),
        make_door("d_draw_a_foyer", 5.70, 1.10, ["room_L0_foyer", "room_L0_drawing"], 1.07),
        make_door("d_draw_b_dining", 6.60, 4.80, ["room_L0_drawing", "room_L0_dining"], 1.52, is_pocket=True),
        make_door("d_foyer_dining", 4.80, 2.20, ["room_L0_foyer", "room_L0_dining"], 1.10),
        make_door("d_lounge_master", 2.20, 8.80, ["room_L0_lounge", "room_L0_master_bed"], 0.95),
        make_door("d_bed_dressing", 4.60, 9.60, ["room_L0_master_bed", "room_L0_dressing"], 0.85),
        make_door("d_bed_bath", 4.60, 11.40, ["room_L0_master_bed", "room_L0_master_bath"], 0.85),
        make_door("d_kitchen_guest", 6.80, 8.80, ["room_L0_kitchen", "room_L0_guest_bed"], 0.90),
        make_door("d_master_lawn", 2.00, y_rear, ["room_L0_master_bed", "room_L0_rear_lawn"], 1.60, is_pocket=True),
        make_door("d_guest_lawn", 6.80, y_rear, ["room_L0_guest_bed", "room_L0_rear_lawn"], 0.90),

        make_window("w_front_draw", 6.65, 0.0, 1.60),
        make_window("w_front_foyer", 4.95, 0.0, 1.20)
    ]

    return assemble_plan("5M-D1", "5M-D1 (Linear Open Great Room)", W, D, rooms, openings)


def build_5m_d2_side_light_court() -> CanonicalFloorPlan:
    """5M-D2: Foyer opens to dining adjacent to 4ft x 10ft side glass courtyard; central TV lounge; side kitchen; rear master suite."""
    W = 7.62
    D = 13.72
    y_rear = 12.81

    rooms = [
        make_room("room_L0_porch", "parking", "Covered Car Porch", 0.0, 0.0, 4.00, 4.80, hab=False),
        make_room("room_L0_foyer", "foyer", "Entrance Foyer", 4.00, 0.0, 5.40, 2.20, hab=True),
        make_room("room_L0_powder", "bathroom", "Screened Powder Room", 4.00, 2.20, 5.40, 3.60, hab=False),
        make_room("room_L0_drawing", "living_room", "Formal Guest Drawing Room", 5.40, 0.0, 7.62, 4.80, hab=True, meta={"drawing_room": True}),

        make_room("room_L0_courtyard", "outdoor", "4ft x 10ft Side Glass Courtyard", 0.0, 4.80, 1.22, 7.85, hab=False),
        make_room("room_L0_stairs", "corridor", "Lateral Cantilevered Stair", 0.0, 7.85, 1.05, 10.50, hab=False, meta={"typology": "floating", "headroom_m": 2.20, "lateral": True}),
        make_room("room_L0_dining", "dining_room", "Glass Court Dining Space", 1.22, 4.80, 4.60, 7.50, hab=True, meta={"open_concept": True}),
        make_room("room_L0_kitchen", "kitchen", "Side Show Kitchen & Island", 4.60, 4.80, 7.62, 7.50, hab=True, meta={"open_concept": True, "waterfall_island": True}),
        make_room("room_L0_lounge", "living_room", "Central TV Lounge", 1.05, 7.50, 7.62, 9.80, hab=True, meta={"open_concept": True}),

        make_room("room_L0_master_bed", "bedroom", "Rear Master Suite", 0.0, 10.50, 4.80, y_rear, hab=True, meta={"master": True, "garden_view": True}),
        make_room("room_L0_master_bath", "bathroom", "Attached Luxury Ensuite", 4.80, 9.80, 7.62, y_rear, hab=False),
        make_room("room_L0_rear_lawn", "outdoor", "3ft Rear Green Setback", 0.0, y_rear, 7.62, D, hab=False),
    ]

    openings = [
        make_door("d_porch_foyer", 4.00, 1.10, ["room_L0_porch", "room_L0_foyer"], 1.10),
        make_door("d_foyer_powder", 4.70, 2.20, ["room_L0_foyer", "room_L0_powder"], 0.75),
        make_door("d_draw_a_foyer", 5.40, 1.10, ["room_L0_foyer", "room_L0_drawing"], 1.07),
        make_door("d_draw_b_kitchen", 6.20, 4.80, ["room_L0_drawing", "room_L0_kitchen"], 1.52, is_pocket=True),
        make_door("d_foyer_dining", 4.60, 2.20, ["room_L0_foyer", "room_L0_dining"], 1.10),
        make_door("d_lounge_master", 2.40, 10.50, ["room_L0_lounge", "room_L0_master_bed"], 0.95),
        make_door("d_bed_bath", 4.80, 11.20, ["room_L0_master_bed", "room_L0_master_bath"], 0.85),
        make_door("d_master_patio", 2.20, y_rear, ["room_L0_master_bed", "room_L0_rear_lawn"], 1.60, is_pocket=True),

        make_window("w_front_draw", 6.50, 0.0, 1.60),
        make_window("w_court_dining", 1.22, 6.10, 2.00)
    ]

    return assemble_plan("5M-D2", "5M-D2 (Side-Light Court House)", W, D, rooms, openings)


def build_5m_d3_symmetrical_duplex() -> CanonicalFloorPlan:
    """5M-D3: Central front foyer flanked by car porch (left) and drawing (right); central open hall with floating stair; rear master & guest."""
    W = 7.62
    D = 13.72
    y_rear = 12.81

    rooms = [
        make_room("room_L0_porch", "parking", "Flank Car Porch", 0.0, 0.0, 3.40, 4.80, hab=False),
        make_room("room_L0_foyer", "foyer", "Central Entrance Foyer", 3.40, 0.0, 4.60, 3.20, hab=True),
        make_room("room_L0_powder", "bathroom", "Screened Powder Room", 3.40, 3.20, 4.60, 4.80, hab=False),
        make_room("room_L0_drawing", "living_room", "Flank Formal Drawing Salon", 4.60, 0.0, 7.62, 4.80, hab=True, meta={"drawing_room": True}),

        make_room("room_L0_stairs", "corridor", "Lateral Floating Staircase", 0.0, 4.80, 1.05, 8.00, hab=False, meta={"typology": "floating", "headroom_m": 2.20, "lateral": True}),
        make_room("room_L0_lounge", "living_room", "Central Open Living Hall", 1.05, 4.80, 4.60, 8.80, hab=True, meta={"open_concept": True}),
        make_room("room_L0_dining", "dining_room", "Open Dining Space", 4.60, 4.80, 7.62, 6.80, hab=True, meta={"open_concept": True}),
        make_room("room_L0_kitchen", "kitchen", "Gourmet Show Kitchen & Island", 4.60, 6.80, 7.62, 8.80, hab=True, meta={"open_concept": True, "waterfall_island": True}),

        make_room("room_L0_master_bed", "bedroom", "Rear Master Suite", 0.0, 8.80, 4.50, y_rear, hab=True, meta={"master": True, "garden_view": True}),
        make_room("room_L0_duct_bath", "bathroom", "Master Ensuite Bath", 4.50, 8.80, 5.80, 10.80, hab=False),
        make_room("room_L0_duct_ots", "outdoor", "Central Ventilation Duct", 4.50, 10.80, 5.80, y_rear, hab=False),
        make_room("room_L0_guest_bed", "bedroom", "Corner Guest Bedroom", 5.80, 8.80, 7.62, y_rear, hab=True),
        make_room("room_L0_rear_lawn", "outdoor", "3ft Rear Landscaped Court", 0.0, y_rear, 7.62, D, hab=False),
    ]

    openings = [
        make_door("d_porch_foyer", 3.40, 1.60, ["room_L0_porch", "room_L0_foyer"], 1.10),
        make_door("d_foyer_powder", 4.00, 3.20, ["room_L0_foyer", "room_L0_powder"], 0.75),
        make_door("d_draw_a_foyer", 4.60, 1.60, ["room_L0_foyer", "room_L0_drawing"], 1.07),
        make_door("d_draw_b_dining", 6.00, 4.80, ["room_L0_drawing", "room_L0_dining"], 1.52, is_pocket=True),
        make_door("d_foyer_lounge", 4.00, 3.20, ["room_L0_foyer", "room_L0_lounge"], 1.10),
        make_door("d_lounge_master", 2.20, 8.80, ["room_L0_lounge", "room_L0_master_bed"], 0.95),
        make_door("d_bed_bath", 4.50, 9.60, ["room_L0_master_bed", "room_L0_duct_bath"], 0.85),
        make_door("d_kitchen_guest", 6.70, 8.80, ["room_L0_kitchen", "room_L0_guest_bed"], 0.90),
        make_door("d_master_lawn", 2.20, y_rear, ["room_L0_master_bed", "room_L0_rear_lawn"], 1.50, is_pocket=True),

        make_window("w_front_draw", 6.10, 0.0, 1.50),
        make_window("w_front_foyer", 4.00, 0.0, 1.00)
    ]

    return assemble_plan("5M-D3", "5M-D3 (Symmetrical Duplex Executive)", W, D, rooms, openings)


def build_5m_d4_cantilevered_stair() -> CanonicalFloorPlan:
    """5M-D4: Front porch & drawing; open TV lounge and dining around lateral cantilevered stair with glass balustrade; open kitchen island; rear master."""
    W = 7.62
    D = 13.72
    y_rear = 12.81

    rooms = [
        make_room("room_L0_porch", "parking", "Front Car Porch", 0.0, 0.0, 3.80, 4.80, hab=False),
        make_room("room_L0_foyer", "foyer", "Modern Entrance Foyer", 3.80, 0.0, 5.00, 2.20, hab=True),
        make_room("room_L0_powder", "bathroom", "Screened Powder Room", 3.80, 2.20, 5.00, 3.80, hab=False),
        make_room("room_L0_drawing", "living_room", "Front Modern Drawing Room", 5.00, 0.0, 7.62, 4.80, hab=True, meta={"drawing_room": True}),

        make_room("room_L0_stairs", "corridor", "Lateral Cantilevered Stair", 0.0, 4.80, 1.05, 8.20, hab=False, meta={"typology": "floating", "headroom_m": 2.20, "lateral": True}),
        make_room("room_L0_lounge", "living_room", "Open TV Lounge", 1.05, 4.80, 4.80, 8.80, hab=True, meta={"open_concept": True}),
        make_room("room_L0_dining", "dining_room", "Open Dining Room", 4.80, 4.80, 7.62, 6.80, hab=True, meta={"open_concept": True}),
        make_room("room_L0_kitchen", "kitchen", "Open Kitchen & Island Counter", 4.80, 6.80, 7.62, 8.80, hab=True, meta={"open_concept": True, "waterfall_island": True}),

        make_room("room_L0_master_bed", "bedroom", "Executive Rear Master Suite", 0.0, 8.80, 4.80, y_rear, hab=True, meta={"master": True, "garden_view": True}),
        make_room("room_L0_dressing", "closet", "Master Walk-in Closet", 4.80, 8.80, 6.20, 10.60, hab=False),
        make_room("room_L0_master_bath", "bathroom", "Ensuite Master Spa Bath", 4.80, 10.60, 6.20, y_rear, hab=False),
        make_room("room_L0_sec_bed", "bedroom", "Secondary Bedroom", 6.20, 8.80, 7.62, y_rear, hab=True),
        make_room("room_L0_rear_lawn", "outdoor", "3ft Rear Landscaped Yard", 0.0, y_rear, 7.62, D, hab=False),
    ]

    openings = [
        make_door("d_porch_foyer", 3.80, 1.10, ["room_L0_porch", "room_L0_foyer"], 1.10),
        make_door("d_foyer_powder", 4.40, 2.20, ["room_L0_foyer", "room_L0_powder"], 0.75),
        make_door("d_draw_a_foyer", 5.00, 1.10, ["room_L0_foyer", "room_L0_drawing"], 1.07),
        make_door("d_draw_b_dining", 6.30, 4.80, ["room_L0_drawing", "room_L0_dining"], 1.52, is_pocket=True),
        make_door("d_foyer_dining", 4.40, 2.20, ["room_L0_foyer", "room_L0_dining"], 1.10),
        make_door("d_lounge_master", 2.40, 8.80, ["room_L0_lounge", "room_L0_master_bed"], 0.95),
        make_door("d_bed_dressing", 4.80, 9.60, ["room_L0_master_bed", "room_L0_dressing"], 0.85),
        make_door("d_bed_bath", 4.80, 11.40, ["room_L0_master_bed", "room_L0_master_bath"], 0.85),
        make_door("d_kitchen_sec", 6.90, 8.80, ["room_L0_kitchen", "room_L0_sec_bed"], 0.90),
        make_door("d_master_lawn", 2.20, y_rear, ["room_L0_master_bed", "room_L0_rear_lawn"], 1.50, is_pocket=True),

        make_window("w_front_draw", 6.30, 0.0, 1.60),
        make_window("w_front_foyer", 4.40, 0.0, 1.00)
    ]

    return assemble_plan("5M-D4", "5M-D4 (Cantilevered Stair Modern)", W, D, rooms, openings)
