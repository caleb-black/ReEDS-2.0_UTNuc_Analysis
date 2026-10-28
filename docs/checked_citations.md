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
