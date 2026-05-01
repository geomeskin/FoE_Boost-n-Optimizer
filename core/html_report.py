# ===============================
# FILE: core/html_report.py
# ===============================

import json as _json
import config
from .io_utils import load_json

RANKINGS_COLS = [
    {"key": "rank_balanced", "label": "Rank",      "type": "num"},
    {"key": "name",          "label": "Building",   "type": "str"},
    {"key": "type",          "label": "Type",       "type": "str"},
    {"key": "area",          "label": "Tiles",      "type": "num"},
    {"key": "requires_road", "label": "Road",       "type": "bool"},
    {"key": "efficiency",    "label": "Base Eff",   "type": "num"},
    {"key": "att_per_tile",  "label": "Att/Tile",   "type": "num"},
    {"key": "def_per_tile",  "label": "Def/Tile",   "type": "num"},
    {"key": "score_balanced","label": "Bal Score",  "type": "num"},
    {"key": "score_GBG",     "label": "GBG Score",  "type": "num"},
    {"key": "score_GE",      "label": "GE Score",   "type": "num"},
    {"key": "score_QI",      "label": "QI Score",   "type": "num"},
    {"key": "tier_balanced", "label": "Bal",        "type": "tier"},
    {"key": "tier_GBG",      "label": "GBG",        "type": "tier"},
    {"key": "tier_GE",       "label": "GE",         "type": "tier"},
    {"key": "tier_QI",       "label": "QI",         "type": "tier"},
]

MY_CITY_COLS = [
    {"key": "replaceable",    "label": "Swap?",     "type": "replaceable"},
    {"key": "scoring_source", "label": "Source",    "type": "source"},
    {"key": "name",           "label": "Building",  "type": "str"},
    {"key": "type",           "label": "Type",      "type": "str"},
    {"key": "area",           "label": "Tiles",     "type": "num"},
    {"key": "connected",      "label": "Road",      "type": "num"},
    {"key": "efficiency",     "label": "Eff/Tile",  "type": "num"},
    {"key": "daily_value",    "label": "Daily Val", "type": "num"},
    {"key": "att_per_tile",   "label": "Att/Tile",  "type": "num"},
    {"key": "def_per_tile",   "label": "Def/Tile",  "type": "num"},
    {"key": "tier_balanced",  "label": "Bal",       "type": "tier"},
    {"key": "tier_GBG",       "label": "GBG",       "type": "tier"},
    {"key": "tier_GE",        "label": "GE",        "type": "tier"},
    {"key": "tier_QI",        "label": "QI",        "type": "tier"},
]

MOVERS_COLS = [
    {"key": "name",          "label": "Building",   "type": "str"},
    {"key": "type",          "label": "Type",       "type": "str"},
    {"key": "area",          "label": "Tiles",      "type": "num"},
    {"key": "requires_road", "label": "Road",       "type": "bool"},
    {"key": "efficiency",    "label": "Base Eff",   "type": "num"},
    {"key": "att_per_tile",  "label": "Att/Tile",   "type": "num"},
    {"key": "def_per_tile",  "label": "Def/Tile",   "type": "num"},
    {"key": "rank_balanced", "label": "Bal Rank",   "type": "num"},
    {"key": "rank_GBG",      "label": "GBG Rank",   "type": "num"},
    {"key": "rank_GE",       "label": "GE Rank",    "type": "num"},
    {"key": "rank_QI",       "label": "QI Rank",    "type": "num"},
    {"key": "jump_GBG",      "label": "GBG Jump",   "type": "jump"},
    {"key": "jump_GE",       "label": "GE Jump",    "type": "jump"},
    {"key": "jump_QI",       "label": "QI Jump",    "type": "jump"},
    {"key": "tier_balanced", "label": "Bal",        "type": "tier"},
    {"key": "tier_GBG",      "label": "GBG",        "type": "tier"},
    {"key": "tier_GE",       "label": "GE",         "type": "tier"},
    {"key": "tier_QI",       "label": "QI",         "type": "tier"},
]


def _read_csv(path):
    import csv
    with open(path, encoding="utf-8-sig") as f:
        return list(csv.DictReader(f))


