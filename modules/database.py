"""Shared database access layer (single source of truth for every page).

Pages must NOT write SQL themselves. They call the functions below.

Database selection
------------------
1. data/nasa_combustion.db              -> the REAL database (from Phase 2)
2. data/placeholder_nasa_combustion.db  -> DEMO data, only so the UI can be built

If the real DB exists it is always used. `is_placeholder()` tells the UI
whether to show the "placeholder data" warning banner.

Missing values
--------------
Missing measurements are stored as NULL in SQLite and arrive here as NaN/None.
They are NEVER replaced with 0 or an average. Use data_processing.fmt_value()
to show them as "Not available".
"""
from __future__ import annotations

import sqlite3
from pathlib import Path
from typing import Optional

import pandas as pd

try:  # streamlit is optional so this module can be unit-tested without it
    import streamlit as st

    _cache = st.cache_data(ttl=300, show_spinner=False)
except Exception:  # pragma: no cover
    def _cache(func):
        return func

ROOT = Path(__file__).resolve().parent.parent
REAL_DB = ROOT / "data" / "nasa_combustion.db"
PLACEHOLDER_DB = ROOT / "data" / "placeholder_nasa_combustion.db"

# Phase 2 schema. Extra nullable columns (original_value, original_unit,
# source_reference, page_number) follow the parameters.csv recommendation in
# the Phase 2 brief. If the real DB has different/missing columns the pages
# still work, because they use SELECT * and tolerate absent columns.
SCHEMA = """
CREATE TABLE IF NOT EXISTS investigations (
    investigation_id TEXT PRIMARY KEY,
    name             TEXT,
    acronym          TEXT,
    research_area    TEXT,
    objectives       TEXT,
    platform         TEXT,
    doi              TEXT,
    source_url       TEXT,
    project_type     TEXT,
    sub_research_area TEXT,
    experiment_hardware TEXT,
    hypothesis       TEXT,
    principal_investigator TEXT,
    notes            TEXT
);
CREATE TABLE IF NOT EXISTS parameters (
    parameter_id     INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT,
    parameter_name   TEXT,
    value            REAL,
    unit             TEXT,
    parameter_type   TEXT,   -- condition | measurement | derived | model_prediction
    original_value   REAL,
    original_unit    TEXT,
    source_reference TEXT,
    statistic        TEXT,   -- how `value` was derived: single | constant | median (NULL value = no honest single value)
    n_runs           INTEGER,
    value_min        REAL,
    value_max        REAL,
    quality_flag     TEXT,
    FOREIGN KEY (investigation_id) REFERENCES investigations(investigation_id)
);
CREATE TABLE IF NOT EXISTS experimental_runs (
    run_row_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT,
    run_id           TEXT,
    parameter_name   TEXT,
    value            REAL,   -- standard units; NULL = not available / not numeric
    value_low        REAL,   -- only when the source gave a range
    value_high       REAL,
    unit             TEXT,
    original_text    TEXT,   -- exactly what the source table contained
    original_unit    TEXT,
    text_value       TEXT,   -- for categorical items (fuel, material, test end ...)
    quality_flag     TEXT,
    FOREIGN KEY (investigation_id) REFERENCES investigations(investigation_id)
);
CREATE INDEX IF NOT EXISTS idx_run_inv   ON experimental_runs(investigation_id);
CREATE INDEX IF NOT EXISTS idx_run_param ON experimental_runs(parameter_name);
CREATE TABLE IF NOT EXISTS findings (
    finding_id       INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT,
    finding_text     TEXT,
    category         TEXT,   -- Prevention | Detection | Suppression | Multiple | Unclassified
    source_reference TEXT,
    page_number      INTEGER,
    FOREIGN KEY (investigation_id) REFERENCES investigations(investigation_id)
);
CREATE TABLE IF NOT EXISTS resources (
    resource_id      INTEGER PRIMARY KEY AUTOINCREMENT,
    investigation_id TEXT,
    resource_type    TEXT,
    file_name        TEXT,
    source_url       TEXT,
    page_number      INTEGER,
    FOREIGN KEY (investigation_id) REFERENCES investigations(investigation_id)
);
CREATE INDEX IF NOT EXISTS idx_param_inv  ON parameters(investigation_id);
CREATE INDEX IF NOT EXISTS idx_param_name ON parameters(parameter_name);
CREATE INDEX IF NOT EXISTS idx_find_inv   ON findings(investigation_id);
CREATE INDEX IF NOT EXISTS idx_res_inv    ON resources(investigation_id);
"""

