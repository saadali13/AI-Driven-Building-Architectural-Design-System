"""
Plan Geometry Engine, Open Prompt ArchiScript & Text-Based AI Civil Architect Interview tests.

Verifies:
  * RAG and fixed society rules are completely removed
  * Marla / Kanal / sq ft / W x L sizing terms are preserved
  * Dense custom requests (such as 5 rooms in 5 Marla with zero setbacks and street door) fit and pass validation
  * Pure text-based AI Civil Architect Interview Bot conducts natural text interviews and updates the brief
  * Doors, wall cutouts, furniture placement, and multi-storey stair stacking work accurately
"""
import copy
import json
import os
import sys

import pytest
from shapely.geometry import box

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from generation import plan_geometry_engine as pge  # noqa: E402
from generation.design_script import SCRIPT_SPEC, parse_script, to_script  # noqa: E402

P = {
    "plot_width_ft": 30.0,
    "plot_length_ft": 60.0,
    "front_setback_ft": 7.5,
    "rear_setback_ft": 5.0,
}

SAMPLE_2_STOREY_SCRIPT = SCRIPT_SPEC.split("design from the client's brief):\n", 1)[1]

FIVE_MARLA_FIVE_ROOMS_SCRIPT = """PLOT 25 x 45
SETBACKS front 0 rear 0
LEVEL 0 "GROUND FLOOR - 5 ROOMS IN 5 MARLA"
ROWS
  11 COLS
    10 | BED ROOM 1 | bedroom | door: CENTRAL LOUNGE
    5 | ENT CORRIDOR | entrance | door: STREET | main_door
    10 | BED ROOM 2 | bedroom | door: CENTRAL LOUNGE
  11 COLS
    10 | BED ROOM 3 | bedroom | door: CENTRAL LOUNGE
    9 | CENTRAL LOUNGE | lounge | door: ENT CORRIDOR
    6 | KITCHEN | kitchen | door: CENTRAL LOUNGE
  12 COLS
    10 | BED ROOM 4 | bedroom | door: CENTRAL LOUNGE
    5 | REAR PASSAGE | corridor | door: CENTRAL LOUNGE
    10 | BED ROOM 5 | bedroom | door: CENTRAL LOUNGE
  11 COLS
    9 | BATH 1 | bath | door: BED ROOM 4
    7 | OTS COURTYARD | ots | door: REAR PASSAGE
    9 | BATH 2 | bath | door: BED ROOM 5
"""


def reference_layout():
    parsed = parse_script(SAMPLE_2_STOREY_SCRIPT, 30.0, 60.0, 7.5, 5.0)
    assert parsed["errors"] == [], parsed["errors"]
    return {"floors": copy.deepcopy(parsed["floors"])}


def _analyse(layout=None, beds=5, baths=5, **plot):
    p = {**P, **plot}
    return pge.analyse_layout(
        layout or reference_layout(),
        p["plot_width_ft"],
        p["plot_length_ft"],
        p["front_setback_ft"],
        p["rear_setback_ft"],
        beds,
        baths,
    )


def _codes(geo):
    return {i["code"] for i in geo["validation"]["errors"]}


def _all_codes(geo):
    return {i["code"] for i in geo["validation"]["errors"] + geo["validation"]["warnings"]}


def _find(tree, room_id):
    if isinstance(tree.get("room"), dict) and tree["room"].get("id") == room_id:
        return tree
    for p in tree.get("parts", []):
        hit = _find(p, room_id)
        if hit:
            return hit
    return None


@pytest.fixture(scope="module")
def ref_geo():
    return _analyse()


# ---------------------------------------------------------------------------
# Core Geometry Engine Checks
# ---------------------------------------------------------------------------

def test_reference_layout_has_zero_errors(ref_geo):
    v = ref_geo["validation"]
    assert v["status"] == "PASS", json.dumps(v["errors"], indent=1)
    assert v["errors"] == []


def test_rooms_tile_the_plot_exactly(ref_geo):
    plot_area = P["plot_width_ft"] * P["plot_length_ft"]
    for fl in ref_geo["floors"]:
        boxes = [box(*pge._rect(r)) for r in fl["rooms"]]
        assert abs(sum(b.area for b in boxes) - plot_area) < 0.5
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                assert boxes[i].intersection(boxes[j]).area < 0.01


def test_every_internal_door_is_on_a_shared_wall(ref_geo):
    W, L = P["plot_width_ft"], P["plot_length_ft"]
    n = 0
    for fl in ref_geo["floors"]:
        by_id = {r["id"]: r for r in fl["rooms"]}
        for d in fl["doors"]:
            n += 1
            assert not pge._on_plot_boundary(d, W, L), d
            a, b = by_id[d["room_id"]], by_id[d["from_id"]]
            edge = pge.shared_edge(a, b)
            assert edge is not None, d
            orient, coord, lo, hi = edge
            assert orient == d["orient"] and abs(coord - d["coord"]) < 1e-6
            assert lo - 1e-6 <= d["s"] < d["e"] <= hi + 1e-6
            assert pge.is_enclosed(a["category"])
    assert n >= 15


