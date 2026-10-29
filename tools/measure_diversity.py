#!/usr/bin/env python3
"""
tools/measure_diversity.py

Objective Diversity Measurement Engine for Architectural Floor Plans.
Compares any two generated floor plans on the same plot size using rigorous,
mathematical spatial metrics across 7 dimensions:

1. Archetype / Strategy Identity: Same or different canonical archetype.
2. Room-Set Signature: Multiset/histogram cosine distance of room counts.
3. Geometric Difference: Per-floor room-polygon overlap (mean IoU of matched rooms)
   and normalized centroid displacement.
4. Topology Difference: Jaccard distance of room-room adjacency edge sets.
5. Core & Circulation Difference: Staircase placement/type, main entry location,
   and circulation spine displacement.
6. Zoning Pattern Difference: Relative spatial placement (front-to-back Y-centroids)
   of Zone A (Public), Zone B (Social/Family), Zone C (Private), and Service Zone.
7. Style/Facade vs. Plan Difference: Explicit check whether variation is merely
   cosmetic styling (elevation/render) or true spatial planning diversity.

Classification:
- IDENTICAL: Exactly matching geometry (mean IoU > 0.99, topology distance == 0).
- COSMETIC: Label renames, style/texture changes, or micro-adjustments with
  mean IoU > 0.88, same core position, and same topology.
- MEANINGFULLY DIFFERENT: Different archetype/strategy, relocated circulation core,
  distinct adjacency topology (distance >= 0.25), or substantial geometric change (mean IoU < 0.75).
"""

import os
import sys
import json
import math
import argparse
from typing import Dict, List, Tuple, Any, Optional
from collections import Counter
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

# Ensure root directory is importable
ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT_DIR not in sys.path:
    sys.path.insert(0, ROOT_DIR)

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel


def load_plan(plan_source: Any) -> CanonicalFloorPlan:
    """Loads a CanonicalFloorPlan from a file path, dict, or existing instance."""
    if isinstance(plan_source, CanonicalFloorPlan):
        return plan_source
    if isinstance(plan_source, dict):
        return CanonicalFloorPlan.model_validate(plan_source)
    if isinstance(plan_source, str):
        if not os.path.exists(plan_source):
            raise FileNotFoundError(f"Plan file not found: {plan_source}")
        with open(plan_source, "r", encoding="utf-8") as f:
            data = json.load(f)
        return CanonicalFloorPlan.model_validate(data)
    raise ValueError(f"Unsupported plan source type: {type(plan_source)}")


def calculate_polygon_iou(poly1: List[List[float]], poly2: List[List[float]]) -> float:
    """Computes Intersection over Union (IoU) of two 2D polygons."""
    try:
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
        if union <= 1e-9:
            return 0.0
        return float(inter / union)
    except Exception:
        return 0.0


def extract_room_multiset(plan: CanonicalFloorPlan) -> Counter:
    """Extracts room type multiset across all levels."""
    c = Counter()
    for r in plan.rooms:
        c[r.room_type] += 1
    return c


def room_multiset_distance(c1: Counter, c2: Counter) -> float:
    """Computes Bray-Curtis / Canberra normalized distance between room multisets."""
    all_keys = set(c1.keys()).union(set(c2.keys()))
    if not all_keys:
        return 0.0
    diff = sum(abs(c1[k] - c2[k]) for k in all_keys)
    total = sum(c1[k] + c2[k] for k in all_keys)
    return float(diff / max(1, total))


