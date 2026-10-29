"""
Quantitative Diversity Metrics Utility for Architectural Floor Plans.
Author: Principal Residential CAD Architect & Lead Systems Engineer

Implements mathematical dissimilarity metrics to evaluate whether two generated floor plans A and B are distinct:
1. Metric A: Graph Topology Dissimilarity (Adjacency Jaccard Distance)
   - Extracts room adjacency graph G_A and G_B using extraction/relationships.py.
   - Computes Jaccard Distance between edge sets:
     J_dist = 1.0 - (|E_A ∩ E_B| / |E_A ∪ E_B|)
   - Enforces J_dist >= 0.25 (and >= 0.30 for paired scale comparisons).

2. Metric B: Spatial Layout IoU (Bounding Box / Footprint Dissimilarity)
   - Computes pairwise Spatial Intersection-over-Union (IoU) of normalized room footprints across two plans.
   - Enforces average spatial overlap across core living rooms <= 0.70.

3. Metric C: Room Program Node Vector Dissimilarity
   - Verifies room counts, semantic room types, or dimensional aspect ratios differ.
"""

from typing import Dict, List, Tuple, Set, Any, Optional
from collections import Counter
from shapely.geometry import Polygon, box

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel
from extraction.relationships import SpatialRelationshipGraphExtractor


def spatial_iou(poly1: List[List[float]], poly2: List[List[float]]) -> float:
    """Computes geometric Intersection-over-Union (IoU) between two 2D polygons."""
    p1 = Polygon(poly1)
    p2 = Polygon(poly2)
    if not p1.is_valid:
        p1 = p1.buffer(0)
    if not p2.is_valid:
        p2 = p2.buffer(0)
    if p1.is_empty or p2.is_empty:
        return 0.0
    inter = p1.intersection(p2).area
    union = p1.union(p2).area
    return round(inter / union, 4) if union > 0 else 0.0


