# How to run the analysis with Claude Code

This guide shows how to run one stage of `docs/plan.md` on your computer, from the first branch to the merge. The agents and their bounds are in `docs/plan.md`, "Agent team" (D20 to D23). The setup choices in this guide are D24.

You do three things in each stage. You start each agent. You pass the Verifier's gap list to the Builder. You merge. The agents do the rest.

## 1. One-time setup

1. Clone this repo, for example to `C:\Users\caleb\ReEDS-2.0_UTNuc_Analysis`.
2. The ReEDS source is at `C:\Users\caleb\ReEDS` (HEAD is later than `0c0ea27`). The Reviewer checks citations with `git show 0c0ea27:<path>` there (D30).
3. Activate the conda `reeds` env (D18): `conda activate reeds`. To build it: take `environment.yml` at `0c0ea27` (`git show 0c0ea27:environment.yml`), keep the required conda packages, drop the optional block and the whole `pip:` block (`gamsapi`, `gdxpds`, `gamspy_base` need GAMS; `pulp` is not used), add `ipykernel=7.3`, then `conda env create -f <that file>`. Built 28 Oct: Python 3.14.10, pandas 3.0.6, h5py 3.16.0.
4. Make the Verifier's folder. This is a second copy of the repo on `main`, next to the first one:

   ```
   git worktree add --detach ../utnuc-verify main
   ```

   That copy never contains a stage branch, so the Verifier cannot read the Builder's scripts (D21).
5. Keep the raw run folders outside the repo. They are in `D:\ReEDS\runs` (D25). In stage 00 the Builder writes that path and the ReEDS source path in `00_config/`.

The agent files are in `.claude/agents/`. Claude Code finds them on its own when you start `claude` in either folder.

## 2. Run one stage

The example is stage 02. Use the same steps for every stage.

**Step 1: Make the stage branch (main folder).**

```
git checkout main
git pull
git checkout -b stage/02_clean
claude
```

**Step 2: Builder.** In Claude Code, type:

> Use the builder agent to build stage 02_clean from docs/plan.md.

The Builder writes the scripts, runs them, commits, and writes the check report to `outputs/checks/02_clean.md`.

**Step 3: Verifier (second terminal, Verifier folder).**

```
cd ../utnuc-verify
git fetch origin
git checkout --detach origin/main
claude
```

Then type:

> Use the verifier agent on stage 02_clean. The Builder's check report is at `../ReEDS-2.0_UTNuc_Analysis/outputs/checks/02_clean.md`.

The Verifier gives a list of gaps: metric, case, both values, relative gap. It does not show its method.

**Step 4: Fix round.** Paste the gap list into the Builder session:

> The verifier reports these gaps. Fix them. You have one try.

Run Step 3 again. If a gap is still there, it is yours to look at (D21). You decide which value is right.

**Step 5: Reviewer (main folder).** Type:

> Use the reviewer agent on this branch.

The Reviewer gives a pass or fail list and adds rows to `docs/checked_citations.md`. One fail blocks the stage. Give the fails to the Builder, then run the Reviewer again.

**Step 6: Your check.** Read the check report, the Verifier result and the review. If you approve:

```
git push -u origin stage/02_clean
```

Open a PR on GitHub and merge it into `main`.

## 3. Stage 04 and later

Two more agents start here (D23).

1. **Cost-driver analyst:** type "Use the cost-analyst agent to propose a method for splitting the system cost change." It writes a draft in `notes/proposals/`.
2. **You decide.** If you approve, add it as a new decision (section 4). Then the Builder writes it as a `04_analyze` script, and steps 3 to 6 apply.
3. After the merge, the analyst writes its notes in `notes/analysis/`. The Explainer writes the text for each figure in `notes/text/`: "Use the explainer agent on stage 04_analyze."

## 4. Change an analysis choice

Never change a decision on a stage branch.

1. Make a small branch from `main`, for example `docs/D25-new-peak-rule`.
2. Add a new entry to `docs/decisions.md`, and change `docs/plan.md` or `docs/data_dictionary.md` if needed.
3. Merge it into `main`.
4. On the open stage branch: `git merge main`. Then the agents work with the new rule.

## 5. Keep credit use low (D23)

- Use one Claude Code session for each agent and each stage. Type `/clear` before you start the next agent.
- Do not paste the thread history or raw data into a session. The agents read the files that they need.
- Type `/cost` to see the use of the session.
- Start the Cost-driver analyst and the Explainer only at stage 04.
## 6. Open the outputs as CSV (D49)

The pipeline keeps its tables as `.h5`. To get CSV copies of the stage 01 and stage 03 tables:

```
conda activate reeds
python tools/export_csv.py
```

The copies go to `outputs/csv/`, under the same path as the `.h5` file, one file per batch and arm. For example: `outputs/csv/03_derive/capacity_generation/UON_ref.csv`. Every file opens in Excel (the largest has about 544,000 rows). `outputs/csv/index.csv` lists every file with its rows and columns. Units are in `docs/data_dictionary.md`; stage 03 tables also have a `unit` column, stage 01 tables do not. Stage 04 tables are already CSV, in `outputs/04_analyze/`.

Run it again after any stage that changes its tables; unchanged tables are skipped. `--tables prices_region` exports only that table; `--force` redoes it.

**Large tables.** `gen_h`, `reqt_quant`, `reqt_price`, `tran_util_h_rep` and `reduced_cost` have 6 to 57 million rows and are not exported. Read only the part you need, for example:

```python
import pandas as pd
df = pd.read_hdf('outputs/01_ingest/outputs/gen_h.h5', 'data',
                 where='case == "UON_20261022_3G_ref" & r == "p25" & t == 2050')
df.to_csv('gen_h_p25_2050.csv', index=False)
```

Every column except `Value` can go in `where=` (`batch`, `arm`, `level`, `case`, `r`, `t`, `i`, `h`, ...). `python tools/export_csv.py --tables gen_h` would export a whole table, one file per case, but it takes a long time and several GB.
