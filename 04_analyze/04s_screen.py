"""04s_screen: rough first look at which stage 03 metrics move with the nuclear level (D42).

For each batch, arm, group and post-plant year: the group value of every stage 03
metric at every level, its Diff against the same batch-arm's 0 GW case (D2), and
the Diff as % of the 0 GW value. UON and UOS are never mixed (D26).

Group values are simple sums over member regions (00_config/region_groups.csv):
- prices: sum of dollars / sum of `load` quantity (D6), never an average of prices;
- peak price: the group's highest block price from group_block_price (D14);
- peak/average ratio: group peak / group average energy price, blank if the
  average is <= 0 (D37b);
- system cost, net imports, capacity, generation: sums over member regions;
- capacity and generation are totals by ReEDS technology group (tech_map.csv at
  0c0ea27, D37g, via 03_derive/derive_common.tech_map); shares are the group's
  tech-group total / group total, in %;
- expenditure flows: sum of flows that cross the group border, kept by direction
  (out: r in group, rr outside; in: r outside, rr in group), per type;
- new lines (invtran_out): sum over lines with r or rr in the group;
- lines at limit: count of (member region, rank-1 peak block, line) rows of
  line_use_peak with at_limit True, summed over member regions. Rough only.
Missing rows in sum metrics are 0.

Flag per metric (D42, D41): "moves" if in any batch, arm, group and post-plant
year (a) |Diff at 3 GW| > 1% of |0 GW value|, or (b) the step slopes between
neighboring levels change sign (any strictly positive and any strictly negative
slope). Otherwise "flat". Where the 0 GW value is 0, (a) cannot be evaluated;
such cases are counted in the report.

Lighter rules (D42): no Verifier, no Reviewer, no citations. Results are not findings.

In:  outputs/03_derive/{prices_region,group_block_price,expenditure_flow,
     capacity_generation,line_use_peak}.h5, system_cost.csv, system_cost_total.csv;
     outputs/01_ingest/outputs/{net_import_ann_rep,invtran_out}.h5 (read only, D36, D37f);
     00_config/study_cases.csv, region_groups.csv, study_settings.csv.
Out: outputs/04_analyze/04s_screen.csv, outputs/04_analyze/04s_flags.csv,
     outputs/04_analyze/figures/04s_screen_<batch>_p<k>.png,
     outputs/checks/04s_screen.md.
"""

import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "03_derive"))
from derive_common import tech_map  # noqa: E402  (ReEDS tech groups, D37g)

CONFIG = REPO / "00_config"
IN03 = REPO / "outputs" / "03_derive"
IN01 = REPO / "outputs" / "01_ingest" / "outputs"
OUT = REPO / "outputs" / "04_analyze"
FIG = OUT / "figures"
REPORT = REPO / "outputs" / "checks" / "04s_screen.md"

GROUPS = ["focus", "utah_rest", "neighbors", "rest_wecc", "wecc"]
SC_TOTAL_YEAR = "2044-2050"
ROWS_PER_PAGE = 12
TOP_LEVEL = 3.0
THRESH_PCT = 1.0

settings = pd.read_csv(CONFIG / "study_settings.csv")
SET = dict(zip(settings["setting"], settings["value"]))
YEARS = [int(x) for x in SET["post_plant_years"].split()]
CASES = pd.read_csv(CONFIG / "study_cases.csv")[["batch", "arm", "level", "case"]]
RG = pd.read_csv(CONFIG / "region_groups.csv")[["batch", "group", "region"]]
T_WHERE = "t in [" + ",".join(str(y) for y in YEARS) + "]"


def members(df, rcol="r"):
    """Join each region row to every group it belongs to (per batch)."""
    return df.merge(RG.rename(columns={"region": rcol}), on=["batch", rcol])


def grid(metrics, years=YEARS):
    """All case x group x year x metric combinations (for zero-filling sums)."""
    g = CASES.merge(pd.DataFrame({"group": GROUPS}), how="cross")
    g = g.merge(pd.DataFrame({"year": years}), how="cross")
    return g.merge(pd.DataFrame({"metric": metrics}), how="cross")


