"""00a_study: write down the study (docs/plan.md, stage 00_config).

Lists every UON and UOS case used in the study (D25, D27), records the setup
switches of every case from inputs_case/switches.csv (D30), the ReEDS source
path and HEAD, the region groups, the 34 western zones, the solve years and the
dollar factor. Checks the case list and the switches against
docs/data_dictionary.md. Writes a check report to outputs/checks/00_config.md.

A failed check makes the script exit with code 1 (plan rule 5). No data are
changed to make a check pass.

Run:  conda run -n reeds python 00_config/00a_study.py
"""

import io
import re
import subprocess
import sys
from pathlib import Path

import h5py
import pandas as pd

# ---------------------------------------------------------------------------
# Paths (set once here; D25, D30)
# ---------------------------------------------------------------------------
REPO = Path(__file__).resolve().parents[1]
RUNS_ROOT = Path(r"D:\ReEDS\runs")              # D25
REEDS_SRC = Path(r"C:\Users\caleb\ReEDS")       # D30
REEDS_COMMIT = "0c0ea27"                        # D1, D30

CONFIG_DIR = REPO / "00_config"                 # committed study tables
OUT_DIR = REPO / "outputs" / "00_config"        # generated, not committed
CHECK_REPORT = REPO / "outputs" / "checks" / "00_config.md"   # D24

# ---------------------------------------------------------------------------
# Study definition, from docs/data_dictionary.md and docs/decisions.md
# ---------------------------------------------------------------------------
# Batches and folder prefixes (data dictionary "Runs and batches"; D25).
BATCHES = {"UON": "UON_20261022_", "UOS": "UOS_20261021_"}

# Arms and levels (data dictionary "Arms and their baselines"; D27).
UON_LEVELS = [i * 0.25 for i in range(13)]   # 0 to 3 GW, step 0.25
UOS_LEVELS = [i * 0.5 for i in range(7)]     # 0 to 3 GW, step 0.5
ARMS = {
    "UON": {a: UON_LEVELS for a in
            ["ref", "gaslow", "loadhigh", "loadlow", "pvadv", "smrcons"]},
    "UOS": {a: UOS_LEVELS for a in ["ref", "loadhigh", "loadlow"]},
}
TRUNK_LEVEL = 0.5   # data dictionary "Study terms": Trunk; D28

# Setup switches that are the same in every case (data dictionary "Model setup").
# GSw_LoadProfiles is listed there for `ref`; the load arms change it, so it is
# checked with the arm switches below.
SETUP_SWITCHES = {
    "GSw_Region": {"UON": "interconnect/western", "UOS": "interconnect/western"},
    "GSw_ZoneSet": {"UON": "z132", "UOS": "z132"},
    "GSw_GasCurve": {"UON": "2", "UOS": "2"},
    "GSw_Clean_Air_Act": {"UON": "0", "UOS": "0"},
    "GSw_Upgrades": {"UON": "0", "UOS": "1"},
    "GSw_ForcePrescription": {"UON": "1", "UOS": "1"},
    "demandscen": {"UON": "AEO_2026_baseline", "UOS": "AEO_2026_baseline"},
    "GSw_PRM_CapCredit": {"UON": "0", "UOS": "0"},
}
REF_LOAD_PROFILE = "EER2025_IRAlow"   # data dictionary "Model setup", `ref`

# The one arm switch per arm (data dictionary "Arms and their baselines").
ARM_SWITCH = {
    "ref": None,
    "gaslow": ("ngscen", "AEO_2026_HOG"),
    "loadhigh": ("GSw_LoadProfiles", "EER2025_100by2050"),
    "loadlow": ("GSw_LoadProfiles", "EER2025_Baseline_AEO2023"),
    "pvadv": ("plantchar_upv", "upv_ATB_2024_advanced"),
    "smrcons": ("plantchar_nuclear_smr", "nuclear-smr_ATB_2024_conservative"),
}
ARM_SWITCH_NAMES = sorted({v[0] for v in ARM_SWITCH.values() if v})

# Solve years (data dictionary "Study terms": Solve year).
SOLVE_YEARS = [2010, 2015, 2020, 2023] + list(range(2026, 2051, 3))
POST_PLANT_YEARS = [2044, 2047, 2050]
SYSTEM_COST_YEARS = [2044, 2047, 2050]   # D10

