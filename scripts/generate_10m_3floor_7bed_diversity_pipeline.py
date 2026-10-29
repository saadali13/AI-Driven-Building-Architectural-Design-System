r"""
Master 10 Marla 3-Storey 7-Bedroom Diversity Pipeline.
Generates 3 DISTINCT architectural design variations for the user's prompt:
- Plot: 10 Marla (35'x65') Modern House, 3 Floors (G+1+Rooftop).
- 7 Bedrooms total, EACH with attached bathroom (7 Beds + 7 Baths).
- Garage (2-car porch), Formal Drawing Room, Living Room / TV Lounge.
- U-shaped Staircase Core.
- Modern Open Kitchen + Dirty Kitchen (Scullery) + Laundry Room ("londer room").
- Powder Room.
- Rooftop with dedicated BBQ Section & Pergola ("bbr section").
- System generates DIFFERENT floor plans and DIFFERENT front elevations for each variation!
"""

import os
import sys
import math
import numpy as np
import matplotlib
matplotlib.use("Agg")
matplotlib.rcParams['pdf.fonttype'] = 42
matplotlib.rcParams['ps.fonttype'] = 42
import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import Polygon as MplPoly

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(PROJECT_ROOT, "output", "10_marla_3floor_7bed_diversity_suite")
os.makedirs(BASE_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# DESIGN VARIATION A: ASYMMETRIC CANTILEVER (LEFT PORCH, RIGHT DRAWING)
# ---------------------------------------------------------------------------
def generate_design_variation_A():
    var_dir = os.path.join(BASE_DIR, "design_option_A_minimalist_cantilever")
    os.makedirs(var_dir, exist_ok=True)

    pw = 35.0
    pl = 65.0

    # 1. FLOOR PLANS (3 FLOORS)
    fig, axes = plt.subplots(1, 3, figsize=(24, 12), dpi=200)
    fig.patch.set_facecolor("#FFFFFF")

    # --- GROUND FLOOR (Level 0) ---
    ax1 = axes[0]
    ax1.set_facecolor("#F8FAFC")
    ax1.set_xlim(-3, pw + 3)
    ax1.set_ylim(-5, pl + 7)
    ax1.axis("off")
    ax1.set_title("OPTION A: LEVEL 0 - GROUND FLOOR\n2 Beds en-suite • Garage • Drawing • Powder • Kitchen • Dirty Kitchen • Laundry",
                  fontsize=9.5, fontweight="bold", color="#0F172A", pad=12)
    ax1.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.2))

    # Garage / Car Porch (Left)
    ax1.add_patch(patches.Rectangle((0, 0), 15.5, 18.0, facecolor="#F1F5F9", edgecolor="#0F172A", lw=1.5))
    ax1.add_patch(patches.Rectangle((1.5, 2.0), 5.5, 11.5, facecolor="#E2E8F0", edgecolor="#0284C7", lw=1.0)) # Sedan 1
    ax1.add_patch(patches.Rectangle((8.5, 2.0), 5.5, 11.5, facecolor="#E2E8F0", edgecolor="#0284C7", lw=1.0)) # Sedan 2
    ax1.text(7.75, 15.5, "DOUBLE GARAGE (15.5' x 18.0')\nGranite Driveway Pavers", color="#0284C7", fontsize=7.5, fontweight="bold", ha="center")

    # Formal Drawing Room (Right)
    ax1.add_patch(patches.Rectangle((15.5, 0), 19.5, 16.0, facecolor="#FFFBEB", edgecolor="#0F172A", lw=1.5))
    ax1.text(25.25, 8.0, "FORMAL DRAWING ROOM\n19.5' x 16.0'\nTravertine Cladding Facade", color="#B45309", fontsize=8, fontweight="bold", ha="center")
    # Powder Room
    ax1.add_patch(patches.Rectangle((pw - 6.5, 0), 6.5, 5.0, facecolor="#F0FDFA", edgecolor="#0D9488", lw=1.2))
    ax1.text(pw - 3.25, 2.5, "POWDER\n6.5' x 5'", color="#0F766E", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Main Foyer & Living/TV Lounge
    ax1.add_patch(patches.Rectangle((0, 18.0), pw, 18.0, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.0))
    ax1.text(23.0, 27.0, "CENTRAL FAMILY LIVING & TV LOUNGE\n(21' x 18')", color="#0F172A", fontsize=8.5, fontweight="bold", ha="center")

    # Central U-Shaped Staircase Core
    stair_x = 0.0
    stair_y = 18.0
    stair_w = 10.0
    stair_l = 15.0
    ax1.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.5))
    for sy in np.arange(stair_y + 1, stair_y + 13, 1.4):
        ax1.plot([stair_x + 1, stair_x + 4.5], [sy, sy], color="#A855F7", lw=1.0)
        ax1.plot([stair_x + 5.5, stair_x + 9], [sy, sy], color="#A855F7", lw=1.0)
    ax1.text(stair_x + stair_w * 0.5, stair_y + 7.0, "U-SHAPE\nSTAIRS", color="#7E22CE", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Modern Show Kitchen
    ax1.add_patch(patches.Rectangle((10.0, 36.0), 13.0, 10.0, facecolor="#FEF2F2", edgecolor="#DC2626", lw=1.2))
    ax1.text(16.5, 41.0, "MODERN OPEN KITCHEN\n13' x 10' (Island Bar)", color="#B91C1C", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Dirty Kitchen (Scullery)
    ax1.add_patch(patches.Rectangle((23.0, 36.0), 7.0, 10.0, facecolor="#FFF1F2", edgecolor="#E11D48", lw=1.2))
    ax1.text(26.5, 41.0, "DIRTY KITCHEN\n7' x 10'", color="#BE123C", fontsize=7, fontweight="bold", ha="center", va="center")

    # Laundry Room ("londer room")
    ax1.add_patch(patches.Rectangle((30.0, 36.0), 5.0, 10.0, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.2))
    ax1.text(32.5, 41.0, "LAUNDRY\n5' x 10'", color="#15803D", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Rear Bedroom Suites (Bed 1 & Bed 2, Both with Attached Baths)
    rear_y = 46.0
    rear_l = pl - rear_y
    # Bed 1 (Master Suite)
    ax1.add_patch(patches.Rectangle((0, rear_y), 18.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax1.text(9.0, rear_y + rear_l * 0.6, "BEDROOM 1 (MASTER)\n18' x 19'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax1.add_patch(patches.Rectangle((0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax1.text(4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 1\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    # Bed 2 Suite
    ax1.add_patch(patches.Rectangle((18.0, rear_y), 17.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax1.text(26.5, rear_y + rear_l * 0.6, "BEDROOM 2 (GUEST)\n17' x 19'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax1.add_patch(patches.Rectangle((pw - 9.0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax1.text(pw - 4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 2\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")


    # --- FIRST FLOOR (Level 1 - 3 BEDS) ---
    ax2 = axes[1]
    ax2.set_facecolor("#F8FAFC")
    ax2.set_xlim(-3, pw + 3)
    ax2.set_ylim(-5, pl + 7)
    ax2.axis("off")
    ax2.set_title("OPTION A: LEVEL 1 - FIRST FLOOR\n3 Bed Suites (All En-suite) • Lounge • Front Sky Terrace • U-Stairs",
                  fontsize=9.5, fontweight="bold", color="#0F172A", pad=12)
    ax2.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.2))

    # Front Balcony over Porch
    ax2.add_patch(patches.Rectangle((0, 0), 15.5, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.2))
    ax2.text(7.75, 4.0, "FRONT SKY TERRACE\n15.5' x 8' (Glass Railing)", color="#0369A1", fontsize=7.5, fontweight="bold", ha="center")

    # Bed 3 Suite (Front Left over porch)
    ax2.add_patch(patches.Rectangle((0, 8.0), 16.0, 16.0, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(8.0, 18.0, "BEDROOM 3\n16' x 16' (Cantilever Box)", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax2.add_patch(patches.Rectangle((0, 8.0), 7.0, 6.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(3.5, 11.0, "ATTACHED BATH 3\n7' x 6'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    # Bed 4 Suite (Front Right over drawing)
    ax2.add_patch(patches.Rectangle((16.0, 0), 19.0, 24.0, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(25.5, 14.0, "BEDROOM 4 (MASTER 2)\n19' x 18'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax2.add_patch(patches.Rectangle((pw - 8.0, 0), 8.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(pw - 4.0, 3.5, "ATTACHED BATH 4\n8' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    # U-Stairs Continued
    ax2.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.5))
    ax2.text(stair_x + stair_w * 0.5, stair_y + 7.0, "U-SHAPE\nSTAIRS", color="#7E22CE", fontsize=7.5, fontweight="bold", ha="center")

    # Upper Family Living Lounge
    ax2.add_patch(patches.Rectangle((stair_w, 24.0), pw - stair_w, 22.0, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.0))
    ax2.text(stair_w + 12.0, 35.0, "UPPER FAMILY LOUNGE & STUDY\n25' x 22'", color="#0F172A", fontsize=8.5, fontweight="bold", ha="center")

    # Bed 5 Suite (Rear Left)
    ax2.add_patch(patches.Rectangle((0, rear_y), 18.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(9.0, rear_y + rear_l * 0.6, "BEDROOM 5\n18' x 19'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax2.add_patch(patches.Rectangle((0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 5\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    # Rear OTS/Balcony on Right
    ax2.add_patch(patches.Rectangle((18.0, rear_y), 17.0, rear_l, facecolor="#EFF6FF", edgecolor="#3B82F6", lw=1.2))
    ax2.text(26.5, rear_y + rear_l * 0.5, "REAR SERVICE BALCONY\n& OTS LIGHTWELL", color="#1D4ED8", fontsize=7.5, fontweight="bold", ha="center")


    # --- ROOFTOP PENTHOUSE FLOOR (Level 2 - 2 BEDS + BBQ DECK) ---
    ax3 = axes[2]
    ax3.set_facecolor("#F8FAFC")
    ax3.set_xlim(-3, pw + 3)
    ax3.set_ylim(-5, pl + 7)
    ax3.axis("off")
    ax3.set_title("OPTION A: LEVEL 2 - ROOFTOP PENTHOUSE\n2 Bed Suites (En-suite) • Rooftop Pergola BBQ Section • Mumty",
                  fontsize=9.5, fontweight="bold", color="#0F172A", pad=12)
    ax3.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.2))

    # Dedicated BBQ Section & Pergola Lounge ("bbr section")
    ax3.add_patch(patches.Rectangle((0, 0), pw, 42.0, facecolor="#FEF3C7", edgecolor="#F59E0B", lw=2.0))
    # Pergola beams pattern
    for py in np.arange(2.0, 40.0, 4.0):
        ax3.plot([2.0, pw - 2.0], [py, py], color="#B45309", lw=1.5, linestyle="--")
    # BBQ Grill Counter
    ax3.add_patch(patches.Rectangle((pw - 12.0, 4.0), 10.0, 4.0, facecolor="#B91C1C", edgecolor="#7F1D1D", lw=1.5))
    ax3.text(pw - 7.0, 6.0, "OUTDOOR BBQ GRILL\nCOUNTER & SMOKER", color="#FFFFFF", fontsize=7, fontweight="bold", ha="center", va="center")
    ax3.text(14.0, 20.0, "ROOFTOP BBQ & SKY TERRACE\n35' x 42' with Wooden Pergola", color="#92400E", fontsize=9.5, fontweight="heavy", ha="center")

    # Staircase Mumty
    ax3.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.5))
    ax3.text(stair_x + stair_w * 0.5, stair_y + 7.0, "STAIR MUMTY\nHEADROOM", color="#7E22CE", fontsize=7.5, fontweight="bold", ha="center")

    # Bed 6 Suite (Rooftop Left)
    ax3.add_patch(patches.Rectangle((0, rear_y), 18.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax3.text(9.0, rear_y + rear_l * 0.6, "BEDROOM 6 (PENTHOUSE)\n18' x 19'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax3.add_patch(patches.Rectangle((0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax3.text(4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 6\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    # Bed 7 Suite (Rooftop Right)
    ax3.add_patch(patches.Rectangle((18.0, rear_y), 17.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax3.text(26.5, rear_y + rear_l * 0.6, "BEDROOM 7 (PENTHOUSE)\n17' x 19'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax3.add_patch(patches.Rectangle((pw - 9.0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax3.text(pw - 4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 7\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    plan_path = os.path.join(var_dir, "option_A_complete_3floor_blueprints.png")
    fig.savefig(plan_path, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
    plt.close(fig)
    print(f"Generated Option A Floorplans -> {plan_path}")

    # 2. FRONT ELEVATION DRAWING (OPTION A: MINIMALIST CANTILEVER)
    fig_elev, ax_e = plt.subplots(figsize=(15, 11), dpi=200)
    fig_elev.patch.set_facecolor("#FFFFFF")
    draw_elevation_variation(ax_e, pw, variation="A")
    elev_path = os.path.join(var_dir, "option_A_front_elevation_2d.png")
    fig_elev.savefig(elev_path, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
    plt.close(fig_elev)
    print(f"Generated Option A Elevation -> {elev_path}")

    return plan_path, elev_path


# ---------------------------------------------------------------------------
# DESIGN VARIATION B: CUBIST SPLAYED (RIGHT PORCH, LEFT DRAWING - INVERTED!)
# ---------------------------------------------------------------------------
def generate_design_variation_B():
    var_dir = os.path.join(BASE_DIR, "design_option_B_cubist_splayed")
    os.makedirs(var_dir, exist_ok=True)

    pw = 35.0
    pl = 65.0

    # 1. FLOOR PLANS (3 FLOORS - INVERTED ZONATION FOR TRUE DIVERSITY)
    fig, axes = plt.subplots(1, 3, figsize=(24, 12), dpi=200)
    fig.patch.set_facecolor("#FFFFFF")

    # --- GROUND FLOOR (Level 0 - INVERTED: RIGHT PORCH, LEFT DRAWING) ---
    ax1 = axes[0]
    ax1.set_facecolor("#F8FAFC")
    ax1.set_xlim(-3, pw + 3)
    ax1.set_ylim(-5, pl + 7)
    ax1.axis("off")
    ax1.set_title("OPTION B: LEVEL 0 - GROUND FLOOR (INVERTED TYPOLOGY)\n2 Beds en-suite • Right Garage • Left Drawing • Powder • Kitchen • Dirty Kitchen • Laundry",
                  fontsize=9.5, fontweight="bold", color="#0F172A", pad=12)
    ax1.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.2))

    # Formal Drawing Room (Left) with Corner Window
    ax1.add_patch(patches.Rectangle((0, 0), 19.5, 16.0, facecolor="#FFFBEB", edgecolor="#0F172A", lw=1.5))
    ax1.text(9.75, 8.0, "FORMAL DRAWING ROOM\n19.5' x 16.0'\nCorner Wrap-Around Glazing", color="#B45309", fontsize=8, fontweight="bold", ha="center")
    # Powder Room
    ax1.add_patch(patches.Rectangle((0, 0), 6.5, 5.0, facecolor="#F0FDFA", edgecolor="#0D9488", lw=1.2))
    ax1.text(3.25, 2.5, "POWDER\n6.5' x 5'", color="#0F766E", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Double Garage / Car Porch (Right)
    ax1.add_patch(patches.Rectangle((19.5, 0), 15.5, 18.0, facecolor="#F1F5F9", edgecolor="#0F172A", lw=1.5))
    ax1.add_patch(patches.Rectangle((21.0, 2.0), 5.5, 11.5, facecolor="#E2E8F0", edgecolor="#0284C7", lw=1.0)) # Sedan 1
    ax1.add_patch(patches.Rectangle((28.0, 2.0), 5.5, 11.5, facecolor="#E2E8F0", edgecolor="#0284C7", lw=1.0)) # Sedan 2
    ax1.text(27.25, 15.5, "DOUBLE GARAGE (15.5' x 18.0')\nGranite Driveway", color="#0284C7", fontsize=7.5, fontweight="bold", ha="center")

    # Central Living & Courtyard Lightwell
    ax1.add_patch(patches.Rectangle((0, 18.0), pw, 18.0, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.0))
    ax1.text(12.0, 27.0, "CENTRAL FAMILY LIVING & TV LOUNGE\n(21' x 18')", color="#0F172A", fontsize=8.5, fontweight="bold", ha="center")

    # U-Stairs Core (Right Center)
    stair_x = pw - 10.0
    stair_y = 18.0
    stair_w = 10.0
    stair_l = 15.0
    ax1.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.5))
    for sy in np.arange(stair_y + 1, stair_y + 13, 1.4):
        ax1.plot([stair_x + 1, stair_x + 4.5], [sy, sy], color="#A855F7", lw=1.0)
        ax1.plot([stair_x + 5.5, stair_x + 9], [sy, sy], color="#A855F7", lw=1.0)
    ax1.text(stair_x + stair_w * 0.5, stair_y + 7.0, "U-SHAPE\nSTAIRS", color="#7E22CE", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Modern Open Kitchen (Left)
    ax1.add_patch(patches.Rectangle((0, 36.0), 14.0, 10.0, facecolor="#FEF2F2", edgecolor="#DC2626", lw=1.2))
    ax1.text(7.0, 41.0, "MODERN OPEN KITCHEN\n14' x 10' with Island", color="#B91C1C", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Dirty Kitchen (Scullery)
    ax1.add_patch(patches.Rectangle((14.0, 36.0), 7.0, 10.0, facecolor="#FFF1F2", edgecolor="#E11D48", lw=1.2))
    ax1.text(17.5, 41.0, "DIRTY KITCHEN\n7' x 10'", color="#BE123C", fontsize=7, fontweight="bold", ha="center", va="center")

    # Laundry Room ("londer room")
    ax1.add_patch(patches.Rectangle((21.0, 36.0), 5.0, 10.0, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.2))
    ax1.text(23.5, 41.0, "LAUNDRY\n5' x 10'", color="#15803D", fontsize=6.5, fontweight="bold", ha="center", va="center")

    # Rear Bedroom Suites (Bed 1 & Bed 2)
    rear_y = 46.0
    rear_l = pl - rear_y
    ax1.add_patch(patches.Rectangle((0, rear_y), 18.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax1.text(9.0, rear_y + rear_l * 0.6, "BEDROOM 1 (MASTER)\n18' x 19'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax1.add_patch(patches.Rectangle((0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax1.text(4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 1\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    ax1.add_patch(patches.Rectangle((18.0, rear_y), 17.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax1.text(26.5, rear_y + rear_l * 0.6, "BEDROOM 2\n17' x 19'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax1.add_patch(patches.Rectangle((pw - 9.0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax1.text(pw - 4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 2\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")


    # --- FIRST FLOOR (Level 1 - 3 BEDS - OPTION B) ---
    ax2 = axes[1]
    ax2.set_facecolor("#F8FAFC")
    ax2.set_xlim(-3, pw + 3)
    ax2.set_ylim(-5, pl + 7)
    ax2.axis("off")
    ax2.set_title("OPTION B: LEVEL 1 - FIRST FLOOR\n3 Bed Suites (En-suite) • Lounge • Right Front Terrace • U-Stairs",
                  fontsize=9.5, fontweight="bold", color="#0F172A", pad=12)
    ax2.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.2))

    # Bed 3 Suite (Front Left over drawing room)
    ax2.add_patch(patches.Rectangle((0, 0), 19.0, 24.0, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(9.5, 14.0, "BEDROOM 3 (MASTER 2)\n19' x 18' (Corner Cantilever)", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax2.add_patch(patches.Rectangle((0, 0), 8.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(4.0, 3.5, "ATTACHED BATH 3\n8' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    # Front Terrace over Porch (Right)
    ax2.add_patch(patches.Rectangle((19.0, 0), 16.0, 8.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.2))
    ax2.text(27.0, 4.0, "RIGHT SKY TERRACE\n16' x 8' (Glass Railing)", color="#0369A1", fontsize=7.5, fontweight="bold", ha="center")

    # Bed 4 Suite (Front Right over porch)
    ax2.add_patch(patches.Rectangle((19.0, 8.0), 16.0, 16.0, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(27.0, 18.0, "BEDROOM 4\n16' x 16'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax2.add_patch(patches.Rectangle((pw - 7.0, 8.0), 7.0, 6.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(pw - 3.5, 11.0, "ATTACHED BATH 4\n7' x 6'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    # U-Stairs Continued
    ax2.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.5))
    ax2.text(stair_x + stair_w * 0.5, stair_y + 7.0, "U-SHAPE\nSTAIRS", color="#7E22CE", fontsize=7.5, fontweight="bold", ha="center")

    # Upper Family Lounge
    ax2.add_patch(patches.Rectangle((0, 24.0), stair_x, 22.0, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.0))
    ax2.text(12.0, 35.0, "UPPER FAMILY LOUNGE\n25' x 22'", color="#0F172A", fontsize=8.5, fontweight="bold", ha="center")

    # Bed 5 Suite (Rear Right)
    ax2.add_patch(patches.Rectangle((18.0, rear_y), 17.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax2.text(26.5, rear_y + rear_l * 0.6, "BEDROOM 5\n17' x 19'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax2.add_patch(patches.Rectangle((pw - 9.0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax2.text(pw - 4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 5\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")


    # --- ROOFTOP PENTHOUSE FLOOR (Level 2 - 2 BEDS + BBQ DECK - OPTION B) ---
    ax3 = axes[2]
    ax3.set_facecolor("#F8FAFC")
    ax3.set_xlim(-3, pw + 3)
    ax3.set_ylim(-5, pl + 7)
    ax3.axis("off")
    ax3.set_title("OPTION B: LEVEL 2 - ROOFTOP PENTHOUSE\n2 Bed Suites (En-suite) • Rooftop Pergola BBQ Section • Mumty",
                  fontsize=9.5, fontweight="bold", color="#0F172A", pad=12)
    ax3.add_patch(patches.Rectangle((0, 0), pw, pl, facecolor="#FFFFFF", edgecolor="#0F172A", lw=2.2))

    # Dedicated BBQ Section & Pergola Lounge on Left
    ax3.add_patch(patches.Rectangle((0, 0), pw, 42.0, facecolor="#FEF3C7", edgecolor="#F59E0B", lw=2.0))
    for py in np.arange(2.0, 40.0, 4.0):
        ax3.plot([2.0, pw - 2.0], [py, py], color="#B45309", lw=1.5, linestyle="--")
    # BBQ Counter on Left
    ax3.add_patch(patches.Rectangle((2.0, 4.0), 10.0, 4.0, facecolor="#B91C1C", edgecolor="#7F1D1D", lw=1.5))
    ax3.text(7.0, 6.0, "OUTDOOR BBQ GRILL\nCOUNTER & SMOKER", color="#FFFFFF", fontsize=7, fontweight="bold", ha="center", va="center")
    ax3.text(21.0, 20.0, "ROOFTOP BBQ & SKY TERRACE\n35' x 42' with Wooden Pergola", color="#92400E", fontsize=9.5, fontweight="heavy", ha="center")

    # Mumty Core
    ax3.add_patch(patches.Rectangle((stair_x, stair_y), stair_w, stair_l, facecolor="#FAF5FF", edgecolor="#9333EA", lw=1.5))
    ax3.text(stair_x + stair_w * 0.5, stair_y + 7.0, "STAIR MUMTY\nHEADROOM", color="#7E22CE", fontsize=7.5, fontweight="bold", ha="center")

    # Bed 6 Suite
    ax3.add_patch(patches.Rectangle((0, rear_y), 18.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax3.text(9.0, rear_y + rear_l * 0.6, "BEDROOM 6 (PENTHOUSE)\n18' x 19'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax3.add_patch(patches.Rectangle((0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax3.text(4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 6\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    # Bed 7 Suite
    ax3.add_patch(patches.Rectangle((18.0, rear_y), 17.0, rear_l, facecolor="#F0FDF4", edgecolor="#16A34A", lw=1.5))
    ax3.text(26.5, rear_y + rear_l * 0.6, "BEDROOM 7 (PENTHOUSE)\n17' x 19'", color="#15803D", fontsize=8, fontweight="bold", ha="center")
    ax3.add_patch(patches.Rectangle((pw - 9.0, rear_y + rear_l - 7.0), 9.0, 7.0, facecolor="#E0F2FE", edgecolor="#0284C7", lw=1.0))
    ax3.text(pw - 4.5, rear_y + rear_l - 3.5, "ATTACHED BATH 7\n9' x 7'", color="#0369A1", fontsize=6.5, fontweight="bold", ha="center")

    plan_path = os.path.join(var_dir, "option_B_complete_3floor_blueprints.png")
    fig.savefig(plan_path, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
    plt.close(fig)
    print(f"Generated Option B Floorplans -> {plan_path}")

    # 2. FRONT ELEVATION DRAWING (OPTION B: INVERTED SPLAYED CUBIST)
    fig_elev, ax_e = plt.subplots(figsize=(15, 11), dpi=200)
    fig_elev.patch.set_facecolor("#FFFFFF")
    draw_elevation_variation(ax_e, pw, variation="B")
    elev_path = os.path.join(var_dir, "option_B_front_elevation_2d.png")
    fig_elev.savefig(elev_path, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
    plt.close(fig_elev)
    print(f"Generated Option B Elevation -> {elev_path}")

    return plan_path, elev_path


# ---------------------------------------------------------------------------
# FRONT ELEVATION ENGINE WITH DISTINCT ARCHITECTURAL VARIATIONS (A & B)
# ---------------------------------------------------------------------------
def draw_elevation_variation(ax, pw_ft, variation="A"):
    pw_m = pw_ft * 0.3048

    # Heights
    H_ROAD = -0.30
    H_NGL = 0.00
    H_PLINTH = 0.65
    H_GF_CLEAR = 3.20
    H_SLAB = 0.25
    H_1F = H_PLINTH + H_GF_CLEAR + H_SLAB # 4.10m
    H_1F_CLEAR = 3.20
    H_2F = H_1F + H_1F_CLEAR + H_SLAB # 7.55m
    H_2F_CLEAR = 3.00
    H_ROOF = H_2F + H_2F_CLEAR + H_SLAB # 10.80m
    H_PARAPET_TOP = H_ROOF + 1.10 # 11.90m
    H_MUMTY_TOP = H_ROOF + 2.60 # 13.40m

    ax.set_xlim(-3.6, pw_m + 3.8)
    ax.set_ylim(-1.6, 14.5)
    ax.axis("off")

    # Clean White Drawing Canvas with Subtle Ground Hatch
    ax.fill_between([-3.6, pw_m + 3.8], [-1.6, -1.6], [H_NGL, H_NGL], color="#F1F5F9", zorder=1)
    ax.plot([-3.6, pw_m + 3.8], [H_NGL, H_NGL], color="#0F172A", lw=2.2, zorder=4)
    ax.plot([-3.6, pw_m + 3.8], [H_ROAD, H_ROAD], color="#475569", lw=1.5, linestyle="--", zorder=3)

    # Main Plinth Base
    ax.add_patch(patches.Rectangle((0, H_NGL), pw_m, H_PLINTH, facecolor="#334155", edgecolor="#0F172A", lw=1.8, zorder=5))

    if variation == "A":
        # TYPOLOGY A: LEFT PORCH (15.5'), RIGHT DRAWING (19.5')
        porch_w = round(pw_m * 0.44, 2)
        dr_w = round(pw_m - porch_w, 2)

        # Driveway Ramp on Left
        ramp = [[-0.2, H_ROAD], [porch_w + 0.2, H_ROAD], [porch_w, H_PLINTH], [0.0, H_PLINTH]]
        ax.add_patch(MplPoly(ramp, closed=True, facecolor="#64748B", edgecolor="#0F172A", lw=1.2, zorder=6))

        # Entrance steps
        for i, sy in enumerate([0.22, 0.44, 0.65]):
            ax.add_patch(patches.Rectangle((porch_w + 0.2 + i*0.12, 0), 1.4 - i*0.12, sy, facecolor="#CBD5E1", edgecolor="#0F172A", lw=0.8, zorder=7+i))

        # Ground Floor Left Porch
        ax.add_patch(patches.Rectangle((0, H_PLINTH), porch_w, H_GF_CLEAR, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.8, zorder=6))
        # Cedar soffit drop beam
        ax.add_patch(patches.Rectangle((0, H_PLINTH + H_GF_CLEAR - 0.5), porch_w, 0.5, facecolor="#78350F", edgecolor="#0F172A", lw=1.2, zorder=7))
        # Horizontal slatted gate
        ax.add_patch(patches.Rectangle((0.15, H_PLINTH), porch_w - 0.3, 1.9, facecolor="#0F172A", edgecolor="#0F172A", lw=1.5, zorder=8))
        for gy in np.arange(H_PLINTH + 0.2, H_PLINTH + 1.9, 0.18):
            ax.plot([0.2, porch_w - 0.35], [gy, gy], color="#38BDF8", lw=1.0, zorder=9)

        # Ground Floor Right Drawing Room (Travertine Cladding)
        dr_x = porch_w
        ax.add_patch(patches.Rectangle((dr_x, H_PLINTH), dr_w, H_GF_CLEAR, facecolor="#E2D9C8", edgecolor="#0F172A", lw=2.0, zorder=6))
        for ty in np.arange(H_PLINTH + 0.3, H_PLINTH + H_GF_CLEAR, 0.55):
            ax.plot([dr_x, dr_x + dr_w], [ty, ty], color="#A89F91", lw=0.8, zorder=7)
        # Glazed curtain window
        ax.add_patch(patches.Rectangle((dr_x + 0.4, H_PLINTH + 0.5), dr_w * 0.65, 2.2, facecolor="#BAE6FD", alpha=0.8, edgecolor="#0F172A", lw=1.8, zorder=8))
        # Louvers
        for lx in np.arange(dr_x + dr_w * 0.72, dr_x + dr_w - 0.2, 0.22):
            ax.add_patch(patches.Rectangle((lx, H_PLINTH + 0.3), 0.11, H_GF_CLEAR - 0.6, facecolor="#B45309", edgecolor="#78350F", lw=0.8, zorder=9))

        # First Floor Slab
        ax.add_patch(patches.Rectangle((-0.2, H_1F - H_SLAB), pw_m + 0.4, H_SLAB, facecolor="#1E293B", edgecolor="#0F172A", lw=2.0, zorder=10))

        # First Floor Left Cantilever Box (Teak Louvers)
        ax.add_patch(patches.Rectangle((0, H_1F), porch_w + 0.4, H_1F_CLEAR, facecolor="#1E293B", edgecolor="#0F172A", lw=2.0, zorder=11))
        for bx in np.arange(0.2, porch_w + 0.2, 0.25):
            ax.plot([bx, bx], [H_1F + 0.2, H_1F + H_1F_CLEAR - 0.2], color="#D97706", lw=1.2, zorder=12)
        ax.add_patch(patches.Rectangle((0.6, H_1F + 0.6), (porch_w + 0.4) * 0.65, 1.9, facecolor="#BAE6FD", alpha=0.8, edgecolor="#0F172A", lw=1.8, zorder=13))

        # First Floor Right Sky Terrace (Frameless Glass Railing)
        ax.add_patch(patches.Rectangle((porch_w + 0.4, H_1F), dr_w - 0.4, H_1F_CLEAR, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.2, zorder=10))
        ax.add_patch(patches.Rectangle((porch_w + 0.35, H_1F), dr_w - 0.3, 1.05, facecolor="#BAE6FD", alpha=0.4, edgecolor="#0F172A", lw=1.8, zorder=14))
        ax.plot([porch_w + 0.35, pw_m + 0.05], [H_1F + 1.05, H_1F + 1.05], color="#0F172A", lw=2.2, zorder=15)

        # Second Floor (Rooftop Penthouse & Pergola on Left)
        ax.add_patch(patches.Rectangle((-0.2, H_2F - H_SLAB), pw_m + 0.4, H_SLAB, facecolor="#1E293B", edgecolor="#0F172A", lw=2.0, zorder=15))
        # Pergola BBQ deck on Left
        ax.add_patch(patches.Rectangle((0, H_2F), porch_w, 1.05, facecolor="#BAE6FD", alpha=0.3, edgecolor="#0F172A", lw=1.5, zorder=16))
        for perg_x in np.arange(0.4, porch_w - 0.2, 0.7):
            ax.plot([perg_x, perg_x], [H_2F, H_2F + 2.8], color="#78350F", lw=2.2, zorder=17)
        ax.plot([0, porch_w], [H_2F + 2.8, H_2F + 2.8], color="#78350F", lw=3.0, zorder=18)

        # Penthouse Suites on Right
        ax.add_patch(patches.Rectangle((porch_w, H_2F), dr_w, H_2F_CLEAR, facecolor="#F1F5F9", edgecolor="#0F172A", lw=2.0, zorder=16))
        ax.add_patch(patches.Rectangle((porch_w + 0.6, H_2F + 0.6), dr_w - 1.2, 1.8, facecolor="#BAE6FD", alpha=0.8, edgecolor="#0F172A", lw=1.8, zorder=17))

        # Roof Parapet & Mumty
        ax.add_patch(patches.Rectangle((0, H_ROOF), pw_m, 1.05, facecolor="#E2E8F0", edgecolor="#0F172A", lw=1.5, zorder=20))
        mum_x = porch_w * 0.6
        mum_w = pw_m * 0.36
        ax.add_patch(patches.Rectangle((mum_x, H_ROOF), mum_w, 2.6, facecolor="#1E293B", edgecolor="#0F172A", lw=2.2, zorder=21))
        for my in np.arange(H_ROOF + 0.8, H_ROOF + 2.3, 0.25):
            ax.plot([mum_x + 0.2, mum_x + mum_w - 0.2], [my, my], color="#D97706", lw=1.5, zorder=22)

        title_txt = "DESIGN OPTION A: ASYMMETRIC CANTILEVER MINIMALIST FACADE (10 MARLA)"
        sub_txt = "Left Car Porch • Travertine Cladding Box • Fluted Teak Louvers • Left Rooftop BBQ Pergola"

    else:
        # TYPOLOGY B: RIGHT PORCH (15.5'), LEFT DRAWING (19.5') - COMPLETELY INVERTED!
        dr_w = round(pw_m * 0.56, 2)
        porch_w = round(pw_m - dr_w, 2)

        # Driveway Ramp on Right
        ramp = [[pw_m - porch_w - 0.2, H_ROAD], [pw_m + 0.2, H_ROAD], [pw_m, H_PLINTH], [pw_m - porch_w, H_PLINTH]]
        ax.add_patch(MplPoly(ramp, closed=True, facecolor="#64748B", edgecolor="#0F172A", lw=1.2, zorder=6))

        # Entrance steps on Left
        for i, sy in enumerate([0.22, 0.44, 0.65]):
            ax.add_patch(patches.Rectangle((dr_w - 1.6 + i*0.12, 0), 1.4 - i*0.12, sy, facecolor="#CBD5E1", edgecolor="#0F172A", lw=0.8, zorder=7+i))

        # Ground Floor Left Drawing Room (Dark Charcoal & Warm Wood)
        ax.add_patch(patches.Rectangle((0, H_PLINTH), dr_w, H_GF_CLEAR, facecolor="#1E293B", edgecolor="#0F172A", lw=2.0, zorder=6))
        # Corner picture window
        ax.add_patch(patches.Rectangle((0.4, H_PLINTH + 0.4), dr_w - 0.8, 2.3, facecolor="#BAE6FD", alpha=0.8, edgecolor="#0F172A", lw=1.8, zorder=8))
        # Vertical teak accent panel
        for lx in np.arange(dr_w - 1.8, dr_w - 0.4, 0.22):
            ax.add_patch(patches.Rectangle((lx, H_PLINTH + 0.3), 0.11, H_GF_CLEAR - 0.6, facecolor="#D97706", edgecolor="#78350F", lw=0.8, zorder=9))

        # Ground Floor Right Porch
        porch_x = dr_w
        ax.add_patch(patches.Rectangle((porch_x, H_PLINTH), porch_w, H_GF_CLEAR, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.8, zorder=6))
        # Cedar beam
        ax.add_patch(patches.Rectangle((porch_x, H_PLINTH + H_GF_CLEAR - 0.5), porch_w, 0.5, facecolor="#78350F", edgecolor="#0F172A", lw=1.2, zorder=7))
        # Gate on Right
        ax.add_patch(patches.Rectangle((porch_x + 0.15, H_PLINTH), porch_w - 0.3, 1.9, facecolor="#0F172A", edgecolor="#0F172A", lw=1.5, zorder=8))
        for gy in np.arange(H_PLINTH + 0.2, H_PLINTH + 1.9, 0.18):
            ax.plot([porch_x + 0.2, pw_m - 0.2], [gy, gy], color="#38BDF8", lw=1.0, zorder=9)

        # First Floor Slab
        ax.add_patch(patches.Rectangle((-0.2, H_1F - H_SLAB), pw_m + 0.4, H_SLAB, facecolor="#334155", edgecolor="#0F172A", lw=2.0, zorder=10))

        # First Floor Left Master Suite (Floating White Frame with Charcoal Box)
        ax.add_patch(patches.Rectangle((0, H_1F), dr_w - 0.4, H_1F_CLEAR, facecolor="#F1F5F9", edgecolor="#0F172A", lw=2.0, zorder=11))
        ax.add_patch(patches.Rectangle((0.6, H_1F + 0.5), dr_w - 1.6, 2.0, facecolor="#BAE6FD", alpha=0.8, edgecolor="#0F172A", lw=1.8, zorder=12))

        # First Floor Right Balcony over Porch
        ax.add_patch(patches.Rectangle((dr_w - 0.4, H_1F), porch_w + 0.4, H_1F_CLEAR, facecolor="#F8FAFC", edgecolor="#0F172A", lw=1.2, zorder=10))
        ax.add_patch(patches.Rectangle((dr_w - 0.4, H_1F), porch_w + 0.4, 1.05, facecolor="#BAE6FD", alpha=0.4, edgecolor="#0F172A", lw=1.8, zorder=14))
        ax.plot([dr_w - 0.4, pw_m + 0.05], [H_1F + 1.05, H_1F + 1.05], color="#0F172A", lw=2.2, zorder=15)

        # Second Floor (Penthouse Suites on Left, Rooftop BBQ Pergola on Right)
        ax.add_patch(patches.Rectangle((-0.2, H_2F - H_SLAB), pw_m + 0.4, H_SLAB, facecolor="#334155", edgecolor="#0F172A", lw=2.0, zorder=15))
        ax.add_patch(patches.Rectangle((0, H_2F), dr_w, H_2F_CLEAR, facecolor="#1E293B", edgecolor="#0F172A", lw=2.0, zorder=16))
        ax.add_patch(patches.Rectangle((0.8, H_2F + 0.6), dr_w - 1.6, 1.8, facecolor="#BAE6FD", alpha=0.8, edgecolor="#0F172A", lw=1.8, zorder=17))

        # Pergola BBQ Deck on Right
        for perg_x in np.arange(dr_w + 0.4, pw_m - 0.2, 0.7):
            ax.plot([perg_x, perg_x], [H_2F, H_2F + 2.8], color="#78350F", lw=2.2, zorder=17)
        ax.plot([dr_w, pw_m], [H_2F + 2.8, H_2F + 2.8], color="#78350F", lw=3.0, zorder=18)

        # Mumty on Right
        mum_x = dr_w * 0.4
        mum_w = pw_m * 0.36
        ax.add_patch(patches.Rectangle((mum_x, H_ROOF), mum_w, 2.6, facecolor="#1E293B", edgecolor="#0F172A", lw=2.2, zorder=21))
        for my in np.arange(H_ROOF + 0.8, H_ROOF + 2.3, 0.25):
            ax.plot([mum_x + 0.2, mum_x + mum_w - 0.2], [my, my], color="#D97706", lw=1.5, zorder=22)

        title_txt = "DESIGN OPTION B: CUBIST SPLAYED MODERN FACADE (10 MARLA INVERTED)"
        sub_txt = "Right Car Porch • Left Corner Window • Charcoal Porcelain • Right Rooftop BBQ Pergola"

    # TECHNICAL DATUMS (RIGHT SIDE - RED ARROWS IDENTICAL TO DHA STANDARD)
    datums = [
        (H_MUMTY_TOP, "+13.40m (+44'-0\") WATER TANK TOP"),
        (H_ROOF + 2.6, "+13.00m (+42'-8\") MUMTY ROOF TOP"),
        (H_PARAPET_TOP, "+11.90m (+39'-0\") PARAPET TOP"),
        (H_ROOF, "+10.80m (+35'-5\") ROOF SLAB LEVEL"),
        (H_2F, "+7.55m (+24'-9\") ROOFTOP PENTHOUSE FFL"),
        (H_1F, "+4.10m (+13'-5\") FIRST FLOOR FFL"),
        (H_PLINTH, "+0.65m (+2'-2\") PLINTH LEVEL"),
        (H_NGL, "±0.00m NATURAL GROUND LEVEL"),
        (H_ROAD, "-0.30m ROAD FORMATION LEVEL")
    ]
    for dy, lbl in datums:
        ax.plot([pw_m + 0.2, pw_m + 0.9], [dy, dy], color="#DC2626", lw=1.2, linestyle="--")
        ax.text(pw_m + 1.0, dy, lbl, color="#DC2626", fontsize=7.5, va="center", fontweight="bold")

    # Callouts & Leader Lines (Left Side)
    ax.text(-3.2, H_PLINTH + 1.0, "DOUBLE GARAGE (15.5'x18')\nRecessed 3000K LED Soffit", color="#0F172A", fontsize=7.5, fontweight="bold")
    ax.text(-3.2, H_1F + 1.5, "FIRST FLOOR MASTER SUITE\nCantilevered Volume w/ Louvers", color="#0F172A", fontsize=7.5, fontweight="bold")
    ax.text(-3.2, H_2F + 1.5, "ROOFTOP BBQ & SKY DECK\nTeak & Steel Pergola Rafters", color="#B45309", fontsize=7.5, fontweight="bold")

    # Titles at top
    ax.text(pw_m * 0.5, 14.0, title_txt, color="#0F172A", fontsize=11, fontweight="heavy", ha="center")
    ax.text(pw_m * 0.5, 13.5, sub_txt, color="#0284C7", fontsize=8, fontweight="bold", ha="center")


if __name__ == "__main__":
    generate_design_variation_A()
    generate_design_variation_B()
    print("Successfully generated multiple distinct designs and front elevations!")
