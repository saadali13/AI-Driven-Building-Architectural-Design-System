"""
Structural Design Signature & Topological Similarity Engine.

Generates an immutable structural signature for architectural floor plans:
- Normalized room positions and bounding centroids
- Room adjacency graph topology and traversal paths
- Key anchor positions: Staircase, Kitchen, Dirty Kitchen, Entrance, Parking, Lawn, Courtyard
- Functional zoning: Public formal, Family social, Private bedroom clusters, Service scullery
- Mathematical similarity metric (Jaccard Graph Distance + Anchor IoU + Zone Topology)
"""

import math
import hashlib
from typing import Dict, List, Tuple, Set, Any, Optional
from pydantic import BaseModel, Field
from shapely.geometry import Polygon

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel
from extraction.relationships import SpatialRelationshipGraphExtractor


class StructuralDesignSignature(BaseModel):
    """
    Immutable architectural signature representing the core spatial organization
    of a floor plan (independent of superficial cosmetic finishes, colors, or materials).
    """
    plan_id: str
    scale: str
    planning_strategy: str
    total_area_m2: float
    room_count: int
    room_counts_by_type: Dict[str, int]
    
    # Normalized Centroids: [x_norm, y_norm] where x, y in [0.0, 1.0]
    normalized_centroids: Dict[str, List[float]]
    
    # Key Anchor Zones (e.g. "front_left", "center_right", "rear_left")
    staircase_zone: str
    staircase_typology: str
    kitchen_zone: str
    has_dirty_kitchen: bool
    dirty_kitchen_zone: Optional[str] = None
    entrance_zone: str
    parking_zone: str
    parking_capacity: str  # "single_car" or "double_car"
    lawn_zone: str
    courtyard_zone: Optional[str] = None
    
    # Zoning Centroids (normalized)
    public_zone_centroid: List[float]
    family_lounge_centroid: Optional[List[float]] = None
    private_bedroom_centroids: List[List[float]] = Field(default_factory=list)
    
    # Graph Topology: Set of semantic edge pairs
    adjacency_edges: List[List[str]] = Field(default_factory=list)
    signature_hash: str = ""


def _determine_spatial_zone(x_norm: float, y_norm: float) -> str:
    """Maps normalized [0, 1] coordinates to 9-grid architectural zones."""
    # Y=0 is front (road side), Y=1 is rear (back wall)
    if y_norm < 0.33:
        row = "front"
    elif y_norm < 0.66:
        row = "center"
    else:
        row = "rear"

    if x_norm < 0.33:
        col = "left"
    elif x_norm < 0.66:
        col = "center"
    else:
        col = "right"

    return f"{row}_{col}"