# Dollar factor (D8): 2004 USD to 2024 USD.
DOLLAR_FACTOR = 1.6563
DOLLAR_FACTOR_FILE = "inputs/financials/inflation_default.csv"

# Region groups (data dictionary "Region groups"; D7, D13, D31, D35a).
FOCUS = ["p25"]
UTAH_REST = ["p26"]
NEIGHBORS_EXPECTED = ["p10", "p12", "p16", "p21", "p24", "p27", "p31", "p33", "z28"]  # D35a
N_WEST_ZONES = 34


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def git(*args):
    out = subprocess.run(["git", "-C", str(REEDS_SRC), *args],
                         capture_output=True, text=True, check=True)
    return out.stdout


def level_label(level):
    """0.5 -> '0p5G', 3.0 -> '3G' (D25: 'p' is the decimal point)."""
    s = f"{level:g}".replace(".", "p")
    return f"{s}G"


def parse_case(name):
    """'UON_20261022_2p5G_ref' -> (batch, level, arm) or None."""
    m = re.fullmatch(r"(UON|UOS|UOC)_(\d{8})_(\d+(?:p\d+)?)G_([A-Za-z0-9]+)", name)
    if not m:
        return None
    return m.group(1), float(m.group(3).replace("p", ".")), m.group(4)


def md_table(df):
    """Markdown table without the optional `tabulate` package."""
    cols = list(df.columns)
    out = ["| " + " | ".join(cols) + " |", "| " + " | ".join("---" for _ in cols) + " |"]
    for row in df.itertuples(index=False):
        out.append("| " + " | ".join(str(v) for v in row) + " |")
    return "\n".join(out)


checks = []   # (check, result, detail)


def check(name, ok, detail=""):
    checks.append((name, "PASS" if ok else "FAIL", detail))
    return ok


# ---------------------------------------------------------------------------
# 1. ReEDS source
# ---------------------------------------------------------------------------
reeds_head = git("rev-parse", "HEAD").strip()
reeds_commit_full = git("rev-parse", f"{REEDS_COMMIT}^{{commit}}").strip()
is_ancestor = subprocess.run(
    ["git", "-C", str(REEDS_SRC), "merge-base", "--is-ancestor", REEDS_COMMIT, "HEAD"]
).returncode == 0
check("ReEDS source: commit 0c0ea27 exists and is an ancestor of HEAD", is_ancestor,
      f"HEAD {reeds_head[:7]}, 0c0ea27 = {reeds_commit_full}")

# ---------------------------------------------------------------------------
# 2. Case list
# ---------------------------------------------------------------------------
all_folders = sorted(p.name for p in RUNS_ROOT.iterdir() if p.is_dir())
expected = []
for batch, arms in ARMS.items():
    for arm, levels in arms.items():
        for lv in levels:
            expected.append((batch, arm, lv, f"{BATCHES[batch]}{level_label(lv)}_{arm}"))
expected_names = {e[3] for e in expected}

missing = [e[3] for e in expected if not (RUNS_ROOT / e[3]).is_dir()]
check("Every expected case folder exists", not missing,
      f"{len(expected)} expected; missing: {missing or 'none'}")

# Folders in the batch prefixes that are not used (D25, D27), listed for the record.
excluded = []
for f in all_folders:
    p = parse_case(f)
    if f in expected_names:
        continue
    if any(f.startswith(px) for px in BATCHES.values()) or f.startswith("UOC_"):
        excluded.append(f)
unparsed = [f for f in all_folders
            if any(f.startswith(px) for px in BATCHES.values()) and parse_case(f) is None]
check("Every folder with a study prefix has a readable case name", not unparsed,
      f"unreadable: {unparsed or 'none'}")

# Excluded folders must be only the arms that D25/D27 exclude.
EXCLUDED_ARMS = {"UON": {"gashigh"},                                  # D27
                  "UOS": {"gashigh", "gaslow", "pvadv", "smrcons"}}     # D27
bad_excl = []
for f in excluded:
    if f.startswith("UOC_20261021_"):                                   # D25
        continue
    p = parse_case(f)
    if p is None or p[2] not in EXCLUDED_ARMS.get(p[0], set()):
        bad_excl.append(f)
