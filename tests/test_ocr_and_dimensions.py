"""
Unit tests for Phase 4: OCR Engine and Architectural Dimension Parsing.
"""

import pytest
from extraction.dimensions import DimensionExtractor
from vision.ocr.engine import OCREngine


def test_imperial_dimension_parsing():
    # 12'-6" = 12.5 ft = 3.81 meters
    assert DimensionExtractor.parse_imperial("12'-6\"") == 3.81
    # 10' - 0" = 10 ft = 3.048 meters
    assert DimensionExtractor.parse_imperial("10' - 0\"") == 3.048
    # 10' 6 1/2" = 10.5416 ft = 3.213 meters
    assert DimensionExtractor.parse_imperial("10' 6 1/2\"") == 3.213


def test_metric_dimension_parsing():
    # 4.2m = 4.2 meters
    assert DimensionExtractor.parse_metric("4.2m") == 4.2
    # 3500mm = 3.5 meters
    assert DimensionExtractor.parse_metric("3500mm") == 3.5
    # Raw CAD integer 4200 = 4.2 meters
    assert DimensionExtractor.parse_metric("4200") == 4.2


def test_dimension_product_parsing():
    parsed = DimensionExtractor.parse_dimension_string("12' x 14'")
    assert parsed is not None
    assert parsed["type"] == "area_dimension_pair"
    assert parsed["dim1_m"] == 3.658
    assert parsed["dim2_m"] == 4.267
    assert 15.0 <= parsed["area_m2"] <= 16.0

    parsed_m = DimensionExtractor.parse_dimension_string("3.5 x 4.0 m")
    assert parsed_m is not None
    assert parsed_m["dim1_m"] == 3.5
    assert parsed_m["dim2_m"] == 4.0
    assert parsed_m["area_m2"] == 14.0


def test_scale_estimation():
    parsed_dims = [
        {"value_m": 4.0},
        {"value_m": 5.0},
        {"value_m": 3.0}
    ]
    # At 50 px per meter:
    pixel_lens = [200.0, 250.0, 150.0]
    scale_info = DimensionExtractor.estimate_scale(parsed_dims, pixel_lens)
    assert scale_info is not None
    assert scale_info["pixels_per_meter"] == 50.0
    assert scale_info["sample_count"] == 3
    assert scale_info["confidence"] >= 0.85


def test_architectural_abbreviation_correction():
    # Note: test without loading full EasyOCR model weights to keep test fast
    engine = OCREngine.__new__(OCREngine)
    engine.ABBREVIATION_MAP = OCREngine.ABBREVIATION_MAP
    engine.ROOM_TAXONOMY = OCREngine.ROOM_TAXONOMY

    assert engine.correct_abbreviation("MBR") == "MASTER BEDROOM"
    assert engine.correct_abbreviation("DIBATH") == "BATHROOM"
    assert engine.correct_abbreviation("WASIAREA") == "WASH AREA"
    assert engine.correct_abbreviation("KIT") == "KITCHEN"


def test_room_label_classification():
    engine = OCREngine.__new__(OCREngine)
    engine.ABBREVIATION_MAP = OCREngine.ABBREVIATION_MAP
    engine.ROOM_TAXONOMY = OCREngine.ROOM_TAXONOMY

    assert engine.classify_room_label("Master Bed") == "bedroom"
    assert engine.classify_room_label("DIBATH") == "bathroom"
    assert engine.classify_room_label("Kitchen & Dining") == "kitchen"
    assert engine.classify_room_label("Great Room") == "living_room"
    assert engine.classify_room_label("Balcony") == "balcony"
