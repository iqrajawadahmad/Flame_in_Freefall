"""Build the REAL database  data/nasa_combustion.db  from the NASA PSI files.

Usage:   python scripts/build_real_db.py [--raw data/raw/Free_Fall_Data]

Reads (never modifies) the PSI folders:
  * ISA metadata  (i_Investigation.txt)  -> investigations, resources (publications)
  * experimental tables (CSV)            -> experimental_runs (one row per test x parameter)
                                            parameters        (one summary row per investigation x parameter)
  * ACME final report (PDF, pp. 25-27)   -> findings (paraphrased, with page numbers)

Rules enforced (see README):
  1. Missing / non-numeric data is stored as NULL, never 0 and never an average.
  2. Values are converted to standard units ONLY from the unit stated in the source column;
     the original text and unit are always kept.
  3. Parameters with different physical meaning get different names (e.g. ACME normal vs
     inverse flames, FLEX methanol vs heptane responses), so they are never pooled.
  4. Every data-quality decision is written to data/processed_data/data_quality_log.csv.
"""
from __future__ import annotations

import argparse
import csv
import io
import re
import sqlite3
import statistics
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from modules.data_processing import convert  # noqa: E402
from modules.database import REAL_DB, SCHEMA  # noqa: E402

QUALITY_LOG: list[dict] = []


def log(investigation, source, issue, action, n=1):
    QUALITY_LOG.append(dict(investigation_id=investigation, source=source, issue=issue,
                            action=action, rows_affected=n))


# --------------------------------------------------------------------------
# Generic helpers
# --------------------------------------------------------------------------
MISSING_TOKENS = {"", "nan", "none", "n/a", "na", "-", "–", "—", "\ufffd"}


