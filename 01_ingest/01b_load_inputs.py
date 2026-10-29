"""01b_load_inputs: copy the inputs that later stages need, change nothing.

docs/plan.md, stage 01_ingest. For every case in 00_config/study_cases.csv:
1. <case>/inputs_case/rep/numhours.csv (docs/data_dictionary.md, "Outputs read
   from each run": h; hours; block weight). cost_vom, heat_rate and fuel_price
   are outputs.h5 keys and are read in 01a.
2. `crf` (t, Value), for 03b2 (D44). Read as reeds/io.py read_input does
   (L436-471 at 0c0ea27): from <case>/inputs_case/inputs.h5 if that file exists
   (key `crf`, layout of read_h5, L420-433); if inputs.h5 has no `crf` key, or
   there is no inputs.h5, from <case>/inputs_case/crf.csv. ReEDS writes it with
   write_to_inputs_h5 (calc_financial_inputs.py L516-519 at 0c0ea27), which
   names the last column `Value` (io.py L1786-1788), for the modeled years
   only (`t == modeled_year`, L516).
3. <case>/inputs_case/scalars.csv (name, value), for 03b2: results.py
   calc_systemcost reads `trans_crp` from it with reeds/io.py get_scalars
   (results.py L317, L336; io.py L764-790 at 0c0ea27: no header, first two
   columns). All rows are copied; the comment column is not.

What the script changes, and nothing else:
- numhours: the unnamed block column `*h` is renamed by position to `h` (data
  dictionary name). The value column `numhours` is kept as is.
- crf: from inputs.h5, columns as in the file (`t`, `Value`); from crf.csv, a
  first column `*t` is renamed `t` and the value column is named `Value` (the
  name read_input gets from inputs.h5); the original header is reported.
  Values as stored (float32 in inputs.h5).
- scalars: columns `name`, `value`; value kept as text, as in the file.
- Columns batch, arm, level, case are added from 00_config/study_cases.csv.

Checks (D32): the block count per arm (152 in ref, gaslow, pvadv, smrcons;
144 in loadhigh and loadlow), and that all levels of one batch-arm have the
same blocks and weights. Also shows each case against its batch's `ref` 0 GW
case (the load arms differ from it by design, D32). crf: present in every
case, one value per year, no missing value; values by year and whether they
are equal across the cases of each batch (shown, not judged). scalars: present
in every case; `trans_crp` per case.

Out (generated, not committed):
  outputs/01_ingest/inputs/numhours.h5      (pandas HDFStore, table format, key "data")
  outputs/01_ingest/inputs/crf.h5           (same format)
  outputs/01_ingest/inputs/scalars.h5       (same format)
  outputs/01_ingest/row_counts_inputs.csv   (batch, arm, level, case, file, present, rows)
Check report section "01b" in outputs/checks/01_ingest.md (D24).

A failed check makes the script exit with code 1 (plan rule 5).

Run:  conda run -n reeds python 01_ingest/01b_load_inputs.py
"""

import sys
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO / "00_config"
OUT_DIR = REPO / "outputs" / "01_ingest"
TABLE_DIR = OUT_DIR / "inputs"
CHECK_REPORT = REPO / "outputs" / "checks" / "01_ingest.md"   # D24
SECTION = "01b"

FILE = Path("rep") / "numhours.csv"        # under <case>/inputs_case/
COLUMNS = ["h", "numhours"]                 # data dictionary: h; hours
# Blocks per arm (D32; data dictionary "Study terms": Block).
N_BLOCKS = {"ref": 152, "gaslow": 152, "pvadv": 152, "smrcons": 152,
            "loadhigh": 144, "loadlow": 144}
ID_COLS = ["batch", "arm", "level", "case"]


def md_table(df):
    """Markdown table without the optional `tabulate` package."""
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |",
           "| " + " | ".join("---" for _ in cols) + " |"]
    for row in df.itertuples(index=False):
        out.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(out)


checks = []


def check(name, ok, detail=""):
    checks.append((name, "PASS" if ok else "FAIL", detail))
    return ok


def write_section(path, section, text):
    """Replace only this script's section of the stage check report."""
    start, end = f"<!-- {section} start -->", f"<!-- {section} end -->"
    block = f"{start}\n{text.rstrip()}\n{end}\n"
    header = "# Check report: 01_ingest\n\n"
    old = path.read_text(encoding="utf-8") if path.exists() else header
    if start in old and end in old:
        pre, rest = old.split(start, 1)
        post = rest.split(end, 1)[1].lstrip("\n")
        new = pre + block + post
    else:
        new = old.rstrip("\n") + "\n\n" + block
    path.write_text(new, encoding="utf-8")


cases = pd.read_csv(CONFIG_DIR / "study_cases.csv")
TABLE_DIR.mkdir(parents=True, exist_ok=True)
CHECK_REPORT.parent.mkdir(parents=True, exist_ok=True)

