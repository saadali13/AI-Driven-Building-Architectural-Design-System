"""
Production Multi-Scale Master Canonical Baselines Builder & QA Verifier.
Builds and saves:
- master_3_marla.json (15'x45' | Single-flight / Winder stair | 1 Bed GF + 2 Beds L1)
- master_5_marla.json (25'x45' | Dogleg stair | 2 Beds GF + 2 Beds L1 + Front Terrace)
- master_7_marla.json (30'x55' | Dogleg / L-Stair | 2 Beds GF + 3 Beds L1 + Front Terrace)
- master_10_marla.json (35'x65' | Frozen executive baseline currently in production)
- master_1_kanal.json (50'x90' | Curved/Rotunda Grand Stair | Front Lawn + 2-3 Beds GF + 3 Beds L1)

Validates each against FloorPlanQualityGate to ensure quality_score == 1.0.
"""

import os
import sys
import json
from copy import deepcopy
from typing import Dict, List, Tuple, Any

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from shapely.geometry import Polygon
from dataset.schema.canonical import (
    CanonicalFloorPlan,
    MetadataModel,
    WallModel,
    OpeningModel,
    RoomModel,
    GraphEdgeModel
)
from generation.quality_gate import FloorPlanQualityGate
from extraction.relationships import SpatialRelationshipGraphExtractor
from generation.architectural_templates import (
    Modern5MarlaArchitecturalEngine,
    ExecutiveTwoFloorArchitecturalEngine,
    Luxury1KanalArchitecturalEngine
)


def generate_walls_and_edges(rooms: List[RoomModel], openings: List[OpeningModel], envelope: List[List[float]]) -> Tuple[List[WallModel], List[GraphEdgeModel]]:
    walls: List[WallModel] = []
    
    for lvl in [0, 1]:
        lvl_rooms = [r for r in rooms if r.level_index == lvl]
        if not lvl_rooms:
            continue
        
        # Outer boundary segments
        for i in range(len(envelope) - 1):
            walls.append(WallModel(
                wall_id=f"wall_ext_L{lvl}_{i+1}",
                wall_type="exterior",
                centerline=[envelope[i], envelope[i+1]],
                thickness_m=0.23,
                level_index=lvl
            ))
            
        # Interior shared walls
        for i in range(len(lvl_rooms)):
            p1 = Polygon(lvl_rooms[i].polygon)
            for j in range(i + 1, len(lvl_rooms)):
                p2 = Polygon(lvl_rooms[j].polygon)
                inter = p1.intersection(p2)
                if not inter.is_empty and inter.length >= 0.70:
                    lines = [inter] if inter.geom_type == "LineString" else ([g for g in inter.geoms if g.geom_type == "LineString"] if hasattr(inter, "geoms") else [])
                    for sline in lines:
                        if sline.length >= 0.70:
                            c = list(sline.coords)
                            walls.append(WallModel(
                                wall_id=f"wall_int_L{lvl}_{len(walls)+1}",
                                wall_type="interior",
                                centerline=[[round(c[0][0], 2), round(c[0][1], 2)], [round(c[-1][0], 2), round(c[-1][1], 2)]],
                                thickness_m=0.115,
                                level_index=lvl
                            ))

    extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.50, min_shared_boundary_m=0.60)
    edges, _ = extractor.build_graph(rooms, openings)
    
    stair_0 = next((r for r in rooms if r.level_index == 0 and "stair" in r.room_id.lower()), None)
    stair_1 = next((r for r in rooms if r.level_index == 1 and "stair" in r.room_id.lower()), None)
    if stair_0 and stair_1:
        edges.append(GraphEdgeModel(
            source_room_id=stair_0.room_id,
            target_room_id=stair_1.room_id,
            relationship_type="via_door",
            weight=1.0,
            metadata={"vertical_circulation": "continuous_stairs", "aligned": True}
        ))
        
    return walls, edges


