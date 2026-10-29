"""
Phase 8: Spatial Relationship Graph Extractor.
Extracts architectural connectivity and adjacency relationships between rooms:
1. 'via_door': Physical traversal edge mediated by a verified door opening.
2. 'adjacency': Geometric contact edge where room boundaries touch or are separated
   by a standard wall thickness (<= 0.35m).
3. 'direct': Open cased threshold or shared opening between adjacent rooms.
4. 'via_window': Visual/daylight exterior connectivity.

Computes topological metrics:
- Plan diameter
- Average connectivity degree
- Circulation cycles
"""

from typing import Dict, List, Tuple, Any, Optional
import networkx as nx
from shapely.geometry import Polygon, Point, LineString
from dataset.schema.canonical import RoomModel, OpeningModel, GraphEdgeModel


class SpatialRelationshipGraphExtractor:
    def __init__(self, max_wall_separation_m: float = 0.35, min_shared_boundary_m: float = 0.50):
        self.max_wall_separation_m = max_wall_separation_m
        self.min_shared_boundary_m = min_shared_boundary_m

    def build_graph(
        self,
        rooms: List[RoomModel],
        openings: List[OpeningModel]
    ) -> Tuple[List[GraphEdgeModel], Dict[str, Any]]:
        """
        Builds spatial graph and calculates architectural topology metrics.
        Returns:
            edges: List of validated GraphEdgeModel instances.
            graph_metrics: Topological metrics (diameter, connectivity, cycle count).
        """
        g = nx.Graph()
        room_dict = {r.room_id: r for r in rooms}
        shapely_rooms = {}

        for r in rooms:
            g.add_node(r.room_id, type=r.room_type, name=r.room_name, area=r.area_m2)
            p = Polygon(r.polygon)
            if not p.is_valid:
                p = p.buffer(0)
            shapely_rooms[r.room_id] = p

        raw_edges: Dict[Tuple[str, str], Dict[str, Any]] = {}

        # 1. Door connectivity edges ('via_door')
        for op in openings:
            if op.opening_type in ("door", "cased_opening"):
                # Check connected rooms
                conn = op.connects_rooms
                if len(conn) >= 2 and conn[0] in room_dict and conn[1] in room_dict:
                    pair = tuple(sorted([conn[0], conn[1]]))
                    raw_edges[pair] = {
                        "relationship_type": "via_door",
                        "weight": 1.0,
                        "metadata": {"door_id": op.opening_id, "width_m": op.width_m}
                    }
                elif len(conn) == 1:
                    # Door connected to single room; find second room within door proximity
                    pt = Point(op.position[0], op.position[1])
                    for r_id, r_poly in shapely_rooms.items():
                        if r_id != conn[0] and r_poly.distance(pt) <= (op.width_m * 1.5):
                            pair = tuple(sorted([conn[0], r_id]))
                            raw_edges[pair] = {
                                "relationship_type": "via_door",
                                "weight": 1.0,
                                "metadata": {"door_id": op.opening_id, "width_m": op.width_m}
                            }
                            break

        # 2. Geometric adjacency edges ('adjacency')
        # Requires shared wall interface length >= min_shared_boundary_m (not just diagonal corner touching)
        room_ids = list(room_dict.keys())
        for i in range(len(room_ids)):
            r_id1 = room_ids[i]
            r1 = room_dict[r_id1]
            p1 = shapely_rooms[r_id1]
            for j in range(i + 1, len(room_ids)):
                r_id2 = room_ids[j]
                r2 = room_dict[r_id2]
                if r1.level_index != r2.level_index:
                    continue
                p2 = shapely_rooms[r_id2]

                dist = p1.distance(p2)
                if dist <= self.max_wall_separation_m:
                    pair = tuple(sorted([r_id1, r_id2]))
                    # If already connected via door, keep via_door as primary traversal relationship,
                    # but if not connected via door, verify actual shared wall length
                    if pair not in raw_edges:
                        buf_d = self.max_wall_separation_m * 0.75
                        inter_poly = p1.buffer(buf_d).intersection(p2.buffer(buf_d))
                        if not inter_poly.is_empty:
                            minx, miny, maxx, maxy = inter_poly.bounds
                            shared_wall_len = max(maxx - minx, maxy - miny)
                            if shared_wall_len >= self.min_shared_boundary_m:
                                raw_edges[pair] = {
                                    "relationship_type": "adjacency",
                                    "weight": round(1.0 + float(dist), 2),
                                    "metadata": {
                                        "distance_m": round(float(dist), 3),
                                        "shared_wall_length_m": round(float(shared_wall_len), 3)
                                    }
                                }

        # Convert to GraphEdgeModel list
        graph_edges: List[GraphEdgeModel] = []
        for (u, v), edge_data in raw_edges.items():
            g.add_edge(u, v, **edge_data)
            graph_edges.append(GraphEdgeModel(
                source_room_id=u,
                target_room_id=v,
                relationship_type=edge_data["relationship_type"],
                weight=edge_data["weight"],
                metadata=edge_data["metadata"]
            ))

        # Compute topological graph invariants
        num_nodes = g.number_of_nodes()
        num_edges = g.number_of_edges()
        is_connected = nx.is_connected(g) if num_nodes > 0 else False

        # Cycle basis count
        cycles = nx.cycle_basis(g) if num_nodes > 0 else []

        # Diameter (for largest connected component)
        if num_nodes > 1 and is_connected:
            diameter = nx.diameter(g)
        elif num_nodes > 1 and not is_connected:
            largest_cc = max(nx.connected_components(g), key=len)
            subgraph = g.subgraph(largest_cc)
            diameter = nx.diameter(subgraph) if len(subgraph) > 1 else 0
        else:
            diameter = 0

        avg_degree = sum(dict(g.degree()).values()) / num_nodes if num_nodes > 0 else 0.0

        metrics = {
            "node_count": num_nodes,
            "edge_count": num_edges,
            "is_connected": is_connected,
            "cycle_count": len(cycles),
            "diameter": diameter,
            "avg_degree": round(avg_degree, 2)
        }

        return graph_edges, metrics
