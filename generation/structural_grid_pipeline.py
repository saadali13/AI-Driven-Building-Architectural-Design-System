r"""
Bi-Directional Plan-to-Elevation Coordination Pipeline & Structural Grid Interface.
Synchronizes internal spatial layout with exterior elevation planes via a shared
Structural Grid Interface across both "Floor Plan First" and "Elevation First" workflows.
"""

import math
from typing import Dict, List, Tuple, Any, Optional
from dataclasses import dataclass, field, asdict

from dataset.schema.canonical import CanonicalFloorPlan, RoomModel, OpeningModel
from generation.architectural_styles import ArchitecturalStyleEngine, ArchitecturalStyleConfig


@dataclass
class FenestrationAperture:
    id: str
    level: int               # 0 = Ground, 1 = First, 2 = Second/Roof
    aperture_type: str       # "door", "window", "french_casement", "curtain_wall", "arch_loggia"
    rel_x: float             # center X coordinate relative to site boundary (m)
    y_ground: float          # base elevation (m)
    width_m: float
    height_m: float
    sill_height_m: float
    head_style: str          # "semicircular_roman", "segmental_arched", "rectilinear", "pedimented", "deep_punched"
    reveal_depth_mm: int
    has_architrave: bool
    has_keystone: bool
    mullion_pattern: str     # "divided_lite", "minimalist_single", "industrial_mullion", "corner_butt"
    shutter_style: Optional[str] = None
    balustrade: Optional[str] = None


@dataclass
class ColumnBay:
    index: int
    name: str
    x_start: float
    x_end: float
    width: float
    center_x: float
    column_left_x: float
    column_right_x: float
    column_type: str         # "tuscan", "fluted_classical", "slender_steel_h", "board_marked_pier"
    ground_usage: str        # "CAR_PORCH", "FOYER_ENTRANCE", "DRAWING_ROOM", "ARCHED_LOGGIA", "MONOLITHIC_SUITE"
    upper_usage: str         # "PERGOLA_TERRACE", "CANTILEVERED_SUITE", "FLUSH_CURTAIN_WALL", "JULIET_BALCONY"
    roof_usage: str          # "ROOFTOP_DECK", "PENTHOUSE_ENCLOSED", "MUMTY_TOWER", "TERRACOTTA_HIP", "PEDIMENT"
    fenestrations: List[FenestrationAperture] = field(default_factory=list)


@dataclass
class StructuralGridInterface:
    """
    Shared structural coordinate interface linking 2D floor plan interior rooms
    with 2D technical elevation planes and 3D geometric envelopes.
    """
    plot_width_m: float
    plot_length_m: float
    buildable_width_m: float
    num_floors: int
    style_id: str
    style_display_name: str
    workflow_mode: str       # "floor_plan_first" or "elevation_first"
    bays: List[ColumnBay] = field(default_factory=list)
    stair_x_min: float = 0.0
    stair_x_max: float = 0.0
    stair_width: float = 2.4
    stair_on_left: bool = True
    plinth_height_m: float = 0.65
    floor_height_m: float = 3.20
    slab_thickness_m: float = 0.28
    datum_levels: Dict[str, float] = field(default_factory=dict)
    facade_parameters: Dict[str, Any] = field(default_factory=dict)
    vertical_shaft_alignments: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        """Convert to JSON-serializable dictionary."""
        data = asdict(self)
        return data


