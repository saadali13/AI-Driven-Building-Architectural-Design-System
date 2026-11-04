import time, os, json
os.environ['MPLCONFIGDIR'] = 'C:/Users/m/AppData/Local/Temp'
from generation.design_diversity_engine import DesignDiversityEngine
from generation.strategy_selector import StrategySelector
from generation.quality_gate import FloorPlanQualityGate
from generation.visualizer import FloorPlanVisualizer
from generation.elevation_engine.elevation_builder import ElevationBuilder
from generation.elevation_engine.elevation_svg_renderer import ElevationSVGRenderer
from generation.elevation_engine.elevation_dxf_exporter import ElevationDXFExporter
from generation.floor_plan_to_elevation_mapper import FloorPlanToElevationMapper
from generation.compliance_engine import RequirementsComplianceEngine
from api_server import ProceduralArchitecturalEngine

plots = [
    ('3 Marla', 18.0, 37.5, '3_marla', '3 Marla modern house 3 bed', 'modern'),
    ('5 Marla', 25.0, 45.0, '5_marla', '5 Marla modern house 3 bed', 'modern'),
    ('10 Marla', 35.0, 65.0, '10_marla', '10 Marla modern house 4 bed 4 bath tv lounge', 'modern'),
    ('1 Kanal', 50.0, 90.0, '1_kanal', '1 Kanal modern luxury villa 5 bed', 'modern'),
]

os.makedirs('output/benchmark_scratch/floors', exist_ok=True)
results = {}

for name, w, l, scale, prompt, style in plots:
    # 1. Parse
    t0 = time.perf_counter()
    parsed = ProceduralArchitecturalEngine._parse_prompt_text(prompt)
    stated_reqs = RequirementsComplianceEngine.parse_stated_requirements(prompt, {'plot_width': w, 'plot_length': l, 'floors': 2, 'bedrooms': 4, 'bathrooms': 4, 'style': style})
    t_parse = time.perf_counter() - t0

    # 2. Strategy selection
    t0 = time.perf_counter()
    top_strats = StrategySelector.select_top_3_distinct_strategies(prompt=prompt, scale=scale, plot_width=w, plot_length=l, style=style)
    chosen_strat = top_strats[0]['strategy_id']
    t_strat = time.perf_counter() - t0

    # 3. Solve (diverse engine)
    t0 = time.perf_counter()
    plan = DesignDiversityEngine.synthesize_diverse_plan(prompt=prompt, scale=scale, strategy=chosen_strat, seed=1)
    t_solve = time.perf_counter() - t0

    # 4. Quality gate
    t0 = time.perf_counter()
    qg_eval = FloorPlanQualityGate.evaluate(plan)
    t_qg = time.perf_counter() - t0

    # 5. Blueprint Vector SVG
    t0 = time.perf_counter()
    # Mock / extract vector SVG string
    t_svg = time.perf_counter() - t0

    # 6. Elevation Spec & SVG
    t0 = time.perf_counter()
    spec = ElevationBuilder.build_elevation_spec(plan, style=style)
    elev_svg = ElevationSVGRenderer.render_svg(spec, 'output/benchmark_scratch/elev.svg')
    t_elev_svg = time.perf_counter() - t0

    # 7. 3D Spatial Volumes
    t0 = time.perf_counter()
    all_floors = ProceduralArchitecturalEngine._convert_canonical_to_floors(plan, w, l)
    three_d = ProceduralArchitecturalEngine._generate_3d_geometry(all_floors, w, l, style)
    t_3d = time.perf_counter() - t0

    # 8. DXF Export
    t0 = time.perf_counter()
    ElevationDXFExporter.export_dxf(spec, 'output/benchmark_scratch/elev.dxf')
    t_dxf = time.perf_counter() - t0

    # 9. Matplotlib Elevation PNG
    t0 = time.perf_counter()
    FloorPlanToElevationMapper.map_and_render_elevation(plan, 'output/benchmark_scratch/elev.png', style=style)
    t_elev_png = time.perf_counter() - t0

    # 10. Matplotlib Floor Plan PNGs
    t0 = time.perf_counter()
    FloorPlanVisualizer.render_all_floors(plan, 'output/benchmark_scratch/floors')
    t_floor_png = time.perf_counter() - t0

    results[name] = {
        "parse_ms": round(t_parse * 1000, 2),
        "strategy_ms": round(t_strat * 1000, 2),
        "chosen_strategy": chosen_strat,
        "solve_ms": round(t_solve * 1000, 2),
        "quality_gate_ms": round(t_qg * 1000, 2),
        "elev_svg_ms": round(t_elev_svg * 1000, 2),
        "three_d_ms": round(t_3d * 1000, 2),
        "core_total_s": round(t_parse + t_strat + t_solve + t_qg + t_elev_svg + t_3d, 3),
        "dxf_ms": round(t_dxf * 1000, 2),
        "elev_png_s": round(t_elev_png, 3),
        "floor_png_s": round(t_floor_png, 3),
        "synchronous_total_s": round(t_parse + t_strat + t_solve + t_qg + t_elev_svg + t_3d + t_dxf + t_elev_png + t_floor_png, 3)
    }

print(json.dumps(results, indent=2))
