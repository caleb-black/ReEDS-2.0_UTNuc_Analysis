# p25 nuclear study: data dictionary

Oct 27, 2026 · Caleb

This is the single place for the names, terms and files of the study. Decisions are in `docs/decisions.md`. All model citations are for ReEDS commit `0c0ea27` in `ReEDS-Model/ReEDS` (5 Aug 2026). The report code is now in `reeds/core/terminus/`: `report.gms`, `report_params.csv`, and `report_calcs.py` (transmission outputs).

## Model setup (0c0ea27 runs)

These settings are the same for every case. Only the arm switches in "Arms and their baselines" change.

| Switch | Value | Meaning, from `cases.csv` at `0c0ea27` |
| --- | --- | --- |
| `GSw_Region` | `interconnect/western` | Keep the zones in the western interconnect (L48). |
| `GSw_ZoneSet` | `z132` | Zone set z132 (L49). In the west it has 34 zones. `p28` and `p30` are merged into one zone, `z28` (Arizona). `p25` and `p26` are unchanged (`inputs/zones/z132/hierarchy.csv`). |
| `GSw_GasCurve` | 2 | Static gas supply curve (L142). |
| `GSw_Clean_Air_Act` | 0 | Clean Air Act Section 111 provisions off (L107). |
| `GSw_Upgrades` | 0 | Upgrades off (L348). |
| `demandscen` | EER scenarios (per arm) | Load scenario (L32). |
| `GSw_PRM_CapCredit` | 0 (default) | Stress-period reserve margin (L259). Your `res_marg` rows use stress blocks, which matches this. |

The old switches `GSw_OPGW`, `GSw_NoReinforcement` and `GSw_RegionResolution` do not exist at `0c0ea27`.

## Region groups

Every region belongs to exactly one of the first four groups. `wecc` is the sum of all regions (D7, D13).

| Group name | Regions | How the list is made |
| --- | --- | --- |
| `focus` | p25 | Fixed. The nuclear plant is here. |
| `utah_rest` | p26 | Fixed. The other half of Utah. |
| `neighbors` | Zones directly connected to p25, without p26 | From `tran_out` in the 0 GW `med` case. Read both the `r` and `rr` columns. The list is fixed for all cases. Expected from the z132 interface list: p12, p16, p21, p27, p31, p33, z28 (`inputs/zones/z132/interfaces_r.csv`). If `tran_out` gives a different list, stop and check. |
| `rest_wecc` | All other western zones | The 34 western zones of z132, minus the three groups above. |
| `wecc` | All 34 western zones | The whole system. |

## Study terms

| Term | Meaning |
| --- | --- |
| Arm | A set of cases that share all assumptions except the nuclear level. Example: `med`. |
| Level | GW of nuclear prescribed in p25 from 2044: 0, 0.5, 1, 1.5, 2, 2.5 or 3. In folder names, `p` is the decimal point (`1p5G` = 1.5 GW). |
| Case | One run: one arm at one level. Folder name = `<batch>_<date>_<level>_<arm>`. |
| Trunk | The 0.5 GW case of an arm. A full run from 2010. |
| Branch | Any other level. A copy of the trunk restarted at 2044 with a different nuclear size. |
| Trunk gate | The check that every branch equals its trunk through 2041, in every file (D4). |
| Shared levels | 0, 0.5, 1.5, 2.5 GW. Used for slopes that compare arms (D3). |
| Solve year | A year the model solves: 2010, 2015, 2020, 2023, then every 3 years to 2050. Post-plant years are 2044, 2047, 2050. |
| Block | One representative 3-hour period (152 per year, names `y2012dDDDhHHH`). Its weight in hours is in `numhours.csv`. |
| Stress block | A period chosen by the adequacy loop, used for the reserve margin (names `sy<year>dDDDhHHH`). Not used for energy prices. |
| Diff | Case value minus the value of the arm's own 0 GW case, same region or group and year (D2). |
| Relative Diff | Diff divided by the 0 GW value, in %. Used only for the metrics named in D11. |
| Energy price | The `load` price from `reqt_price`, in $/MWh per block. |
| All-in price | Energy price plus reserve margin, operating reserve, and policy prices, all divided by `load` quantity (D6). |
| Average price | Quantity-weighted mean over blocks and regions (D6). |
| Peak price | The highest energy price over the blocks of one region and year (D9). |
| Peak/average ratio | Peak price divided by the energy-only average price (D9). |
| Price-setter | The plant type whose running cost is within 5% of the block's energy price (D12). Otherwise the block is "set by something else". |
| Running cost | VOM cost plus heat rate times fuel price, $/MWh. |
| Dollar year | All reported money is 2024 USD. Model money is 2004 USD; multiply by 1.6563 (D8). |