frames, counts, headers = [], [], set()
for row in cases.itertuples(index=False):
    p = Path(row.inputs_case) / FILE
    if not p.is_file():
        counts.append((row.batch, row.arm, row.level, row.case, FILE.as_posix(), False, 0))
        continue
    df = pd.read_csv(p)
    headers.add(tuple(df.columns))
    if len(df.columns) != len(COLUMNS) or not df.columns[0].startswith("*") \
            or df.columns[1] != COLUMNS[1]:
        raise SystemExit(f"STOP: {p} has columns {list(df.columns)}; expected "
                         f"an unnamed block column and `{COLUMNS[1]}`.")
    df = df.rename(columns={df.columns[0]: COLUMNS[0]})
    for c, v in (("batch", row.batch), ("arm", row.arm),
                 ("level", float(row.level)), ("case", row.case)):
        df[c] = v
    frames.append(df[ID_COLS + COLUMNS])
    counts.append((row.batch, row.arm, row.level, row.case, FILE.as_posix(), True, len(df)))

counts = pd.DataFrame(counts, columns=["batch", "arm", "level", "case", "file",
                                       "present", "rows"])
counts.to_csv(OUT_DIR / "row_counts_inputs.csv", index=False)
nh = pd.concat(frames, ignore_index=True)
out = TABLE_DIR / "numhours.h5"
out.unlink(missing_ok=True)
nh.to_hdf(out, key="data", format="table", data_columns=ID_COLS + ["h"],
          complevel=5, complib="blosc:zstd", index=False)
with pd.HDFStore(out, mode="r") as st:
    n_written = st.get_storer("data").nrows

# Checks
missing = counts.loc[~counts["present"], "case"].tolist()
check("numhours.csv present in every case", not missing,
      ", ".join(missing) or f"{len(counts)} of {len(cases)} cases")
check("Same header in every case", len(headers) == 1,
      "; ".join(str(list(h)) for h in headers))
expected = counts["arm"].map(N_BLOCKS)
bad_n = counts.loc[counts["present"] & (counts["rows"] != expected), ["case", "rows"]]
check("Blocks per case = 152, or 144 in loadhigh and loadlow (D32)", bad_n.empty,
      ", ".join(f"{c}: {r}" for c, r in bad_n.itertuples(index=False)) or
      f"all {int(counts['present'].sum())} cases")
check("Rows written = rows read", n_written == int(counts["rows"].sum()),
      f"{n_written} vs {int(counts['rows'].sum())}")
check("No missing values", int(nh[COLUMNS].isna().sum().sum()) == 0,
      f"{int(nh[COLUMNS].isna().sum().sum())} missing")
check("Block names unique within each case", not nh.duplicated(["case", "h"]).any(), "")

# All levels of one batch-arm: same blocks and same weights (D32).
arm_rows = []
for (b, a), ca in nh.groupby(["batch", "arm"], sort=False):
    tables = {c: cc.set_index("h")["numhours"].sort_index()
              for c, cc in ca.groupby("case", sort=False)}
    first_case, first = next(iter(tables.items()))
    diff_cases = [c for c, s in tables.items()
                  if not (s.index.equals(first.index) and s.equals(first))]
    arm_rows.append((b, a, len(tables), len(first), diff_cases))
bad_arm = [f"{b} {a}: {', '.join(d)}" for b, a, _, _, d in arm_rows if d]
check("Same blocks and weights at every level of each batch-arm (D32)", not bad_arm,
      "; ".join(bad_arm) or f"all {len(arm_rows)} batch-arms")

# Shown, not judged: blocks and weights against the batch's ref 0 GW case.
cmp_rows = []
for b, cb in nh.groupby("batch", sort=False):
    ref_case = cases.loc[(cases["batch"] == b) & (cases["arm"] == "ref")
                         & (cases["level"] == 0.0), "case"].iloc[0]
    ref = cb[cb["case"] == ref_case].set_index("h")["numhours"]
    for c, cc in cb.groupby("case", sort=False):
        s = cc.set_index("h")["numhours"]
        same_blocks = set(s.index) == set(ref.index)
        same_w = same_blocks and bool((s.sort_index() == ref.sort_index()).all())
        cmp_rows.append((b, cc["arm"].iloc[0], cc["level"].iloc[0], c, ref_case,
                         same_blocks, same_w, f"{s.sum():g}"))
cmp = pd.DataFrame(cmp_rows, columns=["batch", "arm", "level", "case", "compared_with",
                                      "same_blocks", "same_weights", "sum_numhours"])
