# UOS check of UON claims (D43d)

Oct 29, 2026 · Builder, branch `stage/04_uos_check` (from `main` at 865ef9f)

UON is the main study. UOS is used only to check claims made from UON (D43d). This file compares claims in text. It is not a combined table or figure (D26). Each batch's numbers come from its own files:

- UON: `outputs/04_analyze/04b_diff_UON.csv`, `04f_forcing_cost_UON.csv`; check report sections "04a-04f UON" in `outputs/checks/04_analyze.md`.
- UOS: `outputs/04_analyze/04b_diff_UOS.csv`, `04c_slopes_UOS.csv`, `04e_neighbor_prices_UOS.csv`, `04f_forcing_cost_UOS.csv`, figures `outputs/04_analyze/figures/*_UOS.png`; check report sections "04a-04f UOS" in the same file.

Every Diff is against the arm's own 0 GW case in its own batch (D2). Nothing here uses one batch to explain the other (D26). Where a claim does not hold, the reason is not given.

## How UOS ran

All five stage 04 scripts ran on `--batch UOS` with no code change: 04a_groups, 04b_diff, 04c_slopes, 04e_neighbor_table, 04f_forcing_cost_curve. Every check in the UOS sections passed: 3 arms (loadhigh, loadlow, ref), 7 levels each (0 to 3 GW, step 0.5), group sizes 1/1/9/23/34, groups sum to wecc, no zero-filled cost rows, every Diff before 2044 is 0, and 6 steps per series (D41). Because no shared code changed, UON was not rerun. The UON output files have the same md5 as before the UOS run, and the UON sections of the check report are byte-identical.

## Verdict rule and choices (options, with the default used)

These are reading choices for this check. None changes an output file. Caleb to confirm or change.

1. **Tolerance.** "Holds" = same sign and |UOS - UON| <= 0.30 x |UON| (UOS within 30 % of the UON value). "Holds in sign only" = same sign, outside 30 %. "Does not hold" = opposite sign. The rule is applied to each value on its own. Options: a symmetric factor (UOS/UON between 1/1.3 and 1.3), or a different band. Default: the one-sided 30 % band, as asked.
2. **No size floor.** Many "sign only" and "does not hold" results are at 0.5 GW, where the UON Diff is very small (for example ref neighbors energy price, 2050, 0.5 GW: -0.039 $/MWh on a 0 GW value of 40.06, or 0.1 %). D43c adopts no size-floor rule, so none is used here. Option: mark values below a floor as "too small to test". Default: no floor.
3. **Year.** Prices and the ratio: 2050, as asked. Net imports: no year was named, so all three post-plant solve years (2044, 2047, 2050) are given, at the same three levels. Option: 2050 only. Default: all three years.
4. **Forcing cost per GW on the same grid.** UON steps are 0.25 GW and UOS steps are 0.5 GW (D41). To compare at the same level, the UON value on each 0.5 GW step is (Diff(l2) - Diff(l1)) / 0.5 from the UON Diffs. This equals the mean of the two 0.25 GW UON steps. The 0 to 3 GW mean (Diff(3 GW) / 3) is given too. The UOS values are the 04f UOS step values. Option: compare only the 0 to 3 GW mean. Default: both. The full 0.25 GW UON curve is in the 04f UON report section (ref, wecc, 2044-2050: 1.390 to 1.484 billion 2024 $ per GW).
5. **Capital and operations splits.** These are added as context for the cost claims (D46i). They are not separate headline claims.
6. **Arm-pattern claims.** No written list of UON claims exists in the repo yet. The loadhigh/loadlow pattern claims below were written by the Builder from the UON values, as orderings of the arms and sign statements inside UON. Caleb should check that they are the claims he means.
7. **Units in this file.** Net imports are shown in TWh (MWh / 1e6) and costs in billion 2024 $. This is display only.

## Summary

Counts of single values over the 75 values per arm (claims listed below):

- `ref`: 45 hold, 28 hold in sign only, 2 do not hold. Both "do not hold" are neighbors net imports at small levels (2047 1.5 GW, 2050 0.5 GW).
- `loadhigh`: 42 hold, 28 hold in sign only, 5 do not hold. Three are the focus all-in price (UON slightly up, UOS down, at all three levels). Two are the peak/average ratio at 0.5 GW (focus and neighbors; UOS values are near 0).
- `loadlow`: 54 hold, 16 hold in sign only, 5 do not hold. These are neighbors and wecc energy price at 0.5 GW, neighbors all-in price at 0.5 GW, focus net imports 2050 at 0.5 GW, and neighbors net imports 2050 at 1.5 GW.

