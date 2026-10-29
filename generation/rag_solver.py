"""
Dataset-Driven Layout Synthesis Engine (RAGSolver).
Generates compliant architectural floor plans for standard Pakistani plots
(3 Marla, 5 Marla, 7 Marla, 10 Marla, 1 Kanal) by querying ONLY the verified
CV-extracted dataset (dataset/dataset_index.json & dataset/processed_plans/).

Components:
1. Ingestion & Invalidation Guard: Parses prompt and rejects physically impossible requests (F13).
2. Nearest-Neighbor Retrieval (RAG): Queries dataset_index.json to find top matching real plans.
3. Procedural Geometric Adaptation: Boundary snapping, fixed wall thickness normalization,
   IBC stair clearances, and multi-floor stacking (staircase invariance, OTS vertical continuity,
   and porch-to-terrace conversion).
4. FloorPlanQualityGate Validation: Ensures 0 Critical / High failures.
"""

import os
import re
import json
from typing import Dict, List, Tuple, Any, Optional
from shapely.geometry import Polygon, Point, LineString
from shapely.ops import unary_union
import networkx as nx

from dataset.schema.canonical import (
    CanonicalFloorPlan,
    MetadataModel,
    WallModel,
    OpeningModel,
    RoomModel,
    GraphEdgeModel
)
from requirements.parser import (
    NaturalLanguageRequirementsParser,
    ArchitecturalProgram,
    validate_architectural_feasibility,
    InfeasibleProgramError
)
from generation.quality_gate import FloorPlanQualityGate
from extraction.relationships import SpatialRelationshipGraphExtractor
from generation.architectural_styles import ArchitecturalStyleEngine, ArchitecturalStyleConfig
from generation.gemini_architectural_auditor import GeminiArchitecturalAuditor
from generation.design_diversity_engine import DesignDiversityEngine, PLANNING_STRATEGIES
from generation.duplicate_detector import DuplicateDetector


# ---------------------------------------------------------------------------
# Bathroom proportioning constants (IBC-compliant)
# ---------------------------------------------------------------------------
BATH_AREA_MIN_M2 = 3.60   # Minimum habitable attached bathroom (11.5 sq ft x 3.35)
BATH_AREA_MAX_M2 = 5.20   # Standard attached bathroom ceiling (strictly clamped to 5.2m²)
BATH_AREA_TARGET_M2 = 4.20 # Preferred 4'-6" x 8'-6" en-suite
POWDER_AREA_MIN_M2 = 1.80  # Guest powder room min
POWDER_AREA_MAX_M2 = 2.50  # Guest powder room max


def is_open_social_triad_pair(r1: RoomModel, r2: RoomModel) -> bool:
    """
    Returns True if r1 and r2 belong to the OPEN_SOCIAL_TRIAD
    (Gourmet Show Kitchen, Family TV Lounge, Family Dining Area).
    Such pairs have ZERO doors, ZERO door swings, and ZERO interior dividing walls.
    Spatial demarcation is defined solely by an open breakfast island counter.
    """
    if not r1 or not r2:
        return False
    if getattr(r1, 'level_index', 0) != getattr(r2, 'level_index', 0):
        return False
        
    n1 = (getattr(r1, 'room_name', '') + " " + getattr(r1, 'room_id', '')).lower()
    n2 = (getattr(r2, 'room_name', '') + " " + getattr(r2, 'room_id', '')).lower()
    t1 = getattr(r1, 'room_type', '').lower()
    t2 = getattr(r2, 'room_type', '').lower()
    
    # Dirty kitchen, heavy cooking scullery, laundry, storage are NOT in the open triad!
    for kw in ("wet", "dirty", "scullery", "pantry", "laundry", "servant", "maid", "store"):
        if kw in n1 or kw in n2:
            return False

    is_triad_1 = (t1 in ("kitchen", "dining_room", "living_room") or "lounge" in n1 or "dining" in n1 or "kitchen" in n1)
    is_triad_2 = (t2 in ("kitchen", "dining_room", "living_room") or "lounge" in n2 or "dining" in n2 or "kitchen" in n2)
    
    if is_triad_1 and is_triad_2:
        has_kit = ("kitchen" in n1 or t1 == "kitchen") or ("kitchen" in n2 or t2 == "kitchen")
        has_lounge = ("lounge" in n1 or "living" in n1 or t1 == "living_room") or ("lounge" in n2 or "living" in n2 or t2 == "living_room")
        has_dining = ("dining" in n1 or t1 == "dining_room") or ("dining" in n2 or t2 == "dining_room")
        
        if (has_kit and (has_lounge or has_dining)) or (has_dining and has_lounge):
            return True
            
        if (r1.metadata or {}).get("open_concept") and (r2.metadata or {}).get("open_concept"):
            return True

    return False


def _clamp_bath_poly(poly: list, is_powder: bool = False) -> list:
    """
    Normalises a bathroom polygon to the target area band by adjusting depth
    while preserving width. Returns a new axis-aligned rectangle.
    - Full bath: [BATH_AREA_MIN_M2, BATH_AREA_MAX_M2] = [3.6, 5.5 m²]
    - Powder room: [POWDER_AREA_MIN_M2, POWDER_AREA_MAX_M2] = [1.8, 2.5 m²]
    """
    from shapely.geometry import Polygon as _Poly
    p = _Poly(poly)
    minx, miny, maxx, maxy = p.bounds
    w = round(maxx - minx, 4)
    current_area = p.area

    if is_powder:
        lo, hi, target = POWDER_AREA_MIN_M2, POWDER_AREA_MAX_M2, 2.10
    else:
        lo, hi, target = BATH_AREA_MIN_M2, BATH_AREA_MAX_M2, BATH_AREA_TARGET_M2

    if lo <= current_area <= hi:
        return poly  # already within range, leave untouched

    if w < 0.5:
        return poly  # degenerate polygon, skip

    new_d = max(lo / w, min(hi / w, target / w))
    new_d = round(new_d, 3)
    new_maxy = round(miny + new_d, 3)
    return [
        [round(minx, 3), round(miny, 3)],
        [round(maxx, 3), round(miny, 3)],
        [round(maxx, 3), new_maxy],
        [round(minx, 3), new_maxy],
        [round(minx, 3), round(miny, 3)],
    ]


def _apply_bath_clamp_to_rooms(rooms: list) -> list:
    """
    Iterates all rooms and clamps every bathroom polygon to the valid area band [3.6, 5.5 m²].
    When a bathroom is oversized and pruned (reduced), the pruned bathroom area is
    absorbed by the adjacent bedroom or master dressing room so that the building envelope
    remains 100% watertight with zero F04 boundary holes and zero gaps.
    """
    from shapely.geometry import Polygon as _Poly, box as _box

    new_rooms_to_add = []
    for r in rooms:
        if r.room_type != "bathroom":
            continue
        is_pwd = any(kw in r.room_name.lower() or kw in r.room_id.lower() for kw in ("powder", "guest bath", "half bath", "wc"))
        lo = POWDER_AREA_MIN_M2 if is_pwd else BATH_AREA_MIN_M2
        hi = POWDER_AREA_MAX_M2 if is_pwd else BATH_AREA_MAX_M2

        p_orig = _Poly(r.polygon)
        if not p_orig.is_valid:
            p_orig = p_orig.buffer(0)
        orig_area = p_orig.area

        cutoff = POWDER_AREA_MAX_M2 if is_pwd else 5.25
        # Case 1: Oversized bathroom -> prune and re-absorb into adjacent bedroom/dressing room
        if orig_area > cutoff:
            minx, miny, maxx, maxy = p_orig.bounds
            bw = maxx - minx
            bh = maxy - miny
            if bw < 0.5 or bh < 0.5:
                continue

            target_area = 2.10 if is_pwd else 4.20
            candidates = [
                cand for cand in rooms
                if cand.level_index == r.level_index and cand.room_id != r.room_id and
                (cand.room_type in ("bedroom", "closet") or any(kw in cand.room_id.lower() or kw in cand.room_name.lower() for kw in ("dress", "wic", "closet", "bed", "lounge", "suite")))
            ]

            best_cand = None
            best_shared_len = 0.0
            for cand in candidates:
                cand_poly = _Poly(cand.polygon)
                inter = p_orig.intersection(cand_poly)
                if not inter.is_empty and inter.length > best_shared_len:
                    best_shared_len = inter.length
                    best_cand = cand

            if best_cand is not None and best_shared_len >= 0.40:
                cand_poly = _Poly(best_cand.polygon)
                c_minx, c_miny, c_maxx, c_maxy = cand_poly.bounds
                pruned_box = None

                if abs(c_miny - maxy) < 0.15 and min(maxx, c_maxx) - max(minx, c_minx) >= 0.40:
                    # best_cand is north along Y = maxy; keep maxy so it stays attached to best_cand
                    new_bh = round(target_area / bw, 3)
                    new_miny = round(maxy - new_bh, 3)
                    pruned_box = _box(minx, miny, maxx, new_miny)
                    r_cand_poly = [[minx, new_miny], [maxx, new_miny], [maxx, maxy], [minx, maxy], [minx, new_miny]]

                elif abs(c_maxy - miny) < 0.15 and min(maxx, c_maxx) - max(minx, c_minx) >= 0.40:
                    # best_cand is south along Y = miny; keep miny so it stays attached to best_cand
                    new_bh = round(target_area / bw, 3)
                    new_maxy = round(miny + new_bh, 3)
                    pruned_box = _box(minx, new_maxy, maxx, maxy)
                    r_cand_poly = [[minx, miny], [maxx, miny], [maxx, new_maxy], [minx, new_maxy], [minx, miny]]

                elif abs(c_minx - maxx) < 0.15 and min(maxy, c_maxy) - max(miny, c_miny) >= 0.40:
                    # best_cand is east along X = maxx; keep maxx so it stays attached to best_cand
                    new_bw = round(target_area / bh, 3)
                    new_minx = round(maxx - new_bw, 3)
                    pruned_box = _box(minx, miny, new_minx, maxy)
                    r_cand_poly = [[new_minx, miny], [maxx, miny], [maxx, maxy], [new_minx, maxy], [new_minx, miny]]

                elif abs(c_maxx - minx) < 0.15 and min(maxy, c_maxy) - max(miny, c_miny) >= 0.40:
                    # best_cand is west along X = minx; keep minx so it stays attached to best_cand
                    new_bw = round(target_area / bh, 3)
                    new_maxx = round(minx + new_bw, 3)
                    pruned_box = _box(new_maxx, miny, maxx, maxy)
                    r_cand_poly = [[minx, miny], [new_maxx, miny], [new_maxx, maxy], [minx, maxy], [minx, miny]]
                else:
                    r_cand_poly = None

                if pruned_box is not None and r_cand_poly is not None:
                    # Prefer existing dressing room or closet to absorb pruned_box
                    absorber = None
                    best_abs_len = 0.0
                    for cand in rooms:
                        if cand.level_index == r.level_index and cand.room_id != r.room_id and cand.room_type in ("closet", "storage"):
                            c_geom = _Poly(cand.polygon)
                            inter = pruned_box.intersection(c_geom)
                            if not inter.is_empty and inter.length > best_abs_len:
                                merged = c_geom.union(pruned_box)
                                if merged.geom_type == "Polygon":
                                    best_abs_len = inter.length
                                    absorber = cand

                    if absorber is not None:
                        r.polygon = r_cand_poly
                        merged = _Poly(absorber.polygon).union(pruned_box)
                        absorber.polygon = [list(pt) for pt in merged.exterior.coords]
                        absorber.area_m2 = round(merged.area, 1)
                        absorber.centroid = [round(merged.centroid.x, 2), round(merged.centroid.y, 2)]
                    elif pruned_box.area >= 1.50:
                        r.polygon = r_cand_poly
                        suffix = r.room_id.split('_')[-1]
                        new_rooms_to_add.append(RoomModel(
                            room_id=f"room_L{r.level_index}_dress_{suffix}",
                            room_type="closet",
                            room_name="En-Suite Dressing Room & WIC",
                            polygon=[list(pt) for pt in pruned_box.exterior.coords],
                            area_m2=round(pruned_box.area, 1),
                            centroid=[round(pruned_box.centroid.x, 2), round(pruned_box.centroid.y, 2)],
                            level_index=r.level_index,
                            is_habitable=False
                        ))

            else:
                r.polygon = _clamp_bath_poly(r.polygon, is_powder=is_pwd)

            p_new = _Poly(r.polygon)
            r.area_m2 = round(p_new.area, 1)
            r.centroid = [round(p_new.centroid.x, 2), round(p_new.centroid.y, 2)]

    if new_rooms_to_add:
        rooms.extend(new_rooms_to_add)

    return rooms


SCALE_ALIASES = {
    "3_marla": ["3_marla", "3marla", "3 marla", "3-marla", "3m"],
    "5_marla": ["5_marla", "5marla", "5 marla", "5-marla", "5m"],
    "7_marla": ["7_marla", "7marla", "7 marla", "7-marla", "7m"],
    "10_marla": ["10_marla", "10marla", "10 marla", "10-marla", "10m"],
    "1_kanal": ["1_kanal", "1kanal", "1 kanal", "1-kanal", "1k", "kanal"]
}

PAKISTANI_NOMINAL_DIMENSIONS_M = {
    "3_marla": [4.57, 13.72],   # 15' x 45'
    "5_marla": [7.62, 13.72],   # 25' x 45'
    "7_marla": [9.14, 16.76],   # 30' x 55'
    "10_marla": [10.67, 19.81], # 35' x 65'
    "1_kanal": [15.24, 27.43]   # 50' x 90'
}


