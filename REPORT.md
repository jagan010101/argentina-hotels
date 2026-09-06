# When should a hotel change its price?
## Dynamic pricing under inflation — evidence from Buenos Aires hotels

**Project report.** Analysis level: *Buenos Aires City × hotel category × month*
(aggregate official statistics — not individual-hotel dynamic pricing). All
figures are reproduced by `notebooks/01–10`; every table and chart cited is in
`outputs/`.

---

## 1 · Executive summary

Argentina's inflation turned hotel pricing into a moving target: over 2018–2026
the consumer price level rose roughly **×91** (≈ 9,000%), with a monthly peak of
**25% in December 2023**. A hotel that holds its nominal rate loses **10% of its
real value in about two months** at the high-inflation pace. But repricing has
operational and customer costs, so the real decision is one of **timing**: how
much cumulative inflation to let build up before you reset the price.

Main results:

1. **Inflation changes the *size* of price moves, not the *frequency*.** In
   high-inflation months the monthly price change is **+4.4 pp larger**
   (p = 0.001) and **+22 pp more likely to be an increase** (p < 0.001); the
   frequency of >1% moves rises only ~9 pp from an already ~90% base.
2. **Pass-through of inflation into rates is ~1 and differs by tier** — 3★
   **0.83** (the laggard), 4★ 1.08, 5★ **1.23**.
3. **Occupancy's response to real price is not causally identified.** The naive
   slope is positive/zero (endogeneity); a fixed-effects relative-price design
   gives ≈ 0; instruments are weak or invalid. Demand looks **inelastic**. The
   policy work is therefore run across an assumed-elasticity grid and is
   near-invariant to it.
4. **A cumulative-inflation threshold rule with τ\* ≈ 6%** (derived from the
   repricing frontier, not assumed) **roughly halves the number of price changes
   versus repricing every month**, holds the real rate within ~6% of target
   (versus ~11% for what hotels actually did), and leaves revenue unchanged —
   **out-of-sample** and across nine robustness variants.
5. Adding an occupancy tilt (Policy 3) **did not help** out-of-sample.

The recommended rule is in §7 and drawn as a decision tree in Chart 9.

---

## 2 · Research question and framing

> **When should a Buenos Aires hotel category change its price under inflation?**

Inflation erodes the real value of a fixed nominal room rate. Reprice too slowly
and margins/revenue erode; reprice too frequently and you incur menu /
operational / customer-perception costs. The objective is an **inflation-aware,
state-dependent repricing policy**, evaluated against:

* **P0** — never reprice (the erosion reference);
* **P1** — index the price to CPI every month (the mechanical benchmark);
* **observed** — what Buenos Aires hotels actually did.

Because there is **no marginal-cost data**, this report does **not** claim a
profit- or revenue-maximising price. It maps the trade-off between repricing
frequency, real-price stability, occupancy and revenue, and reports the
Pareto frontier.

Define, for month *t*, cumulative inflation since the last price change

    R_t = Π_{s = last change+1}^{t} (1 + π_s) − 1        (compounded, not summed)

The core policy family is: **reprice when `R_t ≥ τ`**, then reset the nominal
price to restore the target real rate.

---

## 3 · Data

### 3.1 Sources (all official, `data/raw/`, read-only)

| File | Series | Freq | Span |
|---|---|---|---|
| `Ehoba_03a_0811.xlsx` | average room rate by category (*tarifa promedio*, pesos) | monthly | 2008-01 … 2026-05 |
| `Ehoba_02a_0811.xlsx` | room-occupancy rate (%) | monthly | 2008-01 … 2026-05 |
| `Ehoba_04_0811.xlsx` | bed-occupancy rate (%) | monthly | 2008-01 … 2026-05 |
| `Ehoba_VA_0811.xlsx` | travellers hosted (hotel sector) | monthly | 2013-01 … 2026-05 |
| `Ehoba_1_ano.xlsx` | establishments, available room-/bed-nights | quarterly | 2008 … 2026-03 |
| `sh_ipc_08_26.xls` | INDEC IPC, base dic-2016 = 100 (GBA + national + 12 divisions) | monthly | GBA 2016-04 … 2026-07 |

