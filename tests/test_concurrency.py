import os
import json
import pytest
import urllib.request
import concurrent.futures

API_BASE = "http://127.0.0.1:8000"

def send_post(endpoint: str, payload: dict) -> dict:
    url = f"{API_BASE}{endpoint}"
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers={"Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))

def test_concurrent_generate_requests():
    """Fire 4 simultaneous /api/generate requests and verify uncorrupted results with distinct plan IDs."""
    prompts = [
        {"prompt": "5 Marla contemporary house with 3 bedrooms", "plot_width": 25.0, "plot_length": 45.0, "style": "modern"},
        {"prompt": "7 Marla spanish villa with 4 bedrooms", "plot_width": 30.0, "plot_length": 52.5, "style": "spanish"},
        {"prompt": "10 Marla modern house with 4 bed 4 bath and tv lounge", "plot_width": 35.0, "plot_length": 65.0, "style": "modern"},
        {"prompt": "1 Kanal classical estate with 5 bedrooms and lawn", "plot_width": 50.0, "plot_length": 90.0, "style": "classical"}
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(send_post, "/api/generate", p) for p in prompts]
        results = [f.result() for f in futures]

    assert len(results) == 4
    plan_ids = set()

    for idx, res in enumerate(results):
        assert "project_id" in res, f"Result {idx} missing project_id"
        pid = res["project_id"]
        assert pid not in plan_ids, f"Duplicate plan_id found: {pid}"
        plan_ids.add(pid)

        # Assert data integrity (no corruptions)
        assert len(res.get("floors", [])) >= 2, f"Plan {pid} has insufficient floors"
        assert res.get("canonical_plan") is not None, f"Plan {pid} missing canonical_plan"
        assert res.get("compliance_checklist") is not None, f"Plan {pid} missing compliance_checklist"
        assert res.get("quality_gate") is not None, f"Plan {pid} missing quality_gate"
        assert res.get("three_d_model") is not None, f"Plan {pid} missing three_d_model"
        assert "images" in res, f"Plan {pid} missing images"
        assert "elevation_svg" in res["images"], f"Plan {pid} missing elevation_svg in images"

    print(f"\n[Test Passed] 4 concurrent /api/generate succeeded with distinct IDs: {plan_ids}")

def test_concurrent_regenerate_requests():
    """Fire 4 simultaneous /api/regenerate requests and verify versioning and consistency."""
    # First generate a base 10 marla plan
    base = send_post("/api/generate", {
        "prompt": "10 Marla modern residence 4 beds",
        "plot_width": 35.0,
        "plot_length": 65.0,
        "style": "modern"
    })
    base_pid = base["project_id"]

    edits = [
        {"plan_id": base_pid, "base_version": 1, "improvement_text": "expand master bedroom width by 2 feet"},
        {"plan_id": base_pid, "base_version": 1, "improvement_text": "expand drawing room width by 1.5 feet"},
        {"plan_id": base_pid, "base_version": 1, "improvement_text": "expand kitchen length by 2 feet"},
        {"plan_id": base_pid, "base_version": 1, "improvement_text": "expand tv lounge length by 2 feet"}
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as executor:
        futures = [executor.submit(send_post, "/api/regenerate", e) for e in edits]
        results = [f.result() for f in futures]

    assert len(results) == 4
    for idx, res in enumerate(results):
        assert res.get("success") is True, f"Regenerate {idx} failed: {res.get('error')}"
        assert (res.get("plan_id") == base_pid or res.get("project_id") == base_pid)
        assert res.get("version") >= 2
        assert len(res.get("floors", [])) >= 2
        assert res.get("canonical_plan") is not None

    print(f"\n[Test Passed] 4 concurrent /api/regenerate on {base_pid} completed successfully without race conditions.")

def test_concurrent_project_persistence():
    """Verify concurrent reads and writes to saved_projects.json are atomic and uncorrupted."""
    projects_to_save = [
        {"project_id": f"proj_test_conc_{i}", "project_title": f"Concurrent Project {i}", "timestamp": i}
        for i in range(10)
    ]

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        futures = [executor.submit(send_post, "/api/projects/save", p) for p in projects_to_save]
        results = [f.result() for f in futures]

    for res in results:
        assert res.get("success") is True

    # Read back projects
    req = urllib.request.Request(f"{API_BASE}/api/projects")
    with urllib.request.urlopen(req, timeout=10) as resp:
        all_projs = json.loads(resp.read().decode("utf-8"))

    saved_ids = {p.get("project_id") for p in all_projs}
    for p in projects_to_save:
        assert p["project_id"] in saved_ids, f"Project {p['project_id']} missing from saved_projects.json"

    # Cleanup test projects
    for p in projects_to_save:
        send_post("/api/projects/delete", {"project_id": p["project_id"]})

    print(f"\n[Test Passed] Concurrent project storage: 10 atomic saves verified and cleaned up.")