class StructuralGridCoordinator:
    """
    Bi-Directional Generative Pipeline Controller.
    Implements Workflow 1 (Floor Plan First) and Workflow 2 (Elevation First / Style First).
    """

    @classmethod
    def derive_datum_levels(cls, floors: int, plinth_h: float = 0.65, fl_h: float = 3.20, slab_t: float = 0.28, style_cfg: Optional[ArchitecturalStyleConfig] = None) -> Dict[str, float]:
        """Calculates precise physical elevation datums."""
        h_road = -0.30
        h_ngl = 0.00
        h_plinth = plinth_h
        h_1f = h_plinth + fl_h + slab_t
        h_roof_2f = h_1f + fl_h + slab_t

        if floors >= 3:
            h_2f_clear = 3.00
            h_roof = h_roof_2f + h_2f_clear + slab_t
            h_parapet = h_roof + 1.10
            h_mumty = h_roof + 2.65
            h_oht = h_mumty + 1.20
        else:
            h_roof = h_roof_2f
            h_parapet = h_roof + 1.10
            h_mumty = h_roof + 2.65
            h_oht = h_mumty + 1.20

        # Style peak adjustments
        h_peak = h_parapet
        if style_cfg:
            if "spanish" in style_cfg.style_id:
                h_peak = h_mumty + 1.35   # Terracotta tiled ridge peak
            elif "neoclassical" in style_cfg.style_id:
                h_peak = h_parapet + 1.20  # Pediment tympanum apex
            elif "brutalist" in style_cfg.style_id:
                h_peak = h_parapet        # Pure flat monolith

        return {
            "road_level_m": h_road,
            "natural_ground_m": h_ngl,
            "plinth_level_m": h_plinth,
            "first_floor_ffl_m": round(h_1f, 2),
            "second_floor_ffl_m": round(h_roof_2f, 2) if floors >= 3 else 0.0,
            "roof_slab_level_m": round(h_roof, 2),
            "parapet_top_m": round(h_parapet, 2),
            "mumty_roof_m": round(h_mumty, 2),
            "oht_water_tank_top_m": round(h_oht, 2),
            "architectural_peak_m": round(h_peak, 2)
        }

    # =========================================================================
    # WORKFLOW 1: "FLOOR PLAN FIRST"
    # =========================================================================
    @classmethod
    def scan_plan_to_grid(
        cls,
        plan: CanonicalFloorPlan,
        style_id: str = "modern_contemporary",
        style_cfg: Optional[ArchitecturalStyleConfig] = None
    ) -> StructuralGridInterface:
        """
        WORKFLOW 1:
        Extracts structural column bays, stair mumty position, and road-facing fenestrations
        from an existing or synthesized canonical floor plan to establish the Structural Grid Interface.
        """
        cfg = style_cfg or ArchitecturalStyleEngine.get_style_by_id(style_id)
        rooms = getattr(plan, "rooms", [])
        all_pts = [pt for r in rooms for pt in r.polygon] if rooms else []

        if all_pts:
            min_x = min(p[0] for p in all_pts)
            max_x = max(p[0] for p in all_pts)
            min_y = min(p[1] for p in all_pts)
            max_y = max(p[1] for p in all_pts)
            width_m = round(max_x - min_x, 2)
            depth_m = round(max_y - min_y, 2)
        else:
            min_x, max_x, width_m = 0.0, 10.67, 10.67
            min_y, max_y, depth_m = 0.0, 19.81, 19.81

        l0_rooms = [r for r in rooms if getattr(r, 'level_index', 0) == 0]
        l1_rooms = [r for r in rooms if getattr(r, 'level_index', 0) == 1]
        num_floors = max(1, len(set(getattr(r, 'level_index', 0) for r in rooms)))

        # 1. Detect Staircase Mumty Core Coordinates
        stair_rooms = [
            r for r in rooms
            if ("stair" in r.room_id.lower() or "stair" in r.room_name.lower())
            and not getattr(r, "metadata", {}).get("is_service_stair", False)
            and "service" not in r.room_name.lower()
        ]
        if stair_rooms:
            s_all_pts = [pt for r in stair_rooms for pt in r.polygon]
            stair_x_min = round(min(p[0] for p in s_all_pts) - min_x, 2)
            stair_x_max = round(max(p[0] for p in s_all_pts) - min_x, 2)
        else:
            stair_x_min = round(width_m * 0.12, 2)
            stair_x_max = round(width_m * 0.38, 2)
        stair_w = round(max(2.2, stair_x_max - stair_x_min), 2)
        stair_on_left = stair_x_min < (width_m - stair_x_max)

        # 2. Raycast critical frontage boundary lines
        front_thresh = min_y + depth_m * 0.45
        front_bld_rooms = [
            r for r in l0_rooms + l1_rooms
            if not (r.room_type.lower() == "outdoor" and any(k in r.room_name.lower() for k in ("lawn", "passage", "setback")))
            and min(p[1] for p in r.polygon) <= front_thresh
        ]

        crit_x = {0.0, width_m}
        crit_x.add(max(0.0, min(width_m, stair_x_min)))
        crit_x.add(max(0.0, min(width_m, stair_x_max)))

        for r in front_bld_rooms:
            for p in r.polygon:
                rx = round(p[0] - min_x, 2)
                if 0.0 <= rx <= width_m:
                    crit_x.add(rx)

        sorted_x = sorted(list(crit_x))
        merged_x = [sorted_x[0]]
        for x in sorted_x[1:]:
            if (x - merged_x[-1]) >= 0.40:
                merged_x.append(x)
            else:
                merged_x[-1] = x
        if merged_x[-1] < width_m:
            merged_x.append(width_m)

        # 3. Build Column Bays and populate Fenestrations
        bays: List[ColumnBay] = []
        for i in range(len(merged_x) - 1):
            bx_start = merged_x[i]
            bx_end = merged_x[i + 1]
            bw = round(bx_end - bx_start, 2)
            mid_x = round((bx_start + bx_end) / 2.0, 2)

            # Classify bay usage based on intersecting room polygons
            g_usage = "DRAWING_ROOM"
            u_usage = "CANTILEVERED_SUITE"
            roof_usage = "ROOFTOP_DECK"

            # Check ground floor room under this bay
            for r in l0_rooms:
                rx_min = min(p[0] for p in r.polygon) - min_x
                rx_max = max(p[0] for p in r.polygon) - min_x
                ry_min = min(p[1] for p in r.polygon) - min_y
                if ry_min <= front_thresh and (rx_min < bx_end and rx_max > bx_start):
                    rname = r.room_name.lower()
                    if "porch" in rname or r.room_type == "garage":
                        g_usage = "CAR_PORCH"
                        u_usage = "PERGOLA_TERRACE"
                        break
                    elif any(k in rname for k in ("foyer", "portico", "entrance", "vestibule")):
                        g_usage = "FOYER_ENTRANCE"
                        break
                    elif "drawing" in rname or "living" in rname:
                        g_usage = "DRAWING_ROOM"

            # Check style overrides
            if "spanish" in cfg.style_id and g_usage == "CAR_PORCH":
                g_usage = "ARCHED_LOGGIA"
            elif "neoclassical" in cfg.style_id and g_usage in ("CAR_PORCH", "FOYER_ENTRANCE"):
                g_usage = "ENTRANCE_PORTICO"
            elif "brutalist" in cfg.style_id:
                if g_usage == "DRAWING_ROOM":
                    g_usage = "MONOLITHIC_SUITE"

            # Check if mumty falls inside this bay
            if bx_start <= stair_x_min < bx_end or bx_start < stair_x_max <= bx_end:
                roof_usage = "MUMTY_TOWER"

            # Scan openings in plan that fall into this bay
            bay_fenestrations: List[FenestrationAperture] = []
            for op in getattr(plan, "openings", []):
                pos = getattr(op, "position", None)
                if not pos or len(pos) < 2:
                    continue
                ox = round(pos[0] - min_x, 2)
                oy = round(pos[1] - min_y, 2)
                if bx_start <= ox <= bx_end and oy <= front_thresh:
                    lvl = getattr(op, "level_index", 0)
                    op_t = getattr(op, "opening_type", "window")
                    op_w = getattr(op, "width_m", 1.8)
                    op_h = getattr(op, "height_m", 2.1)

                    # Determine head style from style taxonomy
                    if "spanish" in cfg.style_id:
                        head = "semicircular_roman" if (op_t == "door" or lvl == 1) else "segmental_arched"
                        rev = 150
                        kstone = True
                        architrave = True
                    elif "neoclassical" in cfg.style_id:
                        head = "pedimented"
                        rev = 120
                        kstone = False
                        architrave = True
                    elif "brutalist" in cfg.style_id:
                        head = "deep_punched"
                        rev = 250
                        kstone = False
                        architrave = False
                    else:
                        head = "rectilinear"
                        rev = 50
                        kstone = False
                        architrave = False

                    fen = FenestrationAperture(
                        id=getattr(op, "opening_id", f"fen_{lvl}_{len(bay_fenestrations)}"),
                        level=lvl,
                        aperture_type=op_t,
                        rel_x=ox,
                        y_ground=cls.derive_datum_levels(num_floors)["plinth_level_m"] if lvl == 0 else cls.derive_datum_levels(num_floors)["first_floor_ffl_m"],
                        width_m=op_w,
                        height_m=op_h,
                        sill_height_m=0.0 if op_t == "door" else 0.65,
                        head_style=head,
                        reveal_depth_mm=rev,
                        has_architrave=architrave,
                        has_keystone=kstone,
                        mullion_pattern="divided_lite" if "spanish" in cfg.style_id or "neoclassical" in cfg.style_id else "minimalist_single"
                    )
                    bay_fenestrations.append(fen)

            col_bay = ColumnBay(
                index=i,
                name=f"Bay {chr(ord('A') + i)}",
                x_start=bx_start,
                x_end=bx_end,
                width=bw,
                center_x=mid_x,
                column_left_x=bx_start,
                column_right_x=bx_end,
                column_type=cfg.column_type,
                ground_usage=g_usage,
                upper_usage=u_usage,
                roof_usage=roof_usage,
                fenestrations=bay_fenestrations
            )
            bays.append(col_bay)

        datum_levels = cls.derive_datum_levels(num_floors, style_cfg=cfg)

        grid = StructuralGridInterface(
            plot_width_m=width_m,
            plot_length_m=depth_m,
            buildable_width_m=width_m,
            num_floors=num_floors,
            style_id=cfg.style_id,
            style_display_name=cfg.display_name,
            workflow_mode="floor_plan_first",
            bays=bays,
            stair_x_min=stair_x_min,
            stair_x_max=stair_x_max,
            stair_width=stair_w,
            stair_on_left=stair_on_left,
            datum_levels=datum_levels,
            facade_parameters=cfg.facade_parameters
        )
        return grid

    # =========================================================================
    # WORKFLOW 2: "ELEVATION FIRST / STYLE FIRST"
    # =========================================================================
    @classmethod
    def create_facade_driven_grid(
        cls,
        style_id: str,
        plot_width_m: float,
        plot_length_m: float,
        floors: int = 2,
        facade_profile: Optional[Dict[str, Any]] = None
    ) -> StructuralGridInterface:
        """
        WORKFLOW 2:
        Select an architectural elevation style and profile first, parameterizing
        front fenestrations, column bays, and rooflines to drive floor plan room zoning accordingly.
        """
        cfg = ArchitecturalStyleEngine.get_style_by_id(style_id)
        facade_prof = facade_profile or {}

        # 1. Compute Architectural Column Bay Spans based on Style Taxonomy
        # - Spanish: Arched Loggia Arcade Bay (Porch) + Symmetrical or Picturesque Drawing Wing
        # - Neoclassical: Strict Symmetrical 3-Bay Tripartite Portico (Flanking wings + Grand Portico Center)
        # - Modern Contemporary: Asymmetric Floating Box Frame Bay + Glass Curtain Wall
        # - Brutalist: Monolithic Punched Bay + Recessed Lightwell Bay

        bays: List[ColumnBay] = []
        stair_on_left = facade_prof.get("stair_on_left", True)

        if "neoclassical" in cfg.style_id:
            # Neoclassical Symmetrical Tripartite Division: 30% Wing | 40% Grand Portico | 30% Wing
            w_flank = round(plot_width_m * 0.30, 2)
            w_portico = round(plot_width_m * 0.40, 2)

            bay_splits = [
                (0.0, w_flank, "Bay A (West Salon Wing)", "DRAWING_ROOM", "UPPER_STATELY_SUITE", "PEDIMENTED_CORNICE"),
                (w_flank, w_flank + w_portico, "Bay B (Grand Portico Axis)", "ENTRANCE_PORTICO", "COLONNADE_BALCONY", "TRIANGULAR_PEDIMENT"),
                (w_flank + w_portico, plot_width_m, "Bay C (East Dining Wing)", "FORMAL_DINING_ROOM", "UPPER_STATELY_SUITE", "PEDIMENTED_CORNICE"),
            ]
            stair_x_min = round(plot_width_m * 0.35, 2)
            stair_x_max = round(plot_width_m * 0.65, 2)

        elif "spanish" in cfg.style_id:
            # Spanish Colonial: 45% Arched Loggia / Porch Arcade | 15% Foyer Vault | 40% Formal Salon
            w_porch = round(plot_width_m * 0.45, 2)
            w_foyer = round(plot_width_m * 0.15, 2)
            w_draw = round(plot_width_m - w_porch - w_foyer, 2)

            if stair_on_left:
                bay_splits = [
                    (0.0, w_porch, "Bay A (Spanish Arched Arcade Loggia)", "ARCHED_LOGGIA", "ARCADED_LOGGIA_BALCONY", "MUMTY_TOWER"),
                    (w_porch, w_porch + w_foyer, "Bay B (Arched Entrance Portal)", "FOYER_ENTRANCE", "JULIET_BALCONY", "STEPPED_MISSION_GABLE"),
                    (w_porch + w_foyer, plot_width_m, "Bay C (Drawing Salon Wing)", "DRAWING_ROOM", "CANTILEVERED_SUITE", "TERRACOTTA_HIP_ROOF"),
                ]
                stair_x_min = round(w_porch * 0.15, 2)
                stair_x_max = round(w_porch * 0.85, 2)
            else:
                bay_splits = [
                    (0.0, w_draw, "Bay A (Drawing Salon Wing)", "DRAWING_ROOM", "CANTILEVERED_SUITE", "TERRACOTTA_HIP_ROOF"),
                    (w_draw, w_draw + w_foyer, "Bay B (Arched Entrance Portal)", "FOYER_ENTRANCE", "JULIET_BALCONY", "STEPPED_MISSION_GABLE"),
                    (w_draw + w_foyer, plot_width_m, "Bay C (Spanish Arched Arcade Loggia)", "ARCHED_LOGGIA", "ARCADED_LOGGIA_BALCONY", "MUMTY_TOWER"),
                ]
                stair_x_min = round(w_draw + w_foyer + w_porch * 0.15, 2)
                stair_x_max = round(w_draw + w_foyer + w_porch * 0.85, 2)

        elif "brutalist" in cfg.style_id:
            # Brutalist / Industrial: Heavy In-Situ Concrete Monolith (55%) | Raw Steel Pergola Court (45%)
            w_mono = round(plot_width_m * 0.55, 2)
            w_pergola = round(plot_width_m - w_mono, 2)

            if stair_on_left:
                bay_splits = [
                    (0.0, w_pergola, "Bay A (Raw Steel I-Beam Pergola Portal)", "CAR_PORCH", "PERGOLA_TERRACE", "RAW_STEEL_DECK"),
                    (w_pergola, plot_width_m, "Bay B (Monolithic Board-Marked Volume)", "MONOLITHIC_SUITE", "PUNCHED_APERTURE_ROOM", "MONOLITHIC_MUMTY"),
                ]
                stair_x_min = round(w_pergola + 0.5, 2)
                stair_x_max = round(w_pergola + 3.2, 2)
            else:
                bay_splits = [
                    (0.0, w_mono, "Bay A (Monolithic Board-Marked Volume)", "MONOLITHIC_SUITE", "PUNCHED_APERTURE_ROOM", "MONOLITHIC_MUMTY"),
                    (w_mono, plot_width_m, "Bay B (Raw Steel I-Beam Pergola Portal)", "CAR_PORCH", "PERGOLA_TERRACE", "RAW_STEEL_DECK"),
                ]
                stair_x_min = 0.5
                stair_x_max = 3.2

        else: # Modern Contemporary Default
            # Modern Contemporary: Floating Cantilever Box (48%) | Glass Curtain Wall Foyer (16%) | Carport (36%)
            w_car = round(plot_width_m * 0.40, 2)
            w_foyer = round(plot_width_m * 0.18, 2)
            w_box = round(plot_width_m - w_car - w_foyer, 2)

            if stair_on_left:
                bay_splits = [
                    (0.0, w_car, "Bay A (Cantilevered Double Carport)", "CAR_PORCH", "PERGOLA_TERRACE", "MUMTY_TOWER"),
                    (w_car, w_car + w_foyer, "Bay B (Glass Pivot Foyer Entry)", "FOYER_ENTRANCE", "FLUSH_CURTAIN_WALL", "ROOFTOP_DECK"),
                    (w_car + w_foyer, plot_width_m, "Bay C (Floating Geometric Box Suite)", "DRAWING_ROOM", "CANTILEVERED_SUITE", "PARAPET_GARDEN"),
                ]
                stair_x_min = round(w_car * 0.10, 2)
                stair_x_max = round(w_car * 0.85, 2)
            else:
                bay_splits = [
                    (0.0, w_box, "Bay A (Floating Geometric Box Suite)", "DRAWING_ROOM", "CANTILEVERED_SUITE", "PARAPET_GARDEN"),
                    (w_box, w_box + w_foyer, "Bay B (Glass Pivot Foyer Entry)", "FOYER_ENTRANCE", "FLUSH_CURTAIN_WALL", "ROOFTOP_DECK"),
                    (w_box + w_foyer, plot_width_m, "Bay C (Cantilevered Double Carport)", "CAR_PORCH", "PERGOLA_TERRACE", "MUMTY_TOWER"),
                ]
                stair_x_min = round(w_box + w_foyer + w_car * 0.10, 2)
                stair_x_max = round(w_box + w_foyer + w_car * 0.85, 2)

        # 2. Build bays and parameterize fenestration rhythm
        for idx, (x0, x1, bname, g_use, u_use, r_use) in enumerate(bay_splits):
            bw = round(x1 - x0, 2)
            mid = round((x0 + x1) / 2.0, 2)
            fens: List[FenestrationAperture] = []

            # Level 0 fenestration
            if g_use in ("FOYER_ENTRANCE", "ENTRANCE_PORTICO"):
                door_w = 1.35 if "spanish" in cfg.style_id or "neoclassical" in cfg.style_id else 1.50
                fens.append(FenestrationAperture(
                    id=f"entry_door_b{idx}",
                    level=0,
                    aperture_type="door",
                    rel_x=mid,
                    y_ground=0.65,
                    width_m=door_w,
                    height_m=2.45,
                    sill_height_m=0.0,
                    head_style="semicircular_roman" if "spanish" in cfg.style_id else "pedimented" if "neoclassical" in cfg.style_id else "rectilinear",
                    reveal_depth_mm=150 if "spanish" in cfg.style_id else 120 if "neoclassical" in cfg.style_id else 50,
                    has_architrave=True,
                    has_keystone="spanish" in cfg.style_id,
                    mullion_pattern="divided_lite" if "spanish" in cfg.style_id else "minimalist_single"
                ))
            elif g_use in ("DRAWING_ROOM", "MONOLITHIC_SUITE", "FORMAL_DINING_ROOM"):
                win_w = min(bw * 0.65, 3.20)
                fens.append(FenestrationAperture(
                    id=f"win_l0_b{idx}",
                    level=0,
                    aperture_type="window",
                    rel_x=mid,
                    y_ground=0.65,
                    width_m=win_w,
                    height_m=2.10,
                    sill_height_m=0.65,
                    head_style="segmental_arched" if "spanish" in cfg.style_id else "pedimented" if "neoclassical" in cfg.style_id else "deep_punched" if "brutalist" in cfg.style_id else "rectilinear",
                    reveal_depth_mm=150 if "spanish" in cfg.style_id else 120 if "neoclassical" in cfg.style_id else 250 if "brutalist" in cfg.style_id else 50,
                    has_architrave="brutalist" not in cfg.style_id,
                    has_keystone="spanish" in cfg.style_id,
                    mullion_pattern="divided_lite" if "spanish" in cfg.style_id or "neoclassical" in cfg.style_id else "industrial_mullion" if "brutalist" in cfg.style_id else "corner_butt"
                ))

            # Level 1 fenestration
            if u_use in ("CANTILEVERED_SUITE", "UPPER_STATELY_SUITE", "PUNCHED_APERTURE_ROOM", "FLUSH_CURTAIN_WALL"):
                uwin_w = min(bw * 0.70, 3.00)
                fens.append(FenestrationAperture(
                    id=f"win_l1_b{idx}",
                    level=1,
                    aperture_type="window",
                    rel_x=mid,
                    y_ground=4.13,
                    width_m=uwin_w,
                    height_m=2.20,
                    sill_height_m=0.65,
                    head_style="semicircular_roman" if "spanish" in cfg.style_id else "segmental_arched" if "neoclassical" in cfg.style_id else "deep_punched" if "brutalist" in cfg.style_id else "rectilinear",
                    reveal_depth_mm=150 if "spanish" in cfg.style_id else 120 if "neoclassical" in cfg.style_id else 250 if "brutalist" in cfg.style_id else 50,
                    has_architrave="brutalist" not in cfg.style_id,
                    has_keystone="spanish" in cfg.style_id,
                    mullion_pattern="divided_lite" if "spanish" in cfg.style_id or "neoclassical" in cfg.style_id else "industrial_mullion" if "brutalist" in cfg.style_id else "minimalist_single"
                ))

            bay = ColumnBay(
                index=idx,
                name=bname,
                x_start=x0,
                x_end=x1,
                width=bw,
                center_x=mid,
                column_left_x=x0,
                column_right_x=x1,
                column_type=cfg.column_type,
                ground_usage=g_use,
                upper_usage=u_use,
                roof_usage=r_use,
                fenestrations=fens
            )
            bays.append(bay)

        datum_levels = cls.derive_datum_levels(floors, style_cfg=cfg)

        grid = StructuralGridInterface(
            plot_width_m=plot_width_m,
            plot_length_m=plot_length_m,
            buildable_width_m=plot_width_m,
            num_floors=floors,
            style_id=cfg.style_id,
            style_display_name=cfg.display_name,
            workflow_mode="elevation_first",
            bays=bays,
            stair_x_min=stair_x_min,
            stair_x_max=stair_x_max,
            stair_width=round(stair_x_max - stair_x_min, 2),
            stair_on_left=stair_on_left,
            datum_levels=datum_levels,
            facade_parameters=cfg.facade_parameters
        )
        return grid

    @classmethod
    def derive_plan_zoning_from_grid(
        cls,
        grid: StructuralGridInterface,
        requirements: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Translates a facade-driven structural grid into interior spatial room zoning
        constraints (room positions, entrance axes, courtyard allocations, and staircase MUMTY placements).
        """
        reqs = requirements or {}
        w = grid.plot_width_m
        d = grid.plot_length_m

        # Extract front bay usages
        porch_bay = next((b for b in grid.bays if b.ground_usage in ("CAR_PORCH", "ARCHED_LOGGIA", "ENTRANCE_PORTICO")), grid.bays[0])
        foyer_bay = next((b for b in grid.bays if b.ground_usage == "FOYER_ENTRANCE"), None)
        drawing_bay = next((b for b in grid.bays if b.ground_usage in ("DRAWING_ROOM", "MONOLITHIC_SUITE", "FORMAL_DINING_ROOM")), grid.bays[-1])

        zoning = {
            "workflow": "elevation_first",
            "style_id": grid.style_id,
            "style_name": grid.style_display_name,
            "stair_mumty_core": {
                "x_min": grid.stair_x_min,
                "x_max": grid.stair_x_max,
                "width": grid.stair_width,
                "on_left": grid.stair_on_left
            },
            "front_porch_arcade": {
                "x_start": porch_bay.x_start,
                "width": porch_bay.width,
                "depth": round(min(5.8, d * 0.28), 2),
                "arcade_loggia": "spanish" in grid.style_id,
                "classical_portico": "neoclassical" in grid.style_id
            },
            "main_entrance_foyer": {
                "x_axis": foyer_bay.center_x if foyer_bay else (porch_bay.x_end if porch_bay.x_start == 0 else porch_bay.x_start),
                "width": foyer_bay.width if foyer_bay else 2.2,
                "aligned_to_bay": foyer_bay.name if foyer_bay else "Shared Boundary"
            },
            "front_drawing_salon": {
                "x_start": drawing_bay.x_start,
                "width": drawing_bay.width,
                "depth": round(min(5.2, d * 0.26), 2)
            },
            "recommended_strategy": (
                "courtyard_patio_centric" if "spanish" in grid.style_id
                else "rotunda_foyer_formal" if "neoclassical" in grid.style_id
                else "central_atrium_lightwell" if "brutalist" in grid.style_id
                else "open_living_minimalist"
            ),
            "openings_coordinate_table": [
                {
                    "bay": b.name,
                    "aperture": fen.id,
                    "level": fen.level,
                    "type": fen.aperture_type,
                    "x_m": fen.rel_x,
                    "width_m": fen.width_m,
                    "head_style": fen.head_style
                }
                for b in grid.bays for fen in b.fenestrations
            ]
        }
        return zoning