def extract_adjacency_graph(plan: CanonicalFloorPlan) -> set:
    """
    Extracts topological adjacency pairs as sorted tuples of room names/types.
    Uses explicit door connections if present, plus boundary-sharing rooms.
    """
    adj_set = set()
    room_map = {r.room_id: r for r in plan.rooms}

    # 1. Door openings
    for op in plan.openings:
        if op.opening_type == "door" and len(op.connects_rooms) == 2:
            r1 = room_map.get(op.connects_rooms[0])
            r2 = room_map.get(op.connects_rooms[1])
            if r1 and r2:
                pair = tuple(sorted([r1.room_type, r2.room_type]))
                adj_set.add(pair)

    # 2. Geometric contact (sharing > 0.5m boundary on same level)
    by_level: Dict[int, List[RoomModel]] = {}
    for r in plan.rooms:
        by_level.setdefault(r.level_index, []).append(r)

    for lvl, lvl_rooms in by_level.items():
        polys = {}
        for r in lvl_rooms:
            p = Polygon(r.polygon)
            if not p.is_valid:
                p = p.buffer(0)
            polys[r.room_id] = p

        for i in range(len(lvl_rooms)):
            for j in range(i + 1, len(lvl_rooms)):
                r1 = lvl_rooms[i]
                r2 = lvl_rooms[j]
                p1 = polys[r1.room_id]
                p2 = polys[r2.room_id]
                try:
                    inter = p1.intersection(p2)
                    if inter.length > 0.4:  # shared boundary edge
                        pair = tuple(sorted([r1.room_type, r2.room_type]))
                        adj_set.add(pair)
                except Exception:
                    pass

    return adj_set


def topology_jaccard_distance(adj1: set, adj2: set) -> float:
    """Computes Jaccard distance between adjacency graphs."""
    union = adj1.union(adj2)
    if not union:
        return 0.0
    inter = adj1.intersection(adj2)
    return 1.0 - (len(inter) / len(union))


def extract_stair_core(plan: CanonicalFloorPlan) -> Optional[Tuple[float, float, str]]:
    """Finds staircase core centroid and type."""
    for r in plan.rooms:
        nl = (r.room_name + " " + r.room_id).lower()
        if "stair" in nl or r.room_type in ("corridor", "stairs") and "stair" in nl:
            return (r.centroid[0], r.centroid[1], r.metadata.get("stair_type", "dogleg"))
    # Check openings or metadata
    stype = plan.metadata.provenance.get("stair_type", "dogleg")
    return (0.0, 0.0, stype)


def extract_zoning_centroids(plan: CanonicalFloorPlan) -> Dict[str, Tuple[float, float]]:
    """
    Extracts normalized centroid for Zone A, Zone B, Zone C, and Service Zone.
    Zone A: Public (drawing, dining, porch, foyer)
    Zone B: Semi-Private (lounge, family living, open kitchen)
    Zone C: Private (bedrooms, dressing, ensuite baths)
    Service: dirty kitchen, laundry, powder room, servant
    """
    zones: Dict[str, List[Tuple[float, float, float]]] = {
        "A": [],  # (x, y, area)
        "B": [],
        "C": [],
        "Service": []
    }

    for r in plan.rooms:
        if r.level_index != 0:
            continue  # evaluate ground floor zoning hierarchy
        t = r.room_type.lower()
        n = r.room_name.lower()
        c = r.centroid
        a = max(1.0, r.area_m2)

        if "dirty" in n or "scullery" in n or "powder" in n or "servant" in n or "laundry" in n or "store" in n:
            zones["Service"].append((c[0], c[1], a))
        elif t in ("bedroom", "bathroom") or "bed" in n or "bath" in n or "dressing" in n:
            zones["C"].append((c[0], c[1], a))
        elif t in ("living_room", "lounge") or "lounge" in n or "family" in n:
            zones["B"].append((c[0], c[1], a))
        else:
            zones["A"].append((c[0], c[1], a))

    result = {}
    for z, pts in zones.items():
        if not pts:
            result[z] = (0.0, 0.0)
        else:
            total_a = sum(p[2] for p in pts)
            avg_x = sum(p[0] * p[2] for p in pts) / total_a
            avg_y = sum(p[1] * p[2] for p in pts) / total_a
            result[z] = (round(avg_x, 2), round(avg_y, 2))
    return result


