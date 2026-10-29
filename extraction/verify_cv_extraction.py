"""
CV Extraction Verification Checkpoint & Quality Audit Engine.
Verifies the accuracy of the computer vision extraction pipeline from real blueprint scans:
1. Boundary Closure & Watertightness: Valid closed planar polygons, no overlapping rooms (IoU < 0.01).
2. Room Classification Audit: Validates room semantics ('bedroom', 'bathroom', 'kitchen', 'tv_lounge', 'drawing_room', 'car_porch', 'ots').
3. Door & Circulation Connectivity: Verifies every room has door openings on shared walls and forms a BFS-connected graph.
4. Scale Sanity Check: Verifies plot dimensions and total area match real Pakistani plots (3M, 5M, 7M, 10M, 1 Kanal).
5. Visual Verification Overlays: Renders side-by-side diagnostic figures (raw scan vs. extracted CAD wireframe) to output/cv_verification_report/.
"""

import os
import json
import glob
from typing import Dict, List, Tuple, Any, Optional
import cv2
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from shapely.geometry import Polygon, Point, LineString
import networkx as nx

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel, OpeningModel


PAKISTANI_PLOT_STANDARDS = {
    "3_marla": {
        "name": "3 Marla",
        "nominal_dimensions_ft": [15.0, 45.0],
        "width_range_m": [4.0, 6.5],
        "depth_range_m": [11.0, 15.0],
        "area_range_sqft": [600.0, 850.0],
        "area_range_m2": [55.0, 80.0]
    },
    "5_marla": {
        "name": "5 Marla",
        "nominal_dimensions_ft": [25.0, 45.0],
        "width_range_m": [7.0, 8.5],
        "depth_range_m": [12.0, 16.0],
        "area_range_sqft": [1050.0, 1350.0],
        "area_range_m2": [95.0, 125.0]
    },
    "7_marla": {
        "name": "7 Marla",
        "nominal_dimensions_ft": [30.0, 55.0],
        "width_range_m": [8.5, 10.0],
        "depth_range_m": [15.0, 19.0],
        "area_range_sqft": [1550.0, 1900.0],
        "area_range_m2": [140.0, 180.0]
    },
    "10_marla": {
        "name": "10 Marla",
        "nominal_dimensions_ft": [35.0, 65.0],
        "width_range_m": [10.0, 12.0],
        "depth_range_m": [18.0, 22.0],
        "area_range_sqft": [2100.0, 2450.0],
        "area_range_m2": [190.0, 230.0]
    },
    "1_kanal": {
        "name": "1 Kanal",
        "nominal_dimensions_ft": [50.0, 90.0],
        "width_range_m": [14.0, 16.5],
        "depth_range_m": [25.0, 30.0],
        "area_range_sqft": [4200.0, 4800.0],
        "area_range_m2": [390.0, 450.0]
    }
}

SEMANTIC_CATEGORIES = {
    "bedroom": ["bedroom", "bed", "master", "suite"],
    "bathroom": ["bathroom", "bath", "powder", "wc", "toilet", "washroom"],
    "kitchen": ["kitchen", "dirty_kitchen", "skit", "cooking", "scullery"],
    "tv_lounge": ["tv_lounge", "lounge", "family", "living"],
    "drawing_room": ["drawing", "formal", "guest_room", "salon"],
    "car_porch": ["porch", "garage", "car", "parking"],
    "ots": ["ots", "shaft", "duct", "patio", "outdoor", "lawn", "court"],
    "circulation": ["stairs", "corridor", "hall", "lobby", "foyer", "passage"]
}

ROOM_COLOR_MAP = {
    "bedroom": "#3B82F6",       # Blue
    "bathroom": "#06B6D4",      # Cyan
    "kitchen": "#F59E0B",       # Amber
    "tv_lounge": "#8B5CF6",     # Purple
    "drawing_room": "#10B981",   # Emerald
    "car_porch": "#64748B",     # Slate
    "ots": "#84CC16",           # Lime
    "circulation": "#EC4899",   # Pink
    "dining": "#F97316",        # Orange
    "default": "#94A3B8"
}


