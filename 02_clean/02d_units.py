"""02d_units: a units lookup table for the stage 01 keys.

docs/plan.md, stage 02_clean, 02d; D33, D35c, D36. Writes ONLY a small lookup
table: key, type, unit. No renames, no copy of the stage 01 data, no unit
check. Later stages read the stage 01 per-key files directly, with ReEDS
column names, and join this table for the unit.

- unit: as docs/data_dictionary.md states it ("Outputs read from each run",
  its SMR paragraph, and the numhours line), or "not stated" where the
  dictionary has none.
- type: filled only for keys whose unit differs by a type column:
  reqt_price and reqt_quant (`type`), valnew (`type`), reduced_cost
  (`variable`). For these keys every value found in the stage 01 table gets
  one row; a value the dictionary does not name gets "not stated". Blank for
  every other key.
- type_column: the stage 01 column that `type` refers to (blank otherwise).

Generated from this script (not hand-maintained), so it is written to
outputs/02_clean/ and not to 00_config/.

In:  outputs/01_ingest/outputs/<key>.h5, outputs/01_ingest/inputs/numhours.h5
     (only the type columns of four keys and the list of files are read)
Out (generated, not committed): outputs/02_clean/units.csv,
     section "02d" of outputs/checks/02_clean.md

Run:  conda run -n reeds python 02_clean/02d_units.py
"""

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
IN_OUT = REPO / "outputs" / "01_ingest" / "outputs"
IN_INP = REPO / "outputs" / "01_ingest" / "inputs"
OUT_DIR = REPO / "outputs" / "02_clean"
CHECK_REPORT = REPO / "outputs" / "checks" / "02_clean.md"
SECTION = "02d"
NOT_STATED = "not stated"

# Units as docs/data_dictionary.md states them (one unit per key).
KEY_UNITS = {
    "systemcost_ba_bulk_ew": "2004 $",
    "systemcost_ba": "2004 $",          # data_dictionary.md (D44 update)
    "net_import_ann_rep": "MWh",
    "net_import_ann_stress": "MWh",
    "expenditure_flow": "2004 $",
    "expenditure_flow_rps": "2004 $",
    "expenditure_flow_int": "2004 $",
    "tran_out": "MW",
    "invtran_out": "MW",
    "tran_util_h_rep": "fraction of capacity, per direction",
    "tran_flow_rep_ann": "MWh, net, signed",
    "cap_ivrt": "MW",
    "ret_ivrt": "MW",
    "gen_ivrt": "MWh",
    "gen_h": "MW",
    "cost_vom": "2004 $/MWh",
    "heat_rate": "MMBtu/MWh",
    "fuel_price": "$/MMBtu (dollar year not stated)",
    "repgasprice_r": "2004 $/MMBtu",
    "lcoe_built": "$/MWh (dollar year not stated)",
    "numhours": "hours",
}
# Keys whose unit differs by a type column: (column, {value: unit}).
TYPE_UNITS = {
    # data_dictionary.md (D37 update; report.gms L330-331, L366 at 0c0ea27)
    "reqt_price": ("type", {"load": "2004 $/MWh", "oper_res": "2004 $/MWh",
                            "res_marg": "2004 $/MW per stress timeslice"}),
    "reqt_quant": ("type", {"load": "MWh per block", "oper_res": "MWh",
                            "res_marg": "MW"}),
    # data_dictionary.md: valnew "2004 $, MW, MWh"; the value types are named in
    # docs/plan.md "What the files are" (val_load, val_resmarg, val_opres,
    # val_rps; MW and MWh of the new build). `_sys` and other types: no unit.
    "valnew": ("type", {"MW": "MW", "MWh": "MWh", "val_load": "2004 $",
                        "val_resmarg": "2004 $", "val_opres": "2004 $",
                        "val_rps": "2004 $"}),
    # data_dictionary.md gives one unit for reduced_cost ("2004 $/kW
    # undiscounted") and does not split it by `variable`; it applies to all.
    "reduced_cost": ("variable", None),
}
REDUCED_COST_UNIT = "2004 $/kW, undiscounted"


def md_table(df):
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |",
           "| " + " | ".join("---" for _ in cols) + " |"]
    for row in df.itertuples(index=False):
        out.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(out)


def write_section(path, section, text, title="# Check report: 02_clean\n\n"):
    """Replace only this script's section of the stage check report."""
    start, end = f"<!-- {section} start -->", f"<!-- {section} end -->"
    block = f"{start}\n{text.rstrip()}\n{end}\n"
    old = path.read_text(encoding="utf-8") if path.exists() else title
    if start in old and end in old:
        pre, rest = old.split(start, 1)
        new = pre + block + rest.split(end, 1)[1].lstrip("\n")
    else:
        new = old.rstrip("\n") + "\n\n" + block
    path.write_text(new, encoding="utf-8")


OUT_DIR.mkdir(parents=True, exist_ok=True)
files = {p.stem: p for p in sorted(IN_OUT.glob("*.h5"))}
files["numhours"] = IN_INP / "numhours.h5"

rows = []
for key in sorted(files):
    if key in TYPE_UNITS:
        col, spec = TYPE_UNITS[key]
        with pd.HDFStore(files[key], "r") as st:
            found = sorted(pd.unique(st.select_column("data", col)))
        for v in found:
            unit = REDUCED_COST_UNIT if spec is None else spec.get(v, NOT_STATED)
            rows.append((key, col, v, unit))
        if spec:
            for v in sorted(set(spec) - set(found)):   # named in docs, absent in data
                rows.append((key, col, v, spec[v] + " (type absent in stage 01 data)"))
    else:
        rows.append((key, "", "", KEY_UNITS.get(key, NOT_STATED)))
units = pd.DataFrame(rows, columns=["key", "type_column", "type", "unit"])
units.to_csv(OUT_DIR / "units.csv", index=False)

checks = [
    ("One row or more per stage 01 table",
     "PASS" if set(units["key"]) == set(files) else "FAIL",
     f"{units['key'].nunique()} keys of {len(files)} files; {len(units)} rows"),
    ("No key without a unit entry in this script",
     "PASS" if not [k for k in files if k not in KEY_UNITS and k not in TYPE_UNITS] else "FAIL",
     ", ".join(k for k in files if k not in KEY_UNITS and k not in TYPE_UNITS) or "none"),
]
ns = units[units["unit"] == NOT_STATED]
ok = all(c[1] == "PASS" for c in checks)
show = units.replace({"": "-"})
lines = [f"## 02d_units — {'PASS' if ok else 'FAIL'}\n",
         "D36: a units lookup only (key, type, unit), from `docs/data_dictionary.md`; "
         "\"not stated\" where it has none. No renames, no copy of the data, no unit check "
         "(D35c). Later stages read the stage 01 files with ReEDS column names. "
         "`type_column` names the stage 01 column that `type` refers to. Generated by "
         "this script, so written to `outputs/02_clean/units.csv` (not `00_config/`).\n",
         "### Checks\n",
         md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
         "### Units\n", md_table(show) + "\n",
         f"### Rows with unit \"{NOT_STATED}\" (for Caleb): {len(ns)}\n",
         (md_table(ns.replace({'': '-'})) if len(ns) else "None.") + "\n"]
write_section(CHECK_REPORT, SECTION, "\n".join(lines))
print(f"02d units lookup: {'PASS' if ok else 'FAIL'} ({len(units)} rows, "
      f"{len(ns)} not stated)")
sys.exit(0 if ok else 1)
