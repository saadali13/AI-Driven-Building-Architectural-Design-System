"""
Phase 11: Professional DHA Islamabad 10 Marla (35' x 65') Architectural Engine.
Implements the authentic 2-storey Pakistani/DHA Islamabad architectural archetype:
- Ground Floor & First Floor structural wall alignment.
- Exact vertical staircase alignment:
  Staircase on Ground Floor matches the Staircase Landing on First Floor in position and dimension.
- 6 Bedrooms with dedicated ensuite attached bathrooms + modern walk-in wardrobes/cabinets.
- Zone 1 (Front): Car Porch (Garage), Formal Drawing Room, Entrance Foyer, Powder Room.
- Zone 2 (Middle): Central TV Lounge, Modern USA-Style Open Kitchen with Island, Dining Room, Double Stairs.
- Zone 3 (Rear): Family Bedrooms with Walk-in Dressing and Ensuite Luxury Bathrooms.
"""

import os
import json
from typing import Dict, List, Tuple, Any, Optional
from shapely.geometry import Polygon
from dataset.schema.canonical import (
    CanonicalFloorPlan,
    MetadataModel,
    WallModel,
    OpeningModel,
    RoomModel,
    GraphEdgeModel
)
from extraction.relationships import SpatialRelationshipGraphExtractor


class DHA10MarlaArchitecturalEngine:
    """
    Standard DHA Islamabad 10 Marla Plot: 35'-0" x 65'-0" (10.67m x 19.81m).
    Covered buildable width: 9.75m (32'-0" leaving 3' side passages).
    Covered buildable depth: 16.00m (52'-6" leaving 8' front & 4'6" rear setbacks).
    """

    @classmethod
    def generate_10_marla_house(cls, plan_id: str = "dha_10m_modern") -> CanonicalFloorPlan:
        # Standard metric coordinates (meters):
        # X: 0.0m to 9.75m (Width)
        # Y: 0.0m to 16.00m (Depth from Front Y=0 to Rear Y=16.0)

        # Coordinate Keypoints:
        x0 = 0.0
        x_split = 4.25   # Divides Left Bay (Porch/Kitchen/Bed1) from Right Bay (Drawing/Lounge/Bed2)
        x_stair = 4.25   # Center stair placement
        x_end = 9.75     # Right edge

        y_front = 0.0    # Porch / Drawing
        y_porch_end = 4.80 # End of Porch / Drawing
        y_mid_split = 10.50 # End of TV Lounge / Dining / Kitchen
        y_rear = 16.00   # End of Rear Bedrooms

        rooms: List[RoomModel] = []
        walls: List[WallModel] = []
        openings: List[OpeningModel] = []

        wall_counter = 1
        opening_counter = 1

        # =========================================================================
        # LEVEL 0: GROUND FLOOR
        # =========================================================================
        # 1. Car Porch / Double Garage (Front-Left: x in [0, 4.25], y in [0, 4.8])
        porch_poly = [[x0, y_front], [x_split, y_front], [x_split, y_porch_end], [x0, y_porch_end], [x0, y_front]]
        rooms.append(RoomModel(
            room_id="room_L0_porch",
            room_type="garage",
            room_name="Car Porch (2 Cars)",
            polygon=porch_poly,
            area_m2=round(4.25 * 4.8, 1), # 20.4 m2 / 220 sqft
            centroid=[round(x0 + 4.25/2, 2), round(y_front + 4.8/2, 2)],
            level_index=0,
            is_habitable=False
        ))

        # 2. Drawing Room (Formal Living) (Front-Right: x in [4.25, 9.75], y in [0, 4.8])
        drawing_poly = [[x_split, y_front], [x_end, y_front], [x_end, y_porch_end], [x_split, y_porch_end], [x_split, y_front]]
        rooms.append(RoomModel(
            room_id="room_L0_drawing",
            room_type="living_room",
            room_name="Drawing Room (Formal)",
            polygon=drawing_poly,
            area_m2=round(5.50 * 4.8, 1), # 26.4 m2 / 284 sqft
            centroid=[round(x_split + 5.5/2, 2), round(y_front + 4.8/2, 2)],
            level_index=0,
            is_habitable=True
        ))

        # 3. Main Entrance Foyer & Double Stair Lobby (Central: x in [4.25, 6.75], y in [4.8, 7.8])
        # STAIRCASE LOCATION: EXACTLY AT x in [4.25, 6.75], y in [4.8, 7.8]
        stair_poly = [[x_split, y_porch_end], [x_split + 2.50, y_porch_end], [x_split + 2.50, 7.80], [x_split, 7.80], [x_split, y_porch_end]]
        rooms.append(RoomModel(
            room_id="room_L0_stairs",
            room_type="corridor",
            room_name="Double Stair Lobby (UP ->)",
            polygon=stair_poly,
            area_m2=round(2.50 * 3.00, 1), # 7.5 m2 / 81 sqft
            centroid=[round(x_split + 1.25, 2), round(y_porch_end + 1.50, 2)],
            level_index=0,
            is_habitable=False
        ))

        # 4. Guest Powder Room (Adjacent to stairs: x in [4.25, 6.75], y in [7.8, 9.0])
        powder_poly = [[x_split, 7.80], [x_split + 2.50, 7.80], [x_split + 2.50, 9.20], [x_split, 9.20], [x_split, 7.80]]
        rooms.append(RoomModel(
            room_id="room_L0_powder",
            room_type="bathroom",
            room_name="Powder Room",
            polygon=powder_poly,
            area_m2=round(2.50 * 1.40, 1), # 3.5 m2 / 38 sqft
            centroid=[round(x_split + 1.25, 2), round(7.80 + 0.70, 2)],
            level_index=0,
            is_habitable=False
        ))

        # 5. Dining Room (Mid-Left: x in [0, 4.25], y in [4.8, 8.0])
        dining_poly = [[x0, y_porch_end], [x_split, y_porch_end], [x_split, 8.00], [x0, 8.00], [x0, y_porch_end]]
        rooms.append(RoomModel(
            room_id="room_L0_dining",
            room_type="dining_room",
            room_name="Dining Room",
            polygon=dining_poly,
            area_m2=round(4.25 * 3.20, 1), # 13.6 m2 / 146 sqft
            centroid=[round(x0 + 4.25/2, 2), round(y_porch_end + 1.60, 2)],
            level_index=0,
            is_habitable=True
        ))

        # 6. Modern USA Open Kitchen with Island & Cabinets (Mid-Left: x in [0, 4.25], y in [8.0, 11.2])
        kitchen_poly = [[x0, 8.00], [x_split, 8.00], [x_split, 11.20], [x0, 11.20], [x0, 8.00]]
        rooms.append(RoomModel(
            room_id="room_L0_kitchen",
            room_type="kitchen",
            room_name="Modern USA Kitchen (Island & Cabinets)",
            polygon=kitchen_poly,
            area_m2=round(4.25 * 3.20, 1), # 13.6 m2 / 146 sqft
            centroid=[round(x0 + 4.25/2, 2), round(8.00 + 1.60, 2)],
            level_index=0,
            is_habitable=True
        ))

        # 7. Central Family TV Lounge (Mid-Right: x in [6.75, 9.75], y in [4.8, 11.2])
        tv_lounge_poly = [[x_split + 2.50, y_porch_end], [x_end, y_porch_end], [x_end, 11.20], [x_split + 2.50, 11.20], [x_split + 2.50, y_porch_end]]
        rooms.append(RoomModel(
            room_id="room_L0_tv_lounge",
            room_type="living_room",
            room_name="Central Family TV Lounge",
            polygon=tv_lounge_poly,
            area_m2=round(3.00 * 6.40, 1), # 19.2 m2 / 207 sqft
            centroid=[round(x_split + 2.50 + 1.50, 2), round(y_porch_end + 3.20, 2)],
            level_index=0,
            is_habitable=True
        ))

        # 8. Ground Bedroom 1 (Rear-Left: x in [0, 4.875], y in [11.2, 16.0] with attached bath)
        # Bedroom space: y in [11.2, 14.5], Bath + Dress: y in [14.5, 16.0]
        gbed1_poly = [[x0, 11.20], [4.875, 11.20], [4.875, 14.50], [x0, 14.50], [x0, 11.20]]
        rooms.append(RoomModel(
            room_id="room_L0_bed1",
            room_type="bedroom",
            room_name="Ground Bedroom 1 (with Wardrobes)",
            polygon=gbed1_poly,
            area_m2=round(4.875 * 3.30, 1), # 16.1 m2 / 173 sqft
            centroid=[round(4.875/2, 2), round(11.20 + 1.65, 2)],
            level_index=0,
            is_habitable=True
        ))
        # Attached Bath 1 + Dress
        gbath1_poly = [[x0, 14.50], [4.875, 14.50], [4.875, y_rear], [x0, y_rear], [x0, 14.50]]
        rooms.append(RoomModel(
            room_id="room_L0_bath1",
            room_type="bathroom",
            room_name="Attached Bath 1 (Dress & Bath)",
            polygon=gbath1_poly,
            area_m2=round(4.875 * 1.50, 1), # 7.3 m2 / 79 sqft
            centroid=[round(4.875/2, 2), round(14.50 + 0.75, 2)],
            level_index=0,
            is_habitable=False
        ))

        # 9. Ground Bedroom 2 (Rear-Right: x in [4.875, 9.75], y in [11.2, 16.0] with attached bath)
        gbed2_poly = [[4.875, 11.20], [x_end, 11.20], [x_end, 14.50], [4.875, 14.50], [4.875, 11.20]]
        rooms.append(RoomModel(
            room_id="room_L0_bed2",
            room_type="bedroom",
            room_name="Ground Bedroom 2 (with Wardrobes)",
            polygon=gbed2_poly,
            area_m2=round(4.875 * 3.30, 1), # 16.1 m2 / 173 sqft
            centroid=[round(4.875 + 4.875/2, 2), round(11.20 + 1.65, 2)],
            level_index=0,
            is_habitable=True
        ))
        # Attached Bath 2 + Dress
        gbath2_poly = [[4.875, 14.50], [x_end, 14.50], [x_end, y_rear], [4.875, y_rear], [4.875, 14.50]]
        rooms.append(RoomModel(
            room_id="room_L0_bath2",
            room_type="bathroom",
            room_name="Attached Bath 2 (Dress & Bath)",
            polygon=gbath2_poly,
            area_m2=round(4.875 * 1.50, 1), # 7.3 m2 / 79 sqft
            centroid=[round(4.875 + 4.875/2, 2), round(14.50 + 0.75, 2)],
            level_index=0,
            is_habitable=False
        ))

        # =========================================================================
        # LEVEL 1: FIRST FLOOR (Exact Structural Alignment with Ground Floor)
        # =========================================================================
        # 10. EXACT MATCHING STAIRCASE LANDING on First Floor!
        # Same coordinates: x in [4.25, 6.75], y in [4.8, 7.8]
        f_stair_poly = [[x_split, y_porch_end], [x_split + 2.50, y_porch_end], [x_split + 2.50, 7.80], [x_split, 7.80], [x_split, y_porch_end]]
        rooms.append(RoomModel(
            room_id="room_L1_stairs",
            room_type="corridor",
            room_name="Upper Stair Lobby (UP to Roof)",
            polygon=f_stair_poly,
            area_m2=round(2.50 * 3.00, 1),
            centroid=[round(x_split + 1.25, 2), round(y_porch_end + 1.50, 2)],
            level_index=1,
            is_habitable=False
        ))

        # 11. First Floor Central Family TV Lounge (Sitting over Ground Lounge: x in [6.75, 9.75], y in [4.8, 11.2])
        f_lounge_poly = [[x_split + 2.50, y_porch_end], [x_end, y_porch_end], [x_end, 11.20], [x_split + 2.50, 11.20], [x_split + 2.50, y_porch_end]]
        rooms.append(RoomModel(
            room_id="room_L1_tv_lounge",
            room_type="living_room",
            room_name="First Floor TV Lounge / Gallery",
            polygon=f_lounge_poly,
            area_m2=round(3.00 * 6.40, 1),
            centroid=[round(x_split + 2.50 + 1.50, 2), round(y_porch_end + 3.20, 2)],
            level_index=1,
            is_habitable=True
        ))

        # 12. Master Bedroom Suite 1 (Front-Right above Drawing: x in [4.25, 9.75], y in [0, 4.8])
        # Bedroom: y in [1.5, 4.8], Master Bath + Walk-in Wardrobe: y in [0, 1.5]
        f_bed1_poly = [[x_split, 1.50], [x_end, 1.50], [x_end, y_porch_end], [x_split, y_porch_end], [x_split, 1.50]]
        rooms.append(RoomModel(
            room_id="room_L1_master",
            room_type="bedroom",
            room_name="Master Suite 1 (Modern Walk-in Cabinets)",
            polygon=f_bed1_poly,
            area_m2=round(5.50 * 3.30, 1), # 18.2 m2 / 196 sqft
            centroid=[round(x_split + 5.5/2, 2), round(1.50 + 1.65, 2)],
            level_index=1,
            is_habitable=True
        ))
        f_bath1_poly = [[x_split, y_front], [x_end, y_front], [x_end, 1.50], [x_split, 1.50], [x_split, y_front]]
        rooms.append(RoomModel(
            room_id="room_L1_master_bath",
            room_type="bathroom",
            room_name="Master Luxury Bath (Jacuzzi & Dress)",
            polygon=f_bath1_poly,
            area_m2=round(5.50 * 1.50, 1), # 8.3 m2 / 89 sqft
            centroid=[round(x_split + 5.5/2, 2), round(y_front + 0.75, 2)],
            level_index=1,
            is_habitable=False
        ))

        # 13. First Bedroom 3 (Front-Left above Porch: x in [0, 4.25], y in [1.8, 4.8])
        # Leaves front Y in [0, 1.8] as Front Open Terrace / Balcony!
        f_terrace_poly = [[x0, y_front], [x_split, y_front], [x_split, 1.80], [x0, 1.80], [x0, y_front]]
        rooms.append(RoomModel(
            room_id="room_L1_terrace",
            room_type="balcony",
            room_name="Front Open Terrace / Balcony",
            polygon=f_terrace_poly,
            area_m2=round(4.25 * 1.80, 1), # 7.7 m2 / 82 sqft
            centroid=[round(x0 + 4.25/2, 2), round(y_front + 0.90, 2)],
            level_index=1,
            is_habitable=False
        ))
        f_bed3_poly = [[x0, 1.80], [x_split, 1.80], [x_split, y_porch_end], [x0, y_porch_end], [x0, 1.80]]
        rooms.append(RoomModel(
            room_id="room_L1_bed3",
            room_type="bedroom",
            room_name="First Bedroom 3 (with Modern Cabinets)",
            polygon=f_bed3_poly,
            area_m2=round(4.25 * 3.00, 1), # 12.8 m2 / 137 sqft
            centroid=[round(x0 + 4.25/2, 2), round(1.80 + 1.50, 2)],
            level_index=1,
            is_habitable=True
        ))
        # Attached Bath 3 (Sitting above Powder/Stair side: x in [4.25, 6.75], y in [7.8, 9.2])
        f_bath3_poly = [[x_split, 7.80], [x_split + 2.50, 7.80], [x_split + 2.50, 9.20], [x_split, 9.20], [x_split, 7.80]]
        rooms.append(RoomModel(
            room_id="room_L1_bath3",
            room_type="bathroom",
            room_name="Attached Bath 3",
            polygon=f_bath3_poly,
            area_m2=round(2.50 * 1.40, 1), # 3.5 m2 / 38 sqft
            centroid=[round(x_split + 1.25, 2), round(7.80 + 0.70, 2)],
            level_index=1,
            is_habitable=False
        ))

        # 14. First Bedroom 4 (Mid-Left above Dining/Kitchen: x in [0, 4.25], y in [4.8, 8.8])
        f_bed4_poly = [[x0, y_porch_end], [x_split, y_porch_end], [x_split, 8.80], [x0, 8.80], [x0, y_porch_end]]
        rooms.append(RoomModel(
            room_id="room_L1_bed4",
            room_type="bedroom",
            room_name="First Bedroom 4 (with Modern Cabinets)",
            polygon=f_bed4_poly,
            area_m2=round(4.25 * 4.00, 1), # 17.0 m2 / 183 sqft
            centroid=[round(x0 + 4.25/2, 2), round(y_porch_end + 2.00, 2)],
            level_index=1,
            is_habitable=True
        ))
        # Attached Bath 4 (x in [0, 4.25], y in [8.8, 11.2])
        f_bath4_poly = [[x0, 8.80], [x_split, 8.80], [x_split, 11.20], [x0, 11.20], [x0, 8.80]]
        rooms.append(RoomModel(
            room_id="room_L1_bath4",
            room_type="bathroom",
            room_name="Attached Bath 4",
            polygon=f_bath4_poly,
            area_m2=round(4.25 * 2.40, 1), # 10.2 m2 / 110 sqft
            centroid=[round(x0 + 4.25/2, 2), round(8.80 + 1.20, 2)],
            level_index=1,
            is_habitable=False
        ))

        # 15. First Bedroom 5 (Rear-Left stacked directly on Ground Bed 1: x in [0, 4.875], y in [11.2, 14.5])
        f_bed5_poly = [[x0, 11.20], [4.875, 11.20], [4.875, 14.50], [x0, 14.50], [x0, 11.20]]
        rooms.append(RoomModel(
            room_id="room_L1_bed5",
            room_type="bedroom",
            room_name="First Bedroom 5 (with Modern Cabinets)",
            polygon=f_bed5_poly,
            area_m2=round(4.875 * 3.30, 1),
            centroid=[round(4.875/2, 2), round(11.20 + 1.65, 2)],
            level_index=1,
            is_habitable=True
        ))
        f_bath5_poly = [[x0, 14.50], [4.875, 14.50], [4.875, y_rear], [x0, y_rear], [x0, 14.50]]
        rooms.append(RoomModel(
            room_id="room_L1_bath5",
            room_type="bathroom",
            room_name="Attached Bath 5 (Dress & Bath)",
            polygon=f_bath5_poly,
            area_m2=round(4.875 * 1.50, 1),
            centroid=[round(4.875/2, 2), round(14.50 + 0.75, 2)],
            level_index=1,
            is_habitable=False
        ))

        # 16. First Bedroom 6 (Rear-Right stacked directly on Ground Bed 2: x in [4.875, 9.75], y in [11.2, 14.5])
        f_bed6_poly = [[4.875, 11.20], [x_end, 11.20], [x_end, 14.50], [4.875, 14.50], [4.875, 11.20]]
        rooms.append(RoomModel(
            room_id="room_L1_bed6",
            room_type="bedroom",
            room_name="First Bedroom 6 (with Modern Cabinets)",
            polygon=f_bed6_poly,
            area_m2=round(4.875 * 3.30, 1),
            centroid=[round(4.875 + 4.875/2, 2), round(11.20 + 1.65, 2)],
            level_index=1,
            is_habitable=True
        ))
        f_bath6_poly = [[4.875, 14.50], [x_end, 14.50], [x_end, y_rear], [4.875, y_rear], [4.875, 14.50]]
        rooms.append(RoomModel(
            room_id="room_L1_bath6",
            room_type="bathroom",
            room_name="Attached Bath 6 (Dress & Bath)",
            polygon=f_bath6_poly,
            area_m2=round(4.875 * 1.50, 1),
            centroid=[round(4.875 + 4.875/2, 2), round(14.50 + 0.75, 2)],
            level_index=1,
            is_habitable=False
        ))

        # =========================================================================
        # WALLS GENERATION (Perimeter & Interior Dividers for Both Levels)
        # =========================================================================
        for lvl in [0, 1]:
            lvl_rooms = [r for r in rooms if r.level_index == lvl]
            # Outer boundary
            boundary_segs = [
                [[x0, y_front], [x_end, y_front]],
                [[x_end, y_front], [x_end, y_rear]],
                [[x_end, y_rear], [x0, y_rear]],
                [[x0, y_rear], [x0, y_front]]
            ]
            for seg in boundary_segs:
                walls.append(WallModel(
                    wall_id=f"wall_{wall_counter:03d}",
                    wall_type="exterior",
                    centerline=seg,
                    thickness_m=0.25,
                    level_index=lvl
                ))
                wall_counter += 1

            # Interior Dividing Walls from shared room edges
            for i in range(len(lvl_rooms)):
                r1 = lvl_rooms[i]
                p1 = Polygon(r1.polygon)
                for j in range(i + 1, len(lvl_rooms)):
                    r2 = lvl_rooms[j]
                    p2 = Polygon(r2.polygon)

                    inter = p1.intersection(p2)
                    if not inter.is_empty and inter.length >= 0.8:
                        if inter.geom_type == "LineString":
                            lines = [inter]
                        elif hasattr(inter, "geoms"):
                            lines = [g for g in inter.geoms if g.geom_type == "LineString"]
                        else:
                            lines = []

                        for sline in lines:
                            if sline.length >= 0.8:
                                coords = list(sline.coords)
                                sp1 = [round(coords[0][0], 2), round(coords[0][1], 2)]
                                sp2 = [round(coords[-1][0], 2), round(coords[-1][1], 2)]
                                walls.append(WallModel(
                                    wall_id=f"wall_{wall_counter:03d}",
                                    wall_type="interior",
                                    centerline=[sp1, sp2],
                                    thickness_m=0.15,
                                    level_index=lvl
                                ))
                                wall_counter += 1

                                # Note: dividing walls are created, doors are placed intentionally below
                                pass

        # =========================================================================
        # INTENTIONAL ARCHITECTURAL DOOR NETWORK (Strict Spatial Circulation)
        # =========================================================================
        # LEVEL 0 (GROUND FLOOR) DOORS:
        # 1. Main Double Entry from Porch into Grand Stair Lobby / Foyer
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[4.25, 4.80],
            width_m=1.40,
            connects_rooms=["room_L0_porch", "room_L0_stairs"],
            level_index=0
        ))
        opening_counter += 1

        # 2. Formal Guest Entry from Porch into Formal Drawing Room
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[4.25, 2.40],
            width_m=1.00,
            connects_rooms=["room_L0_porch", "room_L0_drawing"],
            level_index=0
        ))
        opening_counter += 1

        # 3. Drawing Room to Foyer / TV Lounge Archway
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[5.50, 4.80],
            width_m=1.10,
            connects_rooms=["room_L0_drawing", "room_L0_tv_lounge"],
            level_index=0
        ))
        opening_counter += 1

        # 4. Dining Room connects to Central Foyer / Lounge via 4'-8" (1.40m) wide double-leaf aperture
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[4.25, 6.40],
            width_m=1.40,
            connects_rooms=["room_L0_dining", "room_L0_stairs"],
            level_index=0
        ))
        opening_counter += 1

        # 5. Kitchen connects to Dining Room
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[2.12, 8.00],
            width_m=0.90,
            connects_rooms=["room_L0_dining", "room_L0_kitchen"],
            level_index=0
        ))
        opening_counter += 1

        # 6. Powder Room door opens strictly into Central Lobby
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[4.25, 8.50],
            width_m=0.75,
            connects_rooms=["room_L0_powder", "room_L0_stairs"],
            level_index=0
        ))
        opening_counter += 1

        # 7. Ground Bedroom 1 opens into Central TV Lounge / Circulation (NOT Kitchen!)
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[3.50, 11.20],
            width_m=0.95,
            connects_rooms=["room_L0_bed1", "room_L0_tv_lounge"],
            level_index=0
        ))
        opening_counter += 1

        # 8. Ground Bedroom 2 opens into Central TV Lounge
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[6.00, 11.20],
            width_m=0.95,
            connects_rooms=["room_L0_bed2", "room_L0_tv_lounge"],
            level_index=0
        ))
        opening_counter += 1

        # 9. Attached Bath 1 opens ONLY from inside Bedroom 1 (NO door to Bath 2!)
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[2.44, 14.50],
            width_m=0.80,
            connects_rooms=["room_L0_bed1", "room_L0_bath1"],
            level_index=0
        ))
        opening_counter += 1

        # 10. Attached Bath 2 opens ONLY from inside Bedroom 2 (NO door to Bath 1!)
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[7.31, 14.50],
            width_m=0.80,
            connects_rooms=["room_L0_bed2", "room_L0_bath2"],
            level_index=0
        ))
        opening_counter += 1

        # LEVEL 1 (FIRST FLOOR) DOORS:
        # 11. Stairs go UP and land directly into the Upper TV Lounge / Family Gallery
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[6.75, 6.30],
            width_m=1.20,
            connects_rooms=["room_L1_stairs", "room_L1_tv_lounge"],
            level_index=1
        ))
        opening_counter += 1

        # 12. Master Suite 1 door opens from Upper TV Lounge
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[6.50, 4.80],
            width_m=0.95,
            connects_rooms=["room_L1_master", "room_L1_tv_lounge"],
            level_index=1
        ))
        opening_counter += 1

        # 13. Master Luxury Bath opens ONLY from inside Master Suite 1
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[7.00, 1.50],
            width_m=0.85,
            connects_rooms=["room_L1_master", "room_L1_master_bath"],
            level_index=1
        ))
        opening_counter += 1

        # 14. Bedroom 3 door opens from Upper Lounge / Vestibule (NOT stairs!)
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[4.25, 4.80],
            width_m=0.95,
            connects_rooms=["room_L1_bed3", "room_L1_tv_lounge"],
            level_index=1
        ))
        opening_counter += 1

        # 15. Bedroom 3 opens out to Front Open Terrace / Balcony
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[2.12, 1.80],
            width_m=0.90,
            connects_rooms=["room_L1_bed3", "room_L1_terrace"],
            level_index=1
        ))
        opening_counter += 1

        # 16. Bedroom 4 door opens from Upper TV Lounge
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[4.25, 7.00],
            width_m=0.95,
            connects_rooms=["room_L1_bed4", "room_L1_tv_lounge"],
            level_index=1
        ))
        opening_counter += 1

        # 17. Attached Bath 4 opens ONLY from inside Bedroom 4
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[2.12, 8.80],
            width_m=0.80,
            connects_rooms=["room_L1_bed4", "room_L1_bath4"],
            level_index=1
        ))
        opening_counter += 1

        # 18. Attached Bath 3 opens from Bedroom 3 / Suite side
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[4.25, 8.50],
            width_m=0.80,
            connects_rooms=["room_L1_bed4", "room_L1_bath3"],
            level_index=1
        ))
        opening_counter += 1

        # 19. First Bedroom 5 door opens from Upper TV Lounge
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[3.50, 11.20],
            width_m=0.95,
            connects_rooms=["room_L1_bed5", "room_L1_tv_lounge"],
            level_index=1
        ))
        opening_counter += 1

        # 20. First Bedroom 6 door opens from Upper TV Lounge
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[6.00, 11.20],
            width_m=0.95,
            connects_rooms=["room_L1_bed6", "room_L1_tv_lounge"],
            level_index=1
        ))
        opening_counter += 1

        # 21. Attached Bath 5 opens ONLY from inside Bedroom 5 (NO door to Bath 6!)
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[2.44, 14.50],
            width_m=0.80,
            connects_rooms=["room_L1_bed5", "room_L1_bath5"],
            level_index=1
        ))
        opening_counter += 1

        # 22. Attached Bath 6 opens ONLY from inside Bedroom 6 (NO door to Bath 5!)
        openings.append(OpeningModel(
            opening_id=f"door_{opening_counter:03d}",
            opening_type="door",
            position=[7.31, 14.50],
            width_m=0.80,
            connects_rooms=["room_L1_bed6", "room_L1_bath6"],
            level_index=1
        ))
        opening_counter += 1

        # =========================================================================
        # EXTERIOR WINDOWS (Front, Rear, and Side Daylight Access)
        # =========================================================================
        # Ground Floor Windows
        windows_spec = [
            # Drawing room front bay window
            {"pos": [7.00, y_front], "w": 2.40, "lvl": 0},
            # Kitchen side window
            {"pos": [x0, 9.60], "w": 1.40, "lvl": 0},
            # Lounge side window
            {"pos": [x_end, 8.00], "w": 1.80, "lvl": 0},
            # Ground Bed 1 rear window
            {"pos": [2.40, y_rear], "w": 1.50, "lvl": 0},
            # Ground Bed 2 rear window
            {"pos": [7.30, y_rear], "w": 1.50, "lvl": 0},
            # First Floor Master Suite front window / sliding door to balcony
            {"pos": [7.00, 1.50], "w": 2.40, "lvl": 1},
            # First Bed 3 terrace window
            {"pos": [2.10, 1.80], "w": 1.80, "lvl": 1},
            # First Floor Lounge side window
            {"pos": [x_end, 8.00], "w": 1.80, "lvl": 1},
            # First Bed 4 side window
            {"pos": [x0, 6.80], "w": 1.50, "lvl": 1},
            # First Bed 5 rear window
            {"pos": [2.40, y_rear], "w": 1.50, "lvl": 1},
            # First Bed 6 rear window
            {"pos": [7.30, y_rear], "w": 1.50, "lvl": 1}
        ]

        for w_spec in windows_spec:
            openings.append(OpeningModel(
                opening_id=f"wind_{opening_counter:03d}",
                opening_type="window",
                position=w_spec["pos"],
                width_m=w_spec["w"],
                sill_height_m=0.90,
                level_index=w_spec["lvl"]
            ))
            opening_counter += 1

        # Build Graph
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.40, min_shared_boundary_m=0.50)
        edges, _ = extractor.build_graph(rooms, openings)

        # Explicit vertical stairs link
        edges.append(GraphEdgeModel(
            source_room_id="room_L0_stairs",
            target_room_id="room_L1_stairs",
            relationship_type="via_door",
            weight=1.0,
            metadata={"vertical_circulation": "double_stairs", "aligned": True}
        ))

        total_area = sum(r.area_m2 for r in rooms)
        boundary = [[x0, y_front], [x_end, y_front], [x_end, y_rear], [x0, y_rear], [x0, y_front]]

        return CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="synthetic_generated",
                floor_count=2,
                levels=[0, 1],
                unit="m",
                wall_height_m=3.00,
                provenance={
                    "project_title": "10 Marla Modern 2-Storey House",
                    "plot_size": "10 Marla (35' x 65')",
                    "location": "DHA Islamabad",
                    "style": "Modern USA-Style Open Concept"
                }
            ),
            boundary=boundary,
            total_area_m2=round(total_area, 1),
            walls=walls,
            openings=openings,
            rooms=rooms,
            graph_edges=edges
        )


