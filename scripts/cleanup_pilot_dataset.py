"""
Phase 1: Pilot Dataset Cleanup and Stress-Set Isolation.
Quarantines exact duplicates and multi-resolution cross-folder clones.
Organizes clean unique stress images into data/evaluation_only/pilot_stress_187/
with an auditable stress_manifest.json.
"""

import os
import shutil
import json
import hashlib
from PIL import Image
import imagehash
import cv2
import numpy as np

def main():
    source_dirs = ['1', '3', '5', '7', '10']
    base_out = os.path.join('data', 'evaluation_only', 'pilot_stress_187')
    images_out = os.path.join(base_out, 'images')
    quarantine_exact = os.path.join('data', 'quarantine', 'exact_duplicates')
    quarantine_near = os.path.join('data', 'quarantine', 'near_duplicates_downscaled')

    os.makedirs(images_out, exist_ok=True)
    os.makedirs(quarantine_exact, exist_ok=True)
    os.makedirs(quarantine_near, exist_ok=True)

    # Specific known duplicate files from audit
    exact_dup_targets = {
        '1/dc63fcbef5792c11a0630cf42b1b279a (1).jpg': '1/dc63fcbef5792c11a0630cf42b1b279a.jpg',
        '5/56734469ec2d1b6642d46f696542f158 (1).jpg': '5/56734469ec2d1b6642d46f696542f158.jpg'
    }

    # Cross-folder downscaled duplicates: keep the higher-res original, quarantine lower-res clone
    near_dup_lower_res = {
        '10/6a0b981cfe8407c963ab6686608d2cde.jpg': '3/70607f869fb7db58226ecd20e74f185d.jpg',
        '10/cb33831c86d1f16db29ad58bf9e926f3.jpg': '5/62d5c958516588e9756a20568ad5f365.jpg'
    }

    records = []
    quarantined_exact_list = []
    quarantined_near_list = []

    for d in source_dirs:
        if not os.path.exists(d):
            continue
        for fname in sorted(os.listdir(d)):
            if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff')):
                continue
            src_path = os.path.join(d, fname)
            rel_id = f"{d}/{fname}"

            # Check exact duplicates
            if rel_id in exact_dup_targets:
                dest = os.path.join(quarantine_exact, f"{d}_{fname}")
                shutil.copy2(src_path, dest)
                quarantined_exact_list.append({'id': rel_id, 'clone_of': exact_dup_targets[rel_id], 'quarantine_path': dest})
                continue

            # Check near duplicates (lower-res clone)
            if rel_id in near_dup_lower_res:
                dest = os.path.join(quarantine_near, f"{d}_{fname}")
                shutil.copy2(src_path, dest)
                quarantined_near_list.append({'id': rel_id, 'lower_res_clone_of': near_dup_lower_res[rel_id], 'quarantine_path': dest})
                continue

            # Clean active stress image
            dest_name = f"{d}_{fname}"
            dest_path = os.path.join(images_out, dest_name)
            shutil.copy2(src_path, dest_path)

            with Image.open(src_path) as pimg:
                w, h = pimg.size
                dhash_val = str(imagehash.dhash(pimg))

            cv_img = cv2.imread(src_path)
            if cv_img is not None:
                b, g, r = cv2.split(cv_img)
                color_var = float(np.mean(np.abs(r.astype(float) - g.astype(float)) + np.abs(g.astype(float) - b.astype(float))))
                gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                lap_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
            else:
                color_var, lap_var = 0.0, 0.0

            # Categorize stress type
            stress_tags = []
            if w < 800 or h < 800:
                stress_tags.append('low_resolution')
            if color_var >= 10.0:
                stress_tags.append('color_marketing_render')
            elif color_var < 2.0:
                stress_tags.append('monochrome_line_drawing')
            else:
                stress_tags.append('subtle_tint')

            if lap_var > 4000.0:
                stress_tags.append('high_texture_noise')
            if w >= 1200 or h >= 1200:
                stress_tags.append('high_res_drawing')

            records.append({
                'image_id': dest_name,
                'original_source': rel_id,
                'clean_path': dest_path.replace('\\', '/'),
                'width': w,
                'height': h,
                'dhash': dhash_val,
                'color_variance': round(color_var, 2),
                'texture_variance': round(lap_var, 1),
                'stress_categories': stress_tags
            })

    manifest = {
        'total_scanned': sum(len(os.listdir(d)) for d in source_dirs if os.path.exists(d)),
        'clean_unique_count': len(records),
        'quarantined_exact_count': len(quarantined_exact_list),
        'quarantined_near_count': len(quarantined_near_list),
        'quarantined_exact': quarantined_exact_list,
        'quarantined_near': quarantined_near_list,
        'stress_distribution': {
            'low_resolution': len([r for r in records if 'low_resolution' in r['stress_categories']]),
            'color_marketing_render': len([r for r in records if 'color_marketing_render' in r['stress_categories']]),
            'monochrome_line_drawing': len([r for r in records if 'monochrome_line_drawing' in r['stress_categories']]),
            'high_texture_noise': len([r for r in records if 'high_texture_noise' in r['stress_categories']]),
            'high_res_drawing': len([r for r in records if 'high_res_drawing' in r['stress_categories']])
        },
        'items': records
    }

    manifest_path = os.path.join(base_out, 'stress_manifest.json')
    with open(manifest_path, 'w', encoding='utf-8') as f:
        json.dump(manifest, f, indent=2)

    print(f"Phase 1 Complete:")
    print(f"  Clean unique images: {len(records)}")
    print(f"  Quarantined exact dups: {len(quarantined_exact_list)}")
    print(f"  Quarantined near dups: {len(quarantined_near_list)}")
    print(f"  Stress distribution: {manifest['stress_distribution']}")
    print(f"  Manifest written to: {manifest_path}")

if __name__ == '__main__':
    main()
