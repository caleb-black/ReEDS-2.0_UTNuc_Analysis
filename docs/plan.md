# p25 nuclear study: implementation plan

Oct 28, 2026 · Caleb

This plan tells Claude Code what to build, stage by stage. Definitions are in `docs/data_dictionary.md`. Decisions D1 to D31 are in `docs/decisions.md`. This plan does not repeat them.

## Rules for every stage

Each stage ends with a check that you look at. The next stage starts only after you approve it.

1. **One script, one job.** Name each script with its stage and order, for example `02_clean/02a_trunk_gate`.
2. **Read only from earlier stages.** A script never reads from a later stage or from its own stage's outputs.
3. **Data stays long.** Every table between stages has one row per value, with these columns: batch, arm, level, case, region or group, year, metric, sub-key (tech, block, line), value, unit. Wide tables are made only in stage 05 (D11).
4. **Each stage writes a check report.** A short file with counts, pass or fail for each check, and the path of each check figure. Claude Code shows you this report before it moves on.
5. **Stop on failure.** A failed gate (D4, setup checks, neighbor list) stops the pipeline. Claude Code reports the failure and waits for you. It does not change the data to make a check pass.
6. **Dollars change only once.** Convert 2004 USD to 2024 USD (factor 1.6563, D8) in stage 03. Earlier stages keep model units.
7. **No new model claims in code.** If a script needs a fact about ReEDS that `docs/data_dictionary.md` does not have, Claude Code asks you and cites the file and line at `0c0ea27`.

## Stages 00 to 05

There are six stages. The two gates that can stop the work are in stage 02.

### 00\_config: write down the study

- **00a\_study** — Lists every case of UON and UOS (D25, D27): folder name, batch, arm, level, path to `<case>/outputs/outputs.h5`. Records the setup switches of every case from `inputs_case/switches.csv` (D30), the ReEDS source path and HEAD. Also lists the groups, the 34 zones, report years, dollar factor.
  - In: `D:\ReEDS\runs` (path set once). Out: `study_cases`, `case_switches` and `region_groups` tables.
  - **You check:** one table of all cases. Each batch and arm has the levels in the arm tables of `docs/data_dictionary.md`. No case is missing. Each case has `outputs/outputs.h5`. Setup switches match the data dictionary, except the arm switch.

### 01\_ingest: copy raw files, change nothing

- **01a\_load\_outputs** — Reads each key in "Outputs read from each run" from `outputs.h5` for every case (D29). Renames the `*` columns by position (type, subtype, r, h, t). Adds batch, arm, level, case. Lists absent keys (an absent key is an empty table).
- **01b\_load\_inputs** — Reads `inputs_case/rep/numhours.csv` for every case. (`cost_vom`, `heat_rate`, `fuel_price` are `outputs.h5` keys, read in 01a.)
  - Out: one long table per output key, with UON and UOS rows kept apart by `batch` (D26).
  - **You check:** row count per case per file. Cases of one arm have similar counts. A missing file is listed by name.

### 02\_clean: prove the runs are fit to use

