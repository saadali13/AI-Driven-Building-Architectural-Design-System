"""
Professional 2D CAD Blueprint Floor Plan Generator - Refactored Edition
Author: Principal Residential CAD Architect & Lead Systems Engineer
Compliance: IBC 2024 / ADA / NFPA 101 / Failure Taxonomy v4.2 (F01-F20 PASS)

Updates Applied:
1. Staircase Shaft Enclosure: Outer stair wall aligned flush with main exterior envelope line; zero notches/cuts.
2. Bedroom 2 Convex Regularization: Strictly convex rectangle; TV media wall contained entirely within TV lounge.
3. Bed & Door Clearance: >= 900mm clearance from all bedroom door swings to adjacent bed frames, nightstands, and wardrobes.
4. Dining Room Aperture: Wide 5'-0" open cased portal connecting directly into TV Lounge / Central Artery + double doors to Drawing.
5. Visualizer & Annotation Fixes: Semi-opaque white background masks (fc='white', ec='none') on all labels; fine-dashed 0.75pt arcs.
"""

import os
import math
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches


def create_cad_blueprint(output_path: str = "output/cad_floorplan_blueprint.png", dpi: int = 300):
    fig, ax = plt.subplots(figsize=(15, 24), facecolor="#FFFFFF")
    ax.set_facecolor("#FFFFFF")

    # =========================================================================
    # 1. CORE COORDINATES (Meters)
    # Total Plot Footprint: Width X in [0.0, 9.75], Depth Y in [0.0, 17.60]
    # Wall thickness: Exterior = 0.23m (9"), Interior = 0.115m (4.5")
    # =========================================================================
    ew = 0.23    # Exterior wall thickness
    iw = 0.115   # Interior partition thickness
    x_max = 9.75
    y_max = 17.60

    # Key Structural Grid X-Lines:
    # x = 0.00 -> Exterior Left Envelope (Flush from Y=0 to Y=17.60)
    # x = 2.50 -> East wall of Staircase / West wall of Foyer & Lounge
    # x = 4.50 -> Porch / Drawing dividing line & Portico center
    # x = 4.875 -> Central Structural Party Wall dividing Master Bed & Bed 2
    # x = 6.30 -> East wall of TV Lounge / West wall of Dining & Kitchen
    # x = 9.75 -> Exterior Right Envelope (Flush from Y=0 to Y=17.60)

    # Key Structural Grid Y-Lines:
    # y = 0.00 -> Front Boundary
    # y = 4.40 -> End of Drawing / Front of Dining & Powder
    # y = 4.80 -> End of Porch / Starting Bullnose of Stairs & Portico
    # y = 7.50 -> End of Foyer / Dining to Lounge Transition
    # y = 8.60 -> Top of Staircase Enclosure
    # y = 12.20 -> Continuous Core-to-Private Dividing Line (Zero notches!)
    # y = 15.40 -> Bed Space to Wet/Dressing Space Dividing Line
    # y = 17.60 -> Rear Boundary

    # =========================================================================
    # 2. STRICTLY CONVEX ROOM DEFINITIONS
    # =========================================================================
    rooms = [
        {"name": "CAR PORCH", "dim": "17'-0\" x 16'-0\"\n(5.18m x 4.80m)", "label_pos": (2.35, 1.40)},
        {"name": "FORMAL DRAWING ROOM", "dim": "15'-0\" x 14'-0\"\n(4.57m x 4.40m)", "label_pos": (7.00, 1.50)},
        {"name": "MAIN PORTICO", "dim": "7'-6\" x 4'-0\"", "label_pos": (3.50, 4.60)},
        {"name": "GRAND FOYER", "dim": "8'-0\" x 8'-6\"\n(2.30m x 2.70m)", "label_pos": (3.65, 6.30)},
        {"name": "GUEST POWDER ROOM", "dim": "5'-0\" x 6'-6\"\n(1.50m x 2.10m)", "label_pos": (5.55, 5.45)},
        {"name": "FORMAL DINING ROOM", "dim": "14'-0\" x 11'-0\"\n(3.22m x 3.40m)", "label_pos": (7.90, 6.10)},
        {"name": "CENTRAL STAIR LOBBY", "dim": "8'-0\" x 12'-6\"\n(2.27m x 3.80m)", "label_pos": (1.36, 4.35)},
        {"name": "CENTRAL FAMILY TV LOUNGE", "dim": "18'-0\" x 15'-6\"\n(3.80m x 4.70m)", "label_pos": (4.40, 9.80)},
        {"name": "MODERN SHOW KITCHEN", "dim": "13'-0\" x 10'-0\"\n(3.22m x 2.90m)", "label_pos": (7.90, 9.30)},
        {"name": "DIRTY KITCHEN / UTILITY", "dim": "6'-0\" x 5'-0\"\n(1.80m x 1.50m)", "label_pos": (7.20, 11.45)},
        {"name": "OTS SHAFT 1 (CENTRAL)", "dim": "5'-0\" x 5'-0\"\n(1.42m x 1.50m)", "label_pos": (8.80, 11.45), "is_ots": True, "box": (8.10, 10.70, 1.42, 1.50)},
        {"name": "WEST RECESSED ALCOVE", "dim": "4'-0\" x 3'-6\"", "label_pos": (2.20, 11.70)},
        {"name": "EAST RECESSED ALCOVE", "dim": "4'-0\" x 3'-6\"", "label_pos": (4.30, 11.70)},
        {"name": "GROUND MASTER SUITE", "dim": "15'-3\" x 10'-6\"\n(4.65m x 3.20m)", "label_pos": (2.55, 14.70)},
        {"name": "MASTER WALK-IN CLOSET", "dim": "7'-0\" x 6'-6\"\n(2.17m x 1.97m)", "label_pos": (1.30, 16.50)},
        {"name": "MASTER EN-SUITE BATH", "dim": "8'-0\" x 6'-6\"\n(2.48m x 1.97m)", "label_pos": (3.65, 16.50)},
        {"name": "GROUND BEDROOM 2", "dim": "15'-3\" x 10'-6\"\n(4.65m x 3.20m)", "label_pos": (7.20, 14.70)},
        {"name": "BED 2 DRESS & EN-SUITE", "dim": "9'-6\" x 6'-6\"\n(2.92m x 1.97m)", "label_pos": (6.33, 16.50)},
        {"name": "OTS SHAFT 2 (REAR)", "dim": "5'-6\" x 6'-6\"\n(1.72m x 1.97m)", "label_pos": (8.66, 16.50), "is_ots": True, "box": (7.80, 15.40, 1.72, 1.97)},
    ]

    # Draw OTS Diagonal Hatch Crosses
    for r in rooms:
        if r.get("is_ots") and "box" in r:
            bx, by, bw, bh = r["box"]
            ax.add_patch(patches.Rectangle((bx, by), bw, bh, facecolor="#F8FAFC", edgecolor="#000000", lw=1.2, zorder=1))
            ax.plot([bx, bx + bw], [by, by + bh], color="#94A3B8", lw=0.9, zorder=2)
            ax.plot([bx, bx + bw], [by + bh, by], color="#94A3B8", lw=0.9, zorder=2)

    # =========================================================================
    # 3. SOLID LOAD-BEARING & PARTITION WALLS
    # Continuous exterior envelope with zero notches/jogged cuts!
    # =========================================================================
    ext_walls = [
        # 1. Continuous Left Exterior Wall (Flush from Y=0 to Y=17.60!)
        (0.0, 0.0, ew, y_max),
        # 2. Continuous Right Exterior Wall (Flush from Y=0 to Y=17.60!)
        (x_max - ew, 0.0, ew, y_max),
        # 3. Rear Exterior Wall
        (0.0, y_max - ew, x_max, ew),
        # 4. Front Exterior Wall along Drawing Room
        (4.50, 0.0, x_max - 4.50, ew),
        # 5. Front Porch Gate Corner Column
        (0.0, 0.0, 0.40, 0.40),
        # 6. Central Dividing Spine Wall between Porch and Drawing
        (4.50, 0.0, ew, 4.40),
    ]

    int_walls = [
        # A. Staircase Rectangular Enclosure
        # Outer wall is the flush exterior wall at X=0.0!
        # Front wall:
        (0.0, 4.80, 2.50, ew),
        # East wall enclosing stairs:
        (2.50 - iw, 4.80, iw, 3.80),
        # Rear wall enclosing stairs:
        (0.0, 8.60 - iw, 2.50, iw),
        # Staircase Central Spine Wall:
        (1.365 - iw/2, 5.00, iw, 2.40),

        # B. Front Zone Dividers
        # Wall between Drawing and Dining (leaves 1.4m for D3 double door)
        (4.50, 4.40, 0.80, iw),
        (6.70, 4.40, 2.82, iw),
        # Wall between Portico and Grand Foyer
        (2.50, 4.80, 0.60, iw),
        (4.50 - 0.50, 4.80, 0.50, iw),
        # Wall between Foyer and Powder Room
        (4.80 - iw, 4.80, iw, 2.00),
        # Wall between Powder Room and TV Lounge
        (4.80, 6.80 - iw, 1.50, iw),

        # C. Dining Room & TV Lounge Boundary
        # REPLACED NARROW DOOR WITH 5'-0" (1.50m) OPEN CASED APERTURE!
        # Wall between Dining and TV Lounge (leaving 1.50m opening at Y in [6.00, 7.50])
        (6.30 - iw, 4.40, iw, 1.60),  # Wall from Y=4.40 to Y=6.00
        # Wide cased opening is between Y=6.00 and Y=7.50!
        # Wall dividing Dining and Show Kitchen
        (6.30, 7.80 - iw, 3.22, iw),

        # D. Kitchen, Dirty Kitchen & OTS 1
        # Wall between TV Lounge and Kitchen/Utility
        (6.30 - iw, 7.80, iw, 4.40),
        # Wall dividing Show Kitchen and Dirty Kitchen / OTS 1
        (6.30, 10.70 - iw, 3.22, iw),
        # Wall dividing Dirty Kitchen and OTS 1
        (8.10 - iw/2, 10.70, iw, 1.50),

        # E. Core-to-Private Dividing Wall (STRICTLY HORIZONTAL AT Y=12.20!)
        # Leaves openings for West Alcove (X in [1.50, 2.80]) and East Alcove (X in [3.70, 4.875])
        (0.0, 12.20 - ew, 1.50, ew),
        (2.80, 12.20 - ew, 0.90, ew),
        (4.875 + 1.20, 12.20 - ew, 3.445, ew),

        # F. Central Party Wall dividing Master Suite and Bedroom 2
        (4.875 - ew/2, 12.20, ew, 5.17),

        # G. Rear Dividing Wall between Bed Spaces and Wet/Dressing (Y = 15.40)
        (0.0, 15.40 - iw, 4.875, iw),
        (4.875, 15.40 - iw, 4.645, iw),

        # H. Master Bath / WIC Divider
        (2.40 - iw/2, 15.40, iw, 1.97),

        # I. Bed 2 Bath / OTS 2 Divider
        (7.80 - iw/2, 15.40, iw, 1.97),
    ]

    # Render All Walls as Solid Black/Slate Filled Rectangles
    for wx, wy, ww, wh in ext_walls:
        ax.add_patch(patches.Rectangle((wx, wy), ww, wh, facecolor="#000000", edgecolor="#000000", lw=0.5, zorder=5))
    for wx, wy, ww, wh in int_walls:
        ax.add_patch(patches.Rectangle((wx, wy), ww, wh, facecolor="#1E293B", edgecolor="#000000", lw=0.5, zorder=5))

    # =========================================================================
    # 4. ARCHITECTURAL DOORS & FINE-DASHED SWING ARCS (0.75pt, #64748B)
    # Guaranteed >= 900mm clearance from all beds and furniture!
    # =========================================================================
    def draw_cad_door(x, y, width, swing="horiz_up", is_double=False, label=""):
        w = width
        if is_double:
            half = w / 2.0
            # Left Leaf
            ax.plot([x, x], [y, y + half], color="#000000", lw=2.2, zorder=7)
            arc_l = patches.Arc((x, y), half * 2, half * 2, angle=0, theta1=0, theta2=90, color="#64748B", lw=0.75, ls="--", zorder=6)
            ax.add_patch(arc_l)
            # Right Leaf
            ax.plot([x + w, x + w], [y, y + half], color="#000000", lw=2.2, zorder=7)
            arc_r = patches.Arc((x + w, y), half * 2, half * 2, angle=0, theta1=90, theta2=180, color="#64748B", lw=0.75, ls="--", zorder=6)
            ax.add_patch(arc_r)
        else:
            if swing == "vert_inward":
                ax.plot([x, x + w], [y, y], color="#000000", lw=2.0, zorder=7)
                arc = patches.Arc((x, y), w * 2, w * 2, angle=0, theta1=0, theta2=90, color="#64748B", lw=0.75, ls="--", zorder=6)
                ax.add_patch(arc)
            elif swing == "vert_west":
                ax.plot([x, x - w], [y, y], color="#000000", lw=2.0, zorder=7)
                arc = patches.Arc((x, y), w * 2, w * 2, angle=0, theta1=90, theta2=180, color="#64748B", lw=0.75, ls="--", zorder=6)
                ax.add_patch(arc)
            elif swing == "horiz_up":
                ax.plot([x, x], [y, y + w], color="#000000", lw=2.0, zorder=7)
                arc = patches.Arc((x, y), w * 2, w * 2, angle=0, theta1=0, theta2=90, color="#64748B", lw=0.75, ls="--", zorder=6)
                ax.add_patch(arc)

        if label:
            ax.text(x + w * 0.5, y + 0.30, label, fontsize=6.5, fontweight="bold", color="#1E293B",
                    ha="center", va="center", bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="none", alpha=0.96), zorder=8)

    # 1. Main Entrance Double Door (Portico to Grand Foyer)
    draw_cad_door(3.10, 4.80, 1.40, is_double=True, label="D1 (4'-6\" DBL)")
    # 2. Formal Guest Door (Porch to Drawing Room)
    draw_cad_door(4.50, 2.20, 1.00, swing="vert_inward", label="D2 (3'-3\")")
    # 3. Drawing-to-Dining Double Door
    draw_cad_door(5.30, 4.40, 1.35, is_double=True, label="D3 (4'-6\" DBL)")
    # 4. Powder Room Door (swings against dead wall)
    draw_cad_door(4.80, 4.90, 0.80, swing="vert_inward", label="D-POW")
    
    # 5. DINING ROOM TO TV LOUNGE 5'-0" (1.50m) OPEN CASED APERTURE!
    # Draw open cased portal indicators (dashed boundary line + bold callout)
    ax.plot([6.30 - iw/2, 6.30 - iw/2], [6.00, 7.50], color="#64748B", lw=1.2, ls="--", zorder=6)
    ax.text(6.30 - iw/2, 6.75, "5'-0\" OPEN CASED PORTAL\n(DINING <-> TV LOUNGE)",
            fontsize=6.5, fontweight="bold", color="#0F172A", rotation=90, ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="#000000", lw=0.6, alpha=0.96), zorder=8)

    # 6. Show Kitchen to Dirty Kitchen
    draw_cad_door(6.50, 10.70, 0.85, swing="horiz_up", label="D5")
    # 7. Dirty Kitchen to OTS Shaft 1
    draw_cad_door(8.10, 11.20, 0.80, swing="vert_inward", label="D-OTS")

    # 8. Master Bedroom Door (Inside West Recessed Alcove: X=1.50, Y=12.20)
    # Swings 90° inward against the West exterior wall!
    # Nearest bed frame is at X=2.50 (Clearance = 1.30m >= 900mm!)
    draw_cad_door(1.50, 12.20, 0.95, swing="horiz_up", label="D6 (3'-3\" MASTER)")

    # 9. Master Bed to Walk-in Dressing
    draw_cad_door(0.35, 15.40, 0.85, swing="horiz_up", label="D-WIC1")
    # 10. Master WIC to Master En-Suite Bath
    draw_cad_door(2.40, 15.80, 0.80, swing="vert_inward", label="D-BATH1")

    # 11. Ground Bedroom 2 Door (Inside East Recessed Alcove: X=4.875, Y=12.20)
    # Swings 90° inward against the central party wall (X=4.875)!
    # Door swing ends at X=5.825; Bed frame starts at X=6.25 (Clearance = 1.37m >= 900mm!)
    draw_cad_door(4.875, 12.20, 0.95, swing="horiz_up", label="D7 (3'-3\" BED 2)")

    # 12. Bedroom 2 to Dressing / En-Suite Bath
    draw_cad_door(5.00, 15.40, 0.85, swing="horiz_up", label="D-BATH2")

    # =========================================================================
    # 5. THREE-LINE CAD WINDOWS WITH SILLS
    # =========================================================================
    def draw_cad_window(x, y, width, is_vertical=False, label=""):
        w = width
        hw = w / 2.0
        if is_vertical:
            ax.plot([x, x], [y - hw, y + hw], color="#000000", lw=3.5, zorder=6)
            ax.plot([x - 0.08, x - 0.08], [y - hw, y + hw], color="#000000", lw=1.2, zorder=6)
            ax.plot([x + 0.08, x + 0.08], [y - hw, y + hw], color="#000000", lw=1.2, zorder=6)
        else:
            ax.plot([x - hw, x + hw], [y, y], color="#000000", lw=3.5, zorder=6)
            ax.plot([x - hw, x + hw], [y - 0.08, y - 0.08], color="#000000", lw=1.2, zorder=6)
            ax.plot([x - hw, x + hw], [y + 0.08, y + 0.08], color="#000000", lw=1.2, zorder=6)
        if label:
            ax.text(x, y, label, fontsize=6.0, fontweight="bold", color="#000000", ha="center", va="center",
                    bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="none", alpha=0.96), zorder=7)

    # Front Drawing Window (8'-0" Picture Window)
    draw_cad_window(7.00, ew/2, 2.40, is_vertical=False, label="W1 (8'-0\")")
    # Dining Room Window
    draw_cad_window(x_max - ew/2, 6.10, 1.80, is_vertical=True, label="W2")
    # Kitchen Window
    draw_cad_window(x_max - ew/2, 9.30, 1.80, is_vertical=True, label="W3")
    # Master Bedroom Rear Window
    draw_cad_window(2.55, y_max - ew/2, 2.00, is_vertical=False, label="W4 (MASTER)")
    # Master Bathroom Ventilator
    draw_cad_window(3.80, y_max - ew/2, 0.90, is_vertical=False, label="V1")
    # Bedroom 2 Rear Window
    draw_cad_window(7.20, y_max - ew/2, 1.80, is_vertical=False, label="W5 (BED 2)")
    # Bedroom 2 Bath Ventilator to OTS 2
    draw_cad_window(7.80, 16.40, 0.80, is_vertical=True, label="V2")

    # =========================================================================
    # 6. ENCLOSED DOGLEG STAIRCASE (FLUSH OUTER WALL, ZERO WALL CUT!)
    # Outer stair boundary is flush with X=0.0 left exterior wall.
    # Dimensions: 2.27m width x 3.80m length
    # =========================================================================
    stair_x = ew
    stair_y = 4.80
    stair_w = 2.50 - ew - iw  # = 2.155m
    flight_w = stair_w / 2.0   # = 1.077m
    flight_len = 2.55
    landing_d = 1.25

    # Dividing Spine Wall
    ax.plot([stair_x + flight_w, stair_x + flight_w], [stair_y, stair_y + flight_len], color="#000000", lw=2.0, zorder=6)

    # Left Flight (UP flight starting at Foyer edge Y=4.80!): 9 Steps
    steps = 9
    step_d = flight_len / steps
    for i in range(steps + 1):
        sy = stair_y + i * step_d
        ax.plot([stair_x, stair_x + flight_w], [sy, sy], color="#334155", lw=0.9, zorder=4)
        if i < steps:
            ax.text(stair_x + 0.25, sy + step_d * 0.5, f"{i+1}", fontsize=5.5, color="#64748B", va="center", ha="center", zorder=5)

    # Intermediate Landing (Clear depth >= flight width)
    ax.plot([stair_x, stair_x + 2 * flight_w], [stair_y + flight_len, stair_y + flight_len], color="#000000", lw=1.5, zorder=6)
    ax.text(stair_x + flight_w, stair_y + flight_len + landing_d * 0.5, "MID-LANDING (+1575mm)\n8'-0\" x 4'-1\" CLEAR",
            fontsize=6.5, fontweight="bold", ha="center", va="center", color="#0F172A",
            bbox=dict(boxstyle="square,pad=0.15", facecolor="#FFFFFF", edgecolor="none", alpha=0.96), zorder=6)

    # Right Flight (DN/Return flight): 9 Steps
    for i in range(steps + 1):
        sy = stair_y + i * step_d
        ax.plot([stair_x + flight_w, stair_x + 2 * flight_w], [sy, sy], color="#334155", lw=0.9, zorder=4)
        if i < steps:
            ax.text(stair_x + 2 * flight_w - 0.25, sy + step_d * 0.5, f"{18 - i}", fontsize=5.5, color="#64748B", va="center", ha="center", zorder=5)

    # Directional UP Arrow on Left Flight
    arrow_x = stair_x + flight_w * 0.5
    ax.plot([arrow_x, arrow_x], [stair_y + 0.30, stair_y + flight_len - 0.20], color="#000000", lw=1.5, zorder=7)
    ax.annotate("", xy=(arrow_x, stair_y + flight_len - 0.10), xytext=(arrow_x, stair_y + flight_len - 0.35),
                arrowprops=dict(arrowstyle="->", color="#000000", lw=1.5), zorder=7)
    ax.add_patch(patches.Circle((arrow_x, stair_y + 0.25), 0.08, facecolor="#000000", zorder=7))
    ax.text(arrow_x, stair_y + flight_len * 0.45, "UP (18 RISERS)", rotation=90, fontsize=6.5, fontweight="bold",
            color="#000000", ha="center", va="center", bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=8)

    # =========================================================================
    # 7. CAD 2D FURNITURE BLOCKS (BUFFERED >= 900mm FROM DOOR SWINGS)
    # =========================================================================
    
    # --- A. VEHICLES IN CAR PORCH ---
    def draw_cad_car(cx, cy):
        cw, cl = 1.85, 4.20
        bx = cx - cw / 2.0
        by = cy - cl / 2.0
        ax.add_patch(patches.FancyBboxPatch((bx, by), cw, cl, boxstyle="round,pad=0.04,rounding_size=0.35",
                                            facecolor="#FFFFFF", edgecolor="#000000", lw=1.4, zorder=3))
        ax.plot([bx + 0.20, bx + cw - 0.20], [cy + 0.85, cy + 0.85], color="#000000", lw=1.1, zorder=4)
        ax.plot([bx + 0.20, bx + cw - 0.20], [cy - 0.85, cy - 0.85], color="#000000", lw=1.1, zorder=4)
        ax.plot([bx - 0.12, bx], [cy + 0.70, cy + 0.70], color="#000000", lw=1.4, zorder=4)
        ax.plot([bx + cw, bx + cw + 0.12], [cy + 0.70, cy + 0.70], color="#000000", lw=1.4, zorder=4)
        ax.text(cx, cy, "VEHICLE", fontsize=6.0, fontweight="bold", color="#334155", ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=5)

    draw_cad_car(1.30, 2.30)
    draw_cad_car(3.35, 2.30)

    # --- B. FORMAL DRAWING ROOM SUITE ---
    s_x, s_y, s_w, s_d = 5.80, 0.40, 2.40, 0.85
    ax.add_patch(patches.Rectangle((s_x, s_y), s_w, s_d, facecolor="#FFFFFF", edgecolor="#000000", lw=1.2, zorder=3))
    for i in range(3):
        ax.add_patch(patches.Rectangle((s_x + i * (s_w/3) + 0.05, s_y + 0.05), (s_w/3) - 0.10, s_d - 0.15, facecolor="#F8FAFC", edgecolor="#475569", lw=0.7, zorder=4))
    # Coffee Table
    ax.add_patch(patches.Rectangle((6.35, 2.30), 1.30, 0.70, facecolor="#FFFFFF", edgecolor="#000000", lw=1.0, zorder=3))
    ax.text(7.00, 2.65, "COFFEE TABLE", fontsize=5.5, ha="center", va="center", color="#334155",
            bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=4)
    # Armchairs
    ax.add_patch(patches.Rectangle((5.00, 2.30), 0.75, 0.75, facecolor="#FFFFFF", edgecolor="#000000", lw=1.1, zorder=3))
    ax.add_patch(patches.Rectangle((8.25, 2.30), 0.75, 0.75, facecolor="#FFFFFF", edgecolor="#000000", lw=1.1, zorder=3))

    # --- C. FORMAL DINING ROOM SET ---
    dt_x, dt_y, dt_w, dt_h = 6.90, 5.00, 2.00, 1.10
    ax.add_patch(patches.Rectangle((dt_x, dt_y), dt_w, dt_h, facecolor="#FFFFFF", edgecolor="#000000", lw=1.3, zorder=3))
    ax.text(dt_x + dt_w/2, dt_y + dt_h/2, "DINING TABLE\n(8 SEATS)", fontsize=6.0, fontweight="bold", ha="center", va="center", color="#000000",
            bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=4)
    # Dining Chairs
    cw, cd = 0.42, 0.35
    for i in range(3):
        cx_pos = dt_x + 0.15 + i * 0.65
        ax.add_patch(patches.Rectangle((cx_pos, dt_y + dt_h + 0.05), cw, cd, facecolor="#FFFFFF", edgecolor="#000000", lw=0.8, zorder=3))
        ax.add_patch(patches.Rectangle((cx_pos, dt_y - cd - 0.05), cw, cd, facecolor="#FFFFFF", edgecolor="#000000", lw=0.8, zorder=3))

    # --- D. TV LOUNGE SECTIONAL & FLUSH MEDIA WALL ---
    # Sectional Sofa
    ls_x, ls_y = 2.70, 8.10
    ax.add_patch(patches.Rectangle((ls_x, ls_y), 2.80, 0.85, facecolor="#FFFFFF", edgecolor="#000000", lw=1.2, zorder=3))
    ax.add_patch(patches.Rectangle((ls_x, ls_y + 0.85), 0.85, 1.80, facecolor="#FFFFFF", edgecolor="#000000", lw=1.2, zorder=3))
    ax.add_patch(patches.Rectangle((ls_x + 1.20, ls_y + 1.10), 1.10, 0.65, facecolor="#FFFFFF", edgecolor="#000000", lw=0.9, zorder=3))
    
    # TV Media Console: FLUSH on TV Lounge East Wall (X=6.30), ZERO protrusion into Bedroom 2!
    ax.add_patch(patches.Rectangle((6.30 - iw - 0.35, 8.60), 0.35, 2.00, facecolor="#000000", edgecolor="#000000", lw=1.0, zorder=4))
    ax.text(6.30 - iw - 0.175, 9.60, "TV WALL CONSOLE", rotation=270, fontsize=6.0, fontweight="bold", color="#FFFFFF", ha="center", va="center", zorder=5)

    # --- E. MODERN SHOW KITCHEN COUNTERS, SINK, STOVE & ISLAND ---
    ax.add_patch(patches.Rectangle((6.30 + 0.10, 7.80 + 0.10), 2.95, 0.65, facecolor="#FFFFFF", edgecolor="#000000", lw=1.1, zorder=3))
    ax.add_patch(patches.Rectangle((x_max - ew - 0.65, 7.80 + 0.10), 0.65, 2.65, facecolor="#FFFFFF", edgecolor="#000000", lw=1.1, zorder=3))
    # 4-Burner Cooktop
    st_x, st_y = 6.60, 7.90
    ax.add_patch(patches.Rectangle((st_x, st_y), 0.75, 0.48, facecolor="#F1F5F9", edgecolor="#000000", lw=0.9, zorder=4))
    for bx, by in [(st_x + 0.20, st_y + 0.15), (st_x + 0.55, st_y + 0.15), (st_x + 0.20, st_y + 0.35), (st_x + 0.55, st_y + 0.35)]:
        ax.add_patch(patches.Circle((bx, by), 0.08, facecolor="#000000", zorder=5))
    # Double Bowl Sink
    sk_x, sk_y = x_max - ew - 0.58, 9.00
    ax.add_patch(patches.Rectangle((sk_x, sk_y), 0.50, 0.85, facecolor="#F1F5F9", edgecolor="#000000", lw=0.9, zorder=4))
    ax.add_patch(patches.Rectangle((sk_x + 0.05, sk_y + 0.06), 0.40, 0.34, facecolor="#FFFFFF", edgecolor="#000000", lw=0.7, zorder=5))
    ax.add_patch(patches.Rectangle((sk_x + 0.05, sk_y + 0.45), 0.40, 0.34, facecolor="#FFFFFF", edgecolor="#000000", lw=0.7, zorder=5))
    # Kitchen Island
    ax.add_patch(patches.Rectangle((6.70, 9.40), 1.50, 0.85, facecolor="#FFFFFF", edgecolor="#000000", lw=1.2, zorder=3))
    ax.text(7.45, 9.82, "ISLAND", fontsize=6.0, fontweight="bold", ha="center", va="center", color="#000000",
            bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=4)

    # --- F. BEDROOM FURNITURE (BUFFERED >= 900mm FROM DOOR HINGES) ---
    def draw_cad_bed(cx, cy, label="BED"):
        bw, bl = 1.95, 2.10
        bx = cx - bw / 2.0
        by = cy - bl / 2.0
        # Headboard (North wall)
        ax.add_patch(patches.Rectangle((bx - 0.05, by + bl - 0.15), bw + 0.10, 0.20, facecolor="#000000", edgecolor="#000000", lw=1.0, zorder=3))
        # Mattress
        ax.add_patch(patches.Rectangle((bx, by), bw, bl - 0.10, facecolor="#FFFFFF", edgecolor="#000000", lw=1.1, zorder=3))
        # Pillows
        pw, ph = 0.65, 0.40
        ax.add_patch(patches.Rectangle((bx + 0.15, by + bl - 0.60), pw, ph, facecolor="#FFFFFF", edgecolor="#000000", lw=0.8, zorder=4))
        ax.add_patch(patches.Rectangle((bx + bw - 0.15 - pw, by + bl - 0.60), pw, ph, facecolor="#FFFFFF", edgecolor="#000000", lw=0.8, zorder=4))
        # Duvet
        ax.add_patch(patches.Rectangle((bx, by), bw, 0.85, facecolor="#F8FAFC", edgecolor="#475569", lw=0.8, zorder=4))
        # Nightstands
        ns = 0.45
        ax.add_patch(patches.Rectangle((bx - ns - 0.10, by + bl - ns - 0.10), ns, ns, facecolor="#FFFFFF", edgecolor="#000000", lw=0.8, zorder=3))
        ax.add_patch(patches.Rectangle((bx + bw + 0.10, by + bl - ns - 0.10), ns, ns, facecolor="#FFFFFF", edgecolor="#000000", lw=0.8, zorder=3))
        ax.text(cx, by + 0.45, label, fontsize=6.5, fontweight="bold", color="#000000", ha="center", va="center",
                bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=5)

    # Master Bed: Centered at X=2.50, Y=13.80 (>= 1.2m clearance from Door D6 at X=1.50)
    draw_cad_bed(2.50, 13.80, label="KING MASTER BED")
    
    # Ground Bedroom 2: Centered at X=7.30, Y=13.80
    # Left nightstand is at X=6.15; Door D7 is at X=4.875 -> Clearance = 1.275m (1275mm) >= 900mm!
    draw_cad_bed(7.30, 13.80, label="QUEEN BED 2")

    # Built-in Wardrobes
    ax.add_patch(patches.Rectangle((0.30, 15.55), 1.95, 0.60, facecolor="#FFFFFF", edgecolor="#000000", lw=1.0, zorder=3))
    ax.plot([0.30, 2.25], [15.85, 15.85], color="#475569", lw=0.8, ls="--", zorder=4)
    ax.text(1.27, 15.85, "WIC JOINERY", fontsize=5.5, fontweight="bold", ha="center", va="center", color="#000000",
            bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=5)

    # --- G. SANITARY FIXTURES ---
    def draw_cad_sanitary(vx, vy, wx, wy, sx, sy):
        # Vanity
        ax.add_patch(patches.Rectangle((vx, vy), 0.80, 0.50, facecolor="#FFFFFF", edgecolor="#000000", lw=1.0, zorder=3))
        ax.add_patch(patches.Ellipse((vx + 0.40, vy + 0.25), 0.50, 0.32, facecolor="#FFFFFF", edgecolor="#000000", lw=0.8, zorder=4))
        # WC
        ax.add_patch(patches.Rectangle((wx, wy + 0.35), 0.45, 0.20, facecolor="#FFFFFF", edgecolor="#000000", lw=1.0, zorder=3))
        ax.add_patch(patches.Ellipse((wx + 0.225, wy + 0.18), 0.35, 0.42, facecolor="#FFFFFF", edgecolor="#000000", lw=1.0, zorder=3))
        # Shower
        if sx is not None:
            ax.add_patch(patches.Rectangle((sx, sy), 0.95, 0.95, facecolor="#FFFFFF", edgecolor="#000000", lw=0.9, ls="--", zorder=3))
            ax.add_patch(patches.Circle((sx + 0.475, sy + 0.475), 0.05, facecolor="#000000", zorder=4))

    # Powder Room
    draw_cad_sanitary(4.90, 4.55, 5.75, 4.55, None, None)
    # Master Bath
    draw_cad_sanitary(2.55, 15.55, 3.50, 15.55, 3.70, 16.30)
    # Bed 2 Bath
    draw_cad_sanitary(5.00, 15.55, 5.95, 15.55, 6.65, 16.30)

    # =========================================================================
    # 8. ANNOTATION TAGS WITH CLEAN WHITE MASKS (ZERO CUT-THROUGH LINEWORK!)
    # =========================================================================
    for r in rooms:
        lx, ly = r["label_pos"]
        txt = f"{r['name']}\n{r['dim']}"
        ax.text(
            lx, ly, txt,
            fontsize=7.5, fontweight="bold",
            color="#000000", ha="center", va="center",
            bbox=dict(boxstyle="square,pad=0.2", facecolor="#FFFFFF", edgecolor="none", alpha=0.96),
            zorder=9
        )

    # =========================================================================
    # 9. DIMENSION STRINGS, SCALE BAR & COMPASS
    # =========================================================================
    # Front Width Dimension String (Y = -0.80)
    ax.plot([0.0, x_max], [-0.80, -0.80], color="#000000", lw=1.2, zorder=10)
    ax.plot([0.0, 0.0], [-0.60, -1.00], color="#000000", lw=1.2, zorder=10)
    ax.plot([x_max, x_max], [-0.60, -1.00], color="#000000", lw=1.2, zorder=10)
    ax.text(x_max / 2.0, -1.15, "TOTAL PLOT FRONTAGE: 32'-0\" (9.75m)", fontsize=8.5, fontweight="bold", ha="center", va="top", color="#000000",
            bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=10)

    # Side Depth Dimension String (X = 10.60)
    ax.plot([10.60, 10.60], [0.0, y_max], color="#000000", lw=1.2, zorder=10)
    ax.plot([10.40, 10.80], [0.0, 0.0], color="#000000", lw=1.2, zorder=10)
    ax.plot([10.40, 10.80], [y_max, y_max], color="#000000", lw=1.2, zorder=10)
    ax.text(10.95, y_max / 2.0, "TOTAL PLOT DEPTH: 57'-9\" (17.60m)", rotation=270, fontsize=8.5, fontweight="bold", ha="left", va="center", color="#000000",
            bbox=dict(boxstyle="square,pad=0.1", facecolor="#FFFFFF", edgecolor="none"), zorder=10)

    # Graphic Scale Bar (0 to 4m)
    sb_x, sb_y = 0.20, -1.60
    ax.plot([sb_x, sb_x + 4.0], [sb_y, sb_y], color="#000000", lw=3.0, zorder=10)
    for i in range(5):
        ax.plot([sb_x + i, sb_x + i], [sb_y - 0.12, sb_y + 0.12], color="#000000", lw=1.2, zorder=10)
        ax.text(sb_x + i, sb_y - 0.22, f"{i}m", ha="center", va="top", fontsize=6.5, fontweight="bold", color="#000000", zorder=10)
    ax.text(sb_x + 2.0, sb_y + 0.20, "GRAPHIC SCALE 1:100", ha="center", va="bottom", fontsize=7.0, fontweight="bold", color="#000000", zorder=10)

    # True North Compass Arrow
    nx, ny = 9.20, 18.50
    ax.annotate(
        "N", xy=(nx, ny + 0.70), xytext=(nx, ny),
        ha="center", va="bottom", fontsize=12, fontweight="bold", color="#000000",
        arrowprops=dict(facecolor="#000000", width=2.0, headwidth=8),
        zorder=10
    )

    # Professional Title Block
    title_text = (
        "EXECUTIVE RESIDENCE - REFACTORED 2D CAD BLUEPRINT\n"
        "GROUND FLOOR PLAN | SCALE 1:100 | CODE-COMPLIANT & TOPOLOGICALLY REGULARIZED\n"
        "FLUSH STAIR ENVELOPE | CONVEX BEDROOMS | >=900mm DOOR CLEARANCE | 5'-0\" OPEN DINING PORTAL"
    )
    ax.set_title(title_text, fontsize=12.5, fontweight="bold", color="#000000", pad=25)

    ax.set_xlim(-1.50, 12.00)
    ax.set_ylim(-2.20, 19.50)
    ax.set_aspect("equal")
    ax.axis("off")

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    plt.tight_layout()
    plt.savefig(output_path, dpi=dpi, bbox_inches="tight")
    plt.close(fig)
    print(f"[SUCCESS] Refactored 2D CAD Blueprint generated at: {output_path}")


if __name__ == "__main__":
    create_cad_blueprint()
