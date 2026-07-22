"""
14_ai_evaluate.py — Evaluation harness for the AI extraction POC.

Compares every field extracted by 13_ai_extract.py against the ground truth
in the pv_measurement table (built by the deterministic, hand-verified ETL).
This is the part most AI demos skip: a golden test set with per-field
tolerances, so "does AI keep the quality?" gets a number, not an opinion.

Metric: relative error per field, PASS if within 0.1% (values are copied
verbatim from the sheet, so the bar is exact reproduction).

Run:  python src/14_ai_evaluate.py
"""

import json
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "outputs" / "battery_lab.db"
IN = ROOT / "outputs" / "ai_extracted.json"
OUT = ROOT / "outputs" / "results_ai_extraction.md"

TOL = 0.001  # 0.1 % relative tolerance

FIELD_TO_COLUMN = {
    "Isc": "inst_isc_a", "Voc": "inst_voc_v", "FF": "inst_ff_pct",
    "Vmpp": "inst_vmpp_v", "Impp": "inst_impp_a", "Pmpp": "inst_pmpp_w",
    "ETA": "inst_eta_pct", "Area": "area_cm2",
}


def main():
    data = json.loads(IN.read_text())
    con = sqlite3.connect(DB)
    truth = {row[0]: dict(zip([c[1] for c in
             con.execute("PRAGMA table_info(pv_measurement)")], row))
             for row in con.execute("SELECT * FROM pv_measurement")}

    lines = ["# AI extraction POC — evaluation vs. deterministic ETL\n",
             f"Provider: **{data['provider']}**  ·  "
             f"tolerance: {TOL:.1%} relative\n",
             "| dataset | field | extracted | ground truth | rel. error | result |",
             "|---|---|---|---|---|---|"]
    n_pass = n_fail = n_missing = 0
    for ds, fields in data["files"].items():
        gt_row = truth[ds]
        for field, col in FIELD_TO_COLUMN.items():
            got, want = fields.get(field), gt_row[col]
            if got is None or want is None:
                n_missing += 1
                lines.append(f"| {ds} | {field} | {got} | {want} | — | MISSING |")
                continue
            rel = abs(got - want) / abs(want) if want else abs(got - want)
            ok = rel <= TOL
            n_pass += ok
            n_fail += (not ok)
            if not ok:
                lines.append(f"| {ds} | {field} | {got} | {want} "
                             f"| {rel:.2%} | **FAIL** |")
    total = n_pass + n_fail + n_missing
    summary = (f"\n**{n_pass}/{total} fields correct "
               f"({100.0 * n_pass / total:.1f}%)** · "
               f"{n_fail} wrong · {n_missing} missing "
               f"(failures listed above; passing rows omitted for brevity)\n")
    lines.insert(3, summary)
    OUT.write_text("\n".join(lines))
    print(f"provider: {data['provider']}")
    print(f"accuracy: {n_pass}/{total} fields ({100.0 * n_pass / total:.1f}%) "
          f"· {n_fail} wrong · {n_missing} missing")
    print(f"report: {OUT}")


if __name__ == "__main__":
    main()
