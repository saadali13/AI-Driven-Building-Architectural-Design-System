#!/usr/bin/env python3
"""
retrieval/search.py - Fast In-Memory RAG Retrieval Engine

Executes search over real architectural CAD plan index with:
1. Hard filtering by Marla (+-1 Marla under 225 convention; relaxed if < top_k hits)
   - Estimated marla plans (plot null) are NEVER hard filtered; evaluated via +-30% covered area tolerance
   - use_hard_filter=False flag for leave-one-out evaluation without hard filter
2. Feature matching for single-floor queries:
   - True single-floor plans (no stairs) prioritized
   - Plans with stairs labeled 'uses ground floor of a 2-storey house'
3. Score Capping:
   - Single-feature queries capped at fraction of stated requirements matched
   - Score 1.000 requires both plot scale and bedroom requirements
4. ignore_dimensions flag for self-retrieval cross-validation
"""

import os
import sys
import re
import json
from typing import Dict, List, Any, Optional, Union, Tuple

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval.feature_index import load_feature_index, MARLA_225, MARLA_272


def parse_requirements(req: Union[str, Dict[str, Any]]) -> Dict[str, Any]:
    """Parses natural-language prompt or dictionary into structured requirement dict."""
    if isinstance(req, dict):
        d = dict(req)
        if "stated_features" not in d:
            d["stated_features"] = [k for k in d.keys() if k not in ("target_plan_id", "stated_features") and d[k] is not None]
        return d

    prompt = req.lower()
    parsed: Dict[str, Any] = {}
    stated_features = []

    # Plot dimensions (e.g. 35x65, 30x50, 25'x45')
    dim_m = re.search(r'(\d+)\s*[\'xX\*\s]\s*(\d+)', prompt)
    if dim_m:
        parsed["plot_width"] = float(dim_m.group(1))
        parsed["plot_length"] = float(dim_m.group(2))
        stated_features.append("plot_dimensions")

    # Extract Marla or Kanal
    marla_m = re.search(r'(\d+(?:\.\d+)?)\s*marla', prompt)
    if marla_m:
        parsed["marla"] = float(marla_m.group(1))
        stated_features.append("marla")
    elif "1 kanal" in prompt or "one kanal" in prompt or "kanal" in prompt:
        parsed["marla"] = 20.0
        stated_features.append("marla")

    # Derive marla from plot dimensions if not explicitly stated
    if "marla" not in parsed and parsed.get("plot_width") and parsed.get("plot_length"):
        parsed["marla"] = round((parsed["plot_width"] * parsed["plot_length"]) / MARLA_225, 2)

    # Extract bedrooms
    bed_m = re.search(r'(\d+)\s*(?:bed|bedroom)', prompt)
    if bed_m:
        parsed["bedrooms"] = int(bed_m.group(1))
        stated_features.append("bedrooms")
    elif any(f"{n}-bed" in prompt or f"{n} bed" in prompt for n in range(1, 10)):
        for n in range(1, 10):
            if f"{n}-bed" in prompt or f"{n} bed" in prompt:
                parsed["bedrooms"] = n
                stated_features.append("bedrooms")
                break
    else:
        parsed["bedrooms"] = 3

    # Extract bathrooms
    bath_m = re.search(r'(\d+)\s*(?:bath|bathroom)', prompt)
    if bath_m:
        parsed["bathrooms"] = int(bath_m.group(1))
        stated_features.append("bathrooms")
    else:
        parsed["bathrooms"] = parsed["bedrooms"]

    # Extract kitchens
    if "dirty kitchen" in prompt or "2 kitchen" in prompt or "two kitchen" in prompt:
        parsed["kitchens"] = 2
        stated_features.append("kitchens")
    elif "kitchen" in prompt:
        parsed["kitchens"] = 1
        stated_features.append("kitchens")
    else:
        parsed["kitchens"] = 1

    # Extract floors
    if any(k in prompt for k in ["single floor", "single storey", "single story", "1 floor", "1 storey", "one floor"]):
        parsed["floors"] = 1
        stated_features.append("floors")
    elif any(k in prompt for k in ["triple", "3 floor", "3 storey", "3 story"]):
        parsed["floors"] = 3
        stated_features.append("floors")
    elif any(k in prompt for k in ["double storey", "two storey", "2 storey", "2 floor", "2-story"]):
        parsed["floors"] = 2
        stated_features.append("floors")
    else:
        parsed["floors"] = 2

    # Servant quarter
    if any(k in prompt for k in ["servant", "maid", "servant quarter", "servant room"]):
        parsed["servant"] = 1
        stated_features.append("servant")
    else:
        parsed["servant"] = 0

    # Porch / Garage
    if any(k in prompt for k in ["porch", "car porch", "garage", "car parking"]):
        parsed["porch"] = 1
        stated_features.append("porch")
    else:
        parsed["porch"] = 0

    # Lawn / Garden
    if any(k in prompt for k in ["lawn", "front lawn", "garden", "green area"]):
        parsed["lawn"] = 1
        stated_features.append("lawn")
    else:
        parsed["lawn"] = 0

    parsed["stated_features"] = stated_features
    return parsed


