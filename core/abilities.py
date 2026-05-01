# ==========================================
# FILE: core/abilities.py
# ==========================================

import json
import config


# ------------------------------------------
# helpers
# ------------------------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def as_iterable_entities(data):
    """
    Supports either:
    - dict of entities
    - list of entities
    """
    if isinstance(data, dict):
        return data.values()
    elif isinstance(data, list):
        return data
    return []


# ------------------------------------------
# classification logic
# ------------------------------------------
def classify_ability(ability):

    text = json.dumps(ability).lower()

    if any(x in text for x in [
        "att_boost",
        "def_boost",
        "attacker",
        "defender",
        "boosthint"
    ]):
        return "combat"

    if any(x in text for x in [
        "production",
        "supply",
        "coins",
        "money",
        "forgepoints",
        "medals",
        "goods"
    ]):
        return "production"

    if any(x in text for x in [
        "street",
        "road",
        "placement",
        "adjacent",
        "connected"
    ]):
        return "placement"

    if any(x in text for x in [
        "happiness",
        "population",
        "motivate",
        "polish",
        "chance",
        "reward"
    ]):
        return "utility"

    return "unknown"


# ------------------------------------------
# main runner
# ------------------------------------------
def run():

    print("=== ABILITIES STAGE ===")

    source = config.CITY_ENTITIES_FILE

    print("Loading city_entities.json ...")
    entities = load_json(source)

    combat = []
    placement = []
    production = []
    utility = []
    unknown = []

    records = 0
    abilities_found = 0

    for ent in as_iterable_entities(entities):

        records += 1

        entity_id = ent.get("id", "")
        entity_name = ent.get("name", "")
        width = ent.get("width", 1)
        length = ent.get("length", 1)

        raw_abilities = ent.get("abilities", [])

        if not isinstance(raw_abilities, list):
            continue

        for ability in raw_abilities:

            abilities_found += 1

            row = {
                "building_id": entity_id,
                "building_name": entity_name,
                "width": width,
                "length": length,
                "tiles": width * length,
                "ability": ability
            }

            bucket = classify_ability(ability)

            if bucket == "combat":
                combat.append(row)

            elif bucket == "placement":
                placement.append(row)

            elif bucket == "production":
                production.append(row)

            elif bucket == "utility":
                utility.append(row)

            else:
                unknown.append(row)

    # outputs
    save_json(config.OUTPUT_DIR / "combat_abilities.json", combat)
    save_json(config.OUTPUT_DIR / "placement_abilities.json", placement)
    save_json(config.OUTPUT_DIR / "production_abilities.json", production)
    save_json(config.OUTPUT_DIR / "utility_abilities.json", utility)
    save_json(config.OUTPUT_DIR / "unknown_abilities.json", unknown)

    summary = {
        "records_scanned": records,
        "abilities_found": abilities_found,
        "combat": len(combat),
        "placement": len(placement),
        "production": len(production),
        "utility": len(utility),
        "unknown": len(unknown)
    }

    save_json(config.OUTPUT_DIR / "abilities_summary.json", summary)

    print("DONE")
    print("Records scanned:", records)
    print("Abilities found:", abilities_found)
    print("Combat:", len(combat))
    print("Placement:", len(placement))
    print("Production:", len(production))
    print("Utility:", len(utility))
    print("Unknown:", len(unknown))
    