"""
09_visualize_ppc.py — Figures for the PPC business game.
Run:  python src/09_visualize_ppc.py
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
RC = {1: "#C05146", 2: "#D97E2B", 3: "#2F6FB7", 4: "#3D8B5F"}


def fig_rounds(summary):
    fig, ax = plt.subplots(figsize=(8.5, 4.5))
    labels = [f"R{r}\n{l.split('(')[0].strip()}" for r, l in
              zip(summary['round'], summary.label)]
    bars = ax.bar(labels, summary.horizon_min,
                  color=[RC[r] for r in summary['round']])
    ax.bar_label(bars, fmt="%.0f min")
    ax.set_ylabel("Total production horizon [min]")
    ax2 = ax.twinx()
    ax2.plot(labels, summary.utilization_pct, "-o", color="#E8A020", lw=2)
    for x, u in zip(labels, summary.utilization_pct):
        ax2.annotate(f"{u:.0f}%", (x, u), textcoords="offset points",
                     xytext=(0, 8), color="#B07508", ha="center", fontsize=9)
    ax2.set_ylabel("Average utilization [%]", color="#B07508")
    ax2.set_ylim(0, 45)
    ax2.grid(False)
    ax.set_title("Production horizon and utilization across improvement rounds\n"
                 "125 → 58 min (−54%); R4 is the theoretical lean proposal")
    fig.tight_layout()
    fig.savefig(FIG / "ppc_round_comparison.png", bbox_inches="tight")


def fig_batches(batch):
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(12, 4.5))
    width = 0.27
    x = np.arange(1, 9)
    names = {1: "Round 1 (baseline)", 3: "Round 3 (measured)",
             4: "Round 4 (proposed)"}
    for i, r in enumerate([1, 3, 4]):
        grp = batch[batch['round'] == r].sort_values("batch")
        ax1.bar(x + (i - 1) * width, grp.cycle_min, width,
                color=RC[r], label=names[r])
        ax2.bar(x + (i - 1) * width, grp.waiting_min, width, color=RC[r])
    ax1.set_xlabel("Batch"); ax1.set_ylabel("Cycle time [min]")
    ax1.set_title("Cycle time per batch\nRound 1 queue build-up: 49 → 140 min")
    ax1.set_xticks(x); ax1.legend(fontsize=8)
    ax2.set_xlabel("Batch"); ax2.set_ylabel("Waiting time [min]")
    ax2.set_title("Waiting time per batch\nwaiting share of cycle: 65% → 49% → 28%")
    ax2.set_xticks(x)
    fig.tight_layout()
    fig.savefig(FIG / "ppc_batch_kpis.png", bbox_inches="tight")


def fig_bottleneck(ws):
    fig, axes = plt.subplots(1, 2, figsize=(12, 4.5), sharex=True)
    for ax, r, note in [(axes[0], 1, "bottleneck: Rework (46% of load)"),
                        (axes[1], 3, "bottleneck shifts to A1 (34%)")]:
        grp = ws[(ws['round'] == r) & ws.operation_min.notna()] \
            .sort_values("operation_min")
        y = np.arange(len(grp))
        ax.barh(y - 0.2, grp.operation_min, 0.4, color=RC[r], label="operation")
        ax.barh(y + 0.2, grp.idle_min, 0.4, color="#B9C4B9", label="idle")
        ax.set_yticks(y, grp.workstation)
        ax.set_xlabel("Time [min]")
        ax.set_title(f"Round {r} — {note}", fontsize=10)
        ax.legend(fontsize=8, loc="lower right")
    fig.suptitle("Workstation load vs. idle time (A3/Storage in R1: broken "
                 "#VALUE! formulas in source, kept as missing)", fontsize=10)
    fig.tight_layout()
    fig.savefig(FIG / "ppc_bottleneck.png", bbox_inches="tight")


def main():
    with sqlite3.connect(DB) as con:
        summary = pd.read_sql("SELECT * FROM ppc_round_summary ORDER BY round", con)
        batch = pd.read_sql("SELECT * FROM ppc_batch", con)
        ws = pd.read_sql("SELECT * FROM ppc_workstation", con)
    fig_rounds(summary)
    fig_batches(batch)
    fig_bottleneck(ws)
    print(f"3 figures written to {FIG}")


if __name__ == "__main__":
    main()
