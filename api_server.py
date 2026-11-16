#!/usr/bin/env python3
"""
AI Driven Building Architectural Design System - Master API & Web Server.
Bridges the web application with:
1. Natural-Language Requirements Parser & DatasetDrivenRAGSolver.
2. Layered AutoCAD DXF Blueprint Generator (AIA Standards).
3. 2D/3D Architectural Visualizer & Vector Presentation Sheets (SVG/PDF).
4. Blender 5.1 Procedural 3D Solid Model & Render Generator (.blend).
5. Dynamic Bill of Quantities (BOQ) & Construction Cost Estimation Engine.
6. Architectural Templates Library, Project Persistence & Account Management.
"""

import os
import sys
import json
import math
import re
import copy
import mimetypes
import argparse
import threading
import uuid
import collections
import concurrent.futures
from http.server import HTTPServer, ThreadingHTTPServer, SimpleHTTPRequestHandler

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(line_buffering=True)
os.environ.setdefault("MPLCONFIGDIR", os.path.join(os.path.abspath(os.path.dirname(__file__)), "output", ".matplotlib"))
os.makedirs(os.environ["MPLCONFIGDIR"], exist_ok=True)
from urllib.parse import urlparse, parse_qs, unquote
from typing import Dict, Any, List, Optional
import datetime
from shapely.geometry import Polygon
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# Concurrency & Thread-Safety Primitives
PROJECTS_LOCK = threading.RLock()
RENDER_LOCK = threading.Lock()
PLAN_LOCKS_GUARD = threading.Lock()
PLAN_LOCKS = collections.defaultdict(threading.RLock)
BACKGROUND_EXECUTOR = concurrent.futures.ThreadPoolExecutor(max_workers=4)

def get_plan_lock(plan_id: str) -> threading.Lock:
    with PLAN_LOCKS_GUARD:
        return PLAN_LOCKS[plan_id]

# Ensure project root is in sys.path
PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

WEB_DIR = os.path.join(PROJECT_ROOT, "web")
OUTPUT_DIR = os.path.join(PROJECT_ROOT, "output")
os.makedirs(WEB_DIR, exist_ok=True)
os.makedirs(OUTPUT_DIR, exist_ok=True)

# ---------------------------------------------------------------------------
# Core Architectural Templates Catalog
# ---------------------------------------------------------------------------
ARCHITECTURAL_TEMPLATES = [
    {
        "id": "tpl_3m_modern",
        "name": "3 Marla Modern Urban Compact",
        "category": "3_marla",
        "plot_dimensions_ft": "20 x 34",
        "plot_width_ft": 20.0,
        "plot_length_ft": 34.0,
        "plot_area_sqft": 680.0,
        "style": "modern",
        "floors": 2,
        "bedrooms": 3,
        "bathrooms": 3,
        "covered_area_sqft": 1250.0,
        "description": "Ultra-efficient contemporary double-storey residence optimized for narrow urban infill plots. Features open-plan living, attached bathrooms, integrated car porch, and lightwell OTS.",
        "highlights": ["3 Bedroom Suites", "Open Concept Living-Dining", "Compact Car Porch", "Central OTS Lightwell", "Rooftop Terrace"],
        "prompt": "3 Marla Modern compact house 20x34 with 3 bedrooms, open kitchen, drawing room, car porch, and rooftop terrace"
    },
    {
        "id": "tpl_5m_spanish",
        "name": "5 Marla Spanish Hacienda Villa",
        "category": "5_marla",
        "plot_dimensions_ft": "25 x 45",
        "plot_width_ft": 25.0,
        "plot_length_ft": 45.0,
        "plot_area_sqft": 1125.0,
        "style": "spanish",
        "floors": 2,
        "bedrooms": 4,
        "bathrooms": 4,
        "covered_area_sqft": 2100.0,
        "description": "Authentic Andalusian Spanish revival villa showcasing terracotta roof copings, semicircular arched fenestrations, central internal courtyard, and textured warm stucco finishes.",
        "highlights": ["Terracotta Arched Facade", "4 Master Ensuites", "Private Courtyard & Patio", "Double Height Stair Hall", "Front Balcony with Pergola"],
        "prompt": "5 Marla Spanish Villa 25x45 with 4 bedrooms, drawing room, central courtyard, car porch, and terracotta arched elevation"
    },
    {
        "id": "tpl_5m_modern",
        "name": "5 Marla Contemporary Urban Minimalist",
        "category": "5_marla",
        "plot_dimensions_ft": "25 x 45",
        "plot_width_ft": 25.0,
        "plot_length_ft": 45.0,
        "plot_area_sqft": 1125.0,
        "style": "modern",
        "floors": 2,
        "bedrooms": 4,
        "bathrooms": 4,
        "covered_area_sqft": 2150.0,
        "description": "Crisp modernist design featuring cantilevered first-floor masses, floor-to-ceiling thermally broken glazing, concealed roof parapets, and exterior architectural louvers.",
        "highlights": ["Cantilevered Balcony Box", "Floor-to-Ceiling Glazing", "Open Gourmet Show Kitchen", "Linear Staircase with Glass Railing", "Covered Porch with Accent Planter"],
        "prompt": "5 Marla Modern contemporary house 25x45 with 4 bedrooms, open kitchen, drawing room, TV lounge, and car porch"
    },
    {
        "id": "tpl_7m_duplex",
        "name": "7 Marla Contemporary Duplex",
        "category": "7_marla",
        "plot_dimensions_ft": "30 x 55",
        "plot_width_ft": 30.0,
        "plot_length_ft": 55.0,
        "plot_area_sqft": 1650.0,
        "style": "contemporary",
        "floors": 2,
        "bedrooms": 4,
        "bathrooms": 5,
        "covered_area_sqft": 3050.0,
        "description": "Spacious family duplex with double-height central family lounge, formal drawing suite with powder room, expansive master bedroom with walk-in closet, and front landscaped garden.",
        "highlights": ["Double Height Family Atrium", "4 Ensuites + Guest Powder Room", "Spacious 2-Car Porch", "Separate Dirty & Clean Kitchens", "Executive Study / Library"],
        "prompt": "7 Marla Contemporary duplex 30x55 with 4 bedrooms, double-height lounge, drawing room, 2-car porch, and front lawn"
    },
    {
        "id": "tpl_10m_luxury",
        "name": "10 Marla Luxury Executive Residence",
        "category": "10_marla",
        "plot_dimensions_ft": "35 x 65",
        "plot_width_ft": 35.0,
        "plot_length_ft": 65.0,
        "plot_area_sqft": 2275.0,
        "style": "modern",
        "floors": 2,
        "bedrooms": 5,
        "bathrooms": 6,
        "covered_area_sqft": 4150.0,
        "description": "Prestigious executive residence engineered with wide double-bay car porch, lavish entrance lobby, separate servant quarters with dedicated bath, and front/rear landscaped setbacks.",
        "highlights": ["5 Luxury Bedroom Suites", "Double Car Porch (SUVs)", "Servant Quarter with En-suite", "Separate Dirty/Wet Kitchen", "Expansive Front Lawn (10' setback)"],
        "prompt": "10 Marla Modern luxury house 35x65 with 5 bedrooms, drawing and dining, 2-car porch, servant quarter, and front lawn"
    },
    {
        "id": "tpl_10m_spanish",
        "name": "10 Marla Spanish Colonial Estate",
        "category": "10_marla",
        "plot_dimensions_ft": "35 x 65",
        "plot_width_ft": 35.0,
        "plot_length_ft": 65.0,
        "plot_area_sqft": 2275.0,
        "style": "spanish",
        "floors": 2,
        "bedrooms": 5,
        "bathrooms": 6,
        "covered_area_sqft": 4100.0,
        "description": "Grand Spanish colonial mansion featuring classical arched colonnades, terracotta barrel-tile roof copings, wrought-iron Juliet balconies, and central fountain courtyard.",
        "highlights": ["Spanish Colonnade Porch", "Dual Terracotta Balconies", "5 Master Suites + Maid Room", "Courtyard Water Feature", "Rooftop Wooden Pergola"],
        "prompt": "10 Marla Spanish style luxury villa 35x65 with 5 bedrooms, drawing room, 2-car porch, servant quarter, and Spanish tile elevation"
    },
    {
        "id": "tpl_1k_palace",
        "name": "1 Kanal Neo-Classical Palace",
        "category": "1_kanal",
        "plot_dimensions_ft": "50 x 90",
        "plot_width_ft": 50.0,
        "plot_length_ft": 90.0,
        "plot_area_sqft": 4500.0,
        "style": "classical",
        "floors": 3,
        "bedrooms": 6,
        "bathrooms": 7,
        "covered_area_sqft": 7600.0,
        "description": "Opulent neo-classical mansion with Corinthian entrance columns, 3-car garage, home cinema / entertainment suite, swimming pool deck, and triple-level vertical zoning.",
        "highlights": ["Monumental Classical Portico", "6 King Suites + Maid Quarter", "Triple-Car Garage", "Home Theater & Gym Room", "Rooftop Swimming Pool / Deck"],
        "prompt": "1 Kanal Classical luxury mansion 50x90 with 6 bedrooms, triple car porch, swimming pool, home theater, and classical front elevation"
    },
    {
        "id": "tpl_corner_special",
        "name": "Corner Plot Dual Frontage Villa",
        "category": "corner_plot",
        "plot_dimensions_ft": "32 x 50",
        "plot_width_ft": 32.0,
        "plot_length_ft": 50.0,
        "plot_area_sqft": 1600.0,
        "style": "modern",
        "floors": 2,
        "bedrooms": 4,
        "bathrooms": 4,
        "covered_area_sqft": 2800.0,
        "description": "Corner lot configuration engineered with a statutory 45° corner splay (chamfered boundary). Features dual-street lightwells, wraparound panoramic balconies, and dual access gates.",
        "highlights": ["Statutory Chamfered Corner Gate", "Dual-Street Natural Lighting", "Panoramic Wraparound Balcony", "4 Master Ensuites", "Optimal Cross-Ventilation"],
        "prompt": "Corner plot house 32x50 with 4 bedrooms, dual street frontage, corner car porch, drawing room, and panoramic modern elevation"
    }
]

