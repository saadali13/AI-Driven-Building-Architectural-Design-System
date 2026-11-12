#!/usr/bin/env python3
"""
retrieval/feature_index.py - Feature Extraction & Vector Indexing for Floor Plan Retrieval

Reads ONLY from corpus/plans.jsonl with SHA-256 cache validation.
Extracts structured feature vectors:
- plot width, depth, area, aspect ratio
- marla (225 convention standard, 272.25 secondary)
- floor count
- room counts per canonical type (bedroom, bathroom, kitchen, lounge, drawing, dining, porch, servant, etc.)
- total covered area
- layout usability, tier, and regional origin flags
"""

import os
import json
import hashlib
from typing import Dict, List, Any, Optional

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CORPUS_DIR = os.path.join(PROJECT_ROOT, "corpus")
PLANS_JSONL_PATH = os.path.join(CORPUS_DIR, "plans.jsonl")
FEATURE_INDEX_PATH = os.path.join(PROJECT_ROOT, "retrieval", "feature_index.json")

MARLA_225 = 225.0
MARLA_272 = 272.25


def compute_plans_hash() -> str:
    """Computes SHA-256 hash of corpus/plans.jsonl for cache validation."""
    if not os.path.exists(PLANS_JSONL_PATH):
        from corpus.build_corpus import build_corpus
        build_corpus()
    with open(PLANS_JSONL_PATH, "rb") as f:
        return hashlib.sha256(f.read()).hexdigest()


def extract_zone(loc_norm: Any) -> Dict[str, str]:
    """Determines y_zone (front/middle/back) and x_zone (left/right) from normalized coordinates."""
    if not loc_norm:
        return {"y_zone": "unknown", "x_zone": "unknown"}
    x, y = 0.5, 0.5
    if isinstance(loc_norm, (list, tuple)) and len(loc_norm) >= 2:
        x, y = float(loc_norm[0]), float(loc_norm[1])
    elif isinstance(loc_norm, dict):
        x = float(loc_norm.get("x", 0.5))
        y = float(loc_norm.get("y", 0.5))

    # In architectural sheets, top (low y) is rear/back, bottom (high y) is front (street/porch)
    if y < 0.35:
        y_zone = "back"
    elif y <= 0.65:
        y_zone = "middle"
    else:
        y_zone = "front"

    x_zone = "left" if x < 0.5 else "right"
    return {"y_zone": y_zone, "x_zone": x_zone}


def build_plan_feature_vector(plan_record: Dict[str, Any]) -> Dict[str, Any]:
    """Extracts a feature vector from a single real plan record."""
    pid = plan_record.get("plan_id")
    tier = plan_record.get("tier", "unknown")
    origin = plan_record.get("origin", "unknown")
    usable = plan_record.get("layout_usable", False)
    image_path = plan_record.get("image_path", "")
    penalty_flag = (tier == "needs_review")

    # Plot features
    plot = plan_record.get("plot") or {}
    pw = plot.get("width")
    pd = plot.get("depth")
    p_source = plot.get("source")
    area_sqft = (pw * pd) if (pw and pd and pw > 0 and pd > 0) else None
    aspect_ratio = round(pd / pw, 2) if (pw and pd and pw > 0) else None

    # Marla (225 convention standard)
    m_225 = plan_record.get("marla_225")
    m_272 = plan_record.get("marla_272")
    if area_sqft and not m_225:
        m_225 = round(area_sqft / MARLA_225, 2)
        m_272 = round(area_sqft / MARLA_272, 2)

    plot_class = plan_record.get("plot_class", "unknown")
    floor_count = plan_record.get("floors", 1)
    floor_role = plan_record.get("floor_role", "ground")

    # Room counts and covered area
    rooms = plan_record.get("rooms", [])
    total_covered_area = 0.0
    room_zones = []

    counts = dict(plan_record.get("counts", {}))
    # Ensure all canonical keys exist
    for k in ["bedroom", "bathroom", "kitchen", "lounge", "drawing", "dining", "porch", "servant", "store", "stair", "lawn", "other"]:
        if k not in counts:
            counts[k] = 0

    for rm in rooms:
        dims = rm.get("dimensions")
        if dims and len(dims) == 2 and dims[0] and dims[1]:
            total_covered_area += float(dims[0]) * float(dims[1])
        
        c_type = rm.get("canonical_type", "")
        if c_type in ["master_bedroom", "bedroom", "kitchen", "lounge", "drawing", "dining", "porch"]:
            z = extract_zone(rm.get("rect")[:2] if rm.get("rect") else None)
            room_zones.append({
                "room": rm.get("printed_name"),
                "canonical_type": c_type,
                "y_zone": z["y_zone"],
                "x_zone": z["x_zone"]
            })

    total_covered_area = round(total_covered_area, 2)

    return {
        "plan_id": pid,
        "tier": tier,
        "origin": origin,
        "origin_triggers": plan_record.get("origin_triggers", []),
        "layout_usable": usable,
        "usability_reasons": plan_record.get("usability_reasons", []),
        "image_path": image_path,
        "penalty_flag": penalty_flag,
        "plot_width": pw,
        "plot_depth": pd,
        "plot_area_sqft": area_sqft,
        "aspect_ratio": aspect_ratio,
        "plot_source": plan_record.get("plot_source") or p_source,
        "marla_estimated": plan_record.get("marla_estimated", False),
        "marla_225": m_225,
        "marla_272": m_272,
        "plot_class": plot_class,
        "floor_count": floor_count,
        "floor_role": floor_role,
        "floors_source": plan_record.get("floors_source", "unknown"),
        "counts": counts,
        "total_covered_area": total_covered_area,
        "zones": room_zones
    }


def build_feature_index(force: bool = False) -> Dict[str, Any]:
    """
    Builds the feature index from corpus/plans.jsonl and writes retrieval/feature_index.json.
    Includes SHA-256 hash for cache verification.
    """
    current_hash = compute_plans_hash()

    if not force and os.path.exists(FEATURE_INDEX_PATH):
        try:
            with open(FEATURE_INDEX_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("plans_hash") == current_hash and "vectors" in cached:
                return cached
        except Exception:
            pass

    vectors = []
    with open(PLANS_JSONL_PATH, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            plan = json.loads(line)
            vec = build_plan_feature_vector(plan)
            vectors.append(vec)

    index_data = {
        "plans_hash": current_hash,
        "corpus_version": "2.0-real-cv",
        "total_plans": len(vectors),
        "usable_plans": sum(1 for v in vectors if v["layout_usable"]),
        "vectors": vectors
    }

    with open(FEATURE_INDEX_PATH, "w", encoding="utf-8") as f:
        json.dump(index_data, f, indent=2, ensure_ascii=False)

    print(f"[FeatureIndex] Built index with {len(vectors)} plans ({index_data['usable_plans']} usable) -> {FEATURE_INDEX_PATH}")
    return index_data


def load_feature_index() -> Dict[str, Any]:
    """Loads feature index, auto-rebuilding if hash does not match corpus/plans.jsonl."""
    current_hash = compute_plans_hash()
    if os.path.exists(FEATURE_INDEX_PATH):
        try:
            with open(FEATURE_INDEX_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if cached.get("plans_hash") == current_hash and "vectors" in cached:
                return cached
        except Exception:
            pass
    return build_feature_index(force=True)


if __name__ == "__main__":
    idx = build_feature_index(force=True)
    print(f"Index built with {idx['total_plans']} plans, hash: {idx['plans_hash'][:12]}...")
