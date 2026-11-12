import urllib.request
import json

payload = {
    "prompt": "10 marla, double story, 4 bedrooms with attached baths, drawing room, TV lounge, open kitchen, car porch, modern style",
    "plot_width": 35.0,
    "plot_length": 65.0,
    "floors": 2,
    "bedrooms": 4,
    "bathrooms": 4,
    "style": "modern"
}

req = urllib.request.Request(
    "http://127.0.0.1:8000/api/generate",
    data=json.dumps(payload).encode("utf-8"),
    headers={"Content-Type": "application/json"}
)

with urllib.request.urlopen(req) as resp:
    data = json.loads(resp.read().decode("utf-8"))

print("PROJECT ID:", data.get("project_id"))
print("FALLBACK USED:", data.get("fallback_used"))
print("QUALITY GATE STATUS:", data.get("quality_gate", {}).get("status"))
print("CANONICAL PLAN ID:", data.get("canonical_plan_id"))
print("COMPLIANCE ALL PASSED:", data.get("compliance_checklist", {}).get("all_passed"))
print("COMPLIANCE SCORE:", data.get("compliance_checklist", {}).get("score_pct"))
print("ITEMS COUNT:", len(data.get("compliance_checklist", {}).get("items", [])))
for it in data.get("compliance_checklist", {}).get("items", []):
    print(f"  [{it['status']}] {it['name']}: Req '{it['requested']}' -> Delivered '{it['delivered']}'")

print("\nEXPLAINABILITY:")
exp = data.get("explainability", {})
print("  Strategy:", exp.get("strategy_name"))
print("  Archetype:", exp.get("source_archetype_id"))
print("  Influenced by:", exp.get("influenced_by_plans"))
print("  Bylaw Rules Enforced:", len(exp.get("bylaw_rules_applied", [])))

print("\nVARIANTS (3 Options):")
for v in data.get("variants", []):
    print(f"  * {v['id']}: {v['strategy_name']} ({v['archetype_id']}) - Score: {v['quality_score']*100:.0f}% [Active: {v['is_active']}]")
    print(f"    Description: {v['description']}")

