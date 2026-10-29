"""analyze_common: shared helpers for the 04_analyze scripts (not a stage step).

Holds the group aggregation (04a), the Diff (04b) and the step slope (04c), so
that 04b, 04c, 04e and 04f can rebuild what they need in memory. Plan rule 2:
a script never reads its own stage's outputs, so no 04 script reads another 04
script's file. Inputs are stage 03 outputs, the stage 01 per-key files for net
imports and new lines (D36, D37f), 00_config and the 02d units lookup.

Batch: every function works on one batch (`--batch`, default UON). UON and UOS
are never mixed (D26); output file names carry the batch.

Rules used (docs/decisions.md, docs/data_dictionary.md "Metrics"):
- Groups from 00_config/region_groups.csv (D7, D13, D35a).
- Prices: group sum of dollars / group sum of `load` quantity (D6, D14). Never an
  average of prices. Dollars from stage 03 are already 2024 $ (D8, plan rule 6).
- Peak/average ratio: the group's own peak (highest block of the group block
  price, D14, from 03a group_block_price) / group average energy price; blank
  where the group average is <= 0 (D37b).
- Annualized system cost (D44, 03b2): sum over members, each year 2044-2050 and
  the 2044-2050 total. D10 cost (03b): same sums, secondary cross-check only.
- Net imports (`net_import_ann_rep`, MWh): sum over members (data dictionary).
- New lines (`invtran_out`, MW): sum over lines with r or rr in the group
  ("Sum over lines touching the group"); a line inside the group counts once,
  wecc counts all lines (D46d).
- Line at limit in the peak block: per line touching p25 (data dictionary), in
  p25's rank-1 peak block(s) from 03f line_use_peak.
- Missing rows in summed stage 01 metrics (net imports, new lines) are 0; the
  count is in n_missing_filled and in the 04a report.
- Diff = case minus the same batch-arm's 0 GW case, same group and year (D2).
  % only for D11 metrics (prices, system cost); see PCT_FLOOR.
"""

import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(REPO / "03_derive"))
import derive_common as dc  # noqa: E402  (paths, units lookup, report helpers)

CONFIG = REPO / "00_config"
IN03 = REPO / "outputs" / "03_derive"
IN01 = REPO / "outputs" / "01_ingest" / "outputs"
OUT = REPO / "outputs" / "04_analyze"
FIG = OUT / "figures"
REPORT = REPO / "outputs" / "checks" / "04_analyze.md"
REPORT_TITLE = "# Check report: 04_analyze\n\n"

GROUPS = ["focus", "utah_rest", "neighbors", "rest_wecc", "wecc"]
FOCUS = "p25"
FIRST_POST_YEAR = 2044
TOTAL_T = "2044-2050"            # annualized cost: undiscounted sum of 7 years (D44, D46g)
D10_TOTAL_T = "2044+2047+2050"   # D10 cross-check: sum of the 3 solve years (D10, D46g)
ID = ["batch", "arm", "level", "case"]

# % (D11) is computed only for these metrics, and left blank where |0 GW value|
# is below the floor for the metric's unit (D46a).
PCT_METRICS = {"avg_energy_price", "avg_allin_price",
               "annualized_cost", "annualized_cost_capital", "annualized_cost_op",
               "d10_system_cost", "d10_system_cost_inv", "d10_system_cost_op"}
PCT_FLOOR = {"price": 1.0,       # 2024 $/MWh
             "cost": 1.0e6}      # 2024 $

PRIMARY = "primary"
XCHECK = "secondary cross-check (D10), not the system cost result"
COMPONENT = "component (not diffed, D46e)"

SETTINGS = dc.SETTINGS
SOLVE_YEARS = [int(x) for x in SETTINGS["solve_years"].split()]


# ---------------------------------------------------------------- setup
def parse_batch(desc):
    batches = sorted(pd.read_csv(CONFIG / "study_cases.csv")["batch"].unique())
    ap = argparse.ArgumentParser(description=desc)
    ap.add_argument("--batch", default="UON", choices=batches,
                    help="one batch only (D26); UOS only to check UON claims (D43d)")
    return ap.parse_args().batch


