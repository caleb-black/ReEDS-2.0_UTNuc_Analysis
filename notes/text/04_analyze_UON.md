# Stage 04, UON: plain-language text

Draft by the Explainer. Caleb has not yet agreed to these figure sentences (stage 05 check).
Sources: `outputs/checks/04_analyze.md`, `outputs/checks/03_derive.md` (03b2), the figures and CSVs in `outputs/04_analyze/`, `docs/data_dictionary.md`, `docs/decisions.md`. The cost analyst's notes are not used.

Terms. Diff = the case minus the same arm's own 0 GW case (D2). "focus" = p25. "neighbors" = nine zones joined to p25 by a line (D35). "ref" = reference arm. Costs are in 2024 $. Annualized cost is reported for 2044 to 2050 (D44).

## 1. Stage summary

Stage 04 ran on the UON batch only. UON is the main study (D43d). It has six arms: ref, gaslow, loadhigh, loadlow, pvadv and smrcons. Each arm has 13 levels, 0 to 3 GW in 0.25 GW steps.
The stage made group tables for five groups: focus, utah_rest, neighbors, rest_wecc and wecc. It then made the Diff against the arm's own 0 GW case, the step slopes between levels, a neighbor price table, and the forcing-cost curve (04f).
All checks in the report pass. The Diff is 0 at 0 GW and 0 before 2044. The four groups add up to wecc. The step slopes add up to the Diff at 3 GW.
Two data limits appear in the report. For 1,963 of 5,070 all-in price rows, the unit is not stated (state_rps/nat_gen dollars). For new lines, 3,086 of 5,070 group rows were filled with 0 where stage 01 had no row (D46h).
The report also lists where the curves are not smooth. Many series change direction or have a kink. For example, 138 of 240 annualized cost series change direction. The report does not explain why.
The 03b2 check found that the annualized cost matches a second, independent calculation (largest relative gap 4.21e-16).

## 2. Figures

### 04b_diff_avg_energy_price_UON.png
This figure shows the Diff in average energy price (2024 $/MWh) against level (0 to 3 GW), for each arm, group and for 2044, 2047 and 2050. In UON ref at 3 GW, the focus price falls by 2.35 $/MWh in 2044 and by 1.29 $/MWh in 2050. The wecc price falls by 0.62 $/MWh in 2050.
Shape notes: Direction changes are rarest for wecc in 2047 and focus in 2044 (none). In 2050 the neighbors curve changes direction in all six arms. Kinks of size 1.0 or more appear for neighbors, rest_wecc and wecc in 2044 and 2050 (for example neighbors pvadv 1.4 at 2.75 GW in 2050). Focus has no kink. In all, 35 of 90 series change direction and 17 have a kink.

### 04b_diff_avg_allin_price_UON.png
This figure shows the Diff in average all-in price (2024 $/MWh) against level, for each arm, group and year. In UON ref at 3 GW in 2050, the focus all-in price falls by 1.23 $/MWh (-2.2%). The wecc all-in price falls by 0.27 $/MWh (-0.4%).
Shape notes: Direction changes are common. 55 of 90 series change direction and 35 have a kink. Neighbors, rest_wecc and wecc change direction in many arms in all three years. Focus is smoother in 2044 and 2047 (no change). The unit is not stated for part of the rows (see the summary).

### 04b_diff_peak_avg_ratio_UON.png
This figure shows the Diff in the peak/average price ratio against level, for each arm, group and year. In UON ref at 3 GW in 2050, the focus ratio rises by 0.057 (from 1.402 to 1.459). The wecc ratio rises by 0.021.
Shape notes: 60 of 90 series change direction and 35 have a kink. Focus changes direction in gaslow in all three years and in loadhigh and smrcons in 2050. Rest_wecc and neighbors change direction in most arms in 2044 and 2047. Wecc has kinks in ref, smrcons, pvadv, loadlow and gaslow in 2050.

### 04b_diff_annualized_cost_UON.png
This figure shows the Diff in annualized system cost, summed over 2044 to 2050 (2024 $), against level. In UON ref at 3 GW, the focus cost rises by 6.39 billion $ (+23.2%). The wecc cost rises by 4.28 billion $ (+0.66%). The neighbors cost falls by 1.94 billion $.
Shape notes: Focus and wecc have no direction change in any arm. Utah_rest, neighbors and rest_wecc change direction in most arms. Neighbors and rest_wecc show the most (for example loadlow neighbors at 0.25, 0.5, 0.75, 1, 1.25, 1.5, 2.5 and 2.75 GW). In all, 138 of 240 cost series change direction and 53 have a kink.