check("Excluded folders are only arms excluded by D25/D27", not bad_excl,
      f"{len(excluded)} folders excluded; unexpected: {bad_excl or 'none'}")

rows = []
for batch, arm, lv, name in expected:
    case_dir = RUNS_ROOT / name
    h5 = case_dir / "outputs" / "outputs.h5"
    sw = case_dir / "inputs_case" / "switches.csv"
    rows.append({
        "batch": batch, "arm": arm, "level": lv, "level_label": level_label(lv),
        "case": name,
        "role": "trunk" if lv == TRUNK_LEVEL else "branch",
        "baseline_case": f"{BATCHES[batch]}{level_label(0.0)}_{arm}",
        "outputs_h5": str(h5),
        "inputs_case": str(case_dir / "inputs_case"),
        "outputs_h5_exists": h5.is_file(),
        "outputs_h5_is_hdf5": h5.is_file() and h5py.is_hdf5(h5),
        "outputs_h5_bytes": h5.stat().st_size if h5.is_file() else 0,
        "switches_csv_exists": sw.is_file(),
    })
cases = pd.DataFrame(rows)

no_h5 = cases.loc[~cases.outputs_h5_exists, "case"].tolist()
check("Every case has outputs/outputs.h5", not no_h5, f"missing: {no_h5 or 'none'}")
not_h5 = cases.loc[cases.outputs_h5_exists & ~cases.outputs_h5_is_hdf5, "case"].tolist()
check("Every outputs.h5 is an HDF5 file (h5py.is_hdf5; contents not read)", not not_h5,
      f"not HDF5: {not_h5 or 'none'}")
no_sw = cases.loc[~cases.switches_csv_exists, "case"].tolist()
check("Every case has inputs_case/switches.csv", not no_sw, f"missing: {no_sw or 'none'}")

# Levels per batch and arm match the arm tables.
lv_detail, lv_ok = [], True
for (b, a), g in cases.groupby(["batch", "arm"], sort=False):
    got = sorted(g.level.tolist())
    want = sorted(ARMS[b][a])
    ok = got == want and (g.level == 0).sum() == 1 and (g.level == TRUNK_LEVEL).sum() == 1
    lv_ok &= ok
    lv_detail.append(f"{b} {a}: {len(got)} levels {got[0]:g} to {got[-1]:g}"
                     f"{'' if ok else ' MISMATCH'}")
check("Each batch and arm has the levels of its arm table, one 0 GW and one 0.5 GW case",
      lv_ok, "; ".join(lv_detail))
n_uon, n_uos = (cases.batch == "UON").sum(), (cases.batch == "UOS").sum()
check("Case counts: UON 78, UOS 21", n_uon == 78 and n_uos == 21,
      f"UON {n_uon}, UOS {n_uos}")

# ---------------------------------------------------------------------------
# 3. Switches of every case (D30)
# ---------------------------------------------------------------------------
sw_frames = []
for r in cases.itertuples():
    s = pd.read_csv(Path(r.inputs_case) / "switches.csv", header=None,
                    names=["switch", "value"], dtype=str, keep_default_na=False)
    s.insert(0, "case", r.case)
    s.insert(0, "level", r.level)
    s.insert(0, "arm", r.arm)
    s.insert(0, "batch", r.batch)
    sw_frames.append(s)
case_switches = pd.concat(sw_frames, ignore_index=True)

dups = case_switches.duplicated(["case", "switch"]).sum()
check("switches.csv has one row per switch in every case", dups == 0,
      f"duplicate rows: {dups}")
n_per_case = case_switches.groupby("case").size()
check("Every case has the same number of switches", n_per_case.nunique() == 1,
      f"switches per case: {sorted(n_per_case.unique().tolist())}")

sw = case_switches.set_index(["case", "switch"])["value"]

# Reference values of the arm switches: the batch's own `ref` 0 GW case (D2, D27, D31).
ref0 = {b: f"{BATCHES[b]}{level_label(0.0)}_ref" for b in BATCHES}
ref_arm_values = {b: {k: sw.get((ref0[b], k)) for k in ARM_SWITCH_NAMES} for b in BATCHES}

