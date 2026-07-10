"""
03_visualize.py — Build the figures from battery_lab.db.

Figures (written to outputs/figures/):
    1. ui_characteristics.png   U-I curves + OLS fit lines, artifacts flagged
    2. internal_resistance.png  Ri comparison (from the SQL regression)
    3. battery_kpis.png         SOC vs energy density KPI view
    4. cycle_efficiency.png     NiMH discharge/charge curves + efficiency

Run:  python src/03_visualize.py
"""

from pathlib import Path
import sqlite3

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
DB = ROOT / "outputs" / "battery_lab.db"
FIG = ROOT / "outputs" / "figures"
FIG.mkdir(parents=True, exist_ok=True)

COLORS = {"Li-Ion": "#1f77b4", "NiMH": "#2ca02c", "Lead-acid": "#d62728",
          "LiPo": "#9467bd", "NiZn": "#ff7f0e"}

plt.rcParams.update({"figure.dpi": 150, "font.size": 10,
                     "axes.grid": True, "grid.alpha": 0.3})


def fit_region(df):
    """Same exclusions as sql/analysis_queries.sql Q3."""
    mask = ~(((df.battery == "Li-Ion") & (df.load_resistance_ohm == 1))
             | ((df.battery == "Lead-acid") & (df.current_ma >= 200)))
    return df[mask]


def fig_ui(ui):
    fig, axes = plt.subplots(1, 3, figsize=(12, 4), sharex=False)
    for ax, (name, grp) in zip(axes, ui.groupby("battery", sort=False)):
        color = COLORS[name]
        good = fit_region(grp)
        excluded = grp.loc[~grp.index.isin(good.index)]
        slope, intercept = np.polyfit(good.current_ma, good.voltage_v, 1)
        xs = np.linspace(0, grp.current_ma.max(), 50)
        ax.scatter(good.current_ma, good.voltage_v, color=color, zorder=3,
                   label="measured")
        if len(excluded):
            ax.scatter(excluded.current_ma, excluded.voltage_v, marker="x",
                       color="gray", zorder=3, label="excluded (artifact)")
        ax.plot(xs, intercept + slope * xs, "--", color=color,
                label=f"fit: Ri = {-slope * 1000:.2f} Ω")
        ax.set_title(name)
        ax.set_xlabel("Load current I [mA]")
        ax.legend(fontsize=8)
    axes[0].set_ylabel("Terminal voltage U [V]")
    fig.suptitle("U-I characteristics and internal resistance (OLS fit)")
    fig.tight_layout()
    fig.savefig(FIG / "ui_characteristics.png", bbox_inches="tight")


def fig_ri(ri):
    fig, ax = plt.subplots(figsize=(6, 4))
    bars = ax.bar(ri.battery, ri.internal_resistance_ohm,
                  color=[COLORS[b] for b in ri.battery])
    ax.bar_label(bars, fmt="%.2f Ω")
    ax.set_ylabel("Internal resistance Ri [Ω]")
    ax.set_title("Internal resistance by chemistry\n(least-squares fit computed in SQL)")
    fig.tight_layout()
    fig.savefig(FIG / "internal_resistance.png", bbox_inches="tight")


def fig_kpis(soc):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(11, 4))
    order = soc.sort_values("energy_density_mwh_per_g", ascending=False)
    colors = [COLORS[b] for b in order.battery]

    bars = ax1.bar(order.battery, order.energy_density_mwh_per_g, color=colors)
    ax1.bar_label(bars, fmt="%.1f")
    ax1.set_ylabel("Current energy density [mWh/g]")
    ax1.set_title("Energy density at measured state of charge")

    bars = ax2.bar(order.battery, 100 * order.soc, color=colors)
    ax2.bar_label(bars, fmt="%.0f%%")
    ax2.axhline(20, color="red", ls=":", label="20% SOC floor (lab spec)")
    ax2.set_ylabel("State of charge [%]")
    ax2.set_title("State of charge from open-circuit voltage")
    ax2.legend(fontsize=8)

    fig.tight_layout()
    fig.savefig(FIG / "battery_kpis.png", bbox_inches="tight")


def fig_cycle(cycle, eff):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    for phase, style, color in [("discharge", "-o", "#d62728"),
                                ("charge", "-s", "#2ca02c")]:
        grp = cycle[cycle.phase == phase]
        ax.plot(grp.time_s, grp.voltage_v, style, color=color,
                markersize=4, label=phase)
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Cell voltage U [V]")
    ax.set_title("NiMH 5-min discharge / charge at 230 mA")
    eta = eff.voltage_efficiency_pct.iloc[0]
    wd, wc = eff.w_discharge_j.iloc[0], eff.w_charge_j.iloc[0]
    ax.annotate(f"W_discharge = {wd:.1f} J\nW_charge = {wc:.1f} J\n"
                f"η_voltage = {eta:.1f}%",
                xy=(0.98, 0.5), xycoords="axes fraction", ha="right",
                bbox=dict(boxstyle="round", fc="lightyellow", ec="gray"))
    ax.legend()
    fig.tight_layout()
    fig.savefig(FIG / "cycle_efficiency.png", bbox_inches="tight")


def main():
    with sqlite3.connect(DB) as con:
        ui = pd.read_sql("SELECT * FROM ui_curve ORDER BY battery, current_ma", con)
        soc = pd.read_sql(
            """SELECT battery, soc,
                      capacity_current_mah * ocv_measured_v / weight_g
                          AS energy_density_mwh_per_g
               FROM battery_soc""", con)
        cycle = pd.read_sql("SELECT * FROM cycle_test ORDER BY phase, time_s", con)
        ri = pd.read_sql(
            """WITH f AS (SELECT battery, current_ma x, voltage_v y FROM ui_curve
                          WHERE NOT (battery='Li-Ion' AND load_resistance_ohm=1)
                            AND NOT (battery='Lead-acid' AND current_ma>=200))
               SELECT battery,
                      -1000.0*(AVG(x*y)-AVG(x)*AVG(y))/(AVG(x*x)-AVG(x)*AVG(x))
                          AS internal_resistance_ohm
               FROM f GROUP BY battery ORDER BY 2""", con)
        eff = pd.read_sql(
            """WITH s AS (SELECT phase, voltage_v v, current_ma i,
                          LAG(voltage_v) OVER (PARTITION BY phase ORDER BY time_s) vp,
                          time_s - LAG(time_s) OVER (PARTITION BY phase ORDER BY time_s) dt
                          FROM cycle_test),
               e AS (SELECT phase, SUM((v+vp)/2.0*dt)*MAX(i)/1000.0 ej
                     FROM s WHERE vp IS NOT NULL GROUP BY phase)
               SELECT MAX(CASE WHEN phase='discharge' THEN ej END) w_discharge_j,
                      MAX(CASE WHEN phase='charge' THEN ej END) w_charge_j,
                      100.0*MAX(CASE WHEN phase='discharge' THEN ej END)
                           /MAX(CASE WHEN phase='charge' THEN ej END)
                          AS voltage_efficiency_pct
               FROM e""", con)

    fig_ui(ui)
    fig_ri(ri)
    fig_kpis(soc)
    fig_cycle(cycle, eff)
    print(f"4 figures written to {FIG}")


if __name__ == "__main__":
    main()