Occupancy/rate/traveller data: *Encuesta de Ocupación Hotelera de Buenos Aires
(EHOBA)*, Instituto de Estadística y Censos de la Ciudad de Buenos Aires. Prices
CPI: INDEC. The full structural audit of every sheet (merged cells, header rows,
footnotes, missing-value tokens, category-definition changes) is in
[`DATA_AUDIT.md`](DATA_AUDIT.md).

The **average rate is a category mean** (revenue per occupied room-night reported
by hotels), not a posted/rack price — so a menu-cost "frequency of repricing" is
only weakly observable (it moves most months); the analysis leans on the
*magnitude*, *sign* and *pass-through* of monthly changes instead.

### 3.2 The analysis panel

`notebooks/01–03` turn the presentation-formatted spreadsheets into one clean
monthly panel (`data/processed/03_analysis_panel.parquet`, 2,407 rows,
11 categories):

* **CPI deflators.** `cpi_gba` = IPC Región GBA *Nivel general*, spliced from the
  dic-2016 = 100 bridge sheet (2016-04 … 2016-11) onto the national index sheet's
  GBA block (2016-12 …); a 0.00 index-point join at 2016-12. `cpi_nac` = Total
  nacional. Cross-check: our month-on-month inflation recomputed from the levels
  matches INDEC's published figure to **max 0.05 pp** over 114 months.
* **Real rate.** `RealRate_t = NominalRate_t / CPIIndex_t × 100`, constant
  dic-2016 pesos. GBA is the primary deflator, national a robustness check.
* **Inflation transforms.** month-on-month, year-on-year, and 3/6/12-month
  compounded cumulative inflation, in both percent and fraction units.
* **Composite "Total".** The rate file has **no Total column**. A
  capacity-weighted composite is built:
  `rate_total = Σ_c w_c·rate_c / Σ_c w_c` over the six *hotelero* categories,
  `w_c` = as-of quarterly available room-nights (equal weights when capacity is
  missing). Labelled `total_composite` — derived, not an official series.
* **Capacity** is quarterly; attached *as-of the nearest prior snapshot* in
  `*_asof` columns with an explicit staleness lag. Revenue figures that combine
  monthly occupancy with quarterly capacity are labelled proxies.

Modelled categories: **1-2★, 3★, 4★, 5★** (core), plus Apart and Boutique where
useful, plus the composite Total. Hostel room-occupancy is never published;
"Otros/resto" is thin — both excluded from modelling.

### 3.3 Sample windows and the COVID break

| window | dates | use |
|---|---|---|
| long-run context | 2008-01 … 2017-12 | nominal-only charts (no official CPI) |
| **main analysis sample** | **2018-01 … 2019-12 + 2022-01 … 2026-05** | all estimation |
| COVID (held out) | 2020-01 … 2021-12 | tourism collapse + star-tier rates missing 2020-03 … 2021-12 |
| backtest: train | 2018-19 + 2022 | seasonal factors, real-rate target |
| backtest: validation | 2023 | choose τ\*, δ\* |
| backtest: test | **2024-01 … 2026-05** | untouched until final evaluation |

COVID 2020-21 is **not pooled** with normal periods. Effective clean sample ≈ 77
months per category.

---

## 4 · The inflation environment, 2018–2026

Two high-inflation episodes fall inside the main sample (GBA IPC):

| year | mean %/mo | max %/mo | Dec YoY |
|---|---|---|---|
| 2018 | 3.3 | 6.6 (Sep) | 47% |
| 2019 | 3.6 | 5.8 (Sep) | 53% |
| 2022 | 5.7 | 7.4 (Jul) | 95% |
| **2023** | **10.0** | **25.1 (Dec)** | **210%** |
| 2024 | 7.0 | 19.6 (Jan) | 122% |
| 2025 | 2.3 | 3.9 | 32% |

