"""AI insights (Phase 5 interface).

The core dashboard must work WITHOUT any AI service. So the default here is a
deterministic, source-grounded summary assembled only from database fields.

To add an LLM later: implement `llm_summary()` and read the API key from
st.secrets / environment variables (never commit keys to GitHub). Always fall
back to `grounded_summary()` if the call fails. AI may explain rankings but
must never invent scores, experimental conditions or conclusions.
"""
from __future__ import annotations

import os
from typing import Optional

import pandas as pd

from modules.data_processing import NA, fmt_value


def ai_available() -> bool:
    return bool(os.environ.get("LLM_API_KEY"))


def grounded_summary(investigation: pd.Series, params: pd.DataFrame,
                     findings: pd.DataFrame) -> dict:
    """Three-level summary built strictly from stored records."""
    name = investigation.get("name") or investigation.get("investigation_id")
    objectives = investigation.get("objectives")
    general = (f"{name}: {objectives}" if not pd.isna(objectives) and objectives
               else f"{name}: objective not available in the database.")

    if params.empty:
        engineering = "No experimental parameters are recorded for this investigation."
    else:
        lines = []
        for _, r in params.iterrows():
            lines.append(f"- {r['parameter_name']} ({r.get('parameter_type', '?')}): "
                         f"{fmt_value(r['value'])} {r['unit'] if not pd.isna(r['unit']) else ''}".rstrip())
        engineering = "\n".join(lines)

    if findings.empty:
        fire_safety = "No extracted findings are recorded for this investigation."
    else:
        lines = []
        for _, f in findings.iterrows():
            ref = f.get("source_reference")
            ref = ref if not pd.isna(ref) else "source not recorded"
            lines.append(f"- [{f.get('category', 'Unclassified')}] {f['finding_text']} ({ref})")
        fire_safety = "\n".join(lines)

    return {"general": general, "engineering": engineering, "fire_safety": fire_safety}


def llm_summary(text: str) -> Optional[str]:  # pragma: no cover
    """TODO (optional): call an LLM with the source text and return structured
    extraction with page references. Return None on any failure."""
    return None
