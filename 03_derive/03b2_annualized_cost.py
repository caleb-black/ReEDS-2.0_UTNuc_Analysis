"""03b2_annualized_cost: annualized system cost per region, year and case (D44).

docs/plan.md, stage 03_derive, 03b2; D8, D26, D36, D44. Primary system cost
metric (D44); 03b (D10) stays as the cross-check.

Method: reeds/results.py calc_systemcost, cost_type "annualized"
(L371-466 at 0c0ea27), with its defaults (L265-277):
- `shift_capital=True` (L274): payments start in the build year, crf divided
  by (1 + discount_rate) (L418-424); discount_rate = DEFAULT_DISCOUNT_RATE =
  0.02 (L272; postprocessing/bokehpivot/defaults.py L5).
- `crf_from_user=False` (L276): the case's own `crf` (L310, L411-416),
  reindexed to every year, linear interpolation, then back-filled.
- `remove_existing=False` (L275): ReEDS adds pre-2010 capital
  (`df_capex_init`, L311-314) to `inv_investment_capacity_costs` in the years
  before the first model year (L380-398). Left out here (D44, plan 03b2).
  It cannot reach 2044-2050: it sits in years <= 2009, only in a 30-year
  (non-transmission) category, and the 30-year window of 2044 starts in 2015
  (rolling sum, L437-439). The report checks this.
Steps (per case and region):
1. Capital and operation categories: as gather_cost_types (L230-262), from
   postprocessing/bokehpivot/in/reeds2/cost_cat_map.csv at 0c0ea27
   (`cost_type` Capital / Operation). The report checks that this equals the
   `inv_*` / `op_*` split of D44.
2. Pivot categories to columns; add every year from first model year -
   sys_eval_years to last model year + max(sys_eval_years, trans_crp), for every
   region (L373-378). Capital NaN -> 0 (L430), x crf/(1+0.02) of its own year
   (L429-432).
3. Capital payment in year Y = rolling sum over the last sys_eval_years years
   (30) of step 2; over trans_crp years (40) for the transmission categories
   (L349-356: inv_converter_costs, inv_transmission_line_investment,
   inv_transmission_interzone_ac_investment,
   inv_transmission_interzone_dc_investment) (L437-443).
4. Operations: 0 where missing in a solve year (L457-460), then forward-filled
   up to sys_eval_years - 1 years (L462-465): each solve year's operations fill
   the years up to the next solve year.
sys_eval_years from 00a (`outputs/00_config/case_switches.csv`, the case's
switches.csv, read as results.py L316, L335); trans_crp from 01b
(`scalars.h5`, the case's scalars.csv, read as results.py L317, L336).
Regions: the batch's 34 zones (00_config/region_groups.csv, `wecc`), where
results.py uses the case's `r` set (L320); a region with no row gets 0.

Not done here (results.py does it, but it does not change the annualized
values): inflate_series to 2024 $ with deflator.csv (L344, L219-227; D8 uses
1.6563 instead), the 1e-9 scaling (L330), discounting (L476-480), the
2024-2050 filter (L487-488), drop_zeros (L499-501).

Dollars: all values x 1.6563 (D8), column converted_2004_to_2024 = True.

Checks (report section "03b2"): category map, split, regions, sys_eval_years
and trans_crp, pre-2010 window, a second independent calculation (explicit
sum over build years) for the Verifier sample cases, and the plan check
against the run's own outputs/post_systemcost_annualized.csv if that file
exists (read only for this check; rescaled from its deflator.csv dollar year).
Also the converter-cost carry-over (decisions.md On hold): Diff of annualized
inv_converter_costs against the 0 GW case of UON `ref`, 2044-2050 (D2, D26).

In:  outputs/01_ingest/outputs/systemcost_ba.h5, outputs/01_ingest/inputs/crf.h5,
     outputs/01_ingest/inputs/scalars.h5, outputs/00_config/case_switches.csv,
     00_config/*.csv, outputs/02_clean/units.csv
Out: outputs/03_derive/annualized_cost.csv            (r, t: capital, op, total)
     outputs/03_derive/annualized_cost_total.csv      (r: 2044-2050 sums)
     outputs/03_derive/annualized_cost_category.h5    (r, t, sys_costs; non-zero rows)
     outputs/03_derive/converter_carryover.csv        (UON ref, Diff by r, t, level)
     section "03b2" of outputs/checks/03_derive.md

Run:  conda run -n reeds python 03_derive/03b2_annualized_cost.py
"""