* **2018–2019** — currency-crisis inflation, ~3–4%/mo.
* **2022 → early-2024** — a sustained acceleration from ~4%/mo to double digits,
  peaking with the **December-2023 devaluation (25.1% in one month)**, then
  19.6% / 15.0% / 11.5% over Jan–Mar 2024.
* **mid-2024 onward** — sharp disinflation back to ~2–3%/mo.

Cumulative GBA CPI over 2018-01 → 2026-05: **×91**. The 2024–26 test window is a
*disinflation*; the 2022–23 selection window is an *acceleration* — the two
regimes stress the policies very differently (see §6.6, §6.8).

---

## 5 · Method

### 5.1 Descriptive erosion (notebook 04, Part 1)

Real hotel rates (index, first obs = 100) swung between roughly **80 and 200**
against a flat "kept pace with CPI" line (Charts 1–2). Mechanical erosion clock:
under a frozen nominal rate the real value after *k* months is `1 / Π(1+π)`. At
the sample's high-inflation pace (~9%/mo) it reaches **−5% in 1 month, −10% in
2 months**; at the low pace (~2%/mo), ~3 and ~5 months (`04_erosion_clock`).

### 5.2 Repricing behaviour and pass-through (notebook 05, Parts 2 & 7)

Per category: frequency of non-trivial changes, mean/median |Δln P|, mean
positive and negative change, the p10/p90 of the change distribution, and the
share of months the change beats CPI (`price_adjustment_by_category.csv`).

**Pass-through** — `Δln P_t = α + β·Δln CPI_t + ε` (contemporaneous, Newey–West
HAC SE, 6 lags), plus a short 0–2 distributed lag for a cumulative figure. Fitted
per category (Table 3).

**Inflation regimes** — data-driven **terciles of GBA monthly inflation** within
the sample (cuts ≈ 2.9% and 4.6%/mo; the high tercile averages 9.6%/mo, reaching
25%). Behaviour compared across regimes (Table 2).

**Key-hypothesis test** — *"high inflation → repriced more often"* vs *"→ larger,
more upward, higher pass-through, not more often"*. Pooled OLS over the four star
tiers, **category fixed effects, HAC SE**:

* magnitude: `|Δln P|_t = a + b·1[mid] + c·1[high] + FE`
* asymmetry: `1[ΔP>0]_t = … + FE` (linear probability)
* frequency: `1[|Δln P|>1%]_t = … + FE` (linear probability)
* pass-through: `Δln P_t = β0·Δln CPI + β1·(Δln CPI·1[mid]) + β2·(Δln CPI·1[high]) + FE`

### 5.3 Demand response and identification (notebook 06, Part 3)

**Naive elasticity** — `ln(occ)_t = α + β·ln(RealRate)_t + γ·infl_t + Σ month
dummies + trend + ε`, per category, HAC SE. Four specifications compared:
log–log, log–log + lagged real rate, percentage-point levels, and **logit** (to
respect the 0–100 bound). Table 4.

**Endogeneity** is discussed explicitly (reverse causality — hotels price into
expected demand; omitted seasonal/exchange-rate/event demand shocks; quarterly
capacity; the fact that high-inflation months coincide with high season).

**Identification attempts:**

| # | design | what it removes |
|---|---|---|
| A | year-on-year (12-month) differencing | fixed calendar-month seasonality |
| B | relative-price panel: each tier vs the cross-tier monthly mean, **month + category fixed effects**, clustered SE | *every* city-wide demand shock (time effects) |
| C | **2SLS** — endogenous `ln RealRate`, instrument = lagged log relative price of housing/utilities vs headline CPI (an operating-cost shifter); report first-stage F, Sargan/Hansen over-ID p | demand-driven price variation |

