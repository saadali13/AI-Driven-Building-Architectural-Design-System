"""
Brief Parser — turns the client's free-text brief into an explicit requirements checklist
=======================================================================================

Every requirement found here is
  * built into the starting design by ``typology_generator`` where geometrically possible
    (overflow rooms - servant quarter, prayer room, gym, roof garden, plunge pool - go to a
    ROOF level beside the stair mumty, the usual Pakistani practice),
  * listed as a MUST-HAVE checklist at the top of the Gemini prompt, and
  * verified on the final design by ``check_requirements`` (a design that drops a requested
    feature is rejected in favour of one that keeps it, and anything that cannot be met is
    reported with the reason, never silently ignored).

Briefs are often written in a mix of English and Roman Urdu ("mujhe ek garden bhi chahiye,
chhota sa, chhat pe ho"), so common Roman-Urdu words are normalised to English first.
``merge_llm_requirements`` folds in Gemini's own reading of the brief (optional) so phrasing
the regexes do not know is still understood.
"""

import re
from typing import Any, Dict, List, Optional, Tuple

_NUM = {"one": 1, "single": 1, "two": 2, "double": 2, "three": 3, "triple": 3, "four": 4}
_COUNT_WORDS = {"one": 1, "two": 2, "three": 3, "four": 4, "five": 5, "six": 6, "seven": 7, "eight": 8}


def _to_int(tok: str) -> Optional[int]:
    tok = (tok or "").strip().lower()
    if tok.isdigit():
        return int(tok)
    return _COUNT_WORDS.get(tok)

# Roman Urdu / Urdu-English words -> English (applied on word boundaries, lower case)
_ROMAN_URDU = [
    (r"(chhat|chhatt|chath|chhath|chatt|chaat|chat)", "roof"),
    (r"(baghicha|baghichay|baghiche|bagicha|bageecha|bagheecha|baagh|bagh|ghaas|sabza)", "garden"),
    (r"(gaariyan|gariyan|gaarian|garian|gadiyan|gaadiyan|gaariyon|gaari|gari|gaadi|gadi)", "car"),
    (r"(chowkidar|chokidar|guard ?room)", "guard room"),
    (r"(naukar|nokar|naukron|mulazim|mulazmeen|khansama|maasi|masi)", "servant"),
    (r"(namaaz|namaz|musallah|musalla|ibadat)", "prayer"),
    (r"(seerhiyan|sirhiyan|seerhi|sirhi|seedhi|sidhi|zeena|zina)", "stairs"),
    (r"(bawarchi ?khana|rasoi)", "kitchen"),
    (r"(ghusal ?khana|gusal ?khana|ghusal)", "bathroom"),
    (r"(kamray|kamre|kamrey|kamra)", "room"),
    (r"(mehmaan|mehman|mehmanon|mehmano)", "guest"),
    (r"(baithak)", "drawing room"),
    (r"(talaab|talab)", "pool"),
]
_TYPOS = [   # common misspellings in client briefs -> the word the rules look for
    (r"dra+w+i+n+g+", "drawing"), (r"cor+i+d+o+r+", "corridor"), (r"cor+i+d+o+r+s", "corridors"),
    (r"se+a?t+i+n+g+s?", "seating"), (r"floo[rt]+|flor", "floor"), (r"kitch[ae]n|kichen|kitchn", "kitchen"),
    (r"bath\s*rooms?", "bathroom"), (r"wash\s*rooms?", "washroom"), (r"bed\s*rooms", "bedrooms"),
    (r"bed\s*room", "bedroom"), (r"stair\s*case", "staircase"), (r"verand[ah]+", "verandah"),
]
_RU_NUM = [(r"\b(do)\s+(car|cars)\b", r"2 \2"), (r"\b(teen)\s+(car|cars)\b", r"3 \2"),
           (r"\b(ek|eik|aik|aek)\s+(car|cars)\b", r"1 \2")]

_EXTRA_PATTERNS = (
    ("servant", (r"servant", r"\bmaid", r"driver room", r"staff room", r"helper room")),
    ("prayer", (r"prayer", r"masjid", r"\bmosque\b", r"worship")),
    ("gym", (r"\bgym\b", r"fitness", r"workout")),
    ("study", (r"\bstudy\b", r"office", r"library", r"work from home")),
    ("guest", (r"guest room", r"guest bed")),
    ("dining", (r"dining",)),
    ("laundry", (r"laundry", r"wash area")),
)


def _has(text: str, *patterns: str) -> bool:
    return any(re.search(p, text) for p in patterns)


def normalise_brief(prompt: str) -> str:
    t = " " + (prompt or "").lower().replace("-", " ").replace("_", " ") + " "
    for pat, rep in _TYPOS:
        t = re.sub(r"\b" + pat + r"\b", rep, t)
    for pat, rep in _ROMAN_URDU:
        t = re.sub(r"\b" + pat + r"\b", rep, t)
    for pat, rep in _RU_NUM:
        t = re.sub(pat, rep, t)
    return re.sub(r"[ \t]+", " ", t)