import io
import sys
from itertools import product
from pathlib import Path

import numpy as np
import pandas as pd

import derive_common as dc

SECTION = "03b2"
YEARS = list(range(2044, 2051))          # D44: each year 2044 to 2050
DISCOUNT_RATE = 0.02                     # results.py L272; bokehpivot/defaults.py L5
TRANS_CATS = [                           # results.py L349-356 at 0c0ea27
    "inv_converter_costs",
    "inv_transmission_line_investment",
    "inv_transmission_interzone_ac_investment",
    "inv_transmission_interzone_dc_investment",
]
EXPECTED_SYS_EVAL_YEARS = 30             # D44
EXPECTED_TRANS_CRP = 40                  # D44
CHECK_CASE = "UON_20261022_0G_ref"       # plan 03b2 check: UON ref 0 GW
CONV = "inv_converter_costs"
REL_TOL = 1e-9
SWITCHES_CSV = dc.REPO / "outputs" / "00_config" / "case_switches.csv"


# ---------------------------------------------------------------------------
# Inputs
# ---------------------------------------------------------------------------
def cost_cat_map():
    """cost_cat_map.csv at 0c0ea27, as gather_cost_types reads it (L235-239)."""
    return pd.read_csv(io.BytesIO(dc._git_show(
        "postprocessing/bokehpivot/in/reeds2/cost_cat_map.csv")))


def deflator_2024():
    """deflator.csv at 0c0ea27, row 2024 (inflate_series L219-227; defaults.py L1)."""
    d = pd.read_csv(io.BytesIO(dc._git_show("inputs/financials/deflator.csv")), index_col=0)
    return float(d.loc[2024, "Deflator"])


def case_params(cases):
    """sys_eval_years (00a) and trans_crp (01b) per case."""
    sw = pd.read_csv(SWITCHES_CSV, dtype=str)
    sev = sw[sw["switch"] == "sys_eval_years"].set_index("case")["value"]
    sc = pd.read_hdf(dc.IN_INP / "scalars.h5", "data", where='name == "trans_crp"')
    tcrp = sc.set_index("case")["value"]
    out = cases[["case"]].copy()
    out["sys_eval_years"] = out["case"].map(sev)
    out["trans_crp"] = out["case"].map(tcrp)
    return out


# ---------------------------------------------------------------------------
# Main calculation: port of results.py L371-466 (annualized), without df_capex_init
# ---------------------------------------------------------------------------
def annualize_case(sc, crf_in, regions, cap_cats, op_cats, sev, tcrp):
    """One case. sc: sys_costs, r, t, Value (2004 $). crf_in: t, Value.

    Returns wide table indexed by (year, r), one column per category, 2004 $.
    """
    all_cats = list(cap_cats) + list(op_cats)
    df = sc.rename(columns={"t": "year", "sys_costs": "cost_cat"})         # L323
    # gather_cost_types uses the categories of this case only (L242-262).
    present = set(df["cost_cat"])
    cap_cats = [c for c in cap_cats if c in present]
    op_cats = [c for c in op_cats if c in present]
    sim_years = sorted(df["year"].unique())                                  # L334
    addyears = max(sev, tcrp)                                                # L337
    first, last = int(df["year"].min()), int(df["year"].max())               # L338
    trans = [c for c in cap_cats if c in TRANS_CATS]                         # L349-356
    nontrans = [c for c in cap_cats if c not in trans]                       # L357

    df = df.pivot_table(index=["year", "r"], columns="cost_cat",
                        values="Value").reset_index()                        # L373
    full_yrs = list(range(first - sev, last + addyears + 1))                 # L376
    allyrs = pd.DataFrame(list(product(full_yrs, regions)), columns=["year", "r"])
    df = pd.merge(allyrs, df, on=["year", "r"], how="left")                  # L377-378
    # L380-398 (pre-2010 capital, df_capex_init): left out (D44).

    crf = (crf_in.rename(columns={"t": "year", "Value": "crf"})
           .set_index("year")[["crf"]].astype("float64").reindex(full_yrs))  # L413-414
    crf.index.name = "year"
    crf = crf.interpolate(method="linear")                                   # L415
    crf["crf"] = crf["crf"].bfill()                                          # L416
    crf = crf / (1 + DISCOUNT_RATE)                                          # L418-424
    df = pd.merge(left=df.set_index("year"), right=crf, how="left",
                  on=["year"], sort=False)                                   # L429
    df[cap_cats] = df[cap_cats].fillna(0)                                    # L430
    df[cap_cats] = df[cap_cats].multiply(df["crf"], axis="index")            # L432

    df = df.reset_index().set_index(["r", "year"]).sort_index()              # L435
    if nontrans:
        df[nontrans] = (df.groupby("r")[nontrans].rolling(sev).sum()
                        ).reset_index(level=0, drop=True)                    # L437-439
    if trans:
        df[trans] = (df.groupby("r")[trans].rolling(tcrp).sum()
                     ).reset_index(level=0, drop=True)                       # L441-443
    df = df.reset_index()

    keep_yrs = list(range(first, last + addyears + 1))                       # L447-448
    df = df.loc[df["year"].isin(keep_yrs)]
    is_sim = df["year"].isin(sim_years)
    df.loc[is_sim, op_cats] = df.loc[is_sim, op_cats].fillna(0)              # L457-460
    df.loc[:, op_cats] = df.groupby("r")[op_cats].ffill(limit=sev - 1)       # L462-465
    df = df.fillna(0)                                                        # L466
    out = df.set_index(["year", "r"]).reindex(columns=all_cats, fill_value=0.0)
    out.columns.name = "sys_costs"
    return out


