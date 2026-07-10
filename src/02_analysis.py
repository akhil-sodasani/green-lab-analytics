"""
02_analysis.py — Run the SQL analyses against battery_lab.db and print /
export the results. All metrics are computed in SQL (see sql/analysis_queries.sql);
this script only orchestrates and formats.

Run:  python src/02_analysis.py
"""

from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "outputs" / "battery_lab.db"
QUERIES = ROOT / "sql" / "analysis_queries.sql"
REPORT = ROOT / "outputs" / "results_summary.md"

TITLES = [
    "Q1 · Faraday constant from copper electrolysis",
    "Q2 · Battery KPIs: SOC, capacity, energy density",
    "Q3 · Internal resistance (OLS fit in SQL)",
    "Q4 · NiMH round-trip energy efficiency",
]


def split_queries(sql_text: str) -> list[str]:
    """Split on ';' while ignoring comment-only fragments."""
    parts = []
    for chunk in sql_text.split(";"):
        stripped = "\n".join(
            line for line in chunk.splitlines()
            if line.strip() and not line.strip().startswith("--")
        ).strip()
        if stripped:
            parts.append(stripped)
    return parts


def main():
    queries = split_queries(QUERIES.read_text())
    lines = ["# Electrochemical Storage Lab — Results Summary\n"]

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
