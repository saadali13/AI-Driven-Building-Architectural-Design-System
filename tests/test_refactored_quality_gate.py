import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from dataset.schema.canonical import CanonicalFloorPlan, MetadataModel, RoomModel, WallModel, OpeningModel
from generation.quality_gate import FloorPlanQualityGate
from requirements.parser import ArchitecturalProgram, RoomRequirement


def test_quality_gate_compliance():
    # Build CanonicalFloorPlan matching the refactored layout
    rooms = [
        RoomModel(room_id="room_L0_porch", room_type="garage", room_name="Car Porch",
                  polygon=[[0.23, 0.0], [4.50, 0.0], [4.50, 4.80], [0.23, 4.80], [0.23, 0.0]],
                  area_m2=20.5, centroid=[2.36, 2.40], is_habitable=False),
        RoomModel(room_id="room_L0_drawing", room_type="living_room", room_name="Formal Drawing Room",
                  polygon=[[4.50, 0.0], [9.52, 0.0], [9.52, 4.40], [4.50, 4.40], [4.50, 0.0]],
                  area_m2=22.1, centroid=[7.01, 2.20], is_habitable=True),
        RoomModel(room_id="room_L0_stairs", room_type="corridor", room_name="Central Stair Lobby",
                  polygon=[[0.23, 4.80], [2.50, 4.80], [2.50, 8.60], [0.23, 8.60], [0.23, 4.80]],
                  area_m2=8.6, centroid=[1.36, 6.70], is_habitable=False),
        RoomModel(room_id="room_L0_foyer", room_type="corridor", room_name="Grand Foyer",
                  polygon=[[2.50, 4.80], [4.80, 4.80], [4.80, 7.50], [2.50, 7.50], [2.50, 4.80]],
                  area_m2=6.2, centroid=[3.65, 6.15], is_habitable=False),
        RoomModel(room_id="room_L0_powder", room_type="bathroom", room_name="Guest Powder Room",
                  polygon=[[4.80, 4.40], [6.30, 4.40], [6.30, 6.80], [4.80, 6.80], [4.80, 4.40]],
                  area_m2=3.6, centroid=[5.55, 5.60], is_habitable=False),
        RoomModel(room_id="room_L0_dining", room_type="dining_room", room_name="Formal Dining Room",
                  polygon=[[6.30, 4.40], [9.52, 4.40], [9.52, 7.80], [6.30, 7.80], [6.30, 4.40]],
                  area_m2=11.0, centroid=[7.91, 6.10], is_habitable=True),
        RoomModel(room_id="room_L0_tv_lounge", room_type="living_room", room_name="Central Family TV Lounge",
                  polygon=[[2.50, 7.50], [6.30, 7.50], [6.30, 12.20], [2.50, 12.20], [2.50, 7.50]],
                  area_m2=17.9, centroid=[4.40, 9.85], is_habitable=True),
        RoomModel(room_id="room_L0_kitchen", room_type="kitchen", room_name="Modern Show Kitchen",
                  polygon=[[6.30, 7.80], [9.52, 7.80], [9.52, 10.70], [6.30, 10.70], [6.30, 7.80]],
                  area_m2=9.3, centroid=[7.91, 9.25], is_habitable=True),
        RoomModel(room_id="room_L0_dirty_kitchen", room_type="kitchen", room_name="Dirty Kitchen / Utility",
                  polygon=[[6.30, 10.70], [8.10, 10.70], [8.10, 12.20], [6.30, 12.20], [6.30, 10.70]],
                  area_m2=2.7, centroid=[7.20, 11.45], is_habitable=False),
        RoomModel(room_id="room_L0_ots1", room_type="outdoor", room_name="OTS Shaft 1",
                  polygon=[[8.10, 10.70], [9.52, 10.70], [9.52, 12.20], [8.10, 12.20], [8.10, 10.70]],
                  area_m2=2.1, centroid=[8.81, 11.45], is_habitable=False),
        # STRICTLY CONVEX RECTANGULAR BEDROOMS
        RoomModel(room_id="room_L0_bed1", room_type="bedroom", room_name="Ground Master Suite",
                  polygon=[[0.23, 12.20], [4.875, 12.20], [4.875, 15.40], [0.23, 15.40], [0.23, 12.20]],
                  area_m2=14.9, centroid=[2.55, 13.80], is_habitable=True),
        RoomModel(room_id="room_L0_bath1", room_type="bathroom", room_name="Master En-Suite Bath",
                  polygon=[[2.40, 15.40], [4.875, 15.40], [4.875, 17.37], [2.40, 17.37], [2.40, 15.40]],
                  area_m2=4.9, centroid=[3.64, 16.38], is_habitable=False),
        RoomModel(room_id="room_L0_bed2", room_type="bedroom", room_name="Ground Bedroom 2",
                  polygon=[[4.875, 12.20], [9.52, 12.20], [9.52, 15.40], [4.875, 15.40], [4.875, 12.20]],
                  area_m2=14.9, centroid=[7.20, 13.80], is_habitable=True),
        RoomModel(room_id="room_L0_bath2", room_type="bathroom", room_name="Bed 2 En-Suite Bath",
                  polygon=[[4.875, 15.40], [7.80, 15.40], [7.80, 17.37], [4.875, 17.37], [4.875, 15.40]],
                  area_m2=5.8, centroid=[6.34, 16.38], is_habitable=False),
        RoomModel(room_id="room_L0_ots2", room_type="outdoor", room_name="OTS Shaft 2",
                  polygon=[[7.80, 15.40], [9.52, 15.40], [9.52, 17.37], [7.80, 17.37], [7.80, 15.40]],
                  area_m2=3.4, centroid=[8.66, 16.38], is_habitable=False),
    ]

    openings = [
        OpeningModel(opening_id="d1", opening_type="door", position=[3.65, 4.80], width_m=1.40, connects_rooms=["room_L0_porch", "room_L0_foyer"]),
        OpeningModel(opening_id="d2", opening_type="door", position=[4.50, 2.20], width_m=1.00, connects_rooms=["room_L0_porch", "room_L0_drawing"]),
        OpeningModel(opening_id="d3", opening_type="door", position=[6.00, 4.40], width_m=1.35, connects_rooms=["room_L0_drawing", "room_L0_dining"]),
        OpeningModel(opening_id="d_portal", opening_type="door", position=[6.30, 6.75], width_m=1.50, connects_rooms=["room_L0_dining", "room_L0_tv_lounge"]),
        OpeningModel(opening_id="d_pow", opening_type="door", position=[4.80, 5.40], width_m=0.80, connects_rooms=["room_L0_foyer", "room_L0_powder"]),
        OpeningModel(opening_id="d_stair", opening_type="door", position=[2.50, 6.00], width_m=1.15, connects_rooms=["room_L0_foyer", "room_L0_stairs"]),
        OpeningModel(opening_id="d_lounge", opening_type="door", position=[3.65, 7.50], width_m=1.20, connects_rooms=["room_L0_foyer", "room_L0_tv_lounge"]),
        OpeningModel(opening_id="d_kit", opening_type="door", position=[7.91, 7.80], width_m=1.00, connects_rooms=["room_L0_dining", "room_L0_kitchen"]),
        OpeningModel(opening_id="d_dkit", opening_type="door", position=[7.20, 10.70], width_m=0.85, connects_rooms=["room_L0_kitchen", "room_L0_dirty_kitchen"]),
        OpeningModel(opening_id="d_ots1", opening_type="door", position=[8.10, 11.45], width_m=0.80, connects_rooms=["room_L0_dirty_kitchen", "room_L0_ots1"]),
        OpeningModel(opening_id="d6", opening_type="door", position=[2.55, 12.20], width_m=0.95, connects_rooms=["room_L0_tv_lounge", "room_L0_bed1"]),
        OpeningModel(opening_id="d_bath1", opening_type="door", position=[3.64, 15.40], width_m=0.80, connects_rooms=["room_L0_bed1", "room_L0_bath1"]),
        OpeningModel(opening_id="d7", opening_type="door", position=[4.875, 12.20], width_m=0.95, connects_rooms=["room_L0_tv_lounge", "room_L0_bed2"]),
        OpeningModel(opening_id="d_bath2", opening_type="door", position=[6.34, 15.40], width_m=0.80, connects_rooms=["room_L0_bed2", "room_L0_bath2"]),
    ]

    boundary = [[0.0, 0.0], [9.75, 0.0], [9.75, 17.60], [0.0, 17.60], [0.0, 0.0]]

    plan = CanonicalFloorPlan(
        metadata=MetadataModel(plan_id="refactored_10m_plan", source_type="synthetic_generated", floor_count=1, levels=[0]),
        total_area_m2=171.6,
        rooms=rooms,
        walls=[],
        openings=openings,
        boundary=boundary
    )

    program = ArchitecturalProgram(
        project_title="Executive Villa",
        plot_category="10_marla",
        floor_count=1,
        levels=[0],
        requested_room_counts={"bedroom": 2, "bathroom": 3, "kitchen": 2, "living_room": 2},
        rooms=[]
    )

    report = FloorPlanQualityGate.evaluate(plan, program, strict=True)
    print("=== Quality Gate Evaluation Report ===")
    print(f"Final Status: {report['final_status']}")
    print(f"Quality Score: {report['quality_score']}")
    print(f"Critical Failures: {report['critical_failures_count']}")
    print(f"High Failures: {report['high_failures_count']}")
    print(f"Validation Gates: {report['validation_gates']}")
    if report["failures"]:
        print("Failures:")
        for f in report["failures"]:
            print(f" - [{f['code']}] ({f['severity']}) {f['description']}")
    
    assert report["final_status"] == "PASS", f"Quality gate failed: {report['failures']}"
    assert report["critical_failures_count"] == 0
    assert report["high_failures_count"] == 0
    print("[TEST PASSED] Refactored plan achieved 100% Quality Gate PASS!")


if __name__ == "__main__":
    test_quality_gate_compliance()