def parse_brief(prompt: str, plot_w: float = 0, plot_l: float = 0, floors: int = 2,
                bedrooms: int = 0, bathrooms: int = 0) -> Dict[str, Any]:
    t = normalise_brief(prompt)
    req: Dict[str, Any] = {"raw_brief": prompt or "", "notes": [], "other_requests": []}
    roof_words = r"(roof|rooftop|roof top|terrace|mumty)"

    # Swimming pool and where it goes
    if _has(t, r"swimming", r"\bpool\b", r"plunge", r"jacuzzi"):
        loc = "rear"
        if _has(t, r"pool\s+(on|at|over)\s+(the\s+)?" + roof_words, roof_words + r"\s+(swimming\s+|plunge\s+)?pool",
                r"pool\s+roof\s+(pe|pai|par|per)\b"):
            loc = "roof"
        elif _has(t, r"pool[^.]{0,30}\b(front|lawn in front|front lawn)", r"front[^.]{0,20}pool"):
            loc = "front"
        elif _has(t, r"pool[^.]{0,30}\bside\b", r"side[^.]{0,20}pool"):
            loc = "side"
        req["pool"] = {"location": loc}

    # Staircase position (porch / drive way = separate access to the upper portion)
    stair_words = r"(stair|stairs|staircase|stair case)"
    if _has(t, stair_words + r"[^.]{0,40}\b(porch|drive ?way|garage|outside|external|outdoor|separate|independent)",
            r"\b(porch|drive ?way|garage)\b[^.]{0,30}" + stair_words,
            r"(separate|independent)\s+(entrance|entry|access)[^.]{0,30}(upper|first floor|portion)",
            r"upper portion[^.]{0,20}(separate|independent|rent)"):
        req["stair_location"] = "porch"
    elif _has(t, stair_words + r"[^.]{0,40}\b(entrance|entry|lobby|foyer)"):
        req["stair_location"] = "entrance"
    elif _has(t, stair_words + r"[^.]{0,30}\b(inside|internal|lounge)"):   # "in the middle" is a position, not access
        req["stair_location"] = "inside"
    # where along the plot the stair sits ("the staircase is at the back of the plot")
    m_pos = re.search(stair_words + r"[^.]{0,50}\b(front|middle|centre|center|back|rear|left|right)\b(?!\s+setback)", t)
    if m_pos:
        req["stair_position"] = {"centre": "middle", "center": "middle", "rear": "back"}.get(m_pos.group(2), m_pos.group(2))

    # upper floors: their own plan unless the client asks for the same layout on every floor
    if _has(t, r"(every|each|all)\s+floors?\s+(repeats?|has|have|with)\s+(the\s+)?same\s+(layout|plan)",
            r"same\s+(layout|plan)\s+on\s+(every|each|all|both)\s+floors?", r"identical\s+floors",
            r"(repeat|copy)\s+(the\s+)?ground\s+floor\s+(layout|plan)"):
        req["same_layout"] = True

    # bedrooms / rooms per floor ("Bedrooms per floor - ground floor 2, first floor 2" / "2 bedrooms on the ground floor")
    lvl_of = {"ground": 0, "first": 1, "second": 2, "third": 3}
    per: Dict[int, int] = {}
    m_per = re.search(r"(?:bed\s*)?rooms?\s+per\s+floor[^.]*", t)
    if m_per:
        for lv, n in re.findall(r"\b(ground|first|second|third)\s+floor\s*:?\s*(\d+)", m_per.group(0)):
            per[lvl_of[lv]] = int(n)
    for sentence in re.split(r"[.;\n]", t):
        if not re.search(r"\b(bed|room)", sentence):
            continue
        for n, lv in re.findall(r"\b(\d+|" + "|".join(_COUNT_WORDS) + r")\s+(?:(?:bed\s*rooms?|bedrooms?|rooms?)\s+)?(?:on|in)\s+"
                                r"(?:the\s+)?(ground|first|second|third)\s+floor", sentence):
            per.setdefault(lvl_of[lv], _to_int(n) or 0)
    if not per:
        # "each floor has its own lounge, kitchen, 3 bedrooms" / "3 bedrooms on each floor": the count is per floor
        num = r"(\d+|" + "|".join(_COUNT_WORDS) + r")"
        m_each = (re.search(r"\b(?:each|every|per|both)\s+(?:floors?|storeys?|stories|levels?|portions?)\b[^.;\n]{0,90}?\b"
                            + num + r"\s+(?:bed\s*rooms?|bedrooms?)", t) or
                  re.search(r"\b" + num + r"\s+(?:bed\s*rooms?|bedrooms?)\s+(?:on|in|per|for)\s+(?:each|every|both)?\s*"
                            r"(?:floors?|storeys?|stories|levels?|portions?)\b", t))
        m_nf = re.search(r"\b(\d+|" + "|".join(_COUNT_WORDS) + r")\s*[- ]?\s*(?:floors?|storeys?|stories|storied|levels)\b", t)
        n_floors = (_to_int(m_nf.group(1)) or 0) if m_nf else 0
        if not n_floors:
            n_floors = 2 if re.search(r"\b(double|two)[- ]?(storey|story|storied|floor)", t) else \
                3 if re.search(r"\b(triple|three)[- ]?(storey|story|storied|floor)", t) else 0
        n_each = (_to_int(m_each.group(1)) or 0) if m_each else 0
        if n_each and 2 <= n_floors <= 6:
            per = {i: n_each for i in range(n_floors)}
    if per:
        req["beds_per_level"] = {str(k): v for k, v in sorted(per.items())}

    # "no car porch" is an instruction too
    req["no_porch"] = _has(
        t,
        r"\bno\s+(car\s+)?(porch|parking|garage)",
        r"without\s+(a\s+)?(car\s+)?(porch|parking|garage)",
        r"exclud\w+\s+(a\s+|the\s+)?(car\s+)?(porch|parking|garage)",
    )

    # Cars
    m = re.search(r"\b(\d|one|single|two|double|three|triple)\s*(car|cars|vehicle|vehicles)\b", t)
    cars = 1
    if m:
        cars = int(m.group(1)) if m.group(1).isdigit() else _NUM.get(m.group(1), 1)
    elif _has(t, r"double car", r"two car", r"2 car"):
        cars = 2
    req["cars"] = max(1, min(3, cars))
    req["cars_stated"] = bool(m)

    # Extra rooms
    extras: List[str] = []
    for key, pats in _EXTRA_PATTERNS:
        if _has(t, *pats):
            extras.append(key)
    req["extra_rooms"] = extras
    if "servant" in extras:
        req["servant_bath"] = True        # a servant quarter always gets its own toilet

    # Wet areas and kitchens
    req["powder_bath"] = _has(t, r"powder", r"guest\s+(toilet|bath|bathroom|washroom|wc)")
    req["drawing_bath"] = _has(t, r"drawing[^.]{0,30}(attached|with)\s+(a\s+)?(attached\s+)?(bath|toilet|washroom|wc)")
    if req["drawing_bath"] and req["powder_bath"] and not _has(t, r"powder\s+(bath|room|toilet)[^.]{0,40}(entrance|lobby)"):
        req["powder_bath"] = False          # "drawing room with powder bath" = the drawing room's own bath
    req["dirty_kitchen"] = _has(t, r"dirty\s+(mess\s+)?kitchen", r"wet\s+kitchen", r"back\s+kitchen",
                                r"scullery", r"mess\s+kitchen", r"kitchen[^.]{0,20}\bdirty\b")

    # Roof: terrace, garden (Roman Urdu "chhat pe garden" -> "roof pe garden")
    req["roof_garden"] = _has(t, roof_words + r"[^.]{0,40}\b(garden|plants|planters|greenery|lawn)",
                              r"\b(garden|plants|planters|greenery)\b[^.]{0,40}\b(roof|rooftop|roof top)\b",
                              r"green\s+roof")
    req["roof_terrace"] = req["roof_garden"] or _has(
        t, r"roof\s*top", r"rooftop", r"roof\s+terrace", r"terrace\s+on\s+(the\s+)?roof", r"mumty",
        r"roof\s+access") or (int(floors or 1) == 1 and _has(t, r"\bterrace\b"))
    if req.get("pool", {}).get("location") == "roof":
        req["roof_terrace"] = True

    # Gardens / lawns at ground level
    garden_mentions = len(re.findall(r"\b(garden|lawn|greenery|landscap)", t))
    roof_garden_mentions = len(re.findall(r"\b(roof|rooftop)[^.]{0,40}\bgarden|\bgarden\b[^.]{0,40}\b(roof|rooftop)\b", t))
    req["garden"] = garden_mentions > roof_garden_mentions
    req["rear_lawn"] = _has(t, r"(rear|back)\s*(lawn|garden|yard)", r"(lawn|garden)\s*(at|in) (the )?(rear|back)")

    req["drawing_room"] = not _has(t, r"no drawing", r"without (a )?drawing")
    # only what the brief names is required (no drawing room / car porch is assumed when the brief is silent)
    req["drawing_stated"] = _has(t, r"drawing", r"majlis", r"formal\s+(guest|sitting)", r"guest\s+(sitting|lounge)")
    req["porch_stated"] = _has(t, r"porch", r"garage", r"parking", r"\bcars?\b", r"vehicle", r"drive ?way")

    # Which part of the building is being designed (an upper portion is designed on its own level)
    m_up = re.search(r"\b(1st|first|ist|2nd|second|3rd|third|upper)\s+(floo\w*|storey|story|level)\b[^.]{0,40}"
                     r"\b(portion|above|only|upar)", t)
    if m_up or _has(t, r"above\s+(the\s+)?ground\s+(floor\s+)?(portion|floor)", r"upper\s+portion\b[^.]{0,30}(design|only)",
                    r"\b(design|plan)\s+(the\s+|a\s+|only\s+)?(upper|first floor)\s+portion"):
        lvl = 1
        if m_up and m_up.group(1) in ("2nd", "second"):
            lvl = 2
        elif m_up and m_up.group(1) in ("3rd", "third"):
            lvl = 3
        req["portion"] = {"kind": "upper", "level": lvl}

    # Counts stated in the brief override the form ("3 rooms with bath" -> 3 bedrooms)
    nums = "|".join(["\\d+"] + list(_COUNT_WORDS))
    room_counts = [_to_int(m.group(1)) for m in re.finditer(
        r"\b(" + nums + r")\s+(bed\s*rooms?|bedrooms?|rooms?|bed\s*spaces?)\b(?!\s+(on|in)\s+(the\s+)?(ground|first))", t)]
    room_counts = [c for c in room_counts if c and 0 < c <= 12]
    if room_counts:
        req["bedrooms_stated"] = max(room_counts)
    if req.get("beds_per_level"):
        req["bedrooms_stated"] = max(int(req.get("bedrooms_stated") or 0), sum(req["beds_per_level"].values()))
    bath_counts = [_to_int(m.group(1)) for m in re.finditer(
        r"\b(" + nums + r")\s+(bath\s*rooms?|baths?|washrooms?|toilets?)\b", t)]
    bath_counts = [c for c in bath_counts if c and 0 < c <= 12]
    if bath_counts:
        req["bathrooms_stated"] = max(bath_counts)
    m_att = re.search(r"\b(" + nums + r")\s+(bed\s*)?rooms?\s+(each\s+)?with\s+(an?\s+)?(attached\s+)?(bath|washroom|toilet)", t)
    if m_att:
        req["attached_baths"] = _to_int(m_att.group(1))
    elif _has(t, r"(attached|en ?suite)\s+(bath|washroom|toilet)s?"):
        req["attached_baths"] = req.get("bedrooms_stated") or bedrooms
    m_sb = re.search(r"\b(" + nums + r")\s+(of\s+the\s+)?(bed\s*)?rooms?\s+(are|as|with|having)\b[^.]{0,30}sofa\s*(cum\s*)?bed", t)
    if m_sb:
        req["sofa_beds"] = _to_int(m_sb.group(1))
    elif _has(t, r"sofa\s*(cum\s*)?bed"):
        req["sofa_beds"] = 1
    req["floor_seating"] = _has(t, r"(floor|ground)\s+seat", r"majlis", r"arab(ic|ian)?\s+(style|seat)", r"farshi")
    req["open_corridor"] = _has(t, r"open\s+(corridor|gallery|verandah|veranda|passage)", r"\bgallery\b")
    req["entry_gate"] = _has(t, r"\bgate\b")
    if _has(t, r"(single|one|1)\s+kitchen"):
        req["single_kitchen"] = True
        req["dirty_kitchen"] = False
    if _has(t, r"master[^.]{0,30}(ground|downstairs|gf)\b"):
        req["master_floor"] = 0
    req["ventilation"] = _has(t, r"ventilat", r"cross\s+air", r"day ?light", r"natural light", r"\bots\b",
                              r"open to sky", r"courtyard", r"air ?well")
    req["walk_in_closet"] = _has(t, r"walk\s*in\s+(closet|wardrobe)", r"dressing room")
    req["kitchen_stated"] = _has(t, r"kitchen")
    req["room_sizes"] = read_room_sizes(prompt)
    req["pantry"] = _has(t, r"pantry", r"kitchen\s+store")

    # Requested but not drawn by the 2D generator (reported, never silently dropped)
    for word, note, label in (
            (r"basement", "Basement requested - the 2D generator does not draw basements yet", "Basement"),
            (r"\blift\b|elevator", "Lift requested - reserve a 5'x5' shaft beside the stair (not drawn yet)", "Lift"),
            (r"\bshop\b|commercial", "Commercial / shop space requested - not supported yet", "Shop / commercial space"),
            (r"guard room|security", "Guard room requested - not drawn yet (no enclosed rooms in the front setback)",
             "Security guard room"),
            (r"double\s+height", "Double-height foyer requested - shown as a normal-height space in 2D", "Double-height foyer"),
            (r"island", "Kitchen island requested - drawn as wall counters only", "Kitchen island"),
            (r"solar", "Solar inverter shaft requested - not drawn yet", "Solar inverter shaft")):
        if _has(t, word):
            req["notes"].append(note)
            req["other_requests"].append(label)

    req["checklist"] = build_checklist(req, bedrooms, bathrooms, floors)
    return req


# ---------------------------------------------------------------------------
# Room sizes the client writes ("master bedroom 16x18", "12' x 14' drawing room")
# ---------------------------------------------------------------------------

_ROOM_WORDS = [   # most specific first: (regex, label, NAME keywords that identify the room)
    (r"master\s*(bed\s*room|bedroom|bed)?", "Master bedroom", ("MASTER",)),
    (r"guest\s*(bed\s*room|bedroom|room)", "Guest bedroom", ("GUEST",)),
    (r"servant", "Servant quarter", ("SERVANT",)),
    (r"drawing|majlis|baithak", "Drawing room", ("DRAWING", "MAJLIS")),
    (r"lounge|living|family\s+room|tv\s+room", "Lounge", ("LOUNGE", "LIVING")),
    (r"dining", "Dining", ("DINING",)),
    (r"dirty\s+kitchen", "Dirty kitchen", ("DIRTY",)),
    (r"kitchen", "Kitchen", ("KITCHEN",)),
    (r"powder", "Powder bath", ("POWDER",)),
    (r"bath\s*rooms?|baths?|washrooms?|toilets?", "Bathroom", ("BATH", "TOILET", "WASH")),
    (r"bed\s*rooms?|bedrooms?|bed\s*spaces?|rooms?", "Bedroom", ("BED",)),
    (r"porch|garage", "Car porch", ("PORCH", "GARAGE")),
    (r"store|pantry", "Store", ("STORE", "PANTRY")),
    (r"study|office", "Study", ("STUDY", "OFFICE")),
    (r"prayer", "Prayer room", ("PRAYER",)),
    (r"\bgym\b", "Gym", ("GYM",)),
    (r"lobby|foyer|entrance", "Entrance lobby", ("LOBBY", "FOYER", "ENTRANCE", "ENT ")),
    (r"terrace", "Terrace", ("TERRACE",)),
    (r"lawn|garden", "Lawn / garden", ("LAWN", "GARDEN")),
    (r"pool", "Pool", ("POOL",)),
    (r"corridor|gallery|passage", "Corridor", ("CORRIDOR", "GALLERY", "PASSAGE")),
]
_ROOM_DIM = re.compile(r"(\d{1,2}(?:\.\d+)?)\s*(?:'|ft\.?|feet)?(?:\s*-?\s*(\d{1,2})\s*(?:\"|in))?\s*(?:x|×|\*|by)\s*"
                       r"(\d{1,2}(?:\.\d+)?)\s*(?:'|ft\.?|feet)?(?:\s*-?\s*(\d{1,2})\s*(?:\"|in))?", re.I)


