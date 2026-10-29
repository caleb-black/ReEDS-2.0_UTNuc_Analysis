"""04c_slopes: step slopes between neighboring levels, one batch (D41).

docs/plan.md, stage 04_analyze, 04c; D2, D26, D41, D43, D44.

For each arm, group, metric and year: the step slope between each pair of
neighboring levels, (Diff at the higher level - Diff at the lower level) /
(level change), on every level of the batch (13 in UON, 7 in UOS). No line or
curve is fitted (D41). Diff is the 04b Diff, rebuilt in memory with
analyze_common (plan rule 2). Same metrics as 04b (components are not used).

Shape notes (D46f; for the written notes in the check report, nothing is explained):
- direction change: the sign of the step slope changes between steps (steps
  with |slope| <= 1e-6 x the series' largest |slope| count as flat and are
  skipped);
- kink: the largest change between two consecutive step slopes, as a share of
  the series' largest |slope|, and the level where it happens.

In:  as 04a (via analyze_common)
Out: outputs/04_analyze/04c_slopes_<batch>.csv,
     outputs/04_analyze/04c_shape_<batch>.csv,
     section "04c <batch>" of outputs/checks/04_analyze.md

Run:  conda run -n reeds python 04_analyze/04c_slopes.py --batch UON
"""

import numpy as np
import pandas as pd

import analyze_common as ac

NOTE_METRICS = [("avg_energy_price", ["2044", "2047", "2050"]),
                ("avg_allin_price", ["2044", "2047", "2050"]),
                ("peak_avg_ratio", ["2044", "2047", "2050"]),
                ("annualized_cost", [ac.TOTAL_T]),
                ("net_imports", ["2044", "2047", "2050"]),
                ("new_lines", ["2044", "2047", "2050"])]
KINK_NOTE = 1.0   # kink >= 1: one step slope differs from the next by the series' largest |slope|


def main():
    batch = ac.parse_batch(__doc__.splitlines()[0])
    d, _, _ = ac.group_diff(batch)
    d = d[d["t"].str.slice(0, 4).astype(int) >= ac.FIRST_POST_YEAR]
    keys = ["batch", "arm", "group", "metric", "t"]
    sl = ac.step_slopes(d, keys)
    sl = sl.merge(d[["metric", "status"]].drop_duplicates(), on="metric", how="left")
    shp = ac.shape_notes(sl, keys)
    p1 = ac.write_csv(sl, "04c_slopes", batch)
    p2 = ac.write_csv(shp, "04c_shape", batch)

    nlev = ac.cases(batch).groupby("arm")["level"].nunique()
    nsteps = sl.groupby(keys).size()
    checks = [("steps per series = levels - 1 (every level used, D41)",
               bool((nsteps.groupby("arm").max() == nlev - 1).all()
                    and (nsteps.groupby("arm").min() == nlev - 1).all()),
               f"levels per arm {sorted(set(nlev))}, steps per series {sorted(set(nsteps))}")]
    # Diff at the top level = sum of step slope x step width (consistency).
    sl["w"] = sl["level_to"] - sl["level_from"]
    recon = (sl["step_slope"] * sl["w"]).groupby([sl[k] for k in keys]).sum()
    top = d.loc[d.groupby(keys)["level"].idxmax()].set_index(keys)["diff"]
    gap = ((recon - top).abs() / top.abs().where(top.abs() > 0, 1)).max()
    checks.append(("sum of step x width = Diff at the top level", gap < 1e-9,
                   f"max relative gap {gap:.2e}"))
    sl = sl.drop(columns="w")

    t = [f"## 04c_slopes, {batch}", "",
         f"- Step slopes: `{ac.rel(p1)}` ({len(sl):,} rows; post-plant years only, plus the "
         "2044-2050 annualized total and the D10 cross-check total).",
         f"- Shape notes per series: `{ac.rel(p2)}` ({len(shp):,} series).",
         "", "| check | result | detail |", "| --- | --- | --- |"]
    t += [f"| {n} | {'PASS' if ok else 'FAIL'} | {det} |" for n, ok, det in checks]
    t += ["", "### Shape notes for the check-figure metrics", "",
          "Counts of series (one per arm) with at least one direction change, and with a kink "
          f">= {KINK_NOTE:g} (change between consecutive step slopes >= the series' largest |slope|). "
          "Not explained here.", ""]
    rows = []
    for m, yrs in NOTE_METRICS:
        for grp in ac.GROUPS:
            s = shp[(shp["metric"] == m) & (shp["group"] == grp) & shp["t"].isin(yrs)]
            for yr in yrs:
                y = s[s["t"] == yr]
                dirc = y[y["n_dir_changes"] > 0]
                kk = y[y["kink"] >= KINK_NOTE]
                rows.append({"metric": m, "group": grp, "t": yr,
                             "arms_with_dir_change": " ".join(
                                 f"{a}({at})" for a, at in zip(dirc["arm"], dirc["dir_change_at"])) or "-",
                             "arms_with_kink": " ".join(
                                 f"{a}({k:.1f}@{lv:g})" for a, k, lv in zip(kk["arm"], kk["kink"], kk["kink_at"])) or "-"})
    nt = pd.DataFrame(rows)
    t += ["arm(levels where the step slope changes sign, GW at the start of the new step); "
          "arm(kink@level).", "", ac.md_table(nt), ""]
    summ = shp.assign(dir=shp["n_dir_changes"] > 0).groupby("metric").agg(
        series=("dir", "size"), with_dir_change=("dir", "sum"),
        with_kink=("kink", lambda k: int((k >= KINK_NOTE).sum()))).reset_index()
    t += ["All metrics (every group and year):", "", ac.md_table(summ), ""]
    ac.section("04c", batch, "\n".join(t))
    for n, ok, det in checks:
        print("PASS" if ok else "FAIL", n, det)
    print("wrote", ac.rel(p1), ac.rel(p2))
    if not all(ok for _, ok, _ in checks):
        raise SystemExit("04c: a check failed; see the report")


if __name__ == "__main__":
    main()
