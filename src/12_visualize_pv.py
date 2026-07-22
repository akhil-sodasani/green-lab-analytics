"""
12_visualize_pv.py — Figures for the PV module lab.
Run:  python src/12_visualize_pv.py
"""

from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "outputs" / "battery_lab.db"
FIG = ROOT / "outputs" / "figures"
plt.rcParams.update({"figure.dpi": 150, "font.size": 10,
                     "axes.grid": True, "grid.alpha": 0.3})


def load():
    con = sqlite3.connect(DB)
    raw = pd.read_sql("""SELECT r.dataset, m.label, m.condition,
                                m.irradiance_wm2 g, r.voltage_v v, -r.current_a i
                         FROM pv_iv_raw r JOIN pv_measurement m USING (dataset)
                         WHERE r.voltage_v >= 0 ORDER BY r.voltage_v""", con)
    meas = pd.read_sql("SELECT * FROM pv_measurement", con)
    con.close()
    return raw, meas


def fig_family(raw):
    fig, ax = plt.subplots(figsize=(8.5, 5))
    series = raw[raw.condition == "irradiance_series"]
    cmap = plt.cm.YlOrRd(np.linspace(0.35, 0.95, 5))
    for color, (g, grp) in zip(cmap, series.groupby("g")):
        ax.plot(grp.v, grp.i, "-", color=color, lw=1.8,
                label=f"{g:.0f} W/m²")
        pmax_idx = (grp.v * grp.i).idxmax()
        ax.plot(grp.v[pmax_idx], grp.i[pmax_idx], "o", color=color, ms=6)
    ax.set_xlabel("Voltage U [V]")
    ax.set_ylabel("Current I [A]")
    ax.set_xlim(0, 22); ax.set_ylim(0, 6)
    ax.legend(title="Irradiance", fontsize=9)
    ax.set_title("PV module IV family vs. irradiance (MPP marked)\n"
                 "current logged in load convention — sign-inverted; "
                 "reverse-bias branch excluded")
    fig.tight_layout()
    fig.savefig(FIG / "pv_iv_family.png", bbox_inches="tight")


def fig_linearity(raw, meas):
    series = raw[raw.condition == "irradiance_series"]
    rows = []
    for g, grp in series.groupby("g"):
        grp = grp.sort_values("v")
        rows.append({"g": g, "isc": grp.i.iloc[0],
                     "pmax": (grp.v * grp.i).max()})
    df = pd.DataFrame(rows)
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2))
    # SQL results: slope 4.969 mA/(W/m2), intercept 0.066 A
    gg = np.linspace(0, 1100, 2)
    ax1.plot(gg, 0.066 + 4.969e-3 * gg, "--", color="#888",
             label="SQL OLS: 4.97 mA/(W/m²)·G + 0.07 A")
    ax1.plot(df.g, df.isc, "o", color="#D97E2B", ms=8)
    ax1.set_xlabel("Irradiance G [W/m²]"); ax1.set_ylabel("Isc [A]")
    ax1.set_title("Short-circuit current ∝ irradiance")
    ax1.legend(fontsize=8)
    ax2.plot(gg, 0.068 * gg / 1, "--", color="#888",
             label="SQL OLS: 0.068 W/(W/m²)")
    ax2.plot(df.g, df.pmax, "s", color="#C05146", ms=8)
    ax2.set_xlabel("Irradiance G [W/m²]"); ax2.set_ylabel("Pmax [W]")
    ax2.set_title("Maximum power vs. irradiance")
    ax2.legend(fontsize=8)
    fig.suptitle("Irradiance series at ~24 °C — OLS fits computed in SQL", y=1.02)
    fig.tight_layout()
    fig.savefig(FIG / "pv_linearity.png", bbox_inches="tight")


def fig_shading(raw):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4.2),
                                   gridspec_kw={"width_ratios": [3, 2]})
    colors = {"full sun (no shade)": "#3D8B5F",
              "2 cells (parallel) shaded": "#D97E2B",
              "1 cell shaded": "#C05146"}
    sh = raw[raw.condition.isin(["shading_ref", "shading"])]
    for label, grp in sh.groupby("label"):
        grp = grp.sort_values("v")
        ax1.plot(grp.v, grp.i, "-", color=colors[label], lw=1.8, label=label)
    ax1.set_xlabel("Voltage U [V]"); ax1.set_ylabel("Current I [A]")
    ax1.set_xlim(0, 22); ax1.set_ylim(0, 6)
    ax1.legend(fontsize=8)
    ax1.set_title("IV curves at ~1055 W/m² — bypass-diode steps visible")
    losses = [("full sun", 66.6, 0.0, "#3D8B5F"),
              ("2 cells (par.)", 53.2, 20.1, "#D97E2B"),
              ("1 cell", 31.1, 53.3, "#C05146")]
    bars = ax2.bar([l[0] for l in losses], [l[1] for l in losses],
                   color=[l[3] for l in losses])
    for bar, (_, p, loss, _) in zip(bars, losses):
        ax2.annotate(f"{p:.1f} W\n(−{loss:.0f}%)" if loss else f"{p:.1f} W",
                     (bar.get_x() + bar.get_width() / 2, p),
                     ha="center", va="bottom", fontsize=9)
    ax2.set_ylabel("Pmax [W]"); ax2.set_ylim(0, 80)
    ax2.set_title("One shaded cell → −53% module power")
    fig.tight_layout()
    fig.savefig(FIG / "pv_shading.png", bbox_inches="tight")


def main():
    raw, meas = load()
    fig_family(raw)
    fig_linearity(raw, meas)
    fig_shading(raw)
    print(f"3 figures written to {FIG}")


if __name__ == "__main__":
    main()
