# INPUT-SPEC — where-the-money-comes-from (client mode)

What to hand the tool for a client workshop. One channel unit-economics file (one
row per channel), CSV or XLSX. Derived from `src/data/channels.json`, not the README.

## Required columns

| Canonical | Type | Used for |
|---|---|---|
| `channel` | string (unique) | Channel/customer name. §1 |
| `channel_type` | string | `retailer` / `distributor` / `dtc`. §1 |
| `revenue` | number ≥ 0 | Channel revenue → contribution margin %. §1 |
| `contribution_dollars` | number | Contribution dollars (may be negative). §1 |
| `units_shipped` | number ≥ 0 | Units shipped → contribution per unit. §1 |

`contribution_per_unit = contribution_dollars / units_shipped`;
`contribution_margin_pct = contribution_dollars / revenue`.

## DTC basis (important)

DTC contribution is reported **pre-fee** — before processing fees and fulfillment.
No fee-inclusive DTC figure is produced: a canonical after-fees basis is a pending
decision, and this tool never invents one. DTC rows are labeled pre-fee in the
deliverable, and the wholesale channels are labeled "after deductions, chargebacks,
fees."

## Window (engagement.yml)

```yaml
as_of_date: "2026-01-31"          # analysis anchor; NEVER today's date
basis:
  window_label: "CY2025"          # printed on the output
```

## Run

```bash
pip install -e ../engagement-template/lib
python client_mode.py --config engagement.yml --input client-data/channels.csv \
    --out client-output [--final]
```

Output to `client-output/` (gitignored): a branded, provenance-footed,
DRAFT-watermarked `channel-economics-summary.html` (contribution per unit + margin
by channel, ranked, each with its basis) + `json/summary.json`; or a Data Readiness
Report if a required column is missing. The demo app is never edited (golden-locked).
