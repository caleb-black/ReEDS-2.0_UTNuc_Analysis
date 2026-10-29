"""04e_neighbor_table: price change in each neighbor of p25, one batch (sanity check).

docs/plan.md, stage 04_analyze, 04e; D2, D6, D7, D11, D26, D35a.

For each of the 9 neighbors of p25 (00_config/region_groups.csv, group
`neighbors`; D35a), every arm, level and solve year: the region's average
energy price and average all-in price (03a prices_region, 2024 $/MWh, D6), the
Diff against the same arm's 0 GW case (D2), and the % of the 0 GW value (D11;
blank below the analyze_common.PCT_FLOOR floor, a choice for Caleb).

Check: every Diff before 2044 is 0.

In:  outputs/03_derive/prices_region.h5, 00_config/*.csv
Out: outputs/04_analyze/04e_neighbor_prices_<batch>.csv,
     section "04e <batch>" of outputs/checks/04_analyze.md

Run:  conda run -n reeds python 04_analyze/04e_neighbor_table.py --batch UON
"""

import pandas as pd

import analyze_common as ac

METRICS = ["avg_energy_price", "avg_allin_price"]
SHOW_LEVELS = [0.5, 1.5, 3.0]
SHOW_YEAR = "2050"


def main():
    batch = ac.parse_batch(__doc__.splitlines()[0])
    nb = sorted(ac.groups(batch).query("group == 'neighbors'")["region"])
    p = pd.read_hdf(ac.IN03 / "prices_region.h5", "data",
                    where=f'batch == "{batch}" & metric in {METRICS}',
                    columns=ac.ID + ["r", "t", "metric", "value", "unit"])
    p = p[p["r"].isin(nb)].copy()
    p["t"] = p["t"].astype(int).astype(str)
    d = ac.add_diff(p, ["batch", "arm", "r", "t", "metric"])
    d = d.sort_values(["metric", "arm", "r", "t", "level"])
    path = ac.write_csv(d, "04e_neighbor_prices", batch)

    pre = d[d["t"].astype(int) < ac.FIRST_POST_YEAR]
    bad = pre[pre["diff"].fillna(0) != 0]
    checks = [("9 neighbors found", len(nb) == 9 and p["r"].nunique() == 9, " ".join(nb)),
              ("one row per case, neighbor, year, metric",
               not d.duplicated(ac.ID + ["r", "t", "metric"]).any(), ""),
              ("every Diff before 2044 is 0", bad.empty, f"{len(pre):,} rows checked, {len(bad)} not 0")]

    t = [f"## 04e_neighbor_table, {batch}", "",
         f"- Table: `{ac.rel(path)}` ({len(d):,} rows; neighbors {', '.join(nb)}).", "",
         "| check | result | detail |", "| --- | --- | --- |"]
    t += [f"| {n} | {'PASS' if ok else 'FAIL'} | {det} |" for n, ok, det in checks]
    if len(bad):
        t += ["", ac.md_table(bad[["arm", "level", "r", "t", "metric", "value", "value_0GW", "diff"]].head(60))]
    for m in METRICS:
        s = d[(d["metric"] == m) & (d["t"] == SHOW_YEAR) & d["level"].isin(SHOW_LEVELS)]
        w = s.pivot_table(index=["arm", "r"], columns="level", values="diff").reset_index()
        w.columns = ["arm", "r"] + [f"Diff {c:g} GW" for c in w.columns[2:]]
        t += ["", f"{m}, {SHOW_YEAR}, Diff in 2024 $/MWh (wide view for the report only):", "",
              ac.md_table(w, floatfmt="{:.3f}")]
    ac.section("04e", batch, "\n".join(t))
    for n, ok, det in checks:
        print("PASS" if ok else "FAIL", n, det)
    print("wrote", ac.rel(path))
    if not all(ok for _, ok, _ in checks):
        raise SystemExit("04e: a check failed; see the report")


if __name__ == "__main__":
    main()
