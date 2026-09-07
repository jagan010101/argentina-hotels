# When should a hotel change its price?
## Dynamic pricing under inflation — evidence from Buenos Aires hotels

In **December 2023, consumer prices in Argentina rose 25% in a single month.** A
Buenos Aires hotel that left its rate untouched that month handed its guests a
25% discount without meaning to. Over 2018–2025 the price level multiplied
roughly **77-fold**.

When money loses value that fast, the hard question for a hotel is not *what
price to charge*. It is *how long it can wait before it has to change the price
again* — because every price change costs something too (staff time, re-listing
on booking sites, annoyed repeat guests, review risk). Wait too long and
inflation quietly eats your margin. React to every twitch and you pay the
friction every month.

This report uses eight years of official city-level data to find the sweet spot,
and turns it into a rule a hotel can actually follow.

> **The answer in one breath.** Don't chase the "right" price — you can't
> compute one from this data, and trying to is a trap. Instead, **let cumulative
> inflation build up to about 6% since your last change, then reset the price to
> restore its real value.** Backtested on years the rule never saw, this makes
> **~half as many price changes as re-pricing every month, holds the real room
> rate about twice as steady as hotels actually managed, and leaves revenue
> unchanged.** The 6% figure is not a fudge factor: it is what a 1977 textbook
> model of pricing under inflation predicts once you plug in Argentina's numbers.

*Scope: Buenos Aires City × hotel category × month — aggregate official
statistics, not individual-hotel yield management. Every number, table and chart
below is reproduced by the seven pipeline notebooks `01`–`07` (plus an
exploratory `08`, §13); outputs land in `outputs/`.*

---

## 1 · The problem, plainly

Inflation is a slow leak in the real value of any fixed price. If a hotel freezes
its nominal rate, the purchasing power of that rate after *k* months is just
`1 / (compounded inflation over those k months)`.

At the **high-inflation pace in our sample (~9%/month)** a frozen rate loses
**5% of its real value in one month and 10% in two**. Even at the calm pace
(~2%/month) it is 10% down in about five months. Doing nothing is not a neutral
option — it is a standing, automatic price cut.

The obvious fix — **raise the price by last month's inflation, every month** — has
two problems. It is a lot of price changes, each with a cost. And it only ever
adds *last* month's number, so when inflation accelerates it is permanently a
step behind and never closes the gap it has already opened.

So the real decision variable is **timing**: how much cumulative inflation to
let accumulate before you act, and — when you act — resetting the price to its
*target real level* rather than just bolting on the latest monthly figure.

Everything in this report is in service of two questions:

1. **How do hotels actually cope with inflation** — and what does the data let us
   measure cleanly (and not)?
2. **What is the efficient waiting threshold**, does it survive an honest
   out-of-sample test, and is there any reason to believe it beyond the fit?

---

## 2 · How bad is the inflation?

Two high-inflation episodes fall inside the analysis window (GBA consumer price
index):

| year | avg %/month | worst month | Dec year-on-year |
|---|---|---|---|
| 2018 | 3.3 | 6.6 (Sep) | 47% |
| 2019 | 3.6 | 5.8 (Sep) | 53% |
| 2022 | 5.7 | 7.4 (Jul) | 95% |
| **2023** | **10.0** | **25.1 (Dec)** | **210%** |
| 2024 | 7.0 | 19.6 (Jan) | 122% |
| 2025 | 2.3 | 3.9 | 32% |

* **2018–2019** — currency-crisis inflation, a steady 3–4%/month.
* **2022 → early 2024** — a sustained acceleration from ~4%/month into double
  digits, peaking with the **December-2023 devaluation (25% in one month)**, then
  20% / 15% / 12% over January–March 2024.
* **mid-2024 onward** — a sharp disinflation back to ~2–3%/month.

**Cumulative GBA inflation, Jan 2018 → Nov 2025: ×77.**

### A yardstick: Argentina vs India

To feel how extreme this is, compare a "normal" emerging-market inflation
record. Using calendar-year average CPI (World Bank series for India; our panel
for Argentina), anchored at 2017 = 1:

| what 1 unit of 2017 money is worth in… | India (rupee) | Argentina (peso) |
|---|---|---|
| 2020 | 1.15 | 2.9 |
| 2023 | 1.36 | 17.2 |
| **2025** | **1.46** | **79** |

**One rupee kept in 2017 buys what ₹1.46 buys in 2025. One peso buys what ~79
pesos buy.** The peso lost real value roughly **54× faster** than the rupee over
the same eight years. Argentine annual inflation ran **6× to 45× India's**, year
by year (`02_argentina_vs_india_inflation.png`, `02_currency_erosion.png`).

This is why every price in this report is worked in **real** (inflation-adjusted)
terms, and why the modelling window matters: the **2022–23 "acceleration"** and
the **2024–25 "disinflation"** are genuinely different regimes and stress the
policy in opposite ways.

---

## 3 · The data on one page

