"""Transparent weighted investigation-relevance ranking (Phase 5 method).

R_i = sum_j(w_j * S_ij)  with S in 0..5, reported as a percentage.
Missing criteria are UNKNOWN (None) - never zero. The score is computed over
the criteria that have evidence (weights renormalised) and is reported
together with evidence coverage (share of total weight supported by evidence).

This is a decision-support relevance metric, NOT machine learning, NOT a
fire-risk index. AI must never change these numbers.
"""
from __future__ import annotations

from typing import Dict, Optional

import pandas as pd

DEFAULT_WEIGHTS: Dict[str, float] = {
    "Environmental similarity": 25,
    "Fire-safety relevance": 25,
    "Experimental parameter match": 20,
    "Evidence quality": 15,
    "Operational applicability": 15,
}


def validate_weights(weights: Dict[str, float]) -> None:
    if any(w < 0 for w in weights.values()):
        raise ValueError("weights must be non-negative")
    if abs(sum(weights.values()) - 100) > 1e-6:
        raise ValueError(f"weights must sum to 100 (got {sum(weights.values())})")


def score_investigation(scores: Dict[str, Optional[float]],
                        weights: Dict[str, float] = DEFAULT_WEIGHTS) -> dict:
    """scores: criterion -> 0..5, or None/NaN when not documented."""
    validate_weights(weights)
    known_weight = 0.0
    weighted_sum = 0.0
    contributions = {}
    for crit, w in weights.items():
        s = scores.get(crit)
        if s is None or pd.isna(s):
            contributions[crit] = None
            continue
        if not 0 <= s <= 5:
            raise ValueError(f"score for {crit!r} must be between 0 and 5 (got {s})")
        known_weight += w
        weighted_sum += w * s
        contributions[crit] = w * s / 5  # points out of 100 at full weight
    total_w = sum(weights.values())
    coverage = 100.0 * known_weight / total_w
    relevance = (weighted_sum / known_weight) / 5 * 100 if known_weight > 0 else None
    return {
        "relevance_score_pct": relevance,
        "evidence_coverage_pct": coverage,
        "contributions": contributions,
    }


def rank_investigations(score_table: pd.DataFrame,
                        weights: Dict[str, float] = DEFAULT_WEIGHTS,
                        min_coverage: float = 0.0) -> pd.DataFrame:
    """score_table: one row per investigation_id, one column per criterion
    (blank/NaN = unknown). Returns a ranked table."""
    rows = []
    for inv_id, row in score_table.iterrows():
        res = score_investigation(row.to_dict(), weights)
        rows.append({
            "investigation_id": inv_id,
            "relevance_score_pct": res["relevance_score_pct"],
            "evidence_coverage_pct": res["evidence_coverage_pct"],
        })
    out = pd.DataFrame(rows)
    if out.empty:
        return out
    out = out[out["evidence_coverage_pct"] >= min_coverage]
    return out.sort_values(["relevance_score_pct", "evidence_coverage_pct"],
                           ascending=False, na_position="last").reset_index(drop=True)
