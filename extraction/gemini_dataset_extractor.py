"""
Phase 4/7: Gemini Multimodal Vision Dataset Extractor.
STRICT USAGE POLICY:
- Used EXCLUSIVELY for extracting architectural information and creating dataset files from floor plan images.
- FORBIDDEN for floor plan generation (layout generation is strictly handled by the CP-SAT solver and Blender).
"""

import os
import sys
import json
import re
from typing import Dict, List, Any, Optional
from PIL import Image
from config.gemini_config import GeminiConfig
from generation.gemini_service import GeminiService, GeminiServiceUnavailableError


class GeminiDatasetExtractor:
    """
    Extracts high-fidelity architectural specifications from raw floor plan images
    to build training and benchmark dataset files using resilient GeminiService.
    """

    def __init__(self, api_key: Optional[str] = None):
        self.api_key = api_key or GeminiConfig.get_api_key()
        self.service = GeminiService.get_instance(api_key=self.api_key)

    def extract_floor_plan_data(self, image_path: str) -> Dict[str, Any]:
        """
        Analyzes a floor plan image using Gemini multimodal vision and returns structured architectural data.
        """
        if not os.path.exists(image_path):
            raise FileNotFoundError(f"Floor plan image not found: {image_path}")

        img = Image.open(image_path)

        prompt = """
You are an expert architectural analysis AI. Extract all spatial, dimensional, geometric, and functional data from this floor plan drawing or 3D cutaway rendering.

CRITICAL REQUIREMENT: For EVERY room, you MUST extract its spatial position:
1. "box_2d": [ymin, xmin, ymax, xmax] normalized coordinates from 0 to 1000 representing the bounding rectangle of the room within the image.
2. "spatial_zone": The architectural location of the room in the building layout (choose from: "front_left", "front_center", "front_right", "center_left", "center", "center_right", "rear_left", "rear_center", "rear_right").

Return a STRICT, valid JSON object with the following schema:
{
  "project_title": "Descriptive title of the floor plan",
  "plot_archetype": "Estimated plot type (e.g. 3 Marla, 5 Marla, 7 Marla, 10 Marla, 1 Kanal)",
  "dimensions_overall": "Overall width and length if visible or estimated (e.g. 35'x65')",
  "total_bedrooms": <integer>,
  "total_bathrooms": <integer>,
  "has_car_porch": <boolean>,
  "has_stairs": <boolean>,
  "has_open_to_sky": <boolean>,
  "rooms": [
    {
      "room_id": "r_1",
      "name": "Room name (e.g. Master Bedroom, Bedroom, Drawing, Kitchen, Hall, Bath, Toilet, Lobby, Passage, Store)",
      "category": "bedroom / bathroom / kitchen / living / dining / circulation / parking / utility / outdoor",
      "dimensions_raw": "Exact dimension string as written on image (e.g. 16'-3\"x11'-0\")",
      "dimensions_meters": [<width_meters>, <height_meters>],
      "spatial_zone": "front_left / front_center / front_right / center_left / center / center_right / rear_left / rear_center / rear_right",
      "box_2d": [<ymin>, <xmin>, <ymax>, <xmax>],
      "connected_to": ["List of other room names or IDs directly accessible via doors"]
    }
  ],
  "structural_notes": {
    "staircase_location": "central / side / porch",
    "parking_capacity": "single_car / double_car / none",
    "circulation_type": "central_lounge / corridor"
  }
}

Return ONLY raw JSON. No markdown code blocks, no backticks, no explanations.
"""
        try:
            data = self.service.generate_json(
                contents=[prompt, img],
                is_strong_task=False
            )
        except GeminiServiceUnavailableError as exc:
            raise RuntimeError(f"Floor plan extraction temporarily unavailable: {exc}")
        except Exception as exc:
            raise ValueError(f"Failed to extract architectural data from floor plan image: {exc}")

        # Add image provenance metadata
        data["source_image"] = os.path.basename(image_path)
        data["source_path"] = image_path.replace("\\", "/")
        return data

    def process_and_save_dataset_file(self, image_path: str, output_dir: str = "dataset/gemini_extracted") -> str:
        """
        Extracts information from an image and saves it as a canonical dataset JSON file.
        """
        os.makedirs(output_dir, exist_ok=True)
        data = self.extract_floor_plan_data(image_path)

        base_name = os.path.splitext(os.path.basename(image_path))[0]
        out_file = os.path.join(output_dir, f"{base_name}_dataset.json")

        with open(out_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)

        return out_file


def main():
    if len(sys.argv) < 2:
        print("Usage: python -m extraction.gemini_dataset_extractor <image_path> [output_dir]")
        sys.exit(1)

    img_path = sys.argv[1]
    out_dir = sys.argv[2] if len(sys.argv) > 2 else "dataset/gemini_extracted"

    extractor = GeminiDatasetExtractor()
    print(f"Extracting dataset information from: {img_path}...")
    saved_path = extractor.process_and_save_dataset_file(img_path, out_dir)
    print(f"Dataset file successfully created at: {saved_path}")


if __name__ == "__main__":
    main()
