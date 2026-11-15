"""
AI Civil Architect Interview Bot — Pure Text-Based Conversational Brief Builder
================================================================================

Uses the Gemini LLM to act as a real civil engineer and residential architect.
Instead of a rigid form or pre-selected option chips, the architect reads what
the client wrote, considers their place/location and plot sizing (including Marla,
Kanal, sq ft, sq yd, or W x L feet), and conducts a natural text-based interview
to clarify and refine the client's desires into a complete architectural brief.
"""

import json
import re
from typing import Any, Callable, Dict, List, Optional, Union

from generation.brief_parser import MARLA_SQFT, parse_brief, read_site


def _build_conversation_brief(
    initial_prompt: str,
    history: List[Dict[str, str]],
    answers: Optional[Dict[str, str]] = None,
) -> str:
    """Combines the initial prompt and all user messages in history into a single text."""
    parts: List[str] = []
    if (initial_prompt or "").strip():
        parts.append(initial_prompt.strip())
    for item in history or []:
        role = str(item.get("role") or "").lower()
        txt = str(item.get("text") or "").strip()
        if role in ("user", "client") and txt and txt.lower() != "let the architect decide" and txt not in parts:
            parts.append(txt)
    for _, ans in (answers or {}).items():
        ans = (ans or "").strip()
        if ans and ans not in parts:
            parts.append(ans)
    return " ".join(parts).strip()


def _fallback_architect_turn(
    compiled: str,
    site: Dict[str, Any],
    parsed: Dict[str, Any],
    turn_count: int,
) -> Dict[str, Any]:
    """Text-only fallback when Gemini is unreachable or has no API key."""
    has_plot = bool(site.get("width_ft") and site.get("length_ft"))
    has_floors = bool(site.get("storeys") or (parsed.get("portion") or {}).get("kind"))
    has_beds = bool(parsed.get("bedrooms") or re.search(r"\b\d+\s*(?:bed\s*rooms?|rooms?)\b", compiled, re.I))

    if not has_plot:
        return {
            "architect_reply": "What is the size of your plot (in Marla, Kanal, or width x depth in feet) and where is it located?",
            "why": "Everything is planned inside the plot, so I need its width and depth or Marla size.",
            "placeholder": "e.g. 5 Marla in Lahore, or 25 x 45 ft",
            "topic": "plot_size_and_place",
            "compiled_brief": compiled,
            "interview_complete": False,
        }
    if not has_floors:
        return {
            "architect_reply": f"How many floors (storeys) would you like to build on your {site['width_ft']:g}' x {site['length_ft']:g}' plot?",
            "why": "It decides whether we need a staircase and how rooms are distributed vertically.",
            "placeholder": "e.g. Single storey, or double storey (ground + first floor)",
            "topic": "storeys_and_building_type",
            "compiled_brief": compiled,
            "interview_complete": False,
        }
    if not has_beds:
        return {
            "architect_reply": "How many bedrooms or rooms do you want in total, along with bathrooms, kitchen, and lounge spaces?",
            "why": "Rooms take most of the floor area — the layout is arranged around them.",
            "placeholder": "e.g. 5 rooms with 2 baths, a central lounge, and a kitchen",
            "topic": "rooms_and_spatial_program",
            "compiled_brief": compiled,
            "interview_complete": False,
        }
    if turn_count < 2:
        return {
            "architect_reply": "How would you like the entrance, staircase access, car parking (or full-plot room coverage with no porch), and open ventilation spaces arranged?",
            "why": "This shapes privacy, street entry, and how much of the plot is covered by rooms.",
            "placeholder": "e.g. No car porch, entrance in the middle, internal light well for ventilation",
            "topic": "circulation_and_parking",
            "compiled_brief": compiled,
            "interview_complete": False,
        }
    return {
        "architect_reply": "",
        "why": "",
        "placeholder": "",
        "topic": "brief_complete",
        "compiled_brief": compiled,
        "interview_complete": True,
    }