chk_rows = []
for r in cases.itertuples():
    for k, exp in SETUP_SWITCHES.items():
        chk_rows.append((r.batch, r.arm, r.level, r.case, k, "setup",
                         exp[r.batch], sw.get((r.case, k))))
    arm_sw = ARM_SWITCH[r.arm]
    for k in ARM_SWITCH_NAMES:
        if arm_sw and k == arm_sw[0]:
            exp, kind = arm_sw[1], "arm switch"
        elif k == "GSw_LoadProfiles":
            exp, kind = REF_LOAD_PROFILE, "setup (ref value)"
        else:
            exp, kind = ref_arm_values[r.batch][k], "same as batch ref 0 GW"
        chk_rows.append((r.batch, r.arm, r.level, r.case, k, kind, exp,
                         sw.get((r.case, k))))
switch_checks = pd.DataFrame(chk_rows, columns=["batch", "arm", "level", "case", "switch",
                                                "rule", "expected", "value"])
switch_checks["pass"] = switch_checks.expected == switch_checks.value

bad_setup = switch_checks[(~switch_checks["pass"]) & switch_checks.rule.str.startswith("setup")]
check("Setup switches match the data dictionary in every case", bad_setup.empty,
      f"{(switch_checks.rule.str.startswith('setup')).sum()} values checked; "
      f"{len(bad_setup)} differ")
bad_arm = switch_checks[(~switch_checks["pass"]) & ~switch_checks.rule.str.startswith("setup")]
check("Each arm differs from its batch `ref` only by its own arm switch, "
      "with the value in the arm table", bad_arm.empty,
      f"{(~switch_checks.rule.str.startswith('setup')).sum()} values checked; "
      f"{len(bad_arm)} differ")

# Information only: any other switch that differs from the batch ref 0 GW case.
other = case_switches[~case_switches.switch.isin(ARM_SWITCH_NAMES)].copy()
other["ref_value"] = [sw.get((ref0[b], k)) for b, k in zip(other.batch, other.switch)]
other_diff = other[other.value != other.ref_value]
other_summary = (other_diff.groupby(["batch", "switch", "ref_value", "value"])
                 .agg(n_cases=("case", "size"),
                      levels=("level", lambda x: sorted(set(x))))
                 .reset_index())

# ---------------------------------------------------------------------------
# 4. Zones, groups, years, dollar factor
# ---------------------------------------------------------------------------
hier = pd.read_csv(io.StringIO(git("show", f"{REEDS_COMMIT}:inputs/zones/z132/hierarchy.csv")))
west = hier.loc[hier.interconnect == "western", "r"].tolist()
check("z132 hierarchy at 0c0ea27 has 34 western zones, incl. p25, p26 and z28, "
      "no p28 or p30", len(west) == N_WEST_ZONES and {"p25", "p26", "z28"} <= set(west)
      and not {"p28", "p30"} & set(west), f"{len(west)} zones: {', '.join(west)}")

# Each case's own hierarchy has the same 34 zones.
hier_bad = []
for r in cases.itertuples():
    h = pd.read_csv(Path(r.inputs_case) / "hierarchy.csv")
    if sorted(h.iloc[:, 0].tolist()) != sorted(west):
        hier_bad.append(r.case)
check("inputs_case/hierarchy.csv of every case has the same 34 zones", not hier_bad,
      f"differ: {hier_bad or 'none'}")

missing_nb = [z for z in FOCUS + UTAH_REST + NEIGHBORS_EXPECTED if z not in west]
check("Fixed and expected group members are western zones", not missing_nb,
      f"not found: {missing_nb or 'none'}")

# Each case's solve years equal the data dictionary list.
yr_bad = []
for r in cases.itertuples():
    y = pd.read_csv(Path(r.inputs_case) / "modeledyears.csv").columns.astype(int).tolist()
    if y != SOLVE_YEARS:
        yr_bad.append((r.case, y))
check("inputs_case/modeledyears.csv of every case equals the solve years", not yr_bad,
      f"{SOLVE_YEARS}; differ: {yr_bad or 'none'}")

