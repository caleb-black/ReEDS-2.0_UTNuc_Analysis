"""04g_cost_split: PROVISIONAL split of the annualized system cost Diff into parts.

PROVISIONAL (draft D47/D48, not approved). The method is the draft in
notes/proposals/cost_split.md (Option A, Option C, link L2) with the changes
listed below. It is NOT in docs/decisions.md. Every output file carries a
`status` column with the PROVISIONAL label, and so do the figure and the
check section ("04g PROVISIONAL <batch>").

Settled rules used: D2 (Diff vs the arm's own 0 GW case, same batch), D8 (2024 $,
already converted in stage 03), D26 (one batch per run, never mixed), D41 (step
change per GW between neighboring levels), D43d (UON main, UOS checks UON),
D44 (annualized cost from 03b2, 2044..2050 and the undiscounted 2044-2050 total),
D46g (total labeled "2044-2050").

1. Option A. Each `sys_costs` category of 03b2 (annualized_cost_category.h5) is
   mapped to one part: generation, capacity, transmission or other (PART_MAP).
   Changes from the proposal table, checked against report.gms at 0c0ea27:
   - op_acp_compliance_costs -> other (policy): RPS alternative-compliance
     purchases, report.gms L1630-1642 (state ACP L1632-1637, voluntary L1639-1640).
   - op_co2_incentive_negative -> generation: incentive per captured CO2 from
     GEN, report.gms L1644-1646 (also L1436-1438 at tech level). The same
     category also holds the DAC term from PRODUCE (L1648-1649); it stays in
     generation (not split; the table has no tech column).
   - op_consume_fom -> other: fixed O&M of `consume` techs, moved out of
     op_fom_costs at report.gms L1367-1368.
   Spur lines (inv_investment_spurline_costs_rsc_technologies, report.gms
   L1261; op_spurline_fom, L1548) are in capacity and also reported as their
   own sub-row `capacity_spurline` (part of capacity, not added again).
   An unmapped category stops the script.
   Rows: batch, arm, level, group, t (2044..2050 and 2044-2050), part; value,
   0 GW value, Diff. Check: parts sum to the 03b2 annualized cost, per region
   (annualized_cost.csv) and per group (the 04a group value, rebuilt in memory
   with analyze_common, plan rule 2), within 1e-9 relative.
2. Step change per GW (D41) of each part's Diff, every group and t.
3. Option C (UON only; needs `ref` and `smrcons` in the batch): smrcons Diff
   minus ref Diff, per part, group, level, for the 2044-2050 total.
4. L2: part Diff / the group's load (sum of `load` quantity, MWh, 03a), in
   2024 $/MWh, next to the Diff of the average energy and all-in prices, for the
   price years 2044, 2047, 2050. The load is the case's own load_quant; the
   check reports how far it is from the 0 GW load.
5. All-in payments by price type (03a allin_dollars_<type>, already x 1.6563):
   group sum per type and the Diff, plus non_energy = sum of the four
   non-load types. state_rps and nat_gen keep 03a's "unit not stated" label.

In:  outputs/03_derive/annualized_cost_category.h5, annualized_cost.csv,
     annualized_cost_total.csv, prices_region.h5, 00_config/*.csv
Out: outputs/04_analyze/04g_cost_parts_<batch>.csv
     outputs/04_analyze/04g_cost_parts_step_<batch>.csv
     outputs/04_analyze/04g_cost_categories_<batch>.csv
     outputs/04_analyze/04g_option_c_<batch>.csv       (only if ref and smrcons)
     outputs/04_analyze/04g_per_mwh_<batch>.csv
     outputs/04_analyze/04g_allin_types_<batch>.csv
     outputs/04_analyze/figures/04g_cost_split_<batch>.png
     section "04g PROVISIONAL <batch>" of outputs/checks/04_analyze.md

Run:  conda run -n reeds python 04_analyze/04g_cost_split.py --batch UON
"""

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
import numpy as np  # noqa: E402
import pandas as pd  # noqa: E402

import analyze_common as ac  # noqa: E402

