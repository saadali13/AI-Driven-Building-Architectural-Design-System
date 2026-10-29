"""
Image Scanner & Dataset Discovery Engine.

Discovers images across source folders (1, 3, 5, 7, 10, elevationwithfloorplan),
computes SHA-256, MD5, and 64-bit perceptual hashes (pHash), identifies drawing types,
generates stable unique drawing IDs, preserves source file immutability,
and manages the complete dataset manifest (outputs/dataset_manifest.json).
"""

import os
import hashlib
import json
import time
from typing import Dict, List, Tuple, Any, Optional
import cv2
import numpy as np

SUPPORTED_EXTENSIONS = {".png", ".jpg", ".jpeg", ".tiff", ".tif", ".webp", ".pdf"}


def compute_sha256(file_path: str) -> str:
    """Computes SHA-256 hash of a file for cryptographic integrity."""
    hasher = hashlib.sha256()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_md5(file_path: str) -> str:
    """Computes MD5 hash of a file for duplicate detection."""
    hasher = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            hasher.update(chunk)
    return hasher.hexdigest()


def compute_phash(image: np.ndarray, hash_size: int = 8) -> str:
    """
    Computes a 64-bit perceptual hash (pHash) of an image array
    to detect visually identical or re-encoded blueprints.
    """
    if len(image.shape) == 3:
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
    else:
        gray = image
    resized = cv2.resize(gray, (hash_size + 1, hash_size), interpolation=cv2.INTER_AREA)
    diff = resized[:, 1:] > resized[:, :-1]
    return hex(int("".join(["1" if b else "0" for b in diff.flatten()]), 2))[2:].zfill(16)


def hamming_distance(h1: str, h2: str) -> int:
    """Calculates Hamming distance between two hex pHash strings."""
    try:
        val1 = int(h1, 16)
        val2 = int(h2, 16)
        return bin(val1 ^ val2).count("1")
    except Exception:
        return 64


def classify_image_type(image_path: str, img_bgr: Optional[np.ndarray] = None) -> str:
    """
    Classifies image drawing type:
    - 'elevation_with_floorplan': Combined sheet
    - 'colored_3d_rendered': Colored / 3D rendered floor plan
    - 'black_and_white_technical': Pure B&W technical architectural plan
    - 'scanned_blueprint': Scanned blueprint or aged drawing
    - 'floor_plan': Generic architectural floor plan
    - 'uncertain': Low confidence / corrupt
    """
    parent = os.path.basename(os.path.dirname(os.path.abspath(image_path))).lower()
    if parent == "elevationwithfloorplan":
        return "elevation_with_floorplan"

    if img_bgr is None:
        img_bgr = cv2.imread(image_path)
    if img_bgr is None:
        return "unsupported"

    h, w = img_bgr.shape[:2]
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(np.count_nonzero(edges)) / float(max(1, w * h))

    if edge_density < 0.010:
        return "uncertain"

    # Color analysis
    if len(img_bgr.shape) == 3 and img_bgr.shape[2] == 3:
        hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
        sat = hsv[:, :, 1]
        val = hsv[:, :, 2]
        colored_ratio = float(np.count_nonzero((sat > 28) & (val > 60))) / float(max(1, w * h))
        mean_sat = float(np.mean(sat))

        if colored_ratio > 0.08 or mean_sat > 18.0:
            return "colored_3d_rendered"
        elif mean_sat < 5.0:
            bg_pixels = gray[gray > 200]
            bg_std = float(np.std(bg_pixels)) if len(bg_pixels) > 100 else 0.0
            if bg_std > 12.0:
                return "scanned_blueprint"
            return "black_and_white_technical"

    return "floor_plan"


