# ===============================
# FILE: core/optimizer.py
# ===============================

import random
import config
from .city import City
from .roads import collect_road_targets, build_roads
from .scoring import compute_synergy
from .io_utils import load_json, save_json

POOL_SIZE    = 80    # top-N candidates to consider per mode
INITIAL_SIZE = 40    # how many to seed the initial layout with
SWAP_PROB    = 0.25  # chance a mutation swaps a building vs. relocates it

# att boost per tile threshold to classify a building as a combat role
COMBAT_ATT_THRESHOLD = 0.5


def select_candidates(ranked, mode, n=POOL_SIZE):
    """Return top-n buildings sorted by their mode score (already per-tile)."""
    valid = [b for b in ranked if b.get("scores", {}).get(mode, 0) > 0]
    valid.sort(key=lambda b: b["scores"][mode], reverse=True)
    return valid[:n]


def annotate(b, mode):
    """
    Attach optimizer-private fields so scoring can use mode-aware values
    without touching the original building dict.
    """
    area       = max(1, b["width"] * b["height"])
    mode_score = b.get("scores", {}).get(mode, b.get("efficiency", 0))
    boost      = b.get("boost_summary", {})
    att = max(
        boost.get("att_boost_attacker",     0),
        boost.get("att_def_boost_attacker", 0),
    )
    effective_role = "combat" if att >= COMBAT_ATT_THRESHOLD else None
    return {
        **b,
        "_mode_value":     mode_score * area,
        "_mode_score":     mode_score,
        "_effective_role": effective_role,  # None = fall back to type-based role
    }


# ------------------------------------------------------------------
# City construction
# ------------------------------------------------------------------

def _build_city(blueprint):
    city = City()
    for b, x, y in blueprint:
        city.place_building(b, x, y)
    build_roads(city, collect_road_targets(city))
    return city


def _initial_blueprint(buildings):
    bp = []
    for b in buildings:
        x = random.randint(0, max(0, config.CITY_WIDTH  - b["width"]))
        y = random.randint(0, max(0, config.CITY_HEIGHT - b["height"]))
        bp.append((b, x, y))
    return bp


# ------------------------------------------------------------------
# Mutations
# ------------------------------------------------------------------

def _mutate_relocate(bp):
    """Move one random building to a new random position."""
    new_bp = list(bp)
    i = random.randint(0, len(new_bp) - 1)
    b, _, _ = new_bp[i]
    new_bp[i] = (
        b,
        random.randint(0, max(0, config.CITY_WIDTH  - b["width"])),
        random.randint(0, max(0, config.CITY_HEIGHT - b["height"])),
    )
    return new_bp


def _mutate_swap(bp, pool):
    """
    Replace one building in the layout with a different one from the pool.
    Falls back to relocate if the pool has no unused candidates.
    """
    placed_ids   = {b["id"] for b, _, _ in bp}
    alternatives = [b for b in pool if b["id"] not in placed_ids]
    if not alternatives:
        return _mutate_relocate(bp)
    new_bp = list(bp)
    i      = random.randint(0, len(new_bp) - 1)
    new_b  = random.choice(alternatives)
    new_bp[i] = (
        new_b,
        random.randint(0, max(0, config.CITY_WIDTH  - new_b["width"])),
        random.randint(0, max(0, config.CITY_HEIGHT - new_b["height"])),
    )
    return new_bp


# ------------------------------------------------------------------
# Hill-climbing optimizer
# ------------------------------------------------------------------

def optimize(initial_buildings, pool, iterations=None, mode="balanced"):
    if iterations is None:
        iterations = config.ITERATIONS

    best_bp    = _initial_blueprint(initial_buildings)
    best_city  = _build_city(best_bp)
    best_score = compute_synergy(best_city, mode=mode)

    for i in range(iterations):
        if random.random() < SWAP_PROB:
            candidate_bp = _mutate_swap(best_bp, pool)
        else:
            candidate_bp = _mutate_relocate(best_bp)

        candidate_city  = _build_city(candidate_bp)
        candidate_score = compute_synergy(candidate_city, mode=mode)

        if candidate_score > best_score:
            best_bp, best_city, best_score = candidate_bp, candidate_city, candidate_score

        if i % 100 == 0:
            print(
                f"  Iter {i:4d} | Score {best_score:8.2f} | "
                f"Buildings {len(best_city.buildings):3d} | Roads {len(best_city.roads):3d}"
            )

    return best_city, best_score


# ------------------------------------------------------------------
# Output
# ------------------------------------------------------------------

def layout_to_dict(city, score, mode):
    return {
        "score":            round(score, 4) if score is not None else None,
        "mode":             mode,
        "buildings_placed": len(city.buildings),
        "road_tiles":       len(city.roads),
        "placements": [
            {
                "id":     b["id"],
                "name":   b["name"],
                "type":   b.get("type", ""),
                "x":      x,
                "y":      y,
                "width":  b["width"],
                "height": b["height"],
                "tier":   b.get("tiers", {}).get(mode, "?"),
                "mode_score": round(b.get("_mode_score", 0), 2),
            }
            for b, x, y in city.buildings
        ],
        "roads": sorted(list(city.roads)),
    }


# ------------------------------------------------------------------
# Pipeline entry point
# ------------------------------------------------------------------

def run(mode="balanced"):
    print(f"=== OPTIMIZER STAGE  (mode={mode}) ===")
    ranked = load_json(config.RANKED_BUILDINGS_FILE)

    pool    = [annotate(b, mode) for b in select_candidates(ranked, mode, POOL_SIZE)]
    initial = pool[:INITIAL_SIZE]

    print(f"Candidate pool : {len(pool)} buildings")
    print(f"Initial layout : {len(initial)} buildings")
    print(f"Mode           : {mode}")
    print()
    print("Top 5 candidates:")
    for b in pool[:5]:
        tiers = b.get("tiers", {})
        print(
            f"  {b['name'][:40]:40s}  "
            f"score={b['_mode_score']:7.1f}  "
            f"tier={tiers.get(mode, '?')}"
        )
    print()

    city, score = optimize(initial, pool, mode=mode)
    result      = layout_to_dict(city, score, mode)

    # Console summary
    print()
    print(f"Final score      : {score:.2f}")
    print(f"Buildings placed : {len(city.buildings)}")
    print(f"Road tiles       : {len(city.roads)}")
    print()
    placed_by_tier = {}
    for p in result["placements"]:
        t = p["tier"]
        placed_by_tier[t] = placed_by_tier.get(t, 0) + 1
    for tier in ["S", "A", "B", "C", "?"]:
        if tier in placed_by_tier:
            print(f"  {tier}-tier placed: {placed_by_tier[tier]}")

    save_json(config.OPTIMIZED_LAYOUT_FILE, result)
    print(f"\nSaved: {config.OPTIMIZED_LAYOUT_FILE}")
