# FoE Boost-n-Optimizer

A city analysis and optimization tool for **Forge of Empires** players using the [FoE Helper](https://foe-helper.com/) browser extension.

Export your city, run the pipeline, get an instant tier-graded assessment of every building — across all your cities.

---

## What it does

- **Ranks all 689+ game buildings** into S / A / B / C tiers across 4 combat modes (Balanced, GBG, GE, QI)
- **Audits your actual city** — grades every building you've placed against the tier system
- **Flags swap candidates** — C-tier production buildings worth replacing at the next event
- **Generates a self-contained HTML report** — sortable, searchable, no server needed
- **Compares across multiple cities** — one assessment covering all your accounts

---

## Requirements

- Python 3.10+
- No external packages — stdlib only

---

## Setup

1. Clone the repo
2. `enriched_buildings.json` is already in `data/input/` — the game building catalog, included
3. Export your city from FoE Helper:
   - Open FoE Helper → City Planner → Copy to Clipboard
   - Save the JSON file to `data/input/`
   - Name it `Full<CityName>_Export*.json` e.g. `FullMyCity_Export_20260501.json`

---

## Running

**Single city, full pipeline:**

```bash
py run_pipeline.py all FullMyCity_Export.json
```

**All cities at once + cross-city assessment:**

```bash
py run_all_cities.py
```

**Cross-city assessment only (uses latest runs):**

```bash
py run_pipeline.py compare
```

Output lands in `data/output/<CityName>_<timestamp>/` — open `report.html` in any browser.

---

## Pipeline stages

| Stage | Output |
| --- | --- |
| `extract` | `city_entities.json` — game building database |
| `abilities` | Ability classification files |
| `boosts` | `foe_boost_table.csv` — per-tile boost values |
| `rankings` | `ranked_buildings.json` — 689 buildings, S/A/B/C tiers per mode |
| `report` | `report_rankings.csv`, `report_mode_movers.csv` |
| `my_city` | `my_city.json`, `report_my_city.csv` — your placed buildings graded |
| `html` | `report.html` — self-contained, sortable/searchable |
| `optimize` | `optimized_layout.json` — hill-climbing layout optimizer |
| `compare` | Cross-city assessment printed to console |

Run a single stage: `py run_pipeline.py <stage> <export_file.json>`

---

## Modes

| Mode | Focus |
| --- | --- |
| `balanced` | Overall production efficiency |
| `GBG` | Guild Battlegrounds — heavy attack weight |
| `GE` | Guild Expeditions — balanced attack + defense |
| `QI` | Quantum Incursions — attack focused |

---

## Tier system

Tiers are computed from the full population of ranked game buildings:

| Tier | Percentile | Meaning |
| --- | --- | --- |
| S | Top 10% | Elite — keep and prioritize |
| A | 10-30% | Strong — solid contributors |
| B | 30-60% | Average — fine for now |
| C | Bottom 40% | Below average — replace when possible |

Buildings marked **swap?** in the HTML report are C-tier with full scoring — legitimate replacement candidates.

---

## Multiple cities

Drop multiple export files into `data/input/` — one per city.
`run_all_cities.py` detects the latest export per city automatically, runs all pipelines, and prints a cross-city comparison. Auto-cleanup keeps the 2 most recent output runs and latest input per city.

---

## Updating the game catalog

`enriched_buildings.json` covers all current game eras. Refresh it when a new era is released by replacing the file with an updated export from the game.

---

## License

MIT
---nothing follows ---
