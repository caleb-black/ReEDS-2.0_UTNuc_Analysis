"""derive_common: shared helpers for the 03_derive scripts (not a stage step).

Holds only paths, readers and report helpers that every 03 script needs, so
that each 03 script stays one job (plan rule 1). It reads only from earlier
stages: 00_config/ and outputs/01_ingest/ (D36). It never reads outputs of
stage 03 (plan rule 2).

- read_key(key, where, columns): one stage 01 per-key file, filtered on read
  (HDFStore table format, key `data`, D33, D36). ReEDS column names kept.
- DOLLAR: 2004 USD -> 2024 USD factor (D8), read from 00_config/study_settings.csv.
  Stage 03 is the only place where it is applied (plan rule 6).
- peak_blocks(), peak_rows(): the three highest distinct energy prices per region
  and year and their blocks (D9, D37a).
- tech_map(), tech_style(): ReEDS technology groups and colors (D37g).
"""

from pathlib import Path

import pandas as pd

REPO = Path(__file__).resolve().parents[1]
CONFIG_DIR = REPO / "00_config"
IN_OUT = REPO / "outputs" / "01_ingest" / "outputs"
IN_INP = REPO / "outputs" / "01_ingest" / "inputs"
UNITS_CSV = REPO / "outputs" / "02_clean" / "units.csv"
OUT_DIR = REPO / "outputs" / "03_derive"
FIG_DIR = OUT_DIR / "figures"
CHECK_REPORT = REPO / "outputs" / "checks" / "03_derive.md"
REPORT_TITLE = "# Check report: 03_derive\n\n"

CASE_COLS = ["batch", "arm", "level", "case"]
SAMPLE_CASES = ["UON_20261022_0G_ref", "UON_20261022_3G_ref", "UOS_20261021_2p5G_ref"]  # D23, D31
FOCUS = "p25"


def settings():
    s = pd.read_csv(CONFIG_DIR / "study_settings.csv")
    return dict(zip(s["setting"], s["value"]))


SETTINGS = settings()
DOLLAR = float(SETTINGS["dollar_factor_2004_to_2024"])                   # D8
POST_PLANT_YEARS = [int(x) for x in SETTINGS["post_plant_years"].split()]
SYSTEM_COST_YEARS = [int(x) for x in SETTINGS["system_cost_years"].split()]  # D10


def cases():
    """All cases of 00_config/study_cases.csv, in file order."""
    return pd.read_csv(CONFIG_DIR / "study_cases.csv")


def region_groups():
    return pd.read_csv(CONFIG_DIR / "region_groups.csv")


def units():
    return pd.read_csv(UNITS_CSV, dtype=str).fillna("")


def unit_of(key, type_value=""):
    """Unit from the 02d lookup (D36); 'not stated' where the lookup has none."""
    u = units()
    rows = u[(u["key"] == key) & (u["type"] == type_value)]
    if rows.empty:
        rows = u[(u["key"] == key) & (u["type"] == "")]
    return rows["unit"].iloc[0] if len(rows) else "not stated"


def read_key(key, where=None, columns=None):
    """Read one stage 01 key, filtered on read (D36). No copy is written."""
    return pd.read_hdf(IN_OUT / f"{key}.h5", "data", where=where, columns=columns)


def read_numhours(where=None):
    return pd.read_hdf(IN_INP / "numhours.h5", "data", where=where)


def peak_blocks(price, n=3, keys=("r", "t")):
    """Blocks at the n highest distinct energy prices per keys (D9, D37a).

    price: rows with columns case, r, h, t, price. peak_rank = rank of the
    block's price among the distinct prices of that region-year (1 = highest);
    every block at a ranked price is returned. n_blocks_at_price = number of
    blocks of that region-year at exactly that price.
    """
    keys = ["case", *keys]
    p = price.copy()
    p["peak_rank"] = (p.groupby(keys)["price"].rank(method="dense", ascending=False)
                      .astype("int16"))
    p["n_blocks_at_price"] = p.groupby(keys + ["price"])["h"].transform("size").astype("int16")
    return p[p["peak_rank"] <= n].sort_values(keys + ["peak_rank", "h"])