class Spanish3MarlaArchitecturalEngine:
    """
    Standard Pakistani/DHA 3 Marla Plot: 20'-0" x 35'-0" (6.00m x 10.65m).
    Authentic Spanish-style compact residence:
    - Ground Floor + First Floor continuous structural spine wall at x = 2.40m.
    - Identical staircase core footprint on both floors: x in [0, 2.40], y in [3.80, 6.20].
    - 3 Bedrooms total, each with attached ensuite bathroom.
    - Ground Floor: Formal Drawing/Living, Dining Room, TV Lounge, Spanish Kitchen with breakfast bar,
      Guest Powder Room, Car Porch / Garage, and Ground Bedroom 1 with Attached Bath 1.
    - First Floor: First Bedroom 2 (Rear) with Attached Bath 2 (stacked over Ground Bath 1 for vertical plumbing),
      First Bedroom 3 (Front Master Suite) with Attached Bath 3, Family TV Lounge Gallery,
      Spanish Arched Balcony / Terrace overlooking porch, and Modern Stairs continuing to roof.
    """

    @classmethod
    def generate_3_marla_house(cls, plan_id: str = "spanish_3m_residence") -> CanonicalFloorPlan:
        # Metrics:
        x0, x_spine, x_end = 0.0, 2.40, 6.00
        y_front, y_porch_end, y_stair_end, y_powder_end, y_kitchen_end, y_rear = 0.0, 3.80, 6.00, 6.90, 9.15, 10.65

        rooms: List[RoomModel] = []
        walls: List[WallModel] = []
        openings: List[OpeningModel] = []

        wall_counter = 1
        opening_counter = 1

        # =========================================================================
        # LEVEL 0: GROUND FLOOR
        # =========================================================================
        # 1. Car Porch / Compact Garage (Front-Left: x in [0, 2.40], y in [0, 3.80])
        porch_poly = [[x0, y_front], [x_spine, y_front], [x_spine, y_porch_end], [x0, y_porch_end], [x0, y_front]]
        rooms.append(RoomModel(
            room_id="room_L0_porch",
            room_type="garage",
            room_name="Car Porch / Garage",
            polygon=porch_poly,
            area_m2=round(2.40 * 3.80, 1), # 9.1 m2 / 98 sqft
            centroid=[1.20, 1.90],
            level_index=0,
            is_habitable=False
        ))

        # 2. Formal Living / Drawing Room (Front-Right: x in [2.40, 6.00], y in [0, 3.80])
        drawing_poly = [[x_spine, y_front], [x_end, y_front], [x_end, y_porch_end], [x_spine, y_porch_end], [x_spine, y_front]]
        rooms.append(RoomModel(
            room_id="room_L0_drawing",
            room_type="living_room",
            room_name="Formal Living / Drawing Room",
            polygon=drawing_poly,
            area_m2=round(3.60 * 3.80, 1), # 13.7 m2 / 147 sqft
            centroid=[4.20, 1.90],
            level_index=0,
            is_habitable=True
        ))

        # 3. Modern Stairs Core (Central-Left: x in [0, 2.40], y in [3.80, 6.20])
        stair_poly = [[x0, y_porch_end], [x_spine, y_porch_end], [x_spine, y_stair_end], [x0, y_stair_end], [x0, y_porch_end]]
        rooms.append(RoomModel(
            room_id="room_L0_stairs",
            room_type="corridor",
            room_name="Modern Stairs Core (UP ->)",
            polygon=stair_poly,
            area_m2=round(2.40 * (y_stair_end - y_porch_end), 1), # 5.3 m2
            centroid=[1.20, round((y_porch_end + y_stair_end)/2, 2)],
            level_index=0,
            is_habitable=False
        ))

        # 4. Guest Powder Room (Mid-Left: x in [0, 2.40], y in [6.00, 6.90])
        powder_poly = [[x0, y_stair_end], [x_spine, y_stair_end], [x_spine, y_powder_end], [x0, y_powder_end], [x0, y_stair_end]]
        rooms.append(RoomModel(
            room_id="room_L0_powder",
            room_type="bathroom",
            room_name="Guest Powder Room",
            polygon=powder_poly,
            area_m2=round(2.40 * (y_powder_end - y_stair_end), 1), # 2.2 m2
            centroid=[1.20, round((y_stair_end + y_powder_end)/2, 2)],
            level_index=0,
            is_habitable=False
        ))

        # 5. Spanish Kitchen with Cabinets & Breakfast Bar (x in [0, 2.40], y in [6.90, 9.15])
        kitchen_poly = [[x0, y_powder_end], [x_spine, y_powder_end], [x_spine, y_kitchen_end], [x0, y_kitchen_end], [x0, y_powder_end]]
        rooms.append(RoomModel(
            room_id="room_L0_kitchen",
            room_type="kitchen",
            room_name="Spanish Kitchen (Cabinets & Bar)",
            polygon=kitchen_poly,
            area_m2=round(2.40 * (y_kitchen_end - y_powder_end), 1), # 5.4 m2
            centroid=[1.20, round((y_powder_end + y_kitchen_end)/2, 2)],
            level_index=0,
            is_habitable=True
        ))

        # 6. Attached Bath 1 (Rear Ensuite with Dress: x in [0, 2.40], y in [9.15, 10.65])
        bath1_poly = [[x0, y_kitchen_end], [x_spine, y_kitchen_end], [x_spine, y_rear], [x0, y_rear], [x0, y_kitchen_end]]
        rooms.append(RoomModel(
            room_id="room_L0_bath1",
            room_type="bathroom",
            room_name="Attached Bath 1 (Dress & Bath)",
            polygon=bath1_poly,
            area_m2=round(2.40 * 1.50, 1), # 3.6 m2 / 39 sqft
            centroid=[1.20, 9.90],
            level_index=0,
            is_habitable=False
        ))

        # 7. Dining Room (Mid-Right: x in [2.40, 6.00], y in [3.80, 5.50])
        dining_poly = [[x_spine, y_porch_end], [x_end, y_porch_end], [x_end, 5.50], [x_spine, 5.50], [x_spine, y_porch_end]]
        rooms.append(RoomModel(
            room_id="room_L0_dining",
            room_type="dining_room",
            room_name="Dining Room",
            polygon=dining_poly,
            area_m2=round(3.60 * 1.70, 1), # 6.1 m2 / 66 sqft
            centroid=[4.20, 4.65],
            level_index=0,
            is_habitable=True
        ))

        # 8. Central Family TV Lounge (Mid-Right: x in [2.40, 6.00], y in [5.50, 7.50])
        tv_poly = [[x_spine, 5.50], [x_end, 5.50], [x_end, 7.50], [x_spine, 7.50], [x_spine, 5.50]]
        rooms.append(RoomModel(
            room_id="room_L0_tv_lounge",
            room_type="living_room",
            room_name="Family TV Lounge",
            polygon=tv_poly,
            area_m2=round(3.60 * 2.00, 1), # 7.2 m2 / 78 sqft
            centroid=[4.20, 6.50],
            level_index=0,
            is_habitable=True
        ))

        # 9. Ground Bedroom 1 (Rear-Right Suite: x in [2.40, 6.00], y in [7.50, 10.65])
        bed1_poly = [[x_spine, 7.50], [x_end, 7.50], [x_end, y_rear], [x_spine, y_rear], [x_spine, 7.50]]
        rooms.append(RoomModel(
            room_id="room_L0_bed1",
            room_type="bedroom",
            room_name="Ground Bedroom 1 (with Wardrobe)",
            polygon=bed1_poly,
            area_m2=round(3.60 * 3.15, 1), # 11.3 m2 / 122 sqft
            centroid=[4.20, 9.08],
            level_index=0,
            is_habitable=True
        ))

        # =========================================================================
        # LEVEL 1: FIRST FLOOR
        # =========================================================================
        # 10. Spanish Arched Balcony / Terrace (Above Porch: x in [0, 2.40], y in [0, 2.30])
        terrace_poly = [[x0, y_front], [x_spine, y_front], [x_spine, 2.30], [x0, 2.30], [x0, y_front]]
        rooms.append(RoomModel(
            room_id="room_L1_terrace",
            room_type="balcony",
            room_name="Spanish Arched Balcony / Terrace",
            polygon=terrace_poly,
            area_m2=round(2.40 * 2.30, 1), # 5.5 m2 / 59 sqft
            centroid=[1.20, 1.15],
            level_index=1,
            is_habitable=False
        ))

        # 11. Attached Bath 3 (Front Ensuite for Bed 3: x in [0, 2.40], y in [2.30, 3.80])
        f_bath3_poly = [[x0, 2.30], [x_spine, 2.30], [x_spine, y_porch_end], [x0, y_porch_end], [x0, 2.30]]
        rooms.append(RoomModel(
            room_id="room_L1_bath3",
            room_type="bathroom",
            room_name="Attached Bath 3 (Front Ensuite)",
            polygon=f_bath3_poly,
            area_m2=round(2.40 * 1.50, 1), # 3.6 m2 / 39 sqft
            centroid=[1.20, 3.05],
            level_index=1,
            is_habitable=False
        ))

        # 12. Modern Stairs Landing / Core (Identical: x in [0, 2.40], y in [3.80, 6.00])
        f_stair_poly = [[x0, y_porch_end], [x_spine, y_porch_end], [x_spine, y_stair_end], [x0, y_stair_end], [x0, y_porch_end]]
        rooms.append(RoomModel(
            room_id="room_L1_stairs",
            room_type="corridor",
            room_name="Modern Stairs (UP to Roof)",
            polygon=f_stair_poly,
            area_m2=round(2.40 * 2.20, 1), # 5.3 m2 / 57 sqft
            centroid=[1.20, 4.90],
            level_index=1,
            is_habitable=False
        ))

        # 13. Walk-in Wardrobe & Cabinets (x in [0, 2.40], y in [6.00, 9.15])
        dress_poly = [[x0, y_stair_end], [x_spine, y_stair_end], [x_spine, y_kitchen_end], [x0, y_kitchen_end], [x0, y_stair_end]]
        rooms.append(RoomModel(
            room_id="room_L1_dress",
            room_type="closet",
            room_name="Walk-in Wardrobe & Cabinets",
            polygon=dress_poly,
            area_m2=round(2.40 * (y_kitchen_end - y_stair_end), 1), # 7.6 m2 / 81 sqft
            centroid=[1.20, round((y_stair_end + y_kitchen_end)/2, 2)],
            level_index=1,
            is_habitable=False
        ))

        # 14. Attached Bath 2 (Rear Ensuite - stacked over Ground Bath 1: x in [0, 2.40], y in [9.15, 10.65])
        f_bath2_poly = [[x0, y_kitchen_end], [x_spine, y_kitchen_end], [x_spine, y_rear], [x0, y_rear], [x0, y_kitchen_end]]
        rooms.append(RoomModel(
            room_id="room_L1_bath2",
            room_type="bathroom",
            room_name="Attached Bath 2 (Rear Ensuite)",
            polygon=f_bath2_poly,
            area_m2=round(2.40 * 1.50, 1), # 3.6 m2 / 39 sqft
            centroid=[1.20, 9.90],
            level_index=1,
            is_habitable=False
        ))

        # 15. First Bedroom 3 (Front Master Suite: x in [2.40, 6.00], y in [0, 3.80])
        f_bed3_poly = [[x_spine, y_front], [x_end, y_front], [x_end, y_porch_end], [x_spine, y_porch_end], [x_spine, y_front]]
        rooms.append(RoomModel(
            room_id="room_L1_bed3",
            room_type="bedroom",
            room_name="First Bedroom 3 (Front Master Suite)",
            polygon=f_bed3_poly,
            area_m2=round(3.60 * 3.80, 1), # 13.7 m2 / 147 sqft
            centroid=[4.20, 1.90],
            level_index=1,
            is_habitable=True
        ))

        # 16. First Floor TV Lounge / Gallery (x in [2.40, 6.00], y in [3.80, 7.50])
        f_tv_poly = [[x_spine, y_porch_end], [x_end, y_porch_end], [x_end, 7.50], [x_spine, 7.50], [x_spine, y_porch_end]]
        rooms.append(RoomModel(
            room_id="room_L1_tv_lounge",
            room_type="living_room",
            room_name="First Floor TV Lounge / Gallery",
            polygon=f_tv_poly,
            area_m2=round(3.60 * 3.70, 1), # 13.3 m2 / 143 sqft
            centroid=[4.20, 5.65],
            level_index=1,
            is_habitable=True
        ))

        # 17. First Bedroom 2 (Rear Bedroom - stacked over Ground Bed 1: x in [2.40, 6.00], y in [7.50, 10.65])
        f_bed2_poly = [[x_spine, 7.50], [x_end, 7.50], [x_end, y_rear], [x_spine, y_rear], [x_spine, 7.50]]
        rooms.append(RoomModel(
            room_id="room_L1_bed2",
            room_type="bedroom",
            room_name="First Bedroom 2 (Rear Bedroom)",
            polygon=f_bed2_poly,
            area_m2=round(3.60 * 3.15, 1), # 11.3 m2 / 122 sqft
            centroid=[4.20, 9.08],
            level_index=1,
            is_habitable=True
        ))

        # =========================================================================
        # WALLS GENERATION
        # =========================================================================
        for lvl in [0, 1]:
            # Exterior Perimeter Envelope
            walls.append(WallModel(wall_id=f"wall_ext_{lvl}_front", wall_type="exterior", centerline=[[x0, y_front], [x_end, y_front]], thickness_m=0.23, level_index=lvl))
            walls.append(WallModel(wall_id=f"wall_ext_{lvl}_right", wall_type="exterior", centerline=[[x_end, y_front], [x_end, y_rear]], thickness_m=0.23, level_index=lvl))
            walls.append(WallModel(wall_id=f"wall_ext_{lvl}_rear", wall_type="exterior", centerline=[[x_end, y_rear], [x0, y_rear]], thickness_m=0.23, level_index=lvl))
            walls.append(WallModel(wall_id=f"wall_ext_{lvl}_left", wall_type="exterior", centerline=[[x0, y_rear], [x0, y_front]], thickness_m=0.23, level_index=lvl))

            # Continuous Central Spine Wall at x = 2.40
            walls.append(WallModel(wall_id=f"wall_spine_{lvl}", wall_type="interior", centerline=[[x_spine, y_front], [x_spine, y_rear]], thickness_m=0.15, level_index=lvl))

        # Level 0 Interior Partition Walls
        walls.append(WallModel(wall_id="wall_L0_p1", wall_type="interior", centerline=[[x0, y_porch_end], [x_spine, y_porch_end]], thickness_m=0.15, level_index=0))
        walls.append(WallModel(wall_id="wall_L0_p2", wall_type="interior", centerline=[[x0, y_stair_end], [x_spine, y_stair_end]], thickness_m=0.15, level_index=0))
        walls.append(WallModel(wall_id="wall_L0_p3", wall_type="interior", centerline=[[x0, y_powder_end], [x_spine, y_powder_end]], thickness_m=0.15, level_index=0))
        walls.append(WallModel(wall_id="wall_L0_p4", wall_type="interior", centerline=[[x0, y_kitchen_end], [x_spine, y_kitchen_end]], thickness_m=0.15, level_index=0))
        walls.append(WallModel(wall_id="wall_L0_p5", wall_type="interior", centerline=[[x_spine, y_porch_end], [x_end, y_porch_end]], thickness_m=0.15, level_index=0))
        walls.append(WallModel(wall_id="wall_L0_p6", wall_type="interior", centerline=[[x_spine, 5.50], [x_end, 5.50]], thickness_m=0.15, level_index=0))
        walls.append(WallModel(wall_id="wall_L0_p7", wall_type="interior", centerline=[[x_spine, 7.50], [x_end, 7.50]], thickness_m=0.15, level_index=0))

        # Level 1 Interior Partition Walls
        walls.append(WallModel(wall_id="wall_L1_p1", wall_type="interior", centerline=[[x0, y_porch_end], [x_spine, y_porch_end]], thickness_m=0.15, level_index=1))
        walls.append(WallModel(wall_id="wall_L1_p2", wall_type="interior", centerline=[[x0, y_stair_end], [x_spine, y_stair_end]], thickness_m=0.15, level_index=1))
        walls.append(WallModel(wall_id="wall_L1_p3", wall_type="interior", centerline=[[x0, 7.50], [x_spine, 7.50]], thickness_m=0.15, level_index=1))
        walls.append(WallModel(wall_id="wall_L1_p4", wall_type="interior", centerline=[[x0, y_kitchen_end], [x_spine, y_kitchen_end]], thickness_m=0.15, level_index=1))
        walls.append(WallModel(wall_id="wall_L1_p5", wall_type="interior", centerline=[[x_spine, y_porch_end], [x_end, y_porch_end]], thickness_m=0.15, level_index=1))
        walls.append(WallModel(wall_id="wall_L1_p6", wall_type="interior", centerline=[[x_spine, 7.50], [x_end, 7.50]], thickness_m=0.15, level_index=1))

        # =========================================================================
        # OPENINGS (DOORS & WINDOWS)
        # =========================================================================
        # Ground Floor Doors
        openings.append(OpeningModel(opening_id="door_L0_main", opening_type="door", position=[1.20, y_porch_end], width_m=1.00, connects_rooms=["room_L0_porch", "room_L0_stairs"], level_index=0))
        openings.append(OpeningModel(opening_id="door_L0_draw", opening_type="door", position=[x_spine, 1.90], width_m=0.90, connects_rooms=["room_L0_porch", "room_L0_drawing"], level_index=0))
        openings.append(OpeningModel(opening_id="door_L0_draw_din", opening_type="door", position=[3.60, y_porch_end], width_m=0.90, connects_rooms=["room_L0_drawing", "room_L0_dining"], level_index=0))
        openings.append(OpeningModel(opening_id="door_L0_stair_din", opening_type="door", position=[x_spine, 4.65], width_m=0.90, connects_rooms=["room_L0_stairs", "room_L0_dining"], level_index=0))
        openings.append(OpeningModel(opening_id="door_L0_din_tv", opening_type="cased_opening", position=[4.20, 5.50], width_m=1.50, connects_rooms=["room_L0_dining", "room_L0_tv_lounge"], level_index=0))
        openings.append(OpeningModel(opening_id="door_L0_powder", opening_type="door", position=[x_spine, 6.70], width_m=0.80, connects_rooms=["room_L0_tv_lounge", "room_L0_powder"], level_index=0))
        openings.append(OpeningModel(opening_id="door_L0_kitch", opening_type="cased_opening", position=[x_spine, 8.18], width_m=1.20, connects_rooms=["room_L0_tv_lounge", "room_L0_kitchen"], level_index=0))
        openings.append(OpeningModel(opening_id="door_L0_bed1", opening_type="door", position=[3.60, 7.50], width_m=0.90, connects_rooms=["room_L0_tv_lounge", "room_L0_bed1"], level_index=0))
        openings.append(OpeningModel(opening_id="door_L0_bath1", opening_type="door", position=[x_spine, 9.90], width_m=0.80, connects_rooms=["room_L0_bed1", "room_L0_bath1"], level_index=0))

        # First Floor Doors
        openings.append(OpeningModel(opening_id="door_L1_stair_tv", opening_type="door", position=[x_spine, 5.00], width_m=0.90, connects_rooms=["room_L1_stairs", "room_L1_tv_lounge"], level_index=1))
        openings.append(OpeningModel(opening_id="door_L1_terrace", opening_type="door", position=[1.20, y_porch_end], width_m=0.90, connects_rooms=["room_L1_stairs", "room_L1_terrace"], level_index=1))
        openings.append(OpeningModel(opening_id="door_L1_bed3_terr", opening_type="door", position=[x_spine, 1.90], width_m=0.90, connects_rooms=["room_L1_terrace", "room_L1_bed3"], level_index=1))
        openings.append(OpeningModel(opening_id="door_L1_bed3_tv", opening_type="door", position=[3.60, y_porch_end], width_m=0.90, connects_rooms=["room_L1_tv_lounge", "room_L1_bed3"], level_index=1))
        openings.append(OpeningModel(opening_id="door_L1_bath3", opening_type="door", position=[x_spine, 3.05], width_m=0.80, connects_rooms=["room_L1_bed3", "room_L1_bath3"], level_index=1))
        openings.append(OpeningModel(opening_id="door_L1_bed2", opening_type="door", position=[3.60, 7.50], width_m=0.90, connects_rooms=["room_L1_tv_lounge", "room_L1_bed2"], level_index=1))
        openings.append(OpeningModel(opening_id="door_L1_dress", opening_type="door", position=[x_spine, 8.32], width_m=0.80, connects_rooms=["room_L1_bed2", "room_L1_dress"], level_index=1))
        openings.append(OpeningModel(opening_id="door_L1_bath2", opening_type="door", position=[x_spine, 9.90], width_m=0.80, connects_rooms=["room_L1_bed2", "room_L1_bath2"], level_index=1))

        # Windows (Daylight & Ventilation)
        windows = [
            # Ground
            {"pos": [4.20, y_front], "w": 2.00, "lvl": 0},   # Drawing front
            {"pos": [4.20, y_rear], "w": 1.80, "lvl": 0},    # Ground bed rear
            {"pos": [1.20, y_rear], "w": 0.80, "lvl": 0},    # Bath 1 rear vent
            {"pos": [x0, 8.18], "w": 1.20, "lvl": 0},        # Kitchen side vent
            # First Floor
            {"pos": [4.20, y_front], "w": 2.00, "lvl": 1},   # Bed 3 front window
            {"pos": [4.20, y_rear], "w": 1.80, "lvl": 1},    # Bed 2 rear window
            {"pos": [1.20, y_rear], "w": 0.80, "lvl": 1},    # Bath 2 rear vent
            {"pos": [x_end, 5.65], "w": 1.80, "lvl": 1}      # Upper Lounge side window
        ]
        for idx, w in enumerate(windows, 1):
            openings.append(OpeningModel(
                opening_id=f"wind_3m_{idx:03d}",
                opening_type="window",
                position=w["pos"],
                width_m=w["w"],
                sill_height_m=0.90,
                level_index=w["lvl"]
            ))

        # Build Graph
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.40, min_shared_boundary_m=0.50)
        edges, _ = extractor.build_graph(rooms, openings)

        # Explicit vertical stairs link
        edges.append(GraphEdgeModel(
            source_room_id="room_L0_stairs",
            target_room_id="room_L1_stairs",
            relationship_type="via_door",
            weight=1.0,
            metadata={"vertical_circulation": "modern_stairs", "aligned": True}
        ))

        total_area = sum(r.area_m2 for r in rooms)
        boundary = [[x0, y_front], [x_end, y_front], [x_end, y_rear], [x0, y_rear], [x0, y_front]]

        return CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="synthetic_generated",
                floor_count=2,
                levels=[0, 1],
                unit="m",
                wall_height_m=2.90,
                provenance={
                    "project_title": "3 Marla Spanish Contemporary Residence",
                    "plot_size": "3 Marla (20' x 35' = 700 sq ft / 65 m²)",
                    "style": "Spanish Contemporary Architecture",
                    "features": ["3 Ensuite Bedrooms", "Formal Living & Dining", "Central TV Lounge", "Spanish Arched Balcony"]
                }
            ),
            boundary=boundary,
            total_area_m2=round(total_area, 1),
            walls=walls,
            openings=openings,
            rooms=rooms,
            graph_edges=edges
        )


