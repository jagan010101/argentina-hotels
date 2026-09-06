# Findings — Dynamic Pricing Under Inflation, Buenos Aires Hotels

Analysis window **2016-12 → 2026-05** (official CPI coverage). Deflator: IPC
Región GBA (national as robustness), base dic-2016 = 100. Revenue, not profit
(no cost data). Categories: 1–2★, 3★, 4★, 5★, Apart, Boutique. COVID
(2020-03 → 2021-12 hole, 2022 degraded) flagged and excluded from fitting.

Full derivation in `notebooks/`; every number below is reproduced by
`09_results_and_recommendation.ipynb` from the saved tables.

---

## The nine questions (Part 14)

**1 · Does higher inflation make hotels adjust prices more frequently?**
No — on the reported *average* rate, prices move essentially every month in every
inflation regime. What changes is **size and direction**: top inflation tercile
(CPI ≈ 8.8 %/mo) → mean |monthly rate change| **9.6 %** and **83 %** of moves up,
vs **6.3 %** and **64 %** in the low tercile (CPI ≈ 1.8 %/mo). Bigger and more
one-directional, not more often. `table1`, `passthrough_by_regime`.

**2 · Do hotel rates keep up with inflation?** On average yes, in bursts. Real
rates have essentially **zero trend** over the window (real-rate CAGR −1.9 % …
+1.8 % by tier), but the rate beats CPI in only **40–54 %** of months. Catch-up
is lumpy — concentrated around devaluation episodes — with real erosion in
between (Chart B).

**3 · Which categories pass inflation through fastest?** Upper tiers.
Contemporaneous pass-through β (Δln rate on Δln CPI, COVID-excluded, HAC SE):

| 1–2★ | 3★ | 4★ | 5★ | Apart | Boutique |
|---|---|---|---|---|---|
| 0.85 | **0.75** | 1.09 | **1.25** | 0.89 | 1.16 |

5★ / boutique / 4★ pass through fully or slightly over; **3★ is the laggard**.
Identification comes almost entirely from the high-inflation episodes — remove
them and β is not estimable (`table2`, `ex_extreme` sample).

**4 · How sensitive is occupancy to real room rates?** Weakly — demand is
**inelastic**. The naive regression slope is *positive* (endogeneity: hotels
raise real prices into strong demand; visible in the added-variable plots).
Strategies that break that:

| Strategy | β | note |
|---|---|---|
| Relative-price panel, month + category FE | **+0.07 (ns)** | within-month, cross-tier — no trade-off |
| 2SLS, operating-cost instruments (strong 1st stage) | 4★ **−0.26**, Apart **−0.60**, 5★ ≈ −0.07, Boutique ≈ 0 | F = 20–207 |

Best estimates sit in **[0, −0.6]**. 1–2★ and 3★ could not be identified (weak
instruments). `table3`, `identification_summary`.

**5 · Does the demand response differ by category?** Within the inelastic band,
Apart-hotels look most price-sensitive (≈ −0.6), 5★ / boutique least (≈ 0). CIs
overlap — treat as "all fairly inelastic".

**6 · Does full pass-through maximise revenue?** The question is ill-posed here.
With inelastic demand and no marginal-cost data, `RevPAR(P) = P₀Q₀(P/P₀)^{1+β}`
is monotone in P, so the revenue-"optimal" pass-through pins to whatever price
ceiling is imposed (`07` §1; the k* sweep is a step function at the grid edge).
We therefore optimise **real-price tracking**, not an interior point.

**7 · Is partial pass-through better?** No. Any fixed k < 1 lets the real price
compound-erode in a sustained high-inflation regime. The validation-selected
k = 1.4 (fit on 2022) **over-shoots badly out-of-sample** — a fixed partial
coefficient does not travel across inflation regimes (Chart F).

**8 · How does the optimal policy change between high- and low-inflation
periods?** In low inflation, monthly repricing is cheap and a plain CPI reset is
fine. As inflation accelerates, a **cumulative-inflation trigger** — reprice when
CPI has risen ≥ ~5 % since the last change — holds the real price about as tightly
as monthly repricing (real-price CV **≈ 5 %** vs **≈ 13 %** for what hotels
actually did) with **~35 % fewer price changes**. Push the trigger past ~12 % and
worst-case real erosion jumps beyond −20 % (`08` repricing trade-off:
X = 5 % → CV 5.2 %, 24 changes; X = 25 % → CV 9.1 %, 9 changes, erosion −19 %).

**9 · How much can a dynamic policy add over mechanical indexing?** On revenue,
little. At a matched real-price level and β ≈ −0.5, the threshold rule and the
threshold-plus-occupancy-tilt rule are within **1–2 pp of RevPAR** of a plain
monthly CPI reset. The gain over *observed* pricing is **+3 to +13 % RevPAR** for
4★ / 5★ / boutique — and that is mostly from **not letting the real price drift**,
not from clever dynamics (`table5`).

---

## Recommended pricing rule (thresholds estimated, not assumed)

> **1. Anchor.** Set a target *real* rate from your pre-shock competitive
> position (here: 2019 average real rate per category).
>
> **2. Trigger.** Re-index the list price to CPI whenever cumulative CPI
> inflation since your last change exceeds **≈ 5 %**. In practice that is roughly
> monthly when inflation runs > 5 %/mo, and every 2–3 months around 2 %/mo.
>
> **3. Tilt.** At each re-index, adjust **±3–6 %** for whether trailing-quarter
> occupancy is running above or below its seasonal norm.
>
> **4. Never** run a fixed partial pass-through below 1 in a high-inflation
> regime — it guarantees real-price erosion.
>
> **5. Segment.** 4–5★ and boutique can pass through fully or slightly over; 3★
> is the segment that historically lagged and lost the most real value — it has
> the most to gain from disciplined indexing.

Information rule for backtesting: month-*t* price uses CPI and occupancy through
*t − 1* only (INDEC releases month-*t* CPI in mid-month *t + 1*).

---

## Limitations

- No official CPI before 2016-12 → ≈ 78 clean months per category after removing
  COVID. Small for regime splits; regime pass-through differences are **not
  statistically significant** (interaction p = 0.27, 0.39).
- Elasticity is not cleanly identified for 1–2★ and 3★; the 2SLS exclusion
  restriction (operating-cost CPI divisions affect occupancy only through price)
  is plausible but untestable with one instrument set.
- No marginal-cost data → revenue optimisation only, and the revenue optimum is
  degenerate. Profit-optimal pricing (`P* = C·β/(β+1)`) needs a cost series.
- Capacity is quarterly; `revenue_proxy` / RevPAR mix monthly occupancy with
  quarterly-anchored capacity and are labelled proxies.
- `average_rate` is a category mean, not a posted price — "adjustment frequency"
  is uninformative here (≈ 1 in every regime).
- COVID (2020-03 → 2021-12) is a genuine data hole; 2022 is partial (1–2★
  missing). Results are conditioned on excluding these.
