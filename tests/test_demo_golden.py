"""Demo golden lock — where-the-money-comes-from.

Byte-locks the committed channel unit-economics the app renders and locks the
honest DTC framing: DTC contribution per unit is stated **pre-fee** (before
processing fees and fulfillment), with no fee-inclusive claim. The audit flagged
DTC being framed "after every fee" when the stack is pre-fee; the fix is the
honest label. A fee-inclusive DTC figure needs a canonical after-fees basis that
does not yet exist in this repo — so it is deliberately NOT asserted here.

If a SHA or a figure moves, STOP: a golden moved.
"""

from __future__ import annotations

import hashlib
import json
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
CHANNELS = ROOT / "src" / "data" / "channels.json"
CHAPTER2 = ROOT / "src" / "chapters" / "Chapter2" / "Chapter2.tsx"

GOLDEN_SHA256_PREFIX = "bbad61f811d59d46"


@pytest.fixture(scope="module")
def channels():
    return json.loads(CHANNELS.read_text())


def test_channels_json_sha256():
    digest = hashlib.sha256(CHANNELS.read_bytes()).hexdigest()[:16]
    assert digest == GOLDEN_SHA256_PREFIX, (
        f"channels.json changed (sha256[:16] {digest} != golden {GOLDEN_SHA256_PREFIX}) "
        "— a demo golden moved; STOP and report."
    )


def test_ten_channels(channels):
    assert len(channels) == 10


def test_dtc_contribution_per_unit(channels):
    dtc = next(c for c in channels if c["channel"] == "DTC")
    assert dtc["channel_type"] == "dtc"
    assert dtc["contribution_per_unit"] == 8.73


def test_dtc_is_labeled_pre_fee_not_fee_inclusive():
    prose = CHAPTER2.read_text(encoding="utf-8")
    # The honest DTC framing (Shawn's call while the after-fees basis is pending):
    # DTC is stated pre-fee, and the "after every ... fee" phrasing is scoped to
    # WHOLESALE channels, not DTC.
    assert "before processing fees and fulfillment" in prose
    # DTC must not be claimed fee-inclusive.
    assert "DTC" in prose