class Modern5MarlaArchitecturalEngine:
    """
    Standard Pakistani/DHA/LDA 5 Marla Plot: 25'-0" x 45'-0" (7.62m x 13.72m).
    Covered buildable width: 7.00m (x from 0.0 to 7.00).
    Covered buildable depth: 12.50m (y from 0.0 to 12.50).
    
    Architectural Program:
    - 4 Bedrooms (1 Ground Floor, 3 First Floor)
    - 4 En-suite Attached Bathrooms (every bedroom has a private bath)
    - 1 Powder Room (for guests on Ground Floor)
    - Single Car Porch / Garage
    - Formal Living / Drawing Room
    - Central TV Lounge on Ground Floor & Family Lounge on First Floor
    - Dedicated Dining Room adjacent to Lounge & Kitchen
    - Modern Open/Semi-Open Kitchen
    - Aligned Dog-Leg Staircase connecting levels and landing directly in TV Lounge
    """

    @classmethod
    def generate_5_marla_house(cls, plan_id: str = "gen_5m_plan") -> CanonicalFloorPlan:
        x0 = 0.0
        x_split = 3.20      # Divides Porch/Kitchen/Dining from Drawing/Foyer/Lounge
        x_stair_end = 5.10  # Width of Stair Lobby
        x_end = 7.00        # Outer right wall

        y_front = 0.0       # Front boundary
        y_front_split = 4.20 # End of Porch & Drawing
        y_mid_split = 8.60  # End of Kitchen, Dining, Lounge
        y_rear = 12.50      # Rear boundary

        rooms: List[RoomModel] = []
        walls: List[WallModel] = []
        openings: List[OpeningModel] = []

        wall_counter = 1
        opening_counter = 1

        # =========================================================================
        # LEVEL 0: GROUND FLOOR
        # =========================================================================
        # 1. Single Garage / Car Porch (Front-Left: [0, 3.20] x [0, 4.20])
        porch_poly = [[x0, y_front], [x_split, y_front], [x_split, y_front_split], [x0, y_front_split], [x0, y_front]]
        rooms.append(RoomModel(
            room_id="room_L0_porch",
            room_type="garage",
            room_name="Single Car Porch (Garage)",
            polygon=porch_poly,
            area_m2=round(3.20 * 4.20, 1),
            centroid=[round(x0 + 3.20/2, 2), round(y_front + 4.20/2, 2)],
            level_index=0,
            is_habitable=False
        ))

        # 2. Living Room / Formal Drawing Room (Front-Right: [3.20, 7.00] x [0, 4.20])
        drawing_poly = [[x_split, y_front], [x_end, y_front], [x_end, y_front_split], [x_split, y_front_split], [x_split, y_front]]
        rooms.append(RoomModel(
            room_id="room_L0_drawing",
            room_type="living_room",
            room_name="Drawing Room (Living)",
            polygon=drawing_poly,
            area_m2=round((x_end - x_split) * 4.20, 1),
            centroid=[round(x_split + (x_end - x_split)/2, 2), round(y_front + 4.20/2, 2)],
            level_index=0,
            is_habitable=True
        ))

        # 3. Entrance & Stair Lobby with Dog-Leg Stairs (Central: [3.20, 5.10] x [4.20, 6.60])
        foyer_poly = [[x_split, y_front_split], [x_stair_end, y_front_split], [x_stair_end, 6.60], [x_split, 6.60], [x_split, y_front_split]]
        rooms.append(RoomModel(
            room_id="room_L0_foyer",
            room_type="corridor",
            room_name="Entrance & Stair Lobby (UP ->)",
            polygon=foyer_poly,
            area_m2=round((x_stair_end - x_split) * 2.40, 1),
            centroid=[round(x_split + (x_stair_end - x_split)/2, 2), round(y_front_split + 1.20, 2)],
            level_index=0,
            is_habitable=False
        ))

        # 4. Guest Powder Room (Adjacent to stairs: [5.10, 7.00] x [4.20, 5.40])
        powder_poly = [[x_stair_end, y_front_split], [x_end, y_front_split], [x_end, 5.40], [x_stair_end, 5.40], [x_stair_end, y_front_split]]
        rooms.append(RoomModel(
            room_id="room_L0_powder",
            room_type="bathroom",
            room_name="Powder Room (Guest Bath)",
            polygon=powder_poly,
            area_m2=round((x_end - x_stair_end) * 1.20, 1),
            centroid=[round(x_stair_end + (x_end - x_stair_end)/2, 2), round(y_front_split + 0.60, 2)],
            level_index=0,
            is_habitable=False
        ))

        # 5. Central TV Lounge (Family Core: [5.10, 7.00] x [5.40, 6.60] + [3.20, 7.00] x [6.60, 8.60])
        tv_poly = [
            [x_stair_end, 5.40],
            [x_end, 5.40],
            [x_end, y_mid_split],
            [x_split, y_mid_split],
            [x_split, 6.60],
            [x_stair_end, 6.60],
            [x_stair_end, 5.40]
        ]
        tv_area = round((x_end - x_stair_end) * 1.20 + (x_end - x_split) * 2.00, 1)
        rooms.append(RoomModel(
            room_id="room_L0_tv_lounge",
            room_type="lounge",
            room_name="TV Lounge (Family Living)",
            polygon=tv_poly,
            area_m2=tv_area,
            centroid=[5.10, 7.20],
            level_index=0,
            is_habitable=True
        ))

        # 6. Dedicated Dining Room ([0, 3.20] x [4.20, 6.40])
        dining_poly = [[x0, y_front_split], [x_split, y_front_split], [x_split, 6.40], [x0, 6.40], [x0, y_front_split]]
        rooms.append(RoomModel(
            room_id="room_L0_dining",
            room_type="dining",
            room_name="Dining Room",
            polygon=dining_poly,
            area_m2=round(3.20 * 2.20, 1),
            centroid=[round(x0 + 3.20/2, 2), round(y_front_split + 1.10, 2)],
            level_index=0,
            is_habitable=True
        ))

        # 7. Modern Kitchen ([0, 3.20] x [6.40, 8.60])
        kitchen_poly = [[x0, 6.40], [x_split, 6.40], [x_split, y_mid_split], [x0, y_mid_split], [x0, 6.40]]
        rooms.append(RoomModel(
            room_id="room_L0_kitchen",
            room_type="kitchen",
            room_name="Modern Kitchen",
            polygon=kitchen_poly,
            area_m2=round(3.20 * 2.20, 1),
            centroid=[round(x0 + 3.20/2, 2), round(6.40 + 1.10, 2)],
            level_index=0,
            is_habitable=True
        ))

        # 8. Ground Floor Bedroom 1 (Master/Guest Suite: [2.80, 7.00] x [8.60, 12.50])
        bed1_poly = [[2.80, y_mid_split], [x_end, y_mid_split], [x_end, y_rear], [2.80, y_rear], [2.80, y_mid_split]]
        rooms.append(RoomModel(
            room_id="room_L0_bed1",
            room_type="bedroom",
            room_name="Bedroom 1 (Master Suite)",
            polygon=bed1_poly,
            area_m2=round((x_end - 2.80) * 3.90, 1),
            centroid=[round(2.80 + (x_end - 2.80)/2, 2), round(y_mid_split + 1.95, 2)],
            level_index=0,
            is_habitable=True
        ))

        # 9. Attached Bathroom 1 (En-suite: [0, 2.80] x [8.60, 10.60])
        bath1_poly = [[x0, y_mid_split], [2.80, y_mid_split], [2.80, 10.60], [x0, 10.60], [x0, y_mid_split]]
        rooms.append(RoomModel(
            room_id="room_L0_bath1",
            room_type="bathroom",
            room_name="Attached Bath 1",
            polygon=bath1_poly,
            area_m2=round(2.80 * 2.00, 1),
            centroid=[round(x0 + 2.80/2, 2), round(y_mid_split + 1.00, 2)],
            level_index=0,
            is_habitable=False
        ))

        # 10. Rear Open To Sky / Laundry ([0, 2.80] x [10.60, 12.50])
        ots_poly = [[x0, 10.60], [2.80, 10.60], [2.80, y_rear], [x0, y_rear], [x0, 10.60]]
        rooms.append(RoomModel(
            room_id="room_L0_ots",
            room_type="outdoor",
            room_name="Rear OTS & Laundry Duct",
            polygon=ots_poly,
            area_m2=round(2.80 * 1.90, 1),
            centroid=[round(x0 + 2.80/2, 2), round(10.60 + 0.95, 2)],
            level_index=0,
            is_habitable=False
        ))

        # =========================================================================
        # LEVEL 1: FIRST FLOOR
        # =========================================================================
        # 1. Aligned Staircase Landing ([3.20, 5.10] x [4.20, 6.60] - matches Level 0 exactly)
        stair_l1_poly = [[x_split, y_front_split], [x_stair_end, y_front_split], [x_stair_end, 6.60], [x_split, 6.60], [x_split, y_front_split]]
        rooms.append(RoomModel(
            room_id="room_L1_stairs",
            room_type="corridor",
            room_name="Staircase Landing (DN ->)",
            polygon=stair_l1_poly,
            area_m2=round((x_stair_end - x_split) * 2.40, 1),
            centroid=[round(x_split + (x_stair_end - x_split)/2, 2), round(y_front_split + 1.20, 2)],
            level_index=1,
            is_habitable=False
        ))

        # 2. Bedroom 2 (Front Suite with Balcony: [3.20, 7.00] x [0, 4.20])
        bed2_poly = [[x_split, y_front], [x_end, y_front], [x_end, y_front_split], [x_split, y_front_split], [x_split, y_front]]
        rooms.append(RoomModel(
            room_id="room_L1_bed2",
            room_type="bedroom",
            room_name="Bedroom 2 (Front Suite)",
            polygon=bed2_poly,
            area_m2=round((x_end - x_split) * 4.20, 1),
            centroid=[round(x_split + (x_end - x_split)/2, 2), round(y_front + 4.20/2, 2)],
            level_index=1,
            is_habitable=True
        ))

        # 3. Attached Bathroom 2 (En-suite to Bed 2: [5.10, 7.00] x [4.20, 5.60])
        bath2_poly = [[x_stair_end, y_front_split], [x_end, y_front_split], [x_end, 5.60], [x_stair_end, 5.60], [x_stair_end, y_front_split]]
        rooms.append(RoomModel(
            room_id="room_L1_bath2",
            room_type="bathroom",
            room_name="Attached Bath 2",
            polygon=bath2_poly,
            area_m2=round((x_end - x_stair_end) * 1.40, 1),
            centroid=[round(x_stair_end + (x_end - x_stair_end)/2, 2), round(y_front_split + 0.70, 2)],
            level_index=1,
            is_habitable=False
        ))

        # 4. Front Balcony / Terrace ([0, 3.20] x [0, 3.20])
        balcony_poly = [[x0, y_front], [x_split, y_front], [x_split, 3.20], [x0, 3.20], [x0, y_front]]
        rooms.append(RoomModel(
            room_id="room_L1_balcony",
            room_type="outdoor",
            room_name="Front Balcony (Terrace)",
            polygon=balcony_poly,
            area_m2=round(3.20 * 3.20, 1),
            centroid=[1.60, 1.60],
            level_index=1,
            is_habitable=False
        ))

        # 5. Bedroom 3 ([0, 3.20] x [3.20, 7.00])
        bed3_poly = [[x0, 3.20], [x_split, 3.20], [x_split, 7.00], [x0, 7.00], [x0, 3.20]]
        rooms.append(RoomModel(
            room_id="room_L1_bed3",
            room_type="bedroom",
            room_name="Bedroom 3",
            polygon=bed3_poly,
            area_m2=round(3.20 * 3.80, 1),
            centroid=[1.60, 5.10],
            level_index=1,
            is_habitable=True
        ))

        # 6. Attached Bathroom 3 (En-suite to Bed 3: [0, 2.00] x [7.00, 8.60])
        bath3_poly = [[x0, 7.00], [2.00, 7.00], [2.00, y_mid_split], [x0, y_mid_split], [x0, 7.00]]
        rooms.append(RoomModel(
            room_id="room_L1_bath3",
            room_type="bathroom",
            room_name="Attached Bath 3",
            polygon=bath3_poly,
            area_m2=round(2.00 * 1.60, 1),
            centroid=[1.00, 7.80],
            level_index=1,
            is_habitable=False
        ))

        # 7. Upper TV Lounge / Family Gallery ([2.00, 3.20] x [7.00, 8.60] + [5.10, 7.00] x [5.60, 6.60] + [3.20, 7.00] x [6.60, 8.60])
        tv1_poly = [
            [x_stair_end, 5.60],
            [x_end, 5.60],
            [x_end, y_mid_split],
            [2.00, y_mid_split],
            [2.00, 7.00],
            [x_split, 7.00],
            [x_split, 6.60],
            [x_stair_end, 6.60],
            [x_stair_end, 5.60]
        ]
        rooms.append(RoomModel(
            room_id="room_L1_tv_lounge",
            room_type="lounge",
            room_name="Upper TV Lounge & Gallery",
            polygon=tv1_poly,
            area_m2=round(1.90 * 1.00 + 3.80 * 2.00 + 1.20 * 1.60, 1),
            centroid=[4.60, 7.40],
            level_index=1,
            is_habitable=True
        ))

        # 8. Bedroom 4 (Rear Master Suite: [2.80, 7.00] x [8.60, 12.50] - stacked above Bed 1)
        bed4_poly = [[2.80, y_mid_split], [x_end, y_mid_split], [x_end, y_rear], [2.80, y_rear], [2.80, y_mid_split]]
        rooms.append(RoomModel(
            room_id="room_L1_bed4",
            room_type="bedroom",
            room_name="Bedroom 4 (Rear Suite)",
            polygon=bed4_poly,
            area_m2=round((x_end - 2.80) * 3.90, 1),
            centroid=[round(2.80 + (x_end - 2.80)/2, 2), round(y_mid_split + 1.95, 2)],
            level_index=1,
            is_habitable=True
        ))

        # 9. Attached Bathroom 4 (En-suite to Bed 4: [0, 2.80] x [8.60, 10.60] - stacked above Bath 1)
        bath4_poly = [[x0, y_mid_split], [2.80, y_mid_split], [2.80, 10.60], [x0, 10.60], [x0, y_mid_split]]
        rooms.append(RoomModel(
            room_id="room_L1_bath4",
            room_type="bathroom",
            room_name="Attached Bath 4",
            polygon=bath4_poly,
            area_m2=round(2.80 * 2.00, 1),
            centroid=[round(x0 + 2.80/2, 2), round(y_mid_split + 1.00, 2)],
            level_index=1,
            is_habitable=False
        ))

        # 10. Rear Upper Terrace / Open To Sky ([0, 2.80] x [10.60, 12.50])
        ots1_poly = [[x0, 10.60], [2.80, 10.60], [2.80, y_rear], [x0, y_rear], [x0, 10.60]]
        rooms.append(RoomModel(
            room_id="room_L1_ots",
            room_type="outdoor",
            room_name="Rear Upper Terrace / OTS",
            polygon=ots1_poly,
            area_m2=round(2.80 * 1.90, 1),
            centroid=[round(x0 + 2.80/2, 2), round(10.60 + 0.95, 2)],
            level_index=1,
            is_habitable=False
        ))

        # =========================================================================
        # WALLS GENERATION
        # =========================================================================
        for lvl in [0, 1]:
            lvl_rooms = [r for r in rooms if r.level_index == lvl]
            # Exterior perimeter walls
            boundary_segs = [
                [[x0, y_front], [x_end, y_front]],
                [[x_end, y_front], [x_end, y_rear]],
                [[x_end, y_rear], [x0, y_rear]],
                [[x0, y_rear], [x0, y_front]]
            ]
            for seg in boundary_segs:
                walls.append(WallModel(
                    wall_id=f"wall_5m_{wall_counter:03d}",
                    wall_type="exterior",
                    centerline=seg,
                    thickness_m=0.25,
                    level_index=lvl
                ))
                wall_counter += 1

            # Interior Dividing Walls
            for i in range(len(lvl_rooms)):
                r1 = lvl_rooms[i]
                p1 = Polygon(r1.polygon)
                for j in range(i + 1, len(lvl_rooms)):
                    r2 = lvl_rooms[j]
                    p2 = Polygon(r2.polygon)

                    inter = p1.intersection(p2)
                    if not inter.is_empty and inter.length >= 0.6:
                        if inter.geom_type == "LineString":
                            lines = [inter]
                        elif hasattr(inter, "geoms"):
                            lines = [g for g in inter.geoms if g.geom_type == "LineString"]
                        else:
                            lines = []

                        for sline in lines:
                            if sline.length >= 0.6:
                                coords = list(sline.coords)
                                sp1 = [round(coords[0][0], 2), round(coords[0][1], 2)]
                                sp2 = [round(coords[-1][0], 2), round(coords[-1][1], 2)]
                                walls.append(WallModel(
                                    wall_id=f"wall_5m_{wall_counter:03d}",
                                    wall_type="interior",
                                    centerline=[sp1, sp2],
                                    thickness_m=0.15,
                                    level_index=lvl
                                ))
                                wall_counter += 1

        # =========================================================================
        # INTENTIONAL ARCHITECTURAL CIRCULATION & DOORS (Strict Code Compliance)
        # =========================================================================
        # GROUND FLOOR DOORS:
        # 1. Main Double Entrance from Porch into Foyer / Stair Lobby
        openings.append(OpeningModel(
            opening_id="door_L0_main_entry",
            opening_type="door",
            position=[x_split, 4.80],
            width_m=1.20,
            connects_rooms=["room_L0_porch", "room_L0_foyer"],
            level_index=0
        ))
        # 2. Living / Drawing Room Entry from Foyer
        openings.append(OpeningModel(
            opening_id="door_L0_drawing",
            opening_type="door",
            position=[4.20, y_front_split],
            width_m=1.00,
            connects_rooms=["room_L0_foyer", "room_L0_drawing"],
            level_index=0
        ))
        # 3. Guest Powder Room from Foyer (strictly private to guests, not in any bedroom)
        openings.append(OpeningModel(
            opening_id="door_L0_powder",
            opening_type="door",
            position=[x_stair_end, 4.80],
            width_m=0.80,
            connects_rooms=["room_L0_foyer", "room_L0_powder"],
            level_index=0
        ))
        # 4. Foyer / Stairs directly connecting into TV Lounge
        openings.append(OpeningModel(
            opening_id="door_L0_foyer_lounge",
            opening_type="door",
            position=[4.20, 6.60],
            width_m=1.10,
            connects_rooms=["room_L0_foyer", "room_L0_tv_lounge"],
            level_index=0
        ))
        # 5. Dining Room access from TV Lounge
        openings.append(OpeningModel(
            opening_id="door_L0_dining_lounge",
            opening_type="door",
            position=[x_split, 5.60],
            width_m=1.00,
            connects_rooms=["room_L0_tv_lounge", "room_L0_dining"],
            level_index=0
        ))
        # 6. Kitchen service door to Dining Room (no bedroom-to-kitchen doors!)
        openings.append(OpeningModel(
            opening_id="door_L0_kitchen_dining",
            opening_type="door",
            position=[1.60, 6.40],
            width_m=0.90,
            connects_rooms=["room_L0_dining", "room_L0_kitchen"],
            level_index=0
        ))
        # 7. Bedroom 1 entrance from TV Lounge
        openings.append(OpeningModel(
            opening_id="door_L0_bed1_lounge",
            opening_type="door",
            position=[4.50, y_mid_split],
            width_m=0.95,
            connects_rooms=["room_L0_tv_lounge", "room_L0_bed1"],
            level_index=0
        ))
        # 8. Attached Bath 1 - Opens ONLY from inside Bedroom 1!
        openings.append(OpeningModel(
            opening_id="door_L0_bed1_bath1",
            opening_type="door",
            position=[2.80, 9.60],
            width_m=0.80,
            connects_rooms=["room_L0_bed1", "room_L0_bath1"],
            level_index=0
        ))
        # 9. Bath 1 / OTS Door
        openings.append(OpeningModel(
            opening_id="door_L0_bath1_ots",
            opening_type="door",
            position=[1.40, 10.60],
            width_m=0.75,
            connects_rooms=["room_L0_bath1", "room_L0_ots"],
            level_index=0
        ))

        # FIRST FLOOR DOORS:
        # 1. Stairs arrive and open directly into Upper TV Lounge / Gallery
        openings.append(OpeningModel(
            opening_id="door_L1_stair_lounge",
            opening_type="door",
            position=[4.20, 6.60],
            width_m=1.10,
            connects_rooms=["room_L1_stairs", "room_L1_tv_lounge"],
            level_index=1
        ))
        # 2. Bedroom 2 (Front Suite) opens into Upper TV Lounge
        openings.append(OpeningModel(
            opening_id="door_L1_bed2_lounge",
            opening_type="door",
            position=[4.20, y_front_split],
            width_m=0.95,
            connects_rooms=["room_L1_tv_lounge", "room_L1_bed2"],
            level_index=1
        ))
        # 3. Attached Bath 2 - Opens ONLY from inside Bedroom 2!
        openings.append(OpeningModel(
            opening_id="door_L1_bed2_bath2",
            opening_type="door",
            position=[x_stair_end, 4.80],
            width_m=0.80,
            connects_rooms=["room_L1_bed2", "room_L1_bath2"],
            level_index=1
        ))
        # 4. Bedroom 2 Balcony Door
        openings.append(OpeningModel(
            opening_id="door_L1_bed2_balcony",
            opening_type="door",
            position=[x_split, 2.00],
            width_m=0.90,
            connects_rooms=["room_L1_bed2", "room_L1_balcony"],
            level_index=1
        ))
        # 5. Bedroom 3 opens into Upper TV Lounge
        openings.append(OpeningModel(
            opening_id="door_L1_bed3_lounge",
            opening_type="door",
            position=[2.60, 7.00],
            width_m=0.90,
            connects_rooms=["room_L1_tv_lounge", "room_L1_bed3"],
            level_index=1
        ))
        # 6. Attached Bath 3 - Opens ONLY from inside Bedroom 3!
        openings.append(OpeningModel(
            opening_id="door_L1_bed3_bath3",
            opening_type="door",
            position=[1.00, 7.00],
            width_m=0.80,
            connects_rooms=["room_L1_bed3", "room_L1_bath3"],
            level_index=1
        ))
        # 7. Bedroom 4 (Rear Suite) opens into Upper TV Lounge
        openings.append(OpeningModel(
            opening_id="door_L1_bed4_lounge",
            opening_type="door",
            position=[4.50, y_mid_split],
            width_m=0.95,
            connects_rooms=["room_L1_tv_lounge", "room_L1_bed4"],
            level_index=1
        ))
        # 8. Attached Bath 4 - Opens ONLY from inside Bedroom 4!
        openings.append(OpeningModel(
            opening_id="door_L1_bed4_bath4",
            opening_type="door",
            position=[2.80, 9.60],
            width_m=0.80,
            connects_rooms=["room_L1_bed4", "room_L1_bath4"],
            level_index=1
        ))
        # 9. Bath 4 / Upper OTS Door
        openings.append(OpeningModel(
            opening_id="door_L1_bath4_ots",
            opening_type="door",
            position=[1.40, 10.60],
            width_m=0.75,
            connects_rooms=["room_L1_bath4", "room_L1_ots"],
            level_index=1
        ))

        # =========================================================================
        # WINDOWS & VENTILATION (Orientation-Aware)
        # =========================================================================
        windows = [
            # Ground Floor
            {"pos": [5.10, y_front], "w": 2.20, "lvl": 0},      # Drawing front glass window
            {"pos": [4.90, y_rear], "w": 1.80, "lvl": 0},       # Bed 1 rear garden window
            {"pos": [1.40, y_rear], "w": 0.80, "lvl": 0},       # Bath 1 rear vent
            {"pos": [x_end, 7.20], "w": 1.50, "lvl": 0},        # TV Lounge side vertical window
            # First Floor
            {"pos": [5.10, y_front], "w": 2.20, "lvl": 1},      # Bed 2 front panoramic window
            {"pos": [4.90, y_rear], "w": 1.80, "lvl": 1},       # Bed 4 rear window
            {"pos": [1.40, y_rear], "w": 0.80, "lvl": 1},       # Bath 4 rear vent
            {"pos": [x_end, 7.20], "w": 1.50, "lvl": 1},        # Upper Lounge side vertical window
            {"pos": [x0, 5.10], "w": 1.40, "lvl": 1}           # Bed 3 side vertical window
        ]
        for idx, w in enumerate(windows, 1):
            openings.append(OpeningModel(
                opening_id=f"wind_5m_{idx:03d}",
                opening_type="window",
                position=w["pos"],
                width_m=w["w"],
                sill_height_m=0.90,
                level_index=w["lvl"]
            ))

        # Build Graph
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.40, min_shared_boundary_m=0.50)
        edges, _ = extractor.build_graph(rooms, openings)

        # Explicit vertical stairs link
        edges.append(GraphEdgeModel(
            source_room_id="room_L0_foyer",
            target_room_id="room_L1_stairs",
            relationship_type="via_door",
            weight=1.0,
            metadata={"vertical_circulation": "modern_stairs", "aligned": True}
        ))

        total_area = sum(r.area_m2 for r in rooms)
        boundary = [[x0, y_front], [x_end, y_front], [x_end, y_rear], [x0, y_rear], [x0, y_front]]

        return CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="synthetic_generated",
                floor_count=2,
                levels=[0, 1],
                unit="m",
                wall_height_m=2.90,
                provenance={
                    "project_title": "5 Marla Contemporary Luxury Residence",
                    "plot_size": "5 Marla (25' x 45' = 1,125 sq ft / 104.5 m²)",
                    "style": "Modern Contemporary Architecture",
                    "features": [
                        "4 Ensuite Bedrooms",
                        "4 Attached Luxury Bathrooms",
                        "Guest Powder Room",
                        "Single Car Porch (Garage)",
                        "Formal Living & Drawing Room",
                        "Central TV Lounge (Dual-Storey)",
                        "Modern Kitchen & Dedicated Dining",
                        "Aligned Vertical Dog-Leg Staircase"
                    ]
                }
            ),
            boundary=boundary,
            total_area_m2=round(total_area, 1),
            walls=walls,
            openings=openings,
            rooms=rooms,
            graph_edges=edges
        )


