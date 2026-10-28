"""03a_prices: regional prices per region, year and case; group price per block.

docs/plan.md, stage 03_derive, 03a; D6, D8, D9, D14, D32, D35, D36.

Per case, region r and year t (all blocks of the case, its own numhours, D32):
- load_quant      = sum over blocks of `reqt_quant` type `load` (MWh).
- energy_dollars  = sum over blocks of `load` price x `load` quantity.
- avg_energy_price = energy_dollars / load_quant (D6, energy only).
- allin_dollars_<type> for the five D6 types (load, res_marg, oper_res,
  state_rps, nat_gen; the list `price_types` in bokehpivot `reeds2.py` L34 at
  0c0ea27, used by `pre_prices` L959-L979, cited in D6): price x quantity,
  summed over the type's own blocks (rep blocks, stress blocks or 'ann').
  allin_dollars = their sum; avg_allin_price = allin_dollars / load_quant (D6).
- peak_price, ranks 1 to 3: highest `load` price over the case's blocks, with
  block name `h` and its `numhours` (D9). Ties broken by block name.
- peak_avg_ratio = peak_price (rank 1) / avg_energy_price (D9).

Per case, group (00_config/region_groups.csv, 9 neighbors, D35), block h, year t:
- group_load_quant = sum of `load` quantity over member regions.
- group_energy_price = sum of price x quantity / group_load_quant (D14).

Joins. Each quantity row takes the price of the same (type, subtype, r, h, t);
a quantity row with no price row gets price 0, as `pre_prices` does
(`reeds2.py` L965-L966: left join on quantities, `fillna(0)`). Counts of such
rows are in the report. Price rows with no quantity row add nothing.

Dollars (plan rule 6, D8): every dollar or $/MWh value is multiplied by the
factor in 00_config/study_settings.csv (1.6563) here; column
`converted_2004_to_2024` = True on those rows. The `load` price is 2004 $/MWh
(02d units lookup). The units of the res_marg and state_rps prices and
quantities are "not stated" in the lookup (data dictionary); their dollars
are computed as D6 says and flagged with unit "not stated" in the table.

Check figure: map of avg_energy_price, `ref` 0 GW case of each batch, final
year (2050), as the bokehpivot "Energy Price Final BA Map" (`reeds2.py`
L2189: load $ / q_load, year 'last'). One figure per batch (D26). Shapes:
inputs/shapefiles/US_PCA/ at 0c0ea27 (column `rb`), p28 and p30 merged into
z28 (plan, 05b; data dictionary, Model setup). The .shp file is a Git LFS
pointer at 0c0ea27; the working-tree file of the ReEDS source is used only if
its sha256 equals the pointer oid, and the other four files only if their
git blob ids equal those at 0c0ea27.

In:  outputs/01_ingest/outputs/reqt_price.h5, reqt_quant.h5,
     outputs/01_ingest/inputs/numhours.h5, outputs/02_clean/units.csv,
     00_config/study_cases.csv, region_groups.csv, study_settings.csv
Out: outputs/03_derive/prices_region.h5 (long), group_block_price.h5 (long),
     outputs/03_derive/figures/03a_avg_price_map_<batch>.png,
     section "03a" of outputs/checks/03_derive.md

Run:  conda run -n reeds python 03_derive/03a_prices.py
"""

import hashlib
import subprocess
import sys
import time

import numpy as np
import pandas as pd

import derive_common as dc

SECTION = "03a"
PRICE_TYPES = ["load", "res_marg", "oper_res", "state_rps", "nat_gen"]  # reeds2.py L34
MAP_YEAR = 2050                                                          # 'last' solve year
KEYS = ["type", "subtype", "r", "h", "t"]


