"""01a_load_outputs: copy the model outputs of every case, change nothing.

docs/plan.md, stage 01_ingest. Reads each key of docs/data_dictionary.md,
"Outputs read from each run", from <case>/outputs/outputs.h5 for every case in
00_config/study_cases.csv (D29). The file layout is the one that
reeds/io.py read_h5 reads (L420-433 at 0c0ea27): one group per key, a `columns`
dataset with the column names, one dataset per column, byte strings in UTF-8.
A key that is absent from a case is an empty table, not an error
(reeds/io.py L506 at 0c0ea27); absent keys are listed in the check report.

What the script changes, and nothing else:
- Byte strings are decoded as UTF-8 (as read_h5 does).
- The block column `allh` is renamed to `h` (in gen_h and tran_util_h_rep),
  as reeds/io.py read_output does (L524 at 0c0ea27); D33.
- Unnamed columns (`*`, `*.1`, `*.2`) are renamed by position to the column
  names in the data dictionary table. If the named columns of a key do not sit
  at the same positions as in the data dictionary, the script stops: it does
  not guess.
Tables keep `t`, `Value` (float32 as stored) and model units (D33).
- Columns batch, arm, level, case are added from 00_config/study_cases.csv.
No row is dropped, no value is changed, no unit or dollar conversion (rule 6).

Out (generated, not committed): one long table per key,
  outputs/01_ingest/outputs/<key>.h5   (pandas HDFStore, table format, key "data";
                                        every column but Value is queryable,
                                        e.g. pd.read_hdf(p, "data", where='case == "X"'))
  outputs/01_ingest/row_counts_outputs.csv   (batch, arm, level, case, key, present, rows)
  outputs/01_ingest/columns_found.csv        (key, columns in file, columns written)
  outputs/01_ingest/undocumented_keys_summary.csv
Check report section "01a" in outputs/checks/01_ingest.md (D24).

A failed check makes the script exit with code 1 (plan rule 5).

Run:  conda run -n reeds python 01_ingest/01a_load_outputs.py
"""

import re
import sys
import time
from pathlib import Path

import h5py
import numpy as np
import pandas as pd

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO / "00_config"
OUT_DIR = REPO / "outputs" / "01_ingest"
TABLE_DIR = OUT_DIR / "outputs"
CHECK_REPORT = REPO / "outputs" / "checks" / "01_ingest.md"   # D24
SECTION = "01a"

# ---------------------------------------------------------------------------
# Keys to read: docs/data_dictionary.md, "Outputs read from each run".
# Columns are the names in the data dictionary table, in file order (for
# tran_util_h_rep the data dictionary gives the file order). The last three
# keys are from the same section, paragraph "For the SMR value analysis"
# (used by 03g, 03h, 03i; D33).
# ---------------------------------------------------------------------------
KEYS = {
    "reqt_price": ["type", "subtype", "r", "h", "t"],
    "reqt_quant": ["type", "subtype", "r", "h", "t"],
    "systemcost_ba_bulk_ew": ["sys_costs", "r", "t"],
    "net_import_ann_rep": ["r", "t"],
    "net_import_ann_stress": ["r", "t"],            # optional
    "expenditure_flow": ["type", "r", "rr", "t"],
    "expenditure_flow_rps": ["st", "ast", "t"],
    "expenditure_flow_int": ["r", "t"],
    "tran_out": ["r", "rr", "trtype", "t"],
    "invtran_out": ["r", "rr", "trtype", "t"],
    "tran_util_h_rep": ["r", "rr", "h", "t", "trtype"],
    "tran_flow_rep_ann": ["r", "rr", "trtype", "t"],
    "cap_ivrt": ["i", "v", "r", "t"],
    "ret_ivrt": ["i", "v", "r", "t"],
    "gen_ivrt": ["i", "v", "r", "t"],
    "gen_h": ["i", "r", "h", "t"],
    "cost_vom": ["i", "v", "r", "t"],
    "heat_rate": ["i", "v", "r", "t"],
    "fuel_price": ["i", "r", "t"],
    "repgasprice_r": ["r", "t"],                    # optional
    "valnew": ["type", "i", "r", "t"],
    "reduced_cost": ["i", "v", "r", "t", "bin", "variable"],
    "lcoe_built": ["i", "r", "t"],
}
OPTIONAL_KEYS = {"net_import_ann_stress", "repgasprice_r"}
# Units not covered in the documentation (data dictionary); values reported.
UNDOCUMENTED_KEYS = ["cost_vom", "heat_rate", "fuel_price"]
NAMED_RENAMES = {"allh": "h"}  # D33; reeds/io.py read_output L524 at 0c0ea27
VALUE_COL = "Value"            # value column name in outputs.h5, kept as is
ID_COLS = ["batch", "arm", "level", "case"]
STAR = re.compile(r"^\*(\.\d+)?$")

