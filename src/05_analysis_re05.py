"""
05_analysis_re05.py — Run the RE05 / regulator SQL analyses and export results.

Run:  python src/05_analysis_re05.py
"""

from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "outputs" / "battery_lab.db"
QUERIES = ROOT / "sql" / "analysis_re05_queries.sql"
REPORT = ROOT / "outputs" / "results_summary_re05.md"

TITLES = [
    "Q5 · Electrolyzer: gas production, Faradaic & energy efficiency",
    "Q6 · Electrolyzer I-U: decomposition voltage & overpotential",
    "Q7 · PEM fuel cell: maximum power point & ohmic fit",
    "Q8 · SOFC: maximum power, fit & energy efficiency",
    "Q9 · Capacitor discharge time constants (ln-linear OLS in SQL)",
    "Q10 · Regulator topologies: energy delivered to the capacitor",
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
    lines = ["# RE05 Hydrogen Technologies & Regulator Experiments — Results\n"]
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
