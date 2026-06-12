#!/usr/bin/env python3
"""
00_export_snapshot.py — Build or refresh data/snapshot.db from Cinderhaven Postgres.

This is the ONLY script in this project that touches an external database.
All other scripts (01, 02, 03) read from the local snapshot only.

Usage:
  python scripts/00_export_snapshot.py          # export from Fly.io via flyctl
  python scripts/00_export_snapshot.py --seed   # seed from 2026-05-22 baseline constants

Run after seeding/exporting:
  python scripts/01_extract_channel_data.py
  python scripts/02_extract_deductions.py
  python scripts/03_extract_scenarios.py

Requirements (live mode only):
  flyctl authenticated and on PATH: https://fly.io/docs/flyctl/install/

Schema notes:
  The 'units_sold' column is populated by the live export (units_ordered × case_pack_qty).
  It is NULL in the seed baseline — contributing to null contribution_per_unit in JSON.
  Run the live export to populate it.
"""

import argparse
import re
import sqlite3
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DB_PATH = ROOT / "data" / "snapshot.db"
FLY_APP = "cinderhaven-db"

# ── Schema ───────────────────────────────────────────────────────────────────

SCHEMA = """
CREATE TABLE IF NOT EXISTS snapshot_meta (
    key   TEXT PRIMARY KEY,
    value TEXT
);

-- One row per channel. units_sold is NULL until populated by live export.
CREATE TABLE IF NOT EXISTS channels (
    channel         TEXT PRIMARY KEY,
    channel_type    TEXT,     -- 'retailer' | 'distributor' | 'dtc'
    gross_revenue   REAL,
    cogs_amount     REAL,     -- manufacturing COGS (cogs_ratio × gross_revenue)
    total_deductions REAL,    -- sum of all deduction line items
    promo_costs     REAL,
    overhead_cost   REAL,     -- dispute-labor overhead (hours × $35/hr)
    disputes        INTEGER,
    dispute_events  INTEGER,
    units_sold      INTEGER   -- NULL until populated by live export
);

-- One row per channel × deduction type.
CREATE TABLE IF NOT EXISTS deductions (
    channel         TEXT,
    deduction_type  TEXT,
    category        TEXT,     -- 'trade' | 'compliance'
    total_amount    REAL,
    event_count     INTEGER,
    PRIMARY KEY (channel, deduction_type)
);

-- Quarterly revenue for trend charts.
CREATE TABLE IF NOT EXISTS quarterly_revenue (
    quarter_start  TEXT,   -- ISO date, e.g. '2024-01-01'
    channel        TEXT,
    revenue        REAL,
    PRIMARY KEY (quarter_start, channel)
);

-- Quarterly deductions for trend charts.
CREATE TABLE IF NOT EXISTS quarterly_deductions (
    quarter_start  TEXT,
    channel        TEXT,
    total_deductions REAL,
    PRIMARY KEY (quarter_start, channel)
);
"""

# ── Seed constants (2026-05-22 extraction from Cinderhaven Postgres) ─────────
# These are the real numbers pulled by channel-profitability-analysis/scripts/refresh_data.py.
# They represent cumulative revenue across fiscal years 2023–2025 (~3 years).
# units_sold is absent — requires the live export path.

CHANNEL_TYPES = {
    "UNFI": "distributor", "DPI Northwest": "distributor", "KeHE": "distributor",
    "DTC": "dtc",
    "Sprouts": "retailer", "Whole Foods": "retailer", "Regional Group": "retailer",
    "Kroger": "retailer", "Walmart": "retailer", "Costco": "retailer",
}

# Catalog-true ratios: SUM(units ordered x raw.sku_costs.cogs_per_unit) /
# invoiced revenue per channel, certified replica 2026-06-12. Distributors
# buy the same units at lower prices, so their COGS ratio is HIGHER than
# retail. The previous hand-entered ratios (7.6-16.9% wholesale) were ~3x
# low and inverted, which manufactured most of the distributor-vs-retail
# margin delta this project reports.
COGS_RATIOS = {
    "UNFI": 0.5349, "DPI Northwest": 0.5453, "KeHE": 0.5233,
    "DTC": 0.1740,
    "Sprouts": 0.4387, "Whole Foods": 0.4163, "Regional Group": 0.4634,
    "Kroger": 0.4637, "Walmart": 0.4818, "Costco": 0.5015,
}

