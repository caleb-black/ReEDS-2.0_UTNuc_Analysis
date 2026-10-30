# What drives the stage 04 results - UON

Author: Cost-driver analyst (D22). Date: 2026-10-29. Batch: UON only (main study, D43d). No UOS number is
used or shown here (D26).

Sources read (no code run): `outputs/04_analyze/04b_diff_UON.csv`, `04a_groups_UON.csv` (component rows),
`outputs/checks/04_analyze.md`, `outputs/checks/03_derive.md` (03b2 section). Money in 2024 $ (D8). "3 GW" =
Diff of the 3 GW case against the arm's own 0 GW case (D2). bn = 1e9.

Model citations are at `0c0ea27` and only those already confirmed in `docs/checked_citations.md`. Each
section has two parts: **Outputs show** (read straight from the files, or simple arithmetic on them) and
**INFERENCE** (my reasoning, not from the docs). The cost split by generation / capacity / transmission is
NOT yet computed: it needs the category map in `notes/proposals/cost_split.md` (D47 draft). Until then only
capital vs operations (D46i) is available.

---

## 1. Annualized system cost rises about 0.66% at 3 GW (ref): capital up, operations down

**Outputs show** (`04b_diff_UON.csv`, `t` = 2044-2050, ref, 3 GW; bn 2024 $)

| group | total Diff | capital Diff | operations Diff |
| --- | --- | --- | --- |
| focus (p25) | +6.39 | +7.16 | -0.78 |
| utah_rest | -0.17 | -0.14 | -0.03 |
| neighbors | -1.94 | -1.00 | -0.94 |
| rest_wecc | +0.00 | +0.49 | -0.49 |
| wecc | **+4.28 (+0.66%)** | +6.52 (+1.67%) | -2.24 (-0.88%) |

- By year (wecc): 2044 +0.71 bn (capital +1.06, op -0.35); 2047 +0.53 (+0.81, -0.28); 2050 +0.57 (+0.90,
  -0.33). 2045-2046 equal 2044 and 2048-2049 equal 2047: operations of a solve year fill the years to the
  next solve year (`reeds/results.py` L462-465, confirmed), and no capital is added between solve years.
- p25 carries more than the whole rise (+6.39 bn vs +4.28 bn); the other groups together fall by 2.11 bn,
  mostly in `neighbors` (-1.94 bn, split about evenly between capital and operations).
- Capital outside p25 falls by 0.65 bn over 2044-2050, almost all from the 2047 and 2050 solves (2044:
  -0.007 bn/yr; 2047: -0.19 bn/yr; 2050: -0.07 bn/yr). Inside that, `neighbors` capital falls (-1.00 bn)
  while `rest_wecc` capital rises (+0.49 bn).
- Shape: the wecc total has no direction change in any arm (`04_analyze.md` L144); the groups below it
  change direction often (L141-143).

**INFERENCE**
- The p25 capital rise (+7.16 bn, about +1.0 bn/yr) is mainly the SMR's own annualized capital. The rest
  of the system answers by building less (capital down in neighbors, mainly from 2047) and burning less
  (operations down in every group). A cost split by category (D47) is needed to confirm that the operations
  fall is fuel and VOM rather than fixed O&M.
- Cost is placed where the plant or line is, not with who pays (data dictionary L125, itself INFERENCE).
  So the p25 rise and the neighbor fall are not "p25 pays, neighbors gain".
- The wecc total is smooth while the groups are lumpy: the model may move builds between regions in steps
  as the level changes, and these moves nearly cancel in the total.

## 2. Forcing cost about 1.4 bn $/GW (2044-2050) in ref, 2.6x higher in smrcons

**Outputs show** (`04_analyze.md` L338-345, wecc, 2044-2050, bn 2024 $ per GW, per 0.25 GW step)

| arm | first step | last step | 3 GW Diff / 3 | wecc capital Diff | wecc op Diff |
| --- | --- | --- | --- | --- | --- |
| ref | 1.39 | 1.48 | 1.43 | +6.52 | -2.24 |
| smrcons | 3.71 | 3.81 | 3.75 | +11.64 | -0.41 |
| gaslow | 1.88 | 1.97 | 1.91 | +7.21 | -1.49 |
| loadlow | 1.75 | 1.75 | 1.66 | +6.93 | -1.97 |
| pvadv | 1.43 | 1.51 | 1.44 | +6.96 | -2.65 |
| loadhigh | 1.29 | 1.38 | 1.32 | +6.77 | -2.81 |

(Capital and op columns: 3 GW Diff, 2044-2050, bn, from `04b_diff_UON.csv`.)