> The earlier version's second instrument — the *"Restaurantes y hoteles"* CPI
> division — was **dropped**: that division mechanically contains hotel prices
> (≈ 10.8% GBA weight, mostly restaurants), so it violates the exclusion
> restriction. Headline CPI is retained as deflator/regressor: the hotel
> sub-component of headline CPI is ~1%, immaterial.

### 5.4 The policy engine (notebook 07 + `src/policies.py`, Part 4)

Pure functions, unit-testable, with a **strict t−1 information set** (INDEC
publishes month-*t* CPI in mid-month *t+1*, so a month-*t* price may use CPI
through *t−1* only):

| policy | rule |
|---|---|
| **P0** frozen | `P_t = P_anchor` |
| **P1** monthly CPI | `P_t = P_{t-1}·(1 + π_{t-1})` |
| **P2** threshold τ | hold until `CUMINF ≥ τ`; then reset to `target_real × CPI_{t-1} / 100` |
| **P3** threshold τ + occ tilt δ | as P2, ×`(1 + δ·tanh(dev))`, `dev` = trailing-quarter occupancy vs its (training) seasonal norm |

All paths are anchored so each policy **starts at the same real level** (the
pre-COVID target = mean 2018–19 real rate), so the comparison is about *timing*,
not the starting price.

**On the revenue "optimum":** with constant-elasticity demand
`Q(P) = Q₀(P/P₀)^β`, revenue `= P₀Q₀(P/P₀)^{1+β}` is monotone in *P* for
β > −1 (inelastic) — so there is **no interior optimal price**; the revenue-max
τ pins to a grid boundary (`07_revenue_curves`). This is why the analysis is the
frequency/stability trade-off, and why occupancy enters only through the assumed
β grid `{0, −0.25, −0.5, −1.0}`.

### 5.5 Threshold optimisation and the frontier (notebook 08, Part 5)

Simulate P2 over the **selection window 2022–2023** (excludes test) for
τ ∈ {1,2,3,4,5,6,7,8,10}%, pooled across the five present categories. Record
repricing events, mean and worst real-price deviation from target, real-price
CV, occupancy, and revenue vs observed (Table 5).

Trace the **repricing frontier** (x = repricing events, y = mean |real-price
deviation|). The trade-off is strictly monotone, so every τ is technically
Pareto-efficient; the **knee** is located by normalising both axes to [0,1] and
taking the τ closest to the ideal corner. Also: an explicit
`Objective = Revenue − λ · N_reprice · mean_revenue` swept over
λ ∈ {0 … 0.12} (λ is an operational dial, *not* a calibrated cost).

### 5.6 Backtest (notebook 08, Part 6)

Seasonal occupancy factors and the real-rate target are fit on **train** only.
τ\* (the knee) and δ\* are chosen on **validation 2023**. The frozen choice is
evaluated on the **untouched test window 2024-01 … 2026-05**, across all β
scenarios (Table 6). The frontier is re-drawn on the test window as a shape
check (`08_frontier_robustness`). COVID 2020-21 is noted as a separate stress
period where star-tier rates are missing.

---

## 6 · Results

### 6.1 Real-price erosion (Table 1)

Main sample, COVID held out:

| category | mean real rate (dic-2016 ARS) | real-rate CV | worst month (% of mean) | mean rate MoM | months rate rose | months rate beat CPI |
|---|---|---|---|---|---|---|
| 1-2★ | 564 | 9.8% | 78% | 4.9% | 64% | 38% |
| 3★ | 784 | 16.4% | 67% | 6.4% | 70% | 47% |
| 4★ | 1,231 | 13.4% | 72% | 6.5% | 75% | 51% |
| 5★ | 3,191 | 19.0% | 69% | 6.6% | 61% | 44% |
| Total (composite) | 1,569 | 13.9% | 75% | 7.1% | 76% | 52% |

Real rates are **~3× more volatile than CPI** and beat CPI in only ~half of
months — catch-up is lumpy, concentrated around devaluation episodes.

### 6.2 How hotels reprice, and the key hypothesis (Table 2, `regime_tests.csv`)