# ---------------------------------------------------------------------------
# Second, independent calculation (check): explicit sum over build years
# ---------------------------------------------------------------------------
def annualize_direct(sc, crf_in, cap_cats, sev, tcrp, years, build_before=None):
    """Payment(Y) = sum over solve years b in (Y - window, Y] of capital(b) x
    crf(b) / 1.02; op(Y) = op of the latest solve year <= Y. Plain loops.

    build_before: if set, count only capital built before that year.
    Returns dict (r, Y, cat) -> value (2004 $).
    """
    ct = crf_in.sort_values("t")
    xs, ys = ct["t"].to_numpy(float), ct["Value"].to_numpy(float)

    def crf_of(t):     # given value; between given years linear, outside constant
        return float(np.interp(t, xs, ys))

    solve = sorted(int(t) for t in sc["t"].unique())
    out = {}
    for r_, cat, t, v in zip(sc["r"], sc["sys_costs"], sc["t"], sc["Value"]):
        t = int(t)
        if cat in cap_cats:
            if build_before is not None and t >= build_before:
                continue
            w = tcrp if cat in TRANS_CATS else sev
            for y in years:
                if y - w < t <= y:
                    out[(r_, y, cat)] = out.get((r_, y, cat), 0.0) + \
                        float(v) * crf_of(t) / (1 + DISCOUNT_RATE)
        elif build_before is None:
            for y in years:
                last_solve = max(s for s in solve if s <= y)
                if t == last_solve and y - t <= sev - 1:
                    out[(r_, y, cat)] = out.get((r_, y, cat), 0.0) + float(v)
    return out


def rel_gap(a, b):
    return abs(a - b) / max(abs(a), abs(b), 1e-300)


