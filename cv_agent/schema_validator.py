"""
Formal JSON Schema & Validator for Architectural Floor Plan Extraction.

Enforces Section 5 Schema Requirements:
A. Metadata (schema version, drawing ID, hash, timestamps, statuses)
B. Drawing information (type, orientation, plot dimensions, scale calibration)
C. Extracted text (exact OCR, normalized, bounding box, confidences)
D. Rooms (ID, category, dimensions, polygons, adjacency, connected doors)
E. Architectural elements (walls, doors, windows, stairs, columns, outdoor spaces)
F. Validation results (independent metrics, checks, final statuses: PASS_VERIFIED, PASS_WITH_WARNINGS, NEEDS_REVIEW, FAILED, PARTIALLY_PROCESSED, NOT_EVALUABLE)
G. Uncertainty and provenance (ambiguous readings, conflicting evidence, iteration history)
"""

import json
from typing import Dict, List, Tuple, Any, Optional
import jsonschema

FLOORPLAN_JSON_SCHEMA: Dict[str, Any] = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "ArchitecturalFloorPlanExtractionSchema",
    "type": "object",
    "required": [
        "metadata",
        "drawing_information",
        "extracted_text",
        "rooms",
        "architectural_elements",
        "validation_results",
        "uncertainty_and_provenance"
    ],
    "properties": {
        "metadata": {
            "type": "object",
            "required": [
                "schema_version",
                "drawing_id",
                "original_filename",
                "original_relative_path",
                "source_folder",
                "file_hash_sha256",
                "file_hash_md5",
                "image_width",
                "image_height",
                "processing_timestamp",
                "pipeline_version",
                "processing_status"
            ],
            "properties": {
                "schema_version": {"type": "string"},
                "drawing_id": {"type": "string"},
                "original_filename": {"type": "string"},
                "original_relative_path": {"type": "string"},
                "source_folder": {"type": "string"},
                "file_hash_sha256": {"type": "string"},
                "file_hash_md5": {"type": "string"},
                "phash": {"type": "string"},
                "image_width": {"type": "integer", "minimum": 1},
                "image_height": {"type": "integer", "minimum": 1},
                "processing_timestamp": {"type": "string"},
                "pipeline_version": {"type": "string"},
                "model_and_ocr_engine_versions": {"type": "object"},
                "processing_status": {
                    "type": "string",
                    "enum": [
                        "PASS_VERIFIED",
                        "PASS_WITH_WARNINGS",
                        "NEEDS_REVIEW",
                        "FAILED",
                        "PARTIALLY_PROCESSED",
                        "NOT_EVALUABLE"
                    ]
                }
            }
        },
        "drawing_information": {
            "type": "object",
            "required": [
                "drawing_type",
                "detected_floor",
                "measurement_units",
                "scale_information"
            ],
            "properties": {
                "drawing_type": {
                    "type": "string",
                    "enum": ["floor_plan", "elevation", "elevation_with_floorplan", "combined_sheet", "uncertain"]
                },
                "detected_floor": {"type": "string"},
                "drawing_orientation": {"type": "string"},
                "plot_width_ft": {"type": ["number", "null"]},
                "plot_depth_ft": {"type": ["number", "null"]},
                "measurement_units": {"type": "string"},
                "scale_information": {
                    "type": "object",
                    "required": ["calibration_confidence"],
                    "properties": {
                        "pixels_per_meter": {"type": ["number", "null"]},
                        "pixels_per_foot": {"type": ["number", "null"]},
                        "calibration_confidence": {"type": "number"},
                        "calibration_method": {"type": "string"},
                        "scale_consistency_error_pct": {"type": ["number", "null"]}
                    }
                },
                "title_block_information": {"type": "object"}
            }
        },
        "extracted_text": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "text_id",
                    "original_ocr_text",
                    "normalized_text",
                    "bounding_box",
                    "confidence",
                    "validation_result"
                ],
                "properties": {
                    "text_id": {"type": "string"},
                    "original_ocr_text": {"type": "string"},
                    "normalized_text": {"type": "string"},
                    "bounding_box": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 4,
                        "maxItems": 4
                    },
                    "confidence": {"type": "number"},
                    "preprocessing_variant": {"type": "string"},
                    "associated_object": {"type": ["string", "null"]},
                    "validation_result": {"type": "string"},
                    "alternative_readings": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "rooms": {
            "type": "array",
            "items": {
                "type": "object",
                "required": [
                    "room_id",
                    "room_name",
                    "room_category",
                    "pixel_bounding_box",
                    "pixel_polygon",
                    "room_label_confidence",
                    "boundary_confidence",
                    "adjacency_list",
                    "connected_doors",
                    "extraction_warnings"
                ],
                "properties": {
                    "room_id": {"type": "string"},
                    "room_name": {"type": "string"},
                    "room_category": {"type": "string"},
                    "original_dimension_text": {"type": ["string", "null"]},
                    "normalized_width_m": {"type": ["number", "null"]},
                    "normalized_length_m": {"type": ["number", "null"]},
                    "normalized_width_ft": {"type": ["number", "null"]},
                    "normalized_length_ft": {"type": ["number", "null"]},
                    "unit": {"type": "string"},
                    "source_text_references": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "pixel_bounding_box": {
                        "type": "array",
                        "items": {"type": "integer"},
                        "minItems": 4,
                        "maxItems": 4
                    },
                    "pixel_polygon": {
                        "type": "array",
                        "items": {
                            "type": "array",
                            "items": {"type": "number"},
                            "minItems": 2,
                            "maxItems": 2
                        }
                    },
                    "real_world_area_sqm": {"type": ["number", "null"]},
                    "real_world_area_sqft": {"type": ["number", "null"]},
                    "pixel_area": {"type": "number"},
                    "room_label_confidence": {"type": "number"},
                    "boundary_confidence": {"type": "number"},
                    "dimension_confidence": {"type": ["number", "null"]},
                    "adjacency_list": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "connected_doors": {
                        "type": "array",
                        "items": {"type": "string"}
                    },
                    "extraction_warnings": {
                        "type": "array",
                        "items": {"type": "string"}
                    }
                }
            }
        },
        "architectural_elements": {
            "type": "object",
            "required": [
                "walls",
                "doors",
                "windows",
                "stairs"
            ],
            "properties": {
                "walls": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["element_id", "element_type", "geometry", "confidence", "detection_method", "validation_status"],
                        "properties": {
                            "element_id": {"type": "string"},
                            "element_type": {"type": "string"},
                            "wall_type": {"type": "string"},
                            "geometry": {"type": "object"},
                            "thickness_px": {"type": "number"},
                            "orientation": {"type": "string"},
                            "associated_rooms": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number"},
                            "detection_method": {"type": "string"},
                            "validation_status": {"type": "string"}
                        }
                    }
                },
                "doors": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["element_id", "element_type", "geometry", "confidence", "detection_method", "validation_status"],
                        "properties": {
                            "element_id": {"type": "string"},
                            "element_type": {"type": "string"},
                            "geometry": {"type": "object"},
                            "position": {"type": "array", "items": {"type": "number"}},
                            "swing_radius_px": {"type": "number"},
                            "swing_orientation": {"type": "string"},
                            "associated_rooms": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number"},
                            "detection_method": {"type": "string"},
                            "validation_status": {"type": "string"}
                        }
                    }
                },
                "windows": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["element_id", "element_type", "geometry", "confidence", "detection_method", "validation_status"],
                        "properties": {
                            "element_id": {"type": "string"},
                            "element_type": {"type": "string"},
                            "geometry": {"type": "object"},
                            "position": {"type": "array", "items": {"type": "number"}},
                            "orientation": {"type": "string"},
                            "associated_rooms": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number"},
                            "detection_method": {"type": "string"},
                            "validation_status": {"type": "string"}
                        }
                    }
                },
                "stairs": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["element_id", "element_type", "geometry", "confidence", "detection_method", "validation_status"],
                        "properties": {
                            "element_id": {"type": "string"},
                            "element_type": {"type": "string"},
                            "geometry": {"type": "object"},
                            "step_count_estimate": {"type": "integer"},
                            "flight_direction": {"type": "string"},
                            "associated_rooms": {"type": "array", "items": {"type": "string"}},
                            "confidence": {"type": "number"},
                            "detection_method": {"type": "string"},
                            "validation_status": {"type": "string"}
                        }
                    }
                },
                "columns": {
                    "type": "array",
                    "items": {"type": "object"}
                },
                "outdoor_spaces": {
                    "type": "array",
                    "items": {"type": "object"}
                }
            }
        },
        "validation_results": {
            "type": "object",
            "required": [
                "ocr_validation",
                "room_count_validation",
                "dimension_validation",
                "geometry_validation",
                "connectivity_validation",
                "duplicate_detection",
                "missing_feature_checks",
                "source_vs_extracted_metrics",
                "failed_checks",
                "warnings",
                "recommended_corrective_actions",
                "final_status"
            ],
            "properties": {
                "ocr_validation": {"type": "object"},
                "room_count_validation": {"type": "object"},
                "dimension_validation": {"type": "object"},
                "geometry_validation": {"type": "object"},
                "connectivity_validation": {"type": "object"},
                "duplicate_detection": {"type": "object"},
                "missing_feature_checks": {"type": "object"},
                "source_vs_extracted_metrics": {
                    "type": "object",
                    "required": [
                        "ssim",
                        "psnr_db",
                        "pixel_mae",
                        "edge_iou",
                        "composite_quality_score"
                    ],
                    "properties": {
                        "ssim": {"type": "number"},
                        "psnr_db": {"type": "number"},
                        "pixel_mae": {"type": "number"},
                        "edge_iou": {"type": "number"},
                        "composite_quality_score": {"type": "number"},
                        "geometry_f1": {"type": ["number", "null"]},
                        "wall_continuity": {"type": ["number", "null"]},
                        "door_jamb_validity": {"type": ["number", "null"]}
                    }
                },
                "failed_checks": {"type": "array", "items": {"type": "string"}},
                "warnings": {"type": "array", "items": {"type": "string"}},
                "recommended_corrective_actions": {"type": "array", "items": {"type": "string"}},
                "final_status": {
                    "type": "string",
                    "enum": [
                        "PASS_VERIFIED",
                        "PASS_WITH_WARNINGS",
                        "NEEDS_REVIEW",
                        "FAILED",
                        "PARTIALLY_PROCESSED",
                        "NOT_EVALUABLE"
                    ]
                }
            }
        },
        "uncertainty_and_provenance": {
            "type": "object",
            "required": [
                "ambiguous_readings",
                "missing_dimensions",
                "conflicting_evidence",
                "inferred_geometry",
                "human_corrections",
                "processing_iteration_history"
            ],
            "properties": {
                "ambiguous_readings": {"type": "array", "items": {"type": "string"}},
                "missing_dimensions": {"type": "array", "items": {"type": "string"}},
                "conflicting_evidence": {"type": "array", "items": {"type": "string"}},
                "inferred_geometry": {"type": "array", "items": {"type": "string"}},
                "human_corrections": {"type": "array", "items": {"type": "string"}},
                "processing_iteration_history": {
                    "type": "array",
                    "items": {
                        "type": "object",
                        "required": ["iteration", "stage_modified", "action_taken", "metrics_before", "metrics_after", "outcome"],
                        "properties": {
                            "iteration": {"type": "integer"},
                            "stage_modified": {"type": "string"},
                            "action_taken": {"type": "string"},
                            "metrics_before": {"type": "object"},
                            "metrics_after": {"type": "object"},
                            "outcome": {"type": "string"}
                        }
                    }
                }
            }
        }
    }
}


def validate_floorplan_json(data: Dict[str, Any]) -> Tuple[bool, List[str]]:
    """
    Validates data dictionary against the formal architectural schema.
    Returns (is_valid, list_of_error_messages).
    """
    validator = jsonschema.Draft7Validator(FLOORPLAN_JSON_SCHEMA)
    errors = sorted(validator.iter_errors(data), key=lambda e: e.path)
    if not errors:
        return True, []
    
    error_msgs = []
    for err in errors:
        loc = " -> ".join([str(p) for p in err.path]) or "root"
        error_msgs.append(f"[{loc}]: {err.message}")
    return False, error_msgs
