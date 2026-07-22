"""
13_ai_extract.py — POC: LLM-assisted extraction of instrument parameters
from raw lab workbooks into structured JSON.

The idea (and why it matters):
    Modules 1-4 of this repo required hand-written parsers for every workbook
    layout. This module tests whether a generative model can replace that
    manual step: the raw summary sheet is rendered as plain text (exactly as
    messy as it is), sent to an LLM with a strict JSON schema, and the answer
    is validated field-by-field against the deterministic ETL ground truth
    already in the database (see 14_ai_evaluate.py).

Providers (auto-selected):
    ANTHROPIC_API_KEY set  -> Anthropic Claude (claude-sonnet-4-5)
    OPENAI_API_KEY set     -> OpenAI (gpt-4o-mini)
    neither                -> regex baseline ("mock") so the full
                              extract->evaluate harness runs reproducibly
                              without credentials. Clearly labeled in output.

Run:  python src/13_ai_extract.py            # all 11 PV workbooks
      ANTHROPIC_API_KEY=sk-... python src/13_ai_extract.py
"""

import json
import os
import re
from pathlib import Path

import openpyxl

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
OUT = ROOT / "outputs" / "ai_extracted.json"

PV_FILES = [
    "STC_23_99C_179_83Wm2.xlsx", "STC_23_74C_400_42Wm2.xlsx",
    "STC_23_6C_625_62Wm2.xlsx", "STC_23_58C_841_81Wm2.xlsx",
    "STC_25_1C_1052_6Wm2.xlsx", "STC_36_02C_1051_24Wm2_100.xlsx",
    "STC_30_71C_1057_14Wm2_1cell_shade.xlsx",
    "STC_27_95C_1058_35Wm2_2C_PAR_shade.xlsx",
    "Lab_28_7C_731_14Wm2.xlsx",
    "IV-2_Curve_998__29_01C.xlsx", "IV-4_Curve_516__32_82C.xlsx",
]

FIELDS = ["Isc", "Voc", "FF", "Vmpp", "Impp", "Pmpp", "ETA", "Area"]

SYSTEM_PROMPT = """You extract measurement parameters from photovoltaic \
IV-tracer summary sheets. The user gives you a raw text rendering of one \
spreadsheet. Return ONLY a JSON object with these numeric keys (no unit \
strings, no commentary): Isc, Voc, FF, Vmpp, Impp, Pmpp, ETA, Area. \
Use the value exactly as it appears next to each parameter label. If a \
field is absent, use null."""


def sheet_as_text(path):
    """Render the IV-Summary sheet as a plain cell-grid text dump —
    deliberately unparsed, the way an office user would paste it."""
    ws = openpyxl.load_workbook(path, data_only=True)["IV-Summary"]
    lines = []
    for row in ws.iter_rows():
        cells = [f"{c.coordinate}={c.value}" for c in row if c.value is not None]
        if cells:
            lines.append(" | ".join(cells))
    return "\n".join(lines)


def extract_mock(text):
    """Regex baseline: finds 'FIELD | <cell>=<number>' pairs in the dump.
    Serves as the no-credentials fallback AND as the classical baseline the
    LLM has to beat (a fair POC always has a baseline)."""
    result = {}
    for field in FIELDS:
        m = re.search(rf"=\b{field}\b.*?=(-?[\d.]+(?:[eE]-?\d+)?)", text)
        result[field] = float(m.group(1)) if m else None
    return result


def extract_anthropic(text):
    import anthropic
    client = anthropic.Anthropic()
    msg = client.messages.create(
        model="claude-sonnet-4-5",
        max_tokens=300,
        system=SYSTEM_PROMPT,
        messages=[{"role": "user", "content": text}],
    )
    raw = msg.content[0].text.strip().removeprefix("```json").removesuffix("```")
    return json.loads(raw)


def extract_openai(text):
    from openai import OpenAI
    client = OpenAI()
    rsp = client.chat.completions.create(
        model="gpt-4o-mini",
        response_format={"type": "json_object"},
        messages=[{"role": "system", "content": SYSTEM_PROMPT},
                  {"role": "user", "content": text}],
    )
    return json.loads(rsp.choices[0].message.content)


def main():
    if os.environ.get("ANTHROPIC_API_KEY"):
        provider, extract = "anthropic/claude-sonnet-4-5", extract_anthropic
    elif os.environ.get("OPENAI_API_KEY"):
        provider, extract = "openai/gpt-4o-mini", extract_openai
    else:
        provider, extract = "regex-baseline (no API key set)", extract_mock
    print(f"extraction provider: {provider}")

    results = {"provider": provider, "files": {}}
    for fname in PV_FILES:
        text = sheet_as_text(RAW / fname)
        results["files"][fname.replace(".xlsx", "")] = extract(text)
        print(f"  extracted {fname}")
    OUT.write_text(json.dumps(results, indent=2))
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