def fill_sum(df, metrics, unit, years=YEARS):
    """Zero-fill a summed metric over the full grid."""
    g = grid(metrics, years)
    out = g.merge(df, on=["batch", "arm", "level", "case", "group", "year", "metric"], how="left")
    out["value"] = out["value"].fillna(0.0)
    out["unit"] = unit
    return out


# ---------------------------------------------------------------- prices
def prices():
    p = pd.read_hdf(IN03 / "prices_region.h5", "data",
                    where=T_WHERE + " & metric in ['load_quant','energy_dollars','allin_dollars']",
                    columns=["batch", "arm", "level", "case", "r", "t", "metric", "value", "unit"])
    allin_unit_note = sorted(p.loc[p["metric"] == "allin_dollars", "unit"].unique())
    w = p.pivot_table(index=["batch", "arm", "level", "case", "r", "t"], columns="metric",
                      values="value", aggfunc="sum").reset_index()
    w = members(w)
    s = w.groupby(["batch", "arm", "level", "case", "group", "t"], as_index=False)[
        ["load_quant", "energy_dollars", "allin_dollars"]].sum()
    s["avg_energy_price"] = s["energy_dollars"] / s["load_quant"]
    s["avg_allin_price"] = s["allin_dollars"] / s["load_quant"]

    g = pd.read_hdf(IN03 / "group_block_price.h5", "data",
                    where=T_WHERE + " & metric=='group_energy_price'",
                    columns=["case", "group", "h", "t", "value"])
    pk = g.groupby(["case", "group", "t"], as_index=False)["value"].max().rename(
        columns={"value": "peak_price"})
    s = s.merge(pk, on=["case", "group", "t"], how="left")
    s["peak_avg_ratio"] = np.where(s["avg_energy_price"] > 0,
                                   s["peak_price"] / s["avg_energy_price"], np.nan)
    allin_unit = ("2024 $/MWh" if allin_unit_note == ["2024 $"]
                  else "2024 $/MWh (state_rps/nat_gen dollars: unit not stated)")
    units = {"load_quant": "MWh", "avg_energy_price": "2024 $/MWh",
             "avg_allin_price": allin_unit, "peak_price": "2024 $/MWh",
             "peak_avg_ratio": "ratio"}
    long = s.melt(id_vars=["batch", "arm", "level", "case", "group", "t"],
                  value_vars=list(units), var_name="metric", value_name="value")
    long["unit"] = long["metric"].map(units)
    return long.rename(columns={"t": "year"})


# ---------------------------------------------------------------- system cost
def system_cost():
    sc = pd.read_csv(IN03 / "system_cost.csv")
    sc = sc[sc["t"].isin(YEARS)]
    s = members(sc).groupby(["batch", "arm", "level", "case", "group", "t", "metric"],
                            as_index=False)["value"].sum().rename(columns={"t": "year"})
    a = fill_sum(s, ["system_cost", "system_cost_inv", "system_cost_op"], "2024 $")
    tot = pd.read_csv(IN03 / "system_cost_total.csv")
    t = members(tot).groupby(["batch", "arm", "level", "case", "group", "metric"],
                             as_index=False)["value"].sum()
    t["year"] = SC_TOTAL_YEAR
    b = fill_sum(t, ["system_cost_2044_2050"], "2024 $", years=[SC_TOTAL_YEAR])
    return pd.concat([a, b], ignore_index=True)


# ---------------------------------------------------------------- trade, lines
def net_imports():
    n = pd.read_hdf(IN01 / "net_import_ann_rep.h5", "data", where=T_WHERE)
    s = members(n).groupby(["batch", "arm", "level", "case", "group", "t"],
                           as_index=False)["Value"].sum()
    s = s.rename(columns={"t": "year", "Value": "value"})
    s["metric"] = "net_imports"
    return fill_sum(s, ["net_imports"], "MWh")


