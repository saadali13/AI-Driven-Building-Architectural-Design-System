"""
Master Architectural Catalog Builder for Canonical Residential Blueprints.
Procedurally generates and registers 40 production-grade master plans:
- 10 Archetypes for 3 Marla (15' x 45' / 4.57m x 13.72m)
- 10 Archetypes for 7 Marla (30' x 55' / 9.14m x 16.76m)
- 10 Archetypes for 10 Marla (35' x 65' / 10.67m x 19.81m)
- 10 Archetypes for 1 Kanal (50' x 90' / 15.24m x 27.43m)

All 40 plans strictly follow the CanonicalFloorPlan schema and achieve 1.0 QualityGate compliance.
"""

import os
import sys
import json
from copy import deepcopy
from typing import Dict, List, Tuple, Any, Optional
from shapely.geometry import Polygon

# Ensure project root in sys.path
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

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


def rect_poly(x1: float, y1: float, x2: float, y2: float) -> List[List[float]]:
    """Returns closed rectangular polygon coordinates [[x1, y1], [x2, y1], [x2, y2], [x1, y2], [x1, y1]]."""
    return [
        [round(x1, 2), round(y1, 2)],
        [round(x2, 2), round(y1, 2)],
        [round(x2, 2), round(y2, 2)],
        [round(x1, 2), round(y2, 2)],
        [round(x1, 2), round(y1, 2)]
    ]


def make_room(
    room_id: str,
    room_type: str,
    room_name: str,
    x1: float,
    y1: float,
    x2: float,
    y2: float,
    level_index: int = 0,
    is_habitable: bool = True,
    metadata: Optional[Dict[str, Any]] = None
) -> RoomModel:
    """Creates a RoomModel with precise rectangular boundary."""
    poly = rect_poly(x1, y1, x2, y2)
    area = round((x2 - x1) * (y2 - y1), 2)
    centroid = [round((x1 + x2) / 2.0, 2), round((y1 + y2) / 2.0, 2)]
    return RoomModel(
        room_id=room_id,
        room_type=room_type,
        room_name=room_name,
        polygon=poly,
        area_m2=area,
        centroid=centroid,
        level_index=level_index,
        is_habitable=is_habitable,
        confidence=1.0,
        metadata=metadata or {}
    )


def make_door(
    opening_id: str,
    x: float,
    y: float,
    connects_rooms: List[str],
    width_m: float = 0.90,
    level_index: int = 0
) -> OpeningModel:
    """Creates a door opening with connectivity."""
    return OpeningModel(
        opening_id=opening_id,
        opening_type="door",
        position=[round(x, 2), round(y, 2)],
        width_m=round(width_m, 2),
        height_m=2.10,
        sill_height_m=0.0,
        connects_rooms=connects_rooms,
        level_index=level_index
    )


def make_window(
    opening_id: str,
    x: float,
    y: float,
    width_m: float = 1.20,
    sill_height_m: float = 0.90,
    level_index: int = 0
) -> OpeningModel:
    """Creates a window opening on boundary or OTS."""
    return OpeningModel(
        opening_id=opening_id,
        opening_type="window",
        position=[round(x, 2), round(y, 2)],
        width_m=round(width_m, 2),
        height_m=1.50,
        sill_height_m=round(sill_height_m, 2),
        connects_rooms=[],
        level_index=level_index
    )


def generate_walls_and_edges(
    rooms: List[RoomModel],
    openings: List[OpeningModel],
    envelope: List[List[float]]
) -> Tuple[List[WallModel], List[GraphEdgeModel]]:
    """Synthesizes structural exterior/interior walls and dual-layer graph edges."""
    walls: List[WallModel] = []
    levels = sorted(list(set(r.level_index for r in rooms)))

    for lvl in levels:
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
                    lines = [inter] if inter.geom_type == "LineString" else (
                        [g for g in inter.geoms if g.geom_type == "LineString"] if hasattr(inter, "geoms") else []
                    )
                    for sline in lines:
                        if sline.length >= 0.70:
                            c = list(sline.coords)
                            walls.append(WallModel(
                                wall_id=f"wall_int_L{lvl}_{len(walls)+1}",
                                wall_type="interior",
                                centerline=[
                                    [round(c[0][0], 2), round(c[0][1], 2)],
                                    [round(c[-1][0], 2), round(c[-1][1], 2)]
                                ],
                                thickness_m=0.115,
                                level_index=lvl
                            ))

    extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.50, min_shared_boundary_m=0.60)
    edges, _ = extractor.build_graph(rooms, openings)

    # Vertical circulation edges across levels
    for lvl in levels:
        if lvl + 1 in levels:
            stair_curr = next((r for r in rooms if r.level_index == lvl and "stair" in r.room_id.lower()), None)
            stair_next = next((r for r in rooms if r.level_index == lvl + 1 and "stair" in r.room_id.lower()), None)
            if stair_curr and stair_next:
                edges.append(GraphEdgeModel(
                    source_room_id=stair_curr.room_id,
                    target_room_id=stair_next.room_id,
                    relationship_type="via_door",
                    weight=1.0,
                    metadata={"vertical_circulation": "continuous_stairs", "aligned": True}
                ))

    return walls, edges


