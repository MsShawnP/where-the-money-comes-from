---
title: "Interactive Analytics Deliverable: SQLite Snapshot + Baked JSON Architecture"
date: "2026-05-26"
category: "architecture-patterns"
module: "Data Pipeline & Visualization"
problem_type: architecture_pattern
component: tooling
severity: medium
applies_when:
  - "Building an analytics deliverable to be shared as a URL without a backend"
  - "Creating a data story from Postgres/SQL with no live DB connection at runtime"
  - "Interactive charts must work offline and on mobile"
  - "CPG channel profitability or deduction waterfall analysis"
tags:
  - offline-capable
  - sqlite-snapshot
  - vite
  - observable-plot
  - cpg
  - analytics-deliverable
  - data-pipeline
  - interactive-story
---

# Interactive Analytics Deliverable: SQLite Snapshot + Baked JSON Architecture

## Context

Analytics deliverables frequently ship with two failure modes baked in:

1. **Live DB dependency at runtime** — the app hits Postgres at runtime, requires credentials, has an auth surface, and breaks when the DB changes or goes offline. For a deliverable shared as a link, this is a reliability and access problem from the first open.
2. **Brief-driven narrative** — the story is written before the data is audited, producing a polished deliverable that gives the client wrong advice.

The "Where the Money Comes From" project resolved both by separating the data access layer (a one-time Python pipeline run against a committed SQLite snapshot) from the runtime app (a fully static Vite bundle with JSON imported at build time). The original brief anticipated DTC as the hero channel. Real Cinderhaven data showed distributors at 90.2% contribution margin vs retailers at 81.1% — the narrative was rewritten to match what the numbers actually said.

## Guidance

### 1. Data-first narrative architecture

Audit the data before writing a single line of narrative. The workflow:

1. Export and commit a SQLite snapshot from the live DB
2. Run the Python pipeline — compute core metrics and read the output
3. Find what the data *actually* shows before opening any narrative doc
4. Write the chapter structure and framing copy to match the real numbers

If the data contradicts the brief, the data wins. Document the contradiction in DECISIONS.md: "Brief assumed X. Data shows Y. Narrative follows data."

```python
# Audit before writing — run this before drafting any chapter
import sqlite3, pandas as pd

conn = sqlite3.connect("data/snapshot.db")
df = pd.read_sql("""
    SELECT channel,
           ROUND(SUM(net_revenue - cogs) / SUM(net_revenue), 3) AS contribution_margin_pct
    FROM channel_economics
    GROUP BY channel
    ORDER BY contribution_margin_pct DESC
""", conn)
print(df)  # read this before writing Chapter 1
```

### 2. SQLite snapshot + baked JSON pipeline

Replace the live DB connection with a build-time snapshot. The pipeline:

```
00_export_snapshot.py     ← only script that touches external data (Fly.io Postgres)
                           writes: data/snapshot.db (committed to repo)

01_extract_channel_data.py ← reads data/snapshot.db, writes src/data/channels.json
02_extract_deductions.py   ← reads data/snapshot.db, writes src/data/deductions.json
03_extract_scenarios.py    ← reads data/snapshot.db, writes src/data/scenarios.json

vite build                 ← imports *.json at compile time, bundles them in
```

Scripts 01–03 must read *only* from `data/snapshot.db`. The one script that touches external data (`00`) runs manually and deliberately. This makes the project buildable offline and eliminates cross-project dependencies.

```python
# scripts/01_extract_channel_data.py
import sqlite3, json
from pathlib import Path

SNAPSHOT = Path(__file__).parent.parent / "data" / "snapshot.db"
OUTPUT   = Path(__file__).parent.parent / "src" / "data" / "channels.json"

conn = sqlite3.connect(SNAPSHOT)
conn.row_factory = sqlite3.Row  # rows support dict() directly; column aliases become keys

rows = conn.execute("""
    SELECT
        channel_id       AS id,
        channel_name     AS name,
        gross_revenue    AS grossRevenue,
        net_revenue      AS netRevenue,
        cogs,
        units_ordered    AS unitsOrdered,
        case_pack_qty    AS casePackQty,
        -- CRITICAL: units_ordered is cases, not individual units
        ROUND((net_revenue - cogs) /
              (units_ordered * case_pack_qty), 4) AS contributionPerUnit
    FROM channel_economics
""").fetchall()

OUTPUT.write_text(json.dumps([dict(r) for r in rows], indent=2))
```

```typescript
// In Vite component — JSON is a static import, no fetch, no loading state
import channelData from '../data/channels.json'
import * as Plot from '@observablehq/plot'

// TypeScript infers a narrow literal type from JSON imports; cast to the runtime shape.
// `as unknown as` is intentional: the inferred type and Record<string, unknown>[] are
// structurally incompatible under strict mode even though the data matches at runtime.
const data = channelData as unknown as Record<string, unknown>[]

export function ChannelChart() {
  return (
    <PlotChart
      data={data}
      title="Contribution per unit by channel"
      spec={(d) => ({
        marks: [
          Plot.barY(d, { x: 'name', y: 'contributionPerUnit', fill: '#1f2e7a' }),
          Plot.text(d, { x: 'name', y: 'contributionPerUnit',
            text: (r) => `$${Number(r.contributionPerUnit).toFixed(2)}`, dy: -8 }),
        ],
      })}
    />
  )
}
```