def test_windows_only_on_open_air_walls_never_on_party_walls(ref_geo):
    W = P["plot_width_ft"]
    for fl in ref_geo["floors"]:
        for w in fl["windows"]:
            assert not (w["orient"] == "v" and (abs(w["coord"]) < 1e-6 or abs(w["coord"] - W) < 1e-6)), w
            assert w["faces_category"] in ("porch", "outdoor", "ots", "street"), w


def test_furniture_inside_its_room_and_clear_of_every_door_swing(ref_geo):
    for fl in ref_geo["floors"]:
        by_id = {r["id"]: r for r in fl["rooms"]}
        swings = [pge.door_swing_polygon(d) for d in fl["doors"]]
        assert fl["furniture"], "furnishing plan is empty"
        for f in fl["furniture"]:
            fb = box(f["x"], f["y"], f["x"] + f["w"], f["y"] + f["h"])
            assert box(*pge._rect(by_id[f["room_id"]])).buffer(0.01).contains(fb), f
            if f.get("on_counter") or f["type"] == "tree":
                continue
            for s in swings:
                assert fb.intersection(s).area < 0.1, (f, "in door swing")


def test_stair_is_stacked_on_every_floor(ref_geo):
    stairs = [next(r for r in fl["rooms"] if r["category"] == "stair") for fl in ref_geo["floors"]]
    assert pge._rect(stairs[0]) == pge._rect(stairs[1])


def test_wall_geometry_has_true_door_cutouts(ref_geo):
    fl = ref_geo["floors"][0]
    geo = pge.build_wall_geometry(fl["rooms"], fl["doors"], fl["windows"])
    for d in fl["doors"]:
        hole = pge.opening_polygon(d)
        assert geo["walls"].intersection(hole).area < 0.01, d["id"]
        assert geo["solid"].intersection(hole).area > 0.1, d["id"]


# ---------------------------------------------------------------------------
# Open Prompt Freedom: 5 Rooms in 5 Marla (25 x 45 ft) with Zero Setbacks
# ---------------------------------------------------------------------------

def test_five_rooms_in_five_marla_fits_but_windowless_rooms_are_errors():
    from generation.brief_parser import parse_brief, check_requirements, read_site
    site = read_site("5 rooms in 5 marla")
    assert site["width_ft"] == 25.0 and site["length_ft"] == 45.0 and site["marla"] == 5.0
    req = parse_brief("5 rooms in 5 marla", 25.0, 45.0, 1, 5, 2)
    assert req["bedrooms"] == 5

    parsed = parse_script(FIVE_MARLA_FIVE_ROOMS_SCRIPT, 25.0, 45.0, 0.0, 0.0)
    assert parsed["errors"] == [], parsed["errors"]
    geo = pge.analyse_layout({"floors": parsed["floors"]}, 25.0, 45.0, 0.0, 0.0, 5, 2)
    # every room fits and is reachable, but rooms boxed in by other rooms get no window: the engine must say so
    # (a dense brief does not switch daylight off - the design needs an OTS / open strip beside those rooms)
    assert geo["validation"]["status"] == "FAIL"
    assert {e["code"] for e in geo["validation"]["errors"]} == {"LANDLOCKED"}
    assert {"gf_bed_room_3", "gf_central_lounge", "gf_kitchen"} <= {e["room"] for e in geo["validation"]["errors"]}

    # Verify all 5 bedrooms are present and each has a bed placed
    gf = geo["floors"][0]
    beds = [r for r in gf["rooms"] if r["category"] == "bedroom"]
    assert len(beds) == 5
    furnished_bed_rooms = {
        f["room_id"] for f in gf["furniture"] if f["type"] in ("bed_king", "bed_queen", "bed_single")
    }
    assert len(furnished_bed_rooms) == 5

    # Verify street door at y=0 is placed cleanly without DOOR_ON_BOUNDARY error
    street_doors = [d for d in gf["doors"] if d["from_id"] == "STREET"]
    assert len(street_doors) == 1
    assert street_doors[0]["coord"] == 0.0

    # Requirements check passes 5 bedrooms
    rep = {r["item"]: r for r in check_requirements(geo, req, 5, 2)}
    assert rep["5 bedrooms"]["met"]


# ---------------------------------------------------------------------------
# Validator & Tree Builder Tests
# ---------------------------------------------------------------------------

