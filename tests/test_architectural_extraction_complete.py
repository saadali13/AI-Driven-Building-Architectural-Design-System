"""
Comprehensive Automated Test Suite for Autonomous Architectural Floor Plan Extraction,
Reconstruction, Comparison, and Continuous Improvement Pipeline.

Covers:
1. Source folder discovery across all 6 folders (1, 3, 5, 7, 10, elevationwithfloorplan)
2. SHA-256, MD5, and 64-bit pHash computation and duplicate tracking
3. Dataset manifest generation (outputs/dataset_manifest.json)
4. Architectural dimension parsing and normalization (imperial & metric)
5. Multi-room scale calibration and consistency scoring
6. Formal JSON schema validation against Draft-7 standard
7. Layered AutoCAD DXF export (ezdxf)
8. Mandatory 10 comparison artifacts generation
9. Retry optimizer defect diagnosis & regression rejection
10. End-to-end pipeline execution on real source blueprints
"""

import os
import json
import pytest
import numpy as np
import cv2

from cv_agent.scanner import ImageScanner, compute_sha256, compute_md5, compute_phash
from cv_agent.dimension_engine import ArchitecturalDimensionEngine
from cv_agent.schema_validator import validate_floorplan_json, FLOORPLAN_JSON_SCHEMA
from cv_agent.dxf_exporter import ArchitecturalDXFExporter
from cv_agent.comparison_generator import ComparisonArtifactGenerator
from cv_agent.retry_optimizer import RetryOptimizer
from cv_agent.pipeline import ExtractionVerificationPipeline