- In ref and smrcons the step cost rises slowly with level (1.39 to 1.48; 3.71 to 3.81). loadlow is noisy
  (1.43 to 1.83). No sign change in any arm at wecc level (L355-380).
- smrcons vs ref, 3 GW: the arm gap at wecc is +6.96 bn; +6.96 bn of it is in focus. Outside p25 the two
  arms agree closely: neighbors -1.947 vs -1.945 bn; utah_rest -0.166 vs -0.167 bn; rest_wecc +0.006 vs
  +0.003 bn. Prices and net imports agree too (focus 2044 energy price -2.343 vs -2.346 $/MWh; focus net
  imports -8,780,295 vs -8,779,786 MWh).
- In smrcons, p25 **operations rise** (+1.05 bn) where in ref they fall (-0.78 bn); p25 capital Diff is
  +12.29 bn vs +7.16 bn.
- p25 capital Diff is similar in the five arms that use the moderate SMR cost (7.16 to 7.51 bn).

**INFERENCE**
- Forcing cost = added capital minus avoided operations (plus avoided capital elsewhere). The arms rank as
  that reading predicts: where avoided operations are large (loadhigh -2.81, pvadv -2.65, ref -2.24 bn) the
  forcing cost is low; with cheap gas (gaslow, -1.49 bn) less fuel cost is avoided and the forcing cost is
  the highest of the moderate-cost arms. This is consistent with the outputs; the mechanism (which fuel,
  which plants) needs the category split (D47) and generation, which is on hold (D43a).
- Because the prescribed amount is fixed, the SMR cost assumption should change only the SMR's own cost,
  not how the rest of the system responds. The smrcons-ref agreement outside p25 supports this. So the 2.6x
  gap is the SMR cost assumption, not a different system response.
- The p25 operations rise in smrcons is most likely the SMR's own fixed O&M, if that sits in `op_fom_costs`
  (an `op_*` category, so "operations" under D46i; the category content is not in `checked_citations.md`).
  If so, "operations down" in ref is net of the SMR's fixed O&M, and avoided fuel and VOM are larger than
  the -2.24 bn suggests. The category split would show this directly.
- The slow rise of the step cost with level: each extra GW avoids a little less than the one before.
  Small effect over 0-3 GW (about +7% in ref).
- 04f is a finite difference of the annualized cost, not the dual. The docs define a marginal price as the
  change in the objective for a change in the right side (`model_documentation.md` L3218, confirmed). The
  annualized cost is not the model objective (D44 is a revenue-requirement view), so 04f is a proxy only.

## 3. Prices fall mainly in p25 (per MWh), but most of the payment change is outside p25

**Outputs show** (ref, 3 GW; energy price Diff in 2024 $/MWh, % in brackets)

| group | 2044 | 2047 | 2050 |
| --- | --- | --- | --- |
| focus | -2.35 (-6.1%) | -2.15 (-5.6%) | -1.29 (-3.5%) |
| utah_rest | -1.89 (-5.0%) | -1.76 (-4.7%) | -1.05 (-2.8%) |
| neighbors | -0.52 (-1.2%) | -1.47 (-3.4%) | -0.51 (-1.3%) |
| rest_wecc | -0.21 (-0.5%) | -1.13 (-2.9%) | -0.66 (-1.8%) |
| wecc | -0.46 (-1.1%) | -1.33 (-3.3%) | -0.62 (-1.6%) |

- Per MWh the fall is largest in p25 and utah_rest. In 2047 the fall is broad: neighbors and rest_wecc fall
  by 1.1-1.5 $/MWh.
- p25 2044 energy price fall at 3 GW by arm: loadlow -2.78, ref -2.35, smrcons -2.34, pvadv -1.98,
  loadhigh -0.97, gaslow -0.58 $/MWh.
- Every neighbor's 2050 energy price falls in ref at 3 GW (-0.13 to -1.17 $/MWh, `04_analyze.md` L244-252).
- All-in price falls less than energy price outside p25: neighbors all-in 2044 **+0.02** $/MWh while
  energy is -0.52; wecc all-in -0.15 vs energy -0.46.
- Payments (Diff of `energy_dollars`, from `04a_groups_UON.csv`, bn/yr): wecc -0.62 (2044), -1.89 (2047),
  -0.92 (2050). p25's part is small: -0.16, -0.15, -0.09, so the fall outside p25 is 3x (2044) to 12x
  (2047) the fall inside. Load outside p25 is about 20x p25's (`load_quant` 2044: wecc 1.356e9 MWh, focus
  6.6e7 MWh).
- Non-energy payments (`allin_dollars` minus `energy_dollars`, Diff, bn/yr) rise: wecc +0.42 (2044), +1.33
  (2047), +0.52 (2050), all in neighbors (+0.33, +0.55, +0.16) and rest_wecc (+0.09, +0.78, +0.36); p25
  about 0. At wecc level this offsets 57-70% of the energy-payment fall.

