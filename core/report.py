# ===============================
# FILE: core/report.py
# ===============================

import csv
import config
from .io_utils import load_json

MODES = ["balanced", "GBG", "GE", "QI"]


def _att_per_tile(boost):
    """Best single-number attack contribution per tile."""
    return max(
        boost.get("att_boost_attacker", 0),
        boost.get("att_def_boost_attacker", 0),
        boost.get("att_boost_defender", 0),
        boost.get("att_def_boost_defender", 0),
    )


def _def_per_tile(boost):
    """Best single-number defense contribution per tile."""
    return max(
        boost.get("def_boost_defender", 0),
        boost.get("att_def_boost_defender", 0),
        boost.get("def_boost_attacker", 0),
        boost.get("att_def_boost_attacker", 0),
    )


def _write_csv(path, rows, fieldnames):
    with open(path, "w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        w.writerows(rows)


def build_rankings_report(ranked):
    """Full table — one row per building, all modes side by side."""
    rows = []
    for b in ranked:
        boost = b.get("boost_summary", {})
        scores = b.get("scores", {})
        tiers = b.get("tiers", {})
        rows.append({
            "rank_balanced":  b["rank"],
            "name":           b["name"],
            "type":           b.get("type", ""),
            "width":          b["width"],
            "height":         b["height"],
            "area":           b["area"],
            "requires_road":  b.get("requires_road", False),
            "efficiency":     b["efficiency"],
            "att_per_tile":   round(_att_per_tile(boost), 4),
            "def_per_tile":   round(_def_per_tile(boost), 4),
            "score_balanced": scores.get("balanced", ""),
            "score_GBG":      scores.get("GBG", ""),
            "score_GE":       scores.get("GE", ""),
            "score_QI":       scores.get("QI", ""),
            "tier_balanced":  tiers.get("balanced", ""),
            "tier_GBG":       tiers.get("GBG", ""),
            "tier_GE":        tiers.get("GE", ""),
            "tier_QI":        tiers.get("QI", ""),
        })
    return rows


def build_movers_report(ranked):
    """Buildings that jump the most ranks in combat modes vs balanced."""
    # Build per-mode rank lookup
    for mode in MODES:
        mode_sorted = sorted(ranked, key=lambda b: b["scores"][mode], reverse=True)
        for i, b in enumerate(mode_sorted):
            b[f"rank_{mode}"] = i + 1

    rows = []
    for b in ranked:
        boost = b.get("boost_summary", {})
        tiers = b.get("tiers", {})
        bal = b["rank_balanced"]
        jump_GBG = bal - b["rank_GBG"]
        jump_GE  = bal - b["rank_GE"]
        jump_QI  = bal - b["rank_QI"]

        # Only include buildings that move meaningfully in at least one mode
        if max(abs(jump_GBG), abs(jump_GE), abs(jump_QI)) < 5:
            continue

        rows.append({
            "name":           b["name"],
            "type":           b.get("type", ""),
            "area":           b["area"],
            "requires_road":  b.get("requires_road", False),
            "efficiency":     b["efficiency"],
            "att_per_tile":   round(_att_per_tile(boost), 4),
            "def_per_tile":   round(_def_per_tile(boost), 4),
            "rank_balanced":  bal,
            "rank_GBG":       b["rank_GBG"],
            "rank_GE":        b["rank_GE"],
            "rank_QI":        b["rank_QI"],
            "jump_GBG":       jump_GBG,
            "jump_GE":        jump_GE,
            "jump_QI":        jump_QI,
            "tier_balanced":  tiers.get("balanced", ""),
            "tier_GBG":       tiers.get("GBG", ""),
            "tier_GE":        tiers.get("GE", ""),
            "tier_QI":        tiers.get("QI", ""),
        })

    # Sort by biggest single-mode jump
    rows.sort(key=lambda r: max(r["jump_GBG"], r["jump_GE"], r["jump_QI"]), reverse=True)
    return rows


def run():
    print("=== REPORT STAGE ===")
    ranked = load_json(config.RANKED_BUILDINGS_FILE)

    # Full rankings CSV
    rankings_path = config.OUTPUT_DIR / "report_rankings.csv"
    rankings_rows = build_rankings_report(ranked)
    _write_csv(rankings_path, rankings_rows, list(rankings_rows[0].keys()))
    print(f"Rankings report: {len(rankings_rows)} buildings -> {rankings_path}")

    # Mode movers CSV
    movers_path = config.OUTPUT_DIR / "report_mode_movers.csv"
    movers_rows = build_movers_report(ranked)
    _write_csv(movers_path, movers_rows, list(movers_rows[0].keys()))
    print(f"Mode movers:     {len(movers_rows)} buildings -> {movers_path}")

    # Console preview
    print()
    print("Top 5 GBG buildings overall:")
    gbg_overall = sorted(ranked, key=lambda b: b["scores"]["GBG"], reverse=True)[:5]
    for i, b in enumerate(gbg_overall):
        boost = b.get("boost_summary", {})
        att = round(_att_per_tile(boost), 2)
        tiers = b.get("tiers", {})
        print(
            f"  GBG#{i+1}  {b['name'][:38]:38s}  "
            f"att/tile={att:.2f}  "
            f"GBG score={b['scores']['GBG']:8.1f}  "
            f"tier={tiers.get('GBG','?')}"
        )

    print()
    print("Top 5 GBG hidden gems (biggest rank jump vs balanced):")
    hidden = sorted(movers_rows, key=lambda r: r["jump_GBG"], reverse=True)[:5]
    for r in hidden:
        print(
            f"  {r['name'][:38]:38s}  "
            f"bal=#{r['rank_balanced']:3d} -> GBG=#{r['rank_GBG']:3d}  "
            f"(+{r['jump_GBG']:3d} spots)  "
            f"att/tile={r['att_per_tile']:.2f}  "
            f"tier: {r['tier_balanced']}->{r['tier_GBG']}"
        )
