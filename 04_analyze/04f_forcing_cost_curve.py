"""04f_forcing_cost_curve: annualized system cost change per GW between neighboring levels.

docs/plan.md, "SMR value and the cost of prescribing it", 04f; D2, D26, D37e,
D38, D41, D44.

For each arm and group (wecc and the four others): the step slope of the D44
annualized system cost Diff (03b2, 2024 $) between each pair of neighboring
levels, (Diff(l2) - Diff(l1)) / (l2 - l1), in 2024 $ per GW of prescribed
nuclear. For the 2044-2050 total (undiscounted sum, D44) and for each year
2044 to 2050; capital and operations parts too (D46i). INFERENCE (plan, 04f): the
finite difference between levels is the average of the shadow price over the
step (`model_documentation.md` L3214-3220 at 0c0ea27, as cited in the plan).
This is a proxy only; the prescription dual itself is not read here (03j).
The D10 cost is not used (D44).

Diff and slopes are rebuilt in memory with analyze_common (plan rule 2).

Check figure: one panel per arm, forcing cost (2044-2050 total) against the
step's level, one line per group; second row: wecc, each year 2044-2050.

In:  outputs/03_derive/annualized_cost.csv, annualized_cost_total.csv, 00_config/*.csv
Out: outputs/04_analyze/04f_forcing_cost_<batch>.csv,
     outputs/04_analyze/figures/04f_forcing_cost_<batch>.png,
     section "04f <batch>" of outputs/checks/04_analyze.md

Run:  conda run -n reeds python 04_analyze/04f_forcing_cost_curve.py --batch UON
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import pandas as pd  # noqa: E402

import analyze_common as ac  # noqa: E402

METRICS = ["annualized_cost", "annualized_cost_capital", "annualized_cost_op"]
GROUP_STYLE = {"focus": ("tab:red", 1.6), "utah_rest": ("tab:orange", 1.2),
               "neighbors": ("tab:blue", 1.4), "rest_wecc": ("tab:green", 1.2),
               "wecc": ("black", 2.2)}


def figure(fc, batch, arms):
    years = [str(y) for y in range(2044, 2051)]
    cmap = plt.get_cmap("viridis")
    fig, axes = plt.subplots(2, len(arms), figsize=(3.1 * len(arms), 7.0), squeeze=False,
                             sharex=True, sharey="row")
    m = fc[fc["metric"] == "annualized_cost"]
    for j, arm in enumerate(arms):
        ax = axes[0, j]
        for grp in ac.GROUPS:
            s = m[(m["arm"] == arm) & (m["group"] == grp) & (m["t"] == ac.TOTAL_T)].sort_values("level_mid")
            c, lw = GROUP_STYLE[grp]
            ax.plot(s["level_mid"], s["step_slope"] / 1e9, color=c, lw=lw, marker=".", label=grp)
        ax.axhline(0, color="0.7", lw=0.5)
        ax.set_title(arm, fontsize=10)
        ax2 = axes[1, j]
        for k, yr in enumerate(years):
            s = m[(m["arm"] == arm) & (m["group"] == "wecc") & (m["t"] == yr)].sort_values("level_mid")
            ax2.plot(s["level_mid"], s["step_slope"] / 1e9, color=cmap(k / (len(years) - 1)),
                     lw=1.2, marker=".", ms=3, label=yr)
        ax2.axhline(0, color="0.7", lw=0.5)
        ax2.set_xlabel("level, GW (middle of each step)", fontsize=8)
        for a in (ax, ax2):
            a.tick_params(labelsize=7)
    axes[0, 0].set_ylabel("2044-2050 total\nbillion 2024 $ per GW", fontsize=8)
    axes[1, 0].set_ylabel("wecc, each year\nbillion 2024 $ per GW", fontsize=8)
    axes[0, -1].legend(fontsize=7, loc="best")
    axes[1, -1].legend(fontsize=7, loc="best", ncol=2)
    fig.suptitle(f"04f, {batch}: forcing-cost curve, step change in annualized system cost "
                 "(D44) per GW between neighboring levels", fontsize=11)
    fig.tight_layout(rect=(0, 0, 1, 0.95))
    ac.FIG.mkdir(parents=True, exist_ok=True)
    p = ac.FIG / f"04f_forcing_cost_{batch}.png"
    fig.savefig(p, dpi=100)
    plt.close(fig)
    return p


def main():
    batch = ac.parse_batch(__doc__.splitlines()[0])
    a, _ = ac.group_annualized_cost(batch)
    a = a[a["metric"].isin(METRICS)]
    d = ac.add_diff(a, ["batch", "arm", "group", "t", "metric"])
    keys = ["batch", "arm", "group", "metric", "t"]
    fc = ac.step_slopes(d, keys)
    fc["unit"] = fc["unit"].str.replace(" per GW", " per GW of prescribed nuclear", regex=False)
    shp = ac.shape_notes(fc, keys)
    path = ac.write_csv(fc, "04f_forcing_cost", batch)

    nlev = ac.cases(batch).groupby("arm")["level"].nunique()
    n = fc.groupby(keys).size()
    tot = fc[fc["t"] == ac.TOTAL_T].set_index(["arm", "group", "metric", "level_from"])["step_slope"]
    yrs = fc[fc["t"] != ac.TOTAL_T].groupby(["arm", "group", "metric", "level_from"])["step_slope"].sum()
    gap = ((yrs - tot).abs() / tot.abs().where(tot.abs() > 0, 1)).max()
    four = fc[(fc["group"] != "wecc")].groupby(["arm", "metric", "t", "level_from"])["step_slope"].sum()
    w = fc[fc["group"] == "wecc"].set_index(["arm", "metric", "t", "level_from"])["step_slope"]
    ggap = ((four - w).abs() / w.abs().where(w.abs() > 0, 1)).max()
    checks = [("steps per series = levels - 1 (D41)", bool((n == nlev.iloc[0] - 1).all()),
               f"{sorted(set(n))} steps"),
              ("no year before 2044 (annualized cost not reported before 2044)",
               bool((fc["t"].str.slice(0, 4).astype(int) >= ac.FIRST_POST_YEAR).all()), ""),
              ("2044-2050 step = sum of the yearly steps", gap < 1e-9, f"max relative gap {gap:.2e}"),
              ("four groups add up to wecc", ggap < 1e-6, f"max relative gap {ggap:.2e}")]

    arms = list(dict.fromkeys(ac.cases(batch)["arm"]))
    fig = figure(fc, batch, arms)

    wt = fc[(fc["metric"] == "annualized_cost") & (fc["group"] == "wecc") & (fc["t"] == ac.TOTAL_T)]
    wt = wt.assign(step=wt["level_from"].map("{:g}".format) + "-" + wt["level_to"].map("{:g}".format))
    wide = wt.pivot_table(index="arm", columns="step", values="step_slope", sort=False) / 1e9
    sh = shp[(shp["metric"] == "annualized_cost") & (shp["t"] == ac.TOTAL_T)]
    notes = sh[["arm", "group", "n_dir_changes", "dir_change_at", "kink", "kink_at"]]
    t = [f"## 04f_forcing_cost_curve, {batch}", "",
         f"- Table: `{ac.rel(path)}` ({len(fc):,} rows: arm x group x metric (total, capital, op) "
         "x year (2044..2050, 2044-2050) x step).",
         f"- Check figure: `{ac.rel(fig)}`.",
         "- The forcing cost is reported for the total (annualized_cost) and, alongside it, "
         "for capital only (annualized_cost_capital) and operations only "
         "(annualized_cost_op) (D46i). The figure and the table below show the total.", "",
         "| check | result | detail |", "| --- | --- | --- |"]
    t += [f"| {nm} | {'PASS' if ok else 'FAIL'} | {det} |" for nm, ok, det in checks]
    t += ["", "wecc, annualized cost, 2044-2050 total: step change per GW, billion 2024 $ per GW "
          "(columns = step, GW; wide view for the report only):", "",
          ac.md_table(wide.reset_index(), floatfmt="{:.3f}"), "",
          "Shape of the forcing-cost curve itself (2044-2050 total): n_dir_changes = number of "
          "times the forcing cost changes sign between steps (dir_change_at: level where the "
          "new step starts, GW); kink = largest change between consecutive forcing-cost "
          "values / largest |forcing cost| of the series, at level kink_at. Each year: "
          f"`{ac.rel(path)}` and the 04c shape file. Not explained here.", "",
          ac.md_table(notes), ""]
    ac.section("04f", batch, "\n".join(t))
    for nm, ok, det in checks:
        print("PASS" if ok else "FAIL", nm, det)
    print("wrote", ac.rel(path), ac.rel(fig))
    if not all(ok for _, ok, _ in checks):
        raise SystemExit("04f: a check failed; see the report")


if __name__ == "__main__":
    main()
