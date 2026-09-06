# Dynamic Pricing Under Inflation — Buenos Aires Hotels

Pricing & revenue-optimisation study of how Buenos Aires hotels should adjust
room rates when inflation is high. Chain of interest:

> inflation → nominal room rate → occupancy → revenue

**Status:** complete end-to-end (notebooks 01–09). Full pipeline reproduces from
`data/raw/` in ~1.5 min. Headline results and the recommended rule are in
[`FINDINGS.md`](FINDINGS.md) and notebook 09. No causal elasticity is claimed —
see notebook 06b for what the data can and cannot identify.

---

## Data sources (all official, `data/raw/`, read-only)

| File | Series | Freq | Span | Notes |
|---|---|---|---|---|
| `Ehoba_03a_0811.xlsx` | Average room rate by category (**tarifa promedio, pesos**) | monthly | 2008-01 … 2026-05 | the price variable; **no "Total" column** |
| `Ehoba_02a_0811.xlsx` | Room-occupancy rate (%) | monthly | 2008-01 … 2026-05 | Hostel room-occ never published |
| `Ehoba_04_0811.xlsx` | Bed/place-occupancy rate (%) | monthly | 2008-01 … 2026-05 | |
| `Ehoba_VA_0811.xlsx` | Travellers hosted (persons) | monthly | 2013-01 … 2026-05 | hotel sector only, excl. para-hotels |
| `Ehoba_1_ano.xlsx` | Establishments, available room-nights, bed-nights | **quarterly** | 2008 … 2026-03 | 2/yr → 3/yr → 4/yr snapshots; 2008 uses older EOH taxonomy |
| `sh_ipc_08_26.xls` | INDEC IPC, base **dic-2016 = 100** | monthly | GBA 2016-04 … / national 2016-12 … 2026-07 | no pre-2016 CPI exists |

Source: Instituto de Estadística y Censos de la Ciudad de Buenos Aires (EHOBA)
and INDEC (Dirección Nacional de Estadísticas de Precios). See `DATA_AUDIT.md`
for the full structural audit of every sheet.

## Key decisions (see `DATA_AUDIT.md` §10)

* **Analysis window `2016-12 → 2026-05`** — the span with official CPI. Pre-2016
  hotel data is retained for descriptive *nominal* charts only, never deflated.
* **Deflator:** IPC **Región GBA** primary; IPC **Total nacional** as a
  robustness check. Base dic-2016 = 100 → real rates in constant dic-2016 pesos.
* **Revenue, not profit** — no cost/wage data supplied.
* **Categories modelled:** 1-2★, 3★, 4★, 5★ (core) + Apart, Boutique (secondary);
  a capacity-weighted composite stands in for "all hotels". Hostel/Otros not modelled.
* **COVID** `2020-03 … 2021-12` is a hard data hole; `2022` is a degraded
  recovery year (1-2★ missing). Both flagged; excluded from fitting, robustness
  runs keep 2022.

## Pipeline

```
data/raw/*.xlsx,*.xls
   │  notebooks/01_load_data.ipynb      structural extraction → data/processed/01_loaded/*.parquet
   │  notebooks/02_clean_data.ipynb     coercion, missing-reason, outlier register
   │                                    → 02_panel_long / 02_capacity_quarterly / 02_cpi_monthly .parquet
   │  notebooks/03_merge_data.ipynb     CPI merge, inflation, real rates, seasonality,
   │                                    COVID flags, capacity as-of, revenue proxy
   ▼                                    → data/processed/03_analysis_panel.parquet  + checkpoint diagnostics
notebooks/04_descriptive_analysis.ipynb   Plots 1–9, Table 1, COVID shading
notebooks/05_price_adjustment.ipynb       price-change distribution, regression pass-through
                                          (Table 2), inflation regimes, Chart B
notebooks/06_elasticity.ipynb             occupancy vs real rate: log-log / lag / levels /
                                          logit specs (Table 3), endogeneity discussion, Chart C
notebooks/06b_identification.ipynb        YoY-diff / relative-price panel / 2SLS / predetermined-
                                          lag attempts at a causal elasticity
notebooks/07_dynamic_pricing.ipynb        constant-elasticity demand, degenerate revenue optimum,
                                          policy paths A/B/C/D, Charts D & E
notebooks/08_backtest.ipynb               no-look-ahead backtest of repricing rules
                                          (train<=2019 / val 2022 / test 2023-26), Tables 4 & 5,
                                          repricing-frequency trade-off, Chart F
notebooks/09_results_and_recommendation.ipynb   Tables 1–5 + Charts A–F assembled,
                                          Part-14 economic interpretation, the recommended rule
```

Shared config and parsing helpers: `src/config.py`, `src/common.py` (imported by
the notebooks; not run directly).

## Reproduce

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name argentina-hotels --display-name "Python (argentina-hotels)"
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.kernel_name=argentina-hotels \
    notebooks/0*.ipynb          # runs 01 → 09 in order (~1.5 min)
```

Or open the notebooks in Jupyter and run top-to-bottom; each reads the parquet
outputs of the previous one from `data/processed/`.

Every cleaning decision is appended to `data/processed/cleaning_audit_log.csv`
(idempotent per notebook). Outputs land in `outputs/figures/` and `outputs/tables/`.

## Outputs

`outputs/tables/` (14 CSVs): `data_dictionary`, `missing_value_map`,
`coverage_by_category`, `outlier_register`, `table1_descriptives`,
`price_adjustment_stats`, `table2_passthrough`, `passthrough_by_regime`,
`table3_elasticity`, `elasticity_robustness`, `identification_summary`,
`table4_policy_comparison`, `table5_out_of_sample`, `backtest_robustness`.

`outputs/figures/` (24 PNGs @ 200 dpi): Plots 1–9 (`04_*`), presentation
Charts A–F (`09_chartA`, `05_chartB`, `06_chartC`, `07_chartD`,
`08_chartE`, `08_chartF`), plus diagnostic figures for each stage.

`data/processed/`: `01_loaded/*.parquet` (raw tables, tidy), `02_panel_long`,
`02_capacity_quarterly`, `02_cpi_monthly`, `03_analysis_panel` (the modelling
table), and `cleaning_audit_log.csv` (every transformation, idempotent per notebook).

## Limitations (running list)

* No official CPI before 2016-12 → ~90 clean months per category (≈78 excluding
  the full COVID disruption). Small sample for regime splits.
* Capacity is quarterly; monthly revenue figures are explicitly `*_proxy`.
* `Restaurantes y hoteles` CPI is a consumer-price division, not a cost index —
  no profit optimisation.
* Raw price/occupancy correlation is positive (demand-driven) — causal
  interpretation of elasticity requires the controls and caveats in notebook 06.