def read_room_sizes(prompt: str) -> List[Dict[str, Any]]:
    """Sizes the brief gives for particular rooms. Each becomes a checklist item that is verified on the plan."""
    out: List[Dict[str, Any]] = []
    raw = (prompt or "").lower()
    for clause in re.split(r"[.;\n]|,(?!\d)|\band\b", raw):
        for m in _ROOM_DIM.finditer(clause):
            w, l = _feet(m.group(1), m.group(2)), _feet(m.group(3), m.group(4))
            if min(w, l) < 3 or w * l >= 450:
                continue                                 # too small to be a room, or the plot itself
            best = None
            for pat, label, keys in _ROOM_WORDS:
                for rm in re.finditer(pat, clause):
                    if rm.group(0).strip() in ("", "room", "rooms") and pat.startswith("bed"):
                        if not re.search(r"\b(bed|sleep)", clause):
                            continue                     # a bare "room" counts as a bedroom only next to bed words
                    gap = m.start() - rm.end() if rm.end() <= m.start() else rm.start() - m.end() + 0.5
                    if gap < 0 or gap > 40:
                        continue
                    if best is None or gap < best[0]:
                        best = (gap, label, keys)
                if best and best[1] == label:
                    break                                # the most specific word wins at equal distance
            if best:
                every = bool(re.search(r"\b(each|every|all)\b", clause))
                if not any(o["label"] == best[1] and abs(o["w_ft"] - w) < 0.01 and abs(o["l_ft"] - l) < 0.01 for o in out):
                    out.append({"label": best[1], "keywords": list(best[2]), "w_ft": w, "l_ft": l,
                                "every": every, "quote": clause.strip()[:80]})
    return out


def _size_text(v: float) -> str:
    f = int(v)
    i = int(round((v - f) * 12))
    return f"{f}'" + (f"-{i}\"" if i else "")


# ---------------------------------------------------------------------------
# The site, read from the prompt itself (plot size, storeys, setbacks, style)
# ---------------------------------------------------------------------------

MARLA_SQFT = 225.0          # DHA / LDA / CDA marla; 1 kanal = 20 marla
_MARLA_TYPICAL = {3: (20.0, 34.0), 5: (25.0, 45.0), 7: (30.0, 52.5), 8: (30.0, 60.0), 10: (35.0, 65.0),
                  20: (50.0, 90.0), 40: (75.0, 120.0)}
_AREA_WORDS = dict(_COUNT_WORDS, nine=9, ten=10, twelve=12, fifteen=15, twenty=20, half=0.5)
_LEN = r"(\d{1,3}(?:\.\d+)?)\s*(?:'|ft\.?|feet|foot)?(?:\s*-?\s*(\d{1,2}(?:\.\d+)?)\s*(?:\"|''|in\.?|inch(?:es)?))?"
_DIM_RE = re.compile(_LEN + r"\s*(?:x|×|\*|by)\s*" + _LEN, re.I)
_PLOT_CONTEXT = re.compile(r"plot|marla|kanal|site|land|sq|area|house|home|portion|villa|bungalow|frontage|\(", re.I)
_STYLES = [(r"spanish|mediterranean", "Spanish Villa"), (r"minimal", "Minimalist"),
           (r"classic|colonial|victorian", "Classical Estate"), (r"haveli|traditional|mughal", "Traditional Haveli"),
           (r"modern|contemporary", "Modern Contemporary")]


def _feet(whole: str, inches: Optional[str]) -> float:
    return round(float(whole) + (float(inches) / 12.0 if inches else 0.0), 2)


def _area_num(tok: str) -> Optional[float]:
    tok = tok.strip().lower()
    try:
        return float(tok)
    except ValueError:
        return _AREA_WORDS.get(tok)


def typical_plot_for_marla(marla: float) -> Tuple[float, float]:
    """The usual shape of a plot of this many marla (used only when the prompt gives the area but not the sides)."""
    if int(marla) == marla and int(marla) in _MARLA_TYPICAL:
        return _MARLA_TYPICAL[int(marla)]
    area = marla * MARLA_SQFT
    w = round((area / 1.8) ** 0.5 * 2) / 2.0
    return w, round(area / w * 2) / 2.0


def read_site(prompt: str) -> Dict[str, Any]:
    """Plot size, storeys, setbacks and style exactly as the client wrote them. Nothing is filled in here:
    whatever the prompt does not say is listed under 'missing' (or, for an area-only plot, under 'assumptions')."""
    raw = (prompt or "").lower()
    t = normalise_brief(prompt)
    site: Dict[str, Any] = {"width_ft": None, "length_ft": None, "plot_source": None, "plot_quote": "",
                            "marla": None, "storeys": None, "storeys_quote": "", "front_setback_ft": None,
                            "rear_setback_ft": None, "setback_quote": "", "style": None, "assumptions": [],
                            "missing": []}
    # marla / kanal
    m = re.search(r"\b(\d+(?:\.\d+)?|" + "|".join(_AREA_WORDS) + r")\s*marla", t)
    k = re.search(r"\b(\d+(?:\.\d+)?|" + "|".join(_AREA_WORDS) + r")\s*kanal", t)
    if m and _area_num(m.group(1)):
        site["marla"] = _area_num(m.group(1))
    elif k and _area_num(k.group(1)):
        site["marla"] = _area_num(k.group(1)) * 20.0
    # explicit sides: "53x25", "25' x 45'", "35'-6\" by 70 ft" (first number = street frontage)
    cands = []
    for mm in _DIM_RE.finditer(raw):
        w, l = _feet(mm.group(1), mm.group(2)), _feet(mm.group(3), mm.group(4))
        if min(w, l) < 15 or w * l < 450:
            continue                                   # a room size, not the plot
        ctx = raw[max(0, mm.start() - 40): mm.end() + 25]
        score = (2 if _PLOT_CONTEXT.search(ctx) else 0)
        if site["marla"]:
            score += 3 if abs(w * l - site["marla"] * MARLA_SQFT) / (site["marla"] * MARLA_SQFT) < 0.2 else 0
        cands.append((score, w * l, w, l, mm.group(0).strip()))
    if cands:
        _, _, w, l, q = max(cands)
        site.update(width_ft=w, length_ft=l, plot_source="prompt", plot_quote=q)
    else:
        wm = re.search(r"(\d{1,3}(?:\.\d+)?)\s*(?:'|ft|feet)?\s*(?:wide|width|frontage|front(?!\s*setback))\b", t) or \
            re.search(r"\b(?:width|frontage)\s*(?:of|is|=|:)?\s*(\d{1,3}(?:\.\d+)?)", t)
        lm = re.search(r"(\d{1,3}(?:\.\d+)?)\s*(?:'|ft|feet)?\s*(?:deep|depth|long|length)\b", t) or \
            re.search(r"\b(?:depth|length)\s*(?:of|is|=|:)?\s*(\d{1,3}(?:\.\d+)?)", t)
        if wm and lm and float(wm.group(1)) >= 15 and float(lm.group(1)) >= 15:
            site.update(width_ft=float(wm.group(1)), length_ft=float(lm.group(1)), plot_source="prompt",
                        plot_quote=f"{wm.group(0).strip()} ... {lm.group(0).strip()}")
    # storeys (an upper-floor portion is a single level and is handled by parse_brief)
    n = None
    sm = re.search(r"\b(1|2|3|4|one|two|three|four|single|double|triple)\s*(storey|story|stories|storeys|storied|"
                   r"floors?)\b(?!\s*portion)", t)
    if sm:
        n = _to_int(sm.group(1)) or _NUM.get(sm.group(1))
    elif re.search(r"ground\s*floor\s*only|only\s*(the\s*)?ground\s*floor|\bbungalow\b", t):
        n, sm = 1, re.search(r"ground\s*floor\s*only|only\s*(the\s*)?ground\s*floor|\bbungalow\b", t)
    else:
        sm = re.search(r"\bg\s*\+\s*(\d)\b", t) or re.search(r"ground\s*(\+|plus|and)\s*(1|one|first|2|two|second)", t)
        if sm:
            tok = sm.group(sm.lastindex)
            n = 1 + ({"1": 1, "one": 1, "first": 1, "2": 2, "two": 2, "second": 2}.get(tok) or int(tok))
    if n and 1 <= n <= 4:
        site["storeys"], site["storeys_quote"] = n, sm.group(0).strip()
    # setbacks the client states (their society's bylaws) win over the database
    for side, words in (("front", "front"), ("rear", "rear|back")):
        sb = re.search(r"\b(?:" + words + r")\s+setback\s*(?:of|is|=|:)?\s*(\d{1,2}(?:\.\d+)?)", t) or \
            re.search(r"(\d{1,2}(?:\.\d+)?)\s*(?:'|ft|feet)?\s*(?:" + words + r")\s+setback", t)
        if sb:
            site[side + "_setback_ft"] = float(sb.group(1))
            site["setback_quote"] = (site["setback_quote"] + " / " if site["setback_quote"] else "") + sb.group(0).strip()
        elif re.search(r"\bno\s+(?:" + words + r")\s+setback", t):
            site[side + "_setback_ft"] = 0.0
    for pat, label in _STYLES:
        if re.search(pat, t):
            site["style"] = label
            break
    return finish_site(site)


def finish_site(site: Dict[str, Any]) -> Dict[str, Any]:
    site["assumptions"], site["missing"] = [], []
    if not site.get("width_ft") and site.get("marla"):
        w, l = typical_plot_for_marla(float(site["marla"]))
        site.update(width_ft=w, length_ft=l, plot_source="marla_typical")
        site["assumptions"].append(f"The prompt gives {site['marla']:g} marla but not the sides - the usual "
                                   f"{w:g}' x {l:g}' shape is used. Write the exact size (e.g. \"{w:g} x {l:g} ft\") "
                                   f"if your plot is different.")
    if not site.get("width_ft"):
        site["missing"].append("Plot size - write it in the prompt, e.g. \"30 x 60 ft\", \"53 ft wide and 25 ft deep\" "
                               "or \"10 marla\".")
    return site


