"""03b_system_cost: system cost per region, year and case (D10).

docs/plan.md, stage 03_derive, 03b; D8, D10, D36.

From `systemcost_ba_bulk_ew` (sys_costs, r, t; 2004 $; report_params.csv L190):
- system_cost_inv = sum of the `inv_*` categories, per r and t,
- system_cost_op  = sum of the `op_*` categories,
- system_cost     = inv + op,
for t in 2044, 2047, 2050 (00_config/study_settings.csv `system_cost_years`).
D10 follows the code (report.gms L1663-L1664): in 2050 op costs are one year;
nothing is rescaled here. Also `system_cost_2044_2050` = the sum of
system_cost over the three years, per region (table system_cost_total).

Every category of the file must start with `inv_` or `op_`; any other is
listed in the report and left out (a FAIL: the D10 rule would not cover it).
A region with no row in a year gets no row (no zero is invented); the
report counts regions per case-year.

Dollars: all values x 1.6563 (D8), column converted_2004_to_2024 = True.

In:  outputs/01_ingest/outputs/systemcost_ba_bulk_ew.h5, 00_config/*.csv,
     outputs/02_clean/units.csv
Out: outputs/03_derive/system_cost.csv (r, t), system_cost_total.csv (r),
     section "03b" of outputs/checks/03_derive.md

Run:  conda run -n reeds python 03_derive/03b_system_cost.py
"""

import sys

import numpy as np
import pandas as pd

import derive_common as dc

SECTION = "03b"


def main():
    cases = dc.cases()
    years = dc.SYSTEM_COST_YEARS
    unit_in = dc.unit_of("systemcost_ba_bulk_ew")
    yw = " | ".join(f"t == {y}" for y in years)
    s = dc.read_key("systemcost_ba_bulk_ew", where=f"({yw})")
    s["Value"] = s["Value"].astype("float64")
    cats = sorted(s["sys_costs"].unique())
    part = np.select([s["sys_costs"].str.startswith("inv_"), s["sys_costs"].str.startswith("op_")],
                     ["inv", "op"], default="other")
    s["part"] = part
    other = sorted(s.loc[s.part == "other", "sys_costs"].unique())
    s = s[s.part != "other"]

    g = s.groupby(dc.CASE_COLS + ["r", "t", "part"])["Value"].sum().unstack("part")
    g = g.reindex(columns=["inv", "op"]).fillna(0.0)
    g["total"] = g["inv"] + g["op"]
    g = g * dc.DOLLAR
    long = (g.rename(columns={"inv": "system_cost_inv", "op": "system_cost_op",
                              "total": "system_cost"})
            .stack().rename("value").reset_index().rename(columns={"part": "metric"}))
    long["unit"] = "2024 $"
    long["converted_2004_to_2024"] = True
    p1 = dc.write_long(long, "system_cost")

    tot = (long[long.metric == "system_cost"].groupby(dc.CASE_COLS + ["r"])["value"]
           .agg(["sum", "count"]).reset_index())
    tot = tot.rename(columns={"sum": "value", "count": "n_years"})
    tot.insert(len(dc.CASE_COLS) + 1, "metric", "system_cost_2044_2050")
    tot["unit"] = "2024 $"
    tot["converted_2004_to_2024"] = True
    p2 = dc.write_long(tot, "system_cost_total")

    # ---------------- checks ----------------
    n_ry = long[long.metric == "system_cost"].groupby(["case", "t"])["r"].nunique()
    cases_found = long["case"].nunique()
    raw_sum = s["Value"].sum() * dc.DOLLAR
    out_sum = long.loc[long.metric == "system_cost", "value"].sum()
    checks = [
        ("Unit of input (02d lookup)", "PASS" if unit_in == "2004 $" else "FAIL", unit_in),
        ("Cases with rows", "PASS" if cases_found == len(cases) else "FAIL",
         f"{cases_found} of {len(cases)}"),
        ("Every category is `inv_*` or `op_*`", "PASS" if not other else "FAIL",
         ", ".join(other) or f"{len(cats)} categories, all inv_ or op_"),
        ("Years per case", "PASS" if long.groupby("case")["t"].nunique().eq(len(years)).all()
         else "FAIL", ", ".join(str(y) for y in years)),
        ("Regions per case-year = 34", "PASS" if (n_ry == 34).all() else "INFO",
         f"min {n_ry.min()}, max {n_ry.max()}"),
        ("Sum of output = sum of input x factor", "PASS"
         if abs(out_sum - raw_sum) <= 1e-9 * abs(raw_sum) else "FAIL",
         f"{out_sum:,.6g} vs {raw_sum:,.6g}"),
        ("Every region has 3 years in system_cost_total", "PASS" if (tot.n_years == 3).all()
         else "INFO", f"min {tot.n_years.min()}"),
    ]
    fail = any(c[1] == "FAIL" for c in checks)

    samp = long[long.case.isin(dc.SAMPLE_CASES) & (long.r == dc.FOCUS)].pivot_table(
        index=["case", "t"], columns="metric", values="value").reset_index()
    samp_tot = tot[tot.case.isin(dc.SAMPLE_CASES) & tot.r.isin([dc.FOCUS])][
        ["case", "r", "value"]]
    wecc = (tot[tot.case.isin(dc.SAMPLE_CASES)].groupby("case")["value"].sum()
            .rename("sum over 34 regions").reset_index())
    cat_tab = (s[s.case.isin(dc.SAMPLE_CASES[:1])].groupby(["sys_costs", "part"])["Value"]
               .sum().mul(dc.DOLLAR).rename("UON ref 0 GW, 2044+2047+2050, 2024 $").reset_index())

    text = [
        f"## 03b_system_cost — {'FAIL' if fail else 'PASS'}\n",
        "Rule D10: sum of `inv_*` and `op_*` from `systemcost_ba_bulk_ew`, for 2044, 2047, 2050; "
        "in 2050 op costs are one year (as the code does, `report.gms` L1663-L1664). "
        f"All values x {dc.DOLLAR} (D8; converted: system_cost_inv, system_cost_op, system_cost, "
        "system_cost_2044_2050).\n",
        f"Tables: `{dc.rel(p1)}` ({len(long):,} rows), `{dc.rel(p2)}` ({len(tot):,} rows).\n",
        "### Checks\n",
        dc.md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Categories (UON `ref` 0 GW)\n",
        dc.md_table(cat_tab, floatfmt="{:,.6g}") + "\n",
        "### Verifier sample cases: p25 (2024 $)\n",
        dc.md_table(samp, floatfmt="{:,.6g}") + "\n",
        "Sum over 2044, 2047, 2050:\n",
        dc.md_table(samp_tot, floatfmt="{:,.6g}") + "\n",
        dc.md_table(wecc, floatfmt="{:,.6g}") + "\n",
    ]
    dc.write_section(SECTION, "\n".join(text))
    print(f"03b done: {'FAIL' if fail else 'PASS'}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