### 3.1 Sources — all official, `data/raw/`, read-only

| file | what it is | frequency | span |
|---|---|---|---|
| `Ehoba_03a_0811.xlsx` | average room rate by category (pesos) — **the price** | monthly | 2008-01 … 2026-05 |
| `Ehoba_02a_0811.xlsx` | room-occupancy rate (%) | monthly | 2008-01 … 2026-05 |
| `Ehoba_04_0811.xlsx` | bed-occupancy rate (%) | monthly | 2008-01 … 2026-05 |
| `Ehoba_VA_0811.xlsx` | travellers hosted (hotel sector) | monthly | 2013-01 … 2026-05 |
| `Ehoba_1_ano.xlsx` | establishments, available room-/bed-nights | quarterly | 2008 … 2026-03 |
| `sh_ipc_08_26.xls` | INDEC CPI, base dic-2016 = 100 (GBA + national + 12 sub-indices) | monthly | GBA 2016-04 … 2026-07 |
| `India_CPI/` | World Bank India CPI inflation (annual %) — context only | annual | 1960 … 2025 |

Hotel data: *Buenos Aires Hotel Occupancy Survey (EHOBA)*, Buenos Aires City
Statistics and Census Institute. Prices: INDEC. The full sheet-by-sheet audit
(merged cells, header quirks, missing-value tokens, category redefinitions) is
carried out in the *load* section of `01_build_dataset`, with every decision
logged to `data/processed/cleaning_audit_log.csv`.

**One caveat that shapes everything:** the "average rate" is a **category mean**
(roughly revenue per occupied room-night), *not* a posted or rack price. It moves
almost every month simply because the mix of rooms sold shifts. So we cannot
cleanly measure *how often* a hotel "changes its price" — instead we lean on the
**size**, **direction** and **inflation pass-through** of the monthly change,
which are informative.

### 3.2 The analysis panel

Notebook `01_build_dataset` turns six presentation-formatted spreadsheets into
one clean monthly table (`data/processed/03_analysis_panel.parquet`, 2,407 rows,
11 categories):

* **Deflator.** `cpi_gba` = the GBA headline index, spliced from the dic-2016
  bridge sheet onto the national sheet's GBA block (the join is exact, 0.00
  index points, at 2016-12). Our month-on-month inflation recomputed from levels
  matches INDEC's published figure to **within 0.05 pp over 114 months**.
* **Real rate** = nominal rate ÷ CPI × 100 (constant dic-2016 pesos). GBA is
  primary; the national index is a robustness check.
* **Inflation transforms** — month-on-month, year-on-year, and 3/6/12-month
  *compounded* cumulative inflation.
* **Composite "Total".** The rate file has no "all hotels" column, so we build a
  capacity-weighted one (weights = available room-nights). Clearly labelled
  `total_composite` — derived, not an official series.
* **Capacity** is quarterly and attached "as-of the nearest prior snapshot" with
  an explicit staleness lag.

Modelled: **1-2★, 3★, 4★, 5★** (core), plus Apart and Boutique where useful, plus
the composite. Hostel room-occupancy is never published; "Other/rest" is too
thin — both dropped from modelling.

### 3.3 The windows — and the COVID hole

| window | dates | role |
|---|---|---|
| long-run context | 2008-01 … 2017-12 | nominal-only charts (no official CPI yet) |
| **main analysis sample** | **2018-01 … 2019-12 + 2022-01 … 2025-11** | all estimation |
| COVID (held out) | 2020-01 … 2021-12 | tourism collapse; star-tier rates missing for 22 of 24 months |
| backtest — train | 2018-19 + 2022 | seasonal factors, real-rate target |
| backtest — validation | 2023 | pick the threshold τ\* and tilt δ\* |
| backtest — test | **2024-01 … 2025-11** | untouched until the final evaluation |

COVID is **never pooled** with normal months — hotels were legally barred from
taking tourists and some housed quarantine patients, so there is no market price
to model. The raw panel runs to 2026-05, but from 2025-12 the EHOBA rates are
provisional and straddle a data gap, so estimation stops at 2025-11. Effective
clean sample: **≈ 71 months per category**.

---

## 4 · Finding 1 — inflation makes each price move *bigger*, not more *frequent*

Split every month into three **inflation regimes** (low / mid / high terciles of
GBA monthly inflation; the high tercile averages 9.9%/month and reaches 25%),
pool the four star tiers, and look at how the monthly price change behaves:

| regime | CPI %/mo | share of months with a >1% move | mean size of move | median size | share that are **increases** |
|---|---|---|---|---|---|
| low | 2.4 | 87% | 7.1% | 5.0% | 68% |
| mid | 4.2 | 92% | 6.8% | 5.0% | 76% |
| **high** | **9.9** | **99%** | **11.4%** | **10.6%** | **87%** |

Formal test (high regime vs low, pooled with category fixed effects and
autocorrelation-robust standard errors, `regime_tests.csv`):