def cases(batch):
    c = pd.read_csv(CONFIG / "study_cases.csv")
    return c.loc[c["batch"] == batch, ID].reset_index(drop=True)


def groups(batch):
    g = pd.read_csv(CONFIG / "region_groups.csv")
    return g.loc[g["batch"] == batch, ["group", "region"]].reset_index(drop=True)


def members(df, batch, rcol="r"):
    """Join each region row to every group it belongs to."""
    return df.merge(groups(batch).rename(columns={"region": rcol}), on=rcol)


def grid(batch, metrics, years):
    g = cases(batch).merge(pd.DataFrame({"group": GROUPS}), how="cross")
    g = g.merge(pd.DataFrame({"t": [str(y) for y in years]}), how="cross")
    return g.merge(pd.DataFrame({"metric": metrics}), how="cross")


def fill_sum(df, batch, metrics, years, unit):
    """Zero-fill a summed metric over every case x group x year."""
    out = grid(batch, metrics, years).merge(
        df[ID + ["group", "t", "metric", "value"]],
        on=ID + ["group", "t", "metric"], how="left")
    out["n_missing_filled"] = out["value"].isna().astype(int)
    out["value"] = out["value"].fillna(0.0)
    out["unit"] = unit
    return out


# ---------------------------------------------------------------- prices
def group_prices(batch):
    """Group average energy / all-in price, peak/average ratio, with components."""
    p = pd.read_hdf(IN03 / "prices_region.h5", "data",
                    where=f'batch == "{batch}" & metric in '
                          "['load_quant','energy_dollars','allin_dollars']",
                    columns=ID + ["r", "t", "metric", "value", "unit"])
    allin_ns = p[(p["metric"] == "allin_dollars") & (p["unit"] != "2024 $")]
    allin_ns = allin_ns[ID + ["r", "t"]].assign(allin_not_stated=1)
    w = p.pivot_table(index=ID + ["r", "t"], columns="metric", values="value",
                      aggfunc="sum").reset_index()
    w = w.merge(allin_ns, on=ID + ["r", "t"], how="left")
    w["allin_not_stated"] = w["allin_not_stated"].fillna(0)
    w = members(w, batch)
    s = w.groupby(ID + ["group", "t"], as_index=False)[
        ["load_quant", "energy_dollars", "allin_dollars", "allin_not_stated"]].sum()
    s["n_regions"] = w.groupby(ID + ["group", "t"]).size().to_numpy()
    s["avg_energy_price"] = s["energy_dollars"] / s["load_quant"]
    s["avg_allin_price"] = s["allin_dollars"] / s["load_quant"]

    g = pd.read_hdf(IN03 / "group_block_price.h5", "data",
                    where=f'batch == "{batch}" & metric == "group_energy_price"',
                    columns=["case", "group", "h", "t", "value"])
    mx = g.groupby(["case", "group", "t"])["value"].transform("max")
    top = g[g["value"] == mx].sort_values("h")
    pk = top.groupby(["case", "group", "t"], as_index=False).agg(
        peak_energy_price=("value", "first"), peak_h=("h", lambda x: ";".join(x)))
    s = s.merge(pk, on=["case", "group", "t"], how="left")
    s["peak_avg_ratio"] = np.where(s["avg_energy_price"] > 0,
                                   s["peak_energy_price"] / s["avg_energy_price"], np.nan)
    s["t"] = s["t"].astype(int).astype(str)

    allin_unit = np.where(s["allin_not_stated"] > 0,
                          "2024 $/MWh (includes state_rps/nat_gen dollars, unit not stated)",
                          "2024 $/MWh")
    spec = [("avg_energy_price", "2024 $/MWh", PRIMARY),
            ("avg_allin_price", None, PRIMARY),
            ("peak_avg_ratio", "ratio", PRIMARY),
            ("load_quant", "MWh", COMPONENT),
            ("energy_dollars", "2024 $", COMPONENT),
            ("allin_dollars", None, COMPONENT),
            ("peak_energy_price", "2024 $/MWh", COMPONENT + "; peak price alone on hold (D43a)")]
    rows = []
    for m, unit, status in spec:
        x = s[ID + ["group", "t", "n_regions"]].copy()
        x["metric"], x["value"], x["status"] = m, s[m], status
        if m == "avg_allin_price":
            x["unit"] = allin_unit
        elif m == "allin_dollars":
            x["unit"] = np.where(s["allin_not_stated"] > 0,
                                 "2024 $ (includes state_rps/nat_gen dollars, unit not stated)",
                                 "2024 $")
        else:
            x["unit"] = unit
        x["detail"] = s["peak_h"] if m in ("peak_energy_price", "peak_avg_ratio") else ""
        rows.append(x)
    return pd.concat(rows, ignore_index=True)


