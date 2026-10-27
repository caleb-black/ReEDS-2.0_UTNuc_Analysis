# p25 nuclear study: decision log

Nineteen decisions are settled. Citations are for ReEDS commit `0c0ea27`. Do not change a decision in code. Add a new entry instead.

| ID | Decided | Decision | Source or reason |
| --- | --- | --- | --- |
| D1 | 2026-10-26 | All model claims use ReEDS commit `0c0ea27` (`ReEDS-Model/ReEDS`, your branch `ce/used`, no local edits). This replaces `730c582` (22 Oct). | Commit that made the current runs. |
| D2 | 2026-10-22 | Compare only within an arm. Diff = case minus the arm's own 0 GW case. `nuccons` uses the `med` 0 GW case, if D4 passes. | Study design. |
| D3 | 2026-10-22 | Slopes that compare arms use only 0, 0.5, 1.5, 2.5 GW. | Levels shared by all arms. |
| D4 | 2026-10-22 | Trunk gate: each branch equals its trunk through 2041, in every file. `nuccons` 0.5 GW equals `med` 0.5 GW through 2041. A failure stops the pipeline. | Branches restart from the trunk at 2044. |
| D5 | 2026-10-22 | `c66BA` is a reproducibility check only. | Clustering stops at 19 days. |
| D6 | 2026-10-22 | Average price = sum of price times quantity / sum of `load` quantity, over blocks and regions. | `model_documentation.md` L3214-3226, L3807-3815; `reeds2.py` `pre_prices` L959. |
| D7 | 2026-10-22 | Five region groups; `utah_rest` (p26) is its own group. Neighbor list from `tran_out`, 0 GW `med`, fixed for all cases. | Caleb, 22 Oct. |
| D8 | 2026-10-22 | Report 2024 USD; factor 1.6563 from `inputs/financials/inflation_default.csv`. Not `deflator.csv`. | Same values at `0c0ea27`. Caleb: bokehpivot deflator is likely out of date. |
| D9 | 2026-10-23 | Peak = highest energy price over blocks. Report block name, hours, and 2nd and 3rd highest. In peak blocks, check line use with `tran_util_h_rep`. | Study asks about the marginal price when cheap generation is used up. |
| D10 | 2026-10-23 | System cost from `systemcost_ba_bulk_ew`, sum of `inv_*` and `op_*`, over 2044, 2047, 2050. Follow the code (`report.gms` L1663-1664): in 2050, op costs are one year; investment is the same as in `systemcost_ba`. The params comment (L190, "CRF times the investment") is not used. | Chosen by Caleb, 23 Oct; end-year rule 26 Oct. |
| D11 | 2026-10-23 | Absolute and %: average price, peak price, system cost. Absolute only: net imports, expenditure flows, transmission, peak/average ratio. Capacity and generation: absolute plus share of regional total. | % has no meaning when the 0 GW value is near zero. |
| D12 | 2026-10-26 | Price-setter = plant type with running cost within 5% of the block price. Plot all gaps first. | Not covered in the docs; study choice. |
| D13 | 2026-10-26 | Group names: `focus`, `utah_rest`, `neighbors`, `rest_wecc`, `wecc`. | Caleb, 26 Oct. |
| D14 | 2026-10-26 | Group peak = group price per block (sum of dollars / sum of `load` over members), then the highest block. That block is broken down by member region. | Caleb, 26 Oct. Same weighting as D6. |
| D15 | 2026-10-26 | Groups are the primary results. Regions are shown as maps (average price, Diff in price, Diff in system cost). The system cost map is shown next to the `expenditure_flow` map. | Caleb, 26 Oct. |
| D16 | 2026-10-26 | No earlier scripts are reused. All analysis scripts are new. No cleanup inventory is needed. Branching (`branch_from_trunk.py`) is part of running the model, not of the analysis. | Caleb, 26 Oct. |
| D17 | 2026-10-27 | Model setup: `GSw_Region=interconnect/western`, `GSw_ZoneSet=z132` (34 western zones; p28 and p30 merged into `z28`), gas curve 2, Clean Air Act off, upgrades off, EER load scenarios. | Caleb, 27 Oct; `cases.csv` and `inputs/zones/z132/` at `0c0ea27`. |
| D18 | 2026-10-27 | Scripts in Python, in the conda `reeds` environment from `environment.yml` at `0c0ea27`, without the GAMS packages (`gamsapi`, `gamspy_base`). Scripts read CSV outputs only, because GDX files need the GAMS API. | Caleb, 27 Oct. |
| D19 | 2026-10-27 | SMR net value of energy = `valnew` value per MWh minus `lcoe_built` (Nuclear-SMR, p25). The prescription dual comes from an output file Caleb adds; the system cost change per GW is a cross-check. | NVOE in `model_documentation.md` L3333-3354; `report_params.csv` L116. Caleb, 27 Oct. |

## On hold

- The group-to-group trade table and the cost views A (where cost is incurred), B (after trade) and C (load payment at marginal prices). Caleb decides. Until then, `03c_trade` builds only net imports, expenditure flows and new lines.

## Removed scripts

None. No earlier scripts are reused (D16). When a script is moved to `archive/` or deleted, record here what it did and where that job now lives.