def test_tree_sizes_are_rescaled_to_fill_the_plot():
    tree = {"split": "rows", "parts": [
        {"size_ft": 10, "room": {"id": "a", "type": "lawn"}},
        {"size_ft": 10, "split": "cols", "parts": [
            {"size_ft": 7, "room": {"id": "b", "type": "bedroom"}},
            {"size_ft": 7, "room": {"id": "c", "type": "bedroom"}},
        ]},
    ]}
    rooms = pge.build_rooms_from_tree(tree, 30.0, 50.0, 0)
    assert abs(sum(r["w_ft"] * r["l_ft"] for r in rooms) - 1500.0) < 0.01
    assert max(r["y_ft"] + r["l_ft"] for r in rooms) == 50.0
    assert max(r["x_ft"] + r["w_ft"] for r in rooms) == 30.0


OLD_FREEFORM_LAYOUT = {"floors": [
    {"level": 0, "label": "GROUND FLOOR", "rooms": [
        {"name": "CAR PORCH", "type": "car_porch", "x_ft": 0, "y_ft": 0, "w_ft": 18, "l_ft": 18},
        {"name": "DRAWING ROOM", "type": "drawing", "x_ft": 18, "y_ft": 0, "w_ft": 17, "l_ft": 20},
        {"name": "POWDER ROOM", "type": "powder", "x_ft": 18, "y_ft": 20, "w_ft": 5, "l_ft": 6},
        {"name": "FAMILY TV LOUNGE", "type": "lounge", "x_ft": 0, "y_ft": 20, "w_ft": 23, "l_ft": 22},
        {"name": "SHOW KITCHEN", "type": "kitchen", "x_ft": 23, "y_ft": 20, "w_ft": 12, "l_ft": 14},
        {"name": "MASTER BEDROOM 1", "type": "bedroom", "x_ft": 0, "y_ft": 42, "w_ft": 14, "l_ft": 16},
        {"name": "BEDROOM 2", "type": "bedroom", "x_ft": 14, "y_ft": 51, "w_ft": 13, "l_ft": 14},
    ]},
    {"level": 1, "label": "FIRST FLOOR", "rooms": [
        {"name": "UPPER FAMILY LOUNGE", "type": "lounge", "x_ft": 0, "y_ft": 0, "w_ft": 35, "l_ft": 16},
        {"name": "EXECUTIVE SUITE 3", "type": "bedroom", "x_ft": 0, "y_ft": 16, "w_ft": 14, "l_ft": 15},
    ]},
]}


def test_validator_rejects_the_old_freeform_output():
    geo = pge.analyse_layout(OLD_FREEFORM_LAYOUT, 35.0, 65.0, 7.5, 5.0, 4, 4)
    assert geo["validation"]["status"] == "FAIL"
    assert {"OVERLAP", "TILING_GAP", "STAIR_MISSING"} <= _codes(geo)
    assert {"SETBACK_FRONT", "SETBACK_REAR"} <= _all_codes(geo)


def test_landlocked_and_walk_through_rooms_are_errors():
    tree = {"split": "rows", "parts": [
        {"size_ft": 8, "split": "cols", "parts": [
            {"size_ft": 12, "room": {"id": "p", "name": "CAR PORCH", "type": "car_porch"}},
            {"size_ft": 18, "room": {"id": "lw", "name": "LAWN", "type": "lawn"}}]},
        {"size_ft": 12, "split": "cols", "parts": [
            {"size_ft": 6, "room": {"id": "e", "name": "ENT LOBBY", "type": "entrance", "door_from": "p"}},
            {"size_ft": 24, "room": {"id": "lo", "name": "TV LOUNGE", "type": "lounge", "door_from": "e"}}]},
        {"size_ft": 12, "split": "cols", "parts": [
            {"size_ft": 18, "room": {"id": "mid", "name": "BED ROOM", "type": "bedroom", "door_from": "lo"}},
            {"size_ft": 12, "room": {"id": "k", "name": "KITCHEN", "type": "kitchen", "door_from": "lo"}}]},
        {"size_ft": 13, "room": {"id": "b2", "name": "BED ROOM 2", "type": "bedroom", "door_from": "mid"}},
        {"size_ft": 5, "room": {"id": "r", "name": "OPEN", "type": "open"}},
    ]}
    geo = pge.analyse_layout({"floors": [{"level": 0, "layout": tree}]}, 30, 50, 8, 5, 2, 0)
    errors = geo["validation"]["errors"]
    landlocked = {i["room"] for i in errors if i["code"] == "LANDLOCKED"}
    assert "mid" in landlocked and "k" in landlocked
    assert any(i["code"] == "WALK_THROUGH_BEDROOM" and i["room"] == "b2" for i in errors)