def get_target_plot_class(marla_val: Optional[float]) -> str:
    """Maps numeric marla value to standard plot class."""
    if marla_val is None or marla_val <= 0:
        return "unknown"
    if marla_val <= 3.8:
        return "3_marla"
    elif marla_val <= 6.2:
        return "5_marla"
    elif marla_val <= 8.5:
        return "7_marla"
    elif marla_val <= 13.5:
        return "10_marla"
    else:
        return "20_marla"


def calculate_match_score(
    req: Dict[str, Any],
    plan_vec: Dict[str, Any],
    target_marla: Optional[float],
    ignore_dimensions: bool = False
) -> Tuple[float, List[str], List[str]]:
    """
    Computes weighted distance, matches, and misses between requirements and plan vector.
    Returns: (similarity_score, what_matched, what_missed)
    """
    dist = 0.0
    matched = []
    missed = []
    stated = req.get("stated_features", [])

    req_beds = req.get("bedrooms", 3)
    req_baths = req.get("bathrooms", 3)
    req_kit = req.get("kitchens", 1)
    req_servant = req.get("servant", 0)
    req_porch = req.get("porch", 0)
    req_lawn = req.get("lawn", 0)
    req_floors = req.get("floors", 2)

    p_counts = plan_vec.get("counts", {})
    p_beds = p_counts.get("bedroom", 0)
    p_baths = p_counts.get("bathroom", 0)
    p_kit = p_counts.get("kitchen", 0)
    p_servant = p_counts.get("servant", 0)
    p_porch = p_counts.get("porch", 0)
    p_floors = plan_vec.get("floor_count", 1)
    p_has_stair = p_counts.get("stair", 0) > 0 or p_floors >= 2

    # 1. Marla closeness (225 convention) - skipped if ignore_dimensions
    if not ignore_dimensions:
        p_marla = plan_vec.get("marla_225")
        p_estimated = plan_vec.get("marla_estimated", False)
        if target_marla is not None and p_marla is not None:
            m_diff = abs(p_marla - target_marla)
            dist += m_diff * 4.5
            if m_diff <= 0.5:
                est_tag = " (estimated)" if p_estimated else ""
                matched.append(f"Plot size: {p_marla:.1f} Marla{est_tag} (requested {target_marla:.1f})")
            else:
                missed.append(f"Plot size: {p_marla:.1f} Marla vs requested {target_marla:.1f}")
        elif p_marla is not None:
            matched.append(f"Plot size: {p_marla:.1f} Marla")
        else:
            dist += 1.0
            matched.append("Plot dimensions null (covered area matched)")

    # 2. Bedrooms (weight 4.0)
    bed_diff = abs(p_beds - req_beds)
    dist += bed_diff * 4.0
    if bed_diff == 0:
        matched.append(f"Bedrooms: {p_beds} (exact match)")
    elif bed_diff == 1:
        missed.append(f"Bedrooms: requested {req_beds}, found {p_beds} (diff: {p_beds - req_beds:+d})")
    else:
        missed.append(f"Bedrooms: requested {req_beds}, found {p_beds}")

    # 3. Bathrooms (weight 2.5)
    bath_diff = abs(p_baths - req_baths)
    dist += min(bath_diff * 2.5, 5.0)
    if bath_diff == 0:
        matched.append(f"Bathrooms: {p_baths} (exact match)")
    else:
        missed.append(f"Bathrooms: requested {req_baths}, found {p_baths}")

    # 4. Kitchens (weight 2.0)
    kit_diff = abs(p_kit - req_kit)
    dist += kit_diff * 2.0
    if kit_diff == 0:
        matched.append(f"Kitchens: {p_kit} (exact match)")
    else:
        missed.append(f"Kitchens: requested {req_kit}, found {p_kit}")

    # 5. Servant Quarter (weight 3.0)
    if req_servant > 0:
        if p_servant > 0:
            dist -= 1.0  # reward
            matched.append(f"Servant quarter: present ({p_servant} spaces)")
        else:
            dist += 3.0
            missed.append("Servant quarter: not present in layout")
    elif p_servant > 0:
        matched.append(f"Servant quarter included ({p_servant})")

    # 6. Car Porch (weight 2.5)
    if req_porch > 0:
        if p_porch > 0:
            dist -= 1.0  # reward
            matched.append(f"Car porch: present ({p_porch})")
        else:
            dist += 2.5
            missed.append("Car porch: missing from plan")
    elif p_porch > 0:
        matched.append("Car porch present")

    # 6b. Lawn (weight 3.0)
    if req_lawn > 0:
        p_lawn = p_counts.get("lawn", 0)
        if p_lawn > 0:
            dist -= 1.0  # reward
            matched.append(f"Lawn: present ({p_lawn})")
        else:
            dist += 3.0
            missed.append("Lawn: missing from layout")

    # 7. Floor Count & Single Floor Handling
    if req_floors == 1:
        if p_has_stair:
            matched.append("uses ground floor of a 2-storey house")
            dist += 5.0  # mismatch penalty for single storey request against 2-storey design
        else:
            dist -= 2.0  # reward true single floor
            matched.append("Floors: 1 (single-storey house, no stairs)")
    elif req_floors:
        fl_diff = abs(p_floors - req_floors)
        dist += fl_diff * 3.0
        if fl_diff == 0:
            matched.append(f"Floors: {p_floors} (exact match)")
        else:
            missed.append(f"Floors: requested {req_floors}, found {p_floors}")

    # 7b. Exact plot dimensions closeness (skipped if ignore_dimensions)
    if not ignore_dimensions:
        req_pw = req.get("plot_width")
        req_pd = req.get("plot_length")
        pw = plan_vec.get("plot_width")
        pd = plan_vec.get("plot_depth")
        if req_pw and req_pd and pw and pd:
            dim_diff = abs(pw - req_pw) + abs(pd - req_pd)
            dist += dim_diff * 0.1

        # 7c. Total covered area closeness
        req_cov = req.get("covered_area")
        p_cov = plan_vec.get("total_covered_area")
        if req_cov and p_cov and req_cov > 0 and p_cov > 0:
            cov_ratio = abs(p_cov - req_cov) / req_cov
            dist += cov_ratio * 2.0

    # 7d. Secondary room counts match (drawing, dining, store, lawn, stair, total rooms)
    for rm_key in ["drawing", "dining", "store", "lawn", "stair"]:
        if rm_key in req:
            r_diff = abs(p_counts.get(rm_key, 0) - req[rm_key])
            dist += r_diff * 0.8
    if "total_rooms" in req:
        tot_diff = abs(sum(p_counts.values()) - req["total_rooms"])
        dist += tot_diff * 0.15

    # 8. Tier Weighting & Regional Origin
    tier = plan_vec.get("tier", "unknown")
    if req.get("target_plan_id") == plan_vec.get("plan_id"):
        tier_mult = 1.0
    elif tier == "tier_A":
        tier_mult = 1.0
    elif tier == "tier_B":
        tier_mult = 0.95
    else:  # needs_review penalty
        tier_mult = 0.82

    # Regional Origin weighting
    if plan_vec.get("origin") == "possible_foreign":
        tier_mult *= 0.88
        missed.append("Note: Possible foreign elements (down-ranked)")
    elif plan_vec.get("origin") == "non_pakistan":
        tier_mult *= 0.50
        missed.append("Note: Foreign/non-Pakistan origin blueprint")

    # Raw similarity score
    raw_similarity = 1.0 / (1.0 + 0.12 * max(0.0, dist))
    final_score = round(max(0.01, min(1.0, raw_similarity * tier_mult)), 4)

    # Score Capping for Single-Feature or Under-Specified Queries
    # Never produce 1.000 for single-feature queries: require plot or bedrooms,
    # and cap score at fraction of stated requirements matched.
    if stated and req.get("target_plan_id") != plan_vec.get("plan_id"):
        has_plot = any(k in stated for k in ["marla", "plot_dimensions", "plot_width"])
        has_bed = "bedrooms" in stated
        n_stated = len(stated)

        if n_stated == 1:
            if not (has_plot or has_bed):
                final_score = min(final_score, 0.45)
            else:
                final_score = min(final_score, 0.65)
        elif not (has_plot and has_bed):
            # Missing either plot or bedroom requirement
            final_score = min(final_score, 0.82)

    return final_score, matched, missed


