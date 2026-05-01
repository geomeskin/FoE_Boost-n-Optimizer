# ===============================
# FILE: core/roads.py
# ===============================

from collections import deque

NEIGHBORS = [(1, 0), (-1, 0), (0, 1), (0, -1)]


def collect_road_targets(city):
    return [(x, y) for b, x, y in city.buildings if b.get("requires_road", True)]


def build_roads(city, targets):
    """BFS spanning tree from Town Hall; stops once all targets are adjacent to road."""
    tx, ty   = city.townhall
    queue    = deque([(tx, ty)])
    visited  = set()
    remaining = set(map(tuple, targets))

    while queue and remaining:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        city.place_road(x, y)

        for t in list(remaining):
            if abs(t[0] - x) + abs(t[1] - y) == 1:
                remaining.discard(t)

        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if city.in_bounds(nx, ny) and (nx, ny) not in visited:
                queue.append((nx, ny))


def validate_roads(city):
    tx, ty  = city.townhall
    visited = set()
    queue   = deque([(tx, ty)])

    while queue:
        x, y = queue.popleft()
        if (x, y) in visited:
            continue
        visited.add((x, y))
        for dx, dy in NEIGHBORS:
            nx, ny = x + dx, y + dy
            if city.in_bounds(nx, ny) and city.grid[ny][nx] == "R":
                queue.append((nx, ny))

    if not all(r in visited for r in city.roads):
        return False, "Road network not fully connected to Town Hall"

    for b, x, y in city.buildings:
        if not b.get("requires_road", True):
            continue
        adjacent = False
        for dy in range(b["height"]):
            for dx in range(b["width"]):
                for ox, oy in NEIGHBORS:
                    nx, ny = x + dx + ox, y + dy + oy
                    if city.in_bounds(nx, ny) and city.grid[ny][nx] == "R":
                        adjacent = True
        if not adjacent:
            return False, f"Building '{b['name']}' at ({x},{y}) has no road access"

    return True, "OK"
