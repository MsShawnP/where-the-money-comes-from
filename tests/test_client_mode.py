"""Client-mode tests for where-the-money-comes-from.

Adversarial fixtures per checklist §6: clean run, DTC reported pre-fee (no
fee-inclusive claim), missing required column (blocked), duplicate channel, empty
file, and the --final watermark. Fictional-placeholder identity.

Skipped if lailara_engagement isn't installed.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

pytest.importorskip("lailara_engagement")

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
import client_mode  # noqa: E402

from lailara_engagement.errors import ReadError  # noqa: E402

_CONFIG = """
client: {name: Meridian Farms}
engagement: {id: MER-2026-08}
as_of_date: "2026-01-31"
demo: true
basis: {window_label: CY2025}
columns:
  channel: channel
  channel_type: channel_type
  revenue: revenue
  contribution_dollars: contribution_dollars
  units_shipped: units_shipped
"""

_CLEAN = (
    "channel,channel_type,revenue,contribution_dollars,units_shipped\n"
    "Harborline,retailer,1000000,500000,100000\n"      # $5.00/unit
    "Shopify DTC,dtc,200000,90000,10000\n"             # $9.00/unit pre-fee
)


def _cfg(tmp_path):
    p = tmp_path / "engagement.yml"
    p.write_text(_CONFIG, encoding="utf-8")
    return str(p)


def _write(tmp_path, name, text):
    p = tmp_path / name
    p.write_text(text, encoding="utf-8")
    return str(p)


def test_clean_run(tmp_path):
    src = _write(tmp_path, "c.csv", _CLEAN)
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    assert result["status"] == "ok"
    assert result["channels"] == 2
    s = json.load(open(result["summary_json"], encoding="utf-8"))
    by = {c["channel"]: c for c in s["channels"]}
    assert by["Harborline"]["contribution_per_unit"] == 5.0
    assert by["Shopify DTC"]["contribution_per_unit"] == 9.0
    html = open(result["report"], encoding="utf-8").read()
    assert "Meridian Farms" in html and "SHA-256" in html and "DRAFT" in html


def test_dtc_reported_pre_fee_no_fee_inclusive_claim(tmp_path):
    src = _write(tmp_path, "c.csv", _CLEAN)
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    s = json.load(open(result["summary_json"], encoding="utf-8"))
    dtc = next(c for c in s["channels"] if c["channel_type"] == "dtc")
    assert "pre-fee" in dtc["basis"]
    assert "PRE-FEE" in s["dtc_note"]
    html = open(result["report"], encoding="utf-8").read()
    assert "pre-fee" in html.lower()


def test_missing_required_column_blocks(tmp_path):
    src = _write(tmp_path, "bad.csv", "channel,channel_type,revenue\nA,retailer,100\n")
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    assert result["status"] == "blocked"
    rr = open(result["readiness_report"], encoding="utf-8").read().lower()
    assert "contribution_dollars" in rr or "units_shipped" in rr


def test_duplicate_channel_blocks(tmp_path):
    src = _write(tmp_path, "dup.csv",
                 "channel,channel_type,revenue,contribution_dollars,units_shipped\n"
                 "A,retailer,100,50,10\nA,retailer,200,80,20\n")
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))
    assert result["status"] == "blocked"
    assert "duplicat" in open(result["readiness_report"], encoding="utf-8").read().lower()


def test_empty_file_raises(tmp_path):
    src = _write(tmp_path, "e.csv", "")
    with pytest.raises(ReadError):
        client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"))


def test_final_drops_watermark(tmp_path):
    src = _write(tmp_path, "c.csv", _CLEAN)
    result = client_mode.run(_cfg(tmp_path), src, str(tmp_path / "out"), final=True)
    assert "ll-draft" not in open(result["report"], encoding="utf-8").read()