| what changes with high inflation | effect | p-value |
|---|---|---|
| **size** of the price move | **+4.3 pp larger** | **<0.001** |
| **direction** — probability it's an increase | **+20 pp more likely up** | **<0.001** |
| pass-through slope | +1.02 steeper | 0.10 |
| **frequency** of >1% moves | +13 pp (from a ~86% base) | **<0.001** |

> **Verdict (supported).** High inflation makes each repricing **much larger and
> almost always upward**. The frequency of big moves also rises (+13 pp), but
> from an already ~86% base, and the size and direction effects are what
> dominate. *"Inflation does not mainly make hotels reprice more often; it makes
> each repricing decision more consequential."*

This matters for the rule: since the *frequency* margin is nearly maxed out and
barely responsive, the lever that matters is *how large a real-price gap you
allow before you close it*.

---

## 5 · Finding 2 — you cannot watch demand react to price

If you raise the real price, does occupancy fall? We tried hard to measure this
and the honest answer is: **not from this data.**

**The naive number.** Regress log occupancy on the log real rate (plus
seasonality, trend, inflation), per category, four functional forms. The slope
comes out **zero or positive everywhere** — 1-2★ +0.83, 3★ +0.12, 4★ +0.28,
5★ +0.13, Apart +0.34, Boutique +0.12. That is the *wrong sign* for a demand
curve, and the reason is obvious: **hotels raise real prices into strong
demand** (holidays, events, favourable exchange-rate windows for foreign
tourists), so price and occupancy rise together.

**Three attempts to break that entanglement:**

| approach | idea | result |
|---|---|---|
| A · year-on-year differencing | remove fixed seasonal demand | still positive for most tiers (3★ +0.13, 4★ +0.40, Apart +0.66); 1-2★ ≈ 0 — seasonality is not the confound |
| B · relative-price panel | compare tiers *within the same month* (month + category fixed effects), so every city-wide demand shock is absorbed | **β ≈ +0.07** — essentially no relative demand response |
| C · instrumental variables | use a supply-side cost shifter (lagged housing/utilities inflation) as an instrument for the real rate | first stage weak for most tiers (F 2–16); where not weak, the over-identification test **rejects**; 4★ point estimate −0.19 (not significant) |

> **Occupancy elasticity is associational, not causally identified. Demand looks
> inelastic.** No design delivers a robust negative estimate.

**Why this does not sink the project.** Two reasons:

1. We were never going to claim a "revenue-maximising price" anyway. With
   constant-elasticity, inelastic demand, revenue is *monotone* in price — there
   is no interior optimum without marginal-cost data, which we do not have
   (`07_revenue_curves`). So the analysis is deliberately a **timing / stability
   trade-off**, not an optimisation.
2. Every policy simulation is run across an **assumed-elasticity grid**
   β ∈ {0, −0.25, −0.5, −1.0}, and — see §8 — the ranking of policies barely
   moves across it. The policies being compared all steer toward the *same real
   price*, so the elasticity (which acts on the price *level*) nearly cancels
   out.

---

## 6 · Finding 3 — rates roughly keep up with CPI, but lumpily

**Pass-through.** Regress the monthly change in log rate on the monthly change in
log CPI (contemporaneous, HAC standard errors):

| category | pass-through β | t | cumulative over 0–2 months |
|---|---|---|---|
| **3★** | **0.78** | 4.4 | 0.60 |
| 1-2★ | 0.84 | 7.1 | 0.74 |
| 4★ | 1.04 | 6.1 | 0.73 |
| Apart | 0.97 | 4.4 | 0.81 |
| Boutique | 1.20 | 6.3 | 0.92 |
| **5★** | **1.16** | 4.0 | 0.83 |

Upper tiers pass inflation through fully or a touch more; **3★ is the laggard**.

**But the catch-up is not smooth.** Over the main sample, COVID held out:

| category | mean real rate (dic-2016 ARS) | how volatile vs CPI | worst month (% of its own mean) | mean monthly move | months the rate rose | months it beat CPI |
|---|---|---|---|---|---|---|
| 1-2★ | 561 | CV 9.7% | 79% | 5.3% | 68% | 41% |
| 3★ | 791 | CV 16.0% | 66% | 6.4% | 75% | 51% |
| 4★ | 1,236 | CV 13.4% | 71% | 6.8% | 80% | 55% |
| 5★ | 3,215 | CV 18.7% | 71% | 7.2% | 66% | 48% |
| Total (composite) | 1,578 | CV 13.7% | 75% | 7.6% | 79% | 55% |

> Real rates are **~3× more volatile than CPI** and beat CPI in only about
> **half** of months. Hotels catch up in lumps, concentrated around devaluation
> episodes, and let the real rate sag in between. That sag is exactly what a
> better *timing* rule can tighten.

---

## 7 · The rule — optimise the *timing*, not the price

Since there is no "optimal price" to find, define a family of **timing rules** and
compare them on the axes we *can* measure: number of price changes, how tightly
the real rate is held to target, occupancy, revenue.

