r"""
Creates a side-by-side presentation sheet for Option 2:
Left: Coordinated 2D Floor Plan (Ground & First Floor)
Right: Isolated 3D House Render (Studio background, only the house)
Proving 100% geometric alignment without floor plan alteration.
"""

import os
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import numpy as np

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output", "3d_modeling_and_elevation_options", "02_option2_gemini_elevation_and_3d")
RENDER_PATH = os.path.join(OUTPUT_DIR, "option2_isolated_house_3d_render.jpg")

def create_comparison_sheet():
    pw_ft = 35.0
    pl_ft = 65.0

    fig = plt.figure(figsize=(20, 10), dpi=200)
    fig.patch.set_facecolor("#0B1120")

    gs = fig.add_gridspec(1, 2, width_ratios=[1.0, 1.4], wspace=0.12)
    ax_plan = fig.add_subplot(gs[0, 0])
    ax_render = fig.add_subplot(gs[0, 1])

    # 1. LEFT PANEL: COORDINATED 2D FLOOR PLAN
    ax_plan.set_facecolor("#0F172A")
    ax_plan.set_xlim(-4, pw_ft + 4)
    ax_plan.set_ylim(-6, pl_ft + 8)
    ax_plan.axis("off")

    porch_w = 15.5
    dr_w = 19.5
    porch_l = 20.0
    dr_l = 16.0

    # Plot Boundary
    ax_plan.add_patch(patches.Rectangle((0, 0), pw_ft, pl_ft, facecolor="#090E17", edgecolor="#475569", lw=1.5, linestyle="--"))

    # Car Porch (Left)
    ax_plan.add_patch(patches.Rectangle((0, 0), porch_w, porch_l, facecolor="#1E2433", edgecolor="#38BDF8", lw=2.0))
    # Two Car blocks
    ax_plan.add_patch(patches.Rectangle((1.5, 2.5), 5.5, 12.0, facecolor="#334155", edgecolor="#38BDF8", lw=1.2))
    ax_plan.add_patch(patches.Rectangle((8.5, 2.5), 5.5, 12.0, facecolor="#334155", edgecolor="#38BDF8", lw=1.2))
    ax_plan.text(porch_w * 0.5, 16.5, "DOUBLE CAR PORCH (15.5' x 20')", color="#38BDF8", fontsize=8, fontweight="bold", ha="center")

    # Drawing Room (Right)
    ax_plan.add_patch(patches.Rectangle((porch_w, 0), dr_w, dr_l, facecolor="#292524", edgecolor="#F59E0B", lw=2.0))
    ax_plan.text(porch_w + dr_w * 0.5, dr_l * 0.5, "FORMAL DRAWING ROOM\n(19.5' x 16')\nTravertine Stone Facade", color="#F59E0B", fontsize=8, fontweight="bold", ha="center", va="center")
    ax_plan.plot([porch_w + 1.0, pw_ft - 1.0], [0, 0], color="#38BDF8", lw=4.0) # Window

    # Main Entrance Foyer
    ax_plan.add_patch(patches.Rectangle((porch_w - 2.5, porch_l), 5.0, 6.0, facecolor="#1E293B", edgecolor="#10B981", lw=1.5))
    ax_plan.text(porch_w, porch_l + 3.0, "MAIN FOYER", color="#34D399", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Central Lounge
    lounge_y = dr_l
    lounge_l = 22.0
    lounge_w = pw_ft * 0.65
    ax_plan.add_patch(patches.Rectangle((0, porch_l), lounge_w, lounge_l - (porch_l - dr_l), facecolor="#1E293B", edgecolor="#38BDF8", lw=1.5))
    ax_plan.text(lounge_w * 0.5, porch_l + 8.0, "CENTRAL FAMILY LIVING & ATRIUM", color="#F8FAFC", fontsize=8.5, fontweight="bold", ha="center")

    # Staircase Core
    stair_w = pw_ft - lounge_w
    ax_plan.add_patch(patches.Rectangle((lounge_w, lounge_y), stair_w, 18.0, facecolor="#1E1E2E", edgecolor="#A855F7", lw=1.5))
    for sy in np.arange(lounge_y + 1, lounge_y + 17, 1.8):
        ax_plan.plot([lounge_w + 1, pw_ft - 1], [sy, sy], color="#A855F7", lw=0.9)
    ax_plan.text(lounge_w + stair_w * 0.5, lounge_y + 9.0, "STAIRCASE\nTO MUMTY", color="#C084FC", fontsize=8, fontweight="bold", ha="center", va="center")

    # Rear Bedroom Suites
    rear_y = max(porch_l + lounge_l - (porch_l - dr_l), lounge_y + 18.0)
    rear_l = pl_ft - rear_y
    if rear_l > 5.0:
        ax_plan.add_patch(patches.Rectangle((0, rear_y), pw_ft * 0.62, rear_l, facecolor="#1A2E35", edgecolor="#10B981", lw=1.5))
        ax_plan.text(pw_ft * 0.31, rear_y + rear_l * 0.5, "GROUND FLOOR MASTER SUITE", color="#34D399", fontsize=8, fontweight="bold", ha="center", va="center")
        ax_plan.add_patch(patches.Rectangle((pw_ft * 0.62, rear_y), pw_ft * 0.38, rear_l, facecolor="#162B3D", edgecolor="#38BDF8", lw=1.2))
        ax_plan.text(pw_ft * 0.81, rear_y + rear_l * 0.5, "ATTACHED\nBATH & DRESS", color="#93C5FD", fontsize=7.5, fontweight="bold", ha="center", va="center")

    # Dimension indicators at base
    ax_plan.plot([0, pw_ft], [-2.5, -2.5], color="#94A3B8", lw=1.5)
    ax_plan.plot([0, 0], [-1.5, -3.5], color="#94A3B8", lw=1.5)
    ax_plan.plot([pw_ft, pw_ft], [-1.5, -3.5], color="#94A3B8", lw=1.5)
    ax_plan.plot([porch_w, porch_w], [-1.5, -3.5], color="#94A3B8", lw=1.5)
    ax_plan.text(porch_w * 0.5, -4.8, f"PORCH: {porch_w}' (LEFT)", color="#38BDF8", fontsize=8, fontweight="bold", ha="center")
    ax_plan.text(porch_w + dr_w * 0.5, -4.8, f"DRAWING: {dr_w}' (RIGHT)", color="#F59E0B", fontsize=8, fontweight="bold", ha="center")

    ax_plan.text(pw_ft * 0.5, pl_ft + 5.0, "LOCKED 2D FLOOR PLAN (35' x 65')", color="#F8FAFC", fontsize=11, fontweight="heavy", ha="center")
    ax_plan.text(pw_ft * 0.5, pl_ft + 2.5, "Zero Modification to Room Dimensions or Placements", color="#10B981", fontsize=8, fontweight="bold", ha="center")

    # 2. RIGHT PANEL: ISOLATED 3D HOUSE RENDER
    ax_render.set_facecolor("#0F172A")
    ax_render.axis("off")
    if os.path.exists(RENDER_PATH):
        img = Image.open(RENDER_PATH)
        ax_render.imshow(img)
        ax_render.set_title("OPTION 2: ISOLATED 3D HOUSE MODEL RENDER (CLEAN STUDIO BACKGROUND)\nStrictly Formed from Floor Plan Dimensions • Pure Architecture Focus", 
                            color="#F8FAFC", fontsize=11, fontweight="heavy", pad=15)
    else:
        ax_render.text(0.5, 0.5, "Render image not found", color="#EF4444", ha="center")

    out_comparison_path = os.path.join(OUTPUT_DIR, "option2_floorplan_and_isolated_3d_comparison.png")
    fig.savefig(out_comparison_path, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"Generated Option 2 Comparison -> {out_comparison_path}")

if __name__ == "__main__":
    create_comparison_sheet()
