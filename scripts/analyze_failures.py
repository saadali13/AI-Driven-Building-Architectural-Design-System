import os
import cv2
import json
import re
import numpy as np

def run_failure_analysis():
    test_set = [
        ('10/cb33831c86d1f16db29ad58bf9e926f3.jpg', 'low_res_thumbnail'),
        ('1/00770eba64db20501bbd30bb21ce6aa5.jpg', 'tall_narrow_plan'),
        ('1/download.png', 'high_res_marketing'),
        ('3/0adf5f25feca052f9968d0a9f42bd8eb.jpg', 'color_furniture'),
        ('7/0162fa659d7392157fc0854ef058f419.jpg', 'dimension_heavy'),
        ('3/0d2f29cf25a408c7e552e39b91189b34.jpg', 'corridor_heavy'),
        ('5/195e61769696aa144d1388a68ef92cc9.jpg', 'bordered_marketing'),
        ('5/1dfd85587a24e04e1e93659ba35f33cb.jpg', 'contrast_challenged'),
        ('7/01d47a008ad8498cf8bc3f78cfc87765.jpg', 'compact_flat'),
        ('10/052da9368c90d89e449dc37055603d7d.jpg', 'small_res_plan')
    ]
    
    findings = []
    
    for img_p, cat in test_set:
        if not os.path.exists(img_p):
            continue
        im = cv2.imread(img_p)
        h, w = im.shape[:2]
        gray = cv2.cvtColor(im, cv2.COLOR_BGR2GRAY)
        
        # 1. Border artifact check: check pixel intensity of 5% border margin
        margin_x = int(w * 0.05)
        margin_y = int(h * 0.05)
        borders = [gray[:margin_y, :], gray[-margin_y:, :], gray[:, :margin_x], gray[:, -margin_x:]]
        border_darkness = [np.mean(b < 50) for b in borders]
        has_heavy_border = any(bd > 0.3 for bd in border_darkness)
        
        # 2. Otsu wall binarization and gap leakage
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        walls = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        inv_walls = cv2.bitwise_not(walls)
        num_labels, labels, stats, _ = cv2.connectedComponentsWithStats(inv_walls)
        
        # Room candidate stats
        room_areas = [s[cv2.CC_STAT_AREA] for s in stats[1:]]
        max_room_ratio = max(room_areas) / (w * h) if room_areas else 0
        leaked_exterior = max_room_ratio > 0.45
        
        # 3. High frequency texture check (e.g. wood flooring or hatched tiles)
        laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
        
        findings.append({
            'image': img_p,
            'category': cat,
            'resolution': f"{w}x{h}",
            'has_heavy_border': bool(has_heavy_border),
            'leaked_exterior_merge': bool(leaked_exterior),
            'max_component_ratio': round(float(max_room_ratio), 3),
            'components_count': len(stats) - 1,
            'texture_variance': round(float(laplacian_var), 1)
        })
        
    print(json.dumps(findings, indent=2))
    with open('reports/failure_analysis_raw.json', 'w') as f:
        json.dump(findings, f, indent=2)

if __name__ == '__main__':
    run_failure_analysis()
