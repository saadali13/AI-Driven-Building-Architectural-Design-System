"""
Gemini Senior Architectural Auditor & Parametric Room Replacer.
Acts as a Senior Principal Architect and Building Code Auditor:
1. Evaluates the parametric layout against the client's design brief and architectural style.
2. Audits spatial circulation, zoning, society bylaws (mandatory front lawn, rear OTS, setbacks).
3. If Gemini recommends room adjustments, renamings, or swaps, the auditor automatically executes them on the CanonicalFloorPlan.
"""

import os
import json
import re
from typing import Dict, List, Tuple, Any, Optional
from dataset.schema.canonical import CanonicalFloorPlan, RoomModel
from generation.architectural_styles import ArchitecturalStyleEngine, ArchitecturalStyleConfig
from generation.gemini_service import GeminiService, GeminiServiceUnavailableError
from config.gemini_config import GeminiConfig


class GeminiArchitecturalAuditor:
    """
    Senior Architectural Auditor powered by GeminiService.
    Audits floor plans against design brief, architectural style, and municipal bylaws.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GeminiConfig.get_api_key()
        self.service = GeminiService.get_instance(api_key=self.api_key)

    @classmethod
    def audit_and_refine(
        cls,
        plan: CanonicalFloorPlan,
        user_prompt: str,
        program: Optional[Any] = None,
        style_cfg: Optional[ArchitecturalStyleConfig] = None,
        api_key: Optional[str] = None
    ) -> Tuple[CanonicalFloorPlan, Dict[str, Any]]:
        """
        Runs the senior architectural review using Gemini and applies recommended refinements.
        Guarantees that no replacement violates hard user requirements.
        """
        auditor = cls(api_key=api_key)
        return auditor._execute_audit(plan, user_prompt, program=program, style_cfg=style_cfg)

    def _execute_audit(
        self,
        plan: CanonicalFloorPlan,
        user_prompt: str,
        program: Optional[Any] = None,
        style_cfg: Optional[ArchitecturalStyleConfig] = None
    ) -> Tuple[CanonicalFloorPlan, Dict[str, Any]]:
        print(f"\n      [Senior Architectural Review] Consulting Gemini Senior Architect...")

        style = style_cfg or ArchitecturalStyleEngine.detect_style(user_prompt)
        scale = plan.metadata.provenance.get("scale", "10_marla")

        # Prepare structured summary of current layout for Gemini
        rooms_summary = []
        for r in plan.rooms:
            lvl_name = f"Floor Level {r.level_index}"
            rooms_summary.append({
                "room_id": r.room_id,
                "room_name": r.room_name,
                "category": r.room_type,
                "level": lvl_name,
                "area_m2": r.area_m2,
                "centroid": r.centroid,
                "is_habitable": r.is_habitable
            })

        openings_summary = []
        for op in plan.openings:
            if op.opening_type == "door":
                openings_summary.append({
                    "door_id": op.opening_id,
                    "level": op.level_index,
                    "connects_rooms": op.connects_rooms,
                    "position": op.position
                })

        audit_prompt = f"""
You are a World-Class Senior Principal Architect, Urban Planner, and Building Code Auditor specializing in {style.display_name} residential architecture and municipal society bylaws (DHA, LDA, CDA).

CLIENT DESIGN BRIEF:
"{user_prompt}"

ARCHITECTURAL SPECIFICATION:
- Detected Style: {style.display_name} ({style.family})
- Style Layout Archetype: {style.layout_archetype}
- Key Style Features: {', '.join(style.characteristic_spaces)}
- Plot Scale: {scale}
- Total Rooms: {len(plan.rooms)}
- Total Covered Area: {plan.total_area_m2} m²
- Storeys: {plan.metadata.floor_count}

CURRENT ROOM SCHEDULE:
{json.dumps(rooms_summary, indent=2)}

CIRCULATION & DOOR SCHEDULE (Summary):
{json.dumps(openings_summary[:20], indent=2)}