Four candidates (in `src/policies.py`; each may use CPI only through *t−1*, since
INDEC publishes month-*t* inflation in mid-month *t+1*):

| policy | rule |
|---|---|
| **P0** frozen | never change the nominal price |
| **P1** monthly CPI | raise by last month's inflation, every month |
| **P2** threshold τ | hold until cumulative inflation since the last change ≥ **τ**, then reset the price to restore the target real rate |
| **P3** threshold τ + tilt δ | P2, but scale the reset up/down by whether trailing occupancy is above/below its seasonal norm |

Two benchmarks travel alongside: **P0** (the erosion reference) and **observed**
(what hotels actually charged). All paths start at the same real level, so the
comparison is purely about timing.

### Deriving τ — don't guess, trace the trade-off

Simulate P2 over the **2022–23 selection window** (test data excluded) for
τ from 1% to 10%:

| policy | price changes | mean real-price gap | real-price volatility (CV) | revenue vs observed |
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
| **observed** | 21.4 | **15.7%** | **15.3%** | 0 (reference) |

Reading it:

* As you raise τ you make **fewer changes** (good) and let the real price
  **drift a little further** (bad) — a smooth trade-off. The **"knee"** — the
  point of best balance, found by normalising both axes and taking the τ closest
  to the ideal corner — is **τ\* = 6%** (`08_chart7_frontier.png`).
* An explicit penalty sweep (`Objective = Revenue − λ · changes`) picks τ = 4% at
  a light penalty, 5% at a moderate one, 7% at a heavier one — i.e. **any
  reasonable cost of repricing lands in the 4–7% band.**
* **Observed pricing is beaten on both axes at once:** hotels changed prices as
  often as τ = 1–3% would, yet let the real rate wander **twice as far** with
  **three times the volatility**. The −10% "revenue vs observed" for the
  threshold rows is a *level* effect — hotels sat above the pre-COVID real target
  during 2022–23 — and the out-of-sample test below controls for it.
* P1 (monthly indexing) looks tidy on volatility but its real-price gap is
  **17%** — it keeps adding last month's number and never closes the accumulated
  hole in an acceleration.

---

## 8 · Does it actually work? The out-of-sample test

Freeze τ\* = 6% and δ\* using **only 2018–2023 data**. Fit the seasonal factors
and the real-rate target on the training years. Then run the frozen rule on the
**2024-01 … 2025-11 window it has never seen**:

| policy | price changes | mean real-price gap | real-price volatility | revenue vs observed |
|---|---|---|---|---|
| **P0** frozen | 1 | **51%** | 25% | −31% |
| **P1** monthly CPI | 23 | 4.4% | 4.0% | +0.3% |
| **P2** τ = 6% | **12** | **6.0%** | **3.7%** | **−0.6%** |
| **P3** τ = 6% + occupancy tilt | 12 | 8.9% | 4.0% | −2.3% |
| observed (hotels) | 23 | 10.6% | 12.8% | 0 (reference) |

Across every elasticity assumption β ∈ {0, −0.25, −0.5, −1.0} the revenue column
moves by **about a percentage point at most** — the ranking does not depend on
the number we could not identify.

> **P2 at τ ≈ 6% makes roughly half as many price changes as indexing every
> month, for the same real-price control and the same revenue — and it holds the
> real rate about twice as tightly as hotels actually managed, at half the number
> of changes** (`08_chart8_backtest.png`).

Two footnotes to the story:

* **The occupancy tilt (P3) did not help.** In 2024–25 occupancy sat *below* its
  seasonal norm, so the tilt trimmed the catch-up and *added* real erosion; with
  demand inelastic there is no occupancy gain to offset it. Keep it as an
  optional lever, not a proven improvement.
* **P1 only wins here because 2024–25 was a disinflation.** In the 2022–23
  acceleration its real-price gap was ~17% (§7). The threshold rule's
  *level-restoring reset* is what protects it when inflation is rising.

---

## 9 · One rule fits every category

Give each category its *own* frontier and its *own* knee:

| category | pass-through β | mean move size | its own knee τ\* | change-count cut vs monthly indexing (out-of-sample) | real-price gap: P2 vs observed |
|---|---|---|---|---|---|
| 1-2★ | 0.84 | 6.9% | **6%** | −48% | 6.0% vs 9.3% |
| 3★ | 0.78 | 8.0% | **6%** | −48% | 6.0% vs 10.5% |
| 4★ | 1.04 | 7.6% | **6%** | −48% | 6.0% vs 10.1% |
| 5★ | 1.16 | 10.7% | **6%** | −48% | 6.0% vs 13.6% |
| Total (composite) | — | — | **6%** | −48% | 6.0% vs 9.6% |

> **The *timing* is universal — τ\* ≈ 6% for every category.** What differs is
> *how* they pass inflation through (3★ lowest, 5★ highest) and how big their
> moves are (5★ largest), not *when* to act. One τ ≈ 6% serves all; the upper
> tiers can sit at the top of the 4–7% band (`09_chart6_category.png`).

