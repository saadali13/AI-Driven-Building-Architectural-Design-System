import os
import cv2
import json
import re
import numpy as np
import easyocr

def test_pipeline():
    test_imgs = [
        '1/00770eba64db20501bbd30bb21ce6aa5.jpg', # tall plan
        '1/download.png',                         # high-res png
        '10/cb33831c86d1f16db29ad58bf9e926f3.jpg',# tiny low-res (236x433)
        '3/0adf5f25feca052f9968d0a9f42bd8eb.jpg', # color/tinted
        '7/0162fa659d7392157fc0854ef058f419.jpg'  # high-res 1200x1697
    ]
    
    import sys
    if sys.platform == 'win32':
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
        sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')
    reader = easyocr.Reader(['en'], gpu=False, verbose=False)
    results = []
    
    for img_p in test_imgs:
        if not os.path.exists(img_p):
            continue
        img = cv2.imread(img_p)
        h, w = img.shape[:2]
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        # Otsu thresholding
        _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV + cv2.THRESH_OTSU)
        
        # Morphological wall isolation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (3, 3))
        walls = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, kernel)
        contours, _ = cv2.findContours(walls, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        
        # Room candidate segmentation via connected components on inverted walls
        inv_walls = cv2.bitwise_not(walls)
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(inv_walls)
        room_candidates = [s for s in stats if (w * h * 0.005) < s[cv2.CC_STAT_AREA] < (w * h * 0.4)]
        
        # EasyOCR execution
        ocr_out = reader.readtext(img)
        text_entries = [t[1] for t in ocr_out if t[2] > 0.3]
        
        # Dimension regex matching
        dim_regex = re.compile(r"(\d+[\'’\-]\s*\d+|\d+\.?\d*\s*(?:m|mm|ft|\"|'|x|X))")
        dims_found = [t for t in text_entries if dim_regex.search(t)]
        
        # Room label keyword matching
        room_keywords = ['bed', 'bath', 'living', 'kitchen', 'dining', 'hall', 'room', 'balcony', 'porch', 'entry', 'wc', 'garage']
        rooms_found = [t for t in text_entries if any(k in t.lower() for k in room_keywords)]
        
        res = {
            'image_path': img_p,
            'resolution': f"{w}x{h}",
            'wall_contours': len(contours),
            'room_candidates': len(room_candidates),
            'ocr_text_count': len(text_entries),
            'dimensions_detected': dims_found[:5],
            'rooms_detected': rooms_found[:5],
            'ocr_sample': text_entries[:6]
        }
        results.append(res)
        print(f"Processed {img_p}:")
        print(f"  Res: {w}x{h}, OCR items: {len(text_entries)}, Dims: {len(dims_found)}, Room keywords: {len(rooms_found)}")
        print(f"  Sample text: {text_entries[:4]}")
        print(f"  Room candidates: {len(room_candidates)}")
        print("-" * 50)
        
    with open('reports/sample_stress_test.json', 'w') as f:
        json.dump(results, f, indent=2)

if __name__ == '__main__':
    test_pipeline()
