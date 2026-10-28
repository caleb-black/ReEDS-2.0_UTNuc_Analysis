"""03d_capacity_generation: capacity and generation by technology, with share.

docs/plan.md, stage 03_derive, 03d; D11, D36; data_dictionary.md, Metrics.

- capacity:   `cap_ivrt` (i, v, r, t; MW; report_params.csv L19), summed over
  vintage v -> one value per technology i, region, year, case.
- generation: `gen_ivrt` (i, v, r, t; MWh, annual; report_params.csv L84),
  summed over v the same way.
- capacity_share, generation_share = value / sum over all i of the region
  and year (D11: absolute plus share of regional total), in %.

Technologies are the ReEDS `i` names as stored (no grouping: no grouping
rule is in docs/decisions.md). The regional total is the sum of every `i`
as stored. `gen_ivrt` has some negative values; the report gives their
count and size, and they are kept as they are.

In:  outputs/01_ingest/outputs/cap_ivrt.h5, gen_ivrt.h5, 00_config/*.csv,
     outputs/02_clean/units.csv
Out: outputs/03_derive/capacity_generation.h5 (long),
     section "03d" of outputs/checks/03_derive.md

Run:  conda run -n reeds python 03_derive/03d_capacity_generation.py
"""

import sys

import numpy as np
import pandas as pd

import derive_common as dc

SECTION = "03d"


def by_tech(key, metric):
    d = dc.read_key(key)
    d["Value"] = d["Value"].astype("float64")
    neg = d[d["Value"] < 0]
    g = d.groupby(dc.CASE_COLS + ["i", "r", "t"])["Value"].sum().rename("value").reset_index()
    tot = g.groupby(dc.CASE_COLS + ["r", "t"])["value"].transform("sum")
    with np.errstate(divide="ignore", invalid="ignore"):
        share = 100.0 * g["value"] / tot
    a = g.assign(metric=metric, unit=dc.unit_of(key))
    b = g.assign(metric=f"{metric}_share", value=share, unit="% of regional total")
    out = pd.concat([a, b], ignore_index=True)
    out["converted_2004_to_2024"] = False
    info = {"key": key, "rows in": len(d), "rows out": len(out),
            "negative rows in": len(neg),
            "most negative": float(neg["Value"].min()) if len(neg) else 0.0,
            "region-years with total <= 0": int((g.groupby(dc.CASE_COLS + ["r", "t"])["value"]
                                                .sum() <= 0).sum()),
            "sum in": float(d["Value"].sum()), "sum out": float(a["value"].sum())}
    return out, info


def main():
    cases = dc.cases()
    cap, ic = by_tech("cap_ivrt", "capacity")
    gen, ig = by_tech("gen_ivrt", "generation")
    allt = pd.concat([cap, gen], ignore_index=True)
    allt = allt[dc.CASE_COLS + ["metric", "i", "r", "t", "value", "unit", "converted_2004_to_2024"]]
    path = dc.write_long(allt, "capacity_generation", big=True)

    info = pd.DataFrame([ic, ig])
    share_sum = (allt[allt.metric.str.endswith("_share")]
                 .groupby(["metric", "case", "r", "t"])["value"].sum())
    checks = [
        ("Units of inputs (02d lookup)",
         "PASS" if (cap.unit.iloc[0] == "MW" and gen.unit.iloc[0] == "MWh") else "FAIL",
         f"cap_ivrt {cap.unit.iloc[0]}; gen_ivrt {gen.unit.iloc[0]}"),
        ("Cases", "PASS" if allt.case.nunique() == len(cases) else "FAIL",
         f"{allt.case.nunique()} of {len(cases)}"),
        ("Sum over v keeps the total (sum out = sum in)",
         "PASS" if all(abs(r["sum out"] - r["sum in"]) <= 1e-9 * abs(r["sum in"])
                       for r in [ic, ig]) else "FAIL",
         "; ".join(f"{r['key']}: {r['sum out']:,.6g} vs {r['sum in']:,.6g}" for r in [ic, ig])),
        ("Shares add to 100 % per region-year",
         "PASS" if np.allclose(share_sum.dropna(), 100.0, atol=1e-6) else "FAIL",
         f"min {share_sum.min():.6f}, max {share_sum.max():.6f}"),
        ("Negative generation rows (kept)", "INFO",
         f"{ig['negative rows in']} rows; most negative {ig['most negative']:.3g} MWh"),
        ("Region-years with total <= 0", "PASS" if ic["region-years with total <= 0"] == 0
         and ig["region-years with total <= 0"] == 0 else "INFO",
         f"capacity {ic['region-years with total <= 0']}, generation {ig['region-years with total <= 0']}"),
    ]
    fail = any(c[1] == "FAIL" for c in checks)

    s = allt[allt.case.isin(dc.SAMPLE_CASES) & (allt.r == dc.FOCUS) & (allt.t == 2044)
             & allt.i.str.contains("uclear", case=False)]
    s = s.pivot_table(index=["case", "i"], columns="metric", values="value").reset_index()
    tot = (allt[allt.case.isin(dc.SAMPLE_CASES) & (allt.r == dc.FOCUS)
                & allt.t.isin(dc.POST_PLANT_YEARS) & allt.metric.isin(["capacity", "generation"])]
           .groupby(["case", "t", "metric"])["value"].sum().unstack("metric").reset_index())

    text = [
        f"## 03d_capacity_generation — {'FAIL' if fail else 'PASS'}\n",
        "Capacity (`cap_ivrt`, MW) and generation (`gen_ivrt`, MWh) summed over vintage `v`, per "
        "ReEDS technology `i` as stored; share = value / sum over all `i` of the region and year "
        "(%, D11). No dollars, nothing converted.\n",
        f"Table: `{dc.rel(path)}` ({len(allt):,} rows).\n",
        "### Checks\n",
        dc.md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Verifier sample cases: nuclear in p25, 2044\n",
        dc.md_table(s, floatfmt="{:,.6g}") + "\n",
        "p25 totals over all technologies:\n",
        dc.md_table(tot, floatfmt="{:,.6g}") + "\n",
    ]
    dc.write_section(SECTION, "\n".join(text))
    print(f"03d done: {'FAIL' if fail else 'PASS'}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