def assemble_plan(
    metadata: MetadataModel,
    envelope: List[List[float]],
    rooms: List[RoomModel],
    openings: List[OpeningModel]
) -> CanonicalFloorPlan:
    """Assembles a CanonicalFloorPlan with complete geometry and connectivity."""
    walls, edges = generate_walls_and_edges(rooms, openings, envelope)
    total_area = sum(r.area_m2 for r in rooms)
    return CanonicalFloorPlan(
        metadata=metadata,
        boundary=envelope,
        total_area_m2=round(total_area, 2),
        walls=walls,
        openings=openings,
        rooms=rooms,
        graph_edges=edges
    )


def build_index_entry(plan: CanonicalFloorPlan, rel_canonical_path: str) -> Dict[str, Any]:
    """Generates the metadata entry for dataset/dataset_index.json."""
    import hashlib
    bx = [pt[0] for pt in plan.boundary]
    by = [pt[1] for pt in plan.boundary]
    w_m = round(max(bx) - min(bx), 2)
    d_m = round(max(by) - min(by), 2)
    frontage_ft = round(w_m * 3.28084, 1)
    depth_ft = round(d_m * 3.28084, 1)
    total_area_sqft = round(w_m * d_m * 10.7639, 1)

    scale = plan.metadata.provenance.get("scale", "unknown")
    typology_tag = plan.metadata.provenance.get("typology", "")
    stair_type = plan.metadata.provenance.get("stair_type", "dogleg")

    room_counts: Dict[str, int] = {}
    ground_room_counts: Dict[str, int] = {}
    bedrooms = 0
    bathrooms = 0

    for r in plan.rooms:
        room_counts[r.room_type] = room_counts.get(r.room_type, 0) + 1
        if r.room_type == "bedroom":
            bedrooms += 1
        elif r.room_type == "bathroom":
            bathrooms += 1

        if r.level_index == 0:
            ground_room_counts[r.room_type] = ground_room_counts.get(r.room_type, 0) + 1

    conn_map: Dict[str, List[str]] = {}
    for edge in plan.graph_edges:
        if edge.relationship_type == "via_door":
            conn_map.setdefault(edge.source_room_id, []).append(edge.target_room_id)
            conn_map.setdefault(edge.target_room_id, []).append(edge.source_room_id)

    ground_floor_rooms = []
    for r in plan.rooms:
        if r.level_index == 0:
            poly_coords = r.polygon
            xs = [pt[0] for pt in poly_coords]
            ys = [pt[1] for pt in poly_coords]
            min_x, max_x = min(xs), max(xs)
            min_y, max_y = min(ys), max(ys)

            ground_floor_rooms.append({
                "room_id": r.room_id,
                "room_name": r.room_name,
                "room_type": r.room_type,
                "bbox_m": [round(min_x, 2), round(min_y, 2), round(max_x, 2), round(max_y, 2)],
                "bbox_ft": [
                    round(min_x * 3.28084, 1),
                    round(min_y * 3.28084, 1),
                    round(max_x * 3.28084, 1),
                    round(max_y * 3.28084, 1),
                ],
                "area_m2": r.area_m2,
                "centroid": r.centroid,
                "connected_to": sorted(list(set(conn_map.get(r.room_id, []))))
            })

    edge_summary = f"{plan.metadata.plan_id}_{len(plan.rooms)}_{len(plan.graph_edges)}"
    graph_hash = hashlib.md5(edge_summary.encode()).hexdigest()[:16]

    return {
        "plan_id": plan.metadata.plan_id,
        "source_type": "canonical_master",
        "scale": scale,
        "plot_category": scale,
        "typology_tag": typology_tag,
        "typology": typology_tag,
        "layout_style": typology_tag,
        "spatial_typology": typology_tag,
        "staircase_type": stair_type,
        "stair_type": stair_type,
        "frontage_ft": frontage_ft,
        "depth_ft": depth_ft,
        "total_area_sqft": total_area_sqft,
        "dimensions_m": [round(w_m, 2), round(d_m, 2)],
        "total_area_m2": round(w_m * d_m, 2),
        "floors": plan.metadata.floor_count,
        "levels": plan.metadata.levels,
        "bedrooms": bedrooms,
        "bathrooms": bathrooms,
        "room_counts": room_counts,
        "ground_room_counts": ground_room_counts,
        "topology_graph_hash": graph_hash,
        "canonical_path": rel_canonical_path.replace("\\", "/"),
        "ground_floor_rooms": ground_floor_rooms
    }