---

## 10 · Robustness

Re-run the whole pipeline under eight variations — GBA vs national CPI, room vs
bed occupancy, all four β values, drop the most extreme inflation months,
selection = 2023 only, core tiers vs including the composite:

| claim | how it holds up |
|---|---|
| **A** — the knee τ\* sits in the 4–7% band | 7 of 8 variants (τ = 7% under the national deflator) |
| **B** — the threshold rule beats observed pricing on **both** real-price stability **and** change count, out-of-sample | **8 of 8** |
| **C** — monthly indexing lags in an acceleration | ~17% real-price gap in 2022–23 (7/8); ~4.4% in the 2024–25 disinflation |
| **D** — demand inelastic / not identified | holds |
| **E** — bigger, more-upward moves; frequency effect much smaller | size & direction significant 3/3; the >1% frequency also rises (~+10 pp) but off an already ~86% base |
| **F** — the rule does not break in a demand collapse | see COVID stress below |

**COVID stress test.** Through 2020–21, total-hotel occupancy fell **62% → 27%**.
There is no market rate to model, but we can *simulate* the policies against the
real CPI path. The frozen price loses **−27%** of its real value; monthly
indexing holds ~−3%; **the τ ≈ 6% rule fires 10 times (vs 24 for indexing) and
holds the real price within ~5% of target** — it does **not** break. But it is
inflation-state-dependent only: **it has no branch that cuts the price when
occupancy craters** (see §14).

---

## 11 · The theory — why 6% is not an accident

Everything so far is empirical: τ ≈ 6% is where a fitted trade-off curve bends.
This section shows the **same number falls out of a 50-year-old model** of
pricing under inflation — and then tests that model's sharpest prediction against
the data.

### 11.1 The model — Sheshinski & Weiss (1977), Barro (1972)

Set-up (in logs, real terms; the target real price is normalised to 0):

* With the nominal price fixed, the firm's **real price `p` drifts down at the
  inflation rate**: `dp/dt = −π`.
* Being off the target real price carries a **flow loss** `L(p) = (b/2)·p²` — the
  quadratic (second-order) approximation of *any* smooth revenue-or-profit
  function near its peak; `b` is that function's curvature.
* **Each price change costs a fixed `κ`** — the "menu cost": re-tagging,
  re-listing on OTAs, staff time, customer/fairness friction.

The firm can neither hold `p` at 0 (that needs continuous repricing at infinite
cost) nor ignore it (the loss compounds). The optimal compromise is an
**(s, S) band**: let the real price erode from an upper reset point `S` down to a
lower trigger `s`, then jump the nominal price to put `p` back at `S`; repeat.
Averaging both costs over one cycle,

    C(w) = κ·π / w  +  (b / 24)·w²        band width  w = S − s

(menu cost, paid π/w times per unit time, plus the mean quadratic loss inside a
band of width `w`). Minimising over `w` gives `w* = (12·κ·π / b)^(1/3)`, and:

| quantity | formula | scales with inflation as |
|---|---|---|
| optimal band width | `w* = (12·κ·π / b)^(1/3)` | **π^(1/3)** |
| time between resets | `T* = w*/π` | π^(−2/3) |
| repricing frequency | `f* = 1/T*` | **π^(2/3)** |
| **cumulative inflation between resets** | **`τ* = w*`** | **π^(1/3)** |

The last row is the point: **the cumulative inflation a firm optimally lets build
up before repricing is exactly the band width `w*`.** "Reprice when cumulative
inflation since the last change reaches τ" — **Policy P2** — *is* the
Sheshinski–Weiss (s, S) rule, with `τ = w*`.

### 11.2 One modification, and why

In the original model the *target* real price is a monopoly optimum
`p* = c·η/(η−1)`, which needs **elastic demand** (`η > 1`) and a **marginal cost
`c`**. We have neither: no cost data, and §5 found demand **inelastic** (implied
`η ≈ 0–0.6`), so there is no interior monopoly optimum to reset to.

We therefore take the target real price **`p̄` as exogenous** — the hotel's
*competitive / positioning benchmark* (what comparable hotels charge, what the
OTA ranking rewards) — and let **`b` be the curvature of the penalty for
deviating from it** (lost bookings + customer-fairness backlash + OTA-ranking
demotion). This is the standard **reference-price / customer-market** treatment
(Rotemberg 2005; Nakamura & Steinsson 2011). The (s, S) algebra above is
**unchanged** — only the interpretation of the target and of `b` shifts.

### 11.3 Calibrating the model

Every reset in the model is exactly `w*` wide, so the **observed mean absolute
log price change identifies `w*`** directly, and `κ/b = w*³ / (12·π̄)` (in
months). Two versions:

| calibration | `w*` = | note |
|---|---|---|
| raw | mean of \|Δln P\| | an **upper bound** — inflated by ordinary seasonal moves |
| deseasonalised | mean of \|Δln P − monthly mean\| | strips calendar effects — the one to use |