## Arms and their baselines

Seven arms are used in results. `c66BA` is only a reproducibility check (D5).

| Arm | Levels (GW) | Only difference from `med` | Baseline (0 GW case) | Notes |
| --- | --- | --- | --- | --- |
| `med` | 0, 0.5, 1, 1.5, 2, 2.5, 3 | None (reference) | Its own | Plant is `Nuclear-SMR`. |
| `high` | 0, 0.5, 1, 1.5, 2, 2.5, 3 | High load growth | Its own | Different representative hours; compare peaks only as ratios. |
| `nuccons` | 0.5, 1, 1.5, 2, 2.5, 3 | Conservative nuclear cost | `CBBA_20261006_0G_med`, if the gate in D4 passes | Builds conventional `Nuclear`, not SMR. Label it that way. |
| `lowBA` | 0, 0.5, 1.5, 2.5 | Low load growth | Its own | Different representative hours. |
| `no13BA` | 0, 0.5, 1.5, 2.5 | No stress periods from 2013 | Its own |  |
| `txstBA` | 0, 0.5, 1.5, 2.5 | No new interstate transmission | Its own |  |
| `gashiBA` | 0, 0.5 | High gas price | Its own | Builds endogenous `Nuclear-Stor1`. Show as one point, not a slope. |
| `c66BA` | 0, 0.5 | 66 clusters asked (gives 19, same as `med`) | Not used in results | Must equal `med`. |

## Metrics

Average price, peak price and system cost are the primary results. The rest explain them or check them.

| Metric | Definition | Unit (reported) | Source files | Group aggregation | Change reported (D11) |
| --- | --- | --- | --- | --- | --- |
| Average energy price | Sum of energy price times `load` quantity, divided by sum of `load` quantity | 2024 $/MWh | `reqt_price`, `reqt_quant` | Sum dollars and quantity over regions, then divide | Absolute and % |
| Average all-in price | As above, with dollars from `load`, `res_marg`, `oper_res`, `state_rps`, `nat_gen` | 2024 $/MWh | `reqt_price`, `reqt_quant` | Same | Absolute and % |
| Peak price | Highest energy price over blocks, with block name and hours; 2nd and 3rd highest too | 2024 $/MWh | `reqt_price`, `numhours` | Group price per block (sum of dollars / sum of load over members), then the highest block (D14) | Absolute and % |
| Peak/average ratio | Peak price divided by average energy price | ratio | derived | From the group's own peak and average | Absolute |
| System cost | Sum of `inv_*` and `op_*` categories over 2044, 2047, 2050 | 2024 $ | `systemcost_ba_bulk_ew` | Sum | Absolute and % |
| Net imports | Annual net imports in representative periods | MWh | `net_import_ann_rep` | Sum (flows inside a group cancel, except losses) | Absolute |
| Expenditure flows | Value of energy and capacity sent from r to rr | 2024 $ | `expenditure_flow` | Sum of flows that cross the group border | Absolute |
| Transmission | Line capacity; new lines | MW | `tran_out`, `invtran_out` | Sum over lines touching the group | Absolute |
| Capacity | Capacity by technology | MW, and % of regional total | `cap_ivrt` | Sum | Absolute and share |
| Generation | Annual generation by technology | MWh, and % of regional total | `gen_ivrt` | Sum | Absolute and share |
| Price-setter share | Share of blocks per price-setter type, and "set by something else" | % of blocks | `gen_h`, `cost_vom`, `heat_rate`, `fuel_price`, `reqt_price` | Per region | Absolute |
| Line at limit in peak block | Flow in the peak block compared with line capacity | yes or no, % of capacity | `tran_util_h_rep` | Per line touching p25 | Absolute |