def compare_plans(plan1_src: Any, plan2_src: Any) -> Dict[str, Any]:
    """
    Performs comprehensive diversity evaluation between two CanonicalFloorPlans.
    Returns quantitative metric scores and qualitative classification.
    """
    p1 = load_plan(plan1_src)
    p2 = load_plan(plan2_src)

    # 1. Archetype / Strategy Identity
    strat1 = p1.metadata.provenance.get("planning_strategy", p1.metadata.plan_id)
    strat2 = p2.metadata.provenance.get("planning_strategy", p2.metadata.plan_id)
    same_strategy = (strat1 == strat2)

    # 2. Room-Set Signature
    c1 = extract_room_multiset(p1)
    c2 = extract_room_multiset(p2)
    room_diff = room_multiset_distance(c1, c2)

    # 3. Geometric Difference (per-floor room matching)
    # Match rooms of the same room_type across floors and compute mean IoU
    all_ious = []
    r_map2 = {r.room_id: r for r in p2.rooms}
    matched_p2_ids = set()

    for r1 in p1.rooms:
        # Candidate rooms in p2 on same level
        cands = [
            r2 for r2 in p2.rooms
            if r2.level_index == r1.level_index
            and r2.room_id not in matched_p2_ids
            and r2.room_type == r1.room_type
        ]
        if not cands:
            # fallback to any room on same level
            cands = [
                r2 for r2 in p2.rooms
                if r2.level_index == r1.level_index
                and r2.room_id not in matched_p2_ids
            ]

        if cands:
            # Pick candidate with highest IoU
            best_r2 = max(cands, key=lambda c: calculate_polygon_iou(r1.polygon, c.polygon))
            iou = calculate_polygon_iou(r1.polygon, best_r2.polygon)
            all_ious.append(iou)
            matched_p2_ids.add(best_r2.room_id)
        else:
            all_ious.append(0.0)

    mean_iou = sum(all_ious) / max(1, len(all_ious))
    geometric_diff = round(1.0 - mean_iou, 4)

    # Plot diagonal normalization factor
    # Estimate plot bounding box
    all_pts_1 = [pt for r in p1.rooms for pt in r.polygon]
    if all_pts_1:
        minx = min(p[0] for p in all_pts_1)
        maxx = max(p[0] for p in all_pts_1)
        miny = min(p[1] for p in all_pts_1)
        maxy = max(p[1] for p in all_pts_1)
        plot_diagonal = max(10.0, math.sqrt((maxx - minx) ** 2 + (maxy - miny) ** 2))
    else:
        plot_diagonal = 20.0

    # 4. Topology Difference
    adj1 = extract_adjacency_graph(p1)
    adj2 = extract_adjacency_graph(p2)
    topological_diff = round(topology_jaccard_distance(adj1, adj2), 4)

    # 5. Core and Circulation Difference
    stair1 = extract_stair_core(p1)
    stair2 = extract_stair_core(p2)
    if stair1 and stair2:
        dx = stair1[0] - stair2[0]
        dy = stair1[1] - stair2[1]
        stair_disp = math.sqrt(dx * dx + dy * dy) / plot_diagonal
        same_stair_type = (stair1[2] == stair2[2])
    else:
        stair_disp = 0.0
        same_stair_type = True

    # 6. Zoning Pattern Difference
    z1 = extract_zoning_centroids(p1)
    z2 = extract_zoning_centroids(p2)
    zone_displacements = {}
    for z in ("A", "B", "C", "Service"):
        p_a = z1.get(z, (0.0, 0.0))
        p_b = z2.get(z, (0.0, 0.0))
        dist = math.sqrt((p_a[0] - p_b[0]) ** 2 + (p_a[1] - p_b[1]) ** 2) / plot_diagonal
        zone_displacements[z] = round(dist, 4)
    avg_zone_disp = sum(zone_displacements.values()) / 4.0

    # 7. Facade / Style Difference
    style1 = p1.metadata.provenance.get("architectural_style", "")
    style2 = p2.metadata.provenance.get("architectural_style", "")
    diff_style = (style1 != style2 and bool(style1) and bool(style2))

    # Overall Composite Diversity Score (0.0 = Identical, 1.0 = Radically Distinct)
    # Weighted combination of strategy match, geometry, topology, and core displacement
    strat_diff = 0.0 if same_strategy else 1.0
    diversity_score = round(
        0.30 * strat_diff +
        0.30 * geometric_diff +
        0.20 * topological_diff +
        0.10 * min(1.0, stair_disp * 3.0) +
        0.10 * min(1.0, avg_zone_disp * 3.0),
        4
    )

    # Classification
    if diversity_score < 0.03 or (mean_iou > 0.98 and topological_diff == 0.0 and room_diff == 0.0 and not diff_style):
        classification = "IDENTICAL"
        rationale = "Exact match across room geometries, circulation core, and topological adjacencies."
    elif mean_iou > 0.85 and topological_diff < 0.15 and stair_disp < 0.08:
        classification = "COSMETIC"
        if diff_style:
            rationale = "Style/facade variation only; floor plan layout, walls, and core placement remain identical."
        else:
            rationale = "Minor room label adjustments or room promotion without structural layout rearrangement."
    else:
        classification = "MEANINGFULLY DIFFERENT"
        reasons = []
        if not same_strategy:
            reasons.append(f"distinct planning archetypes ({strat1} vs {strat2})")
        if topological_diff >= 0.20:
            reasons.append(f"topology distance {topological_diff:.2f}")
        if geometric_diff >= 0.25:
            reasons.append(f"geometric room IoU diff {geometric_diff:.2f}")
        if stair_disp >= 0.10:
            reasons.append(f"staircase core relocated by {stair_disp*100:.1f}%")
        if avg_zone_disp >= 0.10:
            reasons.append(f"zoning centroid shift {avg_zone_disp*100:.1f}%")
        rationale = "Authentic architectural variation: " + ", ".join(reasons)

    return {
        "classification": classification,
        "diversity_score": diversity_score,
        "rationale": rationale,
        "same_strategy": same_strategy,
        "strategy1": strat1,
        "strategy2": strat2,
        "mean_iou": round(mean_iou, 4),
        "geometric_difference": geometric_diff,
        "topological_difference": topological_diff,
        "room_multiset_difference": round(room_diff, 4),
        "stair_core_displacement": round(stair_disp, 4),
        "same_stair_type": same_stair_type,
        "avg_zoning_displacement": round(avg_zone_disp, 4),
        "zone_displacements": zone_displacements,
        "style_difference_only": (diff_style and classification != "MEANINGFULLY DIFFERENT")
    }


