"""Shared UI helpers (header, placeholder warning, empty-state messages)."""
from __future__ import annotations

from html import escape
from urllib.parse import urlsplit

import streamlit as st

from modules import database as db
from ui_theme import load_theme

_NAV_ITEMS = (
    ("Dashboard", "🏠", ""),
    ("Investigation Explorer", "🔍", "Investigation_Explorer"),
    ("Parameter Analyzer", "📊", "Parameter_Analyzer"),
    ("Investigation Comparison", "⚖️", "Investigation_Comparison"),
    ("Physics Calculators", "🧮", "Physics_Calculators"),
    ("Investigation Ranking", "🏅", "Investigation_Ranking"),
    ("Grounded Research Insights", "💡", "Grounded_Research_Insights"),
    ("Fire Safety Assessment", "🛡️", "Fire_Safety_Assessment"),
)


def _navigation_markup() -> str:
    current_url = st.context.url
    if current_url is None:
        current_path = "/"
    else:
        if not isinstance(current_url, str):
            current_url = current_url.decode("utf-8")
        current_path = str(urlsplit(current_url).path)
    current_route = current_path.rstrip("/").rsplit("/", maxsplit=1)[-1]
    routes = {route for _, _, route in _NAV_ITEMS if route}
    if current_route in routes:
        base_path = current_path[: -len(current_route)]
    else:
        base_path = current_path.rstrip("/") + "/"
        current_route = ""

    links = []
    for label, icon, route in _NAV_ITEMS:
        href = f"{base_path}{route}"
        active = ' aria-current="page"' if route == current_route else ""
        links.append(
            f'<a class="ff-nav-link" href="{escape(href, quote=True)}" '
            f'target="_self"{active}>'
            f'<span class="ff-nav-icon" aria-hidden="true">{icon}</span>'
            f'<span>{label}</span></a>'
        )
    return f'<nav class="ff-sidebar-nav" aria-label="Main navigation">{"".join(links)}</nav>'