def build_master_3_marla() -> CanonicalFloorPlan:
    """15' x 45' (4.57m x 13.72m) | Single-flight straight stair along East wall | 1 Bed GF + 2 Beds L1"""
    w, d = 4.57, 13.72
    envelope = [[0.0, 0.0], [w, 0.0], [w, d], [0.0, d], [0.0, 0.0]]
    rooms, openings = [], []

    # LEVEL 0
    rooms.append(RoomModel(room_id="room_L0_porch", room_type="garage", room_name="Car Porch (1 Car)", polygon=[[0, 0], [w, 0], [w, 3.8], [0, 3.8], [0, 0]], area_m2=round(w * 3.8, 1), centroid=[round(w / 2, 2), 1.9], level_index=0, is_habitable=False))
    rooms.append(RoomModel(room_id="room_L0_tv_lounge", room_type="lounge", room_name="Open TV Lounge & Dining", polygon=[[0, 3.8], [3.65, 3.8], [3.65, 7.8], [0, 7.8], [0, 3.8]], area_m2=round(3.65 * 4.0, 1), centroid=[1.82, 5.8], level_index=0, is_habitable=True))
    rooms.append(RoomModel(room_id="room_L0_stairs", room_type="corridor", room_name="Staircase Core (Straight UP ->)", polygon=[[3.65, 3.8], [w, 3.8], [w, 7.8], [3.65, 7.8], [3.65, 3.8]], area_m2=round((w - 3.65) * 4.0, 1), centroid=[round(3.65 + (w - 3.65) / 2, 2), 5.8], level_index=0, is_habitable=False, metadata={"typology": "straight"}))

    # Core: Kitchen [0, 2.50], Lobby [2.50, 3.45], Powder [3.45, w]
    rooms.append(RoomModel(room_id="room_L0_kitchen", room_type="kitchen", room_name="Modern Kitchen", polygon=[[0, 7.8], [2.50, 7.8], [2.50, 9.8], [0, 9.8], [0, 7.8]], area_m2=round(2.50 * 2.0, 1), centroid=[1.25, 8.8], level_index=0, is_habitable=True))
    rooms.append(RoomModel(room_id="room_L0_lobby", room_type="corridor", room_name="Bed Lobby", polygon=[[2.50, 7.8], [3.45, 7.8], [3.45, 9.8], [2.50, 9.8], [2.50, 7.8]], area_m2=round((3.45 - 2.50) * 2.0, 1), centroid=[2.97, 8.8], level_index=0, is_habitable=False))
    rooms.append(RoomModel(room_id="room_L0_powder", room_type="bathroom", room_name="Powder Room", polygon=[[3.45, 7.8], [w, 7.8], [w, 9.8], [3.45, 9.8], [3.45, 7.8]], area_m2=round((w - 3.45) * 2.0, 1), centroid=[round(3.45 + (w - 3.45) / 2, 2), 8.8], level_index=0, is_habitable=False))

    # Rear
    rooms.append(RoomModel(room_id="room_L0_bed1", room_type="bedroom", room_name="Ground Master Bedroom 1", polygon=[[0, 9.8], [3.05, 9.8], [3.05, d], [0, d], [0, 9.8]], area_m2=round(3.05 * (d - 9.8), 1), centroid=[1.52, round(9.8 + (d - 9.8) / 2, 2)], level_index=0, is_habitable=True))
    rooms.append(RoomModel(room_id="room_L0_bath1", room_type="bathroom", room_name="Attached Bath 1", polygon=[[3.05, 9.8], [w, 9.8], [w, 12.0], [3.05, 12.0], [3.05, 9.8]], area_m2=round((w - 3.05) * 2.2, 1), centroid=[round(3.05 + (w - 3.05) / 2, 2), 10.9], level_index=0, is_habitable=False))
    rooms.append(RoomModel(room_id="room_L0_ots", room_type="outdoor", room_name="Rear OTS", polygon=[[3.05, 12.0], [w, 12.0], [w, d], [3.05, d], [3.05, 12.0]], area_m2=round((w - 3.05) * (d - 12.0), 1), centroid=[round(3.05 + (w - 3.05) / 2, 2), 12.86], level_index=0, is_habitable=False))

    openings.append(OpeningModel(opening_id="d_3m_01", opening_type="door", position=[1.82, 3.8], width_m=1.10, connects_rooms=["room_L0_porch", "room_L0_tv_lounge"], level_index=0))
    openings.append(OpeningModel(opening_id="d_3m_02", opening_type="door", position=[3.65, 5.0], width_m=0.90, connects_rooms=["room_L0_tv_lounge", "room_L0_stairs"], level_index=0))
    openings.append(OpeningModel(opening_id="d_3m_03", opening_type="door", position=[1.25, 7.8], width_m=0.90, connects_rooms=["room_L0_tv_lounge", "room_L0_kitchen"], level_index=0))
    openings.append(OpeningModel(opening_id="d_3m_04", opening_type="door", position=[2.97, 7.8], width_m=0.90, connects_rooms=["room_L0_tv_lounge", "room_L0_lobby"], level_index=0))
    openings.append(OpeningModel(opening_id="d_3m_05", opening_type="door", position=[3.45, 8.8], width_m=0.80, connects_rooms=["room_L0_lobby", "room_L0_powder"], level_index=0))
    openings.append(OpeningModel(opening_id="d_3m_06", opening_type="door", position=[2.97, 9.8], width_m=0.90, connects_rooms=["room_L0_lobby", "room_L0_bed1"], level_index=0))
    openings.append(OpeningModel(opening_id="d_3m_07", opening_type="door", position=[3.05, 10.9], width_m=0.80, connects_rooms=["room_L0_bed1", "room_L0_bath1"], level_index=0))
    openings.append(OpeningModel(opening_id="d_3m_08", opening_type="door", position=[3.05, 12.86], width_m=0.80, connects_rooms=["room_L0_bed1", "room_L0_ots"], level_index=0))
    openings.append(OpeningModel(opening_id="w_3m_01", opening_type="window", position=[round(w / 2, 2), 0.0], width_m=1.50, sill_height_m=0.90, level_index=0))
    openings.append(OpeningModel(opening_id="w_3m_02", opening_type="window", position=[1.52, d], width_m=1.20, sill_height_m=0.90, level_index=0))

    # LEVEL 1
    rooms.append(RoomModel(room_id="room_L1_terrace", room_type="balcony", room_name="Front Open Terrace", polygon=[[0, 0], [w, 0], [w, 3.8], [0, 3.8], [0, 0]], area_m2=round(w * 3.8, 1), centroid=[round(w / 2, 2), 1.9], level_index=1, is_habitable=False))
    rooms.append(RoomModel(room_id="room_L1_stairs", room_type="corridor", room_name="Staircase Landing (DN <-)", polygon=[[3.65, 3.8], [w, 3.8], [w, 7.8], [3.65, 7.8], [3.65, 3.8]], area_m2=round((w - 3.65) * 4.0, 1), centroid=[round(3.65 + (w - 3.65) / 2, 2), 5.8], level_index=1, is_habitable=False, metadata={"typology": "straight"}))
    rooms.append(RoomModel(room_id="room_L1_bed2", room_type="bedroom", room_name="Bedroom 2 (Front Suite)", polygon=[[0, 3.8], [3.65, 3.8], [3.65, 7.8], [0, 7.8], [0, 3.8]], area_m2=round(3.65 * 4.0, 1), centroid=[1.82, 5.8], level_index=1, is_habitable=True))
    rooms.append(RoomModel(room_id="room_L1_bath2", room_type="bathroom", room_name="Attached Bath 2", polygon=[[0, 7.8], [2.50, 7.8], [2.50, 9.8], [0, 9.8], [0, 7.8]], area_m2=round(2.50 * 2.0, 1), centroid=[1.25, 8.8], level_index=1, is_habitable=False))
    rooms.append(RoomModel(room_id="room_L1_gallery", room_type="corridor", room_name="Upper Gallery / Study Nook", polygon=[[2.50, 7.8], [w, 7.8], [w, 9.8], [2.50, 9.8], [2.50, 7.8]], area_m2=round((w - 2.50) * 2.0, 1), centroid=[round(2.50 + (w - 2.50) / 2, 2), 8.8], level_index=1, is_habitable=False))
    rooms.append(RoomModel(room_id="room_L1_bed3", room_type="bedroom", room_name="Bedroom 3 (Rear Suite)", polygon=[[0, 9.8], [3.05, 9.8], [3.05, d], [0, d], [0, 9.8]], area_m2=round(3.05 * (d - 9.8), 1), centroid=[1.52, round(9.8 + (d - 9.8) / 2, 2)], level_index=1, is_habitable=True))
    rooms.append(RoomModel(room_id="room_L1_bath3", room_type="bathroom", room_name="Attached Bath 3", polygon=[[3.05, 9.8], [w, 9.8], [w, 12.0], [3.05, 12.0], [3.05, 9.8]], area_m2=round((w - 3.05) * 2.2, 1), centroid=[round(3.05 + (w - 3.05) / 2, 2), 10.9], level_index=1, is_habitable=False))
    rooms.append(RoomModel(room_id="room_L1_ots", room_type="outdoor", room_name="Upper OTS Void", polygon=[[3.05, 12.0], [w, 12.0], [w, d], [3.05, d], [3.05, 12.0]], area_m2=round((w - 3.05) * (d - 12.0), 1), centroid=[round(3.05 + (w - 3.05) / 2, 2), 12.86], level_index=1, is_habitable=False))

    openings.append(OpeningModel(opening_id="d_3m_l1_01", opening_type="door", position=[1.82, 3.8], width_m=1.00, connects_rooms=["room_L1_bed2", "room_L1_terrace"], level_index=1))
    openings.append(OpeningModel(opening_id="d_3m_l1_02", opening_type="door", position=[3.65, 5.0], width_m=0.90, connects_rooms=["room_L1_bed2", "room_L1_stairs"], level_index=1))
    openings.append(OpeningModel(opening_id="d_3m_l1_03", opening_type="door", position=[1.25, 7.8], width_m=0.80, connects_rooms=["room_L1_bed2", "room_L1_bath2"], level_index=1))
    openings.append(OpeningModel(opening_id="d_3m_l1_04", opening_type="door", position=[3.65, 7.8], width_m=0.90, connects_rooms=["room_L1_stairs", "room_L1_gallery"], level_index=1))
    openings.append(OpeningModel(opening_id="d_3m_l1_05", opening_type="door", position=[2.97, 9.8], width_m=0.90, connects_rooms=["room_L1_gallery", "room_L1_bed3"], level_index=1))
    openings.append(OpeningModel(opening_id="d_3m_l1_06", opening_type="door", position=[3.05, 10.9], width_m=0.80, connects_rooms=["room_L1_bed3", "room_L1_bath3"], level_index=1))
    openings.append(OpeningModel(opening_id="d_3m_l1_07", opening_type="door", position=[3.05, 12.86], width_m=0.80, connects_rooms=["room_L1_bed3", "room_L1_ots"], level_index=1))
    openings.append(OpeningModel(opening_id="w_3m_l1_01", opening_type="window", position=[round(w / 2, 2), 0.0], width_m=1.50, sill_height_m=0.90, level_index=1))
    openings.append(OpeningModel(opening_id="w_3m_l1_02", opening_type="window", position=[1.52, d], width_m=1.20, sill_height_m=0.90, level_index=1))

    walls, edges = generate_walls_and_edges(rooms, openings, envelope)
    total_area = sum(r.area_m2 for r in rooms)

    metadata = MetadataModel(
        plan_id="master_3_marla",
        source_type="synthetic_generated",
        floor_count=2,
        levels=[0, 1],
        provenance={"scale": "3_marla", "stair_type": "straight", "typology": "CANONICAL_3_MARLA"}
    )

    return CanonicalFloorPlan(
        metadata=metadata,
        boundary=envelope,
        total_area_m2=round(total_area, 1),
        walls=walls,
        openings=openings,
        rooms=rooms,
        graph_edges=edges
    )