### 04b_diff_net_imports_UON.png
This figure shows the Diff in net imports (MWh) against level, for each arm, group and year. In UON ref at 3 GW in 2050, focus net imports fall by 6.89 million MWh. Neighbors rise by 6.74 million MWh. Wecc changes by -0.13 million MWh.
Shape notes: Wecc and focus (2044) have few changes. Neighbors, rest_wecc and utah_rest change direction in most arms, mainly in 2047 and 2050 (loadlow has the most). In all, 68 of 90 series change direction and 31 have a kink.

### 04b_diff_new_lines_UON.png
This figure shows the Diff in new transmission line capacity (MW) against level, for each arm, group and year. In UON ref at 3 GW in 2050, focus new lines rise by 37 MW (from 140 to 177 MW). Wecc new lines rise by 20 MW (from 3,100 to 3,120 MW).
Shape notes: Utah_rest has no direction change (it is 0 in the plot). All other groups change direction in most arms and years. 68 of 90 series change direction and 45 have a kink. Kinks of 1.5 or more appear for example in smrcons wecc (1.8 at 1.75 GW) and ref focus (1.8 at 1.5 GW) in 2050. Many new-line rows were zero-filled (see the summary).

### 04f_forcing_cost_UON.png
This figure shows the step change in annualized cost per GW between neighboring levels (billion $ per GW). The top row is the 2044-2050 total by group. The bottom row is wecc for each year. For wecc, the total is 1.39 to 1.48 billion $/GW in ref. It is 3.71 to 3.81 billion $/GW in smrcons. Loadhigh is the lowest (1.23 to 1.38).
Shape notes: Wecc and focus have no direction change in any arm. Neighbors change direction 4 to 8 times, rest_wecc 0 to 6 times, utah_rest 0 to 5 times. Loadlow neighbors has 8 changes and the largest kink (1.769 at 0.25 GW). Loadlow rest_wecc has 5 changes and kink 1.306 at 0.25 GW. Ref rest_wecc has kink 1.348 at 2.5 GW.

## 3. Headline findings (UON)

1. Prescribed nuclear in p25 lowers the focus average energy price in ref. At 3 GW the change is -2.35 $/MWh in 2044 (-6.1%) and -1.29 $/MWh in 2050 (-3.5%). Source: 04b_diff_UON.csv, ref, 3 GW.
2. The all-in price falls less than the energy price. In ref at 3 GW in 2050 the focus all-in change is -1.23 $/MWh (-2.2%) and the wecc change is -0.27 $/MWh (-0.4%). The wecc energy price change is -0.62 $/MWh (-1.6%). Source: 04b_diff_UON.csv.
3. System cost rises with the nuclear capacity, mostly in focus. In ref at 3 GW the 2044-2050 annualized cost rises by 6.39 billion $ in focus (+23.2%) and 4.28 billion $ in wecc (+0.66%). Neighbors fall by 1.94 billion $. Source: 04b_diff_UON.csv.
4. Power flows shift. In ref at 3 GW in 2050, focus net imports fall by 6.89 million MWh and neighbors net imports rise by 6.74 million MWh. Source: 04b_diff_UON.csv.
5. The peak/average ratio in focus rises with capacity. In ref at 3 GW in 2050 it rises by 0.057 (1.402 to 1.459). Source: 04b_diff_UON.csv.
6. The cost per GW depends on the arm. The wecc forcing cost is 1.39 to 1.48 billion $/GW in ref and 3.71 to 3.81 billion $/GW in smrcons. Source: 04f section of the check report.

## 4. Open questions

1. Why do the neighbors and rest_wecc curves zig-zag? In the 04f figure the neighbors forcing cost changes sign up to 8 times (loadlow) while wecc has none. The outputs show this. They do not explain it.
2. Why is the smrcons forcing cost so high? Wecc is 3.71 to 3.81 billion $/GW against 1.39 to 1.48 in ref. The outputs do not say why. (The check report gives no cause.)
3. Why do ref and smrcons look almost the same in the price and flow figures? For example the ref and smrcons focus energy price Diff at 3 GW in 2050 are -1.294 and -1.290 $/MWh. The cost Diff is very different. The outputs do not explain this.
4. Why are the loadlow curves more irregular? The loadlow arm has the largest kinks in the 04f table (1.769 neighbors, 1.306 rest_wecc) and spikes in the new-lines figure (2047). The outputs do not explain this.
5. How much do the zero-filled new-line rows (3,086 of 5,070) and the all-in price rows with an unstated unit (1,963 of 5,070) change the picture? The report counts them. It does not test their effect. INFERENCE: the new-line results should be read with care until this is known.
