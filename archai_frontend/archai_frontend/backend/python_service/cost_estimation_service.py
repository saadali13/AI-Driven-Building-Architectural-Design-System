import os
import math
import httpx
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

cost_router = APIRouter(prefix="/api/v1/cost", tags=["Location-Aware Cost Estimation"])

# Google Maps API Key configuration
GOOGLE_MAPS_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY", "")

# ---------------------------------------------------------------------------
# Comprehensive Regional Construction Market & Municipal By-Laws Database
# ---------------------------------------------------------------------------
REGIONAL_MARKET_DATABASE: Dict[str, Dict[str, Any]] = {
    "islamabad": {
        "city": "Islamabad",
        "region": "Federal Capital Territory",
        "country": "Pakistan",
        "authority": "Capital Development Authority (CDA)",
        "coordinates": {"lat": 33.6844, "lng": 73.0479},
        "currency": "PKR",
        "currency_symbol": "₨",
        "seismic_zone": "2B (Moderate-High)",
        "bylaws": {
            "max_ground_coverage_pct": 65.0,
            "max_height_ft": 35.0,
            "front_setback_ft": 10.0,
            "rear_setback_ft": 5.0,
            "side_setback_ft": 4.0,
            "floor_area_ratio": "1:1.6",
            "rainwater_harvesting_mandatory": True,
            "solar_provision_mandatory": True
        },
        "materials": {
            "cement_bag_pkr": 1420.0,        # Fauji / Bestway Cement 50kg
            "steel_ton_pkr": 265000.0,       # Mughal / Amreli Grade 60 Rebar per Ton
            "bricks_per_1000_pkr": 14200.0,  # Potohar Red Clay First-Class
            "sand_per_100cft_pkr": 4800.0,   # Margalla Pit Sand
            "crush_per_100cft_pkr": 5200.0,  # Margalla Limestone 1/2" Aggregate
            "labor_sqft_pkr": 480.0,         # Master Mason + Laborer Blend
            "mep_sqft_pkr": 320.0,           # Electrical & Plumbing Conduit Index
            "finishing_sqft_base": 650.0     # Tile, Paint, Joinery
        }
    },
    "rawalpindi": {
        "city": "Rawalpindi",
        "region": "Punjab",
        "country": "Pakistan",
        "authority": "Rawalpindi Development Authority (RDA) / Bahria / DHA",
        "coordinates": {"lat": 33.5651, "lng": 73.0169},
        "currency": "PKR",
        "currency_symbol": "₨",
        "seismic_zone": "2B (Moderate)",
        "bylaws": {
            "max_ground_coverage_pct": 70.0,
            "max_height_ft": 38.0,
            "front_setback_ft": 8.0,
            "rear_setback_ft": 5.0,
            "side_setback_ft": 0.0,
            "floor_area_ratio": "1:1.75",
            "rainwater_harvesting_mandatory": False,
            "solar_provision_mandatory": False
        },
        "materials": {
            "cement_bag_pkr": 1410.0,
            "steel_ton_pkr": 264000.0,
            "bricks_per_1000_pkr": 13900.0,
            "sand_per_100cft_pkr": 4700.0,
            "crush_per_100cft_pkr": 5100.0,
            "labor_sqft_pkr": 460.0,
            "mep_sqft_pkr": 310.0,
            "finishing_sqft_base": 620.0
        }
    },
    "lahore": {
        "city": "Lahore",
        "region": "Punjab",
        "country": "Pakistan",
        "authority": "Lahore Development Authority (LDA) / DHA Lahore",
        "coordinates": {"lat": 31.5204, "lng": 74.3587},
        "currency": "PKR",
        "currency_symbol": "₨",
        "seismic_zone": "2A (Low-Moderate)",
        "bylaws": {
            "max_ground_coverage_pct": 65.0,
            "max_height_ft": 40.0,
            "front_setback_ft": 10.0,
            "rear_setback_ft": 5.0,
            "side_setback_ft": 5.0,
            "floor_area_ratio": "1:1.6",
            "rainwater_harvesting_mandatory": True,
            "solar_provision_mandatory": False
        },
        "materials": {
            "cement_bag_pkr": 1390.0,        # Maple Leaf / DG Cement
            "steel_ton_pkr": 262000.0,       # Ittefaq / Mughal Steel
            "bricks_per_1000_pkr": 13200.0,  # Chenab Kiln First Class
            "sand_per_100cft_pkr": 4200.0,   # Ravi / Chenab Clean Sand
            "crush_per_100cft_pkr": 4900.0,  # Sargodha Black Stone Aggregate
            "labor_sqft_pkr": 450.0,
            "mep_sqft_pkr": 300.0,
            "finishing_sqft_base": 610.0
        }
    },
    "karachi": {
        "city": "Karachi",
        "region": "Sindh",
        "country": "Pakistan",
        "authority": "Sindh Building Control Authority (SBCA) / Clifton Board",
        "coordinates": {"lat": 24.8607, "lng": 67.0011},
        "currency": "PKR",
        "currency_symbol": "₨",
        "seismic_zone": "2B (Moderate) + Coastal Marine Corrosion",
        "bylaws": {
            "max_ground_coverage_pct": 70.0,
            "max_height_ft": 42.0,
            "front_setback_ft": 8.0,
            "rear_setback_ft": 6.0,
            "side_setback_ft": 4.0,
            "floor_area_ratio": "1:1.8",
            "rainwater_harvesting_mandatory": False,
            "marine_anti_corrosive_spec": True
        },
        "materials": {
            "cement_bag_pkr": 1470.0,        # Lucky / Thatta Sulphate Resistant
            "steel_ton_pkr": 272000.0,       # Amreli / Razmak Marine Rebar
            "bricks_per_1000_pkr": 14800.0,  # Concrete Hollow Blocks / Clay Bricks
            "sand_per_100cft_pkr": 5200.0,   # Hub River Washed Sand
            "crush_per_100cft_pkr": 5600.0,  # Nooriabad Hard Rock Aggregate
            "labor_sqft_pkr": 510.0,
            "mep_sqft_pkr": 340.0,
            "finishing_sqft_base": 680.0
        }
    },
    "peshawar": {
        "city": "Peshawar",
        "region": "Khyber Pakhtunkhwa",
        "country": "Pakistan",
        "authority": "Peshawar Development Authority (PDA)",
        "coordinates": {"lat": 34.0151, "lng": 71.5249},
        "currency": "PKR",
        "currency_symbol": "₨",
        "seismic_zone": "3 (High Seismic Demand)",
        "bylaws": {
            "max_ground_coverage_pct": 65.0,
            "max_height_ft": 35.0,
            "front_setback_ft": 10.0,
            "rear_setback_ft": 5.0,
            "side_setback_ft": 5.0,
            "floor_area_ratio": "1:1.5",
            "high_seismic_detailing": True
        },
        "materials": {
            "cement_bag_pkr": 1380.0,        # Cherat Cement
            "steel_ton_pkr": 268000.0,       # Frontier / Mughal Rebar
            "bricks_per_1000_pkr": 13500.0,
            "sand_per_100cft_pkr": 4400.0,
            "crush_per_100cft_pkr": 4800.0,
            "labor_sqft_pkr": 440.0,
            "mep_sqft_pkr": 290.0,
            "finishing_sqft_base": 590.0
        }
    },
    "faisalabad": {
        "city": "Faisalabad",
        "region": "Punjab",
        "country": "Pakistan",
        "authority": "Faisalabad Development Authority (FDA)",
        "coordinates": {"lat": 31.4504, "lng": 73.1350},
        "currency": "PKR",
        "currency_symbol": "₨",
        "seismic_zone": "2A (Low-Moderate)",
        "bylaws": {
            "max_ground_coverage_pct": 68.0,
            "max_height_ft": 38.0,
            "front_setback_ft": 8.0,
            "rear_setback_ft": 5.0,
            "side_setback_ft": 4.0,
            "floor_area_ratio": "1:1.6"
        },
        "materials": {
            "cement_bag_pkr": 1395.0,
            "steel_ton_pkr": 263000.0,
            "bricks_per_1000_pkr": 12900.0,
            "sand_per_100cft_pkr": 4100.0,
            "crush_per_100cft_pkr": 4850.0,
            "labor_sqft_pkr": 435.0,
            "mep_sqft_pkr": 295.0,
            "finishing_sqft_base": 595.0
        }
    },
    "multan": {
        "city": "Multan",
        "region": "Punjab",
        "country": "Pakistan",
        "authority": "Multan Development Authority (MDA)",
        "coordinates": {"lat": 30.1575, "lng": 71.5249},
        "currency": "PKR",
        "currency_symbol": "₨",
        "seismic_zone": "2A (Low)",
        "bylaws": {
            "max_ground_coverage_pct": 68.0,
            "max_height_ft": 36.0,
            "front_setback_ft": 9.0,
            "rear_setback_ft": 5.0,
            "side_setback_ft": 4.0,
            "floor_area_ratio": "1:1.6"
        },
        "materials": {
            "cement_bag_pkr": 1405.0,
            "steel_ton_pkr": 264500.0,
            "bricks_per_1000_pkr": 12800.0,
            "sand_per_100cft_pkr": 4000.0,
            "crush_per_100cft_pkr": 4950.0,
            "labor_sqft_pkr": 430.0,
            "mep_sqft_pkr": 290.0,
            "finishing_sqft_base": 585.0
        }
    },
    "dubai": {
        "city": "Dubai",
        "region": "Dubai Emirate",
        "country": "United Arab Emirates",
        "authority": "Dubai Municipality / Trakhees (Al Sa'fat Green Code)",
        "coordinates": {"lat": 25.2048, "lng": 55.2708},
        "currency": "AED",
        "currency_symbol": "AED ",
        "seismic_zone": "2A (International)",
        "bylaws": {
            "max_ground_coverage_pct": 60.0,
            "max_height_ft": 45.0,
            "front_setback_ft": 12.0,
            "rear_setback_ft": 8.0,
            "side_setback_ft": 6.0,
            "floor_area_ratio": "1:1.4",
            "green_building_rating": "Al Sa'fat Bronze Mandatory"
        },
        "materials": {
            "cement_bag_pkr": 45.0,          # AED per bag
            "steel_ton_pkr": 2950.0,         # AED per ton
            "bricks_per_1000_pkr": 1800.0,   # AED per 1000 blocks
            "sand_per_100cft_pkr": 220.0,
            "crush_per_100cft_pkr": 280.0,
            "labor_sqft_pkr": 45.0,
            "mep_sqft_pkr": 38.0,
            "finishing_sqft_base": 110.0
        }
    }
}

