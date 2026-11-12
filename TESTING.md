# ArchiCraft AI Studio — Manual Test Script (10-Step Guide)

Welcome to the ArchiCraft AI Studio pair-programming validation run. This document guides you through testing the real running application end-to-end.

## Active Service URLs
* **Frontend Web Application**: [http://127.0.0.1:5173](http://127.0.0.1:5173)
* **Backend API Server**: [http://127.0.0.1:8000](http://127.0.0.1:8000)
* **API Health Status**: [http://127.0.0.1:8000/api/status](http://127.0.0.1:8000/api/status)

---

## 10-Step Manual Test Procedure

### Step 1: Access the Application
* **Action**: Open [http://127.0.0.1:5173](http://127.0.0.1:5173) in your browser.
* **Expected Result**: The ArchiCraft AI Studio homepage loads with zero console or network errors.

### Step 2: Open Requirements Studio
* **Action**: Click **"Launch Studio"** or navigate to the Workspace tab.
* **Expected Result**: The architectural requirements form appears with plot size, bedroom, bathroom, and floor controls.

### Step 3: Fetch Similar Real References
* **Action**: Enter a program: `10 Marla (35x65)`, `4 Bedrooms`, `4 Bathrooms`, `2 Floors`.
* **Expected Result**: Top 3 real blueprint references are retrieved with percentage similarity scores, matched/missed feature breakdowns, and blueprint image previews.

### Step 4: Generate Design from Reference
* **Action**: Select the top-ranked reference (or click **"Generate Design"**).
* **Expected Result**: The system synthesizes the multi-floor design with Ground, First Floor, Rooftop, and 2D Front Elevation blueprints rendered at 1:1 scale.

### Step 5: Switch Candidates (A / B / C)
* **Action**: Use the Candidates switcher to view:
  - **Candidate A**: Primary real reference adaptation
  - **Candidate B**: Alternative real reference adaptation
  - **Candidate C**: Template library hand-crafted variant
* **Expected Result**: Each candidate displays its Design Quality Score, provenance badge (`real_reference` vs `template_library`), and similarity rating.

### Step 6: Test Room Edit: Add Room
* **Action**: In the edit console, select **"Add Room"** -> `Servant Quarter` -> `Back Zone` (or submit instruction: `"add a servant quarter in the back corner"`).
* **Expected Result**: The plan regenerates to Version 2. The servant room appears in the rear zone, and the op-log confirms the addition.

### Step 7: Test Room Edit: Convert / Replace Room
* **Action**: Select **"Replace Room"** -> replace `Drawing Room` with `Study` (or submit: `"replace drawing room with study"`).
* **Expected Result**: Version increments to v3. The formal drawing room is converted into a private study/library.

### Step 8: Test Room Edit: Mirror Layout
* **Action**: Click **"Mirror Layout"** (or submit: `"mirror the layout"`).
* **Expected Result**: The car porch, drawing room, and entrance flip across the X-axis (e.g. from left to right side). Version increments to v4.

### Step 9: Test Version History & Undo / Redo
* **Action**: Click the **"Undo"** button twice.
* **Expected Result**: The active plan reverts back to Version 2 (before the mirror and room replacement). Clicking **"Redo"** moves forward to v3.

### Step 10: Export Deliverables
* **Action**: Click the export buttons in the header:
  - **Export PNG**: Downloads high-resolution blueprint raster image.
  - **Export DXF**: Downloads layered AutoCAD vector file compatible with AutoCAD / LibreCAD.
  - **Export BOQ**: Downloads itemized construction cost estimation in PKR.
* **Expected Result**: All 3 files download successfully and are verified non-empty.