# Verifier sample cases (D23, D31); used for the undocumented-key findings.
SAMPLE_CASES = [("UON", "ref", 0.0), ("UON", "ref", 3.0), ("UOS", "ref", 2.5)]


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def md_table(df):
    """Markdown table without the optional `tabulate` package."""
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |",
           "| " + " | ".join("---" for _ in cols) + " |"]
    for row in df.itertuples(index=False):
        out.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(out)


checks = []   # (check, result, detail)


def check(name, ok, detail=""):
    checks.append((name, "PASS" if ok else "FAIL", detail))
    return ok


def write_section(path, section, text):
    """Write this script's section of the stage check report.

    The report holds one section per script, between markers. Only this
    script's section is replaced, so 01a and 01b can run in any order.
    """
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


def read_key(f, key):
    """Read one key as read_h5 does (reeds/io.py L420-433 at 0c0ea27).

    Returns (DataFrame, file column list), or (None, None) if the key is absent.
    """
    if key not in f:
        return None, None
    g = f[key]
    columns = [c.decode() for c in g["columns"]]
    data = {}
    for c in columns:
        a = g[c][...]
        if a.dtype.kind == "S":
            a = np.char.decode(a, "utf-8").astype(object)
        data[c] = a
    df = pd.DataFrame(data, columns=columns)
    for c in columns:
        if df[c].dtype == object:
            df[c] = df[c].astype("str")
    return df, columns


def rename_map(key, file_cols):
    """Rename `allh` to `h` (D33) and `*` columns by position.

    Named columns must already equal the data dictionary name at the same
    position whenever the key has `*` columns; otherwise the rename would be a
    guess, and the script stops.
    """
    dd = KEYS[key]
    out = {c: NAMED_RENAMES[c] for c in file_cols if c in NAMED_RENAMES}
    stars = [c for c in file_cols if STAR.match(c)]
    if not stars:
        return out
    idx_cols = [out.get(c, c) for c in file_cols if c != VALUE_COL]
    if len(idx_cols) != len(dd):
        raise SystemExit(f"STOP: {key} has unnamed columns {stars} but the data "
                         f"dictionary gives no matching column list ({dd}).")
    for pos, c in enumerate(idx_cols):
        if STAR.match(c):
            out[c] = dd[pos]
        elif c != dd[pos]:
            raise SystemExit(f"STOP: {key} column {pos} is '{c}' in the file and "
                             f"'{dd[pos]}' in the data dictionary; rename by "
                             f"position would be a guess.")
    return out


# ---------------------------------------------------------------------------
# 1. Case list (00_config, stage 00a)
# ---------------------------------------------------------------------------
cases = pd.read_csv(CONFIG_DIR / "study_cases.csv")
check("Case list read from 00_config/study_cases.csv",
      len(cases) > 0 and cases["case"].is_unique,
      f"{len(cases)} cases, {cases['batch'].nunique()} batches")
check("Every outputs.h5 exists",
      all(Path(p).is_file() for p in cases["outputs_h5"]),
      ", ".join(c for c, p in zip(cases["case"], cases["outputs_h5"])
                if not Path(p).is_file()) or "all present")

# ---------------------------------------------------------------------------
# 2. Pre-pass: string widths and column lists per key (metadata only), so that
#    every string column gets a fixed width wide enough for all cases.
# ---------------------------------------------------------------------------
width = {k: {} for k in KEYS}           # key -> column -> max bytes
file_cols_seen = {k: set() for k in KEYS}
for p in cases["outputs_h5"]:
    with h5py.File(p, "r") as f:
        for k in KEYS:
            if k not in f:
                continue
            cols = [c.decode() for c in f[k]["columns"]]
            file_cols_seen[k].add(tuple(cols))
            for c in cols:
                dt = f[k][c].dtype
                if dt.kind == "S":
                    width[k][c] = max(width[k].get(c, 1), dt.itemsize)