- **02a\_trunk\_gate** (D4) — (D28) Within each batch, each branch equals its trunk (0.5 GW case of the same arm) for every year up to 2041, in every output. **Stops on failure.**
- **02b\_setup\_checks** — p25 coal is near zero from 2044. p25 nuclear equals the level in each case. Where the model also builds nuclear on its own, prescribed and endogenous nuclear are shown apart. The 0 GW cases have no new p25 nuclear.
- **02c\_neighbor\_list** (D7) — In each batch, builds the neighbor list from `tran_out` (that batch's 0 GW `ref`, both columns; D31). Compares it with the expected list (p12, p16, p21, p27, p31, p33, z28). **Stops if they differ.**
- **02d\_units** — Confirms units per file against `docs/data_dictionary.md`. Confirms all solve years are present.
  - **You check:** the gate report (pass or fail per case and file), and one plot of p25 capacity by technology over time, one panel per case.

### 03\_derive: one value per region, year, case

- **03a\_prices** (D6, D9) — Per region and year: average energy price, average all-in price, peak price with block name and hours, 2nd and 3rd peaks, peak/average ratio. Also the group price per block (D14).
- **03b\_system\_cost** (D10) — Sum of `inv_*` and `op_*` from `systemcost_ba_bulk_ew` for 2044, 2047, 2050.
- **03c\_trade** — Net imports; expenditure flows by type; new lines.
- **03d\_capacity\_generation** — Capacity and generation by technology, with share of the regional total.
- **03e\_price\_setter** (D12) — Per block: highest running cost of the techs that run; gap to the price; price-setter or "set by something else".
- **03f\_line\_use** (D9) — Line use in each peak block, from `tran_util_h_rep`.
  - **You check:** a map of average price for the 0 GW `ref` case of each batch. Compare it by eye with the bokehpivot "Energy Price Final BA Map" of the same run. Also the plot of all price gaps from 03e.

### 04\_analyze: groups and differences

- **04a\_groups** — Aggregates every metric to the five groups, with the rule in the metrics table of `docs/data_dictionary.md`.
- **04b\_diff** (D2, D11) — Diff (and % where D11 says) against the arm's own 0 GW case in the same batch.
- **04c\_slopes** (D3) — Slopes on the shared levels only.
- **04d\_peak\_drilldown** (D14) — For each group peak block: one row per member region.
- **04e\_neighbor\_table** — Price change for each neighbor of p25 (sanity check).
  - **You check:** Diff against level, one line per group, one panel per arm, one figure per batch (D26). Every value before 2044 is zero. Changes are smooth and mostly in one direction; anything else gets a written note.

### 05\_visualize: final figures and tables

- **05a\_group\_figures** — Primary results per group: price, peak, ratio, cost.
- **05b\_region\_maps** (D15) — Maps of average price, Diff in price, Diff in system cost; `expenditure_flow` map next to the cost map. Shapes from `inputs/shapefiles/US_PCA/` (merge p28 and p30 into z28).
- **05c\_price\_setter\_figures** — Share of blocks per price-setter type, by level.
- **05d\_wide\_tables** — One wide CSV per metric and batch: arm, region or group, year, value per level, Diff per level.
  - **You check:** each figure has a one-line statement under it that you agree with.

## SMR value and the cost of prescribing it

Two questions: what is the prescribed SMR worth to the system, and what does it cost to force it in? `valnew` answers the first. The dual of the prescription constraint answers the second, but that dual is not in the normal outputs at `0c0ea27`.

**What the files are**

- `valnew` is not a dual. It is the value of new builds at marginal prices: `val_load` (generation times the energy price), `val_resmarg` (generation in stress blocks times the reserve margin price), `val_opres`, `val_rps`, plus `MW` and `MWh` of the new build (`report.gms` L1043-1130; `report_params.csv` L231, 2004 $). There are also `_sys` versions at system prices, and `benchmark` rows for each region.
- The docs define net value as value minus cost, with NVOE in $/MWh and NVOC in $/kW-yr. They also say that net value "is related to" the reduced cost of the linear program (`model_documentation.md` L3333-3354).
- The prescription constraint is `eq_forceprescription_power` (`reeds/core/setup/c_model.gms` L930-951). It says new investment = prescribed amount + `EXTRA_PRESCRIP`, and `EXTRA_PRESCRIP` is a free slack. INFERENCE: so the prescribed amount is a minimum. The model can build more for free in the same equation.
- `report.gms` never reads the marginal of this equation. It is not in `results.gdx` (`report_data.csv`) or in `report_params.csv`. `dump_alldata` (`cases.csv` L368, default 0) writes `alldata.gdx`, which holds the full model data, but for the final solve year only. The prescription binds in 2044. **Not covered in the documentation:** whether any standard output holds the 2044 dual.
- `reduced_cost` (`report_params.csv` L144; `report.gms` L1868-1870) is the reduced cost of each investment option, in 2004 $/kW, undiscounted.

**Proposed analysis (stages 03 and 04)**

- **03g\_smr\_value** — For `Nuclear-SMR` in p25, each case and year from 2044: `val_load`, `val_resmarg`, `val_opres`, `val_rps` from `valnew`. Report them per kW-yr and per MWh. Show the value by service as stacked bars by level. If any case builds other nuclear types in p25, show them apart.
- **03h\_smr\_cost\_gap** — Net value = value minus the SMR's annual cost. INFERENCE: for a forced build, a negative net value is the part the system pays to force it in. Cost side (D19): `lcoe_built` for `Nuclear-SMR` in p25 (`report_params.csv` L116; `report.gms` L264). Net value of energy = value per MWh (`valnew` value / `valnew` MWh) minus `lcoe_built`, as the NVOE in `model_documentation.md` L3333-3354.
- **03i\_smr\_reduced\_cost** — In each 0 GW case: the `reduced_cost` of `INV` for `Nuclear-SMR` in p25 in 2044. INFERENCE: this is how far, in $/kW, the SMR is from being built by the model's own choice. In the prescribed cases the investment is basic, so its reduced cost is about zero and tells us nothing.
- **04f\_forcing\_cost\_curve** — A proxy for the dual, from outputs you already have: the change in system cost (D10) per GW between neighboring levels (0 to 0.5, 0.5 to 1, ...). INFERENCE: a shadow price is the change in the objective for one more unit on the right side of the constraint (`model_documentation.md` L3214-3220). The finite difference between levels is the average of that value over the step. Compare it with 03h.
  - **You check:** one figure per arm with three lines against level: the forcing-cost curve, minus the net value per kW (03h), and the 0 GW reduced cost (03i, one point). If the model is consistent, the three should tell the same story.

## Agent team

Five agents do the work. You make every analysis choice and do every merge (D20). Every agent works under `CLAUDE.md` and reads only what its role needs (D23).

| Agent | Does | May write | May not |
| --- | --- | --- | --- |
| Builder | Writes the scripts for one stage, on that stage's branch, as this plan says. Fixes what the Verifier and the Reviewer report. | Scripts in `00_config/` to `05_visualize/`. | Edit `docs/`. Make an analysis choice that is not in `docs/decisions.md`. |
| Verifier | Recomputes the check values from the raw run outputs (`outputs.h5`) with its own calculation. Does not read the Builder's code (D21). | Its own check files, outside the pipeline. | Read the Builder's scripts. Send its method to the Builder. |
| Reviewer | Checks each PR against this plan, `CLAUDE.md` and `docs/decisions.md`. Checks each new model claim against a file and line at `0c0ea27`, or marks it "Not covered in the documentation". | Review comments. New rows in `docs/checked_citations.md`. | Merge. Change scripts. |
| Cost-driver analyst | From stage 04: proposes how to split each change in system cost into generation, capacity and transmission parts, and links them to price changes. Explains the results. All reasoning beyond the docs is marked INFERENCE (D22). | Proposed decision entries for you. Notes on results. | Write pipeline scripts. Apply a method that you have not approved. |
| Explainer | From stage 04: writes the plain-language text for each stage and figure, from the outputs and `docs/data_dictionary.md` only. | Text under each figure; the summary of each stage. | Add a claim that is not in the outputs or the docs. |

**Order of work in each stage** (commands in `docs/how_to_run.md`)

1. The Builder writes the stage scripts and runs them. Each stage writes its check report to `outputs/checks/<stage>.md` (D24).
2. The Verifier recomputes the check values for the sample cases: UON `ref` 0 GW, UON `ref` 3 GW, UOS `ref` 2.5 GW (D23, D31). The trunk gate script already compares every case.
3. The Verifier tells the Builder only what is different: the metric, the case, both values and the gap. It reports any relative gap above 1e-4 (D21).
4. The Builder has one try to fix each gap. If a gap stays, it goes to you with both values. You check the logic.
5. The Reviewer checks the PR. A failed check blocks the PR.
6. You read the check report, the Verifier result and the review, and you merge or ask for changes.

**New methods (stage 04 and later).** The Cost-driver analyst proposes a method as a new decision entry. After you approve it, the Builder writes it as a `04_analyze` script. The Verifier checks it, as for every other script. Then the analyst reads the outputs and explains them (D22).

**Stop rule.** Any agent that meets a choice that is not in `docs/decisions.md` stops and asks you. No agent changes data to make a check pass.

**Keep credit use low (D23)**

- Five agents, not six: the Reviewer also does the source check.
- The Cost-driver analyst and the Explainer start at stage 04.
- The Verifier checks a fixed sample of three cases, not all cases.
- Each citation is checked once and listed in `docs/checked_citations.md`. The Reviewer checks only new citations.
- Each agent reads only its part of this plan and the stage check report, not the raw data or the thread history.
- Use smaller models for the Verifier and the Reviewer checklist. Use the larger model for the Builder and the analyst.
- One fix round between the Verifier and the Builder. After that, the gap comes to you.

## Git

Commit the scripts, the config and the docs. Do not commit run data or generated outputs. The folder layout is the one in `CLAUDE.md`.

| Path | Committed? | Why |
| --- | --- | --- |
| `00_config/` to `05_visualize/` (scripts) | Yes | The analysis itself. |
| `00_config/` study tables (cases, groups) | Yes | Small, written by hand, needed to rerun. |
| `docs/plan.md`, `docs/decisions.md`, `docs/data_dictionary.md`, `docs/checked_citations.md` | Yes | The plan, the data dictionary and the decision log. |
| Raw ReEDS run folders | No | Large; referenced by path only (`CLAUDE.md`). |
| `outputs/` (tables, figures) | No, for now | Generated. Can be rebuilt from scripts. Decide later if final figures go in Git LFS. |
| Check reports from each stage | No | Generated; you read them, they are not the record. |

**Branches.** One branch per stage, as `CLAUDE.md` says. Each commit message starts with the stage, for example `[02_clean] add trunk gate`. Merge a stage branch only after you approved its check.

## CLAUDE.md

The working rules from this plan are also in `CLAUDE.md` (source of truth, scenarios, working rules, agent team, Git).

## On hold and open items

- [ ] **On hold (Caleb):** the group-to-group trade table and the cost views A, B, C (see `docs/decisions.md`, On hold). Stage 03c builds only net imports, flows and new lines until this is decided.
- [x] Decided (D18): Python with the conda `reeds` environment from `environment.yml` at `0c0ea27`, without the GAMS packages (`gamsapi`, `gamspy_base`). Note: reading any GDX file (`gdxpds`) needs the GAMS API. So with no GAMS, the scripts do not read GDX files. Outputs are read from `outputs.h5` with `h5py` (D29).
- [x] Checked: `inputs/shapefiles/US_PCA/` has shapes for `p28` and `p30`, and none for `z28`. So 05b must merge the two shapes into `z28`.
- [ ] **Open:** units of `cost_vom`, `heat_rate`, `fuel_price` (check when the files are collected).
- [x] Decided (27 Oct): Caleb adds the marginal of `eq_forceprescription_power` as an output file when collecting the files. Add a script **03j\_prescription\_dual** that reads it for `Nuclear-SMR` in p25 in 2044. Keep 04f (forcing-cost curve) as a cross-check against it. Columns, units and sign: check when the file arrives.
- [x] Decided (D19): the SMR net value uses `lcoe_built`. Add `lcoe_built.csv` to the files to collect.
