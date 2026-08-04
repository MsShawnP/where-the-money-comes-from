"""Client-mode CLI for where-the-money-comes-from.

Render a client-workshop version of the channel unit economics from the client's
own numbers — validated, never committed, never deployed. The demo React app is
untouched.

DTC is reported **pre-fee** (contribution before processing fees and fulfillment);
no fee-inclusive claim is made, because a canonical after-fees basis is a pending
Shawn decision. Never invent it.

Usage:
    python client_mode.py --config engagement.yml --input client-data/channels.csv \
        --out client-output [--final]
"""

from __future__ import annotations

import argparse
import html
import json
from pathlib import Path

from lailara_engagement import (
    ColumnSpec,
    PreflightSpec,
    build_provenance,
    load_config,
    read_table,
    run_preflight,
    validation_status_label,
    write_report,
)
from lailara_engagement import palette as P
from lailara_engagement.provenance import Provenance

TOOL = "where-the-money-comes-from"
TOOL_VERSION = "1.0"


def _spec() -> PreflightSpec:
    return PreflightSpec(
        tool=TOOL, version=TOOL_VERSION,
        columns=[
            ColumnSpec(name="channel", dtype="string", required=True, unique=True,
                       description="channel/customer name", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="channel_type", dtype="string", required=True,
                       description="retailer / distributor / dtc", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="revenue", dtype="number", required=True, not_negative=True,
                       description="channel revenue", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="contribution_dollars", dtype="number", required=True,
                       description="contribution dollars (may be negative)", spec_ref="INPUT-SPEC §1"),
            ColumnSpec(name="units_shipped", dtype="number", required=True, not_negative=True,
                       description="units shipped", spec_ref="INPUT-SPEC §1"),
        ],
    )


def _num(v) -> float:
    try:
        return float(str(v).strip())
    except (ValueError, TypeError):
        return 0.0


def run(config_path: str, input_path: str, out_dir: str, *, final: bool = False) -> dict:
    config = load_config(config_path)
    read = read_table(input_path)
    report = run_preflight(read, _spec(), config)

    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    provenance = build_provenance(
        tool=TOOL, tool_version=TOOL_VERSION, inputs=[read], config=config,
        validation_status=validation_status_label(report.status, report.n_warnings))
    if not report.passed:
        paths = write_report(report, config, str(out), provenance=provenance,
                             draft=not final, basename="data-readiness-report",
                             title="Channel Economics Data Readiness Report")
        return {"status": "blocked", "readiness_report": paths["html"]}

    m = report.column_mapping
    frame = read.frame
    rows = []
    has_dtc = False
    for i in range(len(frame)):
        ch = str(frame[m["channel"]].iloc[i]).strip()
        ctype = str(frame[m["channel_type"]].iloc[i]).strip()
        rev = _num(frame[m["revenue"]].iloc[i])
        contrib = _num(frame[m["contribution_dollars"]].iloc[i])
        units = _num(frame[m["units_shipped"]].iloc[i])
        is_dtc = ctype.lower() == "dtc"
        has_dtc = has_dtc or is_dtc
        rows.append({
            "channel": ch, "channel_type": ctype,
            "revenue": round(rev, 2), "contribution_dollars": round(contrib, 2),
            "units_shipped": round(units, 2),
            "contribution_per_unit": round(contrib / units, 2) if units else None,
            "contribution_margin_pct": round(contrib / rev, 4) if rev else None,
            "basis": "pre-fee (before processing fees & fulfillment)" if is_dtc else "after deductions, chargebacks, fees",
        })

    rows.sort(key=lambda r: (r["contribution_per_unit"] is None, -(r["contribution_per_unit"] or 0)))
    summary = {
        "window": {"label": config.basis.get("window_label", "")},
        "channels": rows,
        "dtc_note": ("DTC contribution is reported PRE-FEE (before processing fees and "
                     "fulfillment). No fee-inclusive DTC figure is claimed — that needs a "
                     "canonical after-fees basis not provided.") if has_dtc else None,
    }
    json_dir = out / "json"; json_dir.mkdir(parents=True, exist_ok=True)
    (json_dir / "summary.json").write_text(json.dumps(summary, indent=2), encoding="utf-8")
    report_path = out / "channel-economics-summary.html"
    report_path.write_text(_summary_html(config, summary, provenance, draft=not final), encoding="utf-8")
    return {"status": "ok", "channels": len(rows), "has_dtc": has_dtc,
            "report": str(report_path), "summary_json": str(json_dir / "summary.json"),
            "n_warnings": report.n_warnings}