class CVExtractionVerifier:
    """
    Automated verification suite auditing extracted floor plan JSONs
    against architectural standards and blueprint image scans.
    """

    def __init__(self, report_dir: str = "output/cv_verification_report"):
        self.report_dir = report_dir
        os.makedirs(self.report_dir, exist_ok=True)

    def audit_plan(self, plan: CanonicalFloorPlan) -> Dict[str, Any]:
        """
        Executes comprehensive automated verification checks on a single extracted plan.
        """
        issues = []
        checks = {
            "watertightness": True,
            "classification": True,
            "door_connectivity": True,
            "scale_sanity": True
        }

        scale = plan.metadata.provenance.get("scale", "5_marla") if plan.metadata.provenance else "5_marla"
        std_scale = PAKISTANI_PLOT_STANDARDS.get(scale, PAKISTANI_PLOT_STANDARDS["5_marla"])

        # -------------------------------------------------------------
        # 1. Boundary Closure & Watertightness
        # -------------------------------------------------------------
        rooms = plan.rooms
        polys: List[Tuple[str, Polygon]] = []
        for r in rooms:
            if len(r.polygon) < 3:
                issues.append(f"Watertightness: Room '{r.room_name}' has degenerate polygon (<3 vertices).")
                checks["watertightness"] = False
                continue
            poly = Polygon(r.polygon)
            if not poly.is_valid or poly.is_empty or poly.area <= 0.01:
                issues.append(f"Watertightness: Room '{r.room_name}' is not a valid planar polygon (area={poly.area:.2f}).")
                checks["watertightness"] = False
            polys.append((r.room_id, poly))

        # Check pairwise room overlaps (IoU < 0.01)
        for i in range(len(polys)):
            id1, p1 = polys[i]
            for j in range(i + 1, len(polys)):
                id2, p2 = polys[j]
                inter_area = p1.intersection(p2).area
                min_area = min(p1.area, p2.area)
                iou = inter_area / (p1.area + p2.area - inter_area) if (p1.area + p2.area - inter_area) > 0 else 0
                if iou >= 0.01 and inter_area > 0.05:
                    issues.append(f"Boundary Overlap: '{id1}' and '{id2}' overlap by {inter_area:.2f}m² (IoU={iou:.3f}).")
                    checks["watertightness"] = False

        # -------------------------------------------------------------
        # 2. Room Count & Classification Audit
        # -------------------------------------------------------------
        detected_categories = set()
        for r in rooms:
            name_lower = (r.room_name + " " + r.room_id + " " + r.room_type).lower()
            matched_cat = None
            for cat, keywords in SEMANTIC_CATEGORIES.items():
                if any(k in name_lower for k in keywords):
                    matched_cat = cat
                    break
            if matched_cat:
                detected_categories.add(matched_cat)
            else:
                detected_categories.add("other")

        # Must have essential residential categories
        essential = {"bedroom", "bathroom", "kitchen", "tv_lounge"}
        missing_essential = essential - detected_categories
        if missing_essential:
            issues.append(f"Classification: Missing essential functional zones: {missing_essential}")
            checks["classification"] = False

        # -------------------------------------------------------------
        # 3. Door & Circulation Connectivity (BFS)
        # -------------------------------------------------------------
        g = nx.Graph()
        for r in rooms:
            g.add_node(r.room_id)

        # Doors hosted on room boundaries
        doors = [op for op in plan.openings if op.opening_type == "door"]
        for d in doors:
            pt = Point(d.position[0], d.position[1])
            # Check proximity to connecting rooms
            for rid in d.connects_rooms:
                r_match = plan.get_room_by_id(rid)
                if r_match:
                    dist = Polygon(r_match.polygon).exterior.distance(pt)
                    if dist > 0.45:
                        issues.append(f"Door Hosting: Door '{d.opening_id}' at {d.position} is detached from room '{rid}' boundary (dist={dist:.2f}m).")
                        checks["door_connectivity"] = False

            if len(d.connects_rooms) == 2:
                g.add_edge(d.connects_rooms[0], d.connects_rooms[1])

        # Graph edges
        for e in plan.graph_edges:
            if e.relationship_type in ("via_door", "direct"):
                g.add_edge(e.source_room_id, e.target_room_id)

        # BFS reachability from entrance
        entrance_room = next((r for r in rooms if "porch" in r.room_id.lower() or "foyer" in r.room_id.lower() or "entry" in r.room_id.lower()), rooms[0])
        habitable_rooms = [r.room_id for r in rooms if r.is_habitable]
        unreachable = []
        for h in habitable_rooms:
            if h != entrance_room.room_id:
                if not nx.has_path(g, entrance_room.room_id, h):
                    unreachable.append(h)

        if unreachable:
            issues.append(f"BFS Reachability: Habitable rooms unreachable from entrance '{entrance_room.room_name}': {unreachable}")
            checks["door_connectivity"] = False

        # -------------------------------------------------------------
        # 4. Scale Sanity Check
        # -------------------------------------------------------------
        env_poly = Polygon(plan.boundary)
        minx, miny, maxx, maxy = env_poly.bounds
        w_m, d_m = maxx - minx, maxy - miny
        plot_area_m2 = env_poly.area
        plot_area_sqft = plot_area_m2 * 10.7639

        w_min, w_max = std_scale["width_range_m"]
        d_min, d_max = std_scale["depth_range_m"]
        a_min, a_max = std_scale["area_range_m2"]

        if not (w_min * 0.90 <= w_m <= w_max * 1.10):
            issues.append(f"Scale Sanity: Envelope width {w_m:.2f}m outside expected {scale} range [{w_min:.1f}m - {w_max:.1f}m].")
            checks["scale_sanity"] = False

        if not (d_min * 0.90 <= d_m <= d_max * 1.10):
            issues.append(f"Scale Sanity: Envelope depth {d_m:.2f}m outside expected {scale} range [{d_min:.1f}m - {d_max:.1f}m].")
            checks["scale_sanity"] = False

        if not (a_min * 0.85 <= plot_area_m2 <= a_max * 1.15):
            issues.append(f"Scale Sanity: Plot envelope area {plot_area_m2:.1f}m² ({plot_area_sqft:.0f} sqft) outside expected {scale} range [{a_min:.0f}m² - {a_max:.0f}m²].")
            checks["scale_sanity"] = False

        is_valid = all(checks.values()) and len(issues) == 0

        return {
            "plan_id": plan.metadata.plan_id,
            "scale": scale,
            "is_valid": is_valid,
            "checks": checks,
            "issues": issues,
            "metrics": {
                "room_count": len(rooms),
                "door_count": len(doors),
                "envelope_m": [round(w_m, 2), round(d_m, 2)],
                "total_area_m2": round(plot_area_m2, 1),
                "total_area_sqft": round(plot_area_sqft, 1),
                "carpet_area_m2": round(sum(r.area_m2 for r in rooms), 1),
                "detected_categories": list(detected_categories)
            }
        }

    def generate_diagnostic_overlay(
        self,
        raw_image_path: str,
        plan: CanonicalFloorPlan,
        output_image_path: str,
        audit_result: Optional[Dict[str, Any]] = None
    ) -> str:
        """
        Renders a side-by-side verification plot:
        - Left: Raw blueprint scan.
        - Right: Extracted vector wireframe with color-coded polygons, door swings, and OCR labels.
        """
        scale = plan.metadata.provenance.get("scale", "5_marla") if plan.metadata.provenance else "5_marla"
        plot_info = PAKISTANI_PLOT_STANDARDS.get(scale, PAKISTANI_PLOT_STANDARDS["5_marla"])
        
        fig, axes = plt.subplots(1, 2, figsize=(16, 9), dpi=180)
        fig.patch.set_facecolor("#0F172A")  # Dark slate background

        # -------------------------------------------------------------
        # Left Panel: Original Blueprint Image
        # -------------------------------------------------------------
        ax_img = axes[0]
        ax_img.set_facecolor("#1E293B")
        
        if os.path.exists(raw_image_path):
            img_bgr = cv2.imread(raw_image_path)
            if img_bgr is not None:
                img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
                ax_img.imshow(img_rgb)
                h, w = img_rgb.shape[:2]
                ax_img.set_title(f"Raw Blueprint Scan: {os.path.basename(raw_image_path)}\nResolution: {w}x{h} px | Scale: {plot_info['name']}",
                                 color="#F8FAFC", fontsize=11, fontweight="bold", pad=12)
            else:
                ax_img.text(0.5, 0.5, "Image could not be decoded", color="#EF4444", ha="center", va="center")
        else:
            ax_img.text(0.5, 0.5, f"Image not found:\n{raw_image_path}", color="#EF4444", ha="center", va="center")

        ax_img.axis("off")

        # -------------------------------------------------------------
        # Right Panel: Extracted CAD Vector Wireframe
        # -------------------------------------------------------------
        ax_vec = axes[1]
        ax_vec.set_facecolor("#020617")

        env_poly = Polygon(plan.boundary)
        minx, miny, maxx, maxy = env_poly.bounds
        w_m, d_m = maxx - minx, maxy - miny

        # Draw outer boundary
        bx, by = env_poly.exterior.xy
        ax_vec.plot(bx, by, color="#38BDF8", linewidth=2.5, linestyle="--", label="Plot Envelope")

        # Draw walls
        for w in plan.walls:
            c = w.centerline
            wall_color = "#E2E8F0" if w.wall_type == "exterior" else "#94A3B8"
            lw = 3.0 if w.wall_type == "exterior" else 1.6
            ax_vec.plot([c[0][0], c[1][0]], [c[0][1], c[1][1]], color=wall_color, linewidth=lw, solid_capstyle="round", zorder=3)

        # Draw room polygons with color coding
        for r in plan.rooms:
            # Determine color
            name_lower = (r.room_name + " " + r.room_id + " " + r.room_type).lower()
            room_cat = "default"
            for cat, keywords in SEMANTIC_CATEGORIES.items():
                if any(k in name_lower for k in keywords):
                    room_cat = cat
                    break
            
            fill_color = ROOM_COLOR_MAP.get(room_cat, "#94A3B8")
            pts = np.array(r.polygon)
            polygon_patch = patches.Polygon(pts, closed=True, facecolor=fill_color, alpha=0.35, edgecolor=fill_color, linewidth=1.5, zorder=2)
            ax_vec.add_patch(polygon_patch)

            # Room text label
            cx, cy = r.centroid[0], r.centroid[1]
            poly = Polygon(r.polygon)
            area_sqft = poly.area * 10.7639
            r_name = r.room_name.split("(")[0].strip()
            label_text = f"{r_name}\n{poly.area:.1f}m² ({area_sqft:.0f}ft²)"
            ax_vec.text(cx, cy, label_text, color="#FFFFFF", fontsize=7.5, fontweight="bold", ha="center", va="center",
                        bbox=dict(boxstyle="round,pad=0.2", facecolor="#0F172A", alpha=0.75, edgecolor="none"), zorder=4)

        # Draw doors
        for op in plan.openings:
            if op.opening_type == "door":
                px, py = op.position
                ax_vec.scatter([px], [py], color="#EF4444", s=35, zorder=5)
                # Door swing arc approximation
                arc = patches.Arc((px, py), width=op.width_m, height=op.width_m, angle=0, theta1=0, theta2=90, color="#EF4444", linewidth=1.5, zorder=5)
                ax_vec.add_patch(arc)
            elif op.opening_type == "window":
                px, py = op.position
                ax_vec.scatter([px], [py], color="#38BDF8", s=25, marker="s", zorder=5)

        # Add dimension annotations
        ax_vec.text(minx + w_m / 2, miny - 0.45, f"Frontage: {w_m:.2f}m ({w_m*3.28084:.1f}')", color="#38BDF8", fontsize=9, fontweight="bold", ha="center")
        ax_vec.text(maxx + 0.45, miny + d_m / 2, f"Depth: {d_m:.2f}m ({d_m*3.28084:.1f}')", color="#38BDF8", fontsize=9, fontweight="bold", va="center", rotation=270)

        # Status Badge
        status_text = "PASSED AUDIT (100% WATERTIGHT & BFS CONNECTED)" if (audit_result and audit_result["is_valid"]) else "VERIFICATION AUDITED"
        status_color = "#22C55E" if (audit_result and audit_result["is_valid"]) else "#F59E0B"
        ax_vec.set_title(f"Extracted Vector CAD Wireframe: {plan.metadata.plan_id}\n{status_text}",
                         color=status_color, fontsize=11, fontweight="bold", pad=12)

        ax_vec.set_xlim(minx - 1.2, maxx + 1.5)
        ax_vec.set_ylim(maxy + 1.2, miny - 1.2)  # Inverted Y matching architectural top-down scan
        ax_vec.set_aspect("equal")
        ax_vec.grid(True, linestyle=":", color="#334155", alpha=0.5)
        ax_vec.tick_params(colors="#94A3B8", labelsize=8)

        # Main Title Banner
        fig.suptitle(f"Computer Vision Extraction Verification Checkpoint | {plot_info['name']} Ground Floor Blueprint",
                     color="#F8FAFC", fontsize=14, fontweight="bold", y=0.98)

        plt.tight_layout()
        plt.savefig(output_image_path, dpi=180, facecolor=fig.get_facecolor(), bbox_inches="tight")
        plt.close(fig)
        return output_image_path

    def run_full_verification(
        self,
        processed_dir: str = "dataset/processed_plans",
        index_path: str = "dataset/dataset_index.json"
    ) -> Dict[str, Any]:
        """
        Audits all processed plans in the dataset, generates side-by-side plots
        for representative plans per scale, and writes a comprehensive report.
        """
        plan_files = glob.glob(os.path.join(processed_dir, "*.json"))
        print(f"\n=================================================================")
        print(f"  CV EXTRACTION VERIFICATION CHECKPOINT: Auditing {len(plan_files)} plans")
        print(f"=================================================================\n")

        audited_records = []
        scale_stats: Dict[str, Dict[str, int]] = {}
        sample_per_scale: Dict[str, Tuple[str, CanonicalFloorPlan, Dict[str, Any]]] = {}

        for pf in plan_files:
            try:
                with open(pf, "r", encoding="utf-8") as f:
                    plan_data = json.load(f)
                plan = CanonicalFloorPlan.from_dict(plan_data)
                scale = plan.metadata.provenance.get("scale", "5_marla") if plan.metadata.provenance else "5_marla"
                
                result = self.audit_plan(plan)
                audited_records.append(result)

                stats = scale_stats.setdefault(scale, {"total": 0, "passed": 0, "watertight": 0, "connected": 0})
                stats["total"] += 1
                if result["is_valid"]:
                    stats["passed"] += 1
                if result["checks"]["watertightness"]:
                    stats["watertight"] += 1
                if result["checks"]["door_connectivity"]:
                    stats["connected"] += 1

                # Keep first valid sample for visualization
                if scale not in sample_per_scale and result["is_valid"]:
                    raw_img = plan.metadata.provenance.get("source_path", "") if plan.metadata.provenance else ""
                    sample_per_scale[scale] = (raw_img, plan, result)

            except Exception as e:
                print(f"Error auditing {pf}: {e}")

        # If any scale didn't have valid sample, take any sample
        for pf in plan_files:
            with open(pf, "r", encoding="utf-8") as f:
                plan_data = json.load(f)
            plan = CanonicalFloorPlan.from_dict(plan_data)
            scale = plan.metadata.provenance.get("scale", "5_marla") if plan.metadata.provenance else "5_marla"
            if scale not in sample_per_scale:
                raw_img = plan.metadata.provenance.get("source_path", "") if plan.metadata.provenance else ""
                sample_per_scale[scale] = (raw_img, plan, self.audit_plan(plan))

        # Generate side-by-side overlay plots for each of the 5 plot scales
        overlay_images = {}
        for scale in ["3_marla", "5_marla", "7_marla", "10_marla", "1_kanal"]:
            if scale in sample_per_scale:
                raw_img, plan, audit_res = sample_per_scale[scale]
                out_png = os.path.join(self.report_dir, f"verification_{scale}.png")
                self.generate_diagnostic_overlay(raw_img, plan, out_png, audit_res)
                overlay_images[scale] = out_png
                print(f"Generated diagnostic overlay: {out_png}")

        total_plans = len(audited_records)
        total_passed = sum(1 for r in audited_records if r["is_valid"])
        pass_rate = round((total_passed / max(1, total_plans)) * 100, 1)

        summary = {
            "total_plans_audited": total_plans,
            "total_passed": total_passed,
            "pass_rate_percent": pass_rate,
            "scale_breakdown": scale_stats,
            "sample_overlays": overlay_images,
            "audits": audited_records
        }

        # Save summary JSON
        summary_path = os.path.join(self.report_dir, "verification_summary.json")
        with open(summary_path, "w", encoding="utf-8") as f:
            json.dump({k: v for k, v in summary.items() if k != "audits"}, f, indent=2)

        # Generate markdown report
        md_path = os.path.join(self.report_dir, "verification_report.md")
        with open(md_path, "w", encoding="utf-8") as f:
            f.write("# Computer Vision Extraction Verification Report\n\n")
            f.write(f"- **Total Plans Audited**: {total_plans}\n")
            f.write(f"- **Total Passed**: {total_passed} ({pass_rate}%)\n\n")
            f.write("## Scale Breakdown\n\n")
            f.write("| Scale | Total Plans | Watertight | Connected (BFS) | Passed Audit |\n")
            f.write("| :--- | :--- | :--- | :--- | :--- |\n")
            for scale, st in scale_stats.items():
                f.write(f"| {scale} | {st['total']} | {st['watertight']} | {st['connected']} | {st['passed']} |\n")
            f.write("\n## Generated Diagnostic Overlays\n\n")
            for scale, img_p in overlay_images.items():
                f.write(f"- **{scale}**: `{img_p}`\n")

        print(f"\nAudit complete: {total_passed}/{total_plans} ({pass_rate}%) plans passed.")
        print(f"Summary saved to: {summary_path}")
        print(f"Markdown report saved to: {md_path}")

        return summary


if __name__ == "__main__":
    verifier = CVExtractionVerifier()
    verifier.run_full_verification()
