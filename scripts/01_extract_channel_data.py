#!/usr/bin/env python3
"""
01_extract_channel_data.py — Generate src/data/channels.json from data/snapshot.db.

Reads the local SQLite snapshot (no network required).
Run 00_export_snapshot.py first if you need to refresh the snapshot.

Output shape per channel:
  channel            str   — display name
  channel_type       str   — 'retailer' | 'distributor' | 'dtc'
  revenue            float — gross revenue
  contribution_dollars  float — revenue - cogs - deductions - promo - overhead
  contribution_margin_pct  float — contribution / revenue
  units_shipped      int | null — null until live export populates units_sold
  contribution_per_unit  float | null — null until units_shipped is populated
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "snapshot.db"
OUT_PATH = ROOT / "src" / "data" / "channels.json"

REQUIRED_FIELDS = {
    "channel", "channel_type", "revenue",
    "contribution_dollars", "contribution_margin_pct",
}


def load_channels(db: sqlite3.Connection) -> list[dict]:
    db.row_factory = sqlite3.Row
    cur = db.cursor()
    cur.execute("""
        SELECT channel, channel_type, gross_revenue, cogs_amount,
               total_deductions, promo_costs, overhead_cost, units_sold
        FROM channels
        ORDER BY gross_revenue DESC
    """)
    rows = cur.fetchall()
    if not rows:
        print("ERROR: channels table is empty. Run 00_export_snapshot.py first.", file=sys.stderr)
        sys.exit(1)
    return [dict(r) for r in rows]


def compute(row: dict) -> dict:
    revenue = row["gross_revenue"]
    contribution = round(
        revenue
        - row["cogs_amount"]
        - row["total_deductions"]
        - row["promo_costs"]
        - row["overhead_cost"],
        2,
    )
    margin_pct = round(contribution / revenue, 4) if revenue else 0.0

    units = row["units_sold"]
    per_unit = round(contribution / units, 2) if (units and units > 0) else None

    return {
        "channel": row["channel"],
        "channel_type": row["channel_type"],
        "revenue": revenue,
        "contribution_dollars": contribution,
        "contribution_margin_pct": margin_pct,
        "units_shipped": units,
        "contribution_per_unit": per_unit,
    }


def reconcile(data: list[dict]) -> None:
    if not data:
        raise ValueError("No channel records to reconcile.")

    seen = set()
    for ch in data:
        missing = REQUIRED_FIELDS - ch.keys()
        if missing:
            raise ValueError(f"{ch.get('channel', '?')}: missing fields {missing}")

        name = ch["channel"]
        if name in seen:
            raise ValueError(f"Duplicate channel: {name}")
        seen.add(name)

        if ch["revenue"] <= 0:
            raise ValueError(f"{name}: revenue must be positive, got {ch['revenue']}")

        if ch["contribution_dollars"] < 0:
            print(f"WARN: {name} has negative contribution ({ch['contribution_dollars']:.0f}). "
                  "Verify COGS and deduction data.", file=sys.stderr)


def main() -> None:
    if not DB_PATH.exists():
        print(
            f"ERROR: {DB_PATH} not found.\n"
            "Run: python scripts/00_export_snapshot.py --seed",
            file=sys.stderr,
        )
        sys.exit(1)

    with sqlite3.connect(DB_PATH) as db:
        rows = load_channels(db)

    data = [compute(r) for r in rows]
    reconcile(data)

    null_units = [ch["channel"] for ch in data if ch["units_shipped"] is None]
    if null_units:
        print(
            f"NOTE: units_shipped is null for: {', '.join(null_units)}\n"
            "      contribution_per_unit will be null in the output.\n"
            "      Run: python scripts/00_export_snapshot.py (live mode) to populate.",
            file=sys.stderr,
        )

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Written: {OUT_PATH} ({len(data)} channels)")


if __name__ == "__main__":
    main()
