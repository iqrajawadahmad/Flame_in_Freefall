"""Numerical verification with hand-calculated expected values (Phase 8, step 3)."""
import math
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules import physics_models as pm  # noqa: E402
from modules.data_processing import convert, fmt_value, to_kelvin  # noqa: E402
from modules.ranking_engine import DEFAULT_WEIGHTS, score_investigation  # noqa: E402


def test_convective():
    assert pm.convective_heat_transfer(10, 0.5, 400, 300) == pytest.approx(500.0)


def test_energy_balance():
    assert pm.energy_balance_heat(0.01, 1000, 300, 310) == pytest.approx(100.0)
    assert pm.air_temperature_rise(100.0, 0.01, 1000) == pytest.approx(10.0)
    assert pm.energy_over_time(100.0, 60) == pytest.approx(6000.0)


def test_thermal_diffusion():
    alpha = pm.thermal_diffusivity(0.2, 1000, 2000)
    assert alpha == pytest.approx(1e-7)
    assert pm.diffusion_timescale(0.01, alpha) == pytest.approx(1000.0)


def test_oxygen_partial_pressure():
    assert pm.oxygen_partial_pressure(0.21, 101325) == pytest.approx(21278.25)


def test_fick():
    assert pm.fick_flux(2e-5, 10.0, 5.0, 0.01) == pytest.approx(0.01)


def test_ideal_gas_concentration():
    # 1 mol at 273.15 K, 101325 Pa occupies ~0.022414 m^3
    assert pm.molar_concentration_ideal_gas(1.0, 101325, 273.15) == pytest.approx(44.615, rel=1e-3)


def test_radiation():
    expected = 1.0 * 5.670374419e-8 * 1.0 * (500 ** 4 - 300 ** 4)
    assert pm.radiative_heat_transfer(1.0, 1.0, 500, 300) == pytest.approx(expected)


@pytest.mark.parametrize("call", [
    lambda: pm.thermal_diffusivity(0.2, 0, 1000),       # zero denominator
    lambda: pm.convective_heat_transfer(10, -1, 400, 300),  # negative area
    lambda: pm.oxygen_partial_pressure(1.5, 101325),     # fraction > 1
    lambda: pm.radiative_heat_transfer(0.9, 1, -5, 300), # negative Kelvin
])
def test_invalid_inputs_raise(call):
    with pytest.raises(ValueError):
        call()


def test_unit_conversion():
    assert to_kelvin(0, "C") == pytest.approx(273.15)
    assert convert(1, "atm", "pressure") == pytest.approx(101325)
    with pytest.raises(ValueError):
        convert(1, "furlong", "length")


def test_missing_value_is_not_zero():
    assert fmt_value(None) == "Not available"
    assert fmt_value(float("nan")) == "Not available"


def test_ranking_full_matches_phase5_example():
    r = score_investigation({"Environmental similarity": 5, "Fire-safety relevance": 4,
                             "Experimental parameter match": 4, "Evidence quality": 5,
                             "Operational applicability": 3})
    assert r["relevance_score_pct"] == pytest.approx(85.0)
    assert r["evidence_coverage_pct"] == pytest.approx(100.0)


def test_ranking_unknown_is_not_zero():
    r = score_investigation({"Environmental similarity": 5, "Fire-safety relevance": 5,
                             "Experimental parameter match": None, "Evidence quality": None,
                             "Operational applicability": None})
    assert r["relevance_score_pct"] == pytest.approx(100.0)  # renormalised over known weights
    assert r["evidence_coverage_pct"] == pytest.approx(50.0)


def test_ranking_score_range_validated():
    with pytest.raises(ValueError):
        score_investigation({"Environmental similarity": 6})
