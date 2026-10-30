# Neighbors of p25: capacity and generation changes (PRELIMINARY)

29 Oct 2026. Exploration only, not a pipeline stage: capacity and generation are on hold (D43a), so nothing here is a finding until Caleb decides. UON (D43d). Diff = case minus the same arm's 0 GW case (D2). Tech groups from ReEDS `tech_map.csv` at `0c0ea27` (D37g).

Source: `outputs/03_derive/capacity_generation.h5`, `outputs/04_analyze/04e_neighbor_prices_UON.csv`, `outputs/01_ingest/outputs/net_import_ann_rep.h5`. Scratch scripts `neighbors.py` and `levels.py` in the session scratchpad; the region-by-tech table they wrote is `nb_capgen_diff_UON.csv` there (not in the repo). Everything under "Why" is INFERENCE: the model docs were not checked for these mechanisms.

## p25 itself (ref, 3 GW)
- Capacity: +3,000 MW Nuclear-SMR; -1.7 to -2.2 GW Gas-CC and -1.2 to -1.7 GW Gas-CT built (2044-2050). Net capacity change is small (+42 MW in 2044, -886 MW in 2050).
- Generation: SMR +22.4 TWh; Gas-CC -13 to -14 TWh. Net +8.8 TWh (2044) to +6.9 TWh (2050), which leaves p25 as lower net imports (-8.8 to -6.9 TWh).

## Neighbors, ranked by size of change (ref, 3 GW, 2044 / 2047 / 2050)

| Region | Line to p25 | Generation Diff (TWh) | Main capacity change | Main generation change | Net imports Diff (TWh) | Energy price Diff ($/MWh) |
| --- | --- | --- | --- | --- | --- | --- |
| p10 | DC (LCC) | +0.1 / -6.2 / -4.6 | 2047+: Battery -1.4 GW, UPV -1.2 GW | UPV -3.7, Battery -2.7 (2047) | -0.2 / +3.1 / +2.4 | -0.2 / -2.2 / -0.7 |
| p33 | AC | -3.1 / -3.0 / -3.2 | Gas-CC -670 MW, Gas-CT +400 to +680 MW; 2050 UPV -850, wind +450 | Gas-CC -2.7 to -3.6 | +3.2 / +3.1 / +3.4 | -1.0 / -1.1 / -0.5 |
| z28 | AC | -0.7 / +3.1 / +2.1 | 2047+: Gas-CC +570, UPV +410 to +740 MW | UPV and Gas-CC up (2047+) | +0.7 / -3.1 / -2.0 | -0.7 / -0.9 / -0.1 |
| p24 | DC (VSC) | -0.8 / -1.4 / -1.1 | Onshore wind -250 MW, Gas-CT +250 MW | Wind -1.1 to -1.2; coal -0.6 (2044) | +0.8 / +1.4 / +1.1 | -1.2 / -1.3 / -0.7 |
| p31 | AC | 0.0 / -0.4 / -1.1 | Onshore wind -90 to -180 MW | Wind, UPV down | 0.0 / +0.4 / +1.1 | -0.7 / -0.8 / -0.2 |
| p21 | AC | about 0 | Gas-CT +130 to +260 MW | Gas-CT up slightly | +0.4 to +0.6 | -0.9 / -1.2 / -1.2 |
| p16 | AC | -0.3 / 0.0 / -0.2 | Onshore wind -60 to -100 MW | Wind down, Gas-CC-CCS up (2047) | small | -0.6 / -0.8 / -1.0 |
| p12, p27 | AC | about 0 | none > 50 MW | small | small | -0.2 to -0.5 |

p26 (utah_rest, also beside p25): wind -210 to -340 MW, Gas-CT +80 to +220 MW; generation -1.4 to -0.5 TWh; imports up by the same.

## How it scales with level (ref)
- **p10**: in 2047 its generation falls steadily from about 0.75 GW upward, to -6.2 TWh at 3 GW. In 2044 it barely moves.
- **z28**: mirrors p10 in 2047 (+1 TWh at 0.75 GW, plateau about +3 to +4 TWh above 2 GW).
- **p33**: almost no change up to 1.75 GW, then falls fast (-0.9 TWh at 2 GW to -3.1 TWh at 3 GW in 2044).
- **p24, p26**: fall gradually with level.