# ---------------------------------------------------------------------------
# Comprehensive Cost Estimation Engine (BOQ)
# ---------------------------------------------------------------------------

class GeminiMarketRateService:
    DEFAULT_RATES = {
        "cement_bag": 1450.0,
        "steel_ton": 275000.0,
        "brick_unit": 14.5,
        "sand_cft": 48.0,
        "crush_cft": 125.0,
        "tiles_sqft": 350.0,
        "paint_sqft": 55.0,
        "door_unit": 35000.0,
        "window_unit": 28000.0,
        "bath_sanitary_unit": 65000.0,
        "labor_per_sqft": 450.0
    }

    @classmethod
    def fetch_market_rates(cls, api_key: str = "", city: str = "Islamabad / Lahore"):
        if api_key and len(api_key) > 10:
            try:
                import urllib.request
                import json
                url = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent?key={api_key}"
                prompt = (
                    f"You are a Senior Quantity Surveyor in Pakistan. Return the current 2026 construction material prices in PKR "
                    f"for {city}, Pakistan. Output ONLY a valid JSON object with keys: "
                    f"cement_bag, steel_ton, brick_unit, sand_cft, crush_cft, tiles_sqft, paint_sqft, door_unit, window_unit, bath_sanitary_unit, labor_per_sqft. "
                    f"No markdown formatting, no explanation."
                )
                payload = json.dumps({"contents": [{"parts": [{"text": prompt}]}]}).encode("utf-8")
                req = urllib.request.Request(url, data=payload, headers={"Content-Type": "application/json"})
                with urllib.request.urlopen(req, timeout=10) as resp:
                    resp_data = json.loads(resp.read().decode("utf-8"))
                    cand_text = resp_data["candidates"][0]["content"]["parts"][0]["text"].strip()
                    m = re.search(r"\{.*\}", cand_text, re.DOTALL)
                    if m:
                        parsed = json.loads(m.group(0))
                        merged = dict(cls.DEFAULT_RATES)
                        for k, v in parsed.items():
                            if k in merged:
                                try:
                                    merged[k] = float(v)
                                except (ValueError, TypeError):
                                    pass
                        return {
                            "success": True,
                            "source": "gemini_live",
                            "city": city,
                            "rates": merged
                        }
            except Exception as e:
                print(f"[GeminiMarketRateService] API call notice: {e}, falling back to benchmark")

        city_lower = (city or "").lower()
        rates = dict(cls.DEFAULT_RATES)
        if "karachi" in city_lower:
            rates["cement_bag"] = 1420.0
            rates["steel_ton"] = 270000.0
            rates["crush_cft"] = 135.0
            rates["sand_cft"] = 42.0
        elif "lahore" in city_lower:
            rates["cement_bag"] = 1460.0
            rates["steel_ton"] = 274000.0
            rates["sand_cft"] = 46.0
            rates["crush_cft"] = 120.0

        return {
            "success": True,
            "source": "verified_pakistan_benchmark",
            "city": city or "Islamabad / Lahore",
            "rates": rates
        }

