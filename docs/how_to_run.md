# How to run the analysis with Claude Code

This guide shows how to run one stage of `docs/plan.md` on your computer, from the first branch to the merge. The agents and their bounds are in `docs/plan.md`, "Agent team" (D20 to D23). The setup choices in this guide are D24.

You do three things in each stage. You start each agent. You pass the Verifier's gap list to the Builder. You merge. The agents do the rest.

## 1. One-time setup

1. Clone this repo, for example to `C:\Users\caleb\ReEDS-2.0_UTNuc_Analysis`.
2. Have a local copy of the ReEDS source at commit `0c0ea27`. The Reviewer reads it to check citations.
3. Activate the conda `reeds` env (D18): `conda activate reeds`.
4. Make the Verifier's folder. This is a second copy of the repo on `main`, next to the first one:

   ```
   git worktree add --detach ../utnuc-verify main
   ```

   That copy never contains a stage branch, so the Verifier cannot read the Builder's scripts (D21).
5. Keep the raw run folders outside the repo. In stage 00 you give the Builder their path and the ReEDS source path. It writes them in `00_config/`.

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
