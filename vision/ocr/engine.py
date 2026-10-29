"""
Phase 4: High-Fidelity OCR Engine with Architectural Post-Processing.
Extracts text strings, bboxes, room labels, and dimensions with Levenshtein
abbreviation correction and multi-scale tiling.
"""

import sys
import io
import cv2
import numpy as np
import easyocr
from typing import Dict, List, Optional, Tuple, Any
from extraction.dimensions import DimensionExtractor


class OCREngine:
    # Standard architectural abbreviations lexicon
    ABBREVIATION_MAP = {
        "MBR": "MASTER BEDROOM",
        "M.BED": "MASTER BEDROOM",
        "BED": "BEDROOM",
        "BEDRM": "BEDROOM",
        "BATH": "BATHROOM",
        "DIBATH": "BATHROOM",
        "W/C": "WATER CLOSET",
        "WC": "WATER CLOSET",
        "TOI": "TOILET",
        "KIT": "KITCHEN",
        "KIT.": "KITCHEN",
        "LIV": "LIVING ROOM",
        "DIN": "DINING ROOM",
        "BALC": "BALCONY",
        "CORR": "CORRIDOR",
        "HALL": "HALLWAY",
        "WASIAREA": "WASH AREA",
        "WASH": "WASH AREA",
        "UTIL": "UTILITY ROOM",
        "STOR": "STORAGE",
        "GAR": "GARAGE",
        "FOY": "FOYER"
    }

    ROOM_TAXONOMY = {
        "bedroom": ["bedroom", "master bedroom", "bed", "m.bed", "mbr", "guest room", "children bedroom"],
        "bathroom": ["bathroom", "bath", "toilet", "wc", "water closet", "powder room", "ensuite", "wash"],
        "kitchen": ["kitchen", "kit", "pantry", "cooking"],
        "living_room": ["living room", "living", "great room", "drawing room", "family room", "lounge"],
        "dining_room": ["dining room", "dining", "din"],
        "corridor": ["corridor", "hallway", "hall", "passage", "entry", "foyer", "lobby"],
        "balcony": ["balcony", "balc", "terrace", "patio", "verandah", "deck", "porch"],
        "garage": ["garage", "carport", "parking"],
        "utility": ["utility", "laundry", "wash area", "storage", "stor"]
    }

    def __init__(self, gpu: bool = False):
        if sys.platform == "win32":
            # Guard against Windows cp1252 charmap crashes
            try:
                sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
                sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding="utf-8", errors="replace")
            except Exception:
                pass
        self.reader = easyocr.Reader(["en"], gpu=gpu, verbose=False)
        self.dim_extractor = DimensionExtractor()

    def correct_abbreviation(self, word: str) -> str:
        """Corrects known architectural shorthand and OCR typos."""
        clean = word.strip().upper()
        if clean in self.ABBREVIATION_MAP:
            return self.ABBREVIATION_MAP[clean]
        
        # Levenshtein distance 1 match
        for abbr, full in self.ABBREVIATION_MAP.items():
            if len(clean) == len(abbr):
                diff = sum(c1 != c2 for c1, c2 in zip(clean, abbr))
                if diff == 1:
                    return full
        return word

    def classify_room_label(self, text: str) -> Optional[str]:
        """Matches a recognized text string against standard room taxonomy."""
        normalized = self.correct_abbreviation(text).lower()
        for category, keywords in self.ROOM_TAXONOMY.items():
            for kw in keywords:
                if kw in normalized:
                    return category
        return None

    def read_image(self, img: np.ndarray, upscale_if_low_res: bool = True) -> List[Dict[str, Any]]:
        """
        Runs OCR on architectural image.
        Returns recognized entries with text, bbox, confidence, and semantic classification.
        """
        h, w = img.shape[:2]
        target_img = img

        # Multi-scale 2x upscaling if image has low DPI
        scale_factor = 1.0
        if upscale_if_low_res and (w < 800 or h < 800):
            scale_factor = 2.0
            target_img = cv2.resize(img, (int(w * scale_factor), int(h * scale_factor)), interpolation=cv2.INTER_CUBIC)

        raw_results = self.reader.readtext(target_img)
        entries = []

        for bbox, text, conf in raw_results:
            if conf < 0.25 or not text.strip():
                continue

            # Rescale bbox coordinates if upscaled
            adjusted_bbox = [[round(pt[0] / scale_factor, 1), round(pt[1] / scale_factor, 1)] for pt in bbox]
            centroid = [
                round(sum(pt[0] for pt in adjusted_bbox) / 4.0, 1),
                round(sum(pt[1] for pt in adjusted_bbox) / 4.0, 1)
            ]

            corrected_text = self.correct_abbreviation(text)
            room_class = self.classify_room_label(text)
            dim_parsed = self.dim_extractor.parse_dimension_string(text)

            entry = {
                "raw_text": text,
                "corrected_text": corrected_text,
                "bbox": adjusted_bbox,
                "centroid": centroid,
                "confidence": round(float(conf), 3),
                "is_room_label": room_class is not None,
                "room_category": room_class,
                "is_dimension": dim_parsed is not None,
                "dimension_data": dim_parsed
            }
            entries.append(entry)

        return entries
