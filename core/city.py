# ===============================
# FILE: core/city.py
# ===============================

import config


class City:

    def __init__(self):
        self.grid      = [[None] * config.CITY_WIDTH for _ in range(config.CITY_HEIGHT)]
        self.townhall  = (config.CITY_WIDTH // 2, config.CITY_HEIGHT // 2)
        self.buildings = []   # list of (building_dict, x, y)
        self.roads     = set()

        tx, ty = self.townhall
        self.grid[ty][tx] = "TH"

    def in_bounds(self, x, y):
        return 0 <= x < config.CITY_WIDTH and 0 <= y < config.CITY_HEIGHT

    def can_place(self, x, y, w, h):
        for dy in range(h):
            for dx in range(w):
                nx, ny = x + dx, y + dy
                if not self.in_bounds(nx, ny) or self.grid[ny][nx] is not None:
                    return False
        return True

    def place_building(self, b, x, y):
        w, h = b["width"], b["height"]
        if not self.can_place(x, y, w, h):
            return False
        for dy in range(h):
            for dx in range(w):
                self.grid[y + dy][x + dx] = b["id"]
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