```json
{
  "scripts": {
    "pipeline": "python scripts/01_extract_channel_data.py && python scripts/02_extract_deductions.py && python scripts/03_extract_scenarios.py",
    "prebuild": "npm run pipeline",
    "build": "vite build"
  }
}
```

### 3. Units mismatch in CPG aggregate data

**In CPG databases, `units_ordered` is denominated in cases, not individual selling units.** This is the single most common data trap in food/bev channel analysis.

```python
# Wrong — produces ~$48/unit when the product is $4
per_unit = net_revenue / units_ordered

# Correct — multiply by case pack quantity
per_unit = net_revenue / (units_ordered * case_pack_qty)
```

Run this sanity check on any new CPG data source before computing per-unit economics:

```python
import sqlite3, pandas as pd
conn = sqlite3.connect("data/snapshot.db")
df = pd.read_sql(
    "SELECT net_revenue, units_ordered, case_pack_qty FROM channel_economics", conn
)

df['raw']       = df['net_revenue'] / df['units_ordered']
df['corrected'] = df['net_revenue'] / (df['units_ordered'] * df['case_pack_qty'])
print("Raw avg:", df['raw'].mean())       # will be implausibly high (cases)
print("Corrected avg:", df['corrected'].mean())  # will be plausible (individual units)
```

If `case_pack_qty` varies by SKU (it usually does), join on SKU-level master data — don't use a global constant.

### 4. CPG deduction waterfall structure

For CPG channel comparison, always compute the full waterfall from gross to contribution. The standard structure:

```
Gross Revenue
  − Trade Spend (slotting fees, MCBs, promotional allowances)
  − Returns & Allowances
  − Distribution Fees (broker commission, 3PL, freight)
= Net Revenue

Net Revenue
  − COGS (ingredients, packaging, manufacturing)
= Contribution Margin
```

Distributor-specific hidden deductions (often omitted from reports):
- Broker commission: typically 5–7% of gross
- Case price reductions / off-invoice deductions
- Distribution margin (what the distributor keeps before passing revenue to the brand)

DTC-specific hidden deductions:
- Platform fees: Shopify + payment processing ~3%
- Fulfillment and shipping: $4–8/order depending on weight
- Returns: higher rate than retail for food

```python
def compute_waterfall(gross, trade_spend, returns, dist_fees, cogs):
    net = gross - trade_spend - returns - dist_fees
    contribution = net - cogs
    return {
        "gross_revenue": gross,
        "trade_spend": trade_spend,
        "returns": returns,
        "distribution_fees": dist_fees,
        "net_revenue": net,
        "cogs": cogs,
        "contribution_margin": contribution,
        "contribution_margin_pct": contribution / net if net > 0 else 0,
    }
```

### 5. Click-to-pin interaction pattern for shared deliverables

Use click-to-pin instead of hover tooltips for any chart in a deliverable shared as a URL.

```typescript
const [pinnedId, setPinnedId] = useState<string | null>(null)

// Build a lookup map so the pinned card can access data by id
const dataById: Record<string, ChannelData> = Object.fromEntries(
  channels.map(ch => [ch.id, ch])
)

// Chart element
<rect
  onClick={() => setPinnedId(prev => prev === channel.id ? null : channel.id)}
  style={{
    opacity: pinnedId === null || pinnedId === channel.id ? 1 : 0.3,
    transition: 'opacity 200ms ease-out',
    cursor: 'pointer',
  }}
/>

// Pinned callout card (Lailara dark card) — guard the lookup: indexing a Record
// returns T | undefined if the id is unexpected
{pinnedId && dataById[pinnedId] && (
  <div style={{ background: '#1a1a1a', color: '#fff', borderRadius: '2px', padding: '20px' }}>
    <DetailContent data={dataById[pinnedId]} />
  </div>
)}
```

```css
@media (prefers-reduced-motion: reduce) {
  .chart-element { transition: none; }
}
```

Non-selected elements dim to 0.3 opacity. The pinned card stays visible until dismissed. This works on touch screens, in screen recordings, and when the viewer wants to screenshot or copy a number.

### 6. Observable Plot wrapper for Economist-style charts

Build a thin `PlotChart` wrapper that handles: responsive sizing via ResizeObserver, SVG `<title>` injection for accessibility, and Economist-style defaults (no X gridlines, horizontal Y gridlines only, no decorative elements).

