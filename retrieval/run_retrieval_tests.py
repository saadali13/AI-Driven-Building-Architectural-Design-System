#!/usr/bin/env python3
"""
retrieval/run_retrieval_tests.py - Benchmark 5 Diverse Sample Requests

Runs 5 distinct user architectural queries:
1. 5 Marla (25x45, 3-bed, 3-bath, 2-floor)
2. 10 Marla (35x65, 4-bed, 4-bath, 2-floor)
3. 1 Kanal (50x90, 5-bed, 5-bath, 2-floor)
4. 3-Bed Compact Family Residence (3-bed, 2-bath, 1-floor)
5. 5-Bed Luxury Villa with Servant Quarter (50x90, 5-bed, 5-bath, servant quarter)

Outputs results to results/retrieval_tests.md with top 3 hits per request.
"""

import os
import sys
import json

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from retrieval.search import search
OUTPUT_MD = os.path.join(PROJECT_ROOT, "results", "retrieval_tests.md")

TEST_CASES = [
    {
        "id": "REQ-1",
        "name": "5 Marla Standard Residential",
        "requirements": {
            "prompt": "5 Marla modern house (25x45) with 3 bedrooms, 3 bathrooms, 2 floors",
            "marla": 5.0,
            "plot_width": 25.0,
            "plot_length": 45.0,
            "bedrooms": 3,
            "bathrooms": 3,
            "floors": 2
        }
    },
    {
        "id": "REQ-2",
        "name": "10 Marla Executive Villa",
        "requirements": {
            "prompt": "10 Marla Spanish villa (35x65) with 4 bedrooms, 4 bathrooms, 2 floors, car porch",
            "marla": 10.0,
            "plot_width": 35.0,
            "plot_length": 65.0,
            "bedrooms": 4,
            "bathrooms": 4,
            "floors": 2
        }
    },
    {
        "id": "REQ-3",
        "name": "1 Kanal Luxury Estate",
        "requirements": {
            "prompt": "1 Kanal contemporary residence (50x90) with 5 bedrooms, 5 bathrooms, 2 floors, lawn and double garage",
            "marla": 20.0,
            "plot_width": 50.0,
            "plot_length": 90.0,
            "bedrooms": 5,
            "bathrooms": 5,
            "floors": 2
        }
    },
    {
        "id": "REQ-4",
        "name": "Compact 3-Bed Single-Storey",
        "requirements": {
            "prompt": "Compact single storey 3 bedroom house with 2 bathrooms and kitchen",
            "bedrooms": 3,
            "bathrooms": 2,
            "floors": 1
        }
    },
    {
        "id": "REQ-5",
        "name": "5-Bed Estate with Servant Quarter",
        "requirements": {
            "prompt": "1 Kanal 5 bedroom luxury house with 5 bathrooms, servant quarter, 2 floors, car porch",
            "marla": 20.0,
            "plot_width": 50.0,
            "plot_length": 90.0,
            "bedrooms": 5,
            "bathrooms": 5,
            "floors": 2,
            "servant": 1
        }
    }
]


def run_tests():
    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    md_lines = [
        "# Architectural Plan Retrieval Benchmark: 5 Diverse Requests\n",
        "Evaluation of nearest-neighbor plan retrieval against verified CV dataset records (Tier A & Tier B prioritized, needs_review penalized).\n"
    ]

    for tc in TEST_CASES:
        req = tc["requirements"]
        hits = search(req, k=3)
        md_lines.append(f"## {tc['id']}: {tc['name']}")
        md_lines.append(f"**User Requirements**: `{req['prompt']}`")
        md_lines.append(f"- Target: Bedrooms: {req.get('bedrooms')}, Bathrooms: {req.get('bathrooms')}, Floors: {req.get('floors', 2)}, Marla: {req.get('marla', 'N/A')}\n")
        md_lines.append("| Rank | Record ID | Tier | Similarity | Plot Size | Matched Features & Explanations | Source Image |")
        md_lines.append("|:---:|:---|:---:|:---:|:---:|:---|:---|")

        for rank, h in enumerate(hits, start=1):
            expl_str = "; ".join(h["explanations"][:4])
            img_path = h.get("image_path") or f"{h['folder']}/{h['image_file']}"
            md_lines.append(
                f"| {rank} | `{h['record_id']}` | **{h['tier']}** | `{h['similarity_pct']}` | {h['plot_dimensions']} | {expl_str} | `file:///{PROJECT_ROOT.replace(chr(92), '/')}/{img_path}` |"
            )
        md_lines.append("\n---\n")

    report_content = "\n".join(md_lines)
    with open(OUTPUT_MD, 'w', encoding='utf-8') as f:
        f.write(report_content)

    print(f"Retrieval tests complete! Saved to {OUTPUT_MD}")
    print(report_content)


if __name__ == "__main__":
    run_tests()
