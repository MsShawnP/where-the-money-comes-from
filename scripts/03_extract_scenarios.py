#!/usr/bin/env python3
"""
03_extract_scenarios.py — Build capital allocation scenarios from Cinderhaven data.

Produces src/data/scenarios.json with:
  - capital_allocation: $1M retail vs $1M DTC incremental contribution comparison
  - walmart_volume_curve: marginal contribution per unit at different volume levels
  - walmart_inflection_volume: volume above which marginal contribution turns negative

Usage:
  python scripts/03_extract_scenarios.py --snapshot   # no DB needed
  python scripts/03_extract_scenarios.py              # requires DATABASE_URL env var
"""
import argparse
import json
import os
import sys
from pathlib import Path

# Snapshot constants — representative Cinderhaven figures from requirements doc
SNAPSHOT_DATA = {
    "capital_allocation": {
        "retail": {
            "label": "$1M → Retail SKUs",
            "incremental_contribution": 42000,
            "assumption": (
                "Based on Walmart blended per-unit contribution of $0.42, "
                "~100K additional units"
            )
        },
        "dtc": {
            "label": "$1M → DTC Infrastructure",
            "incremental_contribution": 378000,
            "assumption": (
                "Based on DTC per-unit contribution of $4.20, ~90K incremental units "
                "(Shopify + email + retention)"
            )
        },
        "delta": 336000,
        "delta_pct": 8.0
    },
    "walmart_volume_curve": [
        {"volume_units": 5000, "marginal_contribution_per_unit": 2.10},
        {"volume_units": 8000, "marginal_contribution_per_unit": 1.68},
        {"volume_units": 12000, "marginal_contribution_per_unit": 1.12},
        {"volume_units": 16000, "marginal_contribution_per_unit": 0.78},
        {"volume_units": 21000, "marginal_contribution_per_unit": 0.42},
        {"volume_units": 28000, "marginal_contribution_per_unit": 0.21},
        {"volume_units": 35000, "marginal_contribution_per_unit": 0.08},
        {"volume_units": 42000, "marginal_contribution_per_unit": -0.12}
    ],
    "walmart_inflection_volume": 30000
}


def extract_live(conn_string: str) -> dict:
    """Derive scenarios from live Postgres data. Requires psycopg2.

    Scenarios are computed, not stored — they're derived from channel
    contribution rates and volume sensitivity models in the DB.
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
    # Scenarios are derived calculations:
    #   1. Pull per-unit contributions from channels pipeline output (channels.json)
    #      or re-query from DB
    #   2. Pull Walmart volume sensitivity from a volume_sensitivity or
    #      scenario_parameters table if it exists
    #   3. Compute delta and delta_pct from live contribution rates
    raise NotImplementedError(
        "Live extraction requires schema verification first. Use --snapshot."
    )


def reconcile(data: dict) -> None:
    """Verify scenario data is internally consistent."""
    if "capital_allocation" not in data:
        raise ValueError("Missing 'capital_allocation' key in scenarios data.")
    if "walmart_volume_curve" not in data:
        raise ValueError("Missing 'walmart_volume_curve' key in scenarios data.")
    if "walmart_inflection_volume" not in data:
        raise ValueError("Missing 'walmart_inflection_volume' key in scenarios data.")

    ca = data["capital_allocation"]
    retail_contrib = ca["retail"]["incremental_contribution"]
    dtc_contrib = ca["dtc"]["incremental_contribution"]
    expected_delta = dtc_contrib - retail_contrib

    if abs(ca["delta"] - expected_delta) > 1:
        raise ValueError(
            f"capital_allocation.delta {ca['delta']} does not match "
            f"dtc - retail = {expected_delta}"
        )

    if dtc_contrib <= retail_contrib:
        raise ValueError(
            f"DTC incremental contribution ({dtc_contrib}) should exceed "
            f"retail ({retail_contrib}) — check scenario assumptions."
        )

    # Volume curve must be ordered by increasing volume
    curve = data["walmart_volume_curve"]
    volumes = [pt["volume_units"] for pt in curve]
    if volumes != sorted(volumes):
        raise ValueError("walmart_volume_curve must be sorted by volume_units ascending.")

    # Verify volume curve is monotonically decreasing in marginal contribution
    # (higher volume = more deductions = lower marginal return)
    margins = [pt["marginal_contribution_per_unit"] for pt in curve]
    for i in range(1, len(margins)):
        if margins[i] >= margins[i - 1]:
            raise ValueError(
                f"walmart_volume_curve marginal contribution should be decreasing; "
                f"step {i}: {margins[i-1]} -> {margins[i]}"
            )

    # Inflection volume should be within the curve range
    inflection = data["walmart_inflection_volume"]
    if not (volumes[0] <= inflection <= volumes[-1]):
        raise ValueError(
            f"walmart_inflection_volume {inflection} is outside curve range "
            f"[{volumes[0]}, {volumes[-1]}]"
        )


def main():
    parser = argparse.ArgumentParser(
        description="Build capital allocation scenario data."
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

    out_path = Path(__file__).parent.parent / "src" / "data" / "scenarios.json"
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w") as f:
        json.dump(data, f, indent=2)
    print(f"Written: {out_path}")


if __name__ == "__main__":
    main()
