"""Create a PLACEHOLDER database so the dashboard can be developed before the
real NASA data arrives.

Everything here is FAKE (investigations are named DEMO-xxx, values are
arbitrary). It is written to data/placeholder_nasa_combustion.db, which the
app ignores as soon as the real data/nasa_combustion.db exists.

Usage:  python scripts/make_placeholder_db.py
"""
import sqlite3
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from modules.database import PLACEHOLDER_DB, SCHEMA  # noqa: E402

INVESTIGATIONS = [
    ("DEMO-001", "Demo Investigation One", "DEMO1", "Combustion Science",
     "PLACEHOLDER objective: demo solid-material experiment.", "Demo platform", None, None),
    ("DEMO-002", "Demo Investigation Two", "DEMO2", "Combustion Science",
     "PLACEHOLDER objective: demo suppression experiment.", "Demo platform", None, None),
    ("DEMO-003", "Demo Investigation Three", "DEMO3", "Combustion Science",
     "PLACEHOLDER objective: demo smoke experiment.", "Demo platform", None, None),
]

# (investigation_id, name, value, unit, type, original_value, original_unit, source)
PARAMETERS = [
    ("DEMO-001", "Oxygen mole fraction", 0.21, "-", "condition", 21.0, "%", "PLACEHOLDER p.1"),
    ("DEMO-001", "Absolute pressure", 101325.0, "Pa", "condition", 101.325, "kPa", "PLACEHOLDER p.1"),
    ("DEMO-001", "Airflow velocity", 0.10, "m/s", "condition", 10.0, "cm/s", "PLACEHOLDER p.2"),
    ("DEMO-002", "Oxygen mole fraction", 0.30, "-", "condition", 30.0, "%", "PLACEHOLDER p.1"),
    ("DEMO-002", "Absolute pressure", 70000.0, "Pa", "condition", 70.0, "kPa", "PLACEHOLDER p.1"),
    ("DEMO-002", "Airflow velocity", None, "m/s", "condition", None, None, "not documented"),
    ("DEMO-003", "Oxygen mole fraction", 0.21, "-", "condition", 21.0, "%", "PLACEHOLDER p.3"),
    ("DEMO-003", "Absolute pressure", 101325.0, "Pa", "condition", 1.0, "atm", "PLACEHOLDER p.3"),
]

# (investigation_id, text, category, source, page)
FINDINGS = [
    ("DEMO-001", "PLACEHOLDER finding about flame spread under given conditions.", "Prevention", "PLACEHOLDER report", 4),
    ("DEMO-002", "PLACEHOLDER finding about extinguishment behaviour.", "Suppression", "PLACEHOLDER report", 7),
    ("DEMO-003", "PLACEHOLDER finding about smoke transport.", "Detection", "PLACEHOLDER report", 2),
    ("DEMO-003", "PLACEHOLDER finding relevant to several pillars.", "Multiple", "PLACEHOLDER report", 9),
]

RESOURCES = [
    ("DEMO-001", "Research report", "demo_report_1.pdf", None, None),
    ("DEMO-002", "Dataset", "demo_data_2.csv", None, None),
]


def main() -> None:
    if PLACEHOLDER_DB.exists():
        PLACEHOLDER_DB.unlink()
    PLACEHOLDER_DB.parent.mkdir(parents=True, exist_ok=True)
    with sqlite3.connect(PLACEHOLDER_DB) as conn:
        conn.executescript(SCHEMA)
        conn.executemany("INSERT INTO investigations (investigation_id, name, acronym, research_area, objectives, platform, doi, source_url) VALUES (?,?,?,?,?,?,?,?)", INVESTIGATIONS)
        conn.executemany(
            "INSERT INTO parameters (investigation_id, parameter_name, value, unit, parameter_type,"
            " original_value, original_unit, source_reference) VALUES (?,?,?,?,?,?,?,?)", PARAMETERS)
        conn.executemany(
            "INSERT INTO findings (investigation_id, finding_text, category, source_reference, page_number)"
            " VALUES (?,?,?,?,?)", FINDINGS)
        conn.executemany(
            "INSERT INTO resources (investigation_id, resource_type, file_name, source_url, page_number)"
            " VALUES (?,?,?,?,?)", RESOURCES)
    print(f"Placeholder database written to {PLACEHOLDER_DB}")


if __name__ == "__main__":
    main()
