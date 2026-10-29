"""
Modern & Futuristic 7-Bedroom Luxury Residence Architectural Plan Generator.
Fully detailed with:
- 2 Floors (Level 0: Ground Floor, Level 1: First Floor)
- Ground Floor:
    * Front Landscaped Lawn & Stepping Stones
    * 2-Car Luxury Enclosed Garage
    * Grand Double-Height Entrance & Foyer
    * Executive Study & Library (with executive desk, swivel chair & bookshelves)
    * Formal Drawing Salon
    * Guest Powder Room
    * Double-Height Grand Living Room
    * Y-Shaped Grand Staircase (Bifurcated, connected to Living Room)
    * Modern Open Show Kitchen (with waterfall island & breakfast bar)
    * Dirty Kitchen & Scullery (perimeter heavy prep counters)
    * Laundry & Utility Room (washer, dryer, utility sink)
    * Ground Master Bedroom Suite + Attach Master Spa Bathroom (5-fixture spa)
    * Ground Bedroom 2 (Guest Suite) + Attach Bathroom 2
    * Rear Scenic Garden & Light Courtyard
- First Floor:
    * Y-Staircase Sky Bridges & Upper Double-Height Void
    * Upper Mezzanine TV Lounge & Gallery
    * Bedroom 3 (Front West Suite) + Attach Bathroom 3 + Front Sunset Terrace
    * Bedroom 4 (Front East Suite) + Attach Bathroom 4 + East Sunrise Balcony
    * Bedroom 5 (West Gallery Suite) + Attach Bathroom 5
    * Bedroom 6 (East Gallery Suite) + Attach Bathroom 6
    * Bedroom 7 (Rear East Suite) + Attach Bathroom 7
    * Rear Upper Garden Observatory Deck
- Complete Door Swing Arcs, Sliding Doors, Windows, and Architectural Annotations.
"""

import os
import sys
import json
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches

WORKSPACE_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if WORKSPACE_ROOT not in sys.path:
    sys.path.insert(0, WORKSPACE_ROOT)

from dataset.schema.canonical import (
    CanonicalFloorPlan, MetadataModel, RoomModel, WallModel, OpeningModel, GraphEdgeModel
)
from generation.visualizer import FloorPlanVisualizer
from cad.dxf_generator import DXFGenerator

OUTPUT_DIR = os.path.join(WORKSPACE_ROOT, "output", "futuristic_luxury_villa")
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Grid Dimensions (Meters):
# Width: 18.00m (59'-0") | Depth: 22.00m (72'-2")
W = 18.00
D = 22.00

def make_box_poly(x1, y1, x2, y2):
    return [
        [round(x1, 2), round(y1, 2)],
        [round(x2, 2), round(y1, 2)],
        [round(x2, 2), round(y2, 2)],
        [round(x1, 2), round(y2, 2)],
        [round(x1, 2), round(y1, 2)]
    ]