Behaviour by inflation regime (pooled star tiers):

| regime | CPI %/mo | freq(|Δ|>1%) | mean |Δln rate| | median |Δln rate| | share up |
|---|---|---|---|---|---|
| low | 2.3 | 88% | 7.4% | 5.6% | 65% |
| mid | 3.9 | 90% | 6.2% | 4.5% | 71% |
| **high** | **9.6** | **98%** | **11.3%** | **10.3%** | **87%** |

Formal tests (high regime vs low; category FE; HAC):

| margin | coefficient | p |
|---|---|---|
| magnitude, |Δln P| (pp) | **+3.79** | **0.0012** |
| upward asymmetry, P(rise) | **+0.223** | **<0.001** |
| pass-through slope | +0.928 | 0.092 |
| frequency of >1% moves | +0.099 | 0.010 |

> **Verdict (supported):** high inflation makes each repricing *much larger*
> (+3.8 pp) and *far more one-directional* (+22 pp). The frequency of >1% moves
> also rises, but only ~10 pp from an already ~90% base — an order of magnitude
> smaller than the magnitude / asymmetry response.
> *"Inflation does not mainly make hotels reprice more often; it makes each
> repricing decision more consequential."*

### 6.3 Pass-through by category (Table 3)

`Δln rate` on `Δln CPI`, contemporaneous, HAC SE, main sample:

| category | β (contemp.) | t | R² | cumulative β (0–2 lags) |
|---|---|---|---|---|
| 3★ | **0.83** | 4.4 | .13 | 0.66 |
| 1-2★ | 0.88 | 7.4 | .19 | 0.79 |
| 4★ | 1.08 | 6.4 | .28 | 0.78 |
| Apart | 1.05 | 4.0 | .11 | 0.91 |
| Boutique | 1.20 | 6.4 | .30 | 0.92 |
| 5★ | **1.23** | 4.2 | .10 | 0.92 |

Upper tiers pass inflation through fully or slightly over; **3★ is the laggard**
and, consistent with §6.1, has the widest real-rate swings. Pass-through is
identified mostly off the 2022–24 acceleration.

### 6.4 Elasticity: associational, not identified (Table 4, `identification_summary.csv`)

Naive log–log β (occupancy w.r.t. real rate): 1-2★ **+0.85** (t 8.9), 3★ +0.10,
4★ +0.30 (t 2.1), 5★ +0.14, Apart +0.28, Boutique +0.12 — **positive or zero
everywhere**, the wrong sign for a demand curve. The logit and levels specs
agree.

Identification:

| strategy | result |
|---|---|
| A · YoY differencing | still positive (1-2★ +0.89, 4★ +0.43) — seasonality is not the confound |
| B · relative-price panel, month + category FE | **β = +0.07** (t 2.3) — no downward *relative* demand response |
| C · 2SLS (housing/utilities cost instrument) | first stages weak (F 2–17); where not weak, over-ID **rejected** (5★ p = 0.009, 3★ p = 0.000); 4★ β = −0.07 (t −0.17). No robust negative estimate. |

> **Occupancy elasticity is associational, not causally identified. Demand looks
> inelastic.** Consequently the policy simulations run across β ∈ {0, −0.25,
> −0.5, −1.0} and, per §6.6, the ranking of policies is essentially β-invariant.

### 6.5 The threshold frontier and its knee (Table 5, Chart 7, `lambda_sweep.csv`)

Selection window 2022–2023, pooled across categories:

| policy | repricing events | mean |real dev| | real-price CV | vs observed revenue |
|---|---|---|---|---|
| P2 τ = 1–3% | 21.6 | 7.9% | 5.1% | −10% |
| P2 τ = 4% | 21.0 | 8.0% | 5.0% | −10% |
| P2 τ = 5% | 19.2 | 8.3% | 5.0% | −10% |
| **P2 τ = 6% (knee)** | **17.2** | **8.8%** | 5.1% | −10% |
| P2 τ = 7% | 14.8 | 9.5% | 5.1% | −11% |
| P2 τ = 8% | 13.0 | 10.1% | 5.6% | −11% |
| P2 τ = 10% | 12.0 | 10.5% | 5.9% | −11% |
| P0 frozen | 1.0 | 50.7% | 41.4% | −44% |
| P1 monthly CPI | 21.6 | **16.6%** | 3.7% | −15% |
| **observed** | 21.4 | **15.7%** | **15.3%** | 0 (ref) |

