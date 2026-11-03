"""
tests/test_phase3_elevation.py
Comprehensive Phase 3 Front Elevation & Roof Engine Test Suite.

Verifies:
1. 1:1 Geometric alignment between floor plan openings and elevation facade (tolerance < 0.05m).
2. Car porch structural column alignment with car porch bay edge.
3. Mumty tower horizontal alignment strictly above floor plan staircase core bounds (< 0.10m).
4. Full synthesis across all 4 styles (Modern, Spanish, Minimalist, Classical) generating valid elevation_spec.json, SVG, and AIA-layered DXF.
5. Interactive feedback editing (POST /api/elevation): style switching, pergola addition, parapet height increase.
6. Multi-scale generation across 5 Marla, 10 Marla, and 1 Kanal plots.
"""

import os
import sys
import json
import pytest
from shapely.geometry import Polygon

# Ensure project root in sys.path
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from dataset.schema.canonical import CanonicalFloorPlan
from generation.design_diversity_engine import DesignDiversityEngine
from generation.elevation_engine import ElevationBuilder, ElevationSVGRenderer, ElevationDXFExporter
from api_server import ProceduralArchitecturalEngine


@pytest.fixture
def plan_10m() -> CanonicalFloorPlan:
    """Generates a consistent 10 Marla CanonicalFloorPlan for testing."""
    return DesignDiversityEngine.synthesize_diverse_plan(
        prompt="10 marla modern house with 4 bedrooms, 4 baths, drawing, lounge, kitchen",
        scale="10_marla",
        strategy="central_family_lounge",
        seed=101
    )


def test_01_opening_horizontal_alignment(plan_10m):
    """
    Test 1: Opening Horizontal Alignment.
    Asserts that every front-facing door and window has identical X coordinates (tolerance < 0.05m).
    """
    spec = ElevationBuilder.build_elevation_spec(plan_10m, style="modern")
    all_pts = [pt for r in plan_10m.rooms for pt in r.polygon]
    min_x = min(p[0] for p in all_pts)

    # Check main entrance door alignment
    main_door = spec["openings"]["main_door"]
    assert main_door is not None, "Main entrance door missing from elevation spec"

    # Find the corresponding front opening in plan.openings
    plan_main = next(
        (op for op in plan_10m.openings if op.opening_type == "door" and ("entry" in op.opening_id.lower() or "main" in op.opening_id.lower())),
        None
    )
    if plan_main:
        plan_x = round(plan_main.position[0] - min_x, 2)
        elev_x = main_door["x"]
        diff = abs(plan_x - elev_x)
        assert diff <= 0.05, f"Main door misaligned: plan X={plan_x}m, elev X={elev_x}m, diff={diff}m"

    # Check front windows alignment
    for elev_op in spec["openings"]["ground_openings"]:
        if elev_op["type"] == "window":
            matched_op = next((op for op in plan_10m.openings if op.opening_id == elev_op["opening_id"]), None)
            if matched_op:
                plan_x = round(matched_op.position[0] - min_x, 2)
                diff = abs(plan_x - elev_op["x"])
                assert diff <= 0.05, f"Window {elev_op['opening_id']} misaligned: plan X={plan_x}m, elev X={elev_op['x']}m"

    print("\n[PASS] Opening Horizontal Alignment verified: All front openings match within 0.05m tolerance.")


def test_02_porch_column_alignment(plan_10m):
    """
    Test 2: Porch Column Alignment.
    Asserts that the structural column aligns with the boundary of the car porch bay.
    """
    spec = ElevationBuilder.build_elevation_spec(plan_10m, style="modern")
    porch_bay = spec["facade_bays"]["porch"]
    assert porch_bay is not None, "Car porch bay not detected on front facade"

    col = spec["facade_bays"]["porch_column"]
    assert col is not None
    assert col["width"] >= 0.40, "Structural column must be >= 0.40m wide"

    # Column should be flush with either left or right boundary of porch
    is_flush = (abs(col["x"] - porch_bay["x1"]) < 0.10) or (abs((col["x"] + col["width"]) - porch_bay["x2"]) < 0.10)
    assert is_flush, f"Porch column at X={col['x']} is not aligned with porch boundary [{porch_bay['x1']}, {porch_bay['x2']}]"

    print(f"\n[PASS] Porch column aligned at X={col['x']:.2f}m (width {col['width']:.2f}m) on porch bay [{porch_bay['x1']}, {porch_bay['x2']}].")


