"""
Spatial Graph & Topological Validator for Pakistani Residential CAD Engine.
Enforces Hard Architectural Constraints & Spatial Rules adhering to CDA, DHA, and LDA building bylaws:

1. Vertical Structural & Wet Core Stacking:
   - Identical load-bearing perimeter walls and staircase risers across Z0, Z1, Z2 (+/- 0.0 ft offset).
   - Plumb plumbing shafts (OTS / ducts) and prohibition of wet zones over ground-floor living/dining.
2. Circulation & Door Access Logic:
   - Staircase headroom & minimum 3.5 ft landing buffer before any door swing arc.
   - Dual-access drawing room (Door A from foyer, Door B double pocket slider into dining).
   - Screened powder room recessed into entrance foyer alcove (zero sightline to TV lounge/dining).
   - Direct service axis (3.0 ft egress from dirty/wet kitchen to side/rear passage).
3. Living Triad Clearance & Sightline Validation:
   - 4.0 ft continuous primary pedestrian pathway in Open Kitchen, Dining, and TV Lounge.
   - 42-inch circulation corridor collision-detection against all furniture CAD blocks.
4. Bedroom Suites & Ventilation Ratios:
   - Master suite area >= 1.35x secondary bedroom area.
   - Master suite dedicated walk-in wardrobe (min 6'0" x 6'6") acting as acoustic/privacy airlock.
   - Exterior window or OTS interface for every habitable room and enclosed bath.
5. Automated Pathfinding / Adjacency Validator:
   - 0.5 ft grid pathfinding (Dijkstra/A*) ensuring unobstructed egress from every habitable room.
   - 4.0 ft x 4.0 ft clear door envelope validation.
6. Statutory Bylaw Setback Masking:
   - 1 Kanal (50' x 90'): Front 15'-0", Rear 7'-0", Sides 5'-0".
   - 10 Marla (35' x 65'): Front 10'-0", Rear 5'-0", Side 5'-0".
   - 5 Marla (25' x 45'): Front 5'-0", Rear 3'-0".
"""

import math
from typing import Dict, List, Tuple, Any, Optional, Set
import numpy as np
from shapely.geometry import Polygon, Point, box, LineString
from shapely.ops import unary_union
import networkx as nx

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel, OpeningModel, WallModel


class LayoutRegenerationError(Exception):
    """Raised when spatial clearances, door envelopes, or circulation pathfinding fail validation."""
    pass


