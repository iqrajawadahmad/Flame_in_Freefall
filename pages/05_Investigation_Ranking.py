"""Evidence-based relevance ranking; never manufacture unsupported scores."""
from pathlib import Path

import pandas as pd
import streamlit as st

from modules import database as db
from modules.ranking_engine import DEFAULT_WEIGHTS, rank_investigations
from modules.ui import no_data, page_header

st.set_page_config(page_title="Investigation Ranking", page_icon="🏅", layout="wide")

if page_header("Investigation Ranking", "Transparent relevance scores with evidence coverage"):
    st.warning(
        "This is a research-relevance decision aid, not a fire-risk score or an AI prediction. "
        "Only enter scores that your team can support with cited evidence."
    )
    st.write("Weights used by the ranking method:")
    st.dataframe(
        pd.DataFrame({"Criterion": DEFAULT_WEIGHTS.keys(), "Weight (%)": DEFAULT_WEIGHTS.values()}),
        width="stretch",
        hide_index=True,
    )

    ids = db.get_all_investigations()
    if ids.empty:
        no_data("Investigations")
        st.stop()
    investigation_ids = ids["investigation_id"].astype(str).tolist()
    criteria = list(DEFAULT_WEIGHTS)
    template = pd.DataFrame(columns=["investigation_id", *criteria])
    template["investigation_id"] = investigation_ids
    st.download_button(
        "Download blank scoring template (CSV)",
        template.to_csv(index=False).encode("utf-8"),
        file_name="investigation_scores_template.csv",
        mime="text/csv",
    )

    score_path = Path(__file__).resolve().parents[1] / "data" / "processed_data" / "investigation_scores.csv"
    uploaded = st.file_uploader("Upload completed investigation_scores.csv", type=["csv"])
    score_table = None
    source_label = ""
    try:
        if uploaded is not None:
            score_table = pd.read_csv(uploaded)
            source_label = "uploaded file"
        elif score_path.exists():
            score_table = pd.read_csv(score_path)
            source_label = str(score_path.name)
    except (OSError, pd.errors.ParserError, UnicodeDecodeError) as error:
        st.error(f"Could not read the ranking CSV: {error}")
        st.stop()

    if score_table is None:
        st.info(
            "No ranking score file is available yet. Download the template, fill only "
            "evidence-supported 0–5 scores, leave unknown scores blank, and upload it."
        )
        st.stop()
    if "investigation_id" not in score_table.columns:
        st.error("The ranking CSV must include an 'investigation_id' column.")
        st.stop()
    if score_table["investigation_id"].isna().any():
        st.error("Every scoring row must have an investigation ID.")
        st.stop()
    score_table["investigation_id"] = score_table["investigation_id"].astype(str)
    if score_table["investigation_id"].duplicated().any():
        st.error("The ranking CSV contains duplicate investigation IDs.")
        st.stop()

    unknown_ids = sorted(set(score_table["investigation_id"].dropna()) - set(investigation_ids))
    if unknown_ids:
        st.error(f"Unknown investigation IDs in the ranking CSV: {', '.join(unknown_ids)}")
        st.stop()

    table = score_table.set_index("investigation_id").reindex(investigation_ids)
    for criterion in criteria:
        if criterion not in table.columns:
            table[criterion] = float("nan")

    raw_scores = table[criteria]
    numeric_scores = raw_scores.apply(pd.to_numeric, errors="coerce")
    non_numeric = raw_scores.notna() & numeric_scores.isna()
    if non_numeric.any().any():
        st.error("Every non-blank criterion score must be a number from 0 to 5.")
        st.stop()
    invalid = numeric_scores.notna() & ~numeric_scores.apply(lambda col: col.between(0, 5))
    if invalid.any().any():
        st.error("Scores must be from 0 to 5; blanks represent unknown evidence.")
        st.stop()
    ranking = rank_investigations(numeric_scores, min_coverage=0)
    ranking.rename(columns={
        "relevance_score_pct": "Relevance (%)",
        "evidence_coverage_pct": "Evidence coverage (%)",
        "investigation_id": "Investigation",
    }, inplace=True)
    st.subheader("Ranked investigations")
    st.dataframe(ranking, width="stretch", hide_index=True)
    st.caption(f"Scores loaded from {source_label}.")
    st.caption(
        "Scores are normalized over known criteria only. Evidence coverage reports "
        "how much of the total criterion weight had a non-blank score."
    )
