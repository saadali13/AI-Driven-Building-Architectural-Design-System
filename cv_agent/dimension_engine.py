"""
Architectural Dimension & Scale Calibration Engine.

Parses architectural dimension strings:
- 14'-0" X 18'
- 17' X 11'
- 50'-0"
- 90'-0"
- 12'-6" x 14'-3"
- Metric dimensions (4.5m x 3.2m, 4500 x 3000 mm)

Provides:
- Dimension normalization to SI meters and imperial decimal feet.
- Scale calibration (px/foot, px/meter) across independent room measurements.
- Scale consistency scoring and conflict detection.
"""

import re
import math
from typing import Dict, List, Tuple, Any, Optional
import numpy as np

# Architectural dual dimension regex: e.g. 14'-0" X 18'-0", 14'-0" X 18', 14' x 16', 10'6" x 12'
DUAL_DIM_PATTERN = re.compile(
    r"""(?ix)
    (?P<w_ft>\d{1,3})\s*(?:'|ft|feet)?\s*(?:[\-])?\s*(?:(?P<w_in>\d{1,2}(?:\.\d+)?)\s*(?:"|in|inch|'')?)?
    \s*(?:[xX×\*]|by|and)\s*
    (?P<l_ft>\d{1,3})\s*(?:'|ft|feet)?\s*(?:[\-])?\s*(?:(?P<l_in>\d{1,2}(?:\.\d+)?)\s*(?:"|in|inch|'')?)?
    """
)

# Metric dual dimension regex: e.g. 4.5m x 3.2m or 4500 x 3200 mm
METRIC_DUAL_DIM_PATTERN = re.compile(
    r"""(?ix)
    (?P<w_val>\d+(?:\.\d+)?)\s*(?P<w_unit>m|mm|cm|meters)?
    \s*(?:[xX×\*])\s*
    (?P<l_val>\d+(?:\.\d+)?)\s*(?P<l_unit>m|mm|cm|meters)?
    """
)

# Single dimension regex: e.g. 50'-0", 90'-0", 30'
SINGLE_DIM_PATTERN = re.compile(
    r"""(?ix)
    ^(?P<ft>\d{1,3})\s*(?:'|ft|feet)?\s*(?:[\-])?\s*(?:(?P<in>\d{1,2}(?:\.\d+)?)\s*(?:"|in|inch|'')?)?$
    """
)