def expenditure_flows():
    e = pd.read_hdf(IN03 / "expenditure_flow.h5", "data", where=T_WHERE,
                    columns=["batch", "arm", "level", "case", "type", "r", "rr", "t", "value"])
    rows = []
    for (batch, grp), mem in RG.groupby(["batch", "group"]):
        mem = set(mem["region"])
        eb = e[e["batch"] == batch]
        r_in, rr_in = eb["r"].isin(mem), eb["rr"].isin(mem)
        for direction, mask in (("out", r_in & ~rr_in), ("in", ~r_in & rr_in)):
            x = eb[mask].groupby(["batch", "arm", "level", "case", "type", "t"],
                                 as_index=False)["value"].sum()
            x["metric"] = "expenditure_flow_" + x["type"] + "_" + direction
            x["group"] = grp
            rows.append(x.drop(columns="type"))
    s = pd.concat(rows, ignore_index=True).rename(columns={"t": "year"})
    mets = sorted(f"expenditure_flow_{t}_{d}" for t in e["type"].unique() for d in ("out", "in"))
    return fill_sum(s, mets, "2024 $")


def new_lines():
    v = pd.read_hdf(IN01 / "invtran_out.h5", "data", where=T_WHERE)
    rows = []
    for (batch, grp), mem in RG.groupby(["batch", "group"]):
        mem = set(mem["region"])
        vb = v[(v["batch"] == batch) & (v["r"].isin(mem) | v["rr"].isin(mem))]
        x = vb.groupby(["batch", "arm", "level", "case", "t"], as_index=False)["Value"].sum()
        x["group"] = grp
        rows.append(x)
    s = pd.concat(rows, ignore_index=True).rename(columns={"t": "year", "Value": "value"})
    s["metric"] = "new_lines"
    return fill_sum(s, ["new_lines"], "MW")


def lines_at_limit():
    l = pd.read_hdf(IN03 / "line_use_peak.h5", "data", where=T_WHERE + " & peak_rank==1",
                    columns=["batch", "arm", "level", "case", "peak_r", "t", "at_limit"])
    l = members(l, rcol="peak_r")
    s = l.groupby(["batch", "arm", "level", "case", "group", "t"], as_index=False)[
        "at_limit"].sum().rename(columns={"t": "year", "at_limit": "value"})
    s["value"] = s["value"].astype(float)
    s["metric"] = "lines_at_limit_peak"
    return fill_sum(s, ["lines_at_limit_peak"], "count of line rows")


# ---------------------------------------------------------------- capacity, generation
def capacity_generation():
    c = pd.read_hdf(IN03 / "capacity_generation.h5", "data",
                    where=T_WHERE + " & metric in ['capacity','generation']",
                    columns=["batch", "arm", "level", "case", "metric", "i", "r", "t", "value"])
    tm = tech_map()
    names = pd.Series(c["i"].unique())
    c["tg"] = c["i"].map(dict(zip(names, names.map(tm))))
    s = members(c).groupby(["batch", "arm", "level", "case", "group", "t", "metric", "tg"],
                           as_index=False)["value"].sum().rename(columns={"t": "year"})
    out = []
    for kind, unit in (("capacity", "MW"), ("generation", "MWh")):
        k = s[s["metric"] == kind]
        tot = k.groupby(["batch", "arm", "level", "case", "group", "year"],
                        as_index=False)["value"].sum()
        tot["metric"] = f"{kind}_total"
        a = k.assign(metric=kind + "_" + k["tg"]).drop(columns="tg")
        mets = sorted(a["metric"].unique())
        full = fill_sum(pd.concat([tot, a], ignore_index=True),
                        [f"{kind}_total"] + mets, unit)
        out.append(full)
        # shares: group tech-group total / group total, %
        sh = full[full["metric"] != f"{kind}_total"].merge(
            full[full["metric"] == f"{kind}_total"][
                ["case", "group", "year", "value"]].rename(columns={"value": "total"}),
            on=["case", "group", "year"])
        sh["value"] = np.where(sh["total"] != 0, 100 * sh["value"] / sh["total"], np.nan)
        sh["metric"] = sh["metric"].str.replace(f"{kind}_", f"{kind}_share_", n=1)
        sh["unit"] = "% of group total"
        out.append(sh.drop(columns="total"))
    return pd.concat(out, ignore_index=True)


