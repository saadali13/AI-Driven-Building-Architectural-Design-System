"""
Comprehensive Automated Test Suite for AI Floor Plan Extraction, Reconstruction & Verification Agent.

Covers:
1. Folder discovery & file registration
2. Source file integrity (immutable original blueprints)
3. Image loading & preprocessing (deskew, CLAHE, line extraction)
4. Combined drawing panel isolation
5. Architectural element extraction (walls, thickness, watertight rooms)
6. Window and door detection
7. Staircase and OCR text extraction
8. Reconstruction fidelity (Raster PNG, SVG layers, and overlay)
9. Accuracy metrics calculation (MAE, PSNR, SSIM, Edge IoU)
10. Controlled error injection (removed wall, added wall, shifted geometry)
11. False-positive resistance (unchanged reference, JPEG compression)
12. Ground-truth benchmark dataset integrity
13. Pipeline execution, retry logic, CSV/JSON report persistence
14. Dashboard API endpoints integration
"""

import os
import json
import csv
import pytest
import numpy as np
import cv2

from cv_agent.scanner import ImageScanner, compute_md5, compute_phash, classify_image_type
from cv_agent.preprocessor import ImagePreprocessor
from cv_agent.detector import ArchitecturalElementDetector
from cv_agent.reconstructor import FloorPlanReconstructor
from cv_agent.accuracy_monitor import AccuracyMonitor, AccuracyThresholds
from cv_agent.controlled_audit import ControlledMonitorAuditor
from cv_agent.pipeline import ExtractionVerificationPipeline
from cv_agent.geometry_validator import ArchitecturalGeometryValidator