def _apply_dashboard_style() -> None:
    st.markdown(
        """
        <style>
        :root {
            --ink: #eef4ff;
            --muted: #9eafc9;
            --line: rgba(149, 178, 219, 0.17);
            --accent: #42b6ff;
            --navy: #071226;
        }
        [data-testid="stAppViewContainer"] {
            background:
                radial-gradient(ellipse at 80% 0%, rgba(29, 103, 191, 0.16), transparent 38%),
                radial-gradient(ellipse at 8% 42%, rgba(88, 52, 184, 0.08), transparent 34%),
                #080f20;
            background-attachment: fixed;
        }
        [data-testid="stHeader"] {
            background: rgba(8, 15, 32, 0.9);
        }
        .block-container {
            max-width: 1440px;
            padding-top: 1.35rem;
            padding-bottom: 4rem;
        }
        h1, h2, h3, p, label {
            color: var(--ink);
        }
        h1, h2, h3 { letter-spacing: -0.035em; }
        h1 { font-weight: 760; }
        h2, h3 { font-weight: 680; }
        [data-testid="stCaptionContainer"] {
            color: var(--muted);
        }
        [data-testid="stSidebar"] {
            background:
                radial-gradient(ellipse at 30% 100%, rgba(30, 94, 182, 0.19), transparent 38%),
                #050b18;
            border-right: 1px solid rgba(86, 132, 197, 0.2);
        }
        [data-testid="stSidebar"] [data-testid="stMarkdownContainer"],
        [data-testid="stSidebar"] [data-testid="stCaptionContainer"],
        [data-testid="stSidebar"] p,
        [data-testid="stSidebar"] span {
            color: #e7eef6;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] {
            padding-top: 0.5rem;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a {
            border-radius: 0.6rem;
            margin: 0.12rem 0.4rem;
            transition: background 140ms ease;
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a[aria-current="page"] {
            background: linear-gradient(100deg, #0879e8, #5737cf);
            box-shadow: 0 5px 20px rgba(30, 110, 235, 0.2);
        }
        [data-testid="stSidebar"] [data-testid="stSidebarNav"] a:hover {
            background: rgba(255, 255, 255, 0.1);
        }
        .ff-sidebar-nav {
            display: grid;
            gap: 0.3rem;
            margin: 0.1rem 0 0.8rem;
        }
        .ff-sidebar-nav a {
            display: flex;
            align-items: center;
            gap: 0.68rem;
            min-height: 2.45rem;
            padding: 0.48rem 0.68rem;
            border: 1px solid transparent;
            border-radius: 0.62rem;
            background: transparent;
            color: #d7e4f5;
            font-size: 0.9rem;
            font-weight: 560;
            text-decoration: none;
            transition: background 140ms ease, border-color 140ms ease, color 140ms ease;
        }
        .ff-sidebar-nav a:hover {
            border-color: rgba(142, 183, 238, 0.14);
            background: rgba(255, 255, 255, 0.075);
        }
        .ff-sidebar-nav a[aria-current="page"] {
            border-color: rgba(98, 171, 255, 0.2);
            background: linear-gradient(100deg, #0879e8, #5737cf);
            color: #ffffff;
            box-shadow: 0 5px 20px rgba(30, 110, 235, 0.2);
        }
        .ff-nav-icon {
            width: 1.3rem;
            flex: 0 0 1.3rem;
            text-align: center;
        }
        [data-testid="stMetric"] {
            background: linear-gradient(145deg, rgba(20, 34, 59, 0.96), rgba(11, 22, 42, 0.96));
            border: 1px solid var(--line);
            border-radius: 0.85rem;
            padding: 1rem 1.1rem;
            box-shadow: 0 9px 28px rgba(0, 0, 0, 0.17);
            transition: transform 160ms ease, border-color 160ms ease, box-shadow 160ms ease;
        }
        [data-testid="stMetric"]:hover {
            transform: translateY(-2px);
            border-color: rgba(75, 171, 255, 0.38);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.24), 0 0 22px rgba(47, 134, 245, 0.08);
        }
        [data-testid="stMetricLabel"] {
            color: #a9bad3;
            font-weight: 600;
        }
        [data-testid="stMetricValue"] {
            color: #f3f7ff;
            font-weight: 760;
        }
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--line);
            border-radius: 0.9rem;
            background: linear-gradient(145deg, rgba(19, 32, 55, 0.93), rgba(12, 23, 42, 0.93));
            box-shadow: 0 8px 26px rgba(0, 0, 0, 0.12);
            backdrop-filter: blur(12px);
            -webkit-backdrop-filter: blur(12px);
            transition: border-color 160ms ease, box-shadow 160ms ease, transform 160ms ease;
        }
        [data-testid="stVerticalBlockBorderWrapper"]:hover {
            border-color: rgba(113, 165, 235, 0.28);
            box-shadow: 0 12px 30px rgba(0, 0, 0, 0.18);
        }
        [data-testid="stPlotlyChart"],
        [data-testid="stArrowVegaLiteChart"] {
            border: 1px solid var(--line);
            border-radius: 0.9rem;
            background: rgba(12, 23, 42, 0.8);
            padding: 0.45rem;
        }
        .stButton > button, .stDownloadButton > button, [data-testid="stLinkButton"] a {
            border-radius: 0.65rem;
            font-weight: 650;
        }
        [data-testid="stMain"] [data-testid="stPageLink"] a {
            border: 1px solid rgba(98, 154, 227, 0.25);
            border-radius: 0.65rem;
            background: rgba(29, 91, 164, 0.14);
            color: #8bcaff;
            font-weight: 650;
            transition: background 140ms ease, border-color 140ms ease;
        }
        [data-testid="stMain"] [data-testid="stPageLink"] a:hover {
            border-color: rgba(77, 172, 255, 0.6);
            background: rgba(29, 111, 201, 0.24);
        }
        div[data-testid="stAlert"] {
            border-radius: 0.8rem;
        }
        .ff-eyebrow {
            color: #8bcaff;
            font-size: 0.76rem;
            font-weight: 750;
            letter-spacing: 0.14em;
            text-transform: uppercase;
        }
        .ff-hero {
            position: relative;
            overflow: hidden;
            min-height: 300px;
            padding: clamp(1.7rem, 4vw, 3.1rem);
            border: 1px solid rgba(115, 165, 226, 0.25);
            border-radius: 1.2rem;
            background:
                radial-gradient(1px 1px at 9% 18%, #d7edff 99%, transparent),
                radial-gradient(1px 1px at 20% 72%, #d7edff 99%, transparent),
                radial-gradient(1px 1px at 37% 31%, #d7edff 99%, transparent),
                radial-gradient(1px 1px at 59% 16%, #d7edff 99%, transparent),
                radial-gradient(1px 1px at 66% 73%, #d7edff 99%, transparent),
                radial-gradient(ellipse at 85% 130%, rgba(16, 118, 228, 0.88), transparent 34%),
                radial-gradient(ellipse at 75% 125%, rgba(111, 160, 247, 0.5), transparent 25%),
                linear-gradient(112deg, #030916 0%, #08172e 56%, #102849 100%);
            color: #ffffff;
            box-shadow: 0 20px 55px rgba(0, 0, 0, 0.32);
            margin-bottom: 1.2rem;
        }
        .ff-hero:after {
            content: "";
            position: absolute;
            width: clamp(220px, 30vw, 390px);
            height: clamp(220px, 30vw, 390px);
            right: -3%;
            top: -34%;
            border-radius: 50%;
            opacity: 0.8;
            background:
                radial-gradient(circle at 32% 28%, rgba(255,255,255,0.95), transparent 2%),
                radial-gradient(circle at 66% 57%, rgba(83, 171, 255, 0.82), transparent 3%),
                radial-gradient(circle at 33% 65%, rgba(52, 123, 224, 0.75), transparent 18%),
                radial-gradient(circle at 40% 35%, #3975bd 0%, #152c52 50%, #050a17 74%);
            border: 1px solid rgba(137, 196, 255, 0.42);
            box-shadow: inset -26px -16px 55px rgba(0, 0, 0, 0.6), 0 0 65px rgba(37, 140, 255, 0.25);
            pointer-events: none;
        }
        .ff-hero:before {
            content: "";
            position: absolute;
            width: clamp(270px, 36vw, 460px);
            height: clamp(270px, 36vw, 460px);
            right: -5%;
            top: -50%;
            border-radius: 50%;
            border: 1px solid rgba(103, 172, 255, 0.15);
            box-shadow: 0 0 48px rgba(47, 134, 245, 0.12), inset 0 0 34px rgba(47, 134, 245, 0.08);
            transform: rotate(-24deg) scaleY(0.44);
            pointer-events: none;
            animation: ff-orbit 34s linear infinite;
        }
        @keyframes ff-orbit {
            from { transform: rotate(-24deg) scaleY(0.44); }
            to { transform: rotate(336deg) scaleY(0.44); }
        }
        .ff-hero-content {
            position: relative;
            z-index: 1;
            max-width: 720px;
        }
        .ff-hero h1 {
            color: #ffffff;
            font-size: clamp(2.15rem, 5vw, 3.65rem);
            line-height: 1.04;
            margin: 0.7rem 0 0.8rem 0;
            text-shadow: 0 5px 26px rgba(0, 0, 0, 0.26);
        }
        .ff-hero h1 span {
            background: linear-gradient(95deg, #ffffff 12%, #85d4ff 58%, #9a7aff 100%);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .ff-hero p {
            color: #c3d3e8;
            font-size: 1.03rem;
            line-height: 1.65;
            max-width: 660px;
            margin-bottom: 1rem;
        }
        .ff-pill {
            display: inline-block;
            border: 1px solid rgba(166, 205, 255, 0.22);
            border-radius: 99px;
            padding: 0.32rem 0.7rem;
            color: #f3f7fa;
            background: rgba(12, 35, 65, 0.72);
            font-size: 0.78rem;
            margin: 0.2rem 0.25rem 0 0;
        }
        .ff-section-label {
            color: #49b7ff;
            font-size: 0.74rem;
            font-weight: 750;
            letter-spacing: 0.14em;
            text-transform: uppercase;
            margin-bottom: 0.35rem;
        }
        .ff-source {
            color: var(--muted);
            font-size: 0.82rem;
            line-height: 1.5;
        }
        .ff-quote {
            border: 1px solid rgba(75, 156, 235, 0.3);
            border-radius: 0.95rem;
            padding: 1.25rem 1.35rem;
            background:
                radial-gradient(ellipse at 100% 100%, rgba(29, 106, 188, 0.26), transparent 48%),
                linear-gradient(130deg, rgba(17, 31, 55, 0.96), rgba(8, 18, 35, 0.96));
            color: #d9e8ff;
            font-size: 1.08rem;
            font-weight: 620;
            line-height: 1.55;
        }
        .ff-quote small {
            display: block;
            color: #91a8c8;
            font-size: 0.78rem;
            font-weight: 500;
            margin-top: 0.5rem;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid rgba(149, 178, 219, 0.13);
            border-radius: 0.72rem;
            overflow: hidden;
        }
        input, textarea, [data-baseweb="select"] > div {
            border-color: rgba(149, 178, 219, 0.22) !important;
        }
        :focus-visible {
            outline: 2px solid #42b6ff !important;
            outline-offset: 2px;
        }
        @media (max-width: 700px) {
            .block-container { padding-top: 1.1rem; }
            .ff-hero { border-radius: 1rem; }
            .ff-hero:after { right: -34%; top: -38%; opacity: 0.42; }
            .ff-hero:before { right: -42%; top: -40%; }
        }
        @media (prefers-reduced-motion: reduce) {
            *, *:before, *:after {
                animation-duration: 0.01ms !important;
                animation-iteration-count: 1 !important;
                scroll-behavior: auto !important;
                transition-duration: 0.01ms !important;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )
    load_theme()


def _sidebar_brand() -> None:
    with st.sidebar:
        st.markdown(
            """
            <div style="padding: 0.7rem 0.35rem 1.15rem;">
              <div style="width: 46px; height: 46px; display:flex; align-items:center;
                          justify-content:center; border-radius:50%;
                          background:linear-gradient(145deg,#0879e8,#5338ca);
                          box-shadow:0 0 22px rgba(34,137,255,.35); font-size:1.55rem;">
                🔥
              </div>
              <div style="font-size: 1.04rem; font-weight: 760; margin-top: 0.75rem;">
                Flame in Freefall
              </div>
              <div style="font-size: 0.74rem; opacity: 0.74; margin-top: 0.25rem; line-height:1.5;">
                NASA Microgravity Combustion
              </div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown(_navigation_markup(), unsafe_allow_html=True)
        st.markdown("---")
        st.caption("NASA Physical Sciences Informatics")


def page_header(title: str, subtitle: str = "") -> bool:
    """Render the page title + data-status banners.
    Returns False if there is no database at all (page should stop)."""
    _apply_dashboard_style()
    _sidebar_brand()
    if title:
        st.title(title)
    if subtitle:
        st.caption(subtitle)
    if not db.db_available():
        st.error("No database found. Run `python scripts/make_placeholder_db.py` "
                 "for demo data, or copy the real `nasa_combustion.db` into `data/`.")
        return False
    if db.is_placeholder():
        st.warning("PLACEHOLDER DATA: values shown are NOT NASA data. They exist only "
                   "so the interface can be built. Replace with the real "
                   "`data/nasa_combustion.db` before the demo.")
    return True


def no_data(what: str) -> None:
    st.info(f"{what}: Not available in the current database.")
