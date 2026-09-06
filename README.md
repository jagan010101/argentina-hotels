# Dynamic Pricing Under Inflation — Buenos Aires Hotels

Pricing & revenue-optimisation study of how Buenos Aires hotels should adjust
room rates when inflation is high. Chain of interest:

> inflation → nominal room rate → occupancy → revenue

**Status:** data pipeline complete (notebooks 01–03). Modelling (04–08) pending
sign-off on the notebook-03 checkpoint. Nothing causal is claimed yet.

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
notebooks/04_descriptive_analysis.ipynb   (pending)
notebooks/05_price_adjustment.ipynb       (pending)  price-change frequency / magnitude / pass-through
notebooks/06_elasticity.ipynb             (pending)  occupancy response to real rate
notebooks/07_dynamic_pricing.ipynb        (pending)  demand model + counterfactual optimal price
notebooks/08_backtest.ipynb               (pending)  repricing rules, out-of-sample
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
    notebooks/01_load_data.ipynb notebooks/02_clean_data.ipynb notebooks/03_merge_data.ipynb
```

Every cleaning decision is appended to `data/processed/cleaning_audit_log.csv`
(idempotent per notebook). Outputs land in `outputs/figures/` and `outputs/tables/`.

## Outputs so far

`outputs/tables/`: `data_dictionary.csv`, `missing_value_map.csv`,
`coverage_by_category.csv`, `outlier_register.csv`, `table1_descriptives.csv`.
`outputs/figures/`: `03_indec_crosscheck.png`, `03_nominal_vs_real.png`,
`03_occ_vs_realrate_raw.png`.

## Limitations (running list)

* No official CPI before 2016-12 → ~90 clean months per category (≈78 excluding
  the full COVID disruption). Small sample for regime splits.
* Capacity is quarterly; monthly revenue figures are explicitly `*_proxy`.
* `Restaurantes y hoteles` CPI is a consumer-price division, not a cost index —
  no profit optimisation.
* Raw price/occupancy correlation is positive (demand-driven) — causal
  interpretation of elasticity requires the controls and caveats in notebook 06.
