"""Review source-classified findings and project data-quality flags."""
from pathlib import Path

import pandas as pd
import streamlit as st

from modules import database as db
from modules.fire_safety import ENVIRONMENTS, GAP_STATUSES, HAZARD_CATEGORIES, PILLARS
from modules.ui import no_data, page_header

st.set_page_config(page_title="Fire-Safety Assessment", page_icon="🧯", layout="wide")

if page_header("Fire-Safety Assessment", "Evidence status and data-quality context"):
    findings = db.get_findings()
    st.warning(
        "This page organizes recorded evidence; it is not a spacecraft safety "
        "certification or operational hazard assessment."
    )
    st.subheader("Recorded findings by source category")
    if findings.empty:
        no_data("Extracted findings")
    else:
        classified = findings["category"].fillna("Unclassified")
        counts = classified.value_counts().rename_axis("Category").reset_index(name="Findings")
        st.dataframe(counts, width="stretch", hide_index=True)
        unclassified = int((classified == "Unclassified").sum())
        if unclassified:
            st.info(
                f"{unclassified} finding(s) are unclassified. They are not assigned "
                "to Prevention, Detection, or Suppression without a documented review."
            )
        for pillar in PILLARS:
            with st.expander(f"{pillar} findings"):
                selected = findings[
                    findings["category"].isin([pillar, "Multiple"])
                ]
                if selected.empty:
                    st.caption("No findings are currently classified under this pillar.")
                else:
                    st.dataframe(
                        selected[[c for c in (
                            "investigation_id", "finding_text", "category",
                            "source_reference", "page_number",
                        ) if c in selected.columns]],
                        width="stretch",
                        hide_index=True,
                    )

    st.subheader("Reference hazard categories")
    st.caption("These are analysis prompts, not findings extracted from NASA data.")
    st.dataframe(HAZARD_CATEGORIES, width="stretch", hide_index=True)
    st.subheader("Environment comparison context")
    st.dataframe(ENVIRONMENTS, width="stretch", hide_index=True)

    root = Path(__file__).resolve().parents[1]
    quality_log = root / "data" / "processed_data" / "data_quality_log.csv"
    st.subheader("Data quality and unresolved questions")
    if quality_log.exists():
        try:
            quality = pd.read_csv(quality_log)
        except (OSError, pd.errors.ParserError, UnicodeDecodeError) as error:
            st.error(f"Could not read the data-quality log: {error}")
        else:
            st.dataframe(quality, width="stretch", hide_index=True)
            st.download_button(
                "Download data-quality log (CSV)",
                quality.to_csv(index=False).encode("utf-8"),
                file_name="data_quality_log.csv",
                mime="text/csv",
            )
    else:
        st.info("No processed-data quality log is present.")

    st.subheader("Optional evidence inputs")
    for filename, label in (
        ("engineering_implications.csv", "Engineering implications"),
        ("research_gaps.csv", "Research gaps"),
    ):
        path = root / "data" / "processed_data" / filename
        if path.exists():
            try:
                frame = pd.read_csv(path)
            except (OSError, pd.errors.ParserError, UnicodeDecodeError) as error:
                st.error(f"Could not read {filename}: {error}")
            else:
                st.markdown(f"**{label}**")
                st.dataframe(frame, width="stretch", hide_index=True)
        else:
            st.caption(f"{label}: not provided.")
    st.caption(f"Research-gap statuses used by the project: {', '.join(GAP_STATUSES)}.")