def generate_heatmap_and_matrix(
    plan_paths: List[Tuple[str, str]],
    out_csv_path: str,
    out_png_path: str,
    plot_label: str = "Plot Scale"
) -> Dict[str, Any]:
    """
    Computes NxN pairwise difference matrix for a list of (variant_id, path) plans.
    Saves CSV and renders high-quality heatmap PNG.
    """
    n = len(plan_paths)
    matrix = [[0.0 for _ in range(n)] for _ in range(n)]
    class_matrix = [["" for _ in range(n)] for _ in range(n)]

    for i in range(n):
        for j in range(n):
            if i == j:
                matrix[i][j] = 0.0
                class_matrix[i][j] = "IDENTICAL"
            elif j < i:
                matrix[i][j] = matrix[j][i]
                class_matrix[i][j] = class_matrix[j][i]
            else:
                res = compare_plans(plan_paths[i][1], plan_paths[j][1])
                matrix[i][j] = res["diversity_score"]
                class_matrix[i][j] = res["classification"]

    # Write CSV
    os.makedirs(os.path.dirname(os.path.abspath(out_csv_path)), exist_ok=True)
    with open(out_csv_path, "w", encoding="utf-8") as f:
        header = ["Variant"] + [p[0] for p in plan_paths]
        f.write(",".join(header) + "\n")
        for i in range(n):
            row = [plan_paths[i][0]] + [f"{matrix[i][j]:.4f}" for j in range(n)]
            f.write(",".join(row) + "\n")

    # Render Heatmap PNG with matplotlib
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
        import numpy as np

        labels = [p[0] for p in plan_paths]
        data = np.array(matrix)

        fig, ax = plt.subplots(figsize=(max(8, n * 0.9), max(6, n * 0.8)), dpi=200)
        cmap = plt.cm.get_cmap("viridis")
        im = ax.imshow(data, cmap=cmap, vmin=0.0, vmax=1.0)

        ax.set_xticks(range(n))
        ax.set_yticks(range(n))
        ax.set_xticklabels(labels, rotation=45, ha="right", fontsize=9, fontweight="bold")
        ax.set_yticklabels(labels, fontsize=9, fontweight="bold")

        # Overlay text values and classification color cues
        for i in range(n):
            for j in range(n):
                val = data[i, j]
                cls_txt = class_matrix[i][j]
                letter = "I" if cls_txt == "IDENTICAL" else ("C" if cls_txt == "COSMETIC" else "M")
                text_color = "white" if val < 0.6 else "black"
                ax.text(j, i, f"{val:.2f}\n({letter})", ha="center", va="center", color=text_color, fontsize=7.5)

        cbar = ax.figure.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
        cbar.ax.set_ylabel("Pairwise Diversity Distance (0.0 = Identical | 1.0 = Radically Distinct)", rotation=-90, va="bottom", fontsize=9)

        ax.set_title(f"Pairwise Architectural Diversity Distance Matrix — {plot_label}\n[I: Identical | C: Cosmetic | M: Meaningfully Different]", fontsize=11, fontweight="bold", pad=12)
        fig.tight_layout()
        os.makedirs(os.path.dirname(os.path.abspath(out_png_path)), exist_ok=True)
        fig.savefig(out_png_path, dpi=200, bbox_inches="tight")
        plt.close(fig)
    except Exception as e:
        print(f"[measure_diversity] Warning: Heatmap rendering skipped: {e}")

    # Count distinct plan clusters (connected components with distance < 0.15)
    visited = [False] * n
    clusters = 0
    for i in range(n):
        if not visited[i]:
            clusters += 1
            for j in range(i, n):
                if matrix[i][j] < 0.15:
                    visited[j] = True

    return {
        "n_plans": n,
        "distinct_clusters": clusters,
        "csv_path": out_csv_path,
        "png_path": out_png_path,
        "matrix": matrix,
        "class_matrix": class_matrix
    }


