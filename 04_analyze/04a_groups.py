"""04a_groups: every go-on metric for the five region groups, one batch (D43a).

docs/plan.md, stage 04_analyze, 04a; D6, D7, D13, D14, D26, D35a, D36, D37b,
D37f, D43, D44, D45; data_dictionary.md "Metrics" (group aggregation column).

Metrics (D43a, D44):
- avg_energy_price, avg_allin_price: group sum of dollars / group sum of `load`
  quantity (D6), from 03a prices_region (2024 $).
- peak_avg_ratio: group peak (highest block of 03a group_block_price, D14) /
  group average energy price; blank where the average is <= 0 (D37b).
- annualized_cost, _capital, _op (D44, 03b2): sum over members; t = 2044..2050
  and t = "2044-2050" (undiscounted 7-year total from annualized_cost_total).
- d10_system_cost, _inv, _op (D10, 03b): secondary cross-check only, labeled in
  the `status` column; t = 2044, 2047, 2050 and "2044+2047+2050".
- net_imports (MWh, `net_import_ann_rep`) and new_lines (MW, `invtran_out`),
  read from the stage 01 files (D36, D37f), all solve years.
- n_lines_at_limit_peak (focus only) and the per-line table: line use in p25's
  rank-1 peak block(s), per line touching p25 (03f line_use_peak; D46b, D46c).
Components (load_quant, energy_dollars, allin_dollars, peak_energy_price with
its block names) are kept with status "component" so the group values can be
recomputed; they are not diffed. Peak price alone is on hold (D43a, D46e).

The rules are in analyze_common.py (shared with 04b, 04c, 04f; plan rule 2).

In:  outputs/03_derive/{prices_region,group_block_price,line_use_peak}.h5,
     annualized_cost.csv, annualized_cost_total.csv, system_cost.csv,
     system_cost_total.csv; outputs/01_ingest/outputs/{net_import_ann_rep,
     invtran_out}.h5; 00_config/*.csv; outputs/02_clean/units.csv
Out: outputs/04_analyze/04a_groups_<batch>.csv,
     outputs/04_analyze/04a_p25_lines_<batch>.csv,
     section "04a <batch>" of outputs/checks/04_analyze.md

Run:  conda run -n reeds python 04_analyze/04a_groups.py --batch UON
"""

import numpy as np
import pandas as pd

import analyze_common as ac

SUMMED = ["annualized_cost", "annualized_cost_capital", "annualized_cost_op",
          "d10_system_cost", "d10_system_cost_inv", "d10_system_cost_op",
          "net_imports", "load_quant", "energy_dollars", "allin_dollars"]


