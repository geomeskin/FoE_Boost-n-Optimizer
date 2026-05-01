# ===============================
# FILE: city_compare.py
# ===============================
# Cross-city assessment. Reads the latest output folder per city and
# prints a formatted report. Run standalone or via run_pipeline.py compare.

import json
import glob
from datetime import datetime

SEP_WIDE  = "=" * 64
SEP_THIN  = "-" * 64


def _detect_cities():
    """Auto-detect city names from existing output folders."""
    seen = set()
    cities = []
    for folder in sorted(glob.glob("data/output/*_*")):
        name = Path(folder).name
        city = name.rsplit("_", 2)[0]   # strip _YYYYMMDD_HHMMSS
        if city and city not in seen:
            seen.add(city)
            cities.append(city)
    return cities


def _latest(city):
    folders = sorted(glob.glob(f"data/output/{city}_*"))
    return folders[-1] if folders else None


def _load(city):
    folder = _latest(city)
    if not folder:
        return None, None
    path = folder + "/my_city.json"
    try:
        with open(path, encoding="utf-8") as f:
            return folder, json.load(f)
    except FileNotFoundError:
        return folder, None


def _top_producers(buildings, n=3):
    return sorted(buildings, key=lambda b: -b.get("daily_value", 0))[:n]


def _swap_names(buildings):
    return [b["name"] for b in buildings if b.get("replaceable")]


def _action(city, summary, buildings):
    swaps   = _swap_names(buildings)
    s_count = summary["balanced"]["tiers"]["S"]
    c_count = summary["balanced"]["tiers"]["C"]
    total   = summary["scored"]

    if total == 0:
        return "No scored buildings — drop any event building here for instant improvement"
    if summary["balanced"]["total_city_score"] < 5000:
        return "Critical: all C-tier production. Any event building is an upgrade"
    if s_count == 0:
        return f"0 S-tier buildings -- prioritize S-tier event buildings at next opportunity"
    if swaps:
        return f"Replace {len(swaps)} C-tier swap candidate(s) at next event opportunity"
    return "Solid foundation — keep stacking S/A-tier event buildings"


def run():
    print()
    print(SEP_WIDE)
    print(f"  FoE CITY ASSESSMENT  --  {datetime.now().strftime('%Y-%m-%d')}")
    print(SEP_WIDE)

    cities  = _detect_cities()
    results = {}
    for city in cities:
        folder, data = _load(city)
        if not data:
            print(f"\n  {city}: no data found (run the pipeline first)")
            continue

        s       = data["summary"]
        blds    = data["buildings"]
        t       = s["balanced"]["tiers"]
        score   = s["balanced"]["total_city_score"]
        swaps   = _swap_names(blds)
        top     = _top_producers(blds)
        src     = s["by_source"]
        ts      = folder.split("_", 1)[-1] if folder else "?"

        results[city] = {"summary": s, "buildings": blds, "score": score, "swaps": swaps}

        print()
        tier_str = f"S:{t['S']}  A:{t['A']}  B:{t['B']}  C:{t['C']}"
        flag = "  ** ALL C-TIER **" if t["S"] == 0 and t["A"] == 0 and t["B"] == 0 else ""
        print(f"  {city}  |  run: {ts}  |  {s['total_placed']} placed  |  {s['scored']} scored  |  score: {score:,.0f}")
        print(f"  Tiers (balanced):  {tier_str}{flag}")

        scored_src = f"entity_levels: {src.get('entity_levels',0)}  live-snapshot: {src.get('production_state',0)}  unscored: {s['unscored']}"
        print(f"  Scoring sources:   {scored_src}")

        if top:
            top_str = "  |  ".join(
                f"{b['name'][:30]} {b['daily_value']:,.0f}/day [{b['tier_balanced']}]"
                for b in top
            )
            print(f"  Top producers:     {top_str}")

        if swaps:
            print(f"  Swap candidates:   {', '.join(swaps)}")
        else:
            print(f"  Swap candidates:   None")

        print(f"  >> {_action(city, s, blds)}")

    if len(results) < 2:
        print()
        print(SEP_WIDE)
        return

    print()
    print(SEP_THIN)
    print("  CROSS-CITY SNAPSHOT")
    print(SEP_THIN)

    best_city  = max(results, key=lambda c: results[c]["score"])
    total_swaps = sum(len(v["swaps"]) for v in results.values())
    swap_str   = "  ".join(f"{c}:{len(results[c]['swaps'])}" for c in cities if c in results)

    print(f"  Best balanced score:    {best_city} ({results[best_city]['score']:,.0f})")

    s_leaders = {c: results[c]["summary"]["balanced"]["tiers"]["S"] for c in results}
    top_s = max(s_leaders, key=lambda c: s_leaders[c])
    print(f"  Most S-tier buildings:  {top_s} ({s_leaders[top_s]})")

    print(f"  Total swap candidates:  {total_swaps}   ({swap_str})")

    # Cross-city building appearances (deduplicated per city)
    name_cities = {}
    for city, v in results.items():
        for b in v["buildings"]:
            n = b["name"]
            if city not in name_cities.get(n, []):
                name_cities.setdefault(n, []).append(city)
    shared = {n: cs for n, cs in name_cities.items() if len(cs) > 1}
    if shared:
        print()
        print("  Buildings appearing in multiple cities:")
        for name, cities_found in sorted(shared.items(), key=lambda x: -len(x[1])):
            cities_str = " + ".join(cities_found)
            print(f"    {name[:40]:40s}  [{cities_str}]")

    print()
    print(SEP_WIDE)
    print()


if __name__ == "__main__":
    run()