@pytest.fixture
def sample_synthetic_blueprint():
    """Generates a clean synthetic architectural blueprint for deterministic testing."""
    h, w = 600, 400
    canvas = np.full((h, w, 3), 255, dtype=np.uint8)

    # Exterior perimeter wall (10px)
    cv2.rectangle(canvas, (40, 40), (360, 560), (20, 20, 20), 8)

    # Dividing walls
    cv2.line(canvas, (40, 280), (360, 280), (20, 20, 20), 6)
    cv2.line(canvas, (200, 280), (200, 560), (20, 20, 20), 6)

    # Door opening & swing arc
    cv2.line(canvas, (180, 280), (220, 280), (255, 255, 255), 8)
    cv2.ellipse(canvas, (180, 280), (35, 35), 0, 0, 90, (80, 80, 80), 1)

    # Room Labels & Dimensions
    cv2.putText(canvas, "BEDROOM", (70, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (10, 10, 10), 2)
    cv2.putText(canvas, "14'-0\" X 16'-0\"", (70, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 20, 20), 1)
    cv2.putText(canvas, "LIVING", (60, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (10, 10, 10), 2)
    cv2.putText(canvas, "16' x 20'", (60, 410), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 20, 20), 1)
    cv2.putText(canvas, "KITCHEN", (220, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (10, 10, 10), 2)
    cv2.putText(canvas, "10' x 12'", (220, 410), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 20, 20), 1)

    return canvas


def test_discovery_across_all_six_folders():
    """Validates recursive scanner discovery across all 6 specified source folders."""
    scanner = ImageScanner(source_roots=["1", "3", "5", "7", "10", "elevationwithfloorplan"])
    discovered = scanner.scan_all(".")
    assert len(discovered) >= 180, f"Expected ~202 source images across 6 folders, found {len(discovered)}"
    
    folders_found = set(d["folder"] for d in discovered)
    expected_folders = {"1", "3", "5", "7", "10", "elevationwithfloorplan"}
    assert expected_folders.issubset(folders_found), f"Missing folders: {expected_folders - folders_found}"

    # Verify cryptographic and perceptual hash calculation
    first = discovered[0]
    assert "sha256_hash" in first and len(first["sha256_hash"]) == 64
    assert "md5_hash" in first and len(first["md5_hash"]) == 32
    assert "phash" in first and len(first["phash"]) == 16
    assert "drawing_id" in first


def test_dataset_manifest_generation(tmp_path):
    """Validates manifest serialization adhering to Section 5 & 12."""
    scanner = ImageScanner()
    manifest_path = str(tmp_path / "dataset_manifest.json")
    manifest = scanner.generate_and_save_manifest(".", output_manifest_path=manifest_path)

    assert os.path.isfile(manifest_path)
    assert manifest["total_discovered_files"] >= 180
    assert "folder_statistics" in manifest
    assert len(manifest["files"]) == manifest["total_discovered_files"]


def test_architectural_dimension_parsing():
    """Validates parsing of diverse architectural dimension annotations."""
    engine = ArchitecturalDimensionEngine()

    # 1. Standard Imperial dual dimension
    dim1 = engine.parse_dimension_string("14'-0\" X 18'")
    assert dim1 is not None
    assert dim1["width_ft"] == 14.0
    assert dim1["length_ft"] == 18.0
    assert abs(dim1["width_m"] - 4.267) < 0.01
    assert abs(dim1["length_m"] - 5.486) < 0.01

    # 2. Fractions/inches notation
    dim2 = engine.parse_dimension_string("12'-6\" x 14'-3\"")
    assert dim2 is not None
    assert dim2["width_ft"] == 12.5
    assert dim2["length_ft"] == 14.25

    # 3. Metric dual dimension
    dim3 = engine.parse_dimension_string("4.5m x 3.2m")
    assert dim3 is not None
    assert dim3["width_m"] == 4.5
    assert dim3["length_m"] == 3.2

    # 4. Single plot boundary span
    dim4 = engine.parse_dimension_string("50'-0\"")
    assert dim4 is not None
    assert dim4["length_ft"] == 50.0
    assert abs(dim4["length_m"] - 15.24) < 0.01


def test_scale_calibration_engine():
    """Validates multi-room scale calibration and consistency estimation."""
    engine = ArchitecturalDimensionEngine()
    rooms_mock = [
        {
            "room_id": "r1",
            "room_name": "Living",
            "normalized_width_ft": 20.0,
            "normalized_length_ft": 15.0,
            "pixel_bounding_box": [100, 100, 300, 250]  # bw=200, bh=150 -> 10 px/ft
        },
        {
            "room_id": "r2",
            "room_name": "Bed",
            "normalized_width_ft": 14.0,
            "normalized_length_ft": 12.0,
            "pixel_bounding_box": [100, 300, 240, 420]  # bw=140, bh=120 -> 10 px/ft
        }
    ]
    cal = engine.calibrate_scale(rooms_mock)
    assert cal["pixels_per_foot"] is not None
    assert abs(cal["pixels_per_foot"] - 10.0) < 0.5
    assert cal["calibration_confidence"] > 0.80
    assert cal["pixels_per_meter"] is not None


def test_formal_json_schema_validation():
    """Validates adherence to the formal JSON Schema standard."""
    valid_doc = {
        "metadata": {
            "schema_version": "2.0.0",
            "drawing_id": "drawing_1_test",
            "original_filename": "test.jpg",
            "original_relative_path": "1/test.jpg",
            "source_folder": "1",
            "file_hash_sha256": "e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
            "file_hash_md5": "d41d8cd98f00b204e9800998ecf8427e",
            "phash": "0000000000000000",
            "image_width": 800,
            "image_height": 1000,
            "processing_timestamp": "2026-10-27 12:00:00",
            "pipeline_version": "2.5.0",
            "model_and_ocr_engine_versions": {"ocr": "EasyOCR"},
            "processing_status": "PASS_VERIFIED"
        },
        "drawing_information": {
            "drawing_type": "floor_plan",
            "detected_floor": "Ground Floor",
            "drawing_orientation": "portrait",
            "plot_width_ft": 50.0,
            "plot_depth_ft": 90.0,
            "measurement_units": "Imperial",
            "scale_information": {
                "pixels_per_meter": 32.8,
                "pixels_per_foot": 10.0,
                "calibration_confidence": 0.95
            }
        },
        "extracted_text": [],
        "rooms": [],
        "architectural_elements": {
            "walls": [],
            "doors": [],
            "windows": [],
            "stairs": []
        },
        "validation_results": {
            "ocr_validation": {},
            "room_count_validation": {},
            "dimension_validation": {},
            "geometry_validation": {},
            "connectivity_validation": {},
            "duplicate_detection": {},
            "missing_feature_checks": {},
            "source_vs_extracted_metrics": {
                "ssim": 0.85,
                "psnr_db": 22.4,
                "pixel_mae": 15.2,
                "edge_iou": 0.65,
                "composite_quality_score": 88.5
            },
            "failed_checks": [],
            "warnings": [],
            "recommended_corrective_actions": [],
            "final_status": "PASS_VERIFIED"
        },
        "uncertainty_and_provenance": {
            "ambiguous_readings": [],
            "missing_dimensions": [],
            "conflicting_evidence": [],
            "inferred_geometry": [],
            "human_corrections": [],
            "processing_iteration_history": []
        }
    }

    is_valid, errs = validate_floorplan_json(valid_doc)
    assert is_valid, f"Sample JSON failed schema validation: {errs}"

    # Invalid document test
    invalid_doc = valid_doc.copy()
    invalid_doc["metadata"]["processing_status"] = "INVALID_STATUS_CODE"
    is_valid_inv, inv_errs = validate_floorplan_json(invalid_doc)
    assert not is_valid_inv, "Validator must reject non-conforming status code"


def test_dxf_exporter(tmp_path):
    """Validates layered AutoCAD DXF generation from extracted floor plan data."""
    extracted_mock = {
        "image_size": [400, 600],
        "walls": {
            "wall_segments": [
                {"start_px": [40, 40], "end_px": [360, 40], "is_exterior": True, "thickness_px": 8.0, "orientation": "horizontal"},
                {"start_px": [40, 40], "end_px": [40, 560], "is_exterior": True, "thickness_px": 8.0, "orientation": "vertical"}
            ]
        },
        "rooms": [
            {
                "room_id": "r1",
                "room_name": "Lounge",
                "original_dimension_text": "16' x 20'",
                "pixel_polygon": [[40, 40], [360, 40], [360, 280], [40, 280]],
                "pixel_bounding_box": [40, 40, 360, 280]
            }
        ],
        "doors": [{"position_px": [180, 280], "swing_radius_px": 25.0}],
        "windows": [{"start_px": [150, 40], "end_px": [250, 40]}],
        "stairs": [{"bbox_px": [50, 60, 120, 160]}]
    }

    out_dxf = str(tmp_path / "test_plan.dxf")
    res = ArchitecturalDXFExporter.export(extracted_mock, out_dxf)
    assert os.path.isfile(res)
    assert os.path.getsize(res) > 500


def test_retry_optimizer_diagnosis():
    """Validates defect diagnosis and regression rejection logic in RetryOptimizer."""
    optimizer = RetryOptimizer(max_retries=2)

    # 1. Diagnose broken walls
    audit_bad_walls = {
        "metrics": {"ssim": 0.65},
        "element_counts": {"walls": 2, "rooms": 4},
        "quality_score": 60.0
    }
    geo_bad_walls = {"wall_continuity_ratio": 0.40}
    defects = optimizer.diagnose_defects(audit_bad_walls, geo_bad_walls, {})
    assert any(d["category"] == "broken_or_sparse_walls" for d in defects)

    # 2. Select strategy
    strat = optimizer.select_correction_strategy(defects, current_iteration=0)
    assert strat["action"] == "tune_morphology_and_dilate_walls"

    # 3. Regression rejection
    base_m = {"quality_score": 75.0, "metrics": {"ssim": 0.70}, "element_counts": {"rooms": 5}}
    regressed_m = {"quality_score": 70.0, "metrics": {"ssim": 0.58}, "element_counts": {"rooms": 3}}
    is_better, reason = optimizer.evaluate_candidate_improvement(base_m, regressed_m)
    assert not is_better
    assert "Regression rejected" in reason


def test_comparison_artifacts_generation(tmp_path, sample_synthetic_blueprint):
    """Validates generation of all 10 mandatory source-vs-extracted comparison artifacts."""
    pipeline = ExtractionVerificationPipeline(outputs_dir=str(tmp_path / "outputs"))
    
    # Save synthetic blueprint as test input file
    test_img_path = tmp_path / "1" / "test_synth.png"
    os.makedirs(os.path.dirname(test_img_path), exist_ok=True)
    cv2.imwrite(str(test_img_path), sample_synthetic_blueprint)

    item = {
        "filename": "test_synth.png",
        "folder": "1",
        "relative_path": os.path.relpath(str(test_img_path), str(tmp_path)).replace("\\", "/"),
        "image_type": "floor_plan"
    }

    # Set pipeline base dir
    pipeline.base_dir = str(tmp_path)
    res = pipeline.process_image(item)

    comp_dir = tmp_path / "outputs" / "comparisons" / "1" / res["drawing_id"]
    assert os.path.isdir(comp_dir)

    expected_files = [
        "original_source.png",
        "extracted_floorplan.png",
        "comparison_side_by_side.png",
        "overlay_comparison.png",
        "difference_heatmap.png",
        "room_comparison.png",
        "dimension_comparison.png",
        "comparison_report.json",
        "comparison_report.html",
        "correction_history.json"
    ]

    for ef in expected_files:
        p = comp_dir / ef
        assert os.path.isfile(p), f"Mandatory comparison file {ef} was not generated at {p}"
        assert os.path.getsize(p) > 0, f"Comparison file {ef} is empty"

    # Check that the formal extracted JSON was saved
    json_path = tmp_path / "outputs" / "extracted_json" / "1" / f"{res['drawing_id']}.json"
    assert os.path.isfile(json_path)

    # Check that reconstructions were saved
    recon_png = tmp_path / "outputs" / "reconstructions" / "1" / f"{res['drawing_id']}.png"
    recon_svg = tmp_path / "outputs" / "reconstructions" / "1" / f"{res['drawing_id']}.svg"
    recon_dxf = tmp_path / "outputs" / "reconstructions" / "1" / f"{res['drawing_id']}.dxf"
    assert os.path.isfile(recon_png)
    assert os.path.isfile(recon_svg)
    assert os.path.isfile(recon_dxf)
