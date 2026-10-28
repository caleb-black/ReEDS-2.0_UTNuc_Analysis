"""03h_smr_cost_gap: net value of the SMR's energy (NVOE), D19.

docs/plan.md, "SMR value and the cost of prescribing it", 03h; D8, D19, D36.

For i = Nuclear-SMR, r = p25, each case and year from 2044 where both
`valnew` (MW row) and `lcoe_built` have a row:
- value_per_mwh = (val_load + val_resmarg + val_opres + val_rps) / MWh,
  from `valnew` (report.gms L1044-L1130; absent service rows = 0, as in 03g).
- lcoe_built (`lcoe_built`, i, r, t; $/MWh; report_params.csv L116;
  report.gms L264-L284).
- nvoe = value_per_mwh - lcoe_built (D19; NVOE as in model_documentation.md
  L3333-L3354).
- net_value = value - lcoe_built x MWh (2024 $), and net_value_per_kw_yr =
  net_value / (MW x 1000). This is the same quantity as nvoe x MWh; it is
  given per kW-yr because plan 04f compares "the net value per kW (03h)".
INFERENCE (plan): for a forced build, a negative net value is the part the
system pays to force it in.

Dollar year of `lcoe_built`: NOT STATED (02d lookup: "$/MWh (dollar year not
stated)"; report_params.csv L116 gives "$/MWh"). D19 subtracts it from the
`valnew` value (2004 $). That subtraction needs both in the same dollars, so
lcoe_built is multiplied by the same 1.6563 here. This is flagged in the
report as an open item for Caleb; the unconverted lcoe_built is kept in the
table (metric lcoe_built_model_units).

In:  outputs/01_ingest/outputs/valnew.h5, lcoe_built.h5, 00_config/*.csv,
     outputs/02_clean/units.csv
Out: outputs/03_derive/smr_cost_gap.csv (long), section "03h" of
     outputs/checks/03_derive.md

Run:  conda run -n reeds python 03_derive/03h_smr_cost_gap.py
"""

import sys

import pandas as pd

import derive_common as dc

SECTION = "03h"
SMR = "Nuclear-SMR"
SERVICES = ["val_load", "val_resmarg", "val_opres", "val_rps"]
FIRST_YEAR = min(dc.POST_PLANT_YEARS)