def extract_structural_signature(plan: CanonicalFloorPlan) -> StructuralDesignSignature:
    """
    Extracts the immutable structural design signature from a CanonicalFloorPlan.
    """
    min_x = min(pt[0] for pt in plan.boundary)
    max_x = max(pt[0] for pt in plan.boundary)
    min_y = min(pt[1] for pt in plan.boundary)
    max_y = max(pt[1] for pt in plan.boundary)
    span_x = max(0.1, max_x - min_x)
    span_y = max(0.1, max_y - min_y)

    scale = plan.metadata.provenance.get("target_scale", plan.metadata.provenance.get("scale", "10_marla"))
    strategy = plan.metadata.provenance.get("planning_strategy", plan.metadata.provenance.get("archetype_name", "standard"))

    room_counts: Dict[str, int] = {}
    normalized_centroids: Dict[str, List[float]] = {}
    bedroom_centroids: List[List[float]] = []
    public_pts: List[List[float]] = []

    staircase_zone = "unknown"
    staircase_typology = "dogleg"
    kitchen_zone = "unknown"
    has_dirty_kitchen = False
    dirty_kitchen_zone = None
    entrance_zone = "front_center"
    parking_zone = "front_left"
    parking_cap = "single_car"
    lawn_zone = "front_right"
    courtyard_zone = None
    lounge_centroid = None

    for r in plan.rooms:
        r_type = r.room_type
        room_counts[r_type] = room_counts.get(r_type, 0) + 1

        nx = round((r.centroid[0] - min_x) / span_x, 3)
        ny = round((r.centroid[1] - min_y) / span_y, 3)
        zone = _determine_spatial_zone(nx, ny)
        normalized_centroids[r.room_id] = [nx, ny]

        r_name_lower = r.room_name.lower()
        r_id_lower = r.room_id.lower()

        # Staircase
        if "stair" in r_name_lower or "stair" in r_id_lower or r.metadata.get("typology") in ("dogleg", "straight", "rotunda", "bifurcated"):
            staircase_zone = zone
            staircase_typology = r.metadata.get("typology", "dogleg")
            if "rotunda" in r_name_lower or "curved" in r_name_lower:
                staircase_typology = "rotunda"
            elif "bifurcated" in r_name_lower or "imperial" in r_name_lower:
                staircase_typology = "bifurcated"
            elif "linear" in r_name_lower or "straight" in r_name_lower:
                staircase_typology = "straight"

        # Kitchen & Dirty Kitchen
        if "dirty" in r_name_lower or "scullery" in r_name_lower or "dirty" in r_id_lower or r.metadata.get("is_dirty_kitchen"):
            has_dirty_kitchen = True
            dirty_kitchen_zone = zone
        elif r_type == "kitchen" or "kitchen" in r_name_lower:
            kitchen_zone = zone

        # Parking
        if r_type == "garage" or "porch" in r_name_lower:
            parking_zone = zone
            # If porch width is >= 5.2m, it accommodates 2 cars
            poly_w = max(pt[0] for pt in r.polygon) - min(pt[0] for pt in r.polygon)
            if poly_w >= 5.0 or "2 car" in r_name_lower or "double" in r_name_lower:
                parking_cap = "double_car"
            else:
                parking_cap = "single_car"

        # Lawn
        if "lawn" in r_name_lower or ("outdoor" in r_type and "ots" not in r_name_lower and "courtyard" not in r_name_lower and ny < 0.35):
            lawn_zone = zone

        # Courtyard / Patio / Atrium
        if "courtyard" in r_name_lower or "atrium" in r_name_lower or "patio" in r_name_lower:
            courtyard_zone = zone

        # Lounge
        if "lounge" in r_name_lower or ("living" in r_name_lower and "drawing" not in r_name_lower):
            lounge_centroid = [nx, ny]

        # Bedrooms
        if r_type == "bedroom":
            bedroom_centroids.append([nx, ny])

        # Public spaces (drawing, dining)
        if "drawing" in r_name_lower or "dining" in r_name_lower or "foyer" in r_name_lower:
            public_pts.append([nx, ny])

    # Public Zone Centroid
    if public_pts:
        pub_x = round(sum(p[0] for p in public_pts) / len(public_pts), 3)
        pub_y = round(sum(p[1] for p in public_pts) / len(public_pts), 3)
    else:
        pub_x, pub_y = 0.5, 0.2
    public_zone_centroid = [pub_x, pub_y]

    # Graph Edges
    extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.5, min_shared_boundary_m=0.35)
    edges, _ = extractor.build_graph(plan.rooms, plan.openings)
    all_edges = list(edges) + list(plan.graph_edges or [])
    
    room_map = {r.room_id: r for r in plan.rooms}
    canonical_edges: Set[Tuple[str, str]] = set()
    for e in all_edges:
        u_room = room_map.get(e.source_room_id)
        v_room = room_map.get(e.target_room_id)
        if u_room and v_room:
            u_tag = f"L{u_room.level_index}_{u_room.room_type}"
            v_tag = f"L{v_room.level_index}_{v_room.room_type}"
            pair = tuple(sorted([u_tag, v_tag]))
            canonical_edges.add(pair)

    # Compute stable signature hash
    hasher = hashlib.sha256()
    hasher.update(scale.encode())
    hasher.update(strategy.encode())
    hasher.update(staircase_zone.encode())
    hasher.update(staircase_typology.encode())
    hasher.update(kitchen_zone.encode())
    hasher.update(str(has_dirty_kitchen).encode())
    hasher.update(str(len(plan.rooms)).encode())
    for e in sorted(canonical_edges):
        hasher.update(f"{e[0]}-{e[1]}".encode())
    sig_hash = hasher.hexdigest()[:16]

    return StructuralDesignSignature(
        plan_id=plan.metadata.plan_id,
        scale=scale,
        planning_strategy=strategy,
        total_area_m2=round(plan.total_area_m2, 1),
        room_count=len(plan.rooms),
        room_counts_by_type=room_counts,
        normalized_centroids=normalized_centroids,
        staircase_zone=staircase_zone,
        staircase_typology=staircase_typology,
        kitchen_zone=kitchen_zone,
        has_dirty_kitchen=has_dirty_kitchen,
        dirty_kitchen_zone=dirty_kitchen_zone,
        entrance_zone=entrance_zone,
        parking_zone=parking_zone,
        parking_capacity=parking_cap,
        lawn_zone=lawn_zone,
        courtyard_zone=courtyard_zone,
        public_zone_centroid=public_zone_centroid,
        family_lounge_centroid=lounge_centroid,
        private_bedroom_centroids=bedroom_centroids,
        adjacency_edges=[list(p) for p in sorted(canonical_edges)],
        signature_hash=sig_hash
    )