class Compact5MarlaSingleStoreyEngine:
    """
    Compact 5 Marla Single-Storey Archetype: 25'-0" x 45'-0" (7.62m x 13.72m).
    Single Level (Level 0):
    - 3 Bedrooms:
      * Master Bedroom (Front Left) with Private Ensuite Bathroom (Front Right)
      * Bedroom 2 (Rear Left)
      * Bedroom 3 (Rear Right)
    - 2 Bathrooms:
      * Master Bathroom (Attached exclusively to Master Bed)
      * Common Bathroom (Accessible from Central TV Lounge)
    - Central TV Lounge (The family distribution hub - no bedroom used as corridor)
    - Kitchen & Dining
    - Entrance Foyer
    """

    @classmethod
    def generate_single_storey(cls, plan_id: str = "gen_5m_single_storey") -> CanonicalFloorPlan:
        x0, x_split, x_end = 0.0, 4.20, 7.00
        y0, y_front, y_mid, y_rear = 0.0, 4.00, 8.50, 12.50

        rooms: List[RoomModel] = []
        walls: List[WallModel] = []
        openings: List[OpeningModel] = []

        # 1. Master Bedroom (Front Left: [0, 4.20] x [0, 4.00] = 16.8 m²)
        master_poly = [[x0, y0], [x_split, y0], [x_split, y_front], [x0, y_front], [x0, y0]]
        rooms.append(RoomModel(
            room_id="room_L0_master_bed",
            room_type="bedroom",
            room_name="Master Bedroom",
            polygon=master_poly,
            area_m2=16.8,
            centroid=[2.10, 2.00],
            level_index=0,
            is_habitable=True
        ))

        # 2. Attached Master Bathroom (Front Right: [4.20, 7.00] x [0, 2.00] = 5.6 m²)
        # Shares wall at x=4.20 from y=0 to y=2.00 (length 2.0m) with Master Bedroom
        bath1_poly = [[x_split, y0], [x_end, y0], [x_end, 2.00], [x_split, 2.00], [x_split, y0]]
        rooms.append(RoomModel(
            room_id="room_L0_master_bath",
            room_type="bathroom",
            room_name="Master Bathroom (Attached)",
            polygon=bath1_poly,
            area_m2=5.6,
            centroid=[5.60, 1.00],
            level_index=0,
            is_habitable=False
        ))

        # 3. Entrance & Porch Foyer (Front Right: [4.20, 7.00] x [2.00, 4.00] = 5.6 m²)
        foyer_poly = [[x_split, 2.00], [x_end, 2.00], [x_end, y_front], [x_split, y_front], [x_split, 2.00]]
        rooms.append(RoomModel(
            room_id="room_L0_foyer",
            room_type="corridor",
            room_name="Entrance Lobby",
            polygon=foyer_poly,
            area_m2=5.6,
            centroid=[5.60, 3.00],
            level_index=0,
            is_habitable=False
        ))

        # 4. Central TV Lounge (Central Hub: [0, 4.20] x [4.00, 8.50] = 18.9 m²)
        lounge_poly = [[x0, y_front], [x_split, y_front], [x_split, y_mid], [x0, y_mid], [x0, y_front]]
        rooms.append(RoomModel(
            room_id="room_L0_living",
            room_type="living_room",
            room_name="Living Room (TV Lounge)",
            polygon=lounge_poly,
            area_m2=18.9,
            centroid=[2.10, 6.25],
            level_index=0,
            is_habitable=True
        ))

        # 5. Kitchen & Dining (Middle Right: [4.20, 7.00] x [4.00, 6.50] = 7.0 m²)
        kitchen_poly = [[x_split, y_front], [x_end, y_front], [x_end, 6.50], [x_split, 6.50], [x_split, y_front]]
        rooms.append(RoomModel(
            room_id="room_L0_kitchen",
            room_type="kitchen",
            room_name="Kitchen & Dining",
            polygon=kitchen_poly,
            area_m2=7.0,
            centroid=[5.60, 5.25],
            level_index=0,
            is_habitable=True
        ))

        # 6. Common Bathroom (Middle Right: [4.20, 7.00] x [6.50, 8.50] = 5.6 m²)
        bath2_poly = [[x_split, 6.50], [x_end, 6.50], [x_end, y_mid], [x_split, y_mid], [x_split, 6.50]]
        rooms.append(RoomModel(
            room_id="room_L0_common_bath",
            room_type="bathroom",
            room_name="Common Bathroom",
            polygon=bath2_poly,
            area_m2=5.6,
            centroid=[5.60, 7.50],
            level_index=0,
            is_habitable=False
        ))

        # 7. Bedroom 2 (Rear Left: [0, 3.50] x [8.50, 12.50] = 14.0 m²)
        bed2_poly = [[x0, y_mid], [3.50, y_mid], [3.50, y_rear], [x0, y_rear], [x0, y_mid]]
        rooms.append(RoomModel(
            room_id="room_L0_bed2",
            room_type="bedroom",
            room_name="Bedroom 2",
            polygon=bed2_poly,
            area_m2=14.0,
            centroid=[1.75, 10.50],
            level_index=0,
            is_habitable=True
        ))

        # 8. Bedroom 3 (Rear Right: [3.50, 7.00] x [8.50, 12.50] = 14.0 m²)
        bed3_poly = [[3.50, y_mid], [x_end, y_mid], [x_end, y_rear], [3.50, y_rear], [3.50, y_mid]]
        rooms.append(RoomModel(
            room_id="room_L0_bed3",
            room_type="bedroom",
            room_name="Bedroom 3",
            polygon=bed3_poly,
            area_m2=14.0,
            centroid=[5.25, 10.50],
            level_index=0,
            is_habitable=True
        ))

        # Exterior Walls
        boundary = [[x0, y0], [x_end, y0], [x_end, y_rear], [x0, y_rear], [x0, y0]]
        for seg in [
            [[x0, y0], [x_end, y0]],
            [[x_end, y0], [x_end, y_rear]],
            [[x_end, y_rear], [x0, y_rear]],
            [[x0, y_rear], [x0, y0]]
        ]:
            walls.append(WallModel(wall_id=f"wall_ext_{len(walls)+1}", wall_type="exterior", centerline=seg, thickness_m=0.25, level_index=0))

        # Interior Walls
        for i in range(len(rooms)):
            p1 = Polygon(rooms[i].polygon)
            for j in range(i + 1, len(rooms)):
                p2 = Polygon(rooms[j].polygon)
                inter = p1.intersection(p2)
                if not inter.is_empty and inter.length >= 0.6:
                    if inter.geom_type == "LineString":
                        lines = [inter]
                    elif inter.geom_type == "MultiLineString":
                        lines = list(inter.geoms)
                    else:
                        lines = []
                    for line in lines:
                        walls.append(WallModel(
                            wall_id=f"wall_int_{len(walls)+1}",
                            wall_type="interior",
                            centerline=[list(line.coords[0]), list(line.coords[-1])],
                            thickness_m=0.15,
                            level_index=0
                        ))

        # Doors (Strict Central Hub Circulation & Privacy)
        # 1. Main entry from outside into Entrance Foyer
        openings.append(OpeningModel(opening_id="door_main_entry", opening_type="door", position=[x_end, 3.00], width_m=1.20, connects_rooms=["room_L0_foyer", "room_L0_living"], level_index=0))
        # 2. Foyer into Central TV Lounge
        openings.append(OpeningModel(opening_id="door_foyer_lounge", opening_type="door", position=[x_split, 3.00], width_m=1.20, connects_rooms=["room_L0_foyer", "room_L0_living"], level_index=0))
        # 3. Central TV Lounge to Master Bedroom
        openings.append(OpeningModel(opening_id="door_lounge_master", opening_type="door", position=[2.10, y_front], width_m=0.95, connects_rooms=["room_L0_living", "room_L0_master_bed"], level_index=0))
        # 4. Master Bedroom to Attached Master Bath (Private door on shared wall at x=4.20)
        openings.append(OpeningModel(opening_id="door_master_bath", opening_type="door", position=[x_split, 1.00], width_m=0.80, connects_rooms=["room_L0_master_bed", "room_L0_master_bath"], level_index=0))
        # 5. Central TV Lounge to Kitchen
        openings.append(OpeningModel(opening_id="door_lounge_kitchen", opening_type="door", position=[x_split, 5.25], width_m=0.90, connects_rooms=["room_L0_living", "room_L0_kitchen"], level_index=0))
        # 6. Central TV Lounge to Common Bathroom
        openings.append(OpeningModel(opening_id="door_lounge_common_bath", opening_type="door", position=[x_split, 7.50], width_m=0.80, connects_rooms=["room_L0_living", "room_L0_common_bath"], level_index=0))
        # 7. Central TV Lounge to Bedroom 2
        openings.append(OpeningModel(opening_id="door_lounge_bed2", opening_type="door", position=[1.75, y_mid], width_m=0.90, connects_rooms=["room_L0_living", "room_L0_bed2"], level_index=0))
        # 8. Central TV Lounge to Bedroom 3
        openings.append(OpeningModel(opening_id="door_lounge_bed3", opening_type="door", position=[4.20, y_mid], width_m=0.90, connects_rooms=["room_L0_living", "room_L0_bed3"], level_index=0))

        # Windows
        windows = [
            {"pos": [2.10, y0], "w": 2.20},        # Master bed front window
            {"pos": [5.60, y0], "w": 0.80},        # Master bath front window/vent
            {"pos": [x0, 6.25], "w": 2.40},        # TV lounge side window
            {"pos": [x_end, 5.25], "w": 1.60},     # Kitchen side window
            {"pos": [x_end, 7.50], "w": 0.80},     # Common bath side vent
            {"pos": [1.75, y_rear], "w": 1.80},    # Bed 2 rear window
            {"pos": [5.25, y_rear], "w": 1.80}     # Bed 3 rear window
        ]
        for idx, w in enumerate(windows, 1):
            openings.append(OpeningModel(opening_id=f"wind_5m_s_{idx}", opening_type="window", position=w["pos"], width_m=w["w"], sill_height_m=0.90, level_index=0))

        # Graph Edges
        edges = [
            GraphEdgeModel(source_room_id="room_L0_foyer", target_room_id="room_L0_living", relationship_type="via_door", weight=1.0),
            GraphEdgeModel(source_room_id="room_L0_living", target_room_id="room_L0_master_bed", relationship_type="via_door", weight=1.0),
            GraphEdgeModel(source_room_id="room_L0_master_bed", target_room_id="room_L0_master_bath", relationship_type="via_door", weight=1.0, metadata={"attached": True}),
            GraphEdgeModel(source_room_id="room_L0_living", target_room_id="room_L0_kitchen", relationship_type="via_door", weight=1.0),
            GraphEdgeModel(source_room_id="room_L0_living", target_room_id="room_L0_common_bath", relationship_type="via_door", weight=1.0),
            GraphEdgeModel(source_room_id="room_L0_living", target_room_id="room_L0_bed2", relationship_type="via_door", weight=1.0),
            GraphEdgeModel(source_room_id="room_L0_living", target_room_id="room_L0_bed3", relationship_type="via_door", weight=1.0),
        ]

        total_area = sum(r.area_m2 for r in rooms)

        return CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="synthetic_generated",
                floor_count=1,
                levels=[0],
                unit="m",
                wall_height_m=2.90,
                provenance={
                    "project_title": "5 Marla Compact Single-Storey Residence",
                    "plot_size": "5 Marla (25' x 45' = 1,125 sq ft / 105 m²)",
                    "style": "Modern Single-Storey Architecture",
                    "features": [
                        "3 Bedrooms (Master Suite + 2 Secondary Bedrooms)",
                        "2 Bathrooms (1 Private Ensuite, 1 Common)",
                        "Central TV Lounge (Family Distribution Hub)",
                        "Kitchen & Dining",
                        "Entrance Foyer"
                    ]
                }
            ),
            boundary=boundary,
            total_area_m2=round(total_area, 1),
            walls=walls,
            openings=openings,
            rooms=rooms,
            graph_edges=edges
        )


