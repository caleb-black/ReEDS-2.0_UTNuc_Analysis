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

## Next checks if you want to go further
- Reserve-margin capacity (firm capacity) by region, to test reading 3 (CT up, wind down).
- p10 / z28 at every level and arm, to see if the swap is a steady effect or a tie between two similar options.
- Line flows p25-p33 and p25-p10 (`tran_flow_rep_ann`), to see where the SMR energy actually goes.
- UOS, to see if p33 and the p10/z28 swap also appear there.