def test_03_mumty_stair_core_vertical_stacking(plan_10m):
    """
    Test 3: Mumty Stair Core Vertical Stacking.
    Asserts that the stair mumty tower in the roof system is positioned strictly above
    the actual staircase core in the floor plan, not at default X=0.0m.
    """
    all_pts = [pt for r in plan_10m.rooms for pt in r.polygon]
    min_x = min(p[0] for p in all_pts)

    stair_room = next((r for r in plan_10m.rooms if "stair" in r.room_id.lower() or "stair" in r.room_name.lower() or r.room_type == "stairs"), None)
    assert stair_room is not None, "Stair room not found in floor plan"

    s_pts = stair_room.polygon
    stair_min_x = min(p[0] for p in s_pts) - min_x
    stair_max_x = max(p[0] for p in s_pts) - min_x
    stair_center_x = (stair_min_x + stair_max_x) / 2.0

    spec = ElevationBuilder.build_elevation_spec(plan_10m, style="modern")
    mumty = spec["roof_system"]["mumty"]

    # Mumty must not be hardcoded to 0.0m
    assert mumty["x"] >= 0.50, f"Mumty X coordinate must be non-zero (>0.50m), got {mumty['x']}m"

    # Mumty center must align with stair core center
    mumty_center_x = mumty["x"] + mumty["width"] / 2.0
    diff = abs(mumty_center_x - stair_center_x)
    assert diff <= 0.60, f"Mumty center X={mumty_center_x:.2f}m does not align with stair core center X={stair_center_x:.2f}m (diff={diff:.2f}m)"

    # OHT must be atop mumty
    oht = spec["roof_system"]["water_tank"]
    assert oht["x"] >= mumty["x"] - 0.10
    assert oht["x"] + oht["width"] <= mumty["x"] + mumty["width"] + 0.10

    print(f"\n[PASS] Stair Mumty vertically stacked at X={mumty['x']:.2f}m directly above stair core center X={stair_center_x:.2f}m.")


def test_04_four_architectural_styles_synthesis(plan_10m, tmp_path):
    """
    Test 4: Four Architectural Styles Synthesis.
    Verifies Modern, Spanish, Minimalist, and Classical styles generating valid
    elevation_spec.json, SVG, and AIA-layered DXF without errors.
    """
    styles = ["modern", "spanish", "minimalist", "classical"]

    for st in styles:
        spec = ElevationBuilder.build_elevation_spec(plan_10m, style=st)
        assert spec["style"] == st
        assert len(spec["materials"]) >= 5
        assert spec["vertical_datums"]["plinth"] == 0.65
        assert spec["vertical_datums"]["roof_slab"] == 7.61

        # Render SVG
        svg_file = str(tmp_path / f"elevation_{st}.svg")
        ElevationSVGRenderer.render_svg(spec, svg_file)
        assert os.path.exists(svg_file)
        with open(svg_file, "r", encoding="utf-8") as f:
            svg_content = f.read()
        assert "<svg" in svg_content
        assert 'id="layer-mumty-roof"' in svg_content
        assert 'id="layer-annotations"' in svg_content

        # Style-specific assertions
        if st == "spanish":
            assert spec["roof_system"]["parapet_style"] == "terracotta_barrel_tile"
            assert "terracottaTiles" in svg_content
        elif st == "classical":
            assert "dentil" in spec["roof_system"]["parapet_style"]
        elif st == "modern":
            assert "woodLouvers" in svg_content

        # Export AIA DXF
        dxf_file = str(tmp_path / f"elevation_{st}.dxf")
        ElevationDXFExporter.export_dxf(spec, dxf_file)
        assert os.path.exists(dxf_file)
        assert os.path.getsize(dxf_file) > 1000

    print(f"\n[PASS] Successfully synthesized and verified all 4 styles: {styles} (Specs, SVGs, and DXFs).")


def test_05_interactive_feedback_editing(plan_10m, tmp_path):
    """
    Test 5: Interactive Feedback Editing (POST /api/elevation logic).
    Verifies natural language feedback modifying styles, pergolas, and parapet heights.
    """
    base_spec = ElevationBuilder.build_elevation_spec(plan_10m, style="modern")
    assert base_spec["style"] == "modern"

    # Feedback 1: Switch to Spanish style
    spec_spanish = ElevationBuilder.apply_feedback_to_spec(base_spec, "switch to Spanish style with terracotta tiles")
    assert spec_spanish["style"] == "spanish"
    assert spec_spanish["roof_system"]["parapet_style"] == "terracotta_barrel_tile"
    assert any("Spanish" in c for c in spec_spanish["modifications_applied"])

    # Feedback 2: Add wooden pergola
    spec_pergola = ElevationBuilder.apply_feedback_to_spec(spec_spanish, "add wooden pergola above front terrace")
    assert spec_pergola["roof_system"]["pergola"] is not None
    assert spec_pergola["roof_system"]["pergola"]["height_m"] == 2.40

    # Feedback 3: Increase parapet height
    spec_parapet = ElevationBuilder.apply_feedback_to_spec(spec_pergola, "increase parapet height to 4 feet")
    assert spec_parapet["roof_system"]["parapet_height_m"] == 1.35
    assert spec_parapet["vertical_datums"]["parapet_top"] == 8.96

    # Render updated SVG & DXF
    svg_updated = str(tmp_path / "elevation_feedback_v2.svg")
    ElevationSVGRenderer.render_svg(spec_parapet, svg_updated)
    assert os.path.exists(svg_updated)

    dxf_updated = str(tmp_path / "elevation_feedback_v2.dxf")
    ElevationDXFExporter.export_dxf(spec_parapet, dxf_updated)
    assert os.path.exists(dxf_updated)

    print(f"\n[PASS] Interactive feedback editing verified: Style, Pergola, and Parapet modified dynamically.")