By claim:

- **wecc annualized system cost (2044-2050) and forcing cost per GW: hold in all three arms.** Diffs at 0.5, 1.5 and 3 GW are within 5 % (ref within 1 %). The 0 to 3 GW mean forcing cost is within 1 % in each arm (ref: UON 1.426, UOS 1.441 billion 2024 $ per GW). Every 0.5 GW step of the total holds. The capital and operations splits hold at the three levels. A few operations-only steps hold in sign only.
- **Focus (p25) energy and all-in price fall, peak/average ratio rises (ref): holds** at 0.5, 1.5 and 3 GW.
- **Neighbors and wecc energy and all-in price fall, ratio rises (ref): holds in sign** at every level. For wecc, energy and all-in price magnitudes hold at 1.5 and 3 GW, but the ratio magnitude holds only at 3 GW. For neighbors, UOS falls more than UON (up to 7x at 0.5 GW, about 1.3x to 1.5x at 3 GW).
- **Net imports (ref): p25 imports less (focus Diff < 0).** This holds in sign at all 9 level-years. The magnitude holds at none: UOS:UON ratios run 0.35 to 4.5, and UOS is larger at 8 of 9.
- **Net imports (ref): the neighbors import more (Diff > 0).** In UON this is true in 2044 and 2050 at all three levels and in 2047 at 3 GW. In 2047 at 0.5 and 1.5 GW the UON Diff is about -0.03 TWh. UOS has the same sign at 7 of 9. It does not hold at 2047 1.5 GW (UON -0.030, UOS +0.422 TWh) or at 2050 0.5 GW (UON +0.728, UOS -0.027 TWh). At 3 GW it holds in all three years (2047 and 2050 within 30 %).
- **Arm patterns.** The arm orderings for focus price, focus ratio, wecc cost and forcing cost hold. The UON loadhigh focus all-in price rise does not hold. The UON order of arms for the neighbors and wecc energy price drop at 3 GW does not hold. Details are in the last section.

## Claim by claim


**Average energy price Diff, 2050** (2024 $/MWh; UON / UOS / UOS:UON ratio / verdict)

- focus, 0.5 GW: UON -0.119, UOS -0.099, ratio 0.83: holds
- focus, 1.5 GW: UON -0.366, UOS -0.419, ratio 1.14: holds
- focus, 3 GW: UON -1.294, UOS -1.458, ratio 1.13: holds
- neighbors, 0.5 GW: UON -0.039, UOS -0.289, ratio 7.38: holds in sign only
- neighbors, 1.5 GW: UON -0.279, UOS -0.365, ratio 1.31: holds in sign only
- neighbors, 3 GW: UON -0.505, UOS -0.750, ratio 1.48: holds in sign only
- wecc, 0.5 GW: UON -0.082, UOS -0.256, ratio 3.13: holds in sign only
- wecc, 1.5 GW: UON -0.305, UOS -0.357, ratio 1.17: holds
- wecc, 3 GW: UON -0.624, UOS -0.758, ratio 1.21: holds

**All-in price Diff, 2050** (2024 $/MWh; UON / UOS / UOS:UON ratio / verdict)

- focus, 0.5 GW: UON -0.083, UOS -0.078, ratio 0.94: holds
- focus, 1.5 GW: UON -0.334, UOS -0.342, ratio 1.03: holds
- focus, 3 GW: UON -1.232, UOS -1.393, ratio 1.13: holds
- neighbors, 0.5 GW: UON -0.020, UOS -0.126, ratio 6.17: holds in sign only
- neighbors, 1.5 GW: UON -0.172, UOS -0.185, ratio 1.08: holds
- neighbors, 3 GW: UON -0.270, UOS -0.356, ratio 1.32: holds in sign only
- wecc, 0.5 GW: UON -0.051, UOS -0.091, ratio 1.78: holds in sign only
- wecc, 1.5 GW: UON -0.145, UOS -0.165, ratio 1.14: holds
- wecc, 3 GW: UON -0.271, UOS -0.330, ratio 1.22: holds

**Peak/average ratio Diff, 2050** (ratio; UON / UOS / UOS:UON ratio / verdict)