class Luxury1KanalArchitecturalEngine:
    """
    1 Kanal Luxury Estate Archetype: 50'-0" x 90'-0" (15.24m x 27.43m).
    Covered buildable width: 12.20m (leaving 5' side passages on both sides).
    Covered buildable depth: 20.00m (leaving 17' front lawn + porch, and 5' rear setback).
    2 Storeys:
    - 5 Bedrooms with 5 Attached Luxury Dressing Bathrooms + 1 Guest Powder Room
    - Double Car Porch (Garage for 2 full SUVs)
    - Formal Drawing Room with 45° chamfered entrance
    - Grand Helical Stair Hall with curved staircase
    - Formal Dining Room
    - Double Kitchen: Main Show Kitchen + Dirty/Spice Kitchen with side service door
    - Internal Green Patio / Light Courtyard
    - Central Family TV Lounge (Dual-Storey)
    """

    @classmethod
    def generate_1_kanal_house(cls, plan_id: str = "gen_1k_plan") -> CanonicalFloorPlan:
        x0, x_split, x_stair, x_end = 0.0, 6.10, 6.10, 12.20
        y_front, y_front_split, y_mid_split, y_rear = 0.0, 5.00, 13.00, 20.00

        rooms: List[RoomModel] = []
        walls: List[WallModel] = []
        openings: List[OpeningModel] = []

        # LEVEL 0 (GROUND FLOOR)
        # 1. Double Car Porch (Front-Right: [6.10, 12.20] x [0, 5.00])
        porch_poly = [[x_split, y_front], [x_end, y_front], [x_end, y_front_split], [x_split, y_front_split], [x_split, y_front]]
        rooms.append(RoomModel(room_id="room_L0_porch", room_type="garage", room_name="Car Porch (2 SUVs)", polygon=porch_poly, area_m2=round(6.10 * 5.00, 1), centroid=[9.15, 2.50], level_index=0, is_habitable=False))

        # 2. Formal Drawing Room (Front-Left: [0, 6.10] x [0, 5.00])
        drawing_poly = [[x0, y_front], [x_split, y_front], [x_split, y_front_split], [x0, y_front_split], [x0, y_front]]
        rooms.append(RoomModel(room_id="room_L0_drawing", room_type="living_room", room_name="Drawing Room (Formal)", polygon=drawing_poly, area_m2=round(6.10 * 5.00, 1), centroid=[3.05, 2.50], level_index=0, is_habitable=True))

        # 3. Grand Helical Stair Hall & Foyer ([0, 5.00] x [5.00, 9.20])
        stair_poly = [[x0, y_front_split], [5.00, y_front_split], [5.00, 9.20], [x0, 9.20], [x0, y_front_split]]
        rooms.append(RoomModel(room_id="room_L0_stair_hall", room_type="corridor", room_name="Stair Hall (Grand Helical)", polygon=stair_poly, area_m2=round(5.00 * 4.20, 1), centroid=[2.50, 7.10], level_index=0, is_habitable=False))

        # 4. Guest Powder Room ([0, 2.00] x [9.20, 10.80])
        powder_poly = [[x0, 9.20], [2.00, 9.20], [2.00, 10.80], [x0, 10.80], [x0, 9.20]]
        rooms.append(RoomModel(room_id="room_L0_powder", room_type="bathroom", room_name="Powder Room", polygon=powder_poly, area_m2=round(2.00 * 1.60, 1), centroid=[1.00, 10.00], level_index=0, is_habitable=False))

        # 5. Formal Dining Room ([7.50, 12.20] x [5.00, 9.00])
        dining_poly = [[7.50, y_front_split], [x_end, y_front_split], [x_end, 9.00], [7.50, 9.00], [7.50, y_front_split]]
        rooms.append(RoomModel(room_id="room_L0_dining", room_type="dining", room_name="Dining Room", polygon=dining_poly, area_m2=round(4.70 * 4.00, 1), centroid=[9.85, 7.00], level_index=0, is_habitable=True))

        # 6. Main Kitchen ([7.50, 12.20] x [9.00, 13.00])
        kitchen_poly = [[7.50, 9.00], [x_end, 9.00], [x_end, y_mid_split], [7.50, y_mid_split], [7.50, 9.00]]
        rooms.append(RoomModel(room_id="room_L0_kitchen", room_type="kitchen", room_name="Main Kitchen", polygon=kitchen_poly, area_m2=round(4.70 * 4.00, 1), centroid=[9.85, 11.00], level_index=0, is_habitable=True))

        # 7. Dirty Kitchen / Spice Kitchen ([5.00, 7.50] x [9.00, 13.00])
        skit_poly = [[5.00, 9.00], [7.50, 9.00], [7.50, y_mid_split], [5.00, y_mid_split], [5.00, 9.00]]
        rooms.append(RoomModel(room_id="room_L0_skit", room_type="kitchen", room_name="Dirty Kitchen (S.KIT)", polygon=skit_poly, area_m2=round(2.50 * 4.00, 1), centroid=[6.25, 11.00], level_index=0, is_habitable=True))

        # 8. Central Family TV Lounge ([2.00, 5.00] x [9.20, 13.00] + [0, 5.00] x [10.80, 13.00])
        lounge_poly = [[2.00, 9.20], [5.00, 9.20], [5.00, y_mid_split], [x0, y_mid_split], [x0, 10.80], [2.00, 10.80], [2.00, 9.20]]
        rooms.append(RoomModel(room_id="room_L0_tv_lounge", room_type="lounge", room_name="TV Lounge (Family Living)", polygon=lounge_poly, area_m2=round(3.00 * 3.80 + 2.00 * 2.20, 1), centroid=[2.80, 11.40], level_index=0, is_habitable=True))

        # 9. Internal Green Patio / Light Courtyard ([5.00, 7.50] x [5.00, 9.00])
        patio_poly = [[5.00, 5.00], [7.50, 5.00], [7.50, 9.00], [5.00, 9.00], [5.00, 5.00]]
        rooms.append(RoomModel(room_id="room_L0_patio", room_type="outdoor", room_name="Internal Green Patio", polygon=patio_poly, area_m2=round(2.50 * 4.00, 1), centroid=[6.25, 7.00], level_index=0, is_habitable=False))

        # 10. Ground Master Bedroom Suite ([0, 6.50] x [13.00, 20.00])
        bed1_poly = [[x0, y_mid_split], [6.50, y_mid_split], [6.50, y_rear], [x0, y_rear], [x0, y_mid_split]]
        rooms.append(RoomModel(room_id="room_L0_bed1", room_type="bedroom", room_name="Master Suite 1 (Ground)", polygon=bed1_poly, area_m2=round(6.50 * 7.00, 1), centroid=[3.25, 16.50], level_index=0, is_habitable=True))

        # 11. Attached Dressing & Bath 1 ([6.50, 12.20] x [13.00, 16.50]) - SHARES 1D WALL WITH BEDROOM 1!
        bath1_poly = [[6.50, y_mid_split], [x_end, y_mid_split], [x_end, 16.50], [6.50, 16.50], [6.50, y_mid_split]]
        rooms.append(RoomModel(room_id="room_L0_bath1", room_type="bathroom", room_name="Attached Bath 1 (D/Bath)", polygon=bath1_poly, area_m2=round(5.70 * 3.50, 1), centroid=[9.35, 14.75], level_index=0, is_habitable=False))

        # 12. Rear OTS / Laundry ([6.50, 12.20] x [16.50, 20.00])
        ots_poly = [[6.50, 16.50], [x_end, 16.50], [x_end, y_rear], [6.50, y_rear], [6.50, 16.50]]
        rooms.append(RoomModel(room_id="room_L0_ots", room_type="outdoor", room_name="Rear OTS & Lawn Passage", polygon=ots_poly, area_m2=round(5.70 * 3.50, 1), centroid=[9.35, 18.25], level_index=0, is_habitable=False))

        # LEVEL 1 (FIRST FLOOR)
        # 4 Additional Ensuite Bedrooms on Level 1 + Upper Lounge
        # Stair Landing matches Level 0: [0, 5.00] x [5.00, 9.20]
        rooms.append(RoomModel(room_id="room_L1_stair_hall", room_type="corridor", room_name="Stair Landing", polygon=stair_poly, area_m2=round(5.00 * 4.20, 1), centroid=[2.50, 7.10], level_index=1, is_habitable=False))
        # Upper Lounge: [0, 6.10] x [9.20, 13.00]
        rooms.append(RoomModel(room_id="room_L1_tv_lounge", room_type="lounge", room_name="Upper Family Lounge", polygon=[[x0, 9.20], [x_split, 9.20], [x_split, y_mid_split], [x0, y_mid_split], [x0, 9.20]], area_m2=round(6.10 * 3.80, 1), centroid=[3.05, 11.10], level_index=1, is_habitable=True))
        # Bed 2 (Front Suite): [0, 6.10] x [0, 5.00]
        rooms.append(RoomModel(room_id="room_L1_bed2", room_type="bedroom", room_name="Bedroom 2 (Front Suite)", polygon=drawing_poly, area_m2=round(6.10 * 5.00, 1), centroid=[3.05, 2.50], level_index=1, is_habitable=True))
        # Bath 2: [6.10, 9.00] x [5.00, 7.50] - SHARES WALL WITH BED 2!
        rooms.append(RoomModel(room_id="room_L1_bath2", room_type="bathroom", room_name="Attached Bath 2", polygon=[[x_split, y_front_split], [9.00, y_front_split], [9.00, 7.50], [x_split, 7.50], [x_split, y_front_split]], area_m2=round(2.90 * 2.50, 1), centroid=[7.55, 6.25], level_index=1, is_habitable=False))
        # Bed 3: [6.10, 12.20] x [0, 5.00] (over porch)
        rooms.append(RoomModel(room_id="room_L1_bed3", room_type="bedroom", room_name="Bedroom 3", polygon=porch_poly, area_m2=round(6.10 * 5.00, 1), centroid=[9.15, 2.50], level_index=1, is_habitable=True))
        # Bath 3: [9.00, 12.20] x [5.00, 7.50] - SHARES WALL WITH BED 3!
        rooms.append(RoomModel(room_id="room_L1_bath3", room_type="bathroom", room_name="Attached Bath 3", polygon=[[9.00, y_front_split], [x_end, y_front_split], [x_end, 7.50], [9.00, 7.50], [9.00, y_front_split]], area_m2=round(3.20 * 2.50, 1), centroid=[10.60, 6.25], level_index=1, is_habitable=False))
        # Bed 4: [0, 6.50] x [13.00, 20.00]
        rooms.append(RoomModel(room_id="room_L1_bed4", room_type="bedroom", room_name="Bedroom 4", polygon=bed1_poly, area_m2=round(6.50 * 7.00, 1), centroid=[3.25, 16.50], level_index=1, is_habitable=True))
        # Bath 4: [6.50, 12.20] x [13.00, 16.50] - SHARES WALL WITH BED 4!
        rooms.append(RoomModel(room_id="room_L1_bath4", room_type="bathroom", room_name="Attached Bath 4", polygon=bath1_poly, area_m2=round(5.70 * 3.50, 1), centroid=[9.35, 14.75], level_index=1, is_habitable=False))
        # Bed 5: [6.10, 12.20] x [7.50, 13.00]
        rooms.append(RoomModel(room_id="room_L1_bed5", room_type="bedroom", room_name="Bedroom 5", polygon=[[x_split, 7.50], [x_end, 7.50], [x_end, y_mid_split], [x_split, y_mid_split], [x_split, 7.50]], area_m2=round(6.10 * 5.50, 1), centroid=[9.15, 10.25], level_index=1, is_habitable=True))
        # Bath 5: [6.50, 12.20] x [16.50, 20.00] (over OTS rear)
        rooms.append(RoomModel(room_id="room_L1_bath5", room_type="bathroom", room_name="Attached Bath 5", polygon=ots_poly, area_m2=round(5.70 * 3.50, 1), centroid=[9.35, 18.25], level_index=1, is_habitable=False))

        # Walls Generation
        for lvl in [0, 1]:
            lvl_rooms = [r for r in rooms if r.level_index == lvl]
            for seg in [
                [[x0, y_front], [x_end, y_front]],
                [[x_end, y_front], [x_end, y_rear]],
                [[x_end, y_rear], [x0, y_rear]],
                [[x0, y_rear], [x0, y_front]]
            ]:
                walls.append(WallModel(wall_id=f"wall_1k_ext_{len(walls)+1}", wall_type="exterior", centerline=seg, thickness_m=0.30, level_index=lvl))

            for i in range(len(lvl_rooms)):
                p1 = Polygon(lvl_rooms[i].polygon)
                for j in range(i + 1, len(lvl_rooms)):
                    p2 = Polygon(lvl_rooms[j].polygon)
                    inter = p1.intersection(p2)
                    if not inter.is_empty and inter.length >= 0.8:
                        if inter.geom_type == "LineString":
                            lines = [inter]
                        elif hasattr(inter, "geoms"):
                            lines = [g for g in inter.geoms if g.geom_type == "LineString"]
                        else:
                            lines = []
                        for sline in lines:
                            if sline.length >= 0.8:
                                c = list(sline.coords)
                                walls.append(WallModel(wall_id=f"wall_1k_int_{len(walls)+1}", wall_type="interior", centerline=[[c[0][0], c[0][1]], [c[-1][0], c[-1][1]]], thickness_m=0.15, level_index=lvl))

        # Doors (Strict Placement)
        # Ground Floor:
        openings.append(OpeningModel(opening_id="door_1k_main", opening_type="door", position=[6.10, 5.00], width_m=1.50, connects_rooms=["room_L0_porch", "room_L0_stair_hall"], level_index=0))
        openings.append(OpeningModel(opening_id="door_1k_draw", opening_type="door", position=[3.05, 5.00], width_m=1.40, connects_rooms=["room_L0_drawing", "room_L0_stair_hall"], level_index=0))
        openings.append(OpeningModel(opening_id="door_1k_powder", opening_type="door", position=[1.00, 9.20], width_m=0.80, connects_rooms=["room_L0_stair_hall", "room_L0_powder"], level_index=0))
        openings.append(OpeningModel(opening_id="door_1k_dining", opening_type="door", position=[6.10, 7.00], width_m=1.40, connects_rooms=["room_L0_stair_hall", "room_L0_dining"], level_index=0))
        openings.append(OpeningModel(opening_id="door_1k_lounge", opening_type="door", position=[2.50, 9.20], width_m=1.20, connects_rooms=["room_L0_stair_hall", "room_L0_tv_lounge"], level_index=0))
        openings.append(OpeningModel(opening_id="door_1k_kit_din", opening_type="door", position=[7.50, 9.00], width_m=1.00, connects_rooms=["room_L0_dining", "room_L0_kitchen"], level_index=0))
        openings.append(OpeningModel(opening_id="door_1k_skit", opening_type="door", position=[6.25, 9.00], width_m=0.90, connects_rooms=["room_L0_kitchen", "room_L0_skit"], level_index=0))
        openings.append(OpeningModel(opening_id="door_1k_bed1", opening_type="door", position=[3.25, 13.00], width_m=1.00, connects_rooms=["room_L0_tv_lounge", "room_L0_bed1"], level_index=0))
        # BEDROOM 1 TO ATTACHED BATH 1 (Private interior door on shared wall!)
        openings.append(OpeningModel(opening_id="door_1k_bed1_bath1", opening_type="door", position=[6.50, 14.75], width_m=0.85, connects_rooms=["room_L0_bed1", "room_L0_bath1"], level_index=0))

        # First Floor:
        openings.append(OpeningModel(opening_id="door_1k_l1_stair", opening_type="door", position=[2.50, 9.20], width_m=1.20, connects_rooms=["room_L1_stair_hall", "room_L1_tv_lounge"], level_index=1))
        openings.append(OpeningModel(opening_id="door_1k_l1_bed2", opening_type="door", position=[3.05, 5.00], width_m=1.00, connects_rooms=["room_L1_stair_hall", "room_L1_bed2"], level_index=1))
        openings.append(OpeningModel(opening_id="door_1k_l1_bath2", opening_type="door", position=[6.10, 6.25], width_m=0.85, connects_rooms=["room_L1_bed2", "room_L1_bath2"], level_index=1))
        openings.append(OpeningModel(opening_id="door_1k_l1_bed3", opening_type="door", position=[6.10, 5.00], width_m=1.00, connects_rooms=["room_L1_stair_hall", "room_L1_bed3"], level_index=1))
        openings.append(OpeningModel(opening_id="door_1k_l1_bath3", opening_type="door", position=[9.00, 6.25], width_m=0.85, connects_rooms=["room_L1_bed3", "room_L1_bath3"], level_index=1))
        openings.append(OpeningModel(opening_id="door_1k_l1_bed4", opening_type="door", position=[3.25, 13.00], width_m=1.00, connects_rooms=["room_L1_tv_lounge", "room_L1_bed4"], level_index=1))
        openings.append(OpeningModel(opening_id="door_1k_l1_bath4", opening_type="door", position=[6.50, 14.75], width_m=0.85, connects_rooms=["room_L1_bed4", "room_L1_bath4"], level_index=1))
        openings.append(OpeningModel(opening_id="door_1k_l1_bed5", opening_type="door", position=[6.10, 10.25], width_m=1.00, connects_rooms=["room_L1_tv_lounge", "room_L1_bed5"], level_index=1))
        openings.append(OpeningModel(opening_id="door_1k_l1_bath5", opening_type="door", position=[9.35, 16.50], width_m=0.85, connects_rooms=["room_L1_bed5", "room_L1_bath5"], level_index=1))

        # Windows
        windows = [
            {"pos": [3.05, y_front], "w": 2.50, "lvl": 0},
            {"pos": [3.25, y_rear], "w": 2.20, "lvl": 0},
            {"pos": [x_end, 11.00], "w": 1.80, "lvl": 0},
            {"pos": [3.05, y_front], "w": 2.50, "lvl": 1},
            {"pos": [9.15, y_front], "w": 2.50, "lvl": 1},
            {"pos": [3.25, y_rear], "w": 2.20, "lvl": 1},
        ]
        for idx, w in enumerate(windows, 1):
            openings.append(OpeningModel(opening_id=f"wind_1k_{idx}", opening_type="window", position=w["pos"], width_m=w["w"], sill_height_m=0.90, level_index=w["lvl"]))

        # Build Graph
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.50, min_shared_boundary_m=0.60)
        edges, _ = extractor.build_graph(rooms, openings)

        edges.append(GraphEdgeModel(
            source_room_id="room_L0_stair_hall",
            target_room_id="room_L1_stair_hall",
            relationship_type="via_door",
            weight=1.0,
            metadata={"vertical_circulation": "grand_helical_stairs", "aligned": True}
        ))

        total_area = sum(r.area_m2 for r in rooms)
        boundary = [[x0, y_front], [x_end, y_front], [x_end, y_rear], [x0, y_rear], [x0, y_front]]

        return CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="synthetic_generated",
                floor_count=2,
                levels=[0, 1],
                unit="m",
                wall_height_m=3.20,
                provenance={
                    "project_title": "1 Kanal Luxury Contemporary Estate",
                    "plot_size": "1 Kanal (50' x 90' = 4,500 sq ft / 418 m²)",
                    "style": "Contemporary Luxury Architecture",
                    "features": [
                        "5 Ensuite Bedrooms with Walk-in Dressing",
                        "5 Attached Luxury Bathrooms",
                        "Guest Powder Room",
                        "Double Car Porch (2 SUVs)",
                        "Formal Drawing & Dining",
                        "Grand Helical Stair Hall",
                        "Double Kitchen (Main + Dirty/Spice Kitchen)",
                        "Internal Green Patio Courtyard"
                    ]
                }
            ),
            boundary=boundary,
            total_area_m2=round(total_area, 1),
            walls=walls,
            openings=openings,
            rooms=rooms,
            graph_edges=edges
        )

def _build_walls_for_levels(rooms: List[RoomModel], x0: float = 0.0, x_end: float = 9.75, y_front: float = 0.0, y_rear: float = 16.0) -> List[WallModel]:
    """Helper to generate continuous exterior envelope and interior divider walls."""
    walls: List[WallModel] = []
    wall_counter = 1
    for lvl in [0, 1]:
        lvl_rooms = [r for r in rooms if r.level_index == lvl]
        # Exterior perimeter boundary
        boundary_segs = [
            [[x0, y_front], [x_end, y_front]],
            [[x_end, y_front], [x_end, y_rear]],
            [[x_end, y_rear], [x0, y_rear]],
            [[x0, y_rear], [x0, y_front]]
        ]
        for seg in boundary_segs:
            walls.append(WallModel(
                wall_id=f"wall_{lvl}_{wall_counter:03d}",
                wall_type="exterior",
                centerline=seg,
                thickness_m=0.25,
                level_index=lvl
            ))
            wall_counter += 1

        # Interior dividing walls from shared boundaries
        for i in range(len(lvl_rooms)):
            r1 = lvl_rooms[i]
            p1 = Polygon(r1.polygon)
            for j in range(i + 1, len(lvl_rooms)):
                r2 = lvl_rooms[j]
                p2 = Polygon(r2.polygon)
                inter = p1.intersection(p2)
                if not inter.is_empty and inter.length >= 0.70:
                    if inter.geom_type == "LineString":
                        lines = [inter]
                    elif hasattr(inter, "geoms"):
                        lines = [g for g in inter.geoms if g.geom_type == "LineString"]
                    else:
                        lines = []
                    for sline in lines:
                        if sline.length >= 0.70:
                            coords = list(sline.coords)
                            sp1 = [round(coords[0][0], 2), round(coords[0][1], 2)]
                            sp2 = [round(coords[-1][0], 2), round(coords[-1][1], 2)]
                            walls.append(WallModel(
                                wall_id=f"wall_{lvl}_{wall_counter:03d}",
                                wall_type="interior",
                                centerline=[sp1, sp2],
                                thickness_m=0.15,
                                level_index=lvl
                            ))
                            wall_counter += 1
    return walls