# ---------------------------------------------------------------------------
# Pydantic Request & Response Schemas
# ---------------------------------------------------------------------------
class CoordinatesRequest(BaseModel):
    latitude: float = Field(..., example=33.6844)
    longitude: float = Field(..., example=73.0479)

class LocationInfoResponse(BaseModel):
    location_key: str
    city: str
    region: str
    country: str
    authority: str
    latitude: float
    longitude: float
    currency: str
    currency_symbol: str
    seismic_zone: str
    bylaws: Dict[str, Any]

class FloorPlanMatrixInput(BaseModel):
    plot_size_marla: Optional[float] = Field(default=5.0, example=5.0)
    covered_area_sqft: float = Field(default=2250.0, example=2250.0)
    carpet_area_sqft: Optional[float] = Field(default=1850.0, example=1850.0)
    num_floors: int = Field(default=2, ge=1, le=5, example=2)
    bed_count: int = Field(default=3, example=3)
    bath_count: int = Field(default=3, example=3)
    room_matrix: Optional[Dict[str, Any]] = None

class CostCalculationRequest(BaseModel):
    location_key: str = Field(default="islamabad", example="islamabad")
    tier: str = Field(default="STANDARD", example="STANDARD") # ECONOMY, STANDARD, LUXURY
    floor_plan: FloorPlanMatrixInput
    custom_contingency_pct: Optional[float] = Field(default=5.0, ge=0.0, le=25.0)

