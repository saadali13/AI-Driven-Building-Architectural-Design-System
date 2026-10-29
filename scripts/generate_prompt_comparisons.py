r"""
Generates coordinated verification sheets comparing the 3-floor floorplans with the isolated 3D renders
for both Prompt 1 (10 Marla 8-bed) and Prompt 2 (1 Kanal 12-bed).
"""

import os
from PIL import Image
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_OUTPUT = os.path.join(PROJECT_ROOT, "output", "advanced_testing_prompts_10m_and_1k")

def create_prompt1_comparison():
    dir_p1 = os.path.join(BASE_OUTPUT, "prompt_1_10_marla_8bed_3floor")
    plan_img_path = os.path.join(dir_p1, "prompt1_10marla_8bed_3floor_complete_blueprints.png")
    render_img_path = os.path.join(dir_p1, "prompt1_10marla_8bed_3floor_modern_3d_render.jpg")

    fig = plt.figure(figsize=(24, 11), dpi=200)
    fig.patch.set_facecolor("#FFFFFF")

    gs = fig.add_gridspec(2, 1, height_ratios=[1.1, 1.2], hspace=0.15)
    ax_top = fig.add_subplot(gs[0, 0])
    ax_bot = fig.add_subplot(gs[1, 0])

    if os.path.exists(plan_img_path):
        im_plan = Image.open(plan_img_path)
        ax_top.imshow(im_plan)
        ax_top.axis("off")
        ax_top.set_title("PROMPT 1: 10 MARLA (35'x65') 3-STOREY COMPLETE BLUEPRINTS (8 BEDS ALL EN-SUITE)\nLevel 1: Ground Floor (2 Beds) • Level 2: First Floor (4 Beds) • Level 3: Rooftop Penthouse (2 Beds)",
                         fontsize=12, fontweight="heavy", color="#0F172A", pad=10)

    if os.path.exists(render_img_path):
        im_render = Image.open(render_img_path)
        ax_bot.imshow(im_render)
        ax_bot.axis("off")
        ax_bot.set_title("MATCHING ISOLATED 3D EXTERIOR MODEL RENDER (CLEAN STUDIO PODIUM)\nStrictly Conforming to Floor Plan: Double Car Porch (Left) • Travertine Drawing Room (Right) • Cantilever Bedroom (1F) • Rooftop Pergola (2F)",
                         fontsize=12, fontweight="heavy", color="#0F172A", pad=10)

    out_p1 = os.path.join(dir_p1, "prompt1_complete_floorplan_and_3d_comparison.png")
    fig.savefig(out_p1, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
    plt.close(fig)
    print(f"[SUCCESS] Generated Prompt 1 Full Comparison -> {out_p1}")


def create_prompt2_comparison():
    dir_p2 = os.path.join(BASE_OUTPUT, "prompt_2_1_kanal_12bed_3floor")
    plan_img_path = os.path.join(dir_p2, "prompt2_1kanal_12bed_3floor_complete_blueprints.png")
    render_img_path = os.path.join(dir_p2, "prompt2_1kanal_12bed_3floor_luxury_3d_render.jpg")

    fig = plt.figure(figsize=(24, 11), dpi=200)
    fig.patch.set_facecolor("#FFFFFF")

    gs = fig.add_gridspec(2, 1, height_ratios=[1.1, 1.2], hspace=0.15)
    ax_top = fig.add_subplot(gs[0, 0])
    ax_bot = fig.add_subplot(gs[1, 0])

    if os.path.exists(plan_img_path):
        im_plan = Image.open(plan_img_path)
        ax_top.imshow(im_plan)
        ax_top.axis("off")
        ax_top.set_title("PROMPT 2: 1 KANAL (50'x90') 3-STOREY COMPLETE BLUEPRINTS (12 BEDS ALL EN-SUITE)\nLevel 1: Ground Floor (4 Beds) • Level 2: First Floor (4 Beds) • Level 3: Rooftop Penthouse (4 Beds)",
                         fontsize=12, fontweight="heavy", color="#0F172A", pad=10)

    if os.path.exists(render_img_path):
        im_render = Image.open(render_img_path)
        ax_bot.imshow(im_render)
        ax_bot.axis("off")
        ax_bot.set_title("MATCHING ISOLATED 3D EXTERIOR MODEL RENDER (CLEAN STUDIO PODIUM)\nStrictly Conforming to Floor Plan: Triple Car Porch (Left) • Double-Height Portico • Travertine Drawing Room (Right) • Lawn (Front) • Rooftop Pergola (2F)",
                         fontsize=12, fontweight="heavy", color="#0F172A", pad=10)

    out_p2 = os.path.join(dir_p2, "prompt2_complete_floorplan_and_3d_comparison.png")
    fig.savefig(out_p2, bbox_inches="tight", facecolor="#FFFFFF", edgecolor="none")
    plt.close(fig)
    print(f"[SUCCESS] Generated Prompt 2 Full Comparison -> {out_p2}")

if __name__ == "__main__":
    create_prompt1_comparison()
    create_prompt2_comparison()
