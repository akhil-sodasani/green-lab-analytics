"""
11_analysis_pv.py — Run the PPC business-game SQL analyses and export results.

Run:  python src/11_analysis_pv.py
"""

from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "outputs" / "battery_lab.db"
QUERIES = ROOT / "sql" / "analysis_pv_queries.sql"
REPORT = ROOT / "outputs" / "results_summary_pv.md"

TITLES = [
    "Q14 · Module KPIs from raw IV sweeps, validated vs instrument",
    "Q15 · Irradiance dependence: Isc & Pmax vs G (OLS in SQL)",
    "Q16 · Shading impact at ~1055 W/m² (power loss vs unshaded)",
]


def split_queries(sql_text):
    parts = []
    for chunk in sql_text.split(";"):
        stripped = "\n".join(
            line for line in chunk.splitlines()
            if line.strip() and not line.strip().startswith("--")).strip()
        if stripped:
            parts.append(stripped)
    return parts


def main():
    queries = split_queries(QUERIES.read_text())
    lines = ["# Photovoltaics Lab — Module IV Curves — Results\n"]
    with sqlite3.connect(DB) as con:
        for title, query in zip(TITLES, queries):
            df = pd.read_sql_query(query, con)
            print(f"\n=== {title} ===")
            print(df.to_string(index=False))
            lines += [f"## {title}\n", df.to_markdown(index=False), ""]
    REPORT.write_text("\n".join(lines))
    print(f"\nReport written to {REPORT}")


if __name__ == "__main__":
    main()