## Is it the same in other arms? (3 GW, sum of |generation Diff| over tech groups and 2044/2047/2050)
- p33 is among the top two in every arm except `loadlow` (19.6 TWh in loadhigh, 2.4 in loadlow).
- p10 is large in ref, smrcons, pvadv and loadhigh, but small in gaslow (1.8).
- p24 is large in loadlow and pvadv (6.3).
- So the ranking depends on the arm; p33 and z28 are the most consistent.

## Why (all INFERENCE)
1. **p33 is the main direct substitute.** It is gas-heavy (Gas-CC about 26 TWh). Above about 2 GW, the SMR's extra energy that p25 cannot absorb by cutting its own gas displaces p33's Gas-CC, and p33 imports more. The threshold looks like p25's own gas being displaced first.
2. **p10 and z28 swap where solar and storage get built.** p10 builds about 1.2 GW less UPV and 1.4 GW less battery from 2047, while z28 builds more UPV and Gas-CC and generates more. Their net-import changes are almost equal and opposite (p10 +3.1, z28 -3.1 TWh in 2047). This looks like the model re-siting new solar-plus-storage between the two regions, not a direct effect of p25's SMR on either one. It is arm-dependent (small in gaslow).
3. **Less new wind near p25, more gas CT.** p24, p26, p31 and p16 build less onshore wind, and p21, p24, p26 and p33 build more Gas-CT. One reading: the SMR covers energy needs, so less energy-heavy wind is built, and some CT is added for capacity; it may also relate to p25 building 1.2 to 1.7 GW less Gas-CT itself. Not checked against the reserve-margin outputs.
4. **Prices fall most where gas is displaced or imports rise**: p24, p21, p33 (about -1 $/MWh), and p10 in 2047 (-2.2).

## Follow-ups at 0 / 1 / 2 / 3 GW (added 29 Oct, still PRELIMINARY)

Script `followups2.py`, output `followups2_out.txt` (session scratchpad). UON `ref` and UOS `ref`. Firm capacity: these runs use the stress-period reserve margin (`GSw_PRM_CapCredit` = 0, data dictionary), so `cap_firm` is not written; the proxy here is mean output over each case's 48 stress blocks per year (`gen_h_stress`, MW, `report_params.csv` L87), the same output `val_resmarg` values (`report.gms` L1077-1080). Line flows: `tran_flow_rep_ann` (stage 01; MWh, net, + = r to rr; `report_params.csv` L201).

### 1. p25 is an import hub, and the SMR mostly cuts its imports
At 0 GW (UON ref, 2044) p25 takes in about 32 TWh from p33 (8.5), p16 (7.9), p24 (7.0), p26 (4.4), p31 (2.3) and p12 (1.6), and sends about 12.9 TWh on to p10 over the DC line. With the SMR, the inflows shrink, while the outflow to p10 barely changes (it even drops 0.7 TWh):

| Line (UON ref, TWh/yr into p25 unless noted) | 0 GW | Diff at 1 GW | 2 GW | 3 GW |
| --- | --- | --- | --- | --- |
| p33 to p25 (2050) | 9.9 | -0.6 | -1.2 | -2.8 |
| p24 to p25 (2044) | 7.0 | -0.3 | -1.0 | -2.7 |
| p16 to p25 (2044) | 7.9 | -0.4 | -1.2 | -2.2 |
| p26 to p25 (2044) | 4.4 | -0.2 | -0.6 | -1.5 |
| p31 to p25 (2044) | 2.3 | -0.3 | -0.4 | -0.7 |
| p25 to p10 (2047) | 10.9 | -0.4 | -1.4 | -0.9 |

So "neighbors import more" mostly means **neighbors send less power into p25**. p16 sends 2.2 TWh less but generates only 0.3 TWh less, so its power goes elsewhere. UOS shows the same pattern, slightly larger (p33 line -3.1 to -3.7, p24 -2.5 to -3.0 at 3 GW).

### 2. Two regimes: below and above about 2 GW
- **Up to about 2 GW, the SMR mainly replaces new gas CC inside p25.** p25 Gas-CC capacity: -1.0 GW at 1 GW, -1.7 GW at 2 GW, then flat (-1.7 GW at 3 GW, 2044). p25 Gas-CC generation: -6.1, -11.1, -13.0 TWh. Neighbors change little.
- **Above about 2 GW, p25 has no more gas CC to drop, and the effect spills out.** p25 then drops Gas-CT capacity instead (-0.07, -0.46, -1.22 GW at 1/2/3 GW in 2044), and the neighbor changes jump: p33 Gas-CC generation -1.0 TWh at 2 GW to -3.6 at 3 GW; p24 wind generation -0.2 to -1.1; most line-flow changes are larger between 2 and 3 GW than between 0 and 2 GW.
- UOS: same shape, but p25's gas-CC drop stops earlier (about -0.8 GW already at 1 GW), and p25 drops more Gas-CT (up to -2.6 GW). INFERENCE: the UOS gas fleet differs (upgrades), so less new CC is there to displace.

