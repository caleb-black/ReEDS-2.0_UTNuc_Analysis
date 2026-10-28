"""03i_smr_reduced_cost: reduced cost of SMR investment in p25, 2044, 0 GW cases.

docs/plan.md, "SMR value and the cost of prescribing it", 03i; D8, D36.

In each 0 GW case: the `reduced_cost` row with i = Nuclear-SMR, r = p25,
t = 2044, variable = INV (`reduced_cost`, i, v, r, t, bin, variable;
2004 $/kW undiscounted; report_params.csv L144; report.gms L1867-L1870:
INV.m / (1000 x cost_scale x pvf_capital)). One row per 0 GW case and
vintage v found; value x 1.6563 (D8).

If a 0 GW case has no such row, the table gets one row with value empty
and in_file = False. Why the row is absent is not covered in the
documentation; it is not set to 0 here. The report lists, for context, every
`reduced_cost` row that does exist for Nuclear-SMR in p25 in that case
(other variables or years); none of them is used in place of the INV row.

In:  outputs/01_ingest/outputs/reduced_cost.h5, 00_config/*.csv,
     outputs/02_clean/units.csv
Out: outputs/03_derive/smr_reduced_cost.csv (long), section "03i" of
     outputs/checks/03_derive.md

Run:  conda run -n reeds python 03_derive/03i_smr_reduced_cost.py
"""

import sys

import pandas as pd

import derive_common as dc

SECTION = "03i"
SMR = "Nuclear-SMR"
YEAR = 2044
VAR = "INV"


def main():
    cases = dc.cases()
    zero = cases[cases.level == 0.0]
    rc = dc.read_key("reduced_cost", where=f'i == "{SMR}" & r == "{dc.FOCUS}"')
    rc["Value"] = rc["Value"].astype("float64")
    rows, ctx = [], []
    for _, c in zero.iterrows():
        d = rc[(rc.case == c["case"])]
        hit = d[(d.t == YEAR) & (d.variable == VAR)]
        if hit.empty:
            rows.append({**{k: c[k] for k in dc.CASE_COLS}, "i": SMR, "v": "", "r": dc.FOCUS,
                         "t": YEAR, "bin": "", "variable": VAR, "value": float("nan"),
                         "in_file": False})
        for h in hit.itertuples():
            rows.append({**{k: c[k] for k in dc.CASE_COLS}, "i": SMR, "v": h.v, "r": dc.FOCUS,
                         "t": YEAR, "bin": h.bin, "variable": VAR,
                         "value": h.Value * dc.DOLLAR, "in_file": True})
        other = (d.groupby(["variable", "t"])["Value"].agg(["size", "min", "max"]).reset_index())
        for o in other.itertuples():
            ctx.append((c["batch"], c["arm"], c["case"], o.variable, o.t, o.size,
                        o.min, o.max))
    out = pd.DataFrame(rows)
    out.insert(len(dc.CASE_COLS), "metric", "reduced_cost_INV")
    out["unit"] = "2024 $/kW, undiscounted"
    out["converted_2004_to_2024"] = True
    path = dc.write_long(out, "smr_reduced_cost")

    n_found = int(out["in_file"].sum())
    any_inv = rc[(rc.variable == VAR)][["case", "t"]].drop_duplicates()
    checks = [
        ("0 GW cases", "INFO", f"{len(zero)}: " + ", ".join(zero["case"])),
        ("0 GW cases with an INV row for Nuclear-SMR, p25, 2044",
         "PASS" if n_found == len(zero) else "OPEN", f"{n_found} of {len(zero)}"),
        ("Any case (any level) with an INV row for Nuclear-SMR in p25", "INFO",
         ", ".join(f"{r.case} {r.t}" for r in any_inv.itertuples()) or "none"),
        ("Unit (02d lookup)", "INFO", dc.unit_of("reduced_cost", VAR)),
    ]
    ctx_df = pd.DataFrame(ctx, columns=["batch", "arm", "case", "variable", "t", "rows",
                                        "min (2004 $/kW)", "max (2004 $/kW)"])
    samp = out[out.case.isin(dc.SAMPLE_CASES)]
    text = [
        f"## 03i_smr_reduced_cost — {'PASS' if n_found == len(zero) else 'OPEN: value absent'}\n",
        "Rule (plan 03i): `reduced_cost` of `INV` for Nuclear-SMR in p25 in 2044, in each 0 GW "
        "case (report.gms L1869; report_params.csv L144). Value x 1.6563 (D8) where present.\n",
        f"Table: `{dc.rel(path)}` ({len(out):,} rows).\n",
        "### Checks\n",
        dc.md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Rows that do exist for Nuclear-SMR in p25 in the 0 GW cases (context only, not used)\n",
        (dc.md_table(ctx_df, floatfmt="{:,.6g}") if len(ctx_df) else "None.") + "\n",
        "### Verifier sample cases\n",
        dc.md_table(samp[["case", "variable", "t", "v", "value", "in_file"]],
                    floatfmt="{:,.6g}") + "\n",
        "UON ref 3 GW and UOS ref 2.5 GW are not 0 GW cases; 03i has no rows for them by its rule.\n",
    ]
    dc.write_section(SECTION, "\n".join(text))
    print("03i done")
    return 0


if __name__ == "__main__":
    sys.exit(main())