- focus, 0.5 GW: UON +0.0092, UOS +0.0098, ratio 1.07: holds
- focus, 1.5 GW: UON +0.0196, UOS +0.0250, ratio 1.27: holds
- focus, 3 GW: UON +0.0568, UOS +0.0600, ratio 1.06: holds
- neighbors, 0.5 GW: UON +0.0021, UOS +0.0049, ratio 2.36: holds in sign only
- neighbors, 1.5 GW: UON +0.0035, UOS +0.0033, ratio 0.96: holds
- neighbors, 3 GW: UON +0.0133, UOS +0.0092, ratio 0.69: holds in sign only
- wecc, 0.5 GW: UON +0.0062, UOS +0.0097, ratio 1.57: holds in sign only
- wecc, 1.5 GW: UON +0.0042, UOS +0.0149, ratio 3.59: holds in sign only
- wecc, 3 GW: UON +0.0209, UOS +0.0216, ratio 1.03: holds

**Net imports Diff (`net_import_ann_rep`)** (TWh (MWh / 1e6); UON / UOS / UOS:UON ratio / verdict)

- focus, 2044, 0.5 GW: UON -0.474, UOS -0.690, ratio 1.46: holds in sign only
- focus, 2044, 1.5 GW: UON -1.605, UOS -5.071, ratio 3.16: holds in sign only
- focus, 2044, 3 GW: UON -8.780, UOS -12.255, ratio 1.40: holds in sign only
- focus, 2047, 0.5 GW: UON -0.544, UOS -0.945, ratio 1.74: holds in sign only
- focus, 2047, 1.5 GW: UON -1.087, UOS -4.870, ratio 4.48: holds in sign only
- focus, 2047, 3 GW: UON -8.251, UOS -12.687, ratio 1.54: holds in sign only
- focus, 2050, 0.5 GW: UON -0.744, UOS -0.258, ratio 0.35: holds in sign only
- focus, 2050, 1.5 GW: UON -1.024, UOS -2.322, ratio 2.27: holds in sign only
- focus, 2050, 3 GW: UON -6.890, UOS -9.846, ratio 1.43: holds in sign only
- neighbors, 2044, 0.5 GW: UON +0.140, UOS +0.716, ratio 5.11: holds in sign only
- neighbors, 2044, 1.5 GW: UON +0.692, UOS +2.734, ratio 3.95: holds in sign only
- neighbors, 2044, 3 GW: UON +5.221, UOS +8.127, ratio 1.56: holds in sign only
- neighbors, 2047, 0.5 GW: UON -0.028, UOS -0.592, ratio 21.04: holds in sign only
- neighbors, 2047, 1.5 GW: UON -0.030, UOS +0.422, ratio -14.27: does not hold
- neighbors, 2047, 3 GW: UON +5.737, UOS +6.789, ratio 1.18: holds
- neighbors, 2050, 0.5 GW: UON +0.728, UOS -0.027, ratio -0.04: does not hold
- neighbors, 2050, 1.5 GW: UON +0.984, UOS +0.846, ratio 0.86: holds
- neighbors, 2050, 3 GW: UON +6.740, UOS +7.426, ratio 1.10: holds

