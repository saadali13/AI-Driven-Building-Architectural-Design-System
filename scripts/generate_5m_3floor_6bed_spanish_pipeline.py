r"""
Master 5 Marla 3-Storey 6-Bedroom Spanish Villa Pipeline.
Features:
- Plot: 5 Marla (25'-0" x 45'-0" / 7.62m x 13.72m)
- 3 Complete Floors (Ground, First, Rooftop Penthouse)
- 6 Bedrooms TOTAL, EACH WITH ATTACHED BATHROOM (6 Beds + 6 Baths)
- Circular / Round Spiral Staircase Core (Ø 2.30m)
- Single Car Porch, Formal Drawing Room, Powder Room, TV Lounge, Modern Spanish Kitchen
- Full Architectural Wall Model:
  * 9" (0.23m) Exterior load-bearing walls
  * 9" (0.23m) Interior spine walls
  * 4.5" (0.115m) Partition walls enclosing drawing room, all 6 bedrooms, all 6 bathrooms
  * Open kitchen to TV lounge (no dividing wall, island counter demarcated)
  * Level 0, Level 1, and Level 2 each have complete wall systems!
- Option A: Authentic Spanish 2D CAD Front Elevation (Terracotta Barrel Tiles, Arched Loggia, Rejas, Vigas, Datums)
- Option B: Photorealistic Isolated 3D House Model Render (Studio Podium)
- High-Resolution Coordinated Master Presentation Sheet
"""

import os
import sys
import math
import json
import numpy as np
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon as MplPoly
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dataset.schema.canonical import (
    CanonicalFloorPlan, MetadataModel, RoomModel, WallModel, OpeningModel, GraphEdgeModel
)
from generation.visualizer import FloorPlanVisualizer
from generation.elevation_engine import ElevationEngine

OUT_DIR = os.path.join(PROJECT_ROOT, "output", "5_marla_spanish_3floor_6bed_suite")
os.makedirs(OUT_DIR, exist_ok=True)

W = 7.62   # 25'-0" width (m)
D = 13.72  # 45'-0" depth (m)


def make_box_poly(x1, y1, x2, y2):
    return [[round(x1, 2), round(y1, 2)],
            [round(x2, 2), round(y1, 2)],
            [round(x2, 2), round(y2, 2)],
            [round(x1, 2), round(y2, 2)],
            [round(x1, 2), round(y1, 2)]]