def compute_structural_similarity(
    sig_a: StructuralDesignSignature,
    sig_b: StructuralDesignSignature
) -> Tuple[float, List[str]]:
    """
    Computes mathematical structural similarity S in [0.0, 1.0] between two designs.
    Returns (similarity_score, list_of_repeated_elements).
    High score (>= 0.70) indicates topological duplication.
    """
    repeated_elements: List[str] = []

    # 1. Graph Topology Similarity (Adjacency Jaccard)
    edges_a = {tuple(e) for e in sig_a.adjacency_edges}
    edges_b = {tuple(e) for e in sig_b.adjacency_edges}
    if edges_a or edges_b:
        inter_edges = edges_a.intersection(edges_b)
        union_edges = edges_a.union(edges_b)
        graph_sim = len(inter_edges) / len(union_edges) if union_edges else 1.0
    else:
        graph_sim = 1.0

    # 2. Key Anchor Concordance
    anchor_matches = 0
    total_anchors = 6

    # Staircase position & typology
    if sig_a.staircase_zone == sig_b.staircase_zone:
        anchor_matches += 1.0
        if sig_a.staircase_typology == sig_b.staircase_typology:
            anchor_matches += 0.5
            repeated_elements.append(f"Identical staircase zone ('{sig_a.staircase_zone}') and typology ('{sig_a.staircase_typology}')")
        else:
            repeated_elements.append(f"Identical staircase zone ('{sig_a.staircase_zone}')")

    # Kitchen position
    if sig_a.kitchen_zone == sig_b.kitchen_zone:
        anchor_matches += 1.0
        repeated_elements.append(f"Identical kitchen position zone ('{sig_a.kitchen_zone}')")

    # Dirty Kitchen status & position
    if sig_a.has_dirty_kitchen == sig_b.has_dirty_kitchen:
        if sig_a.has_dirty_kitchen and sig_a.dirty_kitchen_zone == sig_b.dirty_kitchen_zone:
            anchor_matches += 1.0
            repeated_elements.append(f"Identical dirty kitchen placement ('{sig_a.dirty_kitchen_zone}')")
        else:
            anchor_matches += 0.5

    # Courtyard / Lightwell
    if sig_a.courtyard_zone == sig_b.courtyard_zone and sig_a.courtyard_zone is not None:
        anchor_matches += 1.0
        repeated_elements.append(f"Identical courtyard/atrium zone ('{sig_a.courtyard_zone}')")
    elif sig_a.courtyard_zone is None and sig_b.courtyard_zone is None:
        anchor_matches += 0.5

    # Parking zone
    if sig_a.parking_zone == sig_b.parking_zone:
        anchor_matches += 0.5

    # Lawn zone
    if sig_a.lawn_zone == sig_b.lawn_zone:
        anchor_matches += 0.5

    anchor_sim = min(1.0, anchor_matches / total_anchors)

    # 3. Bedroom Cluster Proximity
    bed_dists = []
    for pa in sig_a.private_bedroom_centroids:
        min_d = min((math.hypot(pa[0] - pb[0], pa[1] - pb[1]) for pb in sig_b.private_bedroom_centroids), default=1.0)
        bed_dists.append(min_d)
    avg_bed_dist = sum(bed_dists) / len(bed_dists) if bed_dists else 0.5
    bed_sim = max(0.0, 1.0 - (avg_bed_dist * 2.0))
    if bed_sim > 0.80:
        repeated_elements.append("Identical bedroom cluster distribution")

    # 4. Programmatic Vector Similarity
    all_types = set(sig_a.room_counts_by_type.keys()).union(set(sig_b.room_counts_by_type.keys()))
    diff_sum = sum(abs(sig_a.room_counts_by_type.get(t, 0) - sig_b.room_counts_by_type.get(t, 0)) for t in all_types)
    max_count = max(sum(sig_a.room_counts_by_type.values()), sum(sig_b.room_counts_by_type.values()), 1)
    prog_sim = max(0.0, 1.0 - (diff_sum / max_count))

    # Composite Similarity S
    composite_sim = round(
        (0.35 * graph_sim) +
        (0.35 * anchor_sim) +
        (0.20 * bed_sim) +
        (0.10 * prog_sim),
        4
    )

    return composite_sim, repeated_elements
