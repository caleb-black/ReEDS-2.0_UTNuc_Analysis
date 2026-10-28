"""03f_line_use: line use in each peak block (D9).

docs/plan.md, stage 03_derive, 03f; D9, D32, D36; data_dictionary.md, Metrics
("Line at limit in peak block").

Peak blocks: for every region r and year t of a case, the three blocks with
the highest `load` price (D9), ranked as in 03a (ties broken by block name;
column n_blocks_at_price). Plan rule 2 forbids reading 03a's output, so the
ranking is recomputed here from `reqt_price` with the same shared function
(derive_common.rank_peaks).

Lines: every `tran_out` row (r, rr, trtype, t) of the case that touches the
peak region in that year. For each line both directions are listed, as
`tran_util_h_rep` rows (r = from, rr = to): utilization in the peak block h.

Facts used (0c0ea27): `tran_util_h_rep` = FLOW(r, rr, h) / CAPTRAN_ENERGY(r, rr)
(`reeds/core/terminus/report_calcs.py` L134), so it is per direction and its
denominator is the capacity in that direction. `tran_out` is the average of
the forward and reverse capacities (`report_calcs.py` L104; report_params.csv
L223); it is attached as line_capacity_avg_mw for reference only.

A direction with no `tran_util_h_rep` row in that block gets value empty
(NaN) and in_file = False. Why a row is absent is not covered in the
documentation; it is not set to 0 here (open item for Caleb).

No "at limit" yes/no flag is made: the threshold is not in
docs/decisions.md (open item for Caleb). The value is the fraction as stored.

The output covers all 34 regions' peaks, a superset of the data dictionary's
"per line touching p25"; the p25 rows are the rows with peak_r = p25.

In:  outputs/01_ingest/outputs/reqt_price.h5, tran_out.h5, tran_util_h_rep.h5,
     outputs/01_ingest/inputs/numhours.h5, 00_config/*.csv, outputs/02_clean/units.csv
Out: outputs/03_derive/line_use_peak.h5 (long),
     section "03f" of outputs/checks/03_derive.md

Run:  conda run -n reeds python 03_derive/03f_line_use.py
"""

import sys
import time

import numpy as np
import pandas as pd

import derive_common as dc

SECTION = "03f"


def per_case(row):
    c = row["case"]
    p = dc.read_key("reqt_price", where=f'case == "{c}" & type == "load"',
                    columns=["r", "h", "t", "Value"]).rename(columns={"Value": "price"})
    p["case"] = c
    top, ties = dc.rank_peaks(p, n=3)
    top = top.drop(columns="case").rename(columns={"r": "peak_r"})
    nh = dc.read_numhours(where=f'case == "{c}"')[["h", "numhours"]]
    top = top.merge(nh, on="h", how="left")

    tr = dc.read_key("tran_out", where=f'case == "{c}"', columns=["r", "rr", "trtype", "t", "Value"])
    tr = tr.rename(columns={"Value": "line_capacity_avg_mw"})
    # both directions of each line
    fwd = tr.copy()
    rev = tr.rename(columns={"r": "rr", "rr": "r"})
    dirs = pd.concat([fwd, rev], ignore_index=True)

    # lines touching the peak region: from = peak_r or to = peak_r
    a = top.merge(dirs, left_on=["peak_r", "t"], right_on=["r", "t"], how="inner")
    b = top.merge(dirs, left_on=["peak_r", "t"], right_on=["rr", "t"], how="inner")
    lines = pd.concat([a, b], ignore_index=True)

    tu = dc.read_key("tran_util_h_rep", where=f'case == "{c}"',
                     columns=["r", "rr", "h", "t", "trtype", "Value"])
    lines = lines.merge(tu, on=["r", "rr", "h", "t", "trtype"], how="left", indicator=True)
    lines["in_file"] = lines["_merge"] == "both"
    lines = lines.drop(columns=["_merge", "price"]).rename(columns={"Value": "value"})
    lines["value"] = lines["value"].astype("float64")
    lines["metric"] = "line_utilization"
    lines["unit"] = dc.unit_of("tran_util_h_rep")
    lines["converted_2004_to_2024"] = False
    for k in dc.CASE_COLS[::-1]:
        lines.insert(0, k, row[k])
    info = {"case": c, "peaks": len(top), "ties": ties, "rows": len(lines),
            "not_in_file": int((~lines["in_file"]).sum()),
            "util_rows_case": len(tu),
            "util_gt1": int((tu["Value"] > 1 + 1e-6).sum()),
            "util_lt0": int((tu["Value"] < -1e-6).sum()),
            "peaks_without_line": int(len(top) - lines[["peak_r", "t", "peak_rank"]]
                                      .drop_duplicates().shape[0]),
            "numhours_missing": int(top["numhours"].isna().sum())}
    return lines, info