Model-implied `τ* = w*`:

| category | raw τ\* | **deseasonalised τ\*** | reset interval T\* |
|---|---|---|---|
| 1-2★ | 6.9% | **4.8%** | ~0.9 mo |
| 3★ | 8.0% | **5.6%** | ~1.0 mo |
| 4★ | 7.6% | **5.2%** | ~1.0 mo |
| 5★ | 10.7% | **9.1%** | ~1.7 mo |
| **mean** | 8.3% | **6.2%** | — |

The deseasonalised mean, **6.2%**, lands **on the empirically fitted knee (6%)**
and inside the λ-penalty band (4–7%) — `11_chart10_model_vs_empirical.png`. Only
the *ratio* `κ/b` is identified (≈ 0.0002–0.0012 months), not `κ` and `b`
separately; pinning `κ` at a literature-plausible ~2% of monthly revenue implies
a loss curvature `b ≈ 15–115` — a steep penalty for off-market real pricing,
consistent with a competitive, OTA-mediated market.

### 11.4 Testing the sharp prediction — the scaling law

The calibration only used the *average* move. The model's real content is the
**exponents**: price-change **size** should have an inflation-elasticity of
**1/3**, and **frequency** an elasticity of **2/3**. Estimated three independent
ways — across inflation *deciles*, across the three *regimes*, and on *12-month
rolling windows* (HAC SE), pooled over the four star tiers:

| margin | deciles | regimes | rolling | **model** |
|---|---|---|---|---|
| **size** of the move (elasticity to inflation) | **0.361** — CI [0.19, 0.53] | **0.337** | **0.313** | **0.333** |
| **frequency** of moves (elasticity to inflation) | 0.066 | 0.075 | 0.067 | 0.667 |

> **Theoretical finding.** The **size** margin obeys the menu-cost scaling law
> almost exactly — inflation-elasticity ≈ 1/3 across every method. The
> **frequency** margin is flat (≈ 0, not 2/3). This is the *structural*
> counterpart of Finding 1: inflation is absorbed by **bigger** price changes,
> not **more frequent** ones. The frequency prediction fails for a measurement
> reason — the reported rate is a monthly mean that already moves nearly every
> month, so there is no slack on the frequency margin
> (`11_chart11_scaling_law.png`).

### 11.5 Closing the loop

Feed each category's **model-calibrated** τ\* (deseasonalised) back through the
out-of-sample simulator:

| | model-τ\* rule | empirical τ = 6% | observed |
|---|---|---|---|
| price changes | 9–12 | 12 | 23 |
| mean real-price gap | 5.8–7.5% | ~6.0% | 9–14% |

**The theory-derived and data-derived thresholds produce the same policy** — and
both dominate what hotels actually did.

### 11.6 What the model assumes (and where it is thin)

1. **Deterministic drift.** The (s, S) formula assumes a *constant* inflation
   rate. Argentine inflation moved sharply in 2023–24; the regime and
   rolling-window versions of the scaling test partly absorb this, but the point
   calibration is at the sample-mean rate.
2. **Only `κ/b` is identified**, not the menu cost `κ` and the loss curvature `b`
   separately.
3. **Raw `w*` is inflated by seasonality** — the raw τ\* is an upper bound; the
   deseasonalised calibration is the headline.
4. **Exogenous target price, aggregate data.** `p̄` is a competitive benchmark,
   not derived; and this is category-level data, so the result is a *category
   pricing policy*, not a firm-level menu-cost estimate.

---

## 12 · The recommended rule

> **Each month, add up CPI inflation since your last price change (`CUMINF`).**
>
> * **`CUMINF` below ~6%** (a 4–7% band; use the top of the band for 4–5★):
>   **hold.** No repricing review.
> * **`CUMINF` at or above ~6%:** **reset the list price** to restore the target
>   *real* rate — i.e. multiply the old price by the CPI increase since the last
>   change.
> * **Optional tilt at the reset:** occupancy running above its seasonal norm →
>   pass through a little extra (×1.00–1.05); at norm → match inflation (×1.00);
>   below norm → hold back a little (×0.95–1.00). *In this data the tilt did not
>   improve real-price control out of sample — treat it as a discretionary
>   lever.*

Backtested out-of-sample (2024-01 … 2025-11): this would have **cut the number of
price changes roughly in half versus repricing every month**, held the real room
rate within **~6% of target** (vs **~11%** for what hotels actually did), and
left revenue essentially unchanged — and it survives the full robustness matrix.

In calm periods (≲ 2%/month) the trigger fires every 2–3 months and a plain CPI
reset is enough. As inflation accelerates it approaches monthly — and that is
exactly when *resetting to the real target* (rather than adding last month's
increment) earns its keep.

---

## 13 · Can demand-based ("surge") pricing sit on top? (notebook 08 — exploratory)

