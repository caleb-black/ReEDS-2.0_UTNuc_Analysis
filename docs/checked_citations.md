# Checked citations

Each model claim is checked once against ReEDS commit `0c0ea27`. The Reviewer adds one row per claim and checks only claims that are not in this list (D23).

| Claim | File and line at `0c0ea27` | Used in | Checked on | Result |
| --- | --- | --- | --- | --- |
| `plantchar_nuclear_smr` is the SMR cost and performance switch | `cases.csv` L23 | data dictionary arm table; 00a | 2026-10-28 | Confirmed |
| `plantchar_upv` is the UPV cost and performance switch | `cases.csv` L28 | data dictionary arm table; 00a | 2026-10-28 | Confirmed |
| `demandscen` is the demand scenario switch | `cases.csv` L32 | data dictionary setup table; 00a | 2026-10-28 | Confirmed |
| `ngscen` is the natural gas price switch | `cases.csv` L39 | data dictionary arm table; 00a | 2026-10-28 | Confirmed |
| `GSw_Region` keeps the zones named by a hierarchy column | `cases.csv` L48 | data dictionary setup table; 00a | 2026-10-28 | Confirmed |
| `GSw_ZoneSet` sets the zone set (z132) | `cases.csv` L49 | data dictionary setup table; 00a | 2026-10-28 | Confirmed |
| `GSw_Clean_Air_Act` turns the CAA Section 111 provisions on or off | `cases.csv` L107 | data dictionary setup table; 00a | 2026-10-28 | Confirmed |
| `GSw_ForcePrescription` turns forced prescriptions on or off | `cases.csv` L139 | data dictionary setup table; 00a | 2026-10-28 | Confirmed |
| `GSw_GasCurve` = 2 is the static gas supply curve | `cases.csv` L142 | data dictionary setup table; 00a | 2026-10-28 | Confirmed |
| `GSw_LoadProfiles` names the demand profile | `cases.csv` L214 | data dictionary setup and arm tables; 00a | 2026-10-28 | Confirmed |
| `GSw_PRM_CapCredit` = 0 is the stress-period formulation | `cases.csv` L259 | data dictionary setup table; 00a | 2026-10-28 | Confirmed |
| `GSw_Upgrades` turns upgrades on or off | `cases.csv` L348 | data dictionary setup table; 00a | 2026-10-28 | Confirmed |
| `keep_g00_files` only keeps or deletes .g00 files for completed solve years | `cases.csv` L372 | 00a check report (info) | 2026-10-28 | Confirmed |
| z132 has 34 western zones; p25, p26, z28 present; p28, p30 absent | `inputs/zones/z132/hierarchy.csv` (column `interconnect` = `western`) | data dictionary; 00a | 2026-10-28 | Confirmed |
| 2004 to 2024 USD factor = product of `inflation_rate` 2005 to 2024 = 1.656315 | `inputs/financials/inflation_default.csv` L93-L112 | D8; 00a | 2026-10-28 | Confirmed |
| p25 interfaces: p12, p16, p21, p26, p27, p31, p33, z28 | `inputs/zones/z132/interfaces_r.csv` L10, L27, L38, L45-L49 | data dictionary neighbor list; 00a | 2026-10-28 | Confirmed |
| `read_h5` reads one group per key: `columns` dataset, one dataset per column, byte strings decoded as UTF-8 | `reeds/io.py` L420-433 | 01a docstring and `read_key` | 2026-10-28 | Confirmed |
| A key absent from `outputs.h5` gives an empty table with the `report_params.csv` index, not an error | `reeds/io.py` L506-L519 (`read_output`) | 01a docstring; 01a check report | 2026-10-28 | Confirmed |
| `read_output` renames `allh` to `h` (also `allt` to `t`, `eall` to `e`) | `reeds/io.py` L524 | 01a docstring; D33 | 2026-10-28 | Confirmed |
| `report_params.csv` lists `cost_vom` (L255), `fuel_price` (L260), `heat_rate` (L263) with empty units and comment, no index, `input` = 1 | `reeds/core/terminus/report_params.csv` L255, L260, L263 (header L3) | 01a check report; data dictionary | 2026-10-28 | Confirmed |
| `cost_vom(i,v,r,t)` is declared "--2004$/MWh-- variable OM" | `reeds/core/setup/b_inputs.gms` L3463 | data dictionary; 03e | 2026-10-28 | Confirmed |
| `heat_rate(i,v,r,t)` is declared "--MMBtu/MWh-- heat rate" | `reeds/core/setup/b_inputs.gms` L3623 | data dictionary; 03e | 2026-10-28 | Confirmed |
| `fuel_price(i,r,t)` is declared "$/MMBtu - fuel prices by technology" (no dollar year) | `reeds/core/setup/b_inputs.gms` L3681 | data dictionary; 03e | 2026-10-28 | Confirmed |
| `price_types` = load, res_marg, oper_res, state_rps, nat_gen | `postprocessing/bokehpivot/reeds2.py` L34 | 03a docstring; D6 | 2026-10-29 | Confirmed |
| `pre_prices`: left join of quantities to prices (L964), missing price filled with 0 (L965), `$` = p x q (L967), total over `price_types` (L968-L972). 03a cites "L965-L966" for the join and fillna: the join is L964 and the fillna L965 | `postprocessing/bokehpivot/reeds2.py` L959-L972 | 03a docstring and check report | 2026-10-29 | Confirmed; cited line range is off by one (L964-L965) |
| `inflate_series` divides by the bokehpivot deflator for the chosen dollar year | `postprocessing/bokehpivot/reeds2.py` L72-L73 | 03a check report | 2026-10-29 | Confirmed |
| "Energy Price Final BA Map ($/MWh)" = `load` $ divided by `q_load`, year `last` | `postprocessing/bokehpivot/reeds2.py` L2189 | 03a check figure | 2026-10-29 | Confirmed |
| Load and operating reserve prices are $/MWh; reserve margin price is $/MW/stress-timeslice for the stress-period formulation ($/MW/rep-day for capacity credit). The comment says "$", not "2004 $" | `reeds/core/terminus/report.gms` L330-L331 | 02d `TYPE_UNITS`; data dictionary `reqt_price` | 2026-10-29 | Confirmed for the per-unit part; the dollar year is Not covered in the documentation at this line (inherited from the `load` row of the data dictionary) |
| Load and operating reserve quantities are MWh; reserve margin quantity is MW | `reeds/core/terminus/report.gms` L366 | 02d `TYPE_UNITS`; data dictionary `reqt_quant` | 2026-10-29 | Confirmed |
| `reqt_price` and `reqt_quant` have unit "varies" in `report_params.csv` (L154, L156) | `reeds/core/terminus/report_params.csv` L154, L156 | data dictionary | 2026-10-29 | Confirmed |
| `cap_ivrt` MW (L19); `gen_ivrt` MWh annual (L84); `expenditure_flow` 2004$ (L77); `systemcost_ba_bulk_ew` 2004$ (L190) | `reeds/core/terminus/report_params.csv` L19, L84, L77, L190 | 03b, 03c, 03d | 2026-10-29 | Confirmed |
| `systemcost_ba_bulk_ew` = `systemcost_ba_bulk`; op categories in the last solve year use `systemcost_ba` (one year) | `reeds/core/terminus/report.gms` L1663-L1664 | D10; 03b | 2026-10-29 | Confirmed |
| `tran_out` = forward plus reverse capacity (`combine_forward_reverse`, `simult`) divided by 2; one row per r < rr pair | `reeds/core/terminus/report_calcs.py` L104; L40-L46; `report_params.csv` L223 | 03f docstring | 2026-10-29 | Confirmed |
| `tran_util_h_rep` = `tran_flow_all_rep` / `tran_cap_energy` (flow over the directional energy capacity) | `reeds/core/terminus/report_calcs.py` L134 (inputs L98, L116) | 03f docstring; D37d | 2026-10-29 | Confirmed |
| bokehpivot maps a column with `tech_map.csv`: `^raw$` with `*` -> `.*`, first match wins, no match keeps the value; text columns are lowercased by `df_to_lowercase` | `postprocessing/bokehpivot/reeds_bokeh.py` L414-L432; L621-L625 | `derive_common.tech_map` (not called in stage 03) | 2026-10-29 | Confirmed; 03_derive cites L414-L431 (L432 is the apply line) and no line for the lowercase step |
| `tech_map.csv` and `tech_style.csv` exist at these paths (columns raw, display; order, color, marker) | `postprocessing/bokehpivot/in/reeds2/tech_map.csv`, `tech_style.csv` | D37g; `derive_common` | 2026-10-29 | Confirmed |
| `US_PCA.shp` is a Git LFS pointer (sha256 oid, size 708152); .shx .dbf .prj .cpg are plain blobs | `inputs/shapefiles/US_PCA/US_PCA.shp` | 03a `shapes()` | 2026-10-29 | Confirmed for .shp; the `rb` column name was not checked by the Reviewer |
