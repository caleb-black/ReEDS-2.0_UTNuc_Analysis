"""04b_diff: Diff against the arm's own 0 GW case, one batch (D2, D11, D26).

docs/plan.md, stage 04_analyze, 04b; D2, D11, D26, D27, D43, D44.

Diff = case value minus the value of the same batch-arm's 0 GW case, same group
(or line) and year (D2). % of the 0 GW value only where D11 says: average
energy and all-in price, and system cost (annualized D44, and the D10
cross-check). Absolute only: peak/average ratio, net imports, new lines, line
use. The % is 100 x Diff / |0 GW value| and is left blank where |0 GW value| is
below a floor: 1 2024 $/MWh for prices, 1e6 2024 $ for costs (analyze_common.
PCT_FLOOR; D46a).

The group values are rebuilt in memory with analyze_common (the 04a rules);
this script does not read 04a's file (plan rule 2).

Checks: Diff at 0 GW is 0; every Diff before 2044 is 0 for prices, net imports,
new lines and line use (rows that are not are listed); annualized cost has no
year before 2044 (not reported, D44).

Check figures: Diff against level, one line per group, one panel per arm, one
figure per metric (rows = post-plant year; for the annualized cost one row, the
2044-2050 total). All in one batch (D26).

In:  as 04a (via analyze_common)
Out: outputs/04_analyze/04b_diff_<batch>.csv (groups),
     outputs/04_analyze/04b_p25_lines_diff_<batch>.csv (per line touching p25),
     outputs/04_analyze/figures/04b_diff_<metric>_<batch>.png,
     section "04b <batch>" of outputs/checks/04_analyze.md

Run:  conda run -n reeds python 04_analyze/04b_diff.py --batch UON
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import analyze_common as ac  # noqa: E402

ZERO_BEFORE_2044 = ["avg_energy_price", "avg_allin_price", "peak_avg_ratio",
                    "net_imports", "new_lines", "n_lines_at_limit_peak"]
FIG_METRICS = [("avg_energy_price", ["2044", "2047", "2050"]),
               ("avg_allin_price", ["2044", "2047", "2050"]),
               ("peak_avg_ratio", ["2044", "2047", "2050"]),
               ("annualized_cost", [ac.TOTAL_T]),
               ("net_imports", ["2044", "2047", "2050"]),
               ("new_lines", ["2044", "2047", "2050"])]
GROUP_STYLE = {"focus": ("tab:red", 2.0), "utah_rest": ("tab:orange", 1.2),
               "neighbors": ("tab:blue", 1.6), "rest_wecc": ("tab:green", 1.2),
               "wecc": ("black", 2.0)}


def line_diff(lines):
    k = ["batch", "arm", "t", "r", "rr", "trtype"]
    x = lines.assign(at_limit_any=lines["at_limit_any"].astype(float))
    long = x.melt(id_vars=ac.ID + ["t", "r", "rr", "trtype", "n_peak_blocks", "peak_h"],
                  value_vars=["util_max", "at_limit_any", "n_blocks_at_limit"],
                  var_name="metric", value_name="value")
    long["unit"] = long["metric"].map({
        "util_max": "fraction of capacity, per direction",
        "at_limit_any": "1 = at limit (>= 0.99, D37d) in any rank-1 peak block",
        "n_blocks_at_limit": "count of rank-1 peak blocks"})
    return ac.add_diff(long, k + ["metric"])


def figure(d, metric, years, batch, arms):
    height = 2.6 * len(years) + 1.2
    fig, axes = plt.subplots(len(years), len(arms), figsize=(3.1 * len(arms), height),
                             squeeze=False, sharex=True, sharey="row")
    md = d[d["metric"] == metric]
    unit = md["unit"].iloc[0].split(" (")[0] if len(md) else ""
    for i, yr in enumerate(years):
        for j, arm in enumerate(arms):
            ax = axes[i, j]
            for grp in ac.GROUPS:
                s = md[(md["t"] == yr) & (md["arm"] == arm) & (md["group"] == grp)].sort_values("level")
                if len(s):
                    c, lw = GROUP_STYLE[grp]
                    ax.plot(s["level"], s["diff"], color=c, lw=lw, marker=".", ms=4, label=grp)
            ax.axhline(0, color="0.7", lw=0.5)
            ax.tick_params(labelsize=7)
            ax.yaxis.get_offset_text().set_fontsize(7)
            if i == 0:
                ax.set_title(arm, fontsize=10)
            if j == 0:
                ax.set_ylabel(f"{yr}\nDiff, {unit}", fontsize=8)
            if i == len(years) - 1:
                ax.set_xlabel("level, GW", fontsize=8)
    h, l = axes[0, 0].get_legend_handles_labels()
    top = 1 - 0.75 / height
    fig.legend(h, l, loc="upper center", ncol=len(l), fontsize=8,
               bbox_to_anchor=(0.5, 1 - 0.35 / height))
    fig.suptitle(f"04b, {batch}: {metric}, Diff against the arm's own 0 GW case", fontsize=11,
                 y=1 - 0.05 / height)
    fig.tight_layout(rect=(0, 0, 1, top))
    ac.FIG.mkdir(parents=True, exist_ok=True)
    p = ac.FIG / f"04b_diff_{metric}_{batch}.png"
    fig.savefig(p, dpi=100)
    plt.close(fig)
    return p


def main():
    batch = ac.parse_batch(__doc__.splitlines()[0])
    d, lines, _ = ac.group_diff(batch)
    ld = line_diff(lines)
    cols = ac.ID + ["group", "t", "metric", "value", "value_0GW", "diff", "diff_pct",
                    "pct_rule", "unit", "status", "detail"]
    p1 = ac.write_csv(d[cols], "04b_diff", batch)
    p2 = ac.write_csv(ld, "04b_p25_lines_diff", batch)

    checks = []

    def chk(name, ok, detail=""):
        checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})

    n_no0 = int((d["value_0GW"].isna() & d["value"].notna()).sum())
    chk("0 GW value found for every non-blank row", n_no0 == 0,
        f"{n_no0} rows without a 0 GW value")
    z0 = d[d["level"] == 0]["diff"].fillna(0).abs().max()
    chk("Diff at 0 GW is 0", z0 == 0, f"max |Diff| at 0 GW {z0:g}")

    yr = d["t"].str.slice(0, 4).astype(int)
    pre = d[(yr < ac.FIRST_POST_YEAR) & d["metric"].isin(ZERO_BEFORE_2044)]
    bad = pre[pre["diff"].fillna(0) != 0]
    chk("every Diff before 2044 is 0 (prices, ratio, net imports, new lines, lines at limit)",
        bad.empty, f"{len(pre):,} rows checked, {len(bad)} not 0")
    lpre = ld[ld["t"].astype(int) < ac.FIRST_POST_YEAR]
    lbad = lpre[lpre["diff"].fillna(0) != 0]
    lmiss = int(lpre["value_0GW"].isna().sum())
    chk("every p25 line Diff before 2044 is 0", lbad.empty and lmiss == 0,
        f"{len(lpre):,} rows checked, {len(lbad)} not 0, {lmiss} without a 0 GW row")
    cost_pre = d[d["metric"].str.startswith("annualized") & (yr < ac.FIRST_POST_YEAR)]
    chk("annualized cost: no year before 2044 (not reported, D44)", cost_pre.empty)
    lpost_miss = int(ld["value_0GW"].isna().sum())

    pct = d[d["metric"].isin(ac.PCT_METRICS)]
    pct_blank = pct[pct["diff_pct"].isna()]
    pr = pct_blank.groupby(["metric", "group"]).size().reset_index(name="rows_blank")

    arms = list(dict.fromkeys(ac.cases(batch)["arm"]))
    paths = [figure(d, m, yrs, batch, arms) for m, yrs in FIG_METRICS]

    t = [f"## 04b_diff, {batch}", "",
         f"- Group Diff table: `{ac.rel(p1)}` ({len(d):,} rows).",
         f"- p25 line Diff table: `{ac.rel(p2)}` ({len(ld):,} rows; "
         f"{lpost_miss} rows with no 0 GW row for that line direction).",
         "- % rule (D46a): % = 100 x Diff / |0 GW value|, only for the D11 metrics "
         "(average energy and all-in price, annualized cost, D10 cross-check cost); blank where "
         f"|0 GW value| < {ac.PCT_FLOOR['price']:g} 2024 $/MWh (prices) or < "
         f"{ac.PCT_FLOOR['cost']:g} 2024 $ (costs).",
         f"- % rows blank by that floor: {len(pct_blank)} of {len(pct):,}.", ""]
    if len(pr):
        t += [ac.md_table(pr), ""]
    t += ["| check | result | detail |", "| --- | --- | --- |"]
    t += [f"| {r['check']} | {r['result']} | {r['detail']} |" for r in checks]
    if len(bad) or len(lbad):
        t += ["", "Rows before 2044 with a non-zero Diff:", ""]
        if len(bad):
            t += [ac.md_table(bad[["arm", "level", "group", "t", "metric", "value", "value_0GW", "diff"]].head(60))]
        if len(lbad):
            t += [ac.md_table(lbad[["arm", "level", "t", "r", "rr", "trtype", "metric", "value", "value_0GW", "diff"]].head(60))]
    t += ["", "Check figures (one line per group, one panel per arm):", ""]
    t += [f"- `{ac.rel(p)}`" for p in paths]
    ac.section("04b", batch, "\n".join(t))
    for r in checks:
        print(r["result"], r["check"], r["detail"])
    print("wrote", ac.rel(p1), ac.rel(p2), *[ac.rel(p) for p in paths])
    if any(r["result"] == "FAIL" for r in checks):
        raise SystemExit("04b: a check failed; see the report")


if __name__ == "__main__":
    main()
