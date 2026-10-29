"""
AI Architectural Floor Plan System - Master Pipeline CLI.
End-to-end pipeline orchestrating:
1. 'generate': Natural-language prompt -> CP-SAT layout -> Multi-floor DXF export -> 2D Blueprint Renders -> Blender 3D procedural solid + render.
2. 'dxf-to-canonical': AutoCAD DXF ingestion -> CanonicalFloorPlan -> Spatial relationship graph -> RAG doc.
"""

import os
import sys
import argparse
import json
from typing import Optional

from dataset.schema.canonical import CanonicalFloorPlan
from requirements.parser import NaturalLanguageRequirementsParser
from generation.solver import LayoutGenerator
from generation.validation import LayoutValidator
from generation.visualizer import FloorPlanVisualizer
from cad.dxf_generator import DXFGenerator
from cad.parser import DXFParser
from three_d.blender_generator import Blender3DGenerator
from dataset.rag_generator import ArchitecturalRAGGenerator
from generation.elevation_engine import ElevationEngine


def run_generation_pipeline(
    prompt: str,
    output_dir: str,
    render_3d: bool = True,
    export_format: str = "all",
    shape: Optional[str] = None,
    sides: Optional[str] = None,
    vertices: Optional[str] = None,
    unit: str = "ft",
    seed: Optional[int] = None,
    variant_index: Optional[int] = None,
    strategy: Optional[str] = None,
    num_variants: int = 1
):
    print("=" * 75)
    print("AI ARCHITECTURAL DESIGN & LAYOUT PIPELINE")
    print("=" * 75)

    is_irregular = bool(shape or sides or vertices)

    if num_variants > 1 and not is_irregular:
        print(f"\n[MULTI-VARIANT MODE] Synthesizing {num_variants} distinct alternatives for brief...")
        generated_plans = []
        from tools.measure_diversity import compare_plans
        cand_idx = 1 if variant_index is None else variant_index
        attempts = 0
        while len(generated_plans) < num_variants and attempts < 12:
            v_dir = os.path.join(output_dir, f"variant_{len(generated_plans) + 1}")
            cand_plan = run_generation_pipeline(
                prompt=prompt,
                output_dir=v_dir,
                render_3d=render_3d,
                export_format=export_format,
                unit=unit,
                seed=seed,
                variant_index=cand_idx,
                strategy=strategy,
                num_variants=1
            )
            cand_idx += 1
            attempts += 1
            if not cand_plan:
                continue
            is_distinct = True
            for prev_p in generated_plans:
                comp = compare_plans(prev_p, cand_plan)
                if comp["classification"] != "MEANINGFULLY DIFFERENT" or comp["composite_diversity_distance"] < 0.20:
                    is_distinct = False
                    break
            if is_distinct or len(generated_plans) == 0:
                generated_plans.append(cand_plan)
                print(f"      -> Accepted Distinct Option {len(generated_plans)}: {cand_plan.metadata.plan_id} (Strategy: {cand_plan.metadata.provenance.get('planning_strategy')})")
            else:
                print(f"      -> Rejection filter: candidate plan failed diversity threshold (D < 0.20), generating next alternative...")

        print(f"\n[MULTI-VARIANT COMPLETE] Successfully synthesized {len(generated_plans)} distinct variants in: {output_dir}")
        return generated_plans[0] if generated_plans else None

    if is_irregular:
        print(f"\n[1/5] Ingesting Non-Orthogonal / Irregular Site Geometry...")
        from requirements.site_geometry import SiteGeometryParser
        from generation.setback_engine import SetbackEngine
        from generation.irregular_solver import IrregularSiteSolver

        if vertices:
            site_boundary = SiteGeometryParser.from_vertex_string(vertices, unit=unit)
            print(f"      -> Ingested Cartesian Polygon: {len(site_boundary.vertices)-1} vertices (Unit: {unit})")
        elif sides and shape:
            parsed_nums = [float(x.strip()) for x in sides.split(",") if x.strip()]
            s_type = shape.lower().strip()
            if s_type == "triangle":
                if len(parsed_nums) != 3:
                    raise ValueError(f"Triangle preset requires 3 sides (front, left, hypotenuse), got {len(parsed_nums)}: {sides}")
                site_boundary = SiteGeometryParser.create_triangle(parsed_nums[0], parsed_nums[1], parsed_nums[2], unit=unit)
            elif s_type == "trapezoid":
                if len(parsed_nums) != 4:
                    raise ValueError(f"Trapezoid preset requires 4 sides (front, rear, left, right), got {len(parsed_nums)}: {sides}")
                site_boundary = SiteGeometryParser.create_trapezoid(parsed_nums[0], parsed_nums[1], parsed_nums[2], parsed_nums[3], unit=unit)
            elif s_type in ("corner_plot", "corner", "chamfer"):
                if len(parsed_nums) != 3:
                    raise ValueError(f"Corner plot preset requires 3 parameters (front, depth, splay), got {len(parsed_nums)}: {sides}")
                site_boundary = SiteGeometryParser.create_corner_plot(parsed_nums[0], parsed_nums[1], parsed_nums[2], unit=unit)
            elif s_type in ("square", "true_square"):
                if len(parsed_nums) == 1:
                    site_boundary = SiteGeometryParser.create_square(parsed_nums[0], parsed_nums[0], unit=unit)
                elif len(parsed_nums) >= 2:
                    site_boundary = SiteGeometryParser.create_square(parsed_nums[0], parsed_nums[1], unit=unit)
                else:
                    raise ValueError(f"Square preset requires 1 or 2 side lengths (e.g. '40,40' or '40'), got: {sides}")
            elif s_type in ("lshape", "l_shape", "l-shape", "notched"):
                if len(parsed_nums) != 4:
                    raise ValueError(
                        f"L-shape preset requires 4 parameters: front_width, total_depth, notch_width, notch_depth "
                        f"(e.g. --sides '40,60,15,20'). Got {len(parsed_nums)}: {sides}"
                    )
                site_boundary = SiteGeometryParser.create_lshape(
                    parsed_nums[0], parsed_nums[1], parsed_nums[2], parsed_nums[3], unit=unit
                )
            else:
                raise ValueError(f"Unsupported shape preset '{shape}'. Choose from: triangle, trapezoid, corner_plot, square, lshape.")
            print(f"      -> Ingested Preset [{shape.upper()}]: sides={sides} ({unit})")
        else:
            raise ValueError("Must provide either --vertices or both --shape and --sides for irregular site generation.")

        print(f"      -> Site Dimensions: Frontage {site_boundary.frontage_ft:.1f} ft, Depth {site_boundary.depth_ft:.1f} ft")
        print(f"      -> Gross Plot Area: {site_boundary.area_sqft:.1f} sq ft ({site_boundary.area_m2:.1f} m² | ~{site_boundary.plot_category})")

        print(f"\n[2/5] Applying Statutory Setbacks & Clipping Inward Envelope...")
        buildable_env = SetbackEngine.compute_buildable_envelope(site_boundary)
        print(f"      -> Legal Buildable Footprint: {buildable_env.area_sqft:.1f} sq ft ({buildable_env.poly_buildable.area:.1f} m²)")
        print(f"      -> Usable Site Coverage Ratio: {buildable_env.usable_coverage * 100.0:.1f}%")

        print(f"\n[3/5] Synthesizing Constrained Layout with IrregularSiteSolver...")
        solver = IrregularSiteSolver()
        plan = solver.synthesize(site_boundary, prompt=prompt)
        program = None

    else:
        print(f"\n[1/5] Parsing Natural-Language Architectural Requirements...")
        print(f"      Prompt: \"{prompt}\"")
        program = NaturalLanguageRequirementsParser.parse(prompt)
        print(f"      -> Project Title: {program.project_title}")
        if program.plot_size_desc:
            print(f"      -> Plot Specification: {program.plot_size_desc}")
        print(f"      -> Total Target Covered Area: {program.total_target_area_m2:.1f} m² ({program.total_target_area_m2 * 10.7639:.0f} sq ft)")
        print(f"      -> Floors: {program.floor_count} ({program.levels})")
        print(f"      -> Total Programmed Rooms: {len(program.rooms)} across {program.floor_count} floor(s)")
        print(f"      -> Programmed Spatial Adjacencies: {len(program.adjacencies)}")

        # Print breakdown by floor
        for lvl in program.levels:
            lvl_name = "Ground Floor" if lvl == 0 else ("First Floor" if lvl == 1 else f"Floor {lvl}")
            lvl_rooms = [r for r in program.rooms if r.level_index == lvl]
            print(f"         * {lvl_name} ({len(lvl_rooms)} spaces): {', '.join(r.room_name for r in lvl_rooms)}")

        # Check Program Feasibility Gate
        if not program.is_feasible:
            os.makedirs(output_dir, exist_ok=True)
            quality_report = {
                "plan_id": "INFEASIBLE_PROGRAM",
                "final_status": "INFEASIBLE_PROGRAM",
                "is_valid": False,
                "infeasibility_reasons": program.infeasibility_reasons,
                "failures": [
                    {
                        "code": "F13",
                        "severity": "CRITICAL",
                        "description": f"Infeasible Program: {reason}"
                    } for reason in program.infeasibility_reasons
                ],
                "summary": f"Requested architectural program is physically infeasible: {'; '.join(program.infeasibility_reasons)}"
            }
            quality_report_path = os.path.join(output_dir, "quality_report.json")
            with open(quality_report_path, "w", encoding="utf-8") as f:
                json.dump(quality_report, f, indent=2)

            print("\n" + "!" * 75)
            print("ARCHITECTURAL QUALITY GATE: [INFEASIBLE_PROGRAM]")
            print("!" * 75)
            for reason in program.infeasibility_reasons:
                print(f"   * {reason}")
            print(f"\n   -> Recorded rejection in: {quality_report_path}")
            print("!" * 75 + "\n")
            return None

        print(f"\n[2/5] Querying Hybrid RAG Matcher & Retrieving Real Blueprint Topology...")
        from generation.rag_matcher import RAGMatcher
        matcher = RAGMatcher("dataset/dataset_index.json")
        base_plan, match_source, sim_score = matcher.query_vector(program)
        print(f"      -> Retrieved Blueprint: {base_plan.metadata.plan_id} (Source: {match_source}, Similarity Score: {sim_score:.3f})")

        print(f"\n[3/5] Synthesizing & Adapting Boundaries with DatasetDrivenRAGSolver...")
        from generation.rag_solver import DatasetDrivenRAGSolver
        solver = DatasetDrivenRAGSolver()
        plan = solver.synthesize(
            prompt,
            strategy=strategy,
            alternative_index=variant_index,
            seed=seed
        )
        if plan and program and getattr(program, "statutory_red_note", None):
            plan.metadata.provenance["statutory_red_note"] = program.statutory_red_note
        if not plan:
            os.makedirs(output_dir, exist_ok=True)
            failed_report = {
                "plan_id": "GENERATION_FAILED",
                "final_status": "GENERATION_FAILED",
                "is_valid": False,
                "failures": [{"code": "F19", "severity": "CRITICAL", "description": "Solver could not find a feasible layout under specified constraints"}],
                "summary": "Generation failed within allowed solver attempts"
            }
            with open(os.path.join(output_dir, "quality_report.json"), "w", encoding="utf-8") as f:
                json.dump(failed_report, f, indent=2)
            print("[ERROR] Solver could not find a feasible layout under specified constraints.")
            return None

    # Step 4: Quality Gate evaluation
    print(f"\n[4/5] Executing Architectural Quality Gate (F01-F20 Compliance Checks)...")
    from generation.quality_gate import FloorPlanQualityGate
    quality_report = FloorPlanQualityGate.evaluate(plan, program)

    os.makedirs(output_dir, exist_ok=True)
    quality_report_path = os.path.join(output_dir, "quality_report.json")
    with open(quality_report_path, "w", encoding="utf-8") as f:
        json.dump(quality_report, f, indent=2)

    failures_list = quality_report.get("failures", quality_report.get("failure_details", []))
    score = quality_report.get("quality_score", 1.0)
    print(f"      -> Quality Gate Evaluation: {quality_report['final_status']} (Score: {score:.2f}, Failures: {len(failures_list)})")
    print(f"      -> Saved Quality Report to: {quality_report_path}")
    if quality_report["final_status"] == "FAIL":
        print(f"[CRITICAL QUALITY FAILURE] Generated plan did not pass quality gate:")
        for fail in failures_list:
            print(f"         - [{fail['code']}] {fail['description']}")
    else:
        print(f"      -> Quality Gate PASSED (Score: {score:.2f}): All F01-F20 criteria met.")

    from generation.fidelity_guard import FidelityGuard
    fid = FidelityGuard.audit(plan, program, prompt=prompt)
    if not fid["fidelity_passed"]:
        print(f"      [FIDELITY WARNING] Violations detected: {'; '.join(fid['violations'])}")
    else:
        print(f"      -> Constraint Fidelity Guard: PASSED ({len(fid['satisfied_constraints'])} brief criteria confirmed)")

    verdict = plan.metadata.provenance.get("senior_architect_verdict")
    if verdict:
        print(f"\n      [Gemini Senior Architect Review]:\n      \"{verdict}\"")
    style_name = plan.metadata.provenance.get("architectural_style")
    if style_name:
        print(f"      -> Architectural Style: {style_name} ({plan.metadata.provenance.get('style_family', '')})")

    os.makedirs(output_dir, exist_ok=True)
    plan_json_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_canonical.json")
    with open(plan_json_path, "w", encoding="utf-8") as f:
        f.write(plan.to_json())
    print(f"      -> Saved Canonical Architectural JSON to: {plan_json_path}")

    # Step 3: DXF Exporter
    if export_format in ("all", "dxf"):
        print(f"\n[3/5] Generating Layered AutoCAD DXF Blueprints (8 AIA Standards)...")
        dxf_gen = DXFGenerator()
        exported_dxfs = dxf_gen.export_all_floor_dxfs(plan, output_dir)
        for slug, path in exported_dxfs.items():
            print(f"      -> DXF [{slug.upper()}]: {path}")

    # Step 4: 2D Raster & Vector Presentations
    if export_format in ("all", "png"):
        print(f"\n[4/5] Rendering High-Resolution 2D Architectural Floor Plan Drawings (PNG)...")
        rendered_2d = FloorPlanVisualizer.render_all_floors(plan, output_dir)
        for slug, path in rendered_2d.items():
            print(f"      -> 2D Drawing [{slug.upper()}]: {path}")

        # FRONT ELEVATION SYNTHESIS (OPTION A & OPTION B)
        print(f"\n[4d/5] Synthesizing Dual Front Elevations (Option A: 2D CAD | Option B: 3D Studio Render)...")
        elev_a_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_front_elevation_2d.png")
        ElevationEngine.render_elevation_option_A(plan, elev_a_path)
        print(f"      -> Front Elevation [OPTION A - 2D CAD]: {elev_a_path}")

        opt_b_prompt = ElevationEngine.generate_isolated_3d_prompt(plan)
        prompt_b_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_option_b_3d_prompt.txt")
        with open(prompt_b_path, "w", encoding="utf-8") as f:
            f.write(opt_b_prompt)
        print(f"      -> Front Elevation [OPTION B - 3D PROMPT]: {prompt_b_path}")

        # Assemble Master Arch-D Presentation Sheet if ground floor exists
        gf_png = rendered_2d.get("ground_floor")
        ff_png = rendered_2d.get("first_floor", "")
        sf_png = rendered_2d.get("second_floor_penthouse", rendered_2d.get("floor_2", rendered_2d.get("level_2", "")))
        master_sheet_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_master_presentation_sheet.png")
        if gf_png and os.path.exists(gf_png):
            ElevationEngine.assemble_master_presentation_sheet(
                plan=plan,
                ground_2d_png=gf_png,
                first_2d_png=ff_png,
                elevation_2d_png=elev_a_path,
                render_3d_jpg="",
                out_sheet_png=master_sheet_path,
                second_2d_png=sf_png
            )
            print(f"      -> Master Presentation Sheet: {master_sheet_path}")

    if export_format in ("all", "pdf"):
        print(f"\n[4b/5] Rendering Arch D (24\"x36\") 300 DPI Vector PDF Presentation Sheet...")
        pdf_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_presentation_sheet.pdf")
        FloorPlanVisualizer.render_vector_sheet(plan, pdf_path, paper_size="ARCH_D", dpi=300)
        print(f"      -> Vector PDF Sheet: {pdf_path}")

    if export_format in ("all", "svg"):
        print(f"\n[4c/5] Rendering Pure Vector SVG Presentation Sheet...")
        svg_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_presentation_sheet.svg")
        FloorPlanVisualizer.render_vector_sheet(plan, svg_path, paper_size="ARCH_D", dpi=300)
        print(f"      -> Vector SVG Sheet: {svg_path}")

    # Generate RAG summary
    rag_doc = ArchitecturalRAGGenerator.generate_document(plan)
    rag_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_specification.txt")
    with open(rag_path, "w", encoding="utf-8") as f:
        f.write(rag_doc["text"])
    print(f"      -> Saved Architectural Specification to: {rag_path}")

    if render_3d:
        print(f"\n[5/5] Procedural 3D Blender Solid Modeling & Perspective Render...")
        blender = Blender3DGenerator()
        if blender.is_blender_available():
            blend_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_3d_model.blend")
            render_path = os.path.join(output_dir, f"{plan.metadata.plan_id}_3d_perspective.png")
            res = blender.generate_3d_model(plan, blend_path, render_path)
            if res["success"]:
                print(f"      -> Blender 3D Model: {blend_path}")
                print(f"      -> 3D Perspective Render: {render_path}")
            else:
                print(f"      -> Blender note: {res.get('stderr')}")
        else:
            print("      -> Blender executable not found; skipping 3D render.")

    print("\n" + "=" * 75)
    proj_name = plan.metadata.provenance.get("project_title", "Architectural Residence")
    print(f"COMPLETE: {proj_name} Generated Successfully!")
    print(f"Location: {output_dir}")
    print("=" * 75 + "\n")
    return plan


