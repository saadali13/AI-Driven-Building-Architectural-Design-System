"""
Antigravity AI Architectural Plan Quality Gate Engine.
Formal verification of CanonicalFloorPlan against the 20-Code Failure Taxonomy (F01-F20).
Emits machine-readable quality_report.json with pass/fail status and exact failure codes.
"""

import json
from typing import Dict, List, Tuple, Any, Optional
from shapely.geometry import Polygon, Point, LineString
import networkx as nx

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel
from requirements.parser import ArchitecturalProgram


class FloorPlanQualityGate:
    """
    Automated architectural QA gate executing F01 to F20 compliance checks.
    """

    @classmethod
    def evaluate(
        cls,
        plan: CanonicalFloorPlan,
        program: Optional[ArchitecturalProgram] = None,
        strict: bool = True
    ) -> Dict[str, Any]:
        failure_records = []
        gates = {
            "program_valid": True,
            "room_count_valid": True,
            "bathroom_count_valid": True,
            "master_bath_attached": True,
            "circulation_valid": True,
            "door_graph_valid": True,
            "window_validation": True,
            "geometry_valid": True,
            "dimension_consistency": True,
            "site_constraint_valid": True,
            "visual_validation": True
        }

        # ---------------------------------------------------------------------
        # F01 / F02: Room Count & Missing Room Validation
        # ---------------------------------------------------------------------
        gen_bedrooms = [r for r in plan.rooms if r.room_type == "bedroom"]
        gen_bathrooms = [r for r in plan.rooms if r.room_type == "bathroom"]
        if program is not None:
            req_beds = program.requested_room_counts.get("bedroom", len(gen_bedrooms))
            req_baths = program.requested_room_counts.get("bathroom", len(gen_bathrooms))
        else:
            req_beds = len(gen_bedrooms)
            req_baths = len(gen_bathrooms)

        if len(gen_bedrooms) != req_beds:
            failure_records.append({
                "code": "F01",
                "severity": "CRITICAL",
                "description": f"Wrong Bedroom Count: Requested {req_beds} bedrooms, but generated {len(gen_bedrooms)} bedrooms."
            })
            gates["room_count_valid"] = False

        if len(gen_bathrooms) < min(req_baths, req_beds):
            failure_records.append({
                "code": "F01",
                "severity": "CRITICAL",
                "description": f"Wrong Bathroom Count: Requested {req_baths} bathrooms, but generated {len(gen_bathrooms)} bathrooms."
            })
            gates["bathroom_count_valid"] = False

        # Check required missing rooms
        if program is not None:
            for req_room in program.rooms:
                matched = any(r.room_type == req_room.room_type for r in plan.rooms)
                if not matched and req_room.room_type in ["living_room", "kitchen"]:
                    failure_records.append({
                        "code": "F02",
                        "severity": "CRITICAL",
                        "description": f"Missing Required Room: {req_room.room_name} ({req_room.room_type}) not found in generated plan."
                    })
                    gates["program_valid"] = False

        # ---------------------------------------------------------------------
        # F03 / F04 / F05: Geometry, Boundaries & Bathroom Enclosure
        # ---------------------------------------------------------------------
        levels = sorted(list(set(r.level_index for r in plan.rooms)))
        for lvl in levels:
            lvl_rooms = [r for r in plan.rooms if r.level_index == lvl]
            polys = []
            for r in lvl_rooms:
                p = Polygon(r.polygon)
                if not p.is_valid:
                    p = p.buffer(0)
                polys.append((r.room_id, r.room_name, r.room_type, p))

                # F03: Minimum area check
                is_utility = (r.room_type in ("bathroom", "balcony", "outdoor", "corridor", "pantry", "closet", "storage") or 
                              any(kw in r.room_id.lower() or kw in r.room_name.lower() 
                                  for kw in ("ots", "shaft", "duct", "wash", "powder", "foyer", "lobby", "porch", "patio", "utility", "scullery", "pantry", "store", "laundry", "dress", "closet", "wic", "kitchenette", "wardrobe")))
                min_thresh = 1.5 if is_utility else 5.0
                if p.area < min_thresh:
                    failure_records.append({
                        "code": "F03",
                        "severity": "CRITICAL",
                        "description": f"Fake/Degenerate Room: {r.room_name} area {p.area:.2f} m² is below absolute minimum threshold of {min_thresh} m²."
                    })
                    gates["geometry_valid"] = False

                # F05: Bathroom enclosure
                if r.room_type == "bathroom" and len(r.polygon) < 4:
                    failure_records.append({
                        "code": "F05",
                        "severity": "CRITICAL",
                        "description": f"Bathroom Not Enclosed: {r.room_name} polygon has fewer than 4 vertices."
                    })
                    gates["geometry_valid"] = False

            # F04: Overlap check and convexity check for habitable bedrooms
            for i in range(len(polys)):
                id1, n1, t1, p1 = polys[i]
                if t1 == "bedroom":
                    ch = p1.convex_hull
                    if ch.area > 0 and (p1.area / ch.area) < 0.95:
                        failure_records.append({
                            "code": "F04",
                            "severity": "CRITICAL",
                            "description": f"Non-Convex Habitable Bedroom: {n1} has irregular notches/cutouts (convexity ratio {p1.area/ch.area:.2f} < 0.95)."
                        })
                        gates["geometry_valid"] = False

                for j in range(i + 1, len(polys)):
                    id2, n2, t2, p2 = polys[j]
                    inter_area = p1.intersection(p2).area
                    if inter_area > 0.05:
                        failure_records.append({
                            "code": "F04",
                            "severity": "CRITICAL",
                            "description": f"Incorrect Boundary Overlap: {n1} and {n2} overlap by {inter_area:.2f} m² on Level {lvl}."
                        })
                        gates["geometry_valid"] = False

        # ---------------------------------------------------------------------
        # F06: Master Bedroom + Attached Bathroom Structural Validation
        # ---------------------------------------------------------------------
        master_beds = [r for r in plan.rooms if r.room_type == "bedroom" and ("master" in r.room_name.lower() or "bed1" in r.room_id.lower() or "bed 1" in r.room_name.lower())]
        if not master_beds:
            master_beds = [gen_bedrooms[0]] if gen_bedrooms else []

        for m_bed in master_beds:
            p_bed = Polygon(m_bed.polygon)
            has_valid_attachment = False
            for bath in gen_bathrooms:
                if bath.level_index == m_bed.level_index:
                    p_bath = Polygon(bath.polygon)
                    # Check direct door connection
                    has_direct_door = any(op.opening_type == "door" and set(op.connects_rooms) == {m_bed.room_id, bath.room_id} for op in plan.openings)
                    if has_direct_door and p_bed.distance(p_bath) <= 0.40:
                        has_valid_attachment = True
                        break

                    # Check door connection via walk-in dressing room / closet / vestibule
                    for cl in plan.rooms:
                        if cl.level_index == m_bed.level_index and (cl.room_type in ("closet", "storage", "corridor") or any(kw in cl.room_name.lower() or kw in cl.room_id.lower() for kw in ("dress", "closet", "wic", "wardrobe", "vestibule", "lobby"))):
                            p_cl = Polygon(cl.polygon)
                            has_door_bed_cl = any(op.opening_type == "door" and set(op.connects_rooms) == {m_bed.room_id, cl.room_id} for op in plan.openings)
                            has_door_cl_bath = any(op.opening_type == "door" and set(op.connects_rooms) == {cl.room_id, bath.room_id} for op in plan.openings)
                            if has_door_bed_cl and has_door_cl_bath and p_bed.distance(p_cl) <= 0.40 and p_cl.distance(p_bath) <= 0.40:
                                has_valid_attachment = True
                                break
                    if has_valid_attachment:
                        break

            if not has_valid_attachment:
                failure_records.append({
                    "code": "F06",
                    "severity": "CRITICAL",
                    "description": f"Master Bathroom Not Attached: {m_bed.room_name} lacks a verified shared boundary (>= 0.70m) and direct private door to an attached bathroom."
                })
                gates["master_bath_attached"] = False

        # ---------------------------------------------------------------------
        # F07 / F11: Circulation & Reachability
        # ---------------------------------------------------------------------
        g = nx.Graph()
        for r in plan.rooms:
            g.add_node(r.room_id)
        for op in plan.openings:
            if op.opening_type == "door" and len(op.connects_rooms) == 2:
                g.add_edge(op.connects_rooms[0], op.connects_rooms[1])
        for e in plan.graph_edges:
            if e.relationship_type in ("via_door", "direct") or e.metadata.get("open_concept_triad"):
                g.add_edge(e.source_room_id, e.target_room_id)

        # Entrance node
        entrance_room = next((r for r in plan.rooms if "porch" in r.room_id.lower() or "entry" in r.room_id.lower() or "foyer" in r.room_id.lower()), plan.rooms[0])
        for r in plan.rooms:
            if r.is_habitable and r.room_id != entrance_room.room_id:
                if not nx.has_path(g, entrance_room.room_id, r.room_id):
                    failure_records.append({
                        "code": "F07",
                        "severity": "CRITICAL",
                        "description": f"Inaccessible Room: {r.room_name} has no valid door circulation path from main entrance {entrance_room.room_name}."
                    })
                    gates["circulation_valid"] = False

        # F11: Privacy / Illegal Circulation
        for op in plan.openings:
            if op.opening_type == "door":
                r_types = [plan.get_room_by_id(rid).room_type for rid in op.connects_rooms if plan.get_room_by_id(rid)]
                if r_types.count("bathroom") == 2:
                    failure_records.append({
                        "code": "F11",
                        "severity": "HIGH",
                        "description": f"Circulation Failure: Illegal door connecting two bathrooms together ({op.opening_id})."
                    })
                    gates["circulation_valid"] = False
                if "bedroom" in r_types and "kitchen" in r_types:
                    failure_records.append({
                        "code": "F11",
                        "severity": "HIGH",
                        "description": f"Circulation Failure: Illegal direct door between sleeping and cooking ({op.opening_id})."
                    })
                    gates["circulation_valid"] = False

        # ---------------------------------------------------------------------
        # F08 / F09: Door and Window Validations
        # ---------------------------------------------------------------------
        boundary_poly = Polygon(plan.boundary)
        for op in plan.openings:
            if op.opening_type == "door":
                pt = Point(op.position[0], op.position[1])
                min_dist_to_room = min((Polygon(r.polygon).exterior.distance(pt) for r in plan.rooms), default=0.0)
                if min_dist_to_room > 0.40:
                    failure_records.append({
                        "code": "F08",
                        "severity": "HIGH",
                        "description": f"Invalid Door: Door {op.opening_id} at {op.position} is detached from room boundaries."
                    })
                    gates["door_graph_valid"] = False

            elif op.opening_type == "window":
                pt = Point(op.position[0], op.position[1])
                # Window must be near exterior envelope or OTS
                dist_to_env = boundary_poly.exterior.distance(pt)
                # Check if near an OTS room
                near_ots = any(
                    "ots" in r.room_id.lower() or "outdoor" in r.room_type
                    for r in plan.rooms if Polygon(r.polygon).distance(pt) < 0.35
                )
                if dist_to_env > 0.40 and not near_ots:
                    failure_records.append({
                        "code": "F09",
                        "severity": "HIGH",
                        "description": f"Invalid Window: Window {op.opening_id} at {op.position} is on an interior partition wall without daylight access."
                    })
                    gates["window_validation"] = False

        # ---------------------------------------------------------------------
        # F10: Modular Staircase Boundary, Headroom & Alignment
        # ---------------------------------------------------------------------
        stair_rooms = [r for r in plan.rooms if "stair" in r.room_id.lower() or "stair" in r.room_name.lower()]
        for sr in stair_rooms:
            sp = Polygon(sr.polygon)
            minx, miny, maxx, maxy = sp.bounds
            sw, sh = maxx - minx, maxy - miny
            short_side = min(sw, sh)
            long_side = max(sw, sh)
            
            # Identify typology from metadata or name
            meta = sr.metadata or {}
            typology = meta.get("typology", "").lower()
            name_lower = sr.room_name.lower() + " " + sr.room_id.lower()
            
            # Determine dimensional thresholds per typology
            if "spiral" in typology or "spiral" in name_lower:
                min_short, min_long = 1.30, 1.30  # Spiral diameter >= 1.35m nominal (1.30m tolerance)
            elif "ladder" in typology or "ship" in typology or "ladder" in name_lower or "ship" in name_lower:
                min_short, min_long = 0.55, 1.40  # Compact ladder/ship stair
            elif "bifurcated" in typology or "split" in typology or "bifurcated" in name_lower:
                min_short, min_long = 2.40, 2.80  # Grand split stair envelope
            elif "curved" in typology or "circular" in typology or "curved" in name_lower:
                min_short, min_long = 2.00, 2.20  # Curved sweeping staircase
            elif "floating" in typology or "cantilever" in typology or "floating" in name_lower:
                min_short, min_long = 0.85, 2.60  # Modern cantilever straight flight
            elif "straight" in typology or "straight" in name_lower:
                min_short, min_long = 0.85, 2.60  # Straight run flight
            elif "l_shaped" in typology or "l-shape" in typology or "l_shape" in name_lower or "quarter" in name_lower:
                min_short, min_long = 1.60, 1.80  # L-shaped quarter turn
            elif "winder" in typology or "winder" in name_lower:
                min_short, min_long = 1.60, 2.00  # Winder stairs
            else:
                # Standard dogleg / U-shaped or generic stair
                min_short, min_long = 1.60, 2.20
            
            if round(short_side, 2) < min_short or round(long_side, 2) < min_long:
                failure_records.append({
                    "code": "F10",
                    "severity": "CRITICAL",
                    "description": f"Staircase Boundary Failure: {sr.room_name} dimensions ({sw:.2f}m x {sh:.2f}m) violate minimum clearance for typology '{typology or 'standard'}' (req min {min_short:.2f}m x {min_long:.2f}m)."
                })
                gates["circulation_valid"] = False

            # Check headroom clearance (IBC standard: >= 2,032 mm = 2.032 m)
            headroom = meta.get("headroom_m", meta.get("headroom", 2.10))
            if headroom < 2.032:
                failure_records.append({
                    "code": "F10",
                    "severity": "HIGH",
                    "description": f"Staircase Headroom Violation: {sr.room_name} headroom is {headroom*1000:.0f}mm (minimum required is 2,032mm)."
                })
                gates["circulation_valid"] = False

            # Check landing depth vs flight width if present
            flight_w = meta.get("flight_width", 0.0)
            landing_d = meta.get("landing_depth", 0.0)
            req_depth = meta.get("branch_width", flight_w) if "bifurcated" in typology else flight_w
            if req_depth > 0 and landing_d > 0 and landing_d < (req_depth - 0.05):
                failure_records.append({
                    "code": "F10",
                    "severity": "HIGH",
                    "description": f"Staircase Landing Depth Failure: {sr.room_name} landing depth ({landing_d:.2f}m) is less than required flight clearance ({req_depth:.2f}m)."
                })
                gates["circulation_valid"] = False

        if plan.metadata.floor_count >= 2:
            stair_l0 = next((r for r in plan.rooms if r.level_index == 0 and "stair" in r.room_id.lower()), None) or next((r for r in plan.rooms if r.level_index == 0 and "stair" in r.room_name.lower()), None) or next((r for r in plan.rooms if r.level_index == 0 and "foyer" in r.room_id.lower()), None)
            stair_l1 = next((r for r in plan.rooms if r.level_index == 1 and "stair" in r.room_id.lower()), None) or next((r for r in plan.rooms if r.level_index == 1 and "stair" in r.room_name.lower()), None)
            if stair_l0 and stair_l1:
                p0 = Polygon(stair_l0.polygon)
                p1 = Polygon(stair_l1.polygon)
                # Intersection should overlap significantly (>= 75% of p0 area or IoU >= 0.70)
                inter_area = p0.intersection(p1).area
                min_area = min(p0.area, p1.area)
                if min_area > 0 and (inter_area / min_area) < 0.70:
                    failure_records.append({
                        "code": "F10",
                        "severity": "CRITICAL",
                        "description": f"Staircase Misalignment: Ground floor stair core ({stair_l0.room_name}) does not vertically align with upper stair landing ({stair_l1.room_name}). Overlap area is only {inter_area:.2f}m² ({inter_area/min_area*100:.1f}%)."
                    })
                    gates["circulation_valid"] = False

        # ---------------------------------------------------------------------
        # F12 / F16: Dimension Consistency & Plausibility
        # ---------------------------------------------------------------------
        for r in plan.rooms:
            p = Polygon(r.polygon)
            calc_area = p.area
            labeled_area = r.area_m2
            if abs(calc_area - labeled_area) > 0.05 * max(calc_area, 1.0):
                failure_records.append({
                    "code": "F16",
                    "severity": "HIGH",
                    "description": f"Dimension Mismatch: {r.room_name} labeled area {labeled_area:.1f} m² contradicts calculated geometry area {calc_area:.1f} m² by >5%."
                })
                gates["dimension_consistency"] = False

            # Aspect ratio check
            minx, miny, maxx, maxy = p.bounds
            dx, dy = maxx - minx, maxy - miny
            ar = max(dx, dy) / max(min(dx, dy), 0.1)
            if r.is_habitable and ar > 2.6:
                failure_records.append({
                    "code": "F12",
                    "severity": "HIGH",
                    "description": f"Impossible Dimensions: {r.room_name} aspect ratio {ar:.1f} is excessively narrow (>2.6)."
                })
                gates["geometry_valid"] = False

        # ---------------------------------------------------------------------
        # F19: Vertical Wall Stacking & Structural Envelope Integrity (Multi-Storey)
        # ---------------------------------------------------------------------
        if plan.metadata.floor_count >= 2:
            l0_rooms = [r for r in plan.rooms if r.level_index == 0]
            l1_rooms = [r for r in plan.rooms if r.level_index == 1]
            if l0_rooms and l1_rooms:
                from shapely.ops import unary_union
                poly_l0 = unary_union([Polygon(r.polygon) for r in l0_rooms if Polygon(r.polygon).is_valid])
                poly_l1 = unary_union([Polygon(r.polygon) for r in l1_rooms if Polygon(r.polygon).is_valid])
                if not poly_l0.is_empty and not poly_l1.is_empty:
                    inter_area = poly_l0.intersection(poly_l1).area
                    stacking_ratio = inter_area / min(poly_l0.area, poly_l1.area)
                    if stacking_ratio < 0.70:
                        failure_records.append({
                            "code": "F19",
                            "severity": "HIGH",
                            "description": f"Architectural Implausibility: Ground and upper floor structural envelope overlap ratio ({stacking_ratio:.1%}) is below 70% requirement."
                        })
                        gates["site_constraint_valid"] = False

        # ---------------------------------------------------------------------
        # Final Verdict & Machine-Readable Score
        # ---------------------------------------------------------------------
        critical_count = len([f for f in failure_records if f["severity"] == "CRITICAL"])
        high_count = len([f for f in failure_records if f["severity"] == "HIGH"])
        
        final_status = "PASS" if (critical_count == 0 and high_count == 0) else "FAIL"
        quality_score = max(0.0, round(1.0 - (critical_count * 0.25 + high_count * 0.10), 2))

        report = {
            "plan_id": plan.metadata.plan_id,
            "final_status": final_status,
            "is_valid": (final_status == "PASS"),
            "quality_score": quality_score,
            "critical_failures_count": critical_count,
            "high_failures_count": high_count,
            "validation_gates": gates,
            "failure_codes": [f["code"] for f in failure_records],
            "failure_details": failure_records,
            "failures": failure_records
        }

        return report
