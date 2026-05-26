#!/usr/bin/env python3
"""
02_extract_deductions.py — Extract deduction waterfall data from Cinderhaven Postgres.

Produces src/data/deductions.json with per-channel waterfall steps:
  gross revenue → deductions → net revenue → COGS → contribution

Each step has:
  label: str          — human-readable name
  value: float        — change at this step (negative = deduction, 0 = subtotal marker)
  cumulative: float   — running total after this step
  is_subtotal: bool   — true for net revenue row (optional field)
  is_total: bool      — true for final contribution row (optional field)

Usage:
  python scripts/02_extract_deductions.py --snapshot   # no DB needed
  python scripts/02_extract_deductions.py              # requires DATABASE_URL env var

Schema notes (for live extraction):
  - Deduction taxonomy completeness is unknown; slotting, MCB, swell, OTIF may not all exist
  - Missing deduction types are excluded from the waterfall (not shown as $0 rows)
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Snapshot constants — representative Cinderhaven figures from requirements doc
SNAPSHOT_DATA = {
    "Walmart": {
        "type": "retail",
        "steps": [
            {"label": "Gross Revenue", "value": 1540000, "cumulative": 1540000},
            {"label": "Slotting Fees", "value": -154000, "cumulative": 1386000},
            {"label": "Trade Spend", "value": -308000, "cumulative": 1078000},
            {"label": "Chargebacks", "value": -92400, "cumulative": 985600},
            {"label": "Swell / Damage", "value": -30800, "cumulative": 954800},
            {"label": "OTIF Penalties", "value": -46200, "cumulative": 908600},
            {"label": "Net Revenue", "value": 0, "cumulative": 908600, "is_subtotal": True},
            {"label": "COGS", "value": -899780, "cumulative": 8820},
            {"label": "Contribution", "value": 0, "cumulative": 8820, "is_total": True}
        ]
    },
    "KeHE": {
        "type": "retail",
        "steps": [
            {"label": "Gross Revenue", "value": 420000, "cumulative": 420000},
            {"label": "Distributor Margin", "value": -126000, "cumulative": 294000},
            {"label": "Trade Spend", "value": -42000, "cumulative": 252000},
            {"label": "Chargebacks", "value": -12600, "cumulative": 239400},
            {"label": "Swell / Damage", "value": -8400, "cumulative": 231000},
            {"label": "Net Revenue", "value": 0, "cumulative": 231000, "is_subtotal": True},
            {"label": "COGS", "value": -198240, "cumulative": 32760},
            {"label": "Contribution", "value": 0, "cumulative": 32760, "is_total": True}
        ]
    },
    "Food Service": {
        "type": "retail",
        "steps": [
            {"label": "Gross Revenue", "value": 380000, "cumulative": 380000},
            {"label": "Distributor Margin", "value": -95000, "cumulative": 285000},
            {"label": "Trade Spend", "value": -38000, "cumulative": 247000},
            {"label": "Chargebacks", "value": -7600, "cumulative": 239400},
            {"label": "Net Revenue", "value": 0, "cumulative": 239400, "is_subtotal": True},
            {"label": "COGS", "value": -216600, "cumulative": 22800},
            {"label": "Contribution", "value": 0, "cumulative": 22800, "is_total": True}
        ]
    },
    "Costco": {
        "type": "retail",
        "steps": [
            {"label": "Gross Revenue", "value": 680000, "cumulative": 680000},
            {"label": "Membership Fee Share", "value": -68000, "cumulative": 612000},
            {"label": "Trade Spend", "value": -102000, "cumulative": 510000},
            {"label": "Chargebacks", "value": -20400, "cumulative": 489600},
            {"label": "Swell / Damage", "value": -10200, "cumulative": 479400},
            {"label": "Net Revenue", "value": 0, "cumulative": 479400, "is_subtotal": True},
            {"label": "COGS", "value": -419900, "cumulative": 59500},
            {"label": "Contribution", "value": 0, "cumulative": 59500, "is_total": True}
        ]
    },
    "UNFI / Whole Foods": {
        "type": "retail",
        "steps": [
            {"label": "Gross Revenue", "value": 520000, "cumulative": 520000},
            {"label": "Distributor Margin", "value": -130000, "cumulative": 390000},
            {"label": "Trade Spend", "value": -62400, "cumulative": 327600},
            {"label": "MCB / Promotions", "value": -20800, "cumulative": 306800},
            {"label": "Chargebacks", "value": -10400, "cumulative": 296400},
            {"label": "Net Revenue", "value": 0, "cumulative": 296400, "is_subtotal": True},
            {"label": "COGS", "value": -241200, "cumulative": 55200},
            {"label": "Contribution", "value": 0, "cumulative": 55200, "is_total": True}
        ]
    },
    "DTC": {
        "type": "dtc",
        "steps": [
            {"label": "Gross Revenue", "value": 960000, "cumulative": 960000},
            {"label": "Customer Acq. Cost", "value": -115200, "cumulative": 844800},
            {"label": "Fulfillment", "value": -153600, "cumulative": 691200},
            {"label": "Payment Processing", "value": -28800, "cumulative": 662400},
            {"label": "Returns", "value": -19200, "cumulative": 643200},
            {"label": "Net Revenue", "value": 0, "cumulative": 643200, "is_subtotal": True},
            {"label": "COGS", "value": -124800, "cumulative": 518400},
            {"label": "Contribution", "value": 0, "cumulative": 518400, "is_total": True}
        ]
    }
}


def extract_live(conn_string: str) -> dict:
    """Extract deduction waterfall from Postgres. Requires psycopg2.

    Schema uncertainty handled:
      - Query information_schema.columns to discover which deduction types exist
      - Build waterfall dynamically from available columns
      - Missing deduction types are omitted from the waterfall
    """
    try:
        import psycopg2  # noqa: F401
    except ImportError:
        print(
            "ERROR: psycopg2 not installed. Run: pip install psycopg2-binary",
            file=sys.stderr
        )
        sys.exit(1)

    # TODO: implement live extraction after schema verification.
    # Key schema unknowns to resolve before implementing:
    #   1. Which deduction types exist? Query information_schema.columns on deductions table.
    #   2. Are deductions in a wide table (one column per type) or narrow (type, amount rows)?
    #   3. How is COGS stored — line item or derived?
    raise NotImplementedError(
        "Live extraction requires schema verification first. Use --snapshot."
    )


def validate_waterfall(channel: str, channel_data: dict) -> None:
    """Verify waterfall arithmetic is internally consistent."""
    steps = channel_data["steps"]

    if not steps:
        raise ValueError(f"{channel}: steps list is empty")

    # First step must be Gross Revenue with positive value
    first = steps[0]
    if first["label"] != "Gross Revenue":
        raise ValueError(f"{channel}: first step must be 'Gross Revenue', got '{first['label']}'")
    if first["value"] <= 0:
        raise ValueError(f"{channel}: Gross Revenue must be positive")

    gross = first["value"]

    # Walk through steps and verify cumulative arithmetic
    running = gross
    net_revenue_cumulative = None
    contribution_cumulative = None

    for step in steps[1:]:
        is_subtotal = step.get("is_subtotal", False)
        is_total = step.get("is_total", False)

        if not is_subtotal and not is_total:
            # Real deduction step: cumulative should advance by value
            running += step["value"]
            if abs(running - step["cumulative"]) > 1:  # $1 tolerance for rounding
                raise ValueError(
                    f"{channel} step '{step['label']}': "
                    f"expected cumulative {running:.0f}, got {step['cumulative']}"
                )
        else:
            # Subtotal/total marker: value=0, cumulative is a checkpoint
            running = step["cumulative"]

        if is_subtotal:
            net_revenue_cumulative = step["cumulative"]
        if is_total:
            contribution_cumulative = step["cumulative"]

    if net_revenue_cumulative is None:
        raise ValueError(f"{channel}: no is_subtotal (Net Revenue) step found")
    if contribution_cumulative is None:
        raise ValueError(f"{channel}: no is_total (Contribution) step found")


def reconcile(data: dict) -> None:
    """Validate all channels in the deductions dataset."""
    if not data:
        raise ValueError("Empty deductions data — nothing to reconcile.")

    for channel, channel_data in data.items():
        if "steps" not in channel_data:
            raise ValueError(f"{channel}: missing 'steps' key")
        if "type" not in channel_data:
            raise ValueError(f"{channel}: missing 'type' key")
        if channel_data["type"] not in ("retail", "dtc"):
            raise ValueError(f"{channel}: unknown type '{channel_data['type']}'")
        validate_waterfall(channel, channel_data)


def main():
    parser = argparse.ArgumentParser(
        description="Extract deduction waterfall data."
    )
    parser.add_argument(
        "--snapshot",
        action="store_true",
        help="Use snapshot data (no DB required)"
    )
    args = parser.parse_args()

    if args.snapshot:
        data = SNAPSHOT_DATA
    else:
        conn_string = os.environ.get("DATABASE_URL")
        if not conn_string:
            print(
                "ERROR: DATABASE_URL environment variable not set. "
                "Use --snapshot for offline mode.",
                file=sys.stderr
            )
            sys.exit(1)
        data = extract_live(conn_string)

    reconcile(data)

    out_path = Path(__file__).parent.parent / "src" / "data" / "deductions.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Written: {out_path} ({len(data)} channels)")


if __name__ == "__main__":
    main()
