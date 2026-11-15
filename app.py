"""Flame in Freefall Streamlit entry point and navigation."""
import streamlit as st

st.set_page_config(
    page_title="Flame in Freefall",
    page_icon="🔥",
    layout="wide",
    initial_sidebar_state="expanded",
)

pages = [
    st.Page("pages/00_Dashboard.py", title="Dashboard", icon=":material/dashboard:", default=True),
    st.Page("pages/01_Investigation_Explorer.py", title="Investigation Explorer", icon=":material/search:"),
    st.Page("pages/02_Parameter_Analyzer.py", title="Parameter Analyzer", icon=":material/monitoring:"),
    st.Page("pages/03_Investigation_Comparison.py", title="Investigation Comparison", icon=":material/compare_arrows:"),
    st.Page("pages/04_Physics_Calculators.py", title="Physics Calculators", icon=":material/functions:"),
    st.Page("pages/05_Investigation_Ranking.py", title="Investigation Ranking", icon=":material/leaderboard:"),
    st.Page("pages/06_Grounded_Research_Insights.py", title="Grounded Research Insights", icon=":material/lightbulb:"),
    st.Page("pages/07_Fire_Safety_Assessment.py", title="Fire Safety Assessment", icon=":material/shield:"),
]

st.navigation(pages, position="hidden").run()
