# ===============================
# FILE: core/scoring.py
# ===============================

from collections import defaultdict

TYPE_TO_ROLE = {
    "military":                  "combat",
    "production":                "economy",
    "residential":               "economy",
    "goods":                     "economy",
    "cultural_goods_production": "economy",
    "random_production":         "economy",
    "clan_power_production":     "economy",
    "culture":                   "culture",
    "decoration":                "culture",
    "diplomacy":                 "culture",
}

NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1)]

ADJ_BONUS = {
    ("economy", "economy"): 2,
    ("combat",  "combat"):  3,
    ("culture", "culture"): 1,
}


def _role(b):
    return TYPE_TO_ROLE.get(b.get("type", ""), "utility")


def compute_synergy(city, mode="balanced"):
    buildings = city.buildings
    cx, cy    = city.townhall
    grid      = city.grid

    role_positions = defaultdict(list)
    score = 0.0

    # base value + distance penalty
    for b, x, y in buildings:
        score += b.get("value", 0)
        score -= (abs(cx - x) + abs(cy - y)) * 0.15
        role_positions[_role(b)].append((x, y))

    # same-role clustering bonus (closer = better)
    for positions in role_positions.values():
        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):
                x1, y1 = positions[i]
                x2, y2 = positions[j]
                score -= (abs(x1 - x2) + abs(y1 - y2)) * 0.08

    # adjacency synergy
    for b, x, y in buildings:
        role = _role(b)
        adj  = 0
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if not city.in_bounds(nx, ny):
                continue
            cell = grid[ny][nx]
            if cell is None or cell in ("R", "TH"):
                continue
            for nb, bx, by in buildings:
                if bx <= nx < bx + nb["width"] and by <= ny < by + nb["height"]:
                    adj += ADJ_BONUS.get((_role(b), _role(nb)), 0.5)
        score += adj

    score -= len(city.roads) * 0.03

    if mode == "GE":
        return score * 1.1
    if mode == "QI":
        return score * 1.2 - len(city.roads) * 0.1

    return score