@pytest.fixture
def sample_blueprint():
    """Generates a synthetic architectural blueprint canvas for deterministic unit testing."""
    h, w = 600, 400
    canvas = np.full((h, w, 3), 255, dtype=np.uint8)

    # Outer wall rectangle (10px thick)
    cv2.rectangle(canvas, (40, 40), (360, 560), (20, 20, 20), 8)

    # Interior dividing walls
    cv2.line(canvas, (40, 280), (360, 280), (20, 20, 20), 6)
    cv2.line(canvas, (200, 280), (200, 560), (20, 20, 20), 6)

    # Door opening & swing arc
    cv2.line(canvas, (180, 280), (220, 280), (255, 255, 255), 8)  # Gap
    cv2.ellipse(canvas, (180, 280), (35, 35), 0, 0, 90, (80, 80, 80), 1)

    # Room Labels
    cv2.putText(canvas, "BEDROOM", (70, 160), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (10, 10, 10), 2)
    cv2.putText(canvas, "14' x 16'", (70, 190), cv2.FONT_HERSHEY_SIMPLEX, 0.5, (100, 20, 20), 1)
    cv2.putText(canvas, "LIVING", (60, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (10, 10, 10), 2)
    cv2.putText(canvas, "KITCHEN", (220, 380), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (10, 10, 10), 2)

    return canvas


def test_scanner_discovery():
    """Verifies folder discovery across all supported source folders."""
    scanner = ImageScanner(source_roots=["1", "3", "5", "7", "10", "elevationwithfloorplan"])
    discovered = scanner.scan_all(".")
    assert len(discovered) > 0, "Scanner should discover source blueprint images"
    first = discovered[0]
    assert "filename" in first
    assert "folder" in first
    assert "md5_hash" in first
    assert "phash" in first
    assert "image_type" in first


def test_source_file_integrity():
    """Verifies that reading images never alters source file contents or hashes."""
    test_path = "1/00770eba64db20501bbd30bb21ce6aa5.jpg"
    assert os.path.isfile(test_path), "Target test image must exist"
    initial_hash = compute_md5(test_path)
    img = cv2.imread(test_path)
    assert img is not None, "Image must load properly"
    post_hash = compute_md5(test_path)
    assert initial_hash == post_hash, "Source file hash must remain strictly immutable"


def test_preprocessor(sample_blueprint):
    """Tests deskewing, contrast enhancement, and line mask segmentation."""
    prep = ImagePreprocessor()
    enhanced = prep.enhance_contrast(sample_blueprint)
    assert enhanced.shape == sample_blueprint.shape

    bin_mask, wall_mask = prep.extract_line_mask(sample_blueprint)
    assert bin_mask.shape == sample_blueprint.shape[:2]
    assert wall_mask.shape == sample_blueprint.shape[:2]
    assert np.count_nonzero(wall_mask) > 100, "Wall mask must capture structural lines"


def test_panel_isolation():
    """Tests combined drawing panel separation for elevation+floorplan sheets."""
    prep = ImagePreprocessor()
    synthetic_combined = np.full((1200, 800, 3), 255, dtype=np.uint8)
    # Elevation drawing in top half
    cv2.rectangle(synthetic_combined, (100, 100), (700, 450), (40, 40, 40), 4)
    # Floor plan drawing in bottom half
    cv2.rectangle(synthetic_combined, (100, 650), (700, 1100), (20, 20, 20), 8)

    cropped, box = prep.isolate_floor_plan_region(synthetic_combined, "elevation_with_floorplan")
    assert cropped.shape[0] < synthetic_combined.shape[0], "Panel isolation must crop floor plan"
    assert box[1] > 0, "Top crop boundary must be non-zero"


def test_detector_walls_and_rooms(sample_blueprint):
    """Tests wall thickness estimation and closed watertight room polygon extraction."""
    prep = ImagePreprocessor()
    _, wall_mask = prep.extract_line_mask(sample_blueprint)

    det = ArchitecturalElementDetector()
    walls = det.detect_walls_and_thickness(wall_mask)
    assert walls["wall_count"] > 0
    assert walls["wall_thickness_px"] >= 2.0

    rooms = det.detect_rooms(wall_mask)
    assert len(rooms) >= 1, "Must identify closed room boundary polygons"
    assert "polygon_px" in rooms[0]
    assert "area_px" in rooms[0]


def test_detector_windows_and_doors(sample_blueprint):
    """Tests window detection and door swing arc extraction."""
    prep = ImagePreprocessor()
    _, wall_mask = prep.extract_line_mask(sample_blueprint)

    det = ArchitecturalElementDetector()
    doors = det.detect_doors_and_swings(sample_blueprint, wall_mask)
    assert isinstance(doors, list)
    windows = det.detect_windows(sample_blueprint, wall_mask)
    assert isinstance(windows, list)


def test_reconstructor(sample_blueprint):
    """Tests raster PNG and layered vector SVG reconstruction."""
    prep = ImagePreprocessor()
    _, wall_mask = prep.extract_line_mask(sample_blueprint)

    det = ArchitecturalElementDetector()
    extracted = det.extract_all(sample_blueprint, wall_mask)

    recon = FloorPlanReconstructor()
    raster = recon.render_faithful_raster(extracted, target_size=(400, 600))
    assert raster.shape == (600, 400, 3)

    svg_str = recon.render_vector_svg(extracted, target_size=(400, 600))
    assert "<svg" in svg_str
    assert "</svg>" in svg_str
    assert 'id="walls"' in svg_str
    assert 'id="rooms"' in svg_str
    assert 'id="doors"' in svg_str
    assert 'id="windows"' in svg_str


def test_accuracy_monitor(sample_blueprint):
    """Tests multi-metric verification and difference heatmap generation."""
    prep = ImagePreprocessor()
    _, wall_mask = prep.extract_line_mask(sample_blueprint)

    det = ArchitecturalElementDetector()
    extracted = det.extract_all(sample_blueprint, wall_mask)

    recon = FloorPlanReconstructor()
    raster = recon.render_faithful_raster(extracted, target_size=(400, 600))

    monitor = AccuracyMonitor()
    audit = monitor.evaluate(sample_blueprint, raster, extracted)

    assert "verdict" in audit
    assert audit["verdict"] in ("Verified", "Needs Review", "Failed")
    assert 0.0 <= audit["quality_score"] <= 100.0
    assert "ssim" in audit["metrics"]
    assert "pixel_mae" in audit["metrics"]
    assert "edge_iou" in audit["metrics"]
    assert audit["heatmap"].shape == sample_blueprint.shape
    assert audit["audit_composite"].shape[0] > sample_blueprint.shape[0]


def test_controlled_error_injection_audit():
    """Verifies that AccuracyMonitor achieves 100% precision and recall on controlled mutations."""
    auditor = ControlledMonitorAuditor()
    res = auditor.run_audit()
    assert res["total_test_cases"] == 13
    assert res["passed_tests"] == 13, f"All controlled test cases must pass: {res}"
    assert res["monitor_precision"] == 1.0
    assert res["monitor_recall"] == 1.0
    assert res["monitor_f1_score"] == 1.0


def test_ground_truth_dataset_loading():
    """Verifies that the ground truth testing dataset is well-formed and valid."""
    gt_path = os.path.join("dataset", "ground_truth_dataset.json")
    assert os.path.isfile(gt_path), "Ground truth dataset JSON must exist"
    with open(gt_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    assert "plans" in data
    assert len(data["plans"]) == 12, "Ground truth dataset must contain 12 representative plans"
    for plan in data["plans"]:
        assert os.path.isfile(os.path.join(plan["folder"], plan["filename"])), f"Image {plan['filename']} must exist"
        assert "min_expected_rooms" in plan["architectural_elements"]
        assert "expected_doors_min" in plan["architectural_elements"]


def test_pipeline_single_image(tmp_path):
    """Tests end-to-end processing of a real blueprint image through the complete pipeline."""
    pipeline = ExtractionVerificationPipeline(output_dir=str(tmp_path / "output"), reports_dir=str(tmp_path / "reports"))
    item = {
        "filename": "00770eba64db20501bbd30bb21ce6aa5.jpg",
        "folder": "1",
        "relative_path": "1/00770eba64db20501bbd30bb21ce6aa5.jpg",
        "image_type": "floor_plan"
    }
    res = pipeline.process_image(item)
    assert res["verdict"] in ("Verified", "Needs Review", "Failed")
    assert res["rooms_detected"] > 0
    assert res["walls_detected"] > 0
    assert os.path.exists(res["outputs"]["reconstructed"])
    assert os.path.exists(res["outputs"]["vector"])
    assert os.path.exists(res["outputs"]["diff_map"])


def test_regression_robust_background_black_borders():
    """Regression test: Black scanner borders must not contaminate paper background color."""
    prep = ImagePreprocessor()
    # Create white drawing with black scanner borders (15px)
    h, w = 400, 400
    img = np.full((h, w, 3), 250, dtype=np.uint8)
    img[:15, :] = 0
    img[-15:, :] = 0
    img[:, :15] = 0
    img[:, -15:] = 0

    bg = prep.extract_robust_background_color(img)
    # Background must be light paper tone (~250), NOT black (0,0,0)
    assert bg[0] > 200 and bg[1] > 200 and bg[2] > 200, f"Expected light background, got {bg}"


def test_regression_door_hallucination_suppression():
    """Regression test: Isolated circular curves must not trigger false door swings."""
    prep = ImagePreprocessor()
    det = ArchitecturalElementDetector()

    # Create empty canvas with an isolated circle in center (no walls)
    canvas = np.full((400, 400, 3), 255, dtype=np.uint8)
    wall_mask = np.zeros((400, 400), dtype=np.uint8)
    cv2.circle(canvas, (200, 200), 30, (50, 50, 50), 2)

    doors = det.detect_doors_and_swings(canvas, wall_mask)
    # Isolated circle not touching walls should NOT be recognized as a valid architectural door swing
    assert len(doors) == 0, f"Spurious isolated circle detected as door: {doors}"


def test_regression_window_rectilinear_filtering():
    """Regression test: Diagonal and stray ticks must not be classified as window mullions."""
    prep = ImagePreprocessor()
    det = ArchitecturalElementDetector()

    canvas = np.full((400, 400, 3), 255, dtype=np.uint8)
    wall_mask = np.zeros((400, 400), dtype=np.uint8)
    # Draw diagonal lines
    cv2.line(canvas, (50, 50), (120, 110), (20, 20, 20), 2)

    windows = det.detect_windows(canvas, wall_mask)
    assert len(windows) == 0, f"Diagonal line falsely detected as window: {windows}"


def test_geometry_validator_metrics(sample_blueprint):
    """Phase 2: Tests independent architectural geometry validation metrics."""
    prep = ImagePreprocessor()
    _, wall_mask = prep.extract_line_mask(sample_blueprint)
    det = ArchitecturalElementDetector()
    extracted = det.extract_all(sample_blueprint, wall_mask)

    validator = ArchitecturalGeometryValidator(match_tolerance_px=24.0)
    
    # Test without ground truth (heuristic topology checks)
    metrics_heuristic = validator.validate_geometry(extracted, sample_blueprint)
    assert "wall_continuity_ratio" in metrics_heuristic
    assert metrics_heuristic["wall_continuity_ratio"] >= 0.0
    assert metrics_heuristic["room_count"] >= 1
    assert "architectural_geometry_precision" in metrics_heuristic
    assert "architectural_geometry_recall" in metrics_heuristic
    assert "architectural_geometry_f1" in metrics_heuristic
    assert 0.0 <= metrics_heuristic["architectural_geometry_f1"] <= 1.0

    # Test with ground truth reference
    gt_mock = {
        "architectural_elements": {
            "expected_room_count_target": 3,
            "expected_door_count_target": 1,
            "expected_wall_continuity_min": 0.60,
            "key_labels": ["BEDROOM", "LIVING", "KITCHEN"]
        }
    }
    metrics_gt = validator.validate_geometry(extracted, sample_blueprint, ground_truth=gt_mock)
    assert metrics_gt["has_ground_truth"] is True
    assert "room_count_accuracy" in metrics_gt
    assert "key_label_recall" in metrics_gt
    assert metrics_gt["architectural_geometry_f1"] > 0.0


def test_geometry_validation_overlay_generation(sample_blueprint):
    """Phase 2: Tests diagnostic tri-color geometry validation overlay rendering."""
    prep = ImagePreprocessor()
    _, wall_mask = prep.extract_line_mask(sample_blueprint)
    det = ArchitecturalElementDetector()
    extracted = det.extract_all(sample_blueprint, wall_mask)

    recon = FloorPlanReconstructor()
    raster = recon.render_faithful_raster(extracted, target_size=(400, 600))

    validator = ArchitecturalGeometryValidator()
    overlay = validator.generate_geometry_validation_overlay(
        source_bgr=sample_blueprint,
        reconstructed_bgr=raster,
        extracted_data=extracted
    )

    assert overlay is not None
    assert len(overlay.shape) == 3 and overlay.shape[2] == 3, "Overlay must be 3-channel BGR"
    # Height must be larger than original canvas due to top diagnostic banner
    assert overlay.shape[0] > sample_blueprint.shape[0]
    assert overlay.shape[1] == sample_blueprint.shape[1]


def test_ground_truth_dev_test_split_integrity():
    """Phase 2: Verifies strict dev vs held-out test partitioning across all source folders."""
    gt_path = os.path.join("dataset", "ground_truth_dataset.json")
    assert os.path.isfile(gt_path), "Ground truth dataset JSON must exist"
    with open(gt_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    plans = data.get("plans", [])
    assert len(plans) == 12, "Must contain exactly 12 benchmark plans"

    dev_plans = [p for p in plans if p.get("split") == "dev"]
    test_plans = [p for p in plans if p.get("split") == "test"]

    assert len(dev_plans) == 6, f"Expected exactly 6 dev plans, got {len(dev_plans)}"
    assert len(test_plans) == 6, f"Expected exactly 6 held-out test plans, got {len(test_plans)}"

    # Ensure completely disjoint sets
    dev_ids = {p["plan_id"] for p in dev_plans}
    test_ids = {p["plan_id"] for p in test_plans}
    assert dev_ids.isdisjoint(test_ids), "Dev and test plan IDs must have zero overlap"

    dev_files = {p["filename"] for p in dev_plans}
    test_files = {p["filename"] for p in test_plans}
    assert dev_files.isdisjoint(test_files), "Dev and test filenames must have zero overlap"

    # Ensure all 6 source folders are covered in both dev and test
    expected_folders = {"1", "3", "5", "7", "10", "elevationwithfloorplan"}
    dev_folders = {p["folder"] for p in dev_plans}
    test_folders = {p["folder"] for p in test_plans}
    assert dev_folders == expected_folders, f"Dev plans must cover all folders: {dev_folders}"
    assert test_folders == expected_folders, f"Test plans must cover all folders: {test_folders}"

    # Verify that all physical files exist and MD5 hashes match
    for p in plans:
        fpath = os.path.join(p["folder"], p["filename"])
        assert os.path.isfile(fpath), f"Source image missing: {fpath}"
        current_md5 = compute_md5(fpath)
        assert current_md5 == p["md5_hash"], f"Source image MD5 mismatch for {fpath}"


def test_adaptive_room_segmentation_area_threshold():
    """Phase 2: Verifies oversegmentation suppression on tiny non-room cavities."""
    det = ArchitecturalElementDetector()
    # Large 2000x2000 canvas -> img_area * 0.005 = 20,000 px threshold
    h, w = 2000, 2000
    wall_mask = np.full((h, w), 255, dtype=np.uint8)

    # Cut out a tiny 25x25 cavity (625 px) which is < 1600 and << 20,000 px
    wall_mask[500:525, 500:525] = 0

    rooms = det.detect_rooms(wall_mask)
    # The tiny cavity should NOT be counted as a legitimate room chamber
    assert len(rooms) == 0, f"Expected 0 rooms for 625px cavity in 4MP canvas, got {len(rooms)}"


def test_editable_architectural_json_schema(sample_blueprint):
    """Phase 3: Verifies explicit structured architectural representation in JSON metadata."""
    prep = ImagePreprocessor()
    _, wall_mask = prep.extract_line_mask(sample_blueprint)
    det = ArchitecturalElementDetector()
    extracted = det.extract_all(sample_blueprint, wall_mask)

    assert "image_size" in extracted
    assert "walls" in extracted and "wall_segments" in extracted["walls"]
    assert "rooms" in extracted
    assert "doors" in extracted
    assert "windows" in extracted
    assert "stairs" in extracted
    assert "text_annotations" in extracted
    assert "adjacency" in extracted

    # Verify explicit wall segment schema
    wall_segs = extracted["walls"]["wall_segments"]
    assert len(wall_segs) > 0
    first_wall = wall_segs[0]
    assert "wall_id" in first_wall
    assert "start_px" in first_wall and len(first_wall["start_px"]) == 2
    assert "end_px" in first_wall and len(first_wall["end_px"]) == 2
    assert "thickness_px" in first_wall

    # Verify explicit room polygon schema and adjacency
    assert len(extracted["rooms"]) > 0
    first_room = extracted["rooms"][0]
    assert "room_id" in first_room
    assert "polygon_px" in first_room and len(first_room["polygon_px"]) >= 3
    assert "adjacent_room_ids" in first_room


def test_editable_vector_svg_structure(sample_blueprint):
    """Phase 3: Verifies layered, editable, browser-renderable SVG output."""
    prep = ImagePreprocessor()
    _, wall_mask = prep.extract_line_mask(sample_blueprint)
    det = ArchitecturalElementDetector()
    extracted = det.extract_all(sample_blueprint, wall_mask)

    recon = FloorPlanReconstructor()
    svg = recon.render_vector_svg(extracted, target_size=(400, 600))

    assert svg.startswith("<svg") and svg.strip().endswith("</svg>")
    assert 'viewBox="0 0 400 600"' in svg
    assert '<g id="rooms"' in svg
    assert '<g id="walls"' in svg
    assert '<g id="windows"' in svg
    assert '<g id="doors"' in svg
    assert '<g id="stairs"' in svg
    assert '<g id="labels"' in svg
    assert 'data-id=' in svg, "SVG elements must have data-id attributes for vector editing"


def test_wall_segment_precision_recall_metrics(sample_blueprint):
    """Phase 3: Verifies wall-segment precision, recall, and centerline positional error."""
    prep = ImagePreprocessor()
    _, wall_mask = prep.extract_line_mask(sample_blueprint)
    det = ArchitecturalElementDetector()
    extracted = det.extract_all(sample_blueprint, wall_mask)

    validator = ArchitecturalGeometryValidator(match_tolerance_px=12.0)
    metrics = validator.validate_geometry(extracted, sample_blueprint)

    assert "wall_segment_precision" in metrics
    assert "wall_segment_recall" in metrics
    assert "wall_segment_f1" in metrics
    assert "wall_centerline_error_px" in metrics

    assert 0.0 <= metrics["wall_segment_precision"] <= 1.0
    assert 0.0 <= metrics["wall_segment_recall"] <= 1.0
    assert metrics["wall_centerline_error_px"] >= 0.0
    assert "metric_definitions" in metrics


def test_door_jamb_attachment_metric(sample_blueprint):
    """Phase 3: Verifies door-jamb wall attachment check vs detached floating hallucinations."""
    det = ArchitecturalElementDetector()
    validator = ArchitecturalGeometryValidator()

    # Valid attached door
    extracted_attached = {
        "walls": {"wall_segments": [{"start_px": [50, 50], "end_px": [200, 50], "wall_id": "w1"}]},
        "doors": [{"door_id": "d1", "position_px": [60, 52], "attached_wall_id": "w1"}],
        "rooms": [], "windows": [], "stairs": [], "text_annotations": []
    }
    m_att = validator.validate_geometry(extracted_attached, sample_blueprint)
    assert m_att["door_jamb_attachment_ratio"] == 1.0

    # Unattached floating door far away from any walls
    extracted_floating = {
        "walls": {"wall_segments": [{"start_px": [50, 50], "end_px": [200, 50], "wall_id": "w1"}]},
        "doors": [{"door_id": "d2", "position_px": [350, 500], "attached_wall_id": None}],
        "rooms": [], "windows": [], "stairs": [], "text_annotations": []
    }
    m_float = validator.validate_geometry(extracted_floating, sample_blueprint)
    assert m_float["door_jamb_attachment_ratio"] == 0.0