def generate(rankings_rows, movers_rows, my_city_data, output_path):
    city_name    = config.CITY_NAME
    data_js      = _json.dumps({"rankings": rankings_rows, "movers": movers_rows,
                                 "my_city": my_city_data.get("buildings", [])},
                                ensure_ascii=False)
    r_cols_js    = _json.dumps(RANKINGS_COLS)
    m_cols_js    = _json.dumps(MOVERS_COLS)
    c_cols_js    = _json.dumps(MY_CITY_COLS)
    c_summary_js = _json.dumps(my_city_data.get("summary", {}), ensure_ascii=False)
    c_unscored_js = _json.dumps(my_city_data.get("unscored", []), ensure_ascii=False)

    html = f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>FoE Boost-n-Optimizer</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: system-ui, sans-serif; background: #f4f6f8; color: #1a1a2e; }}

  header {{ background: #1a1a2e; color: #fff; padding: 14px 24px; display: flex;
            align-items: center; gap: 16px; }}
  header h1 {{ font-size: 1.2rem; font-weight: 700; letter-spacing: .03em; }}
  header span {{ font-size: .8rem; opacity: .6; }}

  .toolbar {{ display: flex; align-items: center; gap: 12px; padding: 12px 24px;
              background: #fff; border-bottom: 1px solid #dde1e7; flex-wrap: wrap; }}

  .tabs {{ display: flex; gap: 4px; }}
  .tab-btn {{ padding: 7px 18px; border: 2px solid #c0c8d4; border-radius: 20px;
              background: transparent; cursor: pointer; font-size: .85rem;
              font-weight: 600; color: #555; transition: all .15s; }}
  .tab-btn.active {{ background: #1a1a2e; color: #fff; border-color: #1a1a2e; }}

  #search {{ padding: 7px 12px; border: 1px solid #c0c8d4; border-radius: 6px;
             font-size: .88rem; width: 260px; outline: none; }}
  #search:focus {{ border-color: #4a6fa5; box-shadow: 0 0 0 2px #4a6fa533; }}

  #row-count {{ margin-left: auto; font-size: .8rem; color: #888; }}

  .table-wrap {{ overflow-x: auto; padding: 16px 24px 40px; }}

  table {{ border-collapse: collapse; width: 100%; font-size: .82rem; background: #fff;
           border-radius: 8px; overflow: hidden;
           box-shadow: 0 1px 4px rgba(0,0,0,.08); }}

  th {{ background: #1a1a2e; color: #fff; padding: 10px 10px; text-align: left;
        white-space: nowrap; user-select: none; cursor: pointer; position: sticky;
        top: 0; z-index: 2; }}
  th:hover {{ background: #2d3a5c; }}
  th .sort-ind {{ margin-left: 4px; opacity: .5; font-size: .75rem; }}
  th.sort-asc .sort-ind::after  {{ content: " v"; opacity: 1; }}
  th.sort-desc .sort-ind::after {{ content: " ^"; opacity: 1; }}

  td {{ padding: 7px 10px; border-bottom: 1px solid #eef0f3; white-space: nowrap; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #f0f4ff; }}

  .tier {{ display: inline-block; min-width: 24px; text-align: center;
           font-weight: 700; font-size: .8rem; padding: 2px 6px;
           border-radius: 4px; }}
  .tier-S {{ background: #ffd700; color: #5a3e00; }}
  .tier-A {{ background: #4caf50; color: #fff; }}
  .tier-B {{ background: #2196f3; color: #fff; }}
  .tier-C {{ background: #9e9e9e; color: #fff; }}

  .jump-pos {{ color: #2e7d32; font-weight: 700; }}
  .jump-neg {{ color: #c62828; font-weight: 700; }}

  .road-y {{ color: #1565c0; font-weight: 600; }}
  .road-n {{ color: #aaa; }}

  .no-results {{ padding: 40px; text-align: center; color: #aaa; font-size: 1rem; }}

  .city-summary {{ display: none; padding: 16px 24px; background: #f4f6f8;
                   border-bottom: 1px solid #dde1e7; gap: 12px; flex-wrap: wrap; }}
  .city-summary.visible {{ display: flex; }}
  .summary-card {{ background: #fff; border-radius: 8px; padding: 12px 18px; min-width: 160px;
                   box-shadow: 0 1px 3px rgba(0,0,0,.08); }}
  .summary-card h4 {{ font-size: .72rem; font-weight: 700; text-transform: uppercase;
                      letter-spacing: .06em; color: #888; margin-bottom: 8px; }}
  .tier-row {{ display: flex; gap: 6px; align-items: center; }}
  .tier-count {{ display: flex; flex-direction: column; align-items: center; gap: 2px; }}
  .tier-count .tier {{ font-size: .75rem; padding: 1px 5px; }}
  .tier-count .cnt {{ font-size: .85rem; font-weight: 700; color: #333; }}
  .summary-stat {{ font-size: .8rem; color: #555; margin-top: 6px; }}
  .source-full {{ color: #2e7d32; font-weight: 700; font-size: .78rem; }}
  .source-state {{ color: #1565c0; font-weight: 700; font-size: .78rem; }}
  .unscored-list {{ padding: 12px 24px 24px; }}
  .unscored-list h3 {{ font-size: .82rem; font-weight: 700; color: #888; margin-bottom: 10px; }}
  .unscored-grid {{ display: flex; flex-wrap: wrap; gap: 6px; }}
  .unscored-chip {{ background: #fff; border: 1px solid #dde1e7; border-radius: 4px;
                    padding: 3px 8px; font-size: .78rem; color: #555; }}

  .legend {{ background: #fff; border-bottom: 1px solid #dde1e7; overflow: hidden; }}
  .legend-toggle {{ width: 100%; text-align: left; padding: 9px 24px;
                    background: #eef2f7; border: none; cursor: pointer;
                    font-size: .82rem; font-weight: 600; color: #4a5568;
                    display: flex; align-items: center; gap: 6px; }}
  .legend-toggle:hover {{ background: #e2e8f0; }}
  .legend-toggle .arr {{ transition: transform .2s; }}
  .legend-toggle.open .arr {{ transform: rotate(90deg); }}
  .legend-body {{ display: none; padding: 16px 24px 20px;
                  display: none; gap: 32px; flex-wrap: wrap; }}
  .legend-body.open {{ display: flex; }}
  .legend-section h3 {{ font-size: .78rem; font-weight: 700; text-transform: uppercase;
                        letter-spacing: .06em; color: #888; margin-bottom: 8px; }}
  .legend-section ul {{ list-style: none; display: flex; flex-direction: column; gap: 5px; }}
  .legend-section li {{ font-size: .82rem; display: flex; align-items: center; gap: 8px; }}
  .legend-section li .lbl {{ min-width: 90px; font-weight: 600; color: #333; }}
  .legend-section li .desc {{ color: #555; }}
</style>
</head>
<body>

<header>
  <h1>FoE Boost-n-Optimizer</h1>
  <span>Building Rankings &amp; Mode Analysis</span>
</header>

<div class="legend">
  <button class="legend-toggle" onclick="toggleLegend(this)">
    <span class="arr">&#9654;</span> Legend / Key
  </button>
  <div class="legend-body" id="legend-body">

    <div class="legend-section">
      <h3>Tiers</h3>
      <ul>
        <li><span class="tier tier-S lbl">S</span><span class="desc">Top 10% by score in that mode — always worth placing</span></li>
        <li><span class="tier tier-A lbl">A</span><span class="desc">Top 10–30% — strong, situationally excellent</span></li>
        <li><span class="tier tier-B lbl">B</span><span class="desc">Top 30–60% — decent, fill space with these</span></li>
        <li><span class="tier tier-C lbl">C</span><span class="desc">Bottom 40% — low priority</span></li>
      </ul>
    </div>

    <div class="legend-section">
      <h3>Modes</h3>
      <ul>
        <li><span class="lbl">Balanced</span><span class="desc">Overall value per tile — economic output is the dominant factor</span></li>
        <li><span class="lbl">GBG</span><span class="desc">Guild Battlegrounds — heavily weights attack boosts when attacking</span></li>
        <li><span class="lbl">GE</span><span class="desc">Guild Expedition — weights both attack and defense evenly</span></li>
        <li><span class="lbl">QI</span><span class="desc">Quantum Incursion — attack boosts plus production (supplies &amp; coins)</span></li>
      </ul>
    </div>

    <div class="legend-section">
      <h3>Columns</h3>
      <ul>
        <li><span class="lbl">Base Eff</span><span class="desc">Economic value divided by tile count (happiness, pop, FPs, goods, etc.)</span></li>
        <li><span class="lbl">Att/Tile</span><span class="desc">Best attack (or combined att+def) boost per tile this building provides</span></li>
        <li><span class="lbl">Def/Tile</span><span class="desc">Best defense boost per tile this building provides</span></li>
        <li><span class="lbl">Score</span><span class="desc">Base Eff + weighted combat boosts for that mode — what tiers are based on</span></li>
        <li><span class="lbl">GBG Jump</span><span class="desc">How many ranks a building moves up (+) or down (-) when switching from Balanced to GBG scoring</span></li>
        <li><span class="lbl">Road</span><span class="desc">Y = requires road connection; - = road-free</span></li>
      </ul>
    </div>

    <div class="legend-section">
      <h3>My City — Source</h3>
      <ul>
        <li><span class="source-full lbl">full</span><span class="desc">Scored from game entity data (entity_levels) — most complete</span></li>
        <li><span class="source-state lbl">live</span><span class="desc">Scored from live production snapshot in your export — reflects your current era &amp; level</span></li>
        <li><span class="lbl" style="color:#aaa">—</span><span class="desc">Unscored — passive/happiness buildings, Great Buildings (no production data in export)</span></li>
        <li><span style="background:#ff8f00;color:#fff;font-weight:700;font-size:.75rem;padding:2px 7px;border-radius:4px;" class="lbl">swap?</span><span class="desc">Full-scored C-tier — legitimate candidate to replace when a better event building comes along</span></li>
      </ul>
    </div>

  </div>
</div>

<div class="toolbar">
  <div class="tabs">
    <button class="tab-btn active" onclick="switchTab('rankings')">Rankings</button>
    <button class="tab-btn"        onclick="switchTab('movers')">Mode Movers</button>
    <button class="tab-btn"        onclick="switchTab('my_city')">My City ({city_name})</button>
  </div>
  <input id="search" type="text" placeholder="Search building name..." oninput="applyFilter()">
  <span id="row-count"></span>
</div>

<div class="city-summary" id="city-summary"></div>

<div class="table-wrap">
  <table id="main-table">
    <thead id="thead"></thead>
    <tbody id="tbody"></tbody>
  </table>
  <div class="no-results" id="no-results" style="display:none">No buildings match your search.</div>
</div>

<div class="unscored-list" id="unscored-section" style="display:none">
  <h3>Unscored buildings (passive providers, Great Buildings — no production data in export)</h3>
  <div class="unscored-grid" id="unscored-grid"></div>
</div>

<script>
const ALL_DATA    = {data_js};
const COL_DEFS    = {{ rankings: {r_cols_js}, movers: {m_cols_js}, my_city: {c_cols_js} }};
const CITY_SUMMARY = {c_summary_js};
const CITY_UNSCORED = {c_unscored_js};
const TAB_NAMES   = ['rankings', 'movers', 'my_city'];

let activeTab   = 'rankings';
let sortCol     = null;
let sortDir     = 1;
let filterTerm  = '';

const TIER_ORDER = {{ S: 4, A: 3, B: 2, C: 1, '': 0 }};

function switchTab(tab) {{
  activeTab = tab;
  sortCol   = null;
  sortDir   = 1;
  document.getElementById('search').value = '';
  filterTerm = '';
  document.querySelectorAll('.tab-btn').forEach((b, i) => {{
    b.classList.toggle('active', TAB_NAMES[i] === tab);
  }});

  const isMy = tab === 'my_city';
  document.getElementById('city-summary').classList.toggle('visible', isMy);
  document.getElementById('unscored-section').style.display = isMy ? '' : 'none';
  if (isMy) renderCitySummary();

  render();
}}

function applyFilter() {{
  filterTerm = document.getElementById('search').value.toLowerCase();
  render();
}}

function colValue(row, col) {{
  const v = row[col.key];
  if (col.type === 'num')  return parseFloat(v) || 0;
  if (col.type === 'jump') return parseInt(v)   || 0;
  if (col.type === 'tier') return TIER_ORDER[v] || 0;
  if (col.type === 'bool') return (v === 'True' || v === true) ? 1 : 0;
  return (v || '').toString().toLowerCase();
}}

function sortData(rows, col) {{
  return [...rows].sort((a, b) => {{
    const av = colValue(a, col), bv = colValue(b, col);
    if (av < bv) return -sortDir;
    if (av > bv) return  sortDir;
    return 0;
  }});
}}

function renderCitySummary() {{
  const s   = CITY_SUMMARY;
  const div = document.getElementById('city-summary');
  const modes = ['balanced', 'GBG', 'GE', 'QI'];
  let html = `<div class="summary-card"><h4>Coverage</h4>
    <div class="summary-stat">Total buildings: <b>${{s.total_placed}}</b></div>
    <div class="summary-stat">Scored: <b>${{s.scored}}</b></div>
    <div class="summary-stat" style="color:#aaa">Unscored (passive): <b>${{s.unscored}}</b></div>
  </div>`;
  modes.forEach(m => {{
    const t = (s[m] || {{}}).tiers || {{}};
    const score = ((s[m] || {{}}).total_city_score || 0).toLocaleString();
    html += `<div class="summary-card"><h4>${{m}}</h4>
      <div class="tier-row">
        <div class="tier-count"><span class="tier tier-S">S</span><span class="cnt">${{t.S||0}}</span></div>
        <div class="tier-count"><span class="tier tier-A">A</span><span class="cnt">${{t.A||0}}</span></div>
        <div class="tier-count"><span class="tier tier-B">B</span><span class="cnt">${{t.B||0}}</span></div>
        <div class="tier-count"><span class="tier tier-C">C</span><span class="cnt">${{t.C||0}}</span></div>
      </div>
      <div class="summary-stat">City score: ${{score}}</div>
    </div>`;
  }});
  div.innerHTML = html;

  const ugrid = document.getElementById('unscored-grid');
  ugrid.innerHTML = CITY_UNSCORED.map(b =>
    `<span class="unscored-chip" title="${{b.type}}">${{b.name}}</span>`
  ).join('');
}}

function cellHtml(val, colType) {{
  if (colType === 'replaceable') {{
    return (val === true || val === 'True')
      ? `<span style="background:#ff8f00;color:#fff;font-weight:700;font-size:.75rem;padding:2px 7px;border-radius:4px;">swap?</span>`
      : '';
  }}
  if (colType === 'source') {{
    if (val === 'entity_levels')    return `<span class="source-full">full</span>`;
    if (val === 'production_state') return `<span class="source-state">live</span>`;
    return `<span style="color:#aaa">-</span>`;
  }}
  if (colType === 'tier') {{
    if (!val || val === '-' || val === '?') return `<span style="color:#ccc">-</span>`;
    return `<span class="tier tier-${{val}}">${{val}}</span>`;
  }}
  if (colType === 'jump') {{
    const n = parseInt(val) || 0;
    if (n > 0) return `<span class="jump-pos">+${{n}}</span>`;
    if (n < 0) return `<span class="jump-neg">${{n}}</span>`;
    return `<span style="color:#aaa">0</span>`;
  }}
  if (colType === 'bool') {{
    const yes = (val === 'True' || val === true);
    return yes ? `<span class="road-y">Y</span>` : `<span class="road-n">-</span>`;
  }}
  if (colType === 'num') {{
    const n = parseFloat(val);
    return isNaN(n) ? '-' : n.toLocaleString(undefined, {{maximumFractionDigits: 2}});
  }}
  return val != null ? val : '-';
}}

function render() {{
  const cols = COL_DEFS[activeTab];
  let rows   = ALL_DATA[activeTab];

  // filter
  if (filterTerm) {{
    rows = rows.filter(r => (r.name || '').toLowerCase().includes(filterTerm));
  }}

  // sort
  const sortColDef = sortCol != null ? cols[sortCol] : null;
  if (sortColDef) rows = sortData(rows, sortColDef);

  // thead
  const thead = document.getElementById('thead');
  thead.innerHTML = '<tr>' + cols.map((c, i) => {{
    let cls = '';
    if (sortCol === i) cls = sortDir === 1 ? 'sort-asc' : 'sort-desc';
    return `<th class="${{cls}}" onclick="onSort(${{i}})">
      ${{c.label}}<span class="sort-ind"></span>
    </th>`;
  }}).join('') + '</tr>';

  // tbody
  const tbody = document.getElementById('tbody');
  if (rows.length === 0) {{
    tbody.innerHTML = '';
    document.getElementById('no-results').style.display = '';
  }} else {{
    document.getElementById('no-results').style.display = 'none';
    tbody.innerHTML = rows.map(r =>
      '<tr>' + cols.map(c => `<td>${{cellHtml(r[c.key], c.type)}}</td>`).join('') + '</tr>'
    ).join('');
  }}

  const total = (ALL_DATA[activeTab] || []).length;
  document.getElementById('row-count').textContent =
    rows.length + ' of ' + total + ' buildings';
}}

function onSort(colIdx) {{
  if (sortCol === colIdx) {{
    sortDir = -sortDir;
  }} else {{
    sortCol = colIdx;
    sortDir = 1;
  }}
  render();
}}

render();

function toggleLegend(btn) {{
  const body = document.getElementById('legend-body');
  const open  = body.classList.toggle('open');
  btn.classList.toggle('open', open);
}}
</script>
</body>
</html>"""

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)


def run():
    print("=== HTML REPORT STAGE ===")
    rankings_path  = config.OUTPUT_DIR / "report_rankings.csv"
    movers_path    = config.OUTPUT_DIR / "report_mode_movers.csv"
    my_city_path   = config.MY_CITY_FILE
    output_path    = config.OUTPUT_DIR / "report.html"

    rankings_rows  = _read_csv(rankings_path)
    movers_rows    = _read_csv(movers_path)
    my_city_data   = load_json(my_city_path) if my_city_path.exists() else {}

    generate(rankings_rows, movers_rows, my_city_data, output_path)
    print(f"Saved: {output_path}")
    print(f"  Rankings : {len(rankings_rows)} buildings")
    print(f"  Movers   : {len(movers_rows)} buildings")
    scored = len(my_city_data.get("buildings", []))
    print(f"  My City  : {scored} scored buildings")
