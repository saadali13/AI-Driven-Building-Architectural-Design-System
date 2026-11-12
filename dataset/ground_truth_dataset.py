"""
Ground Truth Benchmark Dataset Generator for AI Floor Plan Verification.
Constructs verified architectural ground-truth annotations for representative blueprints.
Includes formal train/dev vs. held-out evaluation test splits.
"""

import os
import json
import hashlib
import cv2

GROUND_TRUTH_PLANS = [
    {
        "plan_id": "GT_01_1_00770",
        "split": "dev",
        "folder": "1",
        "filename": "00770eba64db20501bbd30bb21ce6aa5.jpg",
        "category_label": "1 Kanal Luxury Villa",
        "resolution": [877, 1584],
        "aspect_ratio": 0.554,
        "md5_hash": "e6bffb4d4dc549c7ddb082ec1640876b",
        "architectural_elements": {
            "min_expected_rooms": 10,
            "max_expected_rooms": 18,
            "expected_room_count_target": 13,
            "expected_doors_min": 8,
            "expected_doors_max": 18,
            "expected_door_count_target": 12,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 4.5,
            "expected_wall_continuity_min": 0.70,
            "key_labels": ["BATH", "MBED", "DIBATH"],
            "key_dimensions": ["20'-0*14-0\"", "10-3\"x9-0'"],
            "structural_features": ["perimeter_walls", "internal_partitions", "rear_lawn_boundary", "car_porch", "stair_tower"]
        },
        "verification_notes": "Complex 1 Kanal floor plan with large room chambers, multiple ensuites, and dedicated rear service corridor."
    },
    {
        "plan_id": "GT_02_1_027c4",
        "split": "test",
        "folder": "1",
        "filename": "027c487cd8eb1a07ba644f292fd32e0c.jpg",
        "category_label": "1 Kanal Contemporary Estate",
        "resolution": [800, 1163],
        "aspect_ratio": 0.688,
        "md5_hash": "22f39bf92957db80851785cbe66d07ce",
        "architectural_elements": {
            "min_expected_rooms": 8,
            "max_expected_rooms": 15,
            "expected_room_count_target": 11,
            "expected_doors_min": 6,
            "expected_doors_max": 16,
            "expected_door_count_target": 10,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 3.0,
            "expected_wall_continuity_min": 0.72,
            "key_labels": ["TOILET", "KITCHEN", "BEDROOM", "WORKAREA"],
            "key_dimensions": ["2200 x 1530", "3600 x 2000"],
            "structural_features": ["perimeter_walls", "dual_verandas", "enclosed_kitchen", "service_passage"]
        },
        "verification_notes": "Metric-annotated 1 Kanal contemporary drawing with clear perimeter envelope and multiple internal wet areas (Held-out Test)."
    },
    {
        "plan_id": "GT_03_3_0adf5",
        "split": "dev",
        "folder": "3",
        "filename": "0adf5f25feca052f9968d0a9f42bd8eb.jpg",
        "category_label": "3 Marla Urban Compact",
        "resolution": [720, 1042],
        "aspect_ratio": 0.691,
        "md5_hash": "e468dc86fba8a60c721dab313782d539",
        "architectural_elements": {
            "min_expected_rooms": 4,
            "max_expected_rooms": 8,
            "expected_room_count_target": 6,
            "expected_doors_min": 3,
            "expected_doors_max": 8,
            "expected_door_count_target": 5,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 3.8,
            "expected_wall_continuity_min": 0.68,
            "key_labels": ["OPEN", "30'"],
            "key_dimensions": ["12'1.5\"", "4'6\""],
            "structural_features": ["compact_linear_walls", "front_staircase", "compact_courtyard", "party_walls"]
        },
        "verification_notes": "High-density row house footprint typical of 3 Marla compact urban developments."
    },
    {
        "plan_id": "GT_04_3_0d2f2",
        "split": "test",
        "folder": "3",
        "filename": "0d2f29cf25a408c7e552e39b91189b34.jpg",
        "category_label": "3 Marla Small-Plot Multi-Room",
        "resolution": [736, 1104],
        "aspect_ratio": 0.667,
        "md5_hash": "cd49874004c2f6a3f5cc6586a5d7cc15",
        "architectural_elements": {
            "min_expected_rooms": 5,
            "max_expected_rooms": 9,
            "expected_room_count_target": 7,
            "expected_doors_min": 4,
            "expected_doors_max": 9,
            "expected_door_count_target": 6,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 3.5,
            "expected_wall_continuity_min": 0.70,
            "key_labels": ["BATH", "OPEM TO SKAY"],
            "key_dimensions": ["8'-0\"X4'-6\""],
            "structural_features": ["perimeter_walls", "rear_ots_shaft", "central_hall", "front_stair_flight"]
        },
        "verification_notes": "3 Marla plan with clear rear open-to-sky ventilation and dual bath chambers (Held-out Test)."
    },
    {
        "plan_id": "GT_05_5_195e6",
        "split": "dev",
        "folder": "5",
        "filename": "195e61769696aa144d1388a68ef92cc9.jpg",
        "category_label": "5 Marla (25'x50') Standard Family",
        "resolution": [736, 989],
        "aspect_ratio": 0.744,
        "md5_hash": "90ec980f713540cb31373b87795ee640",
        "architectural_elements": {
            "min_expected_rooms": 5,
            "max_expected_rooms": 10,
            "expected_room_count_target": 7,
            "expected_doors_min": 4,
            "expected_doors_max": 10,
            "expected_door_count_target": 7,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 4.0,
            "expected_wall_continuity_min": 0.70,
            "key_labels": ["FOEk"],
            "key_dimensions": [],
            "structural_features": ["load_bearing_brick_walls", "car_porch", "tv_lounge_central", "rear_vent_shaft"]
        },
        "verification_notes": "Standard 5 Marla blueprint format with front driveway and central family living hall."
    },
    {
        "plan_id": "GT_06_5_1dfd8",
        "split": "test",
        "folder": "5",
        "filename": "1dfd85587a24e04e1e93659ba35f33cb.jpg",
        "category_label": "5 Marla Detailed Annotated Plan",
        "resolution": [640, 1136],
        "aspect_ratio": 0.563,
        "md5_hash": "7b92c8b4eb23a1dce994812c93f8fed8",
        "architectural_elements": {
            "min_expected_rooms": 5,
            "max_expected_rooms": 10,
            "expected_room_count_target": 8,
            "expected_doors_min": 5,
            "expected_doors_max": 10,
            "expected_door_count_target": 7,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 3.8,
            "expected_wall_continuity_min": 0.75,
            "key_labels": ["BED ROOM-01", "BED ROOM-02", "BATH", "DRES"],
            "key_dimensions": ["6'x5'-6\"", "6'x6'"],
            "structural_features": ["partition_walls", "dress_room", "master_ensuite", "porch_stairs"]
        },
        "verification_notes": "Exemplary 5 Marla drawing with sharp CAD line work, room labels and imperial dimensions (Held-out Test)."
    },
    {
        "plan_id": "GT_07_7_0162f",
        "split": "dev",
        "folder": "7",
        "filename": "0162fa659d7392157fc0854ef058f419.jpg",
        "category_label": "7 Marla (30'x60') Luxury Residence",
        "resolution": [1200, 1697],
        "aspect_ratio": 0.707,
        "md5_hash": "db384030239efa6a4de1a580a7a38de0",
        "architectural_elements": {
            "min_expected_rooms": 7,
            "max_expected_rooms": 14,
            "expected_room_count_target": 10,
            "expected_doors_min": 6,
            "expected_doors_max": 15,
            "expected_door_count_target": 10,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 4.5,
            "expected_wall_continuity_min": 0.74,
            "key_labels": ["WASH AREA"],
            "key_dimensions": ["84\"X48\""],
            "structural_features": ["9_inch_external_walls", "4.5_inch_partitions", "kitchen_island", "wide_frontage_porch"]
        },
        "verification_notes": "High-resolution 7 Marla blueprint with double bedroom ground floor arrangement and service wash area."
    },
    {
        "plan_id": "GT_08_7_01d47",
        "split": "test",
        "folder": "7",
        "filename": "01d47a008ad8498cf8bc3f78cfc87765.jpg",
        "category_label": "7 Marla Compressed / Low-Res Scan",
        "resolution": [532, 865],
        "aspect_ratio": 0.615,
        "md5_hash": "b6531a038de69791c4c6a23e4aabafaa",
        "architectural_elements": {
            "min_expected_rooms": 4,
            "max_expected_rooms": 9,
            "expected_room_count_target": 6,
            "expected_doors_min": 3,
            "expected_doors_max": 9,
            "expected_door_count_target": 5,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 3.0,
            "expected_wall_continuity_min": 0.65,
            "key_labels": [],
            "key_dimensions": ["14'0\"x16'0\""],
            "structural_features": ["linear_envelope", "central_dining", "drawing_room_entry"]
        },
        "verification_notes": "Lower-resolution compressed scan requiring robust line gap bridging and noise tolerance (Held-out Test)."
    },
    {
        "plan_id": "GT_09_10_052da",
        "split": "dev",
        "folder": "10",
        "filename": "052da9368c90d89e449dc37055603d7d.jpg",
        "category_label": "10 Marla (35'x70') Executive Layout",
        "resolution": [474, 800],
        "aspect_ratio": 0.593,
        "md5_hash": "5d3427c8566bc13c66fe6b231a0e4431",
        "architectural_elements": {
            "min_expected_rooms": 6,
            "max_expected_rooms": 12,
            "expected_room_count_target": 9,
            "expected_doors_min": 5,
            "expected_doors_max": 12,
            "expected_door_count_target": 8,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 3.6,
            "expected_wall_continuity_min": 0.72,
            "key_labels": ["BED ROOM", "TOILET", "OPEN"],
            "key_dimensions": ["11'7\"X13'0\""],
            "structural_features": ["double_bedroom_ground", "drawing_room_external_entry", "wide_car_porch", "lawn"]
        },
        "verification_notes": "10 Marla plan with dual bedroom rear suites and clear door swing arcs."
    },
    {
        "plan_id": "GT_10_10_060d1",
        "split": "test",
        "folder": "10",
        "filename": "060d13de5349461d2064392ce14217fc.jpg",
        "category_label": "10 Marla Luxury Modern Blueprint",
        "resolution": [736, 1308],
        "aspect_ratio": 0.563,
        "md5_hash": "fb6aca5cb1cd13cee809add53305941e",
        "architectural_elements": {
            "min_expected_rooms": 7,
            "max_expected_rooms": 14,
            "expected_room_count_target": 10,
            "expected_doors_min": 6,
            "expected_doors_max": 14,
            "expected_door_count_target": 9,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 4.2,
            "expected_wall_continuity_min": 0.73,
            "key_labels": ["BED-01", "BED-02", "CLOSET", "FOYER"],
            "key_dimensions": ["16 X 12"],
            "structural_features": ["foyer_entry", "walk_in_closets", "staircase_lobby", "side_setback_passages"]
        },
        "verification_notes": "Contemporary 10 Marla architectural layout with foyer, multiple closets, and clear room labels (Held-out Test)."
    },
    {
        "plan_id": "GT_11_ELEV_316c1",
        "split": "dev",
        "folder": "elevationwithfloorplan",
        "filename": "316c1ce21d3d16a6e7e828134413d7fb.jpg",
        "category_label": "Combined Elevation + Blueprint Panel",
        "resolution": [1080, 1350],
        "aspect_ratio": 0.800,
        "md5_hash": "6b9dd1c9ff47d066f98d320f5fdc5019",
        "architectural_elements": {
            "panel_type": "combined_elevation_floorplan",
            "floorplan_crop_box": [0, 607, 1080, 1350],
            "min_expected_rooms": 5,
            "max_expected_rooms": 10,
            "expected_room_count_target": 7,
            "expected_doors_min": 4,
            "expected_doors_max": 10,
            "expected_door_count_target": 6,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 4.0,
            "expected_wall_continuity_min": 0.68,
            "key_labels": ["TOILET", "DRESS"],
            "key_dimensions": ["40'-0\"", "7'0X5'0"],
            "structural_features": ["upper_elevation_facade", "lower_isolated_floor_plan", "veranda", "ensuite_bath"]
        },
        "verification_notes": "Combined presentation sheet requiring automatic isolation of the lower floor plan sub-panel."
    },
    {
        "plan_id": "GT_12_ELEV_398c8",
        "split": "test",
        "folder": "elevationwithfloorplan",
        "filename": "398c88649e95f9986aa61683971e1817.jpg",
        "category_label": "Combined Perspective + 2D Floor Plan",
        "resolution": [1080, 1350],
        "aspect_ratio": 0.800,
        "md5_hash": "26dce0d2574dd855e681aaa7b6b95a65",
        "architectural_elements": {
            "panel_type": "combined_elevation_floorplan",
            "floorplan_crop_box": [0, 607, 1080, 1350],
            "min_expected_rooms": 5,
            "max_expected_rooms": 10,
            "expected_room_count_target": 7,
            "expected_doors_min": 4,
            "expected_doors_max": 10,
            "expected_door_count_target": 6,
            "has_stairs": True,
            "has_courtyard_or_ots": True,
            "expected_wall_thickness_px_target": 4.0,
            "expected_wall_continuity_min": 0.70,
            "key_labels": ["WASH AREA"],
            "key_dimensions": ["49-2\""],
            "structural_features": ["upper_3d_render", "lower_architectural_cad_plan", "living_dining_integrated"]
        },
        "verification_notes": "Difficult combined marketing drawing with top 3D exterior render and bottom architectural line plan (Held-out Test)."
    }
]

def main():
    target_path = os.path.join("dataset", "ground_truth_dataset.json")
    dev_plans = [p for p in GROUND_TRUTH_PLANS if p.get("split") == "dev"]
    test_plans = [p for p in GROUND_TRUTH_PLANS if p.get("split") == "test"]
    payload = {
        "dataset_name": "Antigravity Architectural Ground Truth Benchmark",
        "version": "2.0",
        "total_annotated_plans": len(GROUND_TRUTH_PLANS),
        "dev_split_count": len(dev_plans),
        "test_split_count": len(test_plans),
        "source_folders": ["1", "3", "5", "7", "10", "elevationwithfloorplan"],
        "plans": GROUND_TRUTH_PLANS
    }
    with open(target_path, "w", encoding="utf-8") as f:
        json.dump(payload, f, indent=2)
    print(f"Ground truth dataset saved to {target_path} (Total: {len(GROUND_TRUTH_PLANS)}, Dev: {len(dev_plans)}, Test Held-out: {len(test_plans)}).")

if __name__ == "__main__":
    main()
