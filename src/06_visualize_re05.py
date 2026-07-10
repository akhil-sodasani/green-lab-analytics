"""
06_visualize_re05.py — Figures for the RE05 hydrogen lab and regulator data.

Outputs (outputs/figures/):
    electrolyzer_iu.png    I-U characteristic, OLS fit, overpotential
    fuel_cells.png         PEM vs SOFC: U-I curves + power curves, MPP marked
    regulators.png         capacitor voltage per topology + energy comparison
    cap_discharge.png      discharge transients with exponential fits (semilog)

Run:  python src/06_visualize_re05.py
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


def fig_electrolyzer(iu):
    good = iu[iu.resistance_ohm != 100]
    excl = iu[iu.resistance_ohm == 100]
    slope, u_dec = np.polyfit(good.current_ma, good.voltage_v, 1)
    xs = np.linspace(0, good.current_ma.max() * 1.05, 50)

    fig, ax = plt.subplots(figsize=(7.5, 4.5))
    ax.scatter(good.current_ma, good.voltage_v, color="#2F6FB7", zorder=3,
               label="measured")
    ax.scatter(excl.current_ma, excl.voltage_v, marker="x", color="gray",
               s=70, zorder=3, label="excluded (recording error)")
    ax.plot(xs, u_dec + slope * xs, "--", color="#2F6FB7",
            label=f"fit: U = {u_dec:.2f} V + {slope*1000:.2f} Ω · I")
    ax.axhline(2.46, color="#C05146", ls=":",
               label="thermodynamic minimum 2 × 1.23 V")
    ax.annotate("", xy=(5, u_dec), xytext=(5, 2.46),
                arrowprops=dict(arrowstyle="<->", color="#C05146"))
    ax.text(9, (u_dec + 2.46) / 2, f"overpotential\n≈ {u_dec-2.46:.2f} V",
            color="#C05146", fontsize=9)
    ax.set_xlabel("Current I [mA]")
    ax.set_ylabel("Cell voltage U [V]")
    ax.set_title("Double-cell electrolyzer I-U characteristic")
    ax.legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(FIG / "electrolyzer_iu.png", bbox_inches="tight")


def fig_fuel_cells(pem, sofc):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
    specs = [
        ("PEM fuel cell (single cell)", pem, "#2F6FB7",
         "documented 'new setup' restart between 35.8 and 69.3 mA"),
        ("Solid oxide fuel cell", sofc, "#C05146",
         "R = 0 short-circuit point included for shape, excluded from fits"),
    ]
    for ax, (title, df, color, note) in zip(axes, specs):
        df = df.sort_values("current_ma")
        p_mw = df.current_ma * df.voltage_mv / 1000
        ax.plot(df.current_ma, df.voltage_mv, "-o", color=color, ms=4,
                label="U-I curve")
        ax2 = ax.twinx()
        ax2.plot(df.current_ma, p_mw, "-s", color="#E8A020", ms=4,
                 label="P-I curve")
        ax2.set_ylabel("Power P [mW]", color="#B07508")
        ax2.grid(False)
        mpp = p_mw.idxmax()
        ax2.annotate(f"Pmax = {p_mw[mpp]:.1f} mW",
                     xy=(df.current_ma[mpp], p_mw[mpp]),
                     xytext=(0.45, 0.55), textcoords="axes fraction",
                     arrowprops=dict(arrowstyle="->", color="#B07508"),
                     color="#B07508", fontsize=9)
        ax.set_xlabel("Current I [mA]")
        ax.set_ylabel("Voltage U [mV]", color=color)
        ax.set_title(f"{title}\n{note}", fontsize=10)
        h1, l1 = ax.get_legend_handles_labels()
        h2, l2 = ax2.get_legend_handles_labels()
        ax.legend(h1 + h2, l1 + l2, fontsize=8, loc="upper right")
    fig.suptitle("Fuel-cell characteristics: PEM vs SOFC")
    fig.tight_layout()
    fig.savefig(FIG / "fuel_cells.png", bbox_inches="tight")


def fig_regulators(reg, energy):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5),
                                   gridspec_kw={"width_ratios": [3, 2]})
    colors = {"Series Regulator": "#2F6FB7", "Shunt Regulator": "#3D8B5F",
              "PWM": "#7A5FA8", "Shunt Regulator + Load": "#D97E2B",
              "MPP + Shunt": "#C05146"}
    for topo, grp in reg.groupby("topology"):
        grp = grp[grp.time_s <= 25].sort_values("time_s")
        ax1.plot(grp.time_s, grp.u_cap_v, color=colors[topo], lw=1.4, label=topo)
    ax1.set_xlabel("Time [s]")
    ax1.set_ylabel("Capacitor voltage U [V]")
    ax1.set_title("Capacitor charging by regulator topology (first 25 s)")
    ax1.legend(fontsize=8)

    energy = energy.sort_values("e_to_cap_j")
    bars = ax2.barh(energy.topology, energy.e_to_cap_j,
                    color=[colors[t] for t in energy.topology])
    ax2.bar_label(bars, fmt="%.2f J", fontsize=8)
    ax2.set_xlabel("Energy delivered to capacitor [J]")
    ax2.set_title("Energy in first 25 s (SQL trapezoid)")
    fig.tight_layout()
    fig.savefig(FIG / "regulators.png", bbox_inches="tight")


def fig_cap_discharge(cap, taus):
    fig, ax = plt.subplots(figsize=(8, 4.5))
    colors = {1: "#2F6FB7", 2: "#3D8B5F", 3: "#C05146"}
    for run, grp in cap.groupby("run"):
        grp = grp.sort_values("time_s")
        ax.semilogy(grp.time_s, grp.current_a, ".", ms=3, color=colors[run],
                    alpha=0.6)
        tau = taus.loc[taus.run == run, "tau_s"].iloc[0]
        i0 = taus.loc[taus.run == run, "i0_extrapolated_a"].iloc[0]
        decay = grp[(grp.current_a > 0.05) & (grp.current_a < 1.0)]
        xs = np.linspace(decay.time_s.min(), decay.time_s.max(), 40)
        ax.semilogy(xs, i0 * np.exp(-xs / tau), "--", color=colors[run],
                    label=f"run {run}: τ = {tau:.2f} s")
    ax.set_xlabel("Time [s]")
    ax.set_ylabel("Current I [A] (log scale)")
    ax.set_title("Capacitor discharge transients — exponential fits from ln-linear OLS in SQL\n"
                 "(1.02 A current-limit plateau and <50 mA noise floor excluded from fit)")
    ax.legend(fontsize=9)
    fig.tight_layout()
    fig.savefig(FIG / "cap_discharge.png", bbox_inches="tight")


def main():
    with sqlite3.connect(DB) as con:
        iu = pd.read_sql("SELECT * FROM electrolyzer_iu", con)
        pem = pd.read_sql("SELECT * FROM pem_cell_iu", con)
        sofc = pd.read_sql("SELECT * FROM sofc_iu", con)
        reg = pd.read_sql("SELECT * FROM regulator_run", con)
        cap = pd.read_sql("SELECT * FROM cap_discharge", con)
        energy = pd.read_sql("""
            WITH w AS (
                SELECT topology, u_cap_v*i_cap_a p,
                       LAG(u_cap_v*i_cap_a) OVER (PARTITION BY topology ORDER BY time_s) pp,
                       time_s - LAG(time_s) OVER (PARTITION BY topology ORDER BY time_s) dt
                FROM regulator_run WHERE time_s <= 25)
            SELECT topology, SUM((p+pp)/2.0*dt) e_to_cap_j
            FROM w WHERE pp IS NOT NULL GROUP BY topology""", con)
        taus = pd.read_sql("""
            WITH d AS (SELECT run, time_s x, LN(current_a) y FROM cap_discharge
                       WHERE current_a > 0.05 AND current_a < 1.0),
            s AS (SELECT run, AVG(x) mx, AVG(y) my, AVG(x*y) mxy, AVG(x*x) mxx
                  FROM d GROUP BY run)
            SELECT run, -1.0/((mxy-mx*my)/(mxx-mx*mx)) tau_s,
                   EXP(my - (mxy-mx*my)/(mxx-mx*mx)*mx) i0_extrapolated_a
            FROM s""", con)

    fig_electrolyzer(iu)
    fig_fuel_cells(pem, sofc)
    fig_regulators(reg, energy)
    fig_cap_discharge(cap, taus)
    print(f"4 figures written to {FIG}")


if __name__ == "__main__":
    main()