def test_undersized_stair_is_an_error():
    tree = {"split": "rows", "parts": [
        {"size_ft": 10, "room": {"id": "p", "name": "CAR PORCH", "type": "car_porch"}},
        {"size_ft": 7.5, "split": "cols", "parts": [
            {"size_ft": 25, "room": {"id": "lo", "name": "TV LOUNGE", "type": "lounge", "door_from": "p"}},
            {"size_ft": 5, "room": {"id": "s", "name": "STAIR", "type": "stair", "door_from": "lo"}}]},
        {"size_ft": 32.5, "room": {"id": "r", "name": "OPEN", "type": "open"}},
    ]}
    geo = pge.analyse_layout({"floors": [{"level": 0, "layout": tree}]}, 30, 50, 0, 0, 0, 0)
    assert any(i["code"] == "STAIR_TOO_SMALL" and i["room"] == "s" for i in geo["validation"]["errors"])


def test_misaligned_stair_is_flagged():
    bad_script = SAMPLE_2_STOREY_SCRIPT.replace(
        "    17 | UPPER LOUNGE | lounge | door: STAIR | furniture: sofa_3, tv_console\n    5 | STAIR | stair | door: UPPER LOUNGE",
        "    5 | STAIR | stair | door: UPPER LOUNGE\n    17 | UPPER LOUNGE | lounge | door: STAIR | furniture: sofa_3, tv_console",
    )
    p = parse_script(bad_script, 30.0, 60.0, 7.5, 5.0)
    geo = pge.analyse_layout({"floors": p["floors"]}, 30.0, 60.0, 7.5, 5.0, 5, 5)
    assert "STAIR_MISALIGNED" in _codes(geo)


# ---------------------------------------------------------------------------
# Brief Parser & Marla / Kanal Sizing Terms
# ---------------------------------------------------------------------------

POOL_BRIEF = (
    "4 bed house with a swimming pool at the back, stairs in the driveway, porch for two cars, "
    "servant quarter, prayer room"
)

USER_BRIEF_25x45 = (
    "Design a modern contemporary single-storey 5 Marla (25x45 ft) house in Pakistan with 1 bedrooms, 2 bathrooms, "
    "a guest drawing room near the entrance with powder bath, a practical kitchen with dirty kitchen, a car porch for "
    "two vehicles, a dedicated servant quarter with bath, a quiet prayer area, natural ventilation, a rooftop terrace."
    "add a swimming pool, muja eik garden b chai hai chota sai chat pai ho"
)

PORTION_BRIEF = (
    "This is the 1st floot above ground portion, we want 3 rooms with bath and a drawwing space with bath, "
    "and a open corridoor that has a gate to enter with single kitchen. 2 rooms are bed spaces with sofa bed "
    "for the family. The drawing will have ground seetings arab style."
)

PORTION_SCRIPT = """PLOT 53 x 25
SETBACKS front 7.5 rear 5
LEVEL 1 "FIRST FLOOR PORTION"
ROWS
  7.5 | OPEN CORRIDOR | gallery
  12.5 COLS
    8 | KITCHEN | kitchen | door: OPEN CORRIDOR | furniture: counter, sink, hob, fridge
    4.5 | STAIR | stair | door: OPEN CORRIDOR | gate
    12 ROWS
      8 | DRAWING (MAJLIS) | drawing | door: OPEN CORRIDOR | furniture: floor_seating
      4.5 | DRAWING BATH | bath | door: DRAWING (MAJLIS)
    10.5 ROWS
      8 | BED ROOM 1 | bedroom | door: OPEN CORRIDOR | furniture: queen_bed, wardrobe
      4.5 | BATH 1 | bath | door: BED ROOM 1
    9 ROWS
      8 | BED SPACE 2 | bedroom | door: OPEN CORRIDOR | furniture: sofa_bed, wardrobe
      4.5 | BATH 2 | bath | door: BED SPACE 2
    9 ROWS
      8 | BED SPACE 3 | bedroom | door: OPEN CORRIDOR | furniture: sofa_bed, wardrobe
      4.5 | BATH 3 | bath | door: BED SPACE 3
  5 | REAR OPEN | open
"""


def test_brief_parser_extracts_requirements():
    from generation.brief_parser import parse_brief
    req = parse_brief(POOL_BRIEF + ", master bedroom on ground floor", 35, 65, 2, 4, 4)
    assert req["pool"]["location"] == "rear"
    assert req["stair_location"] == "porch"
    assert req["cars"] == 2
    assert {"servant", "prayer"} <= set(req["extra_rooms"])
    assert req["master_floor"] == 0
    assert any("SWIMMING POOL" in c for c in req["checklist"])


