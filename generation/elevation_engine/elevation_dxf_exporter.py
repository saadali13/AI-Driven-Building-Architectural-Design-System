"""
generation/elevation_engine/elevation_dxf_exporter.py
AIA-Standard Layered AutoCAD DXF Front Elevation Exporter.

Conforms to American Institute of Architects (AIA) CAD Layer Guidelines:
- A-ELEV-WALL: Exterior thermal envelope, facade bays, columns (Lineweight 0.50mm, Color 4 Cyan)
- A-ELEV-ROOF: Parapet, mumty penthouse, slabs, overhead water tank (Lineweight 0.35mm, Color 6 Magenta)
- A-ELEV-GLAZ: Window frames, door leaves, mullions (Lineweight 0.25mm, Color 3 Green)
- A-ELEV-HATCH: Materials, stone texture, earth hatch, tile lines (Lineweight 0.18mm, Color 8 Gray)
- A-ELEV-DIMS: Height level lines, width dimension strings, tick marks (Lineweight 0.18mm, Color 5 Blue)
- A-ELEV-TEXT: Datum callouts, titles, annotations (Lineweight 0.25mm, Color 2 Yellow)
"""

import os
import math
from typing import Dict, Any, List, Optional
import ezdxf
from ezdxf.enums import TextEntityAlignment


