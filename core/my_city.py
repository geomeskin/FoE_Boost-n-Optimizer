# ===============================
# FILE: core/my_city.py
# ===============================
#
# Audits your actual placed city (CityMapData) against the tier system.
# Scoring sources (in priority order):
#   1. ranked_buildings.json — entity_levels scoring (most complete)
#   2. CityMapData.state.current_product — live production snapshot
#   3. Unscored — passive buildings, Great Buildings, happiness providers

import csv
import json
import config
from .io_utils import load_json, save_json

SKIP_TYPES = {"street", "off_grid", "hub_part", "hub_main", "outpost_ship", "friends_tavern"}
TIER_ORDER = {"S": 4, "A": 3, "B": 2, "C": 1}
MODES = ["balanced", "GBG", "GE", "QI"]

# Value weights per resource unit per day — same scale as entity_levels scoring
RESOURCE_WEIGHTS = {
    "money":           0.001,
    "supplies":        0.002,
    "strategy_points": 50.0,
    "forge_points":    50.0,
    "medals":          10.0,
}
GOODS_WEIGHT = 5.0   # era-specific goods (nutrition_research, smart_materials, etc.)


def _load_export():
    with open(config.INPUT_FILE, encoding="utf-8") as f:
        return json.load(f)


def _build_tier_index(ranked):
    return {b["id"]: b for b in ranked}


def _tier_cutoffs(ranked):
    """Efficiency value at each tier boundary (S/A/B) from the full building population."""
    scores = sorted(b["efficiency"] for b in ranked)
    n = len(scores)
    return {
        "S": scores[max(0, int(0.90 * n) - 1)],
        "A": scores[max(0, int(0.70 * n) - 1)],
        "B": scores[max(0, int(0.40 * n) - 1)],
    }


def _tier_from_efficiency(eff, cuts):
    if eff >= cuts["S"]: return "S"
    if eff >= cuts["A"]: return "A"
    if eff >= cuts["B"]: return "B"
    return "C"


def _att_per_tile(boost):
    return max(
        boost.get("att_boost_attacker",     0),
        boost.get("att_def_boost_attacker", 0),
        boost.get("att_boost_defender",     0),
        boost.get("att_def_boost_defender", 0),
    )


def _def_per_tile(boost):
    return max(
        boost.get("def_boost_defender",     0),
        boost.get("att_def_boost_defender", 0),
        boost.get("def_boost_attacker",     0),
        boost.get("att_def_boost_attacker", 0),
    )


def _score_from_state(placed, ent):
    """
    Compute efficiency from live production snapshot.
    Returns (efficiency, daily_value, resource_summary) or None if no state data.
    """
    state    = placed.get("state", {})
    prod     = state.get("current_product", {})
    resources = prod.get("product", {}).get("resources", {})
    if not resources:
        return None

    prod_time        = max(1, prod.get("production_time", 86400))
    daily_multiplier = 86400 / prod_time

    daily_value = 0.0
    for res, amount in resources.items():
        weight = RESOURCE_WEIGHTS.get(res, GOODS_WEIGHT)
        daily_value += amount * daily_multiplier * weight

    area = max(1, ent.get("width", 1) * ent.get("length", 1))
    efficiency = round(daily_value / area, 4)

    res_summary = {r: round(v * daily_multiplier, 1) for r, v in resources.items()}
    return efficiency, round(daily_value, 2), res_summary


def extract_my_buildings(export, tier_index, cuts):
    city_map      = export["CityMapData"]
    city_entities = export["CityEntities"]

    scored   = []   # buildings with full or partial scores
    unscored = []   # passive/happiness buildings we can't score

    for placement_id, placed in city_map.items():
        if placed["type"] in SKIP_TYPES:
            continue

        eid    = placed.get("cityentity_id", "")
        ent    = city_entities.get(eid, {})
        ranked = tier_index.get(eid)

        base = {
            "placement_id": placement_id,
            "id":           eid,
            "name":         ent.get("name", eid),
            "type":         placed["type"],
            "width":        ent.get("width",  1),
            "height":       ent.get("length", 1),
            "area":         max(1, ent.get("width", 1) * ent.get("length", 1)),
            "current_x":    placed.get("x", 0),
            "current_y":    placed.get("y", 0),
            "connected":    placed.get("connected", 0),
        }

        if ranked:
            # Source 1: full entity_levels scoring — most complete
            boost = ranked.get("boost_summary", {})
            base.update({
                "scoring_source":  "entity_levels",
                "efficiency":      ranked.get("efficiency", 0),
                "daily_value":     round(ranked.get("efficiency", 0) * base["area"], 1),
                "daily_resources": {},
                "att_per_tile":    round(_att_per_tile(boost), 4),
                "def_per_tile":    round(_def_per_tile(boost), 4),
                "score_balanced":  ranked["scores"].get("balanced", 0),
                "score_GBG":       ranked["scores"].get("GBG",      0),
                "score_GE":        ranked["scores"].get("GE",       0),
                "score_QI":        ranked["scores"].get("QI",       0),
                "tier_balanced":   ranked["tiers"].get("balanced", "?"),
                "tier_GBG":        ranked["tiers"].get("GBG",      "?"),
                "tier_GE":         ranked["tiers"].get("GE",       "?"),
                "tier_QI":         ranked["tiers"].get("QI",       "?"),
                "rank_balanced":   ranked.get("rank", "?"),
                "replaceable":     ranked["tiers"].get("balanced") == "C",
            })
            scored.append(base)

        else:
            # Source 2: live production state snapshot
            state_result = _score_from_state(placed, ent)
            if state_result:
                eff, daily_val, res_summary = state_result
                tier = _tier_from_efficiency(eff, cuts)
                base.update({
                    "scoring_source":  "production_state",
                    "efficiency":      eff,
                    "daily_value":     daily_val,
                    "daily_resources": res_summary,
                    "att_per_tile":    0,
                    "def_per_tile":    0,
                    "score_balanced":  eff,
                    "score_GBG":       eff,
                    "score_GE":        eff,
                    "score_QI":        eff,
                    "tier_balanced":   tier,
                    "tier_GBG":        tier,
                    "tier_GE":         tier,
                    "tier_QI":         tier,
                    "rank_balanced":   "~",
                    "replaceable":     False,
                })
                scored.append(base)
            else:
                # Source 3: unscored — passive/special building
                base.update({
                    "scoring_source":  "unscored",
                    "efficiency":      0,
                    "daily_value":     0,
                    "daily_resources": {},
                    "att_per_tile":    0,
                    "def_per_tile":    0,
                    "score_balanced":  0,
                    "score_GBG":       0,
                    "score_GE":        0,
                    "score_QI":        0,
                    "tier_balanced":   "—",
                    "tier_GBG":        "—",
                    "tier_GE":         "—",
                    "tier_QI":         "—",
                    "rank_balanced":   "—",
                })
                unscored.append(base)

    return scored, unscored