def parse_number(text):
    """-> (value, low, high, flag). Never invents a number.
    '~6' -> 6 (flag approximate); '21.5 - 21.7' -> midpoint + low/high (flag range);
    'RAMP', 'LOW O2', '–' -> None (flag non-numeric)."""
    if text is None:
        return None, None, None, "empty"
    t = str(text).strip()
    if t.lower() in MISSING_TOKENS:
        return None, None, None, "empty" if t == "" or t.lower() == "nan" else f"non-numeric '{t}'"
    approx = t.startswith("~")
    t2 = t.lstrip("~").strip()
    m = re.fullmatch(r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*-\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", t2)
    if m:
        lo, hi = float(m.group(1)), float(m.group(2))
        return (lo + hi) / 2, lo, hi, f"range {lo}-{hi} in source; midpoint stored, low/high kept"
    try:
        v = float(t2)
    except ValueError:
        return None, None, None, f"non-numeric '{t}'"
    return v, None, None, "approximate value (~) in source" if approx else ""


def read_csv_any(path: Path) -> pd.DataFrame:
    raw = path.read_bytes()
    for enc in ("utf-8", "cp1252"):
        try:
            text = raw.decode(enc)
            break
        except UnicodeDecodeError:
            continue
    df = pd.read_csv(io.StringIO(text), dtype=str, keep_default_na=False)
    df.columns = [c.strip() for c in df.columns]
    return df, enc


def read_isa(path: Path) -> dict:
    text = path.read_text(encoding="utf-8", errors="replace")
    d = {}
    for row in csv.reader(io.StringIO(text), delimiter="\t", quotechar='"'):
        if row and row[0].strip():
            d[row[0].strip()] = [c.strip() for c in row[1:]]
    return d


def first(isa, key):
    vals = isa.get(key) or []
    v = vals[0].strip().strip('"').strip() if vals else ""
    return v or None


# --------------------------------------------------------------------------
# Investigations + publications (ISA metadata)
# --------------------------------------------------------------------------
SOURCES = {
    "PSI-10": ("PSI_10_ACME/PSI-10_metadata_PSI-10-ISA/i_Investigation.txt", None),
    "PSI-60": ("PSI-60_SPICE/i_Investigation.txt", "SPICE"),
    "PSI-62": ("PSI-62_BASS/i_Investigation.txt", "BASS"),
    "PSI-69": ("PSI-69_FLEX/i_Investigation.txt", None),
    "PSI-98": ("PSI_98_SAFFIRE-1/PSI-98_metadata_PSI-166_SAFFIRE-I/i_Investigation.txt", None),
}
REQUIRED_EXPERIMENT_TABLES = (
    "PSI_10_ACME/PSI-10_Experimental table_Flame Design_Normal Flame.csv",
    "PSI_10_ACME/PSI-10_Experimental table_Flame Design_Inverse Flame.csv",
    "PSI-69_FLEX/PSI-69_Experimental table_FLEX.csv",
    "PSI_98_SAFFIRE-1/PSI-98_Experimental table_SAFFIRE-1.csv",
)


def missing_required_sources(raw: Path) -> list[Path]:
    """Return required source files absent from the raw PSI data directory."""
    required = [rel for rel, _ in SOURCES.values()]
    required.extend(REQUIRED_EXPERIMENT_TABLES)
    return [raw / rel for rel in required if not (raw / rel).is_file()]


NOTES = {
    "PSI-60": "GROUND study that analyses SPICE flight data (image processing + soot modelling). "
              "It is not the SPICE flight experiment itself and has no experimental table.",
    "PSI-62": "GROUND modelling study compared against BASS/BASS-II imagery. No experimental table.",
    "PSI-98": "Source folder is named PSI-166_SAFFIRE-I but the study identifier inside the ISA file is "
              "PSI-98 (used here). The ISA dates (2001-2008) do not describe the flight and are not used.",
}


def build_investigations(raw: Path):
    inv, pubs = [], []
    for inv_id, (rel, acro_fallback) in SOURCES.items():
        isa = read_isa(raw / rel)
        sid = first(isa, "Study Identifier")
        assert sid == inv_id, f"{rel}: study id {sid!r} != {inv_id!r}"
        acro = first(isa, "Comment[Investigation Acronym]")
        if not acro and acro_fallback:
            acro = acro_fallback
            log(inv_id, rel, "Investigation Acronym is blank", f"used '{acro}' from the study-design descriptor")
        doi = first(isa, "Comment[DOI]")
        pi = None
        roles = isa.get("Study Person Roles", [])
        for i, role in enumerate(roles):
            if "Principal Investigator" in role:
                pi = f"{isa['Study Person First Name'][i]} {isa['Study Person Last Name'][i]}".strip()
        inv.append((inv_id, first(isa, "Study Title"), acro, first(isa, "Comment[Research Area]"),
                    first(isa, "Comment[Objective]"), first(isa, "Comment[Flight Platform]"), doi,
                    f"https://doi.org/{doi}" if doi else None,
                    first(isa, "Comment[Project Type]"), first(isa, "Comment[SubResearch Area]"),
                    first(isa, "Comment[Experiment Hardware]"), first(isa, "Comment[Hypothesis]"),
                    pi, NOTES.get(inv_id)))
        if not first(isa, "Comment[Flight Platform]"):
            log(inv_id, rel, "Flight Platform blank (ground investigation)", "stored NULL -> shown as Not available")
        titles = isa.get("Study Publication Title", [])
        links = isa.get("Comment[Study Publication Link]", [])
        dois = isa.get("Study Publication DOI", [])
        for i, t in enumerate(titles):
            if not t:
                continue
            url = links[i] if i < len(links) and links[i] else (
                f"https://doi.org/{dois[i]}" if i < len(dois) and dois[i] else None)
            pubs.append((inv_id, "Publication", t, url, None))
    return inv, pubs


# --------------------------------------------------------------------------
# Experimental tables -> run-level rows
# --------------------------------------------------------------------------
# A spec: (parameter_name, source column, source_unit, standard_unit, converter, type, zero_is_missing)
def _id(v):
    return v


def _pct(v):
    return v / 100.0


def spec(name, col, src_unit, std_unit, conv, ptype, zero_missing=False):
    return dict(name=name, col=col, src_unit=src_unit, std_unit=std_unit, conv=conv,
                ptype=ptype, zero_missing=zero_missing)


FRAC = "-"
K = lambda unit, kind: (lambda v: convert(v, unit, kind))  # noqa: E731

FLEX_SPECS = [  # (fuel-specific suffix flag in position 0)
    (False, spec("Ambient pressure", "Ambient pressure; mmHg", "mmHg", "Pa", K("mmHg", "pressure"), "condition", True)),
    (False, spec("Ambient oxygen mole fraction", "O initial ambient composition; mole fraction", "mole fraction", FRAC, _id, "condition")),
    (False, spec("Ambient nitrogen mole fraction", "N initial ambient composition; mole fraction", "mole fraction", FRAC, _id, "condition")),
    (False, spec("Ambient carbon dioxide mole fraction", "CO initial ambient composition; mole fraction", "mole fraction", FRAC, _id, "condition")),
    (False, spec("Ambient helium mole fraction", "He initial ambient composition; mole fraction", "mole fraction", FRAC, _id, "condition")),
    (False, spec("Droplet initial diameter", "Droplet initial diameter; mm", "mm", "m", K("mm", "length"), "condition")),
    (True, spec("Visible flame extinction diameter", "Visible flame extinction diameter; mm", "mm", "m", K("mm", "length"), "measurement", True)),
    (True, spec("Burning rate", "Burning rate; mm", "mm", "unverified (source label: mm)", _id, "measurement")),
    (True, spec("Burn time", "Burn time; s", "s", "s", _id, "measurement")),
]

ACME_COMMON = [
    spec("Ambient pressure", "pinit (atm)", "atm", "Pa", K("atm", "pressure"), "condition"),
    spec("Ambient pressure (final)", "pfinal (atm)", "atm", "Pa", K("atm", "pressure"), "measurement"),
]
ACME_NORMAL = [
    spec("Ambient oxygen mole fraction", "XO2 (init)", "mole fraction", FRAC, _id, "condition"),
    spec("Burner-supply fuel mole fraction", "Xfuel", "mole fraction", FRAC, _id, "condition"),
    spec("Fuel mass flow rate (normal flames)", "mfuel (mg/s)", "mg/s", "mg/s", _id, "condition"),
    spec("Nitrogen mass flow rate (normal flames)", "mN2 (mg/s)", "mg/s", "mg/s", _id, "condition"),
    spec("Total reactant mass flow rate (normal flames)", "mtot (mg/s)", "mg/s", "mg/s", _id, "condition"),
    spec("Stoichiometric mixture fraction (normal flames)", "mean Zst", "-", FRAC, _id, "derived"),
    spec("Adiabatic flame temperature (normal flames)", "Tad (K)", "K", "K", _id, "derived"),
]
ACME_INVERSE = [
    spec("Burner-supply oxygen mole fraction", "XO2", "mole fraction", FRAC, _id, "condition"),
    spec("Ambient fuel mole fraction", "XC2H4 initial", "mole fraction", FRAC, _id, "condition"),
    spec("Oxygen mass flow rate (inverse flames)", "mO2 (mg/s)", "mg/s", "mg/s", _id, "condition"),
    spec("Nitrogen mass flow rate (inverse flames)", "mN2 (mg/s)", "mg/s", "mg/s", _id, "condition"),
    spec("Total reactant mass flow rate (inverse flames)", "mtot (mg/s)", "mg/s", "mg/s", _id, "condition"),
    spec("Stoichiometric mixture fraction (inverse flames)", "mean Zst", "-", FRAC, _id, "derived"),
    spec("Adiabatic flame temperature (inverse flames)", "Tad (K)", "K", "K", _id, "derived"),
]
SAFFIRE_SPECS = [
    spec("Sample thickness", "Sample Thickness (cm)", "cm", "m", K("cm", "length"), "condition"),
    spec("Sample length", "Sample Length (cm)", "cm", "m", K("cm", "length"), "condition"),
    spec("Sample width", "Sample Width (cm)", "cm", "m", K("cm", "length"), "condition"),
    spec("Airflow velocity", "Air Flow (cm/s)", "cm/s", "m/s", K("cm/s", "velocity"), "condition"),
    spec("Ambient oxygen mole fraction", "Percent O2", "%", FRAC, _pct, "condition"),
    spec("Ignition power", "Ignition Power (W)", "W", "W", _id, "condition"),
    spec("Ignition time", "Ignition Time (s)", "s", "s", _id, "condition"),
    spec("Burn time", "Burn Time (s)", "s", "s", _id, "measurement"),
]


def run_rows(inv_id, source, run_id, row, specs, name_suffix="", extra_flag=""):
    """Convert one table row to run-level records."""
    out = []
    for s in specs:
        raw = row.get(s["col"], "")
        v, lo, hi, flag = parse_number(raw)
        flags = [f for f in (flag, extra_flag) if f and f != "empty"]
        if v is not None and s["zero_missing"] and v == 0:
            v, lo, hi = None, None, None
            flags.append("source value 0 is physically meaningless here; treated as Not available")
        if v is not None:
            v = s["conv"](v)
            lo = s["conv"](lo) if lo is not None else None
            hi = s["conv"](hi) if hi is not None else None
        out.append(dict(investigation_id=inv_id, run_id=run_id,
                        parameter_name=s["name"] + name_suffix, value=v, value_low=lo,
                        value_high=hi, unit=s["std_unit"], original_text=raw if raw != "" else None,
                        original_unit=s["src_unit"], text_value=None, quality_flag="; ".join(flags) or None,
                        _ptype=s["ptype"], _src=f"{source}, column '{s['col']}'"))
    return out


def text_row(inv_id, run_id, name, text, source):
    t = (text or "").strip() or None
    return dict(investigation_id=inv_id, run_id=run_id, parameter_name=name, value=None, value_low=None,
                value_high=None, unit=None, original_text=t, original_unit=None, text_value=t,
                quality_flag=None, _ptype="condition", _src=source)


def build_flex(raw: Path):
    rel = "PSI-69_FLEX/PSI-69_Experimental table_FLEX.csv"
    df, enc = read_csv_any(raw / rel)
    inv = "PSI-69"
    if enc != "utf-8":
        log(inv, rel, f"file is {enc}, not UTF-8 (en-dash/missing-value marker bytes)", "decoded as cp1252")
    log(inv, rel, "Column headers 'O', 'N', 'CO' lost their subscript 2",
        "interpreted as O2, N2, CO2 (mole fractions sum to 0.98-1.01 for every test, supporting this); "
        "He kept as helium. CONFIRM with the FLEX data dictionary.", len(df))
    log(inv, rel, "Column 'Burning rate; mm' has a length unit for a rate",
        "values kept as-is; unit stored as 'unverified (source label: mm)'. A droplet burning rate is normally "
        "mm^2/s - verify before using the numbers.", len(df))
    log(inv, rel, "Ambient pressure column is mmHg; not stated whether initial", "treated as ambient pressure "
        "(same meaning as ACME 'pinit')", len(df))
    dup = df["FLEX Identifier"][df["FLEX Identifier"].duplicated(keep=False)]
    if len(dup):
        log(inv, rel, f"FLEX Identifier repeated: {sorted(set(dup))}", "kept both rows (Test # is unique); "
            "run_id uses Test #", len(dup))
    rows = []
    for _, r in df.iterrows():
        run = f"FLEX-{int(float(r['FLEX Test #'])):03d}"
        fuel = r["Fuel"].strip()
        rows += [text_row(inv, run, "Fuel", fuel, rel),
                 text_row(inv, run, "Test identifier", r["FLEX Identifier"], rel),
                 text_row(inv, run, "Test date (GMT)", f"{r['Test Date']} {r['Test GMT']}".strip(), rel),
                 text_row(inv, run, "Test end", r["Test end"], rel)]
        for fuel_specific, s in FLEX_SPECS:
            rows += run_rows(inv, rel, run, r, [s], f" ({fuel})" if fuel_specific else "")
    return rows


def build_acme(raw: Path):
    inv, base = "PSI-10", "PSI_10_ACME/"
    rows = []
    for fname, specs, ftype in (
        ("PSI-10_Experimental table_Flame Design_Normal Flame.csv", ACME_COMMON + ACME_NORMAL, "Normal"),
        ("PSI-10_Experimental table_Flame Design_Inverse Flame.csv", ACME_COMMON + ACME_INVERSE, "Inverse"),
    ):
        rel = base + fname
        df, _ = read_csv_any(raw / rel)
        n_ramp = 0
        for _, r in df.iterrows():
            run = r["Test"].strip()
            rows += [text_row(inv, run, "Flame type", ftype, rel),
                     text_row(inv, run, "Test day", r["Day"], rel)]
            fuel = r["Fuel"].strip() if "Fuel" in r else "C2H4"
            rows.append(text_row(inv, run, "Fuel", fuel, rel))
            tokens = [r.get(c, "") for c in ("Xfuel", "XO2", "mtot (mg/s)")]
            is_ramp = any(str(t).strip().upper() in ("RAMP", "RAMPED", "LOW O2") for t in tokens)
            n_ramp += is_ramp
            new = run_rows(inv, rel, run, r, specs,
                           extra_flag="ramped/non-steady test: reactant composition not a single value" if is_ramp else "")
            # propane day: fuel-specific flow must not be pooled with ethylene
            if fuel != "C2H4":
                for x in new:
                    if x["parameter_name"].startswith(("Fuel mass flow", "Burner-supply fuel")):
                        x["quality_flag"] = ((x["quality_flag"] + "; ") if x["quality_flag"] else "") + f"fuel is {fuel}"
            rows += new
        log(inv, rel, "Tests with 'RAMP'/'RAMPED'/'LOW O2' instead of numbers", "stored NULL (not 0); "
            "kept in run table with flag; pressure columns of those tests are numeric and kept", n_ramp)
    n_prop = sum(1 for r in rows if r["parameter_name"] == "Fuel" and r["text_value"] == "C3H8")
    log(inv, base, "Normal-flame table contains propane (C3H8) tests", "excluded from fuel-based summary values "
        "(median uses ethylene only); kept in run table", n_prop)
    log(inv, base, "Inverse table 'XO2' is the burner-SUPPLY oxygen fraction, normal table 'XO2 (init)' is the "
        "AMBIENT oxygen fraction", "stored under different parameter names so they are never pooled", 1)
    return rows


def build_saffire(raw: Path):
    rel = "PSI_98_SAFFIRE-1/PSI-98_Experimental table_SAFFIRE-1.csv"
    df, _ = read_csv_any(raw / rel)
    inv, rows = "PSI-98", []
    samples = df[df["Sample Number"].str.match(r"^S\d+$")]
    log(inv, rel, "Rows 'F1C1/F1C2', 'F2C1/F2C2' are pre-test flow-visualisation file labels, not samples",
        "excluded from run data", len(df) - len(samples))
    log(inv, rel, "Sample thickness 0.37 'cm' (3.7 mm) is implausible for a fabric sample",
        "converted using the stated unit (cm->m) but flagged: the source label may really be mm - verify",
        len(samples))
    for _, r in samples.iterrows():
        run = r["Sample Number"].strip()
        rows += [text_row(inv, run, "Material", r["Material"], rel),
                 text_row(inv, run, "Flow direction", r["Flow Direction"], rel)]
        new = run_rows(inv, rel, run, r, SAFFIRE_SPECS)
        for x in new:
            if x["parameter_name"] == "Sample thickness":
                x["quality_flag"] = "unit label (cm) looks implausible; verify (could be mm)"
        rows += new
    log(inv, rel, "Percent O2 given as a range ('21.5 - 21.7') and as '~ 21.5'",
        "range stored with low/high and midpoint; '~' value stored with approximate flag", 2)
    return rows


# --------------------------------------------------------------------------
# Investigation-level summary (what the dashboard compares)
# --------------------------------------------------------------------------
def summarise(runs: list[dict]) -> list[tuple]:
    df = pd.DataFrame(runs)
    df = df[df["unit"].notna()]  # numeric parameters only
    out = []
    for (inv, name, unit), g in df.groupby(["investigation_id", "parameter_name", "unit"], sort=True):
        # propane tests are excluded from fuel-based ACME summaries
        if g["quality_flag"].fillna("").str.contains("fuel is C3H8").any():
            g = g[~g["quality_flag"].fillna("").str.contains("fuel is C3H8")]
        vals = g["value"].dropna()
        n = len(vals)
        ptype = g["_ptype"].iloc[0]
        src = g["_src"].iloc[0]
        flags = sorted({f for fl in g["quality_flag"].dropna() for f in fl.split("; ")})
        lows = pd.concat([g["value_low"].dropna(), vals]).min() if n or g["value_low"].notna().any() else None
        highs = pd.concat([g["value_high"].dropna(), vals]).max() if n or g["value_high"].notna().any() else None
        if n == 0:
            value, stat = None, "none"
        elif vals.nunique() == 1 and g["value_low"].isna().all():
            value, stat = float(vals.iloc[0]), "single" if n == 1 else "constant"
        elif n >= 3:
            value, stat = float(statistics.median(vals)), "median"
        else:  # 2 differing values: any single number would be an invention
            value, stat = None, "no single value"
        orig = None
        if value is not None:
            ov = [parse_number(t)[0] for t in g.loc[g["value"].notna(), "original_text"]]
            ov = [x for x in ov if x is not None]
            if stat == "median" and ov:
                orig = float(statistics.median(ov))
            elif ov and len(set(ov)) == 1:
                orig = float(ov[0])
        ref = f"{src}; {stat} of {n} test(s)"
        if n > 1:
            ref += f", range {lows:.4g}-{highs:.4g} {unit}"
        out.append((inv, name, value, unit, ptype, orig, g["original_unit"].iloc[0], ref, stat, int(n),
                    None if lows is None or pd.isna(lows) else float(lows),
                    None if highs is None or pd.isna(highs) else float(highs),
                    "; ".join(flags)[:500] or None))
    return out


# --------------------------------------------------------------------------
# Findings (ACME final report) - paraphrased, with page numbers (PDF page = printed page)
# --------------------------------------------------------------------------
ACME_REPORT = "ACME/Flame Design Final Report (2023), PSI-10_Reports_FinalRpt_ACMEFlameDesign.pdf"
ACME_FINDINGS = [
    ("Across all ISS tests, normal and inverse ethylene spherical diffusion flames extinguished at one critical "
     "temperature, 1130 K. The matching mass-flux thresholds were 0.2 g/m2-s of fuel (normal flames) and "
     "0.68 g/m2-s of oxygen (inverse flames).", 26, "Sec. 4.D"),
    ("Flame growth in microgravity, which ends in radiative extinction once the critical point is reached, is "
     "attributed to the diffusion-limited system developing toward steady state while radiation lowers flame "
     "temperature and transport properties (radiation-induced growth).", 26, "Sec. 4.D"),
    ("Steady-state microgravity spherical diffusion flames can exist despite radiation heat loss if the steady "
     "flame is smaller than the radiative-extinction size and develops fast enough that it stays above 1130 K. "
     "ISS flames showed steady-state behaviour for up to 870 s; the diffusion-limited time scale is on the "
     "order of 100,000 s.", 25, "Sec. 4.C"),
    ("ISS burn times ranged from 28 to 336 s. Flames grow after ignition and peak gas temperature generally "
     "falls with time. Before full extinction a flame may oscillate (partial extinction and re-formation) with "
     "growing amplitude.", 26, "Sec. 4.C"),
    ("Tested envelope (normal flames): ambient O2 mole fraction 0.2-0.38, total mass flow 0.6-12.2 mg/s, "
     "adiabatic flame temperature 2000-2800 K. Inverse flames: ambient fuel mole fraction 0.08-0.12, total mass "
     "flow 2.3-11.3 mg/s, adiabatic flame temperature 2080-2590 K.", 25, "Sec. 4.C"),
    ("Test limits: for safety, O2 mole fraction was capped at 40% (normal flames) and C2H4 at 65% (inverse "
     "flames); CH4 fuel and CO2 diluent tests were planned but not allowed. Co-flow burner tests are suggested "
     "as follow-on work.", 27, "Sec. 5"),
]


def build_findings():
    return [("PSI-10", t, "Unclassified", f"{ACME_REPORT}, {sec}, p. {pg}", pg) for t, pg, sec in ACME_FINDINGS]


def build_file_resources(raw: Path):
    res = []
    kinds = {".pdf": "Report (PDF)", ".csv": "Dataset (CSV)", ".txt": "ISA metadata"}
    owner = {"PSI_10": "PSI-10", "PSI-60": "PSI-60", "PSI-62": "PSI-62", "PSI-69": "PSI-69", "PSI_98": "PSI-98"}
    for f in sorted(raw.rglob("*")):
        if f.is_file() and f.suffix.lower() in kinds and not f.name.startswith("s_"):
            inv = next(v for k, v in owner.items() if f.relative_to(raw).parts[0].startswith(k))
            res.append((inv, kinds[f.suffix.lower()], f.name, None, None))
    return res


# --------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default=str(ROOT / "data" / "raw" / "Free_Fall_Data"))
    ap.add_argument("--out", default=str(REAL_DB))
    a = ap.parse_args()
    raw, out = Path(a.raw), Path(a.out)
    missing = missing_required_sources(raw)
    if missing:
        paths = "\n".join(f"  - {path}" for path in missing)
        ap.error(
            "required source files are missing; the existing database was not changed:\n"
            f"{paths}\n"
            "Provide the complete PSI source data directory with --raw."
        )

    investigations, pubs = build_investigations(raw)
    runs = build_flex(raw) + build_acme(raw) + build_saffire(raw)
    params = summarise(runs)
    findings = build_findings()
    resources = build_file_resources(raw) + pubs

    out.parent.mkdir(parents=True, exist_ok=True)
    if out.exists():
        out.unlink()
    with sqlite3.connect(out) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO investigations (investigation_id, name, acronym, research_area, objectives,"
                         " platform, doi, source_url, project_type, sub_research_area, experiment_hardware,"
                         " hypothesis, principal_investigator, notes) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?)",
                         investigations)
        conn.executemany("INSERT INTO experimental_runs (investigation_id, run_id, parameter_name, value, value_low,"
                         " value_high, unit, original_text, original_unit, text_value, quality_flag)"
                         " VALUES (?,?,?,?,?,?,?,?,?,?,?)",
                         [(r["investigation_id"], r["run_id"], r["parameter_name"], r["value"], r["value_low"],
                           r["value_high"], r["unit"], r["original_text"], r["original_unit"], r["text_value"],
                           r["quality_flag"]) for r in runs])
        conn.executemany("INSERT INTO parameters (investigation_id, parameter_name, value, unit, parameter_type,"
                         " original_value, original_unit, source_reference, statistic, n_runs, value_min,"
                         " value_max, quality_flag) VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)", params)
        conn.executemany("INSERT INTO findings (investigation_id, finding_text, category, source_reference,"
                         " page_number) VALUES (?,?,?,?,?)", findings)
        conn.executemany("INSERT INTO resources (investigation_id, resource_type, file_name, source_url,"
                         " page_number) VALUES (?,?,?,?,?)", resources)

    qdir = ROOT / "data" / "processed_data"
    qdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(QUALITY_LOG).to_csv(qdir / "data_quality_log.csv", index=False)
    pd.DataFrame([{k: v for k, v in r.items() if not k.startswith("_")} for r in runs]).to_csv(
        qdir / "experimental_runs.csv", index=False)
    print(f"Wrote {out}")
    print(f"  investigations={len(investigations)} runs(rows)={len(runs)} parameters={len(params)} "
          f"findings={len(findings)} resources={len(resources)}")
    print(f"  quality log: {len(QUALITY_LOG)} entries -> {qdir / 'data_quality_log.csv'}")


if __name__ == "__main__":
    main()
