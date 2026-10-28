# p25 nuclear study: data dictionary

Oct 28, 2026 · Caleb

This is the single place for the names, terms and files of the study. Decisions are in `docs/decisions.md`. All model citations are for ReEDS commit `0c0ea27` in `ReEDS-Model/ReEDS` (5 Aug 2026). The report code is now in `reeds/core/terminus/`: `report.gms`, `report_params.csv`, and `report_calcs.py` (transmission outputs).

## Runs and batches (D25, D26)

Run folders are in `D:\ReEDS\runs` (path set in `00_config/`). Each case reads its outputs from `<case>/outputs/outputs.h5` (D29) and its inputs from `<case>/inputs_case/`.

| Batch | Folder prefix | Upgrades | Arms used |
| --- | --- | --- | --- |
| UON | `UON_20261022_` | off (`GSw_Upgrades` 0) | `ref`, `gaslow`, `loadhigh`, `loadlow`, `pvadv`, `smrcons` |
| UOS | `UOS_20261021_` | on (`GSw_Upgrades` 1) | `ref`, `loadhigh`, `loadlow` (D27) |

UON and UOS are two separate studies (D26). No table, figure or note mixes them. `UOC_20261021_*` runs are not used.

## Model setup

These settings are the same for every case in both batches, except `GSw_Upgrades`. Only the arm switches in "Arms and their baselines" change. Values are read from `UON_20261022_0G_ref` and `UOS_20261021_0G_ref` (`inputs_case/switches.csv`); 00a records them for every case (D30).

| Switch | Value | Meaning, from `cases.csv` at `0c0ea27` |
| --- | --- | --- |
| `GSw_Region` | `interconnect/western` | Keep the zones in the western interconnect (L48). |
| `GSw_ZoneSet` | `z132` | Zone set z132 (L49). In the west it has 34 zones. `p28` and `p30` are merged into one zone, `z28` (Arizona). `p25` and `p26` are unchanged (`inputs/zones/z132/hierarchy.csv`). |
| `GSw_GasCurve` | 2 | Static gas supply curve (L142). |
| `GSw_Clean_Air_Act` | 0 | Clean Air Act Section 111 provisions off (L107). |
| `GSw_Upgrades` | 0 in UON, 1 in UOS | Upgrades off or on (L348). |
| `GSw_ForcePrescription` | 1 | Forced prescriptions on (L139). |
| `demandscen` | `AEO_2026_baseline` | Demand scenario (L32). Same in every arm. |
| `GSw_LoadProfiles` | `EER2025_IRAlow` in `ref` | Demand profile (L214). The load arms change this switch. |
| `GSw_PRM_CapCredit` | 0 (default) | Stress-period reserve margin (L259). Your `res_marg` rows use stress blocks, which matches this. |

The old switches `GSw_OPGW`, `GSw_NoReinforcement` and `GSw_RegionResolution` do not exist at `0c0ea27`.

## Region groups

Every region belongs to exactly one of the first four groups. `wecc` is the sum of all regions (D7, D13).

| Group name | Regions | How the list is made |
| --- | --- | --- |
| `focus` | p25 | Fixed. The nuclear plant is here. |
| `utah_rest` | p26 | Fixed. The other half of Utah. |
| `neighbors` | Zones directly connected to p25, without p26 | From `tran_out` in the batch's own 0 GW `ref` case (D31). Read both the `r` and `rr` columns. The list is fixed for all cases of that batch. Expected from the z132 interface list: p12, p16, p21, p27, p31, p33, z28 (`inputs/zones/z132/interfaces_r.csv`). If `tran_out` gives a different list, stop and check. |
| `rest_wecc` | All other western zones | The 34 western zones of z132, minus the three groups above. |
| `wecc` | All 34 western zones | The whole system. |

## Study terms

