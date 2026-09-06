# When should a hotel change its price?
### Dynamic pricing under inflation: evidence from Buenos Aires hotels

The project studies the **timing** of repricing for Buenos Aires hotel
categories under Argentine inflation: reprice too slowly and the real room rate
erodes; reprice too often and you pay operational / customer friction. It builds
and backtests an **inflation-aware, state-dependent repricing rule** and
compares it to doing nothing, to mechanical monthly CPI indexing, and to what
hotels actually did.

| document | contents |
|---|---|
| **[`REPORT.md`](REPORT.md)** | **full project report** — motivation, data, method, every result with numbers, the rule, limitations |
| [`FINDINGS.md`](FINDINGS.md) | condensed findings + the recommended rule |
| [`DATA_AUDIT.md`](DATA_AUDIT.md) | structural audit of the six raw government spreadsheets |
| [`PROJECT_AUDIT.md`](PROJECT_AUDIT.md) | method-change log (this project was reframed from an earlier price/inflation correlation study) |

---

## Data (all official, `data/raw/`, read-only)

| File | Series | Freq | Span |
|---|---|---|---|
| `Ehoba_03a_0811.xlsx` | average room rate by category (**pesos**) | monthly | 2008-01 … 2026-05 |
| `Ehoba_02a_0811.xlsx` | room-occupancy rate (%) | monthly | 2008-01 … 2026-05 |
| `Ehoba_04_0811.xlsx` | bed-occupancy rate (%) | monthly | 2008-01 … 2026-05 |
| `Ehoba_VA_0811.xlsx` | travellers hosted | monthly | 2013-01 … 2026-05 |
| `Ehoba_1_ano.xlsx` | establishments, available room-/bed-nights | quarterly | 2008 … 2026-03 |
| `sh_ipc_08_26.xls` | INDEC CPI, base **dic-2016 = 100**, GBA + national + divisions | monthly | GBA 2016-04 … 2026-07 |
| `India_CPI/` | World Bank WDI `FP.CPI.TOTL.ZG` — India CPI inflation (annual %), context only (`02_data_overview`) | annual | 1960 … 2025 |

Sources: Buenos Aires City Statistics and Census Institute (EHOBA) and INDEC.
Analysis is at **Buenos Aires City × hotel category × month** — aggregate, not
individual hotels.

## Framing & key choices

* **Sample:** main analysis **2018-01 … 2019-12 + 2022-01 … 2026-05**;
  **COVID 2020-21 held out**; 2008–2017 for long-run nominal context only.
* **Deflator:** CPI, **GBA region** (national as robustness), base dic-2016 = 100.
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
  `total_composite` is built in notebook 01 (quarterly weights; derived).

## Repository

```
REPORT.md  FINDINGS.md  DATA_AUDIT.md  PROJECT_AUDIT.md   documentation
requirements.txt                                          pinned deps (Python 3.12)

data/raw/                     source spreadsheets (never modified, read-only)
data/processed/               parquet panels + cleaning_audit_log.csv  (git-ignored, reproducible)

src/config.py                 paths, windows, threshold/λ/β grids, backtest split
src/common.py                 text/number helpers + idempotent audit log
src/loaders.py                structural parsers for the six raw spreadsheets
src/policies.py               repricing-policy engine  (P0/P1/P2/P3; strict t-1 info set)
src/pricing_eval.py           policy scoring, λ-objective, Pareto frontier

01_build_dataset.ipynb               load · clean · merge  →  data/processed/*.parquet
02_data_overview.ipynb               orientation / EDA — coverage & gaps, the series, the inflation
                                     environment, seasonality, category comparison (figures only)
03_inflation_and_repricing.ipynb     Parts 1, 2, 7 — Charts 1-4, erosion clock, Tables 1-3, regime tests
04_demand_and_identification.ipynb   Part 3 — elasticity (Table 4), IV scrutiny, Chart 5
05_policies_and_backtest.ipynb       Parts 4, 5, 6 — P0-P3, frontier + knee, λ sweep,
                                     out-of-sample Table 6, Charts 7-8, COVID stress test
06_synthesis_menucost_and_rule.ipynb Parts 8, 10 + theory — Table 7 & Chart 6 (heterogeneity),
                                     Sheshinski–Weiss (s,S) calibration + scaling law
                                     (Tables 8-10, Charts 10-11), decision tree (Chart 9)
07_robustness.ipynb                  Part 9 — robustness matrix + COVID-inclusion note

outputs/figures/   Charts 1-11 + EDA + diagnostics (30 PNG @ 200 dpi)
outputs/tables/    Tables 1-10 + supporting CSVs (23 files)
```

The seven notebooks sit in the repository root and **must be run from the
repository root, in order** (each does `sys.path.insert(0, "src")` and reads the
previous one's `data/processed/` output). They are consolidations of an earlier
11-notebook pipeline; each keeps its section-level names in
`cleaning_audit_log.csv`. Core logic (the policy engine and its scoring) lives in
`src/policies.py` and `src/pricing_eval.py`, not in the notebooks.
`linearmodels` and `patsy` are required (notebook 04; 03/07).

## Reproduce

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name argentina-hotels --display-name "Python (argentina-hotels)"

# from the repository root:
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.kernel_name=argentina-hotels [0-9]*.ipynb      # 01 -> 07, ~30 s
```

Each notebook reads the previous notebook's parquet from `data/processed/`.
Every cleaning / modelling decision is appended to
`data/processed/cleaning_audit_log.csv` (idempotent per notebook).

**Speed.** The full chain runs in **~30 s** (`01_build_dataset` ≈ 4 s cold, ≈ 3 s
warm; the other six ≈ 4 s each). `01_build_dataset` caches each parsed raw table
to `data/processed/01_loaded/*.parquet` and reuses it unless the source file or a
`src/*.py` parser changed — set `FORCE_RELOAD = True` in that notebook to force a
re-parse. The downstream notebooks (02–07) are fast enough that they always
recompute, which avoids stale-result bugs.

## The rule (see Chart 9 / FINDINGS.md)

> Each month, compute cumulative CPI inflation since your last price change.
> Below **τ\* ≈ 6%** (4–7% band; top of the band for 4–5★) → **hold**. At or
> above τ\* → **reset** the price to restore the target real rate, optionally
> tilting by whether occupancy is above / at / below its seasonal norm.

Backtested, this roughly **halves the number of price changes** versus repricing
every month, holds the real rate within **~6%** of target (versus ~11–16% for
observed pricing), and leaves revenue essentially unchanged — out-of-sample and
across robustness checks.

The trigger is the canonical **Sheshinski–Weiss (s, S) menu-cost rule**
(notebook 06): its calibrated τ\* (≈ 6.3%) matches the fitted knee, and its
scaling law — price-change *size* ∝ π^{1/3} — holds in the data (estimated
elasticity 0.33), while *frequency* does not respond.

## Limitations

Aggregate category data; no official CPI pre-2016 (~77 clean months/category);
occupancy elasticity associational only; no cost data (revenue trade-off, not
profit); repricing *frequency* only weakly observable from category-mean rates;
composite "Total" is a construction. **COVID 2020-21**: category rate series are
`///` for 22 of 24 months, so no price-based re-estimation is possible — the
recommended rule is *simulated* through the collapse (notebook 05 stress test:
it holds the real price within ~5% of target and does not break) but it is
**validated for inflation regimes, not demand-collapse regimes**, and has no
price-cut branch.
