"""
Phase 11 / Upgraded: Architectural Layout Validation Engine.
Deep architectural and computational geometry validation:
1. Zero geometric collision between rooms (IoU overlap == 0.0).
2. Code minimum areas and aspect ratios.
3. Daylight access (bedrooms & living room have windows on exterior walls).
4. Full circulation reachability & architectural usability.
5. Strict Master Bedroom + Attached Bathroom boundary & door verification.
6. Integration with FloorPlanQualityGate (F01-F20).
"""

from typing import Dict, List, Tuple, Any, Optional
from shapely.geometry import Polygon, Point
import networkx as nx
from dataset.schema.canonical import CanonicalFloorPlan, RoomModel
from requirements.parser import ArchitecturalProgram
from generation.quality_gate import FloorPlanQualityGate


class LayoutValidator:
    @classmethod
    def validate_plan(
        cls,
        plan: CanonicalFloorPlan,
        program: Optional[ArchitecturalProgram] = None
    ) -> Dict[str, Any]:
        if program is None:
            # Construct a default program matching plan metadata if none provided
            program = ArchitecturalProgram(
                project_title=plan.metadata.provenance.get("project_title", "Residence"),
                requested_room_counts={
                    "bedroom": len([r for r in plan.rooms if r.room_type == "bedroom"]),
                    "bathroom": len([r for r in plan.rooms if r.room_type == "bathroom"])
                }
            )

        # Run comprehensive Quality Gate
        gate_report = FloorPlanQualityGate.evaluate(plan, program)

        return {
            "is_valid": gate_report["final_status"] == "PASS",
            "final_status": gate_report["final_status"],
            "quality_score": gate_report["quality_score"],
            "failure_codes": gate_report["failure_codes"],
            "issues": [f"{f['code']}: {f['description']}" for f in gate_report["failure_details"]],
            "issue_count": len(gate_report["failure_details"]),
            "room_count": len(plan.rooms),
            "total_area_m2": plan.total_area_m2,
            "gate_details": gate_report
        }