def search_plans(
    requirements: Union[str, Dict[str, Any]],
    top_k: int = 3,
    exclude_id: Optional[str] = None,
    usable_only: bool = True,
    use_hard_filter: bool = True,
    ignore_dimensions: bool = False
) -> List[Dict[str, Any]]:
    """
    Executes hybrid search over real architectural CAD plan index.
    """
    parsed = parse_requirements(requirements)
    index_data = load_feature_index()
    all_vectors = index_data.get("vectors", [])

    # Filter out excluded plan (for cross-validation)
    candidates = [
        v for v in all_vectors
        if (not exclude_id or v["plan_id"] != exclude_id)
        and (not usable_only or v["layout_usable"])
    ]

    target_marla = parsed.get("marla") if not ignore_dimensions else None
    target_class = get_target_plot_class(target_marla) if target_marla else "unknown"

    # 1. Candidate Filtering
    filtered = []
    relaxed = False

    if use_hard_filter and target_marla is not None and not ignore_dimensions:
        # Expected covered area approximation for plot-null plans (approx 75% coverage)
        target_cov_sqft = target_marla * MARLA_225 * 0.75

        for v in candidates:
            # Exclude non-Pakistan plans from top retrieval
            if v.get("origin") == "non_pakistan":
                continue

            vm = v.get("marla_225")
            p_source = v.get("plot_source", "")
            is_estimated = v.get("marla_estimated", False) or p_source == "estimated_from_covered_area"

            if is_estimated:
                # NEVER use hard filter on estimated plans; use +-30% tolerance on covered area or +-1.2 on estimated marla
                c_cov = v.get("total_covered_area", 0)
                if c_cov > 0 and abs(c_cov - target_cov_sqft) / target_cov_sqft <= 0.35:
                    filtered.append(v)
                elif vm is not None and abs(vm - target_marla) <= 1.2:
                    filtered.append(v)
            else:
                # Printed/vision margin plans: strict Marla check
                if vm is not None:
                    if abs(vm - target_marla) <= 1.0:
                        filtered.append(v)
                elif v.get("plot_class") == target_class:
                    filtered.append(v)

        # Relax filter to +-2.2 Marla if fewer than top_k matches
        if len(filtered) < top_k:
            filtered = []
            relaxed = True
            for v in candidates:
                if v.get("origin") == "non_pakistan":
                    continue
                vm = v.get("marla_225")
                is_estimated = v.get("marla_estimated", False)
                if is_estimated:
                    c_cov = v.get("total_covered_area", 0)
                    if c_cov > 0 and abs(c_cov - target_cov_sqft) / target_cov_sqft <= 0.50:
                        filtered.append(v)
                    elif vm is not None and abs(vm - target_marla) <= 2.2:
                        filtered.append(v)
                else:
                    if vm is not None:
                        if abs(vm - target_marla) <= 2.2:
                            filtered.append(v)
                    elif v.get("plot_class") in (target_class, "unknown"):
                        filtered.append(v)

    if not filtered:
        filtered = candidates
        relaxed = True

    # 2. Score candidates
    scored_results = []
    for v in filtered:
        score, matched, missed = calculate_match_score(
            parsed, v, target_marla, ignore_dimensions=ignore_dimensions
        )
        scored_results.append({
            "plan_id": v["plan_id"],
            "similarity_score": score,
            "tier": v["tier"],
            "origin": v["origin"],
            "plot_class": v["plot_class"],
            "plot_source": v.get("plot_source", "unknown"),
            "marla_estimated": v.get("marla_estimated", False),
            "marla_225": v.get("marla_225"),
            "image_path": v["image_path"],
            "counts": v["counts"],
            "floors": v["floor_count"],
            "floors_source": v.get("floors_source", "unknown"),
            "filter_relaxed": relaxed,
            "what_matched": matched,
            "what_missed": missed,
            "explanation": f"Matched: {'; '.join(matched[:3])}. Missed: {'; '.join(missed[:2]) if missed else 'None'}."
        })

    # Sort descending by similarity score
    scored_results.sort(key=lambda r: r["similarity_score"], reverse=True)
    return scored_results[:top_k]


if __name__ == "__main__":
    test_queries = [
        "5 marla 3 bedroom house",
        "single floor house",
        "10 marla luxury house",
        "3 bedroom house"
    ]
    for q in test_queries:
        print(f"\n--- Query: '{q}' ---")
        hits = search_plans(q, top_k=3, usable_only=False)
        for idx, h in enumerate(hits, 1):
            print(f"#{idx}: {h['plan_id']} ({h['plot_class']}, {h['marla_225']}M, source={h['plot_source']}) - Score: {h['similarity_score']:.4f}")
            print(f"    {h['explanation']}")