FISCAL_REVENUE = {
    "UNFI": 10450336.32, "DPI Northwest": 5602560.48, "KeHE": 8405927.76,
    "DTC": 572510.27,
    "Sprouts": 8106459.60, "Whole Foods": 9705060.00, "Regional Group": 6075642.72,
    "Kroger": 10550521.68, "Walmart": 10894584.00, "Costco": 6467230.08,
}

DEDUCTIONS_RAW = {
    "UNFI": {
        "promo_billback": (28299.77, 188), "pricing_error": (27958.68, 173),
        "short_ship": (30716.69, 184), "damaged": (32656.85, 191),
        "late_delivery": (26295.48, 166),
    },
    "DPI Northwest": {
        "promo_billback": (13167.27, 83), "pricing_error": (18278.79, 117),
        "short_ship": (16644.98, 94), "damaged": (13288.84, 88),
        "late_delivery": (12959.84, 82),
    },
    "KeHE": {
        "promo_billback": (23856.40, 137), "pricing_error": (22711.33, 155),
        "short_ship": (21105.60, 131), "damaged": (21741.93, 144),
        "late_delivery": (27900.75, 161),
    },
    "Sprouts": {
        "promo_billback": (26076.71, 268), "pricing_error": (26161.47, 256),
        "short_ship": (23103.29, 230), "slotting": (26675.91, 266),
        "label_fine": (23496.94, 228), "spoilage": (23462.67, 239),
        "damaged": (22621.38, 230), "pallet_fine": (23168.62, 238),
        "late_delivery": (22181.71, 233),
    },
    "Whole Foods": {
        "promo_billback": (24508.63, 235), "pricing_error": (23777.81, 226),
        "short_ship": (26259.37, 266), "slotting": (27080.04, 266),
        "label_fine": (28492.83, 263), "spoilage": (29837.61, 276),
        "damaged": (28951.41, 243), "pallet_fine": (29092.92, 281),
        "late_delivery": (28453.72, 269),
    },
    "Regional Group": {
        "promo_billback": (16844.42, 184), "pricing_error": (14670.89, 160),
        "short_ship": (15840.38, 178), "slotting": (17457.95, 186),
        "label_fine": (15393.01, 167), "spoilage": (16468.22, 178),
        "damaged": (17552.71, 198), "pallet_fine": (16414.43, 179),
        "late_delivery": (18217.23, 184),
    },
    "Kroger": {
        "promo_billback": (25484.51, 290), "pricing_error": (28794.63, 322),
        "short_ship": (28839.58, 303), "slotting": (28396.85, 312),
        "label_fine": (29581.42, 316), "spoilage": (29956.72, 317),
        "damaged": (30879.45, 332), "pallet_fine": (29759.91, 298),
        "late_delivery": (31608.55, 335),
    },
    "Walmart": {
        "promo_billback": (29692.07, 324), "pricing_error": (32355.88, 344),
        "short_ship": (33971.93, 377), "slotting": (25739.41, 292),
        "label_fine": (29052.28, 327), "spoilage": (28771.96, 319),
        "damaged": (30202.97, 316), "pallet_fine": (29533.79, 323),
        "late_delivery": (29418.05, 306),
    },
    "Costco": {
        "promo_billback": (19679.80, 229), "pricing_error": (18559.07, 213),
        "short_ship": (16322.63, 200), "slotting": (18544.95, 209),
        "label_fine": (18721.02, 208), "spoilage": (20324.60, 221),
        "damaged": (17656.49, 217), "pallet_fine": (18244.18, 215),
        "late_delivery": (19348.69, 212),
    },
    "DTC": {},  # DTC has no trade deductions (no chargebacks, no slotting)
}

OVERHEAD_RATE = 35.00  # $/hr, fully loaded

