r"""
Master Architectural Prompt Engine for Complex Multi-Storey Residential Designs.
Implements:
Prompt 1: 10 Marla (35'x65') 3-Storey House with 8 Bedrooms (all en-suite), Powder Room,
          Living Room, Drawing Room, U-shape Stairs, Modern Open Kitchen, Rooftop.
Prompt 2: 1 Kanal (50'x90') 3-Storey House with 12 Bedrooms (all en-suite), Powder Room,
          Living Room, Drawing Room, U-shape Stairs, Modern Kitchen, Lawn, Rooftop.
Styles: Modern, Spanish, Contemporary.
Daylight Sky & Realistic PBR Textures (NO black background).
"""

import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon as MplPoly

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_OUTPUT = os.path.join(PROJECT_ROOT, "output", "advanced_testing_prompts_10m_and_1k")
os.makedirs(BASE_OUTPUT, exist_ok=True)

# ---------------------------------------------------------------------------
# COLOR & TEXTURE PALETTES FOR REALISTIC DAYLIGHT ARCHITECTURAL DRAWINGS
# ---------------------------------------------------------------------------
PALETTES = {
    "modern": {
        "sky_top": "#7DD3FC",
        "sky_mid": "#BAE6FD",
        "sky_bottom": "#F0F9FF",
        "wall_primary": "#F1F5F9",
        "wall_accent": "#CBD5E1",
        "stone_cladding": "#D6D3D1", # Travertine
        "stone_joint": "#A8A29E",
        "wood_louver": "#B45309", # Teak
        "wood_louver_edge": "#78350F",
        "glass_face": "#38BDF8",
        "glass_glare": "#FFFFFF",
        "trim": "#0F172A",
        "parapet": "#E2E8F0",
        "lawn": "#22C55E",
        "pavers": "#94A3B8"
    },
    "spanish": {
        "sky_top": "#60A5FA",
        "sky_mid": "#BFDBFE",
        "sky_bottom": "#EFF6FF",
        "wall_primary": "#FEF3C7", # Warm Stucco
        "wall_accent": "#FDE68A",
        "stone_cladding": "#FCD34D", # Antique Limestone
        "stone_joint": "#D97706",
        "wood_louver": "#92400E", # Dark Walnut
        "wood_louver_edge": "#451A03",
        "roof_tile": "#C2410C", # Terracotta Clay
        "roof_tile_shadow": "#9A3412",
        "glass_face": "#67E8F9",
        "glass_glare": "#FFFFFF",
        "trim": "#451A03",
        "parapet": "#FDE68A",
        "lawn": "#16A34A",
        "pavers": "#A8A29E"
    },
    "contemporary": {
        "sky_top": "#93C5FD",
        "sky_mid": "#DBEAFE",
        "sky_bottom": "#F8FAFC",
        "wall_primary": "#E2E8F0", # Fair-face concrete
        "wall_accent": "#334155", # Charcoal
        "stone_cladding": "#64748B", # Slate
        "stone_joint": "#1E293B",
        "wood_louver": "#D97706", # Natural Oak
        "wood_louver_edge": "#B45309",
        "glass_face": "#0EA5E9",
        "glass_glare": "#FFFFFF",
        "trim": "#0F172A",
        "parapet": "#CBD5E1",
        "lawn": "#4ADE80",
        "pavers": "#64748B"
    }
}


def draw_daylight_sky_and_ground(ax, x_min, x_max, y_min, y_max, ground_y, pal):
    """Draws a photorealistic daylight sky gradient and landscaped ground."""
    # Sky vertical gradient
    y_steps = 40
    y_vals = np.linspace(ground_y, y_max, y_steps)
    for i in range(len(y_vals) - 1):
        t = i / float(y_steps)
        # Interpolate sky color
        if t < 0.5:
            t_sub = t * 2.0
            r = int(240 * (1 - t_sub) + 186 * t_sub)
            g = int(249 * (1 - t_sub) + 230 * t_sub)
            b = int(255 * (1 - t_sub) + 253 * t_sub)
        else:
            t_sub = (t - 0.5) * 2.0
            r = int(186 * (1 - t_sub) + 125 * t_sub)
            g = int(230 * (1 - t_sub) + 211 * t_sub)
            b = int(253 * (1 - t_sub) + 252 * t_sub)
        hex_c = f"#{r:02x}{g:02x}{b:02x}"
        ax.fill_between([x_min, x_max], [y_vals[i], y_vals[i]], [y_vals[i+1], y_vals[i+1]], color=hex_c, zorder=1)

    # Soft ambient sun glow (top right)
    sun_x = x_max - 2.5
    sun_y = y_max - 1.5
    for rad, alpha in [(2.2, 0.08), (1.5, 0.15), (0.8, 0.35), (0.4, 0.8)]:
        ax.add_patch(patches.Circle((sun_x, sun_y), rad, facecolor="#FEF08A", alpha=alpha, edgecolor="none", zorder=2))

    # Ground Plane: Asphalt street, curb, and manicured green lawn
    ax.fill_between([x_min, x_max], [y_min, y_min], [ground_y, ground_y], color="#475569", zorder=2) # Road
    ax.fill_between([x_min, x_max], [ground_y - 0.25, ground_y - 0.25], [ground_y, ground_y], color=pal["lawn"], zorder=3) # Grass lawn
    # Road curb curbstone
    ax.plot([x_min, x_max], [ground_y - 0.25, ground_y - 0.25], color="#CBD5E1", lw=2.5, zorder=4)


