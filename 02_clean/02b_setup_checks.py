"""02b_setup_checks: the stage 02 check figure, p25 capacity by technology.

docs/plan.md, stage 02_clean, 02b. D35b: the setup checks (coal, nuclear) are
not run as gates; Caleb confirmed the setup. Only the check figure is kept:
p25 capacity by technology over time, one panel per case, one figure per batch
and arm (D26: UON and UOS never in one figure). Technologies are the `i`
values of `cap_ivrt` as stored, not grouped.

In:  outputs/01_ingest/outputs/cap_ivrt.h5 (stage 01; MW)
     00_config/study_cases.csv, 00_config/study_settings.csv
Out (generated): outputs/02_clean/figures/02b_p25_capacity_<batch>_<arm>.png
     section "02b" of outputs/checks/02_clean.md
No data are changed.

Run:  conda run -n reeds python 02_clean/02b_setup_checks.py
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO / "00_config"
IN_DIR = REPO / "outputs" / "01_ingest" / "outputs"
FIG_DIR = REPO / "outputs" / "02_clean" / "figures"
CHECK_REPORT = REPO / "outputs" / "checks" / "02_clean.md"
SECTION = "02b"

FOCUS = "p25"          # data_dictionary.md, Region groups: focus
MW_PER_GW = 1000.0
NCOL = 4

settings = pd.read_csv(CONFIG_DIR / "study_settings.csv").set_index("setting")["value"]
SOLVE = [int(y) for y in settings["solve_years"].split()]
FIRST_POST = min(int(y) for y in settings["post_plant_years"].split())
cases = pd.read_csv(CONFIG_DIR / "study_cases.csv")


def md_table(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |",
           "| " + " | ".join("---" for _ in cols) + " |"]
    for row in df.itertuples(index=False):
        out.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(out)


def write_section(path, section, text, title="# Check report: 02_clean\n\n"):
    """Replace only this script's section of the stage check report."""
    start, end = f"<!-- {section} start -->", f"<!-- {section} end -->"
    block = f"{start}\n{text.rstrip()}\n{end}\n"
    old = path.read_text(encoding="utf-8") if path.exists() else title
    if start in old and end in old:
        pre, rest = old.split(start, 1)
        new = pre + block + rest.split(end, 1)[1].lstrip("\n")
    else:
        new = old.rstrip("\n") + "\n\n" + block
    path.write_text(new, encoding="utf-8")


FIG_DIR.mkdir(parents=True, exist_ok=True)
for old in FIG_DIR.glob("02b_*.png"):
    old.unlink()
CHECK_REPORT.parent.mkdir(parents=True, exist_ok=True)

cap = pd.read_hdf(IN_DIR / "cap_ivrt.h5", "data", where=f'r == "{FOCUS}"')
cap_t = cap.groupby(["batch", "arm", "level", "case", "i", "t"], as_index=False)["Value"].sum()
techs = sorted(cap_t["i"].unique())
palette = [plt.get_cmap("tab20")(n) for n in range(20)] + \
          [plt.get_cmap("tab20b")(n) for n in range(20)]
colors = {t: palette[n % len(palette)] for n, t in enumerate(techs)}

rows = []
for (b, a), arm_cases in cases.groupby(["batch", "arm"], sort=True):
    arm_cases = arm_cases.sort_values("level")
    g = cap_t[(cap_t["batch"] == b) & (cap_t["arm"] == a)]
    n = len(arm_cases)
    nrow = int(np.ceil(n / NCOL))
    fig, axes = plt.subplots(nrow, NCOL, figsize=(4.2 * NCOL, 3.0 * nrow),
                             sharex=True, sharey=True, squeeze=False)
    panels = 0
    for ax, row in zip(axes.flat, arm_cases.itertuples(index=False)):
        w = (g[g["case"] == row.case]
             .pivot_table(index="t", columns="i", values="Value", aggfunc="sum")
             .reindex(SOLVE).fillna(0.0))
        bottom = np.zeros(len(w))
        for t in [t for t in techs if t in w.columns]:
            vals = w[t].to_numpy() / MW_PER_GW
            ax.bar(w.index, vals, bottom=bottom, width=2.4, color=colors[t])
            bottom += vals
        ax.axvline(FIRST_POST - 1.5, color="k", lw=0.6, ls=":")
        ax.set_title(f"{row.level:g} GW", fontsize=9)
        ax.tick_params(labelsize=7)
        panels += 1
    for ax in axes.flat[n:]:
        ax.set_visible(False)
    for ax in axes[:, 0]:
        ax.set_ylabel("GW", fontsize=8)
    present = [t for t in techs if t in set(g["i"])]
    fig.legend([plt.Rectangle((0, 0), 1, 1, color=colors[t]) for t in present], present,
               loc="lower center", ncol=7, fontsize=7, frameon=False)
    fig.suptitle(f"{b} {a}: p25 capacity by technology (cap_ivrt, MW shown as GW); "
                 f"dotted line = start of post-plant years ({FIRST_POST})", fontsize=10)
    fig.tight_layout(rect=(0, 0.08, 1, 0.96))
    p = FIG_DIR / f"02b_p25_capacity_{b}_{a}.png"
    fig.savefig(p, dpi=110)
    plt.close(fig)
    rows.append((b, a, n, panels, f"`{p.relative_to(REPO).as_posix()}`"))

tab = pd.DataFrame(rows, columns=["batch", "arm", "cases", "panels", "figure"])
ok = bool((tab["cases"] == tab["panels"]).all()) and len(tab) == cases.groupby(["batch", "arm"]).ngroups
lines = [f"## 02b_setup_checks — {'PASS' if ok else 'FAIL'} (check figure only)\n",
         "D35b: the coal and nuclear setup checks are not run as gates; Caleb confirmed "
         "the setup. This script makes only the check figure: p25 capacity by technology "
         "(`cap_ivrt`, `i` as stored), one panel per case, one figure per batch and arm "
         "(D26).\n",
         md_table(tab) + "\n",
         f"Figures: {len(tab)}; panels: {int(tab['panels'].sum())} "
         f"(cases: {len(cases)}).\n"]
write_section(CHECK_REPORT, SECTION, "\n".join(lines))
print(f"02b check figure: {'PASS' if ok else 'FAIL'} ({len(tab)} figures, "
      f"{int(tab['panels'].sum())} panels)")
sys.exit(0 if ok else 1)
