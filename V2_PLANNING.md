# FoE Boost-n-Optimizer — V2 Planning

## What V1 Delivers
- Full in-browser pipeline powered by Pyodide (Python → WebAssembly)
- Hosted on GitHub Pages — no server, no account, no data stored
- User uploads their FoE Helper city export (~37 MB JSON)
- Pipeline runs all stages: extract → abilities → boosts → rankings → my_city → html report
- Self-contained HTML report with 3 tabs: Rankings, Mode Movers, My City
- S/A/B/C tier system across 4 modes: Balanced, GBG, GE, QI
- My City tab shows placed buildings, flags C-tier swap candidates
- Happiness-only building types (decoration, culture, tower) excluded from rankings

---

## Known Limitations Going into V2

### 1. Hard-coded scoring weights
The two sets of weights in the pipeline are currently fixed constants:

**MODE_WEIGHTS** (`core/rankings.py`) — how much each combat boost type contributes
to a building's score in each game mode. These were hand-tuned, not derived from any
established source. Scale was chosen so combat buildings shift rank meaningfully
relative to base efficiency (~1 to ~4000 range).

**RESOURCE_WEIGHTS** (`core/my_city.py`) — how much each resource type is worth
per unit per day when scoring live production buildings:
- coins (money): 0.001
- supplies: 0.002
- forge points / strategy points: 50.0
- medals: 10.0
- era goods: 5.0

These weights reflect general FoE community consensus (FPs are most valuable) but
are still opinions, not facts. Different playstyles warrant different weights.

### 2. The `value` field in enriched_buildings.json
The `value` field comes from the FoE_Bldg_DB repo (a separate codebase). It's a
pre-aggregated composite number — the exact formula isn't visible in this repo.
For happiness buildings it equals raw happiness points, which is why decoration/
culture types had to be excluded. For production buildings the basis is less clear
without reading FoE_Bldg_DB. This is the root of the entire scoring chain and worth
understanding better before V2.

### 3. Rankings use static game database values, not your actual building levels
Rankings reflect reference-level values from enriched_buildings.json — not what
your specific buildings produce at their current level. My City partially bridges
this via the live production snapshot, but it's incomplete coverage.

### 4. No user control over weights
FoE Helper's "Building Efficiency Rating" dialog lets users assign multipliers for
every output category. This tool currently offers only 4 preset modes. Power users
who want to optimize specifically for FPs, or specifically for GBG attack, can't
tune it beyond those presets.

### 5. Optimizer not included in web version
The hill-climbing optimizer (`core/optimizer.py`) was excluded from V1. It's
compute-intensive and untested in Pyodide. Could be a V2 addition if performance
is acceptable.

---

## V2 Feature Ideas

### HIGH PRIORITY

**User-configurable weights (sliders)**
The single most impactful V2 feature. Model it on FoE Helper's approach:
let users set multipliers for each output category (FPs, goods, coins, supplies,
attack boost, defense boost, etc.). Rankings re-compute client-side when weights
change. Implementation path:
- Add a "Customize Weights" panel to the web UI (collapsible, defaults to current
  preset values)
- Pass user weights into the Pyodide pipeline before running rankings
- Re-run only the rankings + report stages when weights change (skip extract/
  abilities/boosts which don't depend on weights)
- Consider exposing raw per-resource output from enriched_buildings so users are
  weighting actual game quantities, not the opaque `value` composite

**Separate happiness building rankings**
Rather than excluding decoration/culture/tower entirely, give them their own tab
or sub-ranking based on happiness per tile. Useful for players who need to know
which happiness buildings are most space-efficient.

### MEDIUM PRIORITY

**Building level awareness**
Rankings currently use static database values. If the export contains level data
(which it does — entity_levels is in the export), use the player's actual building
level to look up the correct output values. My City already does this partially for
production_state buildings. Full coverage would make rankings city-specific.

**Saved weight presets**
Let users save their custom weight configurations (localStorage) so they don't
have to re-enter every time. Ship with the 4 current modes as named presets
(Balanced, GBG, GE, QI).

**Filter/sort improvements in the report**
- Filter Rankings by building type (military, goods, production, etc.)
- Filter My City by tier, scoring source, or swap candidate flag
- Persistent sort preference within a session

**Multi-city comparison**
Allow uploading two city exports side-by-side and comparing My City scores.
Currently handled by `city_compare.py` in the desktop pipeline — needs a web UI.

### LOWER PRIORITY / STRETCH

**Optimizer in the browser**
Re-enable `core/optimizer.py` in the Pyodide pipeline. Run in a Web Worker to
avoid blocking the UI. 500 iterations may be slow in WASM — profile first.

**Reddit / community promotion**
Once V2 has user-configurable weights (the feature that differentiates it from
simply reading patch notes), it's worth posting on r/forgeofempires and the
FoE Helper Discord. The pitch is strongest when users can tune it to their
own playstyle.

**Localization**
FoE has a large non-English player base. The pipeline and report are English-only.
Building names in enriched_buildings.json may or may not be localized depending
on FoE_Bldg_DB. Low priority but worth noting.

---

## Technical Notes for V2

- All Python source files are fetched fresh from GitHub Pages on each Pyodide
  session. Updating the pipeline just requires a push — no cache-busting needed
  beyond normal browser cache TTL.
- enriched_buildings.json (5.3 MB) is fetched once and held in Pyodide's virtual
  FS for the session. If the game DB is updated (new era/buildings), just push
  a new version to Data/Input/enriched_buildings.json.
- User weight customization should be passed to Python via pyodide.globals.set()
  before running the rankings stage — same pattern used for the input filename.
- The report.html is a self-contained file with all data embedded as JSON. Any
  new columns or tabs need changes in both core/html_report.py (data) and the
  embedded JS (rendering).
- Pyodide version: v0.27.0 (pinned in index.html script src). Test against newer
  versions before upgrading.
