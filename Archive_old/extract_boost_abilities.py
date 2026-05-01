import json

INPUT_FILE = "enriched_buildings_full.json"
OUTPUT_FILE = "boost_abilities_raw.json"

def is_structural_boost(a):
    """
    Detects likely real boost objects based on structure,
    not keyword guessing.
    """
    if not isinstance(a, dict):
        return False

    # must have at least one numeric value
    has_numeric = any(isinstance(v, (int, float)) and v != 0 for v in a.values())

    # must NOT be pure placement metadata
    placement_keys = {"gridId", "sector", "allowedPlacements"}

    meaningful_keys = [k for k in a.keys() if k not in placement_keys]

    if not meaningful_keys:
        return False

    # must contain some signal of effect (not just empty scaffolding)
    return has_numeric


with open(INPUT_FILE, "r", encoding="utf-8") as f:
    data = json.load(f)

boosts = []

for building_id, building in data.items():
    abilities = building.get("abilities", [])

    if not isinstance(abilities, list):
        continue

    for ability in abilities:
        if is_structural_boost(ability):
            boosts.append({
                "building_id": building_id,
                "building_name": building.get("name"),
                "width": building.get("width"),
                "length": building.get("length"),
                "ability": ability
            })

with open(OUTPUT_FILE, "w", encoding="utf-8") as f:
    json.dump(boosts, f, indent=2)

print("Total boost-like abilities found:", len(boosts))
print("Saved to:", OUTPUT_FILE)