Notes: (i) at τ ≤ 3% the 2022–23 inflation is so high that the threshold triggers
every month; differentiation begins at τ ≥ 4%. (ii) the ~−10% revenue vs observed
for the threshold rows reflects that observed pricing sat, on average, *above*
the pre-COVID real target during 2022–23 (a real overshoot); the rows are matched
on the *target*, not on the observed level, so this is a level effect, not a
timing loss — the OOS test (§6.6) controls for it. (iii) the worst single-month
real deviation is τ-invariant (≈ −26%): it is the unavoidable one-month CPI
publication lag around the Dec-2023 spike.

**Knee: τ\* = 6%.** The λ-objective picks τ = 4% at λ = 0.01, 5% at λ = 0.02,
7% at λ = 0.03 — i.e. any moderate repricing penalty lands in the **4–7% band**.
Observed pricing is dominated on both axes (same change count as τ = 1–3%, but
2× the real-price deviation and 3× the CV).

### 6.6 Out-of-sample backtest (Table 6, Chart 8)

Frozen τ\* = 6%, δ\* from validation; evaluated on **2024-01 … 2026-05**, pooled
across categories, β = −0.5:

| policy | price changes | mean |real dev| | real-price CV | RevPAR vs observed |
|---|---|---|---|---|
| **P0** frozen | 1 | **53%** | 27% | −32% |
| **P1** monthly CPI | 25 | 4.5% | 3.9% | +0.7% |
| **P2** τ = 6% | **14** | **5.9%** | **3.7%** | +0.0% |
| **P3** τ = 6% + occ tilt | 14 | 8.2% | 4.9% | −1.0% |
| observed (hotels) | 25 | 11.2% | 13.3% | 0 (ref) |

Across β ∈ {0, −0.25, −0.5, −1.0} the revenue column stays within ±0.5 pp for
every policy — **the ranking does not depend on the (unidentified) elasticity.**

> **P2 at τ ≈ 6% makes ~45% fewer price changes than monthly indexing, for the
> same real-price control and the same revenue, and holds the real rate about
> twice as tightly as observed pricing did at ~half the changes.**
>
> **P3 (occupancy tilt) did not help** — 2024–25 occupancy ran below its
> seasonal norm, so the tilt shaved the catch-up and *added* real erosion; with
> demand inelastic there is no offsetting occupancy gain. Treat the tilt as a
> lever, not a proven improvement.
>
> **P1 (monthly indexing) is period-specific.** It is fine here because 2024–26
> was a disinflation; in the 2022–23 acceleration its real-price deviation was
> ~17% (Table 5) — it only ever adds last month's lagged print and never catches
> up the accumulated gap.

### 6.7 Category heterogeneity (Table 7, Chart 6)