class ArchitecturalDimensionEngine:
    """
    Parses and standardizes architectural annotations and computes scale factors.
    """

    @staticmethod
    def parse_dimension_string(raw_text: str) -> Optional[Dict[str, Any]]:
        """
        Parses text for architectural dimension annotations.
        Returns structured dictionary if found, else None.
        """
        cleaned = raw_text.strip().replace("’", "'").replace("”", '"').replace("–", "-")

        # 1. Try dual imperial dimension (width x length)
        m = DUAL_DIM_PATTERN.search(cleaned)
        if m:
            w_ft = float(m.group("w_ft") or 0)
            w_in = float(m.group("w_in") or 0)
            l_ft = float(m.group("l_ft") or 0)
            l_in = float(m.group("l_in") or 0)

            total_w_ft = w_ft + (w_in / 12.0)
            total_l_ft = l_ft + (l_in / 12.0)

            total_w_m = total_w_ft * 0.3048
            total_l_m = total_l_ft * 0.3048

            return {
                "raw_text": raw_text,
                "dimension_type": "dual_room_dimension",
                "unit": "imperial_feet_inches",
                "width_ft": round(total_w_ft, 2),
                "length_ft": round(total_l_ft, 2),
                "width_m": round(total_w_m, 3),
                "length_m": round(total_l_m, 3),
                "normalized_text": f"{int(w_ft)}'-{int(w_in)}\" X {int(l_ft)}'-{int(l_in)}\"",
                "area_sqft": round(total_w_ft * total_l_ft, 2),
                "area_sqm": round(total_w_m * total_l_m, 2),
                "confidence": 0.90 if ('"' in cleaned or "'" in cleaned) else 0.70
            }

        # 2. Try metric dual dimension
        mm = METRIC_DUAL_DIM_PATTERN.search(cleaned)
        if mm and (mm.group("w_unit") or mm.group("l_unit") or "." in cleaned):
            w_val = float(mm.group("w_val"))
            l_val = float(mm.group("l_val"))
            unit_str = (mm.group("w_unit") or mm.group("l_unit") or "m").lower()

            if unit_str == "mm":
                w_m = w_val / 1000.0
                l_m = l_val / 1000.0
            elif unit_str == "cm":
                w_m = w_val / 100.0
                l_m = l_val / 100.0
            else:
                w_m = w_val
                l_m = l_val

            w_ft = w_m / 0.3048
            l_ft = l_m / 0.3048

            return {
                "raw_text": raw_text,
                "dimension_type": "dual_room_dimension",
                "unit": "metric",
                "width_ft": round(w_ft, 2),
                "length_ft": round(l_ft, 2),
                "width_m": round(w_m, 3),
                "length_m": round(l_m, 3),
                "normalized_text": f"{round(w_m, 2)}m X {round(l_m, 2)}m",
                "area_sqft": round(w_ft * l_ft, 2),
                "area_sqm": round(w_m * l_m, 2),
                "confidence": 0.85
            }

        # 3. Try single dimension (e.g. plot boundary 50'-0", 90'-0")
        sm = SINGLE_DIM_PATTERN.search(cleaned)
        if sm:
            ft = float(sm.group("ft") or 0)
            inch = float(sm.group("in") or 0)
            total_ft = ft + (inch / 12.0)
            total_m = total_ft * 0.3048

            return {
                "raw_text": raw_text,
                "dimension_type": "single_span",
                "unit": "imperial_feet_inches",
                "length_ft": round(total_ft, 2),
                "length_m": round(total_m, 3),
                "normalized_text": f"{int(ft)}'-{int(inch)}\"",
                "confidence": 0.90
            }

        return None

    @staticmethod
    def calibrate_scale(
        rooms: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Calculates scale calibration from room pixel dimensions vs parsed text dimensions.
        Computes scale consistency across multiple independent measurements.
        """
        ratios_px_per_ft = []
        references = []

        for r in rooms:
            norm_w_ft = r.get("normalized_width_ft")
            norm_l_ft = r.get("normalized_length_ft")
            bbox = r.get("pixel_bounding_box", [])

            if norm_w_ft and norm_l_ft and len(bbox) == 4:
                bw = abs(bbox[2] - bbox[0])
                bh = abs(bbox[3] - bbox[1])
                if bw > 15 and bh > 15 and norm_w_ft > 2.0 and norm_l_ft > 2.0:
                    # Match oriented dimensions
                    r1 = max(bw, bh) / max(norm_w_ft, norm_l_ft)
                    r2 = min(bw, bh) / min(norm_w_ft, norm_l_ft)
                    ratios_px_per_ft.extend([r1, r2])
                    references.append({
                        "room_id": r.get("room_id"),
                        "room_name": r.get("room_name"),
                        "text_dim": f"{norm_w_ft:.1f}' x {norm_l_ft:.1f}'",
                        "pixel_box": [bw, bh],
                        "estimated_px_per_ft": round((r1 + r2) / 2.0, 2)
                    })

        if not ratios_px_per_ft:
            return {
                "pixels_per_meter": None,
                "pixels_per_foot": None,
                "calibration_confidence": 0.0,
                "calibration_method": "uncalibrated_heuristic",
                "scale_consistency_error_pct": None,
                "calibration_references": []
            }

        median_px_per_ft = float(np.median(ratios_px_per_ft))
        std_px_per_ft = float(np.std(ratios_px_per_ft))
        consistency_error_pct = round((std_px_per_ft / max(0.1, median_px_per_ft)) * 100.0, 2)
        confidence = max(0.1, min(0.98, round(1.0 - (consistency_error_pct / 100.0), 2)))

        px_per_m = median_px_per_ft / 0.3048

        return {
            "pixels_per_meter": round(px_per_m, 2),
            "pixels_per_foot": round(median_px_per_ft, 2),
            "calibration_confidence": confidence,
            "calibration_method": "multi_room_dimension_regression",
            "scale_consistency_error_pct": consistency_error_pct,
            "calibration_references": references
        }