PROMO_COSTS = {
    "UNFI": 444.00, "DPI Northwest": 266.00, "KeHE": 266.00,
    "DTC": 0.00,
    "Sprouts": 538.00, "Whole Foods": 1140.00, "Regional Group": 538.00,
    "Kroger": 538.00, "Walmart": 1613.00, "Costco": 2220.00,
}

DISPUTE_DATA = {
    "Walmart":        {"disputes": 1143, "events": 2928, "hours": 2361.4},
    "Kroger":         {"disputes": 1099, "events": 2825, "hours": 2255.8},
    "Whole Foods":    {"disputes": 945,  "events": 2325, "hours": 2038.8},
    "Sprouts":        {"disputes": 862,  "events": 2188, "hours": 1909.1},
    "Costco":         {"disputes": 743,  "events": 1924, "hours": 1597.3},
    "Regional Group": {"disputes": 597,  "events": 1614, "hours": 1231.1},
    "UNFI":           {"disputes": 315,  "events": 902,  "hours": 497.4},
    "KeHE":           {"disputes": 268,  "events": 728,  "hours": 442.6},
    "DPI Northwest":  {"disputes": 169,  "events": 464,  "hours": 270.5},
    "DTC":            {"disputes": 0,    "events": 0,    "hours": 0.0},
}

QUARTERLY_REVENUE = {
    "2023-01-01": {"UNFI": 740038.56, "DPI Northwest": 337883.04, "KeHE": 604097.76, "DTC": 38338.66, "Sprouts": 537777.84, "Whole Foods": 642028.56, "Regional Group": 388449.12, "Kroger": 710033.76, "Walmart": 763554.00, "Costco": 433693.44},
    "2023-04-01": {"UNFI": 773337.60, "DPI Northwest": 480131.52, "KeHE": 599990.88, "DTC": 47597.63, "Sprouts": 671741.76, "Whole Foods": 828656.40, "Regional Group": 458830.56, "Kroger": 775925.52, "Walmart": 734754.00, "Costco": 531711.36},
    "2023-07-01": {"UNFI": 820043.04, "DPI Northwest": 439206.24, "KeHE": 601840.08, "DTC": 46882.85, "Sprouts": 614320.08, "Whole Foods": 734439.36, "Regional Group": 474634.56, "Kroger": 796722.48, "Walmart": 884832.00, "Costco": 520974.72},
    "2023-10-01": {"UNFI": 1158884.16, "DPI Northwest": 583191.84, "KeHE": 864382.32, "DTC": 61057.42, "Sprouts": 882586.08, "Whole Foods": 990607.20, "Regional Group": 593567.04, "Kroger": 1084892.88, "Walmart": 1158972.00, "Costco": 712874.88},
    "2024-01-01": {"UNFI": 803893.92, "DPI Northwest": 367007.52, "KeHE": 622286.16, "DTC": 39586.25, "Sprouts": 594437.04, "Whole Foods": 618673.68, "Regional Group": 431552.40, "Kroger": 728585.76, "Walmart": 746304.00, "Costco": 452695.68},
    "2024-04-01": {"UNFI": 789677.52, "DPI Northwest": 463061.28, "KeHE": 592820.40, "DTC": 48098.82, "Sprouts": 681847.20, "Whole Foods": 728794.80, "Regional Group": 500438.16, "Kroger": 891440.40, "Walmart": 852426.00, "Costco": 537264.00},
    "2024-07-01": {"UNFI": 842655.36, "DPI Northwest": 491182.56, "KeHE": 696657.12, "DTC": 45839.43, "Sprouts": 670198.08, "Whole Foods": 842059.68, "Regional Group": 515454.24, "Kroger": 841389.12, "Walmart": 946008.00, "Costco": 502686.72},
    "2024-10-01": {"UNFI": 1296819.36, "DPI Northwest": 636086.88, "KeHE": 924224.64, "DTC": 56054.77, "Sprouts": 884634.96, "Whole Foods": 1069252.32, "Regional Group": 647198.64, "Kroger": 1154401.44, "Walmart": 1109310.00, "Costco": 647331.84},
    "2025-01-01": {"UNFI": 706168.56, "DPI Northwest": 327534.24, "KeHE": 504550.08, "DTC": 35748.25, "Sprouts": 551670.24, "Whole Foods": 580649.28, "Regional Group": 425413.92, "Kroger": 706677.84, "Walmart": 747438.00, "Costco": 426055.68},
    "2025-04-01": {"UNFI": 808723.68, "DPI Northwest": 440045.76, "KeHE": 702839.52, "DTC": 42778.60, "Sprouts": 529746.00, "Whole Foods": 791415.36, "Regional Group": 460960.32, "Kroger": 796644.96, "Walmart": 811806.00, "Costco": 518204.16},
    "2025-07-01": {"UNFI": 708474.24, "DPI Northwest": 475247.52, "KeHE": 708315.36, "DTC": 45076.15, "Sprouts": 671315.04, "Whole Foods": 805232.88, "Regional Group": 525874.56, "Kroger": 852390.48, "Walmart": 934014.00, "Costco": 454170.24},
    "2025-10-01": {"UNFI": 980221.20, "DPI Northwest": 547789.44, "KeHE": 962036.64, "DTC": 63895.48, "Sprouts": 797519.28, "Whole Foods": 1041038.40, "Regional Group": 639624.48, "Kroger": 1179229.92, "Walmart": 1176924.00, "Costco": 706170.24},
}