class MaterialBOQItem(BaseModel):
    category: str
    item_name: str
    unit: str
    unit_rate: float
    quantity: float
    total_cost: float
    percentage_of_budget: float
    spec_notes: str

class CostCalculationResponse(BaseModel):
    location: LocationInfoResponse
    tier: str
    covered_area_sqft: float
    cost_per_sqft: float
    grey_structure_total: float
    finishing_total: float
    mep_total: float
    labor_total: float
    contingency_total: float
    grand_total: float
    grand_total_million: float
    currency: str
    currency_symbol: str
    boq_breakdown: List[MaterialBOQItem]
    bylaws_compliance: Dict[str, Any]
    calculated_at: str

# ---------------------------------------------------------------------------
# Geolocation Matching Utility (Haversine Distance & Google Geocode Bridge)
# ---------------------------------------------------------------------------
def calculate_haversine_distance(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Calculate distance in kilometers between two GPS coordinates."""
    r = 6371.0  # Earth's radius in km
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    delta_phi = math.radians(lat2 - lat1)
    delta_lambda = math.radians(lon2 - lon1)
    a = math.sin(delta_phi / 2.0)**2 + math.cos(phi1) * math.cos(phi2) * math.sin(delta_lambda / 2.0)**2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c

def find_nearest_regional_market(lat: float, lng: float) -> str:
    """Find the closest construction market hub based on GPS coordinates."""
    closest_key = "islamabad"
    min_dist = float("inf")
    for key, data in REGIONAL_MARKET_DATABASE.items():
        coords = data["coordinates"]
        dist = calculate_haversine_distance(lat, lng, coords["lat"], coords["lng"])
        if dist < min_dist:
            min_dist = dist
            closest_key = key
    return closest_key

# ---------------------------------------------------------------------------
# API Endpoints
# ---------------------------------------------------------------------------
@cost_router.get("/locations", response_model=List[LocationInfoResponse])
async def list_available_locations():
    """Retrieve all supported regional municipal construction markets & by-laws."""
    results = []
    for key, data in REGIONAL_MARKET_DATABASE.items():
        results.append(LocationInfoResponse(
            location_key=key,
            city=data["city"],
            region=data["region"],
            country=data["country"],
            authority=data["authority"],
            latitude=data["coordinates"]["lat"],
            longitude=data["coordinates"]["lng"],
            currency=data["currency"],
            currency_symbol=data["currency_symbol"],
            seismic_zone=data["seismic_zone"],
            bylaws=data["bylaws"]
        ))
    return results

@cost_router.post("/reverse-geocode", response_model=LocationInfoResponse)
async def reverse_geocode_location(req: CoordinatesRequest):
    """
    Reverse geocodes browser GPS coordinates to municipal authority & material index.
    Attempts Google Maps Geocoding API if key configured; falls back seamlessly to
    nearest municipal boundary vector match.
    """
    city_name = None
    if GOOGLE_MAPS_API_KEY:
        try:
            async with httpx.AsyncClient() as client:
                url = f"https://maps.googleapis.com/maps/api/geocode/json?latlng={req.latitude},{req.longitude}&key={GOOGLE_MAPS_API_KEY}"
                resp = await client.get(url, timeout=4.0)
                if resp.status_code == 200:
                    payload = resp.json()
                    if payload.get("status") == "OK" and payload.get("results"):
                        for comp in payload["results"][0].get("address_components", []):
                            if "locality" in comp.get("types", []):
                                city_name = comp.get("long_name", "").lower()
                                break
        except Exception:
            pass  # Fall back to nearest geo-boundary match

    if city_name and city_name in REGIONAL_MARKET_DATABASE:
        matched_key = city_name
    else:
        matched_key = find_nearest_regional_market(req.latitude, req.longitude)

    data = REGIONAL_MARKET_DATABASE[matched_key]
    return LocationInfoResponse(
        location_key=matched_key,
        city=data["city"],
        region=data["region"],
        country=data["country"],
        authority=data["authority"],
        latitude=req.latitude,
        longitude=req.longitude,
        currency=data["currency"],
        currency_symbol=data["currency_symbol"],
        seismic_zone=data["seismic_zone"],
        bylaws=data["bylaws"]
    )

@cost_router.post("/calculate", response_model=CostCalculationResponse)
async def calculate_construction_cost(req: CostCalculationRequest):
    """
    Dynamically computes high-precision Bill of Quantities (BOQ), material weights,
    workforce hours, and municipal compliance based on active 2D floor plan matrix
    and localized construction market rates.
    """
    loc_key = req.location_key.lower().strip()
    if loc_key not in REGIONAL_MARKET_DATABASE:
        loc_key = "islamabad"

    market = REGIONAL_MARKET_DATABASE[loc_key]
    rates = market["materials"]
    bylaws = market["bylaws"]
    area = max(500.0, float(req.floor_plan.covered_area_sqft))
    tier = req.tier.upper()

    # Tier multipliers for structural specifications
    tier_multipliers = {
        "ECONOMY": {
            "cement_factor": 0.38,       # bags per sq ft
            "steel_factor": 3.6,         # kg per sq ft
            "bricks_factor": 15.0,       # bricks per sq ft
            "sand_factor": 0.55,         # cu.ft per sq ft
            "crush_factor": 0.65,        # cu.ft per sq ft
            "labor_multiplier": 0.90,
            "mep_multiplier": 0.85,
            "finishing_multiplier": 0.75
        },
        "STANDARD": {
            "cement_factor": 0.44,
            "steel_factor": 4.2,
            "bricks_factor": 17.5,
            "sand_factor": 0.65,
            "crush_factor": 0.75,
            "labor_multiplier": 1.0,
            "mep_multiplier": 1.0,
            "finishing_multiplier": 1.0
        },
        "LUXURY": {
            "cement_factor": 0.50,
            "steel_factor": 4.8,
            "bricks_factor": 19.0,
            "sand_factor": 0.75,
            "crush_factor": 0.85,
            "labor_multiplier": 1.25,
            "mep_multiplier": 1.45,
            "finishing_multiplier": 1.65
        }
    }

    t_spec = tier_multipliers.get(tier, tier_multipliers["STANDARD"])

    # 1. Material Quantities & Cost Computations
    # Cement
    total_cement_bags = math.ceil(area * t_spec["cement_factor"])
    cement_cost = total_cement_bags * rates["cement_bag_pkr"]

    # Steel Rebar (Convert kg to Metric Tons)
    total_steel_kg = area * t_spec["steel_factor"]
    total_steel_tons = round(total_steel_kg / 1000.0, 3)
    steel_cost = total_steel_tons * rates["steel_ton_pkr"]

    # Clay Bricks (1000-unit batches)
    total_bricks_units = math.ceil(area * t_spec["bricks_factor"])
    bricks_batches = total_bricks_units / 1000.0
    bricks_cost = bricks_batches * rates["bricks_per_1000_pkr"]

    # Sand (100-cft units)
    total_sand_cft = area * t_spec["sand_factor"]
    sand_cost = (total_sand_cft / 100.0) * rates["sand_per_100cft_pkr"]

    # Aggregate Crush (100-cft units)
    total_crush_cft = area * t_spec["crush_factor"]
    crush_cost = (total_crush_cft / 100.0) * rates["crush_per_100cft_pkr"]

    # 2. Labor Overheads & Engineering Services
    labor_cost = area * rates["labor_sqft_pkr"] * t_spec["labor_multiplier"]

    # 3. MEP (Electrical, Sanitary, HVAC Conduit)
    mep_cost = area * rates["mep_sqft_pkr"] * t_spec["mep_multiplier"]

    # 4. Finishing, Joinery & Tiling Fitouts
    finishing_cost = area * rates["finishing_sqft_base"] * t_spec["finishing_multiplier"]

    # Grey Structure Total
    grey_structure_total = cement_cost + steel_cost + bricks_cost + sand_cost + crush_cost + labor_cost

    # Subtotal
    subtotal = grey_structure_total + mep_cost + finishing_cost

    # Contingency buffer
    contingency_pct = float(req.custom_contingency_pct or 5.0)
    contingency_total = subtotal * (contingency_pct / 100.0)

    grand_total = subtotal + contingency_total
    cost_per_sqft = round(grand_total / area, 2)
    grand_total_million = round(grand_total / 1000000.0, 2) if market["currency"] == "PKR" else round(grand_total / 1000.0, 2)

    # 5. Build Itemized BOQ Structure
    boq_items: List[MaterialBOQItem] = [
        MaterialBOQItem(
            category="Grey Structure",
            item_name="Portland Cement (50kg Bags)",
            unit="Bags",
            unit_rate=rates["cement_bag_pkr"],
            quantity=total_cement_bags,
            total_cost=round(cement_cost, 2),
            percentage_of_budget=round((cement_cost / grand_total) * 100.0, 1),
            spec_notes=f"OPC Grade 53/43 Compliant with {market['authority']} Standards"
        ),
        MaterialBOQItem(
            category="Grey Structure",
            item_name="Deformed Rebar Steel (Grade 60)",
            unit="Metric Tons",
            unit_rate=rates["steel_ton_pkr"],
            quantity=total_steel_tons,
            total_cost=round(steel_cost, 2),
            percentage_of_budget=round((steel_cost / grand_total) * 100.0, 1),
            spec_notes=f"60,000 PSI High-Yield Steel, Seismic Zone {market['seismic_zone']}"
        ),
        MaterialBOQItem(
            category="Grey Structure",
            item_name="First-Class Kiln Clay Bricks",
            unit="Pieces",
            unit_rate=rates["bricks_per_1000_pkr"] / 1000.0,
            quantity=total_bricks_units,
            total_cost=round(bricks_cost, 2),
            percentage_of_budget=round((bricks_cost / grand_total) * 100.0, 1),
            spec_notes="9x4.5x3 in standard kiln burnt red clay bricks"
        ),
        MaterialBOQItem(
            category="Grey Structure",
            item_name="River Pit Sand (Plaster & Masonry)",
            unit="Cubic Feet (CFT)",
            unit_rate=round(rates["sand_per_100cft_pkr"] / 100.0, 2),
            quantity=round(total_sand_cft, 1),
            total_cost=round(sand_cost, 2),
            percentage_of_budget=round((sand_cost / grand_total) * 100.0, 1),
            spec_notes="Washed silt-free graded natural sand"
        ),
        MaterialBOQItem(
            category="Grey Structure",
            item_name="Crushed Coarse Aggregate (1/2\" & 3/4\")",
            unit="Cubic Feet (CFT)",
            unit_rate=round(rates["crush_per_100cft_pkr"] / 100.0, 2),
            quantity=round(total_crush_cft, 1),
            total_cost=round(crush_cost, 2),
            percentage_of_budget=round((crush_cost / grand_total) * 100.0, 1),
            spec_notes="Hard limestone angular crushed gravel for RCC slab casting"
        ),
        MaterialBOQItem(
            category="Civil Workforce",
            item_name="Civil Labor & Formwork Contracts",
            unit="Sq. Ft",
            unit_rate=rates["labor_sqft_pkr"] * t_spec["labor_multiplier"],
            quantity=area,
            total_cost=round(labor_cost, 2),
            percentage_of_budget=round((labor_cost / grand_total) * 100.0, 1),
            spec_notes="Master Masons, Steel fixers, Shuttering carpenters & Excavation"
        ),
        MaterialBOQItem(
            category="Services & Utilities",
            item_name="Electrical, Plumbing & Piping MEP",
            unit="Sq. Ft",
            unit_rate=rates["mep_sqft_pkr"] * t_spec["mep_multiplier"],
            quantity=area,
            total_cost=round(mep_cost, 2),
            percentage_of_budget=round((mep_cost / grand_total) * 100.0, 1),
            spec_notes="PPRC Water pipes, PVC drainage & Class-A copper cabling"
        ),
        MaterialBOQItem(
            category="Architectural Finishing",
            item_name="Flooring, Tiles, Joinery & Paint Fitouts",
            unit="Sq. Ft",
            unit_rate=rates["finishing_sqft_base"] * t_spec["finishing_multiplier"],
            quantity=area,
            total_cost=round(finishing_cost, 2),
            percentage_of_budget=round((finishing_cost / grand_total) * 100.0, 1),
            spec_notes=f"{tier.capitalize()} Grade porcelain tiles, Ash wood doors, Weather-resistant paint"
        ),
        MaterialBOQItem(
            category="Risk & Contingency",
            item_name=f"Price Volatility Reserve ({contingency_pct}%)",
            unit="Fixed Reserve",
            unit_rate=round(contingency_total, 2),
            quantity=1.0,
            total_cost=round(contingency_total, 2),
            percentage_of_budget=round((contingency_total / grand_total) * 100.0, 1),
            spec_notes="Indexed buffer for local steel/fuel inflation"
        )
    ]

    # Municipal By-Laws Verification
    plot_marla = float(req.floor_plan.plot_size_marla or 5.0)
    plot_sqft = plot_marla * 225.0
    ground_floor_sqft = area / float(req.floor_plan.num_floors)
    actual_coverage_pct = round((ground_floor_sqft / plot_sqft) * 100.0, 1) if plot_sqft > 0 else 60.0
    max_allowed_coverage = bylaws.get("max_ground_coverage_pct", 65.0)

    compliance = {
        "authority": market["authority"],
        "plot_marla": plot_marla,
        "plot_sqft": plot_sqft,
        "actual_coverage_pct": actual_coverage_pct,
        "max_allowed_coverage_pct": max_allowed_coverage,
        "is_coverage_compliant": actual_coverage_pct <= max_allowed_coverage,
        "front_setback_required_ft": bylaws.get("front_setback_ft", 10.0),
        "rear_setback_required_ft": bylaws.get("rear_setback_ft", 5.0),
        "seismic_zone": market["seismic_zone"]
    }

    return CostCalculationResponse(
        location=LocationInfoResponse(
            location_key=loc_key,
            city=market["city"],
            region=market["region"],
            country=market["country"],
            authority=market["authority"],
            latitude=market["coordinates"]["lat"],
            longitude=market["coordinates"]["lng"],
            currency=market["currency"],
            currency_symbol=market["currency_symbol"],
            seismic_zone=market["seismic_zone"],
            bylaws=market["bylaws"]
        ),
        tier=tier,
        covered_area_sqft=area,
        cost_per_sqft=cost_per_sqft,
        grey_structure_total=round(grey_structure_total, 2),
        finishing_total=round(finishing_cost, 2),
        mep_total=round(mep_cost, 2),
        labor_total=round(labor_cost, 2),
        contingency_total=round(contingency_total, 2),
        grand_total=round(grand_total, 2),
        grand_total_million=grand_total_million,
        currency=market["currency"],
        currency_symbol=market["currency_symbol"],
        boq_breakdown=boq_items,
        bylaws_compliance=compliance,
        calculated_at=datetime.utcnow().isoformat()
    )
