"""
generation/strategy_selector.py
Plot-Size Suitability Rules & Architectural Strategy Ranking Engine.

Evaluates prompt requirements against the 10 learned architectural strategies
and enforces strict physical and cultural plot suitability rules:
- 3 Marla (<=1000 sq ft): Compact infill plots. Disallows double-height atriums,
  bifurcated formal foyers, and multi-kitchen suites. Prioritizes central lounge
  and perimeter gallery circulation.
- 5 Marla (1001-1600 sq ft): Urban row-housing. Supports split guest-family and
  inward microclimate courtyards. Disallows grand rotundas.
- 7 Marla (1601-2100 sq ft, 30'x55'): Duplex family homes. Supports central atriums,
  split foyers, and dual rear bedroom suites.
- 10 Marla (2101-2800 sq ft, 35'x65'): Executive residences. Supports all 10 archetypes.
- 1 Kanal (>2800 sq ft, 50'x90'): Classical estates. Prioritizes monumental rotundas,
  rear master pavilions, and grand atriums.
"""

from typing import Dict, List, Tuple, Any, Optional

STRATEGY_CATALOG: Dict[str, Dict[str, Any]] = {
    "central_family_lounge": {
        "id": "central_family_lounge",
        "name": "Central Family Lounge & Drawing Front",
        "description": "Segregated family living core with formal front drawing and central living spine.",
        "archetype_version": 1,
        "min_plot_area_sqft": 600,
        "min_plot_width_ft": 18.0,
        "ideal_plot_scales": ["3_marla", "5_marla", "7_marla", "10_marla"],
        "keywords": ["family", "classic", "traditional", "lounge", "standard", "estate"]
    },
    "central_atrium_lightwell": {
        "id": "central_atrium_lightwell",
        "name": "Grand Central Atrium & Lightwell",
        "description": "Double-height central light court delivering natural daylight deep into interior living zones.",
        "archetype_version": 2,
        "min_plot_area_sqft": 1500,     # Disallowed on 3M and tight 5M
        "min_plot_width_ft": 28.0,      # Requires minimum 28' width for double-height void
        "ideal_plot_scales": ["7_marla", "10_marla", "1_kanal"],
        "keywords": ["atrium", "lightwell", "double height", "skylight", "contemporary", "modern", "openness"]
    },
    "side_corridor_gallery": {
        "id": "side_corridor_gallery",
        "name": "Side Circulation Gallery & Linear Spine",
        "description": "Continuous linear circulation gallery along perimeter providing unhindered movement and ventilation.",
        "archetype_version": 3,
        "min_plot_area_sqft": 650,
        "min_plot_width_ft": 18.0,
        "ideal_plot_scales": ["3_marla", "5_marla", "7_marla"],
        "keywords": ["gallery", "linear", "corridor", "spine", "minimalist", "zen", "passage"]
    },
    "rotunda_foyer_formal": {
        "id": "rotunda_foyer_formal",
        "name": "Curved Rotunda Foyer & Salon",
        "description": "Monumental curved entrance staircase and distinct entertaining salon for an executive arrival experience.",
        "archetype_version": 4,
        "min_plot_area_sqft": 2000,     # Disallowed on 3M, 5M, and 7M
        "min_plot_width_ft": 32.0,      # Requires wide entrance bay
        "ideal_plot_scales": ["10_marla", "1_kanal"],
        "keywords": ["rotunda", "curved stair", "curved", "monumental", "salon", "classical", "grand", "mansion"]
    },
    "split_guest_family": {
        "id": "split_guest_family",
        "name": "Split Guest-Family Zoning",
        "description": "Bifurcated foyer strictly separating formal visitor areas from private family quarters and bedrooms.",
        "archetype_version": 5,
        "min_plot_area_sqft": 1100,
        "min_plot_width_ft": 24.0,
        "ideal_plot_scales": ["5_marla", "7_marla", "10_marla"],
        "keywords": ["split", "privacy", "guest privacy", "rental", "independent", "double porch", "separate"]
    },
    "courtyard_patio_centric": {
        "id": "courtyard_patio_centric",
        "name": "Courtyard & Inward Patio-Centric",
        "description": "Central Open-To-Sky courtyard creating a private inward green microclimate with shaded verandas.",
        "archetype_version": 6,
        "min_plot_area_sqft": 1100,
        "min_plot_width_ft": 24.0,
        "ideal_plot_scales": ["5_marla", "7_marla", "10_marla", "1_kanal"],
        "keywords": ["courtyard", "patio", "spanish", "hacienda", "andalusian", "garden", "microclimate", "mediterranean"]
    },
    "multifamily_dual_kitchen": {
        "id": "multifamily_dual_kitchen",
        "name": "Multi-Family Dual Kitchen Suite",
        "description": "Ground floor master kitchen combined with upper-level kitchenette for multi-generational living.",
        "archetype_version": 7,
        "min_plot_area_sqft": 1600,
        "min_plot_width_ft": 30.0,
        "ideal_plot_scales": ["7_marla", "10_marla", "1_kanal"],
        "keywords": ["dual kitchen", "kitchenette", "two family", "multigenerational", "independent unit"]
    },
    "rear_master_pavilion": {
        "id": "rear_master_pavilion",
        "name": "Rear Master Bedroom Pavilion",
        "description": "Master suites secluded across full rear plot width away from street noise, buffered by rear setback.",
        "archetype_version": 8,
        "min_plot_area_sqft": 1600,
        "min_plot_width_ft": 30.0,
        "ideal_plot_scales": ["7_marla", "10_marla", "1_kanal"],
        "keywords": ["rear master", "pavilion", "quiet", "garden view", "secluded", "luxury suite"]
    },
    "corner_splayed_entrance": {
        "id": "corner_splayed_entrance",
        "name": "Corner Splayed Entrance & Dual Frontage",
        "description": "45-degree diagonal entrance with dual-street frontage, optimizing corner plot setbacks.",
        "archetype_version": 9,
        "min_plot_area_sqft": 1100,
        "min_plot_width_ft": 25.0,
        "ideal_plot_scales": ["5_marla", "7_marla", "10_marla", "1_kanal"],
        "keywords": ["corner", "splay", "chamfer", "diagonal", "dual frontage", "corner plot"]
    },
    "open_living_minimalist": {
        "id": "open_living_minimalist",
        "name": "Open-Concept Great Room Minimalist",
        "description": "Continuous flowing pavilion integrating living, dining, and show kitchen with minimal dividing walls.",
        "archetype_version": 10,
        "min_plot_area_sqft": 650,
        "min_plot_width_ft": 18.0,
        "ideal_plot_scales": ["3_marla", "5_marla", "7_marla", "10_marla"],
        "keywords": ["open living", "minimalist", "open concept", "great room", "pavilion", "modernist"]
    }
}