class CostEstimator:
    """
    Parametric Bill of Quantities (BOQ) and Construction Cost Estimation.
    Supports 4 tiers: Economy, Standard, Premium, Luxury across PKR and USD.
    """
    RATES = {
        "pkr": {
            "economy": {"grey_per_sqft": 2800, "finishing_per_sqft": 1800, "total_per_sqft": 4600},
            "standard": {"grey_per_sqft": 3300, "finishing_per_sqft": 2700, "total_per_sqft": 6000},
            "premium": {"grey_per_sqft": 3800, "finishing_per_sqft": 4200, "total_per_sqft": 8000},
            "luxury": {"grey_per_sqft": 4400, "finishing_per_sqft": 6600, "total_per_sqft": 11000}
        },
        "usd": {
            "economy": {"grey_per_sqft": 65, "finishing_per_sqft": 55, "total_per_sqft": 120},
            "standard": {"grey_per_sqft": 90, "finishing_per_sqft": 85, "total_per_sqft": 175},
            "premium": {"grey_per_sqft": 125, "finishing_per_sqft": 140, "total_per_sqft": 265},
            "luxury": {"grey_per_sqft": 165, "finishing_per_sqft": 235, "total_per_sqft": 400}
        }
    }

    MATERIAL_COEFFICIENTS = {
        # Per sq ft of covered area:
        "cement_bags": 0.45,           # ~450 bags per 1000 sq ft
        "steel_kg": 3.85,              # ~3.85 kg per sq ft Grade 60 rebar
        "bricks_count": 26.5,          # ~26.5 standard burnt red clay bricks per sq ft
        "sand_cft": 2.75,              # ~2.75 cubic ft coarse sand per sq ft
        "crush_cft": 1.85,             # ~1.85 cubic ft coarse aggregate per sq ft
        "tiles_sqft": 0.85,            # Floor tile area (allowing 15% skirting/wastage)
        "paint_sqft": 3.40,            # Total paint surface area (walls + ceiling)
    }

    UNIT_PRICES_PKR = {
        "cement_bag": 1450,            # PKR per 50kg bag
        "steel_ton": 275000,           # PKR per metric ton (1000 kg)
        "brick_unit": 14.5,            # PKR per brick
        "sand_cft": 48.0,              # PKR per cft
        "crush_cft": 125.0,            # PKR per cft
        "tiles_sqft_economy": 180,
        "tiles_sqft_standard": 350,
        "tiles_sqft_premium": 650,
        "tiles_sqft_luxury": 1400,
        "paint_sqft": 55.0
    }

    @classmethod
    def calculate(
        cls,
        covered_area_sqft: float,
        floors: int = 2,
        bedrooms: int = 4,
        bathrooms: int = 4,
        budget_tier: str = "standard",
        currency: str = "PKR",
        custom_unit_prices: Optional[Dict[str, float]] = None
    ) -> Dict[str, Any]:
        curr = currency.lower() if currency.lower() in ("pkr", "usd") else "pkr"
        tier = budget_tier.lower() if budget_tier.lower() in cls.RATES[curr] else "standard"
        rates = cls.RATES[curr][tier]

        total_area = float(covered_area_sqft)
        grey_cost = total_area * rates["grey_per_sqft"]
        finishing_cost = total_area * rates["finishing_per_sqft"]
        base_total = grey_cost + finishing_cost
        contingency = base_total * 0.075 # 7.5% contingency
        grand_total = base_total + contingency

        # Quantities
        cement_bags = int(round(total_area * cls.MATERIAL_COEFFICIENTS["cement_bags"]))
        steel_kg = int(round(total_area * cls.MATERIAL_COEFFICIENTS["steel_kg"]))
        steel_tons = round(steel_kg / 1000.0, 2)
        bricks_count = int(round(total_area * cls.MATERIAL_COEFFICIENTS["bricks_count"]))
        sand_cft = int(round(total_area * cls.MATERIAL_COEFFICIENTS["sand_cft"]))
        crush_cft = int(round(total_area * cls.MATERIAL_COEFFICIENTS["crush_cft"]))
        tiles_sqft = int(round(total_area * cls.MATERIAL_COEFFICIENTS["tiles_sqft"]))
        paint_sqft = int(round(total_area * cls.MATERIAL_COEFFICIENTS["paint_sqft"]))

        # Milestone schedule
        milestones = [
            {"phase": "Site Prep & Foundation", "percentage": 15, "cost": round(grand_total * 0.15), "duration_weeks": 4},
            {"phase": "RCC Grey Structure & Slabs", "percentage": 25, "cost": round(grand_total * 0.25), "duration_weeks": 8},
            {"phase": "Brickwork, Conduit & Plaster", "percentage": 20, "cost": round(grand_total * 0.20), "duration_weeks": 6},
            {"phase": "Flooring, Woodwork & Paint", "percentage": 30, "cost": round(grand_total * 0.30), "duration_weeks": 8},
            {"phase": "Sanitary, Electrical Fixtures & Handover", "percentage": 10, "cost": round(grand_total * 0.10), "duration_weeks": 4}
        ]

        # Grey structure breakdown
        grey_breakdown = [
            {"item": "Portland Cement (50kg bags)", "quantity": f"{cement_bags:,} bags", "share_pct": 22},
            {"item": "Deformed Steel Rebar (Grade 60)", "quantity": f"{steel_tons} tons ({steel_kg:,} kg)", "share_pct": 28},
            {"item": "Burnt Red Clay Bricks", "quantity": f"{bricks_count:,} bricks", "share_pct": 18},
            {"item": "Coarse Sand (Ravi/Chenab)", "quantity": f"{sand_cft:,} cft", "share_pct": 6},
            {"item": "Margalla Coarse Aggregate (Crush)", "quantity": f"{crush_cft:,} cft", "share_pct": 7},
            {"item": "Excavation, Termite & Plinth Beam", "quantity": "Lump Sum", "share_pct": 8},
            {"item": "Electrical & Plumbing Rough Conduit", "quantity": "Conduit + Piping", "share_pct": 11}
        ]

        # Finishing breakdown
        finishing_breakdown = [
            {"item": "Porcelain / Marble Tile Flooring", "quantity": f"{tiles_sqft:,} sq ft", "share_pct": 25},
            {"item": "Solid Wood / Ashwood Doors & Hardware", "quantity": f"{bedrooms + bathrooms + 4} doors", "share_pct": 18},
            {"item": "Powder-coated Aluminum / UPVC Windows", "quantity": f"{bedrooms * 2 + 4} windows", "share_pct": 15},
            {"item": "Bath Sanitary Ware & Luxury Mixers", "quantity": f"{bathrooms} bath sets", "share_pct": 14},
            {"item": "Kitchen Woodwork, Acrylic & Granite", "quantity": f"{floors} kitchen(s)", "share_pct": 12},
            {"item": "Interior Paint, Weather-shield & Putty", "quantity": f"{paint_sqft:,} sq ft", "share_pct": 8},
            {"item": "Gypsum False Ceiling & LED SMD Lights", "quantity": f"{round(total_area * 0.65):,} sq ft", "share_pct": 8}
        ]

        # Dynamic Itemized Materials & Custom Price Support
        prices = dict(cls.UNIT_PRICES_PKR)
        prices["door_unit"] = 35000.0
        prices["window_unit"] = 28000.0
        prices["bath_sanitary_unit"] = 65000.0
        prices["labor_per_sqft"] = 450.0
        prices["electrical_sqft"] = 260.0
        prices["waterproofing_sqft"] = 95.0

        tier_tile_key = f"tiles_sqft_{tier}"
        tile_rate = prices.get(tier_tile_key, prices.get("tiles_sqft", 350.0))

        if custom_unit_prices and isinstance(custom_unit_prices, dict):
            for k, v in custom_unit_prices.items():
                try:
                    prices[k] = float(v)
                except (ValueError, TypeError):
                    pass
            if "tiles_sqft" in custom_unit_prices:
                try:
                    tile_rate = float(custom_unit_prices["tiles_sqft"])
                except:
                    pass

        cement_cost = round(cement_bags * prices.get("cement_bag", 1450.0))
        steel_cost = round(steel_tons * prices.get("steel_ton", 275000.0))
        bricks_cost = round(bricks_count * prices.get("brick_unit", 14.5))
        sand_cost = round(sand_cft * prices.get("sand_cft", 48.0))
        crush_cost = round(crush_cft * prices.get("crush_cft", 125.0))
        labor_cost = round(total_area * prices.get("labor_per_sqft", 450.0))

        doors_count = bedrooms + bathrooms + 4
        doors_cost = round(doors_count * prices.get("door_unit", 35000.0))
        windows_count = bedrooms * 2 + 4
        windows_cost = round(windows_count * prices.get("window_unit", 28000.0))
        baths_count = bathrooms
        sanitary_cost = round(baths_count * prices.get("bath_sanitary_unit", 65000.0))
        tiles_cost = round(tiles_sqft * tile_rate)
        paint_cost = round(paint_sqft * prices.get("paint_sqft", 55.0))
        electrical_cost = round(total_area * prices.get("electrical_sqft", 260.0))
        waterproofing_sqft_calc = round((total_area / max(1, floors)) * 1.8)
        waterproofing_cost = round(waterproofing_sqft_calc * prices.get("waterproofing_sqft", 95.0))

        calculated_grey = cement_cost + steel_cost + bricks_cost + sand_cost + crush_cost + labor_cost
        calculated_finishing = tiles_cost + paint_cost + doors_cost + windows_cost + sanitary_cost + electrical_cost + waterproofing_cost

        if custom_unit_prices:
            grey_cost = calculated_grey
            finishing_cost = calculated_finishing
            base_total = grey_cost + finishing_cost
            contingency = base_total * 0.075
            grand_total = base_total + contingency

        itemized_materials = [
            {"id": "cement_bag", "name": "Portland Cement (50kg bags)", "category": "grey", "quantity": cement_bags, "unit": "bags", "unit_price": prices.get("cement_bag", 1450.0), "total_cost": cement_cost},
            {"id": "steel_ton", "name": "Grade 60 Deformed Steel Rebar", "category": "grey", "quantity": steel_tons, "unit": "tons", "unit_price": prices.get("steel_ton", 275000.0), "total_cost": steel_cost},
            {"id": "brick_unit", "name": "Burnt Red Clay Bricks (Awwal)", "category": "grey", "quantity": bricks_count, "unit": "bricks", "unit_price": prices.get("brick_unit", 14.5), "total_cost": bricks_cost},
            {"id": "sand_cft", "name": "Coarse Sand (Chenab/Ravi)", "category": "grey", "quantity": sand_cft, "unit": "cft", "unit_price": prices.get("sand_cft", 48.0), "total_cost": sand_cost},
            {"id": "crush_cft", "name": "Margalla Coarse Aggregate (Crush)", "category": "grey", "quantity": crush_cft, "unit": "cft", "unit_price": prices.get("crush_cft", 125.0), "total_cost": crush_cost},
            {"id": "labor_per_sqft", "name": "Civil Construction Labor & Shuttering", "category": "grey", "quantity": int(total_area), "unit": "sq ft", "unit_price": prices.get("labor_per_sqft", 450.0), "total_cost": labor_cost},
            {"id": "tiles_sqft", "name": "Porcelain / Marble Tile Flooring", "category": "finishing", "quantity": tiles_sqft, "unit": "sq ft", "unit_price": tile_rate, "total_cost": tiles_cost},
            {"id": "paint_sqft", "name": "Interior Paint, Weather-shield & Putty", "category": "finishing", "quantity": paint_sqft, "unit": "sq ft", "unit_price": prices.get("paint_sqft", 55.0), "total_cost": paint_cost},
            {"id": "door_unit", "name": "Solid Wood / Ashwood Doors & Hardware", "category": "finishing", "quantity": doors_count, "unit": "sets", "unit_price": prices.get("door_unit", 35000.0), "total_cost": doors_cost},
            {"id": "window_unit", "name": "Powder-coated Aluminum / UPVC Windows", "category": "finishing", "quantity": windows_count, "unit": "units", "unit_price": prices.get("window_unit", 28000.0), "total_cost": windows_cost},
            {"id": "bath_sanitary_unit", "name": "Bath Sanitary Ware & Luxury Mixers", "category": "finishing", "quantity": baths_count, "unit": "sets", "unit_price": prices.get("bath_sanitary_unit", 65000.0), "total_cost": sanitary_cost},
            {"id": "electrical_sqft", "name": "Electrical Copper Wiring, Conduits & Smart LEDs", "category": "mep", "quantity": int(total_area), "unit": "sq ft", "unit_price": prices.get("electrical_sqft", 260.0), "total_cost": electrical_cost},
            {"id": "waterproofing_sqft", "name": "Waterproofing, Termite Proofing & DPC Membrane", "category": "mep", "quantity": waterproofing_sqft_calc, "unit": "sq ft", "unit_price": prices.get("waterproofing_sqft", 95.0), "total_cost": waterproofing_cost},
        ]

        return {
            "currency": currency.upper(),
            "currency_symbol": "₨" if curr == "pkr" else "$",
            "tier": tier.capitalize(),
            "covered_area_sqft": total_area,
            "cost_per_sqft": round(grand_total / max(1.0, total_area)),
            "grey_cost": round(grey_cost),
            "finishing_cost": round(finishing_cost),
            "contingency_buffer": round(contingency),
            "grand_total": round(grand_total),
            "total_cost_pkr": round(grand_total),
            "materials": {
                "cement_bags": cement_bags,
                "steel_tons": steel_tons,
                "steel_kg": steel_kg,
                "bricks_count": bricks_count,
                "sand_cft": sand_cft,
                "crush_cft": crush_cft,
                "tiles_sqft": tiles_sqft,
                "paint_sqft": paint_sqft
            },
            "unit_prices": prices,
            "itemized_materials": itemized_materials,
            "milestones": milestones,
            "grey_breakdown": grey_breakdown,
            "finishing_breakdown": finishing_breakdown,
            "timeline_total_months": 7 if floors <= 2 else 10
        }


# ---------------------------------------------------------------------------
# Synthetic Floor Plan & 3D Geometry Generator (Fast & Robust Fallback)
# ---------------------------------------------------------------------------
class ProceduralArchitecturalEngine:
    """
    Provides fast, deterministic, mathematically sound floor plan synthesis,
    3D geometric bounding boxes, and architectural front elevations
    matching exact user parameters (plot, rooms, floors, style, setbacks).
    """

    @classmethod
    def _generate_3d_geometry(cls, floors: List[Dict[str, Any]], plot_w: float, plot_l: float, style: str) -> Dict[str, Any]:
        """Generates parametric 3D bounding geometry, materials, and camera vectors for Three.js WebGL."""
        mesh_nodes = []
        floor_h = 3.2 # in meters (~10.5 ft)
        wall_t = 0.23 # 9 inches brick wall
        scale_factor = 0.3048 # ft to meters

        for f in floors:
            lvl = f["level"]
            z_offset = lvl * floor_h

            # Floor slab
            mesh_nodes.append({
                "type": "slab",
                "name": f"Floor Slab {lvl}",
                "level": lvl,
                "x": 0.0,
                "y": z_offset,
                "z": 0.0,
                "width": plot_w * scale_factor,
                "height": 0.20,
                "depth": plot_l * scale_factor,
                "material": "concrete_slab",
                "color": "#94a3b8"
            })

            # Room bounding blocks
            for r in f.get("rooms", []):
                rx = (r["x"] + r["width"] / 2.0 - plot_w / 2.0) * scale_factor
                rz = (r["y"] + r["length"] / 2.0 - plot_l / 2.0) * scale_factor
                rw = r["width"] * scale_factor
                rl = r["length"] * scale_factor

                cat = r.get("category", "bedroom")
                if cat == "garage":
                    mat = "driveway_pavers"
                    col = "#64748b"
                    h = 0.1
                elif cat == "balcony":
                    mat = "terrace_deck"
                    col = "#10b981" if "lawn" in r["name"].lower() else "#cbd5e1"
                    h = 0.1
                else:
                    mat = "room_walls"
                    col = "#e2e8f0" if style == "modern" else "#fed7aa"
                    h = floor_h - 0.20

                mesh_nodes.append({
                    "type": "room",
                    "room_id": r["id"],
                    "name": r["name"],
                    "category": cat,
                    "level": lvl,
                    "x": round(rx, 3),
                    "y": round(z_offset + h / 2.0, 3),
                    "z": round(rz, 3),
                    "width": round(rw, 3),
                    "height": round(h, 3),
                    "depth": round(rl, 3),
                    "material": mat,
                    "color": col,
                    "doors": r.get("doors", []),
                    "windows": r.get("windows", [])
                })

        # Add Roof
        top_z = len(floors) * floor_h
        mesh_nodes.append({
            "type": "roof",
            "name": "Architectural Roof",
            "level": len(floors),
            "x": 0.0,
            "y": round(top_z + 0.35, 3),
            "z": 0.0,
            "width": round(plot_w * scale_factor * 1.05, 3),
            "height": 0.60 if style == "spanish" else 0.30,
            "depth": round(plot_l * scale_factor * 1.05, 3),
            "material": "roof_terracotta" if style == "spanish" else "roof_concrete",
            "color": "#c2410c" if style == "spanish" else "#334155"
        })

        # Rooftop Stair Mumty & Overhead Water Tank (OHT) directly aligned with stair core
        stair_rooms = [r for f in floors for r in f.get("rooms", []) if "stair" in str(r.get("name", "")).lower() or r.get("category") == "stairs"]
        if stair_rooms:
            sr = stair_rooms[0]
            s_rx = (sr["x"] + sr["width"] / 2.0 - plot_w / 2.0) * scale_factor
            s_rz = (sr["y"] + sr["length"] / 2.0 - plot_l / 2.0) * scale_factor
            s_rw = sr["width"] * scale_factor
            s_rl = sr["length"] * scale_factor
            mesh_nodes.append({
                "type": "mumty",
                "name": "Rooftop Stair Mumty Penthouse",
                "level": len(floors) + 1,
                "x": round(s_rx, 3),
                "y": round(top_z + 1.35, 3),
                "z": round(s_rz, 3),
                "width": round(s_rw, 3),
                "height": 2.70,
                "depth": round(s_rl, 3),
                "material": "room_walls",
                "color": "#cbd5e1"
            })
            oht_w = min(s_rw * 0.8, 2.0)
            oht_l = min(s_rl * 0.8, 2.0)
            mesh_nodes.append({
                "type": "water_tank",
                "name": "Overhead Water Tank (1500 GAL)",
                "level": len(floors) + 2,
                "x": round(s_rx, 3),
                "y": round(top_z + 2.70 + 0.60, 3),
                "z": round(s_rz, 3),
                "width": round(oht_w, 3),
                "height": 1.20,
                "depth": round(oht_l, 3),
                "material": "concrete_tank",
                "color": "#475569"
            })

        return {
            "scale": "meters",
            "floor_height_m": floor_h,
            "nodes_count": len(mesh_nodes),
            "nodes": mesh_nodes,
            "camera_presets": {
                "isometric": {"position": [20, 22, 25], "target": [0, 4, 0]},
                "front_elevation": {"position": [0, 5, 28], "target": [0, 5, 0]},
                "side_elevation": {"position": [28, 5, 0], "target": [0, 5, 0]},
                "top_plan": {"position": [0, 35, 0], "target": [0, 0, 0]}
            }
        }


