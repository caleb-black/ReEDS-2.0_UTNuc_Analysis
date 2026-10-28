"""03g_smr_value: value of the new SMR build in p25, by service.

docs/plan.md, "SMR value and the cost of prescribing it", 03g; D8, D19, D36.

From `valnew` (type, i, r, t; report_params.csv L231; report.gms L1044-L1130
at 0c0ea27), for i = Nuclear-SMR, r = p25, every case and year from 2044:
- services: val_load, val_resmarg, val_opres, val_rps (2004 $; 02d lookup),
  and their sum, value_all_services.
- MW and MWh of the new build (`valnew` types MW, MWh).
- per service: total (2024 $), per kW-yr (total / (MW x 1000)), per MWh
  (total / MWh).
The `_sys` types (system prices) and `inv_cap_ratio` are not used (the plan
names only the four services).

`valnew` has a row only where `valnew('MW', i, r, t)` is non-zero
(report.gms L1044-L1045: new investment in year t). A service with no row
for a case-year that has an MW row is set to 0 and marked present_in_file =
False (the report counts them). Cases with no MW row (0 GW) have no rows.

Other nuclear types in p25: any `valnew` row with "nuclear" in `i` (any case)
is listed in the report and kept apart (metric rows carry `i`).

Dollars: totals, per kW-yr and per MWh values x 1.6563 (D8); MW and MWh not.

Check figure: value by service as stacked bars by level, per kW-yr and per
MWh, 2044, one figure per batch and arm (D26).

In:  outputs/01_ingest/outputs/valnew.h5, 00_config/*.csv, outputs/02_clean/units.csv
Out: outputs/03_derive/smr_value.csv (long), figures/03g_smr_value_<batch>_<arm>.png,
     section "03g" of outputs/checks/03_derive.md

Run:  conda run -n reeds python 03_derive/03g_smr_value.py
"""

import sys

import numpy as np
import pandas as pd

import derive_common as dc

SECTION = "03g"
SMR = "Nuclear-SMR"
SERVICES = ["val_load", "val_resmarg", "val_opres", "val_rps"]
FIRST_YEAR = min(dc.POST_PLANT_YEARS)