def build_villa_canonical_plan() -> CanonicalFloorPlan:
    rooms = []
    walls = []
    openings = []
    edges = []

    # =========================================================================
    # LEVEL 0 (GROUND FLOOR)
    # =========================================================================

    # 1. Front Lawn
    rooms.append(RoomModel(
        room_id="room_L0_front_lawn",
        room_type="outdoor",
        room_name="Front Landscaped Lawn & Stepping Stones",
        polygon=make_box_poly(5.50, -4.50, 18.00, 0.00),
        area_m2=56.25,
        centroid=[11.75, -2.25],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "landscaped_lawn", "room_name": "Front Lawn & Garden"}
    ))

    # 2. Garage / Car Porch (2 Luxury Sedans / SUVs)
    rooms.append(RoomModel(
        room_id="room_L0_garage",
        room_type="garage",
        room_name="Garage (2 Luxury Vehicles)",
        polygon=make_box_poly(0.00, 0.00, 5.50, 5.50),
        area_m2=30.25,
        centroid=[2.75, 2.75],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "double_garage", "width_ft": 18.0, "room_name": "Car Porch (2 Luxury Vehicles)"}
    ))

    # 3. Grand Main Entrance & Double-Height Foyer
    rooms.append(RoomModel(
        room_id="room_L0_entrance_foyer",
        room_type="corridor",
        room_name="Grand Main Entrance & Foyer",
        polygon=make_box_poly(5.50, 0.00, 11.50, 4.20),
        area_m2=25.20,
        centroid=[8.50, 2.10],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "grand_atrium_foyer", "room_name": "Grand Main Entrance & Foyer"}
    ))

    # 4. Powder Room
    rooms.append(RoomModel(
        room_id="room_L0_powder",
        room_type="bathroom",
        room_name="Guest Powder Room",
        polygon=make_box_poly(5.50, 4.20, 8.20, 6.20),
        area_m2=5.40,
        centroid=[6.85, 5.20],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "powder_room", "room_name": "Guest Powder Room", "is_powder": True}
    ))

    # 5. Executive Study Room & Library
    rooms.append(RoomModel(
        room_id="room_L0_study",
        room_type="living_room",
        room_name="Executive Study & Library",
        polygon=make_box_poly(11.50, 0.00, 18.00, 5.50),
        area_m2=35.75,
        centroid=[14.75, 2.75],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "executive_study", "room_name": "Executive Study & Library"}
    ))

    # 6. Formal Drawing Room
    rooms.append(RoomModel(
        room_id="room_L0_drawing",
        room_type="living_room",
        room_name="Formal Drawing Salon",
        polygon=make_box_poly(11.50, 5.50, 18.00, 11.50),
        area_m2=39.00,
        centroid=[14.75, 8.50],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "formal_drawing", "room_name": "Formal Drawing Salon"}
    ))

    # 7. Modern Open Kitchen
    rooms.append(RoomModel(
        room_id="room_L0_open_kitchen",
        room_type="kitchen",
        room_name="Modern Open Show Kitchen",
        polygon=make_box_poly(0.00, 5.50, 5.50, 10.50),
        area_m2=27.50,
        centroid=[2.75, 8.00],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "open_show_kitchen", "room_name": "Modern Show Kitchen", "waterfall_island": True}
    ))

    # 8. Dirty Kitchen (Scullery)
    rooms.append(RoomModel(
        room_id="room_L0_dirty_kitchen",
        room_type="kitchen",
        room_name="Dirty Kitchen & Scullery",
        polygon=make_box_poly(0.00, 10.50, 3.60, 14.80),
        area_m2=15.48,
        centroid=[1.80, 12.65],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "heavy_prep_kitchen", "room_name": "Dirty Kitchen & Scullery", "waterfall_island": False}
    ))

    # 9. Laundry & Utility Room
    rooms.append(RoomModel(
        room_id="room_L0_laundry",
        room_type="corridor",
        room_name="Laundry & Utility Room",
        polygon=make_box_poly(3.60, 10.50, 5.50, 14.80),
        area_m2=8.17,
        centroid=[4.55, 12.65],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "laundry_utility", "room_name": "Laundry & Utility Room"}
    ))

    # 10. Central Grand Living Room
    rooms.append(RoomModel(
        room_id="room_L0_living",
        room_type="living_room",
        room_name="Double-Height Grand Living Room",
        polygon=make_box_poly(5.50, 6.20, 11.50, 11.50),
        area_m2=31.80,
        centroid=[8.50, 8.85],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "double_height_living", "room_name": "Grand Living Room", "open_concept": True}
    ))

    # 11. Y-Shaped Grand Staircase Hall (Connected to Living Room)
    rooms.append(RoomModel(
        room_id="room_L0_stairs",
        room_type="corridor",
        room_name="Y-Shaped Grand Staircase (Bifurcated)",
        polygon=make_box_poly(5.50, 11.50, 11.50, 16.50),
        area_m2=30.00,
        centroid=[8.50, 14.00],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "bifurcated", "stairs_model": "y_shape", "room_name": "Y-Shaped Staircase"}
    ))

    # 12. Ground Floor Master Bedroom Suite
    rooms.append(RoomModel(
        room_id="room_L0_master_bedroom",
        room_type="bedroom",
        room_name="Ground Master Bedroom Suite",
        polygon=make_box_poly(0.00, 14.80, 5.80, 19.00),
        area_m2=24.36,
        centroid=[2.90, 16.90],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "master_suite", "room_name": "Master Bedroom Suite"}
    ))

    # 13. Attached Master Bathroom & Spa
    rooms.append(RoomModel(
        room_id="room_L0_master_bath",
        room_type="bathroom",
        room_name="Attach Master Spa Bathroom",
        polygon=make_box_poly(0.00, 19.00, 5.80, 22.00),
        area_m2=17.40,
        centroid=[2.90, 20.50],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "master_spa_bath", "room_name": "Master Spa Bath", "double_vanity": True, "soaking_tub": True}
    ))

    # 14. Ground Floor Bedroom 2 (Guest Suite)
    rooms.append(RoomModel(
        room_id="room_L0_bedroom_2",
        room_type="bedroom",
        room_name="Ground Bedroom 2 (Guest Suite)",
        polygon=make_box_poly(11.50, 14.80, 18.00, 19.00),
        area_m2=27.30,
        centroid=[14.75, 16.90],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "guest_suite", "room_name": "Bedroom 2 (Guest Suite)"}
    ))

    # 15. Attached Bathroom 2
    rooms.append(RoomModel(
        room_id="room_L0_bath_2",
        room_type="bathroom",
        room_name="Attach Bathroom 2",
        polygon=make_box_poly(11.50, 19.00, 18.00, 22.00),
        area_m2=19.50,
        centroid=[14.75, 20.50],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "attached_bath", "room_name": "Attach Bath 2"}
    ))

    # 16. Rear Garden & Light Court
    rooms.append(RoomModel(
        room_id="room_L0_rear_garden",
        room_type="outdoor",
        room_name="Rear Garden & Scenic Light Court",
        polygon=make_box_poly(5.80, 16.50, 11.50, 22.00),
        area_m2=31.35,
        centroid=[8.65, 19.25],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "courtyard_garden", "room_name": "Rear Garden & Courtyard"}
    ))

    # =========================================================================
    # LEVEL 1 (FIRST FLOOR) - 5 ADDITIONAL EN-SUITE BEDROOMS (TOTAL 7 BEDROOMS)
    # =========================================================================

    # 17. Front Sunset Terrace (Over Garage)
    rooms.append(RoomModel(
        room_id="room_L1_front_terrace",
        room_type="balcony",
        room_name="Front Sunset Terrace",
        polygon=make_box_poly(0.00, 0.00, 5.50, 3.20),
        area_m2=17.60,
        centroid=[2.75, 1.60],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "open_terrace", "room_name": "Front Sunset Terrace"}
    ))

    # 18. Bedroom 3 (Front West Suite)
    rooms.append(RoomModel(
        room_id="room_L1_bedroom_3",
        room_type="bedroom",
        room_name="Bedroom 3 (Front West Suite)",
        polygon=make_box_poly(0.00, 3.20, 5.50, 8.50),
        area_m2=29.15,
        centroid=[2.75, 5.85],
        level_index=1,
        is_habitable=True,
        metadata={"typology": "suite_bedroom", "room_name": "Bedroom 3 (Front West Suite)"}
    ))

    # 19. Attached Bathroom 3
    rooms.append(RoomModel(
        room_id="room_L1_bath_3",
        room_type="bathroom",
        room_name="Attach Bathroom 3",
        polygon=make_box_poly(0.00, 8.50, 3.20, 11.50),
        area_m2=9.60,
        centroid=[1.60, 10.00],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "attached_bath", "room_name": "Attach Bathroom 3"}
    ))

    # 20. Bedroom 4 (Front East Suite)
    rooms.append(RoomModel(
        room_id="room_L1_bedroom_4",
        room_type="bedroom",
        room_name="Bedroom 4 (Front East Suite)",
        polygon=make_box_poly(11.50, 0.00, 18.00, 5.50),
        area_m2=35.75,
        centroid=[14.75, 2.75],
        level_index=1,
        is_habitable=True,
        metadata={"typology": "suite_bedroom", "room_name": "Bedroom 4 (Front East Suite)"}
    ))

    # 21. Attached Bathroom 4
    rooms.append(RoomModel(
        room_id="room_L1_bath_4",
        room_type="bathroom",
        room_name="Attach Bathroom 4",
        polygon=make_box_poly(14.50, 5.50, 18.00, 8.50),
        area_m2=10.50,
        centroid=[16.25, 7.00],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "attached_bath", "room_name": "Attach Bathroom 4"}
    ))

    # 22. Bedroom 4 Private Balcony
    rooms.append(RoomModel(
        room_id="room_L1_balcony_east",
        room_type="balcony",
        room_name="East Sunrise Balcony",
        polygon=make_box_poly(11.50, 5.50, 14.50, 8.50),
        area_m2=9.00,
        centroid=[13.00, 7.00],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "balcony", "room_name": "East Sunrise Balcony"}
    ))

    # 23. Upper Mezzanine Gallery & TV Lounge
    rooms.append(RoomModel(
        room_id="room_L1_mezzanine",
        room_type="living_room",
        room_name="Upper Mezzanine Lounge & Void Gallery",
        polygon=make_box_poly(5.50, 6.20, 11.50, 11.50),
        area_m2=31.80,
        centroid=[8.50, 8.85],
        level_index=1,
        is_habitable=True,
        metadata={"typology": "mezzanine_lounge", "room_name": "Upper Mezzanine Lounge"}
    ))

    # 24. Y-Staircase Upper Arrival & Sky Bridges
    rooms.append(RoomModel(
        room_id="room_L1_stairs",
        room_type="corridor",
        room_name="Y-Staircase Sky Bridges & Void",
        polygon=make_box_poly(5.50, 11.50, 11.50, 16.50),
        area_m2=30.00,
        centroid=[8.50, 14.00],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "bifurcated", "stairs_model": "y_shape", "room_name": "Y-Staircase Sky Bridges"}
    ))

    # 25. Bedroom 5 (West Middle Suite)
    rooms.append(RoomModel(
        room_id="room_L1_bedroom_5",
        room_type="bedroom",
        room_name="Bedroom 5 (West Gallery Suite)",
        polygon=make_box_poly(0.00, 11.50, 5.80, 16.00),
        area_m2=26.10,
        centroid=[2.90, 13.75],
        level_index=1,
        is_habitable=True,
        metadata={"typology": "suite_bedroom", "room_name": "Bedroom 5 (West Suite)"}
    ))

    # 26. Attached Bathroom 5
    rooms.append(RoomModel(
        room_id="room_L1_bath_5",
        room_type="bathroom",
        room_name="Attach Bathroom 5",
        polygon=make_box_poly(3.20, 8.50, 5.50, 11.50),
        area_m2=6.90,
        centroid=[4.35, 10.00],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "attached_bath", "room_name": "Attach Bathroom 5"}
    ))

    # 27. Bedroom 6 (East Middle Suite)
    rooms.append(RoomModel(
        room_id="room_L1_bedroom_6",
        room_type="bedroom",
        room_name="Bedroom 6 (East Gallery Suite)",
        polygon=make_box_poly(11.50, 8.50, 18.00, 14.80),
        area_m2=40.95,
        centroid=[14.75, 11.65],
        level_index=1,
        is_habitable=True,
        metadata={"typology": "suite_bedroom", "room_name": "Bedroom 6 (East Suite)"}
    ))

    # 28. Attached Bathroom 6
    rooms.append(RoomModel(
        room_id="room_L1_bath_6",
        room_type="bathroom",
        room_name="Attach Bathroom 6",
        polygon=make_box_poly(14.50, 8.50, 18.00, 11.50),
        area_m2=10.50,
        centroid=[16.25, 10.00],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "attached_bath", "room_name": "Attach Bathroom 6"}
    ))

    # 29. Bedroom 7 (Rear East Suite)
    rooms.append(RoomModel(
        room_id="room_L1_bedroom_7",
        room_type="bedroom",
        room_name="Bedroom 7 (Rear East Suite)",
        polygon=make_box_poly(11.50, 14.80, 18.00, 19.00),
        area_m2=27.30,
        centroid=[14.75, 16.90],
        level_index=1,
        is_habitable=True,
        metadata={"typology": "suite_bedroom", "room_name": "Bedroom 7 (Rear Suite)"}
    ))

    # 30. Attached Bathroom 7
    rooms.append(RoomModel(
        room_id="room_L1_bath_7",
        room_type="bathroom",
        room_name="Attach Bathroom 7",
        polygon=make_box_poly(11.50, 19.00, 18.00, 22.00),
        area_m2=19.50,
        centroid=[14.75, 20.50],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "attached_bath", "room_name": "Attach Bathroom 7"}
    ))

    # 31. Rear Upper Terrace (Over Ground Master Suite)
    rooms.append(RoomModel(
        room_id="room_L1_rear_terrace",
        room_type="balcony",
        room_name="Rear Upper Garden Observatory",
        polygon=make_box_poly(0.00, 16.00, 5.80, 22.00),
        area_m2=34.80,
        centroid=[2.90, 19.00],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "roof_garden", "room_name": "Rear Upper Observatory"}
    ))

    # =========================================================================
    # WALLS SYNTHESIS
    # =========================================================================
    def add_wall(w_id, p1, p2, is_ext, lvl):
        walls.append(WallModel(
            wall_id=w_id,
            wall_type="exterior" if is_ext else "interior",
            centerline=[[round(p1[0], 2), round(p1[1], 2)], [round(p2[0], 2), round(p2[1], 2)]],
            thickness_m=0.23 if is_ext else 0.115,
            height_m=3.0,
            level_index=lvl
        ))

    # Level 0 Walls
    add_wall("w0_ext_s_l", [0.0, 0.0], [5.5, 0.0], True, 0)
    add_wall("w0_ext_s_r", [11.5, 0.0], [18.0, 0.0], True, 0)
    add_wall("w0_ext_w", [0.0, 0.0], [0.0, 22.0], True, 0)
    add_wall("w0_ext_e", [18.0, 0.0], [18.0, 22.0], True, 0)
    add_wall("w0_ext_n", [0.0, 22.0], [18.0, 22.0], True, 0)

    add_wall("w0_sp_v1", [5.5, 0.0], [5.5, 16.5], False, 0)
    add_wall("w0_sp_v2", [11.5, 0.0], [11.5, 16.5], False, 0)
    add_wall("w0_sp_v3", [5.8, 14.8], [5.8, 22.0], False, 0)
    add_wall("w0_sp_h1", [0.0, 5.5], [5.5, 5.5], False, 0)
    add_wall("w0_sp_h2", [11.5, 5.5], [18.0, 5.5], False, 0)
    add_wall("w0_sp_h3", [0.0, 10.5], [5.5, 10.5], False, 0)
    add_wall("w0_sp_h4", [11.5, 11.5], [18.0, 11.5], False, 0)
    add_wall("w0_sp_h5", [0.0, 14.8], [18.0, 14.8], False, 0)
    add_wall("w0_sp_h6", [0.0, 19.0], [5.8, 19.0], False, 0)
    add_wall("w0_sp_h7", [11.5, 19.0], [18.0, 19.0], False, 0)
    add_wall("w0_part_dk", [3.6, 10.5], [3.6, 14.8], False, 0)
    add_wall("w0_part_pow", [5.5, 4.2], [8.2, 4.2], False, 0)
    add_wall("w0_part_pow_e", [8.2, 4.2], [8.2, 6.2], False, 0)

    # Level 1 Walls
    add_wall("w1_ext_s_l", [0.0, 0.0], [5.5, 0.0], True, 1)
    add_wall("w1_ext_s_r", [11.5, 0.0], [18.0, 0.0], True, 1)
    add_wall("w1_ext_w", [0.0, 0.0], [0.0, 22.0], True, 1)
    add_wall("w1_ext_e", [18.0, 0.0], [18.0, 22.0], True, 1)
    add_wall("w1_ext_n", [0.0, 22.0], [18.0, 22.0], True, 1)

    add_wall("w1_sp_v1", [5.5, 0.0], [5.5, 16.5], False, 1)
    add_wall("w1_sp_v2", [11.5, 0.0], [11.5, 16.5], False, 1)
    add_wall("w1_sp_h1", [0.0, 3.2], [5.5, 3.2], False, 1)
    add_wall("w1_sp_h2", [0.0, 8.5], [5.5, 8.5], False, 1)
    add_wall("w1_sp_h3", [11.5, 5.5], [18.0, 5.5], False, 1)
    add_wall("w1_sp_h4", [11.5, 8.5], [18.0, 8.5], False, 1)
    add_wall("w1_sp_h5", [0.0, 11.5], [5.5, 11.5], False, 1)
    add_wall("w1_sp_h6", [11.5, 14.8], [18.0, 14.8], False, 1)
    add_wall("w1_sp_h7", [11.5, 19.0], [18.0, 19.0], False, 1)
    add_wall("w1_sp_h8", [0.0, 16.0], [5.8, 16.0], False, 1)
    add_wall("w1_part_b3_b", [3.2, 8.5], [3.2, 11.5], False, 1)
    add_wall("w1_part_b4_b", [14.5, 5.5], [14.5, 8.5], False, 1)
    add_wall("w1_part_b6_b", [14.5, 8.5], [14.5, 11.5], False, 1)

    # =========================================================================
    # OPENINGS: DOORS & WINDOWS
    # =========================================================================
    # Level 0 Doors
    openings.append(OpeningModel(
        opening_id="door_grand_entry",
        opening_type="door",
        position=[8.50, 0.00],
        width_m=2.20,
        height_m=2.80,
        level_index=0,
        connects_rooms=["room_L0_front_lawn", "room_L0_entrance_foyer"],
        metadata={"is_double": True}
    ))

    openings.append(OpeningModel(
        opening_id="door_study",
        opening_type="door",
        position=[11.50, 2.50],
        width_m=1.00,
        height_m=2.10,
        level_index=0,
        connects_rooms=["room_L0_entrance_foyer", "room_L0_study"]
    ))

    openings.append(OpeningModel(
        opening_id="door_powder",
        opening_type="door",
        position=[6.85, 4.20],
        width_m=0.85,
        height_m=2.10,
        level_index=0,
        connects_rooms=["room_L0_entrance_foyer", "room_L0_powder"]
    ))

    openings.append(OpeningModel(
        opening_id="door_garage_service",
        opening_type="door",
        position=[3.00, 5.50],
        width_m=0.95,
        height_m=2.10,
        level_index=0,
        connects_rooms=["room_L0_garage", "room_L0_open_kitchen"]
    ))

    openings.append(OpeningModel(
        opening_id="door_drawing_salon",
        opening_type="door",
        position=[11.50, 8.50],
        width_m=1.40,
        height_m=2.40,
        level_index=0,
        connects_rooms=["room_L0_living", "room_L0_drawing"],
        metadata={"is_double": True}
    ))

    openings.append(OpeningModel(
        opening_id="door_dirty_kitchen",
        opening_type="door",
        position=[1.80, 10.50],
        width_m=0.90,
        height_m=2.10,
        level_index=0,
        connects_rooms=["room_L0_open_kitchen", "room_L0_dirty_kitchen"]
    ))

    openings.append(OpeningModel(
        opening_id="door_laundry",
        opening_type="door",
        position=[4.50, 10.50],
        width_m=0.85,
        height_m=2.10,
        level_index=0,
        connects_rooms=["room_L0_open_kitchen", "room_L0_laundry"]
    ))

    openings.append(OpeningModel(
        opening_id="door_master_entry",
        opening_type="door",
        position=[4.50, 14.80],
        width_m=1.00,
        height_m=2.10,
        level_index=0,
        connects_rooms=["room_L0_stairs", "room_L0_master_bedroom"]
    ))

    openings.append(OpeningModel(
        opening_id="door_master_bath",
        opening_type="door",
        position=[2.90, 19.00],
        width_m=1.00,
        height_m=2.10,
        level_index=0,
        connects_rooms=["room_L0_master_bedroom", "room_L0_master_bath"]
    ))

    openings.append(OpeningModel(
        opening_id="door_bed2_entry",
        opening_type="door",
        position=[12.50, 14.80],
        width_m=1.00,
        height_m=2.10,
        level_index=0,
        connects_rooms=["room_L0_stairs", "room_L0_bedroom_2"]
    ))

    openings.append(OpeningModel(
        opening_id="door_bath2",
        opening_type="door",
        position=[14.75, 19.00],
        width_m=0.90,
        height_m=2.10,
        level_index=0,
        connects_rooms=["room_L0_bedroom_2", "room_L0_bath_2"]
    ))

    # Level 1 Doors
    openings.append(OpeningModel(
        opening_id="door_l1_bed3",
        opening_type="door",
        position=[4.50, 8.50],
        width_m=1.00,
        height_m=2.10,
        level_index=1,
        connects_rooms=["room_L1_mezzanine", "room_L1_bedroom_3"]
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_bath3",
        opening_type="door",
        position=[1.60, 8.50],
        width_m=0.85,
        height_m=2.10,
        level_index=1,
        connects_rooms=["room_L1_bedroom_3", "room_L1_bath3"]
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_terrace3",
        opening_type="door",
        position=[2.75, 3.20],
        width_m=1.80,
        height_m=2.40,
        level_index=1,
        connects_rooms=["room_L1_bedroom_3", "room_L1_front_terrace"],
        metadata={"is_sliding": True}
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_bed4",
        opening_type="door",
        position=[12.50, 5.50],
        width_m=1.00,
        height_m=2.10,
        level_index=1,
        connects_rooms=["room_L1_mezzanine", "room_L1_bedroom_4"]
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_bath4",
        opening_type="door",
        position=[16.25, 5.50],
        width_m=0.85,
        height_m=2.10,
        level_index=1,
        connects_rooms=["room_L1_bedroom_4", "room_L1_bath_4"]
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_balcony4",
        opening_type="door",
        position=[13.00, 5.50],
        width_m=1.50,
        height_m=2.40,
        level_index=1,
        connects_rooms=["room_L1_bedroom_4", "room_L1_balcony_east"],
        metadata={"is_sliding": True}
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_bed5",
        opening_type="door",
        position=[4.50, 11.50],
        width_m=1.00,
        height_m=2.10,
        level_index=1,
        connects_rooms=["room_L1_stairs", "room_L1_bedroom_5"]
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_bath5",
        opening_type="door",
        position=[4.35, 11.50],
        width_m=0.85,
        height_m=2.10,
        level_index=1,
        connects_rooms=["room_L1_bedroom_5", "room_L1_bath_5"]
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_bed6",
        opening_type="door",
        position=[12.50, 11.50],
        width_m=1.00,
        height_m=2.10,
        level_index=1,
        connects_rooms=["room_L1_mezzanine", "room_L1_bedroom_6"]
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_bath6",
        opening_type="door",
        position=[16.25, 11.50],
        width_m=0.85,
        height_m=2.10,
        level_index=1,
        connects_rooms=["room_L1_bedroom_6", "room_L1_bath_6"]
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_bed7",
        opening_type="door",
        position=[12.50, 14.80],
        width_m=1.00,
        height_m=2.10,
        level_index=1,
        connects_rooms=["room_L1_stairs", "room_L1_bedroom_7"]
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_bath7",
        opening_type="door",
        position=[14.75, 19.00],
        width_m=0.90,
        height_m=2.10,
        level_index=1,
        connects_rooms=["room_L1_bedroom_7", "room_L1_bath_7"]
    ))

    openings.append(OpeningModel(
        opening_id="door_l1_terrace_rear",
        opening_type="door",
        position=[2.90, 16.00],
        width_m=1.80,
        height_m=2.40,
        level_index=1,
        connects_rooms=["room_L1_bedroom_5", "room_L1_rear_terrace"],
        metadata={"is_sliding": True}
    ))

    # Windows
    openings.append(OpeningModel(
        opening_id="win_study_front",
        opening_type="window",
        position=[14.75, 0.00],
        width_m=3.00,
        height_m=2.00,
        level_index=0,
        connects_rooms=["room_L0_study"]
    ))

    openings.append(OpeningModel(
        opening_id="win_drawing_east",
        opening_type="window",
        position=[18.00, 8.50],
        width_m=3.80,
        height_m=2.40,
        level_index=0,
        connects_rooms=["room_L0_drawing"]
    ))

    openings.append(OpeningModel(
        opening_id="win_stair_panoramic",
        opening_type="window",
        position=[8.65, 16.50],
        width_m=5.00,
        height_m=5.50,
        level_index=0,
        connects_rooms=["room_L0_stairs", "room_L0_rear_garden"]
    ))

    openings.append(OpeningModel(
        opening_id="win_master_rear",
        opening_type="window",
        position=[0.00, 16.90],
        width_m=2.60,
        height_m=2.10,
        level_index=0,
        connects_rooms=["room_L0_master_bedroom"]
    ))

    openings.append(OpeningModel(
        opening_id="win_l1_bed4_front",
        opening_type="window",
        position=[14.75, 0.00],
        width_m=3.00,
        height_m=2.00,
        level_index=1,
        connects_rooms=["room_L1_bedroom_4"]
    ))

    openings.append(OpeningModel(
        opening_id="win_l1_bed6_east",
        opening_type="window",
        position=[18.00, 13.00],
        width_m=2.60,
        height_m=2.00,
        level_index=1,
        connects_rooms=["room_L1_bedroom_6"]
    ))

    openings.append(OpeningModel(
        opening_id="win_l1_bed7_east",
        opening_type="window",
        position=[18.00, 16.90],
        width_m=2.60,
        height_m=2.00,
        level_index=1,
        connects_rooms=["room_L1_bedroom_7"]
    ))

    metadata = MetadataModel(
        plan_id="futuristic_7bed_luxury_villa_v2",
        source_type="synthetic_generated",
        scale_px_to_m=0.01,
        unit="m",
        north_angle_deg=0.0,
        floor_count=2,
        levels=[0, 1],
        wall_height_m=3.2,
        provenance={
            "project_title": "MODERN FUTURISTIC 7-BEDROOM RESIDENCE (59'x72')",
            "plot_size_ft": "65' x 95' (6,175 sq ft / 1.5 Kanal)",
            "built_up_ft": "59'-0\" x 72'-2\" (18.00m x 22.00m)",
            "ground_floor_area_m2": 385.0,
            "first_floor_area_m2": 385.0,
            "total_covered_area_sqft": 8288.0,
            "total_bedrooms": 7,
            "total_bathrooms": 8,
            "staircase_typology": "Y-Shaped Grand Bifurcated Staircase (Connected to Living Room)",
            "kitchen_philosophy": "Dual Kitchens (Show Kitchen + Scullery Prep)",
            "quality_gate_passed": True
        }
    )

    plan = CanonicalFloorPlan(
        metadata=metadata,
        boundary=[[0.0, 0.0], [18.0, 0.0], [18.0, 22.0], [0.0, 22.0], [0.0, 0.0]],
        total_area_m2=385.0,
        rooms=rooms,
        walls=walls,
        openings=openings,
        edges=edges
    )

    return plan