PROV = "PROVISIONAL (draft D47/D48, not approved)"
REL_TOL = 1e-9
ID = ac.ID
PRICE_YEARS = ["2044", "2047", "2050"]
PRICE_TYPES = ["load", "res_marg", "oper_res", "state_rps", "nat_gen"]

# Option A map (notes/proposals/cost_split.md, with the three source-checked changes).
PART_MAP = {
    "inv_investment_capacity_costs": "capacity",
    "inv_investment_refurbishment_capacity": "capacity",
    "inv_itc_payments_negative": "capacity",
    "inv_investment_spurline_costs_rsc_technologies": "capacity",
    "op_fom_costs": "capacity",
    "op_spurline_fom": "capacity",
    "op_consume_fom": "other",
    "op_fuelcosts_objfn": "generation",
    "op_vom_costs": "generation",
    "op_startcost": "generation",
    "op_co2_transport_storage": "generation",
    "op_co2_incentive_negative": "generation",
    "op_ptc_payments_negative": "generation",
    "op_acp_compliance_costs": "other",
    "inv_transmission_interzone_ac_investment": "transmission",
    "inv_transmission_interzone_dc_investment": "transmission",
    "inv_converter_costs": "transmission",
    "inv_transmission_line_investment": "transmission",
    "inv_transmission_intrazone_investment": "transmission",
    "op_transmission_fom": "transmission",
    "op_transmission_intrazone_fom": "transmission",
    "inv_h2_production": "other",
    "inv_h2_storage": "other",
    "op_h2_storage": "other",
    "op_h2_transport_intrareg": "other",
    "op_h2_ptc_payments_negative": "other",
}
SPUR = {"inv_investment_spurline_costs_rsc_technologies", "op_spurline_fom"}
PARTS = ["generation", "capacity", "transmission", "other"]
SUB = "capacity_spurline"
ROWS = PARTS + [SUB, "total"]
PART_COLORS = {"generation": "tab:orange", "capacity_excl_spur": "tab:blue",
               SUB: "lightsteelblue", "transmission": "tab:green", "other": "tab:gray"}


# ---------------------------------------------------------------- data
def read_categories(batch):
    c = pd.read_hdf(ac.IN03 / "annualized_cost_category.h5", "data",
                    where=f'batch == "{batch}"',
                    columns=ID + ["r", "t", "sys_costs", "part", "value", "unit"])
    return c.rename(columns={"part": "cost_type"})


def group_categories(c, batch):
    """Group sum per category, each year and the 2044-2050 total; zero-filled grid."""
    s = ac.members(c, batch).groupby(ID + ["group", "t", "sys_costs"], as_index=False)["value"].sum()
    s["t"] = s["t"].astype(str)
    tot = s.groupby(ID + ["group", "sys_costs"], as_index=False)["value"].sum()
    tot["t"] = ac.TOTAL_T
    s = pd.concat([s, tot], ignore_index=True)
    cats = sorted(c["sys_costs"].unique())
    years = [str(y) for y in sorted(c["t"].unique())] + [ac.TOTAL_T]
    g = ac.cases(batch).merge(pd.DataFrame({"group": ac.GROUPS}), how="cross")
    g = g.merge(pd.DataFrame({"t": years}), how="cross")
    g = g.merge(pd.DataFrame({"sys_costs": cats}), how="cross")
    out = g.merge(s, on=ID + ["group", "t", "sys_costs"], how="left")
    out["n_missing_filled"] = out["value"].isna().astype(int)
    out["value"] = out["value"].fillna(0.0)
    out["part"] = out["sys_costs"].map(PART_MAP)
    out["cost_type"] = np.where(out["sys_costs"].str.startswith("inv_"), "capital", "op")
    return out


def to_parts(gc):
    p = gc.groupby(ID + ["group", "t", "part"], as_index=False)["value"].sum()
    sp = gc[gc["sys_costs"].isin(SPUR)].groupby(ID + ["group", "t"], as_index=False)["value"].sum()
    sp["part"] = SUB
    tt = gc.groupby(ID + ["group", "t"], as_index=False)["value"].sum()
    tt["part"] = "total"
    out = pd.concat([p, sp, tt], ignore_index=True)
    out["part"] = pd.Categorical(out["part"], ROWS, ordered=True)
    return out.sort_values(["arm", "group", "t", "part", "level"]).reset_index(drop=True)


