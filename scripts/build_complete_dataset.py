"""
Phase 2/10: Master Dataset Compiler across Folders (1, 3, 5, 7, 10).
Extracts architectural features, room bounding boxes (box_2d), and spatial zones
using Gemini Multimodal Vision, and compiles them into a single master dataset file:
'dataset/complete_architectural_dataset.json'.
"""

import os
import sys
import json
import time
from typing import Dict, List, Any

# Ensure workspace root is in sys.path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from extraction.gemini_dataset_extractor import GeminiDatasetExtractor

FOLDERS = ["1", "3", "5", "7", "10"]
MASTER_OUTPUT_PATH = "dataset/complete_architectural_dataset.json"
INDIVIDUAL_DIR = "dataset/gemini_extracted"


def save_master(all_records):
    master_dataset = {
        "dataset_name": "Antigravity Architectural Master Dataset",
        "description": "Complete ground-truth floor plan dataset with dimensional, topological, and spatial bounding boxes (box_2d)",
        "folders_covered": FOLDERS,
        "total_plans": len(all_records),
        "plans": all_records
    }
    with open(MASTER_OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(master_dataset, f, indent=2)
    return master_dataset


def build_complete_dataset(images_per_folder: int = 1):
    os.makedirs(INDIVIDUAL_DIR, exist_ok=True)
    os.makedirs("dataset", exist_ok=True)

    all_records = []
    processed_images = set()

    # Ingest already extracted files in INDIVIDUAL_DIR
    if os.path.exists(INDIVIDUAL_DIR):
        for fname in sorted(os.listdir(INDIVIDUAL_DIR)):
            if fname.endswith(".json"):
                try:
                    fpath = os.path.join(INDIVIDUAL_DIR, fname)
                    with open(fpath, "r", encoding="utf-8") as f:
                        rec = json.load(f)
                        all_records.append(rec)
                        if rec.get("source_image"):
                            processed_images.add(rec.get("source_image"))
                        if rec.get("source_path"):
                            processed_images.add(os.path.basename(rec.get("source_path")))
                except Exception as e:
                    pass

    print(f"Loaded {len(all_records)} existing records from individual directory.", flush=True)
    save_master(all_records)

    extractor = GeminiDatasetExtractor()
    valid_exts = (".png", ".jpg", ".jpeg", ".webp")

    for folder in FOLDERS:
        if not os.path.exists(folder):
            continue

        images = [f for f in sorted(os.listdir(folder)) if f.lower().endswith(valid_exts) and "download" not in f.lower()]
        if not images:
            images = [f for f in sorted(os.listdir(folder)) if f.lower().endswith(valid_exts)]

        print(f"\nScanning Folder '{folder}' ({len(images)} images)...", flush=True)

        # Check how many images from this folder are already processed
        folder_done = sum(1 for r in all_records if r.get("folder_category") == folder or r.get("source_path", "").startswith(f"{folder}/"))
        needed = max(0, images_per_folder - folder_done)
        if needed == 0:
            print(f" -> Folder '{folder}' already has {folder_done} processed records. Skipping.", flush=True)
            continue

        for img_name in images:
            if needed <= 0:
                break
            if img_name in processed_images:
                continue

            img_path = os.path.join(folder, img_name)
            print(f" -> [{folder}] Extracting: {img_name}...", flush=True)
            try:
                data = extractor.extract_floor_plan_data(img_path)
                data["folder_category"] = folder
                all_records.append(data)
                processed_images.add(img_name)

                # Save individual JSON
                base_name = os.path.splitext(img_name)[0]
                ind_path = os.path.join(INDIVIDUAL_DIR, f"{folder}_{base_name}_dataset.json")
                with open(ind_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=2)

                # Update master dataset file immediately
                save_master(all_records)
                print(f"    SUCCESS: Extracted {len(data.get('rooms', []))} rooms with box_2d. Master dataset now has {len(all_records)} plans.", flush=True)
                needed -= 1
            except Exception as e:
                print(f"    FAILED for {img_name}: {e}", flush=True)

            time.sleep(1.0)

    save_master(all_records)
    print(f"\nMASTER DATASET COMPLETED! Total plans: {len(all_records)}", flush=True)
    print(f"Saved to: {MASTER_OUTPUT_PATH}", flush=True)
    return all_records


if __name__ == "__main__":
    count = int(sys.argv[1]) if len(sys.argv) > 1 else 1
    build_complete_dataset(images_per_folder=count)