def merge_llm_site(site: Dict[str, Any], llm: Optional[Dict[str, Any]], prompt: str) -> Dict[str, Any]:
    """Gemini fills site facts the rules missed - only when the numbers / words are really in the prompt."""
    if not isinstance(llm, dict) or not llm:
        return site
    raw = (prompt or "").lower()
    t = normalise_brief(prompt)

    def in_text(v) -> bool:
        try:
            f = float(v)
        except (TypeError, ValueError):
            return False
        return bool(re.search(r"(?<![\d.])%s(?![\d])" % re.escape(f"{f:g}"), raw))
    try:
        if site.get("plot_source") != "prompt" and llm.get("plot_width_ft") and llm.get("plot_length_ft") and \
                in_text(llm["plot_width_ft"]) and in_text(llm["plot_length_ft"]) and \
                min(float(llm["plot_width_ft"]), float(llm["plot_length_ft"])) >= 15:
            site.update(width_ft=float(llm["plot_width_ft"]), length_ft=float(llm["plot_length_ft"]),
                        plot_source="prompt", plot_quote=str(llm.get("plot_quote", ""))[:80])
        if not site.get("marla") and llm.get("plot_marla") and in_text(llm["plot_marla"]) and \
                re.search(r"marla|kanal", t):
            site["marla"] = float(llm["plot_marla"])
        if not site.get("storeys") and llm.get("storeys") and _quote_ok(t, str(llm.get("storeys_quote", ""))) and \
                re.search(r"storey|story|floor|level|double|single|ground", t):
            n = int(llm["storeys"])
            if 1 <= n <= 4:
                site["storeys"], site["storeys_quote"] = n, str(llm.get("storeys_quote", ""))[:80]
        for side in ("front", "rear"):
            v = llm.get(side + "_setback_ft")
            if site.get(side + "_setback_ft") is None and v is not None and in_text(v) and "setback" in t:
                site[side + "_setback_ft"] = float(v)
    except (TypeError, ValueError):
        pass
    if not site.get("style") and llm.get("style"):
        for pat, label in _STYLES:
            if re.search(pat, str(llm["style"]).lower()) and re.search(pat, t):
                site["style"] = label
                break
    return finish_site(site)


# ---------------------------------------------------------------------------
# Gemini's reading of the brief (optional, merged on top of the rules above)
# ---------------------------------------------------------------------------

LLM_EXTRACTION_PROMPT = """You read house briefs written by Pakistani clients (English, Urdu or Roman Urdu mixed).
List ONLY what the client explicitly asks for. Do not invent anything. Return JSON exactly like:
{{"understood_as": "one plain-English sentence restating the brief",
  "pool": null or {{"location": "rear" | "front" | "side" | "roof"}},
  "stair_location": null | "porch" | "inside",
  "cars": null or an integer,
  "servant_quarter": false, "prayer": false, "gym": false, "study": false, "guest_room": false,
  "dining": false, "laundry": false, "powder_bath": false, "dirty_kitchen": false,
  "roof_terrace": false, "roof_garden": false, "garden": false, "rear_lawn": false,
  "no_drawing_room": false, "master_on_ground": false,
  "bedrooms": null or the number of sleeping rooms / bed spaces the brief states,
  "bathrooms": null or the number of baths the brief states or clearly implies,
  "portion": "whole_house" | "upper_floor_portion" | "ground_floor_only",
  "portion_level": null or 1 | 2 | 3,
  "plot_width_ft": null or the plot's street frontage in feet exactly as written,
  "plot_length_ft": null or the plot's depth (front to back) in feet exactly as written,
  "plot_marla": null or the plot area in marla if the brief states it (1 kanal = 20 marla),
  "plot_quote": "the EXACT words that give the plot size, or empty",
  "storeys": null or the number of storeys of the whole house if the brief states it,
  "storeys_quote": "the EXACT words that give the storeys, or empty",
  "front_setback_ft": null or a front setback the brief states, "rear_setback_ft": null or a rear setback it states,
  "style": null or the architectural style words the client used,
  "custom_items": [{{"item": "short requirement in plain English",
                    "quote": "the EXACT words of the brief it comes from",
                    "room_keyword": "one capital word the room NAME will contain, e.g. DRAWING, BED, KITCHEN, CORRIDOR",
                    "count": 1, "attached_bath": false, "furniture": "" }}],
  "other_requests": ["short names of any OTHER explicitly requested space or feature"]}}
Put every specific space the brief describes (e.g. "drawing with bath", "2 rooms are bed spaces with sofa bed",
"open corridor with a gate", "ground seating arab style") in custom_items.
"Chhat / chat" means roof, "bagh / garden" garden, "gari" car, "namaz" prayer, "naukar" servant.

BRIEF:
{brief}
"""

_LLM_EXTRA_KEYS = {"servant_quarter": "servant", "prayer": "prayer", "gym": "gym", "study": "study",
                   "guest_room": "guest", "dining": "dining", "laundry": "laundry"}

# Gemini may add an item only if the brief contains words that back it up (the fast model
# sometimes "completes" a brief with things the client never asked for)
_EVIDENCE = {
    "pool": [r"pool|swim|plunge|jacuzzi"],
    "stair_porch": [r"stair", r"porch|drive ?way|garage|outside|external|separate|independent"],
    "cars": [r"\bcar|vehicle|parking"],
    "servant_quarter": [r"servant|maid|driver|staff|helper"],
    "prayer": [r"prayer|worship|mosque|masjid"],
    "gym": [r"\bgym|fitness|workout|exercise"],
    "study": [r"study|office|library|work from home"],
    "guest_room": [r"guest (room|bed|suite)|guest\b(?! drawing)(?! powder)(?! toilet)(?! bath)"],
    "dining": [r"dining"],
    "laundry": [r"laundry|wash|dhobi|kapr"],
    "powder_bath": [r"powder|guest (toilet|bath|washroom|wc)|toilet"],
    "dirty_kitchen": [r"dirty|wet kitchen|back kitchen|scullery|mess"],
    "roof_terrace": [r"roof|terrace|mumty"],
    "roof_garden": [r"garden|plant|green|lawn", r"roof|terrace"],
    "garden": [r"garden|lawn|green|plant|landscap"],
    "rear_lawn": [r"rear|back", r"lawn|garden|yard"],
    "no_drawing_room": [r"(no|without|nahi|nahin)[^.]{0,20}drawing|drawing[^.]{0,20}(nahi|nahin|not needed)"],
    "master_on_ground": [r"master", r"ground|downstairs|neeche|niche"],
}


def _evident(t: str, key: str) -> bool:
    return all(re.search(p, t) for p in _EVIDENCE.get(key, [r"."]))


def merge_llm_requirements(req: Dict[str, Any], llm: Optional[Dict[str, Any]], bedrooms: int,
                           bathrooms: int, floors: int) -> Dict[str, Any]:
    """Union of the rule-based reading and Gemini's reading. Gemini can add an item only when the
    brief has words that support it, so nothing the client did not ask for is invented."""
    if not isinstance(llm, dict) or not llm:
        return req
    t = normalise_brief(req.get("raw_brief", ""))
    req["llm_reading"] = {k: v for k, v in llm.items() if not str(k).startswith("_")}
    if llm.get("understood_as"):
        req["llm_summary"] = str(llm["understood_as"])[:400]
    pool = llm.get("pool")
    if isinstance(pool, dict) and not req.get("pool") and _evident(t, "pool"):
        loc = str(pool.get("location", "rear")).lower()
        req["pool"] = {"location": loc if loc in ("rear", "front", "side", "roof") else "rear"}
    if llm.get("stair_location") == "porch" and not req.get("stair_location") and _evident(t, "stair_porch"):
        req["stair_location"] = "porch"
    try:
        if llm.get("cars") and int(llm["cars"]) > int(req.get("cars", 1)) and _evident(t, "cars"):
            req["cars"] = max(1, min(3, int(llm["cars"])))
    except (TypeError, ValueError):
        pass
    for k, e in _LLM_EXTRA_KEYS.items():
        if llm.get(k) is True and e not in req["extra_rooms"] and _evident(t, k):
            req["extra_rooms"].append(e)
    if "servant" in req["extra_rooms"]:
        req["servant_bath"] = True
    for k in ("powder_bath", "dirty_kitchen", "roof_terrace", "roof_garden", "rear_lawn"):
        if llm.get(k) is True and _evident(t, k):
            req[k] = True
    if llm.get("garden") is True and _evident(t, "garden") and not req.get("roof_garden"):
        req["garden"] = True
    if req.get("roof_garden") or (req.get("pool") or {}).get("location") == "roof":
        req["roof_terrace"] = True
    if llm.get("no_drawing_room") is True and _evident(t, "no_drawing_room"):
        req["drawing_room"] = False
    if llm.get("master_on_ground") is True and _evident(t, "master_on_ground"):
        req["master_floor"] = 0
    def _num_evident(n) -> bool:
        words = {v: k for k, v in _COUNT_WORDS.items()}
        return bool(re.search(r"\b%d\b" % n, t)) or (n in words and bool(re.search(r"\b" + words[n] + r"\b", t)))
    try:
        if llm.get("bedrooms") and not req.get("bedrooms_stated") and _num_evident(int(llm["bedrooms"])):
            req["bedrooms_stated"] = int(llm["bedrooms"])
        if llm.get("bathrooms") and not req.get("bathrooms_stated") and int(llm["bathrooms"]) > 0:
            req["bathrooms_llm"] = int(llm["bathrooms"])
    except (TypeError, ValueError):
        pass
    if llm.get("portion") == "upper_floor_portion" and not req.get("portion") and \
            re.search(r"portion|above|upper|upar", t) and re.search(r"floor|storey|level|ground", t):
        try:
            lvl = int(llm.get("portion_level") or 1)
        except (TypeError, ValueError):
            lvl = 1
        req["portion"] = {"kind": "upper", "level": max(1, min(3, lvl))}
    for ci in llm.get("custom_items") or []:
        if isinstance(ci, dict):
            _absorb_custom_item(req, ci, t)

    known = {x.lower() for x in req.get("other_requests", [])}
    skip = ("bed", "bath", "kitchen", "lounge", "drawing", "porch", "car", "garden", "lawn", "pool", "terrace",
            "roof", "servant", "prayer", "stair", "ventilation", "dining", "study", "gym", "laundry", "toilet",
            "washroom", "storey", "floor", "modern", "style", "closet", "pantry", "store", "dressing",
            "corridor", "gallery", "gate", "seating", "sofa", "majlis", "portion", "family", "room", "space")
    for o in llm.get("other_requests") or []:
        o = str(o).strip()[:60]
        if o and o.lower() not in known and not any(s in o.lower() for s in skip):
            req["other_requests"].append(o)
            req["notes"].append(f"{o} requested - not drawn by the 2D generator yet (passed to the AI designer)")
            known.add(o.lower())
    req["checklist"] = build_checklist(req, bedrooms, bathrooms, floors)
    return req


# ---------------------------------------------------------------------------
# Checklist
# ---------------------------------------------------------------------------

