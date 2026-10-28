"""03c_trade: expenditure flows by type.

docs/plan.md, stage 03_derive, 03c; D8, D11, D36, D37f; decisions.md "On hold".

- expenditure_flow: `expenditure_flow` (type, r, rr, t; 2004 $;
  report_params.csv L77, "expenditures from flows of * moving from r to rr"),
  kept by type and line pair; value x 1.6563 (D8).

Net imports (`net_import_ann_rep`) and new lines (`invtran_out`) are not
copied (D37f): later stages read the stage 01 files. The group-to-group trade
table and the cost views A, B, C are on hold (Caleb decides), so
`expenditure_flow_rps`, `expenditure_flow_int` and `tran_flow_rep_ann` are not
read here.

In:  outputs/01_ingest/outputs/expenditure_flow.h5, 00_config/*.csv,
     outputs/02_clean/units.csv
Out: outputs/03_derive/expenditure_flow.h5 (long),
     section "03c" of outputs/checks/03_derive.md

Run:  conda run -n reeds python 03_derive/03c_trade.py
"""

import sys

import pandas as pd

import derive_common as dc

SECTION = "03c"


def main():
    cases = dc.cases()
    ef = dc.read_key("expenditure_flow").rename(columns={"Value": "value"})
    raw_sum = float(ef["value"].astype("float64").sum())
    ef["value"] = ef["value"].astype("float64") * dc.DOLLAR
    ef.insert(len(dc.CASE_COLS), "metric", "expenditure_flow")
    unit_ef = dc.unit_of("expenditure_flow")
    ef["unit"] = "2024 $"
    ef["converted_2004_to_2024"] = True
    path = dc.write_long(ef, "expenditure_flow", big=True)

    self_flow = int((ef["r"] == ef["rr"]).sum())
    checks = [
        ("Unit of input (02d lookup)", "PASS" if unit_ef == "2004 $" else "FAIL", unit_ef),
        ("Cases", "PASS" if ef["case"].nunique() == len(cases) else "INFO",
         f"{ef['case'].nunique()} of {len(cases)}"),
        ("Sum of output = sum of input x factor",
         "PASS" if abs(ef["value"].sum() - raw_sum * dc.DOLLAR) <= 1e-9 * abs(raw_sum * dc.DOLLAR)
         else "FAIL", f"{ef['value'].sum():,.6g}"),
        ("Rows with r = rr", "PASS" if self_flow == 0 else "INFO", str(self_flow)),
        ("Types", "INFO", ", ".join(sorted(ef["type"].unique()))),
    ]
    fail = any(c[1] == "FAIL" for c in checks)

    s_ef = ef[ef.case.isin(dc.SAMPLE_CASES) & ((ef.r == dc.FOCUS) | (ef.rr == dc.FOCUS))
              & ef.t.isin(dc.POST_PLANT_YEARS)]
    s_ef = (s_ef.assign(direction=lambda d: (d.r == dc.FOCUS).map({True: "p25 is r",
                                                                    False: "p25 is rr"}))
            .groupby(["case", "t", "type", "direction"])["value"].sum().reset_index())
    text = [
        f"## 03c_trade — {'FAIL' if fail else 'PASS'}\n",
        "Built: expenditure flows by type (`expenditure_flow`), x 1.6563 (D8). Not copied "
        "(D37f): net imports (`net_import_ann_rep`) and new lines (`invtran_out`); later stages "
        "read the stage 01 files. Not built (On hold): group-to-group trade table, cost views "
        "A, B, C.\n",
        f"Table: `{dc.rel(path)}` ({len(ef):,} rows).\n",
        "### Checks\n",
        dc.md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Verifier sample cases: flows on lines that touch p25, by direction (2024 $)\n",
        dc.md_table(s_ef, floatfmt="{:,.6g}") + "\n",
    ]
    dc.write_section(SECTION, "\n".join(text))
    print(f"03c done: {'FAIL' if fail else 'PASS'}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
