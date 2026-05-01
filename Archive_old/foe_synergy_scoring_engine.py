from collections import defaultdict


# =========================================================
# BUILDING ROLE CLASSIFICATION
# =========================================================
def classify_building(b):

    name = b["name"].lower()

    # Combat-oriented buildings
    if any(k in name for k in ["attack", "def", "military", "barracks"]):
        return "combat"

    # Economy / production buildings
    if any(k in name for k in ["farm", "production", "coin", "goods"]):
        return "economy"

    # Event / misc buildings
    return "utility"


# =========================================================
# SYNERGY MODEL CORE
# =========================================================
def compute_synergy(city):

    grid = city.grid
    buildings = city.buildings

    cx, cy = city.townhall

    # grouping by type
    type_positions = defaultdict(list)
    score = 0

    # -----------------------------------------------------
    # BASE VALUE + ROLE TAGGING
    # -----------------------------------------------------
    for b, x, y in buildings:

        role = classify_building(b)

        # base value
        score += b["value"]

        type_positions[role].append((x, y))

        # distance pressure (encourages clustering near center)
        dist = abs(cx - x) + abs(cy - y)
        score -= dist * 0.15

    # -----------------------------------------------------
    # TYPE CLUSTERING BONUS (KEY MECHANIC)
    # -----------------------------------------------------
    for role, positions in type_positions.items():

        for i in range(len(positions)):
            for j in range(i + 1, len(positions)):

                x1, y1 = positions[i]
                x2, y2 = positions[j]

                d = abs(x1 - x2) + abs(y1 - y2)

                # closer = better (encourages districts)
                score -= d * 0.08

    # -----------------------------------------------------
    # ADJACENCY SYNERGY (FOE-STYLE MECHANIC)
    # -----------------------------------------------------
    for b, x, y in buildings:

        role = classify_building(b)

        adjacency_bonus = 0

        # check 4-neighbourhood
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:

            nx, ny = x + dx, y + dy

            if not city.in_bounds(nx, ny):
                continue

            cell = grid[ny][nx]

            if cell is None or cell in ["R", "TH"]:
                continue

            # find neighbor building
            for nb, bx, by in buildings:

                if bx <= nx < bx + nb["width"] and by <= ny < by + nb["height"]:

                    neighbor_role = classify_building(nb)

                    # synergy rules
                    if role == "economy" and neighbor_role == "economy":
                        adjacency_bonus += 2

                    if role == "combat" and neighbor_role == "combat":
                        adjacency_bonus += 3

                    if role != neighbor_role:
                        adjacency_bonus += 1

        score += adjacency_bonus

    # -----------------------------------------------------
    # ROAD COST (LIGHT BUT MEANINGFUL)
    # -----------------------------------------------------
    score -= len(city.roads) * 0.03

    return score


# =========================================================
# MODE SWITCH (GE / GBG / QI READY HOOK)
# =========================================================
def compute_mode_synergy(city, mode="balanced"):

    base = compute_synergy(city)

    if mode == "GE":
        # emphasize combat clustering
        return base * 1.1

    if mode == "GBG":
        # balanced economy + compactness
        return base * 1.0

    if mode == "QI":
        # reward density / efficiency
        return base * 1.2 - len(city.roads) * 0.1

    return base