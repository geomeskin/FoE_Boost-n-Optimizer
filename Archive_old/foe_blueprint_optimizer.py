import random
from foe_synergy_scoring_engine import compute_mode_synergy
from foe_adaptive_road_engine import build_roads


# =========================================================
# CITY MODEL
# =========================================================
GRID_W = 20
GRID_H = 20


class City:

    def __init__(self):
        self.grid = [[None for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.townhall = (10, 10)
        self.buildings = []
        self.roads = set()

        self.place_townhall()

    def place_townhall(self):
        x, y = self.townhall
        self.grid[y][x] = "TH"

    def in_bounds(self, x, y):
        return 0 <= x < GRID_W and 0 <= y < GRID_H

    def can_place(self, x, y, w, h):

        for dy in range(h):
            for dx in range(w):

                nx, ny = x + dx, y + dy

                if not self.in_bounds(nx, ny):
                    return False

                if self.grid[ny][nx] is not None:
                    return False

        return True

    def place_building(self, b, x, y):

        if not self.can_place(x, y, b["width"], b["height"]):
            return False

        for dy in range(b["height"]):
            for dx in range(b["width"]):

                nx, ny = x + dx, y + dy
                self.grid[ny][nx] = b["name"]

        self.buildings.append((b, x, y))
        return True

    def place_road(self, x, y):

        if not self.in_bounds(x, y):
            return False

        if self.grid[y][x] is None:
            self.grid[y][x] = "R"
            self.roads.add((x, y))
            return True

        return False


# =========================================================
# SCORE WRAPPER (SYNERGY ENGINE HOOK)
# =========================================================
def score(city):
    return compute_mode_synergy(city, mode="balanced")


# =========================================================
# BLUEPRINT INIT
# =========================================================
def initial_blueprint(buildings):

    bp = []

    for b in buildings:
        bp.append((
            b,
            random.randint(0, GRID_W - b["width"]),
            random.randint(0, GRID_H - b["height"])
        ))

    return bp


# =========================================================
# CITY BUILD FROM BLUEPRINT
# =========================================================
def build_city(blueprint):

    city = City()

    # 1. place buildings
    for b, x, y in blueprint:
        city.place_building(b, x, y)

    # 2. collect road targets
    targets = []

    for b, x, y in city.buildings:
        if b.get("requires_road", False):
            targets.append((x, y))

    # 3. adaptive road system (ONLY SYSTEM NOW)
    build_roads(city, targets)

    return city


# =========================================================
# MUTATION
# =========================================================
def mutate(bp):

    new_bp = bp.copy()

    i = random.randint(0, len(new_bp) - 1)

    b, _, _ = new_bp[i]

    new_bp[i] = (
        b,
        random.randint(0, GRID_W - b["width"]),
        random.randint(0, GRID_H - b["height"])
    )

    return new_bp


# =========================================================
# OPTIMIZER LOOP
# =========================================================
def optimize(buildings, iterations=300):

    blueprint = initial_blueprint(buildings)

    best_bp = blueprint
    best_city = build_city(blueprint)
    best_score = score(best_city)

    for i in range(iterations):

        candidate_bp = mutate(blueprint)

        candidate_city = build_city(candidate_bp)
        candidate_score = score(candidate_city)

        if candidate_score > best_score:
            best_bp = candidate_bp
            best_city = candidate_city
            best_score = candidate_score
            blueprint = candidate_bp

        if i % 50 == 0:
            print(f"Iter {i} | Score {best_score:.2f} | Roads {len(best_city.roads)}")

    return best_city


# =========================================================
# TEST RUN
# =========================================================
if __name__ == "__main__":

    TEST_BUILDINGS = [
        {"name": "A", "width": 2, "height": 2, "value": 10, "requires_road": True},
        {"name": "B", "width": 3, "height": 3, "value": 20, "requires_road": True},
        {"name": "C", "width": 1, "height": 1, "value": 5,  "requires_road": False},
        {"name": "D", "width": 2, "height": 1, "value": 12, "requires_road": True},
    ]

    best = optimize(TEST_BUILDINGS)

    print("\nFINAL RESULT")
    print("Buildings:", len(best.buildings))
    print("Road tiles:", len(best.roads))
    print("Final score:", score(best))