def _summary_html(config, s, provenance: Provenance, *, draft: bool) -> str:
    esc = html.escape
    wl = s["window"].get("label") or ""

    def _row(r):
        cpu = "—" if r["contribution_per_unit"] is None else f"${r['contribution_per_unit']:,.2f}"
        mg = "—" if r["contribution_margin_pct"] is None else f"{r['contribution_margin_pct']*100:.1f}%"
        return (f"<tr><td>{esc(r['channel'])}</td><td>{esc(r['channel_type'])}</td>"
                f"<td class=num>${r['revenue']:,.0f}</td><td class=num>{cpu}</td>"
                f"<td class=num>{mg}</td><td>{esc(r['basis'])}</td></tr>")

    rows = "".join(_row(r) for r in s["channels"])
    dtc_note = f"<p class=ll-note>{esc(s['dtc_note'])}</p>" if s.get("dtc_note") else ""
    return f"""<!doctype html><html lang=en><head><meta charset=utf-8>
<meta name=viewport content="width=device-width, initial-scale=1">
<title>Channel Economics — {esc(config.client_name)}</title><style>{_css(draft)}</style></head>
<body class="{' ll-draft' if draft else ''}"><main class=ll-page>
<header class=ll-header>
  <div class=ll-eyebrow>Lailara LLC · Where the Money Comes From</div>
  <h1 class=ll-title>Contribution per Unit by Channel</h1>
  <div class=ll-client>
    <div><span class=ll-k>Client</span> {esc(config.client_name)}</div>
    <div><span class=ll-k>Engagement</span> {esc(config.engagement_id)}</div>
    <div><span class=ll-k>As of</span> {esc(config.as_of_date.isoformat())}</div>
    <div><span class=ll-k>Window</span> {esc(wl) or '—'}</div>
  </div>
</header>
<section class=ll-banner>
  <div class=ll-score>{len(s['channels'])} channels</div>
  <div>ranked by contribution per unit — where each dollar actually earns</div>
</section>
<section class=ll-section>
  <h2 class=ll-h2>Unit economics</h2>
  <table class=ll-table><thead><tr><th>Channel</th><th>Type</th><th>Revenue</th>
  <th>Contribution / unit</th><th>Margin</th><th>Basis</th></tr></thead><tbody>{rows}</tbody></table>
  {dtc_note}
</section>
{provenance.to_html()}
</main></body></html>"""


def _css(draft: bool) -> str:
    draft_css = (
        ".ll-draft::before{content:'DRAFT';position:fixed;top:50%;left:50%;"
        "transform:translate(-50%,-50%) rotate(-32deg);font-family:var(--s);"
        "font-size:22vw;font-weight:700;color:rgba(204,16,10,.06);z-index:0;"
        "pointer-events:none;white-space:nowrap}" if draft else ""
    )
    return f"""
:root{{--s:{P.LL_SERIF};--f:{P.LL_SANS}}}*{{box-sizing:border-box}}
body{{margin:0;background:{P.LL_CANVAS};color:{P.LL_TEXT};font-family:var(--f);line-height:1.6}}
.ll-page{{position:relative;z-index:1;max-width:{P.LL_MAX_WIDTH};margin:0 auto;padding:48px 24px}}
.ll-header{{border-bottom:1px solid {P.LL_GRIDLINE};padding-bottom:24px;margin-bottom:24px}}
.ll-eyebrow{{font-size:12px;letter-spacing:.04em;text-transform:uppercase;color:{P.LL_RED};font-weight:600}}
.ll-title{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:34px;margin:8px 0 16px}}
.ll-client{{display:grid;grid-template-columns:repeat(auto-fit,minmax(160px,1fr));gap:8px 24px;font-size:14px}}
.ll-k{{display:block;color:{P.LL_TEXT_SEC};font-size:11px;text-transform:uppercase;letter-spacing:.04em}}
.ll-banner{{border-radius:2px;padding:16px 20px;margin-bottom:32px;background:{P.LL_HK_SURFACE};color:{P.LL_HK_DARK}}}
.ll-score{{font-family:var(--s);font-weight:700;font-size:22px}}
.ll-section{{margin:0 0 32px}}
.ll-h2{{font-family:var(--s);font-weight:700;color:{P.LL_INK};font-size:22px;
margin:0 0 12px;padding-bottom:6px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.ll-note{{font-size:13px;color:{P.LL_TEXT_SEC};margin-top:8px}}
.ll-table{{width:100%;border-collapse:collapse;font-size:14px}}
.ll-table th{{text-align:left;background:{P.LL_CHICAGO};color:#fff;padding:8px 12px}}
.ll-table td{{padding:8px 12px;border-bottom:1px solid {P.LL_GRIDLINE}}}
.num{{text-align:right;font-variant-numeric:tabular-nums}}
.ll-provenance{{margin-top:40px;background:{P.LL_CARD_BG};color:{P.LL_CARD_TEXT};
padding:20px 24px;border-radius:2px;font-size:13px}}
.ll-prov-title{{font-family:var(--s);font-weight:700;font-size:16px;margin-bottom:8px}}
.ll-provenance div{{margin-bottom:4px;color:{P.LL_CARD_SUBTITLE}}}
.ll-provenance strong{{color:{P.LL_CARD_TEXT}}}
.ll-prov-inputs{{width:100%;border-collapse:collapse;margin-top:8px}}
.ll-prov-inputs th{{text-align:left;border-bottom:1px solid rgba(255,255,255,.12);padding:4px 8px;color:{P.LL_CARD_MUTED}}}
.ll-prov-inputs td{{padding:4px 8px;border-bottom:1px solid rgba(255,255,255,.08);color:{P.LL_CARD_SUBTITLE}}}
.ll-prov-brand{{margin-top:12px;font-family:var(--s);color:{P.LL_CARD_MUTED}}}
{draft_css}
@media print{{body{{background:#fff}}}}
"""


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(prog="where-the-money-comes-from client mode")
    ap.add_argument("--config", required=True)
    ap.add_argument("--input", required=True)
    ap.add_argument("--out", default="client-output")
    ap.add_argument("--final", action="store_true")
    args = ap.parse_args(argv)
    result = run(args.config, args.input, args.out, final=args.final)
    if result["status"] == "blocked":
        print(f"BLOCKED — data not ready. See {result['readiness_report']}")
        return 3
    print(f"scored {result['channels']} channels" + (" (DTC pre-fee)" if result["has_dtc"] else ""))
    print(f"report -> {result['report']}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