class ImageScanner:
    """
    Scans specified directories and builds an immutable manifest of blueprint assets.
    """

    def __init__(self, source_roots: Optional[List[str]] = None):
        self.source_roots = source_roots or ["1", "3", "5", "7", "10", "elevationwithfloorplan"]

    def scan_all(self, base_dir: str = ".") -> List[Dict[str, Any]]:
        """
        Discovers all source files across all 6 folders without modifying them.
        Detects duplicates and produces stable drawing IDs.
        """
        discovered = []
        seen_md5s: Dict[str, str] = {}
        seen_phashes: Dict[str, str] = {}

        for folder in self.source_roots:
            f_path = os.path.join(base_dir, folder)
            if not os.path.exists(f_path):
                continue

            for root, _, files in os.walk(f_path):
                for fname in sorted(files):
                    ext = os.path.splitext(fname)[1].lower()
                    if ext not in SUPPORTED_EXTENSIONS:
                        continue

                    full_path = os.path.join(root, fname)
                    rel_path = os.path.relpath(full_path, base_dir).replace("\\", "/")
                    fsize = os.path.getsize(full_path)

                    if fsize < 100:
                        continue

                    md5 = compute_md5(full_path)
                    sha256 = compute_sha256(full_path)

                    is_exact_dup = md5 in seen_md5s
                    dup_of = seen_md5s.get(md5)
                    if not is_exact_dup:
                        seen_md5s[md5] = rel_path

                    stem = os.path.splitext(fname)[0]
                    clean_stem = "".join([c if c.isalnum() else "_" for c in stem])
                    drawing_id = f"drawing_{folder}_{clean_stem}"

                    img = cv2.imread(full_path)
                    if img is not None:
                        h, w, c = img.shape
                        phash = compute_phash(img)
                        # Check perceptual similarity
                        is_perceptual_dup = False
                        for p_h, prev_file in seen_phashes.items():
                            if hamming_distance(phash, p_h) <= 3:
                                is_perceptual_dup = True
                                dup_of = dup_of or prev_file
                                break

                        if not is_perceptual_dup and not is_exact_dup:
                            seen_phashes[phash] = rel_path

                        img_type = classify_image_type(full_path, img)
                        is_readable = True
                    else:
                        h, w, c = 0, 0, 0
                        phash = "0000000000000000"
                        is_perceptual_dup = False
                        img_type = "corrupt"
                        is_readable = False

                    discovered.append({
                        "drawing_id": drawing_id,
                        "filename": fname,
                        "relative_path": rel_path,
                        "folder": folder,
                        "file_size_bytes": fsize,
                        "resolution_px": [w, h],
                        "aspect_ratio": round(w / float(h), 3) if h > 0 else 1.0,
                        "channels": c,
                        "format": ext.lstrip(".").upper(),
                        "md5_hash": md5,
                        "sha256_hash": sha256,
                        "phash": phash,
                        "is_readable": is_readable,
                        "is_duplicate": is_exact_dup or is_perceptual_dup,
                        "duplicate_of": dup_of,
                        "image_type": img_type
                    })

        return discovered

    def generate_and_save_manifest(
        self,
        base_dir: str = ".",
        output_manifest_path: str = "outputs/dataset_manifest.json"
    ) -> Dict[str, Any]:
        """
        Compiles and writes outputs/dataset_manifest.json adhering to Section 5 & 12.
        """
        discovered = self.scan_all(base_dir)
        total = len(discovered)
        readable = sum(1 for d in discovered if d.get("is_readable", False))
        duplicates = sum(1 for d in discovered if d.get("is_duplicate", False))
        valid_processable = sum(1 for d in discovered if d.get("is_readable", False) and not d.get("is_duplicate", False))

        folder_breakdown = {}
        for d in discovered:
            f = d["folder"]
            folder_breakdown.setdefault(f, {
                "total_files": 0,
                "readable_files": 0,
                "duplicate_files": 0,
                "formats": {}
            })
            folder_breakdown[f]["total_files"] += 1
            if d.get("is_readable", False):
                folder_breakdown[f]["readable_files"] += 1
            if d.get("is_duplicate", False):
                folder_breakdown[f]["duplicate_files"] += 1
            fmt = d.get("format", "UNKNOWN")
            folder_breakdown[f]["formats"][fmt] = folder_breakdown[f]["formats"].get(fmt, 0) + 1

        manifest = {
            "dataset_manifest_version": "2.0.0",
            "generation_timestamp": time.strftime("%Y-%m-%d %H:%M:%S"),
            "total_discovered_files": total,
            "total_readable_files": readable,
            "total_duplicate_files": duplicates,
            "total_processable_unique_drawings": valid_processable,
            "source_folders": self.source_roots,
            "folder_statistics": folder_breakdown,
            "files": discovered
        }

        os.makedirs(os.path.dirname(os.path.abspath(output_manifest_path)), exist_ok=True)
        with open(output_manifest_path, "w", encoding="utf-8") as f:
            json.dump(manifest, f, indent=2)

        return manifest