def build_master_5_marla() -> CanonicalFloorPlan:
    """25' x 45' (7.62m x 13.72m) | Dogleg stair | 2 Beds GF + 2 Beds L1 + Front Terrace"""
    plan = Modern5MarlaArchitecturalEngine.generate_5_marla_house(plan_id="master_5_marla")
    plan.metadata.plan_id = "master_5_marla"
    plan.metadata.provenance = {"scale": "5_marla", "stair_type": "dogleg", "typology": "CANONICAL_5_MARLA"}
    return plan


def build_master_7_marla() -> CanonicalFloorPlan:
    """30' x 55' (9.14m x 16.76m) | Dogleg / L-Stair | 2 Beds GF + 3 Beds L1 + Front Terrace"""
    p10 = ExecutiveTwoFloorArchitecturalEngine.generate_executive_two_floor_plan()
    # Proportional scaling to 7 Marla: 8.50m width x 15.00m depth
    sx = 8.50 / 9.75
    sy = 15.00 / 17.60

    envelope_7m = [[0.0, 0.0], [8.50, 0.0], [8.50, 15.00], [0.0, 15.00], [0.0, 0.0]]

    rooms_7m = []
    for r in p10.rooms:
        poly_scaled = [[round(pt[0] * sx, 2), round(pt[1] * sy, 2)] for pt in r.polygon]
        p_poly = Polygon(poly_scaled)
        rooms_7m.append(RoomModel(
            room_id=r.room_id.replace("executive", "7m"),
            room_type=r.room_type,
            room_name=r.room_name,
            polygon=poly_scaled,
            area_m2=round(p_poly.area, 1),
            centroid=[round(p_poly.centroid.x, 2), round(p_poly.centroid.y, 2)],
            level_index=r.level_index,
            is_habitable=r.is_habitable,
            metadata=deepcopy(r.metadata)
        ))

    openings_7m = []
    for o in p10.openings:
        pos_scaled = [round(o.position[0] * sx, 2), round(o.position[1] * sy, 2)]
        openings_7m.append(OpeningModel(
            opening_id=o.opening_id.replace("executive", "7m"),
            opening_type=o.opening_type,
            position=pos_scaled,
            width_m=o.width_m,
            height_m=o.height_m,
            sill_height_m=o.sill_height_m,
            connects_rooms=deepcopy(o.connects_rooms),
            level_index=o.level_index
        ))

    walls_7m, edges_7m = generate_walls_and_edges(rooms_7m, openings_7m, envelope_7m)

    return CanonicalFloorPlan(
        metadata=MetadataModel(
            plan_id="master_7_marla",
            source_type="synthetic_generated",
            floor_count=2,
            levels=[0, 1],
            provenance={"scale": "7_marla", "stair_type": "dogleg", "typology": "CANONICAL_7_MARLA"}
        ),
        boundary=envelope_7m,
        total_area_m2=round(sum(r.area_m2 for r in rooms_7m), 1),
        walls=walls_7m,
        openings=openings_7m,
        rooms=rooms_7m,
        graph_edges=edges_7m
    )


