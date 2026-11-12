"""
Plan Quality Scorer & Dataset Statistical Benchmark Engine
---------------------------------------------------------
Computes empirical architectural statistics across 91 CV-extracted real Pakistani
residential floor plans from dataset/extracted_vector_knowledge, and rigorously
evaluates synthetic CanonicalFloorPlan models against empirical distributions
and strict architectural CAD rules.
"""

import os
import glob
import json
import math
from typing import Dict, Any, List, Optional, Tuple
from shapely.geometry import Polygon

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel, WallModel, OpeningModel


class PlanQualityScorer:
    """
    Evaluates CanonicalFloorPlan instances against empirical Pakistani residential
    dataset benchmarks and architectural engineering rules.
    """

    BENCHMARKS: Dict[str, Dict[str, Any]] = {}

    @classmethod
    def load_dataset_benchmarks(cls, data_dir: Optional[str] = None) -> Dict[str, Dict[str, Any]]:
        """
        Aggregates empirical statistics across all extracted JSON plans in data_dir.
        """
        if cls.BENCHMARKS:
            return cls.BENCHMARKS

        if not data_dir:
            base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            data_dir = os.path.join(base_dir, "dataset", "extracted_vector_knowledge")

        files = glob.glob(os.path.join(data_dir, "*.json"))
        category_plans: Dict[str, List[Dict[str, Any]]] = {}

        for fpath in files:
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    data = json.load(f)
                cat = data.get("plot", {}).get("category", "unknown")
                if cat not in category_plans:
                    category_plans[cat] = []
                category_plans[cat].append(data)
            except Exception:
                continue

        benchmarks: Dict[str, Dict[str, Any]] = {}

        for cat, plans in category_plans.items():
            if not plans:
                continue

            room_counts = []
            bed_counts = []
            bath_counts = []
            bed_area_pcts = []
            lounge_area_pcts = []
            kitchen_area_pcts = []
            drawing_area_pcts = []
            porch_area_pcts = []
            stair_rel_xs = []

            for p in plans:
                rooms = p.get("rooms", [])
                plot_info = p.get("plot", {})
                dims = plot_info.get("dimensions_ft", [35.0, 65.0])
                plot_w_ft = dims[0] if len(dims) > 0 else 35.0
                plot_l_ft = dims[1] if len(dims) > 1 else 65.0
                total_plot_sqft = plot_w_ft * plot_l_ft

                n_rooms = len(rooms)
                n_bed = sum(1 for r in rooms if r.get("type") == "bedroom")
                n_bath = sum(1 for r in rooms if r.get("type") in ("bathroom", "powder_room"))

                total_room_area = sum(r.get("area_sqft", 0) for r in rooms) or total_plot_sqft

                bed_area = sum(r.get("area_sqft", 0) for r in rooms if r.get("type") == "bedroom")
                lounge_area = sum(r.get("area_sqft", 0) for r in rooms if r.get("type") == "living_room")
                kitchen_area = sum(r.get("area_sqft", 0) for r in rooms if r.get("type") == "kitchen")
                drawing_area = sum(r.get("area_sqft", 0) for r in rooms if r.get("type") == "drawing_room")
                porch_area = sum(r.get("area_sqft", 0) for r in rooms if r.get("type") == "garage")

                stair_rms = [r for r in rooms if r.get("type") in ("staircase", "stairs") or "stair" in r.get("name", "").lower()]
                for sr in stair_rms:
                    bbox = sr.get("bbox_ft", [0, 0, 0, 0])
                    sx = bbox[0] + bbox[2] / 2.0
                    stair_rel_xs.append(sx / max(plot_w_ft, 1.0))

                room_counts.append(n_rooms)
                bed_counts.append(n_bed)
                bath_counts.append(n_bath)
                bed_area_pcts.append((bed_area / total_room_area) * 100.0)
                lounge_area_pcts.append((lounge_area / total_room_area) * 100.0)
                kitchen_area_pcts.append((kitchen_area / total_room_area) * 100.0)
                drawing_area_pcts.append((drawing_area / total_room_area) * 100.0)
                porch_area_pcts.append((porch_area / total_room_area) * 100.0)

            def _mean(lst: List[float], default: float = 0.0) -> float:
                return round(sum(lst) / max(len(lst), 1), 2) if lst else default

            def _std(lst: List[float], m: float) -> float:
                if len(lst) <= 1:
                    return 0.0
                var = sum((x - m) ** 2 for x in lst) / len(lst)
                return round(math.sqrt(var), 2)

            m_rc = _mean(room_counts, 8.0)
            m_bed = _mean(bed_counts, 4.0)
            m_bath = _mean(bath_counts, 4.0)
            m_b_pct = _mean(bed_area_pcts, 32.0)
            m_l_pct = _mean(lounge_area_pcts, 18.0)
            m_k_pct = _mean(kitchen_area_pcts, 9.0)
            m_d_pct = _mean(drawing_area_pcts, 14.0)
            m_p_pct = _mean(porch_area_pcts, 16.0)

            benchmarks[cat] = {
                "sample_size": len(plans),
                "room_count": {"mean": m_rc, "std": _std(room_counts, m_rc)},
                "bed_count": {"mean": m_bed, "std": _std(bed_counts, m_bed)},
                "bath_count": {"mean": m_bath, "std": _std(bath_counts, m_bath)},
                "bedroom_area_pct": {"mean": m_b_pct, "std": _std(bed_area_pcts, m_b_pct)},
                "lounge_area_pct": {"mean": m_l_pct, "std": _std(lounge_area_pcts, m_l_pct)},
                "kitchen_area_pct": {"mean": m_k_pct, "std": _std(kitchen_area_pcts, m_k_pct)},
                "drawing_area_pct": {"mean": m_d_pct, "std": _std(drawing_area_pcts, m_d_pct)},
                "porch_area_pct": {"mean": m_p_pct, "std": _std(porch_area_pcts, m_p_pct)},
                "stair_x_rel": {"mean": _mean(stair_rel_xs, 0.45), "std": _std(stair_rel_xs, _mean(stair_rel_xs, 0.45))},
            }

        cls.BENCHMARKS = benchmarks
        return benchmarks

    @classmethod
    def score_canonical_plan(
        cls,
        plan: CanonicalFloorPlan,
        plot_category: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Rigorously scores a CanonicalFloorPlan against:
        1. Strict Hard Rules (No overlaps, bed-bath attachment, stacked stairs, door access).
        2. Statistical alignment with empirical ground truth for the plot category.
        """
        benchmarks = cls.load_dataset_benchmarks()

        # Determine plot category
        cat = plot_category
        if not cat:
            cat = getattr(plan.metadata, "plot_category", None)
            if not cat and hasattr(plan.metadata, "provenance"):
                cat = (plan.metadata.provenance or {}).get("scale")
            if not cat:
                cat = "10_marla"

        cat = cat.lower().replace(" ", "_")
        if cat not in benchmarks:
            cat = "10_marla" if "10" in cat else ("5_marla" if "5" in cat else ("1_kanal" if "kanal" in cat else "10_marla"))

        ref_stats = benchmarks.get(cat, benchmarks.get("10_marla", {}))

        rooms = plan.rooms
        walls = plan.walls
        openings = plan.openings
        levels = plan.metadata.levels if plan.metadata.levels else [0, 1]

        hard_rules: Dict[str, Dict[str, Any]] = {}

        # -------------------------------------------------------------
        # Hard Rule 1: No room polygon containment or significant overlap
        # -------------------------------------------------------------
        containment_violations = []
        for i, r1 in enumerate(rooms):
            if len(r1.polygon) < 3:
                continue
            poly1 = Polygon(r1.polygon)
            for j, r2 in enumerate(rooms):
                if i >= j or r1.level_index != r2.level_index or len(r2.polygon) < 3:
                    continue
                poly2 = Polygon(r2.polygon)
                if poly1.intersects(poly2):
                    inter_area = poly1.intersection(poly2).area
                    min_area = min(poly1.area, poly2.area)
                    if min_area > 0 and (inter_area / min_area) > 0.08:
                        # Allow open-concept visual regions only if explicitly tagged
                        is_open = (r1.metadata or {}).get("open_concept") or (r2.metadata or {}).get("open_concept")
                        if not is_open:
                            containment_violations.append(
                                f"{r1.room_name} and {r2.room_name} overlap by {inter_area:.2f} m² ({(inter_area/min_area)*100:.1f}%)"
                            )

        hard_rules["no_room_containment"] = {
            "name": "No Room Containment (Zero Nested Rooms)",
            "passed": len(containment_violations) == 0,
            "violations": containment_violations,
            "weight": 15
        }

        # -------------------------------------------------------------
        # Hard Rule 2: Every bedroom must have an attached or ensuite bathroom
        # -------------------------------------------------------------
        bedrooms = [r for r in rooms if r.room_type == "bedroom"]
        bathrooms = [r for r in rooms if r.room_type in ("bathroom", "powder_room")]
        bed_bath_unattached = []

        for bed in bedrooms:
            bed_poly = Polygon(bed.polygon)
            connected = False
            for bath in bathrooms:
                if bath.level_index != bed.level_index:
                    continue
                bath_poly = Polygon(bath.polygon)
                for op in openings:
                    if op.opening_type == "door" and op.level_index == bed.level_index:
                        c_rooms = getattr(op, "connects_rooms", [])
                        if bed.room_id in c_rooms and bath.room_id in c_rooms:
                            connected = True
                            break
                if connected:
                    break
                if bed_poly.distance(bath_poly) <= 0.45:
                    connected = True
                    break

            # Check walk-in dressing suite buffer (Bed -> Dressing -> Bath)
            if not connected:
                dressings = [r for r in rooms if r.level_index == bed.level_index and ("dress" in r.room_name.lower() or "closet" in r.room_name.lower())]
                for dr in dressings:
                    dr_poly = Polygon(dr.polygon)
                    bed_to_dr = False
                    for op in openings:
                        if op.opening_type == "door" and op.level_index == bed.level_index:
                            c_rooms = getattr(op, "connects_rooms", [])
                            if bed.room_id in c_rooms and dr.room_id in c_rooms:
                                bed_to_dr = True
                                break
                    if not bed_to_dr and bed_poly.distance(dr_poly) <= 0.45:
                        bed_to_dr = True

                    if bed_to_dr:
                        for bath in bathrooms:
                            if bath.level_index != bed.level_index:
                                continue
                            bath_poly = Polygon(bath.polygon)
                            for op in openings:
                                if op.opening_type == "door" and op.level_index == bed.level_index:
                                    c_rooms = getattr(op, "connects_rooms", [])
                                    if dr.room_id in c_rooms and bath.room_id in c_rooms:
                                        connected = True
                                        break
                            if connected:
                                break
                            if dr_poly.distance(bath_poly) <= 0.45:
                                connected = True
                                break
                    if connected:
                        break

            if not connected:
                bed_bath_unattached.append(f"{bed.room_name} (L{bed.level_index}) has no attached bathroom")

        hard_rules["bedroom_bath_attachment"] = {
            "name": "Bedroom Attached Bathroom Pairing",
            "passed": len(bed_bath_unattached) == 0,
            "violations": bed_bath_unattached,
            "weight": 15
        }

        # -------------------------------------------------------------
        # Hard Rule 3: Vertical Staircase Stacking & Continuity Across Floors
        # -------------------------------------------------------------
        l0_stairs = [r for r in rooms if r.level_index == 0 and ("stair" in r.room_name.lower() or r.room_type in ("stairs", "staircase"))]
        l1_stairs = [r for r in rooms if r.level_index == 1 and ("stair" in r.room_name.lower() or r.room_type in ("stairs", "staircase"))]

        stair_stacked = False
        stair_err = []
        if len(levels) >= 2:
            if not l0_stairs:
                stair_err.append("No staircase room detected on Ground Floor (Level 0).")
            if not l1_stairs:
                stair_err.append("No staircase room detected on First Floor (Level 1).")
            if l0_stairs and l1_stairs:
                p0 = Polygon(l0_stairs[0].polygon)
                p1 = Polygon(l1_stairs[0].polygon)
                overlap = p0.intersection(p1).area
                min_a = min(p0.area, p1.area)
                if min_a > 0 and (overlap / min_a) >= 0.70:
                    stair_stacked = True
                else:
                    stair_err.append(f"Staircase core shift across floors (overlap: {overlap:.2f} m² / {min_a:.2f} m² = {(overlap/min_a)*100:.1f}%).")
        else:
            stair_stacked = len(l0_stairs) > 0

        hard_rules["stair_vertical_stacking"] = {
            "name": "Staircase Core Structural Stacking",
            "passed": stair_stacked and len(stair_err) == 0,
            "violations": stair_err,
            "weight": 12
        }

        # -------------------------------------------------------------
        # Hard Rule 4: Entrance Foyer Separate from Car Porch
        # -------------------------------------------------------------
        porches = [r for r in rooms if r.level_index == 0 and (r.room_type == "garage" or "porch" in r.room_name.lower())]
        foyers = [r for r in rooms if r.level_index == 0 and ("foyer" in r.room_name.lower() or "entrance" in r.room_name.lower())]
        foyer_ok = True
        foyer_err = []
        if porches and foyers:
            p_poly = Polygon(porches[0].polygon)
            f_poly = Polygon(foyers[0].polygon)
            if p_poly.intersection(f_poly).area > 0.10:
                foyer_ok = False
                foyer_err.append("Foyer overlaps with Car Porch volume.")
        hard_rules["foyer_porch_separation"] = {
            "name": "Entrance Foyer & Car Porch Separation",
            "passed": foyer_ok,
            "violations": foyer_err,
            "weight": 8
        }

        # -------------------------------------------------------------
        # Hard Rule 5: Formal Guest Drawing Room with Powder / Ensuite
        # -------------------------------------------------------------
        drawings = [r for r in rooms if r.level_index == 0 and ("drawing" in r.room_name.lower() or r.room_type == "drawing_room")]
        drawing_bath_ok = True
        drawing_bath_err = []
        if drawings:
            dr = drawings[0]
            dr_poly = Polygon(dr.polygon)
            has_powder = False
            for bath in bathrooms:
                if bath.level_index == 0:
                    # Direct contiguous or accessible via entrance foyer/lobby (<= 3.5m)
                    if Polygon(bath.polygon).distance(dr_poly) <= 3.50:
                        has_powder = True
                        break
            if not has_powder:
                drawing_bath_ok = False
                drawing_bath_err.append(f"Formal Drawing Room '{dr.room_name}' lacks dedicated powder/guest bath access.")
        hard_rules["drawing_powder_access"] = {
            "name": "Drawing Room Powder Facility Access",
            "passed": drawing_bath_ok,
            "violations": drawing_bath_err,
            "weight": 10
        }

        # -------------------------------------------------------------
        # Hard Rule 6: Kitchen Scullery / Dirty Kitchen Provision
        # -------------------------------------------------------------
        kitchens = [r for r in rooms if r.level_index == 0 and (r.room_type == "kitchen" or "kitchen" in r.room_name.lower())]
        has_dirty_or_scullery = False
        kitchen_err = []
        if cat in ("3_marla", "5_marla"):
            # In compact 3 & 5 Marla plots, single open kitchen / scullery is standard
            has_dirty_or_scullery = True
        else:
            if kitchens:
                for k in kitchens:
                    k_name = k.room_name.lower()
                    k_meta = k.metadata or {}
                    if "dirty" in k_name or "scullery" in k_name or k_meta.get("dirty_kitchen") or k_meta.get("scullery"):
                        has_dirty_or_scullery = True
                        break
                # Also check if adjacent utility or dirty kitchen room exists
                if not has_dirty_or_scullery:
                    dirty_rms = [r for r in rooms if r.level_index == 0 and ("dirty" in r.room_name.lower() or "scullery" in r.room_name.lower() or "pantry" in r.room_name.lower())]
                    if dirty_rms:
                        has_dirty_or_scullery = True
                if not has_dirty_or_scullery:
                    kitchen_err.append("Ground floor kitchen lacks distinct dirty mess kitchen / scullery / store provision.")
        hard_rules["kitchen_dirty_scullery"] = {
            "name": "Show Kitchen + Dirty Scullery Provision",
            "passed": has_dirty_or_scullery,
            "violations": kitchen_err,
            "weight": 8
        }

        # -------------------------------------------------------------
        # Hard Rule 7: Every Room Has At Least One Valid Door Access
        # -------------------------------------------------------------
        door_connects = set()
        for op in openings:
            if op.opening_type == "door":
                for rid in getattr(op, "connects_rooms", []):
                    door_connects.add(rid)

        inaccessible_rooms = []
        for r in rooms:
            if r.room_type in ("outdoor", "balcony", "unclassified_closed_region") or "shaft" in r.room_name.lower() or "ots" in r.room_name.lower() or "lawn" in r.room_name.lower():
                continue
            if r.room_id not in door_connects:
                # Check if open concept connecting into adjacent room
                if not (r.metadata or {}).get("open_concept"):
                    inaccessible_rooms.append(f"{r.room_name} ({r.room_id}) on Level {r.level_index}")

        hard_rules["room_door_accessibility"] = {
            "name": "Universal Room Door Ingress & Egress",
            "passed": len(inaccessible_rooms) == 0,
            "violations": inaccessible_rooms,
            "weight": 12
        }

        # -------------------------------------------------------------
        # Hard Rule 8: Every Habitable Room Has Natural Ventilation (Window/OTS)
        # -------------------------------------------------------------
        unventilated_habitable = []
        habitable_rooms = [r for r in rooms if r.is_habitable and r.room_type in ("bedroom", "living_room", "drawing_room", "kitchen", "study")]
        from shapely.geometry import Point

        for hr in habitable_rooms:
            poly = Polygon(hr.polygon)
            has_win = False
            for op in openings:
                if op.opening_type == "window" and op.level_index == hr.level_index:
                    if hr.room_id in getattr(op, "connects_rooms", []):
                        has_win = True
                        break
                    pt = Point(op.position)
                    if poly.distance(pt) <= 0.45:
                        has_win = True
                        break

            if not has_win:
                # Check proximity to OTS courtyard, open airwell, or rear lawn
                ots_rooms = [r for r in rooms if r.level_index == hr.level_index and ("ots" in r.room_name.lower() or "shaft" in r.room_name.lower() or r.room_type == "outdoor" or "lawn" in r.room_name.lower())]
                near_ots = any(poly.distance(Polygon(o.polygon)) <= 0.45 for o in ots_rooms if len(o.polygon) >= 3)
                if near_ots:
                    has_win = True

            # Open concept spaces (e.g. open kitchen / lounge) inherit ventilation from adjoining volume
            if not has_win and (hr.metadata or {}).get("open_concept"):
                has_win = True

            if not has_win:
                unventilated_habitable.append(f"{hr.room_name} (L{hr.level_index}) has no window to exterior or OTS shaft")

        hard_rules["habitable_natural_ventilation"] = {
            "name": "Natural Ventilation & Daylight Compliance",
            "passed": len(unventilated_habitable) == 0,
            "violations": unventilated_habitable,
            "weight": 10
        }

        # -------------------------------------------------------------
        # Hard Rule 9: No Fake Ground "Double-Height Void"
        # -------------------------------------------------------------
        fake_voids = []
        l0_voids = [r for r in rooms if r.level_index == 0 and "double" in r.room_name.lower() and "void" in r.room_name.lower()]
        for v in l0_voids:
            # Must have corresponding void on level 1
            l1_voids = [r for r in rooms if r.level_index == 1 and ("void" in r.room_name.lower() or "open" in r.room_name.lower())]
            if not l1_voids:
                fake_voids.append(f"Ground floor '{v.room_name}' is labelled void but no opening exists on first floor slab.")

        hard_rules["no_fake_voids"] = {
            "name": "Double Height Void Structural Reality",
            "passed": len(fake_voids) == 0,
            "violations": fake_voids,
            "weight": 5
        }

        # -------------------------------------------------------------
        # Hard Rule 10: Dimension Consistency with Plot Boundaries
        # -------------------------------------------------------------
        dim_violations = []
        if getattr(plan, "boundary", None) and len(plan.boundary) >= 3:
            plot_w = max(p[0] for p in plan.boundary)
            plot_l = max(p[1] for p in plan.boundary)
        elif getattr(plan, "envelope", None) and len(plan.envelope) >= 3:
            plot_w = max(p[0] for p in plan.envelope)
            plot_l = max(p[1] for p in plan.envelope)
        elif cat == "1_kanal":
            plot_w, plot_l = 15.24, 27.43
        elif cat == "5_marla":
            plot_w, plot_l = 7.62, 13.72
        else:
            plot_w, plot_l = 10.67, 19.81
        for r in rooms:
            for pt in r.polygon:
                if pt[0] < -0.20 or pt[0] > plot_w + 0.20 or pt[1] < -0.20 or pt[1] > plot_l + 0.20:
                    dim_violations.append(f"{r.room_name} vertex ({pt[0]:.2f}, {pt[1]:.2f}) out of bounds [0..{plot_w:.2f}, 0..{plot_l:.2f}]")
                    break

        hard_rules["dimension_boundary_consistency"] = {
            "name": "Plot Boundary & Setback Geometry Adherence",
            "passed": len(dim_violations) == 0,
            "violations": dim_violations,
            "weight": 5
        }

        # -------------------------------------------------------------
        # Statistical Alignment Scoring (Empirical Comparison)
        # -------------------------------------------------------------
        stat_items = []
        total_covered_m2 = sum(r.area_m2 for r in rooms if r.room_type not in ("outdoor", "balcony", "unclassified_closed_region")) or 1.0

        bed_area = sum(r.area_m2 for r in rooms if r.room_type == "bedroom")
        lounge_area = sum(r.area_m2 for r in rooms if r.room_type in ("living_room", "lounge"))
        kitchen_area = sum(r.area_m2 for r in rooms if r.room_type == "kitchen")
        drawing_area = sum(r.area_m2 for r in rooms if r.room_type == "drawing_room")
        porch_area = sum(r.area_m2 for r in rooms if r.room_type == "garage" or "porch" in r.room_name.lower())

        metrics = [
            ("Bedroom Area Ratio", (bed_area / total_covered_m2) * 100.0, ref_stats.get("bedroom_area_pct", {"mean": 32.0, "std": 6.0})),
            ("Family Lounge Ratio", (lounge_area / total_covered_m2) * 100.0, ref_stats.get("lounge_area_pct", {"mean": 18.0, "std": 5.0})),
            ("Kitchen Area Ratio", (kitchen_area / total_covered_m2) * 100.0, ref_stats.get("kitchen_area_pct", {"mean": 9.0, "std": 3.0})),
            ("Drawing Room Ratio", (drawing_area / total_covered_m2) * 100.0, ref_stats.get("drawing_area_pct", {"mean": 14.0, "std": 4.0})),
            ("Car Porch Area Ratio", (porch_area / total_covered_m2) * 100.0, ref_stats.get("porch_area_pct", {"mean": 16.0, "std": 5.0})),
        ]

        stat_score = 0.0
        max_stat_points = 25.0
        points_per_metric = max_stat_points / len(metrics)

        for m_name, actual_val, target in metrics:
            mean = target.get("mean", actual_val)
            std = target.get("std", 4.0) or 4.0
            diff = abs(actual_val - mean)
            z_score = diff / max(std, 1.0)
            if z_score <= 1.0:
                pts = points_per_metric
            elif z_score <= 2.0:
                pts = points_per_metric * 0.70
            elif z_score <= 3.0:
                pts = points_per_metric * 0.40
            else:
                pts = points_per_metric * 0.10
            stat_score += pts
            stat_items.append({
                "metric": m_name,
                "target_mean": f"{mean:.1f}% (±{std:.1f}%)",
                "actual_value": f"{actual_val:.1f}%",
                "points_awarded": round(pts, 1),
                "max_points": round(points_per_metric, 1)
            })

        # Calculate Total Score: 75 points for Hard Rules + 25 points for Statistical Distribution
        hard_rule_points = 0.0
        total_hard_weight = sum(r["weight"] for r in hard_rules.values())  # 100
        for r_key, r_info in hard_rules.items():
            if r_info["passed"]:
                hard_rule_points += r_info["weight"]

        scaled_hard_score = (hard_rule_points / max(total_hard_weight, 1.0)) * 75.0
        total_score = round(scaled_hard_score + stat_score, 1)

        all_passed = all(r["passed"] for r in hard_rules.values())
        verdict = "PASS - ARCHITECTURAL CAD COMPLIANT" if (all_passed and total_score >= 80.0) else "FAIL - REVISION REQUIRED"

        return {
            "plot_category": cat,
            "total_score": total_score,
            "verdict": verdict,
            "all_hard_rules_passed": all_passed,
            "hard_rules": hard_rules,
            "statistical_alignment": stat_items,
            "dataset_reference_scale": cat
        }
