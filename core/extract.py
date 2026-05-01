# ===============================
# FILE: core/extract.py
# ===============================

import json
from pathlib import Path
import config


def ensure_dirs():
    config.INPUT_DIR.mkdir(parents=True, exist_ok=True)
    config.OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


def load_raw_export():
    if not config.INPUT_FILE.exists():
        raise FileNotFoundError(
            f"Missing input file:\n{config.INPUT_FILE}\n\n"
            f"Export your city from FoE Helper (City Plan -> Clipboard) and\n"
            f"place the JSON file in:\n{config.INPUT_DIR}"
        )

    with open(config.INPUT_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


def extract_city_entities(raw):
    """
    Finds CityEntities from the export.
    Adjust here only if export structure changes.
    """
    if "CityEntities" in raw:
        return raw["CityEntities"]

    raise KeyError("CityEntities key not found in export file.")


def save_json(path, data):
    with open(path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)


def build_summary(entities):

    if isinstance(entities, dict):
        count = len(entities)
        first_record = next(iter(entities.values()), {})
        keys = list(first_record.keys()) if isinstance(first_record, dict) else []

    elif isinstance(entities, list):
        count = len(entities)
        keys = list(entities[0].keys()) if entities else []

    else:
        count = 0
        keys = []

    return {
        "records_found": count,
        "sample_keys_first_record": keys
    }


def run():
    print("=== EXTRACT STAGE ===")

    ensure_dirs()

    print("Loading raw export...")
    raw = load_raw_export()

    print("Extracting CityEntities...")
    entities = extract_city_entities(raw)

    print(f"Records found: {len(entities)}")

    print("Saving city_entities.json ...")
    save_json(config.CITY_ENTITIES_FILE, entities)

    summary = build_summary(entities)

    print("Saving extract_summary.json ...")
    save_json(config.EXTRACT_SUMMARY_FILE, summary)

    print("DONE")
    print(f"Saved: {config.CITY_ENTITIES_FILE}")
    print(f"Saved: {config.EXTRACT_SUMMARY_FILE}")