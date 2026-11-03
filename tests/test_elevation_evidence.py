import os, sys, re, pytest, json
os.environ['MPLCONFIGDIR'] = 'C:/Users/m/AppData/Local/Temp'
from generation.design_diversity_engine import DesignDiversityEngine
from generation.elevation_engine.elevation_builder import ElevationBuilder
from generation.elevation_engine.elevation_svg_renderer import ElevationSVGRenderer
from generation.elevation_engine.elevation_dxf_exporter import ElevationDXFExporter
from generation.floor_plan_to_elevation_mapper import FloorPlanToElevationMapper
from generation.plan_edit_applier import PlanEditApplier
from dataset.schema.canonical import CanonicalFloorPlan

def test_elevation_10m_individual_renders():
    os.makedirs('output/elevations_10m', exist_ok=True)
    styles = ['modern', 'spanish', 'minimalist', 'classical']
    plan_10m = DesignDiversityEngine.synthesize_diverse_plan(
        prompt='10 marla modern house 4 bed',
        scale='10_marla',
        strategy='central_family_lounge',
        seed=1
    )
    for style in styles:
        spec = ElevationBuilder.build_elevation_spec(plan_10m, style=style)
        svg_path = f'output/elevations_10m/10m_{style}.svg'
        png_path = f'output/elevations_10m/10m_{style}.png'
        dxf_path = f'output/elevations_10m/10m_{style}.dxf'
        ElevationSVGRenderer.render_svg(spec, svg_path)
        ElevationDXFExporter.export_dxf(spec, dxf_path)
        FloorPlanToElevationMapper.map_and_render_elevation(
            plan_10m, png_path, style=style, project_title=f'10 Marla {style.capitalize()} Residence'
        )
        assert os.path.exists(svg_path) and os.path.getsize(svg_path) > 1000
        assert os.path.exists(png_path) and os.path.getsize(png_path) > 10000
        assert os.path.exists(dxf_path) and os.path.getsize(dxf_path) > 5000

def test_mumty_stair_strict_offset_tolerance():
    """Item 2(a): Mumty x-range must match stair core footprint within <= 0.15m tolerance."""
    plot_configs = [
        ('5 Marla', '5_marla', 'central_family_lounge'),
        ('10 Marla', '10_marla', 'central_family_lounge'),
        ('1 Kanal', '1_kanal', 'central_atrium_lightwell'),
    ]
    for name, sc, strat in plot_configs:
        p = DesignDiversityEngine.synthesize_diverse_plan(prompt=f'{name} house', scale=sc, strategy=strat, seed=1)
        stairs = [r for r in p.rooms if 'stair' in str(r.room_type).lower() or 'stair' in str(r.room_name).lower()]
        assert len(stairs) > 0, f"No stairs found in {name}"
        stair_x_min = round(min(pt[0] for r in stairs for pt in r.polygon), 2)
        stair_x_max = round(max(pt[0] for r in stairs for pt in r.polygon), 2)
        stair_center = (stair_x_min + stair_x_max) / 2.0

        spec = ElevationBuilder.build_elevation_spec(p, style='modern')
        mumty = spec.get('roof_system', {}).get('mumty')
        assert mumty is not None, f"No stair_mumty in {name} elevation spec"
        mum_x = mumty['x']
        mum_w = mumty['width']
        mum_center = mum_x + mum_w / 2.0

        # Assert mumty start x matches stair core left wall within 0.15m
        assert abs(mum_x - stair_x_min) <= 0.15, (
            f"{name}: Mumty x={mum_x:.2f}m deviates from stair_x_min={stair_x_min:.2f}m by {abs(mum_x - stair_x_min):.2f}m (>0.15m)"
        )
        # Assert mumty center is aligned with stair core center within 0.15m
        assert abs(mum_center - stair_center) <= 0.15, (
            f"{name}: Mumty center={mum_center:.2f}m deviates from stair_center={stair_center:.2f}m by {abs(mum_center - stair_center):.2f}m (>0.15m)"
        )

