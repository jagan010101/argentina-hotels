# When should a hotel change its price?
### Dynamic pricing under inflation: evidence from Buenos Aires hotels

The project studies the **timing** of repricing for Buenos Aires hotel
categories under Argentine inflation: reprice too slowly and the real room rate
erodes; reprice too often and you pay operational / customer friction. It builds
and backtests an **inflation-aware, state-dependent repricing rule** and
compares it to doing nothing, to mechanical monthly CPI indexing, and to what
hotels actually did.

**Headline results & the recommended rule → [`FINDINGS.md`](FINDINGS.md).**
Reframing history & method notes → [`PROJECT_AUDIT.md`](PROJECT_AUDIT.md).
Source-data structure → [`DATA_AUDIT.md`](DATA_AUDIT.md).

---

## Data (all official, `data/raw/`, read-only)

| File | Series | Freq | Span |
|---|---|---|---|
| `Ehoba_03a_0811.xlsx` | average room rate by category (**tarifa promedio, pesos**) | monthly | 2008-01 … 2026-05 |
| `Ehoba_02a_0811.xlsx` | room-occupancy rate (%) | monthly | 2008-01 … 2026-05 |
| `Ehoba_04_0811.xlsx` | bed-occupancy rate (%) | monthly | 2008-01 … 2026-05 |
| `Ehoba_VA_0811.xlsx` | travellers hosted | monthly | 2013-01 … 2026-05 |
| `Ehoba_1_ano.xlsx` | establishments, available room-/bed-nights | quarterly | 2008 … 2026-03 |
| `sh_ipc_08_26.xls` | INDEC IPC, base **dic-2016 = 100**, GBA + national + divisions | monthly | GBA 2016-04 … 2026-07 |

Sources: Instituto de Estadística y Censos de la Ciudad de Buenos Aires (EHOBA)
and INDEC. Analysis is at **Buenos Aires City × hotel category × month** —
aggregate, not individual hotels.

## Framing & key choices

* **Sample:** main analysis **2018-01 … 2019-12 + 2022-01 … 2026-05**;
  **COVID 2020-21 held out**; 2008–2017 for long-run nominal context only.
* **Deflator:** IPC **Región GBA** (national as robustness), base dic-2016 = 100.
  `RealRate = Nominal / CPIIndex × 100`.
* **Cumulative inflation since the last repricing** is compounded
  `Π(1+π_s) − 1`, not summed.
* **Repricing threshold grid** τ ∈ {1,2,3,4,5,6,7,8,10}% — the efficient τ is
  *derived from the frontier*, not assumed.
* **No marginal-cost data** → we compare policies on the
  frequency / real-stability / occupancy / revenue trade-off and report the
  Pareto frontier; **no profit- or revenue-maximising price is claimed**.
* **Occupancy elasticity is not causally identified** → policy sims run across
  an assumed-β grid {0, −0.25, −0.5, −1.0}.
* **"Total"** has no rate column in the source → a capacity-weighted
  `total_composite` is built in notebook 03 (quarterly weights; derived).

## Repository

```
data/raw/                     source spreadsheets (never modified)
data/processed/               parquet panels + cleaning_audit_log.csv  (reproducible)

src/config.py                 paths, windows, threshold/λ/β grids, split
src/common.py                 parsing helpers + idempotent audit log
src/policies.py               repricing-policy engine  (P0/P1/P2/P3; t-1 info set)
src/pricing_eval.py           policy scoring, λ-objective, Pareto frontier

notebooks/
  01_load_data                structural extraction of the government sheets
  02_clean_data               coercion, missing-value classification, CPI deflators
  03_merge_data               panel + inflation transforms + composite Total + splits
  04_descriptive_inflation_story   Part 1  — Charts 1-2, erosion clock, Table 1
  05_repricing_behaviour           Parts 2 & 7 — Tables 2-3, regime tests, Charts 3-4
  06_demand_and_identification     Part 3  — elasticity (Table 4), IV scrutiny, Chart 5
  07_pricing_policies              Part 4  — P0-P3, revenue-optimum degeneracy
  08_threshold_backtest            Parts 5 & 6 — frontier + knee, λ sweep,
                                   out-of-sample Table 6, Charts 7-8
  09_heterogeneity_and_policy      Parts 8 & 10 — Table 7, Chart 6, decision tree (Chart 9)
  10_robustness                    Part 9  — robustness matrix

outputs/figures/   Charts 1-9 + diagnostics (200 dpi PNG)
outputs/tables/    Tables 1-7 + supporting CSVs
```

Core logic (the policy engine and its scoring) lives in `src/policies.py` and
`src/pricing_eval.py`, not in the notebooks.

## Reproduce

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name argentina-hotels --display-name "Python (argentina-hotels)"
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.kernel_name=argentina-hotels notebooks/*.ipynb      # 01 → 10, ~2 min
```

Each notebook reads the previous notebook's parquet from `data/processed/`.
Every cleaning / modelling decision is appended to
`data/processed/cleaning_audit_log.csv` (idempotent per notebook).

## The rule (see Chart 9 / FINDINGS.md)

> Each month, compute cumulative CPI inflation since your last price change.
> Below **τ\* ≈ 6%** (4–7% band; top of the band for 4–5★) → **hold**. At or
> above τ\* → **reset** the price to restore the target real rate, optionally
> tilting by whether occupancy is above / at / below its seasonal norm.

Backtested, this roughly **halves the number of price changes** versus repricing
every month, holds the real rate within **~6%** of target (versus ~11–16% for
observed pricing), and leaves revenue essentially unchanged — out-of-sample and
across robustness checks.

## Limitations

Aggregate category data; no official CPI pre-2016 (~77 clean months/category);
occupancy elasticity associational only; no cost data (revenue trade-off, not
profit); repricing *frequency* only weakly observable from category-mean rates;
COVID 2020-21 held out; composite "Total" is a construction.