```typescript
// src/components/PlotChart.tsx
import { useEffect, useRef } from 'react'
import * as Plot from '@observablehq/plot'

interface PlotChartProps {
  data: Record<string, unknown>[]
  spec: (data: Record<string, unknown>[]) => Plot.PlotOptions
  title: string
  className?: string
}

export function PlotChart({ data, spec, title, className }: PlotChartProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    if (!ref.current) return
    const options = spec(data)
    const chart = Plot.plot({
      ...options,
      style: { fontFamily: "'Source Sans 3', sans-serif" },
      x: { ...(options.x ?? {}), grid: false },   // Economist: no X gridlines; ?? {} handles undefined
      y: { ...(options.y ?? {}), grid: true },    // Economist: horizontal Y gridlines only
    })

    // Inject accessible SVG title
    const svgTitle = document.createElementNS('http://www.w3.org/2000/svg', 'title')
    svgTitle.textContent = title
    chart.querySelector('svg')?.prepend(svgTitle)

    ref.current.innerHTML = ''
    ref.current.appendChild(chart)
    return () => chart.remove()
  }, [data, spec, title])

  return <div ref={ref} className={className} />
}
```

Observable Plot vs D3 for data stories: Observable Plot eliminates scale/axis boilerplate and produces SVG output (print-compatible, accessible). For 5–10 charts on static data, roughly 60–80% less chart setup code. Reach for D3 only when you need pixel-precise custom layout.

## Why This Matters

A narrative written to confirm a prior belief — without auditing the data — gives the client wrong capital allocation advice. In CPG, misallocating channel spend by one quarter can cost hundreds of thousands in lost contribution margin. The whole value of the engagement is honest analysis.

The live-DB dependency compounds this: a delivered link that breaks when DB credentials rotate, or returns a loading spinner on mobile, looks unprofessional regardless of how good the analysis is. Baked JSON eliminates both failure modes — the site loads in under a second, works offline, and will look identical in 6 months.

The units mismatch bug is invisible without a sanity check. The relative rankings of channels still look correct (channels that sell more expensive products still win), so the error isn't obvious from the charts alone — only the absolute numbers (the ones clients use to set price floors and model contribution) are wrong.

## When to Apply

- Any analytics deliverable shared as a link (board decks, investor presentations, client reports, data stories)
- CPG, food/bev, or consumer goods channel analysis where the data source is a distributor system (UNFI, KeHE, SPINS) or retailer portal
- Interactive charts in deliverables that will be opened on mobile, shared in Slack, or viewed without a controlled backend
- Any project where the client has a prior belief about what the data will show — audit before writing

Not appropriate for real-time dashboards or ops monitoring where data must be live.

## Examples

**Data-first narrative:**
> Brief assumed: "DTC is the hero channel — show DTC margin outperforming retail."
> Data audit shows: Distributors (UNFI, KeHE) at 90.2% contribution margin, retailers at 81.1%, DTC at 82.6% but at 15× smaller volume.
> Narrative written: "Distributors deserve the next dollar. $1M into distribution earns ~$91K more contribution than $1M into retail expansion."

**SQLite snapshot:**
> Before: React app with `/api/channel-data` endpoint hitting Postgres. Breaks when credentials rotate. Requires VPN. Loading spinner on every visit.
> After: `prebuild` script runs Python against `data/snapshot.db`, outputs JSON to `src/data/`. Vite imports at build time. Deployed to Netlify as a static site. No backend, no auth, loads in under 1 second.

**Units mismatch:**
> Distributor channel shows $48 avg net revenue per "unit." Looks dramatically more valuable than DTC at $6/unit.
> Cause: distributor data in cases (12-pack), DTC in individual units.
> Corrected: distributor $4/unit, DTC $6/unit — DTC is actually higher per individual unit, but at 15× lower volume.

## What Didn't Work (session history)

*(Tagged from session history — useful guardrails for future builds.)*

- **Netlify CLI auth via background PowerShell** (session history): `netlify login` opens a browser OAuth flow and waits; the background shell times out. Workaround: `netlify deploy --allow-anonymous` — deploys without auth; user claims the site in the browser within 60 minutes.
- **Pipeline scripts relying on live Postgres at runtime** (session history): Original design had a `--live` flag that hit Fly.io Postgres from a sibling project. Was `NotImplementedError` from the start and created a cross-project dependency. The correct architecture is `data/snapshot.db` committed to the repo.
- **`scenarios.json` key rename breaking the UI component** (session history): Rewriting extraction scripts with cleaner key names broke the TypeScript component that expected specific keys (`walmart_volume_curve`, `walmart_inflection_volume`). Fix: maintain backward-compatible keys or update component and extraction script in the same commit.
- **Deduction `type` string mismatch between pipeline and UI** (session history): Pipeline output `type: 'retailer'` but the UI checked `type === 'retail'`. An indented `ui_type` block had also slipped outside its `for` loop, emitting deductions for only 1 channel instead of all. Always grep the exact string the UI checks before naming a type field.
- **`git commit -m @'...'@` in PowerShell 5.1 breaks on apostrophes** (session history): A here-string terminates early at the first `'` inside the body. Use the Bash tool for multi-line git commit messages.
- **`defineConfig` from `vite` vs `vitest/config`** (session history): The `test` property in `vite.config.ts` needs vitest's config types. Importing `defineConfig` from `vite` causes a TypeScript error. Always import from `vitest/config` in Vite+Vitest projects.

## Related

- `docs/brainstorms/channel-profitability-requirements.md` — requirements doc for this project
- `docs/plans/2026-05-26-001-feat-channel-profitability-experience-plan.md` — implementation plan with 10 units
- `data/README.md` — documents the snapshot refresh process
