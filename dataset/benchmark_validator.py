"""
Phase 2: Golden 50 Benchmark Schema, Stratification Protocol, and Evaluator.
Computes multi-layer evaluation metrics:
- Room Polygon mIoU & Area Delta
- Door/Window Precision, Recall, and F1
- Adjacency and Door-Connectivity Graph Metrics
- Dimension Normalization Accuracy
"""

import json
import os
from typing import Dict, List, Optional, Tuple, Any
from pydantic import BaseModel, Field
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union
import networkx as nx


class Point2D(BaseModel):
    x: float
    y: float


class WallGT(BaseModel):
    wall_id: str
    wall_type: str = Field(description="'exterior' or 'interior'")
    centerline: List[List[float]] = Field(description="[[x1, y1], [x2, y2]] in meters or normalized coords")
    thickness_m: float = 0.20


class OpeningGT(BaseModel):
    opening_id: str
    opening_type: str = Field(description="'door' or 'window'")
    position: List[float] = Field(description="[x, y] midpoint")
    width_m: float = 0.90
    connects_rooms: List[str] = Field(default_factory=list, description="IDs of connected rooms (for doors)")
    associated_wall_id: Optional[str] = None


class RoomGT(BaseModel):
    room_id: str
    room_type: str = Field(description="'bedroom', 'bathroom', 'kitchen', 'living_room', 'dining_room', 'corridor', 'balcony', 'unclassified'")
    room_name: str
    polygon: List[List[float]] = Field(description="List of [x, y] coordinates forming closed ring")
    area_m2: float
    level_index: int = 0
    is_habitable: bool = True


class DimensionGT(BaseModel):
    raw_text: str
    normalized_value_m: float
    unit: str = "m"
    associated_wall_id: Optional[str] = None


class GraphEdgeGT(BaseModel):
    source_room_id: str
    target_room_id: str
    relationship_type: str = Field(description="'via_door', 'adjacency', 'direct', 'via_window'")


class GoldenPlan(BaseModel):
    plan_id: str
    category: str = Field(description="One of: '1-2_bedroom', '3_bedroom', '4+_bedroom', 'irregular_l_shaped', 'duplex_multi_floor', 'unusual_commercial'")
    building_boundary: List[List[float]]
    total_area_m2: float
    floor_count: int = 1
    levels: List[int] = Field(default_factory=lambda: [0])
    walls: List[WallGT]
    openings: List[OpeningGT]
    rooms: List[RoomGT]
    dimensions: List[DimensionGT] = Field(default_factory=list)
    graph_edges: List[GraphEdgeGT] = Field(default_factory=list)
    provenance: Dict[str, Any] = Field(default_factory=dict)


class BenchmarkEvaluator:
    @staticmethod
    def polygon_iou(poly1_coords: List[List[float]], poly2_coords: List[List[float]]) -> float:
        """Computes exact geometric IoU between two polygon rings."""
        p1 = Polygon(poly1_coords)
        p2 = Polygon(poly2_coords)
        if not p1.is_valid:
            p1 = p1.buffer(0)
        if not p2.is_valid:
            p2 = p2.buffer(0)
        if p1.is_empty or p2.is_empty:
            return 0.0
        inter = p1.intersection(p2).area
        union = p1.union(p2).area
        return inter / union if union > 0 else 0.0

    @classmethod
    def evaluate_rooms(cls, pred_rooms: List[Dict], gt_rooms: List[RoomGT], iou_threshold: float = 0.5) -> Dict[str, float]:
        """Evaluates room detection mIoU, classification accuracy, precision, and recall."""
        matched_gt = set()
        matched_pred = set()
        ious = []
        correct_classes = 0

        for i, pred in enumerate(pred_rooms):
            pred_poly = pred.get("polygon", [])
            pred_type = pred.get("type", "unclassified")
            best_iou = 0.0
            best_j = -1

            for j, gt in enumerate(gt_rooms):
                if j in matched_gt:
                    continue
                iou = cls.polygon_iou(pred_poly, gt.polygon)
                if iou > best_iou:
                    best_iou = iou
                    best_j = j

            if best_iou >= iou_threshold and best_j >= 0:
                matched_gt.add(best_j)
                matched_pred.add(i)
                ious.append(best_iou)
                if pred_type == gt_rooms[best_j].room_type:
                    correct_classes += 1

        precision = len(matched_pred) / len(pred_rooms) if pred_rooms else 0.0
        recall = len(matched_gt) / len(gt_rooms) if gt_rooms else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0
        mean_iou = float(sum(ious) / len(ious)) if ious else 0.0
        class_acc = (correct_classes / len(matched_pred)) if matched_pred else 0.0

        return {
            "room_precision": round(precision, 4),
            "room_recall": round(recall, 4),
            "room_f1": round(f1, 4),
            "mean_iou": round(mean_iou, 4),
            "classification_accuracy": round(class_acc, 4)
        }

    @classmethod
    def evaluate_graph(cls, pred_edges: List[Dict], gt_edges: List[GraphEdgeGT]) -> Dict[str, float]:
        """Evaluates spatial relationship graph edge precision, recall, and F1."""
        gt_set = set((e.source_room_id, e.target_room_id, e.relationship_type) for e in gt_edges)
        # Also support undirected matching for adjacency
        gt_undirected = set(frozenset([e.source_room_id, e.target_room_id]) for e in gt_edges if e.relationship_type in ['adjacency', 'via_door'])

        pred_set = set((e.get("source"), e.get("target"), e.get("type")) for e in pred_edges)
        pred_undirected = set(frozenset([e.get("source"), e.get("target")]) for e in pred_edges if e.get("type") in ['adjacency', 'via_door'])

        matched = len(pred_undirected.intersection(gt_undirected))
        precision = matched / len(pred_undirected) if pred_undirected else 0.0
        recall = matched / len(gt_undirected) if gt_undirected else 0.0
        f1 = (2 * precision * recall / (precision + recall)) if (precision + recall) > 0 else 0.0

        return {
            "graph_edge_precision": round(precision, 4),
            "graph_edge_recall": round(recall, 4),
            "graph_edge_f1": round(f1, 4)
        }