def build_summary(scored, unscored):
    total = len(scored) + len(unscored)
    by_source = {}
    for b in scored:
        s = b["scoring_source"]
        by_source[s] = by_source.get(s, 0) + 1

    summary = {
        "total_placed": total,
        "scored":       len(scored),
        "unscored":     len(unscored),
        "by_source":    by_source,
    }

    for mode in MODES:
        tier_counts  = {"S": 0, "A": 0, "B": 0, "C": 0}
        total_score  = 0.0
        for b in scored:
            t = b.get(f"tier_{mode}", "")
            if t in tier_counts:
                tier_counts[t] += 1
            total_score += b.get(f"score_{mode}", 0) * b.get("area", 1)
        summary[mode] = {"tiers": tier_counts, "total_city_score": round(total_score, 1)}

    return summary


def _write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames, extrasaction="ignore")
        w.writeheader()
        w.writerows(rows)


def run():
    print("=== MY CITY STAGE ===")

    ranked     = load_json(config.RANKED_BUILDINGS_FILE)
    tier_index = _build_tier_index(ranked)
    cuts       = _tier_cutoffs(ranked)

    print(f"Tier cutoffs (from {len(ranked)} game buildings):")
    print(f"  S >= {cuts['S']:.1f}  |  A >= {cuts['A']:.1f}  |  B >= {cuts['B']:.1f}")
    print()
    print("Loading city export...")
    export = _load_export()

    scored, unscored = extract_my_buildings(export, tier_index, cuts)
    summary = build_summary(scored, unscored)

    # Sort: by tier then score
    scored.sort(key=lambda b: (
        -TIER_ORDER.get(b["tier_balanced"], 0),
        -b["score_balanced"]
    ))
    unscored.sort(key=lambda b: b["name"])

    # Save JSON
    output = {"summary": summary, "buildings": scored, "unscored": unscored}
    save_json(config.MY_CITY_FILE, output)

    # Save CSV — all scored buildings
    csv_fields = [
        "replaceable", "rank_balanced", "name", "type", "scoring_source",
        "width", "height", "area", "connected", "current_x", "current_y",
        "efficiency", "daily_value", "att_per_tile", "def_per_tile",
        "score_balanced", "score_GBG", "score_GE", "score_QI",
        "tier_balanced", "tier_GBG", "tier_GE", "tier_QI",
    ]
    _write_csv(config.MY_CITY_CSV, scored, csv_fields)

    # Console output
    print(f"Your city: {summary['total_placed']} buildings total")
    src = summary["by_source"]
    print(f"  entity_levels scored:    {src.get('entity_levels', 0)}")
    print(f"  production_state scored: {src.get('production_state', 0)}")
    print(f"  unscored (passive):      {summary['unscored']}")
    print()
    for mode in MODES:
        t     = summary[mode]["tiers"]
        score = summary[mode]["total_city_score"]
        print(
            f"  {mode:8s}  S:{t['S']:3d}  A:{t['A']:3d}  B:{t['B']:3d}  C:{t['C']:3d}"
            f"  |  city score: {score:,.0f}"
        )

    print()
    print("Your scored buildings (best first):")
    for b in scored:
        src_tag = "*" if b["scoring_source"] == "entity_levels" else "~"
        print(
            f"  {src_tag} {b['tier_balanced']} | {b['name'][:38]:38s}  "
            f"eff={b['efficiency']:8.1f}  "
            f"daily={b['daily_value']:8.1f}  "
            f"GBG={b['tier_GBG']}"
        )

    print()
    print(f"Unscored buildings ({len(unscored)}) — passive/Great Buildings:")
    for b in unscored[:15]:
        print(f"  {b['name'][:45]:45s}  [{b['type']}]")
    if len(unscored) > 15:
        print(f"  ... and {len(unscored) - 15} more")

    print(f"\nSaved: {config.MY_CITY_FILE}")
    print(f"Saved: {config.MY_CITY_CSV}")