# ---------------------------------------------------------------- diff, flags
def add_diff(df):
    keys = ["metric", "batch", "arm", "group", "year"]
    base = df[df["level"] == 0][keys + ["value"]].rename(columns={"value": "v0"})
    df = df.merge(base, on=keys, how="left")
    df["diff"] = df["value"] - df["v0"]
    df["pct_of_0GW"] = np.where(df["v0"] != 0, 100 * df["diff"] / df["v0"].abs(), np.nan)
    return df


def series_flags(df):
    """One row per metric, batch, arm, group, year with the two D42 tests."""
    rows = []
    for key, g in df.groupby(["metric", "batch", "arm", "group", "year"], sort=False):
        g = g.sort_values("level")
        lv, d = g["level"].to_numpy(), g["diff"].to_numpy()
        v0 = g["v0"].iloc[0]
        d3 = d[lv == TOP_LEVEL][0] if (lv == TOP_LEVEL).any() else np.nan
        ok = ~np.isnan(d)
        steps = np.diff(d[ok])
        slopes = steps / np.diff(lv[ok])
        sign_change = bool((slopes > 0).any() and (slopes < 0).any())
        if np.isnan(v0) or np.isnan(d3):
            pct3, a, zero_base = np.nan, False, False
        elif v0 == 0:
            pct3, a, zero_base = np.nan, False, d3 != 0
        else:
            pct3, zero_base = 100 * d3 / abs(v0), False
            a = abs(pct3) > THRESH_PCT
        rows.append(dict(zip(["metric", "batch", "arm", "group", "year"], key),
                         v0=v0, diff3=d3, pct3=pct3, test_1pct=a, test_sign=sign_change,
                         zero_base=zero_base,
                         max_abs_step=np.abs(steps).max() if len(steps) else np.nan))
    return pd.DataFrame(rows)


def metric_flags(sf, df):
    out = []
    for m, g in sf.groupby("metric", sort=False):
        a, s = g["test_1pct"].any(), g["test_sign"].any()
        reason = ("3 GW > 1% and sign change" if a and s else "3 GW > 1%" if a
                  else "sign change only" if s else "")
        d = df[(df["metric"] == m) & df["pct_of_0GW"].notna()]
        if len(d):
            r = d.loc[d["pct_of_0GW"].abs().idxmax()]
            maxpct, where = abs(r["pct_of_0GW"]), \
                f"{r['batch']} {r['arm']} {r['group']} {r['year']} {r['level']:g} GW"
        else:
            maxpct, where = np.nan, "0 GW value is 0 or blank everywhere"
        rec = dict(metric=m, flag="moves" if (a or s) else "flat", reason=reason,
                   n_series=len(g), n_1pct=int(g["test_1pct"].sum()),
                   n_sign=int(g["test_sign"].sum()), n_zero_base=int(g["zero_base"].sum()),
                   max_abs_pct=maxpct, max_abs_pct_where=where,
                   unit=df.loc[df["metric"] == m, "unit"].iloc[0])
        if reason == "sign change only":
            ss = g[g["test_sign"]]
            r = ss.loc[ss["max_abs_step"].idxmax()]
            rec["largest_step"] = r["max_abs_step"]
            rec["largest_step_pct_of_0GW"] = (100 * r["max_abs_step"] / abs(r["v0"])
                                              if r["v0"] else np.nan)
            rec["largest_step_where"] = f"{r['batch']} {r['arm']} {r['group']} {r['year']}"
        out.append(rec)
    return pd.DataFrame(out)


# ---------------------------------------------------------------- figures
ARM_COLORS = {"ref": "black", "gaslow": "tab:orange", "loadhigh": "tab:red",
              "loadlow": "tab:blue", "pvadv": "tab:olive", "smrcons": "tab:purple"}
YEAR_STYLE = {2044: ":", 2047: "--", 2050: "-", SC_TOTAL_YEAR: "-"}


def family(m):
    for f in ("capacity_share", "generation_share", "capacity", "generation"):
        if m.startswith(f):
            return f
    return "core"


