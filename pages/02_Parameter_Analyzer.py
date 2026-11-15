"""Analyze parameter values without mixing different units."""
import streamlit as st

from modules import database as db
from modules.data_processing import NA
from modules.ui import no_data, page_header
from modules.visualization import run_distribution

st.set_page_config(page_title="Parameter Analyzer", page_icon="📊", layout="wide")

if page_header("Parameter Analyzer", "Inspect run-level conditions and measurements"):
    parameters = db.get_parameters()
    if parameters.empty:
        no_data("Parameter records")
        st.stop()

    choices = (
        parameters[["parameter_name", "unit"]]
        .drop_duplicates()
        .sort_values(["parameter_name", "unit"], na_position="last")
    )
    labels = [
        f"{row.parameter_name} [{row.unit if row.unit else 'unit not recorded'}]"
        for row in choices.itertuples(index=False)
    ]
    selected_label = st.selectbox("Parameter (unit shown to prevent mixing)", labels)
    selected = choices.iloc[labels.index(selected_label)]
    parameter_name = selected["parameter_name"]
    unit = selected["unit"]

    summary = parameters[
        (parameters["parameter_name"] == parameter_name)
        & parameters["unit"].eq(unit)
    ].copy()
    st.subheader("Investigation-level summaries")
    st.dataframe(
        summary[[c for c in (
            "investigation_id", "value", "statistic", "n_runs", "value_min",
            "value_max", "quality_flag", "source_reference",
        ) if c in summary.columns]],
        width="stretch",
        hide_index=True,
    )

    runs = db.get_runs(parameter_name=parameter_name)
    if not runs.empty and "unit" in runs.columns:
        runs = runs[runs["unit"].eq(unit) & runs["value"].notna()].copy()
    else:
        runs = runs.iloc[0:0]

    st.subheader("Individual recorded tests")
    if runs.empty:
        no_data("Numeric run-level observations for this parameter and unit")
    else:
        st.plotly_chart(
            run_distribution(runs, parameter_name, unit or NA),
            width="stretch",
        )
        columns = [c for c in (
            "investigation_id", "run_id", "value", "value_low", "value_high",
            "unit", "original_text", "original_unit", "text_value", "quality_flag",
        ) if c in runs.columns]
        st.dataframe(runs[columns], width="stretch", hide_index=True)
        st.download_button(
            "Download filtered run data (CSV)",
            runs[columns].to_csv(index=False).encode("utf-8"),
            file_name="parameter_run_data.csv",
            mime="text/csv",
        )
    st.caption("Summary values may be medians or ranges; inspect the statistic and quality flags.")
