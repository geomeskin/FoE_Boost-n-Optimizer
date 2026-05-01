# ==========================================
# FILE: core/boosts.py
# ==========================================

import json
import csv
import config


# ------------------------------------------
# helpers
# ------------------------------------------
def load_json(path):
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def flatten_boost_rows(record):

    rows = []

    building_id = record.get("building_id", "")
    building_name = record.get("building_name", "")
    width = record.get("width", 1)
    length = record.get("length", 1)
    tiles = record.get("tiles", width * length)

    ability = record.get("ability", {})

    # Most common pattern:
    # ability -> boostHints -> [ { boostHintEraMap : {Era:{...}} } ]

    boost_hints = ability.get("boostHints", [])

    if not isinstance(boost_hints, list):
        return rows

    for hint in boost_hints:

        era_map = hint.get("boostHintEraMap", {})

        if not isinstance(era_map, dict):
            continue

        for era_name, era_data in era_map.items():

            if not isinstance(era_data, dict):
                continue

            boost_type = era_data.get("type", "")
            value = era_data.get("value", 0)
            target = era_data.get("targetedFeature", "")

            # if missing numeric value, skip
            if value in [None, ""]:
                continue

            try:
                numeric_value = float(value)
            except:
                continue

            per_tile = round(numeric_value / tiles, 4) if tiles else 0

            rows.append({
                "building_id": building_id,
                "building_name": building_name,
                "width": width,
                "length": length,
                "tiles": tiles,
                "era": era_name,
                "boost_type": boost_type,
                "targeted_feature": target,
                "value": numeric_value,
                "per_tile": per_tile
            })

    return rows


def save_csv(path, rows):

    headers = [
        "building_id",
        "building_name",
        "width",
        "length",
        "tiles",
        "era",
        "boost_type",
        "targeted_feature",
        "value",
        "per_tile"
    ]

    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=headers)
        writer.writeheader()

        for row in rows:
            writer.writerow(row)


# ------------------------------------------
# main runner
# ------------------------------------------
def run():

    print("=== BOOSTS STAGE ===")

    source = config.OUTPUT_DIR / "combat_abilities.json"

    print("Loading combat_abilities.json ...")
    data = load_json(source)

    all_rows = []

    for record in data:
        rows = flatten_boost_rows(record)
        all_rows.extend(rows)

    out_csv = config.OUTPUT_DIR / "foe_boost_table.csv"

    print("Writing foe_boost_table.csv ...")
    save_csv(out_csv, all_rows)

    summary = {
        "combat_records_read": len(data),
        "boost_rows_written": len(all_rows)
    }

    with open(config.OUTPUT_DIR / "boosts_summary.json", "w", encoding="utf-8") as f:
        json.dump(summary, f, indent=2)

    print("DONE")
    print("Combat records read:", len(data))
    print("Boost rows written:", len(all_rows))
    