def per_case(row, groups_b):
    c = row["case"]
    p = dc.read_key("reqt_price", where=f'case == "{c}"',
                    columns=["type", "subtype", "r", "h", "t", "Value"])
    q = dc.read_key("reqt_quant", where=f'case == "{c}" & type != "eq_loadcon"',
                    columns=["type", "subtype", "r", "h", "t", "Value"])
    nh = dc.read_numhours(where=f'case == "{c}"')[["h", "numhours"]]
    p = p[p["type"].isin(PRICE_TYPES)].rename(columns={"Value": "price"})
    q = q[q["type"].isin(PRICE_TYPES)].rename(columns={"Value": "quant"})
    p["price"] = p["price"].astype("float64")
    q["quant"] = q["quant"].astype("float64")

    m = q.merge(p, on=KEYS, how="left", indicator=True)
    info = {"case": c}
    for ty in PRICE_TYPES:
        sel = m["type"] == ty
        info[f"q_rows_{ty}"] = int(sel.sum())
        info[f"no_price_{ty}"] = int((sel & (m["_merge"] == "left_only")).sum())
        info[f"p_rows_{ty}"] = int((p["type"] == ty).sum())
    pq = p.merge(q[KEYS], on=KEYS, how="left", indicator=True)
    info["price_rows_without_quant"] = int((pq["_merge"] == "left_only").sum())
    m["price"] = m["price"].fillna(0.0)
    m["dollars"] = m["price"] * m["quant"]

    load = m[m["type"] == "load"]
    blocks = set(load["h"])
    info["blocks"] = len(blocks)
    info["blocks_numhours"] = len(nh)
    info["blocks_equal_numhours"] = blocks == set(nh["h"])
    info["regions"] = load["r"].nunique()
    info["load_quant_le0"] = int((load["quant"] <= 0).sum())
    info["load_price_lt0"] = int((load["price"] < 0).sum())
    rt = load.groupby(["r", "t"]).size()
    info["blocks_per_r_t_min"] = int(rt.min())
    info["blocks_per_r_t_max"] = int(rt.max())

    # region-year sums
    lq = load.groupby(["r", "t"])["quant"].sum().rename("load_quant")
    by_type = m.groupby(["r", "t", "type"])["dollars"].sum().unstack("type")
    by_type = by_type.reindex(columns=PRICE_TYPES).fillna(0.0)
    reg = pd.concat([lq, by_type], axis=1).reset_index()
    reg["load_quant"] = reg["load_quant"].fillna(0.0)
    reg[PRICE_TYPES] = reg[PRICE_TYPES].fillna(0.0)
    info["r_t_load_quant_le0"] = int((reg["load_quant"] <= 0).sum())
    reg["allin"] = reg[PRICE_TYPES].sum(axis=1)

    out = []

    def add(df, metric, col, unit, conv, extra=None):
        d = df[["r", "t"]].copy()
        d["metric"] = metric
        d["value"] = df[col].to_numpy() * (dc.DOLLAR if conv else 1.0)
        d["unit"] = unit
        d["converted_2004_to_2024"] = conv
        if extra is not None:
            for k, v in extra.items():
                d[k] = v.to_numpy() if hasattr(v, "to_numpy") else v
        out.append(d)

    with np.errstate(divide="ignore", invalid="ignore"):
        reg["avg_energy"] = reg["load"] / reg["load_quant"]
        reg["avg_allin"] = reg["allin"] / reg["load_quant"]
    add(reg, "load_quant", "load_quant", "MWh", False)
    add(reg, "energy_dollars", "load", "2024 $", True)
    add(reg, "avg_energy_price", "avg_energy", "2024 $/MWh", True)
    for ty in PRICE_TYPES:
        u = "2024 $" if ty == "load" else "not stated (D6 price x quantity; unit not stated)"
        add(reg, f"allin_dollars_{ty}", ty, u, True)
    add(reg, "allin_dollars", "allin", "not stated (sum of D6 types; non-load units not stated)", True)
    add(reg, "avg_allin_price", "avg_allin",
        "not stated (D6 all-in $ / load MWh; non-load units not stated)", True)

    # peaks (D9)
    pk_in = load[["r", "h", "t", "price"]].copy()
    pk_in["case"] = c
    top, ties = dc.rank_peaks(pk_in, n=3)
    info["peak_ties_rank1"] = ties
    top = top.merge(nh, on="h", how="left")
    info["peak_blocks_without_numhours"] = int(top["numhours"].isna().sum())
    add(top, "peak_price", "price", "2024 $/MWh", True,
        extra={"peak_rank": top["peak_rank"], "h": top["h"], "numhours": top["numhours"],
               "n_blocks_at_price": top["n_blocks_at_price"]})
    r1 = top[top["peak_rank"] == 1][["r", "t", "price"]].merge(
        reg[["r", "t", "avg_energy"]], on=["r", "t"], how="left")
    with np.errstate(divide="ignore", invalid="ignore"):
        r1["ratio"] = r1["price"] / r1["avg_energy"]
    info["ratio_avg_le0"] = int((r1["avg_energy"] <= 0).sum())
    add(r1, "peak_avg_ratio", "ratio", "ratio", False)

    reg_out = pd.concat(out, ignore_index=True)
    for k in ["batch", "arm", "level", "case"][::-1]:
        reg_out.insert(0, k, row[k])

    # group price per block (D14)
    gl = load.merge(groups_b, on="r", how="inner")
    gb = gl.groupby(["group", "h", "t"]).agg(dollars=("dollars", "sum"),
                                              quant=("quant", "sum"),
                                              members=("r", "nunique")).reset_index()
    info["group_blocks_quant_le0"] = int((gb["quant"] <= 0).sum())
    info["group_members"] = gb.groupby("group")["members"].max().to_dict()
    with np.errstate(divide="ignore", invalid="ignore"):
        gb["price"] = gb["dollars"] / gb["quant"] * dc.DOLLAR
    gb = gb.merge(nh, on="h", how="left")
    g1 = gb[["group", "h", "t", "numhours"]].assign(metric="group_energy_price",
                                                     value=gb["price"],
                                                     unit="2024 $/MWh",
                                                     converted_2004_to_2024=True)
    g2 = gb[["group", "h", "t", "numhours"]].assign(metric="group_load_quant",
                                                     value=gb["quant"], unit="MWh",
                                                     converted_2004_to_2024=False)
    grp_out = pd.concat([g1, g2], ignore_index=True)
    for k in ["batch", "arm", "level", "case"][::-1]:
        grp_out.insert(0, k, row[k])
    return reg_out, grp_out, info


