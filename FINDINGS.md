# When should a hotel change its price?
### Dynamic pricing under inflation — evidence from Buenos Aires hotels

The central decision is the **timing** of repricing, not a single optimal room
price. Inflation erodes the real value of a fixed nominal rate; but every price
change carries operational / customer friction. The hotel therefore needs an
**inflation-aware, state-dependent repricing rule**.

Level of analysis: **Buenos Aires City × hotel category × month** (aggregate — not
individual-hotel dynamic pricing). Deflator: **IPC Región GBA** (national as
robustness), base dic-2016 = 100. Main sample **2018-01…2019-12 + 2022-01…2026-05**;
**COVID 2020-21 held out**. Categories: 1-2★, 3★, 4★, 5★, plus a capacity-weighted
**Total (composite)**. No marginal-cost data → we compare *policies* and map the
*trade-off*; we do **not** claim a profit- or revenue-maximising price.

Every number below is reproduced by `notebooks/04–10`.

---

## 1 · How fast does inflation erode a hotel's real price?

Real hotel rates swung from **~80 to ~200** (index, 2018-01 = 100) over the
sample against a flat "kept pace with CPI" line (Charts 1–2). Under a **frozen
nominal rate**, the real value falls to **−5% in 1 month and −10% in 2 months**
at the sample's high-inflation pace (~9%/mo); ~3 and ~5 months at the low pace
(~2%/mo) (`04_erosion_clock`). Doing nothing is not an option in this
environment.

## 2 · Do hotels respond to inflation by repricing more often, or differently?

`average_rate` is a category mean, so a menu-cost "frequency" is barely
observable (it moves most months in every regime). Testing the hypothesis
formally (pooled over the four star tiers, category FE, HAC SE; `regime_tests.csv`):

| high-inflation tercile vs low | coef | p | |
|---|---|---|---|
| **magnitude** \|Δln rate\| | **+4.4 pp** | <0.002 | each change much larger |
| **upward asymmetry** P(rise) | **+0.20** | <0.001 | far more one-sided |
| pass-through slope | +0.9 | 0.09 | somewhat higher |
| frequency of >1% moves | +0.09 | 0.01 | up, but only ~9 pp from an already ~90% base |

> **Inflation does not mainly make hotels reprice more often — it makes each
> repricing decision more consequential** (bigger and more one-directional). This
> survives GBA↔national CPI and room↔bed occupancy (`robustness_regime.csv`).

**Pass-through by category** (Δln rate on Δln CPI, contemporaneous, HAC;
Table 3): 3★ **0.83**, 1-2★ 0.88, 4★ **1.08**, 5★ **1.23**. Upper tiers pass
inflation through fully or slightly over; **3★ is the laggard**.

## 3 · How sensitive is occupancy to real room prices?

The naive elasticity is **positive or ~zero** (1-2★ +0.85, 3★ +0.10, 4★ +0.30,
5★ +0.14; Table 4) — the wrong sign for a demand curve, because hotels raise real
prices *into* strong demand. Identification attempts (notebook 06):

* **relative-price panel** (tier vs cross-tier mean, month + category FE): β = **+0.07** — no downward relative demand response.
* **2SLS** with a housing/utilities operating-cost instrument: first stages weak (F ≈ 2–17) and the over-ID test is rejected for the categories where it isn't weak. The previously-used "Restaurants & hotels" CPI instrument was **dropped** — it mechanically contains hotel prices.

> **Occupancy elasticity is associational, not causally identified. Demand looks
> inelastic.** The policy simulations are therefore run across an assumed-β grid
> {0, −0.25, −0.5, −1.0}; results barely move with β (`robustness_matrix.csv`).

## 4 · Candidate repricing policies

| | rule |
|---|---|
| **P0** frozen nominal | never change price — the erosion reference |
| **P1** monthly CPI index | raise by last month's published inflation every month |
| **P2** cumulative-inflation threshold τ | hold until CPI has risen ≥ τ since the last change, then reset to restore the **target real rate** |
| **P3** threshold τ + occupancy tilt δ | as P2, but scale the reset by trailing occupancy vs its seasonal norm |

All use information available at **t−1 only** (INDEC publishes month-t CPI in
mid-month t+1). With demand inelastic and no cost data, the constant-elasticity
revenue curve is monotone in price (`07_revenue_curves`), so there is **no
interior optimal price** — the analysis is the frequency/stability/revenue
trade-off.

## 5 · The threshold, derived — not assumed

Simulating P2 over 2022–2023 for τ ∈ {1…8, 10}% (Table 5) and tracing the
**repricing frontier** (Chart 7): the trade-off is smooth (every τ technically
Pareto-efficient), and its **knee is τ* ≈ 6%** (4–7% band). The λ-objective
`Revenue − λ·N_reprice·mean_revenue` selects τ = 4–7% for any moderate penalty
(`lambda_sweep.csv`).

What hotels actually did, over the same window: **21 price changes, real-price
deviation 16%, CV 15%**. Every threshold τ tracked the real price **~2× tighter**
at a similar or lower change count.

### A menu-cost (s, S) foundation (notebook 11)

