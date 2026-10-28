"""02c_neighbor_list: p25's neighbors from tran_out, against the expected list.

docs/plan.md, stage 02_clean, 02c; D7, D31, D35a; data_dictionary.md, Region groups.
In each batch, the neighbors are the zones that share a `tran_out` row with
p25 in that batch's `ref` 0 GW case: rr where r = p25, and r where rr = p25
(both columns; report_calcs.py writes each line pair once, r before rr in text
order, data_dictionary.md "Outputs read from each run"). p26 is not a
neighbor (it is its own group, `utah_rest`). Every year and every `trtype`
in the table are read; the report shows them per neighbor. Nothing is
filtered by year or line type: the docs set no such rule.

Expected list (D35a; data_dictionary.md): p10, p12, p16, p21, p24, p27, p31, p33,
z28, any line type (AC or DC). Also
00_config/region_groups.csv, group `neighbors`, for each batch.
**Stops if they differ** (plan rule 5).

In:  outputs/01_ingest/outputs/tran_out.h5 (stage 01)
     00_config/study_cases.csv, 00_config/region_groups.csv
Out (generated): outputs/02_clean/neighbor_list.csv (one row per batch, line),
     section "02c" of outputs/checks/02_clean.md
Exits with code 1 if the list differs. No data are changed.

Run:  conda run -n reeds python 02_clean/02c_neighbor_list.py
"""

import sys
from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO / "00_config"
IN_DIR = REPO / "outputs" / "01_ingest" / "outputs"
OUT_DIR = REPO / "outputs" / "02_clean"
CHECK_REPORT = REPO / "outputs" / "checks" / "02_clean.md"
SECTION = "02c"

FOCUS = "p25"
UTAH_REST = "p26"
REF_ARM, REF_LEVEL = "ref", 0.0                        # D31
EXPECTED = ["p10", "p12", "p16", "p21", "p24", "p27", "p31", "p33", "z28"]  # D35a


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
cases = pd.read_csv(CONFIG_DIR / "study_cases.csv")
groups = pd.read_csv(CONFIG_DIR / "region_groups.csv")

checks, lines_out, results = [], [], []
for b in sorted(cases["batch"].unique()):
    ref0 = cases[(cases["batch"] == b) & (cases["arm"] == REF_ARM)
                 & (cases["level"] == REF_LEVEL)]
    if len(ref0) != 1:
        checks.append((f"{b}: one `ref` 0 GW case", "FAIL", f"{len(ref0)} found"))
        continue
    case = ref0["case"].iloc[0]
    tr = pd.read_hdf(IN_DIR / "tran_out.h5", "data", where=f'case == "{case}"')
    touch = tr[(tr["r"] == FOCUS) | (tr["rr"] == FOCUS)].copy()
    touch["neighbor"] = touch["rr"].where(touch["r"] == FOCUS, touch["r"])
    lines = (touch.groupby(["neighbor", "r", "rr", "trtype"])
             .agg(first_year=("t", "min"), last_year=("t", "max"), years=("t", "nunique"),
                  cap_min_MW=("Value", "min"), cap_max_MW=("Value", "max"))
             .reset_index())
    lines.insert(0, "case", case)
    lines.insert(0, "batch", b)
    lines["in_expected"] = lines["neighbor"].isin(EXPECTED)
    lines["note"] = lines["neighbor"].map(
        lambda n: "p26: own group utah_rest, not a neighbor" if n == UTAH_REST else "")
    lines_out.append(lines)

    found = sorted(set(lines["neighbor"]) - {UTAH_REST})
    cfg = sorted(groups.loc[(groups["batch"] == b) & (groups["group"] == "neighbors"),
                            "region"])
    extra = sorted(set(found) - set(EXPECTED))
    missing = sorted(set(EXPECTED) - set(found))
    ok = not extra and not missing
    checks.append((f"{b}: neighbors from `tran_out` of `{case}` = expected list",
                   "PASS" if ok else "FAIL",
                   f"found {', '.join(found)}; extra: {', '.join(extra) or 'none'}; "
                   f"missing: {', '.join(missing) or 'none'}"))
    checks.append((f"{b}: 00_config/region_groups.csv `neighbors` = expected list",
                   "PASS" if cfg == sorted(EXPECTED) else "FAIL", ", ".join(cfg)))
    results.append((b, case, ", ".join(found), ", ".join(EXPECTED),
                    ", ".join(extra) or "-", ", ".join(missing) or "-"))

lines_all = pd.concat(lines_out, ignore_index=True)
lines_all.to_csv(OUT_DIR / "neighbor_list.csv", index=False)

ok = all(c[1] == "PASS" for c in checks)
show = lines_all.drop(columns=["case"]).copy()
for c in ["cap_min_MW", "cap_max_MW"]:
    show[c] = show[c].map(lambda x: f"{x:,.1f}")
text = [f"## 02c_neighbor_list — {'PASS' if ok else 'FAIL'}\n",
        "Rule (D7, D31, D35a; data_dictionary.md Region groups): in each batch, the zones "
        "that share a `tran_out` row with p25 in that batch's `ref` 0 GW case, from "
        "both `r` and `rr`, minus p26. All years and all `trtype` values (AC or DC) are read.\n",
        "### Checks\n",
        md_table(pd.DataFrame(checks, columns=["check", "result", "detail"])) + "\n",
        "### Found against expected\n",
        md_table(pd.DataFrame(results, columns=["batch", "case", "found", "expected",
                                                "extra", "missing"])) + "\n",
        "### Every `tran_out` line that touches p25\n",
        md_table(show) + "\n",
        "File: `outputs/02_clean/neighbor_list.csv`.\n"]
if not ok:
    text.append("**NEIGHBOR LIST DIFFERS. The pipeline stops here (plan rule 5). "
                "No data or config were changed.**\n")
write_section(CHECK_REPORT, SECTION, "\n".join(text))
print(f"02c neighbor list: {'PASS' if ok else 'FAIL'}")
for c in checks:
    print(" ", c[1], "-", c[0], "-", c[2])
sys.exit(0 if ok else 1)
