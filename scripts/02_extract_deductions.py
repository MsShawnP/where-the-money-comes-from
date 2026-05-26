#!/usr/bin/env python3
"""
02_extract_deductions.py — Generate src/data/deductions.json from data/snapshot.db.

Reads the local SQLite snapshot (no network required).
Run 00_export_snapshot.py first if you need to refresh the snapshot.

Output shape per channel:
  {
    "ChannelName": {
      "type": "retailer" | "distributor" | "dtc",
      "steps": [
        {"label": str, "value": float, "cumulative": float},
        ...
        {"label": "Net Revenue", "value": 0, "cumulative": float, "is_subtotal": true},
        {"label": "COGS",        "value": float, "cumulative": float},
        {"label": "Contribution","value": 0, "cumulative": float, "is_total": true}
      ]
    }
  }

Steps are: Gross Revenue → each deduction type → Net Revenue → COGS → Contribution.
"""

import json
import sqlite3
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "snapshot.db"
OUT_PATH = ROOT / "src" / "data" / "deductions.json"

TYPE_LABELS: dict[str, str] = {
    "promo_billback": "Promo Billback",
    "pricing_error":  "Pricing Error",
    "short_ship":     "Short Ship",
    "slotting":       "Slotting Fees",
    "label_fine":     "Label Fines",
    "spoilage":       "Spoilage",
    "damaged":        "Damaged Goods",
    "pallet_fine":    "Pallet Fines",
    "late_delivery":  "Late Delivery",
}

# Display order: trade types first, then compliance
DEDUCTION_ORDER = [
    "promo_billback", "pricing_error", "short_ship", "slotting",
    "label_fine", "spoilage", "damaged", "pallet_fine", "late_delivery",
]


def load_data(db: sqlite3.Connection) -> tuple[dict, dict]:
    db.row_factory = sqlite3.Row
    cur = db.cursor()

    cur.execute("""
        SELECT channel, channel_type, gross_revenue, cogs_amount, promo_costs, overhead_cost
        FROM channels
        ORDER BY gross_revenue DESC
    """)
    channels = {r["channel"]: dict(r) for r in cur.fetchall()}

    cur.execute("""
        SELECT channel, deduction_type, total_amount
        FROM deductions
        ORDER BY channel, total_amount DESC
    """)
    deductions: dict[str, dict[str, float]] = {}
    for row in cur.fetchall():
        deductions.setdefault(row["channel"], {})[row["deduction_type"]] = row["total_amount"]

    if not channels:
        print("ERROR: channels table is empty. Run 00_export_snapshot.py first.", file=sys.stderr)
        sys.exit(1)

    return channels, deductions


def build_waterfall(channel_name: str, channel: dict, ded_map: dict[str, float]) -> list[dict]:
    gross = channel["gross_revenue"]
    cogs = channel["cogs_amount"]
    promo = channel.get("promo_costs") or 0.0
    overhead = channel.get("overhead_cost") or 0.0

    steps = []
    running = gross
    steps.append({"label": "Gross Revenue", "value": round(gross, 2), "cumulative": round(gross, 2)})

    # Deductions in display order
    for dtype in DEDUCTION_ORDER:
        amount = ded_map.get(dtype)
        if amount is None:
            continue
        running -= amount
        label = TYPE_LABELS.get(dtype, dtype.replace("_", " ").title())
        steps.append({
            "label": label,
            "value": round(-amount, 2),
            "cumulative": round(running, 2),
        })

    # Any deduction types not in DEDUCTION_ORDER (forward-compatible)
    known = set(DEDUCTION_ORDER)
    for dtype, amount in ded_map.items():
        if dtype not in known:
            running -= amount
            label = TYPE_LABELS.get(dtype, dtype.replace("_", " ").title())
            steps.append({
                "label": label,
                "value": round(-amount, 2),
                "cumulative": round(running, 2),
            })

    net_revenue = round(running, 2)
    steps.append({"label": "Net Revenue", "value": 0, "cumulative": net_revenue, "is_subtotal": True})

    running -= cogs
    steps.append({"label": "COGS", "value": round(-cogs, 2), "cumulative": round(running, 2)})

    if promo > 0:
        running -= promo
        steps.append({"label": "Promo Costs", "value": round(-promo, 2), "cumulative": round(running, 2)})

    if overhead > 0:
        running -= overhead
        steps.append({"label": "Dispute Overhead", "value": round(-overhead, 2), "cumulative": round(running, 2)})

    contribution = round(running, 2)
    steps.append({"label": "Contribution", "value": 0, "cumulative": contribution, "is_total": True})

    return steps


def validate_waterfall(channel_name: str, steps: list[dict]) -> None:
    if not steps:
        raise ValueError(f"{channel_name}: steps list is empty")
    if steps[0]["label"] != "Gross Revenue" or steps[0]["value"] <= 0:
        raise ValueError(f"{channel_name}: first step must be Gross Revenue with positive value")

    running = steps[0]["value"]
    has_subtotal = False
    has_total = False
    for step in steps[1:]:
        is_sub = step.get("is_subtotal", False)
        is_tot = step.get("is_total", False)
        if is_sub:
            has_subtotal = True
            running = step["cumulative"]
        elif is_tot:
            has_total = True
        else:
            running = round(running + step["value"], 2)
            if abs(running - step["cumulative"]) > 1:
                raise ValueError(
                    f"{channel_name} '{step['label']}': "
                    f"expected cumulative {running:.0f}, got {step['cumulative']}"
                )

    if not has_subtotal:
        raise ValueError(f"{channel_name}: missing Net Revenue subtotal step")
    if not has_total:
        raise ValueError(f"{channel_name}: missing Contribution total step")


def main() -> None:
    if not DB_PATH.exists():
        print(
            f"ERROR: {DB_PATH} not found.\n"
            "Run: python scripts/00_export_snapshot.py --seed",
            file=sys.stderr,
        )
        sys.exit(1)

    with sqlite3.connect(DB_PATH) as db:
        channels, deductions = load_data(db)

    result = {}
    for channel_name, channel in channels.items():
        ded_map = deductions.get(channel_name, {})
        steps = build_waterfall(channel_name, channel, ded_map)
        validate_waterfall(channel_name, steps)
        # Map SQLite channel_type → UI type tokens:
        # 'retailer' → 'retail' (matches existing Ch3 isRetailChannel check)
        # 'distributor' → 'distributor' (new — Ch3 distributor hidden-tax feature)
        # 'dtc'       → 'dtc'
        ui_type = channel["channel_type"]
        if ui_type == "retailer":
            ui_type = "retail"
        result[channel_name] = {
            "type": ui_type,
            "steps": steps,
        }

    OUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUT_PATH, "w") as f:
        json.dump(result, f, indent=2)
    print(f"Written: {OUT_PATH} ({len(result)} channels)")


if __name__ == "__main__":
    main()