def build_master_10_marla() -> CanonicalFloorPlan:
    """35' x 65' (10.67m x 19.81m) | Frozen executive baseline in production"""
    baseline_path = os.path.join(os.path.dirname(__file__), "..", "dataset", "canonical_baselines", "executive_10_marla_master.json")
    if os.path.exists(baseline_path):
        with open(baseline_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        plan = CanonicalFloorPlan.from_dict(data)
    else:
        plan = ExecutiveTwoFloorArchitecturalEngine.generate_executive_two_floor_plan()
    plan.metadata.plan_id = "master_10_marla"
    plan.metadata.provenance = {"scale": "10_marla", "stair_type": "u_shaped", "typology": "CANONICAL_10_MARLA"}
    return plan


def build_master_1_kanal() -> CanonicalFloorPlan:
    """50' x 90' (15.24m x 27.43m) | 15' Front Lawn Setback | Grand Portico/Foyer | Curved Rotunda Stair | Zoned Wings"""
    w, d = 15.24, 27.43
    envelope = [[0.0, 0.0], [w, 0.0], [w, d], [0.0, d], [0.0, 0.0]]
    rooms, openings = [], []

    # LEVEL 0
    # Front Lawn (15'-0" setback): [0, w] x [0, 4.57]
    rooms.append(RoomModel(room_id="room_L0_lawn", room_type="outdoor", room_name="Front Landscaped Lawn", polygon=[[0, 0], [w, 0], [w, 4.57], [0, 4.57], [0, 0]], area_m2=round(w * 4.57, 1), centroid=[round(w / 2, 2), 2.28], level_index=0, is_habitable=False))

    # Triple Car Porch: [9.14, w] x [4.57, 10.07]
    rooms.append(RoomModel(room_id="room_L0_porch", room_type="garage", room_name="Car Porch (3 Cars)", polygon=[[9.14, 4.57], [w, 4.57], [w, 10.07], [9.14, 10.07], [9.14, 4.57]], area_m2=round((w - 9.14) * 5.50, 1), centroid=[round(9.14 + (w - 9.14) / 2, 2), 7.32], level_index=0, is_habitable=False))

    # Formal Drawing Room (West Wing): [0, 5.24] x [4.57, 10.82]
    rooms.append(RoomModel(room_id="room_L0_drawing", room_type="living_room", room_name="Formal Drawing Room", polygon=[[0, 4.57], [5.24, 4.57], [5.24, 10.82], [0, 10.82], [0, 4.57]], area_m2=round(5.24 * 6.25, 1), centroid=[2.62, 7.70], level_index=0, is_habitable=True))

    # Grand Entrance Foyer: [5.24, 9.14] x [4.57, 10.82]
    rooms.append(RoomModel(room_id="room_L0_foyer", room_type="corridor", room_name="Grand Entrance Foyer", polygon=[[5.24, 4.57], [9.14, 4.57], [9.14, 10.82], [5.24, 10.82], [5.24, 4.57]], area_m2=round(3.90 * 6.25, 1), centroid=[7.19, 7.70], level_index=0, is_habitable=False))

    # Formal Dining Room (West Wing): [0, 5.24] x [10.82, 15.32]
    rooms.append(RoomModel(room_id="room_L0_dining", room_type="dining", room_name="Formal Dining Room", polygon=[[0, 10.82], [5.24, 10.82], [5.24, 15.32], [0, 15.32], [0, 10.82]], area_m2=round(5.24 * 4.50, 1), centroid=[2.62, 13.07], level_index=0, is_habitable=True))

    # Grand Rotunda Staircase: [5.24, 9.14] x [10.82, 15.32]
    rooms.append(RoomModel(room_id="room_L0_stairs", room_type="corridor", room_name="Grand Rotunda Staircase", polygon=[[5.24, 10.82], [9.14, 10.82], [9.14, 15.32], [5.24, 15.32], [5.24, 10.82]], area_m2=round(3.90 * 4.50, 1), centroid=[7.19, 13.07], level_index=0, is_habitable=False, metadata={"typology": "curved"}))

    # Powder Room: [9.14, 11.24] x [10.07, 12.57]
    rooms.append(RoomModel(room_id="room_L0_powder", room_type="bathroom", room_name="Guest Powder Room", polygon=[[9.14, 10.07], [11.24, 10.07], [11.24, 12.57], [9.14, 12.57], [9.14, 10.07]], area_m2=round(2.10 * 2.50, 1), centroid=[10.19, 11.32], level_index=0, is_habitable=False))

    # Executive Show Kitchen (East Wing): [11.24, w] x [10.07, 15.32]
    rooms.append(RoomModel(room_id="room_L0_kitchen", room_type="kitchen", room_name="Executive Show Kitchen", polygon=[[11.24, 10.07], [w, 10.07], [w, 15.32], [11.24, 15.32], [11.24, 10.07]], area_m2=round((w - 11.24) * 5.25, 1), centroid=[round(11.24 + (w - 11.24) / 2, 2), 12.70], level_index=0, is_habitable=True))

    # Dirty Kitchen & Utility (East Wing): [11.24, w] x [15.32, 18.32]
    rooms.append(RoomModel(room_id="room_L0_skit", room_type="kitchen", room_name="Dirty Kitchen & Utility", polygon=[[11.24, 15.32], [w, 15.32], [w, 18.32], [11.24, 18.32], [11.24, 15.32]], area_m2=round((w - 11.24) * 3.00, 1), centroid=[round(11.24 + (w - 11.24) / 2, 2), 16.82], level_index=0, is_habitable=True))

    # Landscaped Patio Court (OTS): [11.24, w] x [18.32, 21.42]
    rooms.append(RoomModel(room_id="room_L0_patio", room_type="outdoor", room_name="Landscaped Patio Court", polygon=[[11.24, 18.32], [w, 18.32], [w, 21.42], [11.24, 21.42], [11.24, 18.32]], area_m2=round((w - 11.24) * 3.10, 1), centroid=[round(11.24 + (w - 11.24) / 2, 2), 19.87], level_index=0, is_habitable=False))

    # Central Lobby & Family Lounge
    rooms.append(RoomModel(room_id="room_L0_lobby_core", room_type="corridor", room_name="Central Lobby", polygon=[[9.14, 12.57], [11.24, 12.57], [11.24, 15.32], [9.14, 15.32], [9.14, 12.57]], area_m2=round(2.10 * 2.75, 1), centroid=[10.19, 13.95], level_index=0, is_habitable=False))
    rooms.append(RoomModel(room_id="room_L0_tv_lounge", room_type="lounge", room_name="Expansive Family Lounge", polygon=[[0, 15.32], [11.24, 15.32], [11.24, 21.42], [0, 21.42], [0, 15.32]], area_m2=round(11.24 * 6.10, 1), centroid=[5.62, 18.37], level_index=0, is_habitable=True))

    # Rear Suite 1 (West): [0, 6.00] x [21.42, d]
    rooms.append(RoomModel(room_id="room_L0_bed1", room_type="bedroom", room_name="Master Bedroom Suite 1", polygon=[[0, 21.42], [6.00, 21.42], [6.00, d], [0, d], [0, 21.42]], area_m2=round(6.00 * (d - 21.42), 1), centroid=[3.00, round(21.42 + (d - 21.42) / 2, 2)], level_index=0, is_habitable=True))

    # Bath 1 & Dress: [6.00, 9.50] x [21.42, 25.00]
    rooms.append(RoomModel(room_id="room_L0_bath1", room_type="bathroom", room_name="Ensuite Luxury Bath 1", polygon=[[6.00, 21.42], [9.50, 21.42], [9.50, 25.00], [6.00, 25.00], [6.00, 21.42]], area_m2=round(3.50 * 3.58, 1), centroid=[7.75, 23.21], level_index=0, is_habitable=False))

    # Rear OTS: [6.00, 9.50] x [25.00, d]
    rooms.append(RoomModel(room_id="room_L0_ots", room_type="outdoor", room_name="Rear Light Court (OTS)", polygon=[[6.00, 25.00], [9.50, 25.00], [9.50, d], [6.00, d], [6.00, 25.00]], area_m2=round(3.50 * (d - 25.00), 1), centroid=[7.75, round(25.0 + (d - 25.0) / 2, 2)], level_index=0, is_habitable=False))

    # Rear Suite 2 (East): [9.50, w] x [21.42, 25.00]
    rooms.append(RoomModel(room_id="room_L0_bed2", room_type="bedroom", room_name="Master Bedroom Suite 2", polygon=[[9.50, 21.42], [w, 21.42], [w, 25.00], [9.50, 25.00], [9.50, 21.42]], area_m2=round((w - 9.50) * 3.58, 1), centroid=[round(9.50 + (w - 9.50) / 2, 2), 23.21], level_index=0, is_habitable=True))

    # Bath 2: [9.50, w] x [25.00, d]
    rooms.append(RoomModel(room_id="room_L0_bath2", room_type="bathroom", room_name="Ensuite Luxury Bath 2", polygon=[[9.50, 25.00], [w, 25.00], [w, d], [9.50, d], [9.50, 25.00]], area_m2=round((w - 9.50) * (d - 25.00), 1), centroid=[round(9.50 + (w - 9.50) / 2, 2), round(25.0 + (d - 25.0) / 2, 2)], level_index=0, is_habitable=False))

    # Doors L0
    openings.append(OpeningModel(opening_id="d_1k_01", opening_type="door", position=[7.19, 4.57], width_m=1.80, connects_rooms=["room_L0_lawn", "room_L0_foyer"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_02", opening_type="door", position=[9.14, 7.32], width_m=1.20, connects_rooms=["room_L0_foyer", "room_L0_porch"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_03", opening_type="door", position=[5.24, 7.70], width_m=1.20, connects_rooms=["room_L0_foyer", "room_L0_drawing"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_04", opening_type="door", position=[2.62, 10.82], width_m=1.20, connects_rooms=["room_L0_drawing", "room_L0_dining"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_05", opening_type="door", position=[7.19, 10.82], width_m=1.50, connects_rooms=["room_L0_foyer", "room_L0_stairs"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_06", opening_type="door", position=[5.24, 13.07], width_m=1.20, connects_rooms=["room_L0_stairs", "room_L0_dining"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_07", opening_type="door", position=[9.14, 11.32], width_m=0.90, connects_rooms=["room_L0_stairs", "room_L0_powder"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_08", opening_type="door", position=[9.14, 13.95], width_m=1.20, connects_rooms=["room_L0_stairs", "room_L0_lobby_core"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_09", opening_type="door", position=[11.24, 12.70], width_m=1.10, connects_rooms=["room_L0_lobby_core", "room_L0_kitchen"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_10", opening_type="door", position=[10.19, 15.32], width_m=1.20, connects_rooms=["room_L0_lobby_core", "room_L0_tv_lounge"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_11", opening_type="door", position=[5.24, 15.32], width_m=1.20, connects_rooms=["room_L0_stairs", "room_L0_tv_lounge"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_12", opening_type="door", position=[13.24, 15.32], width_m=0.90, connects_rooms=["room_L0_kitchen", "room_L0_skit"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_13", opening_type="door", position=[11.24, 19.87], width_m=1.50, connects_rooms=["room_L0_tv_lounge", "room_L0_patio"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_14", opening_type="door", position=[3.00, 21.42], width_m=1.00, connects_rooms=["room_L0_tv_lounge", "room_L0_bed1"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_15", opening_type="door", position=[6.00, 23.21], width_m=0.90, connects_rooms=["room_L0_bed1", "room_L0_bath1"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_16", opening_type="door", position=[7.75, 25.00], width_m=0.80, connects_rooms=["room_L0_bath1", "room_L0_ots"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_17", opening_type="door", position=[9.50, 21.42], width_m=1.00, connects_rooms=["room_L0_tv_lounge", "room_L0_bed2"], level_index=0))
    openings.append(OpeningModel(opening_id="d_1k_18", opening_type="door", position=[12.37, 25.00], width_m=0.90, connects_rooms=["room_L0_bed2", "room_L0_bath2"], level_index=0))
    openings.append(OpeningModel(opening_id="w_1k_01", opening_type="window", position=[2.62, 4.57], width_m=2.40, sill_height_m=0.60, level_index=0))
    openings.append(OpeningModel(opening_id="w_1k_02", opening_type="window", position=[3.00, d], width_m=2.00, sill_height_m=0.80, level_index=0))
    openings.append(OpeningModel(opening_id="w_1k_03", opening_type="window", position=[12.37, d], width_m=2.00, sill_height_m=0.80, level_index=0))

    # LEVEL 1
    # Front Open Terrace over Porch: [9.14, w] x [4.57, 10.07]
    rooms.append(RoomModel(room_id="room_L1_terrace", room_type="balcony", room_name="Front Open Terrace", polygon=[[9.14, 4.57], [w, 4.57], [w, 10.07], [9.14, 10.07], [9.14, 4.57]], area_m2=round((w - 9.14) * 5.50, 1), centroid=[round(9.14 + (w - 9.14) / 2, 2), 7.32], level_index=1, is_habitable=False))

    # Bed 3 (Front West Suite over Drawing): [0, 5.24] x [4.57, 10.82]
    rooms.append(RoomModel(room_id="room_L1_bed3", room_type="bedroom", room_name="Bedroom 3 (Front West Suite)", polygon=[[0, 4.57], [5.24, 4.57], [5.24, 10.82], [0, 10.82], [0, 4.57]], area_m2=round(5.24 * 6.25, 1), centroid=[2.62, 7.70], level_index=1, is_habitable=True))

    # Grand Atrium Void ("OPEN TO BELOW"): [5.24, 9.14] x [4.57, 10.82]
    rooms.append(RoomModel(room_id="room_L1_atrium", room_type="corridor", room_name="Grand Atrium Gallery (OPEN TO BELOW)", polygon=[[5.24, 4.57], [9.14, 4.57], [9.14, 10.82], [5.24, 10.82], [5.24, 4.57]], area_m2=round(3.90 * 6.25, 1), centroid=[7.19, 7.70], level_index=1, is_habitable=False))

    # Bed 4 (West Suite over Dining): [0, 5.24] x [10.82, 15.32]
    rooms.append(RoomModel(room_id="room_L1_bed4", room_type="bedroom", room_name="Bedroom 4 (West Suite)", polygon=[[0, 10.82], [5.24, 10.82], [5.24, 15.32], [0, 15.32], [0, 10.82]], area_m2=round(5.24 * 4.50, 1), centroid=[2.62, 13.07], level_index=1, is_habitable=True))

    # Grand Rotunda Staircase Landing: [5.24, 9.14] x [10.82, 15.32]
    rooms.append(RoomModel(room_id="room_L1_stairs", room_type="corridor", room_name="Grand Rotunda Staircase Landing", polygon=[[5.24, 10.82], [9.14, 10.82], [9.14, 15.32], [5.24, 15.32], [5.24, 10.82]], area_m2=round(3.90 * 4.50, 1), centroid=[7.19, 13.07], level_index=1, is_habitable=False, metadata={"typology": "curved"}))

    # Bath 4: [9.14, 11.24] x [10.07, 12.57]
    rooms.append(RoomModel(room_id="room_L1_bath4", room_type="bathroom", room_name="Attached Bath 4", polygon=[[9.14, 10.07], [11.24, 10.07], [11.24, 12.57], [9.14, 12.57], [9.14, 10.07]], area_m2=round(2.10 * 2.50, 1), centroid=[10.19, 11.32], level_index=1, is_habitable=False))

    # Bed 5 (East Suite over Kitchen): [11.24, w] x [10.07, 15.32]
    rooms.append(RoomModel(room_id="room_L1_bed5", room_type="bedroom", room_name="Bedroom 5 (East Suite)", polygon=[[11.24, 10.07], [w, 10.07], [w, 15.32], [11.24, 15.32], [11.24, 10.07]], area_m2=round((w - 11.24) * 5.25, 1), centroid=[round(11.24 + (w - 11.24) / 2, 2), 12.70], level_index=1, is_habitable=True))

    # Upper Pantry & Kitchenette: [11.24, w] x [15.32, 18.32]
    rooms.append(RoomModel(room_id="room_L1_kitchenette", room_type="kitchen", room_name="Upper Pantry & Kitchenette", polygon=[[11.24, 15.32], [w, 15.32], [w, 18.32], [11.24, 18.32], [11.24, 15.32]], area_m2=round((w - 11.24) * 3.00, 1), centroid=[round(11.24 + (w - 11.24) / 2, 2), 16.82], level_index=1, is_habitable=True))

    # Upper Courtyard Void (over Patio): [11.24, w] x [18.32, 21.42]
    rooms.append(RoomModel(room_id="room_L1_patio_void", room_type="outdoor", room_name="Upper Courtyard Void", polygon=[[11.24, 18.32], [w, 18.32], [w, 21.42], [11.24, 21.42], [11.24, 18.32]], area_m2=round((w - 11.24) * 3.10, 1), centroid=[round(11.24 + (w - 11.24) / 2, 2), 19.87], level_index=1, is_habitable=False))

    # Upper Lounge & Central Gallery
    rooms.append(RoomModel(room_id="room_L1_lobby_core", room_type="corridor", room_name="Upper Central Gallery", polygon=[[9.14, 12.57], [11.24, 12.57], [11.24, 15.32], [9.14, 15.32], [9.14, 12.57]], area_m2=round(2.10 * 2.75, 1), centroid=[10.19, 13.95], level_index=1, is_habitable=False))
    rooms.append(RoomModel(room_id="room_L1_tv_lounge", room_type="lounge", room_name="Upper Family Lounge", polygon=[[0, 15.32], [11.24, 15.32], [11.24, 21.42], [0, 21.42], [0, 15.32]], area_m2=round(11.24 * 6.10, 1), centroid=[5.62, 18.37], level_index=1, is_habitable=True))

    # Rear Suites Level 1:
    # Bed 6 (Upper Master Suite 1): [0, 6.00] x [21.42, d]
    rooms.append(RoomModel(room_id="room_L1_bed6", room_type="bedroom", room_name="Bedroom 6 (Upper Master Suite)", polygon=[[0, 21.42], [6.00, 21.42], [6.00, d], [0, d], [0, 21.42]], area_m2=round(6.00 * (d - 21.42), 1), centroid=[3.00, round(21.42 + (d - 21.42) / 2, 2)], level_index=1, is_habitable=True))

    # Bath 6: [6.00, 9.50] x [21.42, 25.00]
    rooms.append(RoomModel(room_id="room_L1_bath6", room_type="bathroom", room_name="Attached Bath 6", polygon=[[6.00, 21.42], [9.50, 21.42], [9.50, 25.00], [6.00, 25.00], [6.00, 21.42]], area_m2=round(3.50 * 3.58, 1), centroid=[7.75, 23.21], level_index=1, is_habitable=False))

    # Upper Rear OTS Void: [6.00, 9.50] x [25.00, d]
    rooms.append(RoomModel(room_id="room_L1_ots", room_type="outdoor", room_name="Upper Rear OTS Void", polygon=[[6.00, 25.00], [9.50, 25.00], [9.50, d], [6.00, d], [6.00, 25.00]], area_m2=round(3.50 * (d - 25.00), 1), centroid=[7.75, round(25.0 + (d - 25.0) / 2, 2)], level_index=1, is_habitable=False))

    # Bed 7 (Upper Rear Suite 2): [9.50, w] x [21.42, 25.00]
    rooms.append(RoomModel(room_id="room_L1_bed7", room_type="bedroom", room_name="Bedroom 7 (Upper Rear Suite)", polygon=[[9.50, 21.42], [w, 21.42], [w, 25.00], [9.50, 25.00], [9.50, 21.42]], area_m2=round((w - 9.50) * 3.58, 1), centroid=[round(9.50 + (w - 9.50) / 2, 2), 23.21], level_index=1, is_habitable=True))

    # Bath 7: [9.50, w] x [25.00, d]
    rooms.append(RoomModel(room_id="room_L1_bath7", room_type="bathroom", room_name="Attached Bath 7", polygon=[[9.50, 25.00], [w, 25.00], [w, d], [9.50, d], [9.50, 25.00]], area_m2=round((w - 9.50) * (d - 25.00), 1), centroid=[round(9.50 + (w - 9.50) / 2, 2), round(25.0 + (d - 25.0) / 2, 2)], level_index=1, is_habitable=False))

    # Doors L1
    openings.append(OpeningModel(opening_id="d_1k_l1_01", opening_type="door", position=[7.19, 10.82], width_m=1.50, connects_rooms=["room_L1_stairs", "room_L1_atrium"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_02", opening_type="door", position=[9.14, 7.32], width_m=1.20, connects_rooms=["room_L1_atrium", "room_L1_terrace"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_03", opening_type="door", position=[5.24, 7.70], width_m=1.10, connects_rooms=["room_L1_atrium", "room_L1_bed3"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_04", opening_type="door", position=[5.24, 13.07], width_m=1.10, connects_rooms=["room_L1_stairs", "room_L1_bed4"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_05", opening_type="door", position=[9.14, 11.32], width_m=0.80, connects_rooms=["room_L1_stairs", "room_L1_bath4"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_06", opening_type="door", position=[9.14, 13.95], width_m=1.20, connects_rooms=["room_L1_stairs", "room_L1_lobby_core"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_07", opening_type="door", position=[11.24, 12.70], width_m=1.00, connects_rooms=["room_L1_lobby_core", "room_L1_bed5"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_08", opening_type="door", position=[10.19, 15.32], width_m=1.20, connects_rooms=["room_L1_lobby_core", "room_L1_tv_lounge"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_09", opening_type="door", position=[5.24, 15.32], width_m=1.20, connects_rooms=["room_L1_stairs", "room_L1_tv_lounge"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_10", opening_type="door", position=[11.24, 16.82], width_m=0.90, connects_rooms=["room_L1_tv_lounge", "room_L1_kitchenette"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_11", opening_type="door", position=[3.00, 21.42], width_m=1.00, connects_rooms=["room_L1_tv_lounge", "room_L1_bed6"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_12", opening_type="door", position=[6.00, 23.21], width_m=0.90, connects_rooms=["room_L1_bed6", "room_L1_bath6"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_13", opening_type="door", position=[7.75, 25.00], width_m=0.80, connects_rooms=["room_L1_bath6", "room_L1_ots"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_14", opening_type="door", position=[9.50, 21.42], width_m=1.00, connects_rooms=["room_L1_tv_lounge", "room_L1_bed7"], level_index=1))
    openings.append(OpeningModel(opening_id="d_1k_l1_15", opening_type="door", position=[12.37, 25.00], width_m=0.90, connects_rooms=["room_L1_bed7", "room_L1_bath7"], level_index=1))
    openings.append(OpeningModel(opening_id="w_1k_l1_01", opening_type="window", position=[2.62, 4.57], width_m=2.40, sill_height_m=0.60, level_index=1))
    openings.append(OpeningModel(opening_id="w_1k_l1_02", opening_type="window", position=[3.00, d], width_m=2.00, sill_height_m=0.80, level_index=1))
    openings.append(OpeningModel(opening_id="w_1k_l1_03", opening_type="window", position=[12.37, d], width_m=2.00, sill_height_m=0.80, level_index=1))

    walls, edges = generate_walls_and_edges(rooms, openings, envelope)
    total_area = sum(r.area_m2 for r in rooms)

    metadata = MetadataModel(
        plan_id="master_1_kanal",
        source_type="synthetic_generated",
        floor_count=2,
        levels=[0, 1],
        provenance={"scale": "1_kanal", "stair_type": "curved", "typology": "CANONICAL_1_KANAL"}
    )

    return CanonicalFloorPlan(
        metadata=metadata,
        boundary=envelope,
        total_area_m2=round(total_area, 1),
        walls=walls,
        openings=openings,
        rooms=rooms,
        graph_edges=edges
    )


def build_master_5_marla_5bed() -> CanonicalFloorPlan:
    """25' x 45' (7.00m x 12.50m) | 5 Bedrooms (2 GF + 3 L1) | Attached Baths | Family Lounge"""
    base = Modern5MarlaArchitecturalEngine.generate_5_marla_house(plan_id="master_5_marla_5bed")

    # Adapt Ground Floor Drawing into Bedroom 1 (Guest Suite) and align bedrooms
    for r in base.rooms:
        if r.room_id == "room_L0_drawing":
            r.room_id = "room_L0_bed1"
            r.room_type = "bedroom"
            r.room_name = "Bedroom 1 (Guest Suite)"
        elif r.room_id == "room_L0_bed1":
            r.room_id = "room_L0_bed2"
            r.room_name = "Bedroom 2 (Master Suite)"
        elif r.room_id == "room_L0_bath1":
            r.room_id = "room_L0_bath2"
            r.room_name = "Attached Bath 2"
        elif r.room_id == "room_L0_powder":
            r.room_id = "room_L0_bath1"
            r.room_name = "Attached Bath 1 (Powder)"
        elif r.room_id == "room_L1_bed2":
            r.room_id = "room_L1_bed4"
            r.room_name = "Bedroom 4 (Front Suite)"
        elif r.room_id == "room_L1_bath2":
            r.room_id = "room_L1_bath4"
            r.room_name = "Attached Bath 4"
        elif r.room_id == "room_L1_bed4":
            r.room_id = "room_L1_bed5"
            r.room_name = "Bedroom 5 (Rear Suite)"
        elif r.room_id == "room_L1_bath4":
            r.room_id = "room_L1_bath5"
            r.room_name = "Attached Bath 5"

    for o in base.openings:
        new_c = []
        for c in o.connects_rooms:
            if c == "room_L0_drawing":
                new_c.append("room_L0_bed1")
            elif c == "room_L0_bed1":
                new_c.append("room_L0_bed2")
            elif c == "room_L0_bath1":
                new_c.append("room_L0_bath2")
            elif c == "room_L0_powder":
                new_c.append("room_L0_bath1")
            elif c == "room_L1_bed2":
                new_c.append("room_L1_bed4")
            elif c == "room_L1_bath2":
                new_c.append("room_L1_bath4")
            elif c == "room_L1_bed4":
                new_c.append("room_L1_bed5")
            elif c == "room_L1_bath4":
                new_c.append("room_L1_bath5")
            else:
                new_c.append(c)
        o.connects_rooms = new_c

    # Ensure attached door connects Bed 1 to Bath 1
    bath1_door = next((o for o in base.openings if "room_L0_bath1" in o.connects_rooms and "room_L0_bed1" in o.connects_rooms), None)
    if not bath1_door:
        base.openings.append(OpeningModel(
            opening_id="d_L0_bed1_bath1",
            opening_type="door",
            position=[6.05, 4.20],
            width_m=0.80,
            connects_rooms=["room_L0_bed1", "room_L0_bath1"],
            level_index=0
        ))

    base.metadata.plan_id = "master_5_marla_5bed"
    base.metadata.provenance = {"scale": "5_marla", "stair_type": "dogleg", "bedrooms": 5, "typology": "CANONICAL_5_MARLA_5BED"}
    return base


def build_and_save_all_baselines(output_dir: str = "dataset/canonical_baselines") -> Dict[str, Any]:
    os.makedirs(output_dir, exist_ok=True)
    results = {}

    baselines = [
        ("3_marla", build_master_3_marla),
        ("5_marla", build_master_5_marla),
        ("5_marla_5bed", build_master_5_marla_5bed),
        ("7_marla", build_master_7_marla),
        ("10_marla", build_master_10_marla),
        ("1_kanal", build_master_1_kanal),
    ]

    for scale, builder in baselines:
        print(f"Building master baseline for {scale}...")
        plan = builder()
        q = FloorPlanQualityGate.evaluate(plan)
        print(f"  {scale}: Score={q.get('quality_score')}, Valid={q.get('is_valid')}, Failures={q.get('failure_codes')}")

        assert q.get("quality_score") == 1.0, f"Baseline {scale} failed QualityGate: {q.get('failure_details')}"
        assert q.get("is_valid") is True, f"Baseline {scale} is not valid!"

        out_path = os.path.join(output_dir, f"master_{scale}.json")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(plan.to_json(indent=2))
        print(f"  Saved verified baseline to: {out_path}")

        results[scale] = {
            "plan_id": plan.metadata.plan_id,
            "path": out_path,
            "quality_score": q.get("quality_score"),
            "is_valid": q.get("is_valid"),
            "room_count": len(plan.rooms),
            "floor_count": plan.metadata.floor_count
        }

    return results


if __name__ == "__main__":
    res = build_and_save_all_baselines()
    print("All master baselines successfully built and verified!")
