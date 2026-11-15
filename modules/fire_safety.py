"""Fire-safety helpers (Phase 6 interface)."""
from __future__ import annotations

import pandas as pd

PILLARS = ["Prevention", "Detection", "Suppression"]

# Phase 6 research-gap evidence statuses
GAP_STATUSES = {
    "Confirmed gap": "Supported by a documented literature review",
    "Potential gap": "Indicated by incomplete or limited evidence",
    "Unknown": "Insufficient information to conclude",
}

# Phase 6 hazard categories (descriptive reference table, not NASA findings)
HAZARD_CATEGORIES = pd.DataFrame([
    ("Material flammability", "Material composition, ignition behaviour, flame spread", "Selection of safer spacecraft materials"),
    ("Oxygen availability", "Oxygen concentration, partial pressure", "Oxidizer availability"),
    ("Environmental conditions", "Pressure, temperature, gas composition", "Influence on combustion behaviour"),
    ("Fluid flow", "Airflow velocity, direction, ventilation", "Heat and species transport"),
    ("Thermal behaviour", "Surface temperature, heat flux, thermal properties", "Heating and potential ignition"),
    ("Combustion products", "Smoke, particulates, gases", "Detection and crew exposure considerations"),
], columns=["Hazard category", "Parameters to investigate", "Fire-safety significance"])

ENVIRONMENTS = pd.DataFrame([
    ("Earth laboratory", "1 g", "Terrestrial reference conditions"),
    ("ISS", "Microgravity / near free fall", "Buoyancy-driven convection strongly suppressed"),
    ("Lunar habitat", "~0.165 g", "Partial-gravity combustion behaviour"),
    ("Mars habitat", "~0.38 g", "Different buoyancy and flow behaviour"),
], columns=["Environment", "Gravity condition", "Assessment consideration"])


def findings_by_pillar(findings: pd.DataFrame, pillar: str) -> pd.DataFrame:
    """Findings whose category is the pillar or 'Multiple'. Does not force a
    finding into pillars it was not classified under."""
    if findings.empty or "category" not in findings:
        return pd.DataFrame()
    cat = findings["category"].fillna("Unclassified")
    return findings[(cat == pillar) | (cat == "Multiple")]
