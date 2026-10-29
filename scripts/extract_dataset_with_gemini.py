"""
Batch Dataset Builder using Gemini Multimodal Vision.
STRICT POLICY:
- Only extracts architectural ground-truth information and creates dataset files.
- NEVER used for floor plan layout generation.
"""

import os
import sys
import argparse
from extraction.gemini_dataset_extractor import GeminiDatasetExtractor

def process_folder(folder_path: str, output_dir: str = "dataset/gemini_extracted"):
    if not os.path.exists(folder_path):
        print(f"[ERROR] Folder not found: {folder_path}")
        return

    extractor = GeminiDatasetExtractor()
    valid_exts = (".png", ".jpg", ".jpeg", ".webp")
    image_files = [f for f in sorted(os.listdir(folder_path)) if f.lower().endswith(valid_exts)]
    
    print(f"Found {len(image_files)} floor plan images in '{folder_path}'")
    os.makedirs(output_dir, exist_ok=True)

    success_count = 0
    for idx, fname in enumerate(image_files, 1):
        img_path = os.path.join(folder_path, fname)
        print(f"[{idx}/{len(image_files)}] Extracting dataset info: {fname}...")
        try:
            out_file = extractor.process_and_save_dataset_file(img_path, output_dir)
            print(f"       -> Saved: {out_file}")
            success_count += 1
        except Exception as e:
            print(f"       -> [ERROR] Failed to extract {fname}: {e}")

    print(f"\nCompleted: {success_count}/{len(image_files)} dataset files created in '{output_dir}'")

def main():
    parser = argparse.ArgumentParser(description="Extract Dataset Files from Floor Plan Images with Gemini")
    parser.add_argument("--folder", type=str, required=True, help="Input folder (e.g. 1, 3, 5, 7, 10)")
    parser.add_argument("--outdir", type=str, default="dataset/gemini_extracted", help="Output directory for dataset JSONs")
    args = parser.parse_args()

    process_folder(args.folder, args.outdir)

if __name__ == "__main__":
    main()