**INFERENCE**
- The headline "price falls mainly in p25" holds per MWh only. In dollars paid by load, the energy-price
  fall is mostly outside p25, because the load there is much larger.
- Which price type rises in the non-energy payments (reserve margin, operating reserve, state_rps,
  nat_gen) is not in what I read. One possible reading (not from the docs): with lower energy prices, other
  constraints carry more of the plants' cost recovery. This must be checked with a split by price type
  before any claim is made. Note: state_rps/nat_gen dollars have no stated unit (`04_analyze.md` L10).
- Annualized cost rises (+0.53 to +0.71 bn/yr) while energy payments fall (-0.62 to -1.89 bn/yr). The
  docs say price x quantity summed over constraints equals the objective at optimality
  (`model_documentation.md` L3219-3220, confirmed). INFERENCE: the gap between payments and cost is margin
  that resources lose, and for a forced plant part of it is the forcing cost. Linking the two needs the
  D48 draft, and the payment view is close to cost view C, which is On hold.

## 4. Imports shift from p25 to the neighbors

**Outputs show** (ref, 3 GW, net imports Diff, TWh)

| group | 2044 | 2047 | 2050 |
| --- | --- | --- | --- |
| focus | -8.78 | -8.25 | -6.89 |
| utah_rest | +1.35 | +0.75 | +0.50 |
| neighbors | +5.22 | +5.74 | +6.74 |
| rest_wecc | +2.19 | +1.69 | -0.48 |
| wecc | -0.02 | -0.07 | -0.13 |

- p25 2044 import fall by arm: ref and smrcons -8.78, loadlow -7.68, pvadv -7.42, loadhigh -6.75, gaslow
  -5.73 TWh.
- Lines touching p25 at limit in p25's peak block: no change at 3 GW in ref (3, 3, 2 directions in 2044,
  2047, 2050, same as 0 GW).
- New lines, ref 3 GW (MW): focus -313 (2044), -127 (2047), +37 (2050); neighbors -425, +185, +567;
  rest_wecc +845, -12, -17.

**INFERENCE**
- p25 imports less and its neighbors import more (or export less): the SMR's output replaces energy that
  used to flow into p25, mostly from the neighbor group. The wecc total barely moves, as expected for flows
  inside WECC.
- The import fall is about one third of what 3 GW running all year would give (26.3 TWh). How much the SMR
  actually generates, and what it displaces inside p25, needs generation data, which is on hold (D43a).
  Not claimed.
- Fewer new lines into p25 in 2044 fits a smaller import need; the shifts in other groups are mixed, and
  3,086 of 5,070 new_lines group rows are zero-filled (`04_analyze.md` L12, D46h).

## 5. Caveats

- Converter carry-over (On hold): in ref the Diff of annualized `inv_converter_costs` built before 2044 is
  +3.5e7 at 3 GW (`03_derive.md` L645), small against +4.28 bn, but it would sit in the transmission part of
  D47. Report it as its own row.
- 2045-2046 and 2048-2049 repeat solve-year values; the 2044-2050 total weights 2044 and 2047 three times
  and 2050 once. This is the D44 method, not an error.
- All INFERENCE items above are mine; none is a model claim.

---

## Choices for Caleb

1. **Cost split method (D47 draft).** Approve Option A (category map to generation / capacity /
   transmission / other, per group, year, total and per-GW step). Default: **approve A**; keep Option B
   (capital/op, already built) as is.
2. **Spur lines** (`inv_investment_spurline_costs_rsc_technologies`, `op_spurline_fom`). Default:
   **capacity**, shown as its own row so it can move.
3. **Unclear categories** (`op_acp_compliance_costs`, `op_consume_fom`, `op_co2_incentive_negative`), and the
   map as a whole. Default: **place them as in the proposal table, and have the Reviewer check each category
   once against `report.gms` at `0c0ea27`** before the Builder runs.
4. **Price link (D48 draft).** Default: **L2 (cost parts per MWh of load next to the price Diff)**; L1 (payment
   view) as a check table only, and cost view C stays On hold.
5. **smrcons vs ref view (Option C).** Default: **yes, one small table**. It shows that the 2.6x forcing-cost
   gap sits almost entirely in p25's own cost.
6. **Non-energy payments rise outside p25.** Default: **approve a group split of all-in dollars by price
   type** (load, res_marg, oper_res, state_rps, nat_gen) for 2044, 2047, 2050, if 03a already holds the
   per-type dollars. If it does not, this needs a stage 03 change and a separate decision.
