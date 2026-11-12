#!/usr/bin/env python3
"""
generation/topological_knowledge_base.py
Phase 3: Topology Graph Library & Knowledge Base.

Constructs scale-independent Planar Adjacency Graphs using networkx from extracted vector knowledge.
Stores room functional archetypes, aspect ratios, proportional footprint ratios, zoning rules,
and floor-specific spatial programs with ground-to-upper vertical dependencies.
Completely replaces the legacy "Upper Study & Workstation" polygon duplication loop.
"""

import os
import glob
import json
from typing import Dict, List, Tuple, Any, Optional
import networkx as nx

KNOWLEDGE_DIR = os.path.join(os.path.dirname(__file__), "..", "dataset", "extracted_vector_knowledge")


class FunctionalRoomArchetype:
    def __init__(
        self,
        room_type: str,
        zoning: str,
        aspect_ratio_range: Tuple[float, float],
        footprint_ratio_range: Tuple[float, float],
        min_dim_ft: Tuple[float, float],
        target_adjacencies: List[str]
    ):
        self.room_type = room_type
        self.zoning = zoning
        self.aspect_ratio_range = aspect_ratio_range
        self.footprint_ratio_range = footprint_ratio_range
        self.min_dim_ft = min_dim_ft
        self.target_adjacencies = target_adjacencies

    def to_dict(self) -> Dict[str, Any]:
        return {
            "room_type": self.room_type,
            "zoning": self.zoning,
            "aspect_ratio": self.aspect_ratio_range,
            "footprint_ratio": self.footprint_ratio_range,
            "min_dimensions_ft": self.min_dim_ft,
            "required_adjacencies": self.target_adjacencies
        }


# Standard Pakistani Architectural Archetypes
ARCHETYPES: Dict[str, FunctionalRoomArchetype] = {
    "garage": FunctionalRoomArchetype(
        room_type="garage",
        zoning="Front-Public",
        aspect_ratio_range=(0.7, 1.3),
        footprint_ratio_range=(0.14, 0.22),
        min_dim_ft=(10.0, 14.0),
        target_adjacencies=["foyer", "drawing_room", "lawn"]
    ),
    "drawing_room": FunctionalRoomArchetype(
        room_type="drawing_room",
        zoning="Front-Public",
        aspect_ratio_range=(0.85, 1.25),
        footprint_ratio_range=(0.12, 0.20),
        min_dim_ft=(11.0, 13.0),
        target_adjacencies=["garage", "foyer", "powder_room", "living_room"]
    ),
    "living_room": FunctionalRoomArchetype(
        room_type="living_room",
        zoning="Mid-Living-Service",
        aspect_ratio_range=(1.0, 1.6),
        footprint_ratio_range=(0.18, 0.28),
        min_dim_ft=(13.0, 15.0),
        target_adjacencies=["drawing_room", "kitchen", "staircase", "bedroom"]
    ),
    "kitchen": FunctionalRoomArchetype(
        room_type="kitchen",
        zoning="Mid-Living-Service",
        aspect_ratio_range=(0.75, 1.3),
        footprint_ratio_range=(0.08, 0.14),
        min_dim_ft=(8.0, 10.0),
        target_adjacencies=["living_room", "dining_room", "ots"]
    ),
    "bedroom": FunctionalRoomArchetype(
        room_type="bedroom",
        zoning="Rear-Private",
        aspect_ratio_range=(0.85, 1.25),
        footprint_ratio_range=(0.14, 0.22),
        min_dim_ft=(12.0, 14.0),
        target_adjacencies=["living_room", "bathroom", "ots"]
    ),
    "bathroom": FunctionalRoomArchetype(
        room_type="bathroom",
        zoning="Rear-Private",
        aspect_ratio_range=(0.6, 1.1),
        footprint_ratio_range=(0.03, 0.07),
        min_dim_ft=(5.0, 7.0),
        target_adjacencies=["bedroom", "ots"]
    ),
    "staircase": FunctionalRoomArchetype(
        room_type="staircase",
        zoning="Vertical-Circulation",
        aspect_ratio_range=(0.45, 0.8),
        footprint_ratio_range=(0.06, 0.10),
        min_dim_ft=(6.5, 12.0),
        target_adjacencies=["living_room", "foyer"]
    ),
    "ots": FunctionalRoomArchetype(
        room_type="ots",
        zoning="Rear-Private",
        aspect_ratio_range=(0.4, 1.2),
        footprint_ratio_range=(0.02, 0.06),
        min_dim_ft=(3.0, 5.0),
        target_adjacencies=["bathroom", "bedroom", "kitchen"]
    )
}


