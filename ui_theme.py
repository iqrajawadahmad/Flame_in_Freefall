"""Reusable NASA-inspired Streamlit theme and dashboard components."""
from __future__ import annotations

from html import escape
from typing import Iterable, Union

import streamlit as st


def load_theme() -> None:
    """Apply shared presentation styles across the Streamlit application."""
    st.markdown(
        """
        <style>
        :root {
            --ff-ink: #f1f5ff;
            --ff-muted: #b5c6e5;
            --ff-line: rgba(99, 139, 196, 0.3);
            --ff-blue: #35bfff;
            --ff-purple: #9455ff;
        }
        .stApp {
            background:
                radial-gradient(ellipse at 82% 0%, rgba(35, 116, 255, 0.14), transparent 36%),
                radial-gradient(ellipse at 5% 40%, rgba(112, 69, 245, 0.08), transparent 35%),
                #071329;
            color: var(--ff-ink);
            font-family: Inter, "Segoe UI", sans-serif;
        }
        .block-container {
            max-width: 1500px;
            padding: 1.6rem 2.5rem 4rem;
        }
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #071329 0%, #102747 100%);
            border-right: 1px solid #203c65;
        }
        h1, h2, h3 {
            color: var(--ff-ink) !important;
            font-weight: 700 !important;
        }
        .hero {
            position: relative;
            overflow: hidden;
            background:
                radial-gradient(circle at 85% 30%, rgba(35, 116, 255, 0.3), transparent 35%),
                linear-gradient(120deg, #102747, #111a3b);
            border: 1px solid #284775;
            border-radius: 22px;
            padding: clamp(1.7rem, 4vw, 2.8rem);
            margin-bottom: 1.4rem;
            box-shadow: 0 18px 48px rgba(0, 0, 0, 0.24);
        }
        .hero:after {
            content: "";
            position: absolute;
            width: clamp(230px, 30vw, 380px);
            height: clamp(230px, 30vw, 380px);
            top: -38%;
            right: -3%;
            border: 1px solid rgba(126, 187, 255, 0.28);
            border-radius: 50%;
            background: radial-gradient(circle at 34% 30%, #4b96e5, #15294b 54%, #071329 76%);
            box-shadow: inset -22px -18px 48px rgba(0, 0, 0, 0.56), 0 0 58px rgba(37, 140, 255, 0.2);
            pointer-events: none;
        }
        .hero-content {
            position: relative;
            z-index: 1;
            max-width: 740px;
        }
        .hero-label {
            color: var(--ff-blue);
            font-size: 0.75rem;
            font-weight: 750;
            letter-spacing: 0.2em;
        }
        .hero-title {
            margin: 0.8rem 0;
            color: white;
            font-size: clamp(2.4rem, 5vw, 3.8rem);
            font-weight: 800;
            letter-spacing: -0.045em;
            line-height: 1.05;
        }
        .hero-title span {
            background: linear-gradient(90deg, #35bfff, #9455ff);
            background-clip: text;
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
        }
        .hero-description {
            max-width: 660px;
            color: var(--ff-muted);
            font-size: 1rem;
            line-height: 1.7;
        }
        .hero-detail {
            display: inline-block;
            margin: 0.35rem 0.4rem 0 0;
            padding: 0.35rem 0.72rem;
            border: 1px solid rgba(166, 205, 255, 0.22);
            border-radius: 99px;
            background: rgba(12, 35, 65, 0.72);
            color: #f3f7fa;
            font-size: 0.78rem;
        }
        .kpi-card {
            min-height: 112px;
            padding: 1.15rem 1.25rem;
            border: 1px solid #29446b;
            border-radius: 17px;
            background: linear-gradient(145deg, #142744, #0d1930);
            box-shadow: 0 8px 25px rgba(0, 0, 0, 0.15);
            transition: transform 180ms ease, border-color 180ms ease, box-shadow 180ms ease;
        }
        .kpi-card:hover {
            transform: translateY(-3px);
            border-color: #328dff;
            box-shadow: 0 10px 30px rgba(30, 120, 255, 0.15);
        }
        .kpi-label {
            color: #a9bcd9;
            font-size: 0.82rem;
        }
        .kpi-value {
            margin-top: 0.55rem;
            color: #fff;
            font-size: clamp(1.55rem, 3vw, 1.9rem);
            font-weight: 800;
            line-height: 1.2;
        }
        .research-card {
            padding: 1.25rem 1.4rem;
            border: 1px solid #263f65;
            border-radius: 17px;
            background:
                radial-gradient(ellipse at 100% 100%, rgba(29, 106, 188, 0.16), transparent 48%),
                #101f39;
            box-shadow: 0 8px 24px rgba(0, 0, 0, 0.14);
        }
        .research-card h3 {
            margin: 0 0 0.65rem;
            font-size: 1.05rem;
        }
        .research-card p {
            margin: 0;
            color: #b8c8e0;
            line-height: 1.8;
            white-space: pre-line;
        }
        .research-card small {
            display: block;
            margin-top: 0.8rem;
            color: #91a8c8;
            line-height: 1.5;
        }
        [data-testid="stMetric"],
        [data-testid="stVerticalBlockBorderWrapper"] {
            border-color: var(--ff-line);
            border-radius: 0.9rem;
        }
        [data-testid="stDataFrame"] {
            border: 1px solid #29446b;
            border-radius: 12px;
            overflow: hidden;
        }
        .stButton > button, .stDownloadButton > button, [data-testid="stLinkButton"] a {
            border-radius: 0.7rem;
            font-weight: 650;
        }
        .stTabs [data-baseweb="tab"] {
            color: #afc2e0;
        }
        .stTabs [aria-selected="true"] {
            color: #42b7ff !important;
            border-bottom-color: #42b7ff !important;
        }
        :focus-visible {
            outline: 2px solid #42b6ff !important;
            outline-offset: 2px;
        }
        @media (max-width: 700px) {
            .block-container { padding: 1.1rem 1rem 3rem; }
            .hero { border-radius: 16px; }
            .hero:after { right: -38%; top: -42%; opacity: 0.45; }
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


def render_hero(
    eyebrow: str,
    title: str,
    highlight: str,
    description: str,
    details: Iterable[str] = (),
) -> None:
    """Render a space-inspired hero with optional data-backed detail pills."""
    detail_markup = "".join(
        f'<span class="hero-detail">{escape(str(detail))}</span>'
        for detail in details
    )
    st.markdown(
        f"""
        <section class="hero">
          <div class="hero-content">
            <div class="hero-label">{escape(eyebrow)}</div>
            <div class="hero-title">{escape(title)} <span>{escape(highlight)}</span></div>
            <div class="hero-description">{escape(description)}</div>
            {detail_markup}
          </div>
        </section>
        """,
        unsafe_allow_html=True,
    )


def render_kpi(label: str, value: Union[str, int], icon: str) -> None:
    """Render one KPI card; callers supply values from the actual dataset."""
    st.markdown(
        f"""
        <div class="kpi-card">
          <div class="kpi-label">{escape(icon)} {escape(label)}</div>
          <div class="kpi-value">{escape(str(value))}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_research_card(title: str, description: str, meta: str = "") -> None:
    """Render a research card while escaping all record-provided text."""
    meta_markup = f"<small>{escape(meta)}</small>" if meta else ""
    st.markdown(
        f"""
        <article class="research-card">
          <h3>{escape(title)}</h3>
          <p>{escape(description)}</p>
          {meta_markup}
        </article>
        """,
        unsafe_allow_html=True,
    )