def figures(df, flags):
    FIG.mkdir(parents=True, exist_ok=True)
    flag_of = dict(zip(flags["metric"], flags["flag"]))
    paths = []
    order = list(dict.fromkeys(df["metric"]))
    for batch, bd in df.groupby("batch", sort=False):
        mets = [m for m in order
                if (bd.loc[bd["metric"] == m, "value"].fillna(0) != 0).any()]
        pages = []
        for fam in ("core", "capacity", "generation", "capacity_share", "generation_share"):
            fm = [m for m in mets if family(m) == fam]
            pages += [fm[i:i + ROWS_PER_PAGE] for i in range(0, len(fm), ROWS_PER_PAGE)]
        for k, pm in enumerate(pages, 1):
            fig, axes = plt.subplots(len(pm), len(GROUPS), figsize=(18, 2.3 * len(pm) + 1),
                                     squeeze=False, sharex=True)
            for i, m in enumerate(pm):
                md = bd[bd["metric"] == m]
                for j, grp in enumerate(GROUPS):
                    ax = axes[i, j]
                    gd = md[md["group"] == grp]
                    for (arm, yr), s in gd.groupby(["arm", "year"], sort=False):
                        s = s.sort_values("level")
                        ax.plot(s["level"], s["diff"], YEAR_STYLE.get(yr, "-"),
                                color=ARM_COLORS.get(arm, "gray"), lw=1, marker=".", ms=3)
                    ax.axhline(0, color="0.7", lw=0.5)
                    ax.tick_params(labelsize=7)
                    ax.yaxis.get_offset_text().set_fontsize(7)
                    if i == 0:
                        ax.set_title(grp, fontsize=10)
                    if j == 0:
                        unit = md["unit"].iloc[0] if len(md) else ""
                        ax.set_ylabel(f"{m}\n[{flag_of.get(m, '')}]\nDiff, {unit}",
                                      fontsize=7)
                    if i == len(pm) - 1:
                        ax.set_xlabel("level, GW", fontsize=8)
            arms = list(dict.fromkeys(bd["arm"]))
            handles = [plt.Line2D([], [], color=ARM_COLORS.get(a, "gray"), label=a) for a in arms]
            handles += [plt.Line2D([], [], color="k", ls=YEAR_STYLE[y], label=str(y))
                        for y in YEARS]
            fig.legend(handles=handles, loc="upper center", ncol=len(handles), fontsize=8)
            fig.suptitle(f"04s screen, {batch}, page {k}/{len(pages)}: Diff against the arm's "
                         "0 GW case (rough screen, not findings; 2044-2050 cost uses solid line)",
                         fontsize=10, y=0.995)
            fig.tight_layout(rect=(0, 0, 1, 0.97))
            p = FIG / f"04s_screen_{batch}_p{k}.png"
            fig.savefig(p, dpi=90)
            plt.close(fig)
            paths.append(p)
            print("figure", p.name, flush=True)
    return paths


# ---------------------------------------------------------------- report
def md_table(df):
    cols = list(df.columns)
    lines = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in df.itertuples(index=False):
        cells = []
        for v in row:
            if isinstance(v, float):
                cells.append("" if np.isnan(v) else f"{v:,.4g}")
            else:
                cells.append(str(v))
        lines.append("| " + " | ".join(cells) + " |")
    return "\n".join(lines)


def rel(p):
    return Path(p).resolve().relative_to(REPO).as_posix()