def test_brief_parser_reads_every_item_including_roman_urdu():
    from generation.brief_parser import parse_brief
    req = parse_brief(USER_BRIEF_25x45, 25, 45, 1, 1, 2)
    assert req["powder_bath"] and req["dirty_kitchen"] and req["roof_terrace"] and req["ventilation"]
    assert req["roof_garden"]
    assert req["cars"] == 2 and req["pool"] and req["servant_bath"]
    assert set(req["extra_rooms"]) == {"servant", "prayer"}
    assert not req.get("stair_location")
    ru = parse_brief("mujhe do gariyan ki jagah chahiye, namaz ka kamra, naukar ka kamra aur chhat pe bagh", 35, 65, 2, 4, 4)
    assert ru["cars"] == 2 and {"prayer", "servant"} <= set(ru["extra_rooms"]) and ru["roof_garden"]


def test_gemini_reading_cannot_invent_items():
    from generation.brief_parser import parse_brief, merge_llm_requirements
    req = parse_brief(USER_BRIEF_25x45, 25, 45, 1, 1, 2)
    req = merge_llm_requirements(
        req,
        {"stair_location": "porch", "guest_room": True, "gym": True, "other_requests": ["home cinema"]},
        1, 2, 1,
    )
    assert not req.get("stair_location") and "guest" not in req["extra_rooms"] and "gym" not in req["extra_rooms"]
    assert "home cinema" in req["other_requests"]


def test_site_is_read_from_the_prompt_only_and_keeps_marla_sizing():
    from generation.brief_parser import read_site
    s = read_site("1st floor portion on a 53x25 plot with a 12x14 drawing room")
    assert (s["width_ft"], s["length_ft"], s["plot_source"]) == (53.0, 25.0, "prompt")
    s = read_site("house on 35'-6\" x 70' plot, front setback 10 ft, no rear setback, G+1, spanish style")
    assert (s["width_ft"], s["length_ft"], s["storeys"], s["front_setback_ft"], s["rear_setback_ft"], s["style"]) == (
        35.5, 70.0, 2, 10.0, 0.0, "Spanish Villa"
    )
    s = read_site("5 marla house")
    assert (s["width_ft"], s["length_ft"], s["plot_source"]) == (25.0, 45.0, "marla_typical")
    s = read_site("10 marla house")
    assert (s["width_ft"], s["length_ft"], s["plot_source"]) == (35.0, 65.0, "marla_typical")
    s = read_site("1 kanal house")
    assert (s["width_ft"], s["length_ft"], s["plot_source"]) == (50.0, 90.0, "marla_typical")
    s = read_site("a house with 3 bedrooms")
    assert s["width_ft"] is None and s["missing"] and s["storeys"] is None


def test_room_sizes_in_the_prompt_are_checklist_items_and_verified():
    from generation.brief_parser import parse_brief, check_requirements
    req = parse_brief("30x60 plot, master bedroom 14x16, each bedroom 12 x 13, kitchen 8x10", 30, 60, 0, 0, 0)
    labels = [(r["label"], r["w_ft"], r["l_ft"], r["every"]) for r in req["room_sizes"]]
    assert ("Master bedroom", 14.0, 16.0, False) in labels and ("Bedroom", 12.0, 13.0, True) in labels
    assert any("MASTER BEDROOM 14' x 16'" in c for c in req["checklist"])
    floors = [{"level": 0, "doors": [], "furniture": [], "rooms": [
        {"id": "a", "name": "MASTER BED ROOM", "category": "bedroom", "w_ft": 16.0, "l_ft": 14.2},
        {"id": "b", "name": "KITCHEN", "category": "kitchen", "w_ft": 6.0, "l_ft": 9.0},
    ]}]
    rep = {r["item"]: r for r in check_requirements({"floors": floors}, req, 0, 0)}
    assert rep["Master bedroom 14' x 16'"]["status"] == "PASS"
    assert rep["Kitchen 8' x 10'"]["status"] == "FAIL"


# ---------------------------------------------------------------------------
# End-to-End Pipeline with Gemini Mocked
# ---------------------------------------------------------------------------

def _script(layout, W, L, f=7.5, r=5.0):
    return "Here is the design.\n```archiscript\n" + to_script(layout, W, L, f, r) + "\n```\nCHANGES: done"


def _patch_pipeline(monkeypatch, tmp_path, responses, llm_reading=None, candidates=1):
    from generation import gemini_cad_engine as gce
    monkeypatch.setattr(gce, "SCRIPT_CANDIDATES_FIRST", candidates)
    monkeypatch.setattr(gce, "SCRIPT_CANDIDATES_REPAIR", candidates)
    prompts = []

    def fake_text(prompt_text, api_key=None, temperature=0.3):
        prompts.append(prompt_text)
        r = responses[min(len(prompts) - 1, len(responses) - 1)]
        if isinstance(r, Exception):
            raise r
        return r, "mock-model"

    monkeypatch.setattr(gce, "call_gemini_text", fake_text)
    monkeypatch.setattr(gce, "extract_requirements_llm", lambda brief, api_key=None: dict(llm_reading or {}))
    monkeypatch.setattr(gce, "OUTPUT_DIR", str(tmp_path))
    return gce, prompts