class StrategySelector:
    """
    Ranks and selects architectural planning strategies based on:
    1. Plot physical dimension & area suitability rules.
    2. Prompt intent & keyword affinity.
    3. Cultural zoning feasibility.
    """

    @classmethod
    def rank_strategies(
        cls,
        prompt: str,
        scale: str,
        plot_width: float,
        plot_length: float,
        style: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """
        Returns ranked strategies with numeric suitability score and justification.
        """
        area_sqft = plot_width * plot_length
        p_lower = prompt.lower()
        style_lower = (style or "").lower()

        ranked = []

        for strat_id, info in STRATEGY_CATALOG.items():
            score = 50.0  # Base neutral score
            reasons = []

            # 1. Hard Physical Suitability Gates
            is_disallowed = False
            disallow_reason = ""

            if area_sqft < info["min_plot_area_sqft"]:
                is_disallowed = True
                disallow_reason = f"Plot area ({area_sqft:.0f} sq ft) below minimum {info['min_plot_area_sqft']} sq ft required for {info['name']}."
            elif plot_width < info["min_plot_width_ft"]:
                is_disallowed = True
                disallow_reason = f"Plot width ({plot_width:.1f}') narrower than minimum {info['min_plot_width_ft']}' required for {info['name']}."

            if is_disallowed:
                ranked.append({
                    "strategy_id": strat_id,
                    "name": info["name"],
                    "description": info["description"],
                    "archetype_version": info["archetype_version"],
                    "score": 0.0,
                    "tie_breaker_priority": 0,
                    "is_suitable": False,
                    "justification": disallow_reason
                })
                continue

            # Scale match bonus
            if scale in info["ideal_plot_scales"]:
                score += 25.0
                reasons.append(f"Ideal archetype for {scale.replace('_', ' ').title()}")

            # 2. Prompt Functional Requirement & Keyword Matching
            feature_bonus = 0.0
            
            # TV Lounge / Family living affinity
            if any(k in p_lower for k in ["tv lounge", "family lounge", "lounge", "living room"]):
                if strat_id == "central_family_lounge":
                    feature_bonus += 20.0
                    reasons.append("Directly hosts central family TV lounge")
                elif strat_id == "open_living_minimalist":
                    feature_bonus += 10.0

            # Kitchen type affinity
            if any(k in p_lower for k in ["open kitchen", "american kitchen", "show kitchen"]):
                if strat_id == "open_living_minimalist":
                    feature_bonus += 25.0
                    reasons.append("Integrated open-concept American kitchen pavilion")
            elif any(k in p_lower for k in ["dirty kitchen", "scullery", "two kitchen", "dual kitchen"]):
                if strat_id == "multifamily_dual_kitchen":
                    feature_bonus += 25.0
                    reasons.append("Dedicated master & dirty kitchen layout")

            # Formal drawing / entertaining affinity
            if any(k in p_lower for k in ["drawing", "formal drawing", "guest drawing", "salon"]):
                if strat_id in ("central_family_lounge", "rotunda_foyer_formal"):
                    feature_bonus += 15.0
                    reasons.append("Dedicated front formal drawing / salon room")

            # Privacy / Guest segregation affinity
            if any(k in p_lower for k in ["privacy", "guest privacy", "separate guest", "split"]):
                if strat_id == "split_guest_family":
                    feature_bonus += 25.0
                    reasons.append("Bifurcated foyer strictly segregating guest and family zones")

            # Lightwell / Atrium affinity
            if any(k in p_lower for k in ["atrium", "lightwell", "skylight", "double height", "openness", "daylight"]):
                if strat_id == "central_atrium_lightwell":
                    feature_bonus += 25.0
                    reasons.append("Central double-height atrium core delivering daylight")

            # General catalog keyword hits
            kw_hits = sum(1 for kw in info["keywords"] if kw in p_lower)
            if kw_hits > 0:
                feature_bonus += min(20.0, kw_hits * 10.0)

            score += feature_bonus

            # 3. Architectural Style Compatibility
            if "spanish" in style_lower and strat_id == "courtyard_patio_centric":
                score += 30.0
                reasons.append("Authentic Andalusian Spanish central courtyard archetype")
            elif "classical" in style_lower and strat_id in ("rotunda_foyer_formal", "central_family_lounge"):
                score += 25.0
                reasons.append("Classical monumental entrance and segregated public salon")
            elif "minimalist" in style_lower and strat_id in ("open_living_minimalist", "side_corridor_gallery"):
                score += 25.0
                reasons.append("Clean minimalist circulation and open living pavilion")
            elif "modern" in style_lower:
                if strat_id in ("central_family_lounge", "open_living_minimalist", "side_corridor_gallery"):
                    score += 20.0
                    reasons.append("Modernist functional efficiency and spatial flow")
                elif strat_id == "central_atrium_lightwell" and area_sqft >= 1600:
                    score += 20.0
                    reasons.append("Modernist double-height lightwell court")

            # 4. Infill scale penalty for complex typologies on narrow lots
            if scale == "3_marla" and strat_id in ("central_atrium_lightwell", "split_guest_family"):
                score -= 40.0

            # 5. Deterministic Architectural Tie-Breaker Priority
            # Compact plots favor functional carpet area efficiency; Estate plots favor grand circulation cores
            tb_priority = 0
            if scale in ("3_marla", "5_marla"):
                if strat_id == "central_family_lounge": tb_priority = 30
                elif strat_id == "open_living_minimalist": tb_priority = 20
                elif strat_id == "side_corridor_gallery": tb_priority = 10
            elif scale in ("7_marla", "10_marla"):
                if strat_id == "central_family_lounge": tb_priority = 30
                elif strat_id == "central_atrium_lightwell": tb_priority = 20
                elif strat_id == "open_living_minimalist": tb_priority = 10
            elif scale == "1_kanal":
                if strat_id == "central_atrium_lightwell": tb_priority = 30
                elif strat_id == "rotunda_foyer_formal": tb_priority = 20
                elif strat_id == "central_family_lounge": tb_priority = 10

            ranked.append({
                "strategy_id": strat_id,
                "name": info["name"],
                "description": info["description"],
                "archetype_version": info["archetype_version"],
                "score": round(score, 1),
                "tie_breaker_priority": tb_priority,
                "is_suitable": True,
                "justification": "; ".join(reasons) if reasons else "Standard layout compatibility"
            })

        # Sort descending by suitability, score, then deterministic architectural tie-breaker
        ranked.sort(key=lambda x: (x["is_suitable"], x["score"], x.get("tie_breaker_priority", 0)), reverse=True)
        return ranked

    @classmethod
    def select_top_3_distinct_strategies(
        cls,
        prompt: str,
        scale: str,
        plot_width: float,
        plot_length: float,
        style: Optional[str] = None,
        requested_strategy: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """Selects top 3 distinct, physically suitable strategies."""
        ranked = cls.rank_strategies(prompt, scale, plot_width, plot_length, style)
        suitable = [s for s in ranked if s["is_suitable"]]

        if not suitable:
            suitable = ranked[:3]

        selected = []
        if requested_strategy:
            req_item = next((s for s in suitable if s["strategy_id"] == requested_strategy), None)
            if req_item:
                selected.append(req_item)

        for s in suitable:
            if s["strategy_id"] not in [sel["strategy_id"] for sel in selected]:
                selected.append(s)
            if len(selected) == 3:
                break

        return selected

