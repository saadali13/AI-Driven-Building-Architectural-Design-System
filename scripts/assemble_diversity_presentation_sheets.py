r"""
Composite Presentation Sheet & Diversity Proof Generator
For 10 Marla 3-Storey 7-Bedroom (All En-suite) + Dirty Kitchen + Laundry + Powder + U-Stairs + BBQ Section
"""

import os
import shutil
from PIL import Image, ImageDraw, ImageFont

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
BASE_DIR = os.path.join(PROJECT_ROOT, "output", "10_marla_3floor_7bed_diversity_suite")
OPT_A_DIR = os.path.join(BASE_DIR, "design_option_A_minimalist_cantilever")
OPT_B_DIR = os.path.join(BASE_DIR, "design_option_B_cubist_splayed")

SRC_3D_A = r"C:\Users\m\.gemini\antigravity-ide\brain\e418f240-ca20-40a8-9964-94fe92ef6200\opt_a_10m_3flr_7bed_3d_1791885558079.jpg"
SRC_3D_B = r"C:\Users\m\.gemini\antigravity-ide\brain\e418f240-ca20-40a8-9964-94fe92ef6200\opt_b_10m_3flr_7bed_3d_1791885581465.jpg"

DEST_3D_A = os.path.join(OPT_A_DIR, "option_A_isolated_3d_render.jpg")
DEST_3D_B = os.path.join(OPT_B_DIR, "option_B_isolated_3d_render.jpg")

shutil.copyfile(SRC_3D_A, DEST_3D_A)
shutil.copyfile(SRC_3D_B, DEST_3D_B)
print(f"Copied Option A 3D -> {DEST_3D_A}")
print(f"Copied Option B 3D -> {DEST_3D_B}")

def create_option_presentation_sheet(opt_name, opt_dir, plan_file, elev_file, render_3d_file, out_file, title_text, subtitle_text):
    img_plan = Image.open(os.path.join(opt_dir, plan_file))
    img_elev = Image.open(os.path.join(opt_dir, elev_file))
    img_3d = Image.open(os.path.join(opt_dir, render_3d_file))

    # Target width 3600 px
    w_sheet = 3600
    header_h = 240
    
    # Scale plan to full width
    plan_w = w_sheet - 100
    plan_h = int(img_plan.height * (plan_w / img_plan.width))
    img_plan_resized = img_plan.resize((plan_w, plan_h), Image.Resampling.LANCZOS)

    # Lower section: 2 columns (Elevation on left, 3D on right)
    col_w = int((w_sheet - 150) / 2)
    elev_h = int(img_elev.height * (col_w / img_elev.width))
    r3d_h = int(img_3d.height * (col_w / img_3d.width))
    lower_h = max(elev_h, r3d_h)

    img_elev_resized = img_elev.resize((col_w, elev_h), Image.Resampling.LANCZOS)
    img_3d_resized = img_3d.resize((col_w, r3d_h), Image.Resampling.LANCZOS)

    total_h = header_h + plan_h + lower_h + 160
    sheet = Image.new("RGB", (w_sheet, total_h), "#FFFFFF")
    draw = ImageDraw.Draw(sheet)

    # Header bar
    draw.rectangle([0, 0, w_sheet, 16], fill="#0284C7")
    draw.text((60, 45), title_text, fill="#0F172A", font_size=54)
    draw.text((60, 115), subtitle_text, fill="#475569", font_size=32)
    draw.text((60, 165), "PROGRAM: 7 BEDS (ALL EN-SUITE) • DOUBLE GARAGE • DRAWING • LIVING • DIRTY KITCHEN • LAUNDRY • POWDER • U-STAIRS • ROOFTOP BBQ PERGOLA", fill="#B45309", font_size=24)
    draw.line([(60, 215), (w_sheet - 60, 215)], fill="#CBD5E1", width=2)

    # Paste Plans
    y_cursor = header_h + 10
    sheet.paste(img_plan_resized, (50, y_cursor))

    # Section divider
    y_cursor += plan_h + 30
    draw.line([(60, y_cursor), (w_sheet - 60, y_cursor)], fill="#E2E8F0", width=2)
    draw.text((60, y_cursor + 15), "TECHNICAL 2D FRONT ELEVATION (CLEAN WHITE THEME + DATUMS)", fill="#0F172A", font_size=32)
    draw.text((col_w + 100, y_cursor + 15), "COORDINATED ISOLATED 3D HOUSE MODEL RENDER (STUDIO PODIUM)", fill="#0F172A", font_size=32)
    y_cursor += 75

    # Paste Elevation & 3D
    sheet.paste(img_elev_resized, (50, y_cursor))
    sheet.paste(img_3d_resized, (col_w + 100, y_cursor))

    out_path = os.path.join(opt_dir, out_file)
    sheet.save(out_path, quality=95)
    print(f"Generated Presentation Sheet -> {out_path}")
    return out_path

