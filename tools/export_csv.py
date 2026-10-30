"""CSV copies of the analysis tables, for reading outside the pipeline (D49).

Reads every HDFStore table under outputs/01_ingest and outputs/03_derive and writes
the same rows and columns as CSV under outputs/csv/. The pipeline itself keeps
reading the .h5 files (D33); these copies are never read by any stage.

Split rule: one file per batch and arm. If that would pass Excel's row limit, one
file per case instead, in a folder per batch and arm.

    outputs/csv/<same path as the .h5, without .h5>/<batch>_<arm>.csv
    outputs/csv/<same path as the .h5, without .h5>/<batch>_<arm>/<case>.csv
e.g. outputs/csv/01_ingest/outputs/gen_h/UON_ref/UON_20261022_0G_ref.csv

Tables over 5 million rows (gen_h, reqt_quant, reqt_price, tran_util_h_rep,
reduced_cost) are skipped unless named in --tables; read them with a script.

outputs/csv/index.csv lists every file with its rows and columns. A table is
skipped when its source .h5 has not changed since the last export (use --force
to redo it).

Usage:
    python tools/export_csv.py                    # all tables
    python tools/export_csv.py --tables gen_h tran_flow_rep_ann
    python tools/export_csv.py --force
"""
import argparse
import shutil
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
SRC_DIRS = [ROOT / 'outputs' / '01_ingest', ROOT / 'outputs' / '03_derive']
OUT = ROOT / 'outputs' / 'csv'
INDEX = OUT / 'index.csv'
MAX_ROWS = 1_000_000  # Excel holds 1,048,576 rows per sheet
LARGE_ROWS = 5_000_000  # tables above this are skipped unless named in --tables
INDEX_COLS = ['file', 'stage', 'table', 'batch', 'arm', 'case', 'rows', 'columns', 'source', 'source_tag']


def source_tag(p):
    s = p.stat()
    return f'{s.st_size}_{int(s.st_mtime)}'


def export_table(h5, old_index, force=False):
    rel = h5.relative_to(ROOT / 'outputs').with_suffix('')
    stage, table = rel.parts[0], h5.stem
    tag = source_tag(h5)
    prev = old_index.iloc[0:0] if force else old_index[(old_index.source == h5.relative_to(ROOT).as_posix()) & (old_index.source_tag == tag)]
    if len(prev):
        return prev, 'skipped (unchanged)'
    dest = OUT / rel
    if dest.exists():
        shutil.rmtree(dest)
    dest.mkdir(parents=True)
    rows = []
    with pd.HDFStore(h5, 'r') as s:
        # Rows of one case sit in runs (stage 01 writes case by case), so read each run by
        # row position: much faster than a where= query, which scans the whole table.
        case = s.select_column('data', 'case').astype(str).to_numpy()
        starts = [0] + (np.flatnonzero(case[1:] != case[:-1]) + 1).tolist()
        runs = pd.DataFrame({'case': case[starts], 'start': starts, 'stop': starts[1:] + [len(case)]})
        for c in ['batch', 'arm']:
            runs[c] = s.select_column('data', c).astype(str).to_numpy()[starts]
        read = lambda r: pd.concat([s.select('data', start=int(a), stop=int(b)) for a, b in zip(r.start, r.stop)])
        for (batch, arm), r in runs.groupby(['batch', 'arm']):
            if (r.stop - r.start).sum() <= MAX_ROWS:
                parts = [(dest / f'{batch}_{arm}.csv', r)]
            else:
                sub = dest / f'{batch}_{arm}'
                sub.mkdir()
                parts = [(sub / f'{c}.csv', rc) for c, rc in r.groupby('case')]
            for path, rr in parts:
                g = read(rr)
                g.to_csv(path, index=False)
                rows.append({'file': path.relative_to(OUT).as_posix(), 'stage': stage, 'table': table,
                             'batch': batch, 'arm': arm,
                             'case': g['case'].iloc[0] if g['case'].nunique() == 1 else 'all levels',
                             'rows': len(g), 'columns': ' '.join(g.columns),
                             'source': h5.relative_to(ROOT).as_posix(), 'source_tag': tag})
    return pd.DataFrame(rows), f'{len(rows)} files'


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument('--tables', nargs='*', help='table names (file stems), default all')
    ap.add_argument('--force', action='store_true', help='export even if the source is unchanged')
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    old = pd.read_csv(INDEX) if INDEX.exists() else pd.DataFrame(columns=INDEX_COLS)
    old['source_tag'] = old['source_tag'].astype(str)
    sources = sorted(p for d in SRC_DIRS for p in d.rglob('*.h5'))
    if a.tables:
        sources = [p for p in sources if p.stem in a.tables]
    else:
        big = []
        for p in sources:
            with pd.HDFStore(p, 'r') as st:
                if st.get_storer('data').nrows > LARGE_ROWS:
                    big.append(p)
        for p in big:
            print(f'{p.relative_to(ROOT)}: skipped (large; read it with a script, see docs/how_to_run.md)')
        sources = [p for p in sources if p not in big]
    done = {}
    for h5 in sources:
        idx, msg = export_table(h5, old, a.force)
        print(f'{h5.relative_to(ROOT)}: {msg}', flush=True)
        done[h5.relative_to(ROOT).as_posix()] = idx
        keep = old[~old.source.isin(done)]
        out = pd.concat([keep] + list(done.values()), ignore_index=True).sort_values('file')
        out['rows'] = out['rows'].astype(int)
        out[INDEX_COLS].to_csv(INDEX, index=False)
    print(f'index: {INDEX.relative_to(ROOT)}')


if __name__ == '__main__':
    main()