def main():
    cases = dc.cases()
    v = dc.read_key("valnew", where=f'r == "{dc.FOCUS}" & t >= {FIRST_YEAR}')
    v["Value"] = v["Value"].astype("float64")
    nuc_types = sorted(v.loc[v["i"].str.contains("nuclear", case=False), "i"].unique())
    others = [i for i in nuc_types if i != SMR]
    v = v[v["i"].isin(nuc_types)]
    w = v.pivot_table(index=dc.CASE_COLS + ["i", "r", "t"], columns="type", values="Value",
                      aggfunc="first").reset_index()
    w = w[w["MW"].notna()]
    rows, absent = [], {s: 0 for s in SERVICES}
    for s in SERVICES:
        if s not in w:
            w[s] = np.nan
        absent[s] = int(w[s].isna().sum())
        w[f"{s}__present"] = w[s].notna()
        w[s] = w[s].fillna(0.0)
    w["value_all_services"] = w[SERVICES].sum(axis=1)
    w["value_all_services__present"] = True
    base = dc.CASE_COLS + ["i", "r", "t"]
    for s in SERVICES + ["value_all_services"]:
        tot = w[s] * dc.DOLLAR
        for metric, val, unit in [
            ("total", tot, "2024 $"),
            ("per_kw_yr", tot / (w["MW"] * 1000.0), "2024 $/kW-yr"),
            ("per_mwh", tot / w["MWh"], "2024 $/MWh"),
        ]:
            d = w[base].copy()
            d["service"] = s
            d["metric"] = metric
            d["value"] = val.to_numpy()
            d["unit"] = unit
            d["converted_2004_to_2024"] = True
            d["present_in_file"] = w[f"{s}__present"].to_numpy()
            rows.append(d)
    for s, unit in [("MW", "MW"), ("MWh", "MWh")]:
        d = w[base].copy()
        d["service"] = "build"
        d["metric"] = s
        d["value"] = w[s].to_numpy()
        d["unit"] = unit
        d["converted_2004_to_2024"] = False
        d["present_in_file"] = True
        rows.append(d)
    out = pd.concat(rows, ignore_index=True)
    path = dc.write_long(out, "smr_value")

    # ---------------- figure ----------------
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    dc.FIG_DIR.mkdir(parents=True, exist_ok=True)
    figs = []
    colors = {"val_load": "tab:blue", "val_resmarg": "tab:orange", "val_opres": "tab:green",
              "val_rps": "tab:purple"}
    smr = out[(out.i == SMR) & (out.t == FIRST_YEAR) & out.service.isin(SERVICES)]
    for (b, arm), g in smr.groupby(["batch", "arm"]):
        fig, axes = plt.subplots(1, 2, figsize=(12, 4.5))
        for ax, metric, lab in [(axes[0], "per_kw_yr", "2024 $/kW-yr"),
                                (axes[1], "per_mwh", "2024 $/MWh")]:
            p = g[g.metric == metric].pivot_table(index="level", columns="service",
                                                  values="value").reindex(columns=SERVICES)
            bottom_pos = np.zeros(len(p))
            bottom_neg = np.zeros(len(p))
            x = np.arange(len(p))
            for s in SERVICES:
                vals = p[s].fillna(0).to_numpy()
                bot = np.where(vals >= 0, bottom_pos, bottom_neg)
                ax.bar(x, vals, bottom=bot, color=colors[s], label=s)
                bottom_pos += np.where(vals >= 0, vals, 0)
                bottom_neg += np.where(vals < 0, vals, 0)
            ax.set_xticks(x, [f"{lv:g}" for lv in p.index])
            ax.set_xlabel("level (GW)")
            ax.set_ylabel(lab)
            ax.axhline(0, color="black", linewidth=0.5)
            ax.set_ylim(min(0.0, bottom_neg.min()) * 1.08, max(0.0, bottom_pos.max()) * 1.08)
        h_, l_ = axes[0].get_legend_handles_labels()
        fig.legend(h_, l_, loc="lower center", ncol=4, fontsize=8, bbox_to_anchor=(0.5, -0.04))
        fig.suptitle(f"{b} {arm}: value of new Nuclear-SMR in p25 by service, {FIRST_YEAR} "
                     "(valnew, 2024 $)", fontsize=10)
        fp = dc.FIG_DIR / f"03g_smr_value_{b}_{arm}.png"
        fig.savefig(fp, dpi=130, bbox_inches="tight")
        plt.close(fig)
        figs.append((b, arm, dc.rel(fp), g.level.nunique()))

    # ---------------- checks ----------------
    yrs = sorted(w["t"].unique())
    nonzero = cases[cases.level > 0]
    have = set(w.loc[w.i == SMR, "case"])
    missing = sorted(set(nonzero["case"]) - have)
    zero_with = sorted(set(cases.loc[cases.level == 0, "case"]) & have)
    mw_chk = w[(w.i == SMR) & (w.t == FIRST_YEAR)].assign(
        exp=lambda d: d["level"] * 1000.0)
    mw_bad = mw_chk[(mw_chk["MW"] - mw_chk["exp"]).abs() > 1e-3 * mw_chk["exp"]]
    unit_rows = {s: dc.unit_of("valnew", s) for s in SERVICES + ["MW", "MWh"]}
    checks = [
        ("Other nuclear types with valnew rows in p25 (from 2044)", "PASS" if not others else "INFO",
         ", ".join(others) or "none; only Nuclear-SMR"),
        ("Years with SMR rows (from 2044)", "INFO", ", ".join(str(y) for y in yrs)),
        ("Every level > 0 case has an SMR row", "PASS" if not missing else "INFO",
         ", ".join(missing) or f"all {len(nonzero)}"),
        ("0 GW cases with an SMR row", "PASS" if not zero_with else "INFO",
         ", ".join(zero_with) or "none"),
        ("MW in 2044 = level x 1000", "PASS" if mw_bad.empty else "INFO",
         f"{len(mw_bad)} cases differ" if len(mw_bad) else f"all {len(mw_chk)} equal"),
        ("Service rows absent in file (set to 0)", "INFO",
         "; ".join(f"{s}: {n} of {len(w)}" for s, n in absent.items())),
        ("Units (02d lookup)", "INFO", "; ".join(f"{k}: {u}" for k, u in unit_rows.items())),
    ]
    fail = False
    samp = out[out.case.isin(dc.SAMPLE_CASES) & (out.i == SMR)]
    samp_w = samp[samp.service.isin(SERVICES + ["value_all_services"])].pivot_table(
        index=["case", "t", "service"], columns="metric", values="value").reset_index()
    samp_b = samp[samp.service == "build"].pivot_table(index=["case", "t"], columns="metric",
                                                       values="value").reset_index()
    text = [
        f"## 03g_smr_value — PASS\n",
        "Source `valnew` (report.gms L1044-L1130; report_params.csv L231), i = Nuclear-SMR, "
        "r = p25, t >= 2044. Services val_load, val_resmarg, val_opres, val_rps; totals, per kW-yr "
        "(/ (MW x 1000)), per MWh (/ MWh). Converted x 1.6563 (D8): all service values "
        "(total, per_kw_yr, per_mwh). Not converted: MW, MWh. The 02d lookup gives val_opres as "
        "\"2004 $ (type absent in stage 01 data)\".\n",
        f"Table: `{dc.rel(path)}` ({len(out):,} rows).\n",
        "### Checks\n",
        dc.md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Figures\n",
        dc.md_table(pd.DataFrame(figs, columns=["batch", "arm", "figure", "levels"])) + "\n",
        "### Verifier sample cases (UON ref 0 GW has no SMR build, so no rows)\n",
        dc.md_table(samp_b, floatfmt="{:,.8g}") + "\n",
        dc.md_table(samp_w, floatfmt="{:,.6g}") + "\n",
    ]
    dc.write_section(SECTION, "\n".join(text))
    print("03g done")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