def test_script_parser_reports_line_numbers_and_round_trips():
    bad = "PLOT 30 x 60\nLEVEL 0 \"GROUND\"\nROWS\n  20 | LAWN\n  40 | BED ROOM | bedroom | door: HALL\n"
    p = parse_script(bad, 30, 60)
    msgs = " ".join(e["message"] for e in p["errors"])
    assert "line 4" in msgs and "line 5" in msgs and "HALL" in msgs
    lay = reference_layout()
    p2 = parse_script(to_script(lay, 30.0, 60.0, 7.5, 5.0), 30.0, 60.0)
    assert p2["errors"] == []
    geo = pge.analyse_layout({"floors": p2["floors"]}, 30.0, 60.0, 7.5, 5.0, 5, 5)
    assert geo["validation"]["errors"] == []


def test_first_floor_portion_brief_is_fulfilled_end_to_end(tmp_path, monkeypatch):
    answer = "```archiscript\n" + PORTION_SCRIPT + "```"
    gce, prompts = _patch_pipeline(monkeypatch, tmp_path, [answer])
    res = gce.synthesize_design(PORTION_BRIEF, plot_width=53, plot_length=25, floors=1, bedrooms=4, bathrooms=4)
    assert "ONLY LEVEL 1" in prompts[0] and "no car porch" in prompts[0]
    assert res["requirements"]["parsed"]["bedrooms"] == 3 and res["requirements"]["parsed"]["bathrooms"] == 4
    cc = res["compliance_checklist"]
    assert cc["all_passed"], [i for i in cc["requested_items"] if i["status"] != "PASS"]
    assert res["quality_gate"]["status"] == "PASS" and len(prompts) == 1


def test_client_can_run_an_edited_script_and_converse(tmp_path, monkeypatch):
    gce, prompts = _patch_pipeline(monkeypatch, tmp_path, ["unused"])
    res = gce.run_design_script(PORTION_SCRIPT, PORTION_BRIEF, plot_width=53, plot_length=25, floors=1, bedrooms=4, bathrooms=4)
    assert res["design_source"] == "client_edited_script" and res["quality_gate"]["status"] == "PASS"
    assert prompts == []

    changed = PORTION_SCRIPT.replace("| furniture: floor_seating", "| furniture: floor_seating, prayer_mat")
    gce, prompts = _patch_pipeline(monkeypatch, tmp_path, ["```archiscript\n" + changed + "```\nCHANGES: added a prayer mat."])
    res2 = gce.converse_design_script(
        PORTION_SCRIPT, "please add a prayer corner in the drawing", PORTION_BRIEF,
        history=[], plot_width=53, plot_length=25, floors=1, bedrooms=4, bathrooms=4,
        requirements=res["requirements"]["parsed"],
    )
    assert "please add a prayer corner" in prompts[0] and "CURRENT SCRIPT" in prompts[0]
    assert res2["assistant_message"].startswith("added a prayer mat") and res2["change_applied"]
    assert res2["design_source"] == "ai_script_conversation"


def test_prompt_only_generation_reads_everything_from_the_prompt(tmp_path, monkeypatch):
    gce, prompts = _patch_pipeline(monkeypatch, tmp_path, ["```archiscript\n" + PORTION_SCRIPT + "```"])
    brief = PORTION_BRIEF.replace("ground portion,", "ground portion on a 53 x 25 ft plot,")
    res = gce.synthesize_from_prompt(brief)
    assert (res["plot"]["width_ft"], res["plot"]["length_ft"]) == (53.0, 25.0)
    assert res["input_mode"] == "prompt_only" and res["reading"]["plot"]["source"] == "prompt"
    assert res["compliance_checklist"]["all_passed"], res["compliance_checklist"]["requested_items"]
    with pytest.raises(ValueError):
        gce.synthesize_from_prompt("a house with 3 bedrooms")


def test_setbacks_default_to_zero_unless_stated_in_prompt(tmp_path, monkeypatch):
    gce, _ = _patch_pipeline(monkeypatch, tmp_path, ["unused"])
    r = gce.read_brief("5 marla plot, 5 rooms")
    assert r["ok"] and r["setbacks"]["front_ft"] == 0.0 and r["setbacks"]["rear_ft"] == 0.0
    assert r["setbacks"]["front_source"] == "architect_decides"
    r2 = gce.read_brief("30 x 60 ft plot, front setback 10 ft, 3 bedrooms")
    assert r2["ok"] and r2["setbacks"]["front_ft"] == 10.0 and r2["setbacks"]["front_source"] == "prompt"