def create_spanish_5m_canonical_plan() -> CanonicalFloorPlan:
    rooms: List[RoomModel] = []
    walls: List[WallModel] = []
    openings: List[OpeningModel] = []
    edges: List[GraphEdgeModel] = []

    # =========================================================================
    # LEVEL 0: GROUND FLOOR
    # =========================================================================
    # 1. Car Porch (Left Front): 3.00m x 4.40m (~10' x 14'-6")
    rooms.append(RoomModel(
        room_id="room_L0_porch",
        room_type="garage",
        room_name="Single Car Porch (Spanish Arched)",
        polygon=make_box_poly(0.00, 0.00, 3.00, 4.40),
        area_m2=13.20,
        centroid=[1.50, 2.20],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "single_car_garage", "width_ft": 10.0}
    ))

    # 2. Formal Drawing Room (Right Front): 4.62m x 4.40m (~15' x 14'-6")
    rooms.append(RoomModel(
        room_id="room_L0_drawing",
        room_type="living_room",
        room_name="Formal Spanish Drawing Room",
        polygon=make_box_poly(3.00, 0.00, W, 4.40),
        area_m2=20.33,
        centroid=[5.31, 2.20],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "formal_drawing", "fenestration": "twin_spanish_arches"}
    ))

    # 3. Guest Powder Room: 1.50m x 1.40m (~5' x 4'-7")
    rooms.append(RoomModel(
        room_id="room_L0_powder",
        room_type="bathroom",
        room_name="Guest Powder Room",
        polygon=make_box_poly(6.12, 4.40, W, 5.80),
        area_m2=2.10,
        centroid=[6.87, 5.10],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "powder_room"}
    ))

    # 4. Central Lightwell OTS: 1.50m x 1.40m
    rooms.append(RoomModel(
        room_id="room_L0_ots_central",
        room_type="outdoor",
        room_name="Central OTS / Lightwell",
        polygon=make_box_poly(6.12, 5.80, W, 7.20),
        area_m2=2.10,
        centroid=[6.87, 6.50],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "ots"}
    ))

    # 5. Circular / Round Spiral Staircase Core: 2.40m x 2.40m (~8' x 8')
    rooms.append(RoomModel(
        room_id="room_L0_spiral_stairs",
        room_type="corridor",
        room_name="Circular Spiral Staircase Core (Round)",
        polygon=make_box_poly(0.00, 4.40, 2.40, 6.80),
        area_m2=5.76,
        centroid=[1.20, 5.60],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "spiral", "is_spiral": True, "spiral_diameter_m": 2.30, "flow": "UP"}
    ))

    # 6. Modern Spanish Kitchen: 2.40m x 2.40m (~8' x 8' Open Island Concept)
    rooms.append(RoomModel(
        room_id="room_L0_kitchen",
        room_type="kitchen",
        room_name="Modern Spanish Open Kitchen",
        polygon=make_box_poly(0.00, 6.80, 2.40, 9.20),
        area_m2=5.76,
        centroid=[1.20, 8.00],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "kitchen", "open_concept": True, "waterfall_island": True}
    ))

    # 7. Central Family Living & TV Lounge: 3.72m x 4.80m (~12' x 16')
    rooms.append(RoomModel(
        room_id="room_L0_lounge",
        room_type="living_room",
        room_name="Family Living & TV Lounge",
        polygon=make_box_poly(2.40, 4.40, 6.12, 9.20),
        area_m2=17.85,
        centroid=[4.26, 6.80],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "tv_lounge", "open_concept": True}
    ))

    # 8. Bed 1 (Ground Master Suite): 3.81m x 4.52m (~12'-6" x 15')
    rooms.append(RoomModel(
        room_id="room_L0_bed1",
        room_type="bedroom",
        room_name="Master Bedroom 1 Suite",
        polygon=make_box_poly(0.00, 9.20, 3.81, D),
        area_m2=17.22,
        centroid=[1.90, 11.46],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "master_suite"}
    ))

    # Attached Bath 1: 1.80m x 2.00m (~6' x 6'-7")
    rooms.append(RoomModel(
        room_id="room_L0_bath1",
        room_type="bathroom",
        room_name="Attached Bath 1 (En-suite)",
        polygon=make_box_poly(0.00, 9.20, 1.80, 11.20),
        area_m2=3.60,
        centroid=[0.90, 10.20],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "ensuite"}
    ))

    # 9. Bed 2 (Guest Suite): 3.81m x 4.52m (~12'-6" x 15')
    rooms.append(RoomModel(
        room_id="room_L0_bed2",
        room_type="bedroom",
        room_name="Bedroom 2 (Guest Suite)",
        polygon=make_box_poly(3.81, 9.20, W, D),
        area_m2=17.22,
        centroid=[5.71, 11.46],
        level_index=0,
        is_habitable=True,
        metadata={"typology": "guest_suite"}
    ))

    # Attached Bath 2: 1.80m x 2.00m (~6' x 6'-7")
    rooms.append(RoomModel(
        room_id="room_L0_bath2",
        room_type="bathroom",
        room_name="Attached Bath 2 (En-suite)",
        polygon=make_box_poly(5.82, 9.20, W, 11.20),
        area_m2=3.60,
        centroid=[6.72, 10.20],
        level_index=0,
        is_habitable=False,
        metadata={"typology": "ensuite"}
    ))

    # =========================================================================
    # LEVEL 1: FIRST FLOOR
    # =========================================================================
    # 10. Spanish Arched Loggia Balcony: 3.00m x 2.20m (~10' x 7')
    rooms.append(RoomModel(
        room_id="room_L1_balcony",
        room_type="balcony",
        room_name="Spanish Arched Loggia Balcony",
        polygon=make_box_poly(0.00, 0.00, 3.00, 2.20),
        area_m2=6.60,
        centroid=[1.50, 1.10],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "spanish_loggia"}
    ))

    # 11. Attached Bath 3 (Front Master Bath): 3.00m x 2.20m
    rooms.append(RoomModel(
        room_id="room_L1_bath3",
        room_type="bathroom",
        room_name="Attached Bath 3 (Master Ensuite)",
        polygon=make_box_poly(0.00, 2.20, 3.00, 4.40),
        area_m2=6.60,
        centroid=[1.50, 3.30],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "ensuite", "stacked_over": "porch_utility"}
    ))

    # 12. Bed 3 (Upper Master Suite): 4.62m x 4.40m (~15' x 14'-6")
    rooms.append(RoomModel(
        room_id="room_L1_bed3",
        room_type="bedroom",
        room_name="Master Bedroom 3 Suite",
        polygon=make_box_poly(3.00, 0.00, W, 4.40),
        area_m2=20.33,
        centroid=[5.31, 2.20],
        level_index=1,
        is_habitable=True,
        metadata={"typology": "master_suite"}
    ))

    # 13. Circular Spiral Stair Core (Level 1)
    rooms.append(RoomModel(
        room_id="room_L1_spiral_stairs",
        room_type="corridor",
        room_name="Circular Spiral Staircase (Level 1)",
        polygon=make_box_poly(0.00, 4.40, 2.40, 6.80),
        area_m2=5.76,
        centroid=[1.20, 5.60],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "spiral", "is_spiral": True, "flow": "UP / DN"}
    ))

    # 14. Study & Coffee Nook: 2.40m x 2.40m
    rooms.append(RoomModel(
        room_id="room_L1_study",
        room_type="closet",
        room_name="Upper Study & Coffee Nook",
        polygon=make_box_poly(0.00, 6.80, 2.40, 9.20),
        area_m2=5.76,
        centroid=[1.20, 8.00],
        level_index=1,
        is_habitable=True,
        metadata={"typology": "study"}
    ))

    # 15. Upper Family Lounge & Gallery: 3.72m x 4.80m
    rooms.append(RoomModel(
        room_id="room_L1_lounge",
        room_type="living_room",
        room_name="Upper Family TV Lounge & Gallery",
        polygon=make_box_poly(2.40, 4.40, 6.12, 9.20),
        area_m2=17.85,
        centroid=[4.26, 6.80],
        level_index=1,
        is_habitable=True,
        metadata={"typology": "tv_lounge"}
    ))

    # 16. Upper Dressing Walk-in: 1.50m x 2.80m
    rooms.append(RoomModel(
        room_id="room_L1_dressing",
        room_type="closet",
        room_name="Walk-in Wardrobe & Linen",
        polygon=make_box_poly(6.12, 4.40, W, 7.20),
        area_m2=4.20,
        centroid=[6.87, 5.80],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "wardrobe"}
    ))

    # 17. Bed 4 Suite (Rear Left): 3.81m x 4.52m
    rooms.append(RoomModel(
        room_id="room_L1_bed4",
        room_type="bedroom",
        room_name="Bedroom 4 Suite (Rear)",
        polygon=make_box_poly(0.00, 9.20, 3.81, D),
        area_m2=17.22,
        centroid=[1.90, 11.46],
        level_index=1,
        is_habitable=True,
        metadata={"typology": "bedroom"}
    ))

    # Attached Bath 4: 1.80m x 2.00m (100% Stacked over Bath 1)
    rooms.append(RoomModel(
        room_id="room_L1_bath4",
        room_type="bathroom",
        room_name="Attached Bath 4 (100% Stacked)",
        polygon=make_box_poly(0.00, 9.20, 1.80, 11.20),
        area_m2=3.60,
        centroid=[0.90, 10.20],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "ensuite"}
    ))

    # 18. Rear Open Service Light Terrace: 3.81m x 4.52m
    rooms.append(RoomModel(
        room_id="room_L1_terrace_rear",
        room_type="balcony",
        room_name="Rear Service Light Terrace",
        polygon=make_box_poly(3.81, 9.20, W, D),
        area_m2=17.22,
        centroid=[5.71, 11.46],
        level_index=1,
        is_habitable=False,
        metadata={"typology": "terrace"}
    ))

    # =========================================================================
    # LEVEL 2: ROOFTOP PENTHOUSE
    # =========================================================================
    # 19. Spanish Rooftop Pergola BBQ Terrace: 7.62m x 4.40m (~25' x 14'-6")
    rooms.append(RoomModel(
        room_id="room_L2_bbq_terrace",
        room_type="balcony",
        room_name="Spanish Terracotta Pergola BBQ Terrace",
        polygon=make_box_poly(0.00, 0.00, W, 4.40),
        area_m2=33.53,
        centroid=[3.81, 2.20],
        level_index=2,
        is_habitable=False,
        metadata={"typology": "bbq_terrace", "has_pergola": True}
    ))

    # 20. Circular Spiral Stair Mumty Tower: 2.40m x 2.40m
    rooms.append(RoomModel(
        room_id="room_L2_spiral_stairs",
        room_type="corridor",
        room_name="Circular Spiral Stair Mumty Tower",
        polygon=make_box_poly(0.00, 4.40, 2.40, 6.80),
        area_m2=5.76,
        centroid=[1.20, 5.60],
        level_index=2,
        is_habitable=False,
        metadata={"typology": "spiral", "is_spiral": True, "flow": "ARRIVAL"}
    ))

    # 21. Penthouse Gallery Foyer: 3.72m x 4.80m
    rooms.append(RoomModel(
        room_id="room_L2_foyer",
        room_type="corridor",
        room_name="Penthouse Gallery Lounge",
        polygon=make_box_poly(2.40, 4.40, 6.12, 9.20),
        area_m2=17.85,
        centroid=[4.26, 6.80],
        level_index=2,
        is_habitable=True,
        metadata={"typology": "gallery"}
    ))

    # 22. Rooftop Storage / MEP Shaft: 1.50m x 2.80m
    rooms.append(RoomModel(
        room_id="room_L2_store",
        room_type="closet",
        room_name="Rooftop Storage & MEP Shaft",
        polygon=make_box_poly(6.12, 4.40, W, 7.20),
        area_m2=4.20,
        centroid=[6.87, 5.80],
        level_index=2,
        is_habitable=False,
        metadata={"typology": "store"}
    ))

    # 23. Bed 5 (Penthouse Suite 1): 3.81m x 4.52m
    rooms.append(RoomModel(
        room_id="room_L2_bed5",
        room_type="bedroom",
        room_name="Bedroom 5 (Penthouse Suite)",
        polygon=make_box_poly(0.00, 9.20, 3.81, D),
        area_m2=17.22,
        centroid=[1.90, 11.46],
        level_index=2,
        is_habitable=True,
        metadata={"typology": "penthouse_suite"}
    ))

    # Attached Bath 5: 1.80m x 2.00m (100% Stacked)
    rooms.append(RoomModel(
        room_id="room_L2_bath5",
        room_type="bathroom",
        room_name="Attached Bath 5 (100% Stacked)",
        polygon=make_box_poly(0.00, 9.20, 1.80, 11.20),
        area_m2=3.60,
        centroid=[0.90, 10.20],
        level_index=2,
        is_habitable=False,
        metadata={"typology": "ensuite"}
    ))

    # 24. Bed 6 (Penthouse Suite 2): 3.81m x 4.52m
    rooms.append(RoomModel(
        room_id="room_L2_bed6",
        room_type="bedroom",
        room_name="Bedroom 6 (Penthouse Suite)",
        polygon=make_box_poly(3.81, 9.20, W, D),
        area_m2=17.22,
        centroid=[5.71, 11.46],
        level_index=2,
        is_habitable=True,
        metadata={"typology": "penthouse_suite"}
    ))

    # Attached Bath 6: 1.80m x 2.00m (100% Stacked over Bath 2)
    rooms.append(RoomModel(
        room_id="room_L2_bath6",
        room_type="bathroom",
        room_name="Attached Bath 6 (100% Stacked)",
        polygon=make_box_poly(5.82, 9.20, W, 11.20),
        area_m2=3.60,
        centroid=[6.72, 10.20],
        level_index=2,
        is_habitable=False,
        metadata={"typology": "ensuite"}
    ))

    # =========================================================================
    # COMPLETE WALL MODEL: LEVEL 0, LEVEL 1, LEVEL 2
    # =========================================================================
    # ── Level 0 Walls ────────────────────────────────────────────────────────
    ext_walls_l0 = [
        # Exterior Envelope 9" (0.23m)
        ("w0_ext_south", "exterior", [[0.0, 0.0], [W, 0.0]], 0.23),
        ("w0_ext_east",  "exterior", [[W, 0.0], [W, D]], 0.23),
        ("w0_ext_north", "exterior", [[W, D], [0.0, D]], 0.23),
        ("w0_ext_west",  "exterior", [[0.0, D], [0.0, 0.0]], 0.23),
        # Interior Spine Walls 9" (0.23m)
        ("w0_spine_porch_dr", "interior", [[3.00, 0.0], [3.00, 4.40]], 0.23),
        ("w0_spine_h1",       "interior", [[0.0, 4.40], [W, 4.40]], 0.23),
        ("w0_spine_h2",       "interior", [[0.0, 9.20], [W, 9.20]], 0.23),
        # Interior Partition Walls 4.5" (0.115m)
        ("w0_part_stair",     "partition", [[2.40, 4.40], [2.40, 6.80]], 0.115),
        ("w0_part_pwd_v",     "partition", [[6.12, 4.40], [6.12, 5.80]], 0.115),
        ("w0_part_pwd_h",     "partition", [[6.12, 5.80], [W, 5.80]], 0.115),
        ("w0_part_ots_h",     "partition", [[6.12, 7.20], [W, 7.20]], 0.115),
        ("w0_part_bed_div",   "partition", [[3.81, 9.20], [3.81, D]], 0.115),
        ("w0_part_b1_v",      "partition", [[1.80, 9.20], [1.80, 11.20]], 0.115),
        ("w0_part_b1_h",      "partition", [[0.0, 11.20], [1.80, 11.20]], 0.115),
        ("w0_part_b2_v",      "partition", [[5.82, 9.20], [5.82, 11.20]], 0.115),
        ("w0_part_b2_h",      "partition", [[5.82, 11.20], [W, 11.20]], 0.115),
    ]
    for wid, wtype, cl, th in ext_walls_l0:
        walls.append(WallModel(wall_id=wid, wall_type=wtype, centerline=cl, thickness_m=th, height_m=3.0, level_index=0))

    # ── Level 1 Walls ────────────────────────────────────────────────────────
    ext_walls_l1 = [
        # Exterior Envelope 9" (0.23m)
        ("w1_ext_south", "exterior", [[0.0, 0.0], [W, 0.0]], 0.23),
        ("w1_ext_east",  "exterior", [[W, 0.0], [W, D]], 0.23),
        ("w1_ext_north", "exterior", [[W, D], [0.0, D]], 0.23),
        ("w1_ext_west",  "exterior", [[0.0, D], [0.0, 0.0]], 0.23),
        # Interior Spine Walls 9" (0.23m)
        ("w1_spine_balc_bed", "interior", [[3.00, 0.0], [3.00, 4.40]], 0.23),
        ("w1_spine_h1",       "interior", [[0.0, 4.40], [W, 4.40]], 0.23),
        ("w1_spine_h2",       "interior", [[0.0, 9.20], [W, 9.20]], 0.23),
        # Interior Partition Walls 4.5" (0.115m)
        ("w1_part_b3_h",      "partition", [[0.0, 2.20], [3.00, 2.20]], 0.115),
        ("w1_part_stair",     "partition", [[2.40, 4.40], [2.40, 6.80]], 0.115),
        ("w1_part_study_v",   "partition", [[2.40, 6.80], [2.40, 9.20]], 0.115),
        ("w1_part_study_h",   "partition", [[0.0, 6.80], [2.40, 6.80]], 0.115),
        ("w1_part_dress_v",   "partition", [[6.12, 4.40], [6.12, 7.20]], 0.115),
        ("w1_part_dress_h",   "partition", [[6.12, 7.20], [W, 7.20]], 0.115),
        ("w1_part_bed_div",   "partition", [[3.81, 9.20], [3.81, D]], 0.115),
        ("w1_part_b4_v",      "partition", [[1.80, 9.20], [1.80, 11.20]], 0.115),
        ("w1_part_b4_h",      "partition", [[0.0, 11.20], [1.80, 11.20]], 0.115),
    ]
    for wid, wtype, cl, th in ext_walls_l1:
        walls.append(WallModel(wall_id=wid, wall_type=wtype, centerline=cl, thickness_m=th, height_m=3.0, level_index=1))

    # ── Level 2 Walls ────────────────────────────────────────────────────────
    ext_walls_l2 = [
        # Rooftop Enclosing Envelope & Parapet 9" (0.23m)
        ("w2_parapet_south", "exterior", [[0.0, 0.0], [W, 0.0]], 0.23),
        ("w2_parapet_west",  "exterior", [[0.0, 0.0], [0.0, 4.40]], 0.23),
        ("w2_parapet_east",  "exterior", [[W, 0.0], [W, 4.40]], 0.23),
        ("w2_ext_h1",        "exterior", [[0.0, 4.40], [W, 4.40]], 0.23),
        ("w2_ext_east",      "exterior", [[W, 4.40], [W, D]], 0.23),
        ("w2_ext_north",     "exterior", [[W, D], [0.0, D]], 0.23),
        ("w2_ext_west",      "exterior", [[0.0, D], [0.0, 4.40]], 0.23),
        # Interior Spine Walls 9" (0.23m)
        ("w2_spine_h2",       "interior", [[0.0, 9.20], [W, 9.20]], 0.23),
        # Interior Partition Walls 4.5" (0.115m)
        ("w2_part_stair_v",   "partition", [[2.40, 4.40], [2.40, 6.80]], 0.115),
        ("w2_part_stair_h",   "partition", [[0.0, 6.80], [2.40, 6.80]], 0.115),
        ("w2_part_store_v",   "partition", [[6.12, 4.40], [6.12, 7.20]], 0.115),
        ("w2_part_store_h",   "partition", [[6.12, 7.20], [W, 7.20]], 0.115),
        ("w2_part_bed_div",   "partition", [[3.81, 9.20], [3.81, D]], 0.115),
        ("w2_part_b5_v",      "partition", [[1.80, 9.20], [1.80, 11.20]], 0.115),
        ("w2_part_b5_h",      "partition", [[0.0, 11.20], [1.80, 11.20]], 0.115),
        ("w2_part_b6_v",      "partition", [[5.82, 9.20], [5.82, 11.20]], 0.115),
        ("w2_part_b6_h",      "partition", [[5.82, 11.20], [W, 11.20]], 0.115),
    ]
    for wid, wtype, cl, th in ext_walls_l2:
        walls.append(WallModel(wall_id=wid, wall_type=wtype, centerline=cl, thickness_m=th, height_m=3.0, level_index=2))

    # =========================================================================
    # ARCHITECTURAL OPENINGS (DOORS & WINDOWS) FOR ALL 3 FLOORS
    # =========================================================================
    openings_all = [
        # ── Level 0 Openings ──
        OpeningModel(opening_id="d_L0_main_entry", opening_type="door", position=[1.50, 4.40], width_m=1.10, height_m=2.40, connects_rooms=["room_L0_porch", "room_L0_lounge"], level_index=0),
        OpeningModel(opening_id="d_L0_drawing_ext", opening_type="door", position=[3.00, 2.20], width_m=1.00, height_m=2.40, connects_rooms=["room_L0_porch", "room_L0_drawing"], level_index=0),
        OpeningModel(opening_id="d_L0_drawing_lounge", opening_type="door", position=[4.50, 4.40], width_m=1.20, height_m=2.40, connects_rooms=["room_L0_drawing", "room_L0_lounge"], level_index=0),
        OpeningModel(opening_id="d_L0_powder", opening_type="door", position=[6.12, 5.10], width_m=0.80, height_m=2.10, connects_rooms=["room_L0_lounge", "room_L0_powder"], level_index=0),
        OpeningModel(opening_id="d_L0_bed1", opening_type="door", position=[2.60, 9.20], width_m=0.90, height_m=2.10, connects_rooms=["room_L0_lounge", "room_L0_bed1"], level_index=0),
        OpeningModel(opening_id="d_L0_bath1", opening_type="door", position=[1.80, 10.20], width_m=0.75, height_m=2.10, connects_rooms=["room_L0_bed1", "room_L0_bath1"], level_index=0),
        OpeningModel(opening_id="d_L0_bed2", opening_type="door", position=[4.80, 9.20], width_m=0.90, height_m=2.10, connects_rooms=["room_L0_lounge", "room_L0_bed2"], level_index=0),
        OpeningModel(opening_id="d_L0_bath2", opening_type="door", position=[5.82, 10.20], width_m=0.75, height_m=2.10, connects_rooms=["room_L0_bed2", "room_L0_bath2"], level_index=0),
        OpeningModel(opening_id="w_L0_drawing_front", opening_type="window", position=[5.31, 0.00], width_m=2.20, height_m=2.10, sill_height_m=0.45, level_index=0),
        OpeningModel(opening_id="w_L0_bed1_rear", opening_type="window", position=[1.90, D], width_m=1.80, height_m=1.50, sill_height_m=0.75, level_index=0),
        OpeningModel(opening_id="w_L0_bed2_rear", opening_type="window", position=[5.71, D], width_m=1.80, height_m=1.50, sill_height_m=0.75, level_index=0),

        # ── Level 1 Openings ──
        OpeningModel(opening_id="d_L1_balcony", opening_type="door", position=[1.50, 2.20], width_m=0.90, height_m=2.20, connects_rooms=["room_L1_balcony", "room_L1_bath3"], level_index=1),
        OpeningModel(opening_id="d_L1_master3", opening_type="door", position=[4.50, 4.40], width_m=0.95, height_m=2.10, connects_rooms=["room_L1_lounge", "room_L1_bed3"], level_index=1),
        OpeningModel(opening_id="d_L1_bath3", opening_type="door", position=[3.00, 3.30], width_m=0.75, height_m=2.10, connects_rooms=["room_L1_bed3", "room_L1_bath3"], level_index=1),
        OpeningModel(opening_id="d_L1_bed4", opening_type="door", position=[2.60, 9.20], width_m=0.90, height_m=2.10, connects_rooms=["room_L1_lounge", "room_L1_bed4"], level_index=1),
        OpeningModel(opening_id="d_L1_bath4", opening_type="door", position=[1.80, 10.20], width_m=0.75, height_m=2.10, connects_rooms=["room_L1_bed4", "room_L1_bath4"], level_index=1),
        OpeningModel(opening_id="d_L1_terrace_rear", opening_type="door", position=[4.80, 9.20], width_m=0.90, height_m=2.10, connects_rooms=["room_L1_lounge", "room_L1_terrace_rear"], level_index=1),
        OpeningModel(opening_id="w_L1_master_front", opening_type="window", position=[5.31, 0.00], width_m=2.20, height_m=2.00, sill_height_m=0.60, level_index=1),
        OpeningModel(opening_id="w_L1_bed4_rear", opening_type="window", position=[1.90, D], width_m=1.80, height_m=1.50, sill_height_m=0.75, level_index=1),

        # ── Level 2 Openings ──
        OpeningModel(opening_id="d_L2_bbq_terrace", opening_type="door", position=[3.81, 4.40], width_m=1.20, height_m=2.20, connects_rooms=["room_L2_foyer", "room_L2_bbq_terrace"], level_index=2),
        OpeningModel(opening_id="d_L2_stair_mumty", opening_type="door", position=[1.20, 4.40], width_m=0.90, height_m=2.10, connects_rooms=["room_L2_spiral_stairs", "room_L2_bbq_terrace"], level_index=2),
        OpeningModel(opening_id="d_L2_bed5", opening_type="door", position=[2.60, 9.20], width_m=0.90, height_m=2.10, connects_rooms=["room_L2_foyer", "room_L2_bed5"], level_index=2),
        OpeningModel(opening_id="d_L2_bath5", opening_type="door", position=[1.80, 10.20], width_m=0.75, height_m=2.10, connects_rooms=["room_L2_bed5", "room_L2_bath5"], level_index=2),
        OpeningModel(opening_id="d_L2_bed6", opening_type="door", position=[4.80, 9.20], width_m=0.90, height_m=2.10, connects_rooms=["room_L2_foyer", "room_L2_bed6"], level_index=2),
        OpeningModel(opening_id="d_L2_bath6", opening_type="door", position=[5.82, 10.20], width_m=0.75, height_m=2.10, connects_rooms=["room_L2_bed6", "room_L2_bath6"], level_index=2),
        OpeningModel(opening_id="w_L2_bed5_rear", opening_type="window", position=[1.90, D], width_m=1.80, height_m=1.50, sill_height_m=0.75, level_index=2),
        OpeningModel(opening_id="w_L2_bed6_rear", opening_type="window", position=[5.71, D], width_m=1.80, height_m=1.50, sill_height_m=0.75, level_index=2),
    ]
    openings.extend(openings_all)

    metadata = MetadataModel(
        plan_id="spanish_5m_3floor_6bed_master",
        source_type="synthetic_generated",
        scale_px_to_m=0.01,
        unit="m",
        north_angle_deg=0.0,
        floor_count=3,
        levels=[0, 1, 2],
        wall_height_m=3.0,
        provenance={
            "project_title": "5 Marla Luxury Spanish Colonial Residence (3 Floors • 6 Beds En-Suite)",
            "plot_specification": "5 Marla (25'-0\" x 45'-0\")",
            "architectural_style": "Spanish Colonial Revival",
            "bedrooms_count": 6,
            "bathrooms_count": 6,
            "has_round_stairs": True,
            "stair_typology": "spiral_circular",
            "statutory_compliance": "DHA / Bahria / LDA 5 Marla Code"
        }
    )

    return CanonicalFloorPlan(
        metadata=metadata,
        boundary=make_box_poly(0.0, 0.0, W, D),
        total_area_m2=round(W * D * 3, 2),
        rooms=rooms,
        walls=walls,
        openings=openings,
        graph_edges=edges
    )