_EXTRA_LABEL = {"servant": "SERVANT QUARTER", "prayer": "PRAYER ROOM", "gym": "GYM", "study": "STUDY",
                "guest": "GUEST ROOM", "dining": "DINING", "laundry": "LAUNDRY / WASH AREA"}


def _quote_ok(t: str, quote: str) -> bool:
    words = [w for w in re.findall(r"[a-z0-9]+", normalise_brief(quote or "")) if len(w) >= 3]
    if not words:
        return False
    hit = sum(1 for w in words if re.search(r"\b" + re.escape(w), t))
    return hit / float(len(words)) >= 0.75


_COVERED_KEYWORDS = {"DRAWING", "KITCHEN", "PORCH", "CAR", "TERRACE", "ROOF", "BED", "BEDROOM", "BATH", "BATHROOM",
                     "MASTER", "POWDER", "DIRTY", "LAWN", "GARDEN", "POOL", "SERVANT", "PRAYER", "STAIR", "STAIRS",
                     "LOUNGE", "DINING", "STUDY", "GYM", "LAUNDRY", "STORE", "PANTRY"}


def _absorb_custom_item(req: Dict[str, Any], ci: Dict[str, Any], t: str) -> None:
    """A space Gemini read from the brief. Kept only if its quote really is in the brief; mapped onto a
    known check where possible (so typos the rules missed are still understood), else kept as a custom check."""
    quote = str(ci.get("quote", ""))
    if not _quote_ok(t, quote):
        return
    kw = re.sub(r"[^A-Z]", "", str(ci.get("room_keyword", "")).upper())[:16]
    furn = str(ci.get("furniture", "") or "").lower()
    try:
        n = max(1, int(ci.get("count") or 1))
    except (TypeError, ValueError):
        n = 1
    att = bool(ci.get("attached_bath"))
    q = normalise_brief(quote)
    if "sofa" in furn or "sofa" in q and "bed" in q:
        req["sofa_beds"] = max(int(req.get("sofa_beds") or 0), n)
    elif any(k in furn for k in ("floor", "majlis", "cushion", "arab")) or re.search(r"(floor|ground) seat|majlis|arab", q):
        req["floor_seating"] = True
    elif att and kw in ("DRAWING", "MAJLIS", "BAITHAK", "GUEST"):
        req["drawing_bath"] = True
    elif att and kw in ("BED", "BEDROOM", "ROOM", "ROOMS"):
        req["attached_baths"] = max(int(req.get("attached_baths") or 0), n)
    elif kw in ("CORRIDOR", "GALLERY", "VERANDAH", "PASSAGE"):
        req["open_corridor"] = True
        if "gate" in q:
            req["entry_gate"] = True
    elif kw == "GATE":
        req["entry_gate"] = True
    elif kw == "KITCHEN" and re.search(r"single|one|1 kitchen", q):
        req["single_kitchen"] = True
        req["dirty_kitchen"] = False
    elif kw in ("BED", "BEDROOM", "ROOM", "ROOMS") and not furn:
        req.setdefault("bedrooms_stated", n)
    elif kw in _COVERED_KEYWORDS and not furn and not att:
        return                       # already a checklist item from the rules (drawing, kitchen, porch, terrace ...)
    elif kw:
        items = req.setdefault("custom_items", [])
        if not any(c["keyword"] == kw and c.get("furniture") == furn for c in items):
            items.append({"item": str(ci.get("item") or quote)[:90], "quote": quote[:120], "keyword": kw,
                          "count": n, "attached_bath": att, "furniture": furn})


def effective_counts(req: Dict[str, Any], bedrooms: int, bathrooms: int) -> Tuple[int, int]:
    """Counts written in the brief win over the form's numbers (the form only fills gaps)."""
    beds = int(req.get("bedrooms_stated") or bedrooms or 0)
    if req.get("bathrooms_stated"):
        baths = int(req["bathrooms_stated"])
    else:
        derived = int(req.get("attached_baths") or 0) + (1 if req.get("drawing_bath") else 0) + \
            (1 if req.get("powder_bath") else 0) + (1 if req.get("servant_bath") else 0)
        baths = derived if derived else int(req.get("bathrooms_llm") or bathrooms or 0)
    return beds, baths


def summarise_requirements(req: Dict[str, Any], bedrooms: int, bathrooms: int, floors: int) -> str:
    """One plain-English line of what will be built (derived from the checklist, never invented)."""
    portion = req.get("portion") or {}
    if portion.get("kind") == "upper":
        lvl = portion.get("level", 1)
        storey = {1: "First-floor", 2: "Second-floor", 3: "Third-floor"}.get(lvl, "Upper-floor") + \
            " portion (entered by the stair from the ground)"
        parts = [storey]
    else:
        parts = [{1: "Single-storey", 2: "Double-storey", 3: "Triple-storey"}.get(int(floors), f"{floors}-storey") + " house"
                 if floors else "House (storeys not stated - the architect chooses)"]
    rooms_word = "room" if req.get("sofa_beds") else "bedroom"
    if bedrooms:
        parts.append(f"{bedrooms} {rooms_word}{'s' if bedrooms != 1 else ''}" +
                     (" each with an attached bath" if req.get("attached_baths") and req["attached_baths"] >= bedrooms else
                      (f" ({req['attached_baths']} with attached bath)" if req.get("attached_baths") else "")))
    if bathrooms:
        parts.append(f"{bathrooms} bathroom{'s' if bathrooms != 1 else ''} in total")
    if req.get("sofa_beds"):
        parts.append(f"{req['sofa_beds']} of the rooms as family bed spaces with a sofa bed")
    named_drawing = req.get("drawing_stated", True) or req.get("drawing_bath") or req.get("floor_seating")
    if req.get("drawing_room", True) and named_drawing:
        d = "drawing room"
        if req.get("drawing_bath"):
            d += " with its own bath"
        if req.get("floor_seating"):
            d += " and Arab-style floor seating"
        if req.get("powder_bath"):
            d += ", guest powder bath"
        parts.append(d)
    elif req.get("powder_bath"):
        parts.append("guest powder bath")
    elif not req.get("drawing_room", True):
        parts.append("no drawing room")
    if req.get("open_corridor"):
        parts.append("open corridor" + (" with an entrance gate" if req.get("entry_gate") else ""))
    elif req.get("entry_gate"):
        parts.append("entrance gate")
    if req.get("single_kitchen"):
        parts.append("one kitchen")
    elif req.get("dirty_kitchen"):
        parts.append("kitchen + dirty kitchen")
    elif req.get("kitchen_stated", True):
        parts.append("kitchen")
    for rs in req.get("room_sizes", []):
        parts.append(f"{rs['label'].lower()} {_size_text(rs['w_ft'])} x {_size_text(rs['l_ft'])}" +
                     (" (each)" if rs.get("every") else ""))
    if req.get("no_porch"):
        parts.append("no car porch")
    elif portion.get("kind") != "upper" and req.get("porch_stated", True):
        parts.append(f"car porch for {req.get('cars', 1)} car{'s' if req.get('cars', 1) > 1 else ''}")
    if req.get("beds_per_level"):
        names = {"0": "ground", "1": "first", "2": "second", "3": "third"}
        parts.append("bedrooms " + ", ".join(f"{n} on the {names.get(k, k)} floor" for k, n in req["beds_per_level"].items()))
    if req.get("stair_location") == "entrance":
        parts.append("stair near the entrance (from the lobby)")
    elif req.get("stair_location") == "inside":
        parts.append("stair inside, from the lounge")
    if req.get("stair_position"):
        parts.append(f"stair at the {req['stair_position']} of the plot")
    if req.get("same_layout"):
        parts.append("same layout on every floor")
    for ci in req.get("custom_items", []):
        parts.append(ci["item"].lower())
    if req.get("stair_location") == "porch":
        parts.append("stair from the porch / drive way")
    for e in req.get("extra_rooms", []):
        parts.append(_EXTRA_LABEL[e].lower() + (" with its own bath" if e == "servant" and req.get("servant_bath") else ""))
    if req.get("pool"):
        loc = req["pool"]["location"]
        parts.append("swimming pool" + (" on the roof" if loc == "roof" else f" ({loc})"))
    if req.get("roof_garden"):
        parts.append("rooftop terrace with a roof garden")
    elif req.get("roof_terrace"):
        parts.append("rooftop terrace")
    if req.get("rear_lawn"):
        parts.append("rear lawn")
    elif req.get("garden"):
        parts.append("garden / lawn")
    if req.get("master_floor") == 0:
        parts.append("master bedroom on the ground floor")
    if req.get("ventilation"):
        parts.append("natural ventilation")
    parts += [o.lower() for o in req.get("other_requests", [])]
    return ", ".join(parts) + "."


def _count_item(bedrooms: int, bathrooms: int, word: str) -> str:
    if bedrooms and bathrooms:
        return f"{bedrooms} {word} and at least {bathrooms} bathrooms"
    return f"{bedrooms} {word}" if bedrooms else f"at least {bathrooms} bathrooms"