class TypologyALinearSpineEngine:
    """
    Typology A: "Linear Spine / Asymmetrical Villa" (10 Marla / 35'x65' Deep Lot)
    Circulation: Dogleg staircase off Foyer along flank wall [0, 2.50] x [4.80, 8.00]; straight longitudinal central corridor.
    Spatial Flow: Foyer -> Lounge (Central) -> Kitchen & Dining on East Flank -> Rear Dual Bed Suites.
    Level 1: Front Open Terrace directly over Car Porch; 3 Upper Bedrooms with central Upper Lounge.
    """
    @classmethod
    def generate_linear_spine_villa(cls, plan_id: str = "typology_a_linear_spine") -> CanonicalFloorPlan:
        x0, x_split, x_cor_end, x_mid, x_end = 0.0, 2.50, 4.25, 6.80, 9.75
        y_front, y_porch_end, y_stair_end, y_powder_end, y_mid_end, y_bed_split, y_rear = 0.0, 4.80, 8.00, 9.60, 11.20, 14.50, 16.00

        rooms: List[RoomModel] = []
        openings: List[OpeningModel] = []

        # ================= LEVEL 0 (GROUND FLOOR) =================
        rooms.append(RoomModel(room_id="room_L0_porch", room_type="garage", room_name="Car Porch (2 Cars)",
                               polygon=[[x0, y_front], [x_cor_end, y_front], [x_cor_end, y_porch_end], [x0, y_porch_end], [x0, y_front]],
                               area_m2=round(4.25 * 4.80, 1), centroid=[2.12, 2.40], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_drawing", room_type="living_room", room_name="Drawing Room (Formal)",
                               polygon=[[x_cor_end, y_front], [x_end, y_front], [x_end, y_porch_end], [x_cor_end, y_porch_end], [x_cor_end, y_front]],
                               area_m2=round(5.50 * 4.80, 1), centroid=[7.00, 2.40], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_stairs", room_type="corridor", room_name="Dogleg Staircase (UP ->)",
                               polygon=[[x0, y_porch_end], [x_split, y_porch_end], [x_split, y_stair_end], [x0, y_stair_end], [x0, y_porch_end]],
                               area_m2=round(2.50 * 3.20, 1), centroid=[1.25, 6.40], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_powder", room_type="bathroom", room_name="Powder Room",
                               polygon=[[x0, y_stair_end], [x_split, y_stair_end], [x_split, y_powder_end], [x0, y_powder_end], [x0, y_stair_end]],
                               area_m2=round(2.50 * 1.60, 1), centroid=[1.25, 8.80], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_corridor", room_type="corridor", room_name="Central Linear Spine",
                               polygon=[[x_split, y_porch_end], [x_cor_end, y_porch_end], [x_cor_end, y_mid_end], [x_split, y_mid_end], [x_split, y_porch_end]],
                               area_m2=round(1.75 * 6.40, 1), centroid=[3.38, 8.00], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_tv_lounge", room_type="living_room", room_name="Central Family TV Lounge",
                               polygon=[[x_cor_end, y_porch_end], [x_mid, y_porch_end], [x_mid, y_mid_end], [x_cor_end, y_mid_end], [x_cor_end, y_porch_end]],
                               area_m2=round(2.55 * 6.40, 1), centroid=[5.52, 8.00], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_dining", room_type="dining_room", room_name="Formal Dining Room",
                               polygon=[[x_mid, y_porch_end], [x_end, y_porch_end], [x_end, y_stair_end], [x_mid, y_stair_end], [x_mid, y_porch_end]],
                               area_m2=round(2.95 * 3.20, 1), centroid=[8.28, 6.40], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_kitchen", room_type="kitchen", room_name="Modern Kitchen (East Flank)",
                               polygon=[[x_mid, y_stair_end], [x_end, y_stair_end], [x_end, y_mid_end], [x_mid, y_mid_end], [x_mid, y_stair_end]],
                               area_m2=round(2.95 * 3.20, 1), centroid=[8.28, 9.60], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_bed1", room_type="bedroom", room_name="Ground Master Bedroom 1",
                               polygon=[[x0, y_mid_end], [4.875, y_mid_end], [4.875, y_bed_split], [x0, y_bed_split], [x0, y_mid_end]],
                               area_m2=round(4.875 * 3.30, 1), centroid=[2.44, 12.85], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_bath1", room_type="bathroom", room_name="Attached Bath 1 (Master)",
                               polygon=[[x0, y_bed_split], [4.875, y_bed_split], [4.875, y_rear], [x0, y_rear], [x0, y_bed_split]],
                               area_m2=round(4.875 * 1.50, 1), centroid=[2.44, 15.25], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_bed2", room_type="bedroom", room_name="Ground Bedroom 2",
                               polygon=[[4.875, y_mid_end], [x_end, y_mid_end], [x_end, y_bed_split], [4.875, y_bed_split], [4.875, y_mid_end]],
                               area_m2=round(4.875 * 3.30, 1), centroid=[7.31, 12.85], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_bath2", room_type="bathroom", room_name="Attached Bath 2",
                               polygon=[[4.875, y_bed_split], [x_end, y_bed_split], [x_end, y_rear], [4.875, y_rear], [4.875, y_bed_split]],
                               area_m2=round(4.875 * 1.50, 1), centroid=[7.31, 15.25], level_index=0, is_habitable=False))

        # ================= LEVEL 1 (FIRST FLOOR) =================
        # Level 1 Setback Envelope: Car Porch converts to Front Open Terrace
        rooms.append(RoomModel(room_id="room_L1_terrace", room_type="balcony", room_name="Front Open Terrace",
                               polygon=[[x0, y_front], [x_cor_end, y_front], [x_cor_end, y_porch_end], [x0, y_porch_end], [x0, y_front]],
                               area_m2=round(4.25 * 4.80, 1), centroid=[2.12, 2.40], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed3", room_type="bedroom", room_name="Upper Front Bedroom 3",
                               polygon=[[x_cor_end, 1.50], [x_end, 1.50], [x_end, y_porch_end], [x_cor_end, y_porch_end], [x_cor_end, 1.50]],
                               area_m2=round(5.50 * 3.30, 1), centroid=[7.00, 3.15], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath3", room_type="bathroom", room_name="Attached Bath 3",
                               polygon=[[x_cor_end, y_front], [x_end, y_front], [x_end, 1.50], [x_cor_end, 1.50], [x_cor_end, y_front]],
                               area_m2=round(5.50 * 1.50, 1), centroid=[7.00, 0.75], level_index=1, is_habitable=False))
        # Staircase Invariance: Pin exact (X1, Y1, X2, Y2) coordinates between Level 0 and Level 1
        rooms.append(RoomModel(room_id="room_L1_stairs", room_type="corridor", room_name="Upper Stair Landing (DN <-)",
                               polygon=[[x0, y_porch_end], [x_split, y_porch_end], [x_split, y_stair_end], [x0, y_stair_end], [x0, y_porch_end]],
                               area_m2=round(2.50 * 3.20, 1), centroid=[1.25, 6.40], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bath_util", room_type="bathroom", room_name="Upper Bath & Laundry",
                               polygon=[[x0, y_stair_end], [x_split, y_stair_end], [x_split, y_powder_end], [x0, y_powder_end], [x0, y_stair_end]],
                               area_m2=round(2.50 * 1.60, 1), centroid=[1.25, 8.80], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_corridor", room_type="corridor", room_name="Upper Corridor Spine",
                               polygon=[[x_split, y_porch_end], [x_cor_end, y_porch_end], [x_cor_end, y_mid_end], [x_split, y_mid_end], [x_split, y_porch_end]],
                               area_m2=round(1.75 * 6.40, 1), centroid=[3.38, 8.00], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_tv_lounge", room_type="living_room", room_name="Upper Family TV Lounge",
                               polygon=[[x_cor_end, y_porch_end], [x_mid, y_porch_end], [x_mid, y_mid_end], [x_cor_end, y_mid_end], [x_cor_end, y_porch_end]],
                               area_m2=round(2.55 * 6.40, 1), centroid=[5.52, 8.00], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bed4", room_type="bedroom", room_name="Upper Bedroom 4",
                               polygon=[[x_mid, y_porch_end], [x_end, y_porch_end], [x_end, 8.80], [x_mid, 8.80], [x_mid, y_porch_end]],
                               area_m2=round(2.95 * 4.00, 1), centroid=[8.28, 6.80], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath4", room_type="bathroom", room_name="Attached Bath 4",
                               polygon=[[x_mid, 8.80], [x_end, 8.80], [x_end, y_mid_end], [x_mid, y_mid_end], [x_mid, 8.80]],
                               area_m2=round(2.95 * 2.40, 1), centroid=[8.28, 10.00], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed5", room_type="bedroom", room_name="Upper Bedroom 5",
                               polygon=[[x0, y_mid_end], [4.875, y_mid_end], [4.875, y_bed_split], [x0, y_bed_split], [x0, y_mid_end]],
                               area_m2=round(4.875 * 3.30, 1), centroid=[2.44, 12.85], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath5", room_type="bathroom", room_name="Attached Bath 5",
                               polygon=[[x0, y_bed_split], [4.875, y_bed_split], [4.875, y_rear], [x0, y_rear], [x0, y_bed_split]],
                               area_m2=round(4.875 * 1.50, 1), centroid=[2.44, 15.25], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed6", room_type="bedroom", room_name="Upper Bedroom 6",
                               polygon=[[4.875, y_mid_end], [x_end, y_mid_end], [x_end, y_bed_split], [4.875, y_bed_split], [4.875, y_mid_end]],
                               area_m2=round(4.875 * 3.30, 1), centroid=[7.31, 12.85], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath6", room_type="bathroom", room_name="Attached Bath 6",
                               polygon=[[4.875, y_bed_split], [x_end, y_bed_split], [x_end, y_rear], [4.875, y_rear], [4.875, y_bed_split]],
                               area_m2=round(4.875 * 1.50, 1), centroid=[7.31, 15.25], level_index=1, is_habitable=False))

        # DOORS LEVEL 0
        doors_l0 = [
            ("door_L0_01", [3.38, 4.80], 1.20, ["room_L0_porch", "room_L0_corridor"]),
            ("door_L0_02", [4.25, 2.40], 1.00, ["room_L0_porch", "room_L0_drawing"]),
            ("door_L0_03", [2.50, 6.40], 1.10, ["room_L0_corridor", "room_L0_stairs"]),
            ("door_L0_04", [2.50, 8.80], 0.80, ["room_L0_corridor", "room_L0_powder"]),
            ("door_L0_05", [4.25, 8.00], 1.40, ["room_L0_corridor", "room_L0_tv_lounge"]),
            ("door_L0_06", [5.52, 4.80], 1.20, ["room_L0_drawing", "room_L0_tv_lounge"]),
            ("door_L0_07", [6.80, 6.40], 1.20, ["room_L0_tv_lounge", "room_L0_dining"]),
            ("door_L0_08", [8.28, 8.00], 0.90, ["room_L0_dining", "room_L0_kitchen"]),
            ("door_L0_09", [2.44, 11.20], 0.95, ["room_L0_corridor", "room_L0_bed1"]),
            ("door_L0_10", [6.00, 11.20], 0.95, ["room_L0_tv_lounge", "room_L0_bed2"]),
            ("door_L0_11", [2.44, 14.50], 0.80, ["room_L0_bed1", "room_L0_bath1"]),
            ("door_L0_12", [7.31, 14.50], 0.80, ["room_L0_bed2", "room_L0_bath2"]),
        ]
        for did, pos, w, conns in doors_l0:
            openings.append(OpeningModel(opening_id=did, opening_type="door", position=pos, width_m=w, connects_rooms=conns, level_index=0))

        # DOORS LEVEL 1
        doors_l1 = [
            ("door_L1_01", [2.50, 6.40], 1.20, ["room_L1_stairs", "room_L1_corridor"]),
            ("door_L1_02", [2.50, 4.80], 1.00, ["room_L1_corridor", "room_L1_terrace"]),
            ("door_L1_03", [4.25, 4.80], 0.95, ["room_L1_corridor", "room_L1_bed3"]),
            ("door_L1_04", [7.00, 1.50], 0.80, ["room_L1_bed3", "room_L1_bath3"]),
            ("door_L1_05", [2.50, 8.80], 0.80, ["room_L1_corridor", "room_L1_bath_util"]),
            ("door_L1_06", [4.25, 8.00], 1.40, ["room_L1_corridor", "room_L1_tv_lounge"]),
            ("door_L1_07", [6.80, 6.80], 0.95, ["room_L1_tv_lounge", "room_L1_bed4"]),
            ("door_L1_08", [8.28, 8.80], 0.80, ["room_L1_bed4", "room_L1_bath4"]),
            ("door_L1_09", [2.44, 11.20], 0.95, ["room_L1_corridor", "room_L1_bed5"]),
            ("door_L1_10", [6.00, 11.20], 0.95, ["room_L1_tv_lounge", "room_L1_bed6"]),
            ("door_L1_11", [2.44, 14.50], 0.80, ["room_L1_bed5", "room_L1_bath5"]),
            ("door_L1_12", [7.31, 14.50], 0.80, ["room_L1_bed6", "room_L1_bath6"]),
        ]
        for did, pos, w, conns in doors_l1:
            openings.append(OpeningModel(opening_id=did, opening_type="door", position=pos, width_m=w, connects_rooms=conns, level_index=1))

        # Windows
        wins = [
            ("win_L0_draw", [7.00, y_front], 2.40, 0),
            ("win_L0_kit", [x_end, 9.60], 1.40, 0),
            ("win_L0_b1", [2.44, y_rear], 1.50, 0),
            ("win_L0_b2", [7.31, y_rear], 1.50, 0),
            ("win_L1_b3", [x_end, 3.15], 1.80, 1),
            ("win_L1_b4", [x_end, 6.80], 1.50, 1),
            ("win_L1_b5", [2.44, y_rear], 1.50, 1),
            ("win_L1_b6", [7.31, y_rear], 1.50, 1),
        ]
        for wid, pos, w, lvl in wins:
            openings.append(OpeningModel(opening_id=wid, opening_type="window", position=pos, width_m=w, sill_height_m=0.90, level_index=lvl))

        walls = _build_walls_for_levels(rooms, x0, x_end, y_front, y_rear)

        # Graph
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.40, min_shared_boundary_m=0.50)
        edges, _ = extractor.build_graph(rooms, openings)
        edges.append(GraphEdgeModel(
            source_room_id="room_L0_stairs",
            target_room_id="room_L1_stairs",
            relationship_type="via_door",
            weight=1.0,
            metadata={"vertical_circulation": "dogleg_stairs", "aligned": True}
        ))

        total_area = sum(r.area_m2 for r in rooms)
        boundary = [[x0, y_front], [x_end, y_front], [x_end, y_rear], [x0, y_rear], [x0, y_front]]

        return CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="synthetic_generated",
                floor_count=2,
                levels=[0, 1],
                unit="m",
                wall_height_m=3.00,
                provenance={
                    "project_title": "Typology A: Linear Spine Asymmetrical Villa",
                    "plot_size": "10 Marla (35' x 65')",
                    "typology": "linear_spine_villa"
                }
            ),
            boundary=boundary,
            total_area_m2=round(total_area, 1),
            walls=walls,
            openings=openings,
            rooms=rooms,
            graph_edges=edges
        )


class TypologyBRotundaGrandHallEngine:
    """
    Typology B: "Centric Rotunda / Grand Stair Hall" (Executive Luxury Villa 10 Marla / 35'x65')
    Circulation: Grand central curved/semi-circular staircase [3.25, 6.50] x [4.80, 8.40] acting as architectural focal point.
    Spatial Flow: Splayed Entry Lobby -> Central Grand Stair Hall -> Flanking Drawing (West) & Dining (East) -> Rear Master Wing with private patio court.
    Level 1: Circular cut-out / mezzanine void looking down into stair hall; wrap-around gallery leading to 3 perimeter suites.
    """
    @classmethod
    def generate_rotunda_grand_hall(cls, plan_id: str = "typology_b_centric_rotunda") -> CanonicalFloorPlan:
        x0, x_left_bay, x_center_split, x_right_bay, x_end = 0.0, 3.25, 6.50, 7.00, 9.75
        y_front, y_porch_end, y_stair_end, y_pwd_end, y_lounge_end, y_bed_split, y_rear = 0.0, 4.80, 8.40, 10.00, 11.80, 14.50, 16.00

        rooms: List[RoomModel] = []
        openings: List[OpeningModel] = []

        # ================= LEVEL 0 (GROUND FLOOR) =================
        rooms.append(RoomModel(room_id="room_L0_porch", room_type="garage", room_name="Car Porch (2 SUVs)",
                               polygon=[[x0, y_front], [x_left_bay, y_front], [x_left_bay, y_porch_end], [x0, y_porch_end], [x0, y_front]],
                               area_m2=round(3.25 * 4.80, 1), centroid=[1.62, 2.40], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_kitchen", room_type="kitchen", room_name="Chef Kitchen (Front East)",
                               polygon=[[x_center_split, y_front], [x_end, y_front], [x_end, y_porch_end], [x_center_split, y_porch_end], [x_center_split, y_front]],
                               area_m2=round(3.25 * 4.80, 1), centroid=[8.12, 2.40], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_lobby", room_type="corridor", room_name="Grand Rotunda Entry Lobby",
                               polygon=[[x_left_bay, y_front], [x_center_split, y_front], [x_center_split, y_porch_end], [x_left_bay, y_porch_end], [x_left_bay, y_front]],
                               area_m2=round(3.25 * 4.80, 1), centroid=[4.88, 2.40], level_index=0, is_habitable=False))
        # Exact staircase core
        rooms.append(RoomModel(room_id="room_L0_stairs", room_type="corridor", room_name="Grand Stair Hall (Rotunda UP ->)",
                               polygon=[[x_left_bay, y_porch_end], [x_center_split, y_porch_end], [x_center_split, y_stair_end], [x_left_bay, y_stair_end], [x_left_bay, y_porch_end]],
                               area_m2=round(3.25 * 3.60, 1), centroid=[4.88, 6.60], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_drawing", room_type="living_room", room_name="Drawing Room (Flanking West)",
                               polygon=[[x0, y_porch_end], [x_left_bay, y_porch_end], [x_left_bay, y_stair_end], [x0, y_stair_end], [x0, y_porch_end]],
                               area_m2=round(3.25 * 3.60, 1), centroid=[1.62, 6.60], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_dining", room_type="dining_room", room_name="Dining Room (Flanking East)",
                               polygon=[[x_center_split, y_porch_end], [x_end, y_porch_end], [x_end, y_stair_end], [x_center_split, y_stair_end], [x_center_split, y_porch_end]],
                               area_m2=round(3.25 * 3.60, 1), centroid=[8.12, 6.60], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_powder", room_type="bathroom", room_name="Powder Room",
                               polygon=[[x0, y_stair_end], [x_left_bay, y_stair_end], [x_left_bay, y_pwd_end], [x0, y_pwd_end], [x0, y_stair_end]],
                               area_m2=round(3.25 * 1.60, 1), centroid=[1.62, 9.20], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_tv_lounge", room_type="living_room", room_name="Central Family TV Lounge",
                               polygon=[[x_left_bay, y_stair_end], [x_right_bay, y_stair_end], [x_right_bay, y_lounge_end], [x_left_bay, y_lounge_end], [x_left_bay, y_stair_end]],
                               area_m2=round(3.75 * 3.40, 1), centroid=[5.12, 10.10], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_patio", room_type="outdoor", room_name="Private Green Patio Court",
                               polygon=[[x_right_bay, y_stair_end], [x_end, y_stair_end], [x_end, y_lounge_end], [x_right_bay, y_lounge_end], [x_right_bay, y_stair_end]],
                               area_m2=round(2.75 * 3.40, 1), centroid=[8.38, 10.10], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_corridor", room_type="corridor", room_name="Master Suite Vestibule",
                               polygon=[[x0, y_pwd_end], [x_left_bay, y_pwd_end], [x_left_bay, y_lounge_end], [x0, y_lounge_end], [x0, y_pwd_end]],
                               area_m2=round(3.25 * 1.80, 1), centroid=[1.62, 10.90], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_bed1", room_type="bedroom", room_name="Ground Master Bedroom 1",
                               polygon=[[x0, y_lounge_end], [5.00, y_lounge_end], [5.00, y_bed_split], [x0, y_bed_split], [x0, y_lounge_end]],
                               area_m2=round(5.00 * 2.70, 1), centroid=[2.50, 13.15], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_bath1", room_type="bathroom", room_name="Attached Bath 1 (Master)",
                               polygon=[[x0, y_bed_split], [5.00, y_bed_split], [5.00, y_rear], [x0, y_rear], [x0, y_bed_split]],
                               area_m2=round(5.00 * 1.50, 1), centroid=[2.50, 15.25], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_bed2", room_type="bedroom", room_name="Ground Bedroom 2",
                               polygon=[[5.00, y_lounge_end], [x_end, y_lounge_end], [x_end, y_bed_split], [5.00, y_bed_split], [5.00, y_lounge_end]],
                               area_m2=round(4.75 * 2.70, 1), centroid=[7.38, 13.15], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_bath2", room_type="bathroom", room_name="Attached Bath 2",
                               polygon=[[5.00, y_bed_split], [x_end, y_bed_split], [x_end, y_rear], [5.00, y_rear], [5.00, y_bed_split]],
                               area_m2=round(4.75 * 1.50, 1), centroid=[7.38, 15.25], level_index=0, is_habitable=False))

        # ================= LEVEL 1 (FIRST FLOOR) =================
        # Terrace over Porch
        rooms.append(RoomModel(room_id="room_L1_terrace", room_type="balcony", room_name="Front Open Terrace",
                               polygon=[[x0, y_front], [x_left_bay, y_front], [x_left_bay, y_porch_end], [x0, y_porch_end], [x0, y_front]],
                               area_m2=round(3.25 * 4.80, 1), centroid=[1.62, 2.40], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed3", room_type="bedroom", room_name="Upper Front Suite 3",
                               polygon=[[x_center_split, 1.50], [x_end, 1.50], [x_end, y_porch_end], [x_center_split, y_porch_end], [x_center_split, 1.50]],
                               area_m2=round(3.25 * 3.30, 1), centroid=[8.12, 3.15], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath3", room_type="bathroom", room_name="Attached Bath 3",
                               polygon=[[x_center_split, y_front], [x_end, y_front], [x_end, 1.50], [x_center_split, 1.50], [x_center_split, y_front]],
                               area_m2=round(3.25 * 1.50, 1), centroid=[8.12, 0.75], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_lobby", room_type="corridor", room_name="Upper Mezzanine Lobby",
                               polygon=[[x_left_bay, y_front], [x_center_split, y_front], [x_center_split, y_porch_end], [x_left_bay, y_porch_end], [x_left_bay, y_front]],
                               area_m2=round(3.25 * 4.80, 1), centroid=[4.88, 2.40], level_index=1, is_habitable=False))
        # Pinned staircase landing
        rooms.append(RoomModel(room_id="room_L1_stairs", room_type="corridor", room_name="Rotunda Stair Landing & Void (DN <-)",
                               polygon=[[x_left_bay, y_porch_end], [x_center_split, y_porch_end], [x_center_split, y_stair_end], [x_left_bay, y_stair_end], [x_left_bay, y_porch_end]],
                               area_m2=round(3.25 * 3.60, 1), centroid=[4.88, 6.60], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed4", room_type="bedroom", room_name="Upper Bedroom 4 (West)",
                               polygon=[[x0, y_porch_end], [x_left_bay, y_porch_end], [x_left_bay, y_stair_end], [x0, y_stair_end], [x0, y_porch_end]],
                               area_m2=round(3.25 * 3.60, 1), centroid=[1.62, 6.60], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath4", room_type="bathroom", room_name="Attached Bath 4",
                               polygon=[[x0, y_stair_end], [x_left_bay, y_stair_end], [x_left_bay, y_pwd_end], [x0, y_pwd_end], [x0, y_stair_end]],
                               area_m2=round(3.25 * 1.60, 1), centroid=[1.62, 9.20], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed5", room_type="bedroom", room_name="Upper Bedroom 5 (East)",
                               polygon=[[x_center_split, y_porch_end], [x_end, y_porch_end], [x_end, y_stair_end], [x_center_split, y_stair_end], [x_center_split, y_porch_end]],
                               area_m2=round(3.25 * 3.60, 1), centroid=[8.12, 6.60], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_tv_lounge", room_type="living_room", room_name="Upper Family TV Lounge",
                               polygon=[[x_left_bay, y_stair_end], [x_right_bay, y_stair_end], [x_right_bay, y_lounge_end], [x_left_bay, y_lounge_end], [x_left_bay, y_stair_end]],
                               area_m2=round(3.75 * 3.40, 1), centroid=[5.12, 10.10], level_index=1, is_habitable=True))
        # Continuous vertical patio light-well
        rooms.append(RoomModel(room_id="room_L1_patio_void", room_type="outdoor", room_name="Patio Light-well Void",
                               polygon=[[x_right_bay, y_stair_end], [x_end, y_stair_end], [x_end, y_lounge_end], [x_right_bay, y_lounge_end], [x_right_bay, y_stair_end]],
                               area_m2=round(2.75 * 3.40, 1), centroid=[8.38, 10.10], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_corridor", room_type="corridor", room_name="Upper Rear Vestibule",
                               polygon=[[x0, y_pwd_end], [x_left_bay, y_pwd_end], [x_left_bay, y_lounge_end], [x0, y_lounge_end], [x0, y_pwd_end]],
                               area_m2=round(3.25 * 1.80, 1), centroid=[1.62, 10.90], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed6", room_type="bedroom", room_name="Upper Bedroom 6",
                               polygon=[[x0, y_lounge_end], [5.00, y_lounge_end], [5.00, y_bed_split], [x0, y_bed_split], [x0, y_lounge_end]],
                               area_m2=round(5.00 * 2.70, 1), centroid=[2.50, 13.15], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath6", room_type="bathroom", room_name="Attached Bath 6",
                               polygon=[[x0, y_bed_split], [5.00, y_bed_split], [5.00, y_rear], [x0, y_rear], [x0, y_bed_split]],
                               area_m2=round(5.00 * 1.50, 1), centroid=[2.50, 15.25], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed7", room_type="bedroom", room_name="Upper Bedroom 7",
                               polygon=[[5.00, y_lounge_end], [x_end, y_lounge_end], [x_end, y_bed_split], [5.00, y_bed_split], [5.00, y_lounge_end]],
                               area_m2=round(4.75 * 2.70, 1), centroid=[7.38, 13.15], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath7", room_type="bathroom", room_name="Attached Bath 7",
                               polygon=[[5.00, y_bed_split], [x_end, y_bed_split], [x_end, y_rear], [5.00, y_rear], [5.00, y_bed_split]],
                               area_m2=round(4.75 * 1.50, 1), centroid=[7.38, 15.25], level_index=1, is_habitable=False))

        # DOORS LEVEL 0
        doors_l0 = [
            ("door_L0_01", [3.25, 2.40], 1.20, ["room_L0_porch", "room_L0_lobby"]),
            ("door_L0_02", [4.88, 4.80], 1.40, ["room_L0_lobby", "room_L0_stairs"]),
            ("door_L0_03", [3.25, 6.60], 1.10, ["room_L0_stairs", "room_L0_drawing"]),
            ("door_L0_04", [6.50, 6.60], 1.10, ["room_L0_stairs", "room_L0_dining"]),
            ("door_L0_05", [6.50, 2.40], 1.00, ["room_L0_lobby", "room_L0_kitchen"]),
            ("door_L0_06", [8.12, 4.80], 1.00, ["room_L0_kitchen", "room_L0_dining"]),
            ("door_L0_07", [4.88, 8.40], 1.40, ["room_L0_stairs", "room_L0_tv_lounge"]),
            ("door_L0_08", [3.25, 9.20], 0.80, ["room_L0_tv_lounge", "room_L0_powder"]),
            ("door_L0_09", [3.25, 10.90], 1.00, ["room_L0_tv_lounge", "room_L0_corridor"]),
            ("door_L0_10", [2.50, 11.80], 0.95, ["room_L0_corridor", "room_L0_bed1"]),
            ("door_L0_11", [6.00, 11.80], 0.95, ["room_L0_tv_lounge", "room_L0_bed2"]),
            ("door_L0_12", [2.50, 14.50], 0.80, ["room_L0_bed1", "room_L0_bath1"]),
            ("door_L0_13", [7.38, 14.50], 0.80, ["room_L0_bed2", "room_L0_bath2"]),
            ("door_L0_14", [7.00, 10.10], 1.00, ["room_L0_tv_lounge", "room_L0_patio"]),
        ]
        for did, pos, w, conns in doors_l0:
            openings.append(OpeningModel(opening_id=did, opening_type="door", position=pos, width_m=w, connects_rooms=conns, level_index=0))

        # DOORS LEVEL 1
        doors_l1 = [
            ("door_L1_01", [4.88, 4.80], 1.40, ["room_L1_lobby", "room_L1_stairs"]),
            ("door_L1_02", [3.25, 2.40], 1.00, ["room_L1_lobby", "room_L1_terrace"]),
            ("door_L1_03", [6.50, 3.15], 0.95, ["room_L1_lobby", "room_L1_bed3"]),
            ("door_L1_04", [8.12, 1.50], 0.80, ["room_L1_bed3", "room_L1_bath3"]),
            ("door_L1_05", [3.25, 6.60], 1.00, ["room_L1_stairs", "room_L1_bed4"]),
            ("door_L1_06", [1.62, 8.40], 0.80, ["room_L1_bed4", "room_L1_bath4"]),
            ("door_L1_07", [6.50, 6.60], 1.00, ["room_L1_stairs", "room_L1_bed5"]),
            ("door_L1_08", [4.88, 8.40], 1.40, ["room_L1_stairs", "room_L1_tv_lounge"]),
            ("door_L1_09", [3.25, 10.90], 1.00, ["room_L1_tv_lounge", "room_L1_corridor"]),
            ("door_L1_10", [2.50, 11.80], 0.95, ["room_L1_corridor", "room_L1_bed6"]),
            ("door_L1_11", [6.00, 11.80], 0.95, ["room_L1_tv_lounge", "room_L1_bed7"]),
            ("door_L1_12", [2.50, 14.50], 0.80, ["room_L1_bed6", "room_L1_bath6"]),
            ("door_L1_13", [7.38, 14.50], 0.80, ["room_L1_bed7", "room_L1_bath7"]),
        ]
        for did, pos, w, conns in doors_l1:
            openings.append(OpeningModel(opening_id=did, opening_type="door", position=pos, width_m=w, connects_rooms=conns, level_index=1))

        # Windows
        wins = [
            ("win_L0_kit", [8.12, y_front], 1.80, 0),
            ("win_L0_draw", [x0, 6.60], 2.20, 0),
            ("win_L0_din", [x_end, 6.60], 2.20, 0),
            ("win_L0_b1", [2.50, y_rear], 1.60, 0),
            ("win_L0_b2", [7.38, y_rear], 1.60, 0),
            ("win_L1_b3", [x_end, 3.15], 1.80, 1),
            ("win_L1_b4", [x0, 6.60], 1.80, 1),
            ("win_L1_b5", [x_end, 6.60], 1.80, 1),
            ("win_L1_b6", [2.50, y_rear], 1.60, 1),
            ("win_L1_b7", [7.38, y_rear], 1.60, 1),
        ]
        for wid, pos, w, lvl in wins:
            openings.append(OpeningModel(opening_id=wid, opening_type="window", position=pos, width_m=w, sill_height_m=0.90, level_index=lvl))

        walls = _build_walls_for_levels(rooms, x0, x_end, y_front, y_rear)

        # Graph
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.40, min_shared_boundary_m=0.50)
        edges, _ = extractor.build_graph(rooms, openings)
        edges.append(GraphEdgeModel(
            source_room_id="room_L0_stairs",
            target_room_id="room_L1_stairs",
            relationship_type="via_door",
            weight=1.0,
            metadata={"vertical_circulation": "grand_rotunda_stairs", "aligned": True}
        ))

        total_area = sum(r.area_m2 for r in rooms)
        boundary = [[x0, y_front], [x_end, y_front], [x_end, y_rear], [x0, y_rear], [x0, y_front]]

        return CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="synthetic_generated",
                floor_count=2,
                levels=[0, 1],
                unit="m",
                wall_height_m=3.20,
                provenance={
                    "project_title": "Typology B: Centric Rotunda Grand Stair Hall",
                    "plot_size": "10 Marla (35' x 65')",
                    "typology": "centric_rotunda_villa"
                }
            ),
            boundary=boundary,
            total_area_m2=round(total_area, 1),
            walls=walls,
            openings=openings,
            rooms=rooms,
            graph_edges=edges
        )