def diff(df, keys):
    base = df[df["level"] == 0][keys + ["value"]].rename(columns={"value": "value_0GW"})
    out = df.merge(base, on=keys, how="left")
    out["diff"] = out["value"] - out["value_0GW"]
    return out


def cost_unit(t):
    return np.where(t == ac.TOTAL_T, "2024 $ (undiscounted sum of 2044-2050)", "2024 $")


def group_price_parts(batch):
    """03a region dollars per price type and load, summed per group (solve years >= 2044)."""
    mets = ["load_quant", "energy_dollars", "allin_dollars"] + [f"allin_dollars_{t}" for t in PRICE_TYPES]
    p = pd.read_hdf(ac.IN03 / "prices_region.h5", "data",
                    where=f'batch == "{batch}" & metric in {mets} & t >= {ac.FIRST_POST_YEAR}',
                    columns=ID + ["r", "t", "metric", "value", "unit"])
    units = p.groupby("metric")["unit"].agg(lambda x: sorted(set(x)))
    s = ac.members(p, batch).groupby(ID + ["group", "t", "metric"], as_index=False)["value"].sum()
    nr = ac.members(p, batch).groupby(ID + ["group", "t", "metric"]).size()
    s["n_regions"] = nr.to_numpy()
    s["t"] = s["t"].astype(int).astype(str)
    return s, units


# ---------------------------------------------------------------- figure
def figure(parts_d, batch, arms):
    d = parts_d[(parts_d["t"] == ac.TOTAL_T)].copy()
    d["part"] = d["part"].astype(str)
    w = d.pivot_table(index=["arm", "group", "level"], columns="part", values="diff").reset_index()
    w["capacity_excl_spur"] = w["capacity"] - w[SUB]
    stack = ["generation", "capacity_excl_spur", SUB, "transmission", "other"]
    ncol = max(len(ac.GROUPS), len(arms))
    fig, axes = plt.subplots(2, ncol, figsize=(3.3 * ncol, 7.6), squeeze=False)

    def bars(ax, s):
        x = s["level"].to_numpy()
        wd = 0.8 * (np.min(np.diff(np.sort(x))) if len(x) > 1 else 0.25)
        pos, neg = np.zeros(len(s)), np.zeros(len(s))
        for p in stack:
            v = s[p].to_numpy() / 1e9
            b = np.where(v >= 0, pos, neg)
            ax.bar(x, v, wd, bottom=b, color=PART_COLORS[p],
                   label=p.replace("capacity_excl_spur", "capacity (excl. spur)")
                    .replace(SUB, "capacity: spur lines"))
            pos += np.where(v >= 0, v, 0)
            neg += np.where(v < 0, v, 0)
        ax.plot(x, s["total"].to_numpy() / 1e9, "k.", ms=5, label="total Diff")
        ax.axhline(0, color="0.5", lw=0.5)
        ax.tick_params(labelsize=7)

    for j, grp in enumerate(ac.GROUPS):
        s = w[(w["arm"] == "ref") & (w["group"] == grp)].sort_values("level")
        bars(axes[0, j], s)
        axes[0, j].set_title(f"ref, {grp}", fontsize=10)
    for j in range(len(ac.GROUPS), ncol):
        axes[0, j].axis("off")
    for j, arm in enumerate(arms):
        s = w[(w["arm"] == arm) & (w["group"] == "wecc")].sort_values("level")
        bars(axes[1, j], s)
        axes[1, j].set_title(f"{arm}, wecc", fontsize=10)
        axes[1, j].set_xlabel("level, GW", fontsize=8)
    for j in range(len(arms), ncol):
        axes[1, j].axis("off")
    axes[0, 0].set_ylabel("Diff vs 0 GW, 2044-2050 total\nbillion 2024 $", fontsize=8)
    axes[1, 0].set_ylabel("wecc, Diff vs 0 GW\nbillion 2024 $", fontsize=8)
    axes[0, 0].legend(fontsize=6.5, loc="best")
    fig.suptitle(f"04g, {batch}: {PROV}\nannualized system cost Diff (D44) by part "
                 "(Option A map), 2044-2050 total; top: ref arm per group; bottom: wecc per arm",
                 fontsize=10, color="darkred")
    fig.tight_layout(rect=(0, 0, 1, 0.93))
    ac.FIG.mkdir(parents=True, exist_ok=True)
    path = ac.FIG / f"04g_cost_split_{batch}.png"
    fig.savefig(path, dpi=100)
    plt.close(fig)
    return path


