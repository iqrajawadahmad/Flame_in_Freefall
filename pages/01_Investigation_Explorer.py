"""Explore NASA investigation metadata, measurements, findings, and resources."""
import streamlit as st

from modules import database as db
from modules.data_processing import NA, fmt_value, is_missing
from modules.ui import no_data, page_header

st.set_page_config(page_title="Investigation Explorer", page_icon="🔥", layout="wide")

if page_header("Investigation Explorer", "Browse investigation records and their evidence"):
    investigations = db.get_all_investigations()
    if investigations.empty:
        no_data("Investigations")
        st.stop()

    ids = investigations["investigation_id"].astype(str).tolist()
    selected_id = st.selectbox("Select an investigation", ids)
    record = investigations.loc[investigations["investigation_id"] == selected_id].iloc[0]
    title = record.get("name")
    st.subheader(title if title and title != NA else selected_id)
    st.caption(f"Investigation ID: {selected_id}")

    fields = [
        ("Acronym", "acronym"),
        ("Research area", "research_area"),
        ("Project type", "project_type"),
        ("Sub-research area", "sub_research_area"),
        ("Platform", "platform"),
        ("Principal investigator", "principal_investigator"),
        ("NASA PSI dataset DOI", "doi"),
        ("Objectives", "objectives"),
        ("Hypothesis", "hypothesis"),
        ("Experiment hardware", "experiment_hardware"),
        ("Notes", "notes"),
    ]
    metadata = [
        {"Field": label, "Value": fmt_value(record.get(column))}
        for label, column in fields
        if column in record.index and record.get(column) is not None
    ]
    st.dataframe(metadata, width="stretch", hide_index=True)
    source_url = record.get("source_url")
    if not is_missing(source_url):
        st.link_button("Open official NASA PSI dataset record", source_url)

    params = db.get_parameters(selected_id)
    st.subheader("Recorded parameter summaries")
    if params.empty:
        no_data("Parameter summaries")
    else:
        columns = [c for c in (
            "parameter_name", "value", "unit", "statistic", "n_runs",
            "value_min", "value_max", "quality_flag", "source_reference",
        ) if c in params.columns]
        st.dataframe(params[columns], width="stretch", hide_index=True)
        st.download_button(
            "Download parameter summaries (CSV)",
            params[columns].to_csv(index=False).encode("utf-8"),
            file_name=f"{selected_id.lower()}_parameter_summaries.csv",
            mime="text/csv",
        )

    findings = db.get_findings(selected_id)
    st.subheader("Source-linked findings")
    if findings.empty:
        no_data("Extracted findings")
    else:
        for _, finding in findings.iterrows():
            with st.container(border=True):
                st.caption(
                    f"{fmt_value(finding.get('category'))} · "
                    f"{fmt_value(finding.get('source_reference'))}"
                )
                st.write(fmt_value(finding.get("finding_text")))

    resources = db.get_resources(selected_id)
    st.subheader("Resources and publications")
    if resources.empty:
        no_data("Resources")
    else:
        columns = [c for c in (
            "resource_type", "file_name", "source_url", "page_number",
        ) if c in resources.columns]
        st.dataframe(
            resources[columns],
            column_config={
                "source_url": st.column_config.LinkColumn("Source link", display_text="Open source")
            },
            width="stretch",
            hide_index=True,
        )