class TypologyCCourtyardCoreEngine:
    """
    Typology C: "Courtyard Core / Inverted L-Shaped Layout" (Biophilic Light-Well Focus)
    Circulation: Mid-plan U-stair on East flank [7.25, 9.75] x [4.80, 8.00].
    Spatial Flow: Front Drawing & Dining -> Central internal landscaped Courtyard (OTS) [3.40, 6.40] x [8.00, 11.20]
          flanked by Modern Kitchen (West) and TV Lounge (East) -> Split private rear bedrooms.
    Level 1: Bridge corridor overlooking internal courtyard; front master suite with private shaded balcony.
    """
    @classmethod
    def generate_courtyard_core(cls, plan_id: str = "typology_c_courtyard_core") -> CanonicalFloorPlan:
        x0, x_left_flank, x_cor_end, x_court_start, x_court_end, x_stair_split, x_end = 0.0, 2.50, 3.40, 3.40, 6.40, 7.25, 9.75
        y_front, y_porch_end, y_foyer_end, y_court_start, y_court_end, y_bed_split, y_rear = 0.0, 4.80, 6.40, 8.00, 11.20, 14.50, 16.00

        rooms: List[RoomModel] = []
        openings: List[OpeningModel] = []

        # ================= LEVEL 0 (GROUND FLOOR) =================
        rooms.append(RoomModel(room_id="room_L0_porch", room_type="garage", room_name="Car Porch (2 Cars)",
                               polygon=[[x0, y_front], [4.25, y_front], [4.25, y_porch_end], [x0, y_porch_end], [x0, y_front]],
                               area_m2=round(4.25 * 4.80, 1), centroid=[2.12, 2.40], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_drawing", room_type="living_room", room_name="Formal Drawing Room",
                               polygon=[[4.25, y_front], [x_end, y_front], [x_end, y_porch_end], [4.25, y_porch_end], [4.25, y_front]],
                               area_m2=round(5.50 * 4.80, 1), centroid=[7.00, 2.40], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_powder", room_type="bathroom", room_name="Guest Powder Room",
                               polygon=[[x0, y_porch_end], [x_left_flank, y_porch_end], [x_left_flank, y_foyer_end], [x0, y_foyer_end], [x0, y_porch_end]],
                               area_m2=round(2.50 * 1.60, 1), centroid=[1.25, 5.60], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_foyer", room_type="corridor", room_name="Entrance Foyer & Lobby",
                               polygon=[[x_left_flank, y_porch_end], [4.25, y_porch_end], [4.25, y_foyer_end], [x_left_flank, y_foyer_end], [x_left_flank, y_porch_end]],
                               area_m2=round(1.75 * 1.60, 1), centroid=[3.38, 5.60], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_dining", room_type="dining_room", room_name="Formal Dining Room",
                               polygon=[[4.25, y_porch_end], [x_stair_split, y_porch_end], [x_stair_split, y_court_start], [4.25, y_court_start], [4.25, y_porch_end]],
                               area_m2=round(3.00 * 3.20, 1), centroid=[5.75, 6.40], level_index=0, is_habitable=True))
        # Pinned U-stair
        rooms.append(RoomModel(room_id="room_L0_stairs", room_type="corridor", room_name="Mid-Plan U-Stair (UP ->)",
                               polygon=[[x_stair_split, y_porch_end], [x_end, y_porch_end], [x_end, y_court_start], [x_stair_split, y_court_start], [x_stair_split, y_porch_end]],
                               area_m2=round(2.50 * 3.20, 1), centroid=[8.50, 6.40], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_kitchen", room_type="kitchen", room_name="Modern Kitchen (West Flank)",
                               polygon=[[x0, y_foyer_end], [x_left_flank, y_foyer_end], [x_left_flank, y_court_end], [x0, y_court_end], [x0, y_foyer_end]],
                               area_m2=round(2.50 * 4.80, 1), centroid=[1.25, 8.80], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_corridor", room_type="corridor", room_name="Courtyard Gallery Walk",
                               polygon=[[x_left_flank, y_foyer_end], [x_cor_end, y_foyer_end], [x_cor_end, y_court_end], [x_left_flank, y_court_end], [x_left_flank, y_foyer_end]],
                               area_m2=round(0.90 * 4.80, 1), centroid=[2.95, 8.80], level_index=0, is_habitable=False))
        # Biophilic Central Courtyard OTS
        rooms.append(RoomModel(room_id="room_L0_courtyard", room_type="outdoor", room_name="Central Landscaped Courtyard (OTS)",
                               polygon=[[x_court_start, y_court_start], [x_court_end, y_court_start], [x_court_end, y_court_end], [x_court_start, y_court_end], [x_court_start, y_court_start]],
                               area_m2=round(3.00 * 3.20, 1), centroid=[4.90, 9.60], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_tv_lounge", room_type="living_room", room_name="Family TV Lounge (Courtyard View)",
                               polygon=[[x_court_end, y_court_start], [x_end, y_court_start], [x_end, y_court_end], [x_court_end, y_court_end], [x_court_end, y_court_start]],
                               area_m2=round(3.35 * 3.20, 1), centroid=[8.08, 9.60], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_bed1", room_type="bedroom", room_name="Ground Master Bedroom 1",
                               polygon=[[x0, y_court_end], [4.875, y_court_end], [4.875, y_bed_split], [x0, y_bed_split], [x0, y_court_end]],
                               area_m2=round(4.875 * 3.30, 1), centroid=[2.44, 12.85], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_bath1", room_type="bathroom", room_name="Attached Bath 1 (Master)",
                               polygon=[[x0, y_bed_split], [4.875, y_bed_split], [4.875, y_rear], [x0, y_rear], [x0, y_bed_split]],
                               area_m2=round(4.875 * 1.50, 1), centroid=[2.44, 15.25], level_index=0, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L0_bed2", room_type="bedroom", room_name="Ground Bedroom 2",
                               polygon=[[4.875, y_court_end], [x_end, y_court_end], [x_end, y_bed_split], [4.875, y_bed_split], [4.875, y_court_end]],
                               area_m2=round(4.875 * 3.30, 1), centroid=[7.31, 12.85], level_index=0, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L0_bath2", room_type="bathroom", room_name="Attached Bath 2",
                               polygon=[[4.875, y_bed_split], [x_end, y_bed_split], [x_end, y_rear], [4.875, y_rear], [4.875, y_bed_split]],
                               area_m2=round(4.875 * 1.50, 1), centroid=[7.31, 15.25], level_index=0, is_habitable=False))

        # ================= LEVEL 1 (FIRST FLOOR) =================
        # Terrace over Porch
        rooms.append(RoomModel(room_id="room_L1_terrace", room_type="balcony", room_name="Front Shaded Balcony / Terrace",
                               polygon=[[x0, y_front], [4.25, y_front], [4.25, y_porch_end], [x0, y_porch_end], [x0, y_front]],
                               area_m2=round(4.25 * 4.80, 1), centroid=[2.12, 2.40], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed3", room_type="bedroom", room_name="Front Master Suite 3",
                               polygon=[[4.25, 1.50], [x_end, 1.50], [x_end, y_porch_end], [4.25, y_porch_end], [4.25, 1.50]],
                               area_m2=round(5.50 * 3.30, 1), centroid=[7.00, 3.15], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath3", room_type="bathroom", room_name="Attached Bath 3",
                               polygon=[[4.25, y_front], [x_end, y_front], [x_end, 1.50], [4.25, 1.50], [4.25, y_front]],
                               area_m2=round(5.50 * 1.50, 1), centroid=[7.00, 0.75], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bath4", room_type="bathroom", room_name="Attached Bath 4",
                               polygon=[[x0, y_porch_end], [x_left_flank, y_porch_end], [x_left_flank, y_foyer_end], [x0, y_foyer_end], [x0, y_porch_end]],
                               area_m2=round(2.50 * 1.60, 1), centroid=[1.25, 5.60], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_foyer", room_type="corridor", room_name="Upper Entry Vestibule",
                               polygon=[[x_left_flank, y_porch_end], [4.25, y_porch_end], [4.25, y_foyer_end], [x_left_flank, y_foyer_end], [x_left_flank, y_porch_end]],
                               area_m2=round(1.75 * 1.60, 1), centroid=[3.38, 5.60], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed4", room_type="bedroom", room_name="Upper Bedroom 4",
                               polygon=[[4.25, y_porch_end], [x_stair_split, y_porch_end], [x_stair_split, y_court_start], [4.25, y_court_start], [4.25, y_porch_end]],
                               area_m2=round(3.00 * 3.20, 1), centroid=[5.75, 6.40], level_index=1, is_habitable=True))
        # Exact staircase pinning
        rooms.append(RoomModel(room_id="room_L1_stairs", room_type="corridor", room_name="U-Stair Landing (DN <-)",
                               polygon=[[x_stair_split, y_porch_end], [x_end, y_porch_end], [x_end, y_court_start], [x_stair_split, y_court_start], [x_stair_split, y_porch_end]],
                               area_m2=round(2.50 * 3.20, 1), centroid=[8.50, 6.40], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed5", room_type="bedroom", room_name="Upper Bedroom 5 (West)",
                               polygon=[[x0, y_foyer_end], [x_left_flank, y_foyer_end], [x_left_flank, y_court_end], [x0, y_court_end], [x0, y_foyer_end]],
                               area_m2=round(2.50 * 4.80, 1), centroid=[1.25, 8.80], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bridge", room_type="corridor", room_name="Bridge Corridor (Courtyard View)",
                               polygon=[[x_left_flank, y_foyer_end], [x_cor_end, y_foyer_end], [x_cor_end, y_court_end], [x_left_flank, y_court_end], [x_left_flank, y_foyer_end]],
                               area_m2=round(0.90 * 4.80, 1), centroid=[2.95, 8.80], level_index=1, is_habitable=False))
        # Continuous courtyard shaft
        rooms.append(RoomModel(room_id="room_L1_courtyard_void", room_type="outdoor", room_name="Courtyard Light-well Void",
                               polygon=[[x_court_start, y_court_start], [x_court_end, y_court_start], [x_court_end, y_court_end], [x_court_start, y_court_end], [x_court_start, y_court_start]],
                               area_m2=round(3.00 * 3.20, 1), centroid=[4.90, 9.60], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_tv_lounge", room_type="living_room", room_name="Upper TV Lounge Gallery",
                               polygon=[[x_court_end, y_court_start], [x_end, y_court_start], [x_end, y_court_end], [x_court_end, y_court_end], [x_court_end, y_court_start]],
                               area_m2=round(3.35 * 3.20, 1), centroid=[8.08, 9.60], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bed6", room_type="bedroom", room_name="Upper Bedroom 6",
                               polygon=[[x0, y_court_end], [4.875, y_court_end], [4.875, y_bed_split], [x0, y_bed_split], [x0, y_court_end]],
                               area_m2=round(4.875 * 3.30, 1), centroid=[2.44, 12.85], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath6", room_type="bathroom", room_name="Attached Bath 6",
                               polygon=[[x0, y_bed_split], [4.875, y_bed_split], [4.875, y_rear], [x0, y_rear], [x0, y_bed_split]],
                               area_m2=round(4.875 * 1.50, 1), centroid=[2.44, 15.25], level_index=1, is_habitable=False))
        rooms.append(RoomModel(room_id="room_L1_bed7", room_type="bedroom", room_name="Upper Bedroom 7",
                               polygon=[[4.875, y_court_end], [x_end, y_court_end], [x_end, y_bed_split], [4.875, y_bed_split], [4.875, y_court_end]],
                               area_m2=round(4.875 * 3.30, 1), centroid=[7.31, 12.85], level_index=1, is_habitable=True))
        rooms.append(RoomModel(room_id="room_L1_bath7", room_type="bathroom", room_name="Attached Bath 7",
                               polygon=[[4.875, y_bed_split], [x_end, y_bed_split], [x_end, y_rear], [4.875, y_rear], [4.875, y_bed_split]],
                               area_m2=round(4.875 * 1.50, 1), centroid=[7.31, 15.25], level_index=1, is_habitable=False))

        # DOORS LEVEL 0
        doors_l0 = [
            ("door_L0_01", [3.38, 4.80], 1.20, ["room_L0_porch", "room_L0_foyer"]),
            ("door_L0_02", [4.25, 2.40], 1.00, ["room_L0_porch", "room_L0_drawing"]),
            ("door_L0_03", [2.50, 5.60], 0.80, ["room_L0_foyer", "room_L0_powder"]),
            ("door_L0_04", [4.25, 5.60], 1.20, ["room_L0_foyer", "room_L0_dining"]),
            ("door_L0_05", [7.25, 6.40], 1.10, ["room_L0_dining", "room_L0_stairs"]),
            ("door_L0_06", [2.95, 6.40], 0.90, ["room_L0_foyer", "room_L0_corridor"]),
            ("door_L0_07", [2.50, 8.80], 0.90, ["room_L0_corridor", "room_L0_kitchen"]),
            ("door_L0_08", [8.50, 8.00], 1.20, ["room_L0_stairs", "room_L0_tv_lounge"]),
            ("door_L0_09", [6.40, 9.60], 1.20, ["room_L0_tv_lounge", "room_L0_courtyard"]),
            ("door_L0_10", [2.44, 11.20], 0.95, ["room_L0_corridor", "room_L0_bed1"]),
            ("door_L0_11", [7.31, 11.20], 0.95, ["room_L0_tv_lounge", "room_L0_bed2"]),
            ("door_L0_12", [2.44, 14.50], 0.80, ["room_L0_bed1", "room_L0_bath1"]),
            ("door_L0_13", [7.31, 14.50], 0.80, ["room_L0_bed2", "room_L0_bath2"]),
        ]
        for did, pos, w, conns in doors_l0:
            openings.append(OpeningModel(opening_id=did, opening_type="door", position=pos, width_m=w, connects_rooms=conns, level_index=0))

        # DOORS LEVEL 1
        doors_l1 = [
            ("door_L1_01", [8.50, 8.00], 1.20, ["room_L1_stairs", "room_L1_tv_lounge"]),
            ("door_L1_02", [7.25, 6.40], 1.10, ["room_L1_stairs", "room_L1_bed4"]),
            ("door_L1_03", [4.25, 5.60], 0.95, ["room_L1_foyer", "room_L1_bed4"]),
            ("door_L1_04", [2.50, 4.80], 1.00, ["room_L1_foyer", "room_L1_terrace"]),
            ("door_L1_05", [4.25, 4.80], 0.95, ["room_L1_foyer", "room_L1_bed3"]),
            ("door_L1_06", [7.00, 1.50], 0.80, ["room_L1_bed3", "room_L1_bath3"]),
            ("door_L1_07", [2.50, 5.60], 0.80, ["room_L1_foyer", "room_L1_bath4"]),
            ("door_L1_08", [2.95, 6.40], 0.90, ["room_L1_foyer", "room_L1_bridge"]),
            ("door_L1_09", [2.50, 8.80], 0.90, ["room_L1_bridge", "room_L1_bed5"]),
            ("door_L1_10", [2.44, 11.20], 0.95, ["room_L1_bridge", "room_L1_bed6"]),
            ("door_L1_11", [2.44, 14.50], 0.80, ["room_L1_bed6", "room_L1_bath6"]),
            ("door_L1_12", [7.31, 11.20], 0.95, ["room_L1_tv_lounge", "room_L1_bed7"]),
            ("door_L1_13", [7.31, 14.50], 0.80, ["room_L1_bed7", "room_L1_bath7"]),
        ]
        for did, pos, w, conns in doors_l1:
            openings.append(OpeningModel(opening_id=did, opening_type="door", position=pos, width_m=w, connects_rooms=conns, level_index=1))

        # Windows
        wins = [
            ("win_L0_draw", [7.00, y_front], 2.20, 0),
            ("win_L0_kit", [x0, 8.80], 1.80, 0),
            ("win_L0_lou", [x_end, 9.60], 1.80, 0),
            ("win_L0_b1", [2.44, y_rear], 1.60, 0),
            ("win_L0_b2", [7.31, y_rear], 1.60, 0),
            ("win_L1_b3", [x_end, 3.15], 1.80, 1),
            ("win_L1_b5", [x0, 8.80], 1.50, 1),
            ("win_L1_lou", [x_end, 9.60], 1.80, 1),
            ("win_L1_b6", [2.44, y_rear], 1.60, 1),
            ("win_L1_b7", [7.31, y_rear], 1.60, 1),
        ]
        for wid, pos, w, lvl in wins:
            openings.append(OpeningModel(opening_id=wid, opening_type="window", position=pos, width_m=w, sill_height_m=0.90, level_index=lvl))

        walls = _build_walls_for_levels(rooms, x0, x_end, y_front, y_rear)

        # Graph
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.40, min_shared_boundary_m=0.50)
        edges, _ = extractor.build_graph(rooms, openings)
        edges.append(GraphEdgeModel(
            source_room_id="room_L0_stairs",
            target_room_id="room_L1_stairs",
            relationship_type="via_door",
            weight=1.0,
            metadata={"vertical_circulation": "mid_plan_u_stair", "aligned": True}
        ))

        total_area = sum(r.area_m2 for r in rooms)
        boundary = [[x0, y_front], [x_end, y_front], [x_end, y_rear], [x0, y_rear], [x0, y_front]]

        return CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="synthetic_generated",
                floor_count=2,
                levels=[0, 1],
                unit="m",
                wall_height_m=3.00,
                provenance={
                    "project_title": "Typology C: Courtyard Core Biophilic Villa",
                    "plot_size": "10 Marla (35' x 65')",
                    "typology": "courtyard_core_villa"
                }
            ),
            boundary=boundary,
            total_area_m2=round(total_area, 1),
            walls=walls,
            openings=openings,
            rooms=rooms,
            graph_edges=edges
        )


