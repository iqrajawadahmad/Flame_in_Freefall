"""Flame in Freefall - NASA Microgravity Combustion Intelligence Dashboard."""
import pandas as pd
import plotly.express as px
import streamlit as st

from modules import database as db
from modules.data_processing import NA
from modules.ui import page_header
from ui_theme import render_hero, render_kpi, render_research_card

if page_header("", ""):
    investigations = db.get_all_investigations()
    parameters = db.get_parameters()
    findings = db.get_findings()
    resources = db.get_resources()
    runs = db.get_runs()

    investigation_count = len(investigations) if not investigations.empty else 0
    run_record_count = len(runs) if not runs.empty else 0
    cited_findings = (
        int(findings["source_reference"].notna().sum())
        if not findings.empty and "source_reference" in findings.columns else 0
    )
    unclassified_findings = (
        int(
            findings["category"]
            .fillna("Unclassified")
            .replace("", "Unclassified")
            .eq("Unclassified")
            .sum()
        )
        if not findings.empty and "category" in findings.columns else 0
    )
    render_hero(
        "NASA MICROGRAVITY COMBUSTION · RESEARCH DASHBOARD",
        "Flame in",
        "Freefall",
        (
            "Discover how combustion changes when buoyancy fades. Explore spaceflight "
            "studies, compare recorded test conditions, and trace findings to their "
            "sources in an evidence-first research workspace."
        ),
        (
            f"{investigation_count:,} NASA investigations",
            f"{run_record_count:,} run-parameter records",
            f"{cited_findings:,} cited findings",
        ),
    )
    k1, k2, k3, k4 = st.columns(4)
    with k1:
        render_kpi("Investigations", f"{investigation_count:,}" if investigation_count else NA, "🔬")
    with k2:
        render_kpi("Run-parameter records", f"{run_record_count:,}" if run_record_count else NA, "📊")
    with k3:
        render_kpi("Parameter summaries", f"{len(parameters):,}" if not parameters.empty else NA, "🧪")
    with k4:
        render_kpi("Cited findings", f"{cited_findings:,}" if cited_findings else NA, "📚")

    with st.container(border=True):
        safety_copy, safety_status, safety_action = st.columns([2.4, 1, 1.15], vertical_alignment="center")
        with safety_copy:
            st.markdown('<div class="ff-section-label">Fire-safety evidence desk</div>', unsafe_allow_html=True)
            st.subheader("Review the evidence—not an invented risk score")
            st.caption(
                "Inspect source-classified findings, data-quality flags, and open "
                "research questions. This is not an operational hazard assessment."
            )
        with safety_status:
            st.metric("Unclassified findings", unclassified_findings)
        with safety_action:
            st.page_link(
                "pages/07_Fire_Safety_Assessment.py",
                label="Open assessment  →",
                icon=":material/shield:",
            )

    st.write("")
    st.markdown('<div class="ff-section-label">Research activity</div>', unsafe_allow_html=True)
    left, right = st.columns([1.45, 1], gap="large")
    with left:
        st.subheader("Dataset at a glance")
        st.caption("Unique run/sample IDs represented in the run-level records.")
        if not runs.empty and {"investigation_id", "run_id"} <= set(runs.columns):
            run_counts = (
                runs.groupby("investigation_id", as_index=False)["run_id"]
                .nunique()
                .rename(columns={"run_id": "Unique run IDs"})
            )
            if not investigations.empty:
                run_counts = (
                    investigations[["investigation_id"]]
                    .merge(run_counts, on="investigation_id", how="left")
                    .fillna({"Unique run IDs": 0})
                )
            run_counts = run_counts.sort_values("Unique run IDs", ascending=True)
            palette = {
                "PSI-10": "#2889ff",
                "PSI-69": "#9b5cff",
                "PSI-98": "#f4a64e",
            }
            fig = px.bar(
                run_counts,
                x="Unique run IDs",
                y="investigation_id",
                orientation="h",
                text="Unique run IDs",
                color="investigation_id",
                color_discrete_map=palette,
                labels={"investigation_id": "NASA study"},
            )
            fig.update_traces(
                textposition="outside",
                marker_line_width=0,
                texttemplate="%{x:,}",
                cliponaxis=False,
            )
            fig.update_layout(
                height=320,
                margin=dict(l=12, r=38, t=18, b=28),
                showlegend=False,
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                xaxis=dict(showgrid=True, gridcolor="rgba(157,184,220,.13)", zeroline=False, title=None),
                yaxis=dict(showgrid=False, title=None, color="#c7d6eb"),
                font=dict(color="#e6efff"),
                bargap=0.42,
            )
            st.plotly_chart(fig, width="stretch", config={"displayModeBar": False})
            st.caption("PSI-60 and PSI-62 have no run-level experimental records in this database.")
        else:
            st.info("Run-level experiment records are not available in this database.")

    with right:
        st.subheader("Key insight")
        st.caption("Evidence, not assumptions")
        if not findings.empty:
            featured = findings.iloc[0]
            investigation_id = str(featured.get("investigation_id", "NASA PSI"))
            category = str(featured.get("category") or "Unclassified")
            finding_text = str(featured.get("finding_text", "Finding text not available."))
            reference = featured.get("source_reference")
            source_meta = f"Source: {reference}" if pd.notna(reference) else "Source reference not recorded"
            render_research_card(
                f"Recorded finding · {investigation_id}",
                finding_text,
                f"{category} · {source_meta}",
            )
            finding_studies = (
                findings["investigation_id"].dropna().astype(str).unique().tolist()
                if "investigation_id" in findings.columns else []
            )
            if len(finding_studies) == 1:
                st.caption(
                    f"All {len(findings):,} extracted findings in this database are "
                    f"from {finding_studies[0]}; they are not attributed to other studies."
                )
            st.page_link(
                "pages/01_Investigation_Explorer.py",
                label="Read all findings and citations  →",
            )
        else:
            st.info("No source-linked findings are available in this database.")

    st.write("")
    st.markdown('<div class="ff-section-label">Tools &amp; research</div>', unsafe_allow_html=True)
    st.subheader("Go deeper")
    quick_tools = [
        ("🧮", "Physics calculators", "Run simplified reference calculations.", "pages/04_Physics_Calculators.py"),
        ("⚖️", "Compare studies", "Compare matching parameters and units.", "pages/03_Investigation_Comparison.py"),
        ("🏅", "View ranking", "Use transparent, evidence-backed scores.", "pages/05_Investigation_Ranking.py"),
        ("🛡️", "Safety evidence", "Review findings and open data questions.", "pages/07_Fire_Safety_Assessment.py"),
    ]
    for row_start in range(0, len(quick_tools), 2):
        quick_columns = st.columns(2)
        for column, (icon, title, description, target) in zip(
            quick_columns, quick_tools[row_start : row_start + 2]
        ):
            with column:
                with st.container(border=True):
                    st.markdown(f"### {icon} {title}")
                    st.caption(description)
                    st.page_link(target, label="Open tool  →")

    st.write("")
    spotlight = investigations.iloc[0] if not investigations.empty else None
    if spotlight is not None:
        citation, mission = st.columns([1.1, 1], gap="large")
        with citation:
            st.markdown('<div class="ff-section-label">NASA data source</div>', unsafe_allow_html=True)
            st.subheader("Research highlights")
            st.write(spotlight.get("name", "NASA PSI investigation"))
            st.caption(f"{spotlight.get('investigation_id', '')} · NASA Physical Sciences Informatics")
            if pd.notna(spotlight.get("source_url")):
                st.link_button("Open official NASA dataset record", spotlight["source_url"])
        with mission:
            st.markdown(
                """
                <div class="ff-quote">
                  Explore. Analyze. Advance fire-safety research.
                  <small>Flame in Freefall · Evidence-led exploration of combustion beyond Earth</small>
                </div>
                """,
                unsafe_allow_html=True,
            )

    with st.expander("Evidence notes & limitations"):
        st.markdown(
            """
            - This is research exploration—not a spacecraft safety certification or operational fire-risk model.
            - Recorded summaries preserve missing values, original units, ranges, and quality flags.
            - Comparisons only combine matching parameter names and units.
            - Rankings require evidence-supported scores; no scores are invented.
            - Grounded research insights summarize stored records and do not call a generative AI service.
            """
        )
    st.caption(
        f"NASA PSI-linked resource records available: {len(resources):,}. "
        "Source data and quality notes are available from the Investigation Explorer."
        if not resources.empty else "NASA PSI source-resource records are not available in this database."
    )