# Dollar factor: product of inflation rates 2005..2024 (D8).
infl = pd.read_csv(io.StringIO(git("show", f"{REEDS_COMMIT}:{DOLLAR_FACTOR_FILE}")))
prod = infl.loc[infl.t.between(2005, 2024), "inflation_rate"].prod()
check("Dollar factor 1.6563 = product of inflation_rate 2005 to 2024 "
      f"({DOLLAR_FACTOR_FILE} at 0c0ea27)", round(prod, 4) == DOLLAR_FACTOR,
      f"product = {prod:.6f}")

rest = [z for z in west if z not in FOCUS + UTAH_REST + NEIGHBORS_EXPECTED]
grp_rows = []
for b in BATCHES:
    for z in west:
        if z in FOCUS:
            g, src = "focus", "fixed"
        elif z in UTAH_REST:
            g, src = "utah_rest", "fixed"
        elif z in NEIGHBORS_EXPECTED:
            g, src = "neighbors", "expected; confirmed from tran_out in 02c"
        else:
            g, src = "rest_wecc", "34 zones minus the groups above"
        grp_rows.append((b, g, z, src))
        grp_rows.append((b, "wecc", z, "all 34 zones"))
region_groups = pd.DataFrame(grp_rows, columns=["batch", "group", "region", "source"])
region_groups = region_groups.sort_values(["batch", "group", "region"]).reset_index(drop=True)
one_group = region_groups[region_groups.group != "wecc"].groupby(["batch", "region"]).size()
check("Every zone is in exactly one of focus, utah_rest, neighbors, rest_wecc",
      (one_group == 1).all() and len(one_group) == 2 * N_WEST_ZONES,
      f"rest_wecc has {len(rest)} zones")

settings = pd.DataFrame([
    ("runs_root", str(RUNS_ROOT), "", "D25"),
    ("reeds_source", str(REEDS_SRC), "", "D30"),
    ("reeds_commit", reeds_commit_full, "", "D1, D30"),
    ("reeds_source_head", reeds_head, "", "D30"),
    ("solve_years", " ".join(map(str, SOLVE_YEARS)), "year",
     "data_dictionary.md Study terms; checked against inputs_case/modeledyears.csv"),
    ("post_plant_years", " ".join(map(str, POST_PLANT_YEARS)), "year",
     "data_dictionary.md Study terms"),
    ("system_cost_years", " ".join(map(str, SYSTEM_COST_YEARS)), "year", "D10"),
    ("trunk_gate_last_year", "2041", "year", "D4, D28"),
    ("trunk_level", f"{TRUNK_LEVEL:g}", "GW", "data_dictionary.md Study terms; D28"),
    ("shared_levels", "0 0.5 1.5 2.5", "GW", "D3"),
    ("dollar_factor_2004_to_2024", f"{DOLLAR_FACTOR}", "2024 USD per 2004 USD",
     f"D8; {DOLLAR_FACTOR_FILE} L93-L112 at 0c0ea27"),
    ("n_west_zones", str(N_WEST_ZONES), "", "inputs/zones/z132/hierarchy.csv at 0c0ea27"),
], columns=["setting", "value", "unit", "source"])

# ---------------------------------------------------------------------------
# 5. Write tables and the check report
# ---------------------------------------------------------------------------
OUT_DIR.mkdir(parents=True, exist_ok=True)
CHECK_REPORT.parent.mkdir(parents=True, exist_ok=True)

cases.to_csv(CONFIG_DIR / "study_cases.csv", index=False)
region_groups.to_csv(CONFIG_DIR / "region_groups.csv", index=False)
settings.to_csv(CONFIG_DIR / "study_settings.csv", index=False)
case_switches.to_csv(OUT_DIR / "case_switches.csv", index=False)
switch_checks.to_csv(OUT_DIR / "switch_checks.csv", index=False)

n_fail = sum(c[1] == "FAIL" for c in checks)
L = []
L.append("# Check report: 00_config (00a_study)\n")
L.append(f"Overall: **{'PASS' if n_fail == 0 else 'FAIL'}** "
         f"({len(checks) - n_fail} of {len(checks)} checks pass)\n")
L.append(f"- ReEDS source: `{REEDS_SRC}`, HEAD `{reeds_head[:7]}`; citations at "
         f"`{reeds_commit_full[:7]}` (D30)")
