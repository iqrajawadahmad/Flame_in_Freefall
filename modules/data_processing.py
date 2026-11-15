"""Display helpers and unit conversion. Centralised so every page behaves the same."""
from __future__ import annotations

import math
from typing import Any

import pandas as pd

NA = "Not available"

# Conversions to the project's standard units (Phase 3 table).
# Only apply these after verifying the ORIGINAL unit in the NASA source.
_TO_STANDARD = {
    # temperature handled separately (offset conversions)
    "pressure": {"pa": 1.0, "kpa": 1e3, "mpa": 1e6, "bar": 1e5, "atm": 101325.0,
                 "psi": 6894.757, "torr": 133.322, "mmhg": 133.322},
    "length": {"m": 1.0, "cm": 1e-2, "mm": 1e-3, "um": 1e-6},
    "velocity": {"m/s": 1.0, "cm/s": 1e-2, "mm/s": 1e-3},
    "time": {"s": 1.0, "ms": 1e-3, "min": 60.0},
}


def is_missing(value: Any) -> bool:
    if value is None:
        return True
    try:
        return bool(pd.isna(value))
    except (TypeError, ValueError):
        return False


def fmt_value(value: Any, digits: int = 4) -> str:
    """Show missing values as 'Not available' (never 0)."""
    if is_missing(value):
        return NA
    if isinstance(value, (int, float)):
        if value != 0 and (abs(value) >= 1e5 or abs(value) < 1e-3):
            return f"{value:.{digits}g}"
        return f"{value:.{digits}g}"
    return str(value)


def to_kelvin(value: float, unit: str) -> float:
    u = unit.strip().lower().replace("°", "")
    if u in ("k", "kelvin"):
        return value
    if u in ("c", "celsius"):
        return value + 273.15
    if u in ("f", "fahrenheit"):
        return (value - 32.0) * 5.0 / 9.0 + 273.15
    raise ValueError(f"Unsupported temperature unit: {unit!r}")


def convert(value: float, unit: str, kind: str) -> float:
    """Convert to the standard unit for `kind` (pressure/length/velocity/time).
    Raises ValueError for unsupported units instead of guessing."""
    if kind == "temperature":
        return to_kelvin(value, unit)
    table = _TO_STANDARD.get(kind)
    if table is None:
        raise ValueError(f"Unknown quantity kind: {kind!r}")
    factor = table.get(unit.strip().lower())
    if factor is None:
        raise ValueError(f"Unsupported {kind} unit: {unit!r}")
    return value * factor


def parameter_availability(params: pd.DataFrame) -> pd.DataFrame:
    """Investigation x parameter matrix: 1 if at least one non-null value exists."""
    if params.empty or "value" not in params:
        return pd.DataFrame()
    p = params.copy()
    has = p["value"].notna()
    if "value_min" in p:  # range known but no single honest value (e.g. 2 differing tests)
        has = has | p["value_min"].notna()
    p["has_value"] = has.astype(int)
    return p.pivot_table(index="investigation_id", columns="parameter_name",
                         values="has_value", aggfunc="max", fill_value=0)


def parameter_statistics(params: pd.DataFrame) -> pd.DataFrame:
    """Phase 3 statistics. Only groups by parameter AND unit so different units
    are never mixed."""
    if params.empty or "value" not in params:
        return pd.DataFrame()
    p = params.dropna(subset=["value"])
    if p.empty:
        return pd.DataFrame()
    g = p.groupby(["parameter_name", "unit"], dropna=False)["value"]
    out = g.agg(["count", "mean", "median", "min", "max", "std"]).reset_index()
    out["investigations"] = p.groupby(["parameter_name", "unit"], dropna=False)[
        "investigation_id"].nunique().values
    return out.rename(columns={"count": "observations"})