def main():
    t0 = time.time()
    cases = dc.cases()
    outs, infos = [], []
    for _, row in cases.iterrows():
        lines, info = per_case(row)
        outs.append(lines)
        infos.append(info)
        print(f"{row['case']}: {len(lines)} rows ({time.time() - t0:.0f} s)", flush=True)
    allt = pd.concat(outs, ignore_index=True)
    cols = dc.CASE_COLS + ["metric", "peak_r", "t", "peak_rank", "h", "numhours",
                           "n_blocks_at_price", "r", "rr", "trtype", "line_capacity_avg_mw",
                           "value", "in_file", "unit", "converted_2004_to_2024"]
    allt = allt[cols]
    allt["line_capacity_avg_mw"] = allt["line_capacity_avg_mw"].astype("float64")
    path = dc.write_long(allt, "line_use_peak", big=True)
    info = pd.DataFrame(infos)

    checks = [
        ("Cases", "PASS" if len(info) == len(cases) else "FAIL", f"{len(info)} of {len(cases)}"),
        ("Peaks per case = 34 regions x 13 years x 3",
         "PASS" if (info.peaks == 34 * 13 * 3).all() else "INFO",
         f"min {info.peaks.min()}, max {info.peaks.max()}"),
        ("Peak blocks without numhours", "PASS" if info.numhours_missing.sum() == 0 else "FAIL",
         str(int(info.numhours_missing.sum()))),
        ("Peaks with no line in tran_out that year", "INFO", str(int(info.peaks_without_line.sum()))),
        ("Line directions with no tran_util_h_rep row (value left empty)", "OPEN",
         f"{int(info.not_in_file.sum()):,} of {len(allt):,} rows"),
        ("tran_util_h_rep values > 1 or < 0 (all blocks, all cases)",
         "PASS" if info.util_gt1.sum() + info.util_lt0.sum() == 0 else "INFO",
         f"> 1: {int(info.util_gt1.sum())}; < 0: {int(info.util_lt0.sum())}"),
        ("\"At limit\" yes/no flag", "OPEN", "threshold not in decisions.md; not made"),
    ]
    fail = any(c[1] == "FAIL" for c in checks)
    s = allt[allt.case.isin(dc.SAMPLE_CASES) & (allt.peak_r == dc.FOCUS) & (allt.t == 2044)
             & (allt.peak_rank == 1)][["case", "h", "r", "rr", "trtype", "line_capacity_avg_mw",
                                       "value", "in_file"]].sort_values(["case", "r", "rr"])
    text = [
        f"## 03f_line_use — {'FAIL' if fail else 'PASS, with open items'}\n",
        "Peak blocks: top 3 `load` price blocks per region and year (D9; same ranking as 03a, "
        "recomputed). Lines: every `tran_out` line touching the peak region, both directions; "
        "value = `tran_util_h_rep` in that block (FLOW / directional capacity, `report_calcs.py` "
        "L134). line_capacity_avg_mw = `tran_out` (average of both directions, L104), for "
        "reference. No dollars.\n",
        f"Table: `{dc.rel(path)}` ({len(allt):,} rows). Run time {time.time() - t0:.0f} s.\n",
        "### Checks\n",
        dc.md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Verifier sample cases: lines at p25's top peak block, 2044\n",
        dc.md_table(s, floatfmt="{:,.6g}") + "\n",
    ]
    dc.write_section(SECTION, "\n".join(text))
    print(f"03f done: {'FAIL' if fail else 'PASS'}")
    return 1 if fail else 0


if __name__ == "__main__":
    sys.exit(main())
