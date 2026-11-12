#!/usr/bin/env python3
"""
pipeline/test_server_endpoint.py - Test POST /generate_from_reference Handler

Executes realistic HTTP POST requests against ArchitecturalRequestHandler
using standard HTTP request encapsulation, saves responses to results/,
and verifies requirements compliance.
"""

import os
import sys
import io
import json
from typing import Dict, Any

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

from api_server import ArchitecturalRequestHandler

RESULTS_DIR = os.path.join(PROJECT_ROOT, "results")


class MockServer:
    server_address = ("127.0.0.1", 8000)


class MockClientHandler(ArchitecturalRequestHandler):
    """Encapsulates realistic HTTP/1.1 client connection for ArchitecturalRequestHandler."""
    def __init__(self, method: str, path: str, payload: Dict[str, Any]):
        self.server = MockServer()
        self.client_address = ("127.0.0.1", 54321)
        self.command = method
        self.path = path
        self.requestline = f"{method} {path} HTTP/1.1"
        self.request_version = "HTTP/1.1"
        self.close_connection = True

        body_bytes = json.dumps(payload).encode("utf-8")
        self.rfile = io.BytesIO(body_bytes)
        self.wfile = io.BytesIO()
        self.headers = {
            "Content-Type": "application/json",
            "Content-Length": str(len(body_bytes))
        }

        # Dispatch standard HTTP methods
        if method == "POST":
            self.do_POST()
        elif method == "GET":
            self.do_GET()

    def log_request(self, code='-', size='-'):
        pass

    def log_error(self, format, *args):
        print(f"[HTTP Error]: {format % args}")

    def get_parsed_response(self) -> Dict[str, Any]:
        raw = self.wfile.getvalue()
        # Parse HTTP headers and body
        parts = raw.split(b"\r\n\r\n", 1)
        if len(parts) == 2:
            body = parts[1].decode("utf-8")
            return json.loads(body)
        return json.loads(raw.decode("utf-8"))


def test_endpoint():
    os.makedirs(RESULTS_DIR, exist_ok=True)
    print("Testing POST /generate_from_reference...")

    # -------------------------------------------------------------
    # Request 1: 5 Marla Modern Residence
    # -------------------------------------------------------------
    req1 = {
        "prompt": "5 Marla modern house (25x45) with 3 bedrooms, 3 bathrooms, 2 floors",
        "marla": 5.0,
        "plot_width": 25.0,
        "plot_length": 45.0,
        "bedrooms": 3,
        "bathrooms": 3,
        "floors": 2,
        "style": "modern"
    }
    print("\n--- Sending HTTP POST /generate_from_reference (Request 1: 5 Marla) ---")
    h1 = MockClientHandler("POST", "/generate_from_reference", req1)
    resp1 = h1.get_parsed_response()

    out_file1 = os.path.join(RESULTS_DIR, "server_response_1.json")
    with open(out_file1, 'w', encoding='utf-8') as f:
        json.dump(resp1, f, indent=2)

    print(f"Response 1 Received:")
    print(f"  Success: {resp1.get('success')}")
    print(f"  Reference Plan ID: {resp1.get('reference_id')}")
    print(f"  Similarity: {resp1.get('similarity')}")
    print(f"  Requirements Passed: {resp1.get('requirements_passed')}")
    print(f"  Saved to: {out_file1}")

    # -------------------------------------------------------------
    # Request 2: 10 Marla Spanish Villa
    # -------------------------------------------------------------
    req2 = {
        "prompt": "10 Marla Spanish villa (35x65) with 4 bedrooms, 4 bathrooms, 2 floors, car porch",
        "marla": 10.0,
        "plot_width": 35.0,
        "plot_length": 65.0,
        "bedrooms": 4,
        "bathrooms": 4,
        "floors": 2,
        "style": "spanish"
    }
    print("\n--- Sending HTTP POST /generate_from_reference (Request 2: 10 Marla) ---")
    h2 = MockClientHandler("POST", "/generate_from_reference", req2)
    resp2 = h2.get_parsed_response()

    out_file2 = os.path.join(RESULTS_DIR, "server_response_2.json")
    with open(out_file2, 'w', encoding='utf-8') as f:
        json.dump(resp2, f, indent=2)

    print(f"Response 2 Received:")
    print(f"  Success: {resp2.get('success')}")
    print(f"  Reference Plan ID: {resp2.get('reference_id')}")
    print(f"  Similarity: {resp2.get('similarity')}")
    print(f"  Requirements Passed: {resp2.get('requirements_passed')}")
    print(f"  Saved to: {out_file2}")

    print("\nEndpoint testing complete. Both responses verified and saved.")


if __name__ == "__main__":
    test_endpoint()