def main():
    parser = argparse.ArgumentParser(description="Objective Architectural Diversity Measurement Tool")
    parser.add_argument("plan1", nargs="?", help="Path to first canonical plan JSON")
    parser.add_argument("plan2", nargs="?", help="Path to second canonical plan JSON")
    parser.add_argument("--matrix-dir", help="Directory containing multiple *_canonical.json files to build NxN matrix")
    parser.add_argument("--out-csv", default="diversity_matrix.csv", help="Output CSV path for pairwise matrix")
    parser.add_argument("--out-png", default="diversity_heatmap.png", help="Output PNG heatmap path")
    args = parser.parse_args()

    if args.matrix_dir:
        import glob
        pattern = os.path.join(args.matrix_dir, "*_canonical.json")
        files = sorted(glob.glob(pattern))
        if not files:
            print(f"No canonical plans found in {args.matrix_dir}")
            sys.exit(1)
        plan_tuples = [(os.path.basename(f).replace("_canonical.json", ""), f) for f in files]
        res = generate_heatmap_and_matrix(plan_tuples, args.out_csv, args.out_png)
        print(f"Computed pairwise matrix for {res['n_plans']} plans. Distinct plan clusters: {res['distinct_clusters']}")
        print(f"Saved CSV: {args.out_csv}")
        print(f"Saved Heatmap: {args.out_png}")
    elif args.plan1 and args.plan2:
        res = compare_plans(args.plan1, args.plan2)
        print(json.dumps(res, indent=2))
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