def test_syntax_example_shown_to_the_ai_passes_every_engine_check():
    ex = SCRIPT_SPEC.split("design from the client's brief):\n", 1)[1]
    p = parse_script(ex, 30, 60, 7.5, 5)
    assert p["errors"] == []
    geo = pge.analyse_layout({"floors": p["floors"]}, 30, 60, 7.5, 5, 5, 5)
    assert geo["validation"]["errors"] == [], geo["validation"]["errors"][:3]
    assert len(p["floors"]) == 2


# ---------------------------------------------------------------------------
# Text-Based AI Civil Architect Interview Bot
# ---------------------------------------------------------------------------

def test_text_based_civil_architect_interview_bot():
    from generation.brief_interview import conduct_architect_interview

    # 1. Fallback when no LLM function is supplied asks civil architect questions in plain text
    r1 = conduct_architect_interview("I want to build a house in Lahore for my family.")
    assert not r1["ready"]
    assert r1["topic"] == "plot_size_and_place"
    assert len(r1["history"]) == 1 and r1["history"][0]["role"] == "architect"

    # 2. With an LLM callable, the AI Civil Architect updates the compiled brief and asks the next question
    def mock_llm(prompt_text):
        assert "5 Marla in Lahore" in prompt_text
        return {
            "architect_message": "For your 5 Marla (25x45 ft) plot in Lahore with 5 bedrooms, would you like all 5 rooms on a single ground floor or split across two storeys?",
            "updated_brief": "5 Marla (25 x 45 ft) plot in Lahore with 5 bedrooms.",
            "topic": "storeys_and_room_split",
            "interview_complete": False,
        }

    r2 = conduct_architect_interview(
        brief="I want to build a house in Lahore.",
        history=r1["history"],
        user_message="It is 5 Marla in Lahore and I want 5 bedrooms.",
        llm_call_fn=mock_llm,
    )
    assert r2["ready"] is True  # 5 Marla plot size is now known
    assert "5 Marla" in r2["compiled_brief"]
    assert r2["history"][-1]["role"] == "architect"
    assert "single ground floor or split" in r2["architect_message"]


# ---------------------------------------------------------------------------
# Unique-but-right: room budget per level, copied floors, layout concepts
# ---------------------------------------------------------------------------

def _two_storey_geo(script=None):
    p = parse_script(script or SAMPLE_2_STOREY_SCRIPT, 30.0, 60.0, 7.5, 5.0)
    assert p["errors"] == [], p["errors"]
    return pge.analyse_layout({"floors": p["floors"]}, 30.0, 60.0, 7.5, 5.0, 5, 5)


def test_level_budget_shares_the_house_total_over_the_levels():
    from generation.gemini_cad_engine import _level_budget
    none = {"beds": 0, "attached": 0, "baths": 0}
    req = {"bedrooms": 9, "attached_baths": 9, "bathrooms": 9}
    assert _level_budget(req, 0, 3, none) == {"beds": 3, "attached": 3, "baths": 3}
    # the ground floor delivered only 2: the upper levels pick up what is missing (2 + 3 + 4 = 9)
    done = {"beds": 2, "attached": 2, "baths": 2}
    assert _level_budget(req, 1, 3, done)["beds"] == 3
    assert _level_budget(req, 2, 3, {"beds": 5, "attached": 5, "baths": 5}) == {"beds": 4, "attached": 4, "baths": 4}
    # an uneven total leaves the remainder to the upper level (the ground floor also holds porch / drawing / kitchen)
    assert _level_budget({"bedrooms": 5, "bathrooms": 0}, 0, 2, none)["beds"] == 2
    assert _level_budget({"bedrooms": 5, "bathrooms": 0}, 1, 2, {"beds": 2, "attached": 0, "baths": 0})["beds"] == 3
    # numbers the client gave per floor always win
    assert _level_budget({"bedrooms": 4, "beds_per_level": {"0": 1, "1": 3}}, 0, 2, none)["beds"] == 1


def test_level_program_counts_bedrooms_and_attached_baths_per_level():
    from generation.gemini_cad_engine import _level_program, _budget_problems
    geo = _two_storey_geo()
    assert _level_program(geo, 0) == {"beds": 2, "attached": 2, "baths": 2}
    assert _level_program(geo, 1) == {"beds": 3, "attached": 3, "baths": 3}
    short = _budget_problems(1, _level_program(geo, 1), {"beds": 4, "attached": 4, "baths": 4})
    assert len(short) == 3 and "add 1 more" in short[0]
    assert _budget_problems(1, _level_program(geo, 1), {"beds": 3, "attached": 3, "baths": 3}) == []


