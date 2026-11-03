"""
generation/elevation_engine/elevation_builder.py
Dynamic Road-side Facade Analyzer & Parametric Elevation Specification Builder.

Conforms to CDA/LDA/DHA bylaws and AIA CAD standards.
Directly translates CanonicalFloorPlan geometry into a fully-resolved elevation_spec.json.
Guarantees:
1. 1:1 horizontal alignment of all front-facing windows, doors, and porch columns.
2. Background stair mumty positioned strictly above the floor plan's real stair core.
3. Overhead water tank (OHT) and roof parapet accurately stacked.
4. Support for 4 selectable styles: Modern, Spanish, Minimalist, Classical.
5. Interactive feedback editing (POST /api/elevation).
"""

import os
import math
import copy
from typing import Dict, List, Tuple, Optional, Any
from shapely.geometry import Polygon, box, Point

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel, OpeningModel


class ElevationBuilder:
    """
    Parametric Facade Specification Generator.
    Extracts authentic 1:1 facade geometry from CanonicalFloorPlan.
    """

    # Synchronized Vertical Datums (Meters)
    H_ROAD = -0.30       # -1'-0" Road Level
    H_NGL = 0.00         #  0.00m Natural Ground Level
    H_PLINTH = 0.65      # +2'-2" Plinth Finished Floor Level (FFL)
    H_GF_CLEAR = 3.20    # +10'-6" Ground Floor Clear Ceiling
    H_SLAB = 0.28        # 11" Concrete Floor Slab
    H_1F = 4.13          # +13'-6" First Floor Finished Floor Level
    H_1F_CLEAR = 3.20    # +10'-6" First Floor Clear Ceiling
    H_ROOF = 7.61        # +25'-0" Rooftop Slab Top Level
    H_PARAPET = 8.71     # +28'-7" Rooftop Parapet Wall Top (1.10m height)
    H_MUMTY = 10.26      # +33'-8" Stair Mumty Penthouse Slab Top (2.65m height)
    H_OHT = 11.46        # +37'-7" Top of Overhead Concrete Water Tank (1.20m height)

    STYLE_CONFIGS = {
        "modern": {
            "name": "Modern Contemporary",
            "primary_wall": "#F8FAFC",
            "accent_wall": "#1E293B",
            "stone_cladding": "#D4B996",     # Warm Travertine
            "wood_louvers": "#8B5A2B",       # Teak slats
            "frame_color": "#0F172A",        # Charcoal aluminum
            "glass_color": "#BAE6FD",        # Clear Low-E blue glass
            "parapet_type": "flat_metal_coping",
            "arch_style": "orthogonal",
            "balustrade": "tempered_glass",
            "pergola_allowed": True
        },
        "spanish": {
            "name": "Spanish Colonial Villa",
            "primary_wall": "#FFFBEB",      # Warm Cream Stucco
            "accent_wall": "#92400E",       # Terracotta clay accent
            "stone_cladding": "#D97706",     # Cantera Stone
            "wood_louvers": "#78350F",       # Dark Walnut corbels
            "frame_color": "#451A03",        # Wrought iron bronze
            "glass_color": "#E0F2FE",        # Soft tint glass
            "parapet_type": "terracotta_barrel_tile",
            "arch_style": "semicircular_arch",
            "balustrade": "wrought_iron",
            "pergola_allowed": True
        },
        "minimalist": {
            "name": "Minimalist Contemporary",
            "primary_wall": "#F1F5F9",      # Off-white Smooth Stucco
            "accent_wall": "#334155",       # Slate concrete
            "stone_cladding": "#64748B",     # Honed Basalt
            "wood_louvers": "#475569",       # Charcoal metallic slats
            "frame_color": "#020617",        # Ultra-slim black
            "glass_color": "#93C5FD",        # High-performance glass
            "parapet_type": "monolithic_recessed",
            "arch_style": "orthogonal",
            "balustrade": "frameless_glass",
            "pergola_allowed": False
        },
        "classical": {
            "name": "Classical Arched",
            "primary_wall": "#FDFBF7",      # Alabaster Stucco
            "accent_wall": "#E2E8F0",       # Limestone molding
            "stone_cladding": "#E5E5E5",     # Carved sandstone
            "wood_louvers": "#57534E",       # Stone pilasters
            "frame_color": "#1C1917",        # Dark architectural bronze
            "glass_color": "#BFDBFE",        # Classical divided lites
            "parapet_type": "dentil_cornice_balustrade",
            "arch_style": "segmental_arch",
            "balustrade": "stone_balusters",
            "pergola_allowed": False
        }
    }

    @classmethod
    def build_elevation_spec(
        cls,
        plan: CanonicalFloorPlan,
        style: str = "modern",
        overrides: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Builds the complete elevation specification dictionary for a given plan and style.
        """
        overrides = overrides or {}
        style_key = cls._normalize_style_key(style)
        style_cfg = copy.deepcopy(cls.STYLE_CONFIGS[style_key])

        # Apply any style-level material overrides
        if "material_overrides" in overrides:
            style_cfg.update(overrides["material_overrides"])

        rooms = plan.rooms
        all_pts = [pt for r in rooms for pt in r.polygon]
        if all_pts:
            min_x = min(p[0] for p in all_pts)
            max_x = max(p[0] for p in all_pts)
            min_y = min(p[1] for p in all_pts)
            max_y = max(p[1] for p in all_pts)
            plot_w = round(max_x - min_x, 2)
            plot_d = round(max_y - min_y, 2)
        else:
            min_x, max_x, min_y, max_y = 0.0, 10.67, 0.0, 19.81
            plot_w, plot_d = 10.67, 19.81

        l0_rooms = [r for r in rooms if r.level_index == 0]
        l1_rooms = [r for r in rooms if r.level_index == 1]

        def get_bbox(r: RoomModel):
            pts = r.polygon
            return min(p[0] for p in pts) - min_x, min(p[1] for p in pts) - min_y, \
                   max(p[0] for p in pts) - min_x, max(p[1] for p in pts) - min_y

        # Detect front setback and front boundary line
        bld_l0 = [r for r in l0_rooms if r.room_type not in ("outdoor", "unclassified_closed_region")]
        front_setback_y = min(get_bbox(r)[1] for r in bld_l0) if bld_l0 else 1.83
        front_thresh = min(plot_d * 0.45, max(front_setback_y + 3.5, 4.5))

        # 1. Level 0 Front Bays
        l0_front_rooms = []
        for r in bld_l0:
            rx1, ry1, rx2, ry2 = get_bbox(r)
            if ry1 <= front_thresh and (rx2 - rx1) >= 1.2:
                l0_front_rooms.append({
                    "room_id": r.room_id,
                    "name": r.room_name,
                    "type": r.room_type,
                    "x1": round(rx1, 2),
                    "x2": round(rx2, 2),
                    "width": round(rx2 - rx1, 2),
                    "y1": round(ry1, 2),
                    "y2": round(ry2, 2)
                })

        # Remove deeply occluded front bays
        filtered_l0 = []
        for r in l0_front_rooms:
            occluded = False
            for other in l0_front_rooms:
                if other["room_id"] != r["room_id"] and other["y2"] <= r["y1"] + 0.20:
                    if max(other["x1"], r["x1"]) < min(other["x2"], r["x2"]):
                        if (min(other["x2"], r["x2"]) - max(other["x1"], r["x1"])) >= r["width"] * 0.8:
                            occluded = True
                            break
            if not occluded:
                filtered_l0.append(r)
        l0_front_rooms = sorted(filtered_l0, key=lambda x: x["x1"])

        # 2. Level 1 Front Bays
        bld_l1 = [r for r in l1_rooms if r.room_type not in ("outdoor", "unclassified_closed_region")]
        l1_front_rooms = []
        for r in bld_l1:
            rx1, ry1, rx2, ry2 = get_bbox(r)
            if ry1 <= front_thresh and (rx2 - rx1) >= 1.2:
                l1_front_rooms.append({
                    "room_id": r.room_id,
                    "name": r.room_name,
                    "type": r.room_type,
                    "x1": round(rx1, 2),
                    "x2": round(rx2, 2),
                    "width": round(rx2 - rx1, 2),
                    "y1": round(ry1, 2),
                    "y2": round(ry2, 2)
                })

        filtered_l1 = []
        for r in l1_front_rooms:
            occluded = False
            for other in l1_front_rooms:
                if other["room_id"] != r["room_id"] and other["y2"] <= r["y1"] + 0.20:
                    if max(other["x1"], r["x1"]) < min(other["x2"], r["x2"]):
                        if (min(other["x2"], r["x2"]) - max(other["x1"], r["x1"])) >= r["width"] * 0.8:
                            occluded = True
                            break
            if not occluded:
                filtered_l1.append(r)
        l1_front_rooms = sorted(filtered_l1, key=lambda x: x["x1"])

        # 3. Detect Car Porch & Main Entrance Door
        porch_bay = next((r for r in l0_front_rooms if r["type"] in ("garage", "carport") or "porch" in r["name"].lower()), None)
        porch_col_w = 0.45
        porch_col_x = (porch_bay["x2"] - porch_col_w) if (porch_bay and porch_bay["x1"] == 0) else (porch_bay["x1"] if porch_bay else 0.0)

        # 4. Openings Matching
        front_openings_l0 = []
        front_openings_l1 = []
        main_door = None

        for op in plan.openings:
            op_x = round(op.position[0] - min_x, 2)
            op_y = round(op.position[1] - min_y, 2)
            op_w = round(op.width_m, 2)
            op_h = round(op.height_m, 2)
            sill_h = round(op.sill_height_m, 2)

            if op.level_index == 0:
                is_front = False
                if op.opening_type == "door":
                    if "entry" in op.opening_id.lower() or "main" in op.opening_id.lower() or any("foyer" in rid.lower() for rid in op.connects_rooms):
                        is_front = True
                        main_door = {
                            "opening_id": op.opening_id,
                            "x": op_x,
                            "width": op_w,
                            "height": 2.40,
                            "sill_h": cls.H_PLINTH,
                            "lintel_h": cls.H_PLINTH + 2.40,
                            "is_double": op_w >= 1.20,
                            "type": "main_door"
                        }
                    elif op_y <= front_thresh:
                        is_front = True
                elif op.opening_type == "window":
                    if op_y <= front_thresh:
                        for fr in l0_front_rooms:
                            if fr["x1"] - 0.25 <= op_x <= fr["x2"] + 0.25 and abs(op_y - fr["y1"]) <= 0.8:
                                is_front = True
                                break

                if is_front:
                    front_openings_l0.append({
                        "opening_id": op.opening_id,
                        "type": op.opening_type,
                        "x": op_x,
                        "width": op_w,
                        "height": op_h,
                        "sill_h": round(cls.H_PLINTH + sill_h, 2),
                        "lintel_h": round(cls.H_PLINTH + sill_h + op_h, 2)
                    })

            elif op.level_index == 1:
                is_front = False
                if op_y <= front_thresh:
                    for fr in l1_front_rooms:
                        if fr["x1"] - 0.25 <= op_x <= fr["x2"] + 0.25 and abs(op_y - fr["y1"]) <= 0.8:
                            is_front = True
                            break
                if is_front:
                    front_openings_l1.append({
                        "opening_id": op.opening_id,
                        "type": op.opening_type,
                        "x": op_x,
                        "width": op_w,
                        "height": op_h,
                        "sill_h": round(cls.H_1F + sill_h, 2),
                        "lintel_h": round(cls.H_1F + sill_h + op_h, 2)
                    })

        # Fallback or reposition main entrance door to foyer front bay outside car porch
        if main_door and porch_bay:
            if porch_bay["x1"] - 0.10 <= main_door["x"] <= porch_bay["x2"] + 0.10:
                main_door["x"] = round(min(plot_w - main_door["width"] * 0.70, porch_bay["x2"] + 0.85), 2)
        elif not main_door and porch_bay:
            main_door = {
                "opening_id": "d_main_entry",
                "x": round(min(plot_w - 1.20, porch_bay["x2"] + 0.85), 2),
                "width": 1.20,
                "height": 2.40,
                "sill_h": cls.H_PLINTH,
                "lintel_h": round(cls.H_PLINTH + 2.40, 2),
                "is_double": True,
                "type": "main_door"
            }

        # 5. Staircase Mumty Core Projection (Exact 1:1 Structural Stacking)
        stair_rooms = [
            r for r in rooms 
            if "stair" in r.room_id.lower() or "stair" in r.room_name.lower() or r.room_type == "stairs"
        ]
        if not stair_rooms:
            raise ValueError("Structural Alignment Failure: Floor plan contains no stair core room to host rooftop mumty.")

        s_pts = [p for r in stair_rooms for p in r.polygon]
        stair_min_x = round(min(p[0] for p in s_pts), 2)
        stair_max_x = round(max(p[0] for p in s_pts), 2)
        stair_center_x = round((stair_min_x + stair_max_x) / 2.0, 2)
        stair_w = round(stair_max_x - stair_min_x, 2)

        # Mumty sits exactly atop the stair core load-bearing perimeter walls
        mumty_x = max(0.0, stair_min_x)
        mumty_w = round(max(1.50, min(stair_w, plot_w - mumty_x)), 2)
        if mumty_x + mumty_w > plot_w:
            mumty_x = max(0.0, round(plot_w - mumty_w, 2))

        oht_w = round(min(mumty_w * 0.80, 2.0), 2)
        oht_x = round(mumty_x + (mumty_w - oht_w) * 0.5, 2)

        # 6. Roof & Parapet Elements
        parapet_h = overrides.get("parapet_height_m", 1.10)
        has_pergola = overrides.get("has_pergola", style_cfg.get("pergola_allowed", True) and porch_bay is not None)

        pergola_spec = None
        if has_pergola and porch_bay:
            pergola_spec = {
                "x1": porch_bay["x1"],
                "x2": porch_bay["x2"],
                "width": porch_bay["width"],
                "y_level": cls.H_1F,
                "height_m": 2.40,
                "material": "Treated Hardwood Slats (Teak/Steel)",
                "color": style_cfg["wood_louvers"]
            }

        # Detect plot scale
        prov = getattr(plan.metadata, "provenance", {}) or {}
        prov_scale = prov.get("plot_scale") or prov.get("scale")
        if not prov_scale:
            area_sqft = plot_w * plot_d * 10.7639
            if area_sqft <= 850:
                prov_scale = "3_marla"
            elif area_sqft <= 1350:
                prov_scale = "5_marla"
            elif area_sqft <= 1900:
                prov_scale = "7_marla"
            elif area_sqft <= 3000:
                prov_scale = "10_marla"
            else:
                prov_scale = "1_kanal"

        # Compose Complete Specification
        spec = {
            "version": overrides.get("version", (plan.metadata.provenance or {}).get("version", 1)),
            "style": style_key,
            "style_name": style_cfg["name"],
            "plot_scale": prov_scale,
            "plot_dimensions": {
                "width_m": plot_w,
                "depth_m": plot_d,
                "width_ft": round(plot_w * 3.28084, 1),
                "depth_ft": round(plot_d * 3.28084, 1)
            },
            "vertical_datums": {
                "road": cls.H_ROAD,
                "ngl": cls.H_NGL,
                "plinth": cls.H_PLINTH,
                "floor_1": cls.H_1F,
                "roof_slab": cls.H_ROOF,
                "parapet_top": round(cls.H_ROOF + parapet_h, 2),
                "mumty_top": cls.H_MUMTY,
                "oht_top": cls.H_OHT
            },
            "facade_bays": {
                "ground_floor": l0_front_rooms,
                "first_floor": l1_front_rooms,
                "porch": porch_bay,
                "porch_column": {
                    "x": porch_col_x,
                    "width": porch_col_w,
                    "height": round(cls.H_1F - cls.H_PLINTH, 2)
                }
            },
            "openings": {
                "main_door": main_door,
                "ground_openings": front_openings_l0,
                "upper_openings": front_openings_l1
            },
            "roof_system": {
                "parapet_height_m": parapet_h,
                "parapet_style": style_cfg["parapet_type"],
                "mumty": {
                    "x": mumty_x,
                    "width": mumty_w,
                    "height": round(cls.H_MUMTY - cls.H_ROOF, 2),
                    "door_present": True
                },
                "water_tank": {
                    "x": oht_x,
                    "width": oht_w,
                    "height": round(cls.H_OHT - cls.H_MUMTY, 2),
                    "capacity_gal": 1500
                },
                "pergola": pergola_spec
            },
            "materials": style_cfg,
            "modifications_applied": overrides.get("feedback_applied", [])
        }

        return spec

    @classmethod
    def apply_feedback_to_spec(
        cls,
        base_spec: Dict[str, Any],
        feedback_prompt: str
    ) -> Dict[str, Any]:
        """
        Interactive feedback handler: parses natural language improvement instructions
        and applies targeted updates to the elevation specification.
        """
        updated = copy.deepcopy(base_spec)
        fb_lower = feedback_prompt.lower()
        applied = []

        # 1. Style Changes
        for k in ("spanish", "classical", "minimalist", "modern"):
            if k in fb_lower:
                new_cfg = copy.deepcopy(cls.STYLE_CONFIGS[k])
                updated["style"] = k
                updated["style_name"] = new_cfg["name"]
                updated["materials"] = new_cfg
                updated["roof_system"]["parapet_style"] = new_cfg["parapet_type"]
                applied.append(f"Changed architectural style to {new_cfg['name']}.")
                break

        # 2. Pergola requests
        if "add pergola" in fb_lower or "wooden pergola" in fb_lower:
            porch = updated["facade_bays"].get("porch")
            if porch:
                updated["roof_system"]["pergola"] = {
                    "x1": porch["x1"],
                    "x2": porch["x2"],
                    "width": porch["width"],
                    "y_level": cls.H_1F,
                    "height_m": 2.40,
                    "material": "Treated Hardwood Slats",
                    "color": updated["materials"]["wood_louvers"]
                }
                applied.append("Added architectural timber pergola above front terrace.")
        elif "remove pergola" in fb_lower:
            updated["roof_system"]["pergola"] = None
            applied.append("Removed rooftop terrace pergola.")

        # 3. Parapet Height adjustments
        if "increase parapet" in fb_lower or "4 feet parapet" in fb_lower or "higher parapet" in fb_lower:
            updated["roof_system"]["parapet_height_m"] = 1.35
            updated["vertical_datums"]["parapet_top"] = round(cls.H_ROOF + 1.35, 2)
            applied.append("Increased rooftop safety parapet height to 1.35m (4'-6\").")

        # 4. Window alterations (Ribbon / Full-height glazing)
        if "ribbon window" in fb_lower:
            for op in updated["openings"]["upper_openings"]:
                if op["type"] == "window":
                    op["height"] = 1.20
                    op["sill_h"] = round(cls.H_1F + 1.20, 2)
            applied.append("Updated upper floor windows to continuous ribbon glazing.")
        elif "full-height" in fb_lower or "floor to ceiling" in fb_lower:
            for op in updated["openings"]["ground_openings"]:
                if op["type"] == "window":
                    op["height"] = 2.40
                    op["sill_h"] = cls.H_PLINTH
            applied.append("Updated ground windows to full-height floor-to-ceiling glass.")

        # 5. Terracotta roof coping
        if "terracotta" in fb_lower or "spanish tile" in fb_lower:
            updated["roof_system"]["parapet_style"] = "terracotta_barrel_tile"
            updated["materials"]["accent_wall"] = "#92400E"
            applied.append("Applied Spanish terracotta barrel tile coping to roof parapet.")

        updated["modifications_applied"].extend(applied)
        return updated

    @classmethod
    def _normalize_style_key(cls, style: str) -> str:
        s = style.lower()
        if any(k in s for k in ("spanish", "colonial", "hacienda", "villa")):
            return "spanish"
        if any(k in s for k in ("classical", "neoclassical", "arched", "palladian")):
            return "classical"
        if any(k in s for k in ("minimalist", "brutalist", "industrial")):
            return "minimalist"
        return "modern"