| Term | Meaning |
| --- | --- |
| Batch | A set of runs with one upgrades setting: UON (off) or UOS (on). The two batches are separate studies (D26). |
| Arm | A set of cases in one batch that share all assumptions except the nuclear level. Example: `ref`. |
| Level | GW of nuclear prescribed in p25 from 2044. UON: 0 to 3 in steps of 0.25. UOS: 0 to 3 in steps of 0.5. In folder names, `p` is the decimal point (`1p5G` = 1.5 GW). |
| Case | One run: one arm at one level in one batch. Folder name = `<batch>_<date>_<level>_<arm>`, for example `UON_20261022_2p5G_ref`. |
| Trunk | The 0.5 GW case of an arm, in the same batch. A full run from 2010. |
| Branch | Any other level. A copy of the trunk restarted at 2044 with a different nuclear size. |
| Trunk gate | The check that every branch equals its trunk through 2041, in every output (D4, D28). |
| Shared levels | 0, 0.5, 1.5, 2.5 GW. Used for slopes that compare arms (D3). |
| Solve year | A year the model solves: 2010, 2015, 2020, 2023, then every 3 years to 2050. Post-plant years are 2044, 2047, 2050. |
| Block | One representative 3-hour period (152 per year in most arms, 144 in `loadhigh` and `loadlow`, D32; names `y2012dDDDhHHH`). Its weight in hours is in `numhours.csv`. |
| Stress block | A period chosen by the adequacy loop, used for the reserve margin (names `sy<year>dDDDhHHH`). Not used for energy prices. |
| Diff | Case value minus the value of the arm's own 0 GW case in the same batch, same region or group and year (D2, D27). |
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

Every arm uses its own 0 GW case in the same batch as baseline (D2, D27). Switch values are from `inputs_case/switches.csv`; 00a checks every case against its batch's `ref` 0 GW case (the 0.5 GW trunks differ from it only in `keep_g00_files`). Line numbers are for `cases.csv` at `0c0ea27`. Values in `ref`: `ngscen` = `AEO_2026_baseline`, `plantchar_upv` = `upv_ATB_2024_moderate`, `plantchar_nuclear_smr` = `nuclear-smr_ATB_2024_moderate`.

**UON (upgrades off): 6 arms, 78 cases**

| Arm | Levels (GW) | Only difference from `ref` | Notes |
| --- | --- | --- | --- |
| `ref` | 0 to 3, step 0.25 | None (reference). Medium load: `GSw_LoadProfiles` = `EER2025_IRAlow` | Plant is `Nuclear-SMR`. |
| `gaslow` | 0 to 3, step 0.25 | `ngscen` = `AEO_2026_HOG` (L39) |  |
| `loadhigh` | 0 to 3, step 0.25 | `GSw_LoadProfiles` = `EER2025_100by2050` (L214) |  |
| `loadlow` | 0 to 3, step 0.25 | `GSw_LoadProfiles` = `EER2025_Baseline_AEO2023` (L214) |  |
| `pvadv` | 0 to 3, step 0.25 | `plantchar_upv` = `upv_ATB_2024_advanced` (L28) |  |
| `smrcons` | 0 to 3, step 0.25 | `plantchar_nuclear_smr` = `nuclear-smr_ATB_2024_conservative` (L23) |  |

**UOS (upgrades on): 3 arms, 21 cases**

| Arm | Levels (GW) | Only difference from UOS `ref` | Notes |
| --- | --- | --- | --- |
| `ref` | 0 to 3, step 0.5 | None (reference) | |
| `loadhigh` | 0 to 3, step 0.5 | As in UON | |
| `loadlow` | 0 to 3, step 0.5 | As in UON | |

Not used (D27): UON `gashigh` (`ngscen` = `AEO_2026_LOG`, L39; 0, 0.5, 1.5, 2.5 GW), because the model builds nuclear there on its own; and UOS `gashigh`, `gaslow`, `pvadv` and `smrcons` (0.5, 1.5, 2.5 GW), because they have no 0 GW case.