def test_mumty_tracks_horizontal_stair_shift():
    """Item 2(b): After an edit moving stairs horizontally, mumty must move with it."""
    plan_10m = DesignDiversityEngine.synthesize_diverse_plan(
        prompt='10 marla modern house 4 bed',
        scale='10_marla',
        strategy='central_family_lounge',
        seed=1
    )
    stairs = [r for r in plan_10m.rooms if 'stair' in str(r.room_type).lower() or 'stair' in str(r.room_name).lower()]
    assert len(stairs) > 0
    orig_stair_x = min(pt[0] for r in stairs for pt in r.polygon)
    orig_spec = ElevationBuilder.build_elevation_spec(plan_10m, style='modern')
    orig_mumty_x = orig_spec['roof_system']['mumty']['x']

    # Shift stair horizontally by +2.5 meters
    shift_dx = 2.50
    for r in stairs:
        r.polygon = [[round(pt[0] + shift_dx, 2), pt[1]] for pt in r.polygon]

    shifted_spec = ElevationBuilder.build_elevation_spec(plan_10m, style='modern')
    shifted_mumty_x = shifted_spec['roof_system']['mumty']['x']

    assert abs(shifted_mumty_x - (orig_mumty_x + shift_dx)) <= 0.05, (
        f"Mumty did not track stair shift: expected {orig_mumty_x + shift_dx:.2f}m, got {shifted_mumty_x:.2f}m"
    )

def test_mumty_fails_on_missing_stairs():
    """Item 2(c): Fail if mumty position equals default/fallback value; must raise if stair absent."""
    plan_10m = DesignDiversityEngine.synthesize_diverse_plan(
        prompt='10 marla modern house 4 bed',
        scale='10_marla',
        strategy='central_family_lounge',
        seed=1
    )
    # Remove all stairs
    plan_no_stairs = plan_10m.model_copy(deep=True)
    plan_no_stairs.rooms = [r for r in plan_no_stairs.rooms if 'stair' not in str(r.room_type).lower() and 'stair' not in str(r.room_name).lower()]

    with pytest.raises(ValueError, match="Structural Alignment Failure"):
        ElevationBuilder.build_elevation_spec(plan_no_stairs, style='modern')

def test_style_geometry_uniqueness():
    """Item 3: Verify all 4 styles produce distinct geometric parapets and materials."""
    plan_10m = DesignDiversityEngine.synthesize_diverse_plan(
        prompt='10 marla modern house 4 bed',
        scale='10_marla',
        strategy='central_family_lounge',
        seed=1
    )
    styles = ['modern', 'spanish', 'minimalist', 'classical']
    specs = {s: ElevationBuilder.build_elevation_spec(plan_10m, style=s) for s in styles}

    for i in range(len(styles)):
        for j in range(i + 1, len(styles)):
            s1, s2 = styles[i], styles[j]
            r1, r2 = specs[s1]['roof_system']['parapet_style'], specs[s2]['roof_system']['parapet_style']
            assert r1 != r2, f"Styles '{s1}' and '{s2}' produced identical parapet_style '{r1}'"

            svg1 = ElevationSVGRenderer.render_svg(specs[s1], f'output/scratch_{s1}.svg')
            svg2 = ElevationSVGRenderer.render_svg(specs[s2], f'output/scratch_{s2}.svg')
            assert svg1 != svg2, f"SVG outputs for '{s1}' and '{s2}' are identical!"

def test_datum_callout_labels_anti_collision():
    """Item 3: Verify datum callout labels do not overlap (< 22px distance)."""
    plan_10m = DesignDiversityEngine.synthesize_diverse_plan(
        prompt='10 marla modern house 4 bed',
        scale='10_marla',
        strategy='central_family_lounge',
        seed=1
    )
    styles = ['modern', 'spanish', 'minimalist', 'classical']
    for st in styles:
        spec = ElevationBuilder.build_elevation_spec(plan_10m, style=st)
        svg_path = f'output/elevations_10m/test_anticollision_{st}.svg'
        ElevationSVGRenderer.render_svg(spec, svg_path)
        with open(svg_path, 'r', encoding='utf-8') as f:
            svg = f.read()

        # Find all datum callout texts on the right margin (x > 1000)
        # Pattern: <text x="1118..." y="420..." ...>LABEL</text>
        matches = re.findall(r'<text\s+x="(\d+(?:\.\d+)?)"\s+y="(\d+(?:\.\d+)?)"[^>]*>([A-Z\s]+)</text>', svg)
        datum_ys = []
        for x_str, y_str, label in matches:
            x, y = float(x_str), float(y_str)
            if x > 1000 and any(k in label for k in ['TOP', 'SLAB', 'FLOOR', 'PLINTH', 'GROUND']):
                datum_ys.append(y)

        datum_ys.sort()
        for k in range(len(datum_ys) - 1):
            gap = datum_ys[k+1] - datum_ys[k]
            assert gap >= 22.0, f"Style '{st}' datum text overlap detected! Gap between Y={datum_ys[k]} and Y={datum_ys[k+1]} is only {gap:.1f}px (< 22px)"