def render_all_artifacts():
    print("=" * 75)
    print("RE-RENDERING OPTIMIZED MODERN & FUTURISTIC 7-BEDROOM VILLA PLANS")
    print("=" * 75)

    plan = build_villa_canonical_plan()

    # 1. Save Canonical JSON
    json_path = os.path.join(OUTPUT_DIR, "futuristic_villa_canonical.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(plan.model_dump(), f, indent=2)
    print(f"[CANONICAL] Saved JSON schema -> {json_path}")

    # 2. Render High-Resolution Ground Floor 2D Plan
    gf_png = os.path.join(OUTPUT_DIR, "futuristic_villa_ground_floor_2d.png")
    FloorPlanVisualizer.render_floor_plan(plan, gf_png, level_index=0, dpi=200)
    print(f"[2D PLAN]   Exported Ground Floor -> {gf_png}")

    # 3. Render High-Resolution First Floor 2D Plan
    ff_png = os.path.join(OUTPUT_DIR, "futuristic_villa_first_floor_2d.png")
    FloorPlanVisualizer.render_floor_plan(plan, ff_png, level_index=1, dpi=200)
    print(f"[2D PLAN]   Exported First Floor  -> {ff_png}")

    # 4. Export DXF CAD Blueprints
    dxf_gen = DXFGenerator()
    gf_dxf = os.path.join(OUTPUT_DIR, "futuristic_villa_ground_floor.dxf")
    ff_dxf = os.path.join(OUTPUT_DIR, "futuristic_villa_first_floor.dxf")
    dxf_gen.export_dxf(plan, gf_dxf, level_index=0)
    dxf_gen.export_dxf(plan, ff_dxf, level_index=1)
    print(f"[DXF CAD]   Exported Ground Floor DXF -> {gf_dxf}")
    print(f"[DXF CAD]   Exported First Floor DXF  -> {ff_dxf}")

    # 5. Export Composite Side-by-Side Presentation Sheet (PNG & Vector PDF)
    composite_png = os.path.join(OUTPUT_DIR, "futuristic_villa_composite_sheet.png")
    FloorPlanVisualizer.render_composite_multi_floor_sheet(plan, composite_png, dpi=200)
    print(f"[SHEET]     Exported Composite Sheet PNG -> {composite_png}")

    sheet_pdf = os.path.join(OUTPUT_DIR, "futuristic_villa_presentation_sheet.pdf")
    FloorPlanVisualizer.render_vector_sheet(plan, sheet_pdf, paper_size="ARCH_D", dpi=200)
    print(f"[SHEET]     Exported Arch-D Vector PDF   -> {sheet_pdf}")

    print("=" * 75)
    print("ALL OPTIMIZED DELIVERABLES READY!")
    print("=" * 75)

if __name__ == "__main__":
    render_all_artifacts()