def shapes():
    """US_PCA shapes at 0c0ea27, checked against the git objects; p28+p30 -> z28."""
    import geopandas as gpd
    src = dc.SETTINGS["reeds_source"]
    commit = dc.SETTINGS["reeds_commit"]
    base = "inputs/shapefiles/US_PCA/US_PCA"
    notes = []
    for ext in ["shp", "shx", "dbf", "prj", "cpg"]:
        path = f"{src}/{base}.{ext}"
        blob = subprocess.run(["git", "-C", src, "show", f"{commit}:{base}.{ext}"],
                              capture_output=True, check=True).stdout
        if blob.startswith(b"version https://git-lfs"):
            oid = [ln.split(":")[1] for ln in blob.decode().splitlines() if ln.startswith("oid")][0]
            got = hashlib.sha256(open(path, "rb").read()).hexdigest()
            ok = got == oid
            notes.append((f"{base}.{ext}", "LFS pointer; sha256 of working-tree file = oid",
                          "PASS" if ok else "FAIL"))
        else:
            ok = open(path, "rb").read() == blob
            notes.append((f"{base}.{ext}", "working-tree file = blob at 0c0ea27",
                          "PASS" if ok else "FAIL"))
    if not all(n[2] == "PASS" for n in notes):
        return None, notes
    g = gpd.read_file(f"{src}/{base}.shp")[["rb", "geometry"]]
    g["rb"] = g["rb"].replace({"p28": "z28", "p30": "z28"})
    g = g.dissolve(by="rb").reset_index()
    return g, notes