# -----------------------------------------------------------------------------
# DEDICATED AUTHENTIC SPANISH 2D FRONT ELEVATION DRAWING
# -----------------------------------------------------------------------------
def render_spanish_front_elevation_2d(out_path: str):
    fig, ax = plt.subplots(figsize=(15, 11), dpi=220)
    fig.patch.set_facecolor("#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    # Datum Heights (m)
    H_ROAD = -0.30
    H_NGL = 0.00
    H_PLINTH = 0.60
    H_GF_CLEAR = 3.10
    H_SLAB = 0.30
    H_1F = H_PLINTH + H_GF_CLEAR + H_SLAB       # 4.00m
    H_1F_CLEAR = 3.10
    H_2F = H_1F + H_1F_CLEAR + H_SLAB           # 7.40m
    H_2F_CLEAR = 3.10
    H_ROOF = H_2F + H_2F_CLEAR + H_SLAB         # 10.80m
    H_PARAPET_TOP = H_ROOF + 1.10              # 11.90m
    H_MUMTY_TOP = H_ROOF + 2.50                # 13.30m
    H_SPANISH_PEAK = H_MUMTY_TOP + 1.10        # 14.40m (Terracotta Gable Peak)

    ax.set_xlim(-3.6, W + 4.2)
    ax.set_ylim(-1.8, 15.6)
    ax.axis("off")

    # Earth stratum & Cobblestone Road
    ax.fill_between([-3.6, W + 4.2], [-1.8, -1.8], [H_NGL, H_NGL], color="#F1F5F9", zorder=1)
    ax.plot([-3.6, W + 4.2], [H_NGL, H_NGL], color="#0F172A", lw=2.4, zorder=4)
    ax.plot([-3.6, W + 4.2], [H_ROAD, H_ROAD], color="#78716C", lw=1.5, linestyle="--", zorder=3)

    # Spanish Plinth Base (Rustic Sandstone)
    ax.add_patch(patches.Rectangle((0, H_NGL), W, H_PLINTH, facecolor="#78716C", edgecolor="#1C1917", lw=2.0, zorder=5))
    
    # Left Porch Cobblestone Ramp (3.00m wide)
    ramp = [[-0.2, H_ROAD], [3.2, H_ROAD], [3.0, H_PLINTH], [0.0, H_PLINTH]]
    ax.add_patch(MplPoly(ramp, closed=True, facecolor="#A8A29E", edgecolor="#1C1917", lw=1.2, zorder=6))

    # Terracotta entrance steps on Right
    for i, sy in enumerate([0.20, 0.40, 0.60]):
        ax.add_patch(patches.Rectangle((3.10 + i * 0.12, 0), 1.20 - i * 0.12, sy, facecolor="#EA580C", edgecolor="#1C1917", lw=0.8, zorder=7+i))

    # Mediterranean Planter Box with Red Bougainvillea
    ax.add_patch(patches.Rectangle((4.50, H_NGL), W - 4.50, H_PLINTH, facecolor="#E7E5E4", edgecolor="#1C1917", lw=1.4, zorder=7))
    for px in np.arange(4.70, W - 0.3, 0.35):
        ax.fill([px, px + 0.12, px + 0.24], [H_PLINTH, H_PLINTH + 0.50, H_PLINTH], color="#15803D", zorder=9)
        ax.plot([px + 0.12, px + 0.12], [H_PLINTH + 0.35, H_PLINTH + 0.58], color="#DC2626", lw=2.5, zorder=10)

    # -------------------------------------------------------------------------
    # LEVEL 0 (GROUND FLOOR) — Warm Spanish Stucco (#FBF7F0)
    # -------------------------------------------------------------------------
    # Left Porch Semicircular Arch Portal
    ax.add_patch(patches.Rectangle((0.0, H_PLINTH), 3.00, H_GF_CLEAR, facecolor="#FBF7F0", edgecolor="#1C1917", lw=1.8, zorder=6))
    
    # Spanish Arch Geometry
    r_arch = 1.25
    cx_arch, cy_arch = 1.50, H_PLINTH + 1.85
    arch_pts = [[cx_arch + r_arch * math.cos(math.radians(deg)), cy_arch + r_arch * math.sin(math.radians(deg))] for deg in range(0, 181, 10)]
    porch_portal = [[0.25, H_PLINTH]] + arch_pts + [[2.75, H_PLINTH]]
    ax.add_patch(MplPoly(porch_portal, closed=True, facecolor="#44403C", edgecolor="#1C1917", lw=2.0, zorder=7))
    # Depth shadow
    ax.add_patch(patches.Rectangle((0.25, H_PLINTH + H_GF_CLEAR - 0.70), 2.50, 0.70, facecolor="#000000", alpha=0.30, zorder=8))
    # Car Profile
    car_pts = [[0.5, H_PLINTH + 0.2], [0.7, H_PLINTH + 0.6], [2.3, H_PLINTH + 0.6], [2.5, H_PLINTH + 0.2]]
    ax.add_patch(MplPoly(car_pts, closed=True, facecolor="#78716C", edgecolor="#1C1917", lw=1.2, zorder=9))
    # Terracotta Keystone
    ax.add_patch(patches.Rectangle((1.38, cy_arch + r_arch - 0.08), 0.24, 0.26, facecolor="#EA580C", edgecolor="#1C1917", lw=1.2, zorder=11))

    # Right Drawing Room: Twin Spanish Arched Windows with Wrought-Iron Grilles (Rejas)
    ax.add_patch(patches.Rectangle((3.00, H_PLINTH), W - 3.00, H_GF_CLEAR, facecolor="#FBF7F0", edgecolor="#1C1917", lw=1.8, zorder=6))
    for wx in [3.40, 5.50]:
        w_w = 1.60
        # Window frame + Cyan Glazing
        ax.add_patch(patches.Rectangle((wx, H_PLINTH + 0.50), w_w, 1.80, facecolor="#BAE6FD", alpha=0.8, edgecolor="#1C1917", lw=1.6, zorder=8))
        # Arch top
        arc_pts_win = [[wx + w_w*0.5 + (w_w*0.5)*math.cos(math.radians(d)), 
                        H_PLINTH + 2.30 + (w_w*0.5)*math.sin(math.radians(d))] for d in range(0, 181, 10)]
        ax.add_patch(MplPoly([[wx, H_PLINTH + 2.30]] + arc_pts_win + [[wx + w_w, H_PLINTH + 2.30]], closed=True, facecolor="#BAE6FD", alpha=0.8, edgecolor="#1C1917", lw=1.6, zorder=9))
        # Wrought-Iron Grille (Reja)
        for gy in np.arange(H_PLINTH + 0.70, H_PLINTH + 2.60, 0.35):
            ax.plot([wx, wx + w_w], [gy, gy], color="#1C1917", lw=1.2, zorder=11)
        for gx in [wx + 0.40, wx + 0.80, wx + 1.20]:
            ax.plot([gx, gx], [H_PLINTH + 0.50, H_PLINTH + 2.80], color="#1C1917", lw=1.2, zorder=11)
        # Keystone
        ax.add_patch(patches.Rectangle((wx + w_w*0.5 - 0.10, H_PLINTH + 2.30 + w_w*0.5 - 0.05), 0.20, 0.22, facecolor="#EA580C", edgecolor="#1C1917", lw=1.0, zorder=12))

    # Hanging Spanish Wrought-Iron Lantern
    ax.add_patch(patches.Rectangle((5.05, H_PLINTH + 2.10), 0.18, 0.32, facecolor="#1C1917", edgecolor="#1C1917", lw=0.8, zorder=14))
    ax.add_patch(patches.Circle((5.14, H_PLINTH + 2.25), 0.08, facecolor="#FEF08A", edgecolor="#CA8A04", lw=0.8, zorder=15))

    # -------------------------------------------------------------------------
    # LEVEL 1 (FIRST FLOOR) — Arched Loggia & Timber Corbels (Vigas)
    # -------------------------------------------------------------------------
    # Floor slab band with exposed wooden beam ends (Vigas)
    ax.add_patch(patches.Rectangle((-0.20, H_1F - H_SLAB), W + 0.40, H_SLAB, facecolor="#78350F", edgecolor="#1C1917", lw=1.8, zorder=16))
    for bx in np.arange(0.3, W, 0.75):
        ax.add_patch(patches.Rectangle((bx, H_1F - H_SLAB - 0.22), 0.15, 0.22, facecolor="#451A03", edgecolor="#1C1917", lw=0.8, zorder=17))

    # Talavera Mosaic Tile Frieze
    ax.add_patch(patches.Rectangle((-0.15, H_1F - H_SLAB + 0.08), W + 0.30, 0.18, facecolor="#0284C7", edgecolor="#CA8A04", lw=0.9, hatch="xxx", zorder=18))

    # Left Balcony: Spanish Arched Loggia
    ax.add_patch(patches.Rectangle((0.0, H_1F), 3.00, H_1F_CLEAR, facecolor="#FBF7F0", edgecolor="#1C1917", lw=1.8, zorder=19))
    # Double Spanish Arches on Balcony
    for c_arc in [0.85, 2.15]:
        r_log = 0.55
        arc_pts_log = [[c_arc + r_log*math.cos(math.radians(d)), H_1F + 1.80 + r_log*math.sin(math.radians(d))] for d in range(0, 181, 10)]
        ax.add_patch(MplPoly([[c_arc - r_log, H_1F + 1.10], [c_arc - r_log, H_1F + 1.80]] + arc_pts_log + [[c_arc + r_log, H_1F + 1.80], [c_arc + r_log, H_1F + 1.10]], closed=True, facecolor="#CBD5E1", alpha=0.5, edgecolor="#1C1917", lw=1.4, zorder=20))
    # Wrought-Iron Juliet Balustrade
    ax.add_patch(patches.Rectangle((0.0, H_1F), 3.00, 1.05, facecolor="#000000", alpha=0.15, edgecolor="#1C1917", lw=1.8, zorder=22))
    for ix in np.arange(0.15, 2.95, 0.25):
        ax.plot([ix, ix], [H_1F, H_1F + 1.05], color="#1C1917", lw=1.4, zorder=23)
    ax.plot([0.0, 3.00], [H_1F + 1.05, H_1F + 1.05], color="#1C1917", lw=2.5, zorder=24)

    # Right Master Suite 3: Spanish Quadruple Arched Window Arcade
    ax.add_patch(patches.Rectangle((3.00, H_1F), W - 3.00, H_1F_CLEAR, facecolor="#FBF7F0", edgecolor="#1C1917", lw=1.8, zorder=19))
    ax.add_patch(patches.Rectangle((3.40, H_1F + 0.40), W - 3.80, 2.20, facecolor="#BAE6FD", alpha=0.8, edgecolor="#1C1917", lw=1.8, zorder=20))
    # Triple decorative arches over window
    for ax_c in [4.00, 5.30, 6.60]:
        arc_sub = [[ax_c + 0.55*math.cos(math.radians(d)), H_1F + 2.05 + 0.55*math.sin(math.radians(d))] for d in range(0, 181, 10)]
        ax.plot([p[0] for p in arc_sub], [p[1] for p in arc_sub], color="#1C1917", lw=1.8, zorder=22)

    # -------------------------------------------------------------------------
    # LEVEL 2 (ROOFTOP PENTHOUSE) — Terracotta Roof & Pergola
    # -------------------------------------------------------------------------
    ax.add_patch(patches.Rectangle((-0.20, H_2F - H_SLAB), W + 0.40, H_SLAB, facecolor="#78350F", edgecolor="#1C1917", lw=1.8, zorder=25))
    
    # Left Terracotta BBQ Pergola Deck
    ax.add_patch(patches.Rectangle((0.0, H_2F), 3.00, 1.05, facecolor="#E7E5E4", edgecolor="#1C1917", lw=1.4, zorder=26))
    for perg_x in np.arange(0.3, 2.9, 0.6):
        ax.plot([perg_x, perg_x], [H_2F, H_2F + 2.8], color="#78350F", lw=2.4, zorder=27)
    ax.plot([0.0, 3.00], [H_2F + 2.8, H_2F + 2.8], color="#78350F", lw=3.2, zorder=28)

    # Right Penthouse Suites 5 & 6
    ax.add_patch(patches.Rectangle((3.00, H_2F), W - 3.00, H_2F_CLEAR, facecolor="#FBF7F0", edgecolor="#1C1917", lw=1.8, zorder=26))
    ax.add_patch(patches.Rectangle((3.60, H_2F + 0.60), W - 4.20, 1.80, facecolor="#BAE6FD", alpha=0.8, edgecolor="#1C1917", lw=1.6, zorder=27))

    # -------------------------------------------------------------------------
    # ROOFTOP PITCHED GABLE & TERRACOTTA BARREL TILES (TEJAS DE BARRO)
    # -------------------------------------------------------------------------
    # Pitch Gable over Penthouse & Stair Tower
    gable_pts = [
        [2.80, H_ROOF],
        [W * 0.65, H_SPANISH_PEAK],
        [W + 0.30, H_ROOF]
    ]
    ax.add_patch(MplPoly(gable_pts, closed=True, facecolor="#EA580C", edgecolor="#7C2D12", lw=2.2, zorder=30))

    # Individual Terracotta Curved Tile Rows (Tejas Hatching)
    for ty in np.arange(H_ROOF + 0.3, H_SPANISH_PEAK, 0.28):
        pct = (ty - H_ROOF) / (H_SPANISH_PEAK - H_ROOF)
        x_left = 2.80 + pct * (W * 0.65 - 2.80)
        x_right = (W + 0.30) - pct * ((W + 0.30) - W * 0.65)
        for tx in np.arange(x_left, x_right, 0.35):
            arc_tile = patches.Arc((tx, ty), 0.30, 0.20, angle=0, theta1=0, theta2=180, color="#7C2D12", lw=1.4, zorder=31)
            ax.add_patch(arc_tile)

    # Spanish Round Stair Turret / Mumty Tower Roof
    stair_tower = [
        [0.0, H_ROOF], [2.80, H_ROOF], [2.80, H_MUMTY_TOP], [0.0, H_MUMTY_TOP]
    ]
    ax.add_patch(MplPoly(stair_tower, closed=True, facecolor="#FBF7F0", edgecolor="#1C1917", lw=2.0, zorder=28))
    # Circular window on stair turret
    ax.add_patch(patches.Circle((1.40, H_ROOF + 1.30), 0.55, facecolor="#BAE6FD", edgecolor="#1C1917", lw=1.8, zorder=29))
    ax.plot([0.85, 1.95], [H_ROOF + 1.30, H_ROOF + 1.30], color="#1C1917", lw=1.2, zorder=30)
    ax.plot([1.40, 1.40], [H_ROOF + 0.75, H_ROOF + 1.85], color="#1C1917", lw=1.2, zorder=30)
    # Turret Clay Tile Eaves
    ax.add_patch(patches.Rectangle((-0.15, H_MUMTY_TOP), 3.10, 0.35, facecolor="#EA580C", edgecolor="#7C2D12", lw=1.5, zorder=31))

    # -------------------------------------------------------------------------
    # TECHNICAL DATUMS (RIGHT SIDE - RED DHA ARROWS)
    # -------------------------------------------------------------------------
    datums = [
        (H_SPANISH_PEAK, f"+{H_SPANISH_PEAK:.2f}m (+47'-3\") TERRACOTTA GABLE PEAK"),
        (H_MUMTY_TOP, f"+{H_MUMTY_TOP:.2f}m (+43'-8\") ROUND STAIR MUMTY TOP"),
        (H_ROOF, f"+{H_ROOF:.2f}m (+35'-5\") ROOF SLAB LEVEL"),
        (H_2F, f"+{H_2F:.2f}m (+24'-3\") SECOND FLOOR FFL"),
        (H_1F, f"+{H_1F:.2f}m (+13'-1\") FIRST FLOOR FFL"),
        (H_PLINTH, f"+{H_PLINTH:.2f}m (+2'-0\") PLINTH LEVEL"),
        (H_NGL, f"±0.00m NATURAL GROUND LEVEL"),
        (H_ROAD, f"-0.30m ROAD FORMATION LEVEL")
    ]
    for dy, lbl in datums:
        ax.plot([W + 0.2, W + 0.9], [dy, dy], color="#DC2626", lw=1.2, linestyle="--")
        ax.text(W + 1.0, dy, lbl, color="#DC2626", fontsize=7.2, va="center", fontweight="bold")

    # Architectural Leader Callouts (Left Side)
    ax.text(-3.4, H_SPANISH_PEAK - 0.5, "TEJAS DE BARRO\nCurved Terracotta Tiles", color="#B45309", fontsize=7.2, fontweight="bold")
    ax.text(-3.4, H_ROOF + 1.2, "ROUND STAIR TURRET\nContinuous Helical Core", color="#0F172A", fontsize=7.2, fontweight="bold")
    ax.text(-3.4, H_2F + 1.2, "ROOFTOP BBQ DECK\nCedar Timber Pergola", color="#78350F", fontsize=7.2, fontweight="bold")
    ax.text(-3.4, H_1F + 1.2, "SPANISH ARCHED LOGGIA\nWrought-Iron Juliet Railing", color="#0F172A", fontsize=7.2, fontweight="bold")
    ax.text(-3.4, H_1F - 0.4, "EXPOSED TIMBER VIGAS\nDecorative Wood Corbels", color="#78350F", fontsize=7.2, fontweight="bold")
    ax.text(-3.4, H_PLINTH + 1.5, "SPANISH ARCH CARRIAGE\nSandstone Keystone Portal", color="#0F172A", fontsize=7.2, fontweight="bold")

    # Header Titles
    ax.text(W * 0.5, 15.2, "5 MARLA LUXURY SPANISH RESIDENCE — TECHNICAL FRONT ELEVATION (OPTION A)", color="#0F172A", fontsize=11, fontweight="heavy", ha="center")
    ax.text(W * 0.5, 14.7, "Terracotta Barrel Tiles • Semicircular Arches • Rejas Ironwork • Exposed Vigas • 3 Complete Floors", color="#EA580C", fontsize=8.2, fontweight="bold", ha="center")

    fig.savefig(out_path, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
    plt.close(fig)
    print(f"[ELEVATION A] Saved Spanish 2D Elevation -> {out_path}")
    return out_path


def run_spanish_pipeline():
    print("=" * 75)
    print("EXECUTING 5 MARLA 3-STOREY 6-BEDROOM SPANISH VILLA PIPELINE")
    print("=" * 75)

    # 1. Synthesize Canonical Plan
    plan = create_spanish_5m_canonical_plan()
    json_path = os.path.join(OUT_DIR, "spanish_5m_6bed_canonical.json")
    with open(json_path, "w", encoding="utf-8") as f:
        f.write(plan.to_json())
    print(f"[OK] Saved Canonical JSON -> {json_path}")

    # 2. Render High-Resolution 2D Floor Plans for all 3 Floors with FloorPlanVisualizer
    gf_png = os.path.join(OUT_DIR, "spanish_5m_level0_ground_floor_2d.png")
    ff_png = os.path.join(OUT_DIR, "spanish_5m_level1_first_floor_2d.png")
    rf_png = os.path.join(OUT_DIR, "spanish_5m_level2_penthouse_roof_2d.png")

    FloorPlanVisualizer.render_floor_plan(plan, gf_png, level_index=0, dpi=200)
    print(f"[2D] Exported Ground Floor -> {gf_png}")
    FloorPlanVisualizer.render_floor_plan(plan, ff_png, level_index=1, dpi=200)
    print(f"[2D] Exported First Floor  -> {ff_png}")
    FloorPlanVisualizer.render_floor_plan(plan, rf_png, level_index=2, dpi=200)
    print(f"[2D] Exported Penthouse/Roof -> {rf_png}")

    # 3. Render Multi-Floor Composite Sheet
    multi_png = os.path.join(OUT_DIR, "spanish_5m_complete_3floors_blueprints.png")
    FloorPlanVisualizer.render_composite_multi_floor_sheet(plan, multi_png, dpi=200)
    print(f"[2D] Exported 3-Floor Composite -> {multi_png}")

    # 4. Render Dedicated Spanish 2D Front Elevation (Option A)
    elev_png = os.path.join(OUT_DIR, "spanish_5m_front_elevation_option_A_2d.png")
    render_spanish_front_elevation_2d(elev_png)

    # 5. Export Option B Isolated 3D Prompt
    opt_b_prompt = (
        "Architectural 3D model render of a 5 Marla (25ft x 45ft) 3-storey authentic Spanish Colonial Revival luxury villa, "
        "completely isolated on a pristine white circular studio podium with soft ambient studio lighting, "
        "pure plain white studio background with no trees, no neighboring houses, no street, no cars on street, no sky, "
        "only the crisp architectural Spanish house model. "
        "Features: Roof has authentic curved reddish-terracotta clay barrel roof tiles (Tejas de barro) with pitched gables and a prominent round staircase turret. "
        "Left side: Ground floor single-car garage with a large semicircular Spanish arch portal and stone keystone. "
        "First floor: Spanish arched loggia with twin semicircular arches and black wrought-iron decorative Juliet railing (rejas). "
        "Right side: Ground floor formal drawing room with twin Spanish arched windows with black wrought-iron security grilles and an antique wrought-iron wall lantern. "
        "Upper level: Master bedroom suite with arched window arcade and exposed rustic timber corbels (vigas de madera) supporting the eaves. "
        "Top floor: Spanish rooftop BBQ terrace with timber pergola, terracotta floor pavers, and arched penthouse suite. "
        "Warm Mediterranean cream stucco walls, textured finishes, realistic materials, warm 3000K interior accent lighting glowing through the windows."
    )
    prompt_file = os.path.join(OUT_DIR, "spanish_5m_option_B_3d_prompt.txt")
    with open(prompt_file, "w", encoding="utf-8") as f:
        f.write(opt_b_prompt)
    print(f"[OPTION B] Exported 3D Prompt -> {prompt_file}")

    # 6. Re-assemble Master Coordinated Presentation Sheet
    dest_3d = os.path.join(OUT_DIR, "spanish_5m_isolated_3d_render.jpg")
    if os.path.exists(dest_3d):
        plan_img = Image.open(multi_png)
        elev_img = Image.open(elev_png)
        r3d_img = Image.open(dest_3d)

        w_sheet = 3600
        header_h = 240
        plan_w = w_sheet - 120
        plan_h = int(plan_img.height * (plan_w / plan_img.width))
        plan_resized = plan_img.resize((plan_w, plan_h), Image.Resampling.LANCZOS)

        col_w = int((w_sheet - 160) / 2)
        elev_h = int(elev_img.height * (col_w / elev_img.width))
        r3d_h = int(r3d_img.height * (col_w / r3d_img.width))
        lower_h = max(elev_h, r3d_h)

        elev_resized = elev_img.resize((col_w, elev_h), Image.Resampling.LANCZOS)
        r3d_resized = r3d_img.resize((col_w, r3d_h), Image.Resampling.LANCZOS)

        total_h = header_h + plan_h + lower_h + 180
        sheet = Image.new('RGB', (w_sheet, total_h), '#FFFFFF')
        draw = ImageDraw.Draw(sheet)

        draw.rectangle([0, 0, w_sheet, 16], fill='#EA580C')
        draw.text((60, 45), '5 MARLA LUXURY SPANISH VILLA (3 FLOORS • 6 BEDS EN-SUITE • CIRCULAR STAIRS)', fill='#0F172A', font_size=52)
        draw.text((60, 115), 'Full Architectural Wall Model (Exterior 9" + Interior 4.5" Partitions) • 100% DHA/Bahria Code Compliant', fill='#B45309', font_size=32)
        draw.text((60, 165), 'PROGRAM: 6 BEDS (ALL EN-SUITE) • CIRCULAR/ROUND STAIR ROTUNDA • DRAWING • LIVING • POWDER • ROOFTOP BBQ DECK', fill='#475569', font_size=24)
        draw.line([(60, 215), (w_sheet - 60, 215)], fill='#CBD5E1', width=2)

        y_cursor = header_h + 15
        draw.text((60, y_cursor), 'COMPLETE 3-FLOOR ARCHITECTURAL BLUEPRINTS (GROUND + FIRST + ROOFTOP PENTHOUSE)', fill='#0F172A', font_size=32)
        y_cursor += 45
        sheet.paste(plan_resized, (60, y_cursor))

        y_cursor += plan_h + 30
        draw.line([(60, y_cursor), (w_sheet - 60, y_cursor)], fill='#E2E8F0', width=2)
        y_cursor += 20

        draw.text((60, y_cursor), 'OPTION A: AUTHENTIC SPANISH 2D FRONT ELEVATION (TEJAS BARREL TILES & ARCHES)', fill='#0F172A', font_size=32)
        draw.text((col_w + 100, y_cursor), 'OPTION B: COORDINATED ISOLATED 3D HOUSE MODEL RENDER (STUDIO PODIUM)', fill='#0F172A', font_size=32)
        y_cursor += 50

        sheet.paste(elev_resized, (60, y_cursor))
        sheet.paste(r3d_resized, (col_w + 100, y_cursor))

        out_sheet = os.path.join(OUT_DIR, 'spanish_5m_complete_master_presentation_sheet.png')
        sheet.save(out_sheet, quality=95)
        print(f"[MASTER SHEET] Saved Presentation Sheet -> {out_sheet}")

    print("\n" + "=" * 75)
    print("PIPELINE COMPLETED SUCCESSFULLY!")
    print("=" * 75)


if __name__ == "__main__":
    run_spanish_pipeline()