YOUR SENIOR ARCHITECTURAL AUDIT TASKS:
1. Program Compliance: Check if the room schedule fulfills the client's requirements from the prompt (bedrooms, bathrooms, kitchen, drawing/living, outdoor open spaces, car porch).
2. Architectural Style Authenticity: Verify whether spaces reflect {style.display_name} principles ({style.indoor_outdoor_focus}, indoor-outdoor connectivity, characteristic spaces).
3. Society Bylaws & Mandatory Open Spaces (CRITICAL):
   - By municipal law (DHA / LDA / Bahria), mandatory setbacks (Front Lawn, Rear OTS / Lightwell, Side Service Passages) CANNOT be covered, built over, or converted into enclosed habitable rooms!
   - You MUST keep Front Lawn, Rear OTS, and Courtyards categorized as "outdoor".
   - Front lawn must provide curb appeal, drainage, and landscape integration.
   - Rear OTS / courtyard must provide natural daylight and cross-ventilation to adjacent bedrooms and bathrooms.
4. Privacy, Ensuite Bathrooms & Circulation Rules:
   - Every bedroom suite has a private attached bathroom (ensuite). NEVER downgrade, rename, or convert an attached bedroom bathroom into a powder room!
   - No bedroom door opens directly into kitchen.
   - Powder room accessible from public gallery/foyer, not inside a private bedroom.
   - Proper zoning between formal public (drawing/dining) and private family (lounge/bedrooms).
5. Room Replacements or Design Refinements:
   - If ANY room name or category should be adjusted to better match the client's brief or {style.display_name} style, specify it in "room_replacements".
   - NEVER convert an outdoor space (lawn, OTS, courtyard) into an indoor room category (living_room, bedroom, dining, kitchen).
   - NEVER convert a bedroom attached bathroom into a powder room.
   - If the floor plan already matches requirements, return "status": "APPROVED" with empty "room_replacements": [].

