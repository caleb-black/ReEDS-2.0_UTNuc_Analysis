# CLAUDE.md — ReEDS 2.0 Scenario Analysis

## What this repo is
Post-processing, analysis, and interpretation of ReEDS 2.0 model runs across a set of
scenario assumptions. ReEDS itself is upstream, archived, and treated as read-only. This
repo does not modify the model.

## Source of truth
- Model behavior, inputs, and outputs are defined ONLY by the ReEDS documentation and code
  history in `<path/to/reeds>` (docs/, README, changelog, git log).
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
docs/             # plan.md, decisions.md, data_dictionary.md
archive/          # superseded scripts awaiting deletion (see cleanup rules)
```
<!-- TODO: adjust stage names to match the master plan once finalized -->

## Conventions
- Script names carry their stage prefix and order: `02_clean/02a_check_units.py`.
- One script, one job. No script reaches backward into a later stage.
- Raw ReEDS run outputs are never committed. Reference them by path in `00_config/`.
- <!-- TODO: language, environment manager, how to run the full pipeline -->

## Cleanup rules for legacy scripts
- Before deleting anything, record what it did and where that function now lives
  in `docs/decisions.md`.
- Move superseded scripts to `archive/` first. Delete them only after the replacement
  reproduces their outputs.

## Scenarios
<!-- TODO: list each scenario, its key assumptions, and its run folder -->

## Git
- Branch per stage or feature. Commit messages reference the stage (`[02_clean] ...`).
- <!-- TODO: LFS / output handling decision -->