### 3. Firm capacity: a gas-CC to gas-CT shift near p25
Mean output in stress blocks (MW, UON ref, Diff at 1/2/3 GW):
- p25: SMR +894 / +1,787 / +2,681 (about 89% of nameplate); Gas-CC -869 / -1,529 / -1,535; Gas-CT -16 / -137 / -385.
- p33: Gas-CC +24 / -126 / -545; Gas-CT -10 / +27 / +174.
- p26: onshore wind -23 / -78 / -81; Gas-CT +33 / +100 / +27.
- p21: Gas-CC -41 / -41 / -139; Gas-CT about 0 / +2 / +55. p24: wind -7 / -7 / -51; Gas-CT +8 / +8 / +58.
- This supports reading 3 above in sign: near p25, firm duty moves from gas CC (and some wind) to gas CT. The sizes outside p25 are small (50 to 550 MW). UOS shows the same, larger in p33 (Gas-CC -806 MW, Gas-CT +216 MW in stress) and p24 (Gas-CT capacity +525 MW, wind -528 MW at 3 GW in 2050).
- INFERENCE: with the SMR covering energy and some firm need, the cheaper way to keep the reserve margin near p25 becomes CT capacity instead of CC; this was not checked against the reserve-margin prices.

### 4. p10 and z28: a re-siting choice, not a steady SMR effect
2047 total generation Diff (TWh) at 1 / 2 / 3 GW:

| Arm | p10 | z28 |
| --- | --- | --- |
| ref | -2.7 / -4.8 / -6.2 | +1.7 / +3.9 / +3.1 |
| smrcons | same as ref | same as ref |
| loadhigh | +1.0 / -0.6 / -3.7 | +0.8 / +2.2 / +3.6 |
| pvadv | +0.2 / +2.6 / +3.0 | -0.4 / -0.4 / -1.1 |
| loadlow | +0.8 / +0.8 / +1.9 | -0.7 / -1.4 / -3.1 |
| gaslow | -0.7 / 0.0 / -0.2 | 0.0 / -0.1 / -0.2 |

- The sign flips between arms (pvadv and loadlow go the other way from ref), and the two regions always move opposite. In ref it is UPV and battery (p10 -1.2 GW UPV, -1.4 GW battery at 3 GW; z28 +0.4 GW UPV, +0.6 GW Gas-CC).
- UOS ref: same direction as UON ref but smaller (p10 UPV -0.6 GW and battery -0.3 GW in 2050; z28 UPV +0.7 GW).
- INFERENCE: p10 and z28 are near-equal places for new solar and storage, and small changes elsewhere tip the choice. It should not be reported as an effect of the SMR on p10 without more checks.

### 5. UOS overall
Same main story: p25 imports less, p33 is the largest neighbor change (Gas-CC generation -4.3 to -4.9 TWh at 3 GW, larger than UON), wind-to-CT near p25 (p24, p26, p16), p10/z28 swap in the same direction but smaller.

## Next checks if you want to go further
- Done above (29 Oct): firm capacity proxy, p10/z28 by level and arm, line flows, UOS.
- Still open: reserve-margin prices (`reqt_price` type `res_marg`) by region, to test the CC-to-CT reading; the 2 GW threshold at other arms; whether the p26 Gas-CT peak at 2 GW (then lower at 3 GW) is real or a tie.

## Threshold check across arms (added 29 Oct, still PRELIMINARY)

Question: does the "about 2 GW" switch (p25 stops cutting gas CC, and the effect spills to neighbors) hold in every arm? UON: all 6 arms, every 0.25 GW level, 2047 and 2050. UOS: ref, loadhigh, loadlow, every 0.5 GW level. Diff = case minus same arm's 0 GW case (D2); UON and UOS kept apart (D26). Sources: `03_derive/capacity_generation.h5`, stage 01 `tran_flow_rep_ann`, raw `gen_h_stress`. Scratch scripts `arms.py`, `arms_abs.py` (session scratchpad), not pipeline code.

### Facts

