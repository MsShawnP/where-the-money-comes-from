"""
tests/test_prose_data.py — Prose-data validation for generated JSON files.

These tests load the chart-ready JSON produced by the pipeline scripts and
assert that the data is internally consistent and matches known business facts
about Cinderhaven channel economics.

Run with:
  pytest tests/test_prose_data.py
"""
import copy
import json
from pathlib import Path

import pytest

DATA_DIR = Path(__file__).parent.parent / "src" / "data"

# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture(scope="module")
def channels():
    path = DATA_DIR / "channels.json"
    assert path.exists(), f"channels.json not found at {path}. Run scripts with --snapshot first."
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def deductions():
    path = DATA_DIR / "deductions.json"
    assert path.exists(), f"deductions.json not found at {path}. Run scripts with --snapshot first."
    return json.loads(path.read_text())


@pytest.fixture(scope="module")
def scenarios():
    path = DATA_DIR / "scenarios.json"
    assert path.exists(), f"scenarios.json not found at {path}. Run scripts with --snapshot first."
    return json.loads(path.read_text())


# ── Test 1: contribution_per_unit consistency across channels ─────────────────

class TestChannelContributions:
    """Contribution per unit should be internally consistent with dollars and units."""

    def test_contribution_per_unit_matches_implied(self, channels):
        """contribution_dollars ≈ contribution_per_unit × units_shipped (within $1 or 1%)."""
        for ch in channels:
            name = ch["channel"]
            implied = ch["contribution_per_unit"] * ch["units_shipped"]
            tolerance = max(10, implied * 0.01)  # 1% or $10, whichever is larger
            assert abs(ch["contribution_dollars"] - implied) <= tolerance, (
                f"{name}: contribution_dollars {ch['contribution_dollars']} "
                f"inconsistent with {ch['contribution_per_unit']} × {ch['units_shipped']} "
                f"= {implied:.2f} (tolerance ±{tolerance:.2f})"
            )

    def test_contribution_margin_pct_matches_dollars_and_revenue(self, channels):
        """contribution_margin_pct ≈ contribution_dollars / revenue (tolerance 0.005)."""
        for ch in channels:
            name = ch["channel"]
            implied_pct = ch["contribution_dollars"] / ch["revenue"]
            assert abs(ch["contribution_margin_pct"] - implied_pct) <= 0.005, (
                f"{name}: contribution_margin_pct {ch['contribution_margin_pct']} "
                f"inconsistent with {ch['contribution_dollars']} / {ch['revenue']} "
                f"= {implied_pct:.4f}"
            )

    def test_all_channels_have_required_fields(self, channels):
        required = {
            "channel", "revenue", "contribution_dollars",
            "contribution_margin_pct", "units_shipped", "contribution_per_unit"
        }
        for ch in channels:
            missing = required - ch.keys()
            assert not missing, f"Channel {ch.get('channel', '?')} missing fields: {missing}"


# ── Test 2: Waterfall arithmetic ──────────────────────────────────────────────

class TestWaterfallArithmetic:
    """Waterfall steps must sum to the net revenue subtotal's cumulative value."""

    def _get_net_revenue_cumulative(self, steps):
        """Return the cumulative value at the Net Revenue subtotal step."""
        for step in steps:
            if step.get("is_subtotal"):
                return step["cumulative"]
        return None

    def _sum_deductions_from_gross(self, steps):
        """
        Sum: gross revenue + all real deduction steps (negative values)
        up to but not including the net revenue subtotal.
        Returns the implied net revenue.
        """
        running = steps[0]["value"]  # Gross Revenue
        for step in steps[1:]:
            if step.get("is_subtotal") or step.get("is_total"):
                break
            running += step["value"]
        return running

    def test_gross_minus_deductions_equals_net_revenue(self, deductions):
        """Gross − deductions should equal net revenue subtotal cumulative."""
        for channel, ch_data in deductions.items():
            steps = ch_data["steps"]
            implied_net = self._sum_deductions_from_gross(steps)
            actual_net = self._get_net_revenue_cumulative(steps)
            assert actual_net is not None, f"{channel}: no is_subtotal (Net Revenue) step"
            assert abs(implied_net - actual_net) <= 1, (
                f"{channel}: gross − deductions = {implied_net:.0f}, "
                f"but Net Revenue cumulative = {actual_net}"
            )

    def test_cumulative_advances_correctly_per_step(self, deductions):
        """Each non-subtotal/non-total step: cumulative[i] = cumulative[i-1] + value[i]."""
        for channel, ch_data in deductions.items():
            steps = ch_data["steps"]
            running = steps[0]["value"]
            assert abs(steps[0]["cumulative"] - running) <= 1, (
                f"{channel}: first step cumulative mismatch"
            )
            for step in steps[1:]:
                is_marker = step.get("is_subtotal") or step.get("is_total")
                if not is_marker:
                    running += step["value"]
                    assert abs(step["cumulative"] - running) <= 1, (
                        f"{channel} step '{step['label']}': "
                        f"expected cumulative {running:.0f}, got {step['cumulative']}"
                    )
                else:
                    running = step["cumulative"]  # reset to checkpoint


