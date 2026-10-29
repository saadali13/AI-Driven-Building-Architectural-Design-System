"""
Phase 10: Architectural RAG Document and Metadata Generator.
Converts CanonicalFloorPlan instances into high-density architectural summaries
optimized for natural-language retrieval, similarity matching, and design-brief generation.
"""

from typing import Dict, List, Any
from dataset.schema.canonical import CanonicalFloorPlan


class ArchitecturalRAGGenerator:
    @staticmethod
    def generate_document(plan: CanonicalFloorPlan) -> Dict[str, Any]:
        """
        Generates structured metadata and human-readable natural language document
        summarizing room layout, dimensions, zoning, circulation, and openings.
        """
        room_types = [r.room_type for r in plan.rooms]
        bedroom_count = sum(1 for t in room_types if t == "bedroom")
        bathroom_count = sum(1 for t in room_types if t == "bathroom")
        total_habitable_area = sum(r.area_m2 for r in plan.rooms if r.is_habitable)

        # Classification category
        if bedroom_count in (1, 2):
            bhk_tag = f"{bedroom_count}BHK"
        elif bedroom_count >= 3:
            bhk_tag = f"{bedroom_count}BHK"
        else:
            bhk_tag = "Studio/Open"

        # List room summaries
        room_lines = []
        for r in plan.rooms:
            room_lines.append(f"- {r.room_name} ({r.room_type}): {r.area_m2:.1f} m² (centroid: x={r.centroid[0]:.1f}, y={r.centroid[1]:.1f})")

        # Adjacency and door connections
        conn_lines = []
        for edge in plan.graph_edges:
            r1 = plan.get_room_by_id(edge.source_room_id)
            r2 = plan.get_room_by_id(edge.target_room_id)
            r1_name = r1.room_name if r1 else edge.source_room_id
            r2_name = r2.room_name if r2 else edge.target_room_id
            conn_lines.append(f"- {r1_name} connects to {r2_name} via {edge.relationship_type}")

        # Narrative text for dense vector embedding
        text = (
            f"Architectural Floor Plan {plan.metadata.plan_id}.\n"
            f"Category: {bhk_tag} residential layout with {bedroom_count} bedrooms and {bathroom_count} bathrooms.\n"
            f"Total footprint area: {plan.total_area_m2:.1f} m² (Total habitable area: {total_habitable_area:.1f} m²).\n"
            f"Floor count: {plan.metadata.floor_count}.\n"
            f"Rooms ({len(plan.rooms)} total):\n" + "\n".join(room_lines) + "\n"
            f"Spatial Connectivity & Adjacency ({len(plan.graph_edges)} relationships):\n" + "\n".join(conn_lines) + "\n"
            f"Openings: {len([o for o in plan.openings if o.opening_type == 'door'])} doors, "
            f"{len([o for o in plan.openings if o.opening_type == 'window'])} windows."
        )

        metadata = {
            "plan_id": plan.metadata.plan_id,
            "bhk_tag": bhk_tag,
            "bedroom_count": bedroom_count,
            "bathroom_count": bathroom_count,
            "total_area_m2": plan.total_area_m2,
            "habitable_area_m2": total_habitable_area,
            "room_count": len(plan.rooms),
            "floor_count": plan.metadata.floor_count,
            "source_type": plan.metadata.source_type
        }

        return {
            "plan_id": plan.metadata.plan_id,
            "text": text,
            "metadata": metadata
        }