def build_checklist(req: Dict[str, Any], bedrooms: int, bathrooms: int, floors: int) -> List[str]:
    bedrooms, bathrooms = effective_counts(req, bedrooms, bathrooms)
    req["bedrooms"], req["bathrooms"] = bedrooms, bathrooms
    req["understood_as"] = summarise_requirements(req, bedrooms, bathrooms, floors)
    portion = req.get("portion") or {}
    if portion.get("kind") == "upper":
        lvl = portion.get("level", 1)
        items = [f"ONLY LEVEL {lvl} - an upper-floor portion entered by the STAIR coming up from the ground "
                 f"(no ground floor, no car porch)"]
        if bedrooms or bathrooms:
            items.append(_count_item(bedrooms, bathrooms, "rooms / bed spaces") + " on that level")
    else:
        items = []
        if bedrooms or bathrooms:
            items.append(_count_item(bedrooms, bathrooms, "bedrooms") + (f" across {floors} floor(s)" if floors else ""))
    for rs in req.get("room_sizes", []):
        items.append(f"{rs['label'].upper()} {_size_text(rs['w_ft'])} x {_size_text(rs['l_ft'])} as the brief says "
                     f"({'every room whose' if rs.get('every') else 'the room whose'} NAME contains {rs['keywords'][0]})")
    if req.get("attached_baths"):
        items.append(f"{req['attached_baths']} rooms each with its OWN attached bath (the bath's door: is that room)")
    if req.get("sofa_beds"):
        items.append(f"{req['sofa_beds']} of the rooms are family BED SPACES with a SOFA BED (name them BED SPACE n, "
                     f"furniture: sofa_bed)")
    if req.get("drawing_bath"):
        items.append("DRAWING room with its own attached bath (bath entered from the drawing room)")
    if req.get("floor_seating"):
        items.append("DRAWING with Arab-style FLOOR SEATING (majlis) - furniture: floor_seating")
    if req.get("open_corridor"):
        items.append("OPEN CORRIDOR (type gallery, on open air) that the rooms open onto")
    if req.get("entry_gate"):
        items.append("ENTRANCE GATE into the unit - write gate on that line (e.g. the corridor / stair landing)")
    if req.get("single_kitchen"):
        items.append("ONE kitchen only (no dirty kitchen)")
    for ci in req.get("custom_items", []):
        extra = []
        if ci.get("attached_bath"):
            extra.append("with its own attached bath")
        if ci.get("furniture"):
            extra.append(f"furniture: {ci['furniture']}")
        how = f"room NAME contains {ci['keyword']}"
        if ci["keyword"] in _KEYWORD_TYPES:
            how = (f"draw it as a real room: a STORE (type store) and / or a LAUNDRY / WASH AREA (type wash_area), "
                   f"entered from a lobby / corridor / kitchen")
        items.append(f"{ci['item']} ({how}{'; ' + ', '.join(extra) if extra else ''})")
    if req.get("pool"):
        loc = req["pool"]["location"]
        items.append("SWIMMING / PLUNGE POOL (type \"pool\") on the ROOF terrace (floor with \"roof\": true)" if loc == "roof"
                     else f"SWIMMING POOL (type \"pool\") in the {loc} open space, reachable from the house "
                          f"(if it cannot fit on the ground, a plunge pool on the roof terrace)")
    if req.get("stair_location") == "porch":
        items.append("STAIRCASE entered directly from the CAR PORCH / DRIVE WAY (separate access to the upper floors)")
    elif req.get("stair_location") == "inside":
        items.append("STAIRCASE inside the house, entered from the lounge (door: the lounge)")
    elif req.get("stair_location") == "entrance":
        items.append("STAIRCASE near the entrance, entered from the ENT LOBBY (door: the entrance lobby)")
    if req.get("stair_position"):
        p = req["stair_position"]
        where = {"front": "the front third of the built depth (near the street)", "back": "the back third of the built depth",
                 "middle": "the middle of the plot", "left": "the left side of the plot", "right": "the right side of the plot"}[p]
        items.append(f"STAIRCASE placed at {where}")
    if req.get("beds_per_level"):
        items.append("BEDROOMS PER LEVEL: " + ", ".join(f"LEVEL {k}: {n}" for k, n in req["beds_per_level"].items()))
    if req.get("no_porch"):
        items.append("NO car porch (the client said so)")
    if req.get("same_layout"):
        items.append("Every floor repeats the SAME layout (the client asked for it)")
    if req.get("cars", 1) > 1 and portion.get("kind") != "upper" and not req.get("no_porch"):
        items.append(f"CAR PORCH that parks {req['cars']} cars side by side (furniture: car - the engine places the "
                     f"cars and checks they fit)")
    if req.get("powder_bath"):
        items.append("POWDER BATH (type \"powder\") for guests next to the ENT LOBBY / drawing room")
    if req.get("dirty_kitchen"):
        items.append("DIRTY KITCHEN (type \"dirty_kitchen\") beside the main kitchen, with a window on the OTS / outside")
    for e in req.get("extra_rooms", []):
        label = _EXTRA_LABEL[e]
        roof_ok = (req.get("portion") or {}).get("kind") != "upper"
        if e == "servant" and req.get("servant_bath"):
            label += " with its own bath" + (" (may go on the ROOF beside the stair mumty)" if roof_ok else "")
        elif e in ("prayer", "gym", "study", "laundry") and roof_ok:
            label += " (may go on the ROOF beside the stair mumty if the floors are full)"
        items.append(f"{label} as its own room")
    if req.get("roof_terrace"):
        items.append("ROOF level (floor with \"roof\": true) with the stair mumty and an open ROOF TERRACE")
    if req.get("roof_garden"):
        items.append("ROOF GARDEN (type \"garden\") on the roof level")
    if not req.get("drawing_room", True):
        items.append("NO drawing room")
    if req.get("rear_lawn"):
        items.append("REAR LAWN / garden")
    elif req.get("garden"):
        items.append("GARDEN / LAWN at ground level")
    if req.get("master_floor") == 0:
        items.append("MASTER BEDROOM on the ground floor")
    if req.get("ventilation"):
        items.append("NATURAL VENTILATION: every habitable room has a window on open air (setback, lawn, OTS, terrace)")
    return items


# ---------------------------------------------------------------------------
# Verification on the final design
# ---------------------------------------------------------------------------

_UTILITY_WORDS = ("UTILITY", "LAUNDRY", "WASH", "SERVICE", "STORE", "STORAGE", "PANTRY")
_STORAGE_WORDS = ("STORE", "STORAGE", "PANTRY", "UTILITY")
_KEYWORD_SYNONYMS = {"UTILITY": _UTILITY_WORDS, "UTILITIES": _UTILITY_WORDS, "SERVICE": _UTILITY_WORDS,
                     "STORAGE": _STORAGE_WORDS, "STORE": _STORAGE_WORDS, "STOREROOM": _STORAGE_WORDS,
                     "WASHING": ("WASH", "LAUNDRY", "UTILITY"), "WASH": ("WASH", "LAUNDRY", "UTILITY")}
_KEYWORD_TYPES = {"UTILITY": ("store", "wash_area"), "UTILITIES": ("store", "wash_area"), "SERVICE": ("store", "wash_area"),
                  "STORAGE": ("store",), "STORE": ("store",), "STOREROOM": ("store",),
                  "WASHING": ("wash_area",), "WASH": ("wash_area",)}