def main():
    batch = ac.parse_batch(__doc__.splitlines()[0])
    df, lines, cost_units = ac.build_groups(batch)
    p1 = ac.write_csv(df, "04a_groups", batch)
    p2 = ac.write_csv(lines, "04a_p25_lines", batch)

    c = ac.cases(batch)
    checks = []

    def chk(name, ok, detail=""):
        checks.append({"check": name, "result": "PASS" if ok else "FAIL", "detail": detail})

    lv = c.groupby("arm")["level"].agg(["count", "min", "max"])
    chk("cases per arm", lv["count"].nunique() == 1,
        "; ".join(f"{a}: {r['count']} levels {r['min']:g}-{r['max']:g} GW" for a, r in lv.iterrows()))
    chk("every arm has a 0 GW case", bool((lv["min"] == 0).all()))
    g = ac.groups(batch).groupby("group").size()
    chk("group sizes focus 1, utah_rest 1, neighbors 9, rest_wecc 23, wecc 34",
        g.to_dict() == {"focus": 1, "utah_rest": 1, "neighbors": 9, "rest_wecc": 23, "wecc": 34},
        str(g.to_dict()))
    pr = df[df["metric"] == "avg_energy_price"]
    nr = pr.groupby("group")["n_regions"].agg(["min", "max"])
    chk("price rows: every member region present in every case-year",
        all(nr.loc[k, "min"] == nr.loc[k, "max"] == g[k] for k in g.index),
        str(nr.to_dict("index")))
    cnt = df.groupby("metric").agg(rows=("value", "size"), cases=("case", "nunique"),
                                   groups=("group", "nunique"), years=("t", "nunique"),
                                   blank=("value", lambda s: int(s.isna().sum())))
    chk("every metric covers every case", bool((cnt["cases"] == len(c)).all()))
    dup = df.duplicated(ac.ID + ["group", "t", "metric"]).sum()
    chk("one row per case, group, year, metric", dup == 0, f"{dup} duplicates")

    # Sums: the four groups add up to wecc.
    s = df[df["metric"].isin(SUMMED)]
    four = s[s["group"] != "wecc"].groupby(["case", "t", "metric"])["value"].sum()
    w = s[s["group"] == "wecc"].set_index(["case", "t", "metric"])["value"]
    absum = s[s["group"] != "wecc"].assign(a=lambda x: x["value"].abs()).groupby(
        ["case", "t", "metric"])["a"].sum()
    rel = ((four - w).abs() / absum.where(absum > 0, 1)).max()
    chk("summed metrics: focus + utah_rest + neighbors + rest_wecc = wecc", rel < 1e-9,
        f"max gap / sum of |group values| {rel:.2e}")
    # Prices: wecc average is the load-weighted mean of the four groups (D6).
    q = df[df["metric"].isin(["energy_dollars", "load_quant"])].pivot_table(
        index=["case", "t", "group"], columns="metric", values="value").reset_index()
    a = q[q["group"] != "wecc"].groupby(["case", "t"])[["energy_dollars", "load_quant"]].sum()
    ww = q[q["group"] == "wecc"].set_index(["case", "t"])
    pg = ((a["energy_dollars"] / a["load_quant"]) / (ww["energy_dollars"] / ww["load_quant"]) - 1).abs().max()
    chk("wecc energy price = load-weighted mean of the four groups", pg < 1e-9,
        f"max relative gap {pg:.2e}")
    k = ac.ID + ["group", "t"]
    ratio = df[df["metric"] == "peak_avg_ratio"].merge(
        df[df["metric"] == "avg_energy_price"][k + ["value"]].rename(columns={"value": "avg"}), on=k)
    nblank = int(ratio["value"].isna().sum())
    chk("peak/average ratio blank exactly where group average <= 0 (D37b)",
        bool((ratio["value"].isna() == (ratio["avg"] <= 0)).all()), f"{nblank} blank rows")
    ac_yrs = sorted(df.loc[df["metric"] == "annualized_cost", "t"].unique(),
                    key=lambda x: (len(x), x))
    chk("annualized cost years 2044..2050 and 2044-2050", ac_yrs == [str(y) for y in range(2044, 2051)] + [ac.TOTAL_T],
        " ".join(ac_yrs))
    fill = df.loc[df["metric"].isin(["annualized_cost", "d10_system_cost"]), "n_missing_filled"].sum()
    chk("cost rows: no group-year missing in stage 03 (zero-filled count)", fill == 0, f"{int(fill)} filled")
    tot = df[(df["metric"] == "annualized_cost") & (df["t"] == ac.TOTAL_T)].set_index(["case", "group"])["value"]
    yr = df[(df["metric"] == "annualized_cost") & (df["t"] != ac.TOTAL_T)].groupby(["case", "group"])["value"].sum()
    tg = ((yr - tot).abs() / tot.abs()).max()
    chk("annualized cost: sum of 2044..2050 = 2044-2050 total", tg < 1e-9, f"max relative gap {tg:.2e}")
    allin_ns = df[(df["metric"] == "avg_allin_price") & df["unit"].str.contains("not stated")]
    nl = lines.groupby(["t", "case"]).size().groupby("t").agg(["min", "max"])
    chk("p25 line table: same line directions in every case of a year",
        bool((nl["min"] == nl["max"]).all()),
        "; ".join(f"{t}: {r['min']}" for t, r in nl.iterrows()))
    ties = lines.groupby(["case", "t"])["n_peak_blocks"].first()

    t = [f"## 04a_groups, {batch}", "",
         f"- Group table: `{ac.rel(p1)}` ({len(df):,} rows; {df['metric'].nunique()} metrics, "
         f"{df['case'].nunique()} cases, {len(ac.GROUPS)} groups).",
         f"- p25 line table: `{ac.rel(p2)}` ({len(lines):,} rows).",
         f"- Arms: {', '.join(lv.index)}; levels per arm: {int(lv['count'].iloc[0])}.",
         f"- Stage 03 cost units read: {sorted(cost_units)} (already 2024 $; not converted again).",
         f"- All-in price rows whose unit is not stated (state_rps/nat_gen dollars in a member "
         f"region, from 03a): {len(allin_ns):,} of {int((df['metric'] == 'avg_allin_price').sum()):,}"
         f" ({', '.join(sorted(allin_ns['group'].unique())) or 'none'}).",
         f"- p25 peak block ties (rank-1 blocks per case-year): "
         f"{ties.value_counts().sort_index().to_dict()}; per line direction: highest "
         "utilization over the tied blocks, number of tied blocks at limit, at limit in any (D46b).",
         "- Zero-fill (D46h): a case-group-year with no stage 01 row for any member is 0. "
         + "; ".join(f"{m}: {int(df.loc[df['metric'] == m, 'n_missing_filled'].sum()):,} of "
                     f"{int((df['metric'] == m).sum()):,} group rows filled"
                     for m in ("net_imports", "new_lines"))
         + " (missing member rows inside a group that has other rows count as 0 in the sum).", "",
         "| check | result | detail |", "| --- | --- | --- |"]
    t += [f"| {r['check']} | {r['result']} | {r['detail']} |" for r in checks]
    t += ["", "Rows per metric:", "", ac.md_table(cnt.reset_index()), ""]
    ac.section("04a", batch, "\n".join(t))
    for r in checks:
        print(r["result"], r["check"], r["detail"])
    print("wrote", ac.rel(p1), ac.rel(p2))
    if any(r["result"] == "FAIL" for r in checks):
        raise SystemExit("04a: a check failed; see the report")


if __name__ == "__main__":
    main()
