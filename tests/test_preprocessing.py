"""
Unit tests for Phase 3: Image Preprocessing, Resolution Gating, and Deskewing.
"""

import numpy as np
import cv2
from vision.preprocessing.normalizer import Preprocessor


def test_resolution_gating():
    prep = Preprocessor(min_resolution=600)
    
    tiny_img = np.zeros((400, 300, 3), dtype=np.uint8)
    res_tiny = prep.check_resolution(tiny_img)
    assert res_tiny["is_low_res"] is True
    assert res_tiny["requires_upscaling"] is True
    assert res_tiny["resolution_status"] == "insufficient_for_small_ocr"

    hd_img = np.zeros((1600, 1200, 3), dtype=np.uint8)
    res_hd = prep.check_resolution(hd_img)
    assert res_hd["is_low_res"] is False
    assert res_hd["resolution_status"] == "adequate"


def test_deskewing_on_known_rotation():
    prep = Preprocessor()
    # Create synthetic image with horizontal walls
    img = np.full((500, 500), 255, dtype=np.uint8)
    cv2.line(img, (50, 100), (450, 100), 0, 4)
    cv2.line(img, (50, 250), (450, 250), 0, 4)
    cv2.line(img, (50, 400), (450, 400), 0, 4)
    
    # Rotate by 4 degrees
    M = cv2.getRotationMatrix2D((250, 250), 4.0, 1.0)
    rotated = cv2.warpAffine(img, M, (500, 500), borderValue=255)
    
    detected_angle = prep.estimate_skew_angle(rotated)
    # The Hough angle should detect approximately -4 or +4 degrees
    assert abs(abs(detected_angle) - 4.0) < 1.0


def test_border_suppression():
    prep = Preprocessor()
    img = np.full((400, 400), 255, dtype=np.uint8)
    # Draw heavy black border frame around the entire outer margin
    cv2.rectangle(img, (0, 0), (399, 399), 0, 15)
    
    clean, meta = prep.suppress_borders(img, border_ratio=0.04)
    assert meta["border_detected"] is True
    # The corner margins should be converted to white (255)
    assert clean[5, 5] == 255
    assert clean[395, 395] == 255


def test_full_preprocessing_pipeline():
    prep = Preprocessor()
    img = np.full((800, 600, 3), 240, dtype=np.uint8)
    # Draw room lines
    cv2.rectangle(img, (100, 100), (500, 700), (0, 0, 0), 5)
    
    bgr, gray, meta = prep.process(img)
    assert bgr.shape == (800, 600, 3)
    assert gray.shape == (800, 600)
    assert meta["resolution"]["resolution_status"] == "adequate"
    assert "deskew_angle_deg" in meta
    assert "border_suppression" in meta