**Group results and region maps (D15).** Group values are the primary results. Region values are shown as maps: average price, Diff in average price, and Diff in system cost, one panel per nuclear level.

**Peak block drill-down (D14).** The group peak names one block. For that block, make one table with one row per member region: energy price, `load` quantity, share of the group's dollars, price-setter type (D12), and each line that touches the region with its flow as % of capacity. This shows which region and which limit (generation or transmission) drives the group peak.

**Caution for the system cost map.** INFERENCE: `systemcost_ba_bulk_ew` puts a cost in the region where the plant or line is. It does not say who pays. So p25 will show a large cost rise, and its neighbors can show a fall, even when they buy the power. Show the `expenditure_flow` map next to it, so that the reader sees where the money goes.

## Files to collect from each run

You already have the files marked "have". Collect the files marked "get" for all runs. Row numbers are for `reeds/core/terminus/report_params.csv` at `0c0ea27`.

| File | Status | Columns | Unit | Used for | Params row |
| --- | --- | --- | --- | --- | --- |
| `reqt_price.csv` | have | type, subtype, r, h, t | load: 2004 $/MWh | prices | L154 |
| `reqt_quant.csv` | have | type, subtype, r, h, t | load: MWh per block | prices (weights) | L156 |
| `inputs_case/rep/numhours.csv` | have | h | hours | peak block weight | input file |
| `systemcost_ba_bulk_ew.csv` | get | sys\_costs, r, t | 2004 $ | system cost | L190 |
| `net_import_ann_rep.csv` | have | r, t | MWh | net imports | L209 |
| `net_import_ann_stress.csv` | get (optional) | r, t | MWh | net imports in stress periods, check only | L210 |
| `expenditure_flow.csv` | have | type, r, rr, t | 2004 $ | trade money, cost view B | L77 |
| `expenditure_flow_rps.csv`, `expenditure_flow_int.csv` | get | st, ast, t / r, t | 2004 $ | cost view B | L78, L79 |
| `tran_out.csv` | have | r, rr, trtype, t | MW | neighbor list, line capacity | L223 |
| `invtran_out.csv` | get | r, rr, trtype, t | MW | new lines | L114 |
| `tran_util_h_rep.csv` | get | r, rr, h, trtype, t | fraction of capacity, per direction | line at limit in peak block | L203 |
| `tran_flow_rep_ann.csv` | get | r, rr, trtype, t | MWh, net, signed | trade energy | L201 |
| `cap_ivrt.csv` | have | i, v, r, t | MW | capacity, setup checks | L19 |
| `ret_ivrt.csv` | have | i, v, r, t | MW | coal retirement check | L160 |
| `gen_ivrt.csv` | have | i, v, r, t | MWh | generation | L84 |
| `gen_h.csv` | get | i, r, h, t | MW | price-setter test | L85 |
| `cost_vom.csv` | get | per the input file | check | running cost | L255 (input) |
| `heat_rate.csv` | get | per the input file | check | running cost | L263 (input) |
| `fuel_price.csv` | get | per the input file | check | running cost | L260 (input) |
| `repgasprice_r.csv` | get (optional) | r, t | 2004 $/MMBtu | cross-check of the gas price | L148 |

Transmission files now come from `report_calcs.py`. Each line pair is one row, with r before rr in text order (`report_calcs.py` L21-46). Text order is not number order: "p25" comes before "p3". For net flows, a positive value means flow from r to rr (L124).

The columns for the three input files are not stated in the params file. Check them when you collect the files, and add them here.

Added on 27 Oct for the SMR value analysis: `valnew.csv` (have; type, i, r, t; 2004 $, MW, MWh; params L231) and `reduced_cost.csv` (get; i, v, r, t, bin, variable; 2004 $/kW undiscounted; params L144). Also the marginal of `eq_forceprescription_power` (get; Caleb adds it as a new output; columns and units to check when it arrives), and `lcoe_built.csv` (get; i, r, t; $/MWh; params L116).
