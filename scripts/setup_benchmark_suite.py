"""
Setup Regression Benchmark Suite.
Selects representative ground-truth plans from categories 1, 3, 5, 7, 10
and organizes them into benchmark/small, benchmark/medium, benchmark/large
for continuous regression validation.
"""

import os
import json
import shutil

BENCHMARK_DIR = "benchmark"
CATEGORIES = {
    "small": ["3", "5"],     # 3 Marla (~650-950 sq ft), 5 Marla (~1100-1550 sq ft)
    "medium": ["7", "10"],   # 7 Marla (~1600-2050 sq ft), 10 Marla (~2350-2900 sq ft)
    "large": ["1"]           # 1 Kanal (~4000-4800 sq ft)
}

def setup_benchmark():
    os.makedirs(BENCHMARK_DIR, exist_ok=True)
    for group in CATEGORIES:
        os.makedirs(os.path.join(BENCHMARK_DIR, group), exist_ok=True)

    with open("dataset_manifest.json", "r", encoding="utf-8") as f:
        manifest = json.load(f)

    # Group entries by category
    by_cat = {}
    for entry in manifest["assets"]:
        cat = entry["category_label"]
        by_cat.setdefault(cat, []).append(entry)

    regression_suite = {
        "description": "Representative Architectural Benchmark Regression Suite",
        "groups": {}
    }

    for group, cats in CATEGORIES.items():
        regression_suite["groups"][group] = {
            "categories": cats,
            "representative_plans": []
        }
        for cat in cats:
            entries = by_cat.get(cat, [])
            valid_entries = [e for e in entries if e.get("is_valid", True)]
            # Take top 3 representative plans per category
            selected = valid_entries[:3]
            for i, sel in enumerate(selected):
                plan_id = f"{cat}_{i+1:03d}"
                # Copy annotation if available
                ann_src = os.path.join("reference_floorplans", "annotations", f"{plan_id}.json")
                ann_dst = os.path.join(BENCHMARK_DIR, group, f"{plan_id}.json")
                if os.path.exists(ann_src):
                    shutil.copyfile(ann_src, ann_dst)
                
                regression_suite["groups"][group]["representative_plans"].append({
                    "plan_id": plan_id,
                    "category": cat,
                    "image_path": sel["file_path"],
                    "dimensions": f"{sel.get('width_px', 0)}x{sel.get('height_px', 0)}",
                    "inferred_plot": sel["inferred_plot_size"],
                    "annotation_file": ann_dst
                })

    suite_manifest = os.path.join(BENCHMARK_DIR, "regression_manifest.json")
    with open(suite_manifest, "w", encoding="utf-8") as f:
        json.dump(regression_suite, f, indent=2)

    print(f"[SUCCESS] Setup benchmark regression suite in '{BENCHMARK_DIR}/'")
    print(f"         Total groups: {len(CATEGORIES)}")
    for g, info in regression_suite["groups"].items():
        print(f"         - {g.upper()}: {len(info['representative_plans'])} representative blueprints")

if __name__ == "__main__":
    setup_benchmark()