class TopologicalKnowledgeBase:
    """Manages scale-free planar graph topologies and vertical architectural constraints."""
    
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(TopologicalKnowledgeBase, cls).__new__(cls)
            cls._instance._init_knowledge()
        return cls._instance

    def _init_knowledge(self):
        self.graphs: Dict[str, nx.Graph] = {}
        self.topologies_by_scale: Dict[str, List[Dict[str, Any]]] = {
            "3_marla": [],
            "5_marla": [],
            "7_marla": [],
            "10_marla": [],
            "1_kanal": []
        }
        self._load_extracted_graphs()

    def _load_extracted_graphs(self):
        json_files = glob.glob(os.path.join(KNOWLEDGE_DIR, "*.json"))
        for j_path in json_files:
            if j_path.endswith("manifest_index.json"):
                continue
            try:
                with open(j_path, "r", encoding="utf-8") as f:
                    data = json.load(f)
                
                cat = data.get("plot", {}).get("category", "5_marla")
                if cat == "elevation_paired":
                    cat = "5_marla"

                g = nx.Graph()
                rooms = data.get("rooms", [])
                cg = data.get("circulation_graph", {})

                for r in rooms:
                    g.add_node(
                        r["id"],
                        name=r["name"],
                        type=r["type"],
                        zoning=r.get("zoning", "Mid-Living-Service"),
                        bbox=r["bbox_ft"],
                        area=r["area_sqft"],
                        aspect=r.get("aspect_ratio", 1.0)
                    )

                for r1_id, neighbors in cg.items():
                    for r2_id in neighbors:
                        if g.has_node(r1_id) and g.has_node(r2_id):
                            g.add_edge(r1_id, r2_id)

                stem = os.path.splitext(os.path.basename(j_path))[0]
                self.graphs[stem] = g

                if cat in self.topologies_by_scale:
                    self.topologies_by_scale[cat].append({
                        "id": stem,
                        "graph": g,
                        "rooms": rooms,
                        "fenestrations": data.get("fenestrations", []),
                        "setbacks": data.get("plot", {}).get("setbacks_ft", {})
                    })
            except Exception:
                pass

    def query_optimal_topology(self, marla_category: str, required_bedrooms: int) -> Dict[str, Any]:
        """Finds the best-matching topology from extracted knowledge for the requested program."""
        cands = self.topologies_by_scale.get(marla_category, self.topologies_by_scale["5_marla"])
        if not cands:
            # Fallback to any scale
            cands = self.topologies_by_scale["5_marla"]

        best_cand = cands[0]
        best_diff = 999
        for c in cands:
            bed_count = sum(1 for r in c["rooms"] if r["type"] == "bedroom")
            diff = abs(bed_count - required_bedrooms)
            if diff < best_diff:
                best_diff = diff
                best_cand = c

        return best_cand

    @staticmethod
    def get_upper_floor_spatial_program(
        ground_rooms: List[Dict[str, Any]],
        target_bedrooms: int,
        plot_w: float,
        plot_l: float
    ) -> List[Dict[str, Any]]:
        """
        Synthesizes an authentic dedicated Upper Floor program without ever duplicating
        surplus polygons into 'Upper Study & Workstation'.
        
        Enforces:
        - Structural vertical stacking (bathrooms over ground wet zones)
        - Staircase opening continuity (same x,y coordinates)
        - Front open terrace / balcony above the ground car porch
        - Upper Family Lounge & Master Bedroom Suites
        """
        upper_rooms = []
        r_id = 1

        # 1. Front Open Terrace / Balcony above the ground car porch
        porch_r = next((r for r in ground_rooms if r["type"] == "garage"), None)
        if porch_r:
            bx, by, bw, bl = porch_r["bbox_ft"]
            upper_rooms.append({
                "id": f"UF_TERRACE_{r_id}",
                "name": "Front Panoramic Terrace & Balcony",
                "type": "balcony",
                "zoning": "Front-Public",
                "bbox_ft": [bx, by, bw, bl],
                "area_sqft": round(bw * bl, 1),
                "features": ["Tempered Glass Railing (h=3.5')", "Outdoor Sitting"],
                "floor_level": 1
            })
            r_id += 1

        # 2. Upper Staircase Landing (Exactly stacked over ground staircase)
        stair_r = next((r for r in ground_rooms if r["type"] == "staircase"), None)
        if stair_r:
            bx, by, bw, bl = stair_r["bbox_ft"]
            upper_rooms.append({
                "id": f"UF_STAIR_{r_id}",
                "name": "Staircase Landing & Circulation Core",
                "type": "staircase",
                "zoning": "Vertical-Circulation",
                "bbox_ft": [bx, by, bw, bl],
                "area_sqft": round(bw * bl, 1),
                "features": ["Continuous Headroom Core", "Access to Roof Mumty"],
                "floor_level": 1
            })
            r_id += 1

        # 3. Upper Family Lounge (Central social hub)
        lounge_r = next((r for r in ground_rooms if r["type"] == "living_room"), None)
        if lounge_r:
            bx, by, bw, bl = lounge_r["bbox_ft"]
            upper_rooms.append({
                "id": f"UF_LOUNGE_{r_id}",
                "name": "Upper Family TV Lounge",
                "type": "living_room",
                "zoning": "Mid-Living-Service",
                "bbox_ft": [bx, by, bw, bl],
                "area_sqft": round(bw * bl, 1),
                "features": ["Double Height Overlook", "Media Center"],
                "floor_level": 1
            })
            r_id += 1

        # 4. Upper Master Bedrooms & Ensuites (Fulfilling required bedroom quota)
        # Ground floor typically has 1 master bed. Remaining bedrooms go to upper floor.
        upper_beds_needed = max(1, target_bedrooms - 1)
        drawing_r = next((r for r in ground_rooms if r["type"] == "drawing_room"), None)
        
        # Upper Bed 1 above Drawing Room
        if drawing_r and upper_beds_needed >= 1:
            bx, by, bw, bl = drawing_r["bbox_ft"]
            upper_rooms.append({
                "id": f"UF_BED_{r_id}",
                "name": "First Floor Front Master Suite",
                "type": "bedroom",
                "zoning": "Front-Public",
                "bbox_ft": [bx, by, bw, bl],
                "area_sqft": round(bw * bl, 1),
                "features": ["Front Window Vista", "Walk-in Closet"],
                "floor_level": 1
            })
            r_id += 1

        # Upper Bed 2 in Rear Zone
        ground_beds = [r for r in ground_rooms if r["type"] == "bedroom"]
        if ground_beds:
            gb = ground_beds[0]
            bx, by, bw, bl = gb["bbox_ft"]
            upper_rooms.append({
                "id": f"UF_BED_{r_id}",
                "name": "First Floor Rear Suite 2",
                "type": "bedroom",
                "zoning": "Rear-Private",
                "bbox_ft": [bx, by, bw, bl],
                "area_sqft": round(bw * bl, 1),
                "features": ["Overlooking Rear Setback", "Quiet Bedroom Zone"],
                "floor_level": 1
            })
            r_id += 1

        # Upper Bathrooms (Vertically stacked over ground bathrooms for wet plumbing)
        ground_baths = [r for r in ground_rooms if r["type"] == "bathroom"]
        for gb_bath in ground_baths:
            bx, by, bw, bl = gb_bath["bbox_ft"]
            upper_rooms.append({
                "id": f"UF_BATH_{r_id}",
                "name": f"First Floor En-suite Bath {r_id}",
                "type": "bathroom",
                "zoning": "Rear-Private",
                "bbox_ft": [bx, by, bw, bl],
                "area_sqft": round(bw * bl, 1),
                "features": ["Vertical Wet Plumbing Stack (0.0 offset)", "Mechanical Exhaust"],
                "floor_level": 1
            })
            r_id += 1

        # OTS shaft continuity
        ground_ots = next((r for r in ground_rooms if r["type"] == "ots"), None)
        if ground_ots:
            bx, by, bw, bl = ground_ots["bbox_ft"]
            upper_rooms.append({
                "id": f"UF_OTS_{r_id}",
                "name": "Open-To-Sky (OTS) Shaft Void",
                "type": "ots",
                "zoning": "Rear-Private",
                "bbox_ft": [bx, by, bw, bl],
                "area_sqft": round(bw * bl, 1),
                "features": ["Continuous Vertical Ventilation Shaft"],
                "floor_level": 1
            })
            r_id += 1

        return upper_rooms