**Annualized system cost Diff, wecc, 2044-2050 total (D44)** (billion 2024 $; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0.5 GW: UON +0.696, UOS +0.698, ratio 1.00: holds
- wecc, 1.5 GW: UON +2.097, UOS +2.111, ratio 1.01: holds
- wecc, 3 GW: UON +4.279, UOS +4.323, ratio 1.01: holds

**capital only (D46i)** (billion 2024 $; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0.5 GW: UON +1.180, UOS +1.106, ratio 0.94: holds
- wecc, 1.5 GW: UON +3.274, UOS +3.172, ratio 0.97: holds
- wecc, 3 GW: UON +6.516, UOS +6.374, ratio 0.98: holds

**operations only (D46i)** (billion 2024 $; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0.5 GW: UON -0.484, UOS -0.408, ratio 0.84: holds
- wecc, 1.5 GW: UON -1.177, UOS -1.061, ratio 0.90: holds
- wecc, 3 GW: UON -2.237, UOS -2.051, ratio 0.92: holds

**Forcing cost per GW, wecc, 2044-2050 total, on 0.5 GW steps** (billion 2024 $ per GW; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0-0.5: UON 1.393, UOS 1.396, ratio 1.00: holds
- wecc, 0.5-1: UON 1.401, UOS 1.421, ratio 1.01: holds
- wecc, 1-1.5: UON 1.401, UOS 1.405, ratio 1.00: holds
- wecc, 1.5-2: UON 1.432, UOS 1.475, ratio 1.03: holds
- wecc, 2-2.5: UON 1.454, UOS 1.442, ratio 0.99: holds
- wecc, 2.5-3: UON 1.478, UOS 1.507, ratio 1.02: holds
- wecc, 0-3: UON 1.426, UOS 1.441, ratio 1.01: holds

**capital only** (billion 2024 $ per GW; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0-0.5: UON +2.360, UOS +2.212, ratio 0.94: holds
- wecc, 0.5-1: UON +2.132, UOS +1.817, ratio 0.85: holds
- wecc, 1-1.5: UON +2.056, UOS +2.315, ratio 1.13: holds
- wecc, 1.5-2: UON +2.008, UOS +2.350, ratio 1.17: holds
- wecc, 2-2.5: UON +2.353, UOS +2.205, ratio 0.94: holds
- wecc, 2.5-3: UON +2.123, UOS +1.850, ratio 0.87: holds
- wecc, 0-3: UON +2.172, UOS +2.125, ratio 0.98: holds

**operations only** (billion 2024 $ per GW; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0-0.5: UON -0.967, UOS -0.816, ratio 0.84: holds
- wecc, 0.5-1: UON -0.731, UOS -0.396, ratio 0.54: holds in sign only
- wecc, 1-1.5: UON -0.655, UOS -0.910, ratio 1.39: holds in sign only
- wecc, 1.5-2: UON -0.577, UOS -0.874, ratio 1.52: holds in sign only
- wecc, 2-2.5: UON -0.899, UOS -0.763, ratio 0.85: holds
- wecc, 2.5-3: UON -0.645, UOS -0.343, ratio 0.53: holds in sign only
- wecc, 0-3: UON -0.746, UOS -0.684, ratio 0.92: holds

### Arm `loadhigh`


**Average energy price Diff, 2050** (2024 $/MWh; UON / UOS / UOS:UON ratio / verdict)

- focus, 0.5 GW: UON -0.189, UOS -0.002, ratio 0.01: holds in sign only
- focus, 1.5 GW: UON -0.172, UOS -0.281, ratio 1.64: holds in sign only
- focus, 3 GW: UON -0.764, UOS -0.821, ratio 1.07: holds
- neighbors, 0.5 GW: UON -0.212, UOS -0.056, ratio 0.27: holds in sign only
- neighbors, 1.5 GW: UON -0.417, UOS -0.359, ratio 0.86: holds
- neighbors, 3 GW: UON -1.152, UOS -0.769, ratio 0.67: holds in sign only
- wecc, 0.5 GW: UON -0.192, UOS -0.054, ratio 0.28: holds in sign only
- wecc, 1.5 GW: UON -0.359, UOS -0.288, ratio 0.80: holds
- wecc, 3 GW: UON -0.962, UOS -0.630, ratio 0.66: holds in sign only

**All-in price Diff, 2050** (2024 $/MWh; UON / UOS / UOS:UON ratio / verdict)

- focus, 0.5 GW: UON +0.139, UOS -0.039, ratio -0.28: does not hold
- focus, 1.5 GW: UON +0.131, UOS -0.091, ratio -0.69: does not hold
- focus, 3 GW: UON +0.068, UOS -0.454, ratio -6.68: does not hold
- neighbors, 0.5 GW: UON -0.071, UOS -0.049, ratio 0.69: holds in sign only
- neighbors, 1.5 GW: UON -0.167, UOS -0.246, ratio 1.47: holds in sign only
- neighbors, 3 GW: UON -0.209, UOS -0.417, ratio 1.99: holds in sign only
- wecc, 0.5 GW: UON -0.035, UOS -0.045, ratio 1.29: holds
- wecc, 1.5 GW: UON -0.102, UOS -0.151, ratio 1.48: holds in sign only
- wecc, 3 GW: UON -0.118, UOS -0.281, ratio 2.39: holds in sign only

**Peak/average ratio Diff, 2050** (ratio; UON / UOS / UOS:UON ratio / verdict)

- focus, 0.5 GW: UON +0.0012, UOS -0.0010, ratio -0.85: does not hold
- focus, 1.5 GW: UON +0.0047, UOS +0.0079, ratio 1.69: holds in sign only
- focus, 3 GW: UON +0.0200, UOS +0.0224, ratio 1.12: holds
- neighbors, 0.5 GW: UON +0.0048, UOS -0.0001, ratio -0.01: does not hold
- neighbors, 1.5 GW: UON +0.0085, UOS +0.0046, ratio 0.53: holds in sign only
- neighbors, 3 GW: UON +0.0189, UOS +0.0112, ratio 0.59: holds in sign only
- wecc, 0.5 GW: UON +0.0046, UOS +0.0002, ratio 0.04: holds in sign only
- wecc, 1.5 GW: UON +0.0086, UOS +0.0038, ratio 0.44: holds in sign only
- wecc, 3 GW: UON +0.0164, UOS +0.0095, ratio 0.58: holds in sign only

**Net imports Diff (`net_import_ann_rep`)** (TWh (MWh / 1e6); UON / UOS / UOS:UON ratio / verdict)

- focus, 2044, 0.5 GW: UON -0.292, UOS -0.417, ratio 1.43: holds in sign only
- focus, 2044, 1.5 GW: UON -0.737, UOS -1.142, ratio 1.55: holds in sign only
- focus, 2044, 3 GW: UON -6.754, UOS -7.604, ratio 1.13: holds
- focus, 2047, 0.5 GW: UON -0.553, UOS -0.560, ratio 1.01: holds
- focus, 2047, 1.5 GW: UON -1.052, UOS -1.902, ratio 1.81: holds in sign only
- focus, 2047, 3 GW: UON -5.236, UOS -5.432, ratio 1.04: holds
- focus, 2050, 0.5 GW: UON -0.664, UOS -0.482, ratio 0.73: holds
- focus, 2050, 1.5 GW: UON -1.173, UOS -1.731, ratio 1.48: holds in sign only
- focus, 2050, 3 GW: UON -4.807, UOS -4.949, ratio 1.03: holds
- neighbors, 2044, 0.5 GW: UON +0.195, UOS +0.363, ratio 1.86: holds in sign only
- neighbors, 2044, 1.5 GW: UON +1.685, UOS +2.394, ratio 1.42: holds in sign only
- neighbors, 2044, 3 GW: UON +6.615, UOS +7.279, ratio 1.10: holds
- neighbors, 2047, 0.5 GW: UON +0.320, UOS +0.463, ratio 1.45: holds in sign only
- neighbors, 2047, 1.5 GW: UON +2.397, UOS +4.161, ratio 1.74: holds in sign only
- neighbors, 2047, 3 GW: UON +7.114, UOS +7.206, ratio 1.01: holds
- neighbors, 2050, 0.5 GW: UON +0.874, UOS +0.711, ratio 0.81: holds
- neighbors, 2050, 1.5 GW: UON +2.402, UOS +3.202, ratio 1.33: holds in sign only
- neighbors, 2050, 3 GW: UON +5.228, UOS +6.297, ratio 1.20: holds

**Annualized system cost Diff, wecc, 2044-2050 total (D44)** (billion 2024 $; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0.5 GW: UON +0.660, UOS +0.656, ratio 0.99: holds
- wecc, 1.5 GW: UON +1.942, UOS +1.970, ratio 1.01: holds
- wecc, 3 GW: UON +3.961, UOS +3.985, ratio 1.01: holds

**capital only (D46i)** (billion 2024 $; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0.5 GW: UON +1.223, UOS +1.081, ratio 0.88: holds
- wecc, 1.5 GW: UON +3.650, UOS +3.471, ratio 0.95: holds
- wecc, 3 GW: UON +6.772, UOS +7.065, ratio 1.04: holds

**operations only (D46i)** (billion 2024 $; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0.5 GW: UON -0.563, UOS -0.425, ratio 0.75: holds
- wecc, 1.5 GW: UON -1.707, UOS -1.501, ratio 0.88: holds
- wecc, 3 GW: UON -2.811, UOS -3.081, ratio 1.10: holds

**Forcing cost per GW, wecc, 2044-2050 total, on 0.5 GW steps** (billion 2024 $ per GW; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0-0.5: UON 1.319, UOS 1.312, ratio 0.99: holds
- wecc, 0.5-1: UON 1.250, UOS 1.295, ratio 1.04: holds
- wecc, 1-1.5: UON 1.315, UOS 1.333, ratio 1.01: holds
- wecc, 1.5-2: UON 1.331, UOS 1.340, ratio 1.01: holds
- wecc, 2-2.5: UON 1.341, UOS 1.358, ratio 1.01: holds
- wecc, 2.5-3: UON 1.366, UOS 1.332, ratio 0.97: holds
- wecc, 0-3: UON 1.320, UOS 1.328, ratio 1.01: holds

**capital only** (billion 2024 $ per GW; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0-0.5: UON +2.446, UOS +2.161, ratio 0.88: holds
- wecc, 0.5-1: UON +2.569, UOS +2.321, ratio 0.90: holds
- wecc, 1-1.5: UON +2.284, UOS +2.461, ratio 1.08: holds
- wecc, 1.5-2: UON +2.207, UOS +2.322, ratio 1.05: holds
- wecc, 2-2.5: UON +1.974, UOS +2.339, ratio 1.18: holds
- wecc, 2.5-3: UON +2.064, UOS +2.527, ratio 1.22: holds
- wecc, 0-3: UON +2.257, UOS +2.355, ratio 1.04: holds

**operations only** (billion 2024 $ per GW; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0-0.5: UON -1.126, UOS -0.849, ratio 0.75: holds
- wecc, 0.5-1: UON -1.319, UOS -1.025, ratio 0.78: holds
- wecc, 1-1.5: UON -0.970, UOS -1.128, ratio 1.16: holds
- wecc, 1.5-2: UON -0.876, UOS -0.983, ratio 1.12: holds
- wecc, 2-2.5: UON -0.633, UOS -0.982, ratio 1.55: holds in sign only
- wecc, 2.5-3: UON -0.697, UOS -1.195, ratio 1.71: holds in sign only
- wecc, 0-3: UON -0.937, UOS -1.027, ratio 1.10: holds

### Arm `loadlow`


**Average energy price Diff, 2050** (2024 $/MWh; UON / UOS / UOS:UON ratio / verdict)

- focus, 0.5 GW: UON -0.333, UOS -0.520, ratio 1.56: holds in sign only
- focus, 1.5 GW: UON -0.955, UOS -0.857, ratio 0.90: holds
- focus, 3 GW: UON -2.356, UOS -2.257, ratio 0.96: holds
- neighbors, 0.5 GW: UON -0.155, UOS +0.071, ratio -0.46: does not hold
- neighbors, 1.5 GW: UON -0.399, UOS -0.153, ratio 0.38: holds in sign only
- neighbors, 3 GW: UON -0.685, UOS -0.530, ratio 0.77: holds
- wecc, 0.5 GW: UON -0.131, UOS +0.001, ratio -0.01: does not hold
- wecc, 1.5 GW: UON -0.390, UOS -0.176, ratio 0.45: holds in sign only
- wecc, 3 GW: UON -0.676, UOS -0.574, ratio 0.85: holds

**All-in price Diff, 2050** (2024 $/MWh; UON / UOS / UOS:UON ratio / verdict)

- focus, 0.5 GW: UON -0.402, UOS -0.690, ratio 1.72: holds in sign only
- focus, 1.5 GW: UON -1.170, UOS -1.079, ratio 0.92: holds
- focus, 3 GW: UON -2.892, UOS -2.920, ratio 1.01: holds
- neighbors, 0.5 GW: UON -0.090, UOS +0.038, ratio -0.42: does not hold
- neighbors, 1.5 GW: UON -0.271, UOS -0.121, ratio 0.45: holds in sign only
- neighbors, 3 GW: UON -0.579, UOS -0.381, ratio 0.66: holds in sign only
- wecc, 0.5 GW: UON -0.093, UOS -0.029, ratio 0.32: holds in sign only
- wecc, 1.5 GW: UON -0.276, UOS -0.173, ratio 0.63: holds in sign only
- wecc, 3 GW: UON -0.604, UOS -0.462, ratio 0.77: holds

**Peak/average ratio Diff, 2050** (ratio; UON / UOS / UOS:UON ratio / verdict)

- focus, 0.5 GW: UON +0.0143, UOS +0.0213, ratio 1.49: holds in sign only
- focus, 1.5 GW: UON +0.0387, UOS +0.0350, ratio 0.90: holds
- focus, 3 GW: UON +0.1017, UOS +0.0945, ratio 0.93: holds
- neighbors, 0.5 GW: UON +0.0078, UOS +0.0043, ratio 0.55: holds in sign only
- neighbors, 1.5 GW: UON +0.0138, UOS +0.0099, ratio 0.72: holds
- neighbors, 3 GW: UON +0.0208, UOS +0.0193, ratio 0.93: holds
- wecc, 0.5 GW: UON +0.0065, UOS +0.0050, ratio 0.77: holds
- wecc, 1.5 GW: UON +0.0139, UOS +0.0108, ratio 0.77: holds
- wecc, 3 GW: UON +0.0230, UOS +0.0239, ratio 1.04: holds

**Net imports Diff (`net_import_ann_rep`)** (TWh (MWh / 1e6); UON / UOS / UOS:UON ratio / verdict)

- focus, 2044, 0.5 GW: UON -1.000, UOS -0.850, ratio 0.85: holds
- focus, 2044, 1.5 GW: UON -2.995, UOS -2.632, ratio 0.88: holds
- focus, 2044, 3 GW: UON -7.678, UOS -7.856, ratio 1.02: holds
- focus, 2047, 0.5 GW: UON -0.629, UOS -0.565, ratio 0.90: holds
- focus, 2047, 1.5 GW: UON -2.381, UOS -2.492, ratio 1.05: holds
- focus, 2047, 3 GW: UON -5.781, UOS -7.020, ratio 1.21: holds
- focus, 2050, 0.5 GW: UON -0.653, UOS +0.014, ratio -0.02: does not hold
- focus, 2050, 1.5 GW: UON -2.346, UOS -2.442, ratio 1.04: holds
- focus, 2050, 3 GW: UON -5.414, UOS -6.259, ratio 1.16: holds
- neighbors, 2044, 0.5 GW: UON +0.763, UOS +0.732, ratio 0.96: holds
- neighbors, 2044, 1.5 GW: UON +1.768, UOS +2.757, ratio 1.56: holds in sign only
- neighbors, 2044, 3 GW: UON +5.727, UOS +9.621, ratio 1.68: holds in sign only
- neighbors, 2047, 0.5 GW: UON +0.831, UOS +1.871, ratio 2.25: holds in sign only
- neighbors, 2047, 1.5 GW: UON +0.939, UOS +1.195, ratio 1.27: holds
- neighbors, 2047, 3 GW: UON +3.037, UOS +2.549, ratio 0.84: holds
- neighbors, 2050, 0.5 GW: UON +0.030, UOS +1.182, ratio 39.23: holds in sign only
- neighbors, 2050, 1.5 GW: UON -0.499, UOS +0.781, ratio -1.57: does not hold
- neighbors, 2050, 3 GW: UON +3.963, UOS +2.323, ratio 0.59: holds in sign only

**Annualized system cost Diff, wecc, 2044-2050 total (D44)** (billion 2024 $; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0.5 GW: UON +0.795, UOS +0.831, ratio 1.05: holds
- wecc, 1.5 GW: UON +2.459, UOS +2.460, ratio 1.00: holds
- wecc, 3 GW: UON +4.966, UOS +5.000, ratio 1.01: holds

**capital only (D46i)** (billion 2024 $; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0.5 GW: UON +1.138, UOS +1.212, ratio 1.06: holds
- wecc, 1.5 GW: UON +3.518, UOS +3.520, ratio 1.00: holds
- wecc, 3 GW: UON +6.932, UOS +7.051, ratio 1.02: holds

**operations only (D46i)** (billion 2024 $; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0.5 GW: UON -0.344, UOS -0.381, ratio 1.11: holds
- wecc, 1.5 GW: UON -1.059, UOS -1.060, ratio 1.00: holds
- wecc, 3 GW: UON -1.966, UOS -2.051, ratio 1.04: holds

**Forcing cost per GW, wecc, 2044-2050 total, on 0.5 GW steps** (billion 2024 $ per GW; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0-0.5: UON 1.589, UOS 1.662, ratio 1.05: holds
- wecc, 0.5-1: UON 1.670, UOS 1.652, ratio 0.99: holds
- wecc, 1-1.5: UON 1.659, UOS 1.607, ratio 0.97: holds
- wecc, 1.5-2: UON 1.629, UOS 1.618, ratio 0.99: holds
- wecc, 2-2.5: UON 1.608, UOS 1.675, ratio 1.04: holds
- wecc, 2.5-3: UON 1.776, UOS 1.787, ratio 1.01: holds
- wecc, 0-3: UON 1.655, UOS 1.667, ratio 1.01: holds

**capital only** (billion 2024 $ per GW; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0-0.5: UON +2.277, UOS +2.423, ratio 1.06: holds
- wecc, 0.5-1: UON +2.406, UOS +2.351, ratio 0.98: holds
- wecc, 1-1.5: UON +2.353, UOS +2.266, ratio 0.96: holds
- wecc, 1.5-2: UON +2.278, UOS +2.303, ratio 1.01: holds
- wecc, 2-2.5: UON +2.248, UOS +2.254, ratio 1.00: holds
- wecc, 2.5-3: UON +2.303, UOS +2.505, ratio 1.09: holds
- wecc, 0-3: UON +2.311, UOS +2.350, ratio 1.02: holds

**operations only** (billion 2024 $ per GW; UON / UOS / UOS:UON ratio / verdict)

- wecc, 0-0.5: UON -0.687, UOS -0.761, ratio 1.11: holds
- wecc, 0.5-1: UON -0.736, UOS -0.699, ratio 0.95: holds
- wecc, 1-1.5: UON -0.694, UOS -0.659, ratio 0.95: holds
- wecc, 1.5-2: UON -0.648, UOS -0.686, ratio 1.06: holds
- wecc, 2-2.5: UON -0.640, UOS -0.578, ratio 0.90: holds
- wecc, 2.5-3: UON -0.527, UOS -0.717, ratio 1.36: holds in sign only
- wecc, 0-3: UON -0.655, UOS -0.684, ratio 1.04: holds

## Arm-pattern claims (loadhigh, loadlow)

Each claim is an ordering or sign inside one batch, checked in UON and then on its own in UOS. Values are 2050 Diffs at 3 GW unless stated otherwise.

1. **Focus energy price drop: loadlow > ref > loadhigh.** UON -2.356 / -1.294 / -0.764; UOS -2.257 / -1.458 / -0.821 $/MWh. **Holds** (same order, each within 30 %).
2. **Focus all-in price: loadlow and ref fall, loadhigh rises slightly.** UON loadhigh +0.139 / +0.131 / +0.068 at 0.5 / 1.5 / 3 GW. UOS loadhigh -0.039 / -0.091 / -0.454. **Does not hold** for loadhigh. The loadlow and ref parts hold (loadlow -2.892 vs -2.920; ref -1.232 vs -1.393).
3. **Focus peak/average ratio rise: loadlow > ref > loadhigh.** UON +0.1017 / +0.0568 / +0.0200; UOS +0.0945 / +0.0600 / +0.0224. **Holds.**
4. **The peak/average ratio rises in every arm, group and level checked (UON: all 27 values positive).** UOS: 25 of 27 positive. Loadhigh at 0.5 GW is -0.0010 (focus) and -0.00005 (neighbors). **Holds except loadhigh at 0.5 GW.**
5. **Prices fall in every arm, group and level checked, except the loadhigh focus all-in price (UON).** UOS: loadlow at 0.5 GW rises slightly for neighbors energy price (+0.071), wecc energy price (+0.001) and neighbors all-in price (+0.038). **Holds except loadlow at 0.5 GW.** The loadhigh focus exception in UON is not seen in UOS (claim 2).
6. **Neighbors energy price drop at 3 GW: loadhigh > loadlow > ref.** UON -1.152 / -0.685 / -0.505; UOS loadhigh -0.769, loadlow -0.530, ref -0.750. **Does not hold** as an ordering. Loadhigh is still the largest drop, but only just above ref, and ref and loadlow swap. The loadhigh magnitude holds in sign only (ratio 0.67).
7. **wecc energy price drop at 3 GW: loadhigh > loadlow > ref.** UON -0.962 / -0.676 / -0.624; UOS loadhigh -0.630, loadlow -0.574, ref -0.758. **Does not hold** as an ordering. In UOS, ref has the largest drop.
8. **wecc annualized cost Diff and forcing cost: loadlow > ref > loadhigh.** Cost Diff at 3 GW: UON 4.966 / 4.279 / 3.961; UOS 5.000 / 4.323 / 3.985 billion 2024 $. Mean forcing cost 0 to 3 GW: UON 1.655 / 1.426 / 1.320; UOS 1.667 / 1.441 / 1.328 billion 2024 $ per GW. **Holds**, each value within 5 %.
9. **The wecc forcing cost (total) is positive at every step and has no sign change, in every arm.** UOS: all 0.5 GW steps are positive in all three arms (04f UOS report: n_dir_changes = 0 for wecc). **Holds.**
10. **Focus net imports drop at 3 GW, 2050: ref > loadlow > loadhigh.** UON -6.890 / -5.414 / -4.807; UOS -9.846 / -6.259 / -4.949 TWh. **Holds as an ordering.** The ref magnitude holds in sign only (ratio 1.43).