def peak_rows(blocks, keys=("r", "t")):
    """One row per ranked price: h = first block by name, h_all = all blocks (';')."""
    keys = ["case", *keys]
    g = blocks.sort_values("h").groupby(keys + ["peak_rank"], sort=False)
    out = g.agg(price=("price", "first"), h=("h", "first"),
                h_all=("h", lambda s: ";".join(s)),
                n_blocks_at_price=("n_blocks_at_price", "first")).reset_index()
    return out


def _git_show(path):
    import subprocess
    return subprocess.run(["git", "-C", SETTINGS["reeds_source"], "show",
                           f"{SETTINGS['reeds_commit']}:{path}"],
                          capture_output=True, check=True).stdout


def tech_map():
    """ReEDS tech_map.csv at 0c0ea27 (D37g), as (compiled regex, display) pairs.

    Applied as bokehpivot does (`reeds_bokeh.py` L414-L432 at 0c0ea27):
    lowercase value, '^raw$' with '*' -> '.*', first match wins, no match keeps
    the original name.
    """
    import io
    import re
    m = pd.read_csv(io.BytesIO(_git_show("postprocessing/bokehpivot/in/reeds2/tech_map.csv")),
                    comment=None)
    m = m.dropna(subset=["raw", "display"])
    m = m[~m["raw"].astype(str).str.startswith("#")]
    pats = [(re.compile("^" + str(r).replace("*", ".*") + "$"), d)
            for r, d in zip(m["raw"], m["display"])]

    def f(val):
        v = str(val).lower()
        for pat, d in pats:
            if pat.match(v):
                return d
        return val
    f.matched = lambda val: any(pat.match(str(val).lower()) for pat, _ in pats)
    return f


def tech_style():
    """ReEDS tech_style.csv at 0c0ea27 (D37g): display -> color, in file order."""
    import io
    st = pd.read_csv(io.BytesIO(_git_show("postprocessing/bokehpivot/in/reeds2/tech_style.csv")))
    return dict(zip(st["order"], st["color"]))


def md_table(df, floatfmt="{:,.4g}"):
    cols = list(df.columns)
    out = ["| " + " | ".join(str(c) for c in cols) + " |",
           "| " + " | ".join("---" for _ in cols) + " |"]
    for row in df.itertuples(index=False):
        cells = [floatfmt.format(v) if isinstance(v, float) else str(v) for v in row]
        out.append("| " + " | ".join(cells) + " |")
    return "\n".join(out)


def write_section(section, text, path=CHECK_REPORT, title=REPORT_TITLE):
    """Replace only this script's section of the stage check report."""
    path.parent.mkdir(parents=True, exist_ok=True)
    start, end = f"<!-- {section} start -->", f"<!-- {section} end -->"
    block = f"{start}\n{text.rstrip()}\n{end}\n"
    old = path.read_text(encoding="utf-8") if path.exists() else title
    if start in old and end in old:
        pre, rest = old.split(start, 1)
        new = pre + block + rest.split(end, 1)[1].lstrip("\n")
    else:
        new = old.rstrip("\n") + "\n\n" + block
    path.write_text(new, encoding="utf-8")


def write_long(df, name, big=False):
    """Write a long table to outputs/03_derive/ (CSV, or HDFStore table if big)."""
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    if big:
        path = OUT_DIR / f"{name}.h5"
        dc = [c for c in df.columns if c not in ("value",)]
        df.to_hdf(path, key="data", mode="w", format="table", data_columns=dc,
                  complevel=9, complib="blosc:zstd", index=False)
    else:
        path = OUT_DIR / f"{name}.csv"
        df.to_csv(path, index=False)
    return path


def rel(path):
    return Path(path).resolve().relative_to(REPO).as_posix()