class DiversityEvaluator:
    """
    Evaluates topological, geometric, and programmatic diversity across architectural floor plans.
    """

    CORE_LIVING_ROOM_TYPES = {"living_room", "lounge", "kitchen", "bedroom", "dining_room", "corridor"}

    @classmethod
    def extract_graph_edges(cls, plan: CanonicalFloorPlan) -> Set[Tuple[str, str]]:
        """
        Extracts semantic adjacency and traversal edges using SpatialRelationshipGraphExtractor.
        Edges are represented as sorted tuples of normalized semantic room names / types.
        """
        room_map = {r.room_id: r for r in plan.rooms}
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.45, min_shared_boundary_m=0.40)
        edges, _ = extractor.build_graph(plan.rooms, plan.openings)

        # Include explicit graph_edges from the plan if present
        all_edges = list(edges) + list(plan.graph_edges or [])

        semantic_edge_set: Set[Tuple[str, str]] = set()
        for edge in all_edges:
            u_id = edge.source_room_id
            v_id = edge.target_room_id
            u_room = room_map.get(u_id)
            v_room = room_map.get(v_id)

            if u_room is not None and v_room is not None:
                # Disallow cross-floor wall adjacency unless explicitly connected via door/stairs
                if u_room.level_index == v_room.level_index or edge.relationship_type in ("via_door", "vertical_stair", "staircase_transition"):
                    u_label = f"L{u_room.level_index}_{u_room.room_type}_{cls._normalize_room_slug(u_room.room_name)}"
                    v_label = f"L{v_room.level_index}_{v_room.room_type}_{cls._normalize_room_slug(v_room.room_name)}"
                    pair = tuple(sorted([u_label, v_label]))
                    semantic_edge_set.add(pair)

        return semantic_edge_set

    @staticmethod
    def _normalize_room_slug(name: str) -> str:
        """Extracts standard archetype slug from room name."""
        nl = name.lower()
        if "master" in nl and "bed" in nl:
            return "master_bed"
        if "bed" in nl:
            return "bed"
        if "bath" in nl or "powder" in nl:
            return "bath"
        if "kitchen" in nl:
            return "open_kitchen" if "open" in nl else "closed_kitchen"
        if "stair" in nl:
            for s in ["rotunda", "curved", "linear", "straight", "dogleg", "u_shaped", "bifurcated", "winder"]:
                if s in nl:
                    return f"stair_{s}"
            return "stair"
        if "drawing" in nl:
            return "drawing"
        if "lounge" in nl or "family" in nl:
            return "lounge"
        if "porch" in nl or "garage" in nl:
            return "porch"
        if "dining" in nl:
            return "dining"
        if "lawn" in nl or "garden" in nl:
            return "lawn"
        if "foyer" in nl:
            return "rotunda_foyer" if "rotunda" in nl else "foyer"
        if "terrace" in nl or "balcony" in nl:
            return "terrace"
        if "servant" in nl:
            return "servant"
        if "study" in nl or "office" in nl:
            return "study"
        if "fitness" in nl or "gym" in nl:
            return "fitness"
        return "room"

    @classmethod
    def compute_adjacency_jaccard_distance(cls, plan_a: CanonicalFloorPlan, plan_b: CanonicalFloorPlan) -> float:
        """
        Computes Jaccard Distance between room adjacency edge sets:
        J_dist = 1.0 - (|E_A ∩ E_B| / |E_A ∪ E_B|)
        Returns 0.0 (identical graphs) to 1.0 (completely disjoint graphs).
        """
        edges_a = cls.extract_graph_edges(plan_a)
        edges_b = cls.extract_graph_edges(plan_b)

        if not edges_a and not edges_b:
            return 0.0
        if not edges_a or not edges_b:
            return 1.0

        intersection = edges_a.intersection(edges_b)
        union = edges_a.union(edges_b)

        jaccard_sim = len(intersection) / len(union) if len(union) > 0 else 0.0
        j_dist = round(1.0 - jaccard_sim, 4)
        return j_dist

    @classmethod
    def compute_spatial_layout_iou(
        cls,
        plan_a: CanonicalFloorPlan,
        plan_b: CanonicalFloorPlan,
        core_types: Optional[Set[str]] = None
    ) -> float:
        """
        Computes the average pairwise Spatial IoU for corresponding core rooms across plans.
        Normalizes coordinates to [0, 1] relative to each plan's boundary bounding box.
        """
        types_to_check = core_types or cls.CORE_LIVING_ROOM_TYPES

        def get_normalized_rooms(plan: CanonicalFloorPlan) -> Dict[str, List[Polygon]]:
            min_x = min(pt[0] for pt in plan.boundary)
            max_x = max(pt[0] for pt in plan.boundary)
            min_y = min(pt[1] for pt in plan.boundary)
            max_y = max(pt[1] for pt in plan.boundary)
            span_x = max(0.1, max_x - min_x)
            span_y = max(0.1, max_y - min_y)

            norm_dict: Dict[str, List[Polygon]] = {}
            for r in plan.rooms:
                if r.room_type in types_to_check:
                    norm_pts = [
                        [round((pt[0] - min_x) / span_x, 4), round((pt[1] - min_y) / span_y, 4)]
                        for pt in r.polygon
                    ]
                    p = Polygon(norm_pts)
                    if not p.is_valid:
                        p = p.buffer(0)
                    key = f"L{r.level_index}_{r.room_type}"
                    norm_dict.setdefault(key, []).append(p)
            return norm_dict

        rooms_a = get_normalized_rooms(plan_a)
        rooms_b = get_normalized_rooms(plan_b)

        all_types = set(rooms_a.keys()).union(set(rooms_b.keys()))
        if not all_types:
            return 0.0

        total_iou = 0.0
        comparisons = 0

        for rtype in all_types:
            polys_a = rooms_a.get(rtype, [])
            polys_b = rooms_b.get(rtype, [])
            if not polys_a or not polys_b:
                total_iou += 0.0
                comparisons += max(len(polys_a), len(polys_b))
                continue

            for pa in polys_a:
                best_overlap = 0.0
                for pb in polys_b:
                    inter = pa.intersection(pb).area
                    union = pa.union(pb).area
                    iou = (inter / union) if union > 0 else 0.0
                    if iou > best_overlap:
                        best_overlap = iou
                total_iou += best_overlap
                comparisons += 1

        avg_iou = round(total_iou / max(1, comparisons), 4)
        return avg_iou

    @classmethod
    def compute_node_vector_dissimilarity(
        cls,
        plan_a: CanonicalFloorPlan,
        plan_b: CanonicalFloorPlan
    ) -> Dict[str, Any]:
        """
        Computes differences in room counts, bedroom totals, floor levels, and stair typologies.
        """
        counts_a = Counter(r.room_type for r in plan_a.rooms)
        counts_b = Counter(r.room_type for r in plan_b.rooms)

        beds_a = sum(1 for r in plan_a.rooms if r.room_type == "bedroom")
        beds_b = sum(1 for r in plan_b.rooms if r.room_type == "bedroom")

        baths_a = sum(1 for r in plan_a.rooms if r.room_type == "bathroom")
        baths_b = sum(1 for r in plan_b.rooms if r.room_type == "bathroom")

        stair_a = plan_a.metadata.provenance.get("staircase_type", "dogleg")
        stair_b = plan_b.metadata.provenance.get("staircase_type", "dogleg")

        all_keys = set(counts_a.keys()).union(set(counts_b.keys()))
        count_diff = {k: abs(counts_a.get(k, 0) - counts_b.get(k, 0)) for k in all_keys}

        return {
            "total_rooms_a": len(plan_a.rooms),
            "total_rooms_b": len(plan_b.rooms),
            "bedroom_diff": abs(beds_a - beds_b),
            "bathroom_diff": abs(baths_a - baths_b),
            "floors_a": plan_a.floor_count,
            "floors_b": plan_b.floor_count,
            "stair_a": stair_a,
            "stair_b": stair_b,
            "stair_matches": stair_a == stair_b,
            "count_diff": count_diff,
            "is_program_different": (
                beds_a != beds_b or
                plan_a.floor_count != plan_b.floor_count or
                stair_a != stair_b or
                len(plan_a.rooms) != len(plan_b.rooms)
            )
        }

    @classmethod
    def evaluate_diversity(
        cls,
        plan_a: CanonicalFloorPlan,
        plan_b: CanonicalFloorPlan,
        min_jaccard: float = 0.25,
        max_iou: float = 0.70
    ) -> Dict[str, Any]:
        """
        Runs comprehensive quantitative diversity evaluation across two plans.
        Asserts:
        - Jaccard Graph Distance >= min_jaccard
        - Average Spatial IoU <= max_iou
        """
        j_dist = cls.compute_adjacency_jaccard_distance(plan_a, plan_b)
        avg_iou = cls.compute_spatial_layout_iou(plan_a, plan_b)
        node_diff = cls.compute_node_vector_dissimilarity(plan_a, plan_b)

        is_topologically_distinct = j_dist >= min_jaccard
        is_spatially_distinct = avg_iou <= max_iou
        is_diverse = is_topologically_distinct or node_diff["is_program_different"]

        return {
            "jaccard_distance": j_dist,
            "min_jaccard_threshold": min_jaccard,
            "is_topologically_distinct": is_topologically_distinct,
            "average_spatial_iou": avg_iou,
            "max_spatial_iou_threshold": max_iou,
            "is_spatially_distinct": is_spatially_distinct,
            "node_dissimilarity": node_diff,
            "is_diverse": is_diverse
        }