check("Each key has the same columns in every case where it is present",
      all(len(v) <= 1 for v in file_cols_seen.values()),
      "; ".join(f"{k}: {sorted(v)}" for k, v in file_cols_seen.items() if len(v) > 1)
      or "same in every case")

# ---------------------------------------------------------------------------
# 3. Read every key of every case and append to one long table per key.
# ---------------------------------------------------------------------------
TABLE_DIR.mkdir(parents=True, exist_ok=True)
CHECK_REPORT.parent.mkdir(parents=True, exist_ok=True)
for k in KEYS:
    (TABLE_DIR / f"{k}.h5").unlink(missing_ok=True)

stores = {k: pd.HDFStore(TABLE_DIR / f"{k}.h5", mode="w",
                         complevel=5, complib="blosc:zstd") for k in KEYS}
id_width = {"batch": int(cases["batch"].str.len().max()),
            "arm": int(cases["arm"].str.len().max()),
            "case": int(cases["case"].str.len().max())}
counts = []          # one row per case and key
columns_found = {}   # key -> (file columns, written columns)
samples = {}         # (key, case) -> DataFrame, for undocumented keys
value_stats = []     # NaN count per key
t0 = time.time()
try:
    for n, row in enumerate(cases.itertuples(index=False), start=1):
        with h5py.File(row.outputs_h5, "r") as f:
            for k in KEYS:
                df, fcols = read_key(f, k)
                if df is None:
                    counts.append((row.batch, row.arm, row.level, row.case, k, False, 0))
                    continue
                ren = rename_map(k, fcols)
                df = df.rename(columns=ren)
                columns_found.setdefault(k, (fcols, list(df.columns)))
                n_rows = len(df)
                for c, v in (("batch", row.batch), ("arm", row.arm),
                             ("level", float(row.level)), ("case", row.case)):
                    df[c] = v
                df = df[ID_COLS + [c for c in df.columns if c not in ID_COLS]]
                value_stats.append((k, row.case, int(df[VALUE_COL].isna().sum())))
                if k in UNDOCUMENTED_KEYS and (row.batch, row.arm, float(row.level)) in SAMPLE_CASES:
                    samples[(k, row.case)] = df.copy()
                if n_rows:
                    min_itemsize = dict(id_width)
                    for c_file, w in width[k].items():
                        min_itemsize[ren.get(c_file, c_file)] = w
                    stores[k].append(
                        "data", df, format="table", index=False,
                        data_columns=[c for c in df.columns if c != VALUE_COL],
                        min_itemsize=min_itemsize)
                counts.append((row.batch, row.arm, row.level, row.case, k, True, n_rows))
        if n % 10 == 0 or n == len(cases):
            print(f"  {n}/{len(cases)} cases read ({time.time() - t0:.0f} s)", flush=True)
finally:
    for st in stores.values():
        st.close()

counts = pd.DataFrame(counts, columns=["batch", "arm", "level", "case", "key",
                                       "present", "rows"])
counts.to_csv(OUT_DIR / "row_counts_outputs.csv", index=False)
pd.DataFrame([(k, " ".join(v[0]), " ".join(v[1])) for k, v in columns_found.items()],
             columns=["key", "columns_in_file", "columns_written"]
             ).to_csv(OUT_DIR / "columns_found.csv", index=False)

# ---------------------------------------------------------------------------
# 4. Checks
# ---------------------------------------------------------------------------
# 4a. Every case was read for every key (present or listed as absent).
check("Every case and key read",
      len(counts) == len(cases) * len(KEYS),
      f"{len(counts)} case-key pairs = {len(cases)} cases x {len(KEYS)} keys")

# 4b. Rows written equal rows read (written tables re-opened, metadata only).
written = {}
for k in KEYS:
    p = TABLE_DIR / f"{k}.h5"
    with pd.HDFStore(p, mode="r") as st:
        written[k] = st.get_storer("data").nrows if "/data" in st.keys() else 0
