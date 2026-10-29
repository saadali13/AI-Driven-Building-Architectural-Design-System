"""
Post-generation Architectural Constraint Fidelity Guard.
Audits the synthesized CanonicalFloorPlan against the parsed ArchitecturalProgram
and user prompt to strictly verify that hard constraints, room counts, and specialized
functional spaces are preserved.
"""

from typing import Dict, Any, List, Optional
import re
from dataset.schema.canonical import CanonicalFloorPlan
from requirements.parser import ArchitecturalProgram


class ArchitecturalFidelityError(Exception):
    """Raised when a generated floor plan fails hard constraint fidelity checks."""
    pass


class FidelityGuard:
    """
    Audits the synthesized plan against the explicit brief:
    1. Requested bedroom counts (exact count determinism).
    2. Requested auxiliary spaces: Dirty Kitchen / Scullery, Executive Study / Home Office,
       Servant Quarter, Guest Suite, Car Porch Capacity.
    3. Mandatory CDA/LDA/DHA building bylaw statutory warnings.
    """

    @classmethod
    def audit(
        cls,
        plan: CanonicalFloorPlan,
        program: Optional[ArchitecturalProgram] = None,
        prompt: str = "",
        raise_on_failure: bool = False
    ) -> Dict[str, Any]:
        p_text = prompt or (program.raw_prompt if program else "")
        p_lower = p_text.lower()
        scale = plan.metadata.provenance.get("scale", "10_marla")

        violations: List[str] = []
        warnings: List[str] = []
        satisfied: List[str] = []

        # 1. Bedroom Count Verification
        num_map = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}
        bed_match = re.search(r'(\d+)\s*[-]?\s*(?:luxury\s+|master\s+|executive\s+)*(?:bhk|bed|bedroom|suite|br)s?', p_lower)
        req_beds = int(bed_match.group(1)) if bed_match else None
        if req_beds is None:
            m_w = re.search(r'\b(one|two|three|four|five|six|seven|eight)\s*[-]?\s*(?:luxury\s+|master\s+|executive\s+)*(?:bhk|bed|bedroom|suite|br)s?\b', p_lower)
            if m_w:
                req_beds = num_map.get(m_w.group(1))

        actual_beds = [r for r in plan.rooms if r.room_type == "bedroom"]
        actual_bed_count = len(actual_beds)

        if req_beds is not None:
            # Check for legally capped adaptations (e.g. 7 Marla 2-storey max 5 beds)
            if scale == "7_marla" and plan.metadata.floor_count <= 2 and req_beds > 5:
                if actual_bed_count == 5:
                    satisfied.append(f"Bedrooms: 5 suites (legally adapted from requested {req_beds} under CDA/DHA setback bylaws)")
                else:
                    violations.append(f"Expected 5 adapted bedrooms for 7 Marla 2-storey, found {actual_bed_count}")
            elif scale == "3_marla" and req_beds > 4:
                warnings.append(f"Statutory Warning: 3 Marla footprint exceeds normal physical density with {req_beds} bedrooms")
            elif actual_bed_count != req_beds:
                violations.append(f"Bedroom count mismatch: requested {req_beds}, generated {actual_bed_count}")
            else:
                satisfied.append(f"Bedrooms: exactly {actual_bed_count} bedrooms matching brief")

        # 2. Dirty Kitchen / Scullery Verification
        req_dirty = any(k in p_lower for k in ["dirty kitchen", "service kitchen", "scullery", "wet kitchen", "bawarchi khana"])
        if req_dirty:
            has_dirty = any("dirty" in r.room_name.lower() or "scullery" in r.room_name.lower() or r.metadata.get("is_dirty_kitchen") for r in plan.rooms)
            if has_dirty:
                satisfied.append("Dirty Kitchen / Scullery successfully incorporated")
            else:
                violations.append("Requested Dirty Kitchen / Scullery was omitted from synthesized plan")

        # 3. Study / Home Office Verification
        req_study = any(k in p_lower for k in ["study", "home office", "office", "workstation", "library"])
        if req_study:
            has_study = any(r.room_type in ("office", "study") or "study" in r.room_name.lower() or "office" in r.room_name.lower() for r in plan.rooms)
            if has_study:
                satisfied.append("Executive Study / Home Office successfully incorporated")
            else:
                violations.append("Requested Study / Home Office was omitted from synthesized plan")

        # 4. Servant Quarter Verification
        req_servant = any(k in p_lower for k in ["servant quarter", "servant", "maid's room", "maid room", "maid", "servant room"])
        if req_servant:
            if scale in ("10_marla", "1_kanal"):
                has_servant = any("servant" in r.room_name.lower() or "maid" in r.room_name.lower() or r.metadata.get("is_servant_quarter") for r in plan.rooms)
                if has_servant:
                    satisfied.append("Dedicated Servant Quarter & En-suite successfully incorporated")
                else:
                    violations.append("Requested Servant Quarter omitted on large-format plot (>=10 Marla)")
            else:
                warnings.append(f"Statutory Restriction: {scale.replace('_', ' ').title()} plot envelope cannot legally fit a separate servant quarter; notified user.")

        # 5. Parking Capacity Verification
        req_2car = any(k in p_lower for k in ["2-car", "two-car", "2 car", "two car", "double car", "double-car"])
        if req_2car:
            garage = next((r for r in plan.rooms if r.room_type == "garage"), None)
            if garage and (garage.metadata.get("parking_capacity") == "double_car" or "2" in garage.room_name or "double" in garage.room_name.lower()):
                satisfied.append("Two-car parking porch verified")
            else:
                violations.append("Requested Double-Car Porch was not configured with two-car capacity")

        is_valid = len(violations) == 0
        fidelity_report = {
            "fidelity_passed": is_valid,
            "violations": violations,
            "warnings": warnings,
            "satisfied_constraints": satisfied,
            "actual_bedroom_count": actual_bed_count,
            "requested_bedroom_count": req_beds,
            "scale": scale
        }

        # Embed into plan provenance
        plan.metadata.provenance["fidelity_guard"] = fidelity_report

        if not is_valid and raise_on_failure:
            raise ArchitecturalFidelityError(f"Plan failed constraint fidelity guard: {'; '.join(violations)}")

        return fidelity_report
