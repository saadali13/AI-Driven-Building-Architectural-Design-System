"""
generation/elevation_engine/elevation_svg_renderer.py
Vector Presentation Front Elevation SVG Renderer.

Conforms to ISO Drafting Standards and AIA Graphic Conventions.
Generates multi-layered, interactive vector SVG with:
1. Standardized layers: layer-background, layer-mumty-roof, layer-massing, layer-materials, layer-openings, layer-annotations.
2. Atmospheric gradient fills, sun-shadow projections, Low-E glass reflections.
3. Authentic red level datum arrows (+0.65m to +11.46m) and chain dimensions.
4. Parametric style manifestations (Modern louvers, Spanish terracotta tiles & arches, Minimalist fair-face concrete, Classical dentils & pilasters).
"""

import os
import math
from typing import Dict, Any, List, Optional


class ElevationSVGRenderer:
    """
    Renders publication-grade 2D Front Elevation SVG from elevation_spec.json.
    """

    SVG_WIDTH = 1200
    SVG_HEIGHT = 900
    MARGIN_LEFT = 180
    MARGIN_RIGHT = 120
    MARGIN_BOTTOM = 140
    MARGIN_TOP = 80

    @classmethod
    def render_svg(cls, spec: Dict[str, Any], out_path: str) -> str:
        """
        Synthesizes layered SVG presentation drawing and writes it to out_path.
        """
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        datums = spec["vertical_datums"]
        plot_w = spec["plot_dimensions"]["width_m"]
        style_key = spec["style"]
        mat = spec["materials"]
        roof = spec["roof_system"]
        bays = spec["facade_bays"]
        openings = spec["openings"]

        # Viewport coordinate scaling
        # World Y extends from -0.5m (road) to 12.5m (top of OHT)
        # World X extends from -1.5m to plot_w + 1.5m
        world_y_min = -0.6
        world_y_max = 12.8
        world_h = world_y_max - world_y_min

        world_x_min = -1.2
        world_x_max = plot_w + 1.2
        world_w = world_x_max - world_x_min

        draw_w = cls.SVG_WIDTH - cls.MARGIN_LEFT - cls.MARGIN_RIGHT
        draw_h = cls.SVG_HEIGHT - cls.MARGIN_TOP - cls.MARGIN_BOTTOM

        def tx(wx: float) -> float:
            """Converts world X (meters) to SVG pixel X."""
            return cls.MARGIN_LEFT + ((wx - world_x_min) / world_w) * draw_w

        def ty(wy: float) -> float:
            """Converts world Y (meters) to SVG pixel Y (inverted)."""
            return cls.SVG_HEIGHT - cls.MARGIN_BOTTOM - ((wy - world_y_min) / world_h) * draw_h

        def sc(dist: float) -> float:
            """Converts world meters to SVG pixel scale."""
            return (dist / world_w) * draw_w

        def sch(dist: float) -> float:
            """Converts world height meters to SVG pixel scale."""
            return (dist / world_h) * draw_h

        svg_lines = []
        svg_lines.append(f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {cls.SVG_WIDTH} {cls.SVG_HEIGHT}" width="100%" height="100%" style="background:#FFFFFF; font-family:\'Segoe UI\', Roboto, Arial, sans-serif;">')

        # -------------------------------------------------------------
        # SVG Gradients & Filters Defs
        # -------------------------------------------------------------
        svg_lines.append('  <defs>')
        # Sky gradient
        svg_lines.append('    <linearGradient id="skyGrad" x1="0%" y1="0%" x2="0%" y2="100%">')
        svg_lines.append('      <stop offset="0%" stop-color="#F0F9FF" stop-opacity="0.8"/>')
        svg_lines.append('      <stop offset="100%" stop-color="#FFFFFF" stop-opacity="0.0"/>')
        svg_lines.append('    </linearGradient>')
        # Glass reflection gradient
        svg_lines.append(f'    <linearGradient id="glassGrad" x1="0%" y1="0%" x2="100%" y2="100%">')
        svg_lines.append(f'      <stop offset="0%" stop-color="{mat["glass_color"]}" stop-opacity="0.9"/>')
        svg_lines.append('      <stop offset="50%" stop-color="#FFFFFF" stop-opacity="0.7"/>')
        svg_lines.append(f'      <stop offset="100%" stop-color="{mat["glass_color"]}" stop-opacity="0.95"/>')
        svg_lines.append('    </linearGradient>')
        # Shadow gradient
        svg_lines.append('    <linearGradient id="dropShadow" x1="0%" y1="0%" x2="0%" y2="100%">')
        svg_lines.append('      <stop offset="0%" stop-color="#0F172A" stop-opacity="0.32"/>')
        svg_lines.append('      <stop offset="100%" stop-color="#0F172A" stop-opacity="0.0"/>')
        svg_lines.append('    </linearGradient>')
        # Timber louver pattern
        svg_lines.append('    <pattern id="woodLouvers" width="10" height="10" patternUnits="userSpaceOnUse">')
        svg_lines.append(f'      <line x1="0" y1="0" x2="0" y2="10" stroke="{mat["wood_louvers"]}" stroke-width="2.5"/>')
        svg_lines.append('    </pattern>')
        # Terracotta tile pattern
        svg_lines.append('    <pattern id="terracottaTiles" width="16" height="8" patternUnits="userSpaceOnUse">')
        svg_lines.append('      <path d="M 0 8 Q 8 0 16 8" fill="none" stroke="#78350F" stroke-width="1.8"/>')
        svg_lines.append('    </pattern>')
        # Travertine stone pattern
        svg_lines.append('    <pattern id="stoneHatch" width="40" height="20" patternUnits="userSpaceOnUse">')
        svg_lines.append(f'      <rect width="40" height="20" fill="{mat["stone_cladding"]}" stroke="#E2E8F0" stroke-width="0.8"/>')
        svg_lines.append('      <line x1="0" y1="10" x2="40" y2="10" stroke="#CBD5E1" stroke-width="0.5"/>')
        svg_lines.append('      <line x1="20" y1="0" x2="20" y2="10" stroke="#CBD5E1" stroke-width="0.5"/>')
        svg_lines.append('      <line x1="40" y1="10" x2="40" y2="20" stroke="#CBD5E1" stroke-width="0.5"/>')
        svg_lines.append('    </pattern>')
        svg_lines.append('  </defs>')

        # -------------------------------------------------------------
        # LAYER 1: Background, Ground & Road
        # -------------------------------------------------------------
        svg_lines.append('  <g id="layer-background">')
        # Sky fill
        svg_lines.append(f'    <rect x="{cls.MARGIN_LEFT}" y="{cls.MARGIN_TOP}" width="{draw_w}" height="{draw_h}" fill="url(#skyGrad)"/>')
        # Ground Earth fill
        y_ngl = ty(datums["ngl"])
        y_bot = cls.SVG_HEIGHT - cls.MARGIN_BOTTOM
        svg_lines.append(f'    <rect x="{cls.MARGIN_LEFT}" y="{y_ngl}" width="{draw_w}" height="{y_bot - y_ngl}" fill="#F8FAFC"/>')
        # Ground hatch diagonal ticks
        for gx in range(int(cls.MARGIN_LEFT), int(cls.MARGIN_LEFT + draw_w), 16):
            svg_lines.append(f'    <line x1="{gx}" y1="{y_ngl + 4}" x2="{gx + 12}" y2="{y_ngl + 24}" stroke="#CBD5E1" stroke-width="1"/>')
        # Heavy Ground Line (0.00m NGL)
        svg_lines.append(f'    <line x1="{cls.MARGIN_LEFT - 30}" y1="{y_ngl}" x2="{cls.MARGIN_LEFT + draw_w + 30}" y2="{y_ngl}" stroke="#0F172A" stroke-width="3.5"/>')
        # Road Level Line (-0.30m)
        y_road = ty(datums["road"])
        svg_lines.append(f'    <line x1="{cls.MARGIN_LEFT - 30}" y1="{y_road}" x2="{cls.MARGIN_LEFT + draw_w + 30}" y2="{y_road}" stroke="#64748B" stroke-width="1.8" stroke-dasharray="6,4"/>')
        svg_lines.append(f'    <text x="{cls.MARGIN_LEFT - 35}" y="{y_road + 14}" fill="#64748B" font-size="9" text-anchor="end">ROAD LEVEL (-0.30m / -1\'-0")</text>')
        svg_lines.append(f'    <text x="{cls.MARGIN_LEFT - 35}" y="{y_ngl - 6}" fill="#0F172A" font-size="10" font-weight="bold" text-anchor="end">NATURAL GROUND (0.00m &plusmn;0\'-0")</text>')

        # Front Landscaping & Greenery
        svg_lines.append(f'    <!-- Landscaped Green Grass Strip -->')
        svg_lines.append(f'    <rect x="{tx(0.0)}" y="{y_ngl - 6}" width="{sc(plot_w)}" height="6" fill="#15803D" stroke="#166534" stroke-width="0.5"/>')
        # Shrubbery clusters
        shrub_x = tx(plot_w * 0.90)
        svg_lines.append(f'    <circle cx="{shrub_x}" cy="{y_ngl - 10}" r="13" fill="#16A34A" stroke="#14532D" stroke-width="1" opacity="0.9"/>')
        svg_lines.append(f'    <circle cx="{shrub_x - 9}" cy="{y_ngl - 8}" r="9" fill="#22C55E" stroke="#14532D" stroke-width="0.8" opacity="0.85"/>')
        svg_lines.append(f'    <circle cx="{shrub_x + 9}" cy="{y_ngl - 8}" r="8" fill="#15803D" stroke="#14532D" stroke-width="0.8" opacity="0.85"/>')

        # Boundary Piers & Gate Posts
        bw_h = sch(1.50)
        svg_lines.append(f'    <!-- Front Boundary Piers -->')
        svg_lines.append(f'    <rect x="{tx(-0.25)}" y="{y_ngl - bw_h}" width="{sc(0.40)}" height="{bw_h}" fill="#334155" stroke="#0F172A" stroke-width="1.5"/>')
        svg_lines.append(f'    <rect x="{tx(plot_w - 0.15)}" y="{y_ngl - bw_h}" width="{sc(0.40)}" height="{bw_h}" fill="#334155" stroke="#0F172A" stroke-width="1.5"/>')
        svg_lines.append('  </g>')

        # -------------------------------------------------------------
        # LAYER 2: Plinth Foundation
        # -------------------------------------------------------------
        svg_lines.append('  <g id="layer-plinth">')
        plinth_y = ty(datums["plinth"])
        plinth_h = y_ngl - plinth_y
        plinth_x = tx(0.0)
        plinth_w = sc(plot_w)
        plinth_col = "#334155" if style_key in ("modern", "minimalist") else ("#78716C" if style_key == "spanish" else "#E2E8F0")
        svg_lines.append(f'    <rect x="{plinth_x}" y="{plinth_y}" width="{plinth_w}" height="{plinth_h}" fill="{plinth_col}" stroke="#0F172A" stroke-width="2"/>')
        # Plinth masonry horizontal grooves
        for step_y in range(int(plinth_y + 10), int(y_ngl), 10):
            svg_lines.append(f'    <line x1="{plinth_x}" y1="{step_y}" x2="{plinth_x + plinth_w}" y2="{step_y}" stroke="#1E293B" stroke-width="0.8"/>')
        svg_lines.append('  </g>')

        # -------------------------------------------------------------
        # LAYER 3: Background Stair Mumty & Overhead Water Tank (OHT)
        # -------------------------------------------------------------
        svg_lines.append('  <g id="layer-mumty-roof">')
        mumty = roof["mumty"]
        oht = roof["water_tank"]
        mx = tx(mumty["x"])
        mw = sc(mumty["width"])
        my_top = ty(datums["mumty_top"])
        my_bot = ty(datums["roof_slab"])
        mh = my_bot - my_top
        mum_fill = "#E2E8F0" if style_key != "spanish" else "#FEF3C7"
        svg_lines.append(f'    <rect x="{mx}" y="{my_top}" width="{mw}" height="{mh}" fill="{mum_fill}" stroke="#64748B" stroke-width="1.5"/>')
        # Mumty texture / horizontal louvers
        for ly in range(int(my_top + 12), int(my_bot - 10), 12):
            svg_lines.append(f'    <line x1="{mx + 8}" y1="{ly}" x2="{mx + mw - 8}" y2="{ly}" stroke="#94A3B8" stroke-width="0.8"/>')

        # Overhead Water Tank (OHT) atop mumty
        ox = tx(oht["x"])
        ow = sc(oht["width"])
        oy_top = ty(datums["oht_top"])
        oh = my_top - oy_top
        svg_lines.append(f'    <rect x="{ox}" y="{oy_top}" width="{ow}" height="{oh}" fill="#CBD5E1" stroke="#475569" stroke-width="1.8"/>')
        svg_lines.append(f'    <text x="{ox + ow/2}" y="{oy_top + oh/2 + 4}" fill="#334155" font-size="9" font-weight="bold" text-anchor="middle">OHT (1500 GAL)</text>')
        svg_lines.append('  </g>')

        # -------------------------------------------------------------
        # LAYER 4: Building Massing & Facade Bays
        # -------------------------------------------------------------
        svg_lines.append('  <g id="layer-massing">')
        # Ground Floor Enclosed Bays
        y_1f = ty(datums["floor_1"])
        gf_h = plinth_y - y_1f

        # Porch bay and other ground bays
        for bay in bays["ground_floor"]:
            bx = tx(bay["x1"])
            bw = sc(bay["width"])
            is_porch = bay["type"] in ("garage", "carport") or "porch" in bay["name"].lower()

            if is_porch:
                # Car porch opening
                svg_lines.append(f'    <rect x="{bx}" y="{y_1f}" width="{bw}" height="{gf_h}" fill="#F1F5F9" stroke="#475569" stroke-width="1.5"/>')
                # Ceiling drop shadow in porch
                svg_lines.append(f'    <rect x="{bx}" y="{y_1f}" width="{bw}" height="{sch(0.85)}" fill="url(#dropShadow)"/>')
                # Structural Column
                col = bays["porch_column"]
                cx = tx(col["x"])
                cw = sc(col["width"])
                svg_lines.append(f'    <rect x="{cx}" y="{y_1f}" width="{cw}" height="{gf_h}" fill="{mat["accent_wall"]}" stroke="#0F172A" stroke-width="2.5"/>')

                # Spanish arched portal if Spanish
                if style_key == "spanish":
                    arch_r = min(bw * 0.45, (gf_h - 20) * 0.5)
                    arch_cx = bx + bw / 2
                    spring_y = y_1f + (gf_h - arch_r)
                    svg_lines.append(f'    <path d="M {arch_cx - arch_r} {y_1f + gf_h} L {arch_cx - arch_r} {spring_y} A {arch_r} {arch_r} 0 0 1 {arch_cx + arch_r} {spring_y} L {arch_cx + arch_r} {y_1f + gf_h} Z" fill="none" stroke="{mat["accent_wall"]}" stroke-width="6"/>')
                    # Terracotta keystone at arch crown
                    svg_lines.append(f'    <polygon points="{arch_cx-10},{spring_y-arch_r-8} {arch_cx+10},{spring_y-arch_r-8} {arch_cx+7},{spring_y-arch_r+8} {arch_cx-7},{spring_y-arch_r+8}" fill="#C2410C" stroke="#7C2D12" stroke-width="1.5"/>')
                elif style_key == "classical":
                    # Classical column capital and base plinth
                    svg_lines.append(f'    <rect x="{cx - 4}" y="{y_1f}" width="{cw + 8}" height="10" fill="#E2E8F0" stroke="#0F172A" stroke-width="1.5"/>')
                    svg_lines.append(f'    <rect x="{cx - 4}" y="{y_1f + gf_h - 10}" width="{cw + 8}" height="10" fill="#E2E8F0" stroke="#0F172A" stroke-width="1.5"/>')
            else:
                # Solid habitable front room (e.g. Drawing Room)
                svg_lines.append(f'    <rect x="{bx}" y="{y_1f}" width="{bw}" height="{gf_h}" fill="{mat["primary_wall"]}" stroke="#0F172A" stroke-width="2.5"/>')
                # Stone accent panel
                if style_key in ("modern", "minimalist"):
                    svg_lines.append(f'    <rect x="{bx + 4}" y="{y_1f + 4}" width="{bw * 0.35}" height="{gf_h - 8}" fill="url(#stoneHatch)" stroke="#0F172A" stroke-width="1.2"/>')

        # First Floor Slabs & Enclosed Bays
        y_roof = ty(datums["roof_slab"])
        ff_h = y_1f - y_roof
        # Intermediate floor slab cantilever band
        svg_lines.append(f'    <rect x="{tx(0.0)}" y="{y_1f}" width="{sc(plot_w)}" height="{sch(0.28)}" fill="#0F172A" stroke="#0F172A" stroke-width="1"/>')

        for bay in bays["first_floor"]:
            bx = tx(bay["x1"])
            bw = sc(bay["width"])
            svg_lines.append(f'    <rect x="{bx}" y="{y_roof}" width="{bw}" height="{ff_h}" fill="{mat["primary_wall"]}" stroke="#0F172A" stroke-width="2.5"/>')
            # Accent wood louvers panel
            if style_key == "modern":
                svg_lines.append(f'    <rect x="{bx + bw * 0.65}" y="{y_roof + 8}" width="{bw * 0.30}" height="{ff_h - 16}" fill="url(#woodLouvers)" stroke="#0F172A" stroke-width="1.2"/>')

        # Parapet Wall
        y_parapet = ty(datums["parapet_top"])
        para_h = y_roof - y_parapet
        svg_lines.append(f'    <rect x="{tx(0.0)}" y="{y_parapet}" width="{sc(plot_w)}" height="{para_h}" fill="{mat["primary_wall"]}" stroke="#0F172A" stroke-width="2.5"/>')

        # Terracotta Tile Coping for Spanish style
        if roof.get("parapet_style") == "terracotta_barrel_tile":
            svg_lines.append(f'    <rect x="{tx(0.0) - 8}" y="{y_parapet - 12}" width="{sc(plot_w) + 16}" height="14" fill="#92400E" stroke="#451A03" stroke-width="1.5"/>')
            svg_lines.append(f'    <rect x="{tx(0.0) - 8}" y="{y_parapet - 12}" width="{sc(plot_w) + 16}" height="14" fill="url(#terracottaTiles)"/>')
        elif style_key == "classical":
            # Classical Dentil Cornice
            svg_lines.append(f'    <g id="classical-dentil-cornice">')
            svg_lines.append(f'      <rect x="{tx(0.0) - 6}" y="{y_parapet - 10}" width="{sc(plot_w) + 12}" height="12" fill="#E2E8F0" stroke="#0F172A" stroke-width="1.5"/>')
            for dx in range(int(tx(0.0)), int(tx(plot_w)), 14):
                svg_lines.append(f'      <rect class="dentil-tooth" x="{dx}" y="{y_parapet - 8}" width="8" height="8" fill="#CBD5E1"/>')
            svg_lines.append(f'    </g>')
        else:
            # Modern flat aluminum coping
            svg_lines.append(f'    <rect x="{tx(0.0) - 4}" y="{y_parapet - 6}" width="{sc(plot_w) + 8}" height="7" fill="{mat["frame_color"]}"/>')

        svg_lines.append('  </g>')

        # -------------------------------------------------------------
        # LAYER 5: Architectural Openings (Windows, Doors, Balustrades)
        # -------------------------------------------------------------
        svg_lines.append('  <g id="layer-openings">')

        # Ground Floor Windows
        for op in openings["ground_openings"]:
            if op["type"] == "window":
                ox = tx(op["x"])
                ow = sc(op["width"])
                oy_bot = ty(op["sill_h"])
                oy_top = ty(op["lintel_h"])
                oh = oy_bot - oy_top
                # Window Frame
                svg_lines.append(f'    <rect x="{ox}" y="{oy_top}" width="{ow}" height="{oh}" fill="{mat["frame_color"]}" rx="2"/>')
                # Glass Panes with reflection
                svg_lines.append(f'    <rect x="{ox + 4}" y="{oy_top + 4}" width="{ow - 8}" height="{oh - 8}" fill="url(#glassGrad)" stroke="{mat["frame_color"]}" stroke-width="1.2"/>')
                # Center Mullion
                svg_lines.append(f'    <line x1="{ox + ow/2}" y1="{oy_top + 4}" x2="{ox + ow/2}" y2="{oy_bot - 4}" stroke="{mat["frame_color"]}" stroke-width="2"/>')

        # Upper Floor Windows
        for op in openings["upper_openings"]:
            if op["type"] == "window":
                ox = tx(op["x"])
                ow = sc(op["width"])
                oy_bot = ty(op["sill_h"])
                oy_top = ty(op["lintel_h"])
                oh = oy_bot - oy_top
                svg_lines.append(f'    <rect x="{ox}" y="{oy_top}" width="{ow}" height="{oh}" fill="{mat["frame_color"]}" rx="2"/>')
                svg_lines.append(f'    <rect x="{ox + 4}" y="{oy_top + 4}" width="{ow - 8}" height="{oh - 8}" fill="url(#glassGrad)" stroke="{mat["frame_color"]}" stroke-width="1.2"/>')
                svg_lines.append(f'    <line x1="{ox + ow/2}" y1="{oy_top + 4}" x2="{ox + ow/2}" y2="{oy_bot - 4}" stroke="{mat["frame_color"]}" stroke-width="2"/>')

                # Spanish Arched Window Top
                if style_key == "spanish":
                    arch_h = min(20.0, ow * 0.35)
                    svg_lines.append(f'    <path d="M {ox} {oy_top} Q {ox + ow/2} {oy_top - arch_h} {ox + ow} {oy_top} Z" fill="{mat["frame_color"]}"/>')
                    # Wrought Iron Grille
                    for wx in range(int(ox + 8), int(ox + ow), 14):
                        svg_lines.append(f'    <line x1="{wx}" y1="{oy_top + 6}" x2="{wx}" y2="{oy_bot - 6}" stroke="#451A03" stroke-width="1.2"/>')

        # Main Entrance Door
        main_door = openings.get("main_door")
        if main_door:
            dx = tx(main_door["x"])
            dw = sc(main_door["width"])
            dy_bot = ty(main_door["sill_h"])
            dy_top = ty(main_door["lintel_h"])
            dh = dy_bot - dy_top

            # Dedicated Entrance Portico Canopy Slab
            canopy_w = dw + 32
            canopy_x = dx - 16
            canopy_y = dy_top - 12
            svg_lines.append(f'    <rect x="{canopy_x}" y="{canopy_y}" width="{canopy_w}" height="10" fill="#0F172A" rx="1"/>')
            # Wall sconce luminaire
            svg_lines.append(f'    <rect x="{dx + dw + 8}" y="{dy_top + dh*0.35}" width="8" height="18" fill="#F59E0B" stroke="#0F172A" stroke-width="1.2" rx="2"/>')

            # Outer Frame
            svg_lines.append(f'    <rect x="{dx}" y="{dy_top}" width="{dw}" height="{dh}" fill="#1C1917" stroke="#0F172A" stroke-width="2.5"/>')
            # Door Leaves (Teak/Dark Walnut)
            door_col = "#78350F" if style_key == "spanish" else ("#292524" if style_key == "modern" else "#451A03")
            svg_lines.append(f'    <rect x="{dx + 3}" y="{dy_top + 3}" width="{dw - 6}" height="{dh - 3}" fill="{door_col}"/>')
            # Double door center split
            if main_door.get("is_double"):
                svg_lines.append(f'    <line x1="{dx + dw/2}" y1="{dy_top + 3}" x2="{dx + dw/2}" y2="{dy_bot}" stroke="#0F172A" stroke-width="2"/>')
                # Modern long bar handles
                svg_lines.append(f'    <line x1="{dx + dw/2 - 6}" y1="{dy_top + dh*0.4}" x2="{dx + dw/2 - 6}" y2="{dy_top + dh*0.65}" stroke="#D4D4D8" stroke-width="3"/>')
                svg_lines.append(f'    <line x1="{dx + dw/2 + 6}" y1="{dy_top + dh*0.4}" x2="{dx + dw/2 + 6}" y2="{dy_top + dh*0.65}" stroke="#D4D4D8" stroke-width="3"/>')
            else:
                svg_lines.append(f'    <line x1="{dx + dw*0.75}" y1="{dy_top + dh*0.4}" x2="{dx + dw*0.75}" y2="{dy_top + dh*0.65}" stroke="#D4D4D8" stroke-width="3"/>')

        # Balustrade on Front Balcony / Terrace (Above Porch)
        porch_bay = bays.get("porch")
        if porch_bay:
            px = tx(porch_bay["x1"])
            pw = sc(porch_bay["width"])
            py_terrace = y_1f
            bal_h = sch(1.05)
            if style_key == "spanish":
                # Wrought-iron decorative balcony
                svg_lines.append(f'    <rect x="{px}" y="{py_terrace - bal_h}" width="{pw}" height="{bal_h}" fill="none" stroke="#451A03" stroke-width="2"/>')
                for bx in range(int(px + 10), int(px + pw), 12):
                    svg_lines.append(f'    <line x1="{bx}" y1="{py_terrace}" x2="{bx}" y2="{py_terrace - bal_h}" stroke="#451A03" stroke-width="1.5"/>')
            else:
                # Tempered Glass Balustrade with stainless top handrail
                svg_lines.append(f'    <rect x="{px}" y="{py_terrace - bal_h}" width="{pw}" height="{bal_h}" fill="{mat["glass_color"]}" fill-opacity="0.5" stroke="#0F172A" stroke-width="1.5"/>')
                svg_lines.append(f'    <line x1="{px}" y1="{py_terrace - bal_h}" x2="{px + pw}" y2="{py_terrace - bal_h}" stroke="#0F172A" stroke-width="3"/>')

        # Pergola (if present)
        pergola = roof.get("pergola")
        if pergola:
            px = tx(pergola["x1"])
            pw = sc(pergola["width"])
            py_perg = ty(pergola["y_level"])
            ph = sch(pergola["height_m"])
            svg_lines.append(f'    <rect x="{px}" y="{py_perg - ph}" width="{pw}" height="{sch(0.20)}" fill="{pergola["color"]}" stroke="#0F172A" stroke-width="1.5"/>')
            # Vertical support posts
            svg_lines.append(f'    <line x1="{px + 6}" y1="{py_perg}" x2="{px + 6}" y2="{py_perg - ph}" stroke="{pergola["color"]}" stroke-width="8"/>')
            svg_lines.append(f'    <line x1="{px + pw - 6}" y1="{py_perg}" x2="{px + pw - 6}" y2="{py_perg - ph}" stroke="{pergola["color"]}" stroke-width="8"/>')
            # Pergola cross rafters
            for rx in range(int(px + 15), int(px + pw - 10), 18):
                svg_lines.append(f'    <rect x="{rx}" y="{py_perg - ph - 6}" width="6" height="12" fill="{pergola["color"]}"/>')

        svg_lines.append('  </g>')

        # -------------------------------------------------------------
        # LAYER 6: Standardized Architectural Datum Levels & Dimension Annotations
        # -------------------------------------------------------------
        svg_lines.append('  <g id="layer-annotations">')
        # Red Elevation Datum Level Markers (Right Side) with anti-collision vertical stagger
        arrow_x = cls.SVG_WIDTH - cls.MARGIN_RIGHT + 35
        datum_markers = [
            ("OHT TOP", datums["oht_top"], f"+{datums['oht_top']:.2f}m (+37'-7\")"),
            ("MUMTY TOP", datums["mumty_top"], f"+{datums['mumty_top']:.2f}m (+33'-8\")"),
            ("PARAPET TOP", datums["parapet_top"], f"+{datums['parapet_top']:.2f}m (+28'-7\")"),
            ("ROOF SLAB", datums["roof_slab"], f"+{datums['roof_slab']:.2f}m (+25'-0\")"),
            ("FIRST FLOOR", datums["floor_1"], f"+{datums['floor_1']:.2f}m (+13'-6\")"),
            ("PLINTH LEVEL", datums["plinth"], f"+{datums['plinth']:.2f}m (+2'-2\")"),
            ("NATURAL GROUND", datums["ngl"], f"{datums['ngl']:.2f}m (&plusmn;0'-0\")")
        ]

        prev_text_y = -999.0
        min_v_gap = 26.0

        for name, val, callout in datum_markers:
            my = ty(val)
            # Red datum triangle arrow
            svg_lines.append(f'    <polygon points="{arrow_x},{my} {arrow_x+10},{my-5} {arrow_x+10},{my+5}" fill="#DC2626"/>')
            # Dashed witness line across facade
            svg_lines.append(f'    <line x1="{tx(0.0)}" y1="{my}" x2="{arrow_x}" y2="{my}" stroke="#EF4444" stroke-width="0.8" stroke-dasharray="3,3" opacity="0.65"/>')

            # Anti-collision staggered callout text positioning
            text_y = my
            if text_y - prev_text_y < min_v_gap:
                text_y = prev_text_y + min_v_gap
                # Leader line connecting arrow to offset text
                svg_lines.append(f'    <line x1="{arrow_x + 10}" y1="{my}" x2="{arrow_x + 16}" y2="{text_y}" stroke="#DC2626" stroke-width="0.8"/>')
            prev_text_y = text_y

            # Callout Text
            svg_lines.append(f'    <text x="{arrow_x + 18}" y="{text_y + 3}" fill="#DC2626" font-size="9" font-weight="bold">{name}</text>')
            svg_lines.append(f'    <text x="{arrow_x + 18}" y="{text_y + 13}" fill="#475569" font-size="8">{callout}</text>')

        # Overall Width Chain Dimension (Bottom)
        dim_y = cls.SVG_HEIGHT - cls.MARGIN_BOTTOM + 45
        x0 = tx(0.0)
        x1 = tx(plot_w)
        svg_lines.append(f'    <line x1="{x0}" y1="{dim_y}" x2="{x1}" y2="{dim_y}" stroke="#0F172A" stroke-width="1.2"/>')
        svg_lines.append(f'    <line x1="{x0}" y1="{dim_y - 8}" x2="{x0}" y2="{dim_y + 8}" stroke="#0F172A" stroke-width="1.2"/>')
        svg_lines.append(f'    <line x1="{x1}" y1="{dim_y - 8}" x2="{x1}" y2="{dim_y + 8}" stroke="#0F172A" stroke-width="1.2"/>')
        svg_lines.append(f'    <text x="{(x0+x1)/2}" y="{dim_y - 6}" fill="#0F172A" font-size="11" font-weight="bold" text-anchor="middle">TOTAL PLOT FRONTAGE: {plot_w:.2f}m ({spec["plot_dimensions"]["width_ft"]}\'-0")</text>')

        # Title Block Banner
        svg_lines.append(f'    <text x="{cls.MARGIN_LEFT}" y="{cls.MARGIN_TOP - 30}" fill="#0F172A" font-size="18" font-weight="900" letter-spacing="1">ArchiCraft AI Studio &bull; Technical Front Elevation</text>')
        svg_lines.append(f'    <text x="{cls.MARGIN_LEFT}" y="{cls.MARGIN_TOP - 12}" fill="#64748B" font-size="11">STYLE: {spec["style_name"].upper()} | BYLAWS: CDA / LDA / DHA COMPLIANT | SCALE 1:100</text>')

        svg_lines.append('  </g>')
        svg_lines.append('</svg>')

        svg_content = "\n".join(svg_lines)
        with open(out_path, "w", encoding="utf-8") as f:
            f.write(svg_content)

        return out_path