# ---------------------------------------------------------------------------
def main():
    cases = dc.cases()
    rg = dc.region_groups()
    regions_by_batch = {b: sorted(g.loc[g["group"] == "wecc", "region"])
                        for b, g in rg.groupby("batch")}
    unit_in = dc.unit_of("systemcost_ba")
    s = dc.read_key("systemcost_ba")
    s["Value"] = s["Value"].astype("float64")
    s["t"] = s["t"].astype("int64")
    crf_all = pd.read_hdf(dc.IN_INP / "crf.h5", "data")
    crf_all["t"] = crf_all["t"].astype("int64")
    params = case_params(cases).set_index("case")

    # ---- categories (gather_cost_types, L230-262) ----
    cmap = cost_cat_map()
    cats = sorted(s["sys_costs"].unique())
    unmapped = [c for c in cats if c not in set(cmap["raw"])]
    cap_all = set(cmap.loc[cmap["cost_type"] == "Capital", "raw"])
    op_all = set(cmap.loc[cmap["cost_type"] == "Operation", "raw"])
    prefix_mismatch = [c for c in cats
                       if (c in cap_all) != c.startswith("inv_")
                       or (c in op_all) != c.startswith("op_")]
    bad_regions = sorted({(b, r_) for b, r_ in zip(s["batch"], s["r"])
                          if r_ not in regions_by_batch[b]})

    stop_reasons = []
    if unmapped:
        stop_reasons.append(f"categories not in cost_cat_map.csv: {unmapped}")
    if prefix_mismatch:
        stop_reasons.append(f"cost_cat_map split differs from inv_/op_ split: {prefix_mismatch}")
    if bad_regions:
        stop_reasons.append(f"regions outside the 34 zones: {bad_regions}")
    p_sev = params["sys_eval_years"].astype(float)
    p_tc = params["trans_crp"].astype(float)
    if p_sev.isna().any() or p_tc.isna().any():
        stop_reasons.append("sys_eval_years or trans_crp missing for "
                            f"{sorted(params.index[p_sev.isna() | p_tc.isna()])}")
    if (p_sev != EXPECTED_SYS_EVAL_YEARS).any() or (p_tc != EXPECTED_TRANS_CRP).any():
        stop_reasons.append(f"sys_eval_years not {EXPECTED_SYS_EVAL_YEARS} or trans_crp "
                            f"not {EXPECTED_TRANS_CRP} in some case (D44)")
    missing_cases = sorted(set(cases["case"]) - set(s["case"]))
    missing_crf = sorted(set(cases["case"]) - set(crf_all["case"]))
    if missing_cases or missing_crf:
        stop_reasons.append(f"no systemcost_ba rows: {missing_cases}; no crf: {missing_crf}")
    if stop_reasons:
        # Checks that decide whether the method applies: stop, write nothing else.
        text = ["## 03b2_annualized_cost — FAIL (stopped before the calculation)\n",
                *[f"- {r_}" for r_ in stop_reasons]]
        dc.write_section(SECTION, "\n".join(text) + "\n")
        print("03b2 STOP:\n  " + "\n  ".join(stop_reasons))
        return 1

    cap_cats = [c for c in cats if c in cap_all]
    op_cats = [c for c in cats if c in op_all]

    # ---- main calculation, per case ----
    cat_frames, crf_interp = [], []
    for row in cases.itertuples(index=False):
        sc = s.loc[s["case"] == row.case, ["sys_costs", "r", "t", "Value"]]
        cf = crf_all.loc[crf_all["case"] == row.case, ["t", "Value"]]
        solve_cap = sorted(sc.loc[sc["sys_costs"].isin(cap_cats), "t"].unique())
        crf_interp.append((row.case, [t for t in solve_cap if t not in set(cf["t"])]))
        w = annualize_case(sc, cf, regions_by_batch[row.batch], cap_cats, op_cats,
                           int(params.loc[row.case, "sys_eval_years"]),
                           int(params.loc[row.case, "trans_crp"]))
        w = w.loc[w.index.get_level_values("year").isin(YEARS)]
        lg = w.stack().rename("value_2004").reset_index().rename(columns={"year": "t"})
        for c in dc.CASE_COLS:
            lg[c] = getattr(row, c)
        cat_frames.append(lg)
    cat = pd.concat(cat_frames, ignore_index=True)
    cat["part"] = np.where(cat["sys_costs"].isin(cap_cats), "capital", "op")
    cat["value"] = cat["value_2004"] * dc.DOLLAR

    # ---- long tables ----
    g = cat.groupby(dc.CASE_COLS + ["r", "t", "part"])["value"].sum().unstack("part")
    g = g.reindex(columns=["capital", "op"]).fillna(0.0)
    g["total"] = g["capital"] + g["op"]
    long = (g.rename(columns={"capital": "annualized_cost_capital",
                              "op": "annualized_cost_op", "total": "annualized_cost"})
            .stack().rename("value").reset_index().rename(columns={"part": "metric"}))
    long["unit"] = "2024 $"
    long["converted_2004_to_2024"] = True
    p1 = dc.write_long(long, "annualized_cost")

    tot = (long.groupby(dc.CASE_COLS + ["r", "metric"])["value"]
           .agg(["sum", "count"]).reset_index()
           .rename(columns={"sum": "value", "count": "n_years"}))
    tot["metric"] = tot["metric"] + "_2044_2050"
    tot["unit"] = "2024 $ (undiscounted sum of 2044-2050)"
    tot["converted_2004_to_2024"] = True
    p2 = dc.write_long(tot, "annualized_cost_total")

    cat_out = cat.loc[cat["value"] != 0, dc.CASE_COLS + ["r", "t", "sys_costs", "part",
                                                         "value"]].copy()
    cat_out["unit"] = "2024 $"
    cat_out["converted_2004_to_2024"] = True
    p3 = dc.write_long(cat_out, "annualized_cost_category", big=True)

    # ---- check: second independent calculation, sample cases ----
    ind_rows = []
    for case in dc.SAMPLE_CASES:
        sc = s.loc[s["case"] == case]
        cf = crf_all.loc[crf_all["case"] == case]
        d = annualize_direct(sc, cf, set(cap_cats), int(params.loc[case, "sys_eval_years"]),
                             int(params.loc[case, "trans_crp"]), YEARS)
        mine = cat[cat["case"] == case].set_index(["r", "t", "sys_costs"])["value_2004"]
        keys = set(d) | set(k for k, v in mine.items() if v != 0)
        worst, n = 0.0, 0
        for k in keys:
            a, b = mine.get(k, 0.0), d.get(k, 0.0)
            if a == 0 and b == 0:
                continue
            n += 1
            worst = max(worst, rel_gap(a, b))
        nat_m = mine.groupby(level="t").sum()
        nat_d = pd.Series(d).groupby(level=1).sum()
        nat_gap = max(rel_gap(nat_m.get(y, 0.0), nat_d.get(y, 0.0)) for y in YEARS)
        ind_rows.append((case, n, worst, nat_gap))
    ind = pd.DataFrame(ind_rows, columns=["case", "region-year-category values",
                                          "max relative gap", "max relative gap, national by year"])
    ind_ok = bool((ind["max relative gap"] <= REL_TOL).all())

    # ---- national values of the check case (both calculations), 2024 $ ----
    sc0 = s.loc[s["case"] == CHECK_CASE]
    d0 = annualize_direct(sc0, crf_all.loc[crf_all["case"] == CHECK_CASE], set(cap_cats),
                          int(params.loc[CHECK_CASE, "sys_eval_years"]),
                          int(params.loc[CHECK_CASE, "trans_crp"]), YEARS)
    d0s = pd.Series(d0)
    d0s.index.names = ["r", "t", "sys_costs"]
    d0n = (d0s.reset_index(name="v")
           .assign(part=lambda x: np.where(x["sys_costs"].isin(cap_cats), "capital", "op"))
           .groupby(["t", "part"])["v"].sum().unstack("part").reindex(YEARS).fillna(0)
           * dc.DOLLAR)
    m0 = (long[(long["case"] == CHECK_CASE)].groupby(["t", "metric"])["value"].sum()
          .unstack("metric").reindex(YEARS))
    nat_cmp = pd.DataFrame({
        "t": YEARS,
        "capital, 03b2": m0["annualized_cost_capital"].values,
        "capital, second calc": d0n["capital"].values,
        "op, 03b2": m0["annualized_cost_op"].values,
        "op, second calc": d0n["op"].values,
    })
    nat_cmp["max relative gap"] = [
        max(rel_gap(a, b), rel_gap(c, e)) for a, b, c, e in
        nat_cmp[["capital, 03b2", "capital, second calc", "op, 03b2", "op, second calc"]]
        .itertuples(index=False)]

    # ---- plan check: the run's own post_systemcost_annualized.csv ----
    runs_root = Path(dc.SETTINGS["runs_root"])
    post = runs_root / CHECK_CASE / "outputs" / "post_systemcost_annualized.csv"
    defl = deflator_2024()
    rescale = dc.DOLLAR * defl   # file is 2024 $ via deflator.csv; to 2004 $, then x 1.6563
    if post.is_file():
        pf = pd.read_csv(post)
        pf = pf[pf["year"].isin(YEARS)]
        pf["part"] = np.where(pf["cost_cat"].isin(cap_all), "capital", "op")
        pn = (pf.groupby(["year", "part"])["Cost (Bil $)"].sum().unstack("part")
              .reindex(YEARS).fillna(0) * 1e9 * rescale)
        post_cmp = pd.DataFrame({
            "t": YEARS,
            "capital, 03b2": m0["annualized_cost_capital"].values,
            "capital, ReEDS file (rescaled)": pn["capital"].values,
            "op, 03b2": m0["annualized_cost_op"].values,
            "op, ReEDS file (rescaled)": pn["op"].values,
        })
        post_cmp["capital rel. gap"] = [rel_gap(a, b) for a, b in zip(
            post_cmp.iloc[:, 1], post_cmp.iloc[:, 2])]
        post_cmp["op rel. gap"] = [rel_gap(a, b) for a, b in zip(
            post_cmp.iloc[:, 3], post_cmp.iloc[:, 4])]
        post_text = [f"`{post}` found. Its `Cost (Bil $)` is in 2024 $ via "
                     f"`deflator.csv` (2024 deflator {defl:.9g}, results.py L344, L219-227); "
                     f"rescaled by x 1e9 x {defl:.9g} x {dc.DOLLAR} to D8 2024 $. It includes "
                     "the pre-2010 capital (remove_existing=False), which is 0 in 2044-2050 "
                     "(see the window check).\n",
                     dc.md_table(post_cmp, floatfmt="{:,.6g}") + "\n"]
        post_found = True
        post_ok = bool((post_cmp[["capital rel. gap", "op rel. gap"]] <= 1e-4).all().all())
    else:
        post_text = [f"`{post}` does not exist (the run folders hold only `outputs.h5` and "
                     "`inputs_case`). The plan check is replaced by the second, independent "
                     "calculation above (explicit sum over build years), shown for this case "
                     "below.\n"]
        post_found, post_ok = False, None

    # ---- converter carry-over (On hold item), UON ref, Diff vs 0 GW (D2, D26) ----
    ref = cases[(cases["batch"] == "UON") & (cases["arm"] == "ref")]
    base = ref.loc[ref["level"] == 0.0, "case"].iloc[0]
    conv = cat[(cat["case"].isin(ref["case"])) & (cat["sys_costs"] == CONV)]
    conv = conv.set_index(["case", "r", "t"])["value"]
    # Part of the payment from converters built before 2044 (explicit sum).
    pre = {}
    for c in ref["case"]:
        sc = s.loc[(s["case"] == c) & (s["sys_costs"] == CONV)]
        dd = annualize_direct(sc, crf_all.loc[crf_all["case"] == c], {CONV},
                              int(params.loc[c, "sys_eval_years"]),
                              int(params.loc[c, "trans_crp"]), YEARS, build_before=2044)
        for (r_, y, _), v in dd.items():
            pre[(c, r_, y)] = v * dc.DOLLAR
    pre = pd.Series(pre, dtype="float64")
    rows = []
    for c, lev in zip(ref["case"], ref["level"]):
        for r_ in regions_by_batch["UON"]:
            for y in YEARS:
                v = conv.get((c, r_, y), 0.0)
                v0 = conv.get((base, r_, y), 0.0)
                p_ = pre.get((c, r_, y), 0.0)
                p0 = pre.get((base, r_, y), 0.0)
                rows.append(("UON", "ref", lev, c, r_, y, v, v0, v - v0, p_ - p0,
                             (v - v0) - (p_ - p0)))
    carry = pd.DataFrame(rows, columns=["batch", "arm", "level", "case", "r", "t",
                                        "value", "value_0GW", "diff", "diff_built_before_2044",
                                        "diff_built_2044_on"])
    carry_nz = carry[carry["diff"].abs() > 0]
    carry_nz.assign(unit="2024 $", converted_2004_to_2024=True).to_csv(
        dc.OUT_DIR / "converter_carryover.csv", index=False)
    n_reg = carry_nz.groupby("level")["r"].nunique()
    by_level = (carry.groupby("level")
                .agg(max_abs_diff=("diff", lambda x: float(x.abs().max())),
                     sum_diff_2044_2050=("diff", "sum"),
                     sum_diff_built_before_2044=("diff_built_before_2044", "sum"),
                     sum_diff_built_2044_on=("diff_built_2044_on", "sum"))
                .reset_index())
    by_level.insert(1, "regions_nonzero",
                    by_level["level"].map(n_reg).fillna(0).astype(int))
    tot_cost =(long[(long["case"].isin(ref["case"])) & (long["metric"] == "annualized_cost")]
                .groupby("level")["value"].sum())
    by_level["sum_diff_share_of_total_cost_pct"] = [
        100 * v / tot_cost[lv] for lv, v in zip(by_level["level"], by_level["sum_diff_2044_2050"])]
    where = (carry_nz.groupby("r")
             .agg(levels=("level", lambda x: ", ".join(f"{v:g}" for v in sorted(set(x)))),
                  max_abs_diff=("diff", lambda x: float(x.abs().max())),
                  max_abs_diff_built_before_2044=("diff_built_before_2044",
                                                  lambda x: float(x.abs().max())))
             .reset_index().sort_values("max_abs_diff", ascending=False))

    # ---- national values, UON ref 0 and 3 GW ----
    show_cases = ["UON_20261022_0G_ref", "UON_20261022_3G_ref"]
    nat = (long[long["case"].isin(show_cases)].groupby(["case", "t", "metric"])["value"]
           .sum().unstack("metric").reset_index())
    nat = nat[["case", "t", "annualized_cost_capital", "annualized_cost_op",
               "annualized_cost"]]
    nat_tot = (tot[tot["case"].isin(show_cases)].groupby(["case", "metric"])["value"].sum()
               .unstack("metric").reset_index())
    p25 = (long[long["case"].isin(dc.SAMPLE_CASES) & (long["r"] == dc.FOCUS)]
           .pivot_table(index=["case", "t"], columns="metric", values="value").reset_index())

    # ---- checks ----
    n_rows_exp = sum(len(regions_by_batch[b]) for b in cases["batch"]) * len(YEARS) * 3
    sum_out = long.loc[long["metric"] == "annualized_cost", "value"].sum()
    sum_cat = cat["value"].sum()
    interp = [(c, ts) for c, ts in crf_interp if ts]
    sev0 = int(p_sev.iloc[0])
    window_start = YEARS[0] - sev0 + 1
    first_model = int(s["t"].min())
    checks = [
        ("Unit of input (02d lookup)", "PASS" if unit_in == "2004 $" else "FAIL", unit_in),
        ("Every case has systemcost_ba and crf rows", "PASS",
         f"{s['case'].nunique()} and {crf_all['case'].nunique()} of {len(cases)}"),
        ("Every category is in cost_cat_map.csv (gather_cost_types L247-253)", "PASS",
         f"{len(cats)} categories"),
        ("cost_cat_map Capital/Operation = `inv_*`/`op_*` (D44)", "PASS",
         f"{len(cap_cats)} capital, {len(op_cats)} operation"),
        ("Transmission categories (40 years) found in the data", "INFO",
         ", ".join(c for c in TRANS_CATS if c in cap_cats) or "none"),
        ("Regions within the batch's 34 zones", "PASS", "all"),
        ("sys_eval_years = 30, trans_crp = 40 in every case (D44)", "PASS",
         f"sys_eval_years {sorted(set(p_sev.astype(int)))}, "
         f"trans_crp {sorted(set(p_tc.astype(int)))}"),
        ("crf given for every solve year with capital (no interpolation used)",
         "PASS" if not interp else "INFO",
         "; ".join(f"{c}: {ts}" for c, ts in interp) or "all"),
        ("Pre-2010 capital cannot reach 2044-2050 (30-year window of 2044 starts "
         "after the first model year - 1)",
         "PASS" if window_start > first_model - 1 else "FAIL",
         f"window of {YEARS[0]} starts {window_start}; df_capex_init years <= "
         f"{first_model - 1}; it is added only to inv_investment_capacity_costs "
         "(results.py L397), a 30-year category"),
        ("Rows: every case x 34 regions x 7 years x 3 metrics",
         "PASS" if len(long) == n_rows_exp else "FAIL", f"{len(long):,} vs {n_rows_exp:,}"),
        ("Total = sum of category values", "PASS"
         if abs(sum_out - sum_cat) <= 1e-9 * max(abs(sum_cat), 1) else "FAIL",
         f"{sum_out:,.6g} vs {sum_cat:,.6g}"),
        ("No missing value", "PASS" if not long["value"].isna().any() else "FAIL", ""),
        ("Second, independent calculation equals 03b2 (sample cases, every "
         f"region-year-category, rel. gap <= {REL_TOL:g})",
         "PASS" if ind_ok else "FAIL", f"max {ind['max relative gap'].max():.3g}"),
        ("Plan check: run's post_systemcost_annualized.csv (UON ref 0 GW)",
         "INFO" if not post_found else ("PASS" if post_ok else "FAIL"),
         "file absent; replaced by the second calculation" if not post_found else
         "national capital and op by year, rel. gap <= 1e-4"),
    ]
    fail = any(c[1] == "FAIL" for c in checks)

    cat_tab = (cat[(cat["case"] == CHECK_CASE)].groupby(["sys_costs", "part"])["value"].sum()
               .rename("UON ref 0 GW, sum 2044-2050, 2024 $").reset_index())
    cat_tab["window (years)"] = [
        (int(params.loc[CHECK_CASE, "trans_crp"]) if c in TRANS_CATS else sev0)
        if p == "capital" else "-" for c, p in zip(cat_tab["sys_costs"], cat_tab["part"])]

    text = [
        f"## 03b2_annualized_cost — {'FAIL' if fail else 'PASS'}\n",
        "D44: annualized system cost from `systemcost_ba` (report_params.csv L188) and the "
        "case's own `crf`, following `reeds/results.py` `calc_systemcost` (annualized, "
        "L371-466 at 0c0ea27) with its defaults (L272-276): `shift_capital=True` (crf / 1.02, "
        "payments from the build year; discount rate 0.02, bokehpivot `defaults.py` L5), "
        "`crf_from_user=False` (the case's crf), capital paid for `sys_eval_years` (30) "
        "years, transmission categories for `trans_crp` (40) years (L349-356, L437-443); "
        "operations of each solve year fill the years to the next solve year (L457-465). "
        f"All values x {dc.DOLLAR} (D8; converted: every value column).\n",
        "Pre-2010 capital (`df_capex_init`): results.py adds it by default "
        "(`remove_existing=False`, L275, L380-398) to `inv_investment_capacity_costs` in "
        "the years before 2010, annualized like other capital. It is left out here "
        "(D44); with a 30-year window it has no payment in 2044-2050 (check below), so "
        "leaving it out changes no value reported here.\n",
        f"Tables: `{dc.rel(p1)}` ({len(long):,} rows), `{dc.rel(p2)}` ({len(tot):,} rows), "
        f"`{dc.rel(p3)}` ({len(cat_out):,} non-zero rows), "
        f"`outputs/03_derive/converter_carryover.csv` ({len(carry_nz):,} non-zero rows).\n",
        "### Checks\n",
        dc.md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Second calculation, sample cases (2004 $ before the factor)\n",
        dc.md_table(ind, floatfmt="{:.3g}") + "\n",
        f"### Plan check: national values of `{CHECK_CASE}` (2024 $)\n",
        "03b2 against the second calculation:\n",
        dc.md_table(nat_cmp, floatfmt="{:,.6g}") + "\n",
        *post_text,
        f"### Categories, `{CHECK_CASE}`\n",
        dc.md_table(cat_tab, floatfmt="{:,.6g}") + "\n",
        "### National annualized cost, UON `ref` 0 and 3 GW (sum over 34 regions, 2024 $)\n",
        dc.md_table(nat, floatfmt="{:,.6g}") + "\n",
        "Undiscounted 2044-2050 sum:\n",
        dc.md_table(nat_tot, floatfmt="{:,.6g}") + "\n",
        "### Verifier sample cases: p25 (2024 $)\n",
        dc.md_table(p25, floatfmt="{:,.6g}") + "\n",
        "### Converter-cost carry-over (decisions.md, On hold), UON `ref`\n",
        "Diff of annualized `inv_converter_costs` against UON `ref` 0 GW, 2044-2050, "
        "2024 $; split into converters built before 2044 (carried over through the "
        "40-year payments) and built in 2044 or later. Shown, not judged.\n",
        dc.md_table(by_level, floatfmt="{:,.4g}") + "\n",
        "Where (regions with a non-zero Diff in any level and year):\n",
        (dc.md_table(where, floatfmt="{:,.4g}") if len(where) else "None.") + "\n",
    ]
    dc.write_section(SECTION, "\n".join(text))
    print(f"03b2 done: {'FAIL' if fail else 'PASS'}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