L.append(f"- Runs root: `{RUNS_ROOT}` (D25)\n")
L.append("## Counts\n")
L.append("| Batch | Arm | Cases | Levels (GW) | 0 GW case | Trunk (0.5 GW) |")
L.append("| --- | --- | --- | --- | --- | --- |")
for (b, a), g in cases.groupby(["batch", "arm"], sort=False):
    L.append(f"| {b} | {a} | {len(g)} | {g.level.min():g} to {g.level.max():g}, "
             f"step {g.level.sort_values().diff().dropna().unique()[0]:g} | "
             f"`{g.baseline_case.iloc[0]}` | `{g[g.role == 'trunk'].case.iloc[0]}` |")
L.append(f"\nTotal: {len(cases)} cases (UON {n_uon}, UOS {n_uos}). "
         f"Folders in `{RUNS_ROOT}`: {len(all_folders)}; excluded: {len(excluded)}.\n")
L.append("Excluded folders (D25, D27): " + ", ".join(f"`{f}`" for f in excluded) + "\n")
L.append("## Checks\n")
L.append("| # | Check | Result | Detail |")
L.append("| --- | --- | --- | --- |")
for i, (n, res, d) in enumerate(checks, 1):
    L.append(f"| {i} | {n} | {res} | {d} |")
if not bad_setup.empty or not bad_arm.empty:
    L.append("\n### Switch values that differ\n")
    L.append(md_table(pd.concat([bad_setup, bad_arm])))
L.append("\n## Setup switches (value in every case of the batch)\n")
L.append("| Switch | UON | UOS | cases.csv line at 0c0ea27 |")
L.append("| --- | --- | --- | --- |")
cites = {"GSw_Region": "L48", "GSw_ZoneSet": "L49", "GSw_GasCurve": "L142",
         "GSw_Clean_Air_Act": "L107", "GSw_Upgrades": "L348",
         "GSw_ForcePrescription": "L139", "demandscen": "L32", "GSw_PRM_CapCredit": "L259",
         "GSw_LoadProfiles": "L214", "ngscen": "L39", "plantchar_upv": "L28",
         "plantchar_nuclear_smr": "L23"}
for k in list(SETUP_SWITCHES) + ARM_SWITCH_NAMES:
    vals = {b: sorted(case_switches[(case_switches.batch == b) & (case_switches.switch == k)]
                      .groupby("arm").value.first().unique()) for b in BATCHES}
    L.append(f"| `{k}` | {', '.join(vals['UON'])} | {', '.join(vals['UOS'])} | {cites[k]} |")
L.append("\nArm switch values (the batch `ref` value applies to every other arm):\n")
L.append("| Arm | Switch | Value |")
L.append("| --- | --- | --- |")
for a, v in ARM_SWITCH.items():
    L.append(f"| {a} | {v[0] if v else '(none)'} | {v[1] if v else ''} |")
L.append("\n## Other switches that differ from the batch `ref` 0 GW case (information, not a gate)\n")
if other_summary.empty:
    L.append("None.")
else:
    for r in other_summary.itertuples():
        L.append(f"- {r.batch} `{r.switch}`: {r.value} in {r.n_cases} cases "
                 f"(levels {', '.join(f'{x:g}' for x in r.levels)} GW), "
                 f"{r.ref_value} in `ref` 0 GW.")
L.append("\n## Region groups (per batch; same in both)\n")
for g in ["focus", "utah_rest", "neighbors", "rest_wecc", "wecc"]:
    zs = region_groups[(region_groups.batch == "UON") & (region_groups.group == g)].region
    L.append(f"- `{g}` ({len(zs)}): {', '.join(zs)}")
L.append("\n## Settings\n")
L.append(md_table(settings))
L.append("\n## Files written\n")
for p in [CONFIG_DIR / "study_cases.csv", CONFIG_DIR / "region_groups.csv",
          CONFIG_DIR / "study_settings.csv", OUT_DIR / "case_switches.csv",
          OUT_DIR / "switch_checks.csv"]:
    L.append(f"- `{p.relative_to(REPO).as_posix()}`")
L.append("\nNo check figures in this stage.")
CHECK_REPORT.write_text("\n".join(L) + "\n", encoding="utf-8")

print(CHECK_REPORT.read_text(encoding="utf-8"))
sys.exit(1 if n_fail else 0)