class ElevationDXFExporter:
    """
    AutoCAD DXF Elevation Exporter conforming to AIA layering standards.
    """

    @classmethod
    def export_dxf(cls, spec: Dict[str, Any], out_path: str, dxf_version: str = "R2018") -> str:
        """
        Exports the elevation specification into an AIA-compliant layered DXF drawing.
        """
        os.makedirs(os.path.dirname(os.path.abspath(out_path)), exist_ok=True)

        doc = ezdxf.new(dxfversion=dxf_version, setup=True)
        msp = doc.modelspace()

        # Setup Standard AIA Elevation Layers
        doc.layers.add("A-ELEV-WALL", color=4, lineweight=50)   # Cyan, 0.50mm
        doc.layers.add("A-ELEV-ROOF", color=6, lineweight=35)   # Magenta, 0.35mm
        doc.layers.add("A-ELEV-GLAZ", color=3, lineweight=25)   # Green, 0.25mm
        doc.layers.add("A-ELEV-HATCH", color=8, lineweight=18)  # Gray, 0.18mm
        doc.layers.add("A-ELEV-DIMS", color=5, lineweight=18)   # Blue, 0.18mm
        doc.layers.add("A-ELEV-TEXT", color=2, lineweight=25)   # Yellow, 0.25mm

        datums = spec["vertical_datums"]
        plot_w = spec["plot_dimensions"]["width_m"]
        bays = spec["facade_bays"]
        openings = spec["openings"]
        roof = spec["roof_system"]

        # -------------------------------------------------------------
        # 1. Ground, Road & Plinth (A-ELEV-WALL, A-ELEV-HATCH)
        # -------------------------------------------------------------
        y_ngl = datums["ngl"]
        y_road = datums["road"]
        y_plinth = datums["plinth"]
        y_1f = datums["floor_1"]
        y_roof = datums["roof_slab"]
        y_para = datums["parapet_top"]

        # Natural Ground Line
        msp.add_lwpolyline([(-1.5, y_ngl), (plot_w + 1.5, y_ngl)], dxfattribs={"layer": "A-ELEV-WALL"})
        # Road Level Line
        msp.add_lwpolyline([(-1.5, y_road), (plot_w + 1.5, y_road)], dxfattribs={"layer": "A-ELEV-DIMS"})

        # Plinth Foundation Box
        msp.add_lwpolyline([(0.0, y_ngl), (plot_w, y_ngl), (plot_w, y_plinth), (0.0, y_plinth)], close=True, dxfattribs={"layer": "A-ELEV-WALL"})
        # Plinth hatch lines
        for py in [y_ngl + 0.22, y_ngl + 0.44]:
            if py < y_plinth:
                msp.add_line((0.0, py), (plot_w, py), dxfattribs={"layer": "A-ELEV-HATCH"})

        # -------------------------------------------------------------
        # 2. Main Wall Massing & Facade Bays (A-ELEV-WALL)
        # -------------------------------------------------------------
        # Ground Floor Bays
        for bay in bays["ground_floor"]:
            bx1, bx2 = bay["x1"], bay["x2"]
            is_porch = bay["type"] in ("garage", "carport") or "porch" in bay["name"].lower()
            if is_porch:
                # Car porch opening
                msp.add_lwpolyline([(bx1, y_plinth), (bx2, y_plinth), (bx2, y_1f), (bx1, y_1f)], close=True, dxfattribs={"layer": "A-ELEV-WALL"})
                # Column
                col = bays["porch_column"]
                cx, cw = col["x"], col["width"]
                msp.add_lwpolyline([(cx, y_plinth), (cx + cw, y_plinth), (cx + cw, y_1f), (cx, y_1f)], close=True, dxfattribs={"layer": "A-ELEV-WALL"})
            else:
                msp.add_lwpolyline([(bx1, y_plinth), (bx2, y_plinth), (bx2, y_1f), (bx1, y_1f)], close=True, dxfattribs={"layer": "A-ELEV-WALL"})

        # Floor Slab Band
        msp.add_lwpolyline([(0.0, y_1f), (plot_w, y_1f), (plot_w, y_1f + 0.28), (0.0, y_1f + 0.28)], close=True, dxfattribs={"layer": "A-ELEV-WALL"})

        # Upper Floor Bays
        for bay in bays["first_floor"]:
            bx1, bx2 = bay["x1"], bay["x2"]
            msp.add_lwpolyline([(bx1, y_1f + 0.28), (bx2, y_1f + 0.28), (bx2, y_roof), (bx1, y_roof)], close=True, dxfattribs={"layer": "A-ELEV-WALL"})

        # Roof Slab Band
        msp.add_lwpolyline([(0.0, y_roof), (plot_w, y_roof), (plot_w, y_roof + 0.28), (0.0, y_roof + 0.28)], close=True, dxfattribs={"layer": "A-ELEV-ROOF"})

        # Roof Parapet Wall
        msp.add_lwpolyline([(0.0, y_roof + 0.28), (plot_w, y_roof + 0.28), (plot_w, y_para), (0.0, y_para)], close=True, dxfattribs={"layer": "A-ELEV-ROOF"})

        # -------------------------------------------------------------
        # 3. Mumty & Overhead Water Tank (A-ELEV-ROOF)
        # -------------------------------------------------------------
        mumty = roof["mumty"]
        oht = roof["water_tank"]
        mx, mw = mumty["x"], mumty["width"]
        my_top = datums["mumty_top"]
        msp.add_lwpolyline([(mx, y_roof + 0.28), (mx + mw, y_roof + 0.28), (mx + mw, my_top), (mx, my_top)], close=True, dxfattribs={"layer": "A-ELEV-ROOF"})

        # OHT atop mumty
        ox, ow = oht["x"], oht["width"]
        oy_top = datums["oht_top"]
        msp.add_lwpolyline([(ox, my_top), (ox + ow, my_top), (ox + ow, oy_top), (ox, oy_top)], close=True, dxfattribs={"layer": "A-ELEV-ROOF"})
        msp.add_text("OHT (1500 GAL)", dxfattribs={"layer": "A-ELEV-TEXT", "height": 0.25}).set_placement((ox + ow / 2, my_top + 0.45), align=TextEntityAlignment.MIDDLE_CENTER)

        # -------------------------------------------------------------
        # 4. Openings & Glazing (A-ELEV-GLAZ)
        # -------------------------------------------------------------
        # Ground Windows
        for op in openings["ground_openings"]:
            if op["type"] == "window":
                ox, ow = op["x"], op["width"]
                sy, ly = op["sill_h"], op["lintel_h"]
                msp.add_lwpolyline([(ox, sy), (ox + ow, sy), (ox + ow, ly), (ox, ly)], close=True, dxfattribs={"layer": "A-ELEV-GLAZ"})
                # Center mullion
                msp.add_line((ox + ow / 2, sy), (ox + ow / 2, ly), dxfattribs={"layer": "A-ELEV-GLAZ"})

        # Upper Windows
        for op in openings["upper_openings"]:
            if op["type"] == "window":
                ox, ow = op["x"], op["width"]
                sy, ly = op["sill_h"], op["lintel_h"]
                msp.add_lwpolyline([(ox, sy), (ox + ow, sy), (ox + ow, ly), (ox, ly)], close=True, dxfattribs={"layer": "A-ELEV-GLAZ"})
                msp.add_line((ox + ow / 2, sy), (ox + ow / 2, ly), dxfattribs={"layer": "A-ELEV-GLAZ"})

        # Main Entrance Door
        main_door = openings.get("main_door")
        if main_door:
            dx, dw = main_door["x"], main_door["width"]
            sy, ly = main_door["sill_h"], main_door["lintel_h"]
            msp.add_lwpolyline([(dx, sy), (dx + dw, sy), (dx + dw, ly), (dx, ly)], close=True, dxfattribs={"layer": "A-ELEV-GLAZ"})
            if main_door.get("is_double"):
                msp.add_line((dx + dw / 2, sy), (dx + dw / 2, ly), dxfattribs={"layer": "A-ELEV-GLAZ"})

        # -------------------------------------------------------------
        # 5. Dimensions & Annotations (A-ELEV-DIMS, A-ELEV-TEXT)
        # -------------------------------------------------------------
        # Level Marker Lines
        markers = [
            ("OHT TOP", datums["oht_top"]),
            ("MUMTY TOP", datums["mumty_top"]),
            ("PARAPET TOP", datums["parapet_top"]),
            ("ROOF SLAB", datums["roof_slab"]),
            ("FIRST FLOOR", datums["floor_1"]),
            ("PLINTH", datums["plinth"]),
            ("NGL", datums["ngl"])
        ]
        ann_x = plot_w + 1.2
        for name, val in markers:
            msp.add_line((plot_w, val), (ann_x + 1.5, val), dxfattribs={"layer": "A-ELEV-DIMS"})
            msp.add_text(f"{name} +{val:.2f}m", dxfattribs={"layer": "A-ELEV-TEXT", "height": 0.22}).set_placement((ann_x + 1.7, val), align=TextEntityAlignment.MIDDLE_LEFT)

        # Total Width Dimension
        dim_y = y_ngl - 0.75
        msp.add_line((0.0, dim_y), (plot_w, dim_y), dxfattribs={"layer": "A-ELEV-DIMS"})
        msp.add_line((0.0, dim_y - 0.15), (0.0, dim_y + 0.15), dxfattribs={"layer": "A-ELEV-DIMS"})
        msp.add_line((plot_w, dim_y - 0.15), (plot_w, dim_y + 0.15), dxfattribs={"layer": "A-ELEV-DIMS"})
        msp.add_text(f"FRONTAGE {plot_w:.2f}m ({spec['plot_dimensions']['width_ft']}')", dxfattribs={"layer": "A-ELEV-TEXT", "height": 0.30}).set_placement((plot_w / 2, dim_y + 0.20), align=TextEntityAlignment.BOTTOM_CENTER)

        # Drawing Title
        msp.add_text("ARCHITECTURAL FRONT ELEVATION", dxfattribs={"layer": "A-ELEV-TEXT", "height": 0.45}).set_placement((0.0, oy_top + 1.0), align=TextEntityAlignment.BOTTOM_LEFT)
        msp.add_text(f"STYLE: {spec['style_name'].upper()} | AIA LAYERS | SCALE 1:100", dxfattribs={"layer": "A-ELEV-TEXT", "height": 0.25}).set_placement((0.0, oy_top + 0.55), align=TextEntityAlignment.BOTTOM_LEFT)

        doc.saveas(out_path)
        return out_path

