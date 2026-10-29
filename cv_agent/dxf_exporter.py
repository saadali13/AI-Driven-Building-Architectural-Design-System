"""
AutoCAD DXF Exporter for Extracted Architectural Floor Plans.

Converts extracted architectural geometry into standardized layered DXF (R2018)
using the ezdxf library adhering to AIA CAD Layer Guidelines.
"""

import os
import math
from typing import Dict, List, Any, Optional, Tuple
import ezdxf
from ezdxf.enums import TextEntityAlignment


class ArchitecturalDXFExporter:
    """
    Exports extracted floor plan vectors to layered AutoCAD DXF.
    """

    @staticmethod
    def _setup_layers(doc):
        """Initializes standardized AIA CAD layers with standard colors and lineweights."""
        doc.layers.add("A-WALL-EXTR", color=4, lineweight=50)    # Cyan (0.50mm)
        doc.layers.add("A-WALL-INTR", color=7, lineweight=25)    # White (0.25mm)
        doc.layers.add("A-DOOR", color=1, lineweight=25)         # Red (0.25mm)
        doc.layers.add("A-GLAZ", color=3, lineweight=25)         # Green (0.25mm)
        doc.layers.add("A-STRS", color=6, lineweight=35)         # Magenta (0.35mm)
        doc.layers.add("A-ANNO-TEXT", color=2, lineweight=25)    # Yellow (0.25mm)
        doc.layers.add("A-ANNO-DIMS", color=5, lineweight=18)    # Blue (0.18mm)
        doc.layers.add("A-AREA", color=8, lineweight=18)         # Gray (0.18mm)

    @classmethod
    def export(
        cls,
        extracted_data: Dict[str, Any],
        output_path: str,
        scale_factor: float = 1.0
    ) -> str:
        """
        Renders extracted floor plan into DXF file.
        Inverts Y-axis so standard image coordinates map naturally to CAD Cartesian space.
        """
        doc = ezdxf.new("R2018")
        cls._setup_layers(doc)
        msp = doc.modelspace()

        h = extracted_data.get("image_size", (800, 1000))[1]

        def to_cad(x: float, y: float) -> Tuple[float, float]:
            return (float(x) * scale_factor, float(h - y) * scale_factor)

        # 1. Walls
        walls_info = extracted_data.get("walls", {})
        wall_segments = walls_info.get("wall_segments", [])
        for seg in wall_segments:
            s_pt = seg.get("start_px", [0, 0])
            e_pt = seg.get("end_px", [0, 0])
            layer = "A-WALL-EXTR" if seg.get("is_exterior", False) else "A-WALL-INTR"
            p1 = to_cad(s_pt[0], s_pt[1])
            p2 = to_cad(e_pt[0], e_pt[1])
            msp.add_line(p1, p2, dxfattribs={"layer": layer})

        # 2. Room Boundary Polylines (on A-AREA)
        rooms = extracted_data.get("rooms", [])
        for room in rooms:
            pts = room.get("pixel_polygon", room.get("polygon_px", []))
            if len(pts) >= 3:
                cad_pts = [to_cad(p[0], p[1]) for p in pts]
                msp.add_lwpolyline(cad_pts, close=True, dxfattribs={"layer": "A-AREA"})

        # 3. Windows
        windows = extracted_data.get("windows", [])
        for win in windows:
            s_pt = win.get("start_px", [0, 0])
            e_pt = win.get("end_px", [0, 0])
            p1 = to_cad(s_pt[0], s_pt[1])
            p2 = to_cad(e_pt[0], e_pt[1])
            msp.add_line(p1, p2, dxfattribs={"layer": "A-GLAZ"})

        # 4. Doors & Swing Arcs
        doors = extracted_data.get("doors", [])
        for door in doors:
            pos = door.get("position_px", [0, 0])
            r = float(door.get("swing_radius_px", 24)) * scale_factor
            cp = to_cad(pos[0], pos[1])
            # Add door hinge / position marker
            msp.add_circle(cp, radius=2.0 * scale_factor, dxfattribs={"layer": "A-DOOR"})
            # Approximate 90-degree swing arc
            msp.add_arc(cp, radius=r, start_angle=0, end_angle=90, dxfattribs={"layer": "A-DOOR"})

        # 5. Stairs
        stairs = extracted_data.get("stairs", [])
        for stair in stairs:
            bbox = stair.get("bbox_px", [])
            if len(bbox) == 4:
                x1, y1, x2, y2 = bbox
                c_p1 = to_cad(x1, y1)
                c_p2 = to_cad(x2, y2)
                poly = [c_p1, (c_p2[0], c_p1[1]), c_p2, (c_p1[0], c_p2[1])]
                msp.add_lwpolyline(poly, close=True, dxfattribs={"layer": "A-STRS"})

        # 6. Room Names & Dimensions (on A-ANNO-TEXT)
        for room in rooms:
            name = room.get("room_name", "ROOM")
            dim = room.get("original_dimension_text") or room.get("dimension_str") or ""
            bbox = room.get("pixel_bounding_box", [])
            if len(bbox) == 4:
                cx = (bbox[0] + bbox[2]) / 2.0
                cy = (bbox[1] + bbox[3]) / 2.0
                c_pos = to_cad(cx, cy)
                msp.add_text(
                    name.upper(),
                    height=max(8.0, 12.0 * scale_factor),
                    dxfattribs={"layer": "A-ANNO-TEXT"}
                ).set_placement(c_pos, align=TextEntityAlignment.MIDDLE_CENTER)

                if dim:
                    dim_pos = (c_pos[0], c_pos[1] - 16.0 * scale_factor)
                    msp.add_text(
                        dim,
                        height=max(6.0, 9.0 * scale_factor),
                        dxfattribs={"layer": "A-ANNO-DIMS"}
                    ).set_placement(dim_pos, align=TextEntityAlignment.MIDDLE_CENTER)

        os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
        doc.saveas(output_path)
        return output_path