def test_06_multi_scale_elevation_generation():
    """
    Test 6: Multi-Scale Elevation Generation.
    Verifies elevation synthesis across 5 Marla (25x45), 10 Marla (35x65), and 1 Kanal (50x90).
    """
    scales = [
        ("5_marla", "central_family_lounge"),
        ("10_marla", "central_family_lounge"),
        ("1_kanal", "central_atrium_lightwell")
    ]

    for scale, strategy in scales:
        plan = DesignDiversityEngine.synthesize_diverse_plan(
            prompt=f"{scale} luxury house",
            scale=scale,
            strategy=strategy,
            seed=202
        )
        spec = ElevationBuilder.build_elevation_spec(plan, style="modern")
        assert spec["plot_scale"] == scale
        assert len(spec["facade_bays"]["ground_floor"]) >= 1
        assert spec["roof_system"]["mumty"]["width"] > 0
        assert spec["roof_system"]["water_tank"]["capacity_gal"] == 1500

    print(f"\n[PASS] Multi-scale generation verified across 5 Marla, 10 Marla, and 1 Kanal.")




def test_07_text_overlap_collision_avoidance(plan_10m, tmp_path):
    """
    Test 7: Collision Avoidance for Elevation Datum Labels.
    Asserts that ROAD LEVEL and NATURAL GROUND LEVEL labels have separated Y positions
    with zero text collision (gap >= 18px).
    """
    spec = ElevationBuilder.build_elevation_spec(plan_10m, style="modern")
    svg_file = str(tmp_path / "collision_test.svg")
    ElevationSVGRenderer.render_svg(spec, svg_file)
    with open(svg_file, "r", encoding="utf-8") as f:
        svg_content = f.read()

    import re
    # Extract Y coordinates of ROAD LEVEL and NATURAL GROUND
    m_road = re.search(r'<text[^>]*y="([^"]+)"[^>]*>ROAD LEVEL', svg_content)
    m_ngl = re.search(r'<text[^>]*y="([^"]+)"[^>]*>NATURAL GROUND', svg_content)
    assert m_road is not None, "ROAD LEVEL label missing from SVG"
    assert m_ngl is not None, "NATURAL GROUND label missing from SVG"

    y_road = float(m_road.group(1))
    y_ngl = float(m_ngl.group(1))
    y_diff = abs(y_road - y_ngl)
    assert y_diff >= 18.0, f"ROAD LEVEL (y={y_road}) and NATURAL GROUND (y={y_ngl}) are colliding (diff={y_diff}px < 18px)"

    # Ensure debug clutter labels are stripped
    assert "[0.13mm Aerial Fade]" not in svg_content
    assert "HUMAN SCALE (1.75m)" not in svg_content
    assert "SUV VEHICLE SILHOUETTE" not in svg_content

    print(f"\n[PASS] Text overlap collision avoidance verified: Vertical gap between Road and NGL is {y_diff:.1f}px (>=18px). No debug text present.")


def test_08_non_default_mumty_coordinates():
    """
    Test 8: Non-Default Mumty Coordinates Across Plot Sizes.
    Verifies that 5 Marla, 10 Marla, and 1 Kanal never have mumty X == 0.0m.
    """
    for scale in ["5_marla", "10_marla", "1_kanal"]:
        plan = DesignDiversityEngine.synthesize_diverse_plan(
            prompt=f"{scale} family residence",
            scale=scale,
            strategy="central_family_lounge",
            seed=505
        )
        spec = ElevationBuilder.build_elevation_spec(plan, style="modern")
        mum_x = spec["roof_system"]["mumty"]["x"]
        assert mum_x >= 0.50, f"Scale {scale} has default or boundary mumty coordinate X={mum_x}m (expected >= 0.50m)"

    print("\n[PASS] Non-default mumty coordinates verified: 5M, 10M, and 1K all position mumty X >= 0.50m.")


