"""Physics models (Phase 4 interface).

ALL pages must call these functions. Never re-implement a formula in a page.
Units are SI throughout: K, Pa, m, s, kg, W, J, mol.

NOTE FOR THE TEAM: these are working reference implementations so the
Calculators page runs today. If the Phase 4 owner delivers their own
physics_models.py, keep the SAME function names/signatures (or tell the
dashboard owner what changed) and replace this file.

These are simplified engineering calculators, NOT validated spacecraft
fire-risk or flame-spread prediction models.
"""
from __future__ import annotations

SIGMA = 5.670374419e-8  # Stefan-Boltzmann constant, W/(m^2 K^4)
R_UNIVERSAL = 8.314462618  # J/(mol K)


def _positive(name: str, value: float, allow_zero: bool = False) -> None:
    if value is None:
        raise ValueError(f"{name} is required")
    if value < 0 or (value == 0 and not allow_zero):
        raise ValueError(f"{name} must be {'>= 0' if allow_zero else '> 0'} (got {value})")


# ---- A. Convective heat transfer -------------------------------------------
def convective_heat_transfer(h: float, area: float, T_s: float, T_inf: float) -> float:
    """Q = h * A * (T_s - T_inf)   [W]
    h: W/(m^2 K), area: m^2, temperatures in K (absolute).
    Positive Q = heat flows from surface to gas."""
    _positive("h", h, allow_zero=True)
    _positive("area", area)
    _positive("T_s (K)", T_s)
    _positive("T_inf (K)", T_inf)
    return h * area * (T_s - T_inf)


# ---- B. Energy balance on flowing air ---------------------------------------
def energy_balance_heat(m_dot: float, cp: float, T_in: float, T_out: float) -> float:
    """Q = m_dot * cp * (T_out - T_in)   [W]   m_dot: kg/s, cp: J/(kg K)."""
    _positive("m_dot", m_dot)
    _positive("cp", cp)
    _positive("T_in (K)", T_in)
    _positive("T_out (K)", T_out)
    return m_dot * cp * (T_out - T_in)


def air_temperature_rise(Q: float, m_dot: float, cp: float) -> float:
    """dT = Q / (m_dot * cp)   [K]"""
    _positive("m_dot", m_dot)
    _positive("cp", cp)
    return Q / (m_dot * cp)


def energy_over_time(Q: float, duration: float) -> float:
    """E = Q * t   [J]"""
    _positive("duration", duration, allow_zero=True)
    return Q * duration


# ---- C. Thermal diffusion ----------------------------------------------------
def thermal_diffusivity(k: float, rho: float, cp: float) -> float:
    """alpha = k / (rho * cp)   [m^2/s]"""
    _positive("k", k)
    _positive("rho", rho)
    _positive("cp", cp)
    return k / (rho * cp)


def diffusion_timescale(length: float, diffusivity: float) -> float:
    """t_d ~ L^2 / D   [s]   (works for thermal alpha or mass diffusivity D_AB)."""
    _positive("length", length)
    _positive("diffusivity", diffusivity)
    return length ** 2 / diffusivity


# ---- D. Mass diffusion (Fick's first law, 1-D) -----------------------------
def fick_flux(D_AB: float, C_high: float, C_low: float, distance: float) -> float:
    """|J_A| = D_AB * (C_high - C_low) / distance   [mol/(m^2 s)]
    C in mol/m^3. Flux is directed from high to low concentration."""
    _positive("D_AB", D_AB)
    _positive("distance", distance)
    _positive("C_high", C_high, allow_zero=True)
    _positive("C_low", C_low, allow_zero=True)
    return D_AB * (C_high - C_low) / distance


def molar_concentration_ideal_gas(y: float, P_total: float, T: float) -> float:
    """C_A = y_A * P / (R T)   [mol/m^3]   (ideal gas)."""
    if not 0 <= y <= 1:
        raise ValueError("mole fraction y must be between 0 and 1")
    _positive("P_total (Pa)", P_total)
    _positive("T (K)", T)
    return y * P_total / (R_UNIVERSAL * T)


# ---- Oxygen partial pressure ------------------------------------------------
def oxygen_partial_pressure(y_O2: float, P_total: float) -> float:
    """P_O2 = y_O2 * P_total   [Pa]"""
    if not 0 <= y_O2 <= 1:
        raise ValueError("oxygen mole fraction must be between 0 and 1")
    _positive("P_total (Pa)", P_total)
    return y_O2 * P_total


# ---- Thermal radiation ------------------------------------------------------
def radiative_heat_transfer(emissivity: float, area: float, T_s: float, T_surr: float) -> float:
    """Q = eps * sigma * A * (T_s^4 - T_surr^4)   [W]   Kelvin only."""
    if not 0 <= emissivity <= 1:
        raise ValueError("emissivity must be between 0 and 1")
    _positive("area", area)
    _positive("T_s (K)", T_s)
    _positive("T_surr (K)", T_surr)
    return emissivity * SIGMA * area * (T_s ** 4 - T_surr ** 4)