read_rows = counts.groupby("key")["rows"].sum()
bad = [k for k in KEYS if written[k] != read_rows[k]]
check("Rows written = rows read, per key", not bad,
      ", ".join(f"{k}: {written[k]} vs {read_rows[k]}" for k in bad) or
      f"{int(read_rows.sum()):,} rows in {len(KEYS)} tables")

# 4c. No missing values in Value.
vs = pd.DataFrame(value_stats, columns=["key", "case", "nan"])
nan_keys = vs.groupby("key")["nan"].sum()
check("No missing Value", int(nan_keys.sum()) == 0,
      ", ".join(f"{k}: {v}" for k, v in nan_keys.items() if v) or "none")

# 4d. Absent keys.
absent = counts[~counts["present"]]
absent_required = absent[~absent["key"].isin(OPTIONAL_KEYS)]

# 4e. Columns against the data dictionary (after renaming).
col_rows = []
for k, dd in KEYS.items():
    if k not in columns_found:
        col_rows.append((k, "absent in all cases", "", ""))
        continue
    fcols, wcols = columns_found[k]
    idx = [c for c in wcols if c != VALUE_COL]
    if idx == dd:
        verdict = "matches"
    elif sorted(idx) == sorted(dd):
        verdict = "same names, other order"
    else:
        verdict = "differs"
    col_rows.append((k, ", ".join(f"`{c}`" for c in fcols),
                     ", ".join(f"`{c}`" for c in idx),
                     ", ".join(dd) + f" — {verdict}"))
col_table = pd.DataFrame(col_rows, columns=["key", "columns in file",
                                            "columns written (no Value)",
                                            "data dictionary — result"])
bad_cols = [r[0] for r in col_rows if not r[3].endswith("matches")]
check("Columns written match the data dictionary (after renaming)", not bad_cols,
      ", ".join(bad_cols) or f"all {len(KEYS)} keys")

# 4f. Similar counts within each batch and arm.
grp = counts.groupby(["batch", "arm", "key"])["rows"]
spread = grp.agg(cases="count", min="min", max="max", median="median").reset_index()
spread["spread_pct"] = np.where(spread["max"] > 0,
                                100 * (spread["max"] - spread["min"]) / spread["max"], 0.0)
spread["same_in_all_cases"] = spread["min"] == spread["max"]
spread.to_csv(OUT_DIR / "row_count_spread.csv", index=False)

# ---------------------------------------------------------------------------
# 5. Findings for the undocumented keys (cost_vom, heat_rate, fuel_price)
# ---------------------------------------------------------------------------
und_rows = []
und_text = []
for k in UNDOCUMENTED_KEYS:
    und_text.append(f"#### `{k}`\n")
    if k not in columns_found:
        und_text.append("Absent in every case.\n")
        continue
    fcols, wcols = columns_found[k]
    kc = counts[counts["key"] == k]
    und_text.append(f"- Columns in the file: {', '.join(f'`{c}`' for c in fcols)}. "
                    f"Present in {int(kc['present'].sum())} of {len(kc)} cases; "
                    f"rows per case {int(kc['rows'].min())} to {int(kc['rows'].max())}.")
    for (key, case), df in samples.items():
        if key != k:
            continue
        idx = [c for c in df.columns if c not in ID_COLS + [VALUE_COL]]
        uniq = ", ".join(f"{c}: {df[c].nunique()}" for c in idx)
        years = sorted(int(t) for t in df["t"].unique()) if "t" in df else []
        und_text.append(f"- `{case}`: {len(df)} rows; distinct values per column: {uniq}; "
                        f"t from {years[0]} to {years[-1]} ({len(years)} distinct years); "
                        f"Value from {df[VALUE_COL].min():.4g} to {df[VALUE_COL].max():.4g}, "
                        f"median {df[VALUE_COL].median():.4g}.")
        by_i = (df.groupby("i")[VALUE_COL]
                .agg(rows="count", min="min", median="median", max="max").reset_index())
        by_i.insert(0, "case", case)
        by_i.insert(0, "key", k)
        und_rows.append(by_i)
    first = next(((case, df) for (key, case), df in samples.items() if key == k), None)
    if first is not None:
        case, df = first
        show = df.drop(columns=["batch", "arm", "level"]).head(5).copy()
        show[VALUE_COL] = show[VALUE_COL].map(lambda x: f"{x:.4g}")
        und_text.append(f"\nFirst 5 rows of `{case}`:\n\n" + md_table(show) + "\n")
        by_i = (df.groupby("i")[VALUE_COL]
                .agg(rows="count", min="min", median="median", max="max").reset_index())
        for c in ["min", "median", "max"]:
            by_i[c] = by_i[c].map(lambda x: f"{x:.4g}")
        und_text.append(f"Value by `i` in `{case}`, all years:\n\n" + md_table(by_i) + "\n")