cmp.to_csv(OUT_DIR / "numhours_vs_ref0.csv", index=False)
summ = (cmp.groupby(["batch", "arm"], sort=False)
        .agg(cases=("case", "count"),
             same_blocks_as_ref0=("same_blocks", "sum"),
             same_weights_as_ref0=("same_weights", "sum"),
             sum_numhours=("sum_numhours", lambda s: ", ".join(sorted(set(s)))))
        .reset_index())

# ---------------------------------------------------------------------------
# crf (D44): as reeds/io.py read_input (L436-471 at 0c0ea27)
# ---------------------------------------------------------------------------
def read_h5_key(h5path, key):
    """One key of a ReEDS-format .h5 file (reeds/io.py read_h5 L420-433), or None."""
    with h5py.File(h5path, "r") as f:
        if key not in f:
            return None
        g = f[key]
        columns = [c.decode() for c in g["columns"]]
        data = {}
        for c in columns:
            a = g[c][...] if c in g else np.array([])
            if a.dtype.kind == "S":
                a = np.char.decode(a, "utf-8").astype(object)
            data[c] = a
    return pd.DataFrame(data, columns=columns)


crf_frames, crf_src = [], []
for row in cases.itertuples(index=False):
    ic = Path(row.inputs_case)
    h5path, csvpath = ic / "inputs.h5", ic / "crf.csv"
    df, src = None, None
    if h5path.is_file():
        df = read_h5_key(h5path, "crf")
        src = "inputs.h5"
    if df is None and csvpath.is_file():          # read_input L457-468
        df = pd.read_csv(csvpath)
        src = "crf.csv"
    if df is None:
        crf_src.append((row.case, "absent", ""))
        counts.loc[len(counts)] = (row.batch, row.arm, row.level, row.case, "crf",
                                   False, 0)
        continue
    header = list(df.columns)
    if len(header) != 2 or header[0] not in ("t", "*t"):
        raise SystemExit(f"STOP: crf of {row.case} ({src}) has columns {header}; "
                         "expected t and one value column.")
    df = df.rename(columns={header[0]: "t", header[1]: "Value"})
    df["t"] = df["t"].astype("int64")
    for c, v in (("batch", row.batch), ("arm", row.arm),
                 ("level", float(row.level)), ("case", row.case)):
        df[c] = v
    crf_frames.append(df[ID_COLS + ["t", "Value"]])
    crf_src.append((row.case, src, " ".join(header)))
    counts.loc[len(counts)] = (row.batch, row.arm, row.level, row.case, "crf", True, len(df))

crf_src = pd.DataFrame(crf_src, columns=["case", "source", "header"])
crf = pd.concat(crf_frames, ignore_index=True) if crf_frames else pd.DataFrame(
    columns=ID_COLS + ["t", "Value"])
out_crf = TABLE_DIR / "crf.h5"
out_crf.unlink(missing_ok=True)
crf.to_hdf(out_crf, key="data", format="table", data_columns=ID_COLS + ["t"],
           complevel=5, complib="blosc:zstd", index=False)
with pd.HDFStore(out_crf, mode="r") as st:
    n_crf_written = st.get_storer("data").nrows

crf_missing = crf_src.loc[crf_src["source"] == "absent", "case"].tolist()
check("crf present in every case (inputs.h5 or crf.csv)", not crf_missing,
      ", ".join(crf_missing) or
      ", ".join(f"{s}: {n} cases" for s, n in crf_src["source"].value_counts().items()))
check("crf: one row per case and year", not crf.duplicated(["case", "t"]).any(), "")
check("crf: no missing value", int(crf["Value"].isna().sum()) == 0,
      f"{int(crf['Value'].isna().sum())} missing")
check("crf: rows written = rows read", n_crf_written == len(crf),
      f"{n_crf_written} vs {len(crf)}")

# Values by year (shown) and equality across the cases of each batch (shown, not judged).
crf_by_year = (crf.groupby(["batch", "t"])["Value"]
               .agg(cases="count", min="min", max="max").reset_index())
crf_by_year["equal_in_batch"] = crf_by_year["min"] == crf_by_year["max"]
crf_eq = []
for b, cb in crf.groupby("batch", sort=False):
    w = cb.pivot_table(index="t", columns="case", values="Value", aggfunc="first")
    same_years = all(set(cc["t"]) == set(cb["t"]) for _, cc in cb.groupby("case"))
    n_diff = int((w.nunique(axis=1, dropna=False) > 1).sum())
    crf_eq.append((b, cb["case"].nunique(), cb["t"].nunique(), same_years,
                   n_diff == 0, n_diff))
crf_eq = pd.DataFrame(crf_eq, columns=["batch", "cases", "years", "same_years_in_all_cases",
                                       "values_equal_in_all_cases", "years_with_differences"])