def conduct_architect_interview(
    prompt: str = "",
    history: Optional[List[Dict[str, str]]] = None,
    answers: Optional[Dict[str, str]] = None,
    skipped: Optional[List[str]] = None,
    message: Optional[str] = None,
    llm_call_fn: Optional[Callable[[str], Optional[Union[str, Dict[str, Any]]]]] = None,
    brief: Optional[str] = None,
    user_message: Optional[str] = None,
) -> Dict[str, Any]:
    """
    Runs one turn of the pure text-based AI Civil Architect interview.
    """
    seed_prompt = prompt if prompt else (brief or "")
    incoming_msg = message if message is not None else user_message

    hist: List[Dict[str, str]] = [
        {"role": str(h.get("role") or "user"), "text": str(h.get("text") or "").strip()}
        for h in (history or [])
        if str(h.get("text") or "").strip()
    ]
    if incoming_msg and incoming_msg.strip():
        if not hist or hist[-1].get("role") != "user" or hist[-1].get("text") != incoming_msg.strip():
            hist.append({"role": "user", "text": incoming_msg.strip()})

    raw_combined = _build_conversation_brief(seed_prompt, hist, answers)
    pre_site = read_site(raw_combined)
    pre_parsed = parse_brief(
        raw_combined,
        pre_site.get("width_ft") or 0,
        pre_site.get("length_ft") or 0,
        int(pre_site.get("storeys") or 0),
        0,
        0,
    )
    user_turns = sum(1 for h in hist if h["role"] in ("user", "client"))

    llm_result: Optional[Dict[str, Any]] = None
    if llm_call_fn is not None:
        convo_text = "\n".join(
            f"{'ARCHITECT' if h['role'] == 'architect' else 'CLIENT'}: {h['text']}"
            for h in hist[-14:]
        ) or "(Interview just started)"
        understood_items = [x.strip() for x in (pre_parsed.get("understood_as") or "").split("·") if x.strip()]
        understood_text = "\n".join(f"- {u}" for u in understood_items) or "- Nothing extracted yet"
        skip_note = (
            f"\nThe client skipped / asked the architect to decide on: {', '.join(skipped)}."
            if skipped else ""
        )
        interview_prompt = f"""You are a seasoned Civil Engineer and Residential Architect conducting a 1-on-1 text-based design interview with a client.
Your goal is to understand the client's site, location/place, and exact desires, help them think through practical civil/architectural layout decisions, and maintain a clean, comprehensive design brief that our CAD engine will use to draw the 2D floor plans.

=== CORE PRINCIPLES ===
1. NO FIXED RULES OR MANDATORY BYLAWS: Never force society setbacks or reject unusual requests. If the client asks for 5 rooms in 5 Marla, zero setbacks, no car porch, or any custom arrangement, accept their desire and work out how to make it practically fit (e.g. asking whether they prefer compact rooms on one floor, or splitting across two floors, or using a central lounge/corridor). Only physics is not negotiable, and you say so plainly when it matters: every bedroom / lounge / kitchen needs a window on open air (the side boundaries are party walls, so a dense plan needs a small open-to-sky shaft or open strip), every room must be reachable without walking through a bedroom, and a staircase needs about 3.5 x 9 ft. For a house of 2 or more storeys, ask how many bedrooms go on each floor if the client has not said.
2. KEEP MARLA & SIZING TERMS: Understand Pakistani/regional sizing terms naturally (1 Marla = {MARLA_SQFT:g} sq ft; typical plots: 3 Marla ~ 20x34, 5 Marla ~ 25x45, 7 Marla ~ 30x52.5, 10 Marla ~ 35x65, 1 Kanal = 20 Marla ~ 50x90, or exact width x depth in feet).
3. PLACE & SITE AWARENESS: If the client mentions a city, climate, street orientation, or family lifestyle, tailor your architectural questions and suggestions to that place.
4. ONE FOCUSED QUESTION AT A TIME: Ask ONE concise, practical civil/architectural question per turn in plain English, plus a short 1-sentence `why` explaining why that decision matters for the plan, and a short `placeholder` example for the text box.
5. COMPILED BRIEF: Every turn, output an updated `compiled_brief` paragraph in plain English that combines everything the client has stated or confirmed so far (plot size/Marla, number of floors, exact rooms & bedrooms per floor, bathrooms, kitchen, lounge/drawing room, stairs/entrance, setbacks/open spaces, and any specific room dimensions). Never drop details the client gave earlier.

=== CLIENT'S CURRENT BRIEF ===
"{(seed_prompt or '').strip()}"

=== CONVERSATION HISTORY SO FAR ===
{convo_text}{skip_note}

=== WHAT THE PARSER CURRENTLY DETECTS ===
{understood_text}

Return ONLY valid JSON matching this exact structure:
{{
  "architect_reply": "<the next single clear civil-architect question to ask the client (or empty string if interview_complete is true)>",
  "why": "<1 short sentence explaining why this question matters for their floor plan>",
  "placeholder": "<short example answer for the input box, e.g. '2 bedrooms downstairs and 3 upstairs'>",
  "topic": "<short snake_case id for this question topic, e.g. 'plot_size', 'floor_split', 'circulation'>",
  "compiled_brief": "<complete, self-contained plain-English architectural brief incorporating all client requirements and answers so far>",
  "interview_complete": <true if plot size, floors, rooms/bedrooms, baths, kitchen/living, and circulation are sufficiently clear OR after 5-6 answered questions; false if important questions remain>
}}"""
        raw = llm_call_fn(interview_prompt)
        if isinstance(raw, dict):
            llm_result = raw
        elif isinstance(raw, str) and raw.strip():
            m = re.search(r"\{.*\}", raw, re.S)
            if m:
                try:
                    data = json.loads(m.group(0))
                    if isinstance(data, dict):
                        llm_result = data
                except Exception:
                    llm_result = None

    if llm_result is None:
        llm_result = _fallback_architect_turn(raw_combined, pre_site, pre_parsed, user_turns)

    compiled_brief = str(
        llm_result.get("compiled_brief")
        or llm_result.get("updated_brief")
        or raw_combined
    ).strip()

    site = read_site(compiled_brief)
    if raw_combined and not (site.get("width_ft") and site.get("length_ft")) and (pre_site.get("width_ft") and pre_site.get("length_ft")):
        compiled_brief = f"{raw_combined} {compiled_brief}".strip()
        site = read_site(compiled_brief)

    parsed = parse_brief(
        compiled_brief,
        site.get("width_ft") or 0,
        site.get("length_ft") or 0,
        int(site.get("storeys") or 0),
        0,
        0,
    )
    has_plot = bool(site.get("width_ft") and site.get("length_ft"))
    interview_complete = bool(llm_result.get("interview_complete", False)) and has_plot
    architect_reply = str(
        llm_result.get("architect_reply")
        or llm_result.get("architect_message")
        or ""
    ).strip()
    why_text = str(llm_result.get("why") or "").strip()
    placeholder_text = str(llm_result.get("placeholder") or "Type your answer in your own words...").strip()
    topic = str(llm_result.get("topic") or f"q_{user_turns + 1}").strip()

    updated_history = list(hist)
    if architect_reply and (
        not updated_history
        or updated_history[-1].get("role") != "architect"
        or updated_history[-1].get("text") != architect_reply
    ):
        updated_history.append({"role": "architect", "text": architect_reply})

    understood_str = parsed.get("understood_as") or ""
    understood_list = [x.strip() for x in understood_str.split("·") if x.strip()]

    questions: List[Dict[str, Any]] = []
    if not interview_complete and architect_reply:
        qid = f"{topic}_{user_turns + 1}"
        questions.append({
            "id": qid,
            "question": architect_reply,
            "why": why_text,
            "options": [],
            "required": not has_plot,
            "free_text": {
                "placeholder": placeholder_text,
                "template": "{answer}",
            },
            "source": "ai",
        })

    return {
        "compiled_brief": compiled_brief,
        "architect_reply": architect_reply,
        "architect_message": architect_reply,
        "topic": topic,
        "history": updated_history,
        "questions": questions,
        "understood": understood_list,
        "understood_as": understood_str,
        "parsed": {
            "plot_w": site.get("width_ft"),
            "plot_l": site.get("length_ft"),
            "area_marla": site.get("marla"),
            "floors": site.get("storeys"),
            "bedrooms": parsed.get("bedrooms"),
            "bathrooms": parsed.get("bathrooms"),
            "style": site.get("style"),
            "understood_as": understood_str,
        },
        "ready": has_plot,
        "interview_complete": interview_complete,
    }


def next_questions(
    prompt: str,
    answers: Optional[Dict[str, str]] = None,
    skipped: Optional[List[str]] = None,
    extra_questions: Optional[List[Dict[str, Any]]] = None,
    history: Optional[List[Dict[str, str]]] = None,
    message: Optional[str] = None,
    llm_call_fn: Optional[Callable[[str], Optional[Union[str, Dict[str, Any]]]]] = None,
) -> Dict[str, Any]:
    """Compatible entry point delegating to the pure text-based AI Civil Architect interview."""
    return conduct_architect_interview(
        prompt=prompt,
        history=history,
        answers=answers,
        skipped=skipped,
        message=message,
        llm_call_fn=llm_call_fn,
    )
