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

[Decisions about data sources, schemas, transformations]

---

## Visualization

[Chart conventions, palette decisions, interactivity choices]

---

## Output Formats

### 2026-05-26 — No CTA; this piece is a conversation starter, not a funnel
- **Why:** The piece is sent directly by Shawn to a specific prospect before or after a conversation. The CFO is already in a relationship context. A CTA adds friction and changes the tone from "here's something interesting" to "here's a sales page." The piece does the priming; the conversation closes the loop.
- **Scope:** Global — product framing and page design
- **Do not:** Do not add email gates, contact forms, download buttons, or "book a call" links. Do not design the ending as a conversion moment.

---

## Writing & Voice

[Voice, style, terminology decisions specific to this project]

---

## Reversed / Superseded

When a decision is overturned:
1. Strike through the original entry above (don't delete)
2. Add a new entry below with the replacement decision
3. Note the link in both directions

This preserves the history of why something is the way it is.
