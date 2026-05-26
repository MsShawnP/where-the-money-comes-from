# Where the Money Comes From — Decisions Log

Permanent record of choices that should survive session turnover.
If a decision is reversed, strike it through and add the replacement
below — don't delete.

---

## Format

Each entry:
- **Date** — when decided
- **Decision** — one sentence, imperative voice
- **Why** — the reasoning, including what was tried and rejected
- **Scope** — what this applies to (file, chunk, deliverable, or "global")
- **Do not** — explicit anti-instructions, if any

---

## Architecture & Pipeline

### 2026-05-26 — Use React + Vite + TypeScript + Observable Plot for the frontend
- **Why:** React handles chapter navigation and interactive state (channel selection, view toggles). Observable Plot produces clean SVG charts styleable to Lailara exactly — better output than Recharts/Nivo for analytical ranked/waterfall charts. Vite bundles JSON data at compile time for instant, offline-capable rendering. Consistent with Retailer Deduction Recovery project stack.
- **Scope:** Global — all frontend code in this project
- **Do not:** Do not introduce D3 directly, Recharts, Nivo, or a second chart library. Observable Plot covers all chart types needed. Do not use Scrollama or scroll-triggered reveals — chapter navigation is explicit user-controlled.

### 2026-05-26 — Bake all data into the build at compile time; no runtime data fetching
- **Why:** CFO must experience instantaneous load with no waiting. Piece must work offline after initial page load. Cinderhaven data is synthetic and static — it doesn't change between visits. Python pipeline runs once against Postgres, outputs JSON to `src/data/`, Vite bundles it as static imports. All charts render on first paint.
- **Scope:** Global — data pipeline and all chart data
- **Do not:** Do not add runtime fetch calls, API endpoints, or async data loading. Do not connect the frontend directly to Postgres. If data needs updating, re-run the Python pipeline and rebuild.

---

## Data & Schema

### 2026-05-26 — Cinderhaven data source is the SQLite file, not Postgres
- **Why:** The Cinderhaven Postgres platform is not directly accessible from this machine. The SQLite export at `../retailer-deduction-recovery/data/cinderhaven_deductions.db` is complete and reconciled — it's the correct source. Snapshot/fabricated JSON is not acceptable for a live CFO-facing piece.
- **Scope:** Python pipeline scripts (`scripts/01_extract_channel_data.py`, etc.). Any future data update must pull from the SQLite file or a fresh export.
- **Do not:** Fabricate or estimate channel P&L numbers. Do not query Postgres directly unless the connection string is verified and accessible. Do not ship placeholder data to the live site.

### 2026-05-26 — Individual units require case_pack_qty multiplication; never use raw order_lines.units_ordered as unit count
- **Why:** `order_lines.units_ordered` is in **cases**, not individual units. `sku_costs.cogs_per_unit` is per individual unit. Mixing these produces wildly wrong margins. Correct formula: `individual_units = SUM(ol.units_ordered * pm.case_pack_qty)`, `cogs = SUM(ol.units_ordered * pm.case_pack_qty * sc.cogs_per_unit)`.
- **Scope:** All pipeline scripts and any ad-hoc SQL against the Cinderhaven schema.
- **Do not:** Do not use `units_ordered` as a unit count without multiplying by `case_pack_qty`. Do not use `shipments.units_shipped` as a substitute (also in cases).

---

## Visualization

### 2026-05-26 — Ch3 side-by-side comparison direction: retail → UNFI, distributor → Walmart
- **Why:** When a retail channel is selected the most instructive contrast is the best-structured distributor (UNFI — low deductions). When a distributor is selected, the contrast is the highest-deduction retailer (Walmart). This asymmetry maximises the visible gap and makes the structural difference legible.
- **Scope:** `Chapter3.tsx` `getComparisonChannel()` logic and waterfall headings
- **Do not:** Do not default to DTC as the universal comparison — DTC is too small a channel to be the reference point for all other channels.

---

## Output Formats

### 2026-05-26 — No CTA; this piece is a conversation starter, not a funnel
- **Why:** The piece is sent directly by Shawn to a specific prospect before or after a conversation. The CFO is already in a relationship context. A CTA adds friction and changes the tone from "here's something interesting" to "here's a sales page." The piece does the priming; the conversation closes the loop.
- **Scope:** Global — product framing and page design
- **Do not:** Do not add email gates, contact forms, download buttons, or "book a call" links. Do not design the ending as a conversion moment.

---

## Writing & Voice

### 2026-05-26 — Narrative follows data; brief framing is a starting point, not a constraint
- **Why:** Real Cinderhaven numbers showed distributors at 90.2% margin vs retail at 81.1%. The original brief's DTC-hero framing wasn't supported by the data. Rewriting to match produced a more honest and credible piece.
- **Scope:** All chapter prose, framing text, and callout copy
- **Do not:** Do not write or preserve prose that contradicts the actual data values. If data is refreshed (e.g., `units_sold` populated via live export), update prose to match.

### 2026-05-26 — Waterfall must include all cost components to match contribution_dollars
- **Why:** The Ch3 deduction waterfall's final "Contribution" step was missing promo_costs and overhead_cost, producing a number $17K–$84K higher than channels.json depending on the channel. A CFO comparing the waterfall to the summary charts would see different numbers and lose trust. Fix: `02_extract_deductions.py` now loads and applies both fields as explicit steps.
- **Scope:** `scripts/02_extract_deductions.py`, `src/data/deductions.json`, and any future pipeline that builds a waterfall.
- **Do not:** Do not stop the waterfall at COGS. Promo Costs and Dispute Overhead must appear as explicit steps so the final Contribution label matches `contribution_dollars` in channels.json for every channel.

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