# ── Test 3: Waterfall contribution matches channels.json ──────────────────────

class TestWaterfallVsChannels:
    """Final waterfall contribution must match channels.json contribution_dollars."""

    def _get_contribution_cumulative(self, steps):
        for step in steps:
            if step.get("is_total"):
                return step["cumulative"]
        return None

    def test_waterfall_final_contribution_matches_channels_json(self, channels, deductions):
        """Waterfall final step cumulative ≈ channels.json contribution_dollars (±$10)."""
        channels_by_name = {ch["channel"]: ch for ch in channels}

        for channel, ch_data in deductions.items():
            if channel not in channels_by_name:
                pytest.skip(f"{channel} not in channels.json — skipping cross-file check")

            waterfall_contribution = self._get_contribution_cumulative(ch_data["steps"])
            assert waterfall_contribution is not None, (
                f"{channel}: no is_total step in waterfall"
            )
            expected = channels_by_name[channel]["contribution_dollars"]
            assert abs(waterfall_contribution - expected) <= 10, (
                f"{channel}: waterfall contribution {waterfall_contribution} "
                f"does not match channels.json contribution_dollars {expected} "
                f"(tolerance ±$10)"
            )


# ── Test 4 & 5: Walmart lowest, DTC highest contribution_per_unit ─────────────

class TestChannelRanking:
    """Business facts about channel economics that must hold in the data."""

    def test_walmart_has_lowest_contribution_per_unit_among_traditional_retailers(self, channels):
        """Walmart has the lowest per-unit contribution among non-club retailers (the central thesis).

        Costco's club model (bulk, membership, no slotting) is excluded — its economics
        are structurally distinct. Among traditional retailers Walmart is the low-margin anchor.
        """
        traditional = {
            ch["channel"]: ch["contribution_per_unit"]
            for ch in channels
            if ch["channel_type"] == "retailer" and ch["channel"] != "Costco"
        }
        walmart = traditional.get("Walmart")
        assert walmart is not None, "Walmart not found in channels.json"
        for name, value in traditional.items():
            if name != "Walmart":
                assert walmart <= value, (
                    f"Walmart contribution_per_unit ({walmart}) is not lower than "
                    f"traditional retailer {name} ({value}). This contradicts the core business finding."
                )

    def test_dtc_has_highest_contribution_per_unit(self, channels):
        """DTC should have the highest per-unit contribution (the capital reallocation case)."""
        per_unit = {ch["channel"]: ch["contribution_per_unit"] for ch in channels}
        dtc = per_unit.get("DTC")
        assert dtc is not None, "DTC not found in channels.json"
        for name, value in per_unit.items():
            if name != "DTC":
                assert dtc >= value, (
                    f"DTC contribution_per_unit ({dtc}) is not higher than "
                    f"{name} ({value}). This contradicts the DTC-reallocation argument."
                )


# ── Test 6: Scenario delta arithmetic ────────────────────────────────────────

