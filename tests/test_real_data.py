"""Checks for the real database and the build script's parsing rules."""
import sqlite3
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(ROOT / "scripts"))
from build_real_db import missing_required_sources, parse_number  # noqa: E402

DB = ROOT / "data" / "nasa_combustion.db"


@pytest.mark.parametrize("text,expected", [
    ("12.5", (12.5, None, None)),
    ("~6", (6.0, None, None)),
    ("21.5 - 21.7", (pytest.approx(21.6), 21.5, 21.7)),
    ("RAMP", (None, None, None)),
    ("LOW O2", (None, None, None)),
    ("\ufffd", (None, None, None)),
    ("", (None, None, None)),
])
def test_parse_number(text, expected):
    v, lo, hi, _ = parse_number(text)
    assert (v, lo, hi) == expected


def test_approximate_and_range_are_flagged():
    assert "approximate" in parse_number("~9")[3]
    assert "range" in parse_number("21.5 - 21.7")[3]


def test_missing_source_check_reports_required_files(tmp_path):
    missing = missing_required_sources(tmp_path)
    assert missing
    assert all(not path.exists() for path in missing)


@pytest.fixture(scope="module")
def conn():
    if not DB.exists():
        pytest.skip("real database not built")
    c = sqlite3.connect(DB)
    yield c
    c.close()


def q(conn, sql):
    return conn.execute(sql).fetchall()


def test_five_investigations(conn):
    ids = {r[0] for r in q(conn, "SELECT investigation_id FROM investigations")}
    assert ids == {"PSI-10", "PSI-60", "PSI-62", "PSI-69", "PSI-98"}


def test_no_zero_used_for_missing(conn):
    # FLEX had one ambient pressure of 0.0 mmHg and extinction diameters of 0.0: must be NULL
    assert q(conn, "SELECT COUNT(*) FROM experimental_runs WHERE parameter_name='Ambient pressure' "
                   "AND investigation_id='PSI-69' AND value<=0")[0][0] == 0
    assert q(conn, "SELECT COUNT(*) FROM experimental_runs WHERE parameter_name LIKE 'Visible flame extinction%' "
                   "AND value<=0")[0][0] == 0


def test_ramped_tests_are_null_not_zero(conn):
    assert q(conn, "SELECT COUNT(*) FROM experimental_runs WHERE original_text IN ('RAMP','RAMPED','LOW O2') "
                   "AND value IS NOT NULL")[0][0] == 0


def test_unit_conversion_spot_checks(conn):
    # SAFFIRE air flow 20 cm/s -> 0.2 m/s ; ACME pinit ~1 atm -> ~101325 Pa
    v = q(conn, "SELECT value FROM experimental_runs WHERE run_id='S1' AND parameter_name='Airflow velocity'")[0][0]
    assert v == pytest.approx(0.2)
    v = q(conn, "SELECT value FROM experimental_runs WHERE run_id='21328A1' AND parameter_name='Ambient pressure'")[0][0]
    assert v == pytest.approx(0.998235 * 101325, rel=1e-6)


def test_every_parameter_has_a_single_unit(conn):
    bad = q(conn, "SELECT parameter_name FROM parameters GROUP BY investigation_id, parameter_name "
                  "HAVING COUNT(DISTINCT unit) > 1")
    assert bad == []


def test_no_invented_summary_for_two_differing_tests(conn):
    r = q(conn, "SELECT value, statistic FROM parameters WHERE investigation_id='PSI-98' AND parameter_name='Burn time'")[0]
    assert r[0] is None and r[1] == "no single value"


def test_findings_have_page_numbers(conn):
    rows = q(conn, "SELECT page_number, source_reference FROM findings")
    assert rows and all(p and "p." in s for p, s in rows)
