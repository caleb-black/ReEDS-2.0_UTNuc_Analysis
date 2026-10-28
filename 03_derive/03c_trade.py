"""03c_trade: net imports, expenditure flows by type, new lines.

docs/plan.md, stage 03_derive, 03c; D8, D11, D36; decisions.md "On hold".
Only these three tables are built. The group-to-group trade table and the
cost views A, B, C are on hold (Caleb decides), so `expenditure_flow_rps`,
`expenditure_flow_int` and `tran_flow_rep_ann` are not read here.

- net_imports: `net_import_ann_rep` (r, t; MWh; report_params.csv L209,
  "imports - exports with losses on imports", representative periods).
  One value per region, year, case; no change of value.
- expenditure_flow: `expenditure_flow` (type, r, rr, t; 2004 $;
  report_params.csv L77, "expenditures from flows of * moving from r to rr"),
  kept by type and line pair; value x 1.6563 (D8).
- new_lines: `invtran_out` (r, rr, trtype, t; MW; report_params.csv L114,
  "new transmission capacity"). No change of value.

net_imports and new_lines carry the stage 01 values unchanged (the plan
lists them as 03c outputs); they are small. A row absent in stage 01 stays
absent (no zero is invented).

In:  outputs/01_ingest/outputs/net_import_ann_rep.h5, expenditure_flow.h5,
     invtran_out.h5, 00_config/*.csv, outputs/02_clean/units.csv
Out: outputs/03_derive/net_imports.csv, expenditure_flow.csv(.h5 if large),
     new_lines.csv, section "03c" of outputs/checks/03_derive.md

Run:  conda run -n reeds python 03_derive/03c_trade.py
"""

import sys

import pandas as pd

import derive_common as dc

SECTION = "03c"
BIG = 300_000


def main():
    cases = dc.cases()
    out = {}

    ni = dc.read_key("net_import_ann_rep").rename(columns={"Value": "value"})
    ni["value"] = ni["value"].astype("float64")
    ni.insert(len(dc.CASE_COLS), "metric", "net_imports")
    ni["unit"] = dc.unit_of("net_import_ann_rep")
    ni["converted_2004_to_2024"] = False
    out["net_imports"] = ni

    ef = dc.read_key("expenditure_flow").rename(columns={"Value": "value"})
    ef["value"] = ef["value"].astype("float64") * dc.DOLLAR
    ef.insert(len(dc.CASE_COLS), "metric", "expenditure_flow")
    unit_ef = dc.unit_of("expenditure_flow")
    ef["unit"] = "2024 $"
    ef["converted_2004_to_2024"] = True
    out["expenditure_flow"] = ef

    nl = dc.read_key("invtran_out").rename(columns={"Value": "value"})
    nl["value"] = nl["value"].astype("float64")
    nl.insert(len(dc.CASE_COLS), "metric", "new_lines")
    nl["unit"] = dc.unit_of("invtran_out")
    nl["converted_2004_to_2024"] = False
    out["new_lines"] = nl

    paths = {k: dc.write_long(v, k, big=len(v) > BIG) for k, v in out.items()}

    # ---------------- checks ----------------
    wsum = ni.groupby(["batch", "case", "t"])["value"].sum()
    rc = ni.groupby("case")["r"].nunique()
    self_flow = int((ef["r"] == ef["rr"]).sum())
    checks = [
        ("Units of inputs (02d lookup)",
         "PASS" if (ni["unit"].iloc[0] == "MWh" and unit_ef == "2004 $"
                    and nl["unit"].iloc[0] == "MW") else "FAIL",
         f"net_import_ann_rep {ni['unit'].iloc[0]}; expenditure_flow {unit_ef}; "
         f"invtran_out {nl['unit'].iloc[0]}"),
        ("Cases in each table",
         "PASS" if all(v["case"].nunique() == len(cases) for v in out.values()) else "INFO",
         "; ".join(f"{k} {v['case'].nunique()}" for k, v in out.items())),
        ("Regions with net imports per case", "PASS" if (rc == 34).all() else "INFO",
         f"min {rc.min()}, max {rc.max()}; no rows in any case for: "
         + (", ".join(sorted(set(dc.region_groups().query("group == 'wecc'")["region"])
                             - set(ni["r"]))) or "none")),
        ("WECC sum of net imports per case-year <= 0 (losses on imports, L209)",
         "PASS" if (wsum <= 0).all() else "INFO",
         f"min {wsum.min():,.0f}, max {wsum.max():,.0f} MWh"),
        ("expenditure_flow rows with r = rr", "PASS" if self_flow == 0 else "INFO", str(self_flow)),
        ("expenditure_flow types", "INFO", ", ".join(sorted(ef["type"].unique()))),
        ("new_lines line types", "INFO", ", ".join(sorted(nl["trtype"].unique()))),
    ]
    fail = any(c[1] == "FAIL" for c in checks)

    s_ni = ni[ni.case.isin(dc.SAMPLE_CASES) & (ni.r == dc.FOCUS)
              & ni.t.isin(dc.POST_PLANT_YEARS)][["case", "t", "value"]]
    s_ef = ef[ef.case.isin(dc.SAMPLE_CASES) & ((ef.r == dc.FOCUS) | (ef.rr == dc.FOCUS))
              & ef.t.isin(dc.POST_PLANT_YEARS)]
    s_ef = (s_ef.assign(direction=lambda d: (d.r == dc.FOCUS).map({True: "p25 is r", False: "p25 is rr"}))
            .groupby(["case", "t", "type", "direction"])["value"].sum().reset_index())
    s_nl = nl[nl.case.isin(dc.SAMPLE_CASES) & ((nl.r == dc.FOCUS) | (nl.rr == dc.FOCUS))
              & nl.t.isin(dc.POST_PLANT_YEARS)][["case", "r", "rr", "trtype", "t", "value"]]

    text = [
        f"## 03c_trade — {'FAIL' if fail else 'PASS'}\n",
        "Built: net imports (`net_import_ann_rep`), expenditure flows by type "
        "(`expenditure_flow`), new lines (`invtran_out`). Not built (On hold, decisions.md): "
        "group-to-group trade table, cost views A, B, C.\n",
        "Converted 2004 $ -> 2024 $ (x 1.6563, D8): expenditure_flow `value`. Not converted: "
        "net_imports (MWh), new_lines (MW).\n",
        "Tables: " + "; ".join(f"`{dc.rel(p)}` ({len(out[k]):,} rows)" for k, p in paths.items())
        + ".\n",
        "### Checks\n",
        dc.md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Verifier sample cases: p25\n",
        "Net imports (MWh):\n",
        dc.md_table(s_ni, floatfmt="{:,.6g}") + "\n",
        "Expenditure flows on lines that touch p25, summed by direction (2024 $):\n",
        dc.md_table(s_ef, floatfmt="{:,.6g}") + "\n",
        "New lines that touch p25 (MW):\n",
        (dc.md_table(s_nl, floatfmt="{:,.6g}") if len(s_nl) else "None in 2044-2050.") + "\n",
    ]
    dc.write_section(SECTION, "\n".join(text))
    print(f"03c done: {'FAIL' if fail else 'PASS'}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
