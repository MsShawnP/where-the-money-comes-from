# Where the Money Comes From — Failure Log

What was attempted that didn't work, why it didn't work, and what was
tried next.

Lower bar than DECISIONS.md — capture failures even when they didn't
produce a durable rule. The whole point: future-you (or future-Claude)
shouldn't re-attempt dead ends because the lesson got lost.

---

## Format

### YYYY-MM-DD — [One-line failure description]

**Attempted:** [What was tried]

**Why it didn't work:** [Concrete reason, not "it broke." If the
failure mode was technical, name the specific issue. If the failure
mode was scope or approach, name that.]

**What we tried instead:** [The next attempt, which may also have
failed and may have its own entry below]

**Status:** Resolved / open / abandoned

**Tags:** [keywords for future text-search — e.g., "rendering, pandoc,
quarto" or "scope, scrollytelling, decoration"]

---

## Entries

### 2026-05-26 — Brief's prescriptive tool/format assumptions anchored the design conversation

**Attempted:** Starting /clarify and /ce:brainstorm with the original project brief's specifics in context (scroll story, D3, Scrollama, Excel model as standalone deliverable, Jupyter notebook).

**Why it didn't work:** The brief was thorough and detailed, which caused its tool and format choices to be treated as given rather than as open questions. Several exchanges were spent confirming the user wasn't married to those choices before the real framing questions (delivery mechanism, interaction model, offline requirement) could be asked directly.

**What we tried instead:** Explicitly asked the user to confirm the toolset was open ("not married to those choices") early in /clarify, which unblocked the actual design conversation. Going forward: when a detailed brief exists, open /clarify by flagging its assumptions explicitly rather than working around them.

**Status:** Resolved

**Tags:** brief, anchoring, clarify, scope, toolset, workflow