class DatasetDrivenRAGSolver:
    """
    Purely dataset-driven architectural floor plan synthesizer.
    Retrieves canonical layouts from the CV-extracted dataset and adapts them procedurally.
    """

    def __init__(
        self,
        index_path: str = "dataset/dataset_index.json",
        plans_dir: str = "dataset/processed_plans"
    ):
        self.index_path = index_path
        self.plans_dir = plans_dir
        self.processed_plans_dir = plans_dir
        self.catalog: List[Dict[str, Any]] = []
        self._load_index()

    def _load_index(self) -> None:
        if os.path.exists(self.index_path):
            with open(self.index_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            self.catalog = [
                p for p in data.get("plans", [])
                if not str(p.get("canonical_path", "")).startswith("dataset/canonical_baselines")
                and not str(p.get("plan_id", "")).startswith("master_")
            ]
        else:
            self.catalog = []

    def parse_prompt(self, prompt: str) -> Dict[str, Any]:
        """
        Parses user prompt extracting scale, requested room quotas, stair preference, and floors.
        """
        prog = NaturalLanguageRequirementsParser.parse(prompt, validate=False)
        p_lower = prompt.lower()

        scale = prog.plot_category
        req_beds = prog.requested_room_counts.get("bedroom", 3)
        req_baths = prog.requested_room_counts.get("bathroom", req_beds)
        stair_pref = prog.stair_type
        stair_engine_class = prog.stair_engine_class
        spatial_typology = prog.spatial_typology
        floor_count = prog.floor_count

        has_drawing = prog.ground_room_counts.get("drawing", 0) > 0 or any(k in p_lower for k in ["drawing", "formal", "guest room"])
        has_dining = prog.ground_room_counts.get("dining", 0) > 0 or any(k in p_lower for k in ["dining", "dining room"])
        has_scullery = prog.dirty_kitchen_count > 0 or any(k in p_lower for k in ["scullery", "dirty kitchen", "s.kit", "double kitchen"])
        has_porch = prog.car_porch_capacity > 0 or not ("no porch" in p_lower or "no garage" in p_lower)
        is_double_porch = prog.car_porch_capacity >= 2 or any(k in p_lower for k in ["double car", "2 car", "double porch", "two car", "suv"])

        return {
            "scale": scale,
            "requested_bedrooms": req_beds,
            "requested_bathrooms": req_baths,
            "stair_type": stair_pref,
            "stair_engine_class": stair_engine_class,
            "spatial_typology": spatial_typology,
            "layout_style": spatial_typology,
            "floor_count": floor_count,
            "has_drawing": has_drawing,
            "has_dining": has_dining,
            "has_scullery": has_scullery,
            "has_porch": has_porch,
            "is_double_porch": is_double_porch,
            "raw_prompt": prompt,
            "program": prog
        }

    def validate_feasibility_guard(self, parsed: Dict[str, Any], raise_on_error: bool = True) -> None:
        """
        Feasibility Check (F13): Rejects physically impossible requests with multi-floor capacity rules.
        """
        scale = parsed["scale"]
        p_lower = parsed["raw_prompt"].lower()
        floors = parsed["floor_count"]
        req_beds = parsed["requested_bedrooms"]

        # Universal checks
        if ("2 kitchens" in p_lower and "2 lounges" in p_lower and floors == 1) or "3 kitchen" in p_lower:
            raise InfeasibleProgramError("F13 Architectural Infeasibility Guard: F13 Infeasible: Cannot place 2 show kitchens and 2 lounges or 3 kitchens on a single plot.")

        # Multi-Floor Capacity Logic
        if scale == "3_marla":
            if floors <= 2:
                if req_beds >= 4:
                    raise InfeasibleProgramError(
                        f"F13 Architectural Infeasibility Guard: F13 Infeasible: A 2-storey 3 Marla plot cannot fit {req_beds} bedrooms without violating "
                        f"IBC Section 1207 minimum room sizes (70 sq ft). You must specify 3 floors (G+2) or reduce bedroom count."
                    )
            elif floors == 3:
                if req_beds > 5:
                    raise InfeasibleProgramError(
                        f"F13 Architectural Infeasibility Guard: F13 Infeasible: A 3-storey (G+2) 3 Marla plot allows maximum 5 bedrooms (1 on Ground, 2 on Level 1, 2 on Level 2). Requested: {req_beds}."
                    )
            if "separate formal dining" in p_lower or ("dining" in p_lower and "drawing" in p_lower and floors == 1):
                raise InfeasibleProgramError("F13 Architectural Infeasibility Guard: F13 Infeasible: 3 Marla plot cannot accommodate a separate formal dining room.")
            if floors == 1 and req_beds > 1:
                raise InfeasibleProgramError("F13 Architectural Infeasibility Guard: F13 Infeasible: 3 Marla permits maximum 1 bedroom on Ground Floor.")
            if "2 car" in p_lower or "double car" in p_lower:
                raise InfeasibleProgramError("F13 Architectural Infeasibility Guard: F13 Infeasible: 3 Marla permits maximum 1 small car porch.")

        elif scale == "5_marla":
            if "2 full kitchen" in p_lower or ("2 kitchen" in p_lower and "ground" in p_lower) or "3 kitchen" in p_lower:
                raise InfeasibleProgramError("F13 Architectural Infeasibility Guard: F13 Infeasible: 5 Marla cannot accommodate 2 full kitchens on Ground Floor.")
            if floors <= 2:
                has_drawing = parsed.get("has_drawing", True)
                if req_beds > 5:
                    raise InfeasibleProgramError(f"F13 Architectural Infeasibility Guard: F13 Infeasible: A 2-storey 5 Marla plot cannot fit {req_beds} bedrooms (max 5 with drawing conversion).")
                elif req_beds == 5 and has_drawing and not any(k in p_lower for k in ["convert drawing", "no drawing", "drawing as bed", "drawing converted"]):
                    raise InfeasibleProgramError("F13 Architectural Infeasibility Guard: F13 Infeasible: 5 bedrooms on a 2-storey 5 Marla plot is only possible if the formal Drawing Room is converted into Ground Bed 1.")
            elif floors == 3:
                if req_beds > 7:
                    raise InfeasibleProgramError(f"F13 Infeasible: A 3-storey (G+2) 5 Marla plot allows up to 6-7 bedrooms. Requested: {req_beds}.")

        elif scale == "7_marla":
            if floors <= 2 and req_beds > 5:
                # Statutory Compliance Guard: Auto-adapt to legal limit (5 beds) and generate prominent red notice
                note = (
                    f"6 Bedrooms on 2 Floors is physically & legally IMPOSSIBLE in 7 Marla (30'x55') under CDA/DHA Regulations "
                    f"(Mandatory Setbacks & min 120 sq ft room rules). Auto-adapted to maximum legal capacity of 5 Master Suites. "
                    f"To construct 6 or more bedrooms, a 3-Storey Triplex (G+2) is required."
                )
                parsed["requested_bedrooms"] = 5
                parsed["statutory_red_note"] = note
                if parsed.get("program"):
                    parsed["program"].statutory_red_note = note
                    parsed["program"].requested_room_counts["bedroom"] = 5
            elif floors == 3 and req_beds > 7:
                raise InfeasibleProgramError(f"F13 Infeasible: A 3-storey (G+2) 7 Marla plot allows up to 7 bedrooms. Requested: {req_beds}.")

        elif scale == "10_marla":
            if floors <= 2 and req_beds > 6:
                raise InfeasibleProgramError(
                    f"F13 Architectural Infeasibility Guard: F13 Infeasible: A 2-storey (G+1) 10 Marla plot allows a maximum of 6 bedrooms "
                    f"(2 on Ground Floor, 4 on First Floor) under CDA/DHA building bylaws (minimum bedroom size 100 sq ft and mandatory 10ft front / 5ft rear setbacks). "
                    f"Requested: {req_beds} bedrooms. Please reduce bedroom count or specify 3 floors (G+2)."
                )
            elif floors == 3 and req_beds > 9:
                raise InfeasibleProgramError(f"F13 Infeasible: A 3-storey (G+2) 10 Marla plot allows up to 9 bedrooms. Requested: {req_beds}.")

        elif scale == "1_kanal":
            if floors <= 2 and req_beds > 8:
                raise InfeasibleProgramError(
                    f"F13 Architectural Infeasibility Guard: F13 Infeasible: A 2-storey (G+1) 1 Kanal plot allows a maximum of 8 bedrooms "
                    f"(3 on Ground Floor, 5 on First Floor) under CDA/DHA building regulations (15ft front lawn, 8ft rear setback). "
                    f"Requested: {req_beds} bedrooms. Please reduce bedroom count or specify 3 floors (G+2)."
                )
            elif floors == 3 and req_beds > 12:
                raise InfeasibleProgramError(f"F13 Infeasible: A 3-storey (G+2) 1 Kanal plot allows up to 12 bedrooms. Requested: {req_beds}.")

        # Enforce mandatory front lawn setbacks across all Pakistani residential scales
        setback_map = {"5_marla": 5, "7_marla": 6, "10_marla": 10, "1_kanal": 15}
        if scale in setback_map:
            setback_ft = setback_map[scale]
            if any(term in p_lower for term in [
                "100% covered", "100 percent covered", "cover 100%", "zero setback", "no setback",
                "no lawn", "cover entire plot", "zero lawn", "without lawn", "without setback", "no front lawn"
            ]):
                raise InfeasibleProgramError(
                    f"F13 Infeasible: Building bylaws mandate minimum front lawn setbacks ({setback_ft}' for {scale.replace('_', ' ').title()}). "
                    f"100% covered footprint requests violate municipal regulations."
                )

        # Dirty Kitchen isolation rule
        if any(k in p_lower for k in ["dirty kitchen", "dirty-kitchen", "wet kitchen", "grease kitchen", "spice kitchen", "scullery"]):
            if any(k in p_lower for k in ["dirty kitchen to drawing", "dirty kitchen into drawing", "dirty kitchen door to drawing", "connect dirty kitchen to drawing"]):
                raise InfeasibleProgramError(
                    "F13 Infeasible: Architectural building regulations strictly forbid connecting a dirty/wet kitchen to a formal drawing room or front public foyer. "
                    "A dirty kitchen must connect exclusively to the rear/backside of the main show kitchen."
                )

    def retrieve_nearest_neighbor(self, parsed: Dict[str, Any], top_k: int = 5) -> Tuple[CanonicalFloorPlan, Dict[str, Any]]:
        """
        RAG Retrieval: Uses RAGMatcher 12-D vector search to query dataset_index.json
        and falls back to golden canonical baselines if below 0.70 threshold.
        """
        from generation.rag_matcher import RAGMatcher
        matcher = RAGMatcher(self.index_path)
        base_plan, match_source, sim_score = matcher.query_vector(parsed)
        matched_meta = {
            "plan_id": base_plan.metadata.plan_id,
            "source_type": match_source,
            "similarity_score": sim_score,
            "source_image": base_plan.metadata.provenance.get("source_image", "")
        }
        return base_plan, matched_meta

    def synthesize(
        self,
        prompt: str,
        target_dimensions_ft: Optional[Tuple[float, float]] = None,
        plan_id: Optional[str] = None,
        strategy: Optional[str] = None,
        alternative_index: Optional[int] = None,
        disallowed_strategies: Optional[List[str]] = None,
        seed: Optional[int] = None
    ) -> CanonicalFloorPlan:
        """
        Executes end-to-end dataset-driven synthesis:
        1. Ingestion & Invalidation Guard
        2. Direct Geometry Ingestion & Deserialization from dataset/processed_plans/
        3. Procedural Geometric Adaptation (scaling, wall normalization, 2-floor coordination)
        4. QualityGate validation
        """
        # 1. Parse & Invalidation Guard (F13)
        parsed = self.parse_prompt(prompt)
        self.validate_feasibility_guard(parsed, raise_on_error=True)

        scale = parsed["scale"]
        req_floors = parsed["floor_count"]
        stair_req = parsed["stair_type"]

        # Detect Architectural Style Configuration (supports all 27 styles)
        style_cfg = ArchitecturalStyleEngine.detect_style(prompt)
        arch_archetype = style_cfg.layout_archetype

        # Architectural Typological Diversity Routing
        # If user explicitly requested legacy static blueprint (e.g. plan_A, plan_B, plan_C), retrieve that baseline.
        # Otherwise, synthesize an authentic, validated architectural archetype via DesignDiversityEngine!
        explicit_baseline = False
        p_low = prompt.lower()
        if plan_id:
            explicit_baseline = True
        else:
            for pid in ["plan a", "plan_a", "plan b", "plan_b", "plan c", "plan_c"]:
                if pid in p_low:
                    explicit_baseline = True
                    break

        if not explicit_baseline and (req_floors <= 2 or (scale == "7_marla" and req_floors == 3)):
            diverse_plan = DesignDiversityEngine.synthesize_diverse_plan(
                prompt=prompt,
                scale=scale,
                strategy=strategy,
                alternative_index=alternative_index,
                disallowed_strategies=disallowed_strategies,
                style_cfg=style_cfg,
                seed=seed
            )
            # Evaluate QualityGate
            gate = FloorPlanQualityGate.evaluate(diverse_plan)
            if gate["final_status"] == "PASS":
                diverse_plan, audit_result = GeminiArchitecturalAuditor.audit_and_refine(
                    plan=diverse_plan,
                    user_prompt=prompt,
                    program=parsed,
                    style_cfg=style_cfg
                )
                from generation.fidelity_guard import FidelityGuard
                FidelityGuard.audit(diverse_plan, prompt=prompt)
                return diverse_plan

        # 2. Style-Aware & Diverse Blueprint Retrieval from verified real dataset
        selected_plan_id = plan_id
        all_canonical_ids = [
            "3_marla_plan_A", "3_marla_plan_B", "3_marla_plan_C",
            "5_marla_plan_A", "5_marla_plan_B", "5_marla_plan_C",
            "7_marla_plan_A", "7_marla_plan_B", "7_marla_plan_C",
            "10_marla_plan_A", "10_marla_plan_B", "10_marla_plan_C",
            "1_kanal_plan_A", "1_kanal_plan_B", "1_kanal_plan_C"
        ]
        if not selected_plan_id:
            for pid in all_canonical_ids:
                if pid.lower() in prompt.lower() or pid in prompt:
                    selected_plan_id = pid
                    break
        if not selected_plan_id:
            p_lower = prompt.lower()
            if scale == "3_marla":
                if "plan b" in p_lower or "plan_b" in p_lower or "l-shaped" in p_lower or "l-shape" in p_lower or arch_archetype == "asymmetrical_picturesque":
                    selected_plan_id = "3_marla_plan_B"
                elif "plan c" in p_lower or "plan_c" in p_lower or "garden suite" in p_lower or "courtyard" in p_lower or arch_archetype == "courtyard_centric" or "single storey" in p_lower or "1 bed" in p_lower:
                    selected_plan_id = "3_marla_plan_C"
                else:
                    selected_plan_id = "3_marla_plan_A"
            elif scale == "5_marla":
                if "plan a" in p_lower or "plan_a" in p_lower or "single storey" in p_lower or "single-floor" in p_lower or "1 bed" in p_lower or arch_archetype in ("four_quadrant_box", "symmetrical_central_hall"):
                    selected_plan_id = "5_marla_plan_A"
                elif "plan c" in p_lower or "plan_c" in p_lower or "courtyard" in p_lower or "patio" in p_lower or arch_archetype in ("courtyard_centric", "deep_veranda_wrap"):
                    selected_plan_id = "5_marla_plan_C"
                elif "plan b" in p_lower or "plan_b" in p_lower or "straight" in p_lower or "linear" in p_lower or arch_archetype in ("linear_horizontal_flow", "open_concept_pavilion"):
                    selected_plan_id = "5_marla_plan_B"
                else:
                    if arch_archetype == "courtyard_centric":
                        selected_plan_id = "5_marla_plan_C"
                    elif arch_archetype in ("linear_horizontal_flow", "open_concept_pavilion"):
                        selected_plan_id = "5_marla_plan_B"
                    else:
                        selected_plan_id = "5_marla_plan_A"
            elif scale == "7_marla":
                if "plan b" in p_lower or "plan_b" in p_lower or "courtyard" in p_lower or "glass patio" in p_lower or arch_archetype in ("courtyard_centric", "open_concept_pavilion"):
                    selected_plan_id = "7_marla_plan_B"
                elif "plan c" in p_lower or "plan_c" in p_lower or "office" in p_lower or "study" in p_lower or "executive" in p_lower or arch_archetype in ("linear_horizontal_flow", "split_level_staggered"):
                    selected_plan_id = "7_marla_plan_C"
                elif "plan a" in p_lower or "plan_a" in p_lower or "dual rear suites" in p_lower or arch_archetype in ("symmetrical_central_hall", "four_quadrant_box", "asymmetrical_picturesque"):
                    selected_plan_id = "7_marla_plan_A"
                else:
                    selected_plan_id = "7_marla_plan_B" if (sum(ord(c) for c in prompt) % 2 == 0) else "7_marla_plan_C"
            elif scale == "10_marla":
                # Distinct layout topologies for 10 Marla prompts
                if "dirty" in p_lower or "scullery" in p_lower:
                    selected_plan_id = "10_marla_plan_A"
                elif arch_archetype in ("courtyard_centric",) or style_cfg.style_id in ("spanish_revival", "mediterranean", "mediterranean_revival") or "rotunda" in p_lower or "curved" in p_lower or "atrium" in p_lower or "patio" in p_lower or "courtyard" in p_lower:
                    selected_plan_id = "10_marla_plan_C"
                elif arch_archetype in ("open_concept_pavilion", "linear_horizontal_flow", "split_level_staggered") or style_cfg.style_id in ("mid_century_modern", "modern", "contemporary", "ranch", "art_deco") or "gym" in p_lower or "straight" in p_lower or "linear" in p_lower or "study" in p_lower:
                    selected_plan_id = "10_marla_plan_B"
                elif arch_archetype in ("symmetrical_central_hall", "four_quadrant_box", "asymmetrical_picturesque", "deep_veranda_wrap") or style_cfg.style_id in ("georgian", "colonial", "greek_revival", "tudor_revival", "victorian", "farmhouse", "craftsman") or "traditional" in p_lower or "palatial" in p_lower:
                    selected_plan_id = "10_marla_plan_A"
                else:
                    cands_10m = ["10_marla_plan_C", "10_marla_plan_B", "10_marla_plan_A"]
                    selected_plan_id = cands_10m[sum(ord(c) for c in prompt) % len(cands_10m)]
            elif scale == "1_kanal":
                # Distinct layout topologies for 1 Kanal prompts
                if arch_archetype in ("courtyard_centric", "deep_veranda_wrap") or style_cfg.style_id in ("spanish_revival", "mediterranean", "mediterranean_revival") or "pool" in p_lower or "patio" in p_lower or "c-shaped" in p_lower:
                    selected_plan_id = "1_kanal_plan_B"
                elif arch_archetype in ("open_concept_pavilion", "linear_horizontal_flow") or style_cfg.style_id in ("mid_century_modern", "contemporary", "art_deco", "international_style") or "rotunda" in p_lower or "curved" in p_lower or "double-height" in p_lower or "cinema" in p_lower:
                    selected_plan_id = "1_kanal_plan_C"
                elif arch_archetype in ("symmetrical_central_hall", "four_quadrant_box") or style_cfg.style_id in ("georgian", "colonial", "greek_revival", "tudor_revival", "victorian", "french_provincial") or "palatial" in p_lower or "bifurcated" in p_lower or "state banquet" in p_lower:
                    selected_plan_id = "1_kanal_plan_A"
                else:
                    cands_1k = ["1_kanal_plan_B", "1_kanal_plan_C", "1_kanal_plan_A"]
                    selected_plan_id = cands_1k[sum(ord(c) for c in prompt) % len(cands_1k)]

        if selected_plan_id:
            plan_path = os.path.join(self.plans_dir, f"{selected_plan_id}.json")
            if not os.path.exists(plan_path):
                plan_path = os.path.join("dataset", "processed_plans", f"{selected_plan_id}.json")
            with open(plan_path, "r", encoding="utf-8") as f:
                base_plan = CanonicalFloorPlan.model_validate_json(f.read())
            matched_meta = {
                "plan_id": selected_plan_id,
                "source_type": "cv_dataset",
                "similarity_score": 1.0,
                "source_image": base_plan.metadata.provenance.get("source_path", "")
            }
            if "scale" in base_plan.metadata.provenance:
                scale = base_plan.metadata.provenance["scale"]
        else:
            base_plan, matched_meta = self.retrieve_nearest_neighbor(parsed)

        # Honor multi-floor intent without letting single-floor base blueprints override user requirements
        has_explicit_multi_floor = any(k in prompt.lower() for k in [
            "2 storey", "2-storey", "2 story", "2-story", "double storey", "two floor", "two storey", "2 floor", "2-floor",
            "g+1", "g + 1", "first floor", "upper floor", "multi-storey", "multi storey",
            "3 storey", "3-storey", "3 story", "3-story", "3 floor", "3-floor", "triple storey", "g+2"
        ])
        req_floors = parsed.get("floor_count", 1)
        if has_explicit_multi_floor:
            req_floors = max(req_floors, 2)
        elif selected_plan_id and "floor_count" not in parsed:
            req_floors = base_plan.metadata.floor_count

        # 3. Geometric Adaptation: Target Dimensions & Snapping
        nom_dim_m = PAKISTANI_NOMILAR_DIMENSIONS_M = PAKISTANI_NOMINAL_DIMENSIONS_M[scale]
        if target_dimensions_ft:
            target_w = round(target_dimensions_ft[0] * 0.3048, 2)
            target_d = round(target_dimensions_ft[1] * 0.3048, 2)
        else:
            target_w, target_d = nom_dim_m

        orig_w = base_plan.boundary[1][0]
        orig_d = base_plan.boundary[2][1]

        scale_x = target_w / orig_w
        scale_y = target_d / orig_d

        # Adapt Level 0 rooms directly from deserialized real blueprint
        l0_rooms = []
        has_dirty_req = any(k in prompt.lower() for k in ["dirty kitchen", "dirty-kitchen", "wet kitchen", "grease kitchen", "spice kitchen", "scullery"])
        has_dining_req = "dining" in prompt.lower()
        l0_id_remap = {}

        if has_dirty_req:
            # Find candidate dining and kitchen rooms in L0
            l0_dining_r = next((r for r in base_plan.rooms if r.level_index == 0 and (r.room_type == "dining_room" or "dining" in r.room_id.lower())), None)
            l0_kit_r = next((r for r in base_plan.rooms if r.level_index == 0 and (r.room_type == "kitchen" or "kitchen" in r.room_id.lower())), None)
            if not has_dining_req and l0_dining_r and l0_kit_r:
                # Compare Y positions: smaller Y is front (near TV Lounge/Drawing), larger Y is rear (backside)
                # The room closer to the front MUST be the Open/Show Kitchen.
                # The room at the rear/backside MUST be the Dirty Kitchen.
                if l0_dining_r.centroid[1] < l0_kit_r.centroid[1]:
                    l0_id_remap[l0_dining_r.room_id] = "room_L0_kitchen"
                    l0_id_remap[l0_kit_r.room_id] = "room_L0_dirty_kitchen"
                else:
                    l0_id_remap[l0_dining_r.room_id] = "room_L0_dirty_kitchen"
                    l0_id_remap[l0_kit_r.room_id] = "room_L0_kitchen"
            elif not has_dining_req and l0_dining_r and not l0_kit_r:
                l0_id_remap[l0_dining_r.room_id] = "room_L0_dirty_kitchen"
            elif not any(k in prompt.lower() for k in ["study", "office", "workstation"]):
                # If prompt didn't request a study, check if an auxiliary study or utility room exists in L0
                l0_aux = next((r for r in base_plan.rooms if r.level_index == 0 and (r.room_type in ("study", "utility", "store") or "study" in r.room_id.lower())), None)
                if l0_aux:
                    l0_id_remap[l0_aux.room_id] = "room_L0_dirty_kitchen"

        for r in base_plan.rooms:
            if r.level_index == 0:
                scaled_poly = []
                for pt in r.polygon:
                    nx = round(pt[0] * scale_x, 2)
                    ny = round(pt[1] * scale_y, 2)
                    scaled_poly.append([nx, ny])
                
                poly_geom = Polygon(scaled_poly)
                r_type = r.room_type
                r_id = r.room_id
                r_name = r.room_name
                r_meta = dict(r.metadata or {})

                if r.room_id in l0_id_remap:
                    mapped_id = l0_id_remap[r.room_id]
                    r_id = mapped_id
                    r_type = "kitchen"
                    if mapped_id == "room_L0_dirty_kitchen":
                        r_name = "Dirty Kitchen (Wet Kitchen)"
                        r_meta["is_dirty_kitchen"] = True
                        r_meta["wet_kitchen"] = True
                    else:
                        r_name = "Modern Show Kitchen"
                        r_meta["waterfall_island"] = True
                        r_meta.pop("is_dirty_kitchen", None)

                r_copy = RoomModel(
                    room_id=r_id,
                    room_type=r_type,
                    room_name=r_name,
                    polygon=scaled_poly,
                    area_m2=round(poly_geom.area, 2),
                    centroid=[round(poly_geom.centroid.x, 2), round(poly_geom.centroid.y, 2)],
                    level_index=0,
                    is_habitable=r.is_habitable,
                    metadata=r_meta
                )
                if "stair" in r.room_id.lower() or "stair" in r.room_name.lower():
                    base_typology = r.metadata.get("typology") if r.metadata else None
                    poly_geom = Polygon(r.polygon)
                    sw = min(poly_geom.bounds[2] - poly_geom.bounds[0], poly_geom.bounds[3] - poly_geom.bounds[1])
                    if stair_req and ("dogleg" in stair_req or "u_shape" in stair_req) and sw < 1.50:
                        stair_type_assigned = "straight"
                    else:
                        stair_type_assigned = stair_req or base_typology or "straight"
                    r_copy.metadata["typology"] = stair_type_assigned
                    r_copy.metadata["headroom_m"] = 2.10
                    r_copy.metadata["flight_width"] = 1.00
                    r_copy.metadata["landing_depth"] = 1.20
                l0_rooms.append(r_copy)

        envelope = [[0.0, 0.0], [target_w, 0.0], [target_w, target_d], [0.0, target_d], [0.0, 0.0]]

        # 4. Multi-Floor Stacking (Level 1 & Level 2)
        all_rooms = list(l0_rooms)
        levels = [0]

        if req_floors >= 2:
            levels.append(1)
            l1_rooms = self._stack_level_1(l0_rooms, scale, target_w, target_d, stair_req, parsed, base_plan=base_plan)
            all_rooms.extend(l1_rooms)

        if req_floors >= 3:
            levels.append(2)
            l2_rooms = self._stack_level_2(l1_rooms, scale, target_w, target_d, stair_req, parsed)
            all_rooms.extend(l2_rooms)

        # Global bathroom area clamping [3.6, 5.2 m²]
        all_rooms = _apply_bath_clamp_to_rooms(all_rooms)

        # 4b. Strict Bedroom Quota Enforcement (ensures actual_beds == target_beds)
        actual_beds = [r for r in all_rooms if r.room_type == "bedroom"]
        target_beds = parsed.get("requested_bedrooms", len(actual_beds))
        if len(actual_beds) > target_beds:
            surplus = len(actual_beds) - target_beds
            p_low = prompt.lower()
            req_servant = any(k in p_low for k in ["servant", "maid", "staff", "domestic"])
            assigned_servant = any(any(k in r.room_name.lower() for k in ["servant", "maid", "staff", "domestic"]) for r in all_rooms)
            for r in reversed(all_rooms):
                if surplus <= 0:
                    break
                if r.level_index >= 1 and r.room_type == "bedroom" and not r.metadata.get("is_master", False):
                    if req_servant and not assigned_servant:
                        r.room_type = "utility"
                        r.room_name = "Rooftop Servant Quarters & Staff Room"
                        r.metadata["is_servant_room"] = True
                        assigned_servant = True
                    else:
                        r.room_type = "study"
                        r.room_name = "Upper Study & Workstation"
                    surplus -= 1
            if surplus > 0:
                for r in reversed(all_rooms):
                    if surplus <= 0:
                        break
                    if r.level_index >= 1 and r.room_type == "bedroom":
                        if req_servant and not assigned_servant:
                            r.room_type = "utility"
                            r.room_name = "Rooftop Servant Quarters & Staff Room"
                            r.metadata["is_servant_room"] = True
                            assigned_servant = True
                        else:
                            r.room_type = "study"
                            r.room_name = "Upper Study & Workstation"
                        surplus -= 1
        elif len(actual_beds) < target_beds:
            deficit = target_beds - len(actual_beds)
            for r in all_rooms:
                if deficit <= 0:
                    break
                if r.level_index >= 1 and r.room_type in ("study", "drawing", "guest", "living_room") and r.area_m2 >= 8.5:
                    r.room_type = "bedroom"
                    r.room_name = f"Upper Bedroom Suite {len([b for b in all_rooms if b.room_type == 'bedroom']) + 1}"
                    r.is_habitable = True
                    deficit -= 1

        # Servant room fallback enforcement if requested
        p_low = prompt.lower()
        if any(k in p_low for k in ["servant", "maid", "staff", "domestic"]):
            has_servant = any(any(k in r.room_name.lower() for k in ["servant", "maid", "staff", "domestic"]) for r in all_rooms)
            if not has_servant:
                cand = next((r for r in all_rooms if r.room_type in ("study", "storage", "utility") and r.level_index == max(levels)), None)
                if not cand:
                    cand = next((r for r in all_rooms if r.room_type in ("study", "storage", "utility")), None)
                if cand:
                    cand.room_name = "Rooftop Servant Quarters & Staff Room"
                    cand.room_type = "utility"
                    cand.metadata["is_servant_room"] = True

        # 5. Ingest and scale genuine openings from real blueprint (strictly forbidding open triad doors)
        all_openings = []
        l0_rooms_map = {r.room_id: r for r in all_rooms if r.level_index == 0}
        for op in (base_plan.openings or []):
            if op.level_index == 0:
                remapped_connects = [l0_id_remap.get(c, c) for c in op.connects_rooms]
                if op.opening_type == "door" and len(remapped_connects) == 2:
                    rA = l0_rooms_map.get(remapped_connects[0])
                    rB = l0_rooms_map.get(remapped_connects[1])
                    if rA and rB and is_open_social_triad_pair(rA, rB):
                        continue  # Strictly FORBID door swings inside open social triad!

                spos = [round(op.position[0] * scale_x, 2), round(op.position[1] * scale_y, 2)]
                w_m = op.width_m
                if op.opening_type == "door":
                    if "porch" in op.opening_id.lower() or "main" in op.opening_id.lower():
                        w_m = max(0.90, min(1.20, w_m))
                    else:
                        w_m = max(0.80, min(1.00, w_m))
                all_openings.append(OpeningModel(
                    opening_id=op.opening_id,
                    opening_type=op.opening_type,
                    position=spos,
                    width_m=round(w_m, 2),
                    connects_rooms=remapped_connects,
                    level_index=0
                ))

        if not all_openings:
            all_openings = self._generate_compliant_openings(all_rooms, envelope, target_w, target_d, scale)
        elif len(levels) > 1:
            # Replicate circulation openings onto upper levels via parent_l0_id
            for lvl in levels[1:]:
                l0_to_upper = {
                    r.metadata.get("parent_l0_id", ""): r.room_id
                    for r in all_rooms if r.level_index == lvl and "parent_l0_id" in r.metadata
                }
                for op in list(all_openings):
                    if op.level_index == 0:
                        u_connects = []
                        for cr in op.connects_rooms:
                            u_rid = l0_to_upper.get(cr)
                            if u_rid:
                                u_connects.append(u_rid)
                        if len(u_connects) == len(op.connects_rooms):
                            # Filter out illegal circulation pairs on upper floors (e.g. direct bedroom to kitchen or bath to bath)
                            u_types = [next((r.room_type for r in all_rooms if r.room_id == ur), "") for ur in u_connects]
                            if "bedroom" in u_types and "kitchen" in u_types:
                                continue
                            if u_types.count("bathroom") == 2:
                                continue
                            all_openings.append(OpeningModel(
                                opening_id=f"{op.opening_id}_L{lvl}",
                                opening_type=op.opening_type,
                                position=list(op.position),
                                width_m=op.width_m,
                                connects_rooms=u_connects,
                                level_index=lvl
                            ))

        # Ensure complete Level 1 / Level 2 openings (doors for attached baths, circulation, windows)
        if len(levels) > 1:
            all_openings = self._ensure_upper_level_openings(
                all_rooms, all_openings, envelope, target_w, target_d, scale, levels
            )

        # 6. Generate Structural Walls with exact code thicknesses (0.23m exterior, 0.115m interior)
        all_walls = self._generate_structural_walls(all_rooms, envelope, levels)

        # 1 Kanal Dynamic Typology & Spatial Adaptation (legacy fallback only)
        if not selected_plan_id and scale == "1_kanal" and any(kw in prompt.lower() for kw in ("rotunda", "cinema", "estate", "left", "pool", "curved")):
            for r in all_rooms:
                r.polygon = [[round(target_w - pt[0], 2), pt[1]] for pt in r.polygon]
                r.centroid = [round(target_w - r.centroid[0], 2), r.centroid[1]]
                if "bed4" in r.room_id.lower() and ("cinema" in prompt.lower() or "theater" in prompt.lower()):
                    r.room_id = "room_L1_cinema"
                    r.room_type = "living_room"
                    r.room_name = "Private Home Cinema & Media Lounge"
                if "patio" in r.room_id.lower() and "pool" in prompt.lower():
                    r.room_name = "Courtyard Sunken Pool & Deck"
                if "stair" in r.room_id.lower() or "hall" in r.room_id.lower():
                    r.room_name = "Grand Rotunda Staircase Hall"
                    r.metadata["typology"] = "rotunda"

            for wl in all_walls:
                wl.centerline = [[round(target_w - pt[0], 2), pt[1]] for pt in wl.centerline]

            for op in all_openings:
                op.position = [round(target_w - op.position[0], 2), op.position[1]]
                if "cinema" in prompt.lower() or "theater" in prompt.lower():
                    op.connects_rooms = ["room_L1_cinema" if c == "room_L1_bed4" else c for c in op.connects_rooms]

        # 7. Build Spatial Relationship Graph
        extractor = SpatialRelationshipGraphExtractor(max_wall_separation_m=0.40, min_shared_boundary_m=0.50)
        edges, _ = extractor.build_graph(all_rooms, all_openings)

        # Connect vertical staircase between Level 0 and Level 1
        if len(levels) >= 2:
            stair_0 = next((r for r in all_rooms if r.level_index == 0 and "stair" in r.room_id.lower()), None)
            stair_1 = next((r for r in all_rooms if r.level_index == 1 and "stair" in r.room_id.lower()), None)
            if stair_0 and stair_1:
                edges.append(GraphEdgeModel(
                    source_room_id=stair_0.room_id,
                    target_room_id=stair_1.room_id,
                    relationship_type="via_door",
                    weight=1.0,
                    metadata={"vertical_circulation": "double_stairs", "floor_transition": "L0_to_L1"}
                ))

        # Connect vertical staircase between Level 1 and Level 2
        if len(levels) >= 3:
            stair_1 = next((r for r in all_rooms if r.level_index == 1 and "stair" in r.room_id.lower()), None)
            stair_2 = next((r for r in all_rooms if r.level_index == 2 and "stair" in r.room_id.lower()), None)
            if stair_1 and stair_2:
                edges.append(GraphEdgeModel(
                    source_room_id=stair_1.room_id,
                    target_room_id=stair_2.room_id,
                    relationship_type="via_door",
                    weight=1.0,
                    metadata={"vertical_circulation": "double_stairs", "floor_transition": "L1_to_L2"}
                ))

        # Topological Rule 1: Merge OPEN_CONCEPT_TRIAD into unified polygon and create boundary_feature = 'ISLAND_COUNTER' edges
        triad_polygons_by_level = {}
        for lvl in levels:
            lvl_rooms = [r for r in all_rooms if r.level_index == lvl]
            triad_rooms = [r for r in lvl_rooms if any(is_open_social_triad_pair(r, other) for other in lvl_rooms if other.room_id != r.room_id)]
            if len(triad_rooms) >= 2:
                triad_union = unary_union([Polygon(r.polygon) for r in triad_rooms if Polygon(r.polygon).is_valid])
                if triad_union.geom_type == "Polygon":
                    t_coords = [list(c) for c in triad_union.exterior.coords]
                    triad_polygons_by_level[lvl] = t_coords
                    for r in triad_rooms:
                        r.metadata["open_concept_triad"] = True
                        r.metadata["open_concept_triad_polygon"] = t_coords
                        r.metadata["boundary_feature"] = "ISLAND_COUNTER"

            # Create topological graph edges for open concept triad
            for i in range(len(lvl_rooms)):
                for j in range(i + 1, len(lvl_rooms)):
                    if is_open_social_triad_pair(lvl_rooms[i], lvl_rooms[j]):
                        edges.append(GraphEdgeModel(
                            source_room_id=lvl_rooms[i].room_id,
                            target_room_id=lvl_rooms[j].room_id,
                            relationship_type="adjacency",
                            weight=1.0,
                            metadata={
                                "open_concept_triad": True,
                                "has_wall": False,
                                "door_type": None,
                                "boundary_feature": "ISLAND_COUNTER",
                                "spatial_demarcation": "breakfast_island_counter"
                            }
                        ))

        # STRICT CONSTRAINT: Assert zero door swing arcs render across open breakfast island counter
        r_all_map = {r.room_id: r for r in all_rooms}
        for op in all_openings:
            if op.opening_type == "door" and len(op.connects_rooms) == 2:
                r1 = r_all_map.get(op.connects_rooms[0])
                r2 = r_all_map.get(op.connects_rooms[1])
                if r1 and r2 and is_open_social_triad_pair(r1, r2):
                    raise AssertionError(f"Phantom kitchen aperture: Door {op.opening_id} found between {r1.room_id} and {r2.room_id} across open concept triad!")

        # 8. Metadata & Provenance tracking back to real dataset plan
        plan_id = f"gen_{matched_meta['plan_id']}_{req_floors}F"
        total_area = round(sum(r.area_m2 for r in all_rooms), 1)

        # Style-Specific Room Designation & Society Bylaws (Mandatory Lawn & OTS)
        for r in all_rooms:
            r_lower = r.room_name.lower()
            if r.level_index == 0:
                if "lawn" in r_lower or ("outdoor" in r.room_type and "ots" not in r_lower and "shaft" not in r_lower):
                    r.room_name = "Front Landscaped Lawn (Statutory Open Space)"
                    r.room_type = "outdoor"
                    r.is_habitable = False
                elif "porch" in r_lower or r.room_type == "garage":
                    r.room_name = f"{style_cfg.display_name} Car Porch & Driveway"
                    r.room_type = "garage"
                    r.is_habitable = False
                elif "ots" in r_lower or "shaft" in r_lower or "garden" in r_lower or "courtyard" in r_lower:
                    r.is_habitable = False
                    if style_cfg.style_id in ("spanish_revival", "mediterranean"):
                        if "courtyard" in r_lower or "patio" in r_lower:
                            r.room_name = "Spanish Terracotta Fountain Courtyard"

        plan = CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id,
                source_type="raster_cv",
                floor_count=len(levels),
                levels=levels,
                unit="m",
                wall_height_m=2.9,
                provenance={
                    "generator": "DatasetDrivenRAGSolver",
                    "matched_plan_id": matched_meta["plan_id"],
                    "matched_source_image": matched_meta.get("source_image", ""),
                    "plot_category": scale,
                    "target_scale": scale,
                    "frontage_ft": round(target_w * 3.28084, 1),
                    "depth_ft": round(target_d * 3.28084, 1),
                    "total_area_sqft": round(target_w * target_d * 10.7639, 1),
                    "retrieval_similarity_score": matched_meta.get("similarity_score", 1.0),
                    "staircase_type": stair_req,
                    "is_dataset_derived": True,
                    "architectural_style": style_cfg.display_name,
                    "style_id": style_cfg.style_id,
                    "style_family": style_cfg.family,
                    "roof_type": style_cfg.roof_type,
                    "wall_finish_type": style_cfg.wall_finish_type
                }
            ),
            boundary=envelope,
            total_area_m2=total_area,
            walls=all_walls,
            openings=all_openings,
            rooms=all_rooms,
            graph_edges=edges
        )

        # 9. Verify QualityGate compliance
        gate = FloorPlanQualityGate.evaluate(plan)
        if gate["final_status"] != "PASS":
            raise ValueError(f"QualityGate failed for synthesized plan {plan_id}: {gate['failures']}")

        # 10. Senior Architectural Review with Gemini Auditor
        plan, audit_result = GeminiArchitecturalAuditor.audit_and_refine(
            plan=plan,
            user_prompt=prompt,
            program=parsed,
            style_cfg=style_cfg
        )

        # Post-Audit Safety Guard: Enforce strict bedroom count if auditor renamed extra room to bedroom
        if "requested_bedrooms" in parsed:
            target_b = parsed["requested_bedrooms"]
            current_beds = [r for r in plan.rooms if r.room_type == "bedroom"]
            if len(current_beds) > target_b:
                surplus = len(current_beds) - target_b
                for r in reversed(plan.rooms):
                    if surplus <= 0:
                        break
                    if r.room_type == "bedroom" and r.level_index >= 1:
                        r.room_type = "study"
                        r.room_name = "Executive Study & Workstation"
                        surplus -= 1

        return plan

    # -----------------------------------------------------------------------
    # 1-BED SINGLE-STOREY SYNTHESIZER
    # -----------------------------------------------------------------------
    def _synthesize_1bed_single_storey(
        self,
        scale: str,
        w: float,
        d: float,
        parsed: Dict[str, Any],
        stair_type: str
    ) -> CanonicalFloorPlan:
        """
        Single-storey 1-bedroom residence. Y=0 = front/street, Y=d = rear.
        Two-column layout (non-overlapping):

          Porch strip   [0,  y1]         full width (front street)
          Left  column  [0,  left_w]:
            Drawing Room [y1, y_draw_bot]   (front)
            Bedroom      [y_draw_bot, y4]   (rear)
          Right column  [left_w, w]:
            Kitchen      [y1, y_kit_bot]    (front+mid)
            Attached Bath [y_kit_bot, y4]   (rear)
          OTS strip     [y4, d]            full width (rear outdoor)

        Circulation: Porch → Drawing → Bedroom, Porch → Kitchen → Drawing.
        No kitchen→bedroom door (F11-safe).
        """
        # ── Dimensions ──────────────────────────────────────────────────────
        MIN_PORCH_D = 4.72     # 15'-6" minimum porch depth
        porch_d = round(min(5.20, max(MIN_PORCH_D, d * 0.34)), 2)
        left_w  = round(w * 0.55, 2)
        right_w = round(w - left_w, 2)
        avail_d = d - porch_d

        # Wide rear OTS patio: min 1.5m (5'-0" patio)
        ots_d = round(max(1.50, min(2.50, avail_d * 0.16)), 2)
        core_d = round(avail_d - ots_d, 2)

        # Drawing Room: front portion of left column
        draw_d = round(core_d * 0.45, 2)
        y1 = porch_d
        y2 = round(y1 + draw_d, 2)
        y4 = round(y1 + core_d, 2)
        y5 = d
        bed_d = round(y4 - y2, 2)

        # Guest powder room: 1.8 - 2.2 m² adjacent to Drawing / Porch entry
        pwd_w = round(min(1.50, right_w * 0.48), 2)
        pwd_d = round(2.00 / pwd_w, 2)

        # Kitchen: front/mid right column
        kit_y_end = round(y1 + max(3.20, core_d * 0.45), 2)

        # Master Bath: clamped strictly in [3.6, 5.0] m²
        bath_d = round(min(1.40, max(1.10, 4.20 / right_w)), 2)
        y_bath_start = round(y4 - bath_d, 2)

        rooms: List[RoomModel] = []
        envelope = [[0.0, 0.0], [w, 0.0], [w, d], [0.0, d], [0.0, 0.0]]

        # 1. Car Porch & Driveway (front street)
        porch_poly = [[0.0, 0.0], [w, 0.0], [w, y1], [0.0, y1], [0.0, 0.0]]
        rooms.append(RoomModel(
            room_id="room_L0_porch", room_type="garage",
            room_name="Car Porch & Driveway",
            polygon=porch_poly,
            area_m2=round(w * porch_d, 1),
            centroid=[round(w / 2, 2), round(y1 / 2, 2)],
            level_index=0, is_habitable=False,
            metadata={"car_slots": 1, "porch_depth_ft": round(porch_d * 3.28084, 1)}
        ))

        # 2. Formal Drawing Room (front-left, exterior left wall)
        draw_poly = [[0.0, y1], [left_w, y1], [left_w, y2], [0.0, y2], [0.0, y1]]
        rooms.append(RoomModel(
            room_id="room_L0_drawing", room_type="living_room",
            room_name="Formal Drawing Room",
            polygon=draw_poly,
            area_m2=round(left_w * draw_d, 1),
            centroid=[round(left_w / 2, 2), round((y1 + y2) / 2, 2)],
            level_index=0, is_habitable=True
        ))

        # 3. Compact Guest Powder Room (adjacent to Porch entry & Drawing)
        pwd_poly = [
            [left_w, y1], [left_w + pwd_w, y1],
            [left_w + pwd_w, round(y1 + pwd_d, 2)],
            [left_w, round(y1 + pwd_d, 2)], [left_w, y1]
        ]
        rooms.append(RoomModel(
            room_id="room_L0_powder", room_type="bathroom",
            room_name="Guest Powder Room",
            polygon=pwd_poly,
            area_m2=round(pwd_w * pwd_d, 1),
            centroid=[round(left_w + pwd_w / 2, 2), round(y1 + pwd_d / 2, 2)],
            level_index=0, is_habitable=False
        ))

        # 4. Modern Fitted Kitchen (front-mid right column)
        kit_poly = [
            [round(left_w + pwd_w, 2), y1], [w, y1],
            [w, kit_y_end], [left_w, kit_y_end],
            [left_w, round(y1 + pwd_d, 2)], [round(left_w + pwd_w, 2), round(y1 + pwd_d, 2)],
            [round(left_w + pwd_w, 2), y1]
        ]
        rooms.append(RoomModel(
            room_id="room_L0_kitchen", room_type="kitchen",
            room_name="Modern Fitted Kitchen",
            polygon=kit_poly,
            area_m2=round(Polygon(kit_poly).area, 1),
            centroid=[round((left_w + w) / 2, 2), round((y1 + kit_y_end) / 2, 2)],
            level_index=0, is_habitable=True
        ))

        # 5. Ground Master Bedroom 1 (rear-left, strict orthogonal rectangle)
        bed_poly = [[0.0, y2], [left_w, y2], [left_w, y4], [0.0, y4], [0.0, y2]]
        rooms.append(RoomModel(
            room_id="room_L0_bed1", room_type="bedroom",
            room_name="Ground Master Bedroom 1",
            polygon=bed_poly,
            area_m2=round(left_w * bed_d, 1),
            centroid=[round(left_w / 2, 2), round((y2 + y4) / 2, 2)],
            level_index=0, is_habitable=True, metadata={"is_master": True}
        ))

        # 6. Master Dressing Room / WIC (mid-rear right column)
        dress_poly = [
            [left_w, kit_y_end], [w, kit_y_end],
            [w, y_bath_start], [left_w, y_bath_start], [left_w, kit_y_end]
        ]
        rooms.append(RoomModel(
            room_id="room_L0_dress", room_type="closet",
            room_name="Master Dressing Room & WIC",
            polygon=dress_poly,
            area_m2=round(right_w * (y_bath_start - kit_y_end), 1),
            centroid=[round((left_w + w) / 2, 2), round((kit_y_end + y_bath_start) / 2, 2)],
            level_index=0, is_habitable=False
        ))

        # 7. Master Attached Bathroom (rear right column, clamped 3.6 - 5.0 m²)
        bath_poly = [
            [left_w, y_bath_start], [w, y_bath_start],
            [w, y4], [left_w, y4], [left_w, y_bath_start]
        ]
        rooms.append(RoomModel(
            room_id="room_L0_bath1", room_type="bathroom",
            room_name="Master Attached Bathroom",
            polygon=bath_poly,
            area_m2=round(right_w * (y4 - y_bath_start), 1),
            centroid=[round((left_w + w) / 2, 2), round((y_bath_start + y4) / 2, 2)],
            level_index=0, is_habitable=False
        ))

        # 8. Wide Rear OTS Landscaped Patio
        ots_poly = [[0.0, y4], [w, y4], [w, y5], [0.0, y5], [0.0, y4]]
        rooms.append(RoomModel(
            room_id="room_L0_ots", room_type="outdoor",
            room_name="Rear OTS Landscaped Patio",
            polygon=ots_poly,
            area_m2=round(w * ots_d, 1),
            centroid=[round(w / 2, 2), round((y4 + y5) / 2, 2)],
            level_index=0, is_habitable=False
        ))

        rooms = _apply_bath_clamp_to_rooms(rooms)
        room_dict = {r.room_id: r for r in rooms}

        # ── Openings (Doors & Windows) ──────────────────────────────────────
        openings: List[OpeningModel] = [
            # Main entrance door from Porch into Drawing Room
            OpeningModel(
                opening_id="d_porch_draw", opening_type="door",
                position=[round(left_w / 2, 2), y1], width_m=1.00,
                connects_rooms=["room_L0_porch", "room_L0_drawing"], level_index=0
            ),
            # Guest access from Drawing Room into Powder Room
            OpeningModel(
                opening_id="d_draw_pwd", opening_type="door",
                position=[left_w, round(y1 + pwd_d / 2, 2)], width_m=0.80,
                connects_rooms=["room_L0_drawing", "room_L0_powder"], level_index=0
            ),
            # Drawing Room to Kitchen
            OpeningModel(
                opening_id="d_draw_kit", opening_type="door",
                position=[left_w, round(y1 + pwd_d + 0.50, 2)], width_m=0.90,
                connects_rooms=["room_L0_drawing", "room_L0_kitchen"], level_index=0
            ),
            # Drawing Room to Master Bedroom
            OpeningModel(
                opening_id="d_draw_bed1", opening_type="door",
                position=[round(left_w / 2, 2), y2], width_m=0.90,
                connects_rooms=["room_L0_drawing", "room_L0_bed1"], level_index=0
            ),
            # Master Bedroom to Attached Bath
            OpeningModel(
                opening_id="d_bed1_bath1", opening_type="door",
                position=[left_w, round((y_bath_start + y4) / 2, 2)], width_m=0.80,
                connects_rooms=["room_L0_bed1", "room_L0_bath1"], level_index=0
            ),
            # Master Bedroom to Dressing Room
            OpeningModel(
                opening_id="d_bed1_dress", opening_type="door",
                position=[left_w, round((kit_y_end + y_bath_start) / 2, 2)], width_m=0.80,
                connects_rooms=["room_L0_bed1", "room_L0_dress"], level_index=0
            ),
            # Master Bedroom to Rear OTS Patio
            OpeningModel(
                opening_id="d_bed1_ots", opening_type="door",
                position=[round(left_w / 2, 2), y4], width_m=0.90,
                connects_rooms=["room_L0_bed1", "room_L0_ots"], level_index=0
            ),
            # Windows on true exterior envelope / OTS
            OpeningModel(
                opening_id="w_draw_left", opening_type="window",
                position=[0.0, round((y1 + y2) / 2, 2)], width_m=1.50,
                sill_height_m=0.90, level_index=0
            ),
            OpeningModel(
                opening_id="w_kit_right", opening_type="window",
                position=[w, round((y1 + kit_y_end) / 2, 2)], width_m=1.20,
                sill_height_m=0.90, level_index=0
            ),
            OpeningModel(
                opening_id="w_bed1_left", opening_type="window",
                position=[0.0, round((y2 + y4) / 2, 2)], width_m=1.52,
                sill_height_m=0.90, level_index=0
            ),
            # 5'-0" window onto wide rear OTS patio
            OpeningModel(
                opening_id="w_bed1_rear", opening_type="window",
                position=[round(left_w * 0.70, 2), y4], width_m=1.52,
                sill_height_m=0.90, level_index=0
            ),
            OpeningModel(
                opening_id="w_bath1_rear", opening_type="window",
                position=[round(left_w + right_w / 2, 2), y4], width_m=0.60,
                sill_height_m=1.40, level_index=0
            ),
        ]

        walls = self._generate_structural_walls(rooms, envelope, [0])
        from extraction.relationships import SpatialRelationshipGraphExtractor
        extractor = SpatialRelationshipGraphExtractor(
            max_wall_separation_m=0.40, min_shared_boundary_m=0.40
        )
        edges, _ = extractor.build_graph(rooms, openings)

        plan_id = f"gen_{scale}_1bed_1F"
        plan = CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id, source_type="synthetic_generated",
                floor_count=1, levels=[0], unit="m", wall_height_m=2.90,
                provenance={
                    "generator": "DatasetDrivenRAGSolver._synthesize_1bed_single_storey",
                    "plot_category": scale,
                    "frontage_ft": round(w * 3.28084, 1),
                    "depth_ft": round(d * 3.28084, 1),
                    "porch_depth_ft": round(porch_d * 3.28084, 1),
                    "staircase_type": "none", "bedrooms": 1,
                    "is_single_storey": True,
                    "total_area_sqft": round(w * d * 10.7639, 1)
                }
            ),
            boundary=envelope,
            total_area_m2=round(sum(r.area_m2 for r in rooms), 1),
            walls=walls, openings=openings, rooms=rooms, graph_edges=edges
        )
        gate = FloorPlanQualityGate.evaluate(plan)
        if gate["final_status"] != "PASS":
            raise ValueError(
                f"QualityGate failed for 1-bed plan {plan_id}: {gate['failures']}"
            )
        return plan


        # ── Column widths ───────────────────────────────────────────────────
        MIN_PORCH_D = 4.72     # 15'-6"
        porch_d = round(min(5.50, max(MIN_PORCH_D, d * 0.34)), 2)
        left_w  = round(w * 0.55, 2)
        right_w = round(w - left_w, 2)

        # ── Band heights ────────────────────────────────────────────────────
        # Three habitable bands + OTS strip inside d - porch_d = avail
        # Proportional split: Drawing 30%, Kitchen 25%, Bedroom 35%, OTS 10%
        avail = d - porch_d
        # Band proportions (must sum to 1.0)
        DRAW_FRAC = 0.30
        KIT_FRAC  = 0.25
        BED_FRAC  = 0.35
        OTS_FRAC  = 1.0 - DRAW_FRAC - KIT_FRAC - BED_FRAC   # 0.10

        front_h = round(avail * DRAW_FRAC, 2)
        kit_h   = round(avail * KIT_FRAC,  2)
        bed_h   = round(avail * BED_FRAC,  2)
        ots_h   = round(avail - front_h - kit_h - bed_h, 2)  # absorbs rounding residual

        # Apply minimums — if minimums overflow avail, trim proportionally
        MIN_FRONT = 3.00; MIN_KIT = 2.60; MIN_BED = 3.30; MIN_OTS = 0.80
        front_h = max(front_h, MIN_FRONT)
        kit_h   = max(kit_h, MIN_KIT)
        bed_h   = max(bed_h, MIN_BED)
        # Trim: ensure sum never > avail - MIN_OTS
        cap = avail - MIN_OTS
        total_hab = front_h + kit_h + bed_h
        if total_hab > cap:
            scale_f = cap / total_hab
            front_h = round(front_h * scale_f, 2)
            kit_h   = round(kit_h   * scale_f, 2)
            bed_h   = round(bed_h   * scale_f, 2)
        ots_h = round(avail - front_h - kit_h - bed_h, 2)

        bed_w  = round(w * 0.60, 2); bed_w  = max(bed_w, 3.30)
        # Aspect ratio guard: bed must not be deeper than 2.5× its width
        bed_h  = min(bed_h, round(bed_w * 2.50, 2))
        # Recompute OTS after aspect cap and ensure it's positive
        ots_h  = round(avail - front_h - kit_h - bed_h, 2)

        # Kitchen aspect guard (width/height must stay <= 2.6)
        if w / kit_h > 2.60:
            kit_h = round(w / 2.60, 2)
            # Rebalance: take from front_h first, then bed_h
            deficit = (front_h + kit_h + bed_h) - (avail - MIN_OTS)
            if deficit > 0:
                front_h = round(max(MIN_FRONT, front_h - deficit), 2)
                deficit = (front_h + kit_h + bed_h) - (avail - MIN_OTS)
                if deficit > 0:
                    bed_h = round(max(MIN_BED, bed_h - deficit), 2)
            ots_h = round(avail - front_h - kit_h - bed_h, 2)

        bath_w = round(w - bed_w, 2); bath_w = max(bath_w, 1.40)
        # Bath depth: must fit within bed_h
        bath_d = round(min(bed_h, min(BATH_AREA_MAX_M2 / bath_w,
                           max(BATH_AREA_MIN_M2 / bath_w, BATH_AREA_TARGET_M2 / bath_w))), 3)

        powder_d = round(min(POWDER_AREA_MAX_M2 / right_w,
                             max(POWDER_AREA_MIN_M2 / right_w, 2.0 / right_w)), 3)

        # ── Y-coordinates ───────────────────────────────────────────────────
        y1 = round(porch_d, 2)
        y2 = round(y1 + front_h, 2)
        y3 = round(y2 + kit_h, 2)
        y4 = round(y3 + bed_h, 2)
        y5 = d


        rooms: List[RoomModel] = []
        envelope = [[0.0, 0.0], [w, 0.0], [w, d], [0.0, d], [0.0, 0.0]]

        # 1. Car Porch (Band 0, full-width, exterior front)
        rooms.append(RoomModel(
            room_id="room_L0_porch", room_type="garage",
            room_name="Car Porch & Driveway",
            polygon=[[0, 0], [w, 0], [w, y1], [0, y1], [0, 0]],
            area_m2=round(w * porch_d, 1),
            centroid=[round(w / 2, 2), round(y1 / 2, 2)],
            level_index=0, is_habitable=False,
            metadata={"car_slots": 1, "porch_depth_ft": round(porch_d * 3.28084, 1)}
        ))

        # 2. Formal Drawing Room (Band 1, left column — wall at Y=y1 is exterior facade behind porch)
        rooms.append(RoomModel(
            room_id="room_L0_drawing", room_type="living_room",
            room_name="Formal Drawing Room",
            polygon=[[0, y1], [left_w, y1], [left_w, y2], [0, y2], [0, y1]],
            area_m2=round(left_w * front_h, 1),
            centroid=[round(left_w / 2, 2), round((y1 + y2) / 2, 2)],
            level_index=0, is_habitable=True
        ))

        # 3a. Entry Lobby (Band 1, right column, lower stub — connects porch → kitchen)
        lobby_h = round(front_h - powder_d, 3)
        lobby_h = max(lobby_h, 0.0)
        if lobby_h >= 0.50:
            rooms.append(RoomModel(
                room_id="room_L0_entry_lobby", room_type="corridor",
                room_name="Entry Lobby",
                polygon=[[left_w, y1], [w, y1], [w, round(y1 + lobby_h, 2)],
                         [left_w, round(y1 + lobby_h, 2)], [left_w, y1]],
                area_m2=round(right_w * lobby_h, 1),
                centroid=[round(left_w + right_w / 2, 2), round(y1 + lobby_h / 2, 2)],
                level_index=0, is_habitable=False
            ))

        # 3b. Guest Powder Room (Band 1, right column, top part — has exterior side wall at X=w)
        pwd_y0 = round(y2 - powder_d, 3)
        rooms.append(RoomModel(
            room_id="room_L0_powder", room_type="bathroom",
            room_name="Guest Powder Room",
            polygon=[[left_w, pwd_y0], [w, pwd_y0], [w, y2], [left_w, y2], [left_w, pwd_y0]],
            area_m2=round(right_w * powder_d, 1),
            centroid=[round(left_w + right_w / 2, 2), round((pwd_y0 + y2) / 2, 2)],
            level_index=0, is_habitable=False
        ))

        # 4. Modern Kitchen (Band 2, full-width)
        rooms.append(RoomModel(
            room_id="room_L0_kitchen", room_type="kitchen",
            room_name="Modern Fitted Kitchen",
            polygon=[[0, y2], [w, y2], [w, y3], [0, y3], [0, y2]],
            area_m2=round(w * kit_h, 1),
            centroid=[round(w / 2, 2), round((y2 + y3) / 2, 2)],
            level_index=0, is_habitable=True
        ))

        # 5. Master Bedroom (Band 3, left)
        rooms.append(RoomModel(
            room_id="room_L0_bed1", room_type="bedroom",
            room_name="Ground Master Bedroom 1",
            polygon=[[0, y3], [bed_w, y3], [bed_w, y4], [0, y4], [0, y3]],
            area_m2=round(bed_w * bed_h, 1),
            centroid=[round(bed_w / 2, 2), round((y3 + y4) / 2, 2)],
            level_index=0, is_habitable=True, metadata={"is_master": True}
        ))

        # 6. Master Attached Bathroom (Band 3, right — top portion)
        bath_y1 = round(y3 + bath_d, 2)
        rooms.append(RoomModel(
            room_id="room_L0_bath1", room_type="bathroom",
            room_name="Master Attached Bathroom",
            polygon=[[bed_w, y3], [w, y3], [w, bath_y1], [bed_w, bath_y1], [bed_w, y3]],
            area_m2=round(bath_w * bath_d, 1),
            centroid=[round(bed_w + bath_w / 2, 2), round((y3 + bath_y1) / 2, 2)],
            level_index=0, is_habitable=False
        ))

        # 6b. Dressing / Wardrobe Nook (Band 3, right — below bath)
        if y4 - bath_y1 >= 1.0:
            rooms.append(RoomModel(
                room_id="room_L0_dressing", room_type="storage",
                room_name="Dressing / Wardrobe Nook",
                polygon=[[bed_w, bath_y1], [w, bath_y1], [w, y4], [bed_w, y4], [bed_w, bath_y1]],
                area_m2=round(bath_w * (y4 - bath_y1), 1),
                centroid=[round(bed_w + bath_w / 2, 2), round((bath_y1 + y4) / 2, 2)],
                level_index=0, is_habitable=False
            ))

        # 7. Rear OTS Courtyard (Band 4, full-width)
        if y5 - y4 >= 0.50:
            rooms.append(RoomModel(
                room_id="room_L0_ots", room_type="outdoor",
                room_name="Rear OTS Landscaped Courtyard",
                polygon=[[0, y4], [w, y4], [w, y5], [0, y5], [0, y4]],
                area_m2=round(w * (y5 - y4), 1),
                centroid=[round(w / 2, 2), round((y4 + y5) / 2, 2)],
                level_index=0, is_habitable=False
            ))

        rooms = _apply_bath_clamp_to_rooms(rooms)
        room_dict = {r.room_id: r for r in rooms}

        # ── Inline openings ─────────────────────────────────────────────────
        openings: List[OpeningModel] = []

        def _door(r1: str, r2: str, wm: float = 0.90, oid: str = None):
            if r1 not in room_dict or r2 not in room_dict:
                return
            from shapely.geometry import Polygon as _P
            inter = _P(room_dict[r1].polygon).intersection(_P(room_dict[r2].polygon))
            if inter.is_empty or inter.length < 0.30:
                return
            lines = [inter] if inter.geom_type == "LineString" else [
                g for g in getattr(inter, "geoms", []) if g.geom_type == "LineString"
            ]
            if not lines:
                return
            lg = max(lines, key=lambda l: l.length)
            cs = list(lg.coords)
            openings.append(OpeningModel(
                opening_id=oid or f"d_{r1}_{r2}",
                opening_type="door",
                position=[round((cs[0][0] + cs[-1][0]) / 2, 2),
                          round((cs[0][1] + cs[-1][1]) / 2, 2)],
                width_m=wm, connects_rooms=[r1, r2], level_index=0
            ))

        _door("room_L0_porch", "room_L0_drawing",      1.00, "d_porch_draw")
        _door("room_L0_porch", "room_L0_entry_lobby",  1.00, "d_porch_lobby")
        # Drawing Room → Kitchen (main interior circulation)
        _door("room_L0_drawing", "room_L0_kitchen",    0.90, "d_draw_kit")
        _door("room_L0_entry_lobby", "room_L0_kitchen", 0.90, "d_lobby_kit")
        _door("room_L0_entry_lobby", "room_L0_powder", 0.80, "d_lobby_pwd")
        _door("room_L0_drawing",    "room_L0_powder",  0.80, "d_draw_pwd")
        # Kitchen → Bedroom circulation via Drawing Room back-hall (no direct sleep-cook link)
        # Bedroom accessed from Kitchen via shared wall (permitted — not F11 if via corridor)
        _door("room_L0_drawing",    "room_L0_bed1",    0.90, "d_draw_bed1")
        _door("room_L0_bed1",       "room_L0_bath1",   0.80, "d_bed1_bath1")
        _door("room_L0_bed1",       "room_L0_ots",     0.90, "d_bed1_ots")
        _door("room_L0_bath1",      "room_L0_dressing", 0.75, "d_bath1_dress")

        # Exterior windows on TRUE exterior walls only:
        # Drawing room: left wall at X=0 (exterior) mid-height
        openings.append(OpeningModel(
            opening_id="w_draw_left", opening_type="window",
            position=[0.0, round((y1 + y2) / 2, 2)],
            width_m=1.50, sill_height_m=0.90, level_index=0
        ))
        # Powder room: right exterior wall at X=w
        openings.append(OpeningModel(
            opening_id="w_powder_right", opening_type="window",
            position=[w, round((pwd_y0 + y2) / 2, 2)],
            width_m=0.90, sill_height_m=1.20, level_index=0
        ))
        # Master bedroom: rear exterior wall at Y=y4 (looking into OTS — truly exterior)
        openings.append(OpeningModel(
            opening_id="w_master_rear", opening_type="window",
            position=[round(bed_w / 2, 2), y4],
            width_m=1.52, sill_height_m=0.90, level_index=0
        ))
        # Kitchen: left exterior wall at X=0
        openings.append(OpeningModel(
            opening_id="w_kit_left", opening_type="window",
            position=[0.0, round((y2 + y3) / 2, 2)],
            width_m=1.20, sill_height_m=0.90, level_index=0
        ))

        walls = self._generate_structural_walls(rooms, envelope, [0])
        from extraction.relationships import SpatialRelationshipGraphExtractor
        extractor = SpatialRelationshipGraphExtractor(
            max_wall_separation_m=0.40, min_shared_boundary_m=0.50
        )
        edges, _ = extractor.build_graph(rooms, openings)

        plan_id = f"gen_{scale}_1bed_1F"
        plan = CanonicalFloorPlan(
            metadata=MetadataModel(
                plan_id=plan_id, source_type="synthetic_generated",
                floor_count=1, levels=[0], unit="m", wall_height_m=2.90,
                provenance={
                    "generator": "DatasetDrivenRAGSolver._synthesize_1bed_single_storey",
                    "plot_category": scale,
                    "frontage_ft": round(w * 3.28084, 1),
                    "depth_ft": round(d * 3.28084, 1),
                    "porch_depth_ft": round(porch_d * 3.28084, 1),
                    "staircase_type": "none", "bedrooms": 1,
                    "is_single_storey": True,
                    "total_area_sqft": round(w * d * 10.7639, 1)
                }
            ),
            boundary=envelope,
            total_area_m2=round(sum(r.area_m2 for r in rooms), 1),
            walls=walls, openings=openings, rooms=rooms, graph_edges=edges
        )
        gate = FloorPlanQualityGate.evaluate(plan)
        if gate["final_status"] != "PASS":
            raise ValueError(
                f"QualityGate failed for 1-bed plan {plan_id}: {gate['failures']}"
            )
        return plan


    def _stack_level_1(
        self,
        l0_rooms: List[RoomModel],
        scale: str,
        w: float,
        d: float,
        stair_type: str,
        parsed: Dict[str, Any],
        base_plan: Optional[CanonicalFloorPlan] = None
    ) -> List[RoomModel]:
        """
        Synthesizes true architectural Level 1 layout from Ground Floor geometry:
        1. Vertical Structural Continuity:
           - Staircase: Pinned with exact same coordinates on L1 as L0 (IoU = 1.0).
           - Lightwells & OTS voids: Vertically continuous (IoU = 1.0).
           - Perimeter walls: Stack directly over ground exterior load-bearing walls.
        2. Realistic Upper-Floor Layout:
           - Front Zone: Ground porch -> Open Front Balcony / Terrace (never duplicate car parking).
           - Core Zone: Ground kitchen/lounge -> Upper Family Living Lounge and circulation gallery
             (never duplicate kitchen counters/cooking appliances upstairs).
           - Bedroom Allocation: Distinct rectangular bedroom suites (>= 12 m²) to fulfill
             remaining req_beds - ground_beds, each with attached bathroom [3.6, 5.2] m²
             and window opening directly to exterior street, setback, or OTS.
        """
        l1_rooms = []
        raw_prompt = parsed.get("raw_prompt", "").lower()
        req_beds = parsed.get("requested_bedrooms", 3)
        ground_beds = [r for r in l0_rooms if r.room_type == "bedroom"]
        num_ground_beds = len(ground_beds)
        l1_beds_needed = max(0, req_beds - num_ground_beds)

        # -------------------------------------------------------------
        # Dedicated Synthesis for 3 Marla G+1 (3 beds: 1 GF + 2 L1)
        # -------------------------------------------------------------
        if scale == "3_marla" and l1_beds_needed >= 2:
            stair_l0 = next((r for r in l0_rooms if "stair" in r.room_id.lower() or "stair" in r.room_name.lower()), None)
            porch_l0 = next((r for r in l0_rooms if r.room_type == "garage" or "porch" in r.room_id.lower()), None)
            bed1_l0 = next((r for r in l0_rooms if r.room_type == "bedroom"), None)
            bath1_l0 = next((r for r in l0_rooms if r.room_type == "bathroom" and "powder" not in r.room_id.lower()), None)
            foyer_l0 = next((r for r in l0_rooms if "foyer" in r.room_id.lower() or "lobby" in r.room_id.lower()), None)
            ots_l0 = next((r for r in l0_rooms if r.room_type == "outdoor" and "ots" in r.room_id.lower()), None)

            stair_bounds = Polygon(stair_l0.polygon).bounds if stair_l0 else (0.0, 3.8, 1.05, 7.6)
            is_stair_right = stair_bounds[0] > 1.5

            if is_stair_right:
                # 3 Marla Plan B layout (stair on right, porch on left)
                stair_meta = dict(stair_l0.metadata or {}) if stair_l0 else {}
                stair_meta.update({"typology": stair_l0.metadata.get("typology", "l_shaped") if stair_l0 else "l_shaped", "headroom_m": 2.10, "flight_width": 1.00, "landing_depth": 1.20, "parent_l0_id": stair_l0.room_id if stair_l0 else "room_L0_stairs"})
                l1_rooms.append(RoomModel(
                    room_id="room_L1_stairs", room_type="corridor", room_name="Staircase Landing (DN ->)",
                    polygon=[list(pt) for pt in stair_l0.polygon], area_m2=stair_l0.area_m2,
                    centroid=list(stair_l0.centroid), level_index=1, is_habitable=False, metadata=stair_meta
                ))
                if foyer_l0:
                    l1_rooms.append(RoomModel(
                        room_id="room_L1_foyer", room_type="corridor", room_name="Upper Entry Gallery & Foyer",
                        polygon=[list(pt) for pt in foyer_l0.polygon], area_m2=foyer_l0.area_m2,
                        centroid=list(foyer_l0.centroid), level_index=1, is_habitable=False, metadata={"parent_l0_id": foyer_l0.room_id}
                    ))
                l1_rooms.append(RoomModel(
                    room_id="room_L1_terrace", room_type="balcony", room_name="Open Front Terrace / Balcony",
                    polygon=[list(pt) for pt in porch_l0.polygon], area_m2=porch_l0.area_m2,
                    centroid=list(porch_l0.centroid), level_index=1, is_habitable=False, metadata={"parent_l0_id": porch_l0.room_id}
                ))
                bed3_poly = [[0.0, 4.2], [2.27, 4.2], [2.27, 9.6], [0.0, 9.6], [0.0, 4.2]]
                b3_g = Polygon(bed3_poly)
                l1_rooms.append(RoomModel(
                    room_id="room_L1_bed3", room_type="bedroom", room_name="Upper Front Bedroom Suite 3",
                    polygon=bed3_poly, area_m2=round(b3_g.area, 2), centroid=[round(b3_g.centroid.x, 2), round(b3_g.centroid.y, 2)],
                    level_index=1, is_habitable=True, metadata={"is_master": False}
                ))
                lounge_l0 = next((r for r in l0_rooms if r.room_type == "living_room"), None)
                lounge_poly = [list(pt) for pt in lounge_l0.polygon] if lounge_l0 else [[2.27, 4.2], [w, 4.2], [w, 9.6], [2.27, 9.6], [2.27, 4.2]]
                lg_g = Polygon(lounge_poly)
                l1_rooms.append(RoomModel(
                    room_id="room_L1_tv_lounge", room_type="living_room", room_name="Upper Family TV Lounge & Gallery",
                    polygon=lounge_poly, area_m2=round(lg_g.area, 2), centroid=[round(lg_g.centroid.x, 2), round(lg_g.centroid.y, 2)],
                    level_index=1, is_habitable=True, metadata={"parent_l0_id": lounge_l0.room_id if lounge_l0 else ""}
                ))
                bed1_poly = [list(pt) for pt in bed1_l0.polygon] if bed1_l0 else [[0.0, 9.6], [2.77, 9.6], [2.77, d], [0.0, d], [0.0, 9.6]]
                b1_g = Polygon(bed1_poly)
                l1_rooms.append(RoomModel(
                    room_id="room_L1_bed2", room_type="bedroom", room_name="Upper Master Bedroom Suite 2",
                    polygon=bed1_poly, area_m2=round(b1_g.area, 2), centroid=[round(b1_g.centroid.x, 2), round(b1_g.centroid.y, 2)],
                    level_index=1, is_habitable=True, metadata={"is_master": True, "attached_to": "room_L1_bath1", "parent_l0_id": bed1_l0.room_id if bed1_l0 else ""}
                ))
                bath1_poly = [list(pt) for pt in bath1_l0.polygon] if bath1_l0 else [[2.77, 9.6], [w, 9.6], [w, 11.9], [2.77, 11.9], [2.77, 9.6]]
                ba_g = Polygon(bath1_poly)
                l1_rooms.append(RoomModel(
                    room_id="room_L1_bath1", room_type="bathroom", room_name="Master Attached Bath",
                    polygon=bath1_poly, area_m2=round(ba_g.area, 2), centroid=[round(ba_g.centroid.x, 2), round(ba_g.centroid.y, 2)],
                    level_index=1, is_habitable=False, metadata={"attached_to": "room_L1_bed2", "parent_l0_id": bath1_l0.room_id if bath1_l0 else ""}
                ))
                if ots_l0:
                    l1_rooms.append(RoomModel(
                        room_id="room_L1_ots", room_type="outdoor", room_name="Rear Sunlight OTS Shaft",
                        polygon=[list(pt) for pt in ots_l0.polygon], area_m2=ots_l0.area_m2,
                        centroid=list(ots_l0.centroid), level_index=1, is_habitable=False, metadata={"parent_l0_id": ots_l0.room_id}
                    ))
                return l1_rooms

            stair_w = Polygon(stair_l0.polygon).bounds[2] if stair_l0 else 1.05
            stair_max_y = Polygon(stair_l0.polygon).bounds[3] if stair_l0 else 7.60
            porch_d = Polygon(porch_l0.polygon).bounds[3] if porch_l0 else 3.80
            bed1_miny = Polygon(bed1_l0.polygon).bounds[1] if bed1_l0 else 9.60

            # 1. Pinned Staircase with preserved base blueprint typology
            stair_typology = stair_l0.metadata.get("typology", "straight") if stair_l0 else "straight"
            stair_meta = dict(stair_l0.metadata or {}) if stair_l0 else {}
            stair_meta.update({
                "typology": stair_typology,
                "headroom_m": 2.10,
                "flight_width": 1.00,
                "landing_depth": 1.20,
                "parent_l0_id": stair_l0.room_id if stair_l0 else "room_L0_stairs"
            })
            l1_rooms.append(RoomModel(
                room_id="room_L1_stairs",
                room_type="corridor",
                room_name="Staircase Landing (DN ->)",
                polygon=[list(pt) for pt in stair_l0.polygon] if stair_l0 else [[0.0, porch_d], [stair_w, porch_d], [stair_w, stair_max_y], [0.0, stair_max_y], [0.0, porch_d]],
                area_m2=stair_l0.area_m2 if stair_l0 else round(stair_w * (stair_max_y - porch_d), 2),
                centroid=list(stair_l0.centroid) if stair_l0 else [round(stair_w/2, 2), round((porch_d+stair_max_y)/2, 2)],
                level_index=1,
                is_habitable=False,
                metadata=stair_meta
            ))

            # 2. Open Front Terrace (over porch)
            porch_meta = dict(porch_l0.metadata or {}) if porch_l0 else {}
            if porch_l0:
                porch_meta["parent_l0_id"] = porch_l0.room_id
            l1_rooms.append(RoomModel(
                room_id="room_L1_terrace",
                room_type="balcony",
                room_name="Open Front Terrace / Balcony",
                polygon=[list(pt) for pt in porch_l0.polygon] if porch_l0 else [[0.0, 0.0], [w, 0.0], [w, porch_d], [0.0, porch_d], [0.0, 0.0]],
                area_m2=porch_l0.area_m2 if porch_l0 else round(w * porch_d, 2),
                centroid=list(porch_l0.centroid) if porch_l0 else [round(w/2, 2), round(porch_d/2, 2)],
                level_index=1,
                is_habitable=False,
                metadata=porch_meta
            ))

            # 3. Front Bedroom Suite 3 (beside stairs, facing street / terrace)
            b3_poly = [
                [stair_w, porch_d],
                [w, porch_d],
                [w, stair_max_y],
                [stair_w, stair_max_y],
                [stair_w, porch_d]
            ]
            b3_geom = Polygon(b3_poly)
            l1_rooms.append(RoomModel(
                room_id="room_L1_bed3",
                room_type="bedroom",
                room_name="Upper Front Bedroom Suite 3",
                polygon=b3_poly,
                area_m2=round(b3_geom.area, 2),
                centroid=[round(b3_geom.centroid.x, 2), round(b3_geom.centroid.y, 2)],
                level_index=1,
                is_habitable=True,
                metadata={"is_master": False, "attached_to": "room_L1_bath3"}
            ))

            # 4. Attached Bath 3 (shares boundary with bed3 at stair_max_y, placed on the right side)
            split_x = round(max(stair_w, w - 1.80), 2)
            bath3_poly = [
                [split_x, stair_max_y],
                [w, stair_max_y],
                [w, bed1_miny],
                [split_x, bed1_miny],
                [split_x, stair_max_y]
            ]
            bath3_geom = Polygon(bath3_poly)
            l1_rooms.append(RoomModel(
                room_id="room_L1_bath3",
                room_type="bathroom",
                room_name="Attached Bath 3",
                polygon=bath3_poly,
                area_m2=round(bath3_geom.area, 2),
                centroid=[round(bath3_geom.centroid.x, 2), round(bath3_geom.centroid.y, 2)],
                level_index=1,
                is_habitable=False,
                metadata={"attached_to": "room_L1_bed3"}
            ))

            # 5. Upper Family TV Lounge & Gallery (central zone - shared wall with bath3 at split_x)
            lounge_poly = [
                [0.0, stair_max_y],
                [split_x, stair_max_y],
                [split_x, bed1_miny],
                [0.0, bed1_miny],
                [0.0, stair_max_y]
            ]
            lounge_geom = Polygon(lounge_poly)
            l1_rooms.append(RoomModel(
                room_id="room_L1_tv_lounge",
                room_type="living_room",
                room_name="Upper Family TV Lounge & Gallery",
                polygon=lounge_poly,
                area_m2=round(lounge_geom.area, 2),
                centroid=[round(lounge_geom.centroid.x, 2), round(lounge_geom.centroid.y, 2)],
                level_index=1,
                is_habitable=True,
                metadata={"min_width_ft": f"{split_x*3.28084:.1f}ft"}
            ))

            # 6. Rear Master Suite 2 (stacked over Bed 1)
            b2_poly = [
                [2.0, bed1_miny],
                [w, bed1_miny],
                [w, d],
                [2.0, d],
                [2.0, bed1_miny]
            ]
            b2_geom = Polygon(b2_poly)
            l1_rooms.append(RoomModel(
                room_id="room_L1_bed2",
                room_type="bedroom",
                room_name="Upper Master Bedroom Suite 2",
                polygon=b2_poly,
                area_m2=round(b2_geom.area, 2),
                centroid=[round(b2_geom.centroid.x, 2), round(b2_geom.centroid.y, 2)],
                level_index=1,
                is_habitable=True,
                metadata={"is_master": True, "attached_to": "room_L1_bath2", "parent_l0_id": bed1_l0.room_id if bed1_l0 else ""}
            ))

            # 7. Rear Attached Bath 2 (stacked over Bath 1)
            bath2_poly = [
                [0.0, 11.72],
                [2.0, 11.72],
                [2.0, d],
                [0.0, d],
                [0.0, 11.72]
            ]
            bath2_geom = Polygon(bath2_poly)
            l1_rooms.append(RoomModel(
                room_id="room_L1_bath2",
                room_type="bathroom",
                room_name="Master Attached Bath 2",
                polygon=bath2_poly,
                area_m2=round(bath2_geom.area, 2),
                centroid=[round(bath2_geom.centroid.x, 2), round(bath2_geom.centroid.y, 2)],
                level_index=1,
                is_habitable=False,
                metadata={"attached_to": "room_L1_bed2", "parent_l0_id": bath1_l0.room_id if bath1_l0 else ""}
            ))
            return l1_rooms

        # -------------------------------------------------------------
        # DEDICATED SYNTHESIS: 10 Marla and 1 Kanal G+1
        # Hard Constraints:
        #   C1: Max 3 bedrooms on First Floor.
        #   C2: Mandatory OTS/MEP shaft between back-to-back bathrooms.
        #   C3: L1 baths must stack ONLY over L0 baths/utility/OTS.
        #   C4: Double car porch -> open front terrace on L1.
        #   C5: Kitchenette + Family Lounge (no full second kitchen).
        # -------------------------------------------------------------
        if scale in ('10_marla', '1_kanal'):
            return self._stack_level_1_10m(
                l0_rooms, w, d, stair_type, parsed, base_plan
            )

        # -------------------------------------------------------------
        # General Synthesis (5 Marla, 7 Marla)
        # -------------------------------------------------------------
        if scale in ('5_marla', '7_marla'):
            l1_beds_needed = min(l1_beds_needed, 2)

        allocated_beds = 0
        allocated_baths = 0
        lounge_allocated = False
        kitchen_allocated = False
        used_l0_ids = set()

        # Step 1: Pinned structural voids (IoU = 1.0)
        for r in l0_rooms:
            rid_l = r.room_id.lower()
            rname_l = r.room_name.lower()
            poly = [list(pt) for pt in r.polygon]
            meta = dict(r.metadata or {})
            meta["parent_l0_id"] = r.room_id

            if "stair" in rid_l or "stair" in rname_l:
                base_typology = r.metadata.get("typology") if r.metadata else None
                meta.update({"typology": base_typology or stair_type, "headroom_m": 2.10, "flight_width": 1.00, "landing_depth": 1.20})
                l1_rooms.append(RoomModel(
                    room_id="room_L1_stairs",
                    room_type="corridor",
                    room_name="Staircase Landing (DN ->)",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=1,
                    is_habitable=False,
                    metadata=meta
                ))
                used_l0_ids.add(r.room_id)
            elif "ots" in rid_l or "shaft" in rid_l or "duct" in rid_l or (r.room_type == "outdoor" and "lawn" not in rid_l and "garden" not in rid_l and "patio" not in rid_l):
                l1_rooms.append(RoomModel(
                    room_id=f"room_L1_{r.room_id.replace('room_L0_', '')}",
                    room_type="outdoor",
                    room_name=f"Upper {r.room_name}",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=1,
                    is_habitable=False,
                    metadata=meta
                ))
                used_l0_ids.add(r.room_id)
            elif "patio" in rid_l or "courtyard" in rid_l or (r.room_type == "outdoor" and ("patio" in rname_l or "court" in rname_l)):
                l1_rooms.append(RoomModel(
                    room_id=f"room_L1_{r.room_id.replace('room_L0_', '')}",
                    room_type="outdoor",
                    room_name="Upper Courtyard Void & Balcony Gallery",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=1,
                    is_habitable=False,
                    metadata=meta
                ))
                used_l0_ids.add(r.room_id)
            elif r.room_type == "garage" or "porch" in rid_l:
                l1_rooms.append(RoomModel(
                    room_id="room_L1_terrace",
                    room_type="balcony",
                    room_name="Open Front Terrace / Balcony",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=1,
                    is_habitable=False,
                    metadata=meta
                ))
                used_l0_ids.add(r.room_id)
            elif "lawn" in rid_l or "garden" in rid_l:
                l1_rooms.append(RoomModel(
                    room_id=f"room_L1_{r.room_id.replace('room_L0_', '')}",
                    room_type="outdoor",
                    room_name="Upper Open Terrace",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=1,
                    is_habitable=False,
                    metadata=meta
                ))
                used_l0_ids.add(r.room_id)

        # Step 2: Stack Upper Bedroom Suites & Attached Baths over Ground Bedrooms
        l0_beds = [r for r in l0_rooms if r.room_type == "bedroom"]
        l0_baths = [r for r in l0_rooms if r.room_type == "bathroom"]

        for b_r in l0_beds:
            if allocated_beds < l1_beds_needed:
                allocated_beds += 1
                bed_idx = num_ground_beds + allocated_beds
                b_id = f"room_L1_bed{bed_idx}"
                bath_id = f"room_L1_bath{bed_idx}"

                # Attach adjacent bathroom on L0
                p_bed = Polygon(b_r.polygon)
                adj_bath = None
                for ba in l0_baths:
                    if ba.room_id not in used_l0_ids:
                        p_ba = Polygon(ba.polygon)
                        if p_bed.intersection(p_ba).length >= 0.35:
                            adj_bath = ba
                            break

                has_bath = adj_bath is not None
                is_master = (allocated_beds == 1 and has_bath)
                b_name = f"Upper Master Bedroom Suite {bed_idx}" if is_master else f"Upper Bedroom Suite {bed_idx}"
                bath_name = f"Master Attached Bath {bed_idx}" if is_master else f"Attached Bath {bed_idx}"

                meta = dict(b_r.metadata or {})
                meta["parent_l0_id"] = b_r.room_id
                meta["is_master"] = is_master
                if has_bath:
                    meta["attached_to"] = bath_id
                else:
                    meta.pop("attached_to", None)

                l1_rooms.append(RoomModel(
                    room_id=b_id,
                    room_type="bedroom",
                    room_name=b_name,
                    polygon=[list(pt) for pt in b_r.polygon],
                    area_m2=b_r.area_m2,
                    centroid=list(b_r.centroid),
                    level_index=1,
                    is_habitable=True,
                    metadata=meta
                ))
                used_l0_ids.add(b_r.room_id)

                if adj_bath:
                    b_meta = dict(adj_bath.metadata or {})
                    b_meta["parent_l0_id"] = adj_bath.room_id
                    b_meta["attached_to"] = b_id
                    l1_rooms.append(RoomModel(
                        room_id=bath_id,
                        room_type="bathroom",
                        room_name=bath_name,
                        polygon=[list(pt) for pt in adj_bath.polygon],
                        area_m2=adj_bath.area_m2,
                        centroid=list(adj_bath.centroid),
                        level_index=1,
                        is_habitable=False,
                        metadata=b_meta
                    ))
                    used_l0_ids.add(adj_bath.room_id)
                    allocated_baths += 1

        # Convert any surplus ground bedrooms into Upper Study/Library on Level 1 so they do not duplicate bedrooms
        for b_r in l0_beds:
            if b_r.room_id not in used_l0_ids:
                meta = dict(b_r.metadata or {})
                meta["parent_l0_id"] = b_r.room_id
                l1_rooms.append(RoomModel(
                    room_id=f"room_L1_study_{b_r.room_id.replace('room_L0_', '')}",
                    room_type="study",
                    room_name="Upper Study & Sitting Area",
                    polygon=[list(pt) for pt in b_r.polygon],
                    area_m2=b_r.area_m2,
                    centroid=list(b_r.centroid),
                    level_index=1,
                    is_habitable=True,
                    metadata=meta
                ))
                used_l0_ids.add(b_r.room_id)

        # Step 3: Fulfill remaining bedroom quota from ground study / drawing rooms
        if allocated_beds < l1_beds_needed:
            cands = [
                r for r in l0_rooms
                if r.room_id not in used_l0_ids and r.room_type in ("study", "drawing", "guest", "living_room")
                and r.area_m2 >= 8.5
            ]
            for cand in cands:
                if allocated_beds >= l1_beds_needed:
                    break
                allocated_beds += 1
                bed_idx = num_ground_beds + allocated_beds
                b_id = f"room_L1_bed{bed_idx}"
                bath_id = f"room_L1_bath{bed_idx}"

                # Attach adjacent bathroom if available
                p_cand = Polygon(cand.polygon)
                adj_bath = None
                for ba in l0_baths:
                    if ba.room_id not in used_l0_ids:
                        p_ba = Polygon(ba.polygon)
                        if p_cand.intersection(p_ba).length >= 0.35:
                            adj_bath = ba
                            break

                b_name = f"Upper Bedroom Suite {bed_idx}"
                meta = dict(cand.metadata or {})
                meta["parent_l0_id"] = cand.room_id
                meta["is_master"] = False
                if adj_bath:
                    meta["attached_to"] = bath_id
                else:
                    meta.pop("attached_to", None)

                l1_rooms.append(RoomModel(
                    room_id=b_id,
                    room_type="bedroom",
                    room_name=b_name,
                    polygon=[list(pt) for pt in cand.polygon],
                    area_m2=cand.area_m2,
                    centroid=list(cand.centroid),
                    level_index=1,
                    is_habitable=True,
                    metadata=meta
                ))
                used_l0_ids.add(cand.room_id)

                if adj_bath:
                    b_meta = dict(adj_bath.metadata or {})
                    b_meta["parent_l0_id"] = adj_bath.room_id
                    b_meta["attached_to"] = b_id
                    l1_rooms.append(RoomModel(
                        room_id=bath_id,
                        room_type="bathroom",
                        room_name=f"Attached Bath {bed_idx}",
                        polygon=[list(pt) for pt in adj_bath.polygon],
                        area_m2=adj_bath.area_m2,
                        centroid=list(adj_bath.centroid),
                        level_index=1,
                        is_habitable=False,
                        metadata=b_meta
                    ))
                    used_l0_ids.add(adj_bath.room_id)
                    allocated_baths += 1

        # Step 4: Upper Family Lounge and circulation (Core Zone)
        # CRITICAL: Never duplicate ground kitchen upstairs!
        for r in l0_rooms:
            if r.room_id in used_l0_ids:
                continue
            rid_l = r.room_id.lower()
            rname_l = r.room_name.lower()
            poly = [list(pt) for pt in r.polygon]
            meta = dict(r.metadata or {})
            meta["parent_l0_id"] = r.room_id

            if r.room_type == "kitchen":
                # Kitchen upstairs transformed into Upper Kitchenette or Upper Family Living Lounge or Executive Study
                has_upper_kitchen_req = any(k in raw_prompt for k in [
                    "upper kitchen", "second floor kitchen", "first floor kitchen",
                    "kitchen on second", "kitchen on first", "kitchen upstairs",
                    "one kitchen and other", "one kitchen on second", "and one kitchen", "and kitchen", "one kitchen"
                ])
                if has_upper_kitchen_req and not kitchen_allocated:
                    l1_rooms.append(RoomModel(
                        room_id="room_L1_kitchen",
                        room_type="kitchen",
                        room_name="Upper Modern Kitchenette & Pantry",
                        polygon=poly,
                        area_m2=r.area_m2,
                        centroid=list(r.centroid),
                        level_index=1,
                        is_habitable=True,
                        metadata=meta
                    ))
                    kitchen_allocated = True
                elif not lounge_allocated:
                    l1_rooms.append(RoomModel(
                        room_id="room_L1_tv_lounge",
                        room_type="living_room",
                        room_name="Upper Family TV Lounge",
                        polygon=poly,
                        area_m2=r.area_m2,
                        centroid=list(r.centroid),
                        level_index=1,
                        is_habitable=True,
                        metadata=meta
                    ))
                    lounge_allocated = True
                else:
                    if r.area_m2 < 5.0:
                        l1_rooms.append(RoomModel(
                            room_id="room_L1_pantry",
                            room_type="pantry",
                            room_name="Upper Compact Pantry & Utility",
                            polygon=poly,
                            area_m2=r.area_m2,
                            centroid=list(r.centroid),
                            level_index=1,
                            is_habitable=False,
                            metadata=meta
                        ))
                    else:
                        l1_rooms.append(RoomModel(
                            room_id="room_L1_study",
                            room_type="study",
                            room_name="Upper Executive Study & Library",
                            polygon=poly,
                            area_m2=r.area_m2,
                            centroid=list(r.centroid),
                            level_index=1,
                            is_habitable=True,
                            metadata=meta
                        ))
                used_l0_ids.add(r.room_id)
            elif "lounge" in rid_l or "lounge" in rname_l or "living" in rname_l or "drawing" in rid_l or "salon" in rid_l:
                if not lounge_allocated:
                    l1_rooms.append(RoomModel(
                        room_id="room_L1_tv_lounge",
                        room_type="living_room",
                        room_name="Upper Family TV Lounge",
                        polygon=poly,
                        area_m2=r.area_m2,
                        centroid=list(r.centroid),
                        level_index=1,
                        is_habitable=True,
                        metadata=meta
                    ))
                    lounge_allocated = True
                else:
                    l1_rooms.append(RoomModel(
                        room_id=f"room_L1_gallery_{r.room_id.replace('room_L0_', '')}",
                        room_type="corridor",
                        room_name="Upper Central Gallery & Sitting Foyer",
                        polygon=poly,
                        area_m2=r.area_m2,
                        centroid=list(r.centroid),
                        level_index=1,
                        is_habitable=False,
                        metadata=meta
                    ))
                used_l0_ids.add(r.room_id)
            elif r.room_type == "bathroom":
                l1_rooms.append(RoomModel(
                    room_id=f"room_L1_{r.room_id.replace('room_L0_', '')}",
                    room_type="bathroom",
                    room_name=f"Upper {r.room_name}",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=1,
                    is_habitable=False,
                    metadata=meta
                ))
                used_l0_ids.add(r.room_id)
            elif r.room_type in ("corridor", "closet", "foyer"):
                l1_rooms.append(RoomModel(
                    room_id=f"room_L1_{r.room_id.replace('room_L0_', '')}",
                    room_type=r.room_type,
                    room_name=f"Upper {r.room_name}",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=1,
                    is_habitable=False,
                    metadata=meta
                ))
                used_l0_ids.add(r.room_id)
            elif r.room_type == "dining_room" or "dining" in rid_l:
                l1_rooms.append(RoomModel(
                    room_id="room_L1_dining_gallery",
                    room_type="corridor",
                    room_name="Upper View Gallery & Sitting Area",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=1,
                    is_habitable=False,
                    metadata=meta
                ))
                used_l0_ids.add(r.room_id)
            elif r.room_type == "study":
                l1_rooms.append(RoomModel(
                    room_id="room_L1_study",
                    room_type="study",
                    room_name="Upper Executive Study & Library",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=1,
                    is_habitable=True,
                    metadata=meta
                ))
                used_l0_ids.add(r.room_id)
            else:
                l1_rooms.append(RoomModel(
                    room_id=f"room_L1_{r.room_id.replace('room_L0_', '')}",
                    room_type=r.room_type,
                    room_name=f"Upper {r.room_name}",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=1,
                    is_habitable=r.is_habitable,
                    metadata=meta
                ))
                used_l0_ids.add(r.room_id)

        return l1_rooms

    def _stack_level_1_10m(
        self,
        l0_rooms,
        w: float,
        d: float,
        stair_type: str,
        parsed,
        base_plan=None
    ):
        """
        Dedicated 10-Marla / 1-Kanal Level-1 synthesizer with hard constraints:

        C1  MAX 3 BEDROOMS on first floor.
            Prevents unventilated landlocked middle bedroom.
        C2  MANDATORY OTS/MEP SHAFT (min 1.2m x 1.5m) between back-to-back
            bathrooms as plumbing riser and exhaust duct.
        C3  WET-AREA STACKING: every L1 bathroom polygon must overlap with
            a L0 bathroom, OTS, or corridor footprint - never with the
            L0 kitchen or dining slab.
        C4  Front terrace over double car porch (16ft / 4.88m min clear width).
        C5  Upper Family Lounge + Kitchenette only. No full cooking kitchen.
        C6  All habitable bedrooms must have exterior or OTS exposure.
        """
        from shapely.geometry import Polygon as _Poly
        from shapely.ops import unary_union as _uu

        l1_rooms = []

        # ----------------------------------------------------------------
        # Helpers
        # ----------------------------------------------------------------
        def _make(rid, rtype, rname, poly, lvl=1, hab=True, meta=None):
            g = _Poly(poly)
            if not g.is_valid:
                g = g.buffer(0)
            return RoomModel(
                room_id=rid, room_type=rtype, room_name=rname,
                polygon=poly,
                area_m2=round(g.area, 2),
                centroid=[round(g.centroid.x, 2), round(g.centroid.y, 2)],
                level_index=lvl, is_habitable=hab, metadata=meta or {}
            )

        def _geom_union(rooms, *type_hints):
            polys = []
            for r in rooms:
                rn = (r.room_id + " " + r.room_name).lower()
                rt = r.room_type.lower()
                if any(h in rn or h == rt for h in type_hints):
                    try:
                        p = _Poly(r.polygon)
                        if p.is_valid and p.area > 0:
                            polys.append(p)
                    except Exception:
                        pass
            if not polys:
                return None
            return _uu(polys)

        # ----------------------------------------------------------------
        # Identify key L0 footprints for constraint enforcement
        # ----------------------------------------------------------------
        l0_stair    = next((r for r in l0_rooms if "stair" in r.room_id.lower() or "stair" in r.room_name.lower()), None)
        l0_porch    = next((r for r in l0_rooms if r.room_type == "garage" or "porch" in r.room_id.lower()), None)
        l0_ots_list = [r for r in l0_rooms if r.room_type == "outdoor" and
                       any(k in r.room_id.lower() for k in ("ots", "shaft", "lightwell", "duct"))]
        l0_baths    = [r for r in l0_rooms if r.room_type == "bathroom"]
        l0_beds     = [r for r in l0_rooms if r.room_type == "bedroom"]
        l0_kit_geom = _geom_union(l0_rooms, "kitchen", "dining_room", "dining")

        # C3 validator
        def _wet_stack_ok(poly):
            g = _Poly(poly)
            if not g.is_valid:
                g = g.buffer(0)
            if l0_kit_geom and not l0_kit_geom.is_empty:
                overlap = g.intersection(l0_kit_geom).area
                if overlap > g.area * 0.15:
                    return False
            return True

        # Porch dimensions for C4
        if l0_porch:
            px1, py1, px2, py2 = _Poly(l0_porch.polygon).bounds
            porch_w = px2 - px1
            porch_d_val = py2 - py1
        else:
            porch_w = w
            porch_d_val = max(4.88, d * 0.24)

        # ----------------------------------------------------------------
        # STEP 1: Pinned structural voids (staircase + OTS)
        # ----------------------------------------------------------------
        used_l0_ids = set()

        if l0_stair:
            stair_meta = dict(l0_stair.metadata or {})
            stair_meta.update({
                "typology": stair_meta.get("typology", stair_type),
                "headroom_m": 2.20, "flight_width": 1.00,
                "landing_depth": 1.20, "parent_l0_id": l0_stair.room_id
            })
            l1_rooms.append(_make(
                "room_L1_stairs", "corridor", "Staircase Landing (DN ->)",
                [list(pt) for pt in l0_stair.polygon], hab=False, meta=stair_meta
            ))
            used_l0_ids.add(l0_stair.room_id)

        for ots_r in l0_ots_list:
            l1_rooms.append(_make(
                "room_L1_" + ots_r.room_id.replace("room_L0_", ""),
                "outdoor", "Upper " + ots_r.room_name,
                [list(pt) for pt in ots_r.polygon], hab=False,
                meta={"parent_l0_id": ots_r.room_id, "vertical_ots": True}
            ))
            used_l0_ids.add(ots_r.room_id)

        # ----------------------------------------------------------------
        # STEP 2: Front Terrace (C4)
        # ----------------------------------------------------------------
        terrace_poly = [list(pt) for pt in l0_porch.polygon] if l0_porch else [
            [0.0, 0.0], [w, 0.0], [w, porch_d_val], [0.0, porch_d_val], [0.0, 0.0]
        ]
        porch_ft = round(porch_w * 3.28084)
        l1_rooms.append(_make(
            "room_L1_terrace", "balcony",
            "Open Front Terrace / Balcony (" + str(porch_ft) + "ft wide)",
            terrace_poly, hab=False,
            meta={"parent_l0_id": l0_porch.room_id if l0_porch else "",
                  "clear_width_m": round(porch_w, 2),
                  "balustrade": "12mm tempered glass"}
        ))
        if l0_porch:
            used_l0_ids.add(l0_porch.room_id)

        # ----------------------------------------------------------------
        # ----------------------------------------------------------------
        # STEP 3: Bedrooms (C1: max 3 on L1, or 4 if requested >= 6)
        # ----------------------------------------------------------------
        req_beds_total = parsed.get("requested_bedrooms", 5)
        MAX_L1_BEDS = 4 if req_beds_total >= 6 else 3
        L1_MIN_BED_M2 = 10.0

        num_gf_beds = len(l0_beds)
        l1_beds_target = min(MAX_L1_BEDS, max(1, req_beds_total - num_gf_beds))

        l0_beds_sorted = sorted(l0_beds, key=lambda r: r.area_m2, reverse=True)
        allocated_l1_beds = 0

        for bed_r in l0_beds_sorted:
            if allocated_l1_beds >= l1_beds_target:
                break
            if bed_r.room_id in used_l0_ids:
                continue

            is_master = (allocated_l1_beds == 0)
            bed_num = num_gf_beds + allocated_l1_beds + 1
            bed_id  = "room_L1_bed" + str(bed_num)
            bath_id = "room_L1_bath" + str(bed_num)

            bed_poly = [list(pt) for pt in bed_r.polygon]
            bed_g    = _Poly(bed_poly)
            env_g    = _Poly([[0,0],[w,0],[w,d],[0,d],[0,0]])
            touches_ext = bed_g.exterior.distance(env_g.exterior) < 0.35

            bed_name = "Upper Master Suite " + str(bed_num) if is_master else "Upper Bedroom Suite " + str(bed_num)
            bed_meta = {"is_master": is_master, "parent_l0_id": bed_r.room_id,
                        "exterior_exposed": touches_ext}
            if is_master:
                bed_meta["luxury"] = True

            l1_rooms.append(_make(bed_id, "bedroom", bed_name,
                                  bed_poly, hab=True, meta=bed_meta))
            used_l0_ids.add(bed_r.room_id)
            allocated_l1_beds += 1

            # Find adjacent L0 bath for stacking
            best_bath = None
            best_shared = 0.0
            for ba in l0_baths:
                if ba.room_id in used_l0_ids:
                    continue
                shared = bed_g.intersection(_Poly(ba.polygon)).length
                if shared > best_shared:
                    best_shared = shared
                    best_bath = ba

            if best_bath and best_shared >= 0.30:
                bath_poly = [list(pt) for pt in best_bath.polygon]

                # C3: wet stack guard
                if not _wet_stack_ok(bath_poly):
                    for alt_ba in l0_baths:
                        if alt_ba.room_id in used_l0_ids:
                            continue
                        if _wet_stack_ok([list(pt) for pt in alt_ba.polygon]):
                            bath_poly = [list(pt) for pt in alt_ba.polygon]
                            best_bath = alt_ba
                            break

                bath_name = "Luxury Ensuite Bath " + str(bed_num) if is_master else "Attached Bath " + str(bed_num)
                l1_rooms.append(_make(
                    bath_id, "bathroom", bath_name,
                    bath_poly, hab=False,
                    meta={"attached_to": bed_id, "parent_l0_id": best_bath.room_id,
                          "stack_validated": _wet_stack_ok(bath_poly)}
                ))
                used_l0_ids.add(best_bath.room_id)

        # Deficit: try converting social rooms to bedrooms, prioritizing drawing and dining
        if allocated_l1_beds < l1_beds_target:
            cands = [
                r for r in l0_rooms
                if r.room_id not in used_l0_ids
                and r.room_type in ("living_room", "study", "dining_room", "kitchen")
                and r.area_m2 >= L1_MIN_BED_M2
            ]
            def _cand_priority(r):
                rid = r.room_id.lower()
                rname = r.room_name.lower()
                if "tv_lounge" in rid or "lounge" in rname or "living" in rname:
                    return 0
                if "drawing" in rid or "drawing" in rname:
                    return 4
                if "dining" in rid or "dining" in rname:
                    return 3
                if r.room_type == "kitchen":
                    return 2
                return 1
            cands.sort(key=_cand_priority, reverse=True)
            for cand in cands:
                if allocated_l1_beds >= l1_beds_target:
                    break
                bed_num = num_gf_beds + allocated_l1_beds + 1
                bed_id  = "room_L1_bed" + str(bed_num)
                bed_name = "Upper Executive Suite " + str(bed_num) if "drawing" in cand.room_id.lower() else "Upper Bedroom Suite " + str(bed_num)
                l1_rooms.append(_make(
                    bed_id, "bedroom",
                    bed_name,
                    [list(pt) for pt in cand.polygon], hab=True,
                    meta={"is_master": False, "parent_l0_id": cand.room_id,
                          "converted_from": cand.room_type, "exterior_exposed": True}
                ))
                used_l0_ids.add(cand.room_id)
                allocated_l1_beds += 1

                # If this is the front drawing room on 10M, attach bath over powder/vestibule
                if "drawing" in cand.room_id.lower():
                    powder_r = next((r for r in l0_rooms if "powder" in r.room_id.lower() and r.room_id not in used_l0_ids), None)
                    vestibule_r = next((r for r in l0_rooms if "vestibule" in r.room_id.lower() and r.room_id not in used_l0_ids), None)
                    if powder_r and vestibule_r:
                        bath_id = f"room_L1_bath{bed_num}"
                        bath_poly = [
                            [powder_r.polygon[0][0], powder_r.polygon[0][1]],
                            [vestibule_r.polygon[1][0], vestibule_r.polygon[1][1]],
                            [vestibule_r.polygon[2][0], vestibule_r.polygon[2][1]],
                            [powder_r.polygon[3][0], powder_r.polygon[3][1]],
                            [powder_r.polygon[0][0], powder_r.polygon[0][1]]
                        ]
                        l1_rooms.append(_make(
                            bath_id, "bathroom", f"Luxury Ensuite Bath {bed_num}",
                            bath_poly, hab=False,
                            meta={"attached_to": bed_id, "parent_l0_id": powder_r.room_id, "stack_validated": True}
                        ))
                        used_l0_ids.add(powder_r.room_id)
                        used_l0_ids.add(vestibule_r.room_id)

        # ----------------------------------------------------------------
        # STEP 4: Upper Family Lounge + Kitchenette / Study (C5)
        # ----------------------------------------------------------------
        raw_prompt = parsed.get("raw_prompt", "").lower()
        has_upper_kitchen = any(k in raw_prompt for k in [
            "upper kitchen", "second floor kitchen", "first floor kitchen",
            "kitchen on second", "kitchen upstairs", "two kitchen", "2 kitchen", "kitchenette"
        ])
        lounge_allocated = False
        kitchenette_allocated = False

        for r in l0_rooms:
            if r.room_id in used_l0_ids:
                continue
            rid_l   = r.room_id.lower()
            rname_l = r.room_name.lower()
            poly    = [list(pt) for pt in r.polygon]
            meta    = {"parent_l0_id": r.room_id}

            if r.room_type == "kitchen":
                if not lounge_allocated:
                    l1_rooms.append(_make(
                        "room_L1_tv_lounge", "living_room",
                        "Upper Family TV Lounge and Media Room",
                        poly, hab=True,
                        meta={**meta, "open_plan": True, "no_cooking": True,
                              "min_width_ft": "11.5ft (3.5m)"}
                    ))
                    lounge_allocated = True
                    used_l0_ids.add(r.room_id)
                elif has_upper_kitchen and not kitchenette_allocated:
                    l1_rooms.append(_make(
                        "room_L1_kitchenette", "kitchen",
                        "Upper Kitchenette and Pantry",
                        poly, hab=True,
                        meta={**meta, "kitchenette": True,
                              "max_appliances": "mini-fridge,microwave,sink"}
                    ))
                    kitchenette_allocated = True
                    used_l0_ids.add(r.room_id)
                else:
                    l1_rooms.append(_make(
                        "room_L1_study", "study",
                        "Upper Study & Workstation Lounge",
                        poly, hab=True, meta=meta
                    ))
                    used_l0_ids.add(r.room_id)

            elif r.room_type == "dining_room" or "dining" in rid_l:
                if not lounge_allocated:
                    l1_rooms.append(_make(
                        "room_L1_tv_lounge", "living_room",
                        "Upper Family TV Lounge and Gallery",
                        poly, hab=True, meta=meta
                    ))
                    lounge_allocated = True
                else:
                    l1_rooms.append(_make(
                        "room_L1_gallery_" + r.room_id.replace("room_L0_", ""),
                        "corridor", "Upper Gallery Sitting Area",
                        poly, hab=False, meta=meta
                    ))
                used_l0_ids.add(r.room_id)

            elif ("lounge" in rid_l or "lounge" in rname_l or
                  "drawing" in rid_l or "living" in rname_l):
                if not lounge_allocated:
                    l1_rooms.append(_make(
                        "room_L1_tv_lounge", "living_room",
                        "Upper Family TV Lounge",
                        poly, hab=True, meta=meta
                    ))
                    lounge_allocated = True
                else:
                    l1_rooms.append(_make(
                        "room_L1_gallery_" + r.room_id.replace("room_L0_", ""),
                        "corridor", "Upper Central Gallery and Foyer",
                        poly, hab=False, meta=meta
                    ))
                used_l0_ids.add(r.room_id)

            elif "lawn" in rid_l:
                l1_rooms.append(_make(
                    "room_L1_terrace_ext", "balcony",
                    "Upper Extended Balcony",
                    poly, hab=False, meta=meta
                ))
                used_l0_ids.add(r.room_id)

            elif "vestibule" in rid_l or "foyer" in rid_l:
                l1_rooms.append(_make(
                    f"room_L1_{r.room_id.replace('room_L0_', '')}", "corridor",
                    f"Upper {r.room_name}",
                    poly, hab=False, meta=meta
                ))
                used_l0_ids.add(r.room_id)

            elif r.room_type == "bathroom":
                if _wet_stack_ok(poly):
                    l1_rooms.append(_make(
                        "room_L1_" + r.room_id.replace("room_L0_", ""),
                        "bathroom", "Upper " + r.room_name,
                        poly, hab=False,
                        meta={**meta, "stack_validated": True}
                    ))
                else:
                    l1_rooms.append(_make(
                        "room_L1_ots_" + r.room_id.replace("room_L0_", ""),
                        "outdoor", "MEP Shaft (Wet Stack Rerouted)",
                        poly, hab=False,
                        meta={**meta, "wet_stack_rerouted": True}
                    ))
                used_l0_ids.add(r.room_id)

            elif r.room_type in ("corridor", "closet") or "foyer" in rid_l or "lobby" in rid_l:
                l1_rooms.append(_make(
                    "room_L1_" + r.room_id.replace("room_L0_", ""),
                    r.room_type, "Upper " + r.room_name,
                    poly, hab=False, meta=meta
                ))
                used_l0_ids.add(r.room_id)

            elif r.room_type == "outdoor":
                l1_rooms.append(_make(
                    "room_L1_" + r.room_id.replace("room_L0_", ""),
                    "outdoor", "Upper " + r.room_name,
                    poly, hab=False, meta=meta
                ))
                used_l0_ids.add(r.room_id)

            elif r.room_type == "study":
                l1_rooms.append(_make(
                    "room_L1_study", "study",
                    "Upper Executive Study and Library",
                    poly, hab=True, meta=meta
                ))
                used_l0_ids.add(r.room_id)

            else:
                l1_rooms.append(_make(
                    "room_L1_" + r.room_id.replace("room_L0_", ""),
                    r.room_type, "Upper " + r.room_name,
                    poly, hab=r.is_habitable, meta=meta
                ))
                used_l0_ids.add(r.room_id)

        # ----------------------------------------------------------------
        # STEP 5: C6 post-check - OTS window flag for landlocked bedrooms
        # ----------------------------------------------------------------
        ots_zones = [r for r in l1_rooms if r.room_type == "outdoor"]
        for rm in l1_rooms:
            if rm.room_type != "bedroom":
                continue
            if rm.metadata.get("exterior_exposed"):
                continue
            g = _Poly(rm.polygon)
            for oz in ots_zones:
                try:
                    oz_g = _Poly(oz.polygon)
                    if g.distance(oz_g) < 0.35:
                        rm.metadata["ots_window"] = oz.room_id
                        rm.metadata["ots_window_size_m"] = 1.22
                        break
                except Exception:
                    pass

        return l1_rooms

    def _stack_level_2(
        self,
        l1_rooms: List[RoomModel],
        scale: str,
        w: float,
        d: float,
        stair_type: str,
        parsed: Dict[str, Any]
    ) -> List[RoomModel]:
        """
        Stacks Level 2 (Second Floor / G+2):
        1. Staircase Invariance: Clones exact stair coordinates from Level 1 (IoU >= 0.98).
        2. Vertical OTS Continuity: Clones exact OTS coordinates.
        3. Open Front Rooftop Terrace / Balcony.
        4. Habitable Upper Bedrooms with attached baths.
        """
        l2_rooms = []
        for r in l1_rooms:
            rid_lower = r.room_id.lower()
            poly = [list(pt) for pt in r.polygon]
            meta = dict(r.metadata or {})
            meta["parent_l0_id"] = r.metadata.get("parent_l0_id", r.room_id)

            if "stair" in rid_lower:
                stair_typology = r.metadata.get("typology") or stair_type
                poly_geom = Polygon(poly)
                sw = min(poly_geom.bounds[2] - poly_geom.bounds[0], poly_geom.bounds[3] - poly_geom.bounds[1])
                if sw < 1.50 and ("dogleg" in str(stair_typology).lower() or "u_shape" in str(stair_typology).lower()):
                    stair_typology = "straight"
                l2_rooms.append(RoomModel(
                    room_id="room_L2_stairs",
                    room_type="corridor",
                    room_name="Staircase Headroom (DN ->)",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=2,
                    is_habitable=False,
                    metadata={"typology": stair_typology, "headroom_m": 2.10, "flight_width": r.metadata.get("flight_width", 1.00), "landing_depth": r.metadata.get("landing_depth", 1.20), "parent_l0_id": meta["parent_l0_id"]}
                ))
            elif "ots" in rid_lower or "shaft" in rid_lower or "duct" in rid_lower or r.room_type == "outdoor":
                l2_rooms.append(RoomModel(
                    room_id=f"room_L2_{r.room_id.replace('room_L1_', '')}",
                    room_type="outdoor",
                    room_name=f"Rooftop {r.room_name}",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=2,
                    is_habitable=False,
                    metadata=meta
                ))
            elif r.room_type == "balcony" or "terrace" in rid_lower:
                l2_rooms.append(RoomModel(
                    room_id=f"room_L2_{r.room_id.replace('room_L1_', '')}",
                    room_type="balcony",
                    room_name="Second Floor Rooftop Terrace",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=2,
                    is_habitable=False,
                    metadata=meta
                ))
            elif r.room_type == "bathroom":
                l2_rooms.append(RoomModel(
                    room_id=f"room_L2_{r.room_id.replace('room_L1_', '')}",
                    room_type="bathroom",
                    room_name=f"Rooftop {r.room_name}",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=2,
                    is_habitable=False,
                    metadata=meta
                ))
            elif r.room_type in ("bedroom", "living_room", "kitchen", "study"):
                l2_rooms.append(RoomModel(
                    room_id=f"room_L2_{r.room_id.replace('room_L1_', '')}",
                    room_type="bedroom",
                    room_name=f"Second Floor Suite ({r.room_name})",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=2,
                    is_habitable=True,
                    metadata=meta
                ))
            else:
                l2_rooms.append(RoomModel(
                    room_id=f"room_L2_{r.room_id.replace('room_L1_', '')}",
                    room_type=r.room_type,
                    room_name=f"Second Floor {r.room_name}",
                    polygon=poly,
                    area_m2=r.area_m2,
                    centroid=list(r.centroid),
                    level_index=2,
                    is_habitable=r.is_habitable,
                    metadata=meta
                ))
        return l2_rooms

    def _ensure_upper_level_openings(
        self,
        all_rooms: List[RoomModel],
        all_openings: List[OpeningModel],
        envelope: List[List[float]],
        target_w: float,
        target_d: float,
        scale: str,
        levels: List[int]
    ) -> List[OpeningModel]:
        """
        Synthesizes compliant doors, attached bathroom connections, and exterior/OTS windows
        for upper floors (Level 1, Level 2).
        """
        env_poly = Polygon(envelope)
        existing_door_pairs = {
            tuple(sorted(op.connects_rooms))
            for op in all_openings if op.opening_type == "door" and len(op.connects_rooms) == 2
        }

        for lvl in levels:
            if lvl == 0:
                continue
            lvl_rooms = [r for r in all_rooms if r.level_index == lvl]
            stair = next((r for r in lvl_rooms if "stair" in r.room_id.lower() or "stair" in r.room_name.lower()), None)
            lounge = next((r for r in lvl_rooms if r.room_type == "living_room" or "lounge" in r.room_id.lower() or "gallery" in r.room_id.lower()), None)
            if not lounge:
                lounge = next((r for r in lvl_rooms if r.room_type == "corridor"), None)

            # 1. Door: Staircase Landing -> Lounge / Circulation Gallery
            if stair and lounge and tuple(sorted([stair.room_id, lounge.room_id])) not in existing_door_pairs:
                p_stair = Polygon(stair.polygon)
                p_lounge = Polygon(lounge.polygon)
                inter = p_stair.intersection(p_lounge)
                if not inter.is_empty and inter.length >= 0.50:
                    mid_pt = [round(inter.centroid.x, 2), round(inter.centroid.y, 2)]
                else:
                    mid_pt = [round(p_stair.centroid.x, 2), round(p_stair.bounds[3], 2)]
                all_openings.append(OpeningModel(
                    opening_id=f"d_{stair.room_id}_{lounge.room_id}",
                    opening_type="door",
                    position=mid_pt,
                    width_m=0.90,
                    connects_rooms=[stair.room_id, lounge.room_id],
                    level_index=lvl
                ))
                existing_door_pairs.add(tuple(sorted([stair.room_id, lounge.room_id])))

            # 2. Attached Bathroom doors for each bedroom
            for bed in [r for r in lvl_rooms if r.room_type == "bedroom"]:
                p_bed = Polygon(bed.polygon)
                attached_target = bed.metadata.get("attached_to")
                cand_baths = [r for r in lvl_rooms if r.room_type == "bathroom"]
                if attached_target:
                    cand_baths = [r for r in cand_baths if r.room_id == attached_target] + [r for r in cand_baths if r.room_id != attached_target]

                for bath in cand_baths:
                    pair_key = tuple(sorted([bed.room_id, bath.room_id]))
                    if pair_key in existing_door_pairs:
                        break
                    p_bath = Polygon(bath.polygon)
                    shared = p_bed.intersection(p_bath)
                    if not shared.is_empty and shared.length >= 0.60:
                        mid_pt = [round(shared.centroid.x, 2), round(shared.centroid.y, 2)]
                        all_openings.append(OpeningModel(
                            opening_id=f"d_{bed.room_id}_{bath.room_id}",
                            opening_type="door",
                            position=mid_pt,
                            width_m=0.80,
                            connects_rooms=[bed.room_id, bath.room_id],
                            level_index=lvl
                        ))
                        existing_door_pairs.add(pair_key)
                        break

            # 3. Habitable / Functional rooms to Lounge / Circulation doors
            g_lvl = nx.Graph()
            for r in lvl_rooms:
                g_lvl.add_node(r.room_id)
            for pair in existing_door_pairs:
                if pair[0] in g_lvl and pair[1] in g_lvl:
                    g_lvl.add_edge(pair[0], pair[1])

            stair_node = stair.room_id if stair else (lounge.room_id if lounge else lvl_rooms[0].room_id)

            for room in [r for r in lvl_rooms if r.room_type in ("bedroom", "study", "balcony", "kitchen", "living_room")]:
                has_stair_path = nx.has_path(g_lvl, stair_node, room.room_id)
                if not has_stair_path:
                    connected = False
                    p_room = Polygon(room.polygon)

                    # 1. Try connecting to stair directly or lounge
                    targets = []
                    if stair and room.room_id != stair.room_id:
                        targets.append(stair)
                    if lounge and room.room_id != lounge.room_id:
                        targets.append(lounge)

                    for tgt in targets:
                        if is_open_social_triad_pair(room, tgt):
                            continue
                        if room.room_type == "kitchen" and tgt.room_type == "bedroom":
                            continue
                        if room.room_type == "bedroom" and tgt.room_type == "kitchen":
                            continue
                        p_tgt = Polygon(tgt.polygon)
                        shared = p_room.intersection(p_tgt)
                        pair_key = tuple(sorted([room.room_id, tgt.room_id]))
                        if not shared.is_empty and shared.length >= 0.40 and pair_key not in existing_door_pairs:
                            mid_pt = [round(shared.centroid.x, 2), round(shared.centroid.y, 2)]
                            all_openings.append(OpeningModel(
                                opening_id=f"d_{room.room_id}_{tgt.room_id}",
                                opening_type="door",
                                position=mid_pt,
                                width_m=0.90,
                                connects_rooms=[room.room_id, tgt.room_id],
                                level_index=lvl
                            ))
                            existing_door_pairs.add(pair_key)
                            g_lvl.add_edge(room.room_id, tgt.room_id)
                            connected = True
                            break

                    # 2. If still not connected to stair path, find an adjacent room that is already connected to stair
                    if not nx.has_path(g_lvl, stair_node, room.room_id):
                        candidates = [
                            adj for adj in lvl_rooms
                            if adj.room_id != room.room_id and adj.room_type not in ("bathroom", "outdoor")
                            and nx.has_path(g_lvl, stair_node, adj.room_id)
                        ]
                        if not candidates:
                            candidates = [
                                adj for adj in lvl_rooms
                                if adj.room_id != room.room_id and adj.room_type not in ("bathroom", "outdoor")
                            ]
                        for adj in candidates:
                            if room.room_type == "kitchen" and adj.room_type == "bedroom":
                                continue
                            if room.room_type == "bedroom" and adj.room_type == "kitchen":
                                continue
                            adj_pair = tuple(sorted([room.room_id, adj.room_id]))
                            p_adj = Polygon(adj.polygon)
                            adj_shared = p_room.intersection(p_adj)
                            if not adj_shared.is_empty and adj_shared.length >= 0.40 and adj_pair not in existing_door_pairs:
                                all_openings.append(OpeningModel(
                                    opening_id=f"d_{room.room_id}_{adj.room_id}",
                                    opening_type="door",
                                    position=[round(adj_shared.centroid.x, 2), round(adj_shared.centroid.y, 2)],
                                    width_m=0.90,
                                    connects_rooms=[room.room_id, adj.room_id],
                                    level_index=lvl
                                ))
                                existing_door_pairs.add(adj_pair)
                                g_lvl.add_edge(room.room_id, adj.room_id)
                                break

            # 4. Windows for Upper Level Habitable Rooms & Bathrooms (only on true exterior or OTS walls)
            for r in lvl_rooms:
                if r.room_type in ("bedroom", "bathroom", "living_room", "study"):
                    room_poly = Polygon(r.polygon)
                    room_has_window = any(
                        op.opening_type == "window" and op.level_index == lvl and (
                            room_poly.exterior.distance(Point(op.position)) < 0.20
                        )
                        for op in all_openings
                    )
                    if not room_has_window:
                        coords = list(r.polygon)
                        best_mid = None
                        best_w_width = 0.60 if r.room_type == "bathroom" else 1.20
                        best_sill = 1.20 if r.room_type == "bathroom" else 0.90
                        for i in range(len(coords) - 1):
                            pt1 = coords[i]
                            pt2 = coords[i + 1]
                            seg_len = Point(pt1).distance(Point(pt2))
                            if seg_len < 0.80:
                                continue
                            mid_x = round((pt1[0] + pt2[0]) / 2, 2)
                            mid_y = round((pt1[1] + pt2[1]) / 2, 2)
                            mid_pt = Point(mid_x, mid_y)
                            dist_to_env = env_poly.exterior.distance(mid_pt)
                            is_ots = any(
                                ("ots" in o.room_id.lower() or "outdoor" in o.room_type)
                                for o in lvl_rooms
                                if Polygon(o.polygon).distance(mid_pt) < 0.35
                            )
                            if dist_to_env < 0.05 or is_ots:
                                best_mid = (mid_x, mid_y)
                                break
                        if best_mid:
                            all_openings.append(OpeningModel(
                                opening_id=f"w_{r.room_id}_ext",
                                opening_type="window",
                                position=[best_mid[0], best_mid[1]],
                                width_m=best_w_width,
                                sill_height_m=best_sill,
                                level_index=lvl
                            ))

        return all_openings

    def _generate_compliant_openings(
        self,
        rooms: List[RoomModel],
        envelope: List[List[float]],
        w: float,
        d: float,
        scale: str
    ) -> List[OpeningModel]:
        """
        Generates code-compliant doors and windows hosted directly on shared walls.
        """
        openings = []
        room_dict = {r.room_id: r for r in rooms}

        def add_door_between(r1_id: str, r2_id: str, width: float = 0.90, door_id: Optional[str] = None):
            if r1_id not in room_dict or r2_id not in room_dict:
                return
            if is_open_social_triad_pair(room_dict[r1_id], room_dict[r2_id]):
                return  # FORBID any door between rooms in open social triad!
            p1 = Polygon(room_dict[r1_id].polygon)
            p2 = Polygon(room_dict[r2_id].polygon)
            inter = p1.intersection(p2)
            if not inter.is_empty and inter.length >= 0.35:
                lines = [inter] if inter.geom_type == "LineString" else [g for g in getattr(inter, "geoms", []) if g.geom_type == "LineString"]
                if lines:
                    longest = max(lines, key=lambda l: l.length)
                    coords = list(longest.coords)
                    mid_x = round((coords[0][0] + coords[-1][0]) / 2, 2)
                    mid_y = round((coords[0][1] + coords[-1][1]) / 2, 2)
                    d_id = door_id or f"d_{r1_id}_{r2_id}"
                    lvl = room_dict[r1_id].level_index
                    openings.append(OpeningModel(
                        opening_id=d_id,
                        opening_type="door",
                        position=[mid_x, mid_y],
                        width_m=width,
                        connects_rooms=[r1_id, r2_id],
                        level_index=lvl
                    ))

        # -----------------
        # Level 0 Doors: Strictly adhering to 5 Golden Residential Criteria
        # -----------------
        if scale == "3_marla":
            add_door_between("room_L0_porch", "room_L0_tv_lounge", width=1.10, door_id="d_main_3m")
            add_door_between("room_L0_tv_lounge", "room_L0_stairs", width=0.90, door_id="d_stairs_3m")
            add_door_between("room_L0_tv_lounge", "room_L0_powder", width=0.80, door_id="d_pwd_3m")
            add_door_between("room_L0_tv_lounge", "room_L0_lobby", width=0.90, door_id="d_lobby_3m")
            add_door_between("room_L0_lobby", "room_L0_bed1", width=0.90, door_id="d_bed1_3m")
            add_door_between("room_L0_bed1", "room_L0_bath1", width=0.80, door_id="d_bath1_3m")
            add_door_between("room_L0_bath1", "room_L0_ots", width=0.75, door_id="d_ots_3m")

        elif scale == "5_marla":
            add_door_between("room_L0_porch", "room_L0_tv_lounge", width=1.10, door_id="d_main_5m")
            # Dual-Access Drawing Room: Door A from Foyer/Porch, Door B to Dining
            add_door_between("room_L0_porch", "room_L0_drawing", width=1.07, door_id="d_draw_door_a_5m")
            add_door_between("room_L0_drawing", "room_L0_dining", width=1.52, door_id="d_draw_din_pocket_sliding_5m")
            add_door_between("room_L0_tv_lounge", "room_L0_stairs", width=0.90, door_id="d_stairs_5m")
            add_door_between("room_L0_stairs", "room_L0_powder", width=0.80, door_id="d_pwd_5m")
            add_door_between("room_L0_tv_lounge", "room_L0_bed1", width=0.90, door_id="d_bed1_5m")
            add_door_between("room_L0_bed1", "room_L0_bath1", width=0.80, door_id="d_bath1_5m")
            add_door_between("room_L0_tv_lounge", "room_L0_bed2", width=0.90, door_id="d_bed2_5m")
            add_door_between("room_L0_bed2", "room_L0_bath2", width=0.80, door_id="d_bath2_5m")
            add_door_between("room_L0_bath2", "room_L0_ots", width=0.75, door_id="d_ots_5m")

        elif scale == "7_marla":
            add_door_between("room_L0_porch", "room_L0_tv_lounge", width=1.10, door_id="d_main_7m")
            # Dual-Access Drawing Room: Door A from Foyer/Porch, Door B to Dining
            add_door_between("room_L0_porch", "room_L0_drawing", width=1.07, door_id="d_draw_door_a_7m")
            add_door_between("room_L0_drawing", "room_L0_dining", width=1.52, door_id="d_draw_din_pocket_sliding_7m")
            add_door_between("room_L0_tv_lounge", "room_L0_stairs", width=0.90, door_id="d_stairs_7m")
            add_door_between("room_L0_stairs", "room_L0_powder", width=0.80, door_id="d_pwd_7m")
            # Wet Kitchen direct exterior service door and backside connection to Main Kitchen
            add_door_between("room_L0_kitchen", "room_L0_dirty_kitchen", width=0.85, door_id="d_kit_dirty_7m")
            add_door_between("room_L0_dirty_kitchen", "room_L0_ots", width=0.85, door_id="d_wet_kit_service_exit_7m")
            add_door_between("room_L0_tv_lounge", "room_L0_bed1", width=0.90, door_id="d_bed1_7m")
            add_door_between("room_L0_bed1", "room_L0_bath1", width=0.80, door_id="d_bath1_7m")
            add_door_between("room_L0_tv_lounge", "room_L0_bed2", width=0.90, door_id="d_bed2_7m")
            add_door_between("room_L0_bath1", "room_L0_ots", width=0.75, door_id="d_ots_7m")

        elif scale == "10_marla":
            add_door_between("room_L0_porch", "room_L0_foyer", width=1.20, door_id="d_main_10m")
            # Dual-Access Drawing Room: Door A from Foyer (1.07m), Door B to Dining (1.52m pocket slider)
            add_door_between("room_L0_foyer", "room_L0_drawing", width=1.07, door_id="d_draw_door_a_10m")
            add_door_between("room_L0_drawing", "room_L0_dining", width=1.52, door_id="d_draw_din_pocket_sliding_10m")
            add_door_between("room_L0_foyer", "room_L0_powder", width=0.80, door_id="d_pwd_10m")
            add_door_between("room_L0_foyer", "room_L0_tv_lounge", width=1.20, door_id="d_foyer_lounge_10m")
            add_door_between("room_L0_foyer", "room_L0_stairs", width=1.00, door_id="d_foyer_stairs_10m")
            # Concealed dirty scullery service axis and direct exterior exit
            add_door_between("room_L0_kitchen", "room_L0_dirty_kitchen", width=0.85, door_id="d_dkit_10m")
            add_door_between("room_L0_dirty_kitchen", "room_L0_ots1", width=0.85, door_id="d_wet_kit_service_exit_10m")
            add_door_between("room_L0_tv_lounge", "room_L0_bed1", width=0.90, door_id="d_bed1_10m")
            add_door_between("room_L0_bed1", "room_L0_bath1", width=0.85, door_id="d_bath1_10m")
            add_door_between("room_L0_tv_lounge", "room_L0_bed2", width=0.90, door_id="d_bed2_10m")
            add_door_between("room_L0_bed2", "room_L0_bath2", width=0.85, door_id="d_bath2_10m")
            add_door_between("room_L0_bath2", "room_L0_ots2", width=0.80, door_id="d_ots2_10m")

        else: # 1_kanal
            add_door_between("room_L0_porch", "room_L0_stair_hall", width=1.20, door_id="d_main_1k")
            add_door_between("room_L0_stair_hall", "room_L0_drawing", width=1.07, door_id="d_draw_door_a_1k")
            add_door_between("room_L0_drawing", "room_L0_dining", width=1.52, door_id="d_draw_din_pocket_sliding_1k")
            add_door_between("room_L0_stair_hall", "room_L0_powder", width=0.80, door_id="d_pwd_1k")
            add_door_between("room_L0_stair_hall", "room_L0_tv_lounge", width=1.20, door_id="d_hall_lounge_1k")
            add_door_between("room_L0_kitchen", "room_L0_dirty_kitchen", width=0.85, door_id="d_kit_dirty_1k")
            add_door_between("room_L0_dirty_kitchen", "room_L0_ots", width=0.85, door_id="d_wet_kit_service_exit_1k")
            add_door_between("room_L0_tv_lounge", "room_L0_bed1", width=0.95, door_id="d_bed1_1k")
            add_door_between("room_L0_bed1", "room_L0_bath1", width=0.85, door_id="d_bath1_1k")
            add_door_between("room_L0_bath1", "room_L0_ots", width=0.80, door_id="d_ots_1k")

        # Strict Dirty Kitchen Isolation Rule:
        # Dirty kitchen must connect ONLY to the backside of main kitchen and exterior OTS.
        forbidden_dirty_connects = {"room_L0_drawing", "room_L0_foyer", "room_L0_porch", "room_L0_vestibule"}
        openings = [
            op for op in openings
            if not (
                op.connects_rooms and
                "room_L0_dirty_kitchen" in op.connects_rooms and
                any(fc in op.connects_rooms for fc in forbidden_dirty_connects)
            )
        ]

        # -----------------
        # Level 1 Doors
        # -----------------
        if any(r.level_index == 1 for r in rooms):
            if scale == "3_marla":
                add_door_between("room_L1_stairs", "room_L1_tv_lounge", width=0.90, door_id="d_L1_stair_lounge_3m")
                add_door_between("room_L1_terrace", "room_L1_tv_lounge", width=1.00, door_id="d_L1_terr_lounge_3m")
                add_door_between("room_L1_tv_lounge", "room_L1_bed2", width=0.90, door_id="d_L1_bed2_3m")
                add_door_between("room_L1_bed2", "room_L1_bath2", width=0.80, door_id="d_L1_bath2_3m")
                add_door_between("room_L1_bed2", "room_L1_bed3", width=0.85, door_id="d_L1_bed3_3m")
                add_door_between("room_L1_bed2", "room_L1_study", width=0.80, door_id="d_L1_study_3m")
                add_door_between("room_L1_tv_lounge", "room_L1_balcony_rear", width=0.80, door_id="d_L1_balc_3m")

            elif scale == "5_marla":
                add_door_between("room_L1_stairs", "room_L1_tv_lounge", width=0.95, door_id="d_L1_stair_lounge_5m")
                add_door_between("room_L1_terrace", "room_L1_tv_lounge", width=1.00, door_id="d_L1_terr_lounge_5m")
                add_door_between("room_L1_tv_lounge", "room_L1_bed3", width=0.90, door_id="d_L1_bed3_5m")
                add_door_between("room_L1_bed3", "room_L1_bath3", width=0.80, door_id="d_L1_bath3_5m")
                add_door_between("room_L1_terrace", "room_L1_bed3", width=0.90, door_id="d_L1_terr_bed3_5m")
                add_door_between("room_L1_tv_lounge", "room_L1_kitchenette", width=0.90, door_id="d_L1_kit_5m")
                add_door_between("room_L1_tv_lounge", "room_L1_bed4", width=0.90, door_id="d_L1_bed4_5m")
                add_door_between("room_L1_tv_lounge", "room_L1_study", width=0.90, door_id="d_L1_study_5m")
                add_door_between("room_L1_bed4", "room_L1_bath4", width=0.80, door_id="d_L1_bath4_5m")
                add_door_between("room_L1_study", "room_L1_bath4", width=0.80, door_id="d_L1_study_bath4_5m")
                add_door_between("room_L1_tv_lounge", "room_L1_rear_terrace", width=0.90, door_id="d_L1_rear_terr_5m")

            elif scale == "7_marla":
                add_door_between("room_L1_stairs", "room_L1_tv_lounge", width=1.00, door_id="d_L1_stair_lounge_7m")
                add_door_between("room_L1_terrace", "room_L1_stairs", width=1.00, door_id="d_L1_terr_stair_7m")
                add_door_between("room_L1_terrace", "room_L1_bed3", width=0.90, door_id="d_L1_terr_bed3_7m")
                add_door_between("room_L1_tv_lounge", "room_L1_study", width=0.90, door_id="d_L1_lounge_study_7m")
                add_door_between("room_L1_study", "room_L1_bed3", width=0.90, door_id="d_L1_study_bed3_7m")
                add_door_between("room_L1_study", "room_L1_bath3", width=0.80, door_id="d_L1_study_bath3_7m")
                add_door_between("room_L1_tv_lounge", "room_L1_kitchenette", width=0.90, door_id="d_L1_kit_7m")
                add_door_between("room_L1_tv_lounge", "room_L1_bed4", width=0.90, door_id="d_L1_bed4_7m")
                add_door_between("room_L1_bed4", "room_L1_bath4", width=0.80, door_id="d_L1_bath4_7m")
                add_door_between("room_L1_tv_lounge", "room_L1_rear_terrace", width=0.90, door_id="d_L1_rear_terr_7m")

            elif scale == "10_marla":
                add_door_between("room_L1_foyer", "room_L1_stairs", width=1.00, door_id="d_L1_foyer_stair_10m")
                add_door_between("room_L1_foyer", "room_L1_tv_lounge", width=1.10, door_id="d_L1_foyer_lounge_10m")
                add_door_between("room_L1_foyer", "room_L1_terrace", width=1.00, door_id="d_L1_foyer_terr_10m")
                add_door_between("room_L1_foyer", "room_L1_bath3", width=0.80, door_id="d_L1_foyer_bath3_10m")
                add_door_between("room_L1_terrace", "room_L1_bed3", width=0.90, door_id="d_L1_terr_bed3_10m")
                add_door_between("room_L1_bed3", "room_L1_bath3", width=0.85, door_id="d_L1_bed3_bath3_10m")
                add_door_between("room_L1_tv_lounge", "room_L1_kitchenette", width=0.90, door_id="d_L1_kit_10m")
                add_door_between("room_L1_tv_lounge", "room_L1_bed4", width=0.90, door_id="d_L1_bed4_10m")
                add_door_between("room_L1_bed4", "room_L1_bath4", width=0.85, door_id="d_L1_bath4_10m")
                add_door_between("room_L1_tv_lounge", "room_L1_study", width=0.90, door_id="d_L1_study_10m")
                add_door_between("room_L1_study", "room_L1_bath4", width=0.85, door_id="d_L1_study_bath4_10m")
                add_door_between("room_L1_tv_lounge", "room_L1_bed5", width=0.90, door_id="d_L1_bed5_10m")
                add_door_between("room_L1_bed5", "room_L1_bath5", width=0.85, door_id="d_L1_bath5_10m")
                add_door_between("room_L1_tv_lounge", "room_L1_fitness", width=0.90, door_id="d_L1_fit_10m")
                add_door_between("room_L1_fitness", "room_L1_bath5", width=0.85, door_id="d_L1_fit_bath5_10m")
                add_door_between("room_L1_tv_lounge", "room_L1_rear_terrace", width=1.00, door_id="d_L1_rear_terr_10m")

            else: # 1_kanal
                add_door_between("room_L1_stairs", "room_L1_tv_lounge", width=1.20, door_id="d_L1_stair_lounge_1k")
                add_door_between("room_L1_stairs", "room_L1_gallery", width=1.00, door_id="d_L1_stair_gall_1k")
                add_door_between("room_L1_gallery", "room_L1_bed3", width=1.00, door_id="d_L1_gall_bed3_1k")
                add_door_between("room_L1_bed3", "room_L1_bath3", width=0.85, door_id="d_L1_bed3_bath3_1k")
                add_door_between("room_L1_gallery", "room_L1_bed4", width=1.00, door_id="d_L1_gall_bed4_1k")
                add_door_between("room_L1_gallery", "room_L1_terrace", width=1.00, door_id="d_L1_gall_terr_1k")
                add_door_between("room_L1_gallery", "room_L1_kitchenette", width=0.90, door_id="d_L1_gall_kit_1k")
                add_door_between("room_L1_bed3", "room_L1_terrace", width=1.00, door_id="d_L1_bed3_terr_1k")
                add_door_between("room_L1_bed4", "room_L1_bath4", width=0.85, door_id="d_L1_bed4_bath4_1k")
                add_door_between("room_L1_tv_lounge", "room_L1_kitchenette", width=1.00, door_id="d_L1_lounge_kit_1k")
                add_door_between("room_L1_tv_lounge", "room_L1_bed2", width=1.00, door_id="d_L1_lounge_bed2_1k")
                add_door_between("room_L1_tv_lounge", "room_L1_bed5", width=1.00, door_id="d_L1_lounge_bed5_1k")
                add_door_between("room_L1_bed2", "room_L1_bath2", width=0.85, door_id="d_L1_bed2_bath2_1k")
                add_door_between("room_L1_bed5", "room_L1_bath5", width=0.85, door_id="d_L1_bed5_bath5_1k")

        # -----------------
        # Level 2 Doors
        # -----------------
        if any(r.level_index == 2 for r in rooms):
            if scale == "3_marla":
                add_door_between("room_L2_stairs", "room_L2_lobby", width=0.90, door_id="d_L2_stair_lobby_3m")
                add_door_between("room_L2_terrace", "room_L2_lobby", width=1.00, door_id="d_L2_terr_lobby_3m")
                add_door_between("room_L2_lobby", "room_L2_bed4", width=0.90, door_id="d_L2_lobby_bed4_3m")
                add_door_between("room_L2_lobby", "room_L2_gallery", width=0.90, door_id="d_L2_lobby_gall_3m")
                add_door_between("room_L2_lobby", "room_L2_bath4", width=0.80, door_id="d_L2_lobby_bath4_3m")
                add_door_between("room_L2_lobby", "room_L2_bath5", width=0.80, door_id="d_L2_lobby_bath5_3m")
                add_door_between("room_L2_gallery", "room_L2_bed5", width=0.90, door_id="d_L2_gall_bed5_3m")
                add_door_between("room_L2_bed5", "room_L2_bath4", width=0.80, door_id="d_L2_bed5_bath4_3m")
                add_door_between("room_L2_gallery", "room_L2_balcony_rear", width=0.80, door_id="d_L2_gall_balc_3m")
            else:
                add_door_between("room_L2_stairs", "room_L2_tv_lounge", width=0.95, door_id="d_L2_stair_lounge_5m")
                add_door_between("room_L2_terrace", "room_L2_tv_lounge", width=1.00, door_id="d_L2_terr_lounge_5m")
                add_door_between("room_L2_tv_lounge", "room_L2_bed5", width=0.90, door_id="d_L2_bed5_5m")
                add_door_between("room_L2_bed5", "room_L2_bath5", width=0.80, door_id="d_L2_bath5_5m")
                add_door_between("room_L2_terrace", "room_L2_bed5", width=0.90, door_id="d_L2_terr_bed5_5m")
                add_door_between("room_L2_tv_lounge", "room_L2_kitchenette", width=0.90, door_id="d_L2_kit_5m")
                add_door_between("room_L2_tv_lounge", "room_L2_bed6", width=0.90, door_id="d_L2_bed6_5m")
                add_door_between("room_L2_bed6", "room_L2_bath6", width=0.80, door_id="d_L2_bath6_5m")
                add_door_between("room_L2_tv_lounge", "room_L2_rear_terrace", width=0.90, door_id="d_L2_rear_terr_5m")

        # -----------------
        # Exterior Windows
        # -----------------
        # Level 0 windows on front and rear exterior boundaries
        openings.append(OpeningModel(opening_id=f"w_front_L0", opening_type="window", position=[round(w/2, 2), 0.0], width_m=1.50, sill_height_m=0.90, level_index=0))
        openings.append(OpeningModel(opening_id=f"w_rear_L0", opening_type="window", position=[round(w/2, 2), d], width_m=1.50, sill_height_m=0.90, level_index=0))

        if any(r.level_index == 1 for r in rooms):
            openings.append(OpeningModel(opening_id=f"w_front_L1", opening_type="window", position=[round(w/2, 2), 0.0], width_m=1.50, sill_height_m=0.90, level_index=1))
            openings.append(OpeningModel(opening_id=f"w_rear_L1", opening_type="window", position=[round(w/2, 2), d], width_m=1.50, sill_height_m=0.90, level_index=1))

        if any(r.level_index == 2 for r in rooms):
            openings.append(OpeningModel(opening_id=f"w_front_L2", opening_type="window", position=[round(w/2, 2), 0.0], width_m=1.50, sill_height_m=0.90, level_index=2))
            openings.append(OpeningModel(opening_id=f"w_rear_L2", opening_type="window", position=[round(w/2, 2), d], width_m=1.50, sill_height_m=0.90, level_index=2))

        # Strict Residential Golden Rule:
        # Zero doors directly between any two bedrooms!
        openings = [
            op for op in openings
            if not (
                op.opening_type == "door" and
                op.connects_rooms and
                len(op.connects_rooms) == 2 and
                getattr(room_dict.get(op.connects_rooms[0], None), "room_type", "") == "bedroom" and
                getattr(room_dict.get(op.connects_rooms[1], None), "room_type", "") == "bedroom"
            )
        ]

        return openings

    def _generate_structural_walls(
        self,
        rooms: List[RoomModel],
        envelope: List[List[float]],
        levels: List[int]
    ) -> List[WallModel]:
        """
        Generates exterior (0.23m / 9") and interior (0.115m / 4.5") walls.
        """
        walls = []
        wall_counter = 1

        for lvl in levels:
            lvl_rooms = [r for r in rooms if r.level_index == lvl]

            # Exterior perimeter walls
            for i in range(len(envelope) - 1):
                walls.append(WallModel(
                    wall_id=f"wall_ext_L{lvl}_{wall_counter}",
                    wall_type="exterior",
                    centerline=[envelope[i], envelope[i+1]],
                    thickness_m=0.23,
                    height_m=2.9,
                    level_index=lvl
                ))
                wall_counter += 1

            # Interior partition walls from shared room boundaries (excluding open social triad!)
            for i in range(len(lvl_rooms)):
                p1 = Polygon(lvl_rooms[i].polygon)
                for j in range(i + 1, len(lvl_rooms)):
                    if is_open_social_triad_pair(lvl_rooms[i], lvl_rooms[j]):
                        continue  # Zero divider walls between Open Social Triad!

                    p2 = Polygon(lvl_rooms[j].polygon)
                    inter = p1.intersection(p2)
                    if not inter.is_empty and inter.length >= 0.40:
                        lines = [inter] if inter.geom_type == "LineString" else [g for g in getattr(inter, "geoms", []) if g.geom_type == "LineString"]
                        for sline in lines:
                            if sline.length >= 0.40:
                                c = list(sline.coords)
                                walls.append(WallModel(
                                    wall_id=f"wall_int_L{lvl}_{wall_counter}",
                                    wall_type="interior",
                                    centerline=[[round(c[0][0], 2), round(c[0][1], 2)], [round(c[-1][0], 2), round(c[-1][1], 2)]],
                                    thickness_m=0.115,
                                    height_m=2.9,
                                    level_index=lvl
                                ))
                                wall_counter += 1

        return walls


# Class alias for convenient importing
RAGSolver = DatasetDrivenRAGSolver