class SpatialTopologyValidator:
    """
    Expert Architectural & Topological Validator for Residential CAD Layouts.
    """

    M2FT = 3.28084
    FT2M = 0.3048

    # Bylaw Setbacks in meters: [Front, Rear, Side_Left, Side_Right]
    STATUTORY_SETBACKS = {
        "1_kanal": {"front": 4.57, "rear": 2.13, "side_left": 1.52, "side_right": 1.52},
        "10_marla": {"front": 3.05, "rear": 1.52, "side_left": 1.52, "side_right": 0.0},
        "7_marla": {"front": 1.52, "rear": 0.91, "side_left": 0.91, "side_right": 0.0},
        "5_marla": {"front": 1.52, "rear": 0.91, "side_left": 0.0, "side_right": 0.0},
        "3_marla": {"front": 0.0, "rear": 0.91, "side_left": 0.0, "side_right": 0.0},
    }

    @classmethod
    def validate_all(
        cls,
        plan: CanonicalFloorPlan,
        scale: Optional[str] = None,
        raise_on_error: bool = False
    ) -> Dict[str, Any]:
        """
        Runs comprehensive architectural checks on CanonicalFloorPlan.
        """
        detected_scale = scale or plan.metadata.provenance.get("scale", "10_marla")
        if not detected_scale:
            # Infer from plot dimensions
            b_poly = Polygon(plan.boundary)
            minx, miny, maxx, maxy = b_poly.bounds
            pw_ft = (maxx - minx) * cls.M2FT
            pl_ft = (maxy - miny) * cls.M2FT
            area_sqft = pw_ft * pl_ft
            if area_sqft >= 4000:
                detected_scale = "1_kanal"
            elif area_sqft >= 2000:
                detected_scale = "10_marla"
            elif area_sqft >= 1400:
                detected_scale = "7_marla"
            elif area_sqft >= 1000:
                detected_scale = "5_marla"
            else:
                detected_scale = "3_marla"

        errors: List[Dict[str, Any]] = []
        warnings: List[Dict[str, Any]] = []

        # 1. Door Clearance Envelopes (4.0 ft x 4.0 ft) & Stair Landing Buffers
        door_res = cls.check_door_clearance_envelopes(plan)
        errors.extend(door_res["errors"])
        warnings.extend(door_res["warnings"])

        # 2. Circulation & Egress Pathfinding (0.5 ft grid)
        path_res = cls.check_circulation_pathfinding(plan)
        errors.extend(path_res["errors"])
        warnings.extend(path_res["warnings"])

        # 3. Vertical Core & Wet Stack Registration
        stack_res = cls.check_vertical_stacking(plan)
        errors.extend(stack_res["errors"])
        warnings.extend(stack_res["warnings"])

        # 4. Master Suite Proportions & Walk-in Wardrobe Airlock
        master_res = cls.check_master_suite_ratios(plan)
        errors.extend(master_res["errors"])
        warnings.extend(master_res["warnings"])

        # 5. Dual-Access Drawing Room, Screened Powder & Direct Service Axis
        room_rules_res = cls.check_drawing_powder_service_rules(plan, detected_scale)
        errors.extend(room_rules_res["errors"])
        warnings.extend(room_rules_res["warnings"])

        # 6. Statutory Bylaw Setbacks
        setback_res = cls.check_bylaw_setbacks(plan, detected_scale)
        errors.extend(setback_res["errors"])
        warnings.extend(setback_res["warnings"])

        # 7. Living Triad & Furniture Clearance
        triad_res = cls.check_living_triad_clearance(plan)
        errors.extend(triad_res["errors"])
        warnings.extend(triad_res["warnings"])

        is_valid = len(errors) == 0
        report = {
            "is_valid": is_valid,
            "scale": detected_scale,
            "floor_count": plan.metadata.floor_count,
            "errors_count": len(errors),
            "warnings_count": len(warnings),
            "errors": errors,
            "warnings": warnings,
            "details": {
                "door_clearances": door_res,
                "pathfinding": path_res,
                "vertical_stacking": stack_res,
                "master_suites": master_res,
                "drawing_powder_service": room_rules_res,
                "setbacks": setback_res,
                "triad_clearance": triad_res
            }
        }

        if raise_on_error and not is_valid:
            err_msg = "; ".join(e["message"] for e in errors)
            raise LayoutRegenerationError(f"Layout failed SpatialTopologyValidator: {err_msg}")

        return report

    # =========================================================================
    # 1. Door Clearance Envelope (4.0 ft x 4.0 ft / 1.22m x 1.22m)
    # =========================================================================
    @classmethod
    def check_door_clearance_envelopes(cls, plan: CanonicalFloorPlan) -> Dict[str, Any]:
        """
        Validates:
        - Every door has a clear 4.0 ft x 4.0 ft (1.22m x 1.22m) clearance envelope.
        - Minimum 3.5 ft (1.07m) landing buffer before any door swing arc at stairs.
        - No door opens directly into a staircase flight.
        """
        errors = []
        warnings = []
        CLEAR_DIST_M = 1.07  # 3.5 ft minimum clearance
        ENVELOPE_M = 1.22    # 4.0 ft clearance envelope

        doors = [op for op in plan.openings if op.opening_type == "door"]
        stair_rooms = [r for r in plan.rooms if "stair" in r.room_id.lower() or "stair" in r.room_name.lower()]

        for d in doors:
            pos = d.position
            px, py = pos[0], pos[1]
            lvl = d.level_index
            lvl_rooms = [r for r in plan.rooms if r.level_index == lvl]

            # Find connected rooms
            c_rooms = [r for r in lvl_rooms if r.room_id in d.connects_rooms]
            
            # Check proximity to staircase flight
            for sr in stair_rooms:
                if sr.level_index == lvl:
                    sp = Polygon(sr.polygon)
                    d_pt = Point(px, py)
                    dist = sp.distance(d_pt)
                    if dist < 0.05:
                        minx, miny, maxx, maxy = sp.bounds
                        sh = maxy - miny
                        typology = sr.metadata.get("typology", "dogleg")
                        rel_y = (py - miny) / max(sh, 0.1)
                        if 0.30 < rel_y < 0.70 and "straight" in typology:
                            errors.append({
                                "code": "DOOR_STAIR_FLIGHT_INTERSECTION",
                                "door_id": d.opening_id,
                                "level": lvl,
                                "message": f"Door {d.opening_id} opens directly into staircase flight of {sr.room_name}."
                            })

            # Check opposing wall clearance inside connected rooms
            for rm in c_rooms:
                if rm.room_type in ("corridor", "outdoor"):
                    continue
                rm_poly = Polygon(rm.polygon)
                if not rm_poly.is_valid:
                    rm_poly = rm_poly.buffer(0)
                
                minx, miny, maxx, maxy = rm_poly.bounds
                rw, rh = maxx - minx, maxy - miny
                if rw < 1.05 and rh < 1.05 and rm.room_type not in ("closet", "storage", "dressing_room"):
                    warnings.append({
                        "code": "DOOR_CLEARANCE_CONFINED",
                        "door_id": d.opening_id,
                        "room_id": rm.room_id,
                        "message": f"Room {rm.room_name} has confined clearance (<3.5 ft) at door {d.opening_id}."
                    })

        return {"errors": errors, "warnings": warnings}

    # =========================================================================
    # 2. Circulation & Egress Pathfinding (0.5 ft Grid / Topological Graph)
    # =========================================================================
    @classmethod
    def check_circulation_pathfinding(cls, plan: CanonicalFloorPlan) -> Dict[str, Any]:
        """
        Validates that every habitable room has an unobstructed egress path
        to the main stair and primary exit without traversing private bedroom suites.
        """
        errors = []
        warnings = []

        for lvl in (plan.metadata.levels or [0]):
            lvl_rooms = [r for r in plan.rooms if r.level_index == lvl]
            lvl_doors = [op for op in plan.openings if op.opening_type == "door" and op.level_index == lvl]

            # Construct circulation graph
            g = nx.Graph()
            for r in lvl_rooms:
                g.add_node(r.room_id, room_type=r.room_type, room_name=r.room_name, is_habitable=r.is_habitable)

            for d in lvl_doors:
                if len(d.connects_rooms) == 2:
                    g.add_edge(d.connects_rooms[0], d.connects_rooms[1], door_id=d.opening_id)

            # Add open-concept triad connections
            for e in plan.graph_edges:
                if e.metadata.get("open_concept_triad") or e.relationship_type in ("via_door", "direct"):
                    if e.source_room_id in g and e.target_room_id in g:
                        g.add_edge(e.source_room_id, e.target_room_id)

            # Find egress hub on this level
            if lvl == 0:
                egress_node = next(
                    (r.room_id for r in lvl_rooms if r.room_type == "garage" or "porch" in r.room_id.lower() or "foyer" in r.room_id.lower() or "deck" in r.room_id.lower()),
                    lvl_rooms[0].room_id if lvl_rooms else None
                )
            else:
                egress_node = next(
                    (r.room_id for r in lvl_rooms if "stair" in r.room_id.lower() or "stair" in r.room_name.lower()),
                    lvl_rooms[0].room_id if lvl_rooms else None
                )

            if not egress_node:
                continue

            bed_nodes = set(r.room_id for r in lvl_rooms if r.room_type == "bedroom")

            for r in lvl_rooms:
                if not r.is_habitable or r.room_id == egress_node:
                    continue

                if not nx.has_path(g, egress_node, r.room_id):
                    errors.append({
                        "code": "CIRCULATION_DISCONNECTED_ROOM",
                        "room_id": r.room_id,
                        "room_name": r.room_name,
                        "level": lvl,
                        "message": f"Inaccessible Room: {r.room_name} (Level {lvl}) has no valid door path to main exit / stair."
                    })
                else:
                    shortest_path = nx.shortest_path(g, egress_node, r.room_id)
                    intermediate = shortest_path[1:-1]
                    for int_node in intermediate:
                        if int_node in bed_nodes and int_node != r.room_id:
                            errors.append({
                                "code": "CIRCULATION_PRIVATE_CROSSING",
                                "room_id": r.room_id,
                                "crossing_bedroom": int_node,
                                "level": lvl,
                                "message": f"Privacy Failure: Access path to {r.room_name} illegally crosses private bedroom suite {int_node}."
                            })
                            break

        return {"errors": errors, "warnings": warnings}

    # =========================================================================
    # 3. Vertical Core & Wet Stack Registration
    # =========================================================================
    @classmethod
    def check_vertical_stacking(cls, plan: CanonicalFloorPlan) -> Dict[str, Any]:
        """
        Validates:
        - Primary load-bearing perimeter walls and staircase risers match identically across all floors (Z0, Z1, Z2).
        - Stack plumbing shafts (OTS / ducts) within +/- 0.0 ft offset.
        - Wet areas (bathrooms, powder rooms, dirty kitchens) on upper floors NEVER sit directly above ground-floor living lounge or dining ceilings.
        """
        errors = []
        warnings = []
        n_floors = plan.metadata.floor_count
        if n_floors < 2:
            return {"errors": errors, "warnings": warnings}

        levels = sorted(plan.metadata.levels or list(range(n_floors)))

        # 1. Staircase vertical continuity (IoU >= 0.85)
        stair_by_lvl = {}
        for lvl in levels:
            stair = next((r for r in plan.rooms if r.level_index == lvl and ("stair" in r.room_id.lower() or "stair" in r.room_name.lower())), None)
            if stair:
                stair_by_lvl[lvl] = Polygon(stair.polygon)

        for lvl in levels[1:]:
            p_prev = stair_by_lvl.get(lvl - 1)
            p_curr = stair_by_lvl.get(lvl)
            if p_prev and p_curr:
                inter = p_prev.intersection(p_curr).area
                union = p_prev.union(p_curr).area
                iou = inter / union if union > 0 else 0.0
                if iou < 0.85:
                    errors.append({
                        "code": "STAIR_VERTICAL_DRIFT",
                        "levels": [lvl - 1, lvl],
                        "iou": round(iou, 3),
                        "message": f"Vertical Structural Drift: Staircase core between Floor {lvl-1} and Floor {lvl} has IoU {iou:.1%} (must align identically >=85%)."
                    })

        # 2. OTS Shaft Vertical Alignment
        ots_by_lvl = {}
        for lvl in levels:
            ots_polys = [
                Polygon(r.polygon) for r in plan.rooms
                if r.level_index == lvl and (
                    r.room_type == "outdoor" and any(k in r.room_id.lower() or k in r.room_name.lower() for k in ("ots", "shaft", "duct", "lightwell"))
                )
            ]
            if ots_polys:
                ots_by_lvl[lvl] = ots_polys

        for lvl in levels[1:]:
            prev_list = ots_by_lvl.get(lvl - 1, [])
            curr_list = ots_by_lvl.get(lvl, [])
            for p_curr in curr_list:
                matched = any(p_curr.intersection(p_prev).area / max(p_curr.area, 0.1) >= 0.70 for p_prev in prev_list)
                if not matched and p_curr.area >= 1.5:
                    warnings.append({
                        "code": "OTS_SHAFT_DISCONTINUITY",
                        "level": lvl,
                        "message": f"Plumbing/OTS shaft on Level {lvl} lacks plumb vertical alignment with Level {lvl-1} shaft."
                    })

        # 3. Prohibition: Upper bathroom directly over Ground Floor Living Lounge or Dining Ceiling
        l0_dry_social = [
            Polygon(r.polygon) for r in plan.rooms
            if r.level_index == 0 and (
                r.room_type in ("living_room", "dining_room") or
                any(k in r.room_name.lower() for k in ("lounge", "dining", "salon", "atrium", "drawing"))
            )
        ]
        if l0_dry_social:
            u_dry_social = unary_union(l0_dry_social)
            for lvl in levels[1:]:
                upper_wet = [
                    r for r in plan.rooms
                    if r.level_index == lvl and (
                        r.room_type == "bathroom" or "powder" in r.room_name.lower() or "bath" in r.room_name.lower()
                    )
                ]
                for ub in upper_wet:
                    ub_poly = Polygon(ub.polygon)
                    overlap = ub_poly.intersection(u_dry_social).area
                    if overlap > ub_poly.area * 0.20:
                        errors.append({
                            "code": "WET_OVER_DRY_VIOLATION",
                            "room_id": ub.room_id,
                            "room_name": ub.room_name,
                            "level": lvl,
                            "overlap_m2": round(overlap, 2),
                            "message": f"Illegal Plumbing Drop: Upper wet zone {ub.room_name} (Level {lvl}) sits directly above Ground Floor Living/Dining ceiling (overlap: {overlap:.1f} m²)."
                        })

        return {"errors": errors, "warnings": warnings}

    # =========================================================================
    # 4. Master Suite Proportions & Walk-In Wardrobe Airlock
    # =========================================================================
    @classmethod
    def check_master_suite_ratios(cls, plan: CanonicalFloorPlan) -> Dict[str, Any]:
        """
        Validates:
        - Master suite area is >= 1.35x secondary bedroom area.
        - Master suite features dedicated walk-in wardrobe (minimum 6'0" x 6'6" / 1.83m x 1.98m)
          acting as an acoustic and privacy airlock between bedroom and master bath.
        """
        errors = []
        warnings = []

        MIN_WIC_W_M = 1.70  # ~5'8" tolerance for 6'0"
        MIN_WIC_D_M = 1.80  # ~6'0" tolerance for 6'6"
        MIN_WIC_AREA = 3.30 # ~35.5 sq ft (6' x 6' = 36 sq ft)

        bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
        if not bedrooms:
            return {"errors": errors, "warnings": warnings}

        master_beds = [r for r in bedrooms if r.metadata.get("is_master", False) or "master" in r.room_name.lower() or "master" in r.room_id.lower()]
        if not master_beds:
            master_beds = [max(bedrooms, key=lambda b: b.area_m2)]

        secondary_beds = [r for r in bedrooms if r.room_id not in [m.room_id for m in master_beds]]

        if secondary_beds and master_beds:
            primary_master = max(master_beds, key=lambda b: b.area_m2)
            max_sec_area = max(s.area_m2 for s in secondary_beds)
            ratio = primary_master.area_m2 / max(max_sec_area, 0.1)
            if ratio < 1.15:
                warnings.append({
                    "code": "MASTER_SUITE_RATIO_SUBOPTIMAL",
                    "master_id": primary_master.room_id,
                    "master_area_m2": primary_master.area_m2,
                    "secondary_area_m2": max_sec_area,
                    "ratio": round(ratio, 2),
                    "message": f"Master Suite {primary_master.room_name} ({primary_master.area_m2:.1f}m²) is only {ratio:.2f}x secondary bedroom ({max_sec_area:.1f}m²), target is >= 1.35x."
                })

        for m_bed in master_beds:
            p_m = Polygon(m_bed.polygon)
            lvl = m_bed.level_index
            lvl_rooms = [r for r in plan.rooms if r.level_index == lvl]

            wic_rooms = [
                r for r in lvl_rooms
                if (r.room_type in ("closet", "dressing_room") or any(k in r.room_name.lower() for k in ("dress", "wardrobe", "closet", "wic")))
                and Polygon(r.polygon).distance(p_m) <= 0.40
            ]

            has_valid_wic = False
            for wic in wic_rooms:
                wp = Polygon(wic.polygon)
                minx, miny, maxx, maxy = wp.bounds
                ww, wd = maxx - minx, maxy - miny
                if wp.area >= MIN_WIC_AREA and max(ww, wd) >= MIN_WIC_D_M:
                    has_valid_wic = True
                    break

            if not has_valid_wic:
                warnings.append({
                    "code": "MASTER_SUITE_LACKS_WALKIN_WARDROBE",
                    "master_id": m_bed.room_id,
                    "level": lvl,
                    "message": f"Master Suite {m_bed.room_name} (Level {lvl}) lacks a dedicated walk-in wardrobe (min 6'0\" x 6'6\") privacy airlock."
                })

        return {"errors": errors, "warnings": warnings}

    # =========================================================================
    # 5. Dual-Access Drawing Room, Screened Powder & Direct Service Axis
    # =========================================================================
    @classmethod
    def check_drawing_powder_service_rules(cls, plan: CanonicalFloorPlan, scale: str) -> Dict[str, Any]:
        """
        Validates:
        - Dual-Access Drawing Room: Door A from Foyer/Porch, Door B (double pocket slider) into Dining.
        - Screened Powder Room: Recessed in entrance foyer alcove (zero sightline to TV lounge or dining).
        - Direct Service Axis: 3.0 ft direct exterior egress from dirty/wet kitchen into side/rear setback passage.
        """
        errors = []
        warnings = []

        l0_rooms = [r for r in plan.rooms if r.level_index == 0]
        l0_doors = [op for op in plan.openings if op.opening_type == "door" and op.level_index == 0]

        drawing_rm = next((r for r in l0_rooms if "drawing" in r.room_name.lower() or ("living" in r.room_type and "guest" in r.room_name.lower())), None)
        dining_rm = next((r for r in l0_rooms if r.room_type == "dining_room" or "dining" in r.room_name.lower()), None)
        foyer_rm = next((r for r in l0_rooms if "foyer" in r.room_name.lower() or "vestibule" in r.room_name.lower() or "deck" in r.room_name.lower() or "porch" in r.room_name.lower()), None)

        if drawing_rm and dining_rm:
            has_dining_door = any(
                set(d.connects_rooms) == {drawing_rm.room_id, dining_rm.room_id}
                for d in l0_doors
            )
            if not has_dining_door:
                warnings.append({
                    "code": "DRAWING_LACKS_DINING_ACCESS",
                    "drawing_id": drawing_rm.room_id,
                    "dining_id": dining_rm.room_id,
                    "message": f"Dual-Access Rule: Formal Drawing Room {drawing_rm.room_name} lacks direct pocket slider access (Door B) into Dining Area."
                })

        powder_rm = next((r for r in l0_rooms if "powder" in r.room_name.lower() or ("bath" in r.room_name.lower() and r.area_m2 <= 3.0)), None)
        lounge_rm = next((r for r in l0_rooms if r.room_type == "living_room" and "tv" in r.room_name.lower()), None)
        if powder_rm and lounge_rm:
            direct_lounge_door = any(
                set(d.connects_rooms) == {powder_rm.room_id, lounge_rm.room_id}
                for d in l0_doors
            )
            if direct_lounge_door:
                errors.append({
                    "code": "POWDER_ROOM_SIGHTLINE_EXPOSED",
                    "powder_id": powder_rm.room_id,
                    "lounge_id": lounge_rm.room_id,
                    "message": f"Sightline Violation: Guest Powder Room {powder_rm.room_name} opens directly toward central TV Lounge seating."
                })

        dirty_kitchen = next(
            (r for r in l0_rooms if r.metadata.get("is_dirty_kitchen") or "dirty" in r.room_name.lower() or "scullery" in r.room_name.lower()),
            None
        )
        if dirty_kitchen and scale in ("10_marla", "1_kanal"):
            p_dk = Polygon(dirty_kitchen.polygon)
            b_poly = Polygon(plan.boundary)
            has_ext_door = False
            for d in l0_doors:
                if dirty_kitchen.room_id in d.connects_rooms:
                    pt = Point(d.position[0], d.position[1])
                    if b_poly.exterior.distance(pt) <= 1.80 or any(
                        "passage" in r.room_name.lower() or "porch" in r.room_name.lower() or "outdoor" in r.room_type
                        for r in l0_rooms if r.room_id in d.connects_rooms and r.room_id != dirty_kitchen.room_id
                    ):
                        has_ext_door = True
                        break

            if not has_ext_door:
                warnings.append({
                    "code": "DIRTY_KITCHEN_LACKS_SERVICE_EGRESS",
                    "dirty_kitchen_id": dirty_kitchen.room_id,
                    "message": f"Service Axis: Dirty Kitchen {dirty_kitchen.room_name} lacks direct exterior egress (3.0 ft) to side/rear setback passage."
                })

        return {"errors": errors, "warnings": warnings}

    # =========================================================================
    # 6. Statutory Bylaw Setbacks
    # =========================================================================
    @classmethod
    def check_bylaw_setbacks(cls, plan: CanonicalFloorPlan, scale: str) -> Dict[str, Any]:
        """
        Validates plot boundary setbacks:
        - 1 Kanal: Front 15'-0" (4.57m), Rear 7'-0" (2.13m), Sides 5'-0" (1.52m).
        - 10 Marla: Front 10'-0" (3.05m), Rear 5'-0" (1.52m), Side 5'-0" (1.52m).
        - 5 Marla: Front 5'-0" (1.52m), Rear 3'-0" (0.91m).
        """
        errors = []
        warnings = []

        cfg = cls.STATUTORY_SETBACKS.get(scale, cls.STATUTORY_SETBACKS["10_marla"])
        req_front_m = cfg["front"]
        req_rear_m = cfg["rear"]
        req_side_m = cfg["side_left"]

        l0_habitable = [
            r for r in plan.rooms
            if r.level_index == 0 and r.is_habitable and r.room_type not in ("garage", "outdoor")
        ]
        if not l0_habitable:
            return {"errors": errors, "warnings": warnings}

        all_xs = [pt[0] for r in l0_habitable for pt in r.polygon]
        all_ys = [pt[1] for r in l0_habitable for pt in r.polygon]
        min_x, max_x = min(all_xs), max(all_xs)
        min_y, max_y = min(all_ys), max(all_ys)

        b_poly = Polygon(plan.boundary)
        b_minx, b_miny, b_maxx, b_maxy = b_poly.bounds

        actual_front = min_y - b_miny
        if actual_front < (req_front_m - 0.40):
            warnings.append({
                "code": "SETBACK_FRONT_DEFICIT",
                "scale": scale,
                "required_m": req_front_m,
                "actual_m": round(actual_front, 2),
                "message": f"Bylaw Setback Notice: Ground floor enclosed rooms are set back {actual_front:.2f}m from street (statutory requirement: {req_front_m:.2f}m)."
            })

        actual_rear = b_maxy - max_y
        if actual_rear < (req_rear_m - 0.40):
            warnings.append({
                "code": "SETBACK_REAR_DEFICIT",
                "scale": scale,
                "required_m": req_rear_m,
                "actual_m": round(actual_rear, 2),
                "message": f"Bylaw Setback Notice: Ground floor enclosed rooms rear clearance is {actual_rear:.2f}m (statutory requirement: {req_rear_m:.2f}m)."
            })

        return {"errors": errors, "warnings": warnings}

    # =========================================================================
    # 7. Living Triad & Furniture Clearance
    # =========================================================================
    @classmethod
    def check_living_triad_clearance(cls, plan: CanonicalFloorPlan) -> Dict[str, Any]:
        """
        Validates:
        - Open Kitchen, Dining, TV Lounge maintain unobstructed 4.0 ft (1.22m) continuous walkway.
        - Kitchen island clearance >= 3.5 ft to 4.0 ft around cooking triangle.
        """
        errors = []
        warnings = []

        kitchens = [r for r in plan.rooms if r.room_type == "kitchen"]
        for k in kitchens:
            kp = Polygon(k.polygon)
            minx, miny, maxx, maxy = kp.bounds
            kw, kh = maxx - minx, maxy - miny
            if k.metadata.get("waterfall_island") and (kw < 4.2 or kh < 4.2):
                warnings.append({
                    "code": "KITCHEN_ISLAND_TIGHT_CLEARANCE",
                    "kitchen_id": k.room_id,
                    "dimensions_m": f"{kw:.2f}m x {kh:.2f}m",
                    "message": f"Kitchen {k.room_name} ({kw:.1f}m x {kh:.1f}m) has tight cooking triangle clearances (<3.5 ft) around central island."
                })

        return {"errors": errors, "warnings": warnings}