def main():
    parser = argparse.ArgumentParser(description="AI Architectural Floor Plan Pipeline")
    subparsers = parser.add_subparsers(dest="command")

    gen_p = subparsers.add_parser("generate", help="Generate layout from natural language prompt or irregular site")
    gen_p.add_argument("--prompt", type=str, required=True, help="Design prompt")
    gen_p.add_argument("--outdir", type=str, default="output/generated_plan", help="Output directory")
    gen_p.add_argument("--format", type=str, default="all", choices=["png", "svg", "pdf", "dxf", "all"], help="Export format")
    gen_p.add_argument("--no-3d", action="store_true", help="Skip 3D Blender rendering")
    gen_p.add_argument("--shape", type=str, default=None, choices=["triangle", "trapezoid", "corner_plot", "square", "lshape", "polygon", "arbitrary_polygon"], help="Preset site shape geometry")
    gen_p.add_argument("--sides", type=str, default=None, help="Comma-separated side lengths (e.g. '45,65,79' or '40,28,60,55' or '50,60,15')")
    gen_p.add_argument("--vertices", type=str, default=None, help="Ordered Cartesian vertices (e.g. '0,0; 12,0; 10,18; 0,16')")
    gen_p.add_argument("--unit", type=str, default="ft", choices=["ft", "m", "feet", "meters"], help="Unit of boundary measurements")
    gen_p.add_argument("--seed", type=int, default=None, help="Random/variation seed for layout generation")
    gen_p.add_argument("--variant-index", type=int, default=None, help="Explicit variant alternative index (1 to 10)")
    gen_p.add_argument("--strategy", type=str, default=None, help="Explicit planning strategy override")
    gen_p.add_argument("--num-variants", type=int, default=1, help="Number of distinct alternative floor plans to generate")

    dxf_p = subparsers.add_parser("dxf-to-canonical", help="Ingest DXF and output canonical JSON")
    dxf_p.add_argument("--file", type=str, required=True, help="Path to DXF file")
    dxf_p.add_argument("--outdir", type=str, default="output/dxf_ingest", help="Output directory")

    args = parser.parse_args()

    if args.command == "generate":
        run_generation_pipeline(
            prompt=args.prompt,
            output_dir=args.outdir,
            render_3d=not args.no_3d,
            export_format=args.format,
            shape=args.shape,
            sides=args.sides,
            vertices=args.vertices,
            unit=args.unit,
            seed=args.seed,
            variant_index=args.variant_index,
            strategy=args.strategy,
            num_variants=args.num_variants
        )
    elif args.command == "dxf-to-canonical":
        p = DXFParser()
        plan = p.parse_dxf(args.file)
        os.makedirs(args.outdir, exist_ok=True)
        out_file = os.path.join(args.outdir, f"{plan.metadata.plan_id}_canonical.json")
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(plan.to_json())
        print(f"Successfully converted DXF to Canonical JSON: {out_file}")
    else:
        parser.print_help()


if __name__ == "__main__":
    main()

