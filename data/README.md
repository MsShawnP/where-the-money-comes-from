# data/snapshot.db — Cinderhaven Data Snapshot

This SQLite file is the **single source of truth** for all chart data in this project.
It is committed to the repo so the project is self-contained and reproducible offline.

## Current snapshot

| Field | Value |
|---|---|
| Source | Cinderhaven Postgres (cinderhaven-db on Fly.io) |
| Baseline extracted | 2026-05-22 |
| Covers | FY2024–FY2026 cumulative (~3 years) |
| Units populated | No — run live export to populate `units_sold` |

## How to use

**Build the JSON files from the committed snapshot (no network needed):**
```
python scripts/01_extract_channel_data.py
python scripts/02_extract_deductions.py
python scripts/03_extract_scenarios.py
```

**Refresh the snapshot from live Cinderhaven Postgres (requires flyctl):**
```
python scripts/00_export_snapshot.py
python scripts/01_extract_channel_data.py
python scripts/02_extract_deductions.py
python scripts/03_extract_scenarios.py
```

**Reset to the 2026-05-22 baseline (no flyctl needed):**
```
python scripts/00_export_snapshot.py --seed
```

## Schema

| Table | Description |
|---|---|
| `channels` | One row per channel — revenue, COGS, deductions, units |
| `deductions` | One row per channel × deduction type — amount, event count |
| `quarterly_revenue` | Revenue by channel × quarter for trend charts |
| `quarterly_deductions` | Total deductions by channel × quarter |
| `snapshot_meta` | Metadata: exported_at, source, units_populated |

## Why SQLite, not live Postgres?

This project's build process (Vite) is offline and stateless. The JSON files bundled
into the site are generated once from this snapshot, not at request time. That means:

1. The site can be built and deployed without a database connection
2. The data version the site uses is explicit (committed snapshot, not "whatever's in Postgres now")
3. Refreshing data is an intentional act — run the export script, review the output, commit

## Notes

- `units_sold` in the `channels` table is NULL in the seeded baseline.
  This means `contribution_per_unit` will be null in `channels.json` until
  the live export is run (which queries `units_ordered × case_pack_qty`).
  Chapter 2 (Per-Unit Showdown) will show nulls until then.

- Revenue figures are cumulative across the full date range in Postgres
  (FY2024–FY2026, approximately 3 years). For annual comparisons, divide by 3.
