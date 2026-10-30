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