# ---------------------------------------------------------------------------
# PROMPT 1: 10 MARLA (35'x65') 3-FLOOR 8-BEDROOM RESIDENCE
# ---------------------------------------------------------------------------
def generate_prompt1_floorplans(output_dir):
    """
    Renders 3 Coordinated Floor Plans for Prompt 1:
    - Ground Floor (2 Beds en-suite, Drawing, Powder, TV Lounge, Open Kitchen, U-Stairs, Porch)
    - First Floor (4 Beds en-suite, Family Living, Kitchenette, Terrace, U-Stairs)
    - Rooftop Floor (2 Beds en-suite, Stair Mumty, Water Tank, BBQ Sky Terrace)
    Total = 8 Bedrooms with 8 attached bathrooms!
    """
    pw = 35.0
    pl = 65.0

    fig, axes = plt.subplots(1, 3, figsize=(22, 11), dpi=200)
    fig.patch.set_facecolor("#FFFFFF") # Professional bright architectural white paper theme

    porch_w = 15.5
    dr_w = 19.5
    porch_l = 18.0
    dr_l = 15.0

    # ------------------ 1. GROUND FLOOR (2 BEDS) ------------------
    ax1 = axes[0]
    ax1.set_facecolor("#F8FAFC")
    ax1.set_xlim(-3, pw + 3)
    ax1.set_ylim(-5, pl + 7)
    ax1.axis("off")
    ax1.set_title("LEVEL 1: GROUND FLOOR PLAN\n2 Bed Suites • Drawing • Powder • Open Kitchen • U-Stairs", 
                  fontsize=10, fontweight="bold", color="#0F172A", pad=12)

    # Plot Boundary
    ax1.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.0))

    # Car Porch (Front Left)
    ax1.add_patch(patches.Rectangle((0, 0), porch_w, porch_l, facecolor="#F1F5F9", edgecolor="#0F172A", lw=1.5))
    ax1.text(porch_w * 0.5, porch_l * 0.5, "DOUBLE CAR PORCH\n15.5' x 18.0'\n(Paved Driveway)", 
             color="#0284C7", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Front Lawn
    ax1.add_patch(patches.Rectangle((porch_w, 0), dr_w, 4.0, facecolor="#DCFCE7", edgecolor="#16A34A", lw=1.0))
    ax1.text(porch_w + dr_w * 0.5, 2.0, "FRONT LAWN / PATIO (19.5' x 4')", color="#15803D", fontsize=7, fontweight="bold", ha="center", va="center")

    # Drawing Room (Front Right)
    ax1.add_patch(patches.Rectangle((porch_w, 4.0), dr_w, dr_l, facecolor="#FFFBEB", edgecolor="#0F172A", lw=1.5))
    ax1.text(porch_w + dr_w * 0.5, 4.0 + dr_l * 0.5, "FORMAL DRAWING ROOM\n19.5' x 15.0'", color="#B45309", fontsize=8, fontweight="bold", ha="center", va="center")
    # Powder Room
    ax1.add_patch(patches.Rectangle((porch_w + dr_w - 6.0, 4.0), 6.0, 5.0, facecolor="#F0FDFA", edgecolor="#0D9488", lw=1.2))
    ax1.text(porch_w + dr_w - 3.0, 6.5, "POWDER\n6' x 5'", color="#0F766E", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Main Entrance Foyer
    foyer_y = porch_l
    ax1.add_patch(patches.Rectangle((0, foyer_y), 8.0, 5.0, facecolor="#EFF6FF", edgecolor="#2563EB", lw=1.0))
    ax1.text(4.0, foyer_y + 2.5, "MAIN FOYER", color="#1D4ED8", fontsize=7, fontweight="bold", ha="center", va="center")

    # Open Modern Kitchen
    kit_y = 19.0
    kit_w = 14.0
    kit_l = 12.0
    ax1.add_patch(patches.Rectangle((pw - kit_w, kit_y), kit_w, kit_l, facecolor="#FEF2F2", edgecolor="#DC2626", lw=1.2))
    # Kitchen Island
    ax1.add_patch(patches.Rectangle((pw - kit_w + 3.0, kit_y + 4.0), 8.0, 3.5, facecolor="#FECACA", edgecolor="#EF4444", lw=1.0))
    ax1.text(pw - kit_w * 0.5, kit_y + 2.0, "MODERN OPEN KITCHEN (14' x 12')\nwith Island Counter", color="#B91C1C", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # U-Shaped Staircase Lobby (Central)
    stair_x = 0.0
    stair_y = 23.0
    stair_w = 10.0
    stair_l = 15.0
    ax1.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.5))
    # U-shape stair treads
    for s_step in np.arange(stair_y + 1, stair_y + 13, 1.4):
        ax1.plot([stair_x + 1, stair_x + 4.5], [s_step, s_step], color="#A855F7", lw=1.0)
        ax1.plot([stair_x + 5.5, stair_x + 9], [s_step, s_step], color="#A855F7", lw=1.0)
    ax1.plot([stair_x + 1, stair_x + 9], [stair_y + 14, stair_y + 14], color="#9333EA", lw=1.5) # Landing
    ax1.text(stair_x + stair_w * 0.5, stair_y + 7.0, "U-SHAPED\nSTAIRS\n(10'x15')", color="#7E22CE", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Central Family TV Lounge
    lounge_x = stair_w
    lounge_w = pw - stair_w - kit_w
    ax1.add_patch(patches.Rectangle((lounge_x, kit_y), pw - stair_w, 19.0, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.0))
    ax1.text(lounge_x + 6.0, kit_y + 10.0, "FAMILY TV LOUNGE\n(18' x 19')", color="#0F172A", fontsize=8.5, fontweight="bold", ha="center", va="center")

    # Ground Floor Rear Bedrooms (Bed 1 & Bed 2, Both with Attached Baths)
    rear_y = 42.0
    rear_l = pl - rear_y
    bed1_w = 18.0
    bed2_w = pw - bed1_w

    # Bed 1 Suite (Left)
    ax1.add_patch(patches.Rectangle((0, rear_y), bed1_w, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax1.text(bed1_w * 0.5, rear_y + rear_l * 0.6, "BEDROOM 1 (MASTER)\n18' x 16'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    # Attached Bath 1
    ax1.add_patch(patches.Rectangle((0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax1.text(4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 1\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Bed 2 Suite (Right)
    ax1.add_patch(patches.Rectangle((bed1_w, rear_y), bed2_w, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax1.text(bed1_w + bed2_w * 0.5, rear_y + rear_l * 0.6, "BEDROOM 2\n17' x 16'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    # Attached Bath 2
    ax1.add_patch(patches.Rectangle((pw - 9.0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax1.text(pw - 4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 2\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center", va="center")


    # ------------------ 2. FIRST FLOOR (4 BEDS) ------------------
    ax2 = axes[1]
    ax2.set_facecolor("#F8FAFC")
    ax2.set_xlim(-3, pw + 3)
    ax2.set_ylim(-5, pl + 7)
    ax2.axis("off")
    ax2.set_title("LEVEL 2: FIRST FLOOR PLAN\n4 Bed Suites (All En-suite) • Lounge • Terrace • U-Stairs", 
                  fontsize=10, fontweight="bold", color="#0F172A", pad=12)
    ax2.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.0))

    # Front Terrace over Porch
    ax2.add_patch(patches.Rectangle((0, 0), 16.0, 10.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.2))
    ax2.text(8.0, 5.0, "FRONT SKY TERRACE\n16' x 10' (Glass Railing)", color="#0369A1", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Bed 3 Suite (Front Left over porch)
    ax2.add_patch(patches.Rectangle((0, 10.0), 16.0, 14.0, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(8.0, 18.0, "BEDROOM 3\n16' x 14'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax2.add_patch(patches.Rectangle((0, 10.0), 7.0, 6.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(3.5, 13.0, "BATH 3\n7' x 6'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Bed 4 Suite (Front Right over drawing room)
    ax2.add_patch(patches.Rectangle((16.0, 0), 19.0, 20.0, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(25.5, 12.0, "BEDROOM 4 (MASTER 2)\n19' x 14'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax2.add_patch(patches.Rectangle((pw - 8.0, 0), 8.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(pw - 4.0, 3.5, "BATH 4\n8' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # U-Stairs (Continued)
    ax2.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.5))
    for s_step in np.arange(stair_y + 1, stair_y + 13, 1.4):
        ax2.plot([stair_x + 1, stair_x + 4.5], [s_step, s_step], color="#A855F7", lw=1.0)
        ax2.plot([stair_x + 5.5, stair_x + 9], [s_step, s_step], color="#A855F7", lw=1.0)
    ax2.text(stair_x + stair_w * 0.5, stair_y + 7.0, "U-SHAPED\nSTAIRS", color="#7E22CE", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # First Floor Family Living
    ax2.add_patch(patches.Rectangle((stair_w, 20.0), pw - stair_w, 18.0, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.0))
    ax2.text(stair_w + 10.0, 29.0, "FIRST FLOOR FAMILY LOUNGE\n& PANTRY (25' x 18')", color="#0F172A", fontsize=8, fontweight="bold", ha="center", va="center")

    # Bed 5 Suite (Rear Left)
    ax2.add_patch(patches.Rectangle((0, rear_y), bed1_w, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(bed1_w * 0.5, rear_y + rear_l * 0.6, "BEDROOM 5\n18' x 16'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax2.add_patch(patches.Rectangle((0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(4.5, rear_y + rear_l - 3.5, "BATH 5\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Bed 6 Suite (Rear Right)
    ax2.add_patch(patches.Rectangle((bed1_w, rear_y), bed2_w, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(bed1_w + bed2_w * 0.5, rear_y + rear_l * 0.6, "BEDROOM 6\n17' x 16'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax2.add_patch(patches.Rectangle((pw - 9.0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(pw - 4.5, rear_y + rear_l - 3.5, "BATH 6\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center", va="center")


    # ------------------ 3. ROOFTOP FLOOR (2 BEDS) ------------------
    ax3 = axes[2]
    ax3.set_facecolor("#F8FAFC")
    ax3.set_xlim(-3, pw + 3)
    ax3.set_ylim(-5, pl + 7)
    ax3.axis("off")
    ax3.set_title("LEVEL 3: ROOFTOP PENTHOUSE PLAN\n2 Bed Suites (Both En-suite) • Mumty • Sky Deck Terrace", 
                  fontsize=10, fontweight="bold", color="#0F172A", pad=12)
    ax3.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.0))

    # Large Open Sky Roof Deck & BBQ Terrace
    ax3.add_patch(patches.Rectangle((0, 0), pw, 38.0, facecolor="#FEF3C7", edgecolor="#F59E0B", lw=1.5))
    ax3.text(pw * 0.5, 18.0, "EXPANSIVE ROOFTOP SKY TERRACE & BBQ DECK\n35' x 38' (Terracotta Pavers & Pergola Seating)", 
             color="#B45309", fontsize=9, fontweight="bold", ha="center", va="center")

    # Staircase Mumty Lobby (Rooftop Landing)
    ax3.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.5))
    ax3.text(stair_x + stair_w * 0.5, stair_y + 7.0, "STAIR MUMTY\nHEADROOM", color="#7E22CE", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Bed 7 Suite (Rooftop Left)
    ax3.add_patch(patches.Rectangle((0, rear_y), bed1_w, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax3.text(bed1_w * 0.5, rear_y + rear_l * 0.6, "BEDROOM 7 (PENTHOUSE)\n18' x 16'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax3.add_patch(patches.Rectangle((0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax3.text(4.5, rear_y + rear_l - 3.5, "BATH 7\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Bed 8 Suite (Rooftop Right)
    ax3.add_patch(patches.Rectangle((bed1_w, rear_y), bed2_w, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax3.text(bed1_w + bed2_w * 0.5, rear_y + rear_l * 0.6, "BEDROOM 8 (SERVANT/GUEST)\n17' x 16'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax3.add_patch(patches.Rectangle((pw - 9.0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax3.text(pw - 4.5, rear_y + rear_l - 3.5, "BATH 8\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Overhead Water Tank Enclosure
    ax3.add_patch(patches.Rectangle((stair_x, stair_y + stair_l), stair_w, 4.0, facecolor="#E2E8F0", edgecolor="#64748B", lw=1.0))
    ax3.text(stair_x + stair_w * 0.5, stair_y + stair_l + 2.0, "O.H. WATER TANK", color="#475569", fontsize=6.5, fontweight="bold", ha="center", va="center")

    plan_path = os.path.join(output_dir, "prompt1_10marla_8bed_3floor_complete_blueprints.png")
    fig.savefig(plan_path, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"[SUCCESS] Generated Prompt 1 Floorplans -> {plan_path}")
    return plan_path


def draw_daylight_front_elevation_3story(ax, pw_ft, style="modern"):
    """
    Renders 3-storey Front Elevation with realistic daylight background, sun, and PBR textures.
    """
    pw_m = pw_ft * 0.3048
    pal = PALETTES.get(style, PALETTES["modern"])

    porch_w = round(pw_m * 0.44, 2)
    dr_w = round(pw_m - porch_w, 2)

    # 3 Storey Heights (Meters)
    H_ROAD = -0.30
    H_NGL = 0.00
    H_PLINTH = 0.65
    H_GF_CLEAR = 3.20
    H_SLAB = 0.25
    H_1F = H_PLINTH + H_GF_CLEAR + H_SLAB # 4.10m
    H_1F_CLEAR = 3.20
    H_2F = H_1F + H_1F_CLEAR + H_SLAB # 7.55m (Rooftop / 3rd Level)
    H_2F_CLEAR = 3.00
    H_ROOF = H_2F + H_2F_CLEAR + H_SLAB # 10.80m
    H_PARAPET_TOP = H_ROOF + 1.10 # 11.90m
    H_MUMTY_TOP = H_ROOF + 2.60 # 13.40m

    ax.set_xlim(-2.0, pw_m + 3.0)
    ax.set_ylim(-1.5, H_MUMTY_TOP + 1.5)
    ax.axis("off")

    # 1. Daylight Sky & Ground
    draw_daylight_sky_and_ground(ax, -2.0, pw_m + 3.0, -1.5, H_MUMTY_TOP + 1.5, H_NGL, pal)

    # 2. Main Plinth Base
    ax.add_patch(patches.Rectangle((0, H_NGL), pw_m, H_PLINTH, facecolor="#475569", edgecolor="#334155", lw=1.2, zorder=5))
    # Porch Driveway Pavers
    ramp = [[-0.4, H_ROAD], [porch_w + 0.2, H_ROAD], [porch_w, H_PLINTH], [0.0, H_PLINTH]]
    ax.add_patch(MplPoly(ramp, closed=True, facecolor=pal["pavers"], edgecolor="#334155", lw=1.0, zorder=6))

    # 3. LEVEL 1: GROUND FLOOR
    # Porch (Left)
    ax.add_patch(patches.Rectangle((0, H_PLINTH), porch_w, H_GF_CLEAR, facecolor=pal["wall_accent"], edgecolor=pal["trim"], lw=1.8, zorder=6))
    # Drop beam & wood ceiling soffit
    ax.add_patch(patches.Rectangle((0, H_PLINTH + H_GF_CLEAR - 0.5), porch_w, 0.5, facecolor=pal["wood_louver"], edgecolor=pal["wood_louver_edge"], lw=1.2, zorder=7))
    for wy in np.arange(H_PLINTH + H_GF_CLEAR - 0.45, H_PLINTH + H_GF_CLEAR, 0.1):
        ax.plot([0, porch_w], [wy, wy], color=pal["wood_louver_edge"], lw=0.8, zorder=8)
    # Horizontal slatted gate
    ax.add_patch(patches.Rectangle((0.15, H_PLINTH), porch_w - 0.3, 1.9, facecolor="#1E293B", edgecolor=pal["trim"], lw=1.5, zorder=8))
    for gy in np.arange(H_PLINTH + 0.2, H_PLINTH + 1.9, 0.18):
        ax.plot([0.2, porch_w - 0.35], [gy, gy], color="#94A3B8", lw=0.9, zorder=9)

    # Drawing Room Facade (Right)
    dr_x = porch_w
    ax.add_patch(patches.Rectangle((dr_x, H_PLINTH), dr_w, H_GF_CLEAR, facecolor=pal["wall_primary"], edgecolor=pal["trim"], lw=2.0, zorder=6))
    # Travertine Stone Cladding Box
    ax.add_patch(patches.Rectangle((dr_x + 0.25, H_PLINTH + 0.25), dr_w - 0.5, H_GF_CLEAR - 0.5, facecolor=pal["stone_cladding"], edgecolor=pal["stone_joint"], lw=1.5, zorder=7))
    # Stone joints
    for ty in np.arange(H_PLINTH + 0.25, H_PLINTH + H_GF_CLEAR - 0.25, 0.6):
        ax.plot([dr_x + 0.25, dr_x + dr_w - 0.25], [ty, ty], color=pal["stone_joint"], lw=1.0, zorder=8)
    # Picture Window
    win_w = min(2.8, dr_w * 0.65)
    win_h = 2.0
    win_x = dr_x + 0.5
    win_y = H_PLINTH + 0.6
    ax.add_patch(patches.Rectangle((win_x, win_y), win_w, win_h, facecolor=pal["glass_face"], alpha=0.55, edgecolor=pal["trim"], lw=2.0, zorder=9))
    ax.plot([win_x + 0.2, win_x + win_w * 0.6], [win_y + win_h - 0.2, win_y + 0.2], color=pal["glass_glare"], alpha=0.7, lw=2.5, zorder=10)
    # Louvers
    for lx in np.arange(win_x + win_w + 0.2, dr_x + dr_w - 0.3, 0.22):
        ax.add_patch(patches.Rectangle((lx, H_PLINTH + 0.3), 0.11, H_GF_CLEAR - 0.6, facecolor=pal["wood_louver"], edgecolor=pal["wood_louver_edge"], lw=0.8, zorder=9))

    # 4. LEVEL 2: FIRST FLOOR (SLAB & CANTILEVER)
    ax.add_patch(patches.Rectangle((-0.15, H_1F - H_SLAB), pw_m + 0.3, H_SLAB, facecolor="#334155", edgecolor=pal["trim"], lw=1.8, zorder=10))
    # Master Bedroom 3 Cantilever Box (Left)
    ax.add_patch(patches.Rectangle((0, H_1F), porch_w + 0.4, H_1F_CLEAR, facecolor=pal["wall_accent"], edgecolor=pal["trim"], lw=2.0, zorder=11))
    # Fluted Teak louvers texture
    for bx in np.arange(0.2, porch_w + 0.2, 0.25):
        ax.plot([bx, bx], [H_1F + 0.15, H_1F + H_1F_CLEAR - 0.15], color=pal["wood_louver"], lw=1.2, zorder=12)
    # Window
    ax.add_patch(patches.Rectangle((0.6, H_1F + 0.6), (porch_w + 0.4) * 0.65, 1.9, facecolor=pal["glass_face"], alpha=0.5, edgecolor=pal["trim"], lw=1.8, zorder=13))

    # Bedroom 4 & Balcony (Right)
    ax.add_patch(patches.Rectangle((porch_w + 0.4, H_1F), dr_w - 0.4, H_1F_CLEAR, facecolor=pal["wall_primary"], edgecolor=pal["trim"], lw=1.5, zorder=10))
    # Frameless glass balustrade
    ax.add_patch(patches.Rectangle((porch_w + 0.35, H_1F), dr_w - 0.3, 1.05, facecolor=pal["glass_face"], alpha=0.35, edgecolor=pal["trim"], lw=1.8, zorder=14))
    ax.plot([porch_w + 0.35, pw_m + 0.05], [H_1F + 1.05, H_1F + 1.05], color="#F8FAFC", lw=2.5, zorder=15)

    # 5. LEVEL 3: ROOFTOP PENTHOUSE (BED 7 & BED 8)
    ax.add_patch(patches.Rectangle((-0.15, H_2F - H_SLAB), pw_m + 0.3, H_SLAB, facecolor="#334155", edgecolor=pal["trim"], lw=1.8, zorder=15))
    # Sky Terrace Pergola (Left)
    ax.add_patch(patches.Rectangle((0, H_2F), porch_w, 1.05, facecolor=pal["glass_face"], alpha=0.3, edgecolor=pal["trim"], lw=1.5, zorder=16))
    for perg_x in np.arange(0.4, porch_w - 0.2, 0.7):
        ax.plot([perg_x, perg_x], [H_2F, H_2F + 2.8], color="#0F172A", lw=2.0, zorder=17) # Pergola rafters
    ax.plot([0, porch_w], [H_2F + 2.8, H_2F + 2.8], color="#0F172A", lw=3.0, zorder=18)

    # Penthouse Suites (Right)
    ax.add_patch(patches.Rectangle((porch_w, H_2F), dr_w, H_2F_CLEAR, facecolor=pal["wall_primary"], edgecolor=pal["trim"], lw=2.0, zorder=16))
    ax.add_patch(patches.Rectangle((porch_w + 0.5, H_2F + 0.5), dr_w - 1.0, 1.8, facecolor=pal["glass_face"], alpha=0.5, edgecolor=pal["trim"], lw=1.8, zorder=17))

    # 6. ROOF SLAB & MUMTY TOWER
    ax.add_patch(patches.Rectangle((-0.2, H_ROOF - H_SLAB), pw_m + 0.4, H_SLAB, facecolor="#334155", edgecolor=pal["trim"], lw=1.8, zorder=19))
    ax.add_patch(patches.Rectangle((0, H_ROOF), pw_m, 1.05, facecolor=pal["parapet"], edgecolor=pal["trim"], lw=1.5, zorder=20))
    # Mumty Tower (Anchors top)
    mum_x = porch_w * 0.60
    mum_w = pw_m * 0.36
    ax.add_patch(patches.Rectangle((mum_x, H_ROOF), mum_w, 2.6, facecolor=pal["wall_accent"], edgecolor=pal["trim"], lw=2.2, zorder=21))
    # Water Tank Louvers
    for my in np.arange(H_ROOF + 0.8, H_ROOF + 2.3, 0.25):
        ax.plot([mum_x + 0.2, mum_x + mum_w - 0.2], [my, my], color=pal["wood_louver"], lw=1.5, zorder=22)

    # Title Banner
    ax.text(pw_m * 0.5, H_MUMTY_TOP + 0.8, f"DAYLIGHT REALISTIC FRONT ELEVATION ({style.upper()} FACADE)", 
            color="#0F172A", fontsize=11, fontweight="heavy", ha="center")
    ax.text(pw_m * 0.5, H_MUMTY_TOP + 0.45, "Full 3-Storey Elevation • Daylight Sky • Travertine & Teak PBR Textures", 
            color="#0284C7", fontsize=8, fontweight="bold", ha="center")


# ---------------------------------------------------------------------------
# PROMPT 2: 1 KANAL (50'x90') 3-FLOOR 12-BEDROOM RESIDENCE
# ---------------------------------------------------------------------------
def generate_prompt2_floorplans(output_dir):
    """
    Renders 3 Coordinated Floor Plans for Prompt 2:
    - Ground Floor (4 Bed Suites en-suite, Drawing, Dining, Powder, Lounge, Open Kitchen, U-Stairs, Porch, Lawn)
    - First Floor (4 Bed Suites en-suite, Family Living, Kitchenette, Executive Terrace, U-Stairs)
    - Rooftop Floor (4 Bed Suites en-suite, Mumty, Water Tank, Sky Pergola Terrace)
    Total = 12 Bedrooms with 12 attached bathrooms!
    """
    pw = 50.0
    pl = 90.0

    fig, axes = plt.subplots(1, 3, figsize=(24, 12), dpi=200)
    fig.patch.set_facecolor("#FFFFFF")

    porch_w = 22.0
    dr_w = 28.0
    porch_l = 22.0
    dr_l = 18.0

    # ------------------ 1. GROUND FLOOR (4 BEDS) ------------------
    ax1 = axes[0]
    ax1.set_facecolor("#F8FAFC")
    ax1.set_xlim(-4, pw + 4)
    ax1.set_ylim(-6, pl + 8)
    ax1.axis("off")
    ax1.set_title("LEVEL 1: GROUND FLOOR PLAN (1 KANAL)\n4 Bed Suites en-suite • Drawing • Dining • Powder • Open Chef Kitchen", 
                  fontsize=10, fontweight="bold", color="#0F172A", pad=12)
    ax1.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.2))

    # Triple Car Porch (Left)
    ax1.add_patch(patches.Rectangle((0, 0), porch_w, porch_l, facecolor="#F1F5F9", edgecolor="#0F172A", lw=1.8))
    ax1.text(porch_w * 0.5, porch_l * 0.5, "TRIPLE CAR PORCH\n22' x 22'\n(Granite Driveway)", color="#0284C7", fontsize=8, fontweight="bold", ha="center", va="center")

    # Front Landscaped Lawn
    ax1.add_patch(patches.Rectangle((porch_w, 0), dr_w, 5.0, facecolor="#DCFCE7", edgecolor="#16A34A", lw=1.2))
    ax1.text(porch_w + dr_w * 0.5, 2.5, "FRONT LAWN (28' x 5')", color="#15803D", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Formal Drawing Room & Dining (Right)
    ax1.add_patch(patches.Rectangle((porch_w, 5.0), dr_w, dr_l, facecolor="#FFFBEB", edgecolor="#0F172A", lw=1.5))
    ax1.text(porch_w + dr_w * 0.5, 5.0 + dr_l * 0.5, "FORMAL DRAWING & DINING\n28' x 18'", color="#B45309", fontsize=8.5, fontweight="bold", ha="center", va="center")
    # Powder Room
    ax1.add_patch(patches.Rectangle((pw - 7.0, 5.0), 7.0, 6.0, facecolor="#F0FDFA", edgecolor="#0D9488", lw=1.2))
    ax1.text(pw - 3.5, 8.0, "POWDER\n7' x 6'", color="#0F766E", fontsize=7, fontweight="bold", ha="center", va="center")

    # Grand U-Shaped Staircase Lobby (Central)
    stair_x = 0.0
    stair_y = porch_l
    stair_w = 14.0
    stair_l = 20.0
    ax1.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.8))
    for sy in np.arange(stair_y + 1, stair_y + 18, 1.5):
        ax1.plot([stair_x + 1, stair_x + 6], [sy, sy], color="#A855F7", lw=1.2)
        ax1.plot([stair_x + 8, stair_x + 13], [sy, sy], color="#A855F7", lw=1.2)
    ax1.text(stair_x + stair_w * 0.5, stair_y + 10.0, "GRAND U-SHAPED\nSTAIRCASE LOBBY\n14' x 20'", color="#7E22CE", fontsize=8, fontweight="bold", ha="center", va="center")

    # Double-Height Family Lounge
    lounge_x = stair_w
    lounge_w = 22.0
    ax1.add_patch(patches.Rectangle((lounge_x, 23.0), lounge_w, 20.0, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.2))
    ax1.text(lounge_x + lounge_w * 0.5, 33.0, "DOUBLE-HEIGHT FAMILY LOUNGE\n22' x 20'", color="#0F172A", fontsize=8.5, fontweight="bold", ha="center", va="center")

    # Open Modern Chef's Kitchen
    kit_x = lounge_x + lounge_w
    kit_w = pw - kit_x
    ax1.add_patch(patches.Rectangle((kit_x, 23.0), kit_w, 20.0, facecolor="#FEF2F2", edgecolor="#DC2626", lw=1.5))
    ax1.text(kit_x + kit_w * 0.5, 33.0, "OPEN CHEF'S KITCHEN\n14' x 20'\nwith Island & Pantry", color="#B91C1C", fontsize=8, fontweight="bold", ha="center", va="center")

    # 4 Bed Suites on Ground Floor (Bed 1, Bed 2, Bed 3, Bed 4)
    # Mid-Bed 1 & Bed 2
    bed_mid_y = 43.0
    bed_mid_l = 22.0
    ax1.add_patch(patches.Rectangle((0, bed_mid_y), 24.0, bed_mid_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax1.text(12.0, bed_mid_y + 14.0, "BEDROOM 1 (EXECUTIVE MASTER)\n24' x 14'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax1.add_patch(patches.Rectangle((0, bed_mid_y), 12.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax1.text(6.0, bed_mid_y + 4.0, "ATTACHED BATH 1\n12' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")

    ax1.add_patch(patches.Rectangle((24.0, bed_mid_y), 26.0, bed_mid_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax1.text(37.0, bed_mid_y + 14.0, "BEDROOM 2\n26' x 14'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax1.add_patch(patches.Rectangle((pw - 12.0, bed_mid_y), 12.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax1.text(pw - 6.0, bed_mid_y + 4.0, "ATTACHED BATH 2\n12' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")

    # Rear Bed 3 & Bed 4
    rear_y = 65.0
    rear_l = pl - rear_y
    ax1.add_patch(patches.Rectangle((0, rear_y), 24.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax1.text(12.0, rear_y + rear_l * 0.6, "BEDROOM 3\n24' x 17'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax1.add_patch(patches.Rectangle((0, rear_y + rear_l - 8.0), 12.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax1.text(6.0, rear_y + rear_l - 4.0, "ATTACHED BATH 3\n12' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")

    ax1.add_patch(patches.Rectangle((24.0, rear_y), 26.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax1.text(37.0, rear_y + rear_l * 0.6, "BEDROOM 4 (GUEST SUITE)\n26' x 17'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax1.add_patch(patches.Rectangle((pw - 12.0, rear_y + rear_l - 8.0), 12.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax1.text(pw - 6.0, rear_y + rear_l - 4.0, "ATTACHED BATH 4\n12' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")


    # ------------------ 2. FIRST FLOOR (4 BEDS) ------------------
    ax2 = axes[1]
    ax2.set_facecolor("#F8FAFC")
    ax2.set_xlim(-4, pw + 4)
    ax2.set_ylim(-6, pl + 8)
    ax2.axis("off")
    ax2.set_title("LEVEL 2: FIRST FLOOR PLAN (1 KANAL)\n4 Bed Suites en-suite • Family Lounge • Executive Terrace", 
                  fontsize=10, fontweight="bold", color="#0F172A", pad=12)
    ax2.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.2))

    # Executive Front Balcony / Terrace
    ax2.add_patch(patches.Rectangle((0, 0), 22.0, 12.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.2))
    ax2.text(11.0, 6.0, "EXECUTIVE FRONT TERRACE\n22' x 12' (Glass Railing)", color="#0369A1", fontsize=8, fontweight="bold", ha="center", va="center")

    # Bed 5 Suite (Front Left over porch)
    ax2.add_patch(patches.Rectangle((0, 12.0), 22.0, 18.0, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(11.0, 22.0, "BEDROOM 5\n22' x 18'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax2.add_patch(patches.Rectangle((0, 12.0), 10.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(5.0, 15.5, "BATH 5\n10' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Bed 6 Suite (Front Right over drawing)
    ax2.add_patch(patches.Rectangle((22.0, 0), 28.0, 23.0, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(36.0, 14.0, "BEDROOM 6 (MASTER 2)\n28' x 16'", color="#15803D", fontsize=8.5, fontweight="bold", ha="center", va="center")
    ax2.add_patch(patches.Rectangle((pw - 10.0, 0), 10.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(pw - 5.0, 4.0, "BATH 6\n10' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")

    # U-Stairs Continued
    ax2.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.8))
    for sy in np.arange(stair_y + 1, stair_y + 18, 1.5):
        ax2.plot([stair_x + 1, stair_x + 6], [sy, sy], color="#A855F7", lw=1.2)
        ax2.plot([stair_x + 8, stair_x + 13], [sy, sy], color="#A855F7", lw=1.2)
    ax2.text(stair_x + stair_w * 0.5, stair_y + 10.0, "U-SHAPED\nSTAIRS", color="#7E22CE", fontsize=8, fontweight="bold", ha="center", va="center")

    # Upper Family Lounge
    ax2.add_patch(patches.Rectangle((stair_w, 23.0), pw - stair_w, 20.0, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.2))
    ax2.text(stair_w + 18.0, 33.0, "UPPER FAMILY LIVING GALLERY\n36' x 20'", color="#0F172A", fontsize=9, fontweight="bold", ha="center", va="center")

    # Bed 7 Suite (Rear Mid)
    ax2.add_patch(patches.Rectangle((0, bed_mid_y), 24.0, bed_mid_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(12.0, bed_mid_y + 14.0, "BEDROOM 7\n24' x 14'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax2.add_patch(patches.Rectangle((0, bed_mid_y), 12.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(6.0, bed_mid_y + 4.0, "BATH 7\n12' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")

    # Bed 8 Suite (Rear Mid Right)
    ax2.add_patch(patches.Rectangle((24.0, bed_mid_y), 26.0, bed_mid_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(37.0, bed_mid_y + 14.0, "BEDROOM 8\n26' x 14'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax2.add_patch(patches.Rectangle((pw - 12.0, bed_mid_y), 12.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(pw - 6.0, bed_mid_y + 4.0, "BATH 8\n12' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")


    # ------------------ 3. ROOFTOP FLOOR (4 BEDS) ------------------
    ax3 = axes[2]
    ax3.set_facecolor("#F8FAFC")
    ax3.set_xlim(-4, pw + 4)
    ax3.set_ylim(-6, pl + 8)
    ax3.axis("off")
    ax3.set_title("LEVEL 3: ROOFTOP PENTHOUSE PLAN (1 KANAL)\n4 Bed Suites en-suite • Mumty • Sky Deck BBQ Terrace", 
                  fontsize=10, fontweight="bold", color="#0F172A", pad=12)
    ax3.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.2))

    # Vast Rooftop Sky Terrace
    ax3.add_patch(patches.Rectangle((0, 0), pw, 43.0, facecolor="#FEF3C7", edgecolor="#F59E0B", lw=1.8))
    ax3.text(pw * 0.5, 21.0, "GRAND ROOFTOP SKY TERRACE & PERGOLA DECK\n50' x 43'\n(Terracotta Tiles • BBQ Outdoor Lounge)", 
             color="#B45309", fontsize=10, fontweight="bold", ha="center", va="center")

    # Mumty Tower
    ax3.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.8))
    ax3.text(stair_x + stair_w * 0.5, stair_y + 10.0, "STAIR MUMTY\nHEADROOM", color="#7E22CE", fontsize=8, fontweight="bold", ha="center", va="center")

    # Bed 9 Suite (Rooftop)
    ax3.add_patch(patches.Rectangle((0, bed_mid_y), 24.0, bed_mid_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax3.text(12.0, bed_mid_y + 14.0, "BEDROOM 9\n24' x 14'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax3.add_patch(patches.Rectangle((0, bed_mid_y), 12.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax3.text(6.0, bed_mid_y + 4.0, "BATH 9\n12' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")

    # Bed 10 Suite (Rooftop)
    ax3.add_patch(patches.Rectangle((24.0, bed_mid_y), 26.0, bed_mid_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax3.text(37.0, bed_mid_y + 14.0, "BEDROOM 10\n26' x 14'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax3.add_patch(patches.Rectangle((pw - 12.0, bed_mid_y), 12.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax3.text(pw - 6.0, bed_mid_y + 4.0, "BATH 10\n12' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")

    # Bed 11 Suite (Rooftop Rear Left)
    ax3.add_patch(patches.Rectangle((0, rear_y), 24.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax3.text(12.0, rear_y + rear_l * 0.6, "BEDROOM 11\n24' x 17'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax3.add_patch(patches.Rectangle((0, rear_y + rear_l - 8.0), 12.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax3.text(6.0, rear_y + rear_l - 4.0, "BATH 11\n12' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")

    # Bed 12 Suite (Rooftop Rear Right)
    ax3.add_patch(patches.Rectangle((24.0, rear_y), 26.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax3.text(37.0, rear_y + rear_l * 0.6, "BEDROOM 12\n26' x 17'", color="#15803D", fontsize=8, fontweight="bold", ha="center", va="center")
    ax3.add_patch(patches.Rectangle((pw - 12.0, rear_y + rear_l - 8.0), 12.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax3.text(pw - 6.0, rear_y + rear_l - 4.0, "BATH 12\n12' x 8'", color="#0369A1", fontsize=7, fontweight="bold", ha="center", va="center")

    plan_path = os.path.join(output_dir, "prompt2_1kanal_12bed_3floor_complete_blueprints.png")
    fig.savefig(plan_path, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"[SUCCESS] Generated Prompt 2 Floorplans -> {plan_path}")
    return plan_path


# ---------------------------------------------------------------------------
# GENERATE ELEVATIONS ACROSS STYLES (MODERN, SPANISH, CONTEMPORARY)
# ---------------------------------------------------------------------------
def generate_all_elevations():
    styles = ["modern", "spanish", "contemporary"]

    # 1. Prompt 1 (10 Marla 3-floor)
    dir_p1 = os.path.join(BASE_OUTPUT, "prompt_1_10_marla_8bed_3floor")
    os.makedirs(dir_p1, exist_ok=True)
    generate_prompt1_floorplans(dir_p1)

    for st in styles:
        fig, ax = plt.subplots(figsize=(15, 11), dpi=200)
        draw_daylight_front_elevation_3story(ax, 35.0, style=st)
        elev_path = os.path.join(dir_p1, f"prompt1_10marla_front_elevation_{st}.png")
        fig.savefig(elev_path, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
        plt.close(fig)
        print(f"[SUCCESS] Generated Prompt 1 Elevation ({st}) -> {elev_path}")

    # 2. Prompt 2 (1 Kanal 3-floor)
    dir_p2 = os.path.join(BASE_OUTPUT, "prompt_2_1_kanal_12bed_3floor")
    os.makedirs(dir_p2, exist_ok=True)
    generate_prompt2_floorplans(dir_p2)

    for st in styles:
        fig, ax = plt.subplots(figsize=(17, 12), dpi=200)
        draw_daylight_front_elevation_3story(ax, 50.0, style=st)
        elev_path = os.path.join(dir_p2, f"prompt2_1kanal_front_elevation_{st}.png")
        fig.savefig(elev_path, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
        plt.close(fig)
        print(f"[SUCCESS] Generated Prompt 2 Elevation ({st}) -> {elev_path}")

if __name__ == "__main__":
    generate_all_elevations()
