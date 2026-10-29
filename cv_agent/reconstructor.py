"""
Exact Image Reconstruction Engine.

Generates:
1. Faithful raster reconstruction (PNG) preserving original canvas, wall geometry,
   thicknesses, door swings, windows, stairs, and annotations.
2. Structured vector reconstruction (SVG) with organized layers (rooms, walls, doors, windows, stairs, labels).
3. Visual verification overlay combining source and detected vector geometry.
"""

import os
from typing import Dict, List, Tuple, Any, Optional
import cv2
import numpy as np


class FloorPlanReconstructor:
    """
    Renders deterministic architectural reconstructions from extracted vector metadata.
    """

    def __init__(self, bg_color: Tuple[int, int, int] = (255, 255, 255)):
        self.bg_color = bg_color

    def render_faithful_raster(
        self,
        extracted_data: Dict[str, Any],
        target_size: Optional[Tuple[int, int]] = None,
        scale_factor: float = 1.0
    ) -> np.ndarray:
        """
        Renders a high-fidelity raster floor plan matching the source image dimensions.
        Preserves original wall layout, thickness, windows, door swing arcs, stairs, and text annotations.
        """
        w, h = extracted_data.get("image_size", (800, 1000))
        if target_size is not None:
            w, h = target_size

        tw = int(w * scale_factor)
        th = int(h * scale_factor)

        bg = extracted_data.get("background_color_bgr", self.bg_color)
        canvas = np.full((th, tw, 3), bg, dtype=np.uint8)

        walls_info = extracted_data.get("walls", {})
        wall_contours = walls_info.get("wall_contours", [])
        thickness = int(max(2, walls_info.get("wall_thickness_px", 4) * scale_factor))

        # 1. Render Room Fills (respects paper tone to avoid massive artificial color deltas)
        rooms = extracted_data.get("rooms", [])
        bg_mean = float(np.mean(bg))
        for room in rooms:
            pts = room.get("polygon_px", [])
            if len(pts) >= 3:
                scaled_pts = np.array(
                    [[int(p[0] * scale_factor), int(p[1] * scale_factor)] for p in pts],
                    dtype=np.int32
                )
                category = room.get("assigned_category", "room")
                if bg_mean > 240:
                    if category == "bathroom":
                        fill_col = (245, 250, 240)
                    elif category == "kitchen":
                        fill_col = (240, 248, 255)
                    elif category == "car_porch":
                        fill_col = (245, 245, 245)
                    elif category == "ots":
                        fill_col = (250, 250, 240)
                    else:
                        fill_col = tuple(int(c) for c in bg)
                else:
                    # On aged, blueprint, or off-white paper, match detected background
                    fill_col = tuple(int(c) for c in bg)

                cv2.fillPoly(canvas, [scaled_pts], fill_col)

        # 2. Render Walls (clean structural wall segments; fallback to contours if no segments)
        wall_color = (20, 20, 20) if bg_mean > 100 else (235, 235, 235)
        wall_segments = walls_info.get("wall_segments", [])
        measured_thick = int(max(3, walls_info.get("wall_thickness_px", 4) * scale_factor))
        if wall_segments:
            for seg in wall_segments:
                s_pt = seg.get("start_px", [0, 0])
                e_pt = seg.get("end_px", [0, 0])
                p1 = (int(s_pt[0] * scale_factor), int(s_pt[1] * scale_factor))
                p2 = (int(e_pt[0] * scale_factor), int(e_pt[1] * scale_factor))
                seg_thick = int(max(measured_thick, seg.get("thickness_px", 3) * scale_factor))
                cv2.line(canvas, p1, p2, wall_color, seg_thick, cv2.LINE_AA)
        else:
            for poly in wall_contours:
                if len(poly) >= 2:
                    scaled_pts = np.array(
                        [[int(p[0] * scale_factor), int(p[1] * scale_factor)] for p in poly],
                        dtype=np.int32
                    )
                    is_closed = (len(poly) >= 3)
                    cv2.polylines(canvas, [scaled_pts], isClosed=is_closed, color=wall_color, thickness=max(2, thickness // 2))

        # 3. Render Windows (parallel fenestration lines in architectural ink)
        windows = extracted_data.get("windows", [])
        win_color = (45, 45, 45) if bg_mean > 100 else (210, 210, 210)
        for win in windows:
            start = win.get("start_px", [0, 0])
            end = win.get("end_px", [0, 0])
            p1 = (int(start[0] * scale_factor), int(start[1] * scale_factor))
            p2 = (int(end[0] * scale_factor), int(end[1] * scale_factor))
            orient = win.get("orientation", "horizontal")
            # Draw double mullion line for realistic architectural window
            if orient == "horizontal":
                cv2.line(canvas, (p1[0], p1[1] - 1), (p2[0], p2[1] - 1), win_color, 1, cv2.LINE_AA)
                cv2.line(canvas, (p1[0], p1[1] + 1), (p2[0], p2[1] + 1), win_color, 1, cv2.LINE_AA)
            else:
                cv2.line(canvas, (p1[0] - 1, p1[1]), (p2[0] - 1, p2[1]), win_color, 1, cv2.LINE_AA)
                cv2.line(canvas, (p1[0] + 1, p1[1]), (p2[0] + 1, p2[1]), win_color, 1, cv2.LINE_AA)

        # 4. Render Staircases
        stairs = extracted_data.get("stairs", [])
        for stair in stairs:
            bbox = stair.get("bbox_px", [])
            if len(bbox) == 4:
                x1, y1, x2, y2 = [int(v * scale_factor) for v in bbox]
                cv2.rectangle(canvas, (x1, y1), (x2, y2), wall_color, 1)
                steps = stair.get("approx_steps", 10)
                step_h = max(3, (y2 - y1) // max(1, min(steps, 14)))
                for sy in range(y1 + step_h, y2, step_h):
                    cv2.line(canvas, (x1, sy), (x2, sy), wall_color, 1)
                cv2.arrowedLine(
                    canvas,
                    (x1 + (x2 - x1) // 2, y2 - 4),
                    (x1 + (x2 - x1) // 2, y1 + 8),
                    wall_color,
                    1,
                    tipLength=0.2
                )

        # 5. Render Doors and Swing Arcs
        doors = extracted_data.get("doors", [])
        door_arc_color = (75, 75, 75) if bg_mean > 100 else (190, 190, 190)
        for door in doors:
            pos = door.get("position_px", [0, 0])
            r = int(door.get("swing_radius_px", 22) * scale_factor)
            cx, cy = int(pos[0] * scale_factor), int(pos[1] * scale_factor)

            # Draw swing arc with thin stroke
            cv2.ellipse(canvas, (cx, cy), (r, r), 0, 0, 90, door_arc_color, 1, cv2.LINE_AA)
            # Draw door leaf radial line
            cv2.line(canvas, (cx, cy), (cx + r, cy), wall_color, 2, cv2.LINE_AA)

        # 6. Render Architectural Text, Labels & Dimensions
        text_annotations = extracted_data.get("text_annotations", [])
        for ann in text_annotations:
            text = ann.get("text", "")
            center = ann.get("center_px", [0, 0])
            cx, cy = int(center[0] * scale_factor), int(center[1] * scale_factor)
            is_dim = ann.get("is_dimension", False)

            font = cv2.FONT_HERSHEY_SIMPLEX
            font_scale = 0.42 * scale_factor
            font_color = (10, 10, 10) if not is_dim else (120, 20, 20)
            thickness_t = 1

            (tw_txt, th_txt), _ = cv2.getTextSize(text, font, font_scale, thickness_t)
            tx = max(4, cx - tw_txt // 2)
            ty = min(th - 4, cy + th_txt // 2)

            cv2.putText(canvas, text, (tx, ty), font, font_scale, font_color, thickness_t, cv2.LINE_AA)

        return canvas

    def render_vector_svg(
        self,
        extracted_data: Dict[str, Any],
        target_size: Optional[Tuple[int, int]] = None
    ) -> str:
        """
        Generates clean, scalable, layered vector SVG representation.
        Organized into layers: <g id="rooms">, <g id="walls">, <g id="windows">, <g id="doors">, <g id="stairs">, <g id="labels">.
        """
        w, h = extracted_data.get("image_size", (800, 1000))
        if target_size is not None:
            w, h = target_size

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {w} {h}" width="{w}" height="{h}" '
            'style="background-color: #ffffff; font-family: -apple-system, BlinkMacSystemFont, \'Segoe UI\', Roboto, sans-serif;">',
            '  <!-- Metadata -->',
            f'  <!-- Generated by AI Floor Plan Extraction & Reconstruction Agent -->',
            f'  <defs>',
            '    <marker id="arrow" viewBox="0 0 10 10" refX="5" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">',
            '      <path d="M 0 0 L 10 5 L 0 10 z" fill="#555" />',
            '    </marker>',
            '  </defs>',
        ]

        # Layer 1: Rooms
        svg_lines.append('  <g id="rooms" fill="#fafafa" stroke="#e0e0e0" stroke-width="0.5">')
        for room in extracted_data.get("rooms", []):
            pts = room.get("polygon_px", [])
            if len(pts) >= 3:
                pts_str = " ".join([f"{p[0]},{p[1]}" for p in pts])
                cat = room.get("assigned_category", "room")
                label = room.get("assigned_label", "Room")
                fill = "#fdfdfd"
                if cat == "bathroom":
                    fill = "#f4f8fb"
                elif cat == "kitchen":
                    fill = "#fef9e7"
                elif cat == "ots":
                    fill = "#f0f4f0"
                svg_lines.append(f'    <polygon points="{pts_str}" fill="{fill}" data-id="{room.get("room_id")}" data-label="{label}" />')
        svg_lines.append('  </g>')

        # Layer 2: Walls
        walls_info = extracted_data.get("walls", {})
        wall_segments = walls_info.get("wall_segments", [])
        wall_contours = walls_info.get("wall_contours", [])
        thickness = max(2.0, walls_info.get("wall_thickness_px", 3.5))

        svg_lines.append(f'  <g id="walls" stroke="#111111" stroke-width="{thickness}" stroke-linecap="round" stroke-linejoin="round" fill="#111111">')
        if wall_segments:
            for seg in wall_segments:
                sp = seg.get("start_px", [0, 0])
                ep = seg.get("end_px", [0, 0])
                w_id = seg.get("wall_id", "")
                w_type = seg.get("type", "interior")
                svg_lines.append(f'    <line x1="{sp[0]}" y1="{sp[1]}" x2="{ep[0]}" y2="{ep[1]}" data-id="{w_id}" data-type="{w_type}" />')
        elif wall_contours:
            for poly in wall_contours:
                if len(poly) >= 2:
                    pts_str = " ".join([f"{p[0]},{p[1]}" for p in poly])
                    svg_lines.append(f'    <polygon points="{pts_str}" />')
        svg_lines.append('  </g>')

        # Layer 3: Windows
        windows = extracted_data.get("windows", [])
        svg_lines.append('  <g id="windows" stroke="#2563eb" stroke-width="2.5" stroke-linecap="round">')
        for win in windows:
            start = win.get("start_px", [0, 0])
            end = win.get("end_px", [0, 0])
            win_id = win.get("window_id", "")
            att_id = win.get("attached_wall_id", "")
            svg_lines.append(f'    <line x1="{start[0]}" y1="{start[1]}" x2="{end[0]}" y2="{end[1]}" data-id="{win_id}" data-wall="{att_id}" />')
        svg_lines.append('  </g>')

        # Layer 4: Doors & Swing Arcs
        svg_lines.append('  <g id="doors" stroke="#444444" stroke-width="1.2" fill="none">')
        for door in extracted_data.get("doors", []):
            pos = door.get("position_px", [0, 0])
            r = door.get("swing_radius_px", 22)
            cx, cy = pos[0], pos[1]
            q = door.get("swing_quadrant", 0)
            d_id = door.get("door_id", "")
            att_id = door.get("attached_wall_id", "")
            if q == 0:
                svg_lines.append(f'    <path d="M {cx} {cy} L {cx + r} {cy} A {r} {r} 0 0 1 {cx} {cy + r}" stroke-dasharray="2,2" data-id="{d_id}" data-wall="{att_id}" />')
                svg_lines.append(f'    <line x1="{cx}" y1="{cy}" x2="{cx + r}" y2="{cy}" stroke="#111" stroke-width="2" />')
            elif q == 1:
                svg_lines.append(f'    <path d="M {cx} {cy} L {cx + r} {cy} A {r} {r} 0 0 0 {cx} {cy - r}" stroke-dasharray="2,2" data-id="{d_id}" data-wall="{att_id}" />')
                svg_lines.append(f'    <line x1="{cx}" y1="{cy}" x2="{cx + r}" y2="{cy}" stroke="#111" stroke-width="2" />')
            elif q == 2:
                svg_lines.append(f'    <path d="M {cx} {cy} L {cx - r} {cy} A {r} {r} 0 0 1 {cx} {cy - r}" stroke-dasharray="2,2" data-id="{d_id}" data-wall="{att_id}" />')
                svg_lines.append(f'    <line x1="{cx}" y1="{cy}" x2="{cx - r}" y2="{cy}" stroke="#111" stroke-width="2" />')
            else:
                svg_lines.append(f'    <path d="M {cx} {cy} L {cx - r} {cy} A {r} {r} 0 0 0 {cx} {cy + r}" stroke-dasharray="2,2" data-id="{d_id}" data-wall="{att_id}" />')
                svg_lines.append(f'    <line x1="{cx}" y1="{cy}" x2="{cx - r}" y2="{cy}" stroke="#111" stroke-width="2" />')
        svg_lines.append('  </g>')

        # Layer 5: Stairs
        svg_lines.append('  <g id="stairs" stroke="#333333" stroke-width="1.0" fill="none">')
        for stair in extracted_data.get("stairs", []):
            bbox = stair.get("bbox_px", [])
            st_id = stair.get("stair_id", "")
            if len(bbox) == 4:
                x1, y1, x2, y2 = bbox
                svg_lines.append(f'    <rect x="{x1}" y="{y1}" width="{x2 - x1}" height="{y2 - y1}" fill="#f8fafc" stroke="#333" data-id="{st_id}" />')
                steps = min(stair.get("approx_steps", 8), 16)
                step_h = max(4, (y2 - y1) // max(1, steps))
                for sy in range(y1 + step_h, y2, step_h):
                    svg_lines.append(f'    <line x1="{x1}" y1="{sy}" x2="{x2}" y2="{sy}" />')
                mid_x = x1 + (x2 - x1) // 2
                svg_lines.append(f'    <line x1="{mid_x}" y1="{y2 - 6}" x2="{mid_x}" y2="{y1 + 10}" stroke="#555" stroke-width="1.5" marker-end="url(#arrow)" />')
        svg_lines.append('  </g>')

        # Layer 6: Labels and Dimensions
        svg_lines.append('  <g id="labels" font-size="11" font-weight="600" text-anchor="middle" fill="#111111">')
        for ann in extracted_data.get("text_annotations", []):
            txt = ann.get("text", "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
            cx, cy = ann.get("center_px", [0, 0])
            is_dim = ann.get("is_dimension", False)
            col = "#8b0000" if is_dim else "#111111"
            fsize = "10" if is_dim else "11"
            fweight = "normal" if is_dim else "600"
            svg_lines.append(f'    <text x="{cx}" y="{cy}" fill="{col}" font-size="{fsize}" font-weight="{fweight}">{txt}</text>')
        svg_lines.append('  </g>')

        svg_lines.append('</svg>')
        return "\n".join(svg_lines)

    def render_overlay(
        self,
        original_bgr: np.ndarray,
        extracted_data: Dict[str, Any],
        alpha: float = 0.55
    ) -> np.ndarray:
        """
        Creates source-preservation overlay showing reconstructed geometry on the original image.
        """
        h, w = original_bgr.shape[:2]
        recon = self.render_faithful_raster(extracted_data, target_size=(w, h))
        overlay = cv2.addWeighted(original_bgr, 1.0 - alpha, recon, alpha, 0)
        return overlay