Per-category knee τ\* (each category's own 2022–23 frontier):

| category | pass-through β | mean |Δln rate| | knee τ\* | OOS repricing cut vs P1 | OOS |real dev| (P2) vs observed |
|---|---|---|---|---|---|
| 1-2★ | 0.88 | 6.7% | 6% | −44% | 5.8% vs 9.6% |
| 3★ | 0.82 | 8.1% | 6% | −44% | 5.8% vs 11.6% |
| 4★ | 1.08 | 7.6% | 6% | −44% | 5.8% vs 10.3% |
| 5★ | 1.23 | 10.6% | 6% | −44% | 5.8% vs 14.6% |
| Total (composite) | — | — | 6% | −48% | 6.0% vs 10.0% |

> **The *timing* rule is common — τ\* ≈ 6% for every category.** Heterogeneity is
> in *how* categories pass through (3★ lowest at 0.83, 5★ highest at 1.23) and in
> change size (5★ makes the largest moves), not in *when* to trigger. A single
> τ ≈ 6% serves all; upper tiers can sit at the top of the 4–7% band.

### 6.8 Robustness (notebook 10, `robustness_matrix.csv`, `robustness_regime.csv`)

| claim | verdict across variants |
|---|---|
| **A** — knee τ\* in the 4–7% band | 7/8 (τ = 7% under the national CPI deflator) |
| **B** — threshold rule beats observed pricing on real-price stability **and** change count, OOS | **8/8** |
| **C** — monthly indexing lags in an acceleration | ~17% real-price deviation in 2022–23 (7/8); ~4.5% in the 2024–26 disinflation |
| **D** — occupancy inelastic / not identified | holds (notebook 06) |
| **E** — larger & more-upward changes, not mainly more frequent | magnitude & asymmetry significant 3/3; frequency effect ~9 pp, an order of magnitude smaller |

Variants tested: GBA ↔ national CPI; room ↔ bed occupancy; β ∈ {0, −0.25, −0.5,
−1}; exclude extreme-inflation months (> p90); selection = 2023 only; core star
tiers vs including the composite.

---

## 7 · The recommended rule (Chart 9)

> **Each month**, compute cumulative CPI inflation since your last price change
> (`CUMINF`).
>
> * **`CUMINF` < τ\*** — τ\* ≈ **6%** (4–7% band; top of the band for 4–5★):
>   **hold** the price. No repricing review.
> * **`CUMINF` ≥ τ\***: **trigger a repricing review** and reset the list price to
>   restore the target *real* rate (multiply by CPI since the last change).
> * At the reset, **tilt by demand** (optional lever): occupancy above its
>   seasonal norm → fuller pass-through (× 1.00–1.05); at norm → inflation-matched
>   (× 1.00); below norm → partial (× 0.95–1.00). *In this data the tilt did not
>   improve out-of-sample real-price control.*

Backtested (2024-01 … 2026-05, out-of-sample): this would have **cut the number
of price changes roughly in half versus repricing every month**, held the real
room rate within **~6% of target** (versus **~11%** for what Buenos Aires hotels
actually did), and left revenue essentially unchanged — and it holds across the
robustness matrix.

In low-inflation periods (≲ 2%/mo) the trigger fires every 2–3 months and a
simple CPI reset suffices; as inflation accelerates it approaches monthly, which
is when the level-restoring reset (rather than P1's increment-adding) matters
most.

---

## 8 · Limitations

1. **Aggregate data.** City × category × month. This is a *category-level*
   pricing policy, not individual-hotel dynamic pricing / yield management.
2. **No official CPI before 2016-12.** The 2008–2017 stretch is nominal-only
   context; the main sample is ≈ 77 clean months per category — small for
   fine-grained regime splits (the mid-regime pass-through point estimate in
   Table 2 is imprecise; only the low ≈ 0 / high > 0 pattern is interpretable).
3. **Occupancy elasticity is not causally identified.** Instruments are weak or
   invalid; the relative-price panel gives ≈ 0. Policy results are reported
   across an assumed β grid and are near-invariant to it, but a genuine causal
   elasticity would need a supply/cost instrument that is not available here.
4. **No marginal-cost data.** This is a revenue/real-price *trade-off* study, not
   profit maximisation. The constant-elasticity revenue optimum is degenerate
   (monotone in price) and is not used.
5. **Repricing *frequency* is only weakly observable** — `average_rate` is a
   category mean, so it moves most months regardless. The magnitude, asymmetry,
   pass-through and threshold results do not depend on the frequency measure.
6. **COVID 2020-21** is a genuine data hole (star-tier rates missing 2020-03 …
   2021-12); held out entirely.
7. **The composite "Total"** is a capacity-weighted construction with quarterly
   weights, not an INDEC/EHOBA series.
8. **`λ` in the objective** is an operational dial, not a calibrated monetary
   repricing cost; the Pareto frontier is the more defensible object and the λ
   sweep is reported in full.
9. **Hotel prices are a component of the CPI** used as deflator/regressor, but at
   ~1% of the headline index and as a different price concept (fixed-sample rack
   rates vs reported ADR); the contaminated "Restaurants & hotels" division was
   removed from the instrument set.

---

## 9 · Reproducibility

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name argentina-hotels --display-name "Python (argentina-hotels)"
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.kernel_name=argentina-hotels notebooks/*.ipynb        # 01 → 10, ~2 min
```

* `data/raw/**` is never modified. `data/processed/**` is git-ignored and fully
  regenerated by notebooks 01–03.
* Every cleaning / modelling decision is appended to
  `data/processed/cleaning_audit_log.csv` (idempotent per notebook).
* Core logic is in `src/` (`config`, `common`, `policies`, `pricing_eval`), not
  buried in notebooks. `src/policies.py` and `src/pricing_eval.py` are pure and
  independently testable.

### Notebook map

| notebook | brief part(s) | key outputs |
|---|---|---|
| `01_load_data` | — | `data/processed/01_loaded/*.parquet` |
| `02_clean_data` | — | `02_panel_long`, `02_cpi_monthly`, `02_capacity_quarterly` |
| `03_merge_data` | — | `03_analysis_panel.parquet`, `data_dictionary.csv`, INDEC cross-check |
| `04_descriptive_inflation_story` | 1 | Charts 1–2, erosion clock, sample map, Table 1 |
| `05_repricing_behaviour` | 2, 7 | Tables 2–3, `regime_tests.csv`, Charts 3–4 |
| `06_demand_and_identification` | 3 | Table 4, `identification_summary.csv`, Chart 5, `06_identification.png` |
| `07_pricing_policies` | 4 | `07_revenue_curves`, `07_policy_paths_4star`, `table_policy_example.csv` |
| `08_threshold_backtest` | 5, 6 | Tables 5–6, `pareto_frontier.csv`, `lambda_sweep.csv`, Charts 7–8, `08_frontier_robustness` |
| `09_heterogeneity_and_policy` | 8, 10 | Table 7, Chart 6, decision-tree Chart 9 |
| `10_robustness` | 9 | `robustness_matrix.csv`, `robustness_regime.csv` |

### Tables (`outputs/tables/`)

`table1_descriptives` · `table2_regime_behaviour` · `table3_passthrough` ·
`table4_elasticity` · `table5_threshold_sim` · `table6_out_of_sample` ·
`table7_category_policy` — plus `price_adjustment_by_category`, `regime_tests`,
`identification_summary`, `pareto_frontier`, `lambda_sweep`, `robustness_matrix`,
`robustness_regime`, `coverage_by_category`, `data_dictionary`,
`missing_value_map`, `outlier_register`, `table_policy_example`.

### Charts (`outputs/figures/`)

1 `04_chart1_moving_target` — CPI vs hotel rates, 2008–2026
2 `04_chart2_nominal_vs_real` — nominal vs real rates
3 `05_chart3_magnitude_by_regime` — price-change size by inflation regime
4 `05_chart4_frequency_by_regime` — frequency vs upward-share by regime
5 `06_chart5_occupancy_tradeoff` — occupancy vs real rate, controls partialled out
6 `09_chart6_category` — pass-through / knee-τ / repricing-cut by category
7 `08_chart7_frontier` — the repricing frontier + knee
8 `08_chart8_backtest` — dynamic repricing vs mechanical indexing, test window
9 `09_chart9_decision_tree` — the rule

Diagnostics: `03_indec_crosscheck`, `03_composite_check`, `04_erosion_clock`,
`04_sample_map`, `05_cumulative_passthrough`, `06_identification`,
`07_revenue_curves`, `07_policy_paths_4star`, `08_frontier_robustness`.
