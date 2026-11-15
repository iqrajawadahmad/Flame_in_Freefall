"""Source-grounded summaries; no generative AI claims or fabricated conclusions."""
import streamlit as st

from modules import database as db
from modules.ai_insights import grounded_summary
from modules.ui import no_data, page_header

st.set_page_config(page_title="Grounded Research Insights", page_icon="💡", layout="wide")

if page_header("Grounded Research Insights", "Summaries assembled from stored project records"):
    st.info(
        "These are deterministic summaries of the database, not LLM-generated "
        "analysis. No finding, measurement, or score is inferred."
    )
    investigations = db.get_all_investigations()
    if investigations.empty:
        no_data("Investigations")
        st.stop()

    selected_id = st.selectbox(
        "Investigation",
        investigations["investigation_id"].astype(str).tolist(),
    )
    record = investigations.loc[
        investigations["investigation_id"] == selected_id
    ].iloc[0]
    summary = grounded_summary(
        record,
        db.get_parameters(selected_id),
        db.get_findings(selected_id),
    )

    st.subheader("Investigation context")
    st.write(summary["general"])
    st.subheader("Recorded engineering parameters")
    st.markdown(summary["engineering"])
    st.subheader("Recorded findings")
    st.markdown(summary["fire_safety"])
    sources = db.get_resources(selected_id)
    if not sources.empty:
        st.subheader("Related source records")
        st.dataframe(
            sources[[c for c in ("resource_type", "file_name", "source_url") if c in sources.columns]],
            column_config={
                "source_url": st.column_config.LinkColumn("Source link", display_text="Open source")
            },
            width="stretch",
            hide_index=True,
        )
