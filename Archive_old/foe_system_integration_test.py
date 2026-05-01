import random
from collections import deque

GRID_W = 20
GRID_H = 20


# =========================================================
# CITY MODEL
# =========================================================
class City:

    def __init__(self):
        self.grid = [[None for _ in range(GRID_W)] for _ in range(GRID_H)]
        self.townhall = (10, 10)

        self.buildings = []   # (building, x, y)
        self.roads = set()

        self.place_townhall()

    # -----------------------------
    def place_townhall(self):
        x, y = self.townhall
        self.grid[y][x] = "TH"

    # -----------------------------
    def in_bounds(self, x, y):
        return 0 <= x < GRID_W and 0 <= y < GRID_H

    # -----------------------------
    def can_place(self, x, y, w, h):

        for dy in range(h):
            for dx in range(w):

                nx, ny = x + dx, y + dy

                if not self.in_bounds(nx, ny):
                    return False

                if self.grid[ny][nx] is not None:
                    return False

        return True

    # -----------------------------
    def place_building(self, b, x, y):

        w, h = b["width"], b["height"]

        if not self.can_place(x, y, w, h):
            return False

        for dy in range(h):
            for dx in range(w):

                nx, ny = x + dx, y + dy
                self.grid[ny][nx] = b["name"]

        self.buildings.append((b, x, y))
        return True

    # -----------------------------
    def place_road(self, x, y):

        if not self.in_bounds(x, y):
            return False

        if self.grid[y][x] is None:
            self.grid[y][x] = "R"
            self.roads.add((x, y))
            return True

        return False


# =========================================================
# STEP 1 — BUILDINGS
# =========================================================
def place_buildings(city, buildings):

    buildings = sorted(buildings, key=lambda x: x["value"], reverse=True)

    for b in buildings:

        placed = False

        for y in range(GRID_H):
            for x in range(GRID_W):

                if city.place_building(b, x, y):
                    placed = True
                    break

            if placed:
                break


# =========================================================
# STEP 2 — ROAD TARGETS
# =========================================================
def collect_road_targets(city):

    targets = []

    for b, x, y in city.buildings:

        if b.get("requires_road", False):

            # attach to top-left corner (stable deterministic anchor)
            targets.append((x, y))

    return targets


# =========================================================
# STEP 3 — CORRECT ROAD SYSTEM (SPANNING TREE BFS)
# =========================================================
def build_roads(city, targets):

    tx, ty = city.townhall

    queue = deque()
    queue.append((tx, ty))

    visited = set()
    targets = set(targets)

    while queue:

        x, y = queue.popleft()

        if (x, y) in visited:
            continue

        visited.add((x, y))

        # place road
        city.place_road(x, y)

        # check if this road node satisfies any target adjacency
        for t in list(targets):

            tx2, ty2 = t

            if abs(tx2 - x) + abs(ty2 - y) == 1:
                targets.remove(t)

        # expand outward (this creates branching naturally)
        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:

            nx, ny = x + dx, y + dy

            if city.in_bounds(nx, ny):
                queue.append((nx, ny))


# =========================================================
# STEP 4 — VALIDATION
# =========================================================
def validate_road_network(city):

    tx, ty = city.townhall

    visited = set()
    queue = deque([(tx, ty)])

    while queue:

        x, y = queue.popleft()

        if (x, y) in visited:
            continue

        visited.add((x, y))

        for dx, dy in [(1,0),(-1,0),(0,1),(0,-1)]:

            nx, ny = x + dx, y + dy

            if city.in_bounds(nx, ny):

                if city.grid[ny][nx] == "R":
                    queue.append((nx, ny))

    for r in city.roads:
        if r not in visited:
            return False

    return True


def validate_buildings(city):

    for b, x, y in city.buildings:

        if not b.get("requires_road", False):
            continue

        touched = False

        for dy in range(b["height"]):
            for dx in range(b["width"]):

                bx, by = x + dx, y + dy

                for ox, oy in [(1,0),(-1,0),(0,1),(0,-1)]:

                    nx, ny = bx + ox, by + oy

                    if city.in_bounds(nx, ny):
                        if city.grid[ny][nx] == "R":
                            touched = True

        if not touched:
            return False

    return True


# =========================================================
# TEST CONFIG
# =========================================================
TEST_BUILDINGS = [
    {"name": "A", "width": 2, "height": 2, "value": 10, "requires_road": True},
    {"name": "B", "width": 3, "height": 3, "value": 20, "requires_road": True},
    {"name": "C", "width": 1, "height": 1, "value": 5,  "requires_road": False},
    {"name": "D", "width": 2, "height": 1, "value": 12, "requires_road": True},
]


# =========================================================
# MAIN TEST
# =========================================================
def run_test():

    print("\n🧪 FOE INTEGRATION TEST (FIXED ROAD ARCHITECTURE)\n")

    city = City()

    # STEP 1
    print("Step 1: Place buildings")
    place_buildings(city, TEST_BUILDINGS)

    # STEP 2
    print("Step 2: Collect road targets")
    targets = collect_road_targets(city)

    # STEP 3
    print("Step 3: Build road network")
    build_roads(city, targets)

    # STEP 4
    print("Step 4: Validate system")

    road_ok = validate_road_network(city)
    building_ok = validate_buildings(city)

    print("\nRESULTS:")

    if road_ok and building_ok:
        print("✅ SYSTEM VALID — full constraints satisfied")
    else:
        print("❌ SYSTEM FAILURES:")
        if not road_ok:
            print(" - Road network not fully connected to Town Hall")
        if not building_ok:
            print(" - Building road adjacency constraint failed")

    print("\nSummary:")
    print("Buildings placed:", len(city.buildings))
    print("Road tiles:", len(city.roads))


# =========================================================
# RUN
# =========================================================
if __name__ == "__main__":
    run_test()