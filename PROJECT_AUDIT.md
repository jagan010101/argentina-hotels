# PROJECT AUDIT — reframing to "When should a hotel change its price?"

**Date:** 2026-09-06
**Purpose:** inventory the existing project, grade its results, and lay out the
changes needed to turn it into *"Inflation-Aware Dynamic Repricing Policy for
Buenos Aires Hotels."* **No code has been changed yet.**

Bottom line: **~70% of the existing pipeline is reusable.** The data layer
(notebooks 01–03), the descriptive inflation story, the price-adjustment /
pass-through work, and the backtest *engine* all carry over. What must change is
the **framing, the sample windows, the threshold grid, the temporal split, the
policy set (add Policy 0), the objective (Pareto frontier / λ, not tracking
RMSE), the IV (currently not credible — downgrade), and the presentation set.**

---

## 1 · Existing data

| Raw file (`data/raw/`, untouched, read-only) | Content | Freq | Span |
|---|---|---|---|
| `Ehoba_03a_0811.xlsx` | avg room rate by category, **nominal pesos** — the price variable | monthly | 2008-01 … 2026-05 |
| `Ehoba_02a_0811.xlsx` | room-occupancy rate % | monthly | 2008-01 … 2026-05 |
| `Ehoba_04_0811.xlsx` | bed-occupancy rate % | monthly | 2008-01 … 2026-05 |
| `Ehoba_VA_0811.xlsx` | travellers hosted (hotel sector only) | monthly | 2013-01 … 2026-05 |
| `Ehoba_1_ano.xlsx` | establishments, available room-nights, bed-nights | **quarterly** | 2008 … 2026-03 |
| `sh_ipc_08_26.xls` | INDEC IPC, base **dic-2016 = 100**, GBA + national + divisions | monthly | GBA 2016-04 … / nat. 2016-12 … 2026-07 |

**Processed (reproducible):** `data/processed/01_loaded/*.parquet` (6 tidy raw
tables), `02_panel_long.parquet`, `02_capacity_quarterly.parquet`,
`02_cpi_monthly.parquet`, `03_analysis_panel.parquet` (61 cols, the modelling
table), `cleaning_audit_log.csv` (every transformation, idempotent per notebook).

**Category coverage (from `coverage_by_category.csv`), analysis window:**

| Category | rate series? | clean months (ex-COVID) |
|---|---|---|
| 1–2★, 3★, 4★, 5★ | ✔ | 78 (90 incl. 2022) |
| Apart, Boutique | ✔ | 78 |
| **Total (hoteleros)** | **✗ — no rate column in the source** | occupancy only |
| Hostel | ✔ rate, ✗ room-occ (never published) | 78 |

> **Constraint for the new brief:** it asks for a "Total" category. The rate
> file has **no Total column**. A capacity-weighted composite rate can be built
> (Σ rate_c·room-nights_c / Σ room-nights_c) but only at quarterly capacity
> snapshots — it will be labelled a derived composite, not an official series.

**CPI quality:** our GBA MoM recomputed from levels matches INDEC's published
MoM to **max 0.05 pp** over 114 months; GBA bridge splices onto the national
sheet with **0.00** index-point discontinuity at 2016-12. Solid.

---

## 2 · Existing models / notebooks

| NB | What it does | Status for reframe |
|---|---|---|
| **01 load** | structural parsers for the 5 EHOBA sheets + INDEC `.xls` → tidy long parquet, no cleaning | **keep as-is** |
| **02 clean** | numeric coercion, missing-reason classification, outlier register, CPI deflator build (`cpi_gba`, `cpi_nac`, `cpi_resthot_*`) | **keep as-is** |
| **03 merge** | wide panel, inflation transforms (MoM/YoY/cum 3-6-12m), real rates, seasonal dummies, COVID flags, capacity as-of, revenue proxy, `in_window` | **light edit** — redefine the analysis sample (below), add composite Total, add `CUMINF_t` since-last-reprice helper |
| **04 descriptive** | Plots 1–9, Table 1, COVID shading | **reframe** → Part 1 (long-run context 2008–26) + hand the rest to 05/07 |
| **05 price adj.** | Δln P distribution, freq at thresholds, regression pass-through (Table 2), inflation-regime comparison, Chart B | **keep core, extend** → Part 2 + Part 7; add formal tests of magnitude/asymmetry by regime; **drop the regime-interacted β** (noisy, see §4) |
| **06 elasticity** | ln(occ) on ln(realRate) — log-log / lag / levels / logit (Table 3), added-variable plots, endogeneity text | **keep, reframe** → Part 3; sign is positive → already correctly framed as "not a demand curve" |
| **06b identification** | 4 attempts at causal β: YoY diff, relative-price panel + FE, **2SLS**, predetermined lags | **rebuild the IV** (see §4); keep relative-price panel as the headline; likely **relabel elasticity associational** |
| **07 dynamic pricing** | constant-elasticity demand, shows revenue optimum is degenerate, policy paths A/B/C/D, Charts D/E | **keep the degeneracy demo**, reframe → Part 4; add **Policy 0 (frozen nominal)**; align policy names to brief |
| **08 backtest** | walk-forward rule engine, train ≤2019 / val 2022 / test 2023-26, Tables 4/5, threshold sweep, Chart F, robustness | **keep the engine, change everything around it** — new temporal split, new τ grid, Pareto/λ objective, per-category τ*, Policy 0 |
| **09 results** | assembles Tables 1–5 + Charts A–F, Part-14 answers, recommended rule | **rewrite** for the 9-chart / 6-table presentation spec + decision-tree chart |

**Reusable infrastructure:** `src/config.py` (paths, category maps, COVID dates,
plot DPI), `src/common.py` (audit log, Spanish-month / category parsers,
`to_number`). The dedicated Jupyter kernel `argentina-hotels` (Python 3.12,
pinned deps in `requirements.txt`) works; full chain runs in ~90 s.

**Gap vs the brief's coding requirement** ("core logic in reusable modules, not
buried in notebooks"): the rule engine and policy evaluation currently live
**inside notebook 08**. These must be extracted to `src/policies.py` /
`src/pricing_eval.py`.

---

## 3 · Existing findings (with a strength grade)

Grades: **A** = descriptive/robust, **B** = regression-significant but sample-
limited, **C** = weak / not significant / should be dropped or heavily caveated.

| # | Finding | Grade | Notes |
|---|---|---|---|
| F1 | Real hotel rates swung from ~80 to ~200 (index 2017-01 = 100); real-rate CV **9–20 %** by tier; ~0 % real-rate trend over 2017–26 | **A** | pure description; becomes Charts 1–2. "Moving target" holds. |
| F2 | Reported average rate changes **essentially every month in every inflation regime** (freq ≈ 1) | **A**, but partly an artifact | these are category *averages*, not posted prices — freq ≈ 1 by construction. State this explicitly; the "not more frequent" claim is weak *because it can't be otherwise* in this data. |
| F3 | Across CPI-MoM terciles: mean \|Δln rate\| **6.3 % → 5.7 % → 9.6 %**; share of moves that are **up 64 % → 71 % → 83 %**; \|move\|>1 % share 88 % → 88 % → 95 % | **B** | large, monotone in the high tercile; needs a formal test (regress \|Δln P\| and 1[up] on regime dummies with HAC/cluster SE). This is the finding the new brief wants elevated. |
| F4 | Contemporaneous pass-through β (Δln P on Δln CPI, HAC, COVID-excl): **1–2★ 0.85, 3★ 0.75, 4★ 1.09, 5★ 1.25, Apart 0.89, Boutique 1.16**; all t = 4.5–6.9 | **B** | significant, but R² 0.11–0.33 and identified almost entirely off 2–3 devaluation episodes — `ex_extreme` sample makes β explode/collapse. Report as short-run pass-through in a high-inflation sample. |
| F5 | Cumulative pass-through (0–3 lags) ≈ 0.6–0.9, **below** contemporaneous for most tiers | **B/C** | implies overshoot-then-retrace; plausible but imprecise. Keep, don't over-interpret. |
| F6 | Naive occupancy elasticity is **positive or zero** (1–2★ +1.0 t 5.7; 3★ +0.32; 4★/5★/Apart/Boutique ≈ 0) | **A** (as evidence of endogeneity) | the wrong sign *is* the point — observational data cannot trace a demand curve. |
| F7 | Relative-price panel (tier vs cross-tier mean, month + category FE): β = **+0.07, t = 1.13, within-R² 0.005** | **A** | cleanest test — city-wide demand shocks fully absorbed. Says: within a month, a tier that raises price relative to peers does **not** lose relative occupancy → **demand is very inelastic** (or relative price tracks quality). This should be the headline demand statement. |
| F8 | 2SLS with cost instruments: 4★ β = **−0.26** (t −2.7, F 140), Apart **−0.60** (t −2.6, F 20), 5★/Boutique ≈ 0, **3★/1–2★ not identified** (F 2.9 / 6.8) | **C — not credible, see §4** | one instrument (`rel_resthot`) violates the exclusion restriction. Must be rebuilt or dropped. |
| F9 | Regime-interacted pass-through β: low −0.38 / mid **+2.23** / high +0.85, **interaction p = 0.27, 0.39** | **C — drop** | mid = 2.23 is not economically sensible; interactions insignificant; tiny effective n. Remove from `passthrough_by_regime.csv`; keep only the descriptive regime columns (F3). |
| F10 | Constant-elasticity revenue optimum is **degenerate** without marginal cost — optimal pass-through pins to the price-grid boundary for every \|β\| ≠ 1 | **A** (a correct modelling observation) | the new brief explicitly endorses this. Keep; it motivates the Pareto-frontier framing. |
| F11 | Backtest: any inflation-indexation rule cuts real-price volatility from **~13 %** (observed) to **~5 %** of target; a cumulative-inflation trigger at **X ≈ 5 %** matches monthly repricing's stability with **~35 % fewer price changes** (24 vs 37 over 41 months); X > ~12 % lets worst-case erosion pass −20 % | **B** | engine is sound and look-ahead-free. But τ was chosen by **tracking RMSE only** (ignores the frequency cost), the grid is coarse below 5 %, the split is not the brief's, and there's no Policy 0. Re-run needed. |
| F12 | At matched real-price level, threshold / threshold+occupancy rules are within **1–2 pp RevPAR** of monthly CPI reset; **+3–13 % RevPAR vs observed** for 4★/5★/Boutique, mostly from not letting real price drift | **B** | depends on assumed β (sensitivity shown for −0.1/−0.5/−1.0). Keep with the β caveat front and centre. |

---

## 4 · Methodological weaknesses (things to fix)

1. **The IV in 06b is not credible (F8).** Instruments are
   `rel_resthot` = log(CPI "Restaurants & hotels" ÷ headline) and
   `rel_vivienda_l1` = lagged log(CPI "Housing/utilities" ÷ headline).
   - **Exclusion restriction fails for `rel_resthot`:** the "Restaurants and
     hotels" CPI division *mechanically contains hotel room prices* and reflects
     tourism-sector demand — it is correlated with the endogenous regressor
     through exactly the channel we are trying to instrument out, and plausibly
     with occupancy directly. It must be dropped.
   - With `rel_vivienda_l1` alone the first stage will likely weaken
     substantially. **Plan:** re-run 2SLS with (a) `rel_vivienda` only, (b) add
     a lagged national-headline-inflation surprise and/or a lagged
     nominal-FX-depreciation term as cost-push instruments; report first-stage
     F, Sargan/Hansen over-ID p, and Anderson–Rubin CIs. If the first stage is
     weak or over-ID rejects, **state plainly that occupancy elasticity is
     associational, not causal**, and rely on F7 (relative-price panel ≈ 0) as
     the defensible statement: *demand is inelastic; the point estimate is not
     identified.*
   - Do **not** carry −0.26 / −0.60 into the policy sims as if causal. Use a
     **β scenario grid** (e.g. 0, −0.25, −0.5, −1.0) and report policy outcomes
     as a function of assumed β (already the structure in 07/08 — keep it).

2. **Regime pass-through β (F9) is noise.** Drop it. Keep the *descriptive*
   regime table (magnitude, asymmetry, real price, occupancy) and add a formal
   test of the magnitude/asymmetry differences.

3. **Threshold τ was selected on the wrong objective.** Validation minimised
   real-price **tracking RMSE**, which monotonically prefers the smallest τ
   (tightest tracking) and ignores the repricing-frequency cost — the whole
   point of the project. **Fix:** evaluate every τ on the **Pareto frontier
   (repricing events vs cumulative revenue / real-price stability)** and on an
   explicit **Objective = Revenue − λ·N_reprice** for a stated range of λ (λ
   *not* claimed as a monetary cost). Report the frontier; call a τ "preferred"
   only if it is Pareto-efficient and robust.

4. **Threshold grid too coarse at the low end.** Currently
   {2,3,5,8,10,12,15,20,25}%. Brief wants **{1,2,3,4,5,6,7,8,10}%**. Re-grid.

5. **Sample windows don't match the brief.** Current: one window 2016-12→2026-05,
   2020-03→2021-12 excluded, 2022 flagged "recovery" and partly dropped.
   Brief wants **main = 2018-01…2019-12 + 2022-01…2026-05**, **COVID
   2020–2021 handled separately**, 2008–2017 for long-run context only.
   → redefine `analysis_sample` in config/03; 2018–19 is inside GBA-CPI
   coverage so no new data problem. 2022's 1–2★ rate gap remains a genuine
   limitation to flag.

6. **Temporal split doesn't match the brief.** Current train ≤2019 / val 2022 /
   test 2023-26. Brief wants **train 2018–19 + 2022 / validation 2023 / test
   2024-05·2026**. Adopt it; keep an expanding-window variant as robustness.

7. **Policy 0 (frozen nominal price) is missing.** It is the reference that
   *quantifies real-price erosion under no action* — add it explicitly.

8. **"No profit maximisation" caveat is implicit, not prominent.** F10/F12
   already avoid the claim, but the write-up should state up front: no marginal
   cost data → we compare *policies* and map the *trade-off*, we do not find "the
   optimal price".

9. **Core logic lives in notebooks.** Extract the rule engine and evaluation
   into `src/policies.py` and `src/pricing_eval.py` (brief requirement).

10. **`freq ≈ 1` framing.** Because `average_rate` is a category mean, a menu-cost
    "frequency of repricing" is not really observable in this data. The honest
    version of the key hypothesis test is: *inflation raises the **magnitude**
    and **upward asymmetry** of monthly rate changes and the **pass-through
    coefficient**, with no room to raise an already-saturated change frequency.*
    Keep the punch-line only if the magnitude/asymmetry tests (item 2) hold.

11. **Target real-rate anchor = 2019 mean.** 2019 was itself an Argentine crisis
    year. Keep as base case but add robustness anchors (e.g. 2018 mean, full
    pre-COVID mean, rolling 24-month) — item is small but cheap.

---

## 5 · Proposed modifications, mapped to the new brief

| New part | Action | Reuses | New |
|---|---|---|---|
| **1 — Descriptive inflation story** | long-run 2008–26 nominal vs CPI vs real chart; then restrict main analysis to 2018–19 + 2022–26 | 04 plots 1–2, 09 Chart A | redefine `analysis_sample`; Chart 1, Chart 2 |
| **2 — How hotels reprice** | freq / magnitude / +/− asymmetry / vs-CPI / pass-through (contemp + short lag) per category | 05 (most of it), `table2/3` | formal magnitude & asymmetry tests; Table 2, Table 3 |
| **Key hypothesis** | test "high inflation → more frequent repricing" vs "→ larger, more asymmetric, higher pass-through" | 05 regime block | HAC/cluster regressions of \|Δln P\|, 1[up], β on regime; keep the punch-line only if supported |
| **3 — Demand / occupancy** | ln(occ) ~ ln(realP) + infl + season + trend, per category; log / pp / fractional-logit; lagged price; **endogeneity section**; rebuilt IV | 06, 06b (relative-price panel) | drop `rel_resthot`; add FX / headline-surprise instruments; Sargan, AR CIs; relabel associational if weak; Table 4 |
| **4 — Candidate policies** | Policy 0 frozen · 1 monthly CPI index · 2 cumulative-τ threshold · 3 τ + occupancy tilt (tilt validated from data, interpretable) | 07 engine, 08 rule engine | **add Policy 0**; move engine to `src/policies.py`; occupancy tilt tied to regime evidence |
| **5 — Threshold optimisation** | simulate τ ∈ {1…8,10}% historically; table (events, real-P deviation, occ, revenue, revenue vol); **Pareto frontier** freq-vs-revenue and τ-vs-stability; per-category τ* | 08 sweep | new grid; Pareto logic in `src/pricing_eval.py`; Table 5; Charts 7 & 8 |
| **6 — Backtesting** | train 2018–19 + 2022 / val 2023 / test 2024–2026-05; no look-ahead (info ≤ t−1, INDEC release lag); COVID as separate robustness | 08 walk-forward | new split; expanding-window variant; Table 6 |
| **7 — Regime analysis** | low / mid / high inflation (terciles); freq, magnitude, +share, pass-through, occ, real price | 05 regime table (minus F9) | formal tests; Table 2; Charts 3 & 4 |
| **8 — Category heterogeneity** | per-category: pass-through, freq, magnitude, elasticity, **efficient τ**, revenue impact; test "does the optimal policy differ by category?" | 06/08 per-category runs | per-category τ* frontier; Chart 6 |
| **9 — Robustness** | GBA vs national CPI; ex-COVID; τ grid; elasticity specs; nominal vs real; room vs bed occ; splits; lag structures; ex-extreme-inflation; category set | scattered across 03/06/08 `*_robustness.csv` | one consolidated robustness matrix notebook/section |
| **10 — Managerial output** | IF cum-inflation < τ → hold; ≥ τ → trigger review; then occupancy-conditioned adjustment (high → fuller pass-through, weak → partial); τ and coefficients from the analysis | 09 recommendation block | **decision-tree Chart 9**; final one-pager |
| **Presentation** | Charts 1–9 and Tables 1–6 exactly as specified | existing Charts A–F remap to 1,2,3,4,5,8 | Chart 6 (category), Chart 7 (frontier), Chart 9 (decision tree); Table renumbering |