def price_map(reg_all, cases, groups):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.patheffects as pe
    import matplotlib.pyplot as plt
    g, notes = shapes()
    figs = []
    if g is None:
        return figs, notes, "shapes did not match 0c0ea27; no map"
    dc.FIG_DIR.mkdir(parents=True, exist_ok=True)
    for b in sorted(cases["batch"].unique()):
        c = cases[(cases.batch == b) & (cases.arm == "ref") & (cases.level == 0.0)]["case"].iloc[0]
        d = reg_all[(reg_all.case == c) & (reg_all.metric == "avg_energy_price")
                    & (reg_all.t == MAP_YEAR)][["r", "value"]]
        west = set(groups[(groups.batch == b) & (groups.group == "wecc")]["region"])
        gg = g[g["rb"].isin(west)].merge(d, left_on="rb", right_on="r", how="left")
        missing = sorted(west - set(gg["rb"]))
        fig, ax = plt.subplots(figsize=(8, 9))
        gg.plot(column="value", ax=ax, legend=True, cmap="viridis", edgecolor="white",
                linewidth=0.5, legend_kwds={"label": "2024 \\$/MWh", "shrink": 0.6})
        for _, rr in gg.iterrows():
            pt = rr.geometry.representative_point()
            ax.annotate(f"{rr['rb']}\n{rr['value']:.1f}", (pt.x, pt.y), ha="center",
                        va="center", fontsize=6, color="black",
                        path_effects=[pe.withStroke(linewidth=2, foreground="white")])
        ax.set_title(f"{b}: average energy price {MAP_YEAR}, {c}\n"
                     "(D6, load-weighted; 2024 \\$/MWh = 2004 \\$ x 1.6563)", fontsize=10)
        ax.set_axis_off()
        path = dc.FIG_DIR / f"03a_avg_price_map_{b}.png"
        fig.savefig(path, dpi=150, bbox_inches="tight")
        plt.close(fig)
        figs.append((b, c, dc.rel(path), len(gg), ", ".join(missing) or "none"))
    return figs, notes, ""


