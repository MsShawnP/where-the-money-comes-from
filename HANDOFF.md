# Where the Money Comes From — Handoff Log

Session-by-session state. Updated by /log mid-session and /wrap at
session end.

For durable choices, see DECISIONS.md.
For the current work arc, see PLAN.md.
For things that didn't work, see FAILURES.md.

---

## 2026-05-26 — Project initialized

**Started from:** New project setup.

**Did:** Created repo, set up CLAUDE.md/DECISIONS.md/HANDOFF.md/PLAN.md/
FAILURES.md, configured slash commands, ran 95% confidence prompt
in chat.

**State:** Foundation in place. PLAN.md arc defined. Ready to begin
work.

**Next:** Fill in CLAUDE.md bracketed sections, then define first arc in PLAN.md.

---

## 2026-05-26 13:41

**What changed:** Completed /clarify + /ce:brainstorm — requirements doc written, stack and architecture decided

**Why:** Needed to resolve open questions (format, interaction model, data pipeline, toolset) before any code is written. All decisions now documented.

**State:** Requirements doc at `docs/brainstorms/channel-profitability-requirements.md`. PLAN.md updated with full arc definition. No code yet — blank slate.

**Next:** Run `/ce:plan` to produce the implementation plan — Python pipeline queries, React component structure, Observable Plot chart specs, build/deploy setup.

---

## 2026-05-26 13:45

**Started from:** New project, workflow files only, no code, no decisions.

**Did:** Ran /clarify + /ce:brainstorm. Reframed from brief's scroll-story assumptions to methodology+challenge interactive piece. Decided stack (React+Vite+TS+Observable Plot), data architecture (Python→JSON baked into Vite build, offline-capable, instant), framing (no CTA, conversation starter), and confirmed Chapter 5 deferred to v2. Wrote full requirements doc.

**State:** No code. Requirements documented. Stack and architecture decided. PLAN.md arc defined. Ready to plan.

**Next:** Run `/ce:plan` working from `docs/brainstorms/channel-profitability-requirements.md`. Verify five open questions against Cinderhaven Postgres before pipeline build (especially: does `dim_channels` exist? Does deduction taxonomy cover slotting/MCB/swell/OTIF for Ch. 3 waterfalls?).

---

## 2026-05-26 ~17:00

**Started from:** U10 (polish/accessibility/deploy) was the last implementation unit. All 5 chapters existed with snapshot/placeholder data.

**Did:** Completed U10 — sr-only DataTables on all chapters, `.sr-only` + `@media print` styles, SVG `<title>` injection on PlotChart, `netlify.toml`. Deployed to Netlify via anonymous deploy; user claimed site and renamed subdomain to `where-the-money-comes-from`. Fixed accidentally-staged `.claude/worktrees/` files. Queried real Cinderhaven database — discovered snapshot data is completely wrong (UNFI/KeHE are distributors not retailers, Whole Foods is a separate channel, Food Service doesn't exist, DTC has zero orders). Found and documented unit mismatch bug (cases vs individual units via `case_pack_qty`). User requested distributor hidden tax in Chapter 3.

**State:** Site live at https://where-the-money-comes-from.netlify.app with placeholder data. `channels.json` and `deductions.json` still have snapshot numbers. Python pipeline not yet updated to real DB. Chapter 3 waterfall excludes distributors.

**Next:** 
1. Update `scripts/01_extract_channel_data.py` to query `cinderhaven_deductions.db` with correct formula (`units_ordered × case_pack_qty` for individual units)
2. Regenerate `src/data/channels.json` with real 7-channel data
3. Update `src/data/deductions.json` — add UNFI/KeHE as `type: 'distributor'` with real deduction waterfall
4. Update `Ch3HiddenTax.tsx` — extend waterfall gate to include distributors (user request: "hidden tax for distribution as well")
5. Rebuild and redeploy to Netlify

---