# ---------------------------------------------------------------- system cost
def group_annualized_cost(batch):
    """D44 annualized cost (03b2): capital, op, total; 2044..2050 and 2044-2050."""
    a = pd.read_csv(IN03 / "annualized_cost.csv")
    a = a[a["batch"] == batch]
    units = set(a["unit"])
    s = members(a, batch).groupby(ID + ["group", "t", "metric"], as_index=False)["value"].sum()
    s["t"] = s["t"].astype(str)
    years = sorted(a["t"].unique())
    mets = ["annualized_cost", "annualized_cost_capital", "annualized_cost_op"]
    out1 = fill_sum(s, batch, mets, years, "2024 $")
    tt = pd.read_csv(IN03 / "annualized_cost_total.csv")
    tt = tt[tt["batch"] == batch]
    units |= set(tt["unit"])
    ts = members(tt, batch).groupby(ID + ["group", "metric"], as_index=False)["value"].sum()
    ts["metric"] = ts["metric"].str.replace("_2044_2050", "", regex=False)
    ts["t"] = TOTAL_T
    out2 = fill_sum(ts, batch, mets, [TOTAL_T], "2024 $ (undiscounted sum of 2044-2050)")
    out = pd.concat([out1, out2], ignore_index=True)
    out["status"] = PRIMARY + " system cost (D44)"
    out["detail"] = ""
    return out, units


def group_d10_cost(batch):
    """D10 cost (03b), carried only as a labeled secondary cross-check (D44)."""
    a = pd.read_csv(IN03 / "system_cost.csv")
    a = a[a["batch"] == batch]
    s = members(a, batch).groupby(ID + ["group", "t", "metric"], as_index=False)["value"].sum()
    s["t"] = s["t"].astype(str)
    s["metric"] = "d10_" + s["metric"]
    years = sorted(a["t"].unique())
    mets = ["d10_system_cost", "d10_system_cost_inv", "d10_system_cost_op"]
    out1 = fill_sum(s, batch, mets, years, "2024 $")
    tt = pd.read_csv(IN03 / "system_cost_total.csv")
    tt = tt[tt["batch"] == batch]
    ts = members(tt, batch).groupby(ID + ["group", "metric"], as_index=False)["value"].sum()
    ts["metric"] = "d10_" + ts["metric"].str.replace("_2044_2050", "", regex=False)
    ts["t"] = D10_TOTAL_T
    out2 = fill_sum(ts, batch, ["d10_system_cost"], [D10_TOTAL_T],
                    "2024 $ (sum of 2044, 2047, 2050)")
    out = pd.concat([out1, out2], ignore_index=True)
    out["status"] = XCHECK
    out["detail"] = ""
    return out


# ---------------------------------------------------------------- trade, lines
def group_net_imports(batch):
    n = pd.read_hdf(IN01 / "net_import_ann_rep.h5", "data", where=f'batch == "{batch}"')
    n["Value"] = n["Value"].astype("float64")   # stage 01 is float32 (D33); sum in float64
    s = members(n, batch).groupby(ID + ["group", "t"], as_index=False)["Value"].sum()
    s = s.rename(columns={"Value": "value"})
    s["t"] = s["t"].astype(int).astype(str)
    s["metric"] = "net_imports"
    out = fill_sum(s, batch, ["net_imports"], SOLVE_YEARS, dc.unit_of("net_import_ann_rep"))
    out["status"], out["detail"] = PRIMARY, ""
    return out