if und_rows:
    pd.concat(und_rows).to_csv(OUT_DIR / "undocumented_keys_summary.csv", index=False)

# ---------------------------------------------------------------------------
# 6. Check report section
# ---------------------------------------------------------------------------
ok = all(r == "PASS" for _, r, _ in checks)
lines = [f"## 01a_load_outputs — {'PASS' if ok else 'FAIL'}\n",
         f"Source: `outputs.h5` of the {len(cases)} cases in `00_config/study_cases.csv`, "
         f"{len(KEYS)} keys (`docs/data_dictionary.md`, \"Outputs read from each run\", "
         "with `valnew`, `reduced_cost`, `lcoe_built` from its SMR paragraph). "
         "Values kept in model units (float32 as stored).\n",
         f"Tables: `outputs/01_ingest/outputs/<key>.h5` (pandas HDFStore, table format, "
         "key `data`). Counts: `outputs/01_ingest/row_counts_outputs.csv`.\n",
         "### Checks\n",
         md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
         "### Absent keys\n"]
if absent.empty:
    lines.append("No key is absent in any case.\n")
else:
    a = (absent.groupby("key")["case"].apply(lambda s: f"{len(s)} cases: " + ", ".join(s))
         .reset_index())
    a["optional"] = a["key"].isin(OPTIONAL_KEYS)
    lines.append("An absent key is an empty table (reeds/io.py L506 at 0c0ea27); "
                 "not a failure.\n\n" + md_table(a) + "\n")
lines += ["### Columns against the data dictionary\n",
          "`*` columns were renamed by position and `allh` to `h` (D33); other named columns kept as in the file.\n",
          md_table(col_table) + "\n",
          "### Row counts: spread within each batch and arm\n",
          "No threshold for \"similar\" is in `docs/decisions.md`; every batch-arm-key "
          "where counts are not the same in all cases is listed, with its spread "
          "((max - min) / max). Full list: `outputs/01_ingest/row_count_spread.csv`.\n"]
diff = spread[~spread["same_in_all_cases"]].sort_values("spread_pct", ascending=False)
same_n = int(spread["same_in_all_cases"].sum())
lines.append(f"{same_n} of {len(spread)} batch-arm-key groups have the same count in all "
             f"cases. The other {len(diff)}:\n")
if not diff.empty:
    d = diff.copy()
    d["median"] = d["median"].map(lambda x: f"{x:.0f}")
    d["spread_pct"] = d["spread_pct"].map(lambda x: f"{x:.2f}")
    lines.append(md_table(d.drop(columns=["same_in_all_cases"])) + "\n")
lines.append("### Row count per case and key\n")
lines.append("Display only (the data are long in `row_counts_outputs.csv`). "
             "Columns are keys; 0 = absent.\n")
for b, cb in counts.groupby("batch", sort=False):
    w = cb.pivot_table(index=["arm", "level", "case"], columns="key", values="rows",
                       aggfunc="sum", sort=False).reindex(columns=list(KEYS))
    w = w.reset_index()[["case"] + list(KEYS)]
    lines.append(f"**{b}**\n\n" + md_table(w) + "\n")
lines.append("### Undocumented keys: what the files hold\n")
lines.append("`report_params.csv` at 0c0ea27 lists `cost_vom` (L255), `fuel_price` (L260) and "
             "`heat_rate` (L263) with no index, unit or description. Their units are "
             "**Not covered in the documentation** (data dictionary); nothing below is a unit claim. "
             "Shown for the Verifier sample cases (D23, D31). "
             "Per-`i` table for all sample cases: `outputs/01_ingest/undocumented_keys_summary.csv`.\n")
lines += und_text
write_section(CHECK_REPORT, SECTION, "\n".join(lines))
print(f"01a: {'PASS' if ok else 'FAIL'}; report section written to {CHECK_REPORT}")
sys.exit(0 if ok else 1)
