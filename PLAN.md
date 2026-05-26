# Where the Money Comes From — Current Work Plan

The current arc of work. Updated when the arc changes, not every
session. For session-by-session state, see HANDOFF.md.

---

## Goal

Build a complete interactive web experience that shows a CFO/CEO of a $25M specialty food brand what each channel actually pays per unit after all deductions — and why their capital allocation is probably wrong — ready to send as a link for real feedback.

## Why this arc, why now

Cinderhaven Data Platform is complete and reconciled, unblocking the full build. This is the first buyer-facing piece that makes the platform's value tangible.

## Business question this arc answers

Which channel deserves the next dollar of growth investment — and is the brand currently getting that answer wrong because they're reading revenue instead of contribution?

## Differentiation from Velocity Decision Tool

The Velocity Tool answers "how are our products performing inside retail?" (SKU × retailer, units/store/week). This piece answers "which channel deserves our growth investment?" (channel P&L, contribution per unit net of all deductions). Execution vs. strategy. No overlap.

## What we know about the piece

- **Format:** Interactive web experience, sent as a link. CFO/CEO plays with it, explores the data. Eventually repurposed as a website case study
- **Story:** Revenue by channel looks one way; contribution per unit looks completely opposite; the gap drives a capital allocation mistake most brands at this stage are making
- **Data:** Cinderhaven Postgres platform (complete). Subscription data does not exist yet — Chapter 5 (Subscription Overlay) is deferred to v2
- **Toolset:** Open — pick what best serves an interactive data story built from Postgres. Not locked to D3/Scrollama/Excel from the original brief
- **Design:** Lailara Design System v2 (see ~/projects/active/CLAUDE.md for full spec)
- **Done:** Releasable for feedback — real enough that a skeptical CFO could receive this link and take it seriously

## Tasks

[To be defined after /ce:brainstorm or /ce:plan — toolset and architecture decisions first]

## Out of scope for this arc

- Chapter 5 (Subscription Overlay) — subscription data does not exist in the platform
- PDF boardroom export — v2
- Excel financial model as a standalone deliverable — evaluate after core story is built
- Jupyter methodology notebook — evaluate after core story is built

## Definition of done for this arc

- [ ] All chapters 1–5 render with real Cinderhaven data
- [ ] Interactive elements work (CFO can explore, not just read)
- [ ] Hosted at a URL that can be sent in an email
- [ ] Lailara design system applied throughout
- [ ] Loads and works on desktop without errors
- [ ] A real CFO/CEO could receive this link and take it seriously

---

## Arc history

When an arc completes, archive its goal, completion date, and outcome
here. Then start a new arc above. Provides continuity without bloating
the active plan.

### [Date completed] — [Goal]
- Outcome: [what shipped or what was decided]
- Tag: [git tag if one was created]

---

## Improvement history

Track when this project was reviewed and improved via /improve.
Each entry records what was found, what was fixed, and when to
check again.

<!-- Entries are added by /improve — don't delete this section -->
