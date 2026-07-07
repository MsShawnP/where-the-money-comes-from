# Where the Money Comes From

An interactive web experience that answers one question for a $25M specialty food brand: **which channel actually pays after all deductions, and is the capital allocation wrong?**

**Live:** https://capital.lailarallc.com

---

## What it does

Five chapters walk a CFO/CEO from gross revenue through full channel contribution:

1. **The Revenue Illusion** — revenue rankings vs. contribution rankings
2. **The Margin Gap** — contribution margin % by channel
3. **The Hidden Tax of Retail** — deduction waterfalls: retail vs. distributor side-by-side
4. **The Scale Trap** — Walmart marginal contribution curve as volume grows
5. **The Capital Allocation Question** — $1M retail vs. distribution: Retail returns ~$54,000 more per million deployed than distribution

Built on Cinderhaven FY2024–2026 channel P&L data (10 channels: 6 retailers, 3 distributors, DTC).

---

## Data contract

All figures derive from the Cinderhaven Provisions canonical dataset:

- **50 SKUs** across 5 product lines (Artisan Sauces, Pantry Staples, Specialty Condiments, Dried Goods, Snack Bites)
- **6 retailers:** Walmart, Costco, Whole Foods, Sprouts, Kroger, Regional Group
- **3 distributors:** UNFI, KeHE, DPI Northwest
- **1 DTC:** Shopify

Source of truth: `cinderhaven-data-platform/CINDERHAVEN_CANONICAL.md`

---

## Stack

- **Frontend:** React 18 + Vite + TypeScript
- **Charts:** Observable Plot (SVG, no canvas)
- **Design:** Lailara Design System v2 (tokens in `src/tokens.css`)
- **Data pipeline:** Python 3 scripts → JSON baked into the Vite build
- **Hosting:** Cloudflare Pages

---

## How to run

```bash
npm install
npm run dev        # dev server at http://localhost:5173
npm run build      # production build to dist/
npm test           # 61 unit tests via Vitest
```

---

## How to refresh data

Data flows: Cinderhaven Postgres → SQLite snapshot → JSON → Vite build

```bash
# 1. Seed snapshot from hardcoded constants (no network needed)
python scripts/00_export_snapshot.py --seed

# 2. OR export live from Fly.io (requires flyctl authenticated)
python scripts/00_export_snapshot.py

# 3. Regenerate JSON files from the snapshot
python scripts/01_extract_channel_data.py   # → src/data/channels.json
python scripts/02_extract_deductions.py     # → src/data/deductions.json
python scripts/03_extract_scenarios.py      # → src/data/scenarios.json

# 4. Rebuild and deploy
npm run build
npx wrangler pages deploy dist
```

> **Note:** `units_sold` is null in the seed baseline — `contribution_per_unit` will be null
> until a live export populates it (Chapter 2 gracefully falls back to margin %).

---

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
  snapshot.db     — local SQLite cache (gitignored, regenerate with --seed)
```

---
Built by [Lailara LLC](https://lailarallc.com) — data hygiene and analytics consulting for specialty food brands scaling into national retail.
