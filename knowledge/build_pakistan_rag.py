"""
Build the Nationwide Pakistan Construction Rules Knowledge Base & Vector Index
=============================================================================
Creates:
  1. knowledge/pakistan_bylaws.jsonl        — Cited, structured nationwide corpus
  2. knowledge/pakistan_bylaws_vectors.npz  — Gemini (gemini-embedding-001) 768-dim float32 vectors

Run:
    py knowledge/build_pakistan_rag.py
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from typing import Any, Dict, List

import numpy as np
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
KNOWLEDGE_DIR = ROOT / "knowledge"
JSONL_PATH = KNOWLEDGE_DIR / "pakistan_bylaws.jsonl"
VECTORS_PATH = KNOWLEDGE_DIR / "pakistan_bylaws_vectors.npz"

EMBED_MODEL = "gemini-embedding-001"
EMBED_DIM = 768


def _entry(
    eid: str,
    title: str,
    text: str,
    authority: str,
    jurisdiction_level: str,
    province: str,
    city: str,
    society: str,
    plot_sizes: str,
    topic: str,
    source_title: str,
    source_url: str,
    source_type: str,
    year: str = "",
    notes: str = "",
) -> Dict[str, Any]:
    return {
        "id": eid,
        "title": title,
        "text": text.strip(),
        "authority": authority,
        "jurisdiction_level": jurisdiction_level,
        "province": province,
        "city": city,
        "society": society,
        "plot_sizes": plot_sizes,
        "topic": topic,
        "source_title": source_title,
        "source_url": source_url,
        "source_type": source_type,
        "year": year,
        "notes": notes,
    }


def build_corpus() -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []

    # =========================================================================
    # 1. PUNJAB AUTHORITIES (LDA, RDA, FDA, MDA, GDA, BDA, Provincial Rules)
    # =========================================================================
    rows.extend([
        _entry(
            "punjab_lda_marla_definition",
            "LDA Standard Marla Definition (Lahore District)",
            "Under the Lahore Development Authority (LDA) Building and Zoning Regulations 2019, 1 Marla is standardized as exactly 225 square feet (and 1 Kanal = 20 Marlas = 4,500 sq ft) across LDA-controlled areas and approved housing schemes in Lahore District.",
            "Lahore Development Authority (LDA)", "city_authority", "Punjab", "Lahore", "", "all",
            "land_use_zoning", "LDA Building and Zoning Regulations 2019", "https://lda.gop.pk/", "secondary", "2019",
            "Older non-LDA urban areas or other provinces sometimes use 272.25 sq ft per Marla; always confirm plot dimensions in feet."
        ),
        _entry(
            "punjab_lda_setbacks_under_5marla",
            "LDA Setbacks, Coverage & Height — Under 5 Marla",
            "For residential plots smaller than 5 Marla under LDA Building and Zoning Regulations 2019, mandatory open spaces are 5 ft front setback (building line), 5 ft rear setback, and 0 ft side setbacks (attached row housing). Maximum ground coverage is 80%, maximum height is 38 ft (up to 3 storeys), and a basement is allowed within structural safety limits.",
            "Lahore Development Authority (LDA)", "city_authority", "Punjab", "Lahore", "", "3 marla, 4 marla, under 5 marla",
            "setbacks", "LDA Building and Zoning Regulations 2019", "https://lda.gop.pk/", "secondary", "2019"
        ),
        _entry(
            "punjab_lda_setbacks_5_to_10marla",
            "LDA Setbacks, Coverage & Height — 5 Marla to Under 10 Marla",
            "For residential plots from 5 Marla up to under 10 Marla (e.g. 25x45 ft, 30x52.5 ft) under LDA Building and Zoning Regulations 2019, mandatory setbacks are 5 ft front, 5 ft rear, and 0 ft sides (unless scheme layout requires a side passage). Maximum ground coverage is 75%, maximum building height is 38 ft (up to 3 storeys), and a basement is permitted (counted toward FAR).",
            "Lahore Development Authority (LDA)", "city_authority", "Punjab", "Lahore", "", "5 marla, 7 marla, 8 marla",
            "setbacks", "LDA Building and Zoning Regulations 2019", "https://lda.gop.pk/", "secondary", "2019"
        ),
        _entry(
            "punjab_lda_setbacks_10marla_to_1kanal",
            "LDA Setbacks, Coverage & Height — 10 Marla to Under 1 Kanal",
            "For 10 Marla to under 1 Kanal residential plots (e.g. 35x65 ft) under LDA Building and Zoning Regulations 2019, mandatory setbacks are 10 ft front, 7 ft rear, and 5 ft on one side. Maximum ground coverage is 70%, maximum building height is 45 ft (3 to 4 storeys within FAR limits), and basements are permitted.",
            "Lahore Development Authority (LDA)", "city_authority", "Punjab", "Lahore", "", "10 marla, 12 marla, 15 marla",
            "setbacks", "LDA Building and Zoning Regulations 2019", "https://lda.gop.pk/", "secondary", "2019"
        ),
        _entry(
            "punjab_lda_setbacks_1kanal_to_30marla",
            "LDA Setbacks, Coverage & Height — 1 Kanal to 30 Marla",
            "For 1 Kanal to 30 Marla residential plots (e.g. 50x90 ft) under LDA Building and Zoning Regulations 2019, mandatory setbacks are 10 ft front, 7 ft rear, and 5 ft on one side (above 30 Marla to under 2 Kanal requires 5 ft on both sides and 60% ground coverage). Maximum ground coverage for 1 Kanal is 65%, and maximum height is 45 ft (up to 4 storeys within FAR).",
            "Lahore Development Authority (LDA)", "city_authority", "Punjab", "Lahore", "", "1 kanal, 20 marla, 30 marla",
            "setbacks", "LDA Building and Zoning Regulations 2019", "https://lda.gop.pk/", "secondary", "2019"
        ),
        _entry(
            "punjab_lda_setbacks_2kanal_plus",
            "LDA Setbacks, Coverage & Height — 2 Kanal and Above",
            "For residential plots of 2 Kanal (40 Marla) and above under LDA Building and Zoning Regulations 2019, mandatory setbacks are 20 ft front, 10 to 13 ft rear, and 10 to 13 ft on both sides. Maximum ground coverage is 55%, maximum building height is 45 ft (up to 4 storeys), and basements are permitted.",
            "Lahore Development Authority (LDA)", "city_authority", "Punjab", "Lahore", "", "2 kanal, 40 marla, 4 kanal",
            "setbacks", "LDA Building and Zoning Regulations 2019", "https://lda.gop.pk/", "secondary", "2019"
        ),
        _entry(
            "punjab_lda_far_and_basement",
            "LDA Floor Area Ratio (FAR), Basement Inclusion & Height Exclusions",
            "Under LDA Building and Zoning Regulations 2019, cumulative covered area is governed by Floor Area Ratio (FAR), typically around 1:2.4 to 1:2.8 depending on plot bracket. Residential basements are permitted up to the inner lines of mandatory open spaces with retaining walls/underpinning and minimum 8–9 ft clear height, and basement area is counted toward total FAR. Stair towers (mumty), lift machine rooms, and overhead water tanks are generally excluded from the 38 ft / 45 ft parapet height cap.",
            "Lahore Development Authority (LDA)", "city_authority", "Punjab", "Lahore", "", "all",
            "basement", "LDA Building and Zoning Regulations 2019", "https://lda.gop.pk/", "secondary", "2019"
        ),
        _entry(
            "punjab_lda_approvals_one_window",
            "LDA Plan Approval & One-Window Cell Process",
            "In LDA-controlled zones of Lahore (including Johar Town, Gulberg, Model Town extensions, and LDA-approved private schemes), building plans must be vetted by a PCATP-registered architect (and PEC-registered structural engineer for multi-storey/basement works) and submitted through LDA's One-Window Cell before starting construction, followed by plinth/completion verification.",
            "Lahore Development Authority (LDA)", "city_authority", "Punjab", "Lahore", "Johar Town, Gulberg, Model Town", "all",
            "approvals_process", "LDA Building and Zoning Regulations 2019", "https://lda.gop.pk/", "secondary", "2019"
        ),
        _entry(
            "punjab_rda_rawalpindi_bylaws",
            "RDA Rawalpindi Residential Building & Zoning Framework",
            "The Rawalpindi Development Authority (RDA) enforces residential building plans and private housing scheme approvals across Rawalpindi urban and peri-urban tehsils (including Taxila and Gujar Khan) aligned with Punjab Development Authorities Private Housing Schemes Rules. Submissions require vetted architectural drawings via RDA's One-Window Cell adhering to land-use classification, plot-size setbacks, ground coverage, and height caps.",
            "Rawalpindi Development Authority (RDA)", "city_authority", "Punjab", "Rawalpindi", "", "all",
            "approvals_process", "RDA Building and Zoning Regulations", "https://rda.gop.pk/", "official", "2020"
        ),
        _entry(
            "punjab_fda_mda_gda_setbacks",
            "Punjab Regional Authorities (FDA Faisalabad, MDA Multan, GDA Gujranwala) — Residential Setbacks",
            "Under the harmonized Punjab Housing & Urban Development framework adopted by FDA (Faisalabad), MDA (Multan), and GDA (Gujranwala): small plots (3 to <5 Marla) keep 5–10 ft front building line and 0–3 ft rear with 0 ft sides; medium plots (5 to <10 Marla) keep ~10 ft front and ~5 ft rear; 10 Marla to 1 Kanal keep 10–15 ft front, 5–7 ft rear, and 5 ft side(s); 2 Kanal+ require 20 ft front, 10 ft rear, and 10 ft on both sides.",
            "FDA / MDA / GDA (Punjab Development Authorities)", "city_authority", "Punjab", "Faisalabad, Multan, Gujranwala, Bahawalpur", "", "3 marla, 5 marla, 10 marla, 1 kanal, 2 kanal",
            "setbacks", "FDA / MDA / GDA Building & Zoning Regulations", "https://fda.gov.pk/", "official", "2020",
            "Exact front building line varies by approved scheme layout and road Right-of-Way (ROW)."
        ),
        _entry(
            "punjab_fda_mda_gda_coverage_height",
            "Punjab Regional Authorities (FDA, MDA, GDA) — Ground Coverage & Height",
            "Under FDA, MDA, and GDA residential regulations, maximum ground coverage is 75–80% for 3–5 Marla, ~70% for 10 Marla, and 55–65% for 1 Kanal and above. On roads with ROW up to 25 ft, maximum residential height is capped at 38 ft (11.58 m) from road crown to top of parapet wall (typically G+2/G+3) with minimum 9 ft 6 in clear floor-to-ceiling height; mumty, lift machine rooms, and overhead water tanks are excluded up to dimensional limits.",
            "FDA / MDA / GDA (Punjab Development Authorities)", "city_authority", "Punjab", "Faisalabad, Multan, Gujranwala, Bahawalpur", "", "all",
            "height_storeys", "FDA Building & Zoning Regulations", "https://fda.gov.pk/", "official", "2020"
        ),
    ])

    # =========================================================================
    # 2. ISLAMABAD (CDA) & NATIONAL BUILDING CODES (BCP / PEC)
    # =========================================================================
    rows.extend([
        _entry(
            "ict_cda_25x50_5marla",
            "CDA Islamabad Setbacks & Coverage — 25x50 ft (~5 Marla)",
            "Under CDA Islamabad Residential Sectors Building Control Regulations (Schedule-1), 25x50 ft plots (~5 Marla / 139 sq yd) are terraced/attached houses with 5 ft front setback, 5 ft rear setback, and 0 ft side setbacks (shared party walls on both sides). Maximum ground coverage is 75–80% (~1,000 sq ft footprint), permitting Ground + First Floor + Mumty.",
            "Capital Development Authority (CDA)", "federal", "Islamabad Capital Territory", "Islamabad", "CDA Sectors", "25x50, 5 marla",
            "setbacks", "CDA Islamabad Residential Sectors Zoning Regulations", "https://www.cda.gov.pk/", "secondary", "2020"
        ),
        _entry(
            "ict_cda_30x60_8marla",
            "CDA Islamabad Setbacks & Coverage — 30x60 ft (~7–8 Marla)",
            "Under CDA Islamabad Building Control Regulations, 30x60 ft plots (~7–8 Marla) are semi-detached or terraced depending on sector layout, with 8 ft front setback, 6 ft rear setback, and 4 ft on one side (if semi-detached) or 0 ft (if terraced). Maximum ground coverage is 70–75%, permitting Ground + First Floor + Mumty.",
            "Capital Development Authority (CDA)", "federal", "Islamabad Capital Territory", "Islamabad", "CDA Sectors", "30x60, 7 marla, 8 marla",
            "setbacks", "CDA Islamabad Residential Sectors Zoning Regulations", "https://www.cda.gov.pk/", "secondary", "2020"
        ),
        _entry(
            "ict_cda_35x70_10marla",
            "CDA Islamabad Setbacks & Coverage — 35x70 ft (10 Marla)",
            "Under CDA Islamabad Building Control Regulations, 35x70 ft plots (10 Marla / 272 sq yd) are detached or semi-detached with 10 ft front setback, 5–6 ft rear setback, and 5 ft open side passage on one or both sides depending on sector category. Maximum ground coverage is 65–70% (~1,650–1,750 sq ft ground footprint), permitting Ground + First Floor + Mumty.",
            "Capital Development Authority (CDA)", "federal", "Islamabad Capital Territory", "Islamabad", "CDA Sectors", "35x70, 10 marla",
            "setbacks", "CDA Islamabad Residential Sectors Zoning Regulations", "https://www.cda.gov.pk/", "secondary", "2020"
        ),
        _entry(
            "ict_cda_50x90_1kanal",
            "CDA Islamabad Setbacks & Coverage — 50x90 ft (1 Kanal)",
            "Under CDA Islamabad Building Control Regulations, 50x90 ft plots (1 Kanal / 500 sq yd) are detached bungalows with 15 ft front setback, 8–10 ft rear setback, and 5 ft clear open-to-sky setbacks on both sides. Maximum ground coverage is 55–60% (~2,400–2,600 sq ft buildable ground footprint), permitting Ground + First Floor + Mumty.",
            "Capital Development Authority (CDA)", "federal", "Islamabad Capital Territory", "Islamabad", "CDA Sectors", "50x90, 1 kanal, 500 sq yd",
            "setbacks", "CDA Islamabad Residential Sectors Zoning Regulations", "https://www.cda.gov.pk/", "secondary", "2020"
        ),
        _entry(
            "ict_cda_height_and_mumty",
            "CDA Islamabad Storeys, Height & Mumty Width Cap",
            "CDA residential bylaws strictly cap standard residential houses at 2 storeys (Ground + First Floor) plus a rooftop stair tower (Mumty), with overall height from road crown to top of mumty slab generally around 35–38 ft. Mumty width facing the front road cannot exceed 1/3rd of plot width for detached houses and 1/2 of plot width for terraced houses.",
            "Capital Development Authority (CDA)", "federal", "Islamabad Capital Territory", "Islamabad", "CDA Sectors", "all",
            "mumty_roof", "CDA Building Control Regulations", "https://www.cda.gov.pk/", "official", "2020"
        ),
        _entry(
            "ict_cda_basement_rules",
            "CDA Islamabad Residential Basement, Neighbor NOC & Guarantee",
            "Under CDA regulations, a single basement is permitted under the plinth/footprint with a minimum clear ceiling height of 8 ft and is generally excluded from FAR if used for utility/storage/parking without creating a 3-storey street facade. Excavating a basement—especially on terraced 25x50 plots—requires a Neighbor NOC, PEC-registered structural stability certification, and a security bank guarantee to CDA.",
            "Capital Development Authority (CDA)", "federal", "Islamabad Capital Territory", "Islamabad", "CDA Sectors", "all",
            "basement", "CDA Building Control Regulations", "https://www.cda.gov.pk/", "secondary", "2020"
        ),
        _entry(
            "nat_bcp_2021_seismic_zones",
            "Building Code of Pakistan 2021 (BCP-2021) — Seismic Zones & Structural Loads",
            "The Building Code of Pakistan 2021 (BCP-2021), published by PEC in collaboration with ICC (superseding BCP-SP 2007), establishes mandatory earthquake, wind, snow, and rain load criteria across 150+ districts divided into Seismic Zones 1 (very low) through 4 (very high) with mapped spectral accelerations (Ss, S1). Key urban seismic levels: Zone 4 (Quetta, Muzaffarabad, Galiyat/Northern areas), Zone 2B (Islamabad, Rawalpindi, Peshawar, Karachi), Zone 2A (Lahore, Faisalabad, Multan). Includes flood-resistant construction and seismic retrofitting appendices.",
            "Pakistan Engineering Council (PEC) — Building Code of Pakistan", "federal", "national", "all", "", "all",
            "seismic_structural", "Building Code of Pakistan 2021 (BCP-2021)", "https://www.pec.org.pk/", "official", "2021"
        ),
        _entry(
            "nat_bcp_2016_fire_safety",
            "Building Code of Pakistan — Fire Safety Provisions 2016",
            "Developed by PEC and NDMA and benchmarked against NFPA 1, the Building Code of Pakistan Fire Safety Provisions 2016 (cross-referenced directly in BCP-2021) mandate properly dimensioned Means of Egress (safe stairways, unobstructed exit corridors, fire-rated doors where applicable), smoke/heat detection, and active/passive fire protection. For multi-storey residential homes, continuous enclosed/accessible stairs to the roof and clear 3 ft minimum egress doorways are key life-safety practices.",
            "Pakistan Engineering Council (PEC) / NDMA", "federal", "national", "all", "", "all",
            "fire_safety", "Building Code of Pakistan Fire Safety Provisions 2016", "https://www.pec.org.pk/", "official", "2016"
        ),
        _entry(
            "nat_bcp_energy_climate",
            "Building Code of Pakistan — Energy Efficiency & Passive Climate Design",
            "National energy provisions and Pakistani residential climate practice emphasize passive thermal comfort: orienting habitable bedrooms and living rooms away from harsh west afternoon sun (or buffering the west facade with stairs, baths, stores, or deep overhangs/louvers), providing cross-ventilation via Open-To-Sky (OTS) shafts, roof thermal insulation (tile/foam/khaprail), and solar-ready flat roofs.",
            "Pakistan Engineering Council (PEC) / ENERCON", "federal", "national", "all", "", "all",
            "energy_green", "Building Code of Pakistan Energy Provisions", "https://www.pec.org.pk/", "secondary", "2011"
        ),
    ])

    # =========================================================================
    # 3. SINDH (SBCA KARACHI KBTPR 2002, DHA KARACHI / CBC, KDA, BAHRIA KARACHI)
    # =========================================================================
    rows.extend([
        _entry(
            "sindh_sbca_120sqyd",
            "SBCA Karachi (KBTPR 2002) — 120 Sq Yd Plots",
            "Under the Karachi Building & Town Planning Regulations 2002 (SBCA), 120 sq yd residential plots (Category I row houses) allow 70–75% maximum ground coverage (25–30% open space), 0 ft side setbacks (attached row walls), minimal front/rear Compulsory Open Spaces (~3 ft rear if not abutting a back lane; plots under 119 sq yd with back lanes are often exempt from rear COS). In older Karachi localities (Gulshan-e-Iqbal, North Nazimabad, Gulberg, Jamshed Town, Liaquatabad), 120 sq yd plots are capped at Ground + 2 floors.",
            "Sindh Building Control Authority (SBCA)", "provincial", "Sindh", "Karachi", "KDA Schemes, Gulshan-e-Iqbal, North Nazimabad, PECHS", "120 sq yd, 5 marla",
            "setbacks", "Karachi Building & Town Planning Regulations 2002 (KBTPR)", "https://sbca.gos.pk/", "secondary", "2002"
        ),
        _entry(
            "sindh_sbca_240sqyd",
            "SBCA Karachi (KBTPR 2002) — 240 Sq Yd Plots",
            "Under SBCA KBTPR 2002, 240 sq yd residential plots allow 65–70% maximum ground coverage, 5–8 ft front setback (accommodating car porch/lawn), 3–5 ft rear setback, and 0 ft on one side (semi-detached/row) or a nominal side passage depending on KDA/society lease conditions.",
            "Sindh Building Control Authority (SBCA)", "provincial", "Sindh", "Karachi", "KDA Schemes, Scheme 33, PECHS", "240 sq yd, 250 sq yd, 10 marla",
            "setbacks", "Karachi Building & Town Planning Regulations 2002 (KBTPR)", "https://sbca.gos.pk/", "secondary", "2002"
        ),
        _entry(
            "sindh_sbca_400sqyd_basement",
            "SBCA Karachi (KBTPR 2002) — 400 Sq Yd Plots, Basements & Licensing",
            "Under SBCA KBTPR 2002, 400 sq yd residential plots allow 60–65% ground coverage, 8–10 ft front setback, ~5 ft rear setback, and 3–5 ft side setback on at least one side for light/ventilation. Basements are explicitly permissible starting at the 400 sq yd threshold (with max plinth height 2 ft 6 in). Plots exceeding 400 sq yd mandatorily require both a licensed Architect and a Structural Engineer for SBCA plan submission.",
            "Sindh Building Control Authority (SBCA)", "provincial", "Sindh", "Karachi", "KDA Schemes, PECHS", "400 sq yd",
            "basement", "Karachi Building & Town Planning Regulations 2002 (KBTPR)", "https://sbca.gos.pk/", "secondary", "2002"
        ),
        _entry(
            "sindh_sbca_500sqyd_corner",
            "SBCA Karachi (KBTPR 2002) — 500 Sq Yd Plots & Corner Plot Rule",
            "Under SBCA KBTPR 2002, 500 sq yd detached bungalows allow 50–60% ground coverage, 10–15 ft front setback, 5–8 ft rear setback, and 5 ft side setbacks on both sides. Corner residential plots carry distinct open-space conditions on the side facing the intersecting road, requiring wider street-side clearance.",
            "Sindh Building Control Authority (SBCA)", "provincial", "Sindh", "Karachi", "KDA Schemes, PECHS", "500 sq yd, 1 kanal",
            "setbacks", "Karachi Building & Town Planning Regulations 2002 (KBTPR)", "https://sbca.gos.pk/", "secondary", "2002"
        ),
        _entry(
            "sindh_dha_karachi_cbc_coverage",
            "DHA Karachi & Clifton Cantonment Board (CBC) — Ground Coverage & Floors",
            "In DHA Karachi (Phases I–VIII), building plans are scrutinized by DHA Building Control and legally sanctioned by Clifton Cantonment Board (CBC). Standard residential structures permit Basement + Ground + 1 Upper Floor (G+1). Maximum ground coverage by plot size: up to 200 sq yd = 90%; 201–400 sq yd (e.g. 300 sq yd) = 75%; 401–700 sq yd (e.g. 500 sq yd) = 65%; 701 sq yd and above (e.g. 1,000 sq yd) = 50% (PEC/PCATP professionals mandatory).",
            "DHA Karachi / Clifton Cantonment Board (CBC)", "cantonment", "Sindh", "Karachi", "DHA Karachi", "100 sq yd, 200 sq yd, 300 sq yd, 500 sq yd, 1000 sq yd",
            "ground_coverage", "DHA Karachi / CBC Building Control Regulations", "https://www.dhakarachi.org/", "secondary", "2022"
        ),
        _entry(
            "sindh_dha_karachi_cbc_setbacks",
            "DHA Karachi & CBC — Setbacks (Compulsory Open Spaces)",
            "Standard DHA Karachi / CBC residential setbacks: 100–200 sq yd have minimal front/zero-line sides with min 10x14 ft car porch; 300 sq yd keep ~10–12 ft front, ~5 ft rear, and 3 ft on one side; 500 sq yd keep ~15 ft front, 5–7.5 ft rear, and 3–5 ft on both sides; 1,000 sq yd+ keep 15–20 ft front, 10 ft rear, and 5 ft+ on both sides (fully detached).",
            "DHA Karachi / Clifton Cantonment Board (CBC)", "cantonment", "Sindh", "Karachi", "DHA Karachi", "100 sq yd, 200 sq yd, 300 sq yd, 500 sq yd, 1000 sq yd",
            "setbacks", "DHA Karachi / CBC Building Control Regulations", "https://www.dhakarachi.org/", "secondary", "2022"
        ),
        _entry(
            "sindh_dha_karachi_cbc_height_basement",
            "DHA Karachi & CBC — Height Cap, Stairs & Basement Rules",
            "In DHA Karachi / CBC, main residential building height from plinth top to parapet is capped at 32–33 ft, and overall height including stair mumty and overhead water tank is capped at 45 ft. Staircase risers cannot exceed 7 inches. Basements require a Basement Indemnity Bond, soil investigation report, ACI structural vetting, and basement ceiling may not project more than 4 ft above the adjoining street crown.",
            "DHA Karachi / Clifton Cantonment Board (CBC)", "cantonment", "Sindh", "Karachi", "DHA Karachi", "all",
            "height_storeys", "DHA Karachi / CBC Building Control Regulations", "https://www.dhakarachi.org/", "secondary", "2022"
        ),
    ])

    # =========================================================================
    # 4. KP, BALOCHISTAN, GILGIT-BALTISTAN & AJK
    # =========================================================================
    rows.extend([
        _entry(
            "kp_pda_peshawar_bylaws",
            "PDA Peshawar & Hayatabad Building Control Regulations",
            "The Peshawar Development Authority (PDA) regulates urban residential and commercial construction across Peshawar, Hayatabad Township, and Regi Model Town under PDA Building Control Regulations, enforcing plot-size setbacks, ground coverage limits, commercialization fees, and seismic compliance (Peshawar is Seismic Zone 2B under BCP-2021).",
            "Peshawar Development Authority (PDA)", "city_authority", "Khyber Pakhtunkhwa", "Peshawar", "Hayatabad, Regi Model Town", "all",
            "approvals_process", "PDA Building Control Regulations", "https://pda.gkp.pk/", "official", "2021"
        ),
        _entry(
            "kp_dha_peshawar_bylaws",
            "DHA Peshawar Residential Bylaws — Setbacks, Coverage, Height & Solar",
            "Under DHA Peshawar Building Control Regulations: 5 Marla plots keep ~5 ft front, 3–5 ft rear, 3 ft side (75–85% coverage for up to 6–9 Marla); 10 Marla keep ~10 ft front, 7 ft rear, 5 ft side; 1 Kanal keep ~15 ft front, 5–10 ft rear (recent amendments relaxed rear to 5 ft), 5–7 ft sides. Permits G+1 or G+2 plus single basement (8.5–10 ft clear height, mandatory geotech/soil test and retaining walls). Rooftop solar panels must keep a low profile and not breach height codes.",
            "DHA Peshawar", "society", "Khyber Pakhtunkhwa", "Peshawar", "DHA Peshawar", "5 marla, 10 marla, 1 kanal",
            "setbacks", "DHA Peshawar Building Control Regulations", "https://www.dhapeshawar.org/", "official", "2023"
        ),
        _entry(
            "kp_gda_galiyat_hill_bylaws",
            "Galiyat Development Authority (GDA) — Abbottabad / Hill Area Bylaws",
            "In the Galiyat hill stations (Abbottabad, Nathia Gali, Ayubia, Donga Gali), GDA Building Control Regulations cap maximum height at 5 floors, mandate designs following natural hill contours, prohibit excavation below solid bedrock to prevent landslides, require 5–12+ ft setbacks and minimum ~2 ft storm-water plinths, and encourage lightweight/eco-friendly structures with pitched snow-shedding roofs.",
            "Galiyat Development Authority (GDA)", "provincial", "Khyber Pakhtunkhwa", "Abbottabad, Galiyat, Nathia Gali", "", "all",
            "height_storeys", "Galiyat Building Control Regulations", "https://gda.kp.gov.pk/", "secondary", "2024"
        ),
        _entry(
            "balochistan_qda_quetta_seismic",
            "QDA Quetta & Balochistan — Seismic Zone 4 & Mandatory Soil Testing",
            "Under the Quetta Development Authority (QDA) Ordinance and Balochistan building bylaws, Quetta falls in Seismic Zone 4 (Very High Seismicity). QDA enforces strict height ceilings, mandatory geotechnical soil testing reports, PEC-certified earthquake-resistant structural drawings (BCP-2021), and adequate on-site parking/setbacks.",
            "Quetta Development Authority (QDA)", "city_authority", "Balochistan", "Quetta", "", "all",
            "seismic_structural", "QDA Building Regulations & BCP-2021", "https://qda.gob.pk/", "official", "2021"
        ),
        _entry(
            "ajk_gb_erra_seismic_rules",
            "AJK (Muzaffarabad) & Gilgit-Baltistan — ERRA & Seismic Zone 4 Residential Rules",
            "Under the AJK Building Control Ordinance, Development Authority Muzaffarabad (DAM), and post-2005 ERRA earthquake reconstruction guidelines, Muzaffarabad and northern GB/AJK valleys are Seismic Zone 4 (PGA >= 0.40g). Unreinforced masonry without bands is heavily restricted; residential buildings require continuous RCC plinth, lintel, and roof tie-bands, ductile RC frame detailing with closely spaced closed stirrups, step-foundations on sloped terrain, and Grade 40/60 deformed steel.",
            "Development Authority Muzaffarabad (DAM) / ERRA", "provincial", "Azad Jammu and Kashmir", "Muzaffarabad, Gilgit, Skardu", "", "all",
            "seismic_structural", "AJK Building Control Ordinance & ERRA Guidelines", "https://dam.gok.pk/", "official", "2021"
        ),
    ])

    # =========================================================================
    # 5. MAJOR PRIVATE & DEFENCE SOCIETIES (DHA LAHORE/MULTAN/ISLAMABAD, BAHRIA, B-17, LAKE CITY, WAPDA, ASKARI)
    # =========================================================================
    rows.extend([
        _entry(
            "punjab_dha_lahore_setbacks",
            "DHA Lahore Setbacks — 5 Marla, 10 Marla, 1 Kanal & 2 Kanal",
            "Under DHA Lahore Construction & Development Regulations (all phases, incorporating boundary wall thickness): 5 Marla = 5 ft front, 3 ft rear, 3 ft one side; 10 Marla = 10 ft 9 in front, 5 ft 4.5 in rear, 5 ft 4.5 in one side; 1 Kanal = 15 ft 9 in front, 5 ft 4.5 in rear, 5 ft 4.5 in both sides; 2 Kanal = 15 ft 9 in (or 20 ft 9 in on wider avenues) front, 8 ft 4.5 in rear, 5 ft 4.5 in both sides.",
            "DHA Lahore", "society", "Punjab", "Lahore", "DHA Lahore", "5 marla, 10 marla, 1 kanal, 2 kanal",
            "setbacks", "DHA Lahore Construction & Development Regulations", "https://dhalahore.org/", "secondary", "2023"
        ),
        _entry(
            "punjab_dha_lahore_height_coverage_basement",
            "DHA Lahore Height, Storeys, First-Floor Coverage & Basement",
            "DHA Lahore caps total residential height at 39 ft from road crown and permits Basement + Ground + First Floor + Mumty (no habitable 2nd floor). Clear ceiling height is 9.5 ft min to 18 ft max. First-floor coverage is up to 100% of ground floor for 5 Marla, and 75–82% of ground floor for 10 Marla, 1 Kanal, and 2 Kanal. Single-storey basements are allowed (9–14 ft clear height). Swimming pools are permitted only on 1 Kanal and larger plots.",
            "DHA Lahore", "society", "Punjab", "Lahore", "DHA Lahore", "5 marla, 10 marla, 1 kanal, 2 kanal",
            "height_storeys", "DHA Lahore Construction & Development Regulations", "https://dhalahore.org/", "secondary", "2023"
        ),
        _entry(
            "punjab_dha_lahore_boundary_mumty_porch",
            "DHA Lahore Boundary Wall, Mumty Area & Car Porch Rules",
            "In DHA Lahore, boundary walls are capped at 7 ft from road/plinth level (an additional 2 ft security grill/electric fence requires immediate neighbor NOC, max 9 ft total). Mumty area is capped at 175 sq ft for 10 Marla and below, and 300 sq ft for 1–2 Kanal, with compulsory roof access. Car porches need min 9 ft clear height (not exceeding GF slab), typical 12–18 ft depth, and 1 entrance gate on regular plots (up to 2 on corner plots).",
            "DHA Lahore", "society", "Punjab", "Lahore", "DHA Lahore", "all",
            "boundary_wall", "DHA Lahore Construction & Development Regulations", "https://dhalahore.org/", "secondary", "2023"
        ),
        _entry(
            "ict_dha_islamabad_rawalpindi_bylaws",
            "DHA Islamabad-Rawalpindi (DHAI-R) Residential Bylaws",
            "DHA Islamabad-Rawalpindi enforces plot-category setbacks (typically 10–15 ft front, 5–7 ft rear and sides for 10 Marla/1 Kanal), 65–75% ground coverage depending on category, Ground + 2 Floors max (~35–40 ft overall height + mumty), and single basement up to allowable ground footprint (9–10 ft clear height with waterproofing and soil/structural vetting). No habitable rooms, kitchens, or baths are allowed in Compulsory Open Spaces.",
            "DHA Islamabad-Rawalpindi (DHAI-R)", "society", "Islamabad Capital Territory", "Islamabad, Rawalpindi", "DHA Islamabad, DHA Rawalpindi", "5 marla, 10 marla, 1 kanal",
            "setbacks", "DHAI-R Building Control Regulations", "https://www.dhai-r.com.pk/", "official", "2023"
        ),
        _entry(
            "punjab_dha_multan_bylaws",
            "DHA Multan (DHAM) — Heights, Plinth, Parapet & Basement Standards",
            "DHA Multan Construction & Development Regulations specify: plinth height 1.5 ft min to 4 ft max from road crown; Ground Floor clear height 9 ft 6 in to 14 ft; First Floor clear height 9 ft 6 in to 12 ft; max main roof slab height 35 ft (40 ft including mumty/lift); parapet wall 4–5 ft (up to 7 ft on shared side of attached houses). Basements require 8 ft 6 in to 10 ft clear height, 9-inch RCC walls with waterproofing, dewatering plan, and indemnity bond.",
            "DHA Multan", "society", "Punjab", "Multan", "DHA Multan", "5 marla, 10 marla, 1 kanal, 2 kanal",
            "height_storeys", "DHA Multan Construction & Development Regulations", "https://www.dhamultan.org/", "official", "2023"
        ),
        _entry(
            "nat_bahria_town_5marla_125sqyd",
            "Bahria Town (Lahore, Rawalpindi/Islamabad, Karachi) — 5 Marla / 125 Sq Yd",
            "Under Bahria Town Building Control Regulations, 5 Marla (25x45 ft or 30x50 ft) / 125 sq yd plots require 5 ft front setback, 5 ft rear setback, and 0 ft sides (attached/single-side open; corner plots have dual setbacks). Maximum ground coverage is 75–80%, with first-floor coverage 75–100% depending on phase SOP.",
            "Bahria Town Building Control Department", "society", "national", "Lahore, Rawalpindi, Islamabad, Karachi", "Bahria Town, Bahria Orchard", "5 marla, 125 sq yd",
            "setbacks", "Bahria Town Building Control Regulations", "https://bahriatownbcd.com/", "official", "2023"
        ),
        _entry(
            "nat_bahria_town_10marla_250sqyd",
            "Bahria Town (Lahore, Rawalpindi/Islamabad, Karachi) — 10 Marla / 250 Sq Yd",
            "Under Bahria Town Building Control Regulations, 10 Marla (35x65 ft or 30x75 ft) / 250 sq yd plots require 10 ft front setback, 7 ft rear setback, and 5 ft on at least one side. Maximum ground coverage is 70%, and first-floor coverage is approximately 75% of ground floor area with required ventilation cut-outs.",
            "Bahria Town Building Control Department", "society", "national", "Lahore, Rawalpindi, Islamabad, Karachi", "Bahria Town", "10 marla, 250 sq yd",
            "setbacks", "Bahria Town Building Control Regulations", "https://bahriatownbcd.com/", "official", "2023"
        ),
        _entry(
            "nat_bahria_town_1kanal_500sqyd",
            "Bahria Town (Lahore, Rawalpindi/Islamabad, Karachi) — 1 Kanal / 500 Sq Yd",
            "Under Bahria Town Building Control Regulations, 1 Kanal (50x90 ft or 45x100 ft) / 500 sq yd plots are strictly detached structures requiring 10–15 ft front setback, 7–10 ft rear setback, and 5 ft on both sides. Maximum ground coverage is 50–60%, with proportional upper-floor setback/terrace articulation.",
            "Bahria Town Building Control Department", "society", "national", "Lahore, Rawalpindi, Islamabad, Karachi", "Bahria Town", "1 kanal, 500 sq yd",
            "setbacks", "Bahria Town Building Control Regulations", "https://bahriatownbcd.com/", "official", "2023"
        ),
        _entry(
            "nat_bahria_town_height_color_approvals",
            "Bahria Town — Height, Clear Ceiling, Boundary Wall, Ramp & Color Approval",
            "Across Bahria Town projects, overall height is generally capped at 38–45 ft (30–35 ft in certain sub-phases), clear ceiling height is 9 ft 6 in to 12 ft per floor, boundary walls are capped at 7 ft (gates must open inwards), and car porch ramps cannot rise more than 8 inches above road level. Owners must obtain an NDC, physical demarcation, map approval, and mandatory exterior paint/facade clearance from Bahria Town's Color Consultancy Wing.",
            "Bahria Town Building Control Department", "society", "national", "Lahore, Rawalpindi, Islamabad, Karachi", "Bahria Town, Bahria Orchard", "all",
            "approvals_process", "Bahria Town Building Control Regulations", "https://bahriatownbcd.com/", "official", "2023"
        ),
        _entry(
            "ict_b17_multi_gardens_bylaws",
            "B-17 Multi Gardens Islamabad (MPCHS) — Setbacks & Coverage",
            "Managed by MPCHS under CDA/RDA-aligned bylaws, B-17 Multi Gardens allows 2 storeys (Ground + First + Mumty) and basements with light/ventilation. Coverage is ~70% (5 Marla), ~65% (10 Marla), ~60% (1 Kanal). CDA-regulated block setbacks: 5 Marla (25x50) = 5 ft front / 5 ft rear; 8 Marla (30x60) = 6 ft front / 5 ft rear; 10 Marla (35x70) = 10 ft front / 7 ft rear; 1 Kanal (50x90) = 15 ft front / 10 ft rear / 5 ft both sides.",
            "MPCHS (B-17 Multi Gardens)", "society", "Islamabad Capital Territory", "Islamabad", "B-17, Multi Gardens", "5 marla, 8 marla, 10 marla, 1 kanal",
            "setbacks", "MPCHS B-17 Building Regulations", "https://mpchs.com/", "secondary", "2022"
        ),
        _entry(
            "punjab_lake_city_lahore_bylaws",
            "Lake City Lahore Residential Bylaws",
            "Lake City Lahore is an LDA-approved society managed by its own Building Control Directorate. It permits 2 main habitable floors plus mumty, requires mandatory front/rear setbacks scaling from 5 to 15+ ft by plot size (with side passages on 10 Marla and 1–2 Kanal plots), and requires society architectural vetting prior to construction.",
            "Lake City Building Control Directorate", "society", "Punjab", "Lahore", "Lake City", "5 marla, 10 marla, 1 kanal, 2 kanal",
            "setbacks", "Lake City Lahore Building Control Guidelines", "https://lakecitylahore.com/", "secondary", "2022"
        ),
        _entry(
            "punjab_wapda_town_lahore_bylaws",
            "Wapda Town Lahore Residential Bylaws (10 Marla Example)",
            "Wapda Town Lahore (Phases 1 & 2) aligns with Lahore LDA/MCL residential standards. Typical 10 Marla setbacks are ~10 ft front (allowing car porch design), ~7 ft rear (often permitting a compact 7x7 ft service bath/ventilation zone depending on phase), and ~5 ft side setback, with 65–70% ground coverage.",
            "Wapda Town / LDA Lahore", "society", "Punjab", "Lahore", "Wapda Town", "5 marla, 10 marla, 1 kanal",
            "setbacks", "Wapda Town Lahore Building Guidelines", "https://lda.gop.pk/", "secondary", "2022"
        ),
        _entry(
            "punjab_askari_housing_bylaws",
            "Askari Housing Schemes (e.g. Askari-10 Lahore) Residential Bylaws",
            "Askari housing schemes strictly enforce residential uniformity: typical maximum total height is 37 ft 6 in to 40 ft; for 10 Marla plots, setbacks are minimum 8 ft front, 3–5 ft rear, and ~5 ft on the open side, with ~70% ground coverage. Unauthorized room extensions into mandatory setbacks are strictly prohibited and block completion certificates.",
            "Askari Housing Directorate", "society", "Punjab", "Lahore, Rawalpindi, Islamabad, Karachi", "Askari", "5 marla, 10 marla, 1 kanal",
            "setbacks", "Askari Housing Construction Bylaws", "https://fgeha.gov.pk/", "secondary", "2022"
        ),
    ])

    # =========================================================================
    # 6. PAKISTANI ARCHITECTURAL PLANNING & CLIMATE GUIDANCE (PLANNER BRAIN)
    # =========================================================================
    rows.extend([
        _entry(
            "plan_guide_pakistani_privacy_zoning",
            "Pakistani Residential Privacy Zoning (Public vs Family Zones)",
            "Standard Pakistani residential architecture separates guest/public reception from private family living. Place the Drawing Room (and optional Powder Room) near the front entrance/car porch with a direct guest entrance so visitors never walk through the family TV Lounge. Keep the TV Lounge central as the family heart connecting the kitchen, dining, and bedrooms, with bedrooms positioned toward the quiet rear or upper floor.",
            "Pakistani Architectural Practice", "federal", "national", "all", "", "all",
            "general_design_guidance", "Pakistani Residential Space Planning Standards", "", "secondary", "2024"
        ),
        _entry(
            "plan_guide_dual_kitchen_wet_stacking",
            "Main Kitchen, Dirty/Grease Kitchen & Vertical Plumbing Stacking",
            "In 10 Marla and 1 Kanal Pakistani homes, pairing an open/show main kitchen with an adjacent enclosed dirty/grease kitchen (with direct exhaust window to a side passage, rear setback, or OTS shaft) keeps cooking odors out of the lounge. Vertically aligning bathrooms and kitchens between Ground and First floors simplifies plumbing shafts, reduces leakage, and saves construction cost.",
            "Pakistani Architectural Practice", "federal", "national", "all", "", "10 marla, 1 kanal, 2 kanal",
            "plumbing_drainage", "Pakistani Residential Space Planning Standards", "", "secondary", "2024"
        ),
        _entry(
            "plan_guide_climate_punjab_plains",
            "Climate Planning — Hot-Dry Plains (Lahore, Multan, Faisalabad, Bahawalpur)",
            "In Punjab's intense summer heat (42–48°C), buffer west- and south-west-facing walls using staircases, bathrooms, wardrobes, or deep recessed balconies/louvers. Provide cross-ventilation via front/rear setbacks or internal Open-To-Sky (OTS) courtyards (minimum 4–5 ft wide) so every bedroom and lounge gets natural daylight and stack-effect airflow.",
            "Pakistani Architectural Practice", "provincial", "Punjab", "Lahore, Multan, Faisalabad, Gujranwala, Bahawalpur", "", "all",
            "general_design_guidance", "Regional Climate-Responsive Design in Pakistan", "", "secondary", "2024"
        ),
        _entry(
            "plan_guide_climate_karachi_coastal",
            "Climate Planning — Coastal Humid (Karachi & Coastal Sindh)",
            "In Karachi's humid coastal climate, maximizing prevailing southwest sea breeze is the top passive-cooling strategy. Align operable windows and ventilation shafts along the southwest–northeast axis, use covered verandahs/balconies for shaded outdoor living, and avoid dead air pockets in dense 120–240 sq yd row houses by incorporating central or rear OTS lightwells.",
            "Pakistani Architectural Practice", "provincial", "Sindh", "Karachi, Hyderabad", "", "all",
            "general_design_guidance", "Regional Climate-Responsive Design in Pakistan", "", "secondary", "2024"
        ),
        _entry(
            "plan_guide_climate_hills_north",
            "Climate Planning — Cold & Hill Regions (Islamabad, Galiyat, Quetta, AJK, GB)",
            "In Islamabad's cold winters and mountain regions (Galiyat, Abbottabad, Quetta, Muzaffarabad, Gilgit-Baltistan), orient main living areas and master bedrooms toward the south/southeast for winter solar gain, use compact heated volumes with double-glazed windows, and incorporate sloped/pitched roofs or robust waterproofing and storm-water drainage in snow/monsoon zones.",
            "Pakistani Architectural Practice", "federal", "national", "Islamabad, Rawalpindi, Abbottabad, Quetta, Muzaffarabad, Gilgit", "", "all",
            "general_design_guidance", "Regional Climate-Responsive Design in Pakistan", "", "secondary", "2024"
        ),
        _entry(
            "plan_guide_stairs_rental_separation",
            "Staircase Placement — Family Internal vs Independent Rental Portion",
            "In Pakistani double- and triple-storey homes, staircase placement controls family privacy and rental potential. If the client wants to rent out the first floor independently or keep upper-floor traffic separate, place the staircase directly off the front Car Porch / Driveway with its own entrance door. If the home is for a single joint family, placing the stair inside or adjacent to the central TV Lounge creates an open double-height feel and easy family movement.",
            "Pakistani Architectural Practice", "federal", "national", "all", "", "all",
            "stairs", "Pakistani Residential Space Planning Standards", "", "secondary", "2024"
        ),
        _entry(
            "plan_guide_compact_dense_plots",
            "Dense & Small Plot Planning (3 Marla, 5 Marla & High Room-Count Requests)",
            "On compact plots (3–5 Marla) or when a client requests more rooms than typical (e.g. 5 bedrooms on 5 Marla or zero setbacks), maximize buildable efficiency using a central lounge/corridor spine, compact bedrooms (9x10 to 10x12 ft), shared bathrooms (4.5x6.5 ft), and strategically placed internal OTS ventilation shafts (4x5 ft) so every habitable room still receives natural light and ventilation without creating landlocked rooms.",
            "Pakistani Architectural Practice", "federal", "national", "all", "", "3 marla, 5 marla",
            "general_design_guidance", "Compact Urban Housing Design in Pakistan", "", "secondary", "2024"
        ),
        _entry(
            "plan_guide_room_dimensions_practical",
            "Practical Pakistani Residential Room Sizes & Clearances",
            "Typical comfortable room proportions in Pakistan: Master Bedroom 12x14 to 14x16 ft (compact 10x12 ft); Secondary Bedroom 10x12 to 12x14 ft (compact 9x10 ft); Attached Bath 5x7 to 6x8 ft (compact 4.5x6 ft); Powder Room 4x5.5 ft; Kitchen 8x10 to 10x12 ft (compact 6x8 ft); TV Lounge 12x15 to 16x20 ft; Drawing Room 11x14 to 14x16 ft; Car Porch min 10x15 ft for 1 car or 16x18 ft for 2 cars; Stair flight width 3.25–3.5 ft (full U-stair hall ~7x12 to 8x14 ft).",
            "Pakistani Architectural Practice", "federal", "national", "all", "", "all",
            "room_minimums", "Pakistani Residential Space Planning Standards", "", "secondary", "2024"
        ),
    ])

    return rows


def embed_texts(texts: List[str], api_key: str) -> np.ndarray:
    """Batch-embeds texts with Gemini gemini-embedding-001 (768-dim float32, L2-normalized)."""
    url = f"https://generativelanguage.googleapis.com/v1beta/models/{EMBED_MODEL}:batchEmbedContents?key={api_key}"
    all_vecs: List[List[float]] = []
    batch_size = 20
    for start in range(0, len(texts), batch_size):
        chunk = texts[start : start + batch_size]
        requests_payload = [
            {
                "model": f"models/{EMBED_MODEL}",
                "content": {"parts": [{"text": t}]},
                "outputDimensionality": EMBED_DIM,
                "taskType": "RETRIEVAL_DOCUMENT",
            }
            for t in chunk
        ]
        body = json.dumps({"requests": requests_payload}).encode("utf-8")
        req = urllib.request.Request(url, data=body, headers={"Content-Type": "application/json"})
        with urllib.request.urlopen(req, timeout=45) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        for emb in data.get("embeddings", []):
            all_vecs.append(emb["values"])
        print(f"  Embedded {min(start + batch_size, len(texts))}/{len(texts)} entries...")
        if start + batch_size < len(texts):
            time.sleep(0.25)

    arr = np.asarray(all_vecs, dtype=np.float32)
    norms = np.linalg.norm(arr, axis=1, keepdims=True)
    norms = np.where(norms == 0, 1.0, norms)
    return arr / norms


def main() -> None:
    load_dotenv(ROOT / ".env")
    KNOWLEDGE_DIR.mkdir(parents=True, exist_ok=True)

    rows = build_corpus()
    with open(JSONL_PATH, "w", encoding="utf-8") as f:
        for r in rows:
            f.write(json.dumps(r, ensure_ascii=False) + "\n")
    print(f"Wrote {len(rows)} cited rules to {JSONL_PATH}")

    api_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not api_key:
        print("ERROR: GEMINI_API_KEY not found in .env — skipping vector build.", file=sys.stderr)
        sys.exit(1)

    docs = [
        f"{r['title']} | Authority: {r['authority']} | Province: {r['province']} | City: {r['city']} "
        f"| Society: {r['society']} | Plot sizes: {r['plot_sizes']} | Topic: {r['topic']}\n{r['text']}"
        for r in rows
    ]
    vectors = embed_texts(docs, api_key)
    ids = np.asarray([r["id"] for r in rows])
    np.savez_compressed(VECTORS_PATH, ids=ids, vectors=vectors, model=EMBED_MODEL, dim=EMBED_DIM)
    print(f"Saved {vectors.shape} float32 vector index to {VECTORS_PATH} ({VECTORS_PATH.stat().st_size / 1024:.1f} KB)")


if __name__ == "__main__":
    main()
