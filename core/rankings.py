# ===============================
# FILE: core/rankings.py
# ===============================

import csv
import config
from .io_utils import load_json, save_json

MODES = ["balanced", "GBG", "GE", "QI"]

# Happiness-only building types — their "value" is raw happiness points which
# aren't comparable to production output, so they're excluded from rankings.
# Towers are NOT excluded here: combat towers (Ritual Flames etc.) have att/def
# boost data and a real per-tile value even with zero production.
EXCLUDE_TYPES = {"decoration", "culture"}

# Per-mode weights applied to each boost type's max per_tile value.
# Scale is chosen so that strong combat buildings shift rank meaningfully
# relative to base efficiency (value/area), which ranges from ~1 to ~4000.
MODE_WEIGHTS = {
    "balanced": {
        "att_boost_attacker":     100,
        "def_boost_defender":     100,
        "def_boost_attacker":      80,
        "att_boost_defender":      80,
        "att_def_boost_attacker": 150,
        "att_def_boost_defender": 150,
    },
    "GBG": {
        "att_boost_attacker":     400,
        "att_def_boost_attacker": 500,
        "def_boost_attacker":     200,
        "att_boost_defender":      50,
        "def_boost_defender":      50,
        "att_def_boost_defender":  80,
    },
    "GE": {
        "att_boost_attacker":     200,
        "def_boost_defender":     300,
        "att_def_boost_attacker": 250,
        "def_boost_attacker":     150,
        "att_boost_defender":     150,
        "att_def_boost_defender": 300,
    },
    "QI": {
        "att_boost_attacker":     300,
        "att_def_boost_attacker": 350,
        "def_boost_attacker":     150,
        "att_boost_defender":      50,
        "def_boost_defender":      50,
        "att_def_boost_defender":  80,
    },
}

# Tier percentile cutoffs: S >= 90th, A >= 70th, B >= 40th, C below 40th
TIER_CUTS = [90, 70, 40]
TIER_LABELS = ["S", "A", "B", "C"]


def _load_boost_index():
    """Return dict: building_id -> {boost_type -> max per_tile across all eras}"""
    path = config.OUTPUT_DIR / "foe_boost_table.csv"
    index = {}
    with open(path, encoding="utf-8-sig") as f:
        for row in csv.DictReader(f):
            bid = row["building_id"]
            btype = row["boost_type"]
            try:
                pt = float(row["per_tile"])
            except (ValueError, KeyError):
                continue
            if pt <= 0:
                continue
            if bid not in index:
                index[bid] = {}
            index[bid][btype] = max(index[bid].get(btype, 0.0), pt)
    return index


def _mode_score(efficiency, boost_map, mode):
    weights = MODE_WEIGHTS.get(mode, MODE_WEIGHTS["balanced"])
    boost_contrib = sum(boost_map.get(btype, 0.0) * w for btype, w in weights.items())
    return round(efficiency + boost_contrib, 4)


def _percentile_value(sorted_vals, pct):
    """Return the value at the given percentile in a pre-sorted list."""
    idx = max(0, int(pct / 100 * len(sorted_vals)) - 1)
    return sorted_vals[idx]


def _assign_tiers(buildings, scores_by_id):
    for mode in MODES:
        mode_scores = sorted(scores_by_id[b["id"]][mode] for b in buildings)
        cutoffs = [_percentile_value(mode_scores, p) for p in TIER_CUTS]
        for b in buildings:
            s = scores_by_id[b["id"]][mode]
            if s >= cutoffs[0]:
                tier = "S"
            elif s >= cutoffs[1]:
                tier = "A"
            elif s >= cutoffs[2]:
                tier = "B"
            else:
                tier = "C"
            b.setdefault("tiers", {})[mode] = tier


def rank_buildings(buildings):
    boost_index = _load_boost_index()
    scored = []

    for b in buildings:
        if b.get("type") in EXCLUDE_TYPES:
            continue
        # Allow zero-production buildings only if they have att/def boost data
        if b.get("value", 0) <= 0 and b["id"] not in boost_index:
            continue
        area = max(1, b["width"] * b["height"])
        efficiency = round(b["value"] / area, 4)
        boost_map = boost_index.get(b["id"], {})
        scores = {mode: _mode_score(efficiency, boost_map, mode) for mode in MODES}

        scored.append({
            **b,
            "area": area,
            "efficiency": efficiency,
            "boost_summary": {k: round(v, 4) for k, v in boost_map.items()},
            "scores": scores,
        })

    scores_by_id = {b["id"]: b["scores"] for b in scored}
    _assign_tiers(scored, scores_by_id)

    scored.sort(key=lambda x: x["scores"]["balanced"], reverse=True)
    for i, b in enumerate(scored):
        b["rank"] = i + 1

    return scored


def run():
    print("=== RANKINGS STAGE ===")
    buildings = load_json(config.ENRICHED_BUILDINGS_FILE)
    ranked = rank_buildings(buildings)
    excluded = len(buildings) - len(ranked)

    print(f"Ranked {len(ranked)} buildings  (excluded {excluded} with value=0)")
    if ranked:
        print("Top 10 by balanced score:")
        for b in ranked[:10]:
            tiers = b.get("tiers", {})
            boosts = b.get("boost_summary", {})
            att = boosts.get("att_boost_attacker", 0) or boosts.get("att_def_boost_attacker", 0)
            print(
                f"  #{b['rank']:3d}  {b['name'][:35]:35s}  "
                f"eff={b['efficiency']:8.1f}  "
                f"att/tile={att:.2f}  "
                f"tiers: bal={tiers.get('balanced','?')} "
                f"GBG={tiers.get('GBG','?')} "
                f"GE={tiers.get('GE','?')} "
                f"QI={tiers.get('QI','?')}"
            )

    save_json(config.RANKED_BUILDINGS_FILE, ranked)
    print(f"Saved: {config.RANKED_BUILDINGS_FILE}")