def main():
    v = dc.read_key("valnew", where=f'r == "{dc.FOCUS}" & i == "{SMR}" & t >= {FIRST_YEAR}')
    v["Value"] = v["Value"].astype("float64")
    w = v.pivot_table(index=dc.CASE_COLS + ["i", "r", "t"], columns="type", values="Value",
                      aggfunc="first").reset_index()
    w = w[w["MW"].notna()]
    for s in SERVICES:
        if s not in w:
            w[s] = 0.0
        w[s] = w[s].fillna(0.0)
    w["value"] = w[SERVICES].sum(axis=1)
    lc = dc.read_key("lcoe_built", where=f'r == "{dc.FOCUS}" & i == "{SMR}" & t >= {FIRST_YEAR}')
    lc = lc.rename(columns={"Value": "lcoe"})
    lc["lcoe"] = lc["lcoe"].astype("float64")
    m = w.merge(lc, on=dc.CASE_COLS + ["i", "r", "t"], how="outer", indicator=True)
    only_v = m[m["_merge"] == "left_only"]
    only_l = m[m["_merge"] == "right_only"]
    m = m[m["_merge"] == "both"].copy()

    m["value_per_mwh"] = m["value"] / m["MWh"] * dc.DOLLAR
    m["lcoe_2024"] = m["lcoe"] * dc.DOLLAR
    m["nvoe"] = m["value_per_mwh"] - m["lcoe_2024"]
    m["net_value"] = (m["value"] - m["lcoe"] * m["MWh"]) * dc.DOLLAR
    m["net_value_per_kw_yr"] = m["net_value"] / (m["MW"] * 1000.0)
    m["value_per_kw_yr"] = m["value"] * dc.DOLLAR / (m["MW"] * 1000.0)
    m["lcoe_per_kw_yr"] = m["lcoe_2024"] * m["MWh"] / (m["MW"] * 1000.0)

    spec = [
        ("value_per_mwh", "2024 $/MWh", True),
        ("lcoe_built", "2024 $/MWh (lcoe_built dollar year not stated; x 1.6563 applied)", True),
        ("lcoe_built_model_units", "$/MWh (dollar year not stated)", False),
        ("nvoe", "2024 $/MWh (lcoe_built dollar year not stated)", True),
        ("value_per_kw_yr", "2024 $/kW-yr", True),
        ("lcoe_per_kw_yr", "2024 $/kW-yr (lcoe_built dollar year not stated)", True),
        ("net_value", "2024 $ (lcoe_built dollar year not stated)", True),
        ("net_value_per_kw_yr", "2024 $/kW-yr (lcoe_built dollar year not stated)", True),
    ]
    col = {"lcoe_built": "lcoe_2024", "lcoe_built_model_units": "lcoe"}
    rows = []
    for metric, unit, conv in spec:
        d = m[dc.CASE_COLS + ["i", "r", "t"]].copy()
        d["metric"] = metric
        d["value"] = m[col.get(metric, metric)].to_numpy()
        d["unit"] = unit
        d["converted_2004_to_2024"] = conv
        rows.append(d)
    out = pd.concat(rows, ignore_index=True)
    path = dc.write_long(out, "smr_cost_gap")

    chk = (m["nvoe"] * m["MWh"] - m["net_value"]).abs().max()
    checks = [
        ("Case-years with both valnew and lcoe_built", "PASS" if len(m) else "FAIL", str(len(m))),
        ("valnew rows with no lcoe_built", "PASS" if only_v.empty else "INFO",
         ", ".join(f"{r.case} {r.t}" for r in only_v.itertuples()) or "none"),
        ("lcoe_built rows with no valnew MW row", "PASS" if only_l.empty else "INFO",
         ", ".join(f"{r.case} {r.t}" for r in only_l.itertuples()) or "none"),
        ("nvoe x MWh = net_value", "PASS" if chk <= 1e-6 * m["net_value"].abs().max() else "FAIL",
         f"max abs gap {chk:.3g}"),
        ("lcoe_built dollar year", "OPEN",
         f"02d lookup: {dc.unit_of('lcoe_built')}; converted x {dc.DOLLAR} so that D19's "
         "subtraction is in one dollar year"),
        ("Years", "INFO", ", ".join(str(t) for t in sorted(m["t"].unique()))),
    ]
    fail = any(c[1] == "FAIL" for c in checks)
    samp = out[out.case.isin(dc.SAMPLE_CASES)].pivot_table(index=["case", "t"], columns="metric",
                                                           values="value").reset_index()
    summ = out[out.metric.isin(["nvoe", "net_value_per_kw_yr"])].groupby(
        ["batch", "arm", "metric"])["value"].agg(["min", "max"]).reset_index()
    text = [
        f"## 03h_smr_cost_gap — {'FAIL' if fail else 'PASS, with open items'}\n",
        "D19: nvoe = valnew value per MWh (val_load + val_resmarg + val_opres + val_rps) minus "
        "`lcoe_built` (Nuclear-SMR, p25). Also net value in $ and per kW-yr (for 04f). "
        "Converted x 1.6563 (D8): value_per_mwh, value_per_kw_yr, net values, and lcoe_built "
        "(dollar year not stated; see open item). lcoe_built_model_units is not converted.\n",
        f"Table: `{dc.rel(path)}` ({len(out):,} rows).\n",
        "### Checks\n",
        dc.md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Range by batch and arm\n",
        dc.md_table(summ, floatfmt="{:,.4g}") + "\n",
        "### Verifier sample cases (UON ref 0 GW has no SMR build, so no rows)\n",
        dc.md_table(samp, floatfmt="{:,.6g}") + "\n",
    ]
    dc.write_section(SECTION, "\n".join(text))
    print("03h done")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
