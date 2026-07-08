#!/usr/bin/env python3
"""
03_extract_scenarios.py — Generate src/data/scenarios.json from data/snapshot.db.

Reads the local SQLite snapshot (no network required).
Run 00_export_snapshot.py first if you need to refresh the snapshot.

Produces two scenarios:

1. capital_allocation — $1M incremental: blended retail channels vs DTC.
   Uses real contribution margin % from the snapshot.

2. walmart_volume_curve — How Walmart's marginal contribution per unit declines
   as total volume scales. Modeled from real deduction rates + industry-standard
   promotional elasticity (1.8×). Crosses zero at ~walmart_inflection_volume.

   The curve is ANCHORED to real Walmart economics from the snapshot: the base
   point (current annual volume) reproduces the observed contribution per unit
   from channels.json (~$1.86 at a ~$3.85 realized wholesale price). Only volumes
   ABOVE current are modeled — deduction rates escalate with volume at
   PROMO_ELASTICITY; COGS and fixed costs are held constant per unit.
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "snapshot.db"
OUT_PATH = ROOT / "src" / "data" / "scenarios.json"

RETAIL_CHANNELS = {"Sprouts", "Whole Foods", "Regional Group", "Kroger", "Walmart", "Costco"}
DISTRIBUTOR_CHANNELS = {"UNFI", "KeHE", "DPI Northwest"}
DTC_CHANNEL = "DTC"

# $1M of INCREMENTAL REVENUE (not capital). Blended contribution margin applied
# to a marginal revenue dollar — this is a per-revenue-dollar comparison, not ROIC.
INCREMENTAL_REVENUE = 1_000_000

# Promotional elasticity: how fast deduction rate grows as volume scales.
# 1.8 = 1% volume growth → ~1.8% deduction rate growth (industry norm for
# Walmart velocity requirements, slotting resets, promotional funding escalation).
PROMO_ELASTICITY = 1.8

# Number of fiscal years in the snapshot (2024–2026 = 3 years)
SNAPSHOT_YEARS = 3


def load_channels(db: sqlite3.Connection) -> dict[str, dict]:
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    cur.execute("""
        SELECT channel, channel_type, gross_revenue, cogs_amount,
               total_deductions, promo_costs, overhead_cost, units_sold
        FROM channels
    """)
    rows = cur.fetchall()
    if not rows:
        print("ERROR: channels table is empty. Run 00_export_snapshot.py first.", file=sys.stderr)
        sys.exit(1)
    return {r["channel"]: dict(r) for r in rows}


def contribution(row: dict) -> float:
    return (
        row["gross_revenue"]
        - row["cogs_amount"]
        - row["total_deductions"]
        - row["promo_costs"]
        - row["overhead_cost"]
    )


def contribution_margin(row: dict) -> float:
    rev = row["gross_revenue"]
    return contribution(row) / rev if rev else 0.0


def capital_allocation(channels: dict[str, dict]) -> dict:
    """
    $1M of incremental REVENUE: retail vs distributor channel economics.

    This is a per-revenue-dollar comparison, not a return on invested capital.
    Retail channels earn ~51 cents of contribution per revenue dollar. Distributor
    channels (UNFI, KeHE, DPI) earn ~46 cents — lower wholesale prices mean COGS
    consumes a larger share. The ~5-point gap favors retail despite its higher
    deduction burden. These are AVERAGE channel margins; see Chapter 4 for how the
    MARGINAL contribution of a single channel erodes as its own volume scales.
    """
    retail_rows = [v for k, v in channels.items() if k in RETAIL_CHANNELS]
    distributor_rows = [v for k, v in channels.items() if k in DISTRIBUTOR_CHANNELS]

    if not retail_rows:
        raise ValueError("No retail channels found in snapshot.")
    if not distributor_rows:
        raise ValueError("No distributor channels found in snapshot.")

    retail_total_rev = sum(r["gross_revenue"] for r in retail_rows)
    retail_total_contrib = sum(contribution(r) for r in retail_rows)
    retail_margin = retail_total_contrib / retail_total_rev if retail_total_rev else 0.0

    dist_total_rev = sum(r["gross_revenue"] for r in distributor_rows)
    dist_total_contrib = sum(contribution(r) for r in distributor_rows)
    dist_margin = dist_total_contrib / dist_total_rev if dist_total_rev else 0.0

    retail_incremental = round(INCREMENTAL_REVENUE * retail_margin, 0)
    dist_incremental = round(INCREMENTAL_REVENUE * dist_margin, 0)
    delta = round(dist_incremental - retail_incremental, 0)
    delta_pct = round(delta / retail_incremental, 4) if retail_incremental else 0.0

    return {
        "retailer": {
            "label": f"${INCREMENTAL_REVENUE // 1_000_000}M revenue → Retail",
            "margin_pct": round(retail_margin, 4),
            "incremental_contribution": retail_incremental,
            "assumption": (
                f"Blended contribution margin of {retail_margin:.1%} "
                f"across {len(retail_rows)} retail channels (Walmart, Kroger, "
                "Whole Foods, Sprouts, Costco, Regional Group)"
            ),
        },
        "distributor": {
            "label": f"${INCREMENTAL_REVENUE // 1_000_000}M revenue → Distribution",
            "margin_pct": round(dist_margin, 4),
            "incremental_contribution": dist_incremental,
            "assumption": (
                f"Blended contribution margin of {dist_margin:.1%} "
                f"across {len(distributor_rows)} distributor channels "
                "(UNFI, KeHE, DPI Northwest)"
            ),
        },
        "delta": delta,
        "delta_pct": delta_pct,
    }


def walmart_volume_curve(channels: dict[str, dict]) -> tuple[list[dict], int]:
    """
    Model Walmart marginal contribution per unit across volume scenarios.

    Returns (curve_points, inflection_volume).

    Methodology:
      Realized wholesale price = gross_revenue ÷ units_sold (real units from the
      snapshot). Base volume = annual units (units_sold ÷ SNAPSHOT_YEARS). At base
      volume the model reproduces the observed contribution per unit from
      channels.json (price × (1 − cogs_ratio − other_rate − base_ded_rate)).
      Above base volume, only the deduction rate escalates, at PROMO_ELASTICITY —
      capturing real-world Walmart promotional funding escalation. COGS and fixed
      costs (promo + dispute overhead) are held constant per revenue dollar.
    """
    walmart = channels.get("Walmart")
    if not walmart:
        raise ValueError("Walmart not found in snapshot.")

    units_sold = walmart["units_sold"]
    if not units_sold or units_sold <= 0:
        raise ValueError(
            "Walmart units_sold is missing or non-positive. "
            "Run scripts/00_export_snapshot.py to populate real units before "
            "regenerating scenarios."
        )

    annual_rev = walmart["gross_revenue"] / SNAPSHOT_YEARS
    annual_cogs = walmart["cogs_amount"] / SNAPSHOT_YEARS
    annual_ded = walmart["total_deductions"] / SNAPSHOT_YEARS
    annual_other = (walmart["promo_costs"] + walmart["overhead_cost"]) / SNAPSHOT_YEARS

    # Real realized wholesale price and current annual volume — no assumptions.
    realized_price = walmart["gross_revenue"] / units_sold
    base_volume = int(units_sold / SNAPSHOT_YEARS)

    cogs_ratio = annual_cogs / annual_rev if annual_rev else 0.0
    base_ded_rate = annual_ded / annual_rev if annual_rev else 0.0
    # Promo + dispute overhead as a share of revenue, held constant (does not
    # escalate with volume the way trade deductions do).
    other_rate = annual_other / annual_rev if annual_rev else 0.0

    def mc_at_volume(v: int) -> float:
        """Marginal contribution per unit at volume v.

        At v = base_volume this equals the observed contribution per unit in
        channels.json; above base_volume the deduction rate escalates.
        """
        scale = v / base_volume
        effective_ded_rate = base_ded_rate * (scale ** PROMO_ELASTICITY)
        return round(
            realized_price * (1.0 - cogs_ratio - other_rate - effective_ded_rate), 2
        )

    # Build curve at 0.5× through 10× base volume
    multipliers = [0.5, 0.75, 1.0, 1.5, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 10.0]
    curve = []
    for m in multipliers:
        v = int(base_volume * m)
        mc = mc_at_volume(v)
        curve.append({
            "volume_units": v,
            "marginal_contribution_per_unit": mc,
        })

    # Binary search for inflection (mc crosses zero)
    lo, hi = base_volume, base_volume * 20
    inflection = None
    for _ in range(50):  # enough iterations for precision
        mid = (lo + hi) // 2
        if mc_at_volume(mid) > 0:
            lo = mid
        else:
            hi = mid
        if hi - lo < 1000:
            inflection = (lo + hi) // 2
            break

    return curve, inflection or (base_volume * 10)


def main() -> None:
    if not DB_PATH.exists():
        print(
            f"ERROR: {DB_PATH} not found.\n"
            "Run: python scripts/00_export_snapshot.py --seed",
            file=sys.stderr,
        )
        sys.exit(1)

    with sqlite3.connect(DB_PATH) as db:
        channels = load_channels(db)

    alloc = capital_allocation(channels)
    curve, inflection = walmart_volume_curve(channels)

    scenarios = {
        "capital_allocation": alloc,
        "walmart_volume_curve": curve,
        "walmart_inflection_volume": inflection,
    }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(scenarios, f, indent=2)
    print(f"Written: {OUT_PATH}")


if __name__ == "__main__":
    main()