TABLES = ["investigations", "parameters", "experimental_runs", "findings", "resources"]


# --------------------------------------------------------------------------
# Connection helpers
# --------------------------------------------------------------------------
def get_db_path() -> Optional[Path]:
    """Real DB if present, else placeholder DB, else None."""
    if REAL_DB.exists():
        return REAL_DB
    if PLACEHOLDER_DB.exists():
        return PLACEHOLDER_DB
    return None


def is_placeholder() -> bool:
    return get_db_path() == PLACEHOLDER_DB


def db_available() -> bool:
    return get_db_path() is not None


def init_schema(db_path: Path) -> None:
    db_path.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(db_path) as conn:
        conn.executescript(SCHEMA)


def _query(sql: str, params: tuple = ()) -> pd.DataFrame:
    """Run a read-only query. Returns an empty DataFrame if anything fails
    (missing DB, missing table, ...) so pages degrade gracefully."""
    path = get_db_path()
    if path is None:
        return pd.DataFrame()
    try:
        conn = sqlite3.connect(f"file:{path}?mode=ro", uri=True)
        try:
            return pd.read_sql_query(sql, conn, params=params)
        finally:
            conn.close()
    except Exception:
        return pd.DataFrame()


# --------------------------------------------------------------------------
# Public query functions (used by every page)
# --------------------------------------------------------------------------
@_cache
def get_all_investigations() -> pd.DataFrame:
    return _query("SELECT * FROM investigations ORDER BY investigation_id")


@_cache
def get_investigation(investigation_id: str) -> pd.DataFrame:
    return _query(
        "SELECT * FROM investigations WHERE investigation_id = ?",
        (investigation_id,),
    )


@_cache
def get_parameters(investigation_id: Optional[str] = None) -> pd.DataFrame:
    if investigation_id is None:
        return _query("SELECT * FROM parameters ORDER BY investigation_id, parameter_name")
    return _query(
        "SELECT * FROM parameters WHERE investigation_id = ? ORDER BY parameter_name",
        (investigation_id,),
    )


@_cache
def get_runs(investigation_id: Optional[str] = None,
             parameter_name: Optional[str] = None) -> pd.DataFrame:
    """Run-level (per test) values. Empty DataFrame if the table is absent."""
    sql, args = "SELECT * FROM experimental_runs WHERE 1=1", []
    if investigation_id is not None:
        sql += " AND investigation_id = ?"
        args.append(investigation_id)
    if parameter_name is not None:
        sql += " AND parameter_name = ?"
        args.append(parameter_name)
    return _query(sql + " ORDER BY investigation_id, run_id", tuple(args))


@_cache
def get_findings(investigation_id: Optional[str] = None) -> pd.DataFrame:
    if investigation_id is None:
        return _query("SELECT * FROM findings ORDER BY investigation_id")
    return _query(
        "SELECT * FROM findings WHERE investigation_id = ?", (investigation_id,)
    )


@_cache
def get_resources(investigation_id: Optional[str] = None) -> pd.DataFrame:
    if investigation_id is None:
        return _query("SELECT * FROM resources ORDER BY investigation_id")
    return _query(
        "SELECT * FROM resources WHERE investigation_id = ?", (investigation_id,)
    )


@_cache
def table_counts() -> dict:
    """Row counts per table; value is None if the table is unavailable."""
    counts = {}
    for t in TABLES:
        df = _query(f"SELECT COUNT(*) AS n FROM {t}")
        counts[t] = int(df["n"].iloc[0]) if not df.empty else None
    return counts