def main():
    t0 = time.time()
    cases = dc.cases()
    groups = dc.region_groups()
    regs, grps, infos = [], [], []
    for _, row in cases.iterrows():
        gb_ = groups[(groups.batch == row["batch"])][["group", "region"]].rename(
            columns={"region": "r"})
        reg, grp, info = per_case(row, gb_)
        regs.append(reg)
        grps.append(grp)
        infos.append(info)
        print(f"{row['case']}: {len(reg)} region rows, {len(grp)} group rows "
              f"({time.time() - t0:.0f} s)", flush=True)
    reg_all = pd.concat(regs, ignore_index=True)
    grp_all = pd.concat(grps, ignore_index=True)
    for col in ["h"]:
        reg_all[col] = reg_all[col].fillna("")
    reg_all["peak_rank"] = reg_all["peak_rank"].fillna(0).astype("int8")
    reg_all["numhours"] = reg_all["numhours"].astype("float64")
    reg_all["n_blocks_at_price"] = reg_all["n_blocks_at_price"].fillna(0).astype("int16")
    p_reg = dc.write_long(reg_all, "prices_region", big=True)
    p_grp = dc.write_long(grp_all, "group_block_price", big=True)
    info = pd.DataFrame(infos)
    info.drop(columns=["group_members"]).to_csv(dc.OUT_DIR / "03a_case_checks.csv", index=False)

    figs, shape_notes, map_err = price_map(reg_all, cases, groups)

    # ---------------- checks ----------------
    n_cases = len(cases)
    exp_blocks = cases["arm"].map(lambda a: 144 if a in ("loadhigh", "loadlow") else 152)
    nan_vals = reg_all[reg_all.metric.isin(["avg_energy_price", "avg_allin_price",
                                            "peak_price", "peak_avg_ratio"])]["value"]
    members_ok = all(i["group_members"] == {"focus": 1, "utah_rest": 1, "neighbors": 9,
                                             "rest_wecc": 23, "wecc": 34} for i in infos)
    checks = [
        ("Cases processed", "PASS" if len(info) == n_cases else "FAIL", f"{len(info)} of {n_cases}"),
        ("34 regions with `load` rows in every case", "PASS" if (info.regions == 34).all() else "FAIL",
         f"min {info.regions.min()}, max {info.regions.max()}"),
        ("Blocks of `load` rows = blocks in the case's numhours (D32)",
         "PASS" if info.blocks_equal_numhours.all() else "FAIL",
         f"{int(info.blocks_equal_numhours.sum())} of {n_cases} cases equal"),
        ("Block count 152, or 144 in loadhigh/loadlow (D32)",
         "PASS" if (info.blocks.to_numpy() == exp_blocks.to_numpy()).all() else "FAIL",
         f"counts found: {sorted(info.blocks.unique().tolist())}"),
        ("Every region-year has every block",
         "PASS" if (info.blocks_per_r_t_min == info.blocks).all()
         and (info.blocks_per_r_t_max == info.blocks).all() else "FAIL",
         f"blocks per (r, t): min {info.blocks_per_r_t_min.min()}, max {info.blocks_per_r_t_max.max()}"),
        ("`load` quantity rows <= 0", "PASS" if info.load_quant_le0.sum() == 0 else "OPEN",
         f"{int(info.load_quant_le0.sum())} rows (none means the zero-load question does not arise)"),
        ("Region-years with load_quant <= 0", "PASS" if info.r_t_load_quant_le0.sum() == 0 else "OPEN",
         f"{int(info.r_t_load_quant_le0.sum())}"),
        ("Group blocks with group load <= 0", "PASS" if info.group_blocks_quant_le0.sum() == 0 else "OPEN",
         f"{int(info.group_blocks_quant_le0.sum())}"),
        ("`load` quantity rows with no price row (price set to 0, reeds2.py L965-L966)",
         "INFO", f"{int(info.no_price_load.sum())} rows in all cases"),
        ("Negative `load` prices (kept as they are)", "INFO",
         f"{int(info.load_price_lt0.sum())} block rows in all cases"),
        ("Peak ties at rank 1 (broken by block name; see n_blocks_at_price)", "OPEN" if info.peak_ties_rank1.sum() else "PASS",
         f"{int(info.peak_ties_rank1.sum())} region-years"),
        ("Peak blocks without a numhours row", "PASS" if info.peak_blocks_without_numhours.sum() == 0 else "FAIL",
         f"{int(info.peak_blocks_without_numhours.sum())}"),
        ("Region-years with avg energy price <= 0 (ratio not meaningful)",
         "PASS" if info.ratio_avg_le0.sum() == 0 else "OPEN", f"{int(info.ratio_avg_le0.sum())}"),
        ("Missing (NaN/inf) price metrics", "PASS" if np.isfinite(nan_vals).all() else "FAIL",
         f"{int((~np.isfinite(nan_vals)).sum())} of {len(nan_vals)}"),
        ("Group members per batch: focus 1, utah_rest 1, neighbors 9, rest_wecc 23, wecc 34 (D35)",
         "PASS" if members_ok else "FAIL", "from 00_config/region_groups.csv"),
        ("Map shapes equal 0c0ea27", "PASS" if not map_err else "FAIL", map_err or "5 files checked"),
    ]
    ok = all(c[1] in ("PASS", "INFO") for c in checks)
    fail = any(c[1] == "FAIL" for c in checks)
    status = "FAIL" if fail else ("PASS" if ok else "PASS, with open items")

    type_tab = pd.DataFrame([{
        "type": ty,
        "price rows": int(info[f"p_rows_{ty}"].sum()),
        "quantity rows": int(info[f"q_rows_{ty}"].sum()),
        "quantity rows with no price (price 0)": int(info[f"no_price_{ty}"].sum()),
        "unit (02d lookup, price)": dc.unit_of("reqt_price", ty),
        "unit (02d lookup, quantity)": dc.unit_of("reqt_quant", ty),
    } for ty in PRICE_TYPES])

    samp = reg_all[reg_all.case.isin(dc.SAMPLE_CASES) & (reg_all.r == dc.FOCUS)
                   & reg_all.t.isin(dc.POST_PLANT_YEARS)
                   & reg_all.metric.isin(["avg_energy_price", "avg_allin_price", "peak_price",
                                          "peak_avg_ratio"])
                   & (reg_all.peak_rank <= 1)]
    samp = samp.assign(metric=np.where(samp.peak_rank == 1, "peak_price (rank 1)", samp.metric))
    samp_w = samp.pivot_table(index=["case", "t"], columns="metric", values="value").reset_index()
    peaks_s = reg_all[reg_all.case.isin(dc.SAMPLE_CASES) & (reg_all.r == dc.FOCUS)
                      & reg_all.t.isin(dc.POST_PLANT_YEARS) & (reg_all.metric == "peak_price")]
    peaks_s = peaks_s[["case", "t", "peak_rank", "h", "numhours", "n_blocks_at_price",
                       "value"]].sort_values(
        ["case", "t", "peak_rank"])
    gsamp = grp_all[grp_all.case.isin(dc.SAMPLE_CASES) & (grp_all.metric == "group_energy_price")
                    & grp_all.t.isin(dc.POST_PLANT_YEARS)]
    gmax = gsamp.loc[gsamp.groupby(["case", "group", "t"])["value"].idxmax()][
        ["case", "group", "t", "h", "value"]].rename(columns={"value": "max group block price"})

    conv = ["energy_dollars", "avg_energy_price", "allin_dollars_<type> (5 types)",
            "allin_dollars", "avg_allin_price", "peak_price", "group_energy_price"]
    text = [
        f"## 03a_prices — {status}\n",
        "Rules: D6 (average = sum of price x quantity / sum of `load` quantity), D9 (peak, 2nd, "
        "3rd, block name and hours; ratio = peak / energy-only average), D14 (group price per "
        "block), D32 (each case its own blocks and numhours). All-in types: `price_types` in "
        "`reeds2.py` L34 at 0c0ea27 (load, res_marg, oper_res, state_rps, nat_gen); join as "
        "`pre_prices` L959-L979 (left join on quantities, missing price = 0, L965-L966).\n",
        f"Tables: `{dc.rel(p_reg)}` ({len(reg_all):,} rows), `{dc.rel(p_grp)}` "
        f"({len(grp_all):,} rows), per-case counts `outputs/03_derive/03a_case_checks.csv`. "
        f"Run time {time.time() - t0:.0f} s.\n",
        f"Converted 2004 $ -> 2024 $ (x {dc.DOLLAR}, D8): {', '.join(conv)} "
        "(`converted_2004_to_2024` = True). Not converted: load_quant, group_load_quant (MWh), "
        "peak_avg_ratio.\n",
        "### Checks\n",
        dc.md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Requirement types in the all-in price (all cases)\n",
        "The units of the non-load types are \"not stated\" in the 02d lookup. The all-in price "
        "is computed as D6 defines it; its unit column says \"not stated\". For Caleb: the "
        "comments in `report.gms` L330-L331 and L366 at 0c0ea27 say load and operating reserve "
        "prices are $/MWh, the stress-period reserve margin price is $/MW per stress timeslice, "
        "and the reserve margin quantity is MW (not yet in the data dictionary).\n",
        dc.md_table(type_tab) + "\n",
        "### Check figure: average energy price map (`ref` 0 GW, 2050)\n",
        "Compare by eye with bokehpivot \"Energy Price Final BA Map ($/MWh)\" "
        "(`reeds2.py` L2189: load $ / q_load, year 'last'). Note: bokehpivot inflates with its own "
        "deflator (`inflate_series`, `reeds2.py` L72-L73) and dollar-year widget; this map uses "
        "x 1.6563 (D8), so levels can differ by a constant factor.\n",
        dc.md_table(pd.DataFrame(figs, columns=["batch", "case", "figure", "zones drawn",
                                                "west zones without a shape"])) + "\n",
        dc.md_table(pd.DataFrame(shape_notes, columns=["file", "check", "result"])) + "\n",
        "### Verifier sample cases: p25, post-plant years\n",
        dc.md_table(samp_w, floatfmt="{:,.6g}") + "\n",
        "Peak blocks (p25):\n",
        dc.md_table(peaks_s, floatfmt="{:,.6g}") + "\n",
        "Highest group block price (D14), sample cases:\n",
        dc.md_table(gmax, floatfmt="{:,.6g}") + "\n",
    ]
    dc.write_section(SECTION, "\n".join(text))
    print(f"03a done: {status}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