# 1. Sheet Option A
create_option_presentation_sheet(
    "Option A",
    OPT_A_DIR,
    "option_A_complete_3floor_blueprints.png",
    "option_A_front_elevation_2d.png",
    "option_A_isolated_3d_render.jpg",
    "option_A_complete_presentation_sheet.png",
    "10 MARLA LUXURY 3-STOREY RESIDENCE — DESIGN OPTION A (MINIMALIST CANTILEVER)",
    "Spatial Configuration: Left Double Garage • Right Formal Drawing • Left 1F Cantilever Box • Left Rooftop BBQ Pergola"
)

# 2. Sheet Option B
create_option_presentation_sheet(
    "Option B",
    OPT_B_DIR,
    "option_B_complete_3floor_blueprints.png",
    "option_B_front_elevation_2d.png",
    "option_B_isolated_3d_render.jpg",
    "option_B_complete_presentation_sheet.png",
    "10 MARLA LUXURY 3-STOREY RESIDENCE — DESIGN OPTION B (CUBIST SPLAYED MODERN)",
    "Spatial Configuration: Right Double Garage • Left Corner Drawing • Floating Rectilinear Frame • Right Rooftop BBQ Pergola"
)

# 3. Master Side-by-Side Diversity Comparison Sheet
def create_master_diversity_comparison():
    sheet_a = Image.open(os.path.join(OPT_A_DIR, "option_A_isolated_3d_render.jpg"))
    sheet_b = Image.open(os.path.join(OPT_B_DIR, "option_B_isolated_3d_render.jpg"))
    elev_a = Image.open(os.path.join(OPT_A_DIR, "option_A_front_elevation_2d.png"))
    elev_b = Image.open(os.path.join(OPT_B_DIR, "option_B_front_elevation_2d.png"))

    w = 3600
    h = 2400
    canvas = Image.new("RGB", (w, h), "#FFFFFF")
    draw = ImageDraw.Draw(canvas)

    # Header
    draw.rectangle([0, 0, w, 16], fill="#16A34A")
    draw.text((60, 45), "MASTER DIVERSITY VERIFICATION: 10 MARLA 3-FLOOR 7-BEDROOM RESIDENCE", fill="#0F172A", font_size=56)
    draw.text((60, 118), "Proof of Dynamic Generation: Different Floor Plans, Different Room Typologies & Completely Different Front Elevations", fill="#0284C7", font_size=32)
    draw.line([(60, 180), (w - 60, 180)], fill="#CBD5E1", width=2)

    col_w = int((w - 180) / 2)
    
    # Left Column: OPTION A
    draw.text((60, 205), "OPTION A: ASYMMETRIC CANTILEVER FACADE", fill="#0F172A", font_size=38)
    draw.text((60, 255), "Left Car Porch | Right Drawing Room | Fluted Wood Box | Left BBQ Pergola", fill="#64748B", font_size=24)
    r_a = sheet_a.resize((col_w, int(sheet_a.height * (col_w / sheet_a.width))), Image.Resampling.LANCZOS)
    canvas.paste(r_a, (60, 300))

    e_a_h = int(elev_a.height * (col_w / elev_a.width))
    e_a = elev_a.resize((col_w, e_a_h), Image.Resampling.LANCZOS)
    canvas.paste(e_a, (60, 300 + r_a.height + 40))

    # Right Column: OPTION B
    col_x_b = col_w + 120
    draw.text((col_x_b, 205), "OPTION B: CUBIST SPLAYED MODERN FACADE", fill="#0F172A", font_size=38)
    draw.text((col_x_b, 255), "Right Car Porch | Left Corner Glazing | Floating White Frame | Right BBQ Pergola", fill="#64748B", font_size=24)
    r_b = sheet_b.resize((col_w, int(sheet_b.height * (col_w / sheet_b.width))), Image.Resampling.LANCZOS)
    canvas.paste(r_b, (col_x_b, 300))

    e_b_h = int(elev_b.height * (col_w / elev_b.width))
    e_b = elev_b.resize((col_w, e_b_h), Image.Resampling.LANCZOS)
    canvas.paste(e_b, (col_x_b, 300 + r_b.height + 40))

    out_comp = os.path.join(BASE_DIR, "master_diversity_side_by_side_comparison_sheet.png")
    canvas.save(out_comp, quality=95)
    print(f"Generated Master Diversity Comparison -> {out_comp}")
    return out_comp

create_master_diversity_comparison()
print("All composite sheets and diversity proof successfully generated!")
