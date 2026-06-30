"""Cinderhaven canonical data regression tests for where-the-money-comes-from.

Verifies the baked JSON and SQLite artifacts match the Cinderhaven data contract.

Canonical contract (target):
    - 50 SKUs, 5 product lines, 6 retailers
    - Retailers: Walmart, Costco, Whole Foods, Sprouts, Kroger, Regional Group

This repo's scope:
    - 10 channels: 6 retailers + 3 distributors + DTC.
    - Channel-level revenue/contribution view.
    - Overall blended contribution ~50 cents per dollar (CPG economics; regen 2026-06-30).
"""

from __future__ import annotations

import json
import sqlite3
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "src" / "data"
SNAPSHOT_DB = ROOT / "data" / "snapshot.db"


@pytest.fixture(scope="module")
def channels():
    return json.loads((DATA_DIR / "channels.json").read_text())


@pytest.fixture(scope="module")
def deductions():
    return json.loads((DATA_DIR / "deductions.json").read_text())


@pytest.fixture(scope="module")
def snapshot_db():
    assert SNAPSHOT_DB.exists(), f"Snapshot DB not found: {SNAPSHOT_DB}"
    conn = sqlite3.connect(f"file:{SNAPSHOT_DB}?mode=ro", uri=True)
    yield conn
    conn.close()


class TestCinderhavenCanonicalRegression:
    """Guard-rails for the baked Cinderhaven channel dataset."""

    # ------------------------------------------------------------------
    # Channel counts
    # ------------------------------------------------------------------

    def test_channel_count(self, channels):
        """10 channels total."""
        assert len(channels) == 10, f"Expected 10 channels, got {len(channels)}"

    def test_retailer_count(self, channels):
        retailers = [c for c in channels if c["channel_type"] == "retailer"]
        assert len(retailers) == 6, f"Expected 6 retailers, got {len(retailers)}"

    def test_distributor_count(self, channels):
        distributors = [c for c in channels if c["channel_type"] == "distributor"]
        assert len(distributors) == 3, f"Expected 3 distributors, got {len(distributors)}"

    # ------------------------------------------------------------------
    # Canonical 6 retailers present
    # ------------------------------------------------------------------

    def test_canonical_retailers_present(self, channels):
        names = {c["channel"] for c in channels}
        for retailer in ("Walmart", "Costco", "Whole Foods", "Sprouts", "Kroger", "Regional Group"):
            assert retailer in names, f"Canonical retailer {retailer!r} missing"

    # ------------------------------------------------------------------
    # Revenue and contribution sanity
    # ------------------------------------------------------------------

    def test_total_revenue_range(self, channels):
        """Total gross revenue ~$76.8M."""
        total = sum(c["revenue"] for c in channels)
        assert 70_000_000 < total < 85_000_000, (
            f"Total revenue ${total:,.0f} outside expected range"
        )

    def test_blended_contribution_margin(self, channels):
        """Blended contribution ~50 cents per dollar (45%-55% range; CPG economics, regen 2026-06-30)."""
        total_rev = sum(c["revenue"] for c in channels)
        total_contrib = sum(c["contribution_dollars"] for c in channels)
        margin = total_contrib / total_rev
        assert 0.45 < margin < 0.55, (
            f"Blended contribution margin {margin:.4f} outside 45%-55% range"
        )

    # ------------------------------------------------------------------
    # Deductions waterfall completeness
    # ------------------------------------------------------------------

    def test_deductions_cover_all_channels(self, deductions, channels):
        """Deductions waterfall should have entries for all channels."""
        channel_names = {c["channel"] for c in channels}
        deduction_keys = set(deductions.keys())
        missing = channel_names - deduction_keys
        assert not missing, f"Channels missing from deductions waterfall: {missing}"

    # ------------------------------------------------------------------
    # Snapshot DB tables
    # ------------------------------------------------------------------

    def test_snapshot_db_exists(self):
        assert SNAPSHOT_DB.exists(), "snapshot.db missing"

    def test_snapshot_db_channel_count(self, snapshot_db):
        (count,) = snapshot_db.execute("SELECT COUNT(*) FROM channels").fetchone()
        assert count == 10, f"Expected 10 channels in snapshot.db, got {count}"

    # ------------------------------------------------------------------
    # Data file existence
    # ------------------------------------------------------------------

    def test_data_files_exist(self):
        for name in ("channels.json", "deductions.json", "scenarios.json"):
            path = DATA_DIR / name
            assert path.exists(), f"Data file missing: {path}"
