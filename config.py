# ===============================
# FILE: config.py
# ===============================

import re
from pathlib import Path
from datetime import datetime

BASE_DIR  = Path(__file__).resolve().parent
DATA_DIR  = BASE_DIR / "data"
INPUT_DIR = DATA_DIR / "input"

# Optimizer tuning — static
ITERATIONS  = 500
CITY_WIDTH  = 20   # fallback; optimizer should read UnlockedAreas from export
CITY_HEIGHT = 20

# Static game-reference inputs (same for all cities, same game version)
ENRICHED_BUILDINGS_FILE = INPUT_DIR / "enriched_buildings.json"

# ---- Runtime-configured (set by configure()) ----
CITY_NAME = "CITY"

# ---- Runtime-configured paths (set by configure() before any stage runs) ----
INPUT_FILE              = None
OUTPUT_DIR              = None
CITY_ENTITIES_FILE      = None
EXTRACT_SUMMARY_FILE    = None
BOOST_ABILITIES_FILE    = None
RANKED_BUILDINGS_FILE   = None
OPTIMIZED_LAYOUT_FILE   = None
MY_CITY_FILE            = None
MY_CITY_CSV             = None


def _city_name_from_file(filename):
    stem = Path(filename).stem                                    # e.g. "FullCTHG_Export_20260501"
    stem = re.sub(r"^Full",        "", stem)                     # "CTHG_Export_20260501"
    stem = re.sub(r"_Export.*$",   "", stem, flags=re.IGNORECASE) # "CTHG"
    return stem or "CITY"


def configure(input_filename, city_name=None):
    """
    Call once before running any pipeline stage.
    Sets all module-level path variables and creates the output folder.
    Returns the run label (e.g. 'CTHG_20260501_143022').
    """
    global CITY_NAME
    global INPUT_FILE, OUTPUT_DIR
    global CITY_ENTITIES_FILE, EXTRACT_SUMMARY_FILE
    global BOOST_ABILITIES_FILE, RANKED_BUILDINGS_FILE, OPTIMIZED_LAYOUT_FILE
    global MY_CITY_FILE, MY_CITY_CSV

    INPUT_FILE = INPUT_DIR / input_filename

    if city_name is None:
        city_name = _city_name_from_file(input_filename)

    CITY_NAME = city_name
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    run_label = f"{city_name}_{timestamp}"

    OUTPUT_DIR = DATA_DIR / "output" / run_label
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    CITY_ENTITIES_FILE      = OUTPUT_DIR / "city_entities.json"
    EXTRACT_SUMMARY_FILE    = OUTPUT_DIR / "extract_summary.json"
    BOOST_ABILITIES_FILE    = OUTPUT_DIR / "boost_abilities.json"
    RANKED_BUILDINGS_FILE   = OUTPUT_DIR / "ranked_buildings.json"
    OPTIMIZED_LAYOUT_FILE   = OUTPUT_DIR / "optimized_layout.json"
    MY_CITY_FILE            = OUTPUT_DIR / "my_city.json"
    MY_CITY_CSV             = OUTPUT_DIR / "report_my_city.csv"

    return run_label