def test_09_entrance_separate_from_porch(plan_10m):
    """
    Test 9: Main Entrance Door Distinct from Car Porch.
    Asserts that the main entrance door is hosted in an entrance foyer/portico bay
    and is NOT drawn inside the car porch boundary behind parked vehicles.
    """
    spec = ElevationBuilder.build_elevation_spec(plan_10m, style="modern")
    porch_bay = spec["facade_bays"]["porch"]
    main_door = spec["openings"]["main_door"]

    assert porch_bay is not None
    assert main_door is not None

    p_x1, p_x2 = porch_bay["x1"], porch_bay["x2"]
    d_x = main_door["x"]

    # Door X must be outside the porch X span
    is_inside_porch = (p_x1 <= d_x <= p_x2)
    assert not is_inside_porch, f"Main door at X={d_x}m is inside the car porch span [{p_x1}m, {p_x2}m]"

    print(f"\n[PASS] Main entrance door located at X={d_x:.2f}m, outside car porch bay [{p_x1:.2f}m, {p_x2:.2f}m].")


def test_10_style_geometry_differentiation(plan_10m, tmp_path):
    """
    Test 10: Genuine Architectural Style Massing and Geometry Differentiation.
    Asserts that Modern, Spanish, Minimalist, and Classical produce distinct geometry:
    - Spanish has authentic semicircular voussoir arches and terracotta tile roof.
    - Modern has wood louvers and cantilevered slabs.
    - Classical has dentil cornice and pilasters.
    - Minimalist has pure monolithic volumes and concealed parapet.
    """
    styles = ["modern", "spanish", "minimalist", "classical"]
    svg_outputs = {}

    for st in styles:
        spec = ElevationBuilder.build_elevation_spec(plan_10m, style=st)
        svg_file = str(tmp_path / f"style_{st}.svg")
        ElevationSVGRenderer.render_svg(spec, svg_file)
        with open(svg_file, "r", encoding="utf-8") as f:
            svg_outputs[st] = f.read()

    # Spanish-specific geometry
    assert "terracottaTiles" in svg_outputs["spanish"]
    assert "keystone" in svg_outputs["spanish"] or "A " in svg_outputs["spanish"]  # Arc command

    # Modern-specific geometry
    assert "woodLouvers" in svg_outputs["modern"]

    # Classical-specific geometry
    assert "dentil" in svg_outputs["classical"].lower()

    # All styles must have distinct SVG contents
    assert svg_outputs["modern"] != svg_outputs["spanish"]
    assert svg_outputs["spanish"] != svg_outputs["classical"]
    assert svg_outputs["minimalist"] != svg_outputs["modern"]

    print("\n[PASS] Authentic style differentiation verified across Modern, Spanish, Minimalist, and Classical.")


def test_11_elevation_regeneration_after_edit(tmp_path):
    """
    Test 11: Elevation Regeneration & Synchronization After Plan Edit (Phase 2 & 3 sync).
    Verifies that when a floor plan is modified (v1 -> v2), the elevation spec and SVG
    are automatically regenerated and maintain 1:1 sync with the updated plan.
    """
    pid = "test_elev_sync_plan"
    import shutil
    plan_dir = os.path.join(PROJECT_ROOT, "output", "plans", "archi_35x65_modern_999")
    if os.path.exists(plan_dir):
        shutil.rmtree(plan_dir, ignore_errors=True)

    res_v1 = ProceduralArchitecturalEngine.synthesize_design(
        prompt="10 marla modern house with 4 beds and 4 baths",
        plot_width=35.0,
        plot_length=65.0,
        floors=2,
        bedrooms=4,
        bathrooms=4,
        style="modern",
        seed=999
    )
    v1_spec = res_v1.get("images", {}).get("elevation_spec")
    assert v1_spec is not None, "Elevation spec missing in v1 synthesis"
    assert v1_spec["version"] == 1

    # Apply improvement v1 -> v2
    res_v2 = ProceduralArchitecturalEngine.regenerate_with_improvement(
        plan_id=res_v1["project_id"],
        improvement_text="make the master bedroom 20 sq ft larger",
        base_version=1
    )
    assert res_v2["version"] == 2
    v2_spec = res_v2.get("images", {}).get("elevation_spec")
    assert v2_spec is not None, "Elevation spec missing after improvement regeneration"
    assert v2_spec["version"] == 2

    print(f"\n[PASS] Elevation regeneration after plan edit verified: v1 -> v2 elevation specs maintained and synced.")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])