The timing rule and demand pricing solve **two different problems**: P2 keeps the
real price *on* its benchmark; surge pricing moves the *benchmark* with demand.
They are separable — you can run P2 against a benchmark that shifts with demand
instead of a fixed one. Notebook 08 prototypes the conservative version of that.

**What was tested (call it P4).** Keep P2's trigger unchanged. At each reset,
multiply the real target by `1 + tilt`, where `tilt` is built from
panel-observable demand shifters (trailing occupancy vs its training seasonal
norm, travellers vs norm, an occupancy-momentum "pace" proxy, a high-season
flag), then **clamped to `[0, δ_max]`** — **upward-only** (with demand inelastic
and no evidence that data-driven discounts recover occupancy, cuts are the risky
direction) and **capped** at `δ_max ≤ 8%`. `δ_max = 0` reproduces P2 exactly.

**Result (pooled, test window 2024-01 … 2025-11, β = −0.5):**

| | price changes | mean \|real dev\| | mean occupancy | RevPAR vs observed |
|---|---|---|---|---|
| P2 τ = 6% | 12 | 6.0% | 58.1 | −0.6% |
| **P4** (upward tilt ≤ 8%) | 12 | 5.0% | 57.6 | **+0.1%** |
| observed | 23 | 10.6% | 57.3 | 0 (ref) |

* **It does not undo the stabilisation.** Same change count, real-price control
  unchanged (slightly tighter here — 2023–24 demand mostly ran *above* norm, so
  tilting up moved toward the market).
* **The revenue gain is small and entirely a function of the elasticity we
  cannot identify.** `RevPAR(P4) − RevPAR(P2)` is a straight line in β
  (`08_tilt_payoff.png`): at β ≈ 0 (inelastic) it is a small positive gain (order
  of **+1 to +3%**, largest for the upper tiers); at β = −1 it is **exactly
  zero**. There is no way, from this data, to tell "captured real demand" from
  "just charged more" (§5).
* **Hotels already surge harder than a capped tilt.** In peak-season months
  (Jan–Feb, Jul) P4's RevPAR sits slightly *below* observed — real hotels raised
  prices by more than 8% into those windows.

**Verdict.** Architecturally clean, downside-capped, and it does not break P2 —
but a **positioning lever, not a demonstrated improvement**. The panel only
supports three thin demand signals; a genuine surge layer needs firm-level
revenue-management data (pickup/pace curves, competitor rates, an event
calendar), none of which is in EHOBA/INDEC. **The recommendation in §12 stands
as the rule; any demand tilt is discretionary, applied only at resets, capped
and upward-only.**

---

## 14 · What this does **not** do

1. **Aggregate data.** City × category × month — this is a *category-level*
   pricing policy, not individual-hotel yield management.
2. **No official CPI before 2016-12.** The 2008–2017 stretch is nominal-only
   context; the working sample is ≈ 71 clean months per category — small for
   fine regime splits (only the "low ≈ 0 vs high > 0" pass-through pattern is
   interpretable, not the mid-regime point estimate).
3. **The demand elasticity is not causally identified.** Results are reported
   across an assumed β grid and are near-invariant to it, but a genuine causal
   number would need a supply/cost instrument this data does not provide.
4. **No marginal-cost data.** This is a revenue / real-price **trade-off** study,
   not profit maximisation. The constant-elasticity revenue "optimum" is
   degenerate and is not used. In the menu-cost calibration (§11.3) only the
   *ratio* κ/b (fixed cost ÷ loss curvature, ≈ 0.0002–0.0012 months) is
   identified, not κ and b separately; a literature-plausible menu cost of ~2% of
   monthly revenue implies a loss curvature b ≈ 15–115 — a steep penalty for
   off-market real pricing, consistent with an OTA-mediated market.
5. **Repricing *frequency* is only weakly observable** — the rate is a monthly
   mean. The size, direction, pass-through and threshold results do not depend
   on the frequency measure.
6. **COVID 2020–21.** Star-tier rates are missing for 22 of 24 months, so no
   price-based estimate can include it. The rule is *simulated* through the
   collapse and holds the real price, but it is **validated for inflation
   regimes, not demand-collapse regimes**, and has **no price-cut branch** for a
   demand shock (a hotel might still want a discretionary promotional cut for
   cash-flow reasons the model does not capture; with inelastic demand a
   mechanical cut would not recover occupancy).
7. **The composite "Total"** is a capacity-weighted construction with quarterly
   weights, not an official series.
8. **The repricing penalty `λ`** is an operational dial, not a measured cost. The
   frontier and the full λ sweep are the defensible objects; τ ≈ 6% is where any
   moderate penalty points.
9. **Hotel prices are ~1% of the CPI** used as deflator — immaterial, and a
   different price concept (mean ADR vs fixed-basket). The "Restaurants & hotels"
   CPI sub-index, which mechanically contains hotel prices, was **removed** from
   the instrument set.

---

## 15 · Reproduce it