def test_copied_floor_is_measured():
    from generation.gemini_cad_engine import _floor_similarity
    partly = _floor_similarity(_two_storey_geo(), 1)       # the sample's first floor re-plans its front band only
    assert 0.3 < partly < 0.9
    head = SAMPLE_2_STOREY_SCRIPT.split('LEVEL 1 "FIRST FLOOR"')[0]
    lvl0 = head.split('LEVEL 0 "GROUND FLOOR"')[1]
    # level 1 built as a copy of level 0: the same rooms in the same rectangles
    p = parse_script(head + 'LEVEL 1 "FIRST FLOOR"' + lvl0, 30.0, 60.0, 7.5, 5.0)
    geo = pge.analyse_layout({"floors": p["floors"]}, 30.0, 60.0, 7.5, 5.0, 4, 4)
    assert _floor_similarity(geo, 1) > 0.95 > partly


def test_concepts_differ_and_used_ones_are_not_repeated(tmp_path, monkeypatch):
    import generation.gemini_cad_engine as eng
    monkeypatch.setattr(eng, "CONCEPT_HISTORY_FILE", str(tmp_path / "concepts.json"))
    monkeypatch.setattr(eng, "_call_interview_llm_json", lambda *a, **k: None)     # no network: built-in concepts
    ctx = {"brief": "10 marla house, 4 bedrooms", "W": 35.0, "L": 65.0, "floors": 2, "req": {"checklist": []}}
    first = eng.propose_concepts(ctx, None, 3)
    assert len({c["name"] for c in first}) == 3
    assert "LAYOUT CONCEPT" in eng._concept_text(first[0]) and first[0]["stair"] in eng._concept_text(first[0])
    for c in first:
        eng._remember_concept(ctx, c)
    second = eng.propose_concepts(ctx, None, 3)
    assert not {c["name"] for c in first} & {c["name"] for c in second}
    # another brief has its own history
    other = dict(ctx, brief="5 marla house, 3 bedrooms")
    assert eng._concept_history(other) == []


def test_utility_and_storage_request_is_met_by_a_store_or_laundry_room():
    from generation.brief_parser import check_requirements
    geo = _two_storey_geo()     # has a LAUNDRY (wash_area) on the first floor
    req = {"custom_items": [{"item": "utility and storage functions", "quote": "utility and storage", "keyword": "UTILITY",
                             "count": 1, "attached_bath": False, "furniture": ""}]}
    rep = {r["item"]: r for r in check_requirements(geo, req, 0, 0)}
    assert rep["utility and storage functions"]["met"]
    req["custom_items"][0]["keyword"] = "CINEMA"
    assert not check_requirements(geo, req, 0, 0)[0]["met"]


def test_same_name_twice_is_one_space_in_two_parts():
    # an L-shaped lounge written in two bands: doors to "TV LOUNGE" land on the part that is touched, the parts are
    # joined by an arch, and the inner part is lit through the part that has the window
    script = """PLOT 30 x 50
SETBACKS front 0 rear 0
LEVEL 0 "GROUND FLOOR"
ROWS
  10 | FRONT LAWN | lawn
  14 COLS
    18 | TV LOUNGE | lounge | door: FRONT LAWN | furniture: sofa_3
    12 | KITCHEN | kitchen | door: TV LOUNGE
  12 COLS
    10 | TV LOUNGE | lounge
    14 | BED ROOM 1 | bedroom | door: TV LOUNGE | furniture: queen_bed
    6 | BATH 1 | bath | door: BED ROOM 1
  14 COLS
    10 | BED ROOM 2 | bedroom | door: TV LOUNGE | furniture: queen_bed
    20 | REAR LAWN | lawn
"""
    p = parse_script(script, 30.0, 50.0, 0.0, 0.0)
    assert p["errors"] == [], p["errors"]
    geo = pge.analyse_layout({"floors": p["floors"]}, 30.0, 50.0, 0.0, 0.0, 2, 1)
    gf = geo["floors"][0]
    pairs = {(d["room_id"], d["from_id"], d["kind"]) for d in gf["doors"]}
    assert ("gf_bed_room_2", "gf_tv_lounge_2", "door") in pairs          # lands on the second part
    assert any(k == "arch" and {a, b} == {"gf_tv_lounge", "gf_tv_lounge_2"} for a, b, k in pairs)
    codes = {(e["code"], e["room"]) for e in geo["validation"]["errors"]}
    assert ("LANDLOCKED", "gf_tv_lounge_2") not in codes
    assert not any(c in ("DOOR_NO_SHARED_WALL", "UNREACHABLE") for c, _ in codes), geo["validation"]["errors"]
