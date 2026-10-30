# Proposal: splitting the change in annualized system cost, and linking it to prices (UON)

Author: Cost-driver analyst (D22). Date: 2026-10-29. Status: DRAFT for Caleb. Nothing here is applied.
Scope: UON only (D43d). UOS gets the same method only as a check of UON claims, in its own tables (D26).
Primary cost: D44 annualized cost from 03b2, Diff against the arm's own 0 GW case (D2). D10 is not used here.

Citation rule: model lines are only those already confirmed in `docs/checked_citations.md` (rows named by
line there) or in the check reports. Everything else is marked INFERENCE or "Not covered in the documentation".

---

## What is already available (no new method needed)

- `outputs/03_derive/annualized_cost_category.h5` (HDFStore, key `data`): annualized cost per case, region,
  year 2044-2050 and `sys_costs` category, 2024 $ (`outputs/checks/03_derive.md` L486). 25 categories are in
  the data (L494); the full list with UON `ref` 0 GW totals is at L540-566.
- Capital vs operations = `inv_*` vs `op_*`; this is the ReEDS `cost_cat_map.csv` `cost_type` split
  (`docs/checked_citations.md` row "cost_cat_map.csv", confirmed; `reeds/results.py` L230-262 at `0c0ea27`).
- 04a/04b already give `annualized_cost`, `annualized_cost_capital`, `annualized_cost_op` per group and year
  (D46i), and `energy_dollars`, `allin_dollars`, `load_quant` per group as components (D46e).

The only missing piece for a generation / capacity / transmission split is a category-to-part map.

---

## D47 (draft) - Cost split method

### Option A (RECOMMENDED): category map to four parts

**What it computes.** For each UON case, group (focus, utah_rest, neighbors, rest_wecc, wecc), year 2044 to
2050 and the 2044-2050 total: the annualized cost of each part = sum over the categories mapped to that part,
summed over member regions (group rule as for `annualized_cost`). Then Diff against the arm's 0 GW case, and
the step change per GW between neighboring levels (as 04c/04f, D41). Long table:
`batch, arm, level, case, group, t, part, value, value_0GW, diff, step_per_gw`.

**Files.** In: `outputs/03_derive/annualized_cost_category.h5` (key `data`); `00_config` region groups.
Out (proposed name): `outputs/04_analyze/04g_cost_parts_UON.csv`, and a check section in
`outputs/checks/04_analyze.md`.

**Checks for the Builder / Verifier.**
1. Sum of the four parts = `annualized_cost` in 04a for every case, group, year (rel. gap <= 1e-9).
2. Capital part of each Option A part + operations part = 04a capital / op (i.e. the map does not move money
   between capital and op).
3. Every category in the data is mapped exactly once; an unmapped category stops the script.
4. Verifier sample: UON `ref` 0 GW and 3 GW, wecc and focus, 2044 and 2044-2050.

**Exact mapping (25 categories found in the data, plus one listed in `results.py` L349-357 but not found).**
The mapping is by category name only. INFERENCE: the meaning of each category is read from its name; the
category definitions in `report.gms` are NOT in `docs/checked_citations.md`, so the Reviewer must check each
row of this map once against `report.gms` at `0c0ea27` before it is used. Rows marked (?) are the ones where
the name is not clear enough to place without that check.

| sys_costs | capital/op | Part | Note |
| --- | --- | --- | --- |
| `inv_investment_capacity_costs` | capital | capacity | new plant and storage capital (includes the SMR) |
| `inv_investment_refurbishment_capacity` | capital | capacity | |
| `inv_itc_payments_negative` | capital | capacity | tax credit on capital, negative |
| `inv_investment_spurline_costs_rsc_technologies` | capital | capacity (choice S, below) | spur lines of resource-supply-curve techs |
| `op_fom_costs` | op | capacity | fixed O&M; scales with MW, not MWh |
| `op_spurline_fom` | op | capacity (choice S) | |
| `op_consume_fom` (?) | op | other | name suggests fixed O&M of consuming techs; 1.3e7 $ in ref 0 GW |
| `op_fuelcosts_objfn` | op | generation | |
| `op_vom_costs` | op | generation | |
| `op_startcost` | op | generation | |
| `op_co2_transport_storage` | op | generation | scales with captured CO2, so with MWh (INFERENCE) |
| `op_co2_incentive_negative` (?) | op | generation | credit per captured CO2, negative (INFERENCE) |
| `op_ptc_payments_negative` | op | generation | per-MWh credit; 0 in ref 0 GW |
| `op_acp_compliance_costs` (?) | op | generation | 0 in ref 0 GW; meaning not checked |
| `inv_transmission_interzone_ac_investment` | capital | transmission | 40-year category (D45) |
| `inv_transmission_interzone_dc_investment` | capital | transmission | 40-year category (D45) |
| `inv_converter_costs` | capital | transmission | 40-year category (D45); carries the On hold pre-2044 converter gap |
| `inv_transmission_line_investment` | capital | transmission | in `results.py` L349-357, not in the data (`03_derive.md` L496) |
| `inv_transmission_intrazone_investment` | capital | transmission | 30-year category (D45) |
| `op_transmission_fom` | op | transmission | |
| `op_transmission_intrazone_fom` | op | transmission | |
| `inv_h2_production` | capital | other | hydrogen |
| `inv_h2_storage` | capital | other | |
| `op_h2_storage` | op | other | |
| `op_h2_transport_intrareg` | op | other | |
| `op_h2_ptc_payments_negative` | op | other | 0 in ref 0 GW |