```bash
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
python -m ipykernel install --user --name argentina-hotels --display-name "Python (argentina-hotels)"
# run from the repository root, in order:
jupyter nbconvert --to notebook --execute --inplace \
    --ExecutePreprocessor.kernel_name=argentina-hotels [0-9]*.ipynb        # 01 -> 08, ~30 s
```

* `data/raw/**` is never modified. `data/processed/**` is git-ignored and fully
  regenerated by notebook 01.
* Every cleaning / modelling decision is appended to
  `data/processed/cleaning_audit_log.csv` (idempotent per notebook).
* Core logic is in `src/` (`config`, `common`, `loaders`, `policies`,
  `pricing_eval`), not buried in notebooks. `policies.py` and `pricing_eval.py`
  are pure and independently testable.

### Notebook map (run in order from the repo root)

| notebook | what it does | key outputs |
|---|---|---|
| `01_build_dataset` | load · clean · merge the six spreadsheets into one panel | `data/processed/*.parquet`, `data_dictionary.csv`, INDEC cross-check |
| `02_data_overview` | orientation / EDA — coverage & gaps, the series, the inflation environment, **annual-inflation table**, **Argentina vs India**, **currency-erosion stat**, seasonality, category comparison | `annual_inflation.csv`, `currency_erosion.csv`, `02_*.png` |
| `03_inflation_and_repricing` | the descriptive story + Finding 1 + pass-through | Charts 1–4, erosion clock; Tables 1–3; `regime_tests.csv`, `price_adjustment_by_category.csv` |
| `04_demand_and_identification` | Finding 2 — elasticity and why it isn't identified | Table 4, `identification_summary.csv`, Chart 5 |
| `05_policies_and_backtest` | the policy engine, the frontier, the out-of-sample backtest, the COVID stress test | Tables 5–6, `pareto_frontier.csv`, `lambda_sweep.csv`, `covid_stress.csv`, Charts 7–8 |
| `06_synthesis_menucost_and_rule` | one rule per category + the Sheshinski–Weiss (s, S) foundation and its scaling-law test | Table 7 & Chart 6; Tables 8–10, Charts 10–11; decision-tree Chart 9 |
| `07_robustness` | eight variants + the COVID-inclusion note | `robustness_matrix.csv`, `robustness_regime.csv` |
| `08_demand_tilt_exploration` | **exploratory (§13)** — can an upward-only demand tilt sit on top of P2? | `demand_tilt_backtest.csv`, `08_tilt_payoff.png` |

### Tables (`outputs/tables/`)

`table1_descriptives` · `table2_regime_behaviour` · `table3_passthrough` ·
`table4_elasticity` · `table5_threshold_sim` · `table6_out_of_sample` ·
`table7_category_policy` · `table8_menu_cost_calibration` ·
`table9_scaling_law` · `table10_model_tau_backtest` — plus
`annual_inflation`, `currency_erosion`, `price_adjustment_by_category`,
`regime_tests`, `identification_summary`, `pareto_frontier`, `lambda_sweep`,
`robustness_matrix`, `robustness_regime`, `coverage_by_category`,
`data_dictionary`, `missing_value_map`, `outlier_register`,
`table_policy_example`, `demand_tilt_backtest` (§13, exploratory).

### Charts (`outputs/figures/`)

**The story, in order:**

1. `04_chart1_moving_target` — CPI vs hotel rates, 2008–2026
2. `04_chart2_nominal_vs_real` — nominal vs real rates
3. `05_chart3_magnitude_by_regime` — price-change size by inflation regime
4. `05_chart4_frequency_by_regime` — frequency vs upward-share by regime
5. `06_chart5_occupancy_tradeoff` — occupancy vs real rate, controls partialled out
6. `09_chart6_category` — pass-through / knee-τ / repricing-cut by category
7. `08_chart7_frontier` — the repricing frontier and its knee
8. `08_chart8_backtest` — the threshold rule vs mechanical indexing, test window
9. `09_chart9_decision_tree` — the recommended rule
10. `11_chart10_model_vs_empirical` — menu-cost model τ\* vs the fitted knee
11. `11_chart11_scaling_law` — price-change size ∝ π^(1/3); frequency does not

**Orientation (notebook 02):** `02_coverage_heatmap`, `02_sample_map`,
`02_nominal_rates_longrun`, `02_inflation_environment`, `02_real_rates`,
`02_occupancy`, `02_price_change_dist`, `02_passthrough_scatter`,
`02_capacity`, `02_correlations`, `02_argentina_vs_india_inflation`,
`02_currency_erosion`.

**Exploratory (notebook 08, §13):** `08_tilt_payoff` — surge-tilt payoff vs the
unidentified elasticity.

**Diagnostics:** `03_indec_crosscheck`, `03_composite_check`, `04_erosion_clock`,
`04_sample_map`, `05_cumulative_passthrough`, `06_identification`,
`07_revenue_curves`, `07_policy_paths_4star`, `08_frontier_robustness`.