class ExecutiveTwoFloorArchitecturalEngine:
    """
    Executive 10 Marla (32' x 58' / 9.75m x 17.60m) Coordinated Two-Floor Architectural Engine.
    Uses the proven refactored Ground Floor as the Level 0 Master Anchor,
    and projects its natural structural counterpart onto Level 1 (First Floor):
    - Level 0 (Ground):
      * Front: Double Car Porch (left) + Formal Drawing Room (right).
      * Entrance: Main Portico + Grand Foyer + Guest Powder Room.
      * Circulation: Flush dogleg staircase along left envelope with UP flight off Foyer.
      * Core: Spacious central Family TV Lounge + Modern Kitchen & Dining Suite + Dirty Kitchen & OTS 1.
      * Rear: Ground Master Suite + Bedroom 2, each with attached walk-in dressing and private baths venting to OTS 2.
    - Level 1 (First Floor):
      * Front Over Porch: Front Open Terrace / Balcony with perimeter safety parapet rail.
      * Front Over Drawing: Upper Front Suite (Bedroom 5 / Guest Suite) with en-suite bath and terrace access.
      * Circulation: Identical staircase landing with DN flight and protective balustrade railing.
      * Central Core: Upper TV Lounge / Open Family Gallery, plus Pantry Kitchenette & Coffee Bar, Laundry, and Linen Store.
      * Rear Private Zone: Upper Bedroom 3 and Upper Bedroom 4 directly stacked above Ground suites with en-suite baths.
      * Shafts: Continuous OTS Shaft 1 and OTS Shaft 2 projecting directly upward to roof.
    """

    @classmethod
    def generate_executive_two_floor_plan(cls, plan_id: str = "cad_floorplan_executive_two_floors", stair_type: str = "u_shaped") -> CanonicalFloorPlan:
        x_max = 9.75
        y_max = 17.60

        rooms: List[RoomModel] = []
        openings: List[OpeningModel] = []

        # =========================================================================
        # LEVEL 0 (GROUND FLOOR) - REFACTORED MASTER ANCHOR
        # =========================================================================
        # 1. Car Porch (Left Bay: 17'-0" x 16'-0")
        rooms.append(RoomModel(
            room_id="room_L0_porch", room_type="garage", room_name="Car Porch (2 Cars)",
            polygon=[[0.0, 0.0], [4.50, 0.0], [4.50, 4.80], [0.0, 4.80], [0.0, 0.0]],
            area_m2=21.6, centroid=[2.25, 2.40], level_index=0, is_habitable=False
        ))
        # 2. Formal Drawing Room (Right Bay: 15'-0" x 14'-0")
        rooms.append(RoomModel(
            room_id="room_L0_drawing", room_type="living_room", room_name="Formal Drawing Room",
            polygon=[[4.50, 0.0], [9.75, 0.0], [9.75, 4.40], [4.50, 4.40], [4.50, 0.0]],
            area_m2=23.1, centroid=[7.12, 2.20], level_index=0, is_habitable=True
        ))
        # 3. Dogleg / Modular Staircase (Left Flush Outer Wall: 8'-0" x 12'-6")
        stair_label = f"{stair_type.replace('_', ' ').title()} Staircase (UP ->)"
        rooms.append(RoomModel(
            room_id="room_L0_stairs", room_type="corridor", room_name=stair_label,
            polygon=[[0.0, 4.80], [2.50, 4.80], [2.50, 8.60], [0.0, 8.60], [0.0, 4.80]],
            area_m2=9.5, centroid=[1.25, 6.70], level_index=0, is_habitable=False,
            metadata={"typology": stair_type}
        ))
        # 4. Grand Foyer & Portico (8'-0" x 8'-6")
        rooms.append(RoomModel(
            room_id="room_L0_foyer", room_type="corridor", room_name="Grand Foyer",
            polygon=[[2.50, 4.80], [4.80, 4.80], [4.80, 7.50], [2.50, 7.50], [2.50, 4.80]],
            area_m2=6.2, centroid=[3.65, 6.15], level_index=0, is_habitable=False
        ))
        # 5. Guest Powder Room (5'-0" x 6'-6")
        rooms.append(RoomModel(
            room_id="room_L0_powder", room_type="bathroom", room_name="Guest Powder Room",
            polygon=[[4.80, 4.40], [6.30, 4.40], [6.30, 6.80], [4.80, 6.80], [4.80, 4.40]],
            area_m2=3.6, centroid=[5.55, 5.60], level_index=0, is_habitable=False
        ))
        # 6. Formal Dining Room (14'-0" x 11'-0")
        rooms.append(RoomModel(
            room_id="room_L0_dining", room_type="dining_room", room_name="Formal Dining Room",
            polygon=[[6.30, 4.40], [9.75, 4.40], [9.75, 7.80], [6.30, 7.80], [6.30, 4.40]],
            area_m2=11.7, centroid=[8.02, 6.10], level_index=0, is_habitable=True
        ))
        # 7. Central Family TV Lounge (18'-0" x 15'-6")
        rooms.append(RoomModel(
            room_id="room_L0_tv_lounge", room_type="living_room", room_name="Central Family TV Lounge",
            polygon=[[2.50, 7.50], [6.30, 7.50], [6.30, 12.20], [2.50, 12.20], [2.50, 7.50]],
            area_m2=17.9, centroid=[4.40, 9.85], level_index=0, is_habitable=True
        ))
        # 8. West Gallery Alcove (8'-0" x 11'-10")
        rooms.append(RoomModel(
            room_id="room_L0_west_gallery", room_type="corridor", room_name="West Gallery Alcove",
            polygon=[[0.0, 8.60], [2.50, 8.60], [2.50, 12.20], [0.0, 12.20], [0.0, 8.60]],
            area_m2=9.0, centroid=[1.25, 10.40], level_index=0, is_habitable=False
        ))
        # 9. Modern Show Kitchen (13'-0" x 10'-0")
        rooms.append(RoomModel(
            room_id="room_L0_kitchen", room_type="kitchen", room_name="Modern Show Kitchen",
            polygon=[[6.30, 7.80], [9.75, 7.80], [9.75, 10.70], [6.30, 10.70], [6.30, 7.80]],
            area_m2=10.0, centroid=[8.02, 9.25], level_index=0, is_habitable=True
        ))
        # 10. Dirty Kitchen / Utility (6'-0" x 5'-0")
        rooms.append(RoomModel(
            room_id="room_L0_dirty_kitchen", room_type="kitchen", room_name="Dirty Kitchen / Utility",
            polygon=[[6.30, 10.70], [8.10, 10.70], [8.10, 12.20], [6.30, 12.20], [6.30, 10.70]],
            area_m2=2.7, centroid=[7.20, 11.45], level_index=0, is_habitable=False
        ))
        # 11. OTS Shaft 1 (Central: 5'-0" x 5'-0")
        rooms.append(RoomModel(
            room_id="room_L0_ots1", room_type="outdoor", room_name="OTS Shaft 1 (Central)",
            polygon=[[8.10, 10.70], [9.75, 10.70], [9.75, 12.20], [8.10, 12.20], [8.10, 10.70]],
            area_m2=2.5, centroid=[8.92, 11.45], level_index=0, is_habitable=False
        ))
        # 12. Ground Master Suite (15'-3" x 10'-6")
        rooms.append(RoomModel(
            room_id="room_L0_bed1", room_type="bedroom", room_name="Ground Master Suite",
            polygon=[[0.0, 12.20], [4.875, 12.20], [4.875, 15.40], [0.0, 15.40], [0.0, 12.20]],
            area_m2=15.6, centroid=[2.44, 13.80], level_index=0, is_habitable=True
        ))
        # 13. Master Walk-In Dressing (7'-0" x 6'-6")
        rooms.append(RoomModel(
            room_id="room_L0_dress1", room_type="closet", room_name="Master Walk-In Dressing",
            polygon=[[0.0, 15.40], [2.40, 15.40], [2.40, 17.60], [0.0, 17.60], [0.0, 15.40]],
            area_m2=5.3, centroid=[1.20, 16.50], level_index=0, is_habitable=False
        ))
        # 14. Master En-Suite Bath (8'-0" x 6'-6")
        rooms.append(RoomModel(
            room_id="room_L0_bath1", room_type="bathroom", room_name="Master En-Suite Bath",
            polygon=[[2.40, 15.40], [4.875, 15.40], [4.875, 17.60], [2.40, 17.60], [2.40, 15.40]],
            area_m2=5.4, centroid=[3.64, 16.50], level_index=0, is_habitable=False
        ))
        # 15. Ground Bedroom 2 (15'-3" x 10'-6")
        rooms.append(RoomModel(
            room_id="room_L0_bed2", room_type="bedroom", room_name="Ground Bedroom 2",
            polygon=[[4.875, 12.20], [9.75, 12.20], [9.75, 15.40], [4.875, 15.40], [4.875, 12.20]],
            area_m2=15.6, centroid=[7.31, 13.80], level_index=0, is_habitable=True
        ))
        # 16. Bed 2 En-Suite Bath & Dress (9'-6" x 6'-6")
        rooms.append(RoomModel(
            room_id="room_L0_bath2", room_type="bathroom", room_name="Bed 2 En-Suite Bath",
            polygon=[[4.875, 15.40], [7.80, 15.40], [7.80, 17.60], [4.875, 17.60], [4.875, 15.40]],
            area_m2=6.4, centroid=[6.34, 16.50], level_index=0, is_habitable=False
        ))
        # 17. OTS Shaft 2 (Rear: 5'-6" x 6'-6")
        rooms.append(RoomModel(
            room_id="room_L0_ots2", room_type="outdoor", room_name="OTS Shaft 2 (Rear)",
            polygon=[[7.80, 15.40], [9.75, 15.40], [9.75, 17.60], [7.80, 17.60], [7.80, 15.40]],
            area_m2=4.3, centroid=[8.78, 16.50], level_index=0, is_habitable=False
        ))

        # =========================================================================
        # LEVEL 1 (FIRST FLOOR) - NATURAL STRUCTURAL STACKING
        # =========================================================================
        # 1. Front Open Terrace / Balcony (Stacked directly over Car Porch)
        rooms.append(RoomModel(
            room_id="room_L1_terrace", room_type="balcony", room_name="Front Open Terrace / Balcony",
            polygon=[[0.0, 0.0], [4.50, 0.0], [4.50, 4.80], [0.0, 4.80], [0.0, 0.0]],
            area_m2=21.6, centroid=[2.25, 2.40], level_index=1, is_habitable=False
        ))
        # 2. Upper Front Suite (Bedroom 5 / Guest Suite) (Stacked directly over Drawing Room)
        rooms.append(RoomModel(
            room_id="room_L1_bed5", room_type="bedroom", room_name="Upper Front Suite (Bedroom 5)",
            polygon=[[4.50, 0.0], [9.75, 0.0], [9.75, 4.40], [4.50, 4.40], [4.50, 0.0]],
            area_m2=23.1, centroid=[7.12, 2.20], level_index=1, is_habitable=True
        ))
        # 3. Bed 5 En-Suite Bath (Stacked over Powder Room & Portico)
        rooms.append(RoomModel(
            room_id="room_L1_bath5", room_type="bathroom", room_name="Bed 5 En-Suite Bath",
            polygon=[[4.50, 4.40], [6.30, 4.40], [6.30, 6.80], [4.50, 6.80], [4.50, 4.40]],
            area_m2=4.3, centroid=[5.40, 5.60], level_index=1, is_habitable=False
        ))
        # 4. Pantry Kitchenette & Coffee Bar (Stacked over Dining)
        rooms.append(RoomModel(
            room_id="room_L1_kitchenette", room_type="kitchen", room_name="Pantry Kitchenette & Bar",
            polygon=[[6.30, 4.40], [9.75, 4.40], [9.75, 7.80], [6.30, 7.80], [6.30, 4.40]],
            area_m2=11.7, centroid=[8.02, 6.10], level_index=1, is_habitable=True
        ))
        # 5. Upper Laundry & Utility Room (Stacked over Show Kitchen)
        rooms.append(RoomModel(
            room_id="room_L1_laundry", room_type="kitchen", room_name="Upper Laundry & Utility",
            polygon=[[6.30, 7.80], [9.75, 7.80], [9.75, 10.70], [6.30, 10.70], [6.30, 7.80]],
            area_m2=10.0, centroid=[8.02, 9.25], level_index=1, is_habitable=True
        ))
        # 6. Linen & Storage Store (Stacked over Dirty Kitchen)
        rooms.append(RoomModel(
            room_id="room_L1_utility", room_type="closet", room_name="Linen & Storage Store",
            polygon=[[6.30, 10.70], [8.10, 10.70], [8.10, 12.20], [6.30, 12.20], [6.30, 10.70]],
            area_m2=2.7, centroid=[7.20, 11.45], level_index=1, is_habitable=False
        ))
        # 7. OTS Shaft 1 (Continuous upward to roof)
        rooms.append(RoomModel(
            room_id="room_L1_ots1", room_type="outdoor", room_name="OTS Shaft 1 (Continuous)",
            polygon=[[8.10, 10.70], [9.75, 10.70], [9.75, 12.20], [8.10, 12.20], [8.10, 10.70]],
            area_m2=2.5, centroid=[8.92, 11.45], level_index=1, is_habitable=False
        ))
        # 8. Stair Landing (DN <-) - IDENTICAL COORDINATES TO LEVEL 0
        rooms.append(RoomModel(
            room_id="room_L1_stairs", room_type="corridor", room_name="Stair Landing (DN <-)",
            polygon=[[0.0, 4.80], [2.50, 4.80], [2.50, 8.60], [0.0, 8.60], [0.0, 4.80]],
            area_m2=9.5, centroid=[1.25, 6.70], level_index=1, is_habitable=False,
            metadata={"typology": stair_type}
        ))
        # 9. Upper Gallery Vestibule
        rooms.append(RoomModel(
            room_id="room_L1_gallery", room_type="corridor", room_name="Upper Gallery Vestibule",
            polygon=[[2.50, 4.80], [4.50, 4.80], [4.50, 7.50], [2.50, 7.50], [2.50, 4.80]],
            area_m2=5.4, centroid=[3.50, 6.15], level_index=1, is_habitable=False
        ))
        # 10. Upper TV Lounge / Open Family Gallery (Stacked over TV Lounge)
        rooms.append(RoomModel(
            room_id="room_L1_tv_lounge", room_type="living_room", room_name="Upper TV Lounge / Family Gallery",
            polygon=[[2.50, 7.50], [6.30, 7.50], [6.30, 12.20], [2.50, 12.20], [2.50, 7.50]],
            area_m2=17.9, centroid=[4.40, 9.85], level_index=1, is_habitable=True
        ))
        # 11. Upper West Gallery (Stacked over West Alcove)
        rooms.append(RoomModel(
            room_id="room_L1_west_gallery", room_type="corridor", room_name="Upper West Gallery",
            polygon=[[0.0, 8.60], [2.50, 8.60], [2.50, 12.20], [0.0, 12.20], [0.0, 8.60]],
            area_m2=9.0, centroid=[1.25, 10.40], level_index=1, is_habitable=False
        ))
        # 12. Upper Bedroom 3 (Stacked directly over Ground Master Suite)
        rooms.append(RoomModel(
            room_id="room_L1_bed3", room_type="bedroom", room_name="Upper Bedroom 3",
            polygon=[[0.0, 12.20], [4.875, 12.20], [4.875, 15.40], [0.0, 15.40], [0.0, 12.20]],
            area_m2=15.6, centroid=[2.44, 13.80], level_index=1, is_habitable=True
        ))
        # 13. Bed 3 Walk-In Dressing (Stacked directly over Master WIC)
        rooms.append(RoomModel(
            room_id="room_L1_dress3", room_type="closet", room_name="Bed 3 Walk-In Dressing",
            polygon=[[0.0, 15.40], [2.40, 15.40], [2.40, 17.60], [0.0, 17.60], [0.0, 15.40]],
            area_m2=5.3, centroid=[1.20, 16.50], level_index=1, is_habitable=False
        ))
        # 14. Bed 3 En-Suite Bath (Stacked directly over Master Bath)
        rooms.append(RoomModel(
            room_id="room_L1_bath3", room_type="bathroom", room_name="Bed 3 En-Suite Bath",
            polygon=[[2.40, 15.40], [4.875, 15.40], [4.875, 17.60], [2.40, 17.60], [2.40, 15.40]],
            area_m2=5.4, centroid=[3.64, 16.50], level_index=1, is_habitable=False
        ))
        # 15. Upper Bedroom 4 (Stacked directly over Ground Bedroom 2)
        rooms.append(RoomModel(
            room_id="room_L1_bed4", room_type="bedroom", room_name="Upper Bedroom 4",
            polygon=[[4.875, 12.20], [9.75, 12.20], [9.75, 15.40], [4.875, 15.40], [4.875, 12.20]],
            area_m2=15.6, centroid=[7.31, 13.80], level_index=1, is_habitable=True
        ))
        # 16. Bed 4 En-Suite Bath & Dress (Stacked directly over Bed 2 Bath)
        rooms.append(RoomModel(
            room_id="room_L1_bath4", room_type="bathroom", room_name="Bed 4 En-Suite Bath",
            polygon=[[4.875, 15.40], [7.80, 15.40], [7.80, 17.60], [4.875, 17.60], [4.875, 15.40]],
            area_m2=6.4, centroid=[6.34, 16.50], level_index=1, is_habitable=False
        ))
        # 17. OTS Shaft 2 (Continuous upward to roof)
        rooms.append(RoomModel(
            room_id="room_L1_ots2", room_type="outdoor", room_name="OTS Shaft 2 (Continuous)",
            polygon=[[7.80, 15.40], [9.75, 15.40], [9.75, 17.60], [7.80, 17.60], [7.80, 15.40]],
            area_m2=4.3, centroid=[8.78, 16.50], level_index=1, is_habitable=False
        ))

        # =========================================================================
        # OPENINGS - DOORS & WINDOWS
        # =========================================================================
        doors_l0 = [
            ("door_L0_01", [3.65, 4.80], 1.40, ["room_L0_porch", "room_L0_foyer"]),
            ("door_L0_02", [4.50, 2.20], 1.00, ["room_L0_porch", "room_L0_drawing"]),
            ("door_L0_03", [6.00, 4.40], 1.35, ["room_L0_drawing", "room_L0_dining"]),
            ("door_L0_04", [6.30, 6.75], 1.50, ["room_L0_dining", "room_L0_tv_lounge"]),
            ("door_L0_05", [4.80, 5.40], 0.80, ["room_L0_foyer", "room_L0_powder"]),
            ("door_L0_06", [2.50, 6.00], 1.15, ["room_L0_foyer", "room_L0_stairs"]),
            ("door_L0_07", [3.65, 7.50], 1.20, ["room_L0_foyer", "room_L0_tv_lounge"]),
            ("door_L0_08", [7.90, 7.80], 1.00, ["room_L0_dining", "room_L0_kitchen"]),
            ("door_L0_09", [7.20, 10.70], 0.85, ["room_L0_kitchen", "room_L0_dirty_kitchen"]),
            ("door_L0_10", [8.10, 11.45], 0.80, ["room_L0_dirty_kitchen", "room_L0_ots1"]),
            ("door_L0_11", [2.50, 10.00], 1.20, ["room_L0_tv_lounge", "room_L0_west_gallery"]),
            ("door_L0_12", [1.50, 12.20], 0.95, ["room_L0_west_gallery", "room_L0_bed1"]),
            ("door_L0_13", [0.80, 15.40], 0.80, ["room_L0_bed1", "room_L0_dress1"]),
            ("door_L0_14", [3.64, 15.40], 0.80, ["room_L0_bed1", "room_L0_bath1"]),
            ("door_L0_15", [4.875, 12.20], 0.95, ["room_L0_tv_lounge", "room_L0_bed2"]),
            ("door_L0_16", [6.34, 15.40], 0.80, ["room_L0_bed2", "room_L0_bath2"]),
        ]
        for did, pos, w, conns in doors_l0:
            openings.append(OpeningModel(opening_id=did, opening_type="door", position=pos, width_m=w, connects_rooms=conns, level_index=0))

        doors_l1 = [
            ("door_L1_01", [3.50, 4.80], 1.40, ["room_L1_terrace", "room_L1_gallery"]),
            ("door_L1_02", [4.50, 2.20], 1.20, ["room_L1_terrace", "room_L1_bed5"]),
            ("door_L1_03", [4.50, 4.60], 0.95, ["room_L1_gallery", "room_L1_bed5"]),
            ("door_L1_04", [5.40, 4.40], 0.80, ["room_L1_bed5", "room_L1_bath5"]),
            ("door_L1_05", [2.50, 7.40], 1.15, ["room_L1_gallery", "room_L1_stairs"]),
            ("door_L1_06", [3.50, 7.50], 1.20, ["room_L1_gallery", "room_L1_tv_lounge"]),
            ("door_L1_07", [6.30, 6.75], 1.30, ["room_L1_tv_lounge", "room_L1_kitchenette"]),
            ("door_L1_08", [7.90, 7.80], 0.90, ["room_L1_kitchenette", "room_L1_laundry"]),
            ("door_L1_09", [7.20, 10.70], 0.85, ["room_L1_laundry", "room_L1_utility"]),
            ("door_L1_10", [8.10, 11.45], 0.80, ["room_L1_utility", "room_L1_ots1"]),
            ("door_L1_11", [2.50, 10.00], 1.20, ["room_L1_tv_lounge", "room_L1_west_gallery"]),
            ("door_L1_12", [1.50, 12.20], 0.95, ["room_L1_west_gallery", "room_L1_bed3"]),
            ("door_L1_13", [0.80, 15.40], 0.80, ["room_L1_bed3", "room_L1_dress3"]),
            ("door_L1_14", [3.64, 15.40], 0.80, ["room_L1_bed3", "room_L1_bath3"]),
            ("door_L1_15", [4.875, 12.20], 0.95, ["room_L1_tv_lounge", "room_L1_bed4"]),
            ("door_L1_16", [6.34, 15.40], 0.80, ["room_L1_bed4", "room_L1_bath4"]),
        ]
        for did, pos, w, conns in doors_l1:
            openings.append(OpeningModel(opening_id=did, opening_type="door", position=pos, width_m=w, connects_rooms=conns, level_index=1))

        windows = [
            ("win_L0_draw", [7.00, 0.0], 2.40, 0),
            ("win_L0_din", [9.75, 6.10], 1.80, 0),
            ("win_L0_kit", [9.75, 9.25], 1.80, 0),
            ("win_L0_b1", [2.44, 17.60], 1.80, 0),
            ("win_L0_v1", [3.64, 17.60], 0.90, 0),
            ("win_L0_b2", [7.31, 17.60], 1.80, 0),
            ("win_L0_v2", [7.80, 16.50], 0.80, 0),
            ("win_L1_b5", [7.00, 0.0], 2.40, 1),
            ("win_L1_kitch", [9.75, 6.10], 1.80, 1),
            ("win_L1_laun", [9.75, 9.25], 1.80, 1),
            ("win_L1_b3", [2.44, 17.60], 1.80, 1),
            ("win_L1_v3", [3.64, 17.60], 0.90, 1),
            ("win_L1_b4", [7.31, 17.60], 1.80, 1),
            ("win_L1_v4", [7.80, 16.50], 0.80, 1),
        ]
        for wid, pos, w, lvl in windows:
            openings.append(OpeningModel(opening_id=wid, opening_type="window", position=pos, width_m=w, sill_height_m=0.90, level_index=lvl))

        walls = _build_walls_for_levels(rooms, 0.0, x_max, 0.0, y_max)
        # 4.5" (115mm) TV media baffle partition strictly inside TV Lounge coordinate envelope
        walls.append(WallModel(
            wall_id="wall_L0_baffle",
            wall_type="partition",
            centerline=[[3.10, 8.60], [4.95, 8.60]],
            thickness_m=0.115,
            level_index=0
        ))

        # Graph
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.40, min_shared_boundary_m=0.50)
        edges, _ = extractor.build_graph(rooms, openings)
        edges.append(GraphEdgeModel(
            source_room_id="room_L0_stairs",
            target_room_id="room_L1_stairs",
            relationship_type="via_door",
            weight=1.0,
            metadata={"vertical_circulation": "dogleg_staircase", "aligned": True}
        ))

        total_area = sum(r.area_m2 for r in rooms)
        boundary = [[0.0, 0.0], [x_max, 0.0], [x_max, y_max], [0.0, y_max], [0.0, 0.0]]

        return CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="synthetic_generated",
                floor_count=2,
                levels=[0, 1],
                unit="m",
                wall_height_m=3.00,
                provenance={
                    "project_title": "Executive 10 Marla Luxury Villa",
                    "plot_size": "10 Marla (32' x 58')",
                    "typology": "executive_two_floor"
                }
            ),
            boundary=boundary,
            total_area_m2=round(total_area, 1),
            walls=walls,
            openings=openings,
            rooms=rooms,
            graph_edges=edges
        )


class CanonicalMasterBaselines:
    """
    Formal canonical golden baselines registry for 3 Marla, 5 Marla, 7 Marla, 10 Marla, and 1 Kanal.
    Provides verified canonical floor plans with 100% FloorPlanQualityGate compliance.
    """
    BASELINES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "dataset", "canonical_baselines"))

    SCALE_MAP = {
        "3": "master_3_marla.json",
        "3_marla": "master_3_marla.json",
        "3m": "master_3_marla.json",
        "5": "master_5_marla.json",
        "5_marla": "master_5_marla.json",
        "5m": "master_5_marla.json",
        "5_marla_5bed": "master_5_marla_5bed.json",
        "5m_5bed": "master_5_marla_5bed.json",
        "7": "master_7_marla.json",
        "7_marla": "master_7_marla.json",
        "7m": "master_7_marla.json",
        "10": "master_10_marla.json",
        "10_marla": "master_10_marla.json",
        "10m": "master_10_marla.json",
        "1": "master_1_kanal.json",
        "1_kanal": "master_1_kanal.json",
        "1k": "master_1_kanal.json",
        "kanal": "master_1_kanal.json",
    }

    @classmethod
    def get_baseline_path(cls, scale: str) -> str:
        s = scale.lower().strip()
        filename = cls.SCALE_MAP.get(s, f"master_{s}.json")
        return os.path.join(cls.BASELINES_DIR, filename)

    @classmethod
    def get_master_baseline(cls, scale: str) -> CanonicalFloorPlan:
        path = cls.get_baseline_path(scale)
        if not os.path.exists(path):
            # Fallback to 10 marla
            path = os.path.join(cls.BASELINES_DIR, "master_10_marla.json")
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return CanonicalFloorPlan.from_dict(data)

    @classmethod
    def list_baselines(cls) -> List[str]:
        return ["master_3_marla", "master_5_marla", "master_5_marla_5bed", "master_7_marla", "master_10_marla", "master_1_kanal"]

    @classmethod
    def verify_all_baselines(cls) -> Dict[str, Any]:
        from generation.quality_gate import FloorPlanQualityGate
        results = {}
        for scale in ["3_marla", "5_marla", "7_marla", "10_marla", "1_kanal"]:
            plan = cls.get_master_baseline(scale)
            gate = FloorPlanQualityGate.evaluate(plan)
            results[scale] = {
                "final_status": gate["final_status"],
                "score": gate.get("quality_score", 1.0),
                "is_valid": gate.get("is_valid", True),
                "failures": gate.get("failures", []),
                "room_count": len(plan.rooms),
                "floor_count": plan.metadata.floor_count
            }
        return results

