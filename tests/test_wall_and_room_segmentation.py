"""
Unit tests for Phase 5 & Phase 6:
Wall detection, opening detection, and door-aware room segmentation.
Validates:
1. Thick structural wall filtering vs thin lines.
2. Wall gap opening detection with jamb endpoints.
3. Multi-signal room segmentation preventing doorway leakage.
4. Doorway connectivity preservation between room pairs.
5. V4 Semantic discipline: Unlabelled rooms become 'unclassified_closed_region'.
"""

import pytest
import numpy as np
import cv2
from vision.detection.walls import WallDetector
from vision.detection.openings import OpeningDetector
from vision.room_detection.segmentation import RoomSegmentor


@pytest.fixture
def synthetic_two_room_plan():
    """
    Creates a synthetic binary floor plan (height=500, width=600):
    - Exterior border walls: thickness 10px.
    - Outer boundary: x from 50 to 550, y from 50 to 450.
    - Dividing wall at x=300 from y=50 to 450 with an interior door gap from y=200 to y=260.
    - Thin witness line (thickness 1px) from x=60 to 280 at y=480 (outside house).
    - Two rooms:
      Room 1 (Left): x in [50, 300], y in [50, 450]
      Room 2 (Right): x in [300, 550], y in [50, 450]
    """
    img = np.ones((500, 600), dtype=np.uint8) * 255 # White background
    wall_color = 0 # Black walls

    # Outer rectangle: x in [50, 550], y in [50, 450], thickness 10
    cv2.rectangle(img, (50, 50), (550, 450), wall_color, thickness=10)

    # Dividing wall at x=300, leaving an open doorway gap between y=200 and y=260
    # Top segment of dividing wall: y from 50 to 200
    cv2.line(img, (300, 50), (300, 200), wall_color, thickness=10)
    # Bottom segment of dividing wall: y from 260 to 450
    cv2.line(img, (300, 260), (300, 450), wall_color, thickness=10)

    # Thin dimension / witness line (thickness 1px)
    cv2.line(img, (60, 480), (280, 480), wall_color, thickness=1)

    return img


def test_wall_detector_stroke_width_filtering(synthetic_two_room_plan):
    detector = WallDetector(min_wall_thickness=4, max_wall_thickness=30)
    wall_mask = detector.extract_wall_mask(synthetic_two_room_plan)

    assert wall_mask is not None
    assert wall_mask.shape == synthetic_two_room_plan.shape

    # Check that thick walls are present in wall_mask (255)
    # Top exterior wall at (300, 50)
    assert wall_mask[50, 200] == 255
    # Left exterior wall at (50, 200)
    assert wall_mask[200, 50] == 255

    # Check that thin 1px witness line at y=480 was filtered out
    assert np.all(wall_mask[480, 60:280] == 0)


def test_opening_detector_door_gap_detection(synthetic_two_room_plan):
    wall_detector = WallDetector(min_wall_thickness=4)
    wall_mask = wall_detector.extract_wall_mask(synthetic_two_room_plan)

    opening_detector = OpeningDetector(min_door_width_px=20, max_door_width_px=100)
    openings = opening_detector.detect_wall_gap_openings(wall_mask)

    assert len(openings) >= 1, "Should detect at least one wall gap opening for the doorway"
    
    # Check that door gap is located near x=300, y=230
    door = None
    for op in openings:
        if abs(op["position"][0] - 300) < 20 and abs(op["position"][1] - 230) < 30:
            door = op
            break
    
    assert door is not None, f"Expected door gap at ~(300, 230), got {[o['position'] for o in openings]}"
    assert "jamb_endpoints" in door
    assert len(door["jamb_endpoints"]) == 2
    assert 40 <= door["width_px"] <= 80


def test_door_aware_room_segmentation_prevents_leakage(synthetic_two_room_plan):
    wall_detector = WallDetector(min_wall_thickness=4)
    wall_mask = wall_detector.extract_wall_mask(synthetic_two_room_plan)

    # Supply exact doorway jamb opening at x=300, y in [200, 260]
    door_openings = [{
        "opening_id": "door_001",
        "type": "door",
        "position": [300, 230],
        "jamb_endpoints": [[300, 200], [300, 260]],
        "width_px": 60.0
    }]

    # Provide OCR label ONLY for Room 1 (left side)
    ocr_entries = [{
        "text": "MASTER BEDROOM",
        "corrected_text": "MASTER BEDROOM",
        "confidence": 0.94,
        "is_room_label": True,
        "room_category": "bedroom",
        "centroid": [175, 250],
        "bbox": [150, 240, 200, 260]
    }]

    segmentor = RoomSegmentor(min_room_area_px=2000, simplify_tolerance_px=2.0)
    rooms, linked_doors = segmentor.segment_rooms(wall_mask, door_openings, ocr_entries)

    # 1. We should have extracted at least 2 distinct rooms (Left and Right)
    assert len(rooms) >= 2, f"Expected at least 2 rooms, found {len(rooms)}"

    # 2. Check room classifications
    room_types = [r["type"] for r in rooms]
    assert "bedroom" in room_types, "Room 1 should be classified as 'bedroom' from OCR label"
    assert "unclassified_closed_region" in room_types, (
        "Room 2 (with no OCR label) MUST be classified as 'unclassified_closed_region' per V4 semantic discipline"
    )

    # 3. Check V4 discipline confidence
    unclassified_room = next(r for r in rooms if r["type"] == "unclassified_closed_region")
    assert unclassified_room["confidence"] < 0.50
    assert "no_text_label" in unclassified_room["evidence"]

    # 4. Check door connectivity: Door 001 must connect the 2 rooms
    assert len(linked_doors) == 1
    connected = linked_doors[0]["connects_rooms"]
    assert len(connected) == 2, f"Door should connect exactly 2 rooms, got {connected}"
    assert connected[0] != connected[1]