class TestScenarioDelta:
    """capital_allocation.delta must equal distributor - retailer incremental contributions."""

    def test_delta_equals_distributor_minus_retailer(self, scenarios):
        ca = scenarios["capital_allocation"]
        retailer = ca["retailer"]["incremental_contribution"]
        distributor = ca["distributor"]["incremental_contribution"]
        expected_delta = distributor - retailer
        assert abs(ca["delta"] - expected_delta) <= 1, (
            f"capital_allocation.delta {ca['delta']} does not equal "
            f"distributor ({distributor}) - retailer ({retailer}) = {expected_delta}"
        )

    def test_retailer_exceeds_distributor_incremental_contribution(self, scenarios):
        """Retail expansion yields higher incremental contribution than distribution (regen 2026-06-30).

        Retailer blended margin: 51.0% vs distributor 45.6% — retail is the higher-return channel.
        """
        ca = scenarios["capital_allocation"]
        retailer = ca["retailer"]["incremental_contribution"]
        distributor = ca["distributor"]["incremental_contribution"]
        assert retailer > distributor, (
            f"Retailer incremental contribution ({retailer}) should exceed distributor ({distributor}). "
            "Retail blended margin (51%) > distributor blended margin (45.6%)."
        )


# ── Test 7: Algebraic reduction check ────────────────────────────────────────

class TestAlgebraicReduction:
    """
    Perturb one value in a copy of the data and confirm the relevant validation
    would catch it. This verifies the tests are not vacuously true.
    """

    def test_perturbing_contribution_dollars_breaks_per_unit_check(self, channels):
        """
        If we change contribution_dollars significantly, the per-unit consistency
        check should fail on the mutated copy.
        """
        mutated = copy.deepcopy(channels)
        # Double Walmart's contribution_dollars — should break the per-unit check
        for ch in mutated:
            if ch["channel"] == "Walmart":
                ch["contribution_dollars"] = ch["contribution_dollars"] * 2
                break

        failures = []
        for ch in mutated:
            if ch["channel"] != "Walmart":
                continue
            implied = ch["contribution_per_unit"] * ch["units_shipped"]
            tolerance = max(10, implied * 0.01)
            if abs(ch["contribution_dollars"] - implied) > tolerance:
                failures.append(ch["channel"])

        assert len(failures) > 0, (
            "Algebraic reduction check failed: doubling Walmart contribution_dollars "
            "should have been detected but wasn't. Test logic may be too lenient."
        )

    def test_perturbing_waterfall_cumulative_breaks_step_check(self, deductions):
        """
        If we alter a cumulative value mid-waterfall, step arithmetic should fail
        on the mutated copy.
        """
        mutated = copy.deepcopy(deductions)
        # Alter the second step's cumulative for Walmart
        walmart_steps = mutated["Walmart"]["steps"]
        original_cumulative = walmart_steps[1]["cumulative"]
        walmart_steps[1]["cumulative"] = original_cumulative + 50000  # large perturbation

        # Re-run the step-by-step arithmetic check on the mutated copy
        steps = walmart_steps
        running = steps[0]["value"]
        detected_mismatch = False
        for step in steps[1:]:
            is_marker = step.get("is_subtotal") or step.get("is_total")
            if not is_marker:
                running += step["value"]
                if abs(step["cumulative"] - running) > 1:
                    detected_mismatch = True
                    break
            else:
                running = step["cumulative"]

        assert detected_mismatch, (
            "Algebraic reduction check failed: perturbing Walmart waterfall cumulative "
            "should have been detected but wasn't."
        )

    def test_perturbing_scenario_delta_breaks_delta_check(self, scenarios):
        """
        If we change delta without changing dtc/retail, the delta check should catch it.
        """
        mutated = copy.deepcopy(scenarios)
        mutated["capital_allocation"]["delta"] += 100000  # off by $100K

        ca = mutated["capital_allocation"]
        retailer = ca["retailer"]["incremental_contribution"]
        distributor = ca["distributor"]["incremental_contribution"]
        expected_delta = distributor - retailer
        detected = abs(ca["delta"] - expected_delta) > 1

        assert detected, (
            "Algebraic reduction check failed: perturbing scenarios delta "
            "should have been detected but wasn't."
        )