QUARTERLY_DEDUCTIONS = {
    "2023-01-01": {"UNFI": 6015.40,  "KeHE": 5471.28,  "DPI Northwest": 2526.64, "Sprouts": 7486.57,  "Whole Foods": 10722.08, "Regional Group": 4019.01,  "Kroger": 11484.64, "Walmart": 11580.06, "Costco": 4807.11},
    "2023-04-01": {"UNFI": 12916.17, "KeHE": 10630.81, "DPI Northwest": 6617.83, "Sprouts": 16885.52, "Whole Foods": 20518.17, "Regional Group": 10410.60, "Kroger": 18383.05, "Walmart": 21547.53, "Costco": 13278.67},
    "2023-07-01": {"UNFI": 11219.99, "KeHE": 8570.47,  "DPI Northwest": 8664.28, "Sprouts": 16759.33, "Whole Foods": 21015.36, "Regional Group": 12601.80, "Kroger": 23011.24, "Walmart": 21754.29, "Costco": 10737.12},
    "2023-10-01": {"UNFI": 14384.02, "KeHE": 10382.72, "DPI Northwest": 9291.60, "Sprouts": 20829.44, "Whole Foods": 19825.13, "Regional Group": 14958.76, "Kroger": 27611.10, "Walmart": 27763.83, "Costco": 15566.04},
    "2024-01-01": {"UNFI": 18045.26, "KeHE": 9835.88,  "DPI Northwest": 4612.08, "Sprouts": 20990.19, "Whole Foods": 21606.86, "Regional Group": 13592.55, "Kroger": 23193.19, "Walmart": 25482.92, "Costco": 16174.82},
    "2024-04-01": {"UNFI": 12456.01, "KeHE": 8357.20,  "DPI Northwest": 6024.18, "Sprouts": 22608.91, "Whole Foods": 18793.65, "Regional Group": 13604.39, "Kroger": 22828.44, "Walmart": 18081.78, "Costco": 15332.12},
    "2024-07-01": {"UNFI": 9688.02,  "KeHE": 10549.09, "DPI Northwest": 7319.38, "Sprouts": 16522.66, "Whole Foods": 21958.74, "Regional Group": 13884.05, "Kroger": 22186.70, "Walmart": 22874.51, "Costco": 12132.89},
    "2024-10-01": {"UNFI": 12273.23, "KeHE": 13659.71, "DPI Northwest": 4148.39, "Sprouts": 18725.14, "Whole Foods": 23697.00, "Regional Group": 14178.28, "Kroger": 23931.30, "Walmart": 27688.39, "Costco": 20131.86},
    "2025-01-01": {"UNFI": 16293.22, "KeHE": 9162.30,  "DPI Northwest": 5913.25, "Sprouts": 18301.33, "Whole Foods": 21394.37, "Regional Group": 13050.76, "Kroger": 24643.55, "Walmart": 23716.52, "Costco": 13132.65},
    "2025-04-01": {"UNFI": 10002.84, "KeHE": 9237.43,  "DPI Northwest": 4910.64, "Sprouts": 18305.46, "Whole Foods": 18262.34, "Regional Group": 12617.70, "Kroger": 19903.34, "Walmart": 18357.65, "Costco": 12529.18},
    "2025-07-01": {"UNFI": 8997.35,  "KeHE": 9342.50,  "DPI Northwest": 7181.19, "Sprouts": 17421.43, "Whole Foods": 25119.22, "Regional Group": 12512.88, "Kroger": 21367.60, "Walmart": 23822.39, "Costco": 15560.92},
    "2025-10-01": {"UNFI": 13410.14, "KeHE": 11748.08, "DPI Northwest": 6958.50, "Sprouts": 21790.33, "Whole Foods": 23074.70, "Regional Group": 12802.80, "Kroger": 23838.43, "Walmart": 25783.86, "Costco": 17605.83},
}