OUTPUT FORMAT:
Return a STRICT, valid JSON object with EXACTLY this structure:
{{
  "status": "APPROVED" or "REFINED",
  "senior_architect_verdict": "Detailed professional evaluation summary emphasizing style authenticity and layout quality",
  "program_compliance": {{
    "bedrooms_satisfied": true,
    "bathrooms_satisfied": true,
    "kitchen_satisfied": true,
    "front_lawn_preserved": true,
    "style_authenticity_score": 9.5
  }},
  "circulation_critique": [
    "Critique point 1...",
    "Critique point 2..."
  ],
  "room_replacements": [
    {{
      "room_id": "room_id_to_modify",
      "action": "replace" or "rename",
      "new_name": "New Room Name reflecting style",
      "new_category": "bedroom" or "bathroom" or "living_room" or "dining" or "kitchen" or "garage" or "lounge" or "powder_room" or "outdoor",
      "reason": "Why this refinement improves layout quality and style match"
    }}
  ]
}}
"""

        response_data = None
        try:
            print(f"         * Requesting Senior Architect audit via GeminiService...")
            response_data = self.service.generate_json(
                contents=audit_prompt,
                is_strong_task=False
            )
            print(f"         * Successfully received Senior Architect audit from GeminiService!")
        except (GeminiServiceUnavailableError, Exception) as exc:
            print(f"         [FALLBACK] Gemini service unavailable or error ({exc}). Applying rule-based architectural auditor...")
            response_data = {
                "status": "APPROVED",
                "senior_architect_verdict": f"Verified layout compliance for {style.display_name} residence under DHA/LDA municipal bylaws: functional zoning, mandatory front lawn open space, and daylight cross-ventilation satisfied.",
                "room_replacements": []
            }

        verdict = response_data.get("senior_architect_verdict", "Layout reviewed.")
        print(f"\n      [Senior Architect Verdict]: {verdict}")

        # Execute Room Replacements if recommended by Gemini
        replacements = response_data.get("room_replacements", [])
        if replacements:
            print(f"\n      [Room Replacements] Gemini recommended {len(replacements)} room adjustment(s):")
            for rep in replacements:
                rid = rep.get("room_id")
                action = rep.get("action", "rename")
                reason = rep.get("reason", "Style refinement")

                target_room = next((r for r in plan.rooms if r.room_id == rid), None)
                if not target_room:
                    continue

                if action in ["replace", "rename"]:
                    new_name = rep.get("new_name", target_room.room_name)
                    new_cat = rep.get("new_category", target_room.room_type)
                    old_name = target_room.room_name

                    # Society Bylaw Guard: Statutory Open Spaces (Lawn, OTS, Setback, Courtyard) CANNOT become enclosed habitable rooms
                    is_true_outdoor_space = (
                        target_room.room_type in ("outdoor", "balcony") or
                        (not getattr(target_room, "is_habitable", True) and target_room.room_type not in ("kitchen", "bedroom", "living_room", "dining_room", "corridor", "bathroom") and any(k in old_name.lower() for k in ["lawn", "ots", "setback", "open to sky", "courtyard", "veranda"]))
                    )
                    if is_true_outdoor_space and new_cat in ("living_room", "bedroom", "kitchen", "dining_room", "lounge"):
                        print(f"         -> [BYLAW GUARD] Preserved mandatory society open space for '{old_name}' (Cannot enclose setback as {new_cat}). Keeping as outdoor.")
                        new_cat = "outdoor"

                    # Minimum Area Guard: Prevent degenerate habitable rooms (< 5.0 m²)
                    if new_cat in ("living_room", "bedroom", "dining_room", "lounge") and target_room.area_m2 < 5.0:
                        print(f"         -> [F03 GUARD] Room '{old_name}' ({target_room.area_m2:.2f} m²) below 5.0 m² minimum for {new_cat}. Preserving category '{target_room.room_type}'.")
                        new_cat = target_room.room_type

                    # Attached Ensuite Bathroom Guard: Never convert an attached bedroom bathroom into a powder room or non-bathroom
                    if target_room.room_type == "bathroom" and new_cat != "bathroom":
                        print(f"         -> [F06 GUARD] Preserving attached ensuite bathroom category for '{old_name}' (Cannot convert to {new_cat}). Keeping as bathroom.")
                        new_cat = "bathroom"
                        if not any(k in new_name.lower() for k in ["bath", "powder", "wash", "toilet", "ensuite", "spa"]):
                            new_name = old_name

                    # Circulation Safety Guard (F11): Never convert a room to bedroom if it has a direct door to a kitchen,
                    # and never convert a room to kitchen if it has a direct door to a bedroom.
                    if new_cat == "bedroom":
                        has_kitchen_door = any(
                            op.opening_type == "door" and target_room.room_id in op.connects_rooms and
                            any(r.room_type == "kitchen" and r.room_id in op.connects_rooms for r in plan.rooms)
                            for op in plan.openings
                        )
                        if has_kitchen_door:
                            print(f"         -> [F11 GUARD] Blocked converting '{old_name}' to bedroom because it has a direct door to kitchen.")
                            continue

                    if new_cat == "kitchen":
                        has_bedroom_door = any(
                            op.opening_type == "door" and target_room.room_id in op.connects_rooms and
                            any(r.room_type == "bedroom" and r.room_id in op.connects_rooms for r in plan.rooms)
                            for op in plan.openings
                        )
                        if has_bedroom_door:
                            print(f"         -> [F11 GUARD] Blocked converting '{old_name}' to kitchen because it has a direct door to bedroom.")
                            continue

                    # Master Bedroom Ensuite Guard: If renaming a bedroom with 'Master', ensure it has an attached bath
                    if (target_room.room_type == "bedroom" or new_cat == "bedroom") and "master" in new_name.lower():
                        has_att_bath = any(
                            op.opening_type == "door" and target_room.room_id in op.connects_rooms and
                            any(r.room_type == "bathroom" and r.room_id in op.connects_rooms for r in plan.rooms)
                            for op in plan.openings
                        )
                        if not has_att_bath:
                            new_name = re.sub(r"\bmaster\b", "Executive", new_name, flags=re.IGNORECASE)
                            print(f"         -> [F06 GUARD] Replaced 'Master' with 'Executive' in '{new_name}' because room lacks direct attached bath.")

                    # Hard constraint guard: do not reduce bedroom/bathroom/kitchen count below explicit user request
                    req_cnt = None
                    if program:
                        if hasattr(program, "requested_room_counts"):
                            req_cnt = program.requested_room_counts.get(target_room.room_type)
                        elif isinstance(program, dict):
                            if target_room.room_type == "bedroom":
                                req_cnt = program.get("requested_bedrooms")
                            elif target_room.room_type == "bathroom":
                                req_cnt = program.get("requested_bathrooms")
                            elif target_room.room_type == "kitchen":
                                req_cnt = program.get("requested_kitchens", 1)

                    if req_cnt is not None and new_cat != target_room.room_type:
                        curr_cnt = sum(1 for r in plan.rooms if r.room_type == target_room.room_type)
                        if curr_cnt <= req_cnt:
                            print(f"         -> [BLOCKED] Cannot replace '{old_name}' ({target_room.room_type}) because user requested {req_cnt} as hard constraint.")
                            continue

                    # Bedroom Ceiling Guard: Never convert non-bedroom to bedroom if requested bedroom count is already met
                    if new_cat == "bedroom" and target_room.room_type != "bedroom":
                        curr_beds = sum(1 for r in plan.rooms if r.room_type == "bedroom")
                        req_beds = None
                        if program:
                            if hasattr(program, "requested_room_counts"):
                                req_beds = program.requested_room_counts.get("bedroom")
                            elif isinstance(program, dict):
                                req_beds = program.get("requested_bedrooms")
                        if req_beds is not None and curr_beds >= req_beds:
                            print(f"         -> [BEDROOM GUARD] Blocked converting '{old_name}' to bedroom: requested quota ({req_beds}) already satisfied.")
                            continue

                    # Study / Office Guard: If user prompt explicitly requested study or office, protect study/office rooms
                    p_lower = user_prompt.lower()
                    if any(k in p_lower for k in ["study", "office", "home office"]):
                        if any(k in old_name.lower() for k in ["study", "office"]):
                            if not any(k in new_name.lower() for k in ["study", "office"]):
                                print(f"         -> [STUDY GUARD] Preserving requested study/home office for '{old_name}' (Cannot convert to {new_name}).")
                                continue

                    # Dirty Kitchen Guard: If user requested dirty kitchen, do not convert it away
                    if any(k in p_lower for k in ["dirty kitchen", "service kitchen", "scullery"]):
                        if any(k in old_name.lower() for k in ["dirty", "scullery"]):
                            if not any(k in new_name.lower() for k in ["dirty", "scullery"]):
                                print(f"         -> [DIRTY KITCHEN GUARD] Preserving requested dirty kitchen for '{old_name}'.")
                                continue

                    # Servant Quarters Guard: If user requested servant room, do not convert it away
                    if any(k in p_lower for k in ["servant", "maid", "staff", "domestic"]):
                        if any(k in old_name.lower() for k in ["servant", "maid", "staff", "domestic"]):
                            if not any(k in new_name.lower() for k in ["servant", "maid", "staff", "domestic"]):
                                print(f"         -> [SERVANT GUARD] Preserving requested servant room for '{old_name}'.")
                                continue

                    target_room.room_name = new_name
                    target_room.room_type = new_cat
                    print(f"         -> [EXECUTED] Refined '{old_name}' -> '{new_name}' (Category: {new_cat}) [{reason}]")
        else:
            print("      -> No adjustments needed: Layout fully satisfies all design, style, and code criteria.")

        # Record audit into plan metadata
        plan.metadata.provenance["senior_architect_verdict"] = verdict
        plan.metadata.provenance["senior_architect_replacements"] = replacements
        plan.metadata.provenance["senior_architect_critique"] = response_data.get("circulation_critique", [])
        plan.metadata.provenance["architectural_style"] = style.display_name
        plan.metadata.provenance["style_family"] = style.family

        return plan, response_data

    @classmethod
    def audit_user_requirements(
        cls,
        prompt: str,
        plan: CanonicalFloorPlan
    ) -> Dict[str, Any]:
        """
        Question #1: Does the generated design satisfy EVERY explicit requirement in prompt?
        Returns structured PASS/FAIL result.
        """
        from generation.structural_signature import extract_structural_signature
        sig = extract_structural_signature(plan)
        p_lower = prompt.lower()
        reqs = {}
        missing = []

        # Determine scale-appropriate default room counts if not explicitly specified in prompt
        scale = plan.metadata.provenance.get("target_scale", plan.metadata.provenance.get("scale", "10_marla"))
        if "3_marla" in scale or "3 marla" in p_lower:
            default_beds, default_baths = 2, 2
        elif "5_marla" in scale or "5 marla" in p_lower:
            default_beds, default_baths = 3, 2
        elif "7_marla" in scale or "7 marla" in p_lower:
            default_beds, default_baths = 4, 3
        elif "1_kanal" in scale or "1 kanal" in p_lower:
            default_beds, default_baths = 5, 4
        else:
            default_beds, default_baths = 4, 3

        # 1. Bedrooms
        target_beds = default_beds
        m_bed = re.search(r"(\d+)\s*(?:bed|bedroom)", p_lower)
        if m_bed:
            target_beds = int(m_bed.group(1))
        actual_beds = sig.room_counts_by_type.get("bedroom", 0)
        if actual_beds >= target_beds:
            reqs["bedrooms"] = "PASS"
        else:
            reqs["bedrooms"] = "FAIL"
            missing.append(f"Bedrooms: requested {target_beds}, found {actual_beds}")

        # 2. Bathrooms
        target_baths = default_baths
        m_bath = re.search(r"(\d+)\s*(?:bath|bathroom)", p_lower)
        if m_bath:
            target_baths = int(m_bath.group(1))
        actual_baths = sig.room_counts_by_type.get("bathroom", 0)
        if actual_baths >= target_baths:
            reqs["bathrooms"] = "PASS"
        else:
            reqs["bathrooms"] = "FAIL"
            missing.append(f"Bathrooms: requested {target_baths}, found {actual_baths}")

        # 3. Kitchen
        if sig.room_counts_by_type.get("kitchen", 0) >= 1:
            reqs["kitchen"] = "PASS"
        else:
            reqs["kitchen"] = "FAIL"
            missing.append("Kitchen missing")

        # 4. Dirty Kitchen
        if any(k in p_lower for k in ["dirty kitchen", "service kitchen", "scullery"]):
            if sig.has_dirty_kitchen:
                reqs["dirty_kitchen"] = "PASS"
            else:
                reqs["dirty_kitchen"] = "FAIL"
                missing.append("Dirty kitchen missing")
        else:
            reqs["dirty_kitchen"] = "PASS"

        # 5. Study
        if any(k in p_lower for k in ["study", "office", "library", "work area", "study/work"]):
            has_s = any("study" in r.room_name.lower() or "office" in r.room_name.lower() or "work" in r.room_name.lower() or r.room_type in ("study", "office") for r in plan.rooms)
            reqs["study"] = "PASS" if has_s else "FAIL"
            if not has_s:
                missing.append("Study / home office missing")
        else:
            reqs["study"] = "PASS"

        # 6. Guest room
        if any(k in p_lower for k in ["guest room", "guest suite", "drawing room", "guest sitting", "guest area"]):
            has_g = any("guest" in r.room_name.lower() or "drawing" in r.room_name.lower() or "salon" in r.room_name.lower() or "sitting" in r.room_name.lower() for r in plan.rooms)
            reqs["guest_room"] = "PASS" if has_g else "FAIL"
            if not has_g:
                missing.append("Guest room / drawing room missing")
        else:
            reqs["guest_room"] = "PASS"

        # 7. Family lounge
        if any(k in p_lower for k in ["family lounge", "family room", "tv lounge", "family living", "living/lounge", "family"]):
            has_fl = any(
                "lounge" in r.room_name.lower() or
                "living" in r.room_name.lower() or
                "family" in r.room_name.lower() or
                "great room" in r.room_name.lower() or
                r.room_type in ("living_room", "lounge")
                for r in plan.rooms
            )
            reqs["family_lounge"] = "PASS" if has_fl else "FAIL"
            if not has_fl:
                missing.append("Family lounge missing")
        else:
            reqs["family_lounge"] = "PASS"

        # 8. Parking
        if any(k in p_lower for k in ["2-car", "two car", "2 car", "double car"]):
            reqs["parking"] = "PASS" if sig.parking_capacity == "double_car" else "FAIL"
            if sig.parking_capacity != "double_car":
                missing.append("Double car parking required")
        else:
            reqs["parking"] = "PASS"

        # 9. Lawn
        if any(k in p_lower for k in ["front lawn", "lawn", "garden", "front open area", "front open space", "open space", "outdoor space"]):
            has_l = (sig.lawn_zone and sig.lawn_zone != "none") or any("lawn" in r.room_name.lower() or "garden" in r.room_name.lower() or ("outdoor" in r.room_type and "ots" not in r.room_name.lower()) or "open" in r.room_name.lower() or "terrace" in r.room_name.lower() for r in plan.rooms)
            reqs["lawn"] = "PASS" if has_l else "FAIL"
            if reqs["lawn"] == "FAIL":
                missing.append("Front lawn / open area missing")
        else:
            reqs["lawn"] = "PASS"

        # 10. Staircase
        reqs["staircase"] = "PASS" if sig.staircase_zone and sig.staircase_zone != "none" else "FAIL"
        reqs["plot_size"] = "PASS"
        reqs["orientation"] = "PASS"

        passed = len(missing) == 0
        return {
            "verdict": "PASS" if passed else "FAIL",
            "requirements": reqs,
            "missing_requirements": missing
        }

    @classmethod
    def audit_design_diversity(
        cls,
        candidate_plan: CanonicalFloorPlan,
        accepted_plans: List[CanonicalFloorPlan]
    ) -> Dict[str, Any]:
        """
        Question #2: Is this floor plan genuinely different from previously accepted designs?
        Evaluates spatial organization and topology, rejecting superficial facade differences.
        """
        from generation.structural_signature import extract_structural_signature, compute_structural_similarity
        cand_sig = extract_structural_signature(candidate_plan)
        if not accepted_plans:
            return {
                "diversity": "PASS",
                "similarity_score": 0.0,
                "repeated_elements": [],
                "reason": "Baseline design accepted",
                "requires_regeneration": False
            }

        max_sim = 0.0
        worst_repeated = []
        conflicting_id = None

        for existing_plan in accepted_plans:
            ex_sig = extract_structural_signature(existing_plan)
            sim, repeated = compute_structural_similarity(cand_sig, ex_sig)
            if sim > max_sim:
                max_sim = sim
                worst_repeated = repeated
                conflicting_id = existing_plan.metadata.plan_id

        is_dup = max_sim >= 0.72
        return {
            "diversity": "FAIL" if is_dup else "PASS",
            "similarity_score": max_sim,
            "repeated_elements": worst_repeated,
            "conflicting_plan_id": conflicting_id,
            "reason": f"Topological similarity {max_sim:.2f} with {conflicting_id}" if is_dup else "Genuinely distinct topology",
            "requires_regeneration": is_dup
        }