def check_requirements(layout: Dict[str, Any], req: Dict[str, Any], bedrooms: int, bathrooms: int) -> List[Dict[str, Any]]:
    """Returns one entry per requirement: {item, met, detail, requested, delivered, status}."""
    floors = layout.get("floors", [])
    rooms = [(fl.get("level", i), r, bool(fl.get("roof"))) for i, fl in enumerate(floors) for r in fl.get("rooms", [])]
    names = [(lvl, r["name"].upper(), r.get("category", "")) for lvl, r, _ in rooms]
    all_doors = [(fl.get("level", i), d) for i, fl in enumerate(floors) for d in fl.get("doors", [])]
    by_id = {(lvl, r["id"]): r for lvl, r, _ in rooms}
    floor_label = {fl.get("level", i): fl.get("label", f"LEVEL {i}") for i, fl in enumerate(floors)}
    out: List[Dict[str, Any]] = []

    def add(item, met, detail, requested="yes", delivered=None, partial=False):
        out.append({"item": item, "met": bool(met), "detail": detail, "requested": requested,
                    "delivered": delivered if delivered is not None else (detail if met else "missing"),
                    "status": "PASS" if met else ("PARTIAL" if partial else "FAIL")})

    def find(pred):
        return [(lvl, r) for lvl, r, _ in rooms if pred(r)]

    beds = sum(1 for _, n, c in names if c == "bedroom" and "SERVANT" not in n and "GUEST" not in n)
    beds += sum(1 for _, n, c in names if c == "bedroom" and "GUEST" in n and "guest" not in req.get("extra_rooms", []))
    baths = sum(1 for _, _, c in names if c == "bath")
    if bedrooms:            # counts are checked only when the brief gives them
        add(f"{bedrooms} bedrooms", beds >= bedrooms, f"{beds} bedrooms drawn", str(bedrooms), str(beds),
            partial=0 < beds < bedrooms)
    if bathrooms:
        add(f"{bathrooms} bathrooms", baths >= bathrooms, f"{baths} bathrooms drawn (incl. powder / servant baths)",
            str(bathrooms), str(baths), partial=0 < baths < bathrooms)

    if req.get("pool"):
        pools = find(lambda r: r.get("category") == "pool")
        want = req["pool"]["location"]
        if pools:
            lvl, p = pools[0]
            where = floor_label.get(lvl, "")
            add("Swimming pool", True, f"{p['name']} {p['w_ft']:.1f} x {p['l_ft']:.1f} ft on the {where.lower()}",
                f"pool ({want})", f"{p['w_ft']:.0f}' x {p['l_ft']:.0f}' - {where.lower()}")
        else:
            add("Swimming pool", False, "no space for a pool on this plot", f"pool ({want})", "not drawn")
    if req.get("stair_location") == "porch":
        ok = False
        for fl in floors[:1]:
            stairs = {r["id"] for r in fl["rooms"] if r.get("category") == "stair"}
            porches = {r["id"] for r in fl["rooms"] if r.get("category") == "porch" or "DRIVE" in r["name"].upper()}
            ok = any((d["room_id"] in stairs and d["from_id"] in porches) or
                     (d["from_id"] in stairs and d["room_id"] in porches) for d in fl.get("doors", []))
        add("Stair entered from the car porch / drive way", ok,
            "stair opens onto the porch" if ok else "stair is not entered from the porch", "stair in porch / drive way")
    if req.get("stair_location") in ("inside", "entrance") and floors:
        fl = floors[0]
        cat = {r["id"]: (r.get("category", ""), r["name"].upper()) for r in fl.get("rooms", [])}
        stairs = {rid for rid, (c, _) in cat.items() if c == "stair"}
        froms = [cat.get(d["from_id"] if d["room_id"] in stairs else d["room_id"], ("", ""))
                 for d in fl.get("doors", []) if d["room_id"] in stairs or d["from_id"] in stairs]
        if req["stair_location"] == "inside":
            ok = any(c in ("lounge", "circulation") for c, _ in froms)
            add("Stair inside, from the lounge", ok, "stair opens onto " + (", ".join(n for _, n in froms) or "nothing"),
                "stair inside")
        else:
            ok = any(any(k in n for k in ("LOBBY", "ENT", "FOYER")) for _, n in froms)
            add("Stair near the entrance", ok, "stair opens onto " + (", ".join(n for _, n in froms) or "nothing"),
                "stair near the entrance")
    if req.get("stair_position") and floors:
        st = [r for r in floors[0].get("rooms", []) if r.get("category") == "stair"]
        W = float(layout.get("plot_width_ft") or 0)
        L = float(layout.get("plot_length_ft") or 0)
        fs, rs = float(layout.get("front_setback_ft") or 0), float(layout.get("rear_setback_ft") or 0)
        p = req["stair_position"]
        ok, where = False, "no stair"
        if st and W and L:
            s = st[0]
            cx, cy = float(s["x_ft"]) + float(s["w_ft"]) / 2, float(s["y_ft"]) + float(s["l_ft"]) / 2
            depth_axis = p in ("front", "back") or (p == "middle" and (L - fs - rs) >= 20)
            if depth_axis:
                f = (cy - fs) / max(1.0, L - fs - rs)
                where = "front" if f < 1 / 3 else ("back" if f > 2 / 3 else "middle")
            else:
                f = cx / W
                where = "left" if f < 1 / 3 else ("right" if f > 2 / 3 else "middle")
            ok = where == p
        add(f"Stair at the {p}", ok, f"stair is at the {where}", f"stair at the {p}")
    if req.get("beds_per_level"):
        want = {int(k): int(v) for k, v in req["beds_per_level"].items()}
        got = {lv: sum(1 for l2, n, c in names if l2 == lv and c == "bedroom" and "SERVANT" not in n) for lv in want}
        for lv, n in want.items():
            add(f"{n} bedroom{'s' if n != 1 else ''} on level {lv}", got[lv] >= n, f"{got[lv]} drawn on level {lv}",
                str(n), str(got[lv]), partial=0 < got[lv] < n)
            out[-1]["level"] = lv
    if req.get("no_porch"):
        porch = find(lambda r: r.get("category") == "porch")
        add("No car porch", not porch, "none drawn" if not porch else "a car porch is still drawn", "no car porch")
    if req.get("cars", 1) > 1 and not req.get("no_porch"):
        cars = sum(1 for fl in floors[:1] for f in fl.get("furniture", []) if f["type"].startswith("car"))
        add(f"Car porch for {req['cars']} cars", cars >= req["cars"],
            f"{cars} car(s) fit" + ("" if cars >= req["cars"] else
                                    " - the frontage is too narrow for side-by-side parking with an entrance"),
            f"{req['cars']} cars", f"{cars} car(s)", partial=cars > 0)
    if req.get("powder_bath"):
        pw = find(lambda r: r.get("category") == "bath" and "POWDER" in r["name"].upper())
        add("Powder bath for guests", bool(pw),
            f"{pw[0][1]['name']} {pw[0][1]['w_ft']:.1f} x {pw[0][1]['l_ft']:.1f} ft" if pw else
            "no room left beside the entrance / drawing room", "powder bath near the entrance")
    if req.get("dirty_kitchen"):
        dk = find(lambda r: "DIRTY" in r["name"].upper())
        add("Dirty kitchen", bool(dk),
            f"{dk[0][1]['name']} {dk[0][1]['w_ft']:.1f} x {dk[0][1]['l_ft']:.1f} ft beside the kitchen" if dk else
            "the kitchen bay is too narrow for a separate dirty kitchen", "dirty kitchen")
    for e in req.get("extra_rooms", []):
        label = _EXTRA_LABEL[e]
        key = label.split()[0]
        hits = find(lambda r, key=key: key in r["name"].upper()) or \
            (find(lambda r: "DINING" in r["name"].upper()) if e == "dining" else [])
        if hits:
            lvl, r0 = hits[0]
            det = f"{r0['name']} {r0['w_ft']:.1f} x {r0['l_ft']:.1f} ft on the {floor_label.get(lvl, '').lower()}"
        else:
            det = "no free room left - add a floor or reduce bedrooms"
        add(label, bool(hits), det, label.lower())
        if e == "servant" and req.get("servant_bath"):
            ok = False
            for lvl, r0 in hits:
                ok = ok or any(l2 == lvl and ((d["room_id"] == r0["id"] and by_id.get((lvl, d["from_id"]), {}).get("category") == "bath") or
                                              (d["from_id"] == r0["id"] and by_id.get((lvl, d["room_id"]), {}).get("category") == "bath"))
                               for l2, d in all_doors)
            add("Servant quarter has its own bath", ok, "attached bath" if ok else "uses the common bath",
                "servant bath", partial=bool(hits))
    if req.get("roof_terrace"):
        rt = [(lvl, r) for lvl, r, roof in rooms if roof and r.get("category") == "outdoor"
              and any(k in r["name"].upper() for k in ("TERRACE", "GARDEN"))]
        add("Rooftop terrace", bool(rt), "open roof terrace around the stair mumty" if rt else "no roof level drawn",
            "rooftop terrace")
    if req.get("roof_garden"):
        rg = [(lvl, r) for lvl, r, roof in rooms if roof and "GARDEN" in r["name"].upper()]
        add("Roof garden", bool(rg),
            f"{rg[0][1]['name']} {rg[0][1]['w_ft']:.1f} x {rg[0][1]['l_ft']:.1f} ft with planters" if rg else
            "no roof garden drawn", "garden on the roof")
    if not req.get("drawing_room", True):
        has = any("DRAWING" in n or "DRG" in n for _, n, _ in names)
        add("No drawing room", not has, "omitted" if not has else "a drawing room is still drawn", "no drawing room")
    if req.get("rear_lawn"):
        has = any("REAR LAWN" in n or ("LAWN" in n and lvl == 0) for lvl, n, _ in names)
        add("Rear lawn", has, "present" if has else "missing", "rear lawn")
    elif req.get("garden"):
        has = any(lvl == 0 and ("LAWN" in n or "GARDEN" in n) for lvl, n, _ in names)
        add("Garden / lawn", has, "front lawn with planting" if has else "missing", "garden")
    if req.get("master_floor") == 0:
        has = any(lvl == 0 and "MASTER" in n and c == "bedroom" for lvl, n, c in names)
        add("Master bedroom on ground floor", has, "present" if has else "master is upstairs", "master on ground")
    if req.get("ventilation"):
        land = [i for i in (layout.get("validation") or {}).get("errors", []) if i["code"] == "LANDLOCKED"]
        add("Natural ventilation", not land,
            "every habitable room has a window on open air (setback, lawn, OTS or terrace)" if not land else
            f"{len(land)} room(s) without a window", "natural ventilation")
    if req.get("walk_in_closet"):
        dr = find(lambda r: r.get("category") == "dressing" and "DRESS" in r["name"].upper())
        add("Walk-in closet / dressing", bool(dr), f"{len(dr)} dressing room(s)" if dr else "missing", "walk-in closets")
    if req.get("pantry"):
        st = find(lambda r: any(k in r["name"].upper() for k in ("STORE", "PANTRY")))
        add("Pantry / store", bool(st), f"{st[0][1]['name']}" if st else "missing", "pantry store")

    # ---- spaces described in the brief itself ------------------------------------------------
    cat_of = {(lvl, r["id"]): r.get("category", "") for lvl, r, _ in rooms}

    def has_attached_bath(lvl, rid):
        return any(l2 == lvl and ((d["from_id"] == rid and cat_of.get((lvl, d["room_id"])) == "bath") or
                                  (d["room_id"] == rid and cat_of.get((lvl, d["from_id"])) == "bath"))
                   for l2, d in all_doors)

    all_furn = [(fl.get("level", i), f) for i, fl in enumerate(floors) for f in fl.get("furniture", [])]
    portion = req.get("portion") or {}
    if portion.get("kind") == "upper":
        lv = portion.get("level", 1)
        levels = sorted({fl.get("level", i) for i, fl in enumerate(floors)})
        porch = find(lambda r: r.get("category") == "porch")
        ok = levels == [lv] and not porch
        add(f"Only the level-{lv} portion is designed", ok,
            f"LEVEL {lv} entered by the stair" if ok else f"levels drawn: {levels}" + (" (has a car porch)" if porch else ""),
            f"level {lv} portion", f"level(s) {levels}")
    if req.get("attached_baths"):
        n = int(req["attached_baths"])
        beds_att = [r for lvl, r in find(lambda r: r.get("category") == "bedroom") if has_attached_bath(lvl, r["id"])]
        add(f"{n} rooms with their own bath", len(beds_att) >= n,
            f"{len(beds_att)} room(s) with an attached bath: " + ", ".join(r["name"] for r in beds_att[:6]),
            f"{n} rooms with bath", f"{len(beds_att)}", partial=0 < len(beds_att) < n)
    if req.get("sofa_beds"):
        n = int(req["sofa_beds"])
        sb = [f for _, f in all_furn if f["type"] == "sofa_bed"]
        add(f"{n} bed spaces with a sofa bed", len(sb) >= n, f"{len(sb)} sofa bed(s) drawn", f"{n} sofa beds",
            f"{len(sb)}", partial=0 < len(sb) < n)
    if req.get("drawing_bath"):
        dr = [r for lvl, r in find(lambda r: r.get("category") == "drawing") if has_attached_bath(lvl, r["id"])]
        add("Drawing room with its own bath", bool(dr), f"{dr[0]['name']} has an attached bath" if dr else
            "no bath opens off the drawing room", "drawing with bath")
    if req.get("floor_seating"):
        fs = [f for _, f in all_furn if f["type"] == "floor_cushion"]
        add("Arab-style floor seating in the drawing", bool(fs),
            f"{len(fs)} run(s) of floor cushions (majlis) with a low table" if fs else "no floor seating drawn",
            "ground seating, Arab style")
    if req.get("open_corridor"):
        oc = find(lambda r: str(r.get("type", "")).lower() in ("gallery", "open_corridor", "verandah") or
                  any(k in r["name"].upper() for k in ("CORRIDOR", "GALLERY", "VERANDAH")))
        add("Open corridor", bool(oc), f"{oc[0][1]['name']} {oc[0][1]['w_ft']:.1f} x {oc[0][1]['l_ft']:.1f} ft"
            if oc else "missing", "open corridor")
    if req.get("entry_gate"):
        g = find(lambda r: r.get("gate"))
        add("Entrance gate", bool(g), f"gate into the unit at {g[0][1]['name']}" if g else "no entrance gate marked",
            "gate to enter")
    if req.get("single_kitchen"):
        ks = find(lambda r: r.get("category") == "kitchen")
        add("One kitchen", len(ks) == 1, f"{len(ks)} kitchen(s)", "single kitchen", str(len(ks)))
    for rs in req.get("room_sizes", []):
        want = sorted((float(rs["w_ft"]), float(rs["l_ft"])))
        cands = find(lambda r, ks=tuple(rs["keywords"]): any(k in r["name"].upper() for k in ks))
        label = f"{rs['label']} {_size_text(rs['w_ft'])} x {_size_text(rs['l_ft'])}"

        def fit(r, want=want):
            got = sorted((float(r["w_ft"]), float(r["l_ft"])))
            exact = all(abs(g - w) <= max(1.0, 0.08 * w) for g, w in zip(got, want))
            close = abs(got[0] * got[1] - want[0] * want[1]) <= 0.2 * want[0] * want[1]
            return exact, close, f"{r['name']} {_size_text(got[0])} x {_size_text(got[1])}"
        fits = [fit(r) for _, r in cands]
        if not fits:
            add(label, False, "no room with that name in the design", rs.get("quote", label), "not found")
            continue
        if rs.get("every"):
            ok = all(f[0] for f in fits)
            add(label + " (each)", ok, "; ".join(f[2] for f in fits[:6]), rs.get("quote", label),
                f"{sum(f[0] for f in fits)} of {len(fits)} at that size", partial=not ok and any(f[1] for f in fits))
        else:
            fits.sort(key=lambda f: (not f[0], not f[1]))
            add(label, fits[0][0], fits[0][2] + ("" if fits[0][0] else " - not the size the brief asks for"),
                rs.get("quote", label), fits[0][2], partial=fits[0][1])
    for ci in req.get("custom_items", []):
        # a utility / storage request is met by the store, laundry and wash rooms the engine already knows
        words = _KEYWORD_SYNONYMS.get(ci["keyword"], (ci["keyword"],))
        types_ok = _KEYWORD_TYPES.get(ci["keyword"], ())
        hits = find(lambda r, ws=words, ts=types_ok: any(w in r["name"].upper() for w in ws) or
                    str(r.get("type", "")).lower() in ts)
        if ci.get("attached_bath"):
            hits = [(lvl, r) for lvl, r in hits if has_attached_bath(lvl, r["id"])]
        if ci.get("furniture"):
            hits = [(lvl, r) for lvl, r in hits if any(f["room_id"] == r["id"] and ci["furniture"].split("_")[0] in f["type"]
                                                       for l2, f in all_furn if l2 == lvl)]
        n = int(ci.get("count") or 1)
        add(ci["item"], len(hits) >= n, (f"{len(hits)} found: " + ", ".join(r["name"] for _, r in hits[:5])) if hits
            else "not found in the design", ci.get("quote", "")[:60] or ci["item"], partial=0 < len(hits) < n)
    # which level a check belongs to - when a house is designed level by level, ground-floor items are checked
    # (and fixed) while the ground floor is designed; whole-house items (counts, custom rooms) at the end
    ground = ("Stair ", "No car porch", "Car porch for", "Powder bath", "Rear lawn", "Garden / lawn",
              "Master bedroom on ground")
    for e in out:
        if "level" not in e:
            e["level"] = 0 if (e["item"].startswith(ground) or (e["item"] == "Swimming pool" and
                                                                (req.get("pool") or {}).get("location") != "roof")) else None
    return out


