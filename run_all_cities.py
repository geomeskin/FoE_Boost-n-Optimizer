# ===============================
# FILE: run_all_cities.py
# ===============================
# Runs the full pipeline for the latest export file per city,
# then prints the cross-city assessment.
# Cleans up old output folders and input exports automatically.
# Used by the Windows Task Scheduler weekly job.

import re
import shutil
import subprocess
import sys
from pathlib import Path

INPUT_DIR  = Path(__file__).resolve().parent / "data" / "input"
OUTPUT_DIR = Path(__file__).resolve().parent / "data" / "output"

KEEP_OUTPUTS = 2   # output folders to keep per city (current + previous)
KEEP_INPUTS  = 1   # input export files to keep per city (latest only)


def _city_name(filename):
    stem = Path(filename).stem
    stem = re.sub(r"^Full",      "", stem)
    stem = re.sub(r"_Export.*$", "", stem, flags=re.IGNORECASE)
    return stem or "CITY"


def latest_per_city():
    """Return {city_name: Path} — most recently modified input file per city."""
    by_city = {}
    for f in INPUT_DIR.glob("Full*Export*.json"):
        city = _city_name(f.name)
        if city not in by_city or f.stat().st_mtime > by_city[city].stat().st_mtime:
            by_city[city] = f
    return by_city


def cleanup_inputs(keep=KEEP_INPUTS):
    """Delete older input exports, keeping the N most recent per city."""
    all_exports = list(INPUT_DIR.glob("Full*Export*.json"))
    by_city = {}
    for f in all_exports:
        by_city.setdefault(_city_name(f.name), []).append(f)

    removed = []
    for city, files in by_city.items():
        files.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        for old in files[keep:]:
            old.unlink()
            removed.append(old.name)

    if removed:
        print(f"  Removed old input exports: {', '.join(removed)}")


def cleanup_outputs(keep=KEEP_OUTPUTS):
    """Delete older output folders, keeping the N most recent per city."""
    all_folders = [p for p in OUTPUT_DIR.iterdir() if p.is_dir() and "_" in p.name]
    by_city = {}
    for folder in all_folders:
        city = folder.name.split("_")[0]
        by_city.setdefault(city, []).append(folder)

    removed = []
    for city, folders in by_city.items():
        folders.sort(key=lambda f: f.stat().st_mtime, reverse=True)
        for old in folders[keep:]:
            shutil.rmtree(old)
            removed.append(old.name)

    if removed:
        print(f"  Removed old output folders: {', '.join(removed)}")


def main():
    by_city = latest_per_city()

    if not by_city:
        print("No export files found in", INPUT_DIR)
        print("Drop Full*Export*.json files there and re-run.")
        sys.exit(1)

    print(f"Latest export per city:")
    for city, f in sorted(by_city.items()):
        print(f"  {city:8s}  ->  {f.name}")
    print()

    root = Path(__file__).resolve().parent
    for city, export in sorted(by_city.items()):
        print("=" * 60)
        print(f"Running pipeline: {city}  ({export.name})")
        print("=" * 60)
        result = subprocess.run(
            [sys.executable, "run_pipeline.py", "all", export.name],
            cwd=root
        )
        if result.returncode != 0:
            print(f"WARNING: pipeline failed for {export.name} (exit {result.returncode})")
        print()

    print("=" * 60)
    print("CROSS-CITY ASSESSMENT")
    print("=" * 60)
    subprocess.run([sys.executable, "run_pipeline.py", "compare"], cwd=root)

    print()
    print("Cleaning up old files...")
    cleanup_inputs(keep=KEEP_INPUTS)
    cleanup_outputs(keep=KEEP_OUTPUTS)
    print("  Done.")


if __name__ == "__main__":
    main()