The load arms have their own representative days (D32): `loadhigh` and `loadlow` have 144 blocks, the other arms 152. Within one arm, all levels have the same blocks and weights.

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

## Outputs read from each run

Each output is a key in `<case>/outputs/outputs.h5`, read in the layout of `reeds/io.py` `read_h5` (D29). A key that is absent means an empty table. All keys below are present in `UON_20261022_0G_ref` (checked 28 Oct); 01a lists any key missing in other cases. In the file, the unnamed columns are `*`, `*.1`, `*.2`; 01a renames them by position to the names below. Row numbers are for `reeds/core/terminus/report_params.csv` at `0c0ea27`.

| Key | Columns | Unit | Used for | Params row |
| --- | --- | --- | --- | --- |
| `reqt_price` | type, subtype, r, h, t | load: 2004 $/MWh | prices | L154 |
| `reqt_quant` | type, subtype, r, h, t | load: MWh per block | prices (weights) | L156 |
| `systemcost_ba_bulk_ew` | sys\_costs, r, t | 2004 $ | system cost | L190 |
| `net_import_ann_rep` | r, t | MWh | net imports | L209 |
| `net_import_ann_stress` (optional) | r, t | MWh | net imports in stress periods, check only | L210 |
| `expenditure_flow` | type, r, rr, t | 2004 $ | trade money, cost view B | L77 |
| `expenditure_flow_rps`, `expenditure_flow_int` | st, ast, t / r, t | 2004 $ | cost view B | L78, L79 |
| `tran_out` | r, rr, trtype, t | MW | neighbor list, line capacity | L223 |
| `invtran_out` | r, rr, trtype, t | MW | new lines | L114 |
| `tran_util_h_rep` | r, rr, h, t, trtype (file order; params L203 declares r, rr, allh, trtype, t) | fraction of capacity, per direction | line at limit in peak block | L203 |
| `tran_flow_rep_ann` | r, rr, trtype, t | MWh, net, signed | trade energy | L201 |
| `cap_ivrt` | i, v, r, t | MW | capacity, setup checks | L19 |
| `ret_ivrt` | i, v, r, t | MW | coal retirement check | L160 |
| `gen_ivrt` | i, v, r, t | MWh | generation | L84 |
| `gen_h` | i, r, h, t | MW | price-setter test | L85 |
| `cost_vom` | i, v, r, t (solve years) | Not covered in the documentation | running cost | L255 (input) |
| `heat_rate` | i, v, r, t (solve years) | Not covered in the documentation | running cost | L263 (input) |
| `fuel_price` | i, r, t (every year; no `v`) | Not covered in the documentation | running cost | L260 (input) |
| `repgasprice_r` (optional) | r, t | 2004 $/MMBtu | cross-check of the gas price | L148 |

One input file is read as CSV: `<case>/inputs_case/rep/numhours.csv` (h; hours; peak block weight).

Transmission outputs come from `report_calcs.py`. Each line pair is one row, with r before rr in text order (`report_calcs.py` L21-46). Text order is not number order: "p25" comes before "p3". For net flows, a positive value means flow from r to rr (L124).

`report_params.csv` lists `cost_vom`, `heat_rate` and `fuel_price` with no index, unit or description. The columns above are as found in `outputs.h5` (01a, 28 Oct). Their units are not covered in the documentation. `fuel_price` has one value per region and year shared by all techs that burn the same fuel, and no `v` column, so the running-cost join in 03e matches it on i, r, t only. In the file, `gen_h` and `tran_util_h_rep` name the block column `allh`; 01a renames it to `h` (D33).

For the SMR value analysis: `valnew` (type, i, r, t; 2004 $, MW, MWh; params L231), `reduced_cost` (i, v, r, t, bin, variable; 2004 $/kW undiscounted; params L144) and `lcoe_built` (i, r, t; $/MWh; params L116) are keys in `outputs.h5`. The marginal of `eq_forceprescription_power` is not in `outputs.h5`; Caleb adds it as a new output (columns and units to check when it arrives).
