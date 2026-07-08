# Where the Money Comes From — an interactive answer to "which channel actually pays?"

An interactive web experience that answers one question for a $25M specialty
food brand: **which channel actually pays after all deductions, and is the
capital allocation wrong?**

**Live:** https://capital.lailarallc.com

## What it does

Five chapters walk a CFO/CEO from gross revenue through full channel contribution:

1. **The Revenue Illusion** — revenue rankings vs. contribution rankings
2. **The Margin Gap** — contribution margin % by channel
3. **The Hidden Tax of Retail** — deduction waterfalls: retail vs. distributor side-by-side
4. **The Scale Trap** — Walmart marginal contribution curve as volume grows
5. **The Capital Allocation Question** — retail vs. distribution: retail returns ~$54,000 more contribution per $1M of incremental revenue (a per-revenue-dollar comparison, not return on capital)

Built on Cinderhaven FY2024–2026 channel P&L data (10 channels: 6 retailers, 3 distributors, DTC).

## Why it matters

Channel decisions at growing brands are usually made on gross revenue, because
that is the number everyone can see. Deductions, trade spend, and freight land
in different systems, so the true contribution by channel is invisible — and
capital keeps flowing to the biggest account rather than the best one. This
piece makes the gross-to-net story legible in one sitting and ends with a
concrete allocation decision, not a dashboard.

## Data contract

All figures derive from the Cinderhaven Provisions canonical dataset:

- **50 SKUs** across 5 product lines (Artisan Sauces, Pantry Staples, Specialty Condiments, Dried Goods, Snack Bites)
- **6 retailers:** Walmart, Costco, Whole Foods, Sprouts, Kroger, Regional Group
- **3 distributors:** UNFI, KeHE, DPI Northwest
- **1 DTC:** Shopify

Source of truth: `cinderhaven-data-platform/CINDERHAVEN_CANONICAL.md`

## Quick start

```bash
npm install
npm run dev        # dev server at http://localhost:5173
npm run build      # type-check + production build to dist/
npm run preview    # preview the production build
npm run lint       # ESLint
npx vitest run     # unit tests (Vitest + Testing Library)
```

### Refreshing the data

Data flows: Cinderhaven Postgres → SQLite snapshot → JSON → Vite build

```bash
# 1. Seed snapshot from hardcoded constants (no network needed)
python scripts/00_export_snapshot.py --seed

# 2. OR export live from Fly.io (requires flyctl authenticated)
python scripts/00_export_snapshot.py

# 3. Regenerate JSON files from the snapshot
python scripts/01_extract_channel_data.py   # -> src/data/channels.json
python scripts/02_extract_deductions.py     # -> src/data/deductions.json
python scripts/03_extract_scenarios.py      # -> src/data/scenarios.json

# 4. Rebuild and deploy
npm run build
npx wrangler pages deploy dist
```

> **Note:** `units_sold` is null in the seed baseline — `contribution_per_unit` will be null
> until a live export populates it (Chapter 2 gracefully falls back to margin %).

## Tech stack

- **Frontend:** React 19 + Vite + TypeScript
- **Charts:** Observable Plot (SVG, no canvas)
- **Design:** Lailara Design System v2 (tokens in `src/tokens.css`), Playfair
  Display + Source Sans 3 via Fontsource
- **Tests:** Vitest + React Testing Library (jsdom)
- **Data pipeline:** Python 3 scripts → JSON baked into the Vite build
- **Hosting:** Cloudflare Pages (deployed with Wrangler)

## Project structure

```
src/
  chapters/       — Chapter1–5 components
  components/     — PlotChart, WaterfallChart, DataTable, ChapterNav
  data/           — channels.json, deductions.json, scenarios.json (generated)
  utils/          — format.ts (dollar/percent/unit formatters)
  hooks/          — useChannelSelection.ts
  tokens.css      — Lailara Design System v2 tokens
scripts/
  00_export_snapshot.py   — Postgres → data/snapshot.db
  01_extract_channel_data.py
  02_extract_deductions.py
  03_extract_scenarios.py
data/
  snapshot.db     — local SQLite cache (regenerate with --seed)
```

## License

MIT

---
Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.
