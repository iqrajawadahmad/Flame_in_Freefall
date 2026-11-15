"""Reusable Plotly charts. Only call these with comparable data (same unit)."""
from __future__ import annotations

import pandas as pd
import plotly.express as px
import plotly.graph_objects as go


def _dashboard_theme(fig: go.Figure) -> go.Figure:
    fig.update_layout(
        template="plotly_dark",
        paper_bgcolor="rgba(0,0,0,0)",
        plot_bgcolor="rgba(0,0,0,0)",
        font=dict(color="#e6efff"),
    )
    return fig


def availability_heatmap(matrix: pd.DataFrame) -> go.Figure:
    fig = px.imshow(matrix, aspect="auto", color_continuous_scale=[[0, "#17243b"], [1, "#318bff"]],
                    labels=dict(x="Parameter", y="Investigation", color="Available"))
    fig.update_coloraxes(showscale=False)
    fig.update_layout(title="Parameter availability (blue = value present)")
    return _dashboard_theme(fig)


def parameter_bar(df: pd.DataFrame, parameter: str, unit: str) -> go.Figure:
    """One bar per investigation (its summary value). When the database holds the
    min/max over the underlying tests, they are drawn as the error-bar range."""
    fig = px.bar(df, x="investigation_id", y="value", text="value",
                 labels={"value": f"{parameter} [{unit}]", "investigation_id": "Investigation"})
    if {"value_min", "value_max"} <= set(df.columns) and df["value_min"].notna().all():
        fig.update_traces(error_y=dict(type="data", symmetric=False,
                                       array=(df["value_max"] - df["value"]).tolist(),
                                       arrayminus=(df["value"] - df["value_min"]).tolist()))
        fig.update_layout(title=f"{parameter} by investigation ({unit}) - bar = summary value, whiskers = min-max of tests")
    else:
        fig.update_layout(title=f"{parameter} by investigation ({unit})")
    return _dashboard_theme(fig)


def run_distribution(runs: pd.DataFrame, parameter: str, unit: str) -> go.Figure:
    """Every individual test value, grouped by investigation (same parameter AND unit only)."""
    fig = px.box(runs, x="investigation_id", y="value", points="all",
                 hover_data=["run_id", "quality_flag"],
                 labels={"value": f"{parameter} [{unit}]", "investigation_id": "Investigation"})
    fig.update_layout(title=f"{parameter}: all individual tests ({unit})")
    return _dashboard_theme(fig)


def parameter_distribution(df: pd.DataFrame, parameter: str, unit: str) -> go.Figure:
    """Box plot only makes sense with several observations."""
    fig = px.box(df, y="value", points="all", hover_data=["investigation_id"],
                 labels={"value": f"{parameter} [{unit}]"})
    fig.update_layout(title=f"Distribution of {parameter} ({unit})")
    return _dashboard_theme(fig)


def sensitivity_line(x, y, x_label: str, y_label: str, title: str) -> go.Figure:
    fig = px.line(x=x, y=y, labels={"x": x_label, "y": y_label})
    fig.update_layout(title=title)
    return _dashboard_theme(fig)


def contribution_bar(contributions: dict) -> go.Figure:
    known = {k: v for k, v in contributions.items() if v is not None}
    fig = px.bar(x=list(known.values()), y=list(known.keys()), orientation="h",
                 labels={"x": "Points (out of weight)", "y": "Criterion"})
    fig.update_layout(title="Criterion contributions (unknown criteria omitted)")
    return _dashboard_theme(fig)