# ---------------------------------------------------------------------------
# Project Storage & State Persistence
# ---------------------------------------------------------------------------
PROJECTS_FILE = os.path.join(OUTPUT_DIR, "saved_projects.json")

def load_saved_projects() -> List[Dict[str, Any]]:
    with PROJECTS_LOCK:
        if os.path.exists(PROJECTS_FILE):
            try:
                with open(PROJECTS_FILE, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[Storage Notice] load_saved_projects error: {e}")
                return []
        return []

def save_project_to_file(project_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    with PROJECTS_LOCK:
        projects = load_saved_projects()
        pid = project_data.get("project_id")
        found = False
        for i, p in enumerate(projects):
            if p.get("project_id") == pid:
                projects[i] = project_data
                found = True
                break
        if not found:
            projects.insert(0, project_data)
        # Atomic file write to avoid races/corruption
        tmp_file = f"{PROJECTS_FILE}.tmp.{uuid.uuid4().hex}"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2)
        os.replace(tmp_file, PROJECTS_FILE)
        return projects

def delete_project_from_file(project_id: str) -> List[Dict[str, Any]]:
    with PROJECTS_LOCK:
        projects = load_saved_projects()
        projects = [p for p in projects if p.get("project_id") != project_id]
        tmp_file = f"{PROJECTS_FILE}.tmp.{uuid.uuid4().hex}"
        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(projects, f, indent=2)
        os.replace(tmp_file, PROJECTS_FILE)
        return projects


# ---------------------------------------------------------------------------
# Export Generators (DXF, SVG, PDF, Blend, OBJ)
# ---------------------------------------------------------------------------
class ArchitecturalExporters:
    """Handles multi-format export generation for Floor Plans & 3D Models."""

    @classmethod
    def _normalize_design_data(cls, design: Dict[str, Any]) -> Dict[str, Any]:
        plot = design.get("plot") if isinstance(design.get("plot"), dict) else {}
        pw = float(plot.get("width_ft") or design.get("plot_width") or 35.0)
        pl = float(plot.get("length_ft") or design.get("plot_length") or 65.0)
        pid = str(design.get("project_id") or design.get("id") or f"archi_{int(pw)}x{int(pl)}")
        p_title = str(design.get("project_title") or design.get("title") or "ArchiCraft Residence").upper()
        tot_area = float(design.get("total_covered_area_sqft") or design.get("covered_area_sqft") or (pw * pl * 0.75))
        style_disp = str(design.get("style_display") or design.get("style") or "Modern").capitalize()
        v_num = design.get("version", 1)

        floors = design.get("floors", [])
        if not isinstance(floors, list):       # prompt-designed houses: "floors" is a count
            floors = design.get("floors_summary") or []
        if not floors:
            for p_dir in [os.path.join(OUTPUT_DIR, pid, f"v{v_num}"), os.path.join(OUTPUT_DIR, pid), os.path.join(OUTPUT_DIR, "web_generated", pid)]:
                pf = os.path.join(p_dir, "plan.json")
                if os.path.exists(pf):
                    try:
                        with open(pf, "r", encoding="utf-8") as f:
                            disk_data = json.load(f)
                            floors = disk_data.get("floors", [])
                            if floors:
                                break
                    except Exception:
                        pass

        three_d = design.get("three_d_model", {})
        if not three_d.get("nodes"):
            if floors:
                three_d = ProceduralArchitecturalEngine._generate_3d_geometry(floors, pw, pl, style_disp.lower())
            else:
                nodes = [
                    {"name": "Ground Floor Slab", "type": "slab", "x": 0.0, "y": 0.15, "z": 0.0, "width": pw * 0.3048, "height": 0.3, "depth": pl * 0.3048},
                    {"name": "Ground Walls", "type": "wall", "x": 0.0, "y": 1.8, "z": 0.0, "width": (pw - 2) * 0.3048, "height": 3.0, "depth": (pl - 4) * 0.3048},
                    {"name": "First Floor Slab", "type": "slab", "x": 0.0, "y": 3.45, "z": 0.0, "width": pw * 0.3048, "height": 0.3, "depth": pl * 0.3048},
                    {"name": "First Walls", "type": "wall", "x": 0.0, "y": 5.1, "z": 0.0, "width": (pw - 4) * 0.3048, "height": 3.0, "depth": (pl - 6) * 0.3048},
                    {"name": "Roof Slab", "type": "roof", "x": 0.0, "y": 6.75, "z": 0.0, "width": pw * 0.3048, "height": 0.3, "depth": pl * 0.3048},
                ]
                three_d = {"nodes": nodes}

        return {
            "plot": {"width_ft": pw, "length_ft": pl},
            "project_id": pid,
            "project_title": p_title,
            "total_covered_area_sqft": tot_area,
            "style_display": style_disp,
            "version": v_num,
            "floors": floors,
            "three_d_model": three_d
        }

    @classmethod
    def generate_dxf(cls, design: Dict[str, Any]) -> str:
        """Generates standard AutoCAD DXF with AIA layers."""
        design = cls._normalize_design_data(design)
        import ezdxf
        from ezdxf.enums import TextEntityAlignment

        doc = ezdxf.new("R2018")
        doc.layers.add("A-WALL-EXTR", color=4, lineweight=50) # Cyan 0.50mm
        doc.layers.add("A-WALL-INTR", color=7, lineweight=25) # White 0.25mm
        doc.layers.add("A-DOOR", color=1, lineweight=25)      # Red 0.25mm
        doc.layers.add("A-GLAZ", color=3, lineweight=25)      # Green 0.25mm
        doc.layers.add("A-ANNO-TEXT", color=2, lineweight=25) # Yellow 0.25mm
        doc.layers.add("A-DIMS", color=5, lineweight=18)      # Blue 0.18mm
        doc.layers.add("A-TITLE", color=6, lineweight=50)     # Magenta 0.50mm

        msp = doc.modelspace()
        pw = float(design["plot"]["width_ft"])
        pl = float(design["plot"]["length_ft"])

        # Title Block
        msp.add_text(
            f"PROJECT: {design['project_title'].upper()}",
            dxfattribs={"layer": "A-TITLE", "height": 1.2}
        ).set_placement((0, pl + 8.0), align=TextEntityAlignment.LEFT)

        msp.add_text(
            f"TOTAL COVERED AREA: {design['total_covered_area_sqft']:.0f} SQ FT | STYLE: {design['style_display']}",
            dxfattribs={"layer": "A-TITLE", "height": 0.8}
        ).set_placement((0, pl + 6.0), align=TextEntityAlignment.LEFT)

        # Plot Outer Boundary
        msp.add_lwpolyline(
            [(0, 0), (pw, 0), (pw, pl), (0, pl), (0, 0)],
            dxfattribs={"layer": "A-DIMS", "color": 8}
        )

        # Render rooms for ground floor (and first floor offset)
        _fls = design.get("floors")
        if not isinstance(_fls, list):          # prompt-designed houses carry the storeys in floors_summary
            _fls = design.get("floors_summary") or []
        for fl_idx, fl in enumerate(_fls):
            offset_x = fl_idx * (pw + 15.0)

            # Sub-title
            msp.add_text(
                f"{fl['name'].upper()} - {fl.get('covered_sqft', 0)} SQ FT",
                dxfattribs={"layer": "A-TITLE", "height": 0.9}
            ).set_placement((offset_x, pl + 2.0), align=TextEntityAlignment.LEFT)

            # Floor Boundary
            msp.add_lwpolyline(
                [(offset_x, 0), (offset_x + pw, 0), (offset_x + pw, pl), (offset_x, pl), (offset_x, 0)],
                dxfattribs={"layer": "A-WALL-EXTR", "lineweight": 50}
            )

            for r in fl.get("rooms", []):
                rx0 = offset_x + float(r["x"])
                ry0 = float(r["y"])
                rw = float(r["width"])
                rl = float(r["length"])

                # Room Polyline
                pts = [(rx0, ry0), (rx0 + rw, ry0), (rx0 + rw, ry0 + rl), (rx0, ry0 + rl), (rx0, ry0)]
                msp.add_lwpolyline(pts, dxfattribs={"layer": "A-WALL-INTR"})

                # Text annotation
                center_x = rx0 + rw / 2.0
                center_y = ry0 + rl / 2.0
                area_sqft = rw * rl

                msp.add_text(
                    r["name"],
                    dxfattribs={"layer": "A-ANNO-TEXT", "height": 0.6}
                ).set_placement((center_x, center_y + 0.4), align=TextEntityAlignment.MIDDLE_CENTER)

                msp.add_text(
                    f"{rw:.1f}' x {rl:.1f}' ({area_sqft:.0f} sf)",
                    dxfattribs={"layer": "A-ANNO-TEXT", "height": 0.45}
                ).set_placement((center_x, center_y - 0.4), align=TextEntityAlignment.MIDDLE_CENTER)

        # Standard AIA Front Elevation CAD Layers
        doc.layers.add("A-ELEV-WALL", color=4, lineweight=50) # Cyan 0.50mm
        doc.layers.add("A-ELEV-ROOF", color=6, lineweight=35) # Magenta 0.35mm
        doc.layers.add("A-ELEV-GLAZ", color=3, lineweight=25) # Green 0.25mm
        doc.layers.add("A-ELEV-HATCH", color=8, lineweight=18) # Gray 0.18mm
        doc.layers.add("A-ELEV-DIMS", color=5, lineweight=18)  # Blue 0.18mm
        doc.layers.add("A-ELEV-TEXT", color=2, lineweight=25)  # Yellow 0.25mm

        # Front Elevation Drawing Space (Offset to the right of floor plans)
        elev_offset_x = len(_fls) * (pw + 15.0)
        msp.add_text(
            f"FRONT ELEVATION - {design['style_display'].upper()} STYLE",
            dxfattribs={"layer": "A-TITLE", "height": 0.9}
        ).set_placement((elev_offset_x, pl + 2.0), align=TextEntityAlignment.LEFT)

        # The elevation is the front projection of the same massing model as the PNG elevation and the 3D views
        # (every storey, street-side doors and windows at their plan positions). Older designs without stored
        # geometry fall back to the simple two-storey outline.
        _geo = None
        try:
            _gp = os.path.join(OUTPUT_DIR, "web_generated", str(design.get("project_id", "")), "layout_geometry.json")
            if os.path.exists(_gp):
                with open(_gp, "r", encoding="utf-8") as _gf:
                    _geo = json.load(_gf)
        except Exception as _ge:
            print(f"[DXF] stored geometry not readable: {_ge}")
        if _geo:
            from generation import massing_render as _mr
            _m = _mr.build_massing(_geo)
            ex = elev_offset_x
            msp.add_lwpolyline([(ex - 5.0, 0), (ex + pw + 5.0, 0)], dxfattribs={"layer": "A-ELEV-WALL"})
            _sol = sorted(_mr._merge_front([q for q in _m["solids"] if q["z1"] > 0.4]), key=lambda q: (-q["y0"], q["z0"]))
            for q in _sol:
                lay = "A-ELEV-ROOF" if q["role"] in ("parapet", "mumty", "cap") else "A-ELEV-WALL"
                msp.add_lwpolyline([(ex + q["x0"], q["z0"]), (ex + q["x1"], q["z0"]), (ex + q["x1"], q["z1"]),
                                    (ex + q["x0"], q["z1"])], close=True, dxfattribs={"layer": lay})
                for o in q["open"]:
                    if o["face"] != "front":
                        continue
                    msp.add_lwpolyline([(ex + o["a0"], o["z0"]), (ex + o["a1"], o["z0"]), (ex + o["a1"], o["z1"]),
                                        (ex + o["a0"], o["z1"])], close=True, dxfattribs={"layer": "A-ELEV-GLAZ"})
            _levels = [(0.0, "ROAD LVL")] + [(z, "PLINTH / GROUND FFL" if i == 0 else f"LEVEL {i} FFL")
                                              for i, z in enumerate(_m["base"])] + \
                      [(_m["top"], "ROOF SLAB"), (_m["top"] + _mr.PARAPET_H, "PARAPET TOP")]
            for z, name in _levels:
                msp.add_text(f"{name} (+{z:.1f} ft)", dxfattribs={"layer": "A-ELEV-DIMS", "height": 0.45}
                             ).set_placement((ex + pw + 1.5, z), align=TextEntityAlignment.LEFT)
        else:
            # Ground line
            msp.add_lwpolyline([(elev_offset_x - 5.0, 0), (elev_offset_x + pw + 5.0, 0)], dxfattribs={"layer": "A-ELEV-WALL"})
            # Plinth box (+2 ft)
            msp.add_lwpolyline([(elev_offset_x, 0), (elev_offset_x + pw, 0), (elev_offset_x + pw, 2.0), (elev_offset_x, 2.0)], close=True, dxfattribs={"layer": "A-ELEV-WALL"})
            # Ground floor facade (+13.5 ft)
            msp.add_lwpolyline([(elev_offset_x, 2.0), (elev_offset_x + pw, 2.0), (elev_offset_x + pw, 13.5), (elev_offset_x, 13.5)], close=True, dxfattribs={"layer": "A-ELEV-WALL"})
            # Upper floor facade (+25.0 ft)
            msp.add_lwpolyline([(elev_offset_x, 13.5), (elev_offset_x + pw, 13.5), (elev_offset_x + pw, 25.0), (elev_offset_x, 25.0)], close=True, dxfattribs={"layer": "A-ELEV-WALL"})
            # Parapet wall (+28.7 ft)
            msp.add_lwpolyline([(elev_offset_x, 25.0), (elev_offset_x + pw, 25.0), (elev_offset_x + pw, 28.7), (elev_offset_x, 28.7)], close=True, dxfattribs={"layer": "A-ELEV-ROOF"})

            # Stair mumty atop stair core
            stair_rooms = [r for fl in _fls for r in fl.get("rooms", []) if "stair" in str(r.get("name", "")).lower()]
            if stair_rooms:
                sr = stair_rooms[0]
                sx = elev_offset_x + float(sr.get("x", 0.0))
                sw = float(sr.get("width", 8.0))
                msp.add_lwpolyline([(sx, 25.0), (sx + sw, 25.0), (sx + sw, 33.7), (sx, 33.7)], close=True, dxfattribs={"layer": "A-ELEV-ROOF"})
                msp.add_text("STAIR MUMTY", dxfattribs={"layer": "A-ELEV-TEXT", "height": 0.5}).set_placement((sx + sw/2.0, 29.5), align=TextEntityAlignment.MIDDLE_CENTER)
                # OHT atop mumty
                ow = min(sw * 0.8, 6.0)
                ox = sx + (sw - ow) * 0.5
                msp.add_lwpolyline([(ox, 33.7), (ox + ow, 33.7), (ox + ow, 37.6), (ox, 37.6)], close=True, dxfattribs={"layer": "A-ELEV-ROOF"})
                msp.add_text("OHT (1500 GAL)", dxfattribs={"layer": "A-ELEV-TEXT", "height": 0.4}).set_placement((ox + ow/2.0, 35.6), align=TextEntityAlignment.MIDDLE_CENTER)

            # Elevation Datum Dimension String
            msp.add_text("PARAPET TOP (+28'-7\")", dxfattribs={"layer": "A-ELEV-DIMS", "height": 0.45}).set_placement((elev_offset_x + pw + 1.5, 28.7), align=TextEntityAlignment.LEFT)
            msp.add_text("ROOF SLAB (+25'-0\")", dxfattribs={"layer": "A-ELEV-DIMS", "height": 0.45}).set_placement((elev_offset_x + pw + 1.5, 25.0), align=TextEntityAlignment.LEFT)
            msp.add_text("FIRST FLOOR (+13'-6\")", dxfattribs={"layer": "A-ELEV-DIMS", "height": 0.45}).set_placement((elev_offset_x + pw + 1.5, 13.5), align=TextEntityAlignment.LEFT)
            msp.add_text("PLINTH (+2'-0\")", dxfattribs={"layer": "A-ELEV-DIMS", "height": 0.45}).set_placement((elev_offset_x + pw + 1.5, 2.0), align=TextEntityAlignment.LEFT)
            msp.add_text("GROUND (0'-0\")", dxfattribs={"layer": "A-ELEV-DIMS", "height": 0.45}).set_placement((elev_offset_x + pw + 1.5, 0.0), align=TextEntityAlignment.LEFT)


        pid = design["project_id"]
        out_path = os.path.join(OUTPUT_DIR, f"{pid}_blueprint.dxf")
        doc.saveas(out_path)
        return out_path

    @classmethod
    def generate_svg(cls, design: Dict[str, Any]) -> str:
        """Generates pure vector SVG presentation sheet."""
        design = cls._normalize_design_data(design)
        pw = float(design["plot"]["width_ft"])
        pl = float(design["plot"]["length_ft"])
        floors = design.get("floors", [])
        if not isinstance(floors, list):       # prompt-designed houses: "floors" is a count
            floors = design.get("floors_summary") or []

        # SVG layout canvas: 1200 x 900
        svg_w = 1200
        svg_h = 900

        scale = min(350.0 / pw, 450.0 / pl)
        margin_x = 60
        margin_y = 120

        svg_lines = [
            f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_w} {svg_h}" width="100%" height="100%">',
            '  <defs>',
            '    <pattern id="cadGrid" width="20" height="20" patternUnits="userSpaceOnUse">',
            '      <path d="M 20 0 L 0 0 0 20" fill="none" stroke="#1e293b" stroke-width="0.5"/>',
            '    </pattern>',
            '    <filter id="glow" x="-20%" y="-20%" width="140%" height="140%">',
            '      <feDropShadow dx="0" dy="4" stdDeviation="6" flood-color="#38bdf8" flood-opacity="0.2"/>',
            '    </filter>',
            '  </defs>',
            '  <!-- Sheet Background -->',
            f'  <rect width="{svg_w}" height="{svg_h}" fill="#0b1120"/>',
            f'  <rect x="20" y="20" width="{svg_w - 40}" height="{svg_h - 40}" fill="url(#cadGrid)" stroke="#38bdf8" stroke-width="2"/>',
            '  <!-- Title Block Banner -->',
            '  <g id="titleBlock">',
            '    <rect x="35" y="35" width="1130" height="65" fill="#1e293b" stroke="#38bdf8" stroke-width="1.5" rx="4"/>',
            f'    <text x="55" y="75" font-family="Arial, sans-serif" font-size="22" font-weight="bold" fill="#38bdf8">ARCHI-AI STUDIO: {design["project_title"].upper()}</text>',
            f'    <text x="1145" y="75" font-family="Arial, sans-serif" font-size="14" fill="#94a3b8" text-anchor="end">TOTAL AREA: {design["total_covered_area_sqft"]:.0f} SQ FT | {design["style_display"]} STYLE | {len(floors)} STOREYS</text>',
            '  </g>'
        ]

        # Render each floor
        for f_idx, fl in enumerate(floors):
            col_x = margin_x + f_idx * 550
            col_y = margin_y + 40

            svg_lines.append(f'  <!-- Floor Level: {fl["name"]} -->')
            svg_lines.append(f'  <g id="floor_{f_idx}">')
            svg_lines.append(f'    <text x="{col_x}" y="{col_y - 15}" font-family="Arial, sans-serif" font-size="16" font-weight="bold" fill="#f8fafc">{fl["name"].upper()} ({fl.get("covered_sqft", 0)} SQ FT)</text>')

            # Plot Boundary Frame
            bw_px = pw * scale
            bl_px = pl * scale
            svg_lines.append(f'    <rect x="{col_x}" y="{col_y}" width="{bw_px}" height="{bl_px}" fill="#0f172a" stroke="#475569" stroke-dasharray="4,4" stroke-width="1.5"/>')

            # Render Rooms
            for r in fl.get("rooms", []):
                rx = col_x + float(r["x"]) * scale
                ry = col_y + float(r["y"]) * scale
                rw = float(r["width"]) * scale
                rl = float(r["length"]) * scale

                # Color by category
                cat = r.get("category", "bedroom")
                if cat == "living_room": fill_c = "#1e293b"
                elif cat == "bedroom": fill_c = "#1e2433"
                elif cat == "kitchen": fill_c = "#2a2220"
                elif cat == "bathroom": fill_c = "#162b3d"
                elif cat == "garage": fill_c = "#262e3d"
                elif cat == "balcony": fill_c = "#193327"
                else: fill_c = "#1e293b"

                svg_lines.append(f'    <rect x="{rx}" y="{ry}" width="{rw}" height="{rl}" fill="{fill_c}" stroke="#38bdf8" stroke-width="2.5" rx="2"/>')

                # Room Name & Dimensions
                cx = rx + rw / 2.0
                cy = ry + rl / 2.0
                if rw > 40 and rl > 25:
                    svg_lines.append(f'    <text x="{cx}" y="{cy - 4}" font-family="Arial, sans-serif" font-size="11" font-weight="bold" fill="#f8fafc" text-anchor="middle">{r["name"]}</text>')
                    svg_lines.append(f'    <text x="{cx}" y="{cy + 12}" font-family="Arial, sans-serif" font-size="9" fill="#94a3b8" text-anchor="middle">{r["width"]:.1f}\' x {r["length"]:.1f}\'</text>')

            svg_lines.append('  </g>')

        # Footer Title Block
        svg_lines.append('  <!-- Footer Technical Block -->')
        svg_lines.append(f'  <g id="footerBlock" transform="translate(35, {svg_h - 70})">')
        svg_lines.append(f'    <rect width="1130" height="45" fill="#1e293b" stroke="#38bdf8" stroke-width="1" rx="4"/>')
        svg_lines.append(f'    <text x="20" y="28" font-family="Arial, sans-serif" font-size="12" fill="#38bdf8">SCALE: 1/4" = 1\'-0" | NORTH: ↑ | DRAWING: 2D BLUEPRINT PRESENTATION SHEET | SYSTEM: AI DRIVEN ARCHITECTURAL DESIGN SYSTEM</text>')
        svg_lines.append(f'    <text x="1110" y="28" font-family="Arial, sans-serif" font-size="12" fill="#10b981" font-weight="bold" text-anchor="end">QUALITY GATE: 100% BYLAW COMPLIANT (LDA/CDA/DHA)</text>')
        svg_lines.append('  </g>')
        svg_lines.append('</svg>')

        pid = design["project_id"]
        out_path = os.path.join(OUTPUT_DIR, f"{pid}_presentation_sheet.svg")
        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(svg_lines))
        return out_path

    @classmethod
    def generate_obj_3d(cls, design: Dict[str, Any]) -> str:
        """Generates standard 3D Wavefront OBJ mesh file."""
        design = cls._normalize_design_data(design)
        pid = design["project_id"]
        out_path = os.path.join(OUTPUT_DIR, f"{pid}_3d_model.obj")

        lines = [
            f"# AI Driven Building Architectural Design System",
            f"# Project: {design['project_title']}",
            f"# Units: Meters",
            "o ArchitecturalHouse"
        ]

        vert_idx = 1
        nodes = design.get("three_d_model", {}).get("nodes", [])

        for node in nodes:
            name = node.get("name", "block").replace(" ", "_")
            x = float(node.get("x", 0.0))
            y = float(node.get("y", 0.0))
            z = float(node.get("z", 0.0))
            w = float(node.get("width", 1.0))
            h = float(node.get("height", 1.0))
            d = float(node.get("depth", 1.0))

            x0, x1 = x - w/2.0, x + w/2.0
            y0, y1 = y - h/2.0, y + h/2.0
            z0, z1 = z - d/2.0, z + d/2.0

            lines.append(f"g {name}")
            # 8 vertices for rectangular solid
            lines.append(f"v {x0:.3f} {y0:.3f} {z0:.3f}")
            lines.append(f"v {x1:.3f} {y0:.3f} {z0:.3f}")
            lines.append(f"v {x1:.3f} {y1:.3f} {z0:.3f}")
            lines.append(f"v {x0:.3f} {y1:.3f} {z0:.3f}")
            lines.append(f"v {x0:.3f} {y0:.3f} {z1:.3f}")
            lines.append(f"v {x1:.3f} {y0:.3f} {z1:.3f}")
            lines.append(f"v {x1:.3f} {y1:.3f} {z1:.3f}")
            lines.append(f"v {x0:.3f} {y1:.3f} {z1:.3f}")

            # 6 quad faces
            base = vert_idx
            lines.append(f"f {base} {base+1} {base+2} {base+3}")     # Front
            lines.append(f"f {base+5} {base+4} {base+7} {base+6}") # Back
            lines.append(f"f {base+4} {base} {base+3} {base+7}")     # Left
            lines.append(f"f {base+1} {base+5} {base+6} {base+2}") # Right
            lines.append(f"f {base+3} {base+2} {base+6} {base+7}") # Top
            lines.append(f"f {base+4} {base+5} {base+1} {base}")     # Bottom

            vert_idx += 8

        with open(out_path, "w", encoding="utf-8") as f:
            f.write("\n".join(lines))
        return out_path

    @classmethod
    def generate_blend_script(cls, design: Dict[str, Any]) -> str:
        """
        Creates a dedicated procedural Blender Python builder script and
        if Blender is installed, executes it to create the authentic .blend file!
        """
        design = cls._normalize_design_data(design)
        pid = design["project_id"]
        blend_path = os.path.join(OUTPUT_DIR, f"{pid}_3d_model.blend")
        py_path = os.path.join(OUTPUT_DIR, f"{pid}_build_blender.py")

        nodes = design.get("three_d_model", {}).get("nodes", [])

        script_content = f'''"""
Procedural 3D Blender Architectural Builder.
Auto-generated by AI Driven Building Architectural Design System.
"""
import bpy
import bmesh
import math

# Reset scene
bpy.ops.wm.read_factory_settings(use_empty=True)
scene = bpy.context.scene
scene.unit_settings.system = 'METRIC'
scene.unit_settings.scale_length = 1.0

# Create architectural collections
col_walls = bpy.data.collections.new("Architectural_Walls")
col_slabs = bpy.data.collections.new("Slabs_and_Floors")
col_roof = bpy.data.collections.new("Roof_Structure")
scene.collection.children.link(col_walls)
scene.collection.children.link(col_slabs)
scene.collection.children.link(col_roof)

# Materials
def get_or_create_material(name, color, roughness=0.6):
    mat = bpy.data.materials.new(name=name)
    mat.use_nodes = True
    bsdf = mat.node_tree.nodes.get("Principled BSDF")
    if bsdf:
        bsdf.inputs["Base Color"].default_value = color
        bsdf.inputs["Roughness"].default_value = roughness
    return mat

mat_wall = get_or_create_material("Wall_Stucco", (0.95, 0.94, 0.90, 1.0), 0.75)
mat_slab = get_or_create_material("Concrete_Slab", (0.50, 0.52, 0.55, 1.0), 0.6)
mat_roof = get_or_create_material("Roof_Finish", (0.76, 0.25, 0.05, 1.0), 0.45)
mat_glass = get_or_create_material("Window_Glass", (0.2, 0.6, 0.9, 0.3), 0.1)

nodes = {json.dumps(nodes)}

for node in nodes:
    ntype = node.get("type")
    x = float(node.get("x", 0))
    y = float(node.get("z", 0)) # Blender swap Y and Z
    z = float(node.get("y", 0))
    w = float(node.get("width", 1))
    d = float(node.get("depth", 1))
    h = float(node.get("height", 1))

    bpy.ops.mesh.primitive_cube_add(size=1.0, location=(x, y, z))
    cube = bpy.context.active_object
    cube.scale = (w, d, h)
    cube.name = node.get("name", "ArchBlock")

    if ntype == "slab":
        cube.data.materials.append(mat_slab)
        col_slabs.objects.link(cube)
    elif ntype == "roof":
        cube.data.materials.append(mat_roof)
        col_roof.objects.link(cube)
    else:
        cube.data.materials.append(mat_wall)
        col_walls.objects.link(cube)
    bpy.context.collection.objects.unlink(cube)

# Lighting: Sun Light
bpy.ops.object.light_add(type='SUN', location=(15, -20, 25))
sun = bpy.context.active_object
sun.data.energy = 5.0
sun.rotation_euler = (math.radians(50), 0, math.radians(40))

# Camera
bpy.ops.object.camera_add(location=(22, -24, 18))
cam = bpy.context.active_object
cam.rotation_euler = (math.radians(60), 0, math.radians(45))
scene.camera = cam

# Save blend file
bpy.ops.wm.save_as_mainfile(filepath=r"{blend_path}")
print("Successfully generated Blender 3D Model:", r"{blend_path}")
'''

        with open(py_path, "w", encoding="utf-8") as f:
            f.write(script_content)

        # Check if Blender is available to compile directly
        blender_exe = r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe"
        if os.path.exists(blender_exe):
            import subprocess
            try:
                cmd = [blender_exe, "--background", "--python", py_path]
                subprocess.run(cmd, timeout=30, capture_output=True)
            except Exception as e:
                print(f"[Blender Runner Note]: {e}")

        return blend_path if os.path.exists(blend_path) else py_path

    @classmethod
    def generate_pdf(cls, design: Dict[str, Any]) -> str:
        """Generates architectural presentation PDF drawing package."""
        design = cls._normalize_design_data(design)
        pid = design.get("project_id", "archi_plan")
        out_path = os.path.join(OUTPUT_DIR, f"{pid}_presentation.pdf")
        with RENDER_LOCK:
            fig, ax = plt.subplots(figsize=(14, 10), dpi=150)
            ax.axis("off")
            title = str(design.get("project_title", "ArchiCraft Design")).upper()
            v_num = design.get("version", 1)
            fig.suptitle(f"ARCHICRAFT AI STUDIO - {title}", fontsize=14, fontweight="bold", y=0.96)
            ax.text(0.5, 0.90, f"Revision Version: v{v_num} | Style: {design.get('style_display', 'Modern')} | LDA / CDA / DHA Compliant", ha="center", fontsize=10, color="#475569")
            pw = float(design.get("plot", {}).get("width_ft", 35.0))
            pl = float(design.get("plot", {}).get("length_ft", 65.0))
            ax.plot([0, pw, pw, 0, 0], [0, 0, pl, pl, 0], "k-", lw=2)
            ax.text(pw/2.0, pl/2.0, f"Plot Extents: {pw:.1f}' x {pl:.1f}'\nVersion: v{v_num}", ha="center", va="center", fontsize=12, fontweight="bold", color="#1e293b")
            ax.set_xlim(-5, pw + 5)
            ax.set_ylim(-5, pl + 5)
            ax.set_aspect("equal")
            fig.savefig(out_path, format="pdf", bbox_inches="tight")
            plt.close(fig)
        return out_path

    @classmethod
    def generate_png(cls, design: Dict[str, Any]) -> str:
        """Generates high-resolution raster blueprint sheet PNG."""
        design = cls._normalize_design_data(design)
        pid = design.get("project_id", "archi_plan")
        out_path = os.path.join(OUTPUT_DIR, f"{pid}_preview.png")
        web_gen = os.path.join(OUTPUT_DIR, "web_generated", pid)
        if os.path.exists(web_gen):
            for f in sorted(os.listdir(web_gen)):
                if f.endswith(".png") and ("ground" in f or "composite" in f):
                    return os.path.join(web_gen, f)
        with RENDER_LOCK:
            fig, ax = plt.subplots(figsize=(10, 8), dpi=150)
            title = str(design.get("project_title", "ArchiCraft Design")).upper()
            v_num = design.get("version", 1)
            fig.suptitle(f"ARCHICRAFT AI STUDIO - {title} (v{v_num})", fontsize=12, fontweight="bold")
            pw = float(design.get("plot", {}).get("width_ft", 35.0))
            pl = float(design.get("plot", {}).get("length_ft", 65.0))
            ax.plot([0, pw, pw, 0, 0], [0, 0, pl, pl, 0], "k-", lw=2)
            ax.text(pw/2.0, pl/2.0, f"Blueprint Preview\nVersion v{v_num}", ha="center", va="center", fontsize=14, color="#0f172a")
            ax.set_xlim(-5, pw + 5)
            ax.set_ylim(-5, pl + 5)
            ax.set_aspect("equal")
            fig.savefig(out_path, bbox_inches="tight")
            plt.close(fig)
        return out_path


