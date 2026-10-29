import os
import glob
import json
import hashlib
import cv2
import numpy as np
from PIL import Image
import imagehash

def main():
    dirs = ['1', '3', '5', '7', '10']
    records = []
    
    for d in dirs:
        if not os.path.exists(d):
            continue
        for fname in sorted(os.listdir(d)):
            if not fname.lower().endswith(('.png', '.jpg', '.jpeg', '.webp', '.tif', '.tiff')):
                continue
            fpath = os.path.join(d, fname)
            fsize = os.path.getsize(fpath)
            
            with open(fpath, 'rb') as f:
                bytes_data = f.read()
                md5_val = hashlib.md5(bytes_data).hexdigest()
                
            try:
                with Image.open(fpath) as pimg:
                    w, h = pimg.size
                    mode = pimg.mode
                    ahash = str(imagehash.average_hash(pimg))
                    dhash = str(imagehash.dhash(pimg))
                    phash = str(imagehash.phash(pimg))
                    
                cv_img = cv2.imread(fpath)
                if cv_img is not None:
                    gray = cv2.cvtColor(cv_img, cv2.COLOR_BGR2GRAY)
                    mean_luma = float(np.mean(gray))
                    std_luma = float(np.std(gray))
                    edges = cv2.Canny(gray, 50, 150)
                    edge_ratio = float(np.count_nonzero(edges) / (w * h))
                    b, g, r = cv2.split(cv_img)
                    color_var = float(np.mean(np.abs(r.astype(float) - g.astype(float)) + np.abs(g.astype(float) - b.astype(float))))
                else:
                    mean_luma, std_luma, edge_ratio, color_var = None, None, None, None
                    
                rec = {
                    'id': f"{d}/{fname}",
                    'folder': d,
                    'filename': fname,
                    'path': fpath.replace('\\', '/'),
                    'size_bytes': fsize,
                    'width': w,
                    'height': h,
                    'aspect_ratio': round(w / h, 3),
                    'megapixels': round((w * h) / 1e6, 3),
                    'mode': mode,
                    'md5': md5_val,
                    'ahash': ahash,
                    'dhash': dhash,
                    'phash': phash,
                    'mean_luma': round(mean_luma, 1) if mean_luma is not None else None,
                    'std_luma': round(std_luma, 1) if std_luma is not None else None,
                    'edge_ratio': round(edge_ratio, 4) if edge_ratio is not None else None,
                    'color_variance': round(color_var, 2) if color_var is not None else None
                }
                records.append(rec)
            except Exception as e:
                print(f"Error reading {fpath}: {e}")

    print(f"Audited {len(records)} images.")

    # Duplicate & near-duplicate detection
    exact_dups = []
    seen_md5 = {}
    for r in records:
        if r['md5'] in seen_md5:
            exact_dups.append({'original': seen_md5[r['md5']], 'duplicate': r['id']})
        else:
            seen_md5[r['md5']] = r['id']

    near_dups = []
    for i in range(len(records)):
        h1 = imagehash.hex_to_hash(records[i]['dhash'])
        for j in range(i + 1, len(records)):
            h2 = imagehash.hex_to_hash(records[j]['dhash'])
            dist = h1 - h2
            if dist <= 3 and records[i]['md5'] != records[j]['md5']:
                near_dups.append({
                    'item1': records[i]['id'],
                    'item2': records[j]['id'],
                    'hamming_distance': int(dist),
                    'res1': [records[i]['width'], records[i]['height']],
                    'res2': [records[j]['width'], records[j]['height']]
                })

    low_res = [r for r in records if r['width'] < 800 or r['height'] < 800]
    high_res = [r for r in records if r['width'] >= 1500 or r['height'] >= 1500]

    audit_summary = {
        'total_images': len(records),
        'unique_exact_count': len(records) - len(exact_dups),
        'folders': {d: len([r for r in records if r['folder'] == d]) for d in dirs},
        'exact_duplicates_count': len(exact_dups),
        'exact_duplicates': exact_dups,
        'near_duplicates_count': len(near_dups),
        'near_duplicates': near_dups,
        'resolutions': {
            'min_width': min(r['width'] for r in records),
            'max_width': max(r['width'] for r in records),
            'min_height': min(r['height'] for r in records),
            'max_height': max(r['height'] for r in records),
            'avg_width': round(float(np.mean([r['width'] for r in records])), 1),
            'avg_height': round(float(np.mean([r['height'] for r in records])), 1),
            'low_res_count': len(low_res),
            'high_res_count': len(high_res)
        },
        'color_distribution': {
            'pure_grayscale_or_bw': len([r for r in records if r['color_variance'] < 2.0]),
            'subtle_tint_or_low_color': len([r for r in records if 2.0 <= r['color_variance'] < 10.0]),
            'full_color_marketing': len([r for r in records if r['color_variance'] >= 10.0])
        },
        'items': records
    }

    os.makedirs('reports', exist_ok=True)
    with open('reports/existing_dataset_audit.json', 'w') as f:
        json.dump(audit_summary, f, indent=2)

    print("Audit summary written to reports/existing_dataset_audit.json")
    print(f"Total: {len(records)}, Exact dups: {len(exact_dups)}, Near dups: {len(near_dups)}")
    print(f"Avg resolution: {audit_summary['resolutions']['avg_width']} x {audit_summary['resolutions']['avg_height']}")
    print(f"Low res (<800px): {len(low_res)}, High res (>=1500px): {len(high_res)}")
    print(f"Color distribution: {audit_summary['color_distribution']}")

if __name__ == '__main__':
    main()
