# Summary for Caleb: stage 04 results and choices

29 Oct 2026. Written while you were away. Nothing here is merged into `main` or written into `docs/decisions.md`. All dollars are 2024 $. "Diff" = case minus the same arm's 0 GW case (D2). Main numbers are UON `ref`; UOS is only a check (D43d).

## Where things are

| Branch | What | State |
| --- | --- | --- |
| `main` | Stages 00-04 for UON, D1-D46 | merged earlier with your OK |
| `stage/04_uos_check` | UOS run of stage 04 + claim check + agent notes | committed, not pushed |
| `provisional/04g_cost_split` | On top of the above: provisional cost split (04g), reviewed | committed, not pushed |

Files to read, in order:
1. this file
2. `notes/analysis/uos_check.md` (does UOS confirm UON?)
3. `notes/proposals/cost_split.md` (draft D47/D48, the method)
4. `notes/analysis/cost_drivers_uon.md` (what drives the results; facts kept separate from INFERENCE)
5. `notes/text/04_analyze_UON.md` (plain text for each figure)
6. Figures: `outputs/04_analyze/figures/04b_diff_*_UON.png`, `04f_forcing_cost_UON.png`, `04g_cost_split_UON.png`

## Conclusions (UON ref, 3 GW unless stated)

1. **Prices fall a little, most in p25.** Energy price in p25: -1.29 $/MWh in 2050 (-3.5%), -2.35 $/MWh in 2044 (-6.1%). Neighbors -0.51 (-1.3%), all of WECC -0.62 (-1.6%). The all-in price falls less (p25 -2.2%, WECC -0.4%).
2. **The average falls more than the peak.** The p25 peak/average ratio rises from 1.40 to 1.46.
3. **Power flows shift from p25 to its neighbors.** p25 net imports fall by 6.9 TWh in 2050; neighbors' imports rise by 6.7 TWh.
4. **System cost rises steadily, about +0.66%.** Annualized cost (D44), all of WECC, 2044-2050: +$4.28 B. It is all in p25 (+$6.39 B); neighbors fall (-$1.94 B).
5. **The forcing cost is about $1.4 B per GW over 2044-2050** (about $0.2 B per GW-year), slowly rising from 1.39 to 1.48 with level. Highest with conservative SMR cost (`smrcons`, $3.7 B per GW), lowest with high load ($1.3 B).
6. **Provisional cost split (not approved):** +$8.8 B capacity (SMR capital and fixed O&M, net of other plants not built) and -$4.5 B generation (fuel and VOM avoided); transmission about 0. Per GW: capacity +$2.9 B, generation -$1.5 B. In `smrcons` only the capacity part grows (+$5.2 B per GW); the generation savings are the same. The +$7.0 B gap between `smrcons` and `ref` at 3 GW is all capacity cost in p25.
7. **Non-energy payments rise in neighbors and the rest of WECC**, offsetting 57-70% of their energy-payment savings. The provisional payment-type table says the main driver is `state_rps`, whose unit is "not stated" (you chose to leave it so). `res_marg` changes sign. Why `state_rps` payments rise is not explained by the outputs.
8. **UOS confirms the main claims.** Cost (+$4.32 B vs +$4.28 B) and forcing cost ($1.44 B vs $1.43 B per GW) agree within 1%. p25 price and ratio changes hold at every level. Neighbor and WECC price changes and net imports hold in sign, not always in size (largest gaps at 0.5 GW, where the changes are tiny). Some arm-order claims do not hold (e.g. `loadhigh` p25 all-in price rises slightly in UON but falls in UOS).

## Quality

- Stage 04 (UON) passed the Reviewer; three headline numbers recomputed independently.
- UOS ran with no code changes; all checks pass.
- The provisional cost split passed the Reviewer: each of the 26 category mappings checked against `report.gms` at `0c0ea27` (5 citation rows added), and the WECC split recomputed independently (exact match).
- The Verifier has not been used (your call since stage 01).

## Choices for you (my recommended default in brackets)

1. **Adopt the cost split (draft D47, Option A) as a decision?** [Yes. Merge `provisional/04g_cost_split` after you approve; the method is reviewed.]
2. **Spur lines:** keep in capacity as a sub-row. Note the spur share of the ITC credit is not in the sub-row (`report.gms` L1303-1306). [Accept as is.]
3. **DAC term inside the CO2 incentive category** (L1648-1649) stays in "generation", since it cannot be split out. [Accept; it is 0 or tiny here.]
4. **Payment-type and per-MWh tables (draft D48 L2):** they come close to cost view C, which is On hold. [Keep as check tables only; decide view C later.]
5. **UOS claim rule:** "holds" = same sign and within 30% of UON, no size floor. [Accept, or add a floor so 0.5 GW noise does not count.]
6. **Look into the `state_rps` payment rise?** It is the largest non-energy driver, but its unit is not stated. [Yes, later: find the unit in `report.gms` and check which states' RPS prices move.]

Smaller open items from the agents: the neighbor and `rest_wecc` cost curves zig-zag while WECC is smooth; `loadlow` is the most irregular arm; 3,086 of 5,070 group rows for new lines are zero (D46h). None blocks anything.

## Next steps once you choose

- Write D47 (and D48 if you keep it) into `docs/decisions.md`, then merge `stage/04_uos_check` and `provisional/04g_cost_split`.
- Stage 05 (final figures and tables) for the go-on metrics, UON first.
