"""Compare investigations only where parameter name and unit both match."""
import pandas as pd
import streamlit as st

from modules import database as db
from modules.data_processing import NA
from modules.ui import no_data, page_header
from modules.visualization import availability_heatmap, parameter_bar

st.set_page_config(page_title="Investigation Comparison", page_icon="⚖️", layout="wide")

if page_header("Investigation Comparison", "Compare like-named parameters in matching units"):
    investigations = db.get_all_investigations()
    params = db.get_parameters()
    if investigations.empty or params.empty:
        no_data("Investigation comparison data")
        st.stop()

    ids = investigations["investigation_id"].astype(str).tolist()
    ids_with_parameters = set(params["investigation_id"].astype(str))
    default_ids = [investigation_id for investigation_id in ids
                   if investigation_id in ids_with_parameters][:2]
    selected_ids = st.multiselect(
        "Choose at least two investigations",
        ids,
        default=default_ids,
    )
    if len(selected_ids) < 2:
        st.info("Select two or more investigations to compare.")
        st.stop()

    subset = params[params["investigation_id"].isin(selected_ids)].copy()
    available = subset["value"].notna()
    if "value_min" in subset.columns:
        available = available | subset["value_min"].notna()
    matrix_data = subset.assign(
        comparison_parameter=(
            subset["parameter_name"].astype(str)
            + " ["
            + subset["unit"].fillna("unit not recorded").astype(str)
            + "]"
        ),
        available=available.astype(int),
    )
    availability = matrix_data.pivot_table(
        index="investigation_id",
        columns="comparison_parameter",
        values="available",
        aggfunc="max",
        fill_value=0,
    )
    st.subheader("Data coverage")
    st.plotly_chart(availability_heatmap(availability), width="stretch")
    st.caption("A parameter is available when it has a summary value or a recorded range.")

    present = subset[["parameter_name", "unit"]].drop_duplicates()
    shared = []
    for pair in present.itertuples(index=False, name=None):
        matching = subset[
            (subset["parameter_name"] == pair[0]) & subset["unit"].eq(pair[1])
        ]["investigation_id"].nunique()
        if matching == len(selected_ids):
            shared.append(pair)

    if not shared:
        st.warning(
            "These investigations have no parameter name-and-unit pairs in common. "
            "No values have been combined."
        )
        st.stop()

    labels = [
        f"{name} [{unit if unit else 'unit not recorded'}]"
        for name, unit in shared
    ]
    chosen = st.selectbox("Shared parameter", labels)
    parameter_name, unit = shared[labels.index(chosen)]
    selected_rows = subset[
        (subset["parameter_name"] == parameter_name) & subset["unit"].eq(unit)
    ].copy()

    if selected_rows["value"].notna().any():
        st.plotly_chart(
            parameter_bar(selected_rows.dropna(subset=["value"]), parameter_name, unit or NA),
            width="stretch",
        )
    else:
        st.info("No single summary value is available; inspect the recorded ranges below.")

    columns = [c for c in (
        "investigation_id", "value", "unit", "statistic", "n_runs",
        "value_min", "value_max", "quality_flag", "source_reference",
    ) if c in selected_rows.columns]
    st.dataframe(selected_rows[columns], width="stretch", hide_index=True)

    runs = db.get_runs(parameter_name=parameter_name)
    if not runs.empty and {"investigation_id", "unit"} <= set(runs.columns):
        runs = runs[
            runs["investigation_id"].isin(selected_ids)
            & runs["unit"].eq(unit)
            & runs["value"].notna()
        ]
    else:
        runs = pd.DataFrame()
    if not runs.empty:
        with st.expander("Run-level data for the selected comparison"):
            st.dataframe(runs, width="stretch", hide_index=True)
