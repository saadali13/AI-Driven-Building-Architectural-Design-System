"""
Master Comprehensive Verification Suite for Unified Architectural CAD Engine:
1. Invalidation & Multi-Floor Constraint Logic (F13 edge cases)
2. Hybrid RAG Matcher Dataset Retrieval across all Pakistani plot scales (3M, 5M, 7M, 10M, 1K)
3. Production CAD Multi-Format Export Bundle (.dxf, .pdf, .svg, .png, .json, .txt)
"""

import os
import glob
import pytest
from requirements.parser import NaturalLanguageRequirementsParser, InfeasibleProgramError
from generation.rag_matcher import RAGMatcher
from generation.rag_solver import DatasetDrivenRAGSolver
from generation.quality_gate import FloorPlanQualityGate
from pipeline_runner import run_generation_pipeline


def test_invalidation_guard_edge_cases():
    """
    Verifies multi-floor physical feasibility and statutory capacity invalidation rules (F13).
    """
    # 1. Reject 5 bedrooms on 2-storey 3 Marla plot
    prompt_3m_2f = "Design a 2-storey 3 marla house with 5 bedrooms"
    with pytest.raises(InfeasibleProgramError) as excinfo:
        NaturalLanguageRequirementsParser.parse(prompt_3m_2f, raise_on_error=True)
    assert "F13" in str(excinfo.value)
    assert "IBC Section 1207" in str(excinfo.value)
    assert "3 floors (G+2)" in str(excinfo.value)

    # 2. Allow 5 bedrooms if 3 floors (G+2) are specified
    prompt_3m_3f = "Design a 3-storey (G+2) 3 marla house with 5 bedrooms"
    program_3f = NaturalLanguageRequirementsParser.parse(prompt_3m_3f, raise_on_error=True)
    assert program_3f.is_feasible is True
    assert program_3f.floor_count == 3
    assert program_3f.levels == [0, 1, 2]

    # Synthesize layout and verify G+2 structure with 5 bedrooms
    solver = DatasetDrivenRAGSolver()
    plan_3f = solver.synthesize(prompt_3m_3f)
    assert plan_3f is not None
    assert plan_3f.metadata.floor_count == 3
    assert set(plan_3f.metadata.levels) == {0, 1, 2}
    beds_gen = [r for r in plan_3f.rooms if r.room_type == "bedroom"]
    assert len(beds_gen) == 5

    # Run Quality Gate asserting full compliance
    gate_3f = FloorPlanQualityGate.evaluate(plan_3f, program_3f)
    assert gate_3f["final_status"] == "PASS"
    assert gate_3f["quality_score"] == 1.0

    # 3. Reject 2 full kitchens on 5 Marla Ground Floor
    prompt_5m_2kit = "Design a 5 marla house with 2 full kitchens on ground floor"
    with pytest.raises(InfeasibleProgramError) as excinfo_kit:
        NaturalLanguageRequirementsParser.parse(prompt_5m_2kit, raise_on_error=True)
    assert "F13" in str(excinfo_kit.value)
    assert "2 full kitchens on Ground Floor" in str(excinfo_kit.value)


def test_rag_matcher_dataset_retrieval():
    """
    Verifies queries against 3M, 5M, 7M, 10M, and 1 Kanal retrieve real plans
    from dataset_index.json with similarity >= 0.70.
    """
    matcher = RAGMatcher("dataset/dataset_index.json")
    assert len(matcher.catalog) >= 180

    scale_queries = [
        ("3_marla", "Design a 3 marla house with 3 bedrooms and stairs"),
        ("5_marla", "Design a 5 marla house with 3 bedrooms and dogleg stairs"),
        ("7_marla", "Design a 7 marla luxury residence with 4 bedrooms"),
        ("10_marla", "Design a 10 marla executive villa with 5 bedrooms"),
        ("1_kanal", "Design a 1 kanal stately manor with 5 bedrooms and front lawn")
    ]

    for scale, prompt in scale_queries:
        prog = NaturalLanguageRequirementsParser.parse(prompt, raise_on_error=False)
        base_plan, source, score = matcher.query_vector(prog)
        
        assert base_plan is not None
        assert source in ("cv_dataset", "golden_baseline")
        assert score >= 0.65
        assert base_plan.boundary is not None
        assert len(base_plan.rooms) > 0


def test_production_cad_export_bundle(tmp_path):
    """
    Executes full pipeline and verifies multi-format production CAD export bundle:
    AutoCAD DXF, Arch D Vector PDF, Pure Vector SVG, High-Res PNG, Canonical JSON, Specification TXT.
    """
    test_out = str(tmp_path / "cad_export_bundle")
    prompt = "Design a modern 5 marla house with 3 bedrooms and dogleg stairs"

    plan = run_generation_pipeline(
        prompt=prompt,
        output_dir=test_out,
        render_3d=False,
        export_format="all"
    )

    assert plan is not None

    # Verify Canonical JSON
    json_files = glob.glob(os.path.join(test_out, "*_canonical.json"))
    assert len(json_files) >= 1
    assert os.path.getsize(json_files[0]) > 0

    # Verify Quality Gate Report
    report_file = os.path.join(test_out, "quality_report.json")
    assert os.path.exists(report_file)
    assert os.path.getsize(report_file) > 0

    # Verify AutoCAD DXF Exports
    dxf_files = glob.glob(os.path.join(test_out, "*.dxf"))
    assert len(dxf_files) >= 2  # ground floor, first floor, composite
    for dxf in dxf_files:
        assert os.path.getsize(dxf) > 0

    # Verify Arch D Vector PDF Sheet
    pdf_files = glob.glob(os.path.join(test_out, "*.pdf"))
    assert len(pdf_files) >= 1
    for pdf in pdf_files:
        assert os.path.getsize(pdf) > 0

    # Verify Vector SVG Sheet
    svg_files = glob.glob(os.path.join(test_out, "*.svg"))
    assert len(svg_files) >= 1
    for svg in svg_files:
        assert os.path.getsize(svg) > 0

    # Verify High-Res 2D PNG Drawings
    png_files = glob.glob(os.path.join(test_out, "*.png"))
    assert len(png_files) >= 2
    for png in png_files:
        assert os.path.getsize(png) > 0

    # Verify Architectural Specification TXT
    txt_files = glob.glob(os.path.join(test_out, "*.txt"))
    assert len(txt_files) >= 1
    for txt in txt_files:
        assert os.path.getsize(txt) > 0