# ---------------------------------------------------------------------------
# scalars.csv (for trans_crp; reeds/io.py get_scalars L764-790 at 0c0ea27)
# ---------------------------------------------------------------------------
sc_frames, sc_missing = [], []
for row in cases.itertuples(index=False):
    p = Path(row.inputs_case) / "scalars.csv"
    if not p.is_file():
        sc_missing.append(row.case)
        counts.loc[len(counts)] = (row.batch, row.arm, row.level, row.case,
                                   "scalars.csv", False, 0)
        continue
    df = pd.read_csv(p, header=None, usecols=[0, 1], names=["name", "value"], dtype=str)
    for c, v in (("batch", row.batch), ("arm", row.arm),
                 ("level", float(row.level)), ("case", row.case)):
        df[c] = v
    sc_frames.append(df[ID_COLS + ["name", "value"]])
    counts.loc[len(counts)] = (row.batch, row.arm, row.level, row.case, "scalars.csv",
                               True, len(df))
sc = pd.concat(sc_frames, ignore_index=True) if sc_frames else pd.DataFrame(
    columns=ID_COLS + ["name", "value"])
out_sc = TABLE_DIR / "scalars.h5"
out_sc.unlink(missing_ok=True)
sc.to_hdf(out_sc, key="data", format="table", data_columns=ID_COLS + ["name"],
          complevel=5, complib="blosc:zstd", index=False,
          min_itemsize={"value": 64, "name": 64})
check("scalars.csv present in every case", not sc_missing,
      ", ".join(sc_missing) or f"{len(sc_frames)} cases")
tcrp = sc[sc["name"] == "trans_crp"]
check("scalars: one `trans_crp` row per case", len(tcrp) == len(sc_frames)
      and tcrp["case"].is_unique, f"{len(tcrp)} rows")
tcrp_vals = ", ".join(f"{v}: {n} cases" for v, n in tcrp["value"].value_counts().items())

counts.to_csv(OUT_DIR / "row_counts_inputs.csv", index=False)

ok = all(r == "PASS" for _, r, _ in checks)
lines = [f"## 01b_load_inputs — {'PASS' if ok else 'FAIL'}\n",
         f"Source: `inputs_case/rep/numhours.csv` of the {len(cases)} cases. "
         "Column `*h` renamed to `h`; `numhours` kept.\n",
         "Table: `outputs/01_ingest/inputs/numhours.h5`. Counts: "
         "`outputs/01_ingest/row_counts_inputs.csv`.\n",
         "### Checks\n",
         md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
         "### Missing files\n",
         ("None.\n" if not missing else ", ".join(missing) + "\n"),
         "### Row count per case\n",
         "Rows per case: " + ", ".join(f"{r} ({n} cases)" for r, n in
                                       counts.loc[counts["file"] == FILE.as_posix(), "rows"]
                                       .value_counts().items()) + ".\n",
         "### Blocks and weights against the batch's `ref` 0 GW case (shown, not judged)\n",
         "The load arms have their own blocks by design (D32). "
         "Per case: `outputs/01_ingest/numhours_vs_ref0.csv`. `sum_numhours` is the sum "
         "of the block weights in each case (distinct values in the arm).\n",
         md_table(summ) + "\n",
         "### crf (D44, for 03b2)\n",
         "Read as `reeds/io.py` `read_input` (L436-471 at 0c0ea27): `inputs_case/inputs.h5` "
         "key `crf`, else `inputs_case/crf.csv`. Table: `outputs/01_ingest/inputs/crf.h5` "
         "(t, Value; model units, a fraction per `calc_financial_inputs.py` L518).\n",
         "Source per case: " + ", ".join(f"{s} ({n} cases)" for s, n in
                                         crf_src["source"].value_counts().items())
         + ". Headers found: " + ", ".join(f"`{h}`" for h in
                                         sorted(set(crf_src["header"]) - {""})) + ".\n",
         "Rows per case: " + ", ".join(f"{r} ({n} cases)" for r, n in
                                       counts.loc[counts["file"] == "crf", "rows"]
                                       .value_counts().items()) + ".\n",
         "Equal across the cases of each batch (shown, not judged):\n",
         md_table(crf_eq) + "\n",
         "Values by batch and year (min and max over the cases of the batch):\n",
         md_table(crf_by_year.assign(min=crf_by_year["min"].map(lambda x: f"{x:.6g}"),
                                     max=crf_by_year["max"].map(lambda x: f"{x:.6g}")))
         + "\n",
         "### scalars.csv (for 03b2: `trans_crp`)\n",
         "Table: `outputs/01_ingest/inputs/scalars.h5` (name, value as text). "
         f"`trans_crp` values: {tcrp_vals or 'none'}.\n"]
write_section(CHECK_REPORT, SECTION, "\n".join(lines))
print(f"01b: {'PASS' if ok else 'FAIL'}; report section written to {CHECK_REPORT}")
sys.exit(0 if ok else 1)
