#!/usr/bin/env python3
"""
01_extract_channel_data.py — Extract channel profitability from Cinderhaven Postgres.

Produces src/data/channels.json with per-channel revenue, contribution dollars,
contribution margin %, units shipped, and contribution per unit.

Usage:
  python scripts/01_extract_channel_data.py --snapshot   # no DB needed
  python scripts/01_extract_channel_data.py              # requires DATABASE_URL env var

Schema notes (for live extraction):
  - dim_channels may or may not exist; if absent, infer channel from retailer ID
  - Deduction taxonomy completeness is unknown; treat missing deduction types as $0
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Snapshot constants — representative Cinderhaven figures from requirements doc
SNAPSHOT_DATA = [
    {
        "channel": "Walmart",
        "revenue": 1540000,
        "contribution_dollars": 8820,
        "contribution_margin_pct": 0.0057,
        "units_shipped": 21000,
        "contribution_per_unit": 0.42
    },
    {
        "channel": "KeHE",
        "revenue": 420000,
        "contribution_dollars": 32760,
        "contribution_margin_pct": 0.078,
        "units_shipped": 42000,
        "contribution_per_unit": 0.78
    },
    {
        "channel": "Food Service",
        "revenue": 380000,
        "contribution_dollars": 22800,
        "contribution_margin_pct": 0.060,
        "units_shipped": 38000,
        "contribution_per_unit": 0.60
    },
    {
        "channel": "Costco",
        "revenue": 680000,
        "contribution_dollars": 59500,
        "contribution_margin_pct": 0.0875,
        "units_shipped": 70000,
        "contribution_per_unit": 0.85
    },
    {
        "channel": "UNFI / Whole Foods",
        "revenue": 520000,
        "contribution_dollars": 55200,
        "contribution_margin_pct": 0.106,
        "units_shipped": 60000,
        "contribution_per_unit": 0.92
    },
    {
        "channel": "DTC",
        "revenue": 960000,
        "contribution_dollars": 518400,
        "contribution_margin_pct": 0.54,
        "units_shipped": 123429,
        "contribution_per_unit": 4.20
    }
]

REQUIRED_FIELDS = {
    "channel", "revenue", "contribution_dollars",
    "contribution_margin_pct", "units_shipped", "contribution_per_unit"
}


def extract_live(conn_string: str) -> list:
    """Extract from Postgres. Requires psycopg2.

    Schema uncertainty handled:
      - Tries dim_channels first; falls back to grouping by retailer_id
      - Missing deduction types default to 0 (LEFT JOIN pattern)
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
    #   1. Does dim_channels exist? If not, use retailer_id column.
    #   2. Which deduction types are present in the deductions table?
    #   3. What is the units column name (units_shipped, qty_shipped, cases)?
    raise NotImplementedError(
        "Live extraction requires schema verification first. Use --snapshot."
    )


def reconcile(data: list) -> None:
    """Verify structural and numerical consistency. Raises on failure."""
    if not data:
        raise ValueError("Empty channel data — nothing to reconcile.")

    channels_seen = set()
    for ch in data:
        missing = REQUIRED_FIELDS - ch.keys()
        if missing:
            raise ValueError(f"Channel record missing fields: {missing}")

        name = ch["channel"]
        if name in channels_seen:
            raise ValueError(f"Duplicate channel: {name}")
        channels_seen.add(name)

        if ch["revenue"] <= 0:
            raise ValueError(f"{name}: revenue must be positive, got {ch['revenue']}")

        if ch["units_shipped"] <= 0:
            raise ValueError(f"{name}: units_shipped must be positive")

        # Contribution per unit can be low (Walmart is $0.42) but must be > 0
        # for snapshot data. Allow negative only if explicitly labelled.
        if ch["contribution_per_unit"] <= 0:
            raise ValueError(
                f"{name}: contribution_per_unit is {ch['contribution_per_unit']}. "
                "Verify: channel may be loss-making."
            )

        # Sanity check: contribution_dollars ≈ contribution_per_unit * units_shipped
        implied = ch["contribution_per_unit"] * ch["units_shipped"]
        tolerance = max(100, implied * 0.02)  # 2% or $100, whichever is larger
        if abs(ch["contribution_dollars"] - implied) > tolerance:
            raise ValueError(
                f"{name}: contribution_dollars {ch['contribution_dollars']} "
                f"inconsistent with per_unit × units = {implied:.0f} "
                f"(tolerance ±{tolerance:.0f})"
            )


def main():
    parser = argparse.ArgumentParser(
        description="Extract channel profitability data."
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

    out_path = Path(__file__).parent.parent / "src" / "data" / "channels.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Written: {out_path} ({len(data)} channels)")


if __name__ == "__main__":
    main()