1. **p25 Gas-CC capacity falls about 1 GW per GW of SMR, then stops at an arm-specific cap.** Diff at saturation (2047): ref and smrcons -1.94 GW (reached at 1.75-2.0 GW); gaslow -2.39 and pvadv -2.40 (reached at 2.25-2.5 GW); loadhigh pauses at -1.95 around 2.0-2.25 GW, then goes on to -2.59 at 3 GW; loadlow does not saturate (-2.91 at 3 GW).
2. **The cap equals the new Gas-CC p25 builds after 2041 in that arm's 0 GW case.** p25 Gas-CC at 0 GW minus 2041 (GW):

   | UON arm | 2044 | 2047 | 2050 | Diff at 3 GW, 2047 |
   | --- | --- | --- | --- | --- |
   | ref / smrcons | 1.73 | 1.94 | 2.19 | -1.94 |
   | gaslow | 2.39 | 2.39 | 2.66 | -2.39 |
   | pvadv | 2.33 | 2.40 | 2.95 | -2.40 |
   | loadhigh | 1.99 | 2.62 | 2.94 | -2.59 |
   | loadlow | 2.48 | 3.02 | 3.88 | -2.91 |

   At 3 GW, p25 Gas-CC stays at its 2041 value in every arm except loadhigh and loadlow, which add small amounts after 2047. Existing CC is not retired. (loadhigh's pause at 2 GW lines up with its 2044 headroom of 1.99.)
3. **The spillover starts where the cap binds, in every arm.** Once the CC cap is reached, p25 Gas-CT starts to fall, neighbor Gas-CT rises, p33 Gas-CC generation falls, and the inflow cut to p25 speeds up.

   | UON arm (2047) | knee | p25 CT Diff at 3 GW | p33 CC gen at knee / 3 GW (TWh) | inflow cut at knee / 3 GW (TWh) |
   | --- | --- | --- | --- | --- |
   | ref, smrcons | 1.75 to 2.0 | -1.72 GW | -0.84 / -3.33 | -3.74 / -8.93 |
   | loadhigh | 1.75 to 2.0 | -0.53 GW | -0.81 / -0.89 (2050: -3.23 / -2.79) | -2.55 / -4.58 |
   | gaslow | 2.25 to 2.5 | -0.44 GW | -1.64 / -2.86 | -3.33 / -6.20 |
   | pvadv | 2.25 to 2.5 | -0.88 GW | -0.27 / -1.34 | -4.19 / -7.01 |
   | loadlow | none by 3 GW | -0.07 GW | about 0 | steady, -5.40 at 3 GW |

   Below the knee, the inflow cut is about 1 TWh per GW in every arm.
4. **Stress-period output (firm-capacity proxy).** In every arm, p25 SMR gives 894-908 MW per GW (2,681-2,763 MW at 3 GW), and p25 Gas-CC drops by about the same amount up to 2 GW. At 3 GW, p25 CC drops only -1,721 MW in ref, against -2,100 to -2,830 in the other arms. p25 CT drops most in ref (-569 MW). Neighbors' (incl. p26) CT stress output rises in all arms except loadlow 2047 (+88 to +422 MW at 3 GW). Neighbor UPV stress output falls in loadhigh (-890 MW in 2047) and pvadv 2050 (-466).
5. **p25 → p10 flow** barely moves in any arm (|Diff| ≤ 1.4 TWh on about 10 TWh). In ref it falls slightly; in pvadv, loadhigh and loadlow it rises slightly.
6. **UOS shows the same rule.** Headroom (0 GW minus 2041, 2047): ref 0.83, loadhigh 2.55, loadlow 2.74 GW. The CC Diff caps at ref -0.83 (reached at 1.5 GW), loadhigh -2.55, loadlow -2.69 (both reached near 3 GW). The spillover follows: UOS ref p25 CT -2.56 GW and inflow cut -11.0 TWh at 3 GW, the largest of all; loadhigh and loadlow are milder.

### INFERENCE (not checked against the model docs)

- The "2 GW threshold" is not a fixed number. It is how much new Gas-CC p25 would otherwise build from 2044 on. Up to that amount, the SMR takes the place of p25's planned CC, and the neighbors see little. Past it, there is no planned CC left to avoid, so the SMR pushes out p25 CT and imports, and neighbors shift from CC energy to CT capacity.
- So arm order follows the size of p25's planned CC build. ref has the smallest (knee about 2 GW), gaslow and pvadv are in the middle (about 2.4), loadhigh is larger but staged (a pause at 2 GW), and loadlow is largest (no knee by 3 GW, since low load delays CC to later years). UOS ref plans less new CC (knee about 1 GW) because of the upgrades, so its spillover is the largest.
- Whether the plateau is a hard limit in the model (e.g. no early retirement of existing CC) or an economic choice is not shown by these outputs. I have not checked `b_inputs.gms`/`c_supplymodel.gms` at 0c0ea27 for retirement rules.

### Possible next checks

- Check retirement rules at 0c0ea27, to see whether existing CC can retire early (this explains why the plateau sits at the 2041 fleet).
- See whether the knee shows up in the forcing-cost slope by arm (04c/04f). Cost per GW may step up past the cap.
- Neighbor CT build by region past the knee, per arm.

## Follow-up A: can p25 gas CC retire? (added 29 Oct, PRELIMINARY)

Facts, from 0c0ea27 and the run switches (`inputs_case/switches.csv`, same in UON and UOS):
- The runs use `GSw_Retire=5`, `GSw_RetireYear=2027`, `GSw_RetirePenalty=1`. `cases.csv` L299 defines 5 as "same as 3 but nuclear can only retire after 2030". 3 is "new/existing nuclear/coal/gas can retire after minimum age".
- `b_inputs.gms` L5039-5040: with Sw_Retire 3 or 5, all gas vintages, new and existing, are retirable (`valret`). L5048-5049: only existing (`initv`) plants must first reach `min_retire_age`, which is 20 years for Gas-CC and Gas-CT (`inputs/plant_characteristics/min_retire_age.csv`). L5066: no retirements before `Sw_Retireyear`.
- `c_model.gms` L555-580: retirable capacity must be ≤ past investment (or exogenous capacity) and fall monotonically (`eq_cap_new_retub`, `eq_cap_new_retmo`, L750-L800). Non-retirable capacity is held equal (`eq_cap_new_noret`, L693).
- `d_objective.gms` L209-216: retirement penalty, `- cost_fom × retire_penalty(t) × (CAP - INV - ...)` for retirable capacity. `inputs/financials/retire_penalty.csv` gives 1.0 through 2034 and 0.5 from 2035 to 2050. `runfiles.csv` L211 describes it as "penalty for retiring a power plant expressed as a fraction of FOM". `report.gms` L1707-1710 repeats the term in the report.
- In every arm's 3 GW case, p25 Gas-CC stays at its 2041 level (or above it), so the model retires no p25 CC.

So the plateau is **not a hard limit**. The model is allowed to retire the CC p25 built by 2041 and does not.

INFERENCE: from 2035, retiring a gas plant saves only half of its fixed O&M (the penalty credits the other half for capacity kept). Its capital is already spent, and it still provides firm capacity in stress periods. So keeping it is cheaper than retiring it, and past the cap the SMR displaces CT and imports instead. I have not checked whether the penalty term is in our system cost (03b2 uses the `systemcost` categories; `report.gms` L1707 is in the objective report block). Worth checking before using this in text.

## Follow-up B: does the knee show in the forcing cost? (added 29 Oct, PRELIMINARY)

Source: `04f_forcing_cost_*.csv` and provisional `04g_cost_parts_step_*.csv`, WECC, 2044-2050, step slope in $B per GW (D41, no fit).

| UON arm | knee | slope before knee | slope after knee |
| --- | --- | --- | --- |
| ref | 1.75-2.0 | 1.39-1.40 (to 1.4 GW) | 1.44-1.48 |
| smrcons | 1.75-2.0 | 3.71-3.73 | 3.76-3.81 |
| gaslow | 2.25-2.5 | 1.86-1.93 | 2.05, 1.97 |
| pvadv | 2.25-2.5 | 1.39-1.46 | 1.44, 1.51 |
| loadhigh | about 2 | 1.23-1.34 | 1.33-1.38 |
| loadlow | none | 1.43-1.83 (noisy) | 1.67-1.80 |

UOS: ref (knee about 1 GW) 1.40-1.42, then 1.40-1.51; loadhigh 1.30-1.36 throughout; loadlow 1.61-1.79.

- The total slope rises by only about 3-7% after the knee in ref, smrcons, gaslow and pvadv. That is about the size of the step-to-step noise in loadlow, so it is a weak signal.
- The provisional capacity and generation parts swing more (e.g. ref capacity 2.65-3.17, generation -1.16 to -1.79 per GW) but move in opposite directions. They don't show a clean step at the knee.

INFERENCE: the knee changes *what* is displaced (planned CC first, then CT and imports), but the cost per GW barely changes. Past the knee, the SMR saves less in energy (less gas burned per GW) and avoids less capacity, so the forcing cost creeps up a little. It doesn't jump.