def report(df, sf, flags, paths):
    n_moves = int((flags["flag"] == "moves").sum())
    only_sign = flags[flags["reason"] == "sign change only"]
    t = ["# Check report: 04s_screen (rough first look, D42)", "",
         "Lighter rules (D42): no Verifier, no Reviewer, no citations. "
         "These numbers are a screen, not findings.", "",
         "## Counts", "",
         f"- Rows in `outputs/04_analyze/04s_screen.csv`: {len(df):,}",
         f"- Cases: {df['case'].nunique()} ({', '.join(f'{b} {n}' for b, n in df.groupby('batch')['case'].nunique().items())})",
         f"- Metrics: {df['metric'].nunique()}; series (metric x batch x arm x group x year): {len(sf):,}",
         f"- Metrics flagged moves: {n_moves}; flat: {len(flags) - n_moves}",
         f"- Metrics flagged only by sign change: {len(only_sign)}",
         f"- Series where the 0 GW value is 0 and the 3 GW Diff is not (1% test not evaluable): "
         f"{int(sf['zero_base'].sum())}",
         f"- Every 0 GW Diff is 0: {bool((df.loc[df['level'] == 0, 'diff'].fillna(0) == 0).all())}",
         ""]
    if len(only_sign):
        r = only_sign.loc[(only_sign["largest_step_pct_of_0GW"].abs()).idxmax()] \
            if only_sign["largest_step_pct_of_0GW"].notna().any() else only_sign.iloc[0]
        t += ["Largest step among sign-change-only metrics (as % of the 0 GW value): "
              f"{r['metric']}, {r['largest_step']:.4g} {r['unit']} "
              f"({r['largest_step_pct_of_0GW']:.3g} % of 0 GW), at {r['largest_step_where']}.", ""]
    t += ["## Per-metric flags", "",
          "max_abs_pct: largest |Diff| as % of the 0 GW value over all levels, arms, groups "
          "and years; where = batch arm group year level. n_1pct / n_sign: number of series "
          "that pass the 1% test / the sign-change test.", "",
          md_table(flags[["metric", "flag", "reason", "max_abs_pct", "max_abs_pct_where",
                          "n_1pct", "n_sign", "n_zero_base", "n_series"]]), ""]
    if len(only_sign):
        t += ["## Sign-change-only metrics: largest step", "",
              "largest_step: largest |change in Diff| between neighboring levels in any "
              "series with a sign change.", "",
              md_table(only_sign[["metric", "largest_step", "unit", "largest_step_pct_of_0GW",
                                  "largest_step_where"]]), ""]
    t += ["## Figures", "",
          "Rows = metric (only metrics nonzero somewhere in the batch), columns = group, "
          "color = arm, line style = year (dotted 2044, dashed 2047, solid 2050).", ""]
    t += [f"- `{rel(p)}`" for p in paths]
    t += ["", "## Method notes", "",
          "- Prices: group sum of dollars / group sum of `load` quantity (D6). Peak: highest "
          "block of `group_block_price` (D14). Ratio blank where the average is <= 0 (D37b).",
          "- Capacity and generation: totals by ReEDS tech group (`tech_map.csv` at 0c0ea27, "
          "D37g); shares = tech-group total / group total.",
          "- Expenditure flows: flows crossing the group border, by type and direction "
          "(out = r in group; in = rr in group). Zero for `wecc`.",
          "- new_lines: `invtran_out` summed over lines with r or rr in the group (per solve year).",
          "- lines_at_limit_peak: count of at-limit line rows in each member region's rank-1 "
          "peak block(s), summed over members (rough; lines between two members count twice).",
          "- Missing rows in sum metrics are 0.", ""]
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(t), encoding="utf-8")


def main():
    parts = [prices(), system_cost(), net_imports(), expenditure_flows(), new_lines(),
             lines_at_limit(), capacity_generation()]
    df = pd.concat(parts, ignore_index=True)
    df = df[["metric", "batch", "arm", "group", "year", "level", "case", "value", "unit"]]
    df = add_diff(df)
    df = df.sort_values(["batch", "metric", "arm", "group", "year", "level"],
                        key=lambda s: s.astype(str) if s.name == "year" else s)
    OUT.mkdir(parents=True, exist_ok=True)
    cols = ["metric", "batch", "arm", "group", "year", "level", "value", "diff",
            "pct_of_0GW", "unit", "case"]
    df[cols].to_csv(OUT / "04s_screen.csv", index=False)
    print("table written", flush=True)
    sf = series_flags(df)
    flags = metric_flags(sf, df)
    flags.to_csv(OUT / "04s_flags.csv", index=False)
    print("flags written", flush=True)
    paths = figures(df, flags)
    report(df, sf, flags, paths)
    print(flags[["metric", "flag", "reason", "max_abs_pct", "max_abs_pct_where"]].to_string())
    print("figures:", *[rel(p) for p in paths], sep="\n  ")


if __name__ == "__main__":
    main()
