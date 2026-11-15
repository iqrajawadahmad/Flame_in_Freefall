"""Simplified reference calculators; not spacecraft fire-risk predictions."""
import streamlit as st

from modules import physics_models as pm
from modules.ui import page_header

st.set_page_config(page_title="Physics Calculators", page_icon="🧮", layout="wide")

if page_header("Physics Calculators", "Simplified engineering reference calculations"):
    st.warning(
        "These equations are educational reference models. They are not validated "
        "for spacecraft fire-risk, flame spread, or operational safety decisions."
    )
    model = st.selectbox(
        "Choose a calculation",
        [
            "Radiative heat transfer",
            "Convective heat transfer",
            "Oxygen partial pressure",
            "Flow energy balance",
            "Thermal diffusion timescale",
        ],
    )

    if model == "Radiative heat transfer":
        with st.form("radiation_form"):
            emissivity = st.number_input("Emissivity (0–1)", 0.0, 1.0, 0.8)
            area = st.number_input("Area (m²)", min_value=0.000001, value=0.1)
            surface_temp = st.number_input("Surface temperature (K)", min_value=0.000001, value=500.0)
            surroundings_temp = st.number_input("Surroundings temperature (K)", min_value=0.000001, value=300.0)
            submitted = st.form_submit_button("Calculate heat transfer")
        if submitted:
            result = pm.radiative_heat_transfer(emissivity, area, surface_temp, surroundings_temp)
            st.metric("Net radiative heat transfer", f"{result:.4g} W")

    elif model == "Convective heat transfer":
        with st.form("convection_form"):
            coefficient = st.number_input("Heat-transfer coefficient (W/(m² K))", min_value=0.0, value=10.0)
            area = st.number_input("Area (m²)", min_value=0.000001, value=0.1)
            surface_temp = st.number_input("Surface temperature (K)", min_value=0.000001, value=400.0)
            gas_temp = st.number_input("Gas temperature (K)", min_value=0.000001, value=300.0)
            submitted = st.form_submit_button("Calculate heat transfer")
        if submitted:
            result = pm.convective_heat_transfer(coefficient, area, surface_temp, gas_temp)
            st.metric("Convective heat transfer", f"{result:.4g} W")

    elif model == "Oxygen partial pressure":
        with st.form("oxygen_form"):
            fraction = st.number_input("Oxygen mole fraction (0–1)", 0.0, 1.0, 0.21)
            pressure = st.number_input("Total pressure (Pa)", min_value=0.000001, value=101325.0)
            submitted = st.form_submit_button("Calculate partial pressure")
        if submitted:
            result = pm.oxygen_partial_pressure(fraction, pressure)
            st.metric("Oxygen partial pressure", f"{result:.4g} Pa")

    elif model == "Flow energy balance":
        with st.form("energy_form"):
            mass_flow = st.number_input("Mass flow rate (kg/s)", min_value=0.000001, value=0.01, format="%.6f")
            heat_capacity = st.number_input("Specific heat capacity (J/(kg K))", min_value=0.000001, value=1000.0)
            inlet_temp = st.number_input("Inlet temperature (K)", min_value=0.000001, value=300.0)
            outlet_temp = st.number_input("Outlet temperature (K)", min_value=0.000001, value=310.0)
            submitted = st.form_submit_button("Calculate heat rate")
        if submitted:
            result = pm.energy_balance_heat(mass_flow, heat_capacity, inlet_temp, outlet_temp)
            st.metric("Heat rate", f"{result:.4g} W")

    else:
        with st.form("diffusion_form"):
            length = st.number_input("Characteristic length (m)", min_value=0.000001, value=0.01)
            diffusivity = st.number_input("Thermal diffusivity (m²/s)", min_value=0.000001, value=1e-6, format="%.6g")
            submitted = st.form_submit_button("Calculate timescale")
        if submitted:
            result = pm.diffusion_timescale(length, diffusivity)
            st.metric("Characteristic diffusion timescale", f"{result:.4g} s")
    st.caption("Calculations use the shared formulas in modules/physics_models.py and SI units.")