def group_new_lines(batch):
    v = pd.read_hdf(IN01 / "invtran_out.h5", "data", where=f'batch == "{batch}"')
    v["Value"] = v["Value"].astype("float64")   # stage 01 is float32 (D33); sum in float64
    rows = []
    for grp, mem in groups(batch).groupby("group"):
        mem = set(mem["region"])
        x = v[v["r"].isin(mem) | v["rr"].isin(mem)]
        x = x.groupby(ID + ["t"], as_index=False)["Value"].sum()
        x["group"] = grp
        rows.append(x)
    s = pd.concat(rows, ignore_index=True).rename(columns={"Value": "value"})
    s["t"] = s["t"].astype(int).astype(str)
    s["metric"] = "new_lines"
    out = fill_sum(s, batch, ["new_lines"], SOLVE_YEARS, dc.unit_of("invtran_out"))
    out["status"], out["detail"] = PRIMARY, ""
    return out


def p25_lines(batch):
    """Line use in p25's rank-1 peak block(s), one row per line direction (03f).

    With tied peak blocks (n_blocks_at_price > 1), the row gives the largest
    utilization over the tied blocks, the number of tied blocks at limit, and
    at_limit_any (D46b).
    """
    l = pd.read_hdf(IN03 / "line_use_peak.h5", "data",
                    where=f'batch == "{batch}" & peak_r == "{FOCUS}" & peak_rank == 1',
                    columns=ID + ["t", "h", "r", "rr", "trtype", "line_capacity_avg_mw",
                                  "value", "at_limit"])
    k = ID + ["t", "r", "rr", "trtype"]
    out = l.sort_values("h").groupby(k, as_index=False).agg(
        n_peak_blocks=("h", "nunique"), peak_h=("h", lambda x: ";".join(x)),
        util_max=("value", "max"), n_blocks_at_limit=("at_limit", "sum"),
        at_limit_any=("at_limit", "any"),
        line_capacity_avg_mw=("line_capacity_avg_mw", "first"))
    out["t"] = out["t"].astype(int).astype(str)
    out["unit"] = "fraction of capacity, per direction (util_max)"
    return out


def focus_lines_at_limit(lines, batch):
    s = lines.groupby(ID + ["t"], as_index=False)["at_limit_any"].sum()
    s = s.rename(columns={"at_limit_any": "value"})
    s["value"] = s["value"].astype(float)
    s["group"], s["metric"] = "focus", "n_lines_at_limit_peak"
    s["unit"] = "count of line directions touching p25 at limit in p25's peak block"
    s["status"] = PRIMARY + " (line summary, focus only, D46c)"
    s["detail"] = ""
    return s


# ---------------------------------------------------------------- all groups
def build_groups(batch, with_components=True):
    """The 04a long table for one batch: every go-on metric for the five groups."""
    cost, cost_units = group_annualized_cost(batch)
    lines = p25_lines(batch)
    parts = [group_prices(batch), cost, group_d10_cost(batch), group_net_imports(batch),
             group_new_lines(batch), focus_lines_at_limit(lines, batch)]
    df = pd.concat(parts, ignore_index=True)
    if not with_components:
        df = df[~df["status"].str.startswith("component")]
    cols = ID + ["group", "t", "metric", "value", "unit", "status", "detail"]
    df = df[cols + [c for c in ("n_regions", "n_missing_filled") if c in df.columns]]
    df["year_sort"] = df["t"].str.slice(0, 4).astype(int) + df["t"].str.len().gt(4) * 0.5
    df = df.sort_values(["metric", "arm", "group", "year_sort", "level"]).drop(columns="year_sort")
    return df.reset_index(drop=True), lines, cost_units


