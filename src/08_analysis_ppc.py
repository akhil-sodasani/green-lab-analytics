"""
08_analysis_ppc.py — Run the PPC business-game SQL analyses and export results.

Run:  python src/08_analysis_ppc.py
"""

from pathlib import Path
import sqlite3

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "outputs" / "battery_lab.db"
QUERIES = ROOT / "sql" / "analysis_ppc_queries.sql"
REPORT = ROOT / "outputs" / "results_summary_ppc.md"

TITLES = [
    "Q11 · Round-over-round improvement (LAG window function)",
    "Q12 · Batch KPIs per round: cycle, waiting, waiting share",
    "Q13 · Workstation bottleneck analysis (RANK per round)",
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
    lines = ["# Production Planning & Control Business Game — Results\n"]
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