Choice S (spur lines): capacity (default; INFERENCE: a spur line is part of connecting one plant, it is
built with it) or transmission (it is a wire). The Diff is likely small either way; report it as its own
row inside the part so it can be moved later without a rerun.

**Pros.** Answers the study question directly (generation vs capacity vs transmission). Uses only 03b2
output, no new model reads. Exact: parts add up to the primary cost. Works per group and per step, so it
also splits the 04f forcing cost per GW.
**Cons.** The map is a study choice, not a ReEDS grouping; 3 rows (?) need a source check. Fixed O&M under
"capacity" means the capacity part is not the same as "capital" (D46i) - the two splits must be labeled
clearly. Cost is where incurred, not who pays (data dictionary L125, INFERENCE there).

### Option B: capital vs operations by group (already built, D46i)

**What it computes.** No new computation: a 5-group x 2-part table of the 04b Diffs (`annualized_cost_capital`,
`annualized_cost_op`), each year and 2044-2050, plus the 04f per-GW steps for each.
**Files.** `outputs/04_analyze/04b_diff_UON.csv`, `04f_forcing_cost_UON.csv`.
**Pros.** Zero build cost; already Verifier-checked; split follows ReEDS's own `cost_type` (confirmed).
**Cons.** Does not isolate transmission (transmission capital sits in capital, its FOM in op). Plant FOM is in
operations, so "operations down" mixes avoided fuel with the SMR's own fixed O&M (see the smrcons note in
`notes/analysis/cost_drivers_uon.md`). Does not answer "generation vs capacity".

### Option C: Option A plus a "SMR versus response" view across the two nuclear-cost arms

**What it computes.** Option A table, plus, within UON, the per-group Diff of `smrcons` minus the Diff of
`ref` at each level, by part. INFERENCE: `ref` and `smrcons` differ only in `plantchar_nuclear_smr`
(data dictionary L87), and the prescribed amount is fixed, so the build/dispatch response outside p25 should
be the same in both; the gap between the arms then measures how much of the Diff is the SMR's own cost
sensitivity. The outputs so far support this (outside-focus Diffs agree to ~0.1%, see analysis note).
**Files.** Option A output; `04b_diff_UON.csv`.
**Pros.** Separates "what the SMR itself costs" from "what the rest of the system saves" without needing
the SMR's own cost line, which `systemcost_ba` does not give by technology (INFERENCE: the table has no `i`
column, data dictionary L136).
**Cons.** Only two cost points; is a comparison of arms (allowed within a batch, D41), not an exact
decomposition. Adds a second table to explain.

**Recommended default:** Option A, with spur lines in capacity, reported for all five groups, each year,
2044-2050 total, and per-GW step. Keep Option B as is (already reported). Option C only if Caleb wants the
"SMR cost vs system response" sentence in the write-up.

---

## D48 (draft) - Linking the cost parts to price changes

Background. Prices (03a, D6) are marginal values paid by load; the annualized cost is resource cost where
incurred. The docs say price x quantity per constraint sums to the objective at optimality
(`model_documentation.md` L3219-3220, confirmed in `docs/checked_citations.md`, the 04f row). INFERENCE: so
the gap between what load pays and what the system costs is not an error; it is the margin (or shortfall) of
the resources, and for a forced build it includes the part the prescription pays.

**Caution.** The "load payment at marginal prices" view is cost view C, which is On hold
(`docs/decisions.md`, On hold, first bullet). Link L1 below touches view C. Caleb should say whether D48 takes
view C off hold, or whether L1 stays as a check table only.

### Link L2 (RECOMMENDED): per-MWh view, same units as the price

**What it computes.** Per group and post-plant year (2044, 2047, 2050; the years with prices):
`Diff(cost part) / load_quant` in 2024 $/MWh for each Option A part, next to `Diff(avg_energy_price)` and
`Diff(avg_allin_price)` of the same group and year. `load_quant` is the 0 GW value (same in all levels;
04a shows identical values at 0 and 3 GW, e.g. ref focus 2044 66,195,191.87 MWh). Plus one ratio:
Diff(generation part) per MWh against Diff(energy price).
**Files.** Option A output; `04a_groups_UON.csv` (`load_quant`); `04b_diff_UON.csv` (prices).
**Pros.** Same unit as prices; no transfer accounting; does not need view C.
**Cons.** Annualized cost exists for every year 2044-2050, prices only for solve years; the table uses only
2044, 2047, 2050 (INFERENCE: 2045-2046 and 2048-2049 copy the solve-year operations, `results.py` L462-465
confirmed, so nothing new is lost for op; capital is constant between solve years too, 04b shows it).

### Link L1: payment view

**What it computes.** Per group and year: Diff(`energy_dollars`), Diff(`allin_dollars`), and
Diff(`allin_dollars` - `energy_dollars`) (the non-energy payments: reserve margin, operating reserve,
state_rps, nat_gen) next to Diff(annualized cost) and its parts.
**Files.** `04a_groups_UON.csv` (components), Option A output.
**Pros.** Shows that most of the payment change is outside p25 (load there is ~20x p25). Shows a rise in
non-energy payments in `neighbors` that the averages hide.
**Cons.** Close to cost view C (On hold). `allin_dollars` includes state_rps/nat_gen dollars whose unit is
not stated (`outputs/checks/04_analyze.md` L10). A split of the non-energy part by price type needs the
per-type dollars; whether 03a keeps them per type is not stated in its check section I read - the Builder
would confirm.

**Recommended default:** L2 now; L1 as a check table only, unless Caleb takes view C off hold.