---

## 6 · Files that will be changed

**Changed**
- `src/config.py` — `ANALYSIS_SAMPLE` (2018-19 + 2022-26), `LONGRUN_START=2008`,
  `THRESHOLD_GRID=[.01….08,.10]`, `TRAIN/VAL/TEST` split, regime quantiles,
  `LAMBDA_GRID`, composite-Total switch.
- `notebooks/03_merge_data.ipynb` — add composite Total rate (capacity-weighted,
  quarterly), `analysis_sample` flag, `months_since_reprice` / `CUMINF` helpers.
- `notebooks/04` → `04_descriptive_inflation_story.ipynb` (Part 1, trimmed).
- `notebooks/05` → `05_repricing_behaviour.ipynb` (Parts 2 + 7; add formal tests;
  remove regime-interacted β).
- `notebooks/06` + `06b` → merge into `06_demand_and_identification.ipynb`
  (Part 3; rebuilt IV; associational relabel).
- `notebooks/07` → `07_pricing_policies.ipynb` (Part 4; + Policy 0).
- `notebooks/08` → `08_threshold_optimisation_backtest.ipynb` (Parts 5 + 6; new
  split, new grid, Pareto/λ, per-category τ*).
- `notebooks/09` → `09_results_and_policy.ipynb` (Parts 8 + 10; Charts 6/7/9;
  Tables renumbered).
- `README.md`, `FINDINGS.md` — rewrite for the new framing.
- `outputs/tables/*` — renumber to Tables 1–6; drop `passthrough_by_regime`'s β
  column.
- `outputs/figures/*` — regenerate as Charts 1–9 (+ diagnostics).

**Added**
- `src/policies.py` — repricing-policy engine (pure functions: given CPI path,
  occupancy path, params → nominal price path; strict t−1 information set).
- `src/pricing_eval.py` — policy metrics, Pareto frontier, `Objective = Rev − λ·N`.
- `notebooks/10_robustness.ipynb` — consolidated Part 9 matrix.
- `PROJECT_AUDIT.md` — this file.

**Unchanged**
- `data/raw/**` (never touched), `notebooks/01`, `notebooks/02`, `src/common.py`,
  `requirements.txt`, the `argentina-hotels` kernel.

**Retired / merged**
- `notebooks/06b` (folded into 06), the standalone "matched real price" framing
  in 08 (kept as a secondary view; Pareto frontier becomes primary),
  `07_revenue_curves` stays as an appendix figure (degeneracy demo).

---

## 7 · What I will NOT do

- Rebuild 01/02 or re-audit the raw files — they are correct and the brief says
  reuse them.
- Claim a profit- or revenue-maximising price.
- Carry the 2SLS elasticity into the policy sims as causal.
- Declare τ = 5 % optimal by inheritance — it will be re-derived on the frontier
  with the new grid, and replaced if another τ dominates.
- Pool COVID (2020–21) with normal periods.

---

**Awaiting your go-ahead to start on §5 / §6.** If you want a different temporal
split, threshold grid, λ range, or a specific stance on the composite "Total"
category, say so now and I'll fold it in before touching code.