# ---------------------------------------------------------------- diff, slopes
def pct_floor(metric):
    return PCT_FLOOR["price"] if "price" in metric else PCT_FLOOR["cost"]


def add_diff(df, keys):
    """Diff vs the same batch-arm's 0 GW case, same keys (D2); % per D11."""
    base = df[df["level"] == 0][keys + ["value"]].rename(columns={"value": "value_0GW"})
    out = df.merge(base, on=keys, how="left")
    out["diff"] = out["value"] - out["value_0GW"]
    floor = out["metric"].map(pct_floor) if "metric" in out else PCT_FLOOR["price"]
    ok = out["metric"].isin(PCT_METRICS) & (out["value_0GW"].abs() >= floor)
    out["diff_pct"] = np.where(ok, 100 * out["diff"] / out["value_0GW"].abs(), np.nan)
    out["pct_rule"] = np.where(~out["metric"].isin(PCT_METRICS), "absolute only (D11)",
                               np.where(ok, "% of |0 GW value| (D11)",
                                        "blank: |0 GW value| below floor"))
    return out


def group_diff(batch):
    df, lines, units = build_groups(batch, with_components=False)
    keys = ["batch", "arm", "group", "t", "metric"]
    return add_diff(df, keys), lines, units


def step_slopes(d, keys):
    """Step slope between each pair of neighboring levels (D41): Diff change per GW."""
    d = d.sort_values(keys + ["level"])
    g = d.groupby(keys, sort=False)
    out = d[keys + ["unit"]].copy()
    out["level_from"] = g["level"].shift(0)
    out["level_to"] = g["level"].shift(-1)
    out["diff_from"] = d["diff"]
    out["diff_to"] = g["diff"].shift(-1)
    out = out.dropna(subset=["level_to"])
    out["level_mid"] = (out["level_from"] + out["level_to"]) / 2
    out["step_slope"] = (out["diff_to"] - out["diff_from"]) / (out["level_to"] - out["level_from"])
    out["unit"] = out["unit"] + " per GW"
    return out.reset_index(drop=True)


def shape_notes(sl, keys, rel_tol=1e-6):
    """Per series: direction changes (step-slope sign changes) and the largest kink.

    Steps with |slope| <= rel_tol x max|slope| of the series are treated as flat
    and skipped for the sign test (D46f). kink = largest |change between consecutive
    step slopes| / max|slope|. For the written notes only; nothing is explained.
    """
    rows = []
    for k, g in sl.groupby(keys, sort=False):
        s = g.sort_values("level_from")
        v = s["step_slope"].to_numpy()
        lv = s["level_from"].to_numpy()
        m = np.nanmax(np.abs(v)) if len(v) and np.isfinite(v).any() else 0.0
        if m == 0:
            rows.append(dict(zip(keys, k), max_abs_slope=0.0, n_dir_changes=0,
                             dir_change_at="", kink=0.0, kink_at=np.nan))
            continue
        sig = np.where(np.abs(v) > rel_tol * m, np.sign(v), 0)
        nz = [(lv[i], sig[i]) for i in range(len(sig)) if sig[i] != 0 and np.isfinite(v[i])]
        at = [f"{b[0]:g}" for a, b in zip(nz, nz[1:]) if a[1] != b[1]]
        dv = np.abs(np.diff(v))
        j = int(np.nanargmax(dv)) if len(dv) else 0
        rows.append(dict(zip(keys, k), max_abs_slope=m, n_dir_changes=len(at),
                         dir_change_at=" ".join(at),
                         kink=(dv[j] / m) if len(dv) else 0.0,
                         kink_at=lv[j + 1] if len(dv) else np.nan))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------- io, report
def write_csv(df, name, batch):
    OUT.mkdir(parents=True, exist_ok=True)
    path = OUT / f"{name}_{batch}.csv"
    df.to_csv(path, index=False)
    return path


def section(sec, batch, text):
    dc.write_section(f"{sec} {batch}", text, path=REPORT, title=REPORT_TITLE)


md_table = dc.md_table
rel = dc.rel