# ---------------------------------------------------------------- main
def main():
    batch = ac.parse_batch(__doc__.splitlines()[0])
    arms = list(dict.fromkeys(ac.cases(batch)["arm"]))
    checks = []

    # 1. Option A ------------------------------------------------------------
    c = read_categories(batch)
    cats = sorted(c["sys_costs"].unique())
    unmapped = [k for k in cats if k not in PART_MAP]
    if unmapped:
        raise SystemExit(f"04g: unmapped sys_costs categories {unmapped}; stop (no part assigned)")
    checks.append(("every category in the data is mapped exactly once", True,
                   f"{len(cats)} categories in the data, {len(PART_MAP)} in the map; "
                   f"in the map but not in the data: "
                   f"{', '.join(sorted(set(PART_MAP) - set(cats))) or 'none'}"))
    units = sorted(c["unit"].unique())
    checks.append(("input unit is 2024 $ (D8 applied in 03b2)", units == ["2024 $"], str(units)))
    ct_ok = bool((c["cost_type"] == np.where(c["sys_costs"].str.startswith("inv_"), "capital", "op")).all())
    checks.append(("03b2 capital/op = inv_*/op_*", ct_ok, ""))

    # region-level check against annualized_cost.csv
    rc = c.groupby(ID + ["r", "t"], as_index=False)["value"].sum()
    a = pd.read_csv(ac.IN03 / "annualized_cost.csv")
    a = a[(a["batch"] == batch) & (a["metric"] == "annualized_cost")]
    m = a.merge(rc, on=ID + ["r", "t"], how="left", suffixes=("", "_cat"))
    m["value_cat"] = m["value_cat"].fillna(0.0)
    g1 = ((m["value"] - m["value_cat"]).abs() / m["value"].abs().where(m["value"].abs() > 0, 1)).max()
    checks.append(("region: sum of categories = 03b2 annualized_cost, every case-region-year",
                   g1 <= REL_TOL, f"max relative gap {g1:.2e} over {len(m):,} rows"))

    gc = group_categories(c, batch)
    gc["unit"] = cost_unit(gc["t"])
    parts = to_parts(gc)
    parts["unit"] = cost_unit(parts["t"])
    nfill = int(gc["n_missing_filled"].sum())

    ag, _ = ac.group_annualized_cost(batch)   # the 04a group values, rebuilt in memory
    tot = parts[parts["part"] == "total"].merge(
        ag[ag["metric"] == "annualized_cost"][ID + ["group", "t", "value"]],
        on=ID + ["group", "t"], suffixes=("", "_04a"), how="outer", indicator=True)
    g2 = ((tot["value"] - tot["value_04a"]).abs() / tot["value_04a"].abs().where(tot["value_04a"].abs() > 0, 1)).max()
    four = parts[parts["part"].isin(PARTS)].groupby(ID + ["group", "t"])["value"].sum()
    tt = parts[parts["part"] == "total"].set_index(ID + ["group", "t"])["value"]
    g3 = ((four - tt).abs() / tt.abs()).max()
    checks.append(("group: generation + capacity + transmission + other = 04a annualized_cost "
                   "(each year and 2044-2050)",
                   bool((tot["_merge"] == "both").all()) and g2 <= REL_TOL and g3 <= REL_TOL,
                   f"max relative gap vs 04a {g2:.2e}; parts vs own total {g3:.2e}; "
                   f"{len(tot):,} case-group-t rows, unmatched {int((tot['_merge'] != 'both').sum())}"))
    # capital/op preserved (proposal check 2)
    for ctype, met in (("capital", "annualized_cost_capital"), ("op", "annualized_cost_op")):
        s = gc[gc["cost_type"] == ctype].groupby(ID + ["group", "t"], as_index=False)["value"].sum()
        mm = s.merge(ag[ag["metric"] == met][ID + ["group", "t", "value"]], on=ID + ["group", "t"],
                     suffixes=("", "_04a"))
        gg = ((mm["value"] - mm["value_04a"]).abs() / mm["value_04a"].abs().where(mm["value_04a"].abs() > 0, 1)).max()
        checks.append((f"the map moves no money between capital and op: {ctype} categories = 04a {met}",
                       gg <= REL_TOL, f"max relative gap {gg:.2e}"))
    four_g = parts[(parts["group"] != "wecc")].groupby(ID + ["t", "part"], observed=True)["value"].sum()
    wv = parts[parts["group"] == "wecc"].set_index(ID + ["t", "part"])["value"]
    g4 = ((four_g - wv).abs() / wv.abs().where(wv.abs() > 0, 1)).max()
    checks.append(("each part: focus + utah_rest + neighbors + rest_wecc = wecc", g4 <= REL_TOL,
                   f"max relative gap {g4:.2e}"))

    pd_ = diff(parts, ["batch", "arm", "group", "t", "part"])
    z = pd_[pd_["level"] == 0]["diff"].abs().max()
    checks.append(("Diff at 0 GW is 0 and every row has a 0 GW value",
                   z == 0 and pd_["value_0GW"].notna().all(), f"max |Diff| at 0 GW {z:g}"))
    pd_["status"] = PROV
    pd_["part"] = pd_["part"].astype(str)
    p1 = ac.write_csv(pd_[ID + ["group", "t", "part", "value", "value_0GW", "diff", "unit", "status"]],
                      "04g_cost_parts", batch)
    gcd = diff(gc, ["batch", "arm", "group", "t", "sys_costs"])
    gcd["status"] = PROV
    p1c = ac.write_csv(gcd[ID + ["group", "t", "sys_costs", "cost_type", "part", "value", "value_0GW",
                                 "diff", "unit", "n_missing_filled", "status"]],
                       "04g_cost_categories", batch)

    # 2. step change per GW ---------------------------------------------------
    keys = ["batch", "arm", "group", "part", "t"]
    st = ac.step_slopes(pd_, keys)
    st["unit"] = st["unit"].str.replace(" per GW", " per GW of prescribed nuclear", regex=False)
    st["status"] = PROV
    p2 = ac.write_csv(st, "04g_cost_parts_step", batch)
    nlev = ac.cases(batch).groupby("arm")["level"].nunique().iloc[0]
    nst = st.groupby(keys).size()
    checks.append(("steps per series = levels - 1 (D41)", bool((nst == nlev - 1).all()),
                   f"{sorted(set(nst))} steps"))
    s4 = st[st["part"].isin(PARTS)].groupby(["arm", "group", "t", "level_from"])["step_slope"].sum()
    stt = st[st["part"] == "total"].set_index(["arm", "group", "t", "level_from"])["step_slope"]
    g5 = ((s4 - stt).abs() / stt.abs().where(stt.abs() > 0, 1)).max()
    checks.append(("step per GW: parts add up to the total step", g5 <= 1e-6,
                   f"max relative gap {g5:.2e}"))

    # 3. Option C ---------------------------------------------------------------
    p3 = None
    optc = None
    if {"ref", "smrcons"} <= set(arms):
        x = pd_[pd_["t"] == ac.TOTAL_T]
        r_ = x[x["arm"] == "ref"][["group", "level", "part", "diff"]]
        s_ = x[x["arm"] == "smrcons"][["group", "level", "part", "diff"]]
        optc = r_.merge(s_, on=["group", "level", "part"], suffixes=("_ref", "_smrcons"), how="outer")
        optc["smrcons_minus_ref"] = optc["diff_smrcons"] - optc["diff_ref"]
        optc.insert(0, "batch", batch)
        optc["t"] = ac.TOTAL_T
        optc["unit"] = "2024 $ (undiscounted sum of 2044-2050)"
        optc["status"] = PROV
        checks.append(("Option C: same levels in ref and smrcons",
                       bool(optc[["diff_ref", "diff_smrcons"]].notna().all().all()), ""))
        p3 = ac.write_csv(optc, "04g_option_c", batch)

    # 4/5. prices, load, all-in by type ------------------------------------------
    gp, punits = group_price_parts(batch)
    gw = gp.pivot_table(index=ID + ["group", "t"], columns="metric", values="value").reset_index()
    gw["load_quant_0GW"] = gw.merge(
        gw[gw["level"] == 0][["arm", "group", "t", "load_quant"]],
        on=["arm", "group", "t"], suffixes=("_x", ""), how="left")["load_quant"].to_numpy()
    lg = ((gw["load_quant"] - gw["load_quant_0GW"]).abs() / gw["load_quant_0GW"]).max()
    gw["avg_energy_price"] = gw["energy_dollars"] / gw["load_quant"]
    gw["avg_allin_price"] = gw["allin_dollars"] / gw["load_quant"]
    tsum = gw[[f"allin_dollars_{t}" for t in PRICE_TYPES]].sum(axis=1)
    g6 = ((tsum - gw["allin_dollars"]).abs() / gw["allin_dollars"].abs()).max()
    g7 = ((gw["allin_dollars_load"] - gw["energy_dollars"]).abs() / gw["energy_dollars"].abs()).max()
    checks.append(("all-in types: load + res_marg + oper_res + state_rps + nat_gen = allin_dollars",
                   g6 <= REL_TOL, f"max relative gap {g6:.2e}"))
    checks.append(("all-in type load = energy_dollars", g7 <= REL_TOL, f"max relative gap {g7:.2e}"))

    # L2 per MWh
    pyr = pd_[pd_["t"].isin(PRICE_YEARS)][ID + ["group", "t", "part", "diff"]]
    l2 = pyr.merge(gw[ID + ["group", "t", "load_quant"]], on=ID + ["group", "t"], how="left")
    l2["value"] = l2["diff"] / l2["load_quant"]
    l2["metric"] = "cost_diff_per_mwh_" + l2["part"]
    l2["unit"] = "2024 $/MWh (part Diff / group load_quant)"
    pr = ac.add_diff(gw.melt(id_vars=ID + ["group", "t"],
                             value_vars=["avg_energy_price", "avg_allin_price"],
                             var_name="metric", value_name="value"),
                     ["batch", "arm", "group", "t", "metric"])
    pr = pr.merge(gw[ID + ["group", "t", "load_quant"]], on=ID + ["group", "t"])
    ns = ac.members(pd.read_hdf(ac.IN03 / "prices_region.h5", "data",
                                where=f'batch == "{batch}" & metric == "allin_dollars" & t >= {ac.FIRST_POST_YEAR}',
                                columns=ID + ["r", "t", "unit"]), batch)
    ns["ns"] = (ns["unit"] != "2024 $").astype(int)
    ns = ns.groupby(ID + ["group", "t"], as_index=False)["ns"].sum()
    ns["t"] = ns["t"].astype(int).astype(str)
    pr = pr.merge(ns, on=ID + ["group", "t"], how="left")
    pr["unit"] = np.where(pr["metric"] == "avg_energy_price", "2024 $/MWh",
                          np.where(pr["ns"] > 0, "2024 $/MWh (includes state_rps/nat_gen dollars, "
                                   "unit not stated)", "2024 $/MWh"))
    pr["metric"] = "diff_" + pr["metric"]
    pr["value"] = pr["diff"]
    l2o = pd.concat([l2[ID + ["group", "t", "metric", "value", "unit", "load_quant"]],
                     pr[ID + ["group", "t", "metric", "value", "unit", "load_quant"]]], ignore_index=True)
    l2o = l2o.rename(columns={"load_quant": "load_mwh"})
    l2o["status"] = PROV
    p4 = ac.write_csv(l2o, "04g_per_mwh", batch)
    checks.append(("L2: group load_quant vs the 0 GW load (2044, 2047, 2050)", None,
                   f"max relative gap {lg:.2e}; the case's own load is used"))

    # all-in by type
    tcols = [f"allin_dollars_{t}" for t in PRICE_TYPES]
    at = gw.melt(id_vars=ID + ["group", "t"], value_vars=tcols + ["allin_dollars"],
                 var_name="metric", value_name="value")
    ne = gw[ID + ["group", "t"]].copy()
    ne["metric"] = "non_energy_dollars"
    ne["value"] = gw[[f"allin_dollars_{t}" for t in PRICE_TYPES if t != "load"]].sum(axis=1)
    at = pd.concat([at, ne], ignore_index=True)
    at = diff(at, ["batch", "arm", "group", "t", "metric"])
    ulab = {f"allin_dollars_{t}": " / ".join(punits[f"allin_dollars_{t}"]) for t in PRICE_TYPES}
    ulab["allin_dollars"] = "2024 $, or not stated where state_rps/nat_gen dollars are non-zero (03a)"
    ulab["non_energy_dollars"] = ("sum of res_marg, oper_res (2024 $) and state_rps, nat_gen "
                                  "(unit not stated)")
    at["unit"] = at["metric"].map(ulab)
    at["status"] = PROV
    p5 = ac.write_csv(at[ID + ["group", "t", "metric", "value", "value_0GW", "diff", "unit", "status"]],
                      "04g_allin_types", batch)

    fig = figure(pd_, batch, arms)

    # ---------------------------------------------------------------- report
    ok_all = all(ok is not False for _, ok, _ in checks)
    lab = {True: "PASS", False: "FAIL", None: "INFO"}
    ttab = pd_[(pd_["t"] == ac.TOTAL_T) & (pd_["level"] == pd_["level"].max())]

    def wide(df, arm, col="diff", scale=1e9, idx="group"):
        x = df[df["arm"] == arm].pivot_table(index=idx, columns="part", values=col, observed=True)
        x = x[[p for p in ROWS if p in x.columns]] / scale
        return x.reindex([g for g in ac.GROUPS if g in x.index]).reset_index()

    lmax = pd_["level"].max()
    sw = st[(st["t"] == ac.TOTAL_T) & st["group"].isin(["wecc", "focus"])]
    swm = sw.groupby(["arm", "group", "part"], as_index=False)["step_slope"].agg(["mean", "min", "max"])
    swm = swm.reset_index() if "arm" not in swm.columns else swm
    swm[["mean", "min", "max"]] = swm[["mean", "min", "max"]] / 1e9
    swm["part"] = pd.Categorical(swm["part"], ROWS, ordered=True)
    swm = swm.sort_values(["group", "arm", "part"])

    t = [f"## 04g_cost_split, {batch} -- {PROV}", "",
         f"**{PROV}.** Method: `notes/proposals/cost_split.md` (Option A, Option C, L2) with the "
         "changes in the script header (op_acp_compliance_costs -> other, report.gms L1630-1642; "
         "op_co2_incentive_negative -> generation, L1644-1650; op_consume_fom -> other, L1367-1368; "
         "spur lines in capacity, own sub-row `capacity_spurline`). Not a decision in "
         "`docs/decisions.md`. The all-in-by-type table touches cost view C (On hold).", "",
         f"- Parts: `{ac.rel(p1)}` ({len(pd_):,} rows); categories: `{ac.rel(p1c)}` ({len(gcd):,} rows; "
         f"{nfill:,} case-group-t-category rows absent in 03b2 (only non-zero rows are stored) filled with 0).",
         f"- Step per GW: `{ac.rel(p2)}` ({len(st):,} rows).",
         (f"- Option C: `{ac.rel(p3)}` ({len(optc):,} rows)." if p3 else
          "- Option C: not built (the batch has no `smrcons` arm)."),
         f"- L2 per MWh: `{ac.rel(p4)}` ({len(l2o):,} rows); all-in by type: `{ac.rel(p5)}` ({len(at):,} rows).",
         f"- Figure: `{ac.rel(fig)}`.",
         "- Map (part: categories): " + "; ".join(
             f"{p}: " + ", ".join(sorted(k for k, v in PART_MAP.items() if v == p)) for p in PARTS),
         "", "| check | result | detail |", "| --- | --- | --- |"]
    t += [f"| {nm} | {lab[ok]} | {det} |" for nm, ok, det in checks]
    t += ["", f"ref, {lmax:g} GW, Diff vs 0 GW, 2044-2050 total, billion 2024 $ "
          f"(capacity_spurline is inside capacity):", "",
          ac.md_table(wide(ttab, "ref"), floatfmt="{:.3f}"), ""]
    t += ["Step change per GW of the 2044-2050 Diff, focus and wecc, billion 2024 $ per GW "
          "(mean, min, max over the steps):", "", ac.md_table(swm[["group", "arm", "part", "mean", "min", "max"]],
                                                             floatfmt="{:.3f}"), ""]
    if optc is not None:
        oc = optc[(optc["level"] == lmax) & optc["group"].isin(["focus", "wecc"])].copy()
        oc["part"] = pd.Categorical(oc["part"], ROWS, ordered=True)
        oc = oc.sort_values(["group", "part"])
        for col in ("diff_ref", "diff_smrcons", "smrcons_minus_ref"):
            oc[col] = oc[col] / 1e9
        t += [f"Option C, {lmax:g} GW, 2044-2050 total, billion 2024 $ (all levels in the file):", "",
              ac.md_table(oc[["group", "part", "diff_ref", "diff_smrcons", "smrcons_minus_ref"]],
                          floatfmt="{:.3f}"), ""]
    l2r = l2o[(l2o["arm"] == "ref") & (l2o["level"] == lmax)]
    l2w = l2r.pivot_table(index=["group", "t"], columns="metric", values="value").reset_index()
    l2w["group"] = pd.Categorical(l2w["group"], ac.GROUPS, ordered=True)
    l2w = l2w.sort_values(["group", "t"])
    l2w.columns = [c.replace("cost_diff_per_mwh_", "") for c in l2w.columns]
    l2w = l2w[["group", "t"] + ROWS + ["diff_avg_energy_price", "diff_avg_allin_price"]]
    t += [f"L2, ref {lmax:g} GW: part Diff per MWh of group load and price Diffs, 2024 $/MWh "
          "(all-in may include state_rps/nat_gen dollars, unit not stated):", "",
          ac.md_table(l2w, floatfmt="{:.3f}"), ""]
    atr = at[(at["arm"] == "ref") & (at["level"] == lmax)]
    atw = atr.pivot_table(index=["group", "t"], columns="metric", values="diff").reset_index()
    atw["group"] = pd.Categorical(atw["group"], ac.GROUPS, ordered=True)
    atw = atw.sort_values(["group", "t"])
    atw = atw[["group", "t", "allin_dollars"] + [f"allin_dollars_{x}" for x in PRICE_TYPES]
              + ["non_energy_dollars"]]
    atw.columns = [c.replace("allin_dollars_", "") for c in atw.columns]
    atw.iloc[:, 2:] = atw.iloc[:, 2:] / 1e6
    t += [f"All-in payments by price type, ref {lmax:g} GW, Diff vs 0 GW, million (2024 $; "
          "state_rps and nat_gen: unit not stated):", "", ac.md_table(atw, floatfmt="{:.2f}"), ""]
    ac.section("04g PROVISIONAL", batch, "\n".join(t))
    for nm, ok, det in checks:
        print(lab[ok], nm, det)
    print("wrote", *[ac.rel(p) for p in (p1, p1c, p2, p4, p5, fig) + ((p3,) if p3 else ())])
    if not ok_all:
        raise SystemExit("04g: a check failed; see the report")


if __name__ == "__main__":
    main()