The trigger is the canonical **Sheshinski–Weiss (1977)** menu-cost rule: an
(s, S) band of width `w* = (12·κ·π/b)^{1/3}`, repriced when cumulative inflation
reaches τ = w\*. Calibrated to the observed (deseasonalised) price-change size it
predicts **τ\* ≈ 6.3%** (4.8–9.3% by tier) — matching the fitted knee. Its sharp
prediction that price-change **size ∝ π^{1/3}** holds in the data almost exactly
(estimated inflation-elasticity **0.33**, CI [0.17, 0.49]); the companion
prediction that **frequency ∝ π^{2/3}** is rejected (elasticity ≈ 0). Inflation
is absorbed on the size margin — the structural version of §2.

## 6 · Out-of-sample backtest (train 2018-19 + 2022 · validate 2023 · test 2024-01…2026-05)

Freezing **τ* = 6%** from the selection window and evaluating on the untouched
test window (Table 6, β = −0.5, pooled across categories):

| policy | price changes | real-price dev (mean \|·\|) | real-price CV | RevPAR vs observed |
|---|---|---|---|---|
| **P0** frozen | 1 | **53%** | 27% | −32% |
| **P1** monthly CPI | 25 | 4.5% | 3.9% | ≈0 |
| **P2 τ = 6%** | **14** | **5.9%** | **3.7%** | ≈0 |
| **P3** τ = 6% + occ tilt | 14 | 8.2% | 4.9% | −1% |
| observed (hotels) | 25 | 11.2% | 13.3% | 0 (ref) |

> **P2 at τ ≈ 6% roughly halves the number of price changes vs monthly indexing,
> for the same real-price control and the same revenue** — and holds the real
> price about twice as tightly as what hotels actually did, at ~half the changes.
> The occupancy tilt (P3) **did not help** out-of-sample (demand inelastic, and
> 2024–25 was a weak-demand disinflation).
>
> Monthly indexing (P1) is only "fine" here because 2024–26 was a *disinflation*;
> in the 2022–23 *acceleration* P1's real-price deviation was **~17%** because it
> only ever adds last month's (lagged) print and never catches up the gap
> (`robustness_matrix.csv`, Table 5).

## 7 · Heterogeneity across categories

The **knee τ* is ≈ 6% for every category** (Table 7, Chart 6) — the *timing* rule
is common. Categories differ in *how they pass through*: 3★ passes through least
(β 0.83) and has the most real value to lose; 5★ passes through most (β 1.23) and
makes the largest changes (mean \|Δln\| 10.6% vs 6.7% for 1-2★). A single τ ≈ 6%
serves all; upper tiers can carry the top of the 4–7% band.

## 8 · Robustness (notebook 10)

| claim | verdict |
|---|---|
| **A** knee τ* in 4–7% | holds 7/8 variants (τ = 7% under national CPI) |
| **B** threshold beats observed on real-price stability *and* fewer changes | **8/8 variants** |
| **C** monthly indexing lags in an acceleration | madev ≈ 17% in 2022-23 (7/8); fine in the 2024-26 disinflation |
| **D** occupancy inelastic / not identified | holds (nb 06) |
| **E** larger & more-upward changes, not mainly more frequent | magnitude & asymmetry significant 3/3; frequency effect ~9 pp, an order of magnitude smaller |

Tested across: GBA↔national CPI, room↔bed occupancy, β ∈ {0, −0.25, −0.5, −1},
exclude extreme-inflation months, selection = 2023-only, core tiers vs +composite.

---

## The rule (Chart 9)

> **Each month**, compute cumulative CPI inflation since your last price change
> (`CUMINF`).
>
> * **`CUMINF` < τ\*** (τ\* ≈ **6%**; 4–7% band, top of the band for 4–5★):
>   **hold** the price — no repricing review.
> * **`CUMINF` ≥ τ\***: **trigger a repricing review** and reset the list price to
>   restore the target *real* rate (multiply by CPI since the last change).
> * At the reset, **tilt by demand**: occupancy above its seasonal norm →
>   fuller pass-through (× 1.00–1.05); at norm → inflation-matched (× 1.00); below
>   norm → partial (× 0.95–1.00). *(In this data the tilt did not improve
>   out-of-sample real-price control — treat it as a lever, not a proven gain.)*

Historically this would have **cut the number of price changes roughly in half
versus repricing every month**, kept the real room rate within ~6% of target
(versus ~11–16% for what Buenos Aires hotels actually did), and left revenue
essentially unchanged — and it holds up out-of-sample and across robustness
checks.

---

## Limitations

* Aggregate category data — a category-level policy, not individual-hotel dynamic
  pricing.
* No official CPI before 2016; main sample ≈ 77 clean months/category.
* Occupancy elasticity is **not causally identified**; policy results are shown
  across assumed β and are nearly β-invariant.
* No marginal-cost data → revenue trade-off, not profit maximisation; the
  constant-elasticity revenue optimum is degenerate and not used.
* `average_rate` is a category mean, so repricing *frequency* is only weakly
  observable; the magnitude / asymmetry / threshold results do not depend on it.
* COVID 2020-21 is a genuine data hole (star-tier rates missing); held out.
* The composite "Total" rate is a capacity-weighted construction (quarterly
  weights), not an official series.
