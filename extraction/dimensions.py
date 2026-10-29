"""
Phase 4: Architectural Dimension Parsing, Unit Normalization, and Scale Estimation.
Parses imperial (feet-inches) and metric (m, mm) annotations, converts to normalized meters,
and estimates pixel-to-meter scale factors.
"""

import re
from typing import Dict, List, Optional, Tuple, Any


class DimensionExtractor:
    # Regex patterns for architectural dimensions
    # 1. Imperial: 12'-6", 10' - 4", 12'6", 10' 6 1/2"
    IMPERIAL_PATTERN = re.compile(
        r"""(?P<feet>\d+)\s*(?:['’]|ft\.?)\s*(?:[-–]\s*)?(?:(?P<inches>\d+)(?:\s*(?P<frac>\d+/\d+))?\s*["”]?)?|(?P<feet_dash>\d+)\s*[-–]\s*(?P<inches_dash>\d+)(?:\s*(?P<frac_dash>\d+/\d+))?\s*["”]?""",
        re.VERBOSE | re.IGNORECASE
    )
    
    # 2. Metric with explicit units: 4.2m, 3500mm, 4.20 m, 3.5x4.0m
    METRIC_PATTERN = re.compile(
        r"""(?P<val>\d+(?:\.\d+)?)\s*(?P<unit>mm|cm|m)\b""",
        re.IGNORECASE
    )

    # 3. Room dimensions product: 12x14, 10'0" x 12'6", 3.5 x 4.0
    DIM_PRODUCT_PATTERN = re.compile(
        r"""(?P<dim1>[0-9\.\'\-]+(?:\s*["”])?)\s*(?:x|X|\*)\s*(?P<dim2>[0-9\.\'\-]+(?:\s*["”])?)"""
    )

    @classmethod
    def parse_imperial(cls, text: str) -> Optional[float]:
        """Converts imperial string (e.g. 12'-6\", 10' - 4\", 12-6\") to normalized meters."""
        m = cls.IMPERIAL_PATTERN.search(text)
        if not m:
            return None
        if m.group("feet"):
            feet = float(m.group("feet"))
            inches = float(m.group("inches")) if m.group("inches") else 0.0
            frac = m.group("frac")
        else:
            feet = float(m.group("feet_dash"))
            inches = float(m.group("inches_dash")) if m.group("inches_dash") else 0.0
            frac = m.group("frac_dash")

        if frac:
            num, denom = frac.split("/")
            inches += float(num) / float(denom)
        total_inches = (feet * 12.0) + inches
        meters = total_inches * 0.0254
        return round(meters, 3)

    @classmethod
    def parse_metric(cls, text: str) -> Optional[float]:
        """Converts metric string (e.g. 4.2m, 3500mm) to normalized meters."""
        m = cls.METRIC_PATTERN.search(text)
        if not m:
            # Check for pure 4-digit millimeter number common in CAD (e.g. 3600, 4200)
            if text.strip().isdigit() and 1000 <= int(text.strip()) <= 15000:
                return round(float(text.strip()) / 1000.0, 3)
            return None
        val = float(m.group("val"))
        unit = m.group("unit").lower()
        if unit == "mm":
            return round(val / 1000.0, 3)
        elif unit == "cm":
            return round(val / 100.0, 3)
        elif unit == "m":
            return round(val, 3)
        return None

    @classmethod
    def parse_dimension_string(cls, text: str) -> Optional[Dict[str, Any]]:
        """Parses an arbitrary dimension string, returning normalized meters and metadata."""
        cleaned = text.strip()
        
        # Check product e.g. 12'x14' or 3.5 x 4.0
        prod_m = cls.DIM_PRODUCT_PATTERN.search(cleaned)
        if prod_m:
            d1_raw = prod_m.group("dim1")
            d2_raw = prod_m.group("dim2")
            v1 = cls.parse_imperial(d1_raw) or cls.parse_metric(d1_raw)
            v2 = cls.parse_imperial(d2_raw) or cls.parse_metric(d2_raw)
            # If plain numbers without unit, check if imperial or metric range
            if v1 is None and d1_raw.replace('.', '', 1).isdigit():
                num = float(d1_raw)
                v1 = round(num * 0.3048, 3) if num > 6.0 else round(num, 3) # heuristic ft vs m
            if v2 is None and d2_raw.replace('.', '', 1).isdigit():
                num = float(d2_raw)
                v2 = round(num * 0.3048, 3) if num > 6.0 else round(num, 3)

            if v1 and v2:
                return {
                    "raw": cleaned,
                    "type": "area_dimension_pair",
                    "dim1_m": v1,
                    "dim2_m": v2,
                    "area_m2": round(v1 * v2, 2),
                    "confidence": 0.90
                }

        # Check single metric
        v_metric = cls.parse_metric(cleaned)
        if v_metric is not None and 0.5 <= v_metric <= 50.0:
            return {
                "raw": cleaned,
                "type": "single_linear",
                "value_m": v_metric,
                "unit": "m",
                "confidence": 0.95
            }

        # Check single imperial
        v_imp = cls.parse_imperial(cleaned)
        if v_imp is not None and 0.5 <= v_imp <= 50.0:
            return {
                "raw": cleaned,
                "type": "single_linear",
                "value_m": v_imp,
                "unit": "ft-in",
                "confidence": 0.92
            }

        return None

    @classmethod
    def estimate_scale(cls, parsed_dimensions: List[Dict[str, Any]], pixel_lengths: List[float]) -> Optional[Dict[str, Any]]:
        """
        Estimates pixels_per_meter scale factor by correlating parsed dimensions
        with corresponding measured pixel lengths.
        """
        ratios = []
        for dim, px_len in zip(parsed_dimensions, pixel_lengths):
            val_m = dim.get("value_m") or dim.get("dim1_m")
            if val_m and val_m > 0 and px_len > 10:
                ppm = px_len / val_m
                if 10.0 <= ppm <= 500.0: # Plausible range: 10px/m to 500px/m
                    ratios.append(ppm)

        if not ratios:
            return None

        # Median ratio for robustness against outliers
        median_ppm = float(np.median(ratios)) if 'np' in globals() else float(sorted(ratios)[len(ratios)//2])
        return {
            "pixels_per_meter": round(median_ppm, 2),
            "sample_count": len(ratios),
            "confidence": min(round(0.60 + 0.10 * len(ratios), 2), 0.95),
            "method": "dimension_annotation_correlation"
        }
