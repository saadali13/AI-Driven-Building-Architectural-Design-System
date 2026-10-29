# Reference Floor Plan Dataset Inventory Report

**Standard:** Lead Architectural AI & Dataset Verification Standard
**Total Categories Inspected:** 5 (`1/`, `3/`, `5/`, `7/`, `10/`)
**Total Image Assets Audited:** 187
**Total Exact Duplicate Pairs Detected:** 2

## 1. Category Summary Inventory Table

| Category | Inferred Plot Size | Image Count | Valid | Invalid | Duplicates | Formats | Median Resolution |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | 1 Kanal (50' x 90') | 26 | 26 | 0 | 1 | JPEG (24), PNG (2) | 736x1191 |
| **3** | 3 Marla (20' x 35') | 40 | 40 | 0 | 0 | JPEG (38), PNG (2) | 736x1169 |
| **5** | 5 Marla (25' x 45') | 41 | 41 | 0 | 1 | JPEG (41) | 720x1138 |
| **7** | 7 Marla (30' x 55') | 42 | 42 | 0 | 0 | JPEG (39), PNG (3) | 735x1206 |
| **10** | 10 Marla (35' x 65') | 38 | 38 | 0 | 0 | JPEG (37), PNG (1) | 736x1195 |
| **TOTAL** | **All 5 Archetypes** | **187** | **187** | **0** | **2 groups** | **JPEG / PNG** | **Multi-scale** |

## 2. Exact Duplicate Audit

The following duplicate pairs share identical binary content (SHA256 match):

1. `1/dc63fcbef5792c11a0630cf42b1b279a (1).jpg` <=> `1/dc63fcbef5792c11a0630cf42b1b279a.jpg` (SHA256: `2ee729cde1c9...`)
2. `5/56734469ec2d1b6642d46f696542f158 (1).jpg` <=> `5/56734469ec2d1b6642d46f696542f158.jpg` (SHA256: `9364eaa7d83b...`)

## 3. Visual Representation Archetypes

- **Black & White CAD Drafts**: ~45% of plans. Clean wall hatching, explicit dimension leader lines (`X' - Y"`), architectural room abbreviations (`D/BATH`, `S.KIT`, `OTS`, `PDR`).
- **Color Marketing Blueprints**: ~35% of plans. High-contrast room zoning with color fill, scaled vector furniture blocks (beds, sanitary fixtures, cars, trees, pools), and circulation corridors.
- **Multi-Storey Combined Sheets**: ~20% of plans (AR > 1.35). Contain both Ground Floor and First Floor drawings side-by-side on a single canvas, showing vertical alignment.
- **Corrupted / Unreadable Images**: 0 corrupted images found; all images opened and verified via PIL.
