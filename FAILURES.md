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

### 2026-05-26 — Netlify CLI login inaccessible from Claude's PowerShell process

**Attempted:** Running `netlify login` in a background PowerShell process to authenticate the CLI, then using `netlify deploy` with the token.

**Why it didn't work:** Two compounding problems: (1) `netlify login` opens a browser OAuth flow with a 2-minute timeout — Claude's background process timed out before the user could complete it. (2) Even when the user ran `netlify login` in their own terminal, the auth token lives in Windows Credential Manager and is process-scoped — Claude's separate PowerShell process couldn't read it.

**What we tried instead:** `netlify deploy --allow-anonymous` — creates a claimable draft URL without any auth token. User claims the site via the Netlify dashboard within the 24h claim window. Worked cleanly.

**Status:** Resolved

**Tags:** netlify, deployment, windows, credential-manager, auth, powershell, cli

### 2026-05-26 — Snapshot channel data was structurally wrong

**Attempted:** Using `src/data/channels.json` snapshot data (fabricated placeholder values) as the data source for the live site.

**Why it didn't work:** The snapshot had invented channel groupings ("UNFI / Whole Foods" as one merged retailer, "Food Service" as a channel) and fabricated numbers that bore no relationship to the real Cinderhaven database. UNFI and KeHE are distributors in the real DB, not retailers. Whole Foods is a separate direct retailer. Food Service doesn't exist. DTC has zero order history.

**What we tried instead:** Queried the real Cinderhaven SQLite DB at `retailer-deduction-recovery/data/cinderhaven_deductions.db`. Found correct channel structure and computed real P&L using `units_ordered × case_pack_qty` for individual units and `cogs_per_unit` per individual unit. Pipeline update and JSON regeneration is next session's first task.

**Status:** Open — pipeline not yet updated, site still serving placeholder data

**Tags:** data, snapshot, pipeline, channels, units, cogs, math, accuracy

### 2026-05-26 — Unit mismatch in P&L computation (cases vs individual units)

**Attempted:** Computing contribution per unit using `SUM(units_ordered)` directly from `order_lines` as the unit count.

**Why it didn't work:** `order_lines.units_ordered` is in **cases**, not individual units. `sku_costs.cogs_per_unit` is per individual unit. Dividing revenue by case count and multiplying COGS by case count produced absurd margins (78% for Walmart). The correct formula requires joining `product_master` to get `case_pack_qty` and computing `SUM(units_ordered × case_pack_qty)` for individual units.

**What we tried instead:** Corrected the formula: `individual_units = SUM(ol.units_ordered * pm.case_pack_qty)`, `cogs = SUM(ol.units_ordered * pm.case_pack_qty * sc.cogs_per_unit)`. Produces realistic margins (31–43% by channel).

**Status:** Resolved in queries; pipeline script not yet updated to reflect this

**Tags:** math, units, cases, case-pack, cogs, pipeline, sql, channels

### 2026-05-26 — PowerShell here-string breaks git commit messages containing apostrophes

**Attempted:** `git commit -m @'...'@` with a multi-line message body that contained apostrophes (e.g., "doesn't", "it's").

**Why it didn't work:** PowerShell 5.1 single-quoted here-strings terminate at the first bare `'` inside the body when passed to a native executable. Git receives a truncated message and treats the remainder as file path arguments, producing `pathspec did not match` errors.

**What we tried instead:** Used the `Bash` tool for all git commits with multi-line or apostrophe-containing messages. Works cleanly every time.

**Status:** Resolved — use Bash for git commits going forward.

**Tags:** git, powershell, commit, here-string, bash, workflow

### 2026-05-26 — Python encoding failure on Windows when extracting session JSONL files

**Attempted:** Running `ce-sessions` extraction scripts (`extract-skeleton.py`, `extract-metadata.py`) via the Git Bash `python3` command.

**Why it didn't work:** Two compounding issues: (1) `python3` is not on the PATH in the Git Bash environment on this Windows machine — the executable is at `C:/Users/mssha/AppData/Local/Microsoft/WindowsApps/python`. (2) Even with the correct path, the Windows default locale is cp1252, which can't encode certain Unicode characters in session JSONL files — fails with `UnicodeEncodeError: 'charmap' codec can't encode character`.

**What we tried instead:** Used full path `/c/Users/mssha/AppData/Local/Microsoft/WindowsApps/python` and prepended `PYTHONUTF8=1` to force UTF-8 output encoding. Both fixes are required together.

**Status:** Resolved — always use `PYTHONUTF8=1 /c/Users/.../python` for ce-sessions scripts on this machine.

**Tags:** python, windows, encoding, unicode, cp1252, ce-sessions, bash, path