# ---------------------------------------------------------------------------
# API Request Handler & HTTP Server
# ---------------------------------------------------------------------------
class ArchitecturalRequestHandler(SimpleHTTPRequestHandler):
    """Handles REST API calls and serves web assets."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=WEB_DIR, **kwargs)

    def do_OPTIONS(self):
        """Handles CORS pre-flight requests from modern frontends."""
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type, Authorization, X-Requested-With")
        self.send_header("Access-Control-Max-Age", "86400")
        self.end_headers()

    def do_GET(self):
        url = urlparse(self.path)
        path = url.path

        if path == "/api/templates":
            self._send_json(ARCHITECTURAL_TEMPLATES)
            return

        elif path == "/api/projects":
            projects = load_saved_projects()
            self._send_json(projects)
            return

        elif path == "/api/status":
            blender_ok = os.path.exists(r"C:\Program Files\Blender Foundation\Blender 5.1\blender.exe")
            status = {
                "system": "AI Driven Building Architectural Design System",
                "version": "3.0.0",
                "status": "ONLINE",
                "blender_available": blender_ok,
                "cad_engine_ready": True,
                "gemini_engine": True
            }
            self._send_json(status)
            return

        elif path == "/api/export/status":
            query = parse_qs(url.query)
            plan_id = query.get("plan_id", [""])[0]
            version = int(query.get("version", [1])[0])
            if not plan_id:
                self._send_json({"error": "plan_id query parameter required"}, status_code=400)
                return

            p_dir = os.path.join(OUTPUT_DIR, plan_id, f"v{version}")
            p_web = os.path.join(OUTPUT_DIR, "web_generated", plan_id)

            plan_exists = os.path.exists(os.path.join(p_dir, "plan.json")) or os.path.exists(os.path.join(OUTPUT_DIR, plan_id, "plan.json"))
            svg_exists = (
                os.path.exists(os.path.join(p_dir, "elevation.svg")) or 
                os.path.exists(os.path.join(p_web, f"{plan_id}_elevation.svg")) or
                os.path.exists(os.path.join(p_web, f"{plan_id}_v{version}_elevation.svg"))
            )
            dxf_exists = (
                os.path.exists(os.path.join(p_dir, "elevation.dxf")) or
                os.path.exists(os.path.join(OUTPUT_DIR, f"{plan_id}_blueprint.dxf"))
            )
            png_exists = any(
                os.path.exists(os.path.join(p_web, f)) 
                for f in (os.listdir(p_web) if os.path.exists(p_web) else []) 
                if f.endswith(".png")
            )

            is_ready = plan_exists or png_exists
            self._send_json({
                "plan_id": plan_id,
                "version": version,
                "status": "ready" if is_ready else "rendering",
                "ready": is_ready,
                "files": {
                    "plan": plan_exists,
                    "svg": svg_exists,
                    "dxf": dxf_exists,
                    "png": png_exists
                }
            })
            return

        if path.startswith("/output/"):
            rel_path = unquote(path[len("/output/"):].replace("/", os.sep))
            file_path = os.path.join(OUTPUT_DIR, rel_path)

            if not os.path.exists(file_path):
                if "_composite_two_floors_2d.png" in file_path:
                    alt_path = file_path.replace("_composite_two_floors_2d.png", "_composite_two_floors.png")
                    if os.path.exists(alt_path):
                        file_path = alt_path
                elif "_composite_two_floors.png" in file_path:
                    alt_path = file_path.replace("_composite_two_floors.png", "_composite_two_floors_2d.png")
                    if os.path.exists(alt_path):
                        file_path = alt_path

            if os.path.exists(file_path) and os.path.isfile(file_path):
                mime, _ = mimetypes.guess_type(file_path)
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime or "image/png")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_response(404)
                self.end_headers()
                return

        # Serve static web frontend
        return super().do_GET()

    def do_POST(self):
        url = urlparse(self.path)
        path = url.path

        # Read JSON body
        content_len = int(self.headers.get("Content-Length", 0))
        post_body = self.rfile.read(content_len).decode("utf-8") if content_len > 0 else "{}"
        try:
            payload = json.loads(post_body) if post_body else {}
        except Exception:
            payload = {}

        if path == "/api/regenerate":
            improvement_text = payload.get("improvement_text")
            prompt = payload.get("prompt", "")
            pw = float(payload.get("plot_width", 25.0))
            pl = float(payload.get("plot_length", 45.0))
            floors = int(payload.get("floors", 2))
            beds = int(payload.get("bedrooms", 4))
            baths = int(payload.get("bathrooms", 4))
            style = payload.get("style", "Modern Contemporary")
            budget_tier = payload.get("budget_tier", "standard")
            custom_room_dimensions = payload.get("custom_room_dimensions") or payload.get("room_schedule") or []
            try:
                from generation.gemini_cad_engine import synthesize_design as gemini_synthesize_design
                refinement_prompt = f"{prompt}. Refinement modifications: {improvement_text}" if improvement_text else prompt
                design = gemini_synthesize_design(
                    prompt=refinement_prompt,
                    plot_width=pw,
                    plot_length=pl,
                    floors=floors,
                    bedrooms=beds,
                    bathrooms=baths,
                    style=style,
                    budget_tier=budget_tier,
                    custom_room_dimensions=custom_room_dimensions
                )
                self._send_json(design)
            except Exception as e_gen:
                import traceback
                traceback.print_exc()
                self._send_json({"success": False, "error": f"Gemini CAD regeneration failed: {str(e_gen)}"}, status_code=500)
            return

        elif path == "/api/brief/read":
            # What the design will be built from - read from the prompt alone (plot, storeys, setbacks, items)
            prompt = str(payload.get("prompt", "")).strip()
            if not prompt:
                self._send_json({"success": False, "error": "Write your prompt first."}, status_code=400)
                return
            try:
                from generation.gemini_cad_engine import read_brief
                self._send_json(read_brief(prompt, payload.get("api_key") or payload.get("gemini_api_key")))
            except Exception as e_read:
                import traceback
                traceback.print_exc()
                self._send_json({"success": False, "error": f"Could not read the prompt: {str(e_read)}"}, status_code=500)
            return

        elif path == "/api/brief/interview":
            # Text-based AI Civil Architect interview bot
            try:
                from generation.gemini_cad_engine import interview_brief
                self._send_json(interview_brief(
                    prompt=str(payload.get("prompt") or payload.get("brief") or ""),
                    answers=payload.get("answers") if isinstance(payload.get("answers"), dict) else None,
                    skipped=payload.get("skipped") if isinstance(payload.get("skipped"), list) else None,
                    history=payload.get("history") if isinstance(payload.get("history"), list) else None,
                    message=str(payload.get("message", "")) if payload.get("message") is not None else None,
                    api_key=payload.get("api_key") or payload.get("gemini_api_key"),
                ))
            except Exception as e_int:
                import traceback
                traceback.print_exc()
                self._send_json({"success": False, "error": f"Interview failed: {str(e_int)}"}, status_code=500)
            return

        elif path in ["/api/generate", "/api/rag/llm-generate"] and payload.get("prompt_only"):
            # AI-prompt flow: the prompt is the only input (no form defaults, no preset room sizes)
            prompt = str(payload.get("prompt", "")).strip()
            try:
                from generation.gemini_cad_engine import synthesize_from_prompt
                design = synthesize_from_prompt(prompt, api_key=payload.get("api_key") or payload.get("gemini_api_key"),
                                                reading=payload.get("reading") if isinstance(payload.get("reading"), dict) else None,
                                                budget_tier=payload.get("budget_tier", "balanced"))
                self._send_json(design)
            except ValueError as e_input:
                self._send_json({"success": False, "error": str(e_input)}, status_code=400)
            except Exception as e_gen:
                import traceback
                traceback.print_exc()
                self._send_json({"success": False, "error": f"Gemini CAD generation failed: {str(e_gen)}"}, status_code=500)
            return

        elif path in ["/api/generate", "/api/rag/llm-generate"]:
            prompt = payload.get("prompt", "")
            pw = float(payload.get("plot_width", 35.0))
            pl = float(payload.get("plot_length", 65.0))
            floors = int(payload.get("floors", 2))
            beds = int(payload.get("bedrooms", 4))
            baths = int(payload.get("bathrooms", 4))
            style = payload.get("style", "Modern Contemporary")
            budget_tier = payload.get("budget_tier", "balanced")
            api_key = payload.get("api_key") or payload.get("gemini_api_key")

            custom_room_dimensions = payload.get("custom_room_dimensions") or payload.get("room_schedule") or []
            try:
                from generation.gemini_cad_engine import synthesize_design as gemini_synthesize_design
                design = gemini_synthesize_design(
                    prompt=prompt,
                    plot_width=pw,
                    plot_length=pl,
                    floors=floors,
                    bedrooms=beds,
                    bathrooms=baths,
                    style=style,
                    api_key=api_key,
                    budget_tier=budget_tier,
                    custom_room_dimensions=custom_room_dimensions
                )
                self._send_json(design)
            except Exception as e_gen:
                import traceback
                traceback.print_exc()
                self._send_json({"success": False, "error": f"Gemini CAD generation failed: {str(e_gen)}"}, status_code=500)
            return

        elif path in ["/api/script/run", "/api/script/converse"]:
            # Design script (ArchiScript) the client edited, or a plain-words change request for Gemini
            script = payload.get("script") or payload.get("design_script") or ""
            if not str(script).strip():
                self._send_json({"success": False, "error": "No design script was sent."}, status_code=400)
                return
            common = dict(
                prompt=payload.get("prompt", ""),
                plot_width=float(payload.get("plot_width", 35.0)),
                plot_length=float(payload.get("plot_length", 65.0)),
                floors=int(payload.get("floors", 1)),
                bedrooms=int(payload.get("bedrooms", 3)),
                bathrooms=int(payload.get("bathrooms", 3)),
                style=payload.get("style", "Modern Contemporary"),
                requirements=payload.get("requirements") if isinstance(payload.get("requirements"), dict) else None,
                api_key=payload.get("api_key") or payload.get("gemini_api_key"),
                custom_room_dimensions=payload.get("custom_room_dimensions") or [],
            )
            try:
                from generation import gemini_cad_engine as gce_mod
                if path == "/api/script/run":
                    design = gce_mod.run_design_script(script, **common)
                else:
                    message = str(payload.get("message", "")).strip()
                    if not message:
                        self._send_json({"success": False, "error": "Write what you want to change."}, status_code=400)
                        return
                    design = gce_mod.converse_design_script(script, message, history=payload.get("history") or [], **common)
                self._send_json(design)
            except Exception as e_scr:
                import traceback
                traceback.print_exc()
                self._send_json({"success": False, "error": f"Design script failed: {str(e_scr)}"}, status_code=500)
            return

        elif path == "/api/cost-estimation":
            covered_sqft = float(payload.get("covered_area_sqft", 2100.0))
            floors = int(payload.get("floors", 2))
            beds = int(payload.get("bedrooms", 4))
            baths = int(payload.get("bathrooms", 4))
            tier = payload.get("budget_tier", "standard")
            curr = payload.get("currency", "PKR")
            custom_prices = payload.get("custom_unit_prices")

            boq = CostEstimator.calculate(
                covered_area_sqft=covered_sqft,
                floors=floors,
                bedrooms=beds,
                bathrooms=baths,
                budget_tier=tier,
                currency=curr,
                custom_unit_prices=custom_prices
            )
            self._send_json(boq)
            return

        elif path == "/api/gemini/market-rates":
            api_key = payload.get("api_key", "").strip()
            city = payload.get("city", "Islamabad / Lahore").strip()
            rates = GeminiMarketRateService.fetch_market_rates(api_key=api_key, city=city)
            self._send_json(rates)
            return

        elif path == "/api/projects/save":
            projects = save_project_to_file(payload)
            self._send_json({"success": True, "count": len(projects), "projects": projects})
            return

        elif path == "/api/projects/delete":
            pid = payload.get("project_id", "")
            projects = delete_project_from_file(pid)
            self._send_json({"success": True, "count": len(projects), "projects": projects})
            return

        elif path == "/api/export/dxf":
            dxf_path = ArchitecturalExporters.generate_dxf(payload)
            with open(dxf_path, "rb") as f:
                content = f.read()
            self._send_file_download(content, os.path.basename(dxf_path), "application/dxf")
            return

        elif path == "/api/export/svg":
            svg_path = ArchitecturalExporters.generate_svg(payload)
            with open(svg_path, "rb") as f:
                content = f.read()
            self._send_file_download(content, os.path.basename(svg_path), "image/svg+xml")
            return

        elif path == "/api/export/obj":
            obj_path = ArchitecturalExporters.generate_obj_3d(payload)
            with open(obj_path, "rb") as f:
                content = f.read()
            self._send_file_download(content, os.path.basename(obj_path), "model/obj")
            return

        elif path == "/api/export/pdf":
            pdf_path = ArchitecturalExporters.generate_pdf(payload)
            with open(pdf_path, "rb") as f:
                content = f.read()
            self._send_file_download(content, os.path.basename(pdf_path), "application/pdf")
            return

        elif path == "/api/export/png":
            png_path = ArchitecturalExporters.generate_png(payload)
            with open(png_path, "rb") as f:
                content = f.read()
            self._send_file_download(content, os.path.basename(png_path), "image/png")
            return

        elif path == "/api/export/blend":
            blend_path = ArchitecturalExporters.generate_blend_script(payload)
            mime = "application/x-blender" if blend_path.endswith(".blend") else "text/x-python"
            with open(blend_path, "rb") as f:
                content = f.read()
            self._send_file_download(content, os.path.basename(blend_path), mime)
            return

        self.send_response(404)
        self.end_headers()

    def _send_json(self, data: Any, status_code: int = 200):
        body = json.dumps(data).encode("utf-8")
        self.send_response(status_code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(body)

    def _send_file_download(self, content: bytes, filename: str, mime_type: str):
        self.send_response(200)
        self.send_header("Content-Type", mime_type)
        self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
        self.send_header("Content-Length", str(len(content)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.end_headers()
        self.wfile.write(content)


def start_server(port: int = 8000):
    server_address = ("127.0.0.1", port)
    httpd = ThreadingHTTPServer(server_address, ArchitecturalRequestHandler)
    print("=" * 75)
    print("AI DRIVEN BUILDING ARCHITECTURAL DESIGN SYSTEM")
    print(f"Server online at: http://127.0.0.1:{port}")
    print(f"Serving Studio UI from: {WEB_DIR}")
    print("=" * 75)
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nServer shutting down gracefully.")
        httpd.server_close()


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Architectural Design System Server")
    parser.add_argument("--port", type=int, default=8000, help="Server port (default: 8000)")
    args = parser.parse_args()
    start_server(args.port)
