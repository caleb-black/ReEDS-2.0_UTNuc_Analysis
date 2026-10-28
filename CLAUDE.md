# CLAUDE.md — ReEDS 2.0 Scenario Analysis

## What this repo is
Post-processing, analysis, and interpretation of ReEDS 2.0 model runs across a set of
scenario assumptions. ReEDS itself is upstream, archived, and treated as read-only. This
repo does not modify the model.

## Source of truth
- Model behavior, inputs, and outputs are defined ONLY by the ReEDS documentation and code
  history at ReEDS commit 0c0ea27 (github.com/ReEDS-Model/ReEDS, branch ce/used, no local
  edits): docs/, README, changelog, git log.
  Report code: reeds/core/terminus/report.gms, report_params.csv, report_calcs.py.
- Every claim about the model cites a file and line at 0c0ea27.
- Do not use outside papers or general knowledge about ReEDS to explain model behavior.
  If the docs don't cover something, say so. Don't guess.
- Analysis decisions and their rationale live in `docs/plan.md` and `docs/decisions.md`.
  Read those before proposing changes.

## Repo structure (linear order of operations)
Each numbered stage reads only from earlier stages. A reader should be able to follow the
analysis top to bottom.

```
00_config/        # scenario list, paths, shared settings
01_ingest/        # load raw ReEDS outputs; no transformation
02_clean/         # validation, unit harmonization, filtering
03_derive/        # computed metrics
04_analyze/       # comparisons across scenarios
05_visualize/     # figures and tables
outputs/          # generated artifacts (git-ignored or LFS)
docs/             # plan.md, decisions.md, data_dictionary.md, how_to_run.md
notes/            # agent proposals, analysis notes, figure text (D24)
archive/          # superseded scripts awaiting deletion (see cleanup rules)
```
Script names per stage are listed in `docs/plan.md`.

## Conventions
- Script names carry their stage prefix and order: `02_clean/02a_check_units.py`.
- One script, one job. No script reaches backward into a later stage.
- Raw ReEDS run outputs are never committed. Reference them by path in `00_config/`.
- Python, in the conda `reeds` environment from `environment.yml` at 0c0ea27, without the
  GAMS packages (`gamsapi`, `gamspy_base`). Scripts read `outputs.h5` with `h5py`, no GDX (D18, D29).
- Run the pipeline stage by stage, in the order of `docs/plan.md`. Steps: `docs/how_to_run.md`.

## Cleanup rules for legacy scripts
- Before deleting anything, record what it did and where that function now lives
  in `docs/decisions.md`.
- Move superseded scripts to `archive/` first. Delete them only after the replacement
  reproduces their outputs.

## Scenarios
- Arms, levels, baselines, groups and metrics: `docs/data_dictionary.md`.
- Run folders: listed in `00_config/` (stage 00a).
- Decisions D1 to D33: `docs/decisions.md`. Do not change a decision in code; propose a
  new decision entry instead.
- Compare only within an arm, against that arm's own 0 GW case in the same batch (D2). Never mix UON and UOS (D26).

## Working rules
- Follow `docs/plan.md` stage by stage. Stop after each stage and show the check report.
- A failed gate (trunk gate, setup checks, neighbor list) stops the pipeline. Report it
  and wait. Never edit data to make a check pass.
- Keep tables long between stages. Wide tables only in 05_visualize.
- Convert 2004 USD to 2024 USD (x 1.6563) only in 03_derive.

## Agent team
- Five agents with fixed bounds: `docs/plan.md`, "Agent team" (D20 to D23). Files: `.claude/agents/`.
- Caleb makes every analysis choice and does every merge.
- The Verifier never reads the Builder's code and sends only results and gaps.

## Git
- Branch per stage or feature. Commit messages reference the stage (`[02_clean] ...`).
- Outputs are not committed for now. Decide on Git LFS for final figures later.