TRADE_TYPES = {"promo_billback", "pricing_error", "short_ship", "slotting"}
COMPLIANCE_TYPES = {"label_fine", "spoilage", "damaged", "pallet_fine", "late_delivery"}

QUARTER_LABELS = {
    "2023-01-01": "Q1 2023", "2023-04-01": "Q2 2023",
    "2023-07-01": "Q3 2023", "2023-10-01": "Q4 2023",
    "2024-01-01": "Q1 2024", "2024-04-01": "Q2 2024",
    "2024-07-01": "Q3 2024", "2024-10-01": "Q4 2024",
    "2025-01-01": "Q1 2025", "2025-04-01": "Q2 2025",
    "2025-07-01": "Q3 2025", "2025-10-01": "Q4 2025",
}


# ── Seed mode ─────────────────────────────────────────────────────────────────

def seed_snapshot(db: sqlite3.Connection) -> None:
    """Populate snapshot.db from the 2026-05-22 baseline constants."""
    cur = db.cursor()

    # Channels
    for channel, ctype in CHANNEL_TYPES.items():
        revenue = FISCAL_REVENUE[channel]
        cogs = round(revenue * COGS_RATIOS[channel], 2)
        ded_data = DEDUCTIONS_RAW.get(channel, {})
        total_deductions = round(sum(v[0] for v in ded_data.values()), 2)
        promo = PROMO_COSTS.get(channel, 0.0)
        dispute = DISPUTE_DATA.get(channel, {"disputes": 0, "events": 0, "hours": 0.0})
        overhead = round(dispute["hours"] * OVERHEAD_RATE, 2)

        cur.execute(
            """
            INSERT OR REPLACE INTO channels
              (channel, channel_type, gross_revenue, cogs_amount,
               total_deductions, promo_costs, overhead_cost,
               disputes, dispute_events, units_sold)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (channel, ctype, revenue, cogs, total_deductions,
             promo, overhead, dispute["disputes"], dispute["events"], None),
        )

    # Deductions
    for channel, ded_data in DEDUCTIONS_RAW.items():
        for dtype, (amount, count) in ded_data.items():
            category = "trade" if dtype in TRADE_TYPES else "compliance"
            cur.execute(
                """
                INSERT OR REPLACE INTO deductions
                  (channel, deduction_type, category, total_amount, event_count)
                VALUES (?, ?, ?, ?, ?)
                """,
                (channel, dtype, category, round(amount, 2), count),
            )

    # Quarterly revenue
    for q_start, channels_rev in QUARTERLY_REVENUE.items():
        for channel, revenue in channels_rev.items():
            cur.execute(
                "INSERT OR REPLACE INTO quarterly_revenue (quarter_start, channel, revenue) VALUES (?, ?, ?)",
                (q_start, channel, revenue),
            )

    # Quarterly deductions
    for q_start, channels_ded in QUARTERLY_DEDUCTIONS.items():
        for channel, total in channels_ded.items():
            cur.execute(
                "INSERT OR REPLACE INTO quarterly_deductions (quarter_start, channel, total_deductions) VALUES (?, ?, ?)",
                (q_start, channel, total),
            )

    cur.execute(
        "INSERT OR REPLACE INTO snapshot_meta (key, value) VALUES (?, ?)",
        ("exported_at", "2026-05-22T00:00:00+00:00"),
    )
    cur.execute(
        "INSERT OR REPLACE INTO snapshot_meta (key, value) VALUES (?, ?)",
        ("source", "seed — 2026-05-22 Cinderhaven baseline (channel-profitability-analysis)"),
    )
    cur.execute(
        "INSERT OR REPLACE INTO snapshot_meta (key, value) VALUES (?, ?)",
        ("units_populated", "false"),
    )
    db.commit()


# ── Live export (flyctl) ───────────────────────────────────────────────────────

def _run_sql(sql: str) -> str:
    """Run SQL against cinderhaven-db via flyctl and return raw output."""
    cmd = ["flyctl", "postgres", "connect", "-a", FLY_APP]
    full_sql = "\\pset pager off\n\\pset footer off\n\\c cinderhaven\n" + sql
    result = subprocess.run(
        cmd, input=full_sql, capture_output=True, text=True, timeout=180
    )
    if result.returncode != 0:
        print(f"ERROR: flyctl failed:\n{result.stderr}", file=sys.stderr)
        sys.exit(1)
    return result.stdout


def _parse_table(output: str) -> list[dict]:
    """Parse psql tabular output into a list of dicts."""
    lines = output.strip().split("\n")
    headers = None
    rows = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        # Strip ANSI escape sequences
        stripped = re.sub(r"\x1b\[[^a-zA-Z]*[a-zA-Z]|\[\?[0-9]+[hl]", "", stripped).strip()
        if not stripped or set(stripped) <= {"-", "+", " "}:
            continue
        if stripped.startswith("(") and stripped.endswith("rows)"):
            continue
        if "|" not in stripped:
            continue
        parts = [p.strip() for p in stripped.split("|")]
        if headers is None:
            headers = parts
        elif len(parts) == len(headers):
            rows.append(dict(zip(headers, parts)))
    return rows


def live_export(db: sqlite3.Connection) -> None:
    """Export from Fly.io Postgres and write to snapshot.db."""
    cur = db.cursor()

    # Revenue by channel
    print("Fetching revenue…")
    revenue_rows = _parse_table(_run_sql("""
        SELECT channel, channel_type, revenue FROM (
            SELECT dr.retailer_name AS channel, 'retailer' AS channel_type,
                   ROUND(SUM(fo.total_value)::numeric, 2) AS revenue
            FROM public_marts.fct_retailer_orders fo
            JOIN public_marts.dim_retailers dr ON dr.retailer_id = fo.retailer_id
            GROUP BY dr.retailer_name
            UNION ALL
            SELECT dd.distributor_name AS channel, 'distributor' AS channel_type,
                   ROUND(SUM(fo.total_value)::numeric, 2) AS revenue
            FROM public_marts.fct_distributor_orders fo
            JOIN public_marts.dim_distributors dd ON dd.distributor_id = fo.distributor_id
            GROUP BY dd.distributor_name
            UNION ALL
            SELECT 'DTC' AS channel, 'dtc' AS channel_type,
                   ROUND(SUM(fo.gross_revenue)::numeric, 2) AS revenue
            FROM public_marts.fct_dtc_orders fo
        ) combined ORDER BY channel;
    """))

    # Units by channel (units_ordered × case_pack_qty)
    print("Fetching units…")
    units_rows = _parse_table(_run_sql("""
        SELECT channel, units FROM (
            SELECT dr.retailer_name AS channel,
                   SUM(fo.units_ordered * p.case_pack_qty)::int AS units
            FROM public_marts.fct_retailer_orders fo
            JOIN public_marts.dim_retailers dr ON dr.retailer_id = fo.retailer_id
            JOIN public_marts.dim_products p ON p.product_id = fo.product_id
            GROUP BY dr.retailer_name
            UNION ALL
            SELECT dd.distributor_name AS channel,
                   SUM(fo.units_ordered * p.case_pack_qty)::int AS units
            FROM public_marts.fct_distributor_orders fo
            JOIN public_marts.dim_distributors dd ON dd.distributor_id = fo.distributor_id
            JOIN public_marts.dim_products p ON p.product_id = fo.product_id
            GROUP BY dd.distributor_name
            UNION ALL
            SELECT 'DTC' AS channel,
                   COUNT(fo.order_id)::int AS units
            FROM public_marts.fct_dtc_orders fo
        ) combined ORDER BY channel;
    """))

    units_by_channel = {r["channel"]: int(r["units"]) for r in units_rows if r.get("channel")}

    # Deductions by channel × type
    print("Fetching deductions…")
    ded_rows = _parse_table(_run_sql("""
        SELECT channel, deduction_type, event_count, total_amount FROM (
            SELECT dr.retailer_name AS channel, fd.deduction_type,
                   COUNT(*)::int AS event_count,
                   ROUND(SUM(fd.deduction_amount)::numeric, 2) AS total_amount
            FROM public_marts.fct_retailer_deductions fd
            JOIN public_marts.dim_retailers dr ON dr.retailer_id = fd.retailer_id
            GROUP BY dr.retailer_name, fd.deduction_type
            UNION ALL
            SELECT dd.distributor_name AS channel, fd.deduction_type,
                   COUNT(*)::int AS event_count,
                   ROUND(SUM(fd.deduction_amount)::numeric, 2) AS total_amount
            FROM public_marts.fct_distributor_deductions fd
            JOIN public_marts.dim_distributors dd ON dd.distributor_id = fd.distributor_id
            GROUP BY dd.distributor_name, fd.deduction_type
        ) combined ORDER BY channel, total_amount DESC;
    """))

    # Quarterly revenue
    print("Fetching quarterly revenue…")
    qrev_rows = _parse_table(_run_sql("""
        SELECT DATE_TRUNC('quarter', po_date)::date AS quarter_start, channel, revenue FROM (
            SELECT fo.po_date, dr.retailer_name AS channel,
                   ROUND(SUM(fo.total_value)::numeric, 2) AS revenue
            FROM public_marts.fct_retailer_orders fo
            JOIN public_marts.dim_retailers dr ON dr.retailer_id = fo.retailer_id
            GROUP BY DATE_TRUNC('quarter', fo.po_date), dr.retailer_name
            UNION ALL
            SELECT fo.po_date, dd.distributor_name AS channel,
                   ROUND(SUM(fo.total_value)::numeric, 2) AS revenue
            FROM public_marts.fct_distributor_orders fo
            JOIN public_marts.dim_distributors dd ON dd.distributor_id = fo.distributor_id
            GROUP BY DATE_TRUNC('quarter', fo.po_date), dd.distributor_name
            UNION ALL
            SELECT fo.order_date AS po_date, 'DTC' AS channel,
                   ROUND(SUM(fo.gross_revenue)::numeric, 2) AS revenue
            FROM public_marts.fct_dtc_orders fo
            GROUP BY DATE_TRUNC('quarter', fo.order_date)
        ) combined ORDER BY quarter_start, channel;
    """))

    # Quarterly deductions
    print("Fetching quarterly deductions…")
    qded_rows = _parse_table(_run_sql("""
        SELECT DATE_TRUNC('quarter', deduction_date)::date AS quarter_start,
               channel, total_deductions FROM (
            SELECT fd.deduction_date, dr.retailer_name AS channel,
                   ROUND(SUM(fd.deduction_amount)::numeric, 2) AS total_deductions
            FROM public_marts.fct_retailer_deductions fd
            JOIN public_marts.dim_retailers dr ON dr.retailer_id = fd.retailer_id
            GROUP BY DATE_TRUNC('quarter', fd.deduction_date), dr.retailer_name
            UNION ALL
            SELECT fd.deduction_date, dd.distributor_name AS channel,
                   ROUND(SUM(fd.deduction_amount)::numeric, 2) AS total_deductions
            FROM public_marts.fct_distributor_deductions fd
            JOIN public_marts.dim_distributors dd ON dd.distributor_id = fd.distributor_id
            GROUP BY DATE_TRUNC('quarter', fd.deduction_date), dd.distributor_name
        ) combined ORDER BY quarter_start, channel;
    """))

    # Clear and repopulate
    for table in ("channels", "deductions", "quarterly_revenue", "quarterly_deductions"):
        cur.execute(f"DELETE FROM {table}")

    # COGS and promo/overhead are not in the live schema — use seed ratios as defaults
    for row in revenue_rows:
        channel = row["channel"]
        ctype = row["channel_type"]
        revenue = float(row["revenue"])
        # No silent default: an unknown channel must fail loudly rather than
        # get a fabricated cost ratio.
        cogs_ratio = COGS_RATIOS[channel]
        cogs = round(revenue * cogs_ratio, 2)
        promo = PROMO_COSTS.get(channel, 0.0)
        dispute = DISPUTE_DATA.get(channel, {"disputes": 0, "events": 0, "hours": 0.0})
        overhead = round(dispute["hours"] * OVERHEAD_RATE, 2)
        # Deductions will be summed separately below
        cur.execute(
            """
            INSERT OR REPLACE INTO channels
              (channel, channel_type, gross_revenue, cogs_amount,
               total_deductions, promo_costs, overhead_cost,
               disputes, dispute_events, units_sold)
            VALUES (?, ?, ?, ?, 0, ?, ?, ?, ?, ?)
            """,
            (channel, ctype, revenue, cogs,
             promo, overhead, dispute["disputes"], dispute["events"],
             units_by_channel.get(channel)),
        )

    for row in ded_rows:
        channel = row["channel"]
        dtype = row["deduction_type"]
        amount = float(row["total_amount"])
        count = int(row["event_count"])
        category = "trade" if dtype in TRADE_TYPES else "compliance"
        cur.execute(
            "INSERT OR REPLACE INTO deductions (channel, deduction_type, category, total_amount, event_count) VALUES (?, ?, ?, ?, ?)",
            (channel, dtype, category, amount, count),
        )
        cur.execute(
            "UPDATE channels SET total_deductions = total_deductions + ? WHERE channel = ?",
            (amount, channel),
        )

    for row in qrev_rows:
        cur.execute(
            "INSERT OR REPLACE INTO quarterly_revenue (quarter_start, channel, revenue) VALUES (?, ?, ?)",
            (row["quarter_start"], row["channel"], float(row["revenue"])),
        )

    for row in qded_rows:
        cur.execute(
            "INSERT OR REPLACE INTO quarterly_deductions (quarter_start, channel, total_deductions) VALUES (?, ?, ?)",
            (row["quarter_start"], row["channel"], float(row["total_deductions"])),
        )

    now = datetime.now(timezone.utc).isoformat()
    cur.execute("INSERT OR REPLACE INTO snapshot_meta (key, value) VALUES (?, ?)", ("exported_at", now))
    cur.execute("INSERT OR REPLACE INTO snapshot_meta (key, value) VALUES (?, ?)", ("source", f"live — flyctl export from {FLY_APP}"))
    units_populated = "true" if units_by_channel else "false"
    cur.execute("INSERT OR REPLACE INTO snapshot_meta (key, value) VALUES (?, ?)", ("units_populated", units_populated))
    db.commit()
    print(f"Live export complete: {len(revenue_rows)} channels, {len(ded_rows)} deduction rows.")


# ── Entry point ───────────────────────────────────────────────────────────────

def main() -> None:
    parser = argparse.ArgumentParser(description="Build or refresh data/snapshot.db.")
    parser.add_argument("--seed", action="store_true",
                        help="Seed from 2026-05-22 baseline constants (no network)")
    args = parser.parse_args()

    DB_PATH.parent.mkdir(parents=True, exist_ok=True)

    with sqlite3.connect(DB_PATH) as db:
        db.executescript(SCHEMA)

        if args.seed:
            seed_snapshot(db)
            print(f"Seeded: {DB_PATH}")
            print("NOTE: units_sold is NULL — run without --seed to populate from live DB.")
        else:
            live_export(db)
            print(f"Exported: {DB_PATH}")

    print("\nNext: regenerate JSON files:")
    print("  python scripts/01_extract_channel_data.py")
    print("  python scripts/02_extract_deductions.py")
    print("  python scripts/03_extract_scenarios.py")


if __name__ == "__main__":
    main()