def build_and_register_all_masters(
    output_dir: str = "dataset/canonical_baselines",
    index_path: str = "dataset/dataset_index.json"
) -> List[CanonicalFloorPlan]:
    """Generates all 40 master blueprints, writes JSONs, validates QualityGate, and updates dataset_index.json."""
    from dataset.catalog_3_marla import ARCHETYPES_3_MARLA
    from dataset.catalog_7_marla import ARCHETYPES_7_MARLA
    from dataset.catalog_10_marla import ARCHETYPES_10_MARLA
    from dataset.catalog_1_kanal import ARCHETYPES_1_KANAL

    os.makedirs(output_dir, exist_ok=True)

    catalog_groups = [
        ("3_marla", ARCHETYPES_3_MARLA),
        ("7_marla", ARCHETYPES_7_MARLA),
        ("10_marla", ARCHETYPES_10_MARLA),
        ("1_kanal", ARCHETYPES_1_KANAL),
    ]

    generated_plans: List[CanonicalFloorPlan] = []
    index_entries: List[Dict[str, Any]] = []

    for scale_name, builders in catalog_groups:
        for idx, builder in enumerate(builders, start=1):
            plan = builder()
            plan_id = plan.metadata.plan_id
            
            # Verify Quality Gate
            gate_res = FloorPlanQualityGate.evaluate(plan)
            q_score = gate_res.get("quality_score", 0.0)
            status = gate_res.get("final_status", "FAIL")
            crit = len(gate_res.get("critical_failures", []))
            high = len(gate_res.get("high_failures", []))
            if status != "PASS" or q_score < 1.0 or crit > 0 or high > 0:
                print(f"[FAIL] {plan_id}: score={q_score}, crit={crit}, high={high}, failures={gate_res.get('failures')}")
                raise ValueError(f"QualityGate failed for {plan_id}")

            # Save canonical JSON file
            filename = f"{plan_id}.json"
            file_path = os.path.join(output_dir, filename)
            rel_canonical_path = os.path.relpath(file_path, PROJECT_ROOT).replace("\\", "/")

            with open(file_path, "w", encoding="utf-8") as f:
                json.dump(plan.model_dump(mode="json"), f, indent=2)

            # Build index entry
            entry = build_index_entry(plan, rel_canonical_path)
            index_entries.append(entry)
            generated_plans.append(plan)
            print(f"[OK] Generated & Validated: {plan_id} -> {rel_canonical_path}")

    # Update dataset_index.json
    if os.path.exists(index_path):
        with open(index_path, "r", encoding="utf-8") as f:
            catalog = json.load(f)
    else:
        catalog = {
            "dataset_version": "2.0-hybrid",
            "total_plans": 0,
            "scales_indexed": ["3_marla", "5_marla", "7_marla", "10_marla", "1_kanal"],
            "plans": []
        }

    existing_plans = {p["plan_id"]: i for i, p in enumerate(catalog.get("plans", []))}
    for entry in index_entries:
        pid = entry["plan_id"]
        if pid in existing_plans:
            catalog["plans"][existing_plans[pid]] = entry
        else:
            catalog["plans"].append(entry)

    catalog["total_plans"] = len(catalog["plans"])

    scales_indexed = set(catalog.get("scales_indexed", []))
    scales_indexed.update(["3_marla", "5_marla", "7_marla", "10_marla", "1_kanal"])
    catalog["scales_indexed"] = sorted(list(scales_indexed))

    with open(index_path, "w", encoding="utf-8") as f:
        json.dump(catalog, f, indent=2)

    print(f"\nSuccessfully registered {len(generated_plans)} master blueprints in {index_path}.")
    print(f"Total plans in catalog: {catalog['total_plans']}")
    return generated_plans


if __name__ == "__main__":
    build_and_register_all_masters()