def compliance_checklist(report: List[Dict[str, Any]], req: Dict[str, Any], front_sb: float, rear_sb: float,
                         has_ots: bool, has_roof: bool) -> Dict[str, Any]:
    """The UI's REQUIREMENTS COMPLIANCE CHECKLIST panel format."""
    items = [{"name": r["item"], "requested": r.get("requested", "yes"), "delivered": r.get("delivered", ""),
              "detail": r["detail"], "status": r.get("status", "PASS" if r["met"] else "FAIL")} for r in report]
    for o in req.get("other_requests", []):
        items.append({"name": o, "requested": o.lower(), "delivered": "not drawn",
                      "detail": "the 2D generator cannot draw this yet", "status": "FAIL"})
    passed = sum(1 for i in items if i["status"] == "PASS")
    total = len(items)

    def ftin(v):
        f = int(v)
        i = int(round((v - f) * 12))
        return f"{f}'-{i}\""
    defaults = []
    if front_sb > 0:
        defaults.append({"name": "Front setback", "delivered": f"{ftin(front_sb)} open space at the front",
                         "statutory_role": "Requested in prompt", "status": "APPLIED"})
    if rear_sb > 0:
        defaults.append({"name": "Rear setback", "delivered": f"{ftin(rear_sb)} open space at the back",
                         "statutory_role": "Requested in prompt", "status": "APPLIED"})
    defaults.append({"name": "Stair stacked on every level", "delivered": "same rectangle on every floor" +
                     (" up to the roof mumty" if has_roof else ""), "statutory_role": "Structural alignment",
                     "status": "APPLIED"})
    if has_ots:
        defaults.append({"name": "OTS / light well", "delivered": "open to sky, never roofed over",
                         "statutory_role": "Daylight & ventilation of the kitchen / lounge", "status": "APPLIED"})
    out = {"all_passed": passed == total, "score_pct": int(round(100.0 * passed / max(1, total))),
           "passed_count": passed, "total_count": total, "requested_items": items, "items": items,
           "bylaw_defaults": [], "has_fail": passed < total}      # no rule list is applied: the prompt decides
    if req.get("understood_as"):
        out["understood_as"] = req["understood_as"]
    return out


# ---------------------------------------------------------------------------
# Conversation: a change request can add or remove client items
# ---------------------------------------------------------------------------

_REMOVABLE = [
    (r"pool", lambda r: r.pop("pool", None)),
    (r"servant", lambda r: r.__setitem__("extra_rooms", [e for e in r.get("extra_rooms", []) if e != "servant"])),
    (r"prayer", lambda r: r.__setitem__("extra_rooms", [e for e in r.get("extra_rooms", []) if e != "prayer"])),
    (r"gym", lambda r: r.__setitem__("extra_rooms", [e for e in r.get("extra_rooms", []) if e != "gym"])),
    (r"study|office", lambda r: r.__setitem__("extra_rooms", [e for e in r.get("extra_rooms", []) if e != "study"])),
    (r"dining", lambda r: r.__setitem__("extra_rooms", [e for e in r.get("extra_rooms", []) if e != "dining"])),
    (r"laundry", lambda r: r.__setitem__("extra_rooms", [e for e in r.get("extra_rooms", []) if e != "laundry"])),
    (r"store|storage", lambda r: r.__setitem__("extra_rooms", [e for e in r.get("extra_rooms", []) if e not in ("store", "storage")])),
    (r"powder", lambda r: r.__setitem__("powder_bath", False)),
    (r"dirty kitchen", lambda r: r.__setitem__("dirty_kitchen", False)),
    (r"roof garden|garden", lambda r: r.__setitem__("roof_garden", False)),
    (r"roof terrace|terrace|balcony", lambda r: r.__setitem__("roof_terrace", False)),
    (r"rear lawn|front lawn|lawn", lambda r: r.__setitem__("rear_lawn", False)),
    (r"car porch|porch|garage|parking", lambda r: (r.__setitem__("no_car_porch", True), r.__setitem__("cars", 0), r.__setitem__("cars_stated", True))),
    (r"gate", lambda r: r.__setitem__("entry_gate", False)),
    (r"corridor|gallery", lambda r: r.__setitem__("open_corridor", False)),
    (r"sofa ?bed", lambda r: r.pop("sofa_beds", None)),
    (r"floor seating|majlis", lambda r: r.__setitem__("floor_seating", False)),
    (r"drawing", lambda r: r.__setitem__("drawing_room", False)),
]

_REM_VERB = r"(?:remove|delete|drop|cut|eliminate|scrap|omit|without|no|get rid of|hata\w*|nahi|nahin)"


def apply_message_to_requirements(req: Dict[str, Any], message: str, bedrooms: int, bathrooms: int,
                                  floors: int) -> Dict[str, Any]:
    """'add a prayer room' adds the item to the checklist; 'remove/cut the drawing room' takes it off.
    Supports simultaneous cut + add (e.g. 'delete the drawing room and add a study room')."""
    t = normalise_brief(message)
    req = dict(req)
    req["extra_rooms"] = list(req.get("extra_rooms") or [])

    # 1. Process explicit removals / cuts first
    for pat, drop in _REMOVABLE:
        if re.search(rf"\b{_REM_VERB}\b[^.,;]{{0,30}}\b({pat})\b", t):
            drop(req)

    # Bedroom / bathroom decrements (e.g. "remove 1 bedroom", "delete bedroom 3", "cut a bathroom")
    if re.search(rf"\b{_REM_VERB}\b[^.,;]{{0,25}}\b(bed ?rooms?|beds?)\b", t):
        m_cnt = re.search(rf"\b{_REM_VERB}\b[^.,;]{{0,15}}\b(\d+)\s*(?:bed ?rooms?|beds?)\b", t)
        dec = int(m_cnt.group(1)) if m_cnt else 1
        cur_b = int(req.get("bedrooms") or bedrooms or 1)
        new_b = max(1, cur_b - dec)
        req["bedrooms"] = new_b
        req["bedrooms_stated"] = new_b
        req.pop("beds_per_floor", None)
    if re.search(rf"\b{_REM_VERB}\b[^.,;]{{0,25}}\b(bath ?rooms?|baths?|washrooms?|toilets?)\b", t):
        m_cnt = re.search(rf"\b{_REM_VERB}\b[^.,;]{{0,15}}\b(\d+)\s*(?:bath ?rooms?|baths?|washrooms?)\b", t)
        dec = int(m_cnt.group(1)) if m_cnt else 1
        cur_ba = int(req.get("bathrooms") or bathrooms or 1)
        new_ba = max(1, cur_ba - dec)
        req["bathrooms"] = new_ba
        req["bathrooms_stated"] = new_ba

    # 2. Process additions on non-negated clauses (so "remove X and add Y" works cleanly)
    add_text = re.sub(rf"\b{_REM_VERB}\b[^.,;&]*?(?=\band\b|\binstead\b|\breplace\b|,|\.|$)", " ", t)
    add = parse_brief(add_text, 0, 0, floors, bedrooms, bathrooms)
    for k in ("powder_bath", "drawing_bath", "dirty_kitchen", "roof_garden", "roof_terrace", "floor_seating",
              "open_corridor", "entry_gate", "rear_lawn"):
        if add.get(k):
            req[k] = True
    if add.get("pool") and not req.get("pool"):
        req["pool"] = add["pool"]
    inside = re.search(r"\b(corner|nook|mat|alcove|area)\b[^.]{0,30}\b(in|inside|within)\s+(the\s+)?\w+", add_text) or \
        re.search(r"\b(in|inside)\s+(the\s+)?(drawing|lounge|bed ?room|kitchen|corridor|majlis)", add_text)
    for e in add.get("extra_rooms", []):
        if inside or not re.search(r"\b(add|make|create|need|want|replace\s+\w+\s+with|chahiye)\b[^.]{0,35}" + e[:5] + r"\w*", add_text):
            continue
        if e not in req["extra_rooms"]:
            req["extra_rooms"].append(e)
    for k in ("bedrooms_stated", "bathrooms_stated", "attached_baths", "sofa_beds"):
        if add.get(k):
            req[k] = add[k]
            if k == "bedrooms_stated":
                req["bedrooms"] = add[k]
            elif k == "bathrooms_stated":
                req["bathrooms"] = add[k]
    if add.get("cars_stated") and not req.get("no_car_porch"):
        req["cars"] = add["cars"]

    eff_beds = int(req.get("bedrooms") or bedrooms)
    eff_baths = int(req.get("bathrooms") or bathrooms)
    req["checklist"] = build_checklist(req, eff_beds, eff_baths, floors)
    return req
