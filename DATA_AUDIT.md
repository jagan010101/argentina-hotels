# Data Audit Report — Dynamic Pricing Under Inflation (Buenos Aires Hotels)

**Date:** 2026-09-06 (updated 2026-09-06 — CPI files added by user, see §9–§10)
**Scope:** Part 1 (Data Audit). No cleaning, merging, or modeling has been performed.
Raw hotel files have been read **read-only**; nothing in `data/` has been modified except that the
user-pasted CPI workbook was moved into `data/` and four irrelevant pasted files were deleted (§9).

---

## 0. Headline findings

| # | Finding | Consequence |
|---|---------|-------------|
| 1 | **CPI now supplied** as `data/sh_ipc_08_26.xls` (INDEC official IPC, base Dec-2016=100). It covers **2016-12 → 2026-07** (Total nacional) and **2016-04 → 2026-07** (Región GBA via the bridge sheet). **No 2008–2016 CPI** exists in it. | **Decision locked (§10): analysis window = 2016-12 → 2026-05.** Pre-2016 hotel data retained for descriptive nominal context only. Parts 3–14 are unblocked. |
| 2 | **The critical average-rate / price file IS present** — it is `Ehoba_03a_0811.xlsx`, not a separately-named file. Its sheet title is *"Tarifa promedio por categoría hotelera. Ciudad de Buenos Aires. Enero 2008 / Mayo 2026 (pesos)"* — exactly the dataset you described as file #5. | No action needed; price data is available (with caveats below). |
| 3 | The price file has **no "Total" column** — only 8 individual categories. A portfolio/"Total hotels" average rate must be built by weighting, or that category dropped. | Design decision needed (Part 2). |
| 4 | All monthly series share a **COVID structural break**: category-level detail is missing **2020-03 → 2021-12** (rate file fully blank; occupancy files carry only the two "Total" columns), and **1–2 star is missing for all of 2022** in every monthly file. | Part 12/13 COVID handling is not optional — it is forced by the data. |
| 5 | Capacity file (`Ehoba_1_ano.xlsx`) is **quarterly snapshots, not monthly**, with a changing category taxonomy and pre-2013 sourced from a different survey (EOH vs EHOBA). | Revenue proxy (Part 8) must be labelled a proxy; monthly capacity cannot be manufactured. |
| 6 | Government presentation formatting confirmed: title in row 1, **multi-row headers in rows 2–4** (rate file) / rows 3–4 (occupancy), merged cells, year sub-headers interleaved between month rows, and 4–5 trailing footnote rows. Row 1 is never the header. | Parser must be structural, not `header=0`. |

---

## 1. File inventory

| File | Size | Workbook sheets | Statistical content |
|------|------|-----------------|---------------------|
| `Ehoba_02a_0811.xlsx` | 55.8 KB | `Ehoba_02a_0811`, `Ficha Técnica` | Room occupancy rate (**tasa de ocupación de habitaciones**), % |
| `Ehoba_03a_0811.xlsx` | 45.3 KB | `Ehoba_03a_0811`, `Ficha Técnica` | **Average room rate (tarifa promedio), pesos** — the price variable |
| `Ehoba_04_0811.xlsx` | 60.6 KB | `Ehoba_04_0811`, `Ficha Técnica` | Bed/place occupancy rate (**tasa de ocupación de plazas**), % |
| `Ehoba_VA_0811.xlsx` | 24.7 KB | `Ehoba_VA_0811`, `Ficha Técnica` | Travellers hosted (**viajeros/as hospedados/as**), persons |
| `Ehoba_1_ano.xlsx` | 74.6 KB | `Ehoba_1_año` (index), one sheet per year `2008`…`2026`, `Ficha Técnica` | Establishments, available room-nights, available bed-nights |

Source for all: *Instituto de Estadística y Censos de la Ciudad Autónoma de Buenos Aires (GCBA) — Encuesta de Ocupación Hotelera de Buenos Aires (EHOBA)*. Pre-2013 capacity rows cite the older *Dirección General de Estadística y Censos — EOH*.

No CSV/Parquet/other data files exist in the project. Only `.DS_Store` besides the five workbooks.

---

## 2. Per-file structure

### 2.1 `Ehoba_02a_0811.xlsx` — Room occupancy rate (%)

- **Data sheet:** `Ehoba_02a_0811`, range `A1:U259` (used block A1:K245).
- **Merged cells:** `B2:K2` ("Categoría"), `B3:H3` ("Hoteleros"), `I3:K3` ("Parahoteleros"), `A246:K247` + `A248:K248` (footnotes).
- **Header:** row 1 = long title; row 2 = "Categoría" band; row 3 = group band (Hoteleros / Parahoteleros); **row 4 = real column names**. Row 5 onward = data.
- **Column layout (A–K):**
  `A` Período · `B` Total (hoteleros) · `C` 1 y 2 estrellas · `D` 3 estrellas · `E` 4 estrellas · `F` 5 estrellas · `G` Apart · `H` Boutique · `I` Total (parahoteleros) · `J` Hostel · `K` Otros/resto
- **Period representation:** a bare 4-digit **year row** (`2008`, `2009`, …) with empty data cells, followed by 12 Spanish month-name rows (`Enero`…`Diciembre`). The 2020 year-row is labelled **`2020a`** (footnote marker), which a naive `str.isdigit()` check will miss.
- **Coverage:** 2008-01 → 2026-05. Last 3 months (2026-03/04/05) flagged `*` "Datos provisorios".
- **Missing / non-numeric tokens:**
  - `---` / `-` in **Hostel (col J) for every month 2008-01 → 2022-12**, then `///` afterwards. Per footnote: room-occupancy is *deliberately not published* for hostels (shared/semi-private rooms). Treat Hostel room-occupancy as **structurally absent**, not missing-at-random.
  - `///` = "dato que no corresponde".
  - **COVID gap:** 2020-03 = only cols B & I present; **2020-04 → 2020-10 entirely blank**; 2020-11 → 2021-12 = only col B (Total hoteleros) and col I (Total parahoteleros); **2022 all months = "1 y 2 estrellas" (col C) blank** plus Hostel/Otros blank. Full category detail resumes 2023-01.
- **Units:** percentage (0–100), stored as full-precision floats (e.g. `60.3111935773585`); a few later months are pre-rounded (`54.07`, `67.5`).
- **Footnotes (rows 246–250):** COVID note "a"; hostel-not-published note; `///` legend; source line.

### 2.2 `Ehoba_03a_0811.xlsx` — Average rate (pesos)  ← PRICE VARIABLE

- **Data sheet:** `Ehoba_03a_0811`, range `A1:S260` (used block A1:I245).
- **Merged cells:** `A2:A4` ("Período"), `B2:I2` ("Categoría"), `B3:G3` ("Hoteleros"), `H3:I3` ("Parahoteleros"), `A246:I247` (footnote).
- **Header:** row 1 = title incl. "(pesos)"; row 2 = "Categoría"; row 3 = group band; **row 4 = column names**. Data from row 5.
- **Column layout (A–I) — NOTE: no Total column:**
  `A` Período · `B` 1 y 2 estrellas · `C` 3 estrellas · `D` 4 estrellas · `E` 5 estrellas · `F` Apart · `G` Boutique · `H` Hostel · `I` Otros/resto
- **Period representation:** identical year-row / month-row pattern; 2020 year-row again `2020a`.
- **Coverage:** 2008-01 → 2026-05, provisional `*` on 2026-02…05 (2026-01 & 2025-12 are blank — see below).
- **Values:** nominal pesos, full precision. 2008 levels are tens–hundreds of pesos (1–2★ ≈ 97; 5★ ≈ 582); 2025 levels are tens of thousands (1–2★ ≈ 73,000; 5★ ≈ 300,000+). **≈700–3000× nominal growth** over the window — real deflation with CPI is mandatory before any cross-year comparison.
- **Missing / non-numeric:**
  - **COVID gap larger than in the occupancy files:** **2020-03 → 2021-12 is entirely blank for all 8 categories** (no "Total" fallback exists here).
  - **2022 all 12 months:** "1 y 2 estrellas" (col B), "Hostel" (col H), "Otros/resto" (col I) blank; 3★/4★/5★/Apart/Boutique present.
  - **2025-12 and 2026-01 blank for all categories** (publication gap in the provisional tail).
  - One visible outlier to check in cleaning, not drop yet: 5★ Aug-2025 = 381,801 vs ~250–310k neighbours (~+45% one-month spike then reversion).
- **Footnotes (rows 245–249):** `*` provisional; COVID note "a"; `///` legend; source.

### 2.3 `Ehoba_04_0811.xlsx` — Bed/place occupancy rate (%)

- **Data sheet:** `Ehoba_04_0811`, range `A1:V262` (used block A1:K245).
- **Header / column layout:** identical structure and identical 11-column layout (A–K) as `02a` (Total hoteleros … Otros/resto).
- **Key difference from 02a:** the **Hostel column (J) DOES carry data from 2008-01** (bed occupancy is published for hostels even though room occupancy is not).
- **Period representation:** same year-row/month-row; 2020 row = `2020a`.
- **Coverage:** 2008-01 → 2026-05 (`*` provisional 2026-03/04/05).
- **COVID gap:** same shape as 02a — 2020-03 partial, 2020-04→10 blank, 2020-11→2021-12 Totals-only (cols B & I), 2022 missing "1 y 2 estrellas" (col C). Resumes 2023-01.
- **Units:** percentage. Footnotes rows 245–249 (provisional, COVID "a", `///`, source).

### 2.4 `Ehoba_VA_0811.xlsx` — Travellers hosted (persons)

- **Data sheet:** `Ehoba_VA_0811`, range `A1:K189` (used block A1:H178).
- **Merged cells:** `A1:H1` (title), `A2:A3` ("Período"), `B2:B3` ("Total"), `C2:H2` ("Categoría de alojamiento turístico").
- **Header:** row 1 = title; **rows 2–3 = header**; data from row 4.
- **Column layout (A–H):**
  `A` Período · `B` **Total** · `C` 1 y 2 estrellas¹ · `D` 3 estrellas · `E` 4 estrellas · `F` 5 estrellas · `G` Apart hotel · `H` Boutique
  - Footnote 1: 1★ and 2★ are *reported unified because they form a single sampling stratum*.
  - **Nota: "los datos excluyen los establecimientos parahoteleros"** — no Hostel / Otros / parahotel here at all. This series is hotel-sector only.
- **Coverage:** **2013-01 → 2026-05** (starts 5 years later than the rate/occupancy files). `*` provisional 2026-03/04/05.
- **Units:** count of travellers (integers, tens of thousands to ~430,000/month).
- **COVID gap:** 2020-03 = Total only; **2020-04 → 2021-12 entirely blank**; **2022 all months: Total (col B) and 1–2★ (col C) blank**, other five categories present. Full detail resumes 2023-01.
- **Frequency:** monthly. Footnotes rows 179–183.

### 2.5 `Ehoba_1_ano.xlsx` — Establishments / available room-nights / available bed-nights

- **Workbook:** an index sheet `Ehoba_1_año` (lists years 2026→2008, no data), then **one sheet per calendar year** `2008`…`2026`, plus `Ficha Técnica`.
- **Within each year sheet:** 1–4 **quarterly snapshot blocks**, each block = title band + "Categoría" band + group band ("Hoteleros³" / "Parahoteleros³") + column-name row + 3 data rows:
  - `Establecimientos` (count of open establishments)
  - `Habitaciones o unidades disponibles¹` = **rooms × days-open in the reference month** (i.e. available **room-nights**, not a room count)
  - `Plazas disponibles²` = fixed + extra beds × days-open (available **bed-nights**)
- **Snapshot frequency (irregular):**
  - 2008–2010: **2 per year** (March, December)
  - 2011–2015: **3 per year** (March, July, December)
  - 2016–2025: **4 per year** (March, June, September, December)
  - 2026: **1 so far** (March)
- **Column layout (2013+):** `Total (hoteleros) · 1 y 2 estrellas · 3 estrellas · 4 estrellas · 5 estrellas · Apart · Boutique · Total (parahoteleros) · Hostel · Otros/resto`.
- **Category-definition change over time (IMPORTANT):**
  - **2008 sheet** uses the older EOH taxonomy: row label `Hoteles` (not `Establecimientos`), no "Parahoteleros Total" column, and the `Total` column appears to include parahotels (Mar-2008 Total 593 = 296 hotel + 134 Hostel + 163 Otros). Source line: *Dirección General de Estadística y Censos — EOH*.
  - **2009–2012 sheets** already use the EHOBA layout with a separate "Parahoteleros Total"; `Total` = hoteleros only.
  - So the "Total" definition is **not consistent between 2008 and 2009+**. 2009→2026 are comparable to each other.
- **COVID / provisional gaps:** 2020 and 2021 sheets have **only the two "Total" columns**; all star/type breakdowns are `///`. 2022 March still has "1 y 2 estrellas" = `///`. `Habitaciones` Hostel column is `///` throughout (a bed metric, not a room metric). 2020-Jun and 2020-Sep blocks are fully `///`. One data glitch: 2020-Dec `Establecimientos` Total = `169.81…` (non-integer — a modelled/imputed value in the source).
- **Frequency for the panel:** treat as **quarterly** (with the 2008–2015 irregularities). Monthly capacity does **not** exist and must not be interpolated into the panel as if observed.
- **Ficha Técnica:** "Periodicidad de difusión: Trimestral"; method = rooms/beds × days-open in the reference month.

---

## 3. Data dictionary

| variable | definition | source file / sheet | column(s) | frequency | start | end | unit |
|---|---|---|---|---|---|---|---|
| `date` | month (period start) | derived from year-row + month-name | — | monthly | 2008-01 | 2026-05 | date |
| `room_occupancy` | rooms occupied ÷ rooms available for sale, in month | `Ehoba_02a_0811` | B–K by category | monthly | 2008-01 | 2026-05 | % (0–100) |
| `bed_occupancy` | beds (plazas) occupied ÷ beds available, in month | `Ehoba_04_0811` | B–K by category | monthly | 2008-01 | 2026-05 | % (0–100) |
| `average_rate` | mean monthly room rate (tarifa promedio) by category — **nominal pesos** | `Ehoba_03a_0811` | B–I by category (**no Total**) | monthly | 2008-01 | 2026-05 | ARS (nominal) |
| `travelers` | travellers hosted, hotel sector only (excl. parahotel) | `Ehoba_VA_0811` | B–H by category | monthly | **2013-01** | 2026-05 | persons |
| `establishments` | open establishments by category | `Ehoba_1_ano` / year sheets | by category | **quarterly** (2/yr 2008–10, 3/yr 2011–15, 4/yr 2016+) | 2008-03 | 2026-03 | count |
| `available_room_nights` | rooms × days-open in reference month | `Ehoba_1_ano` / year sheets | by category | quarterly (as above) | 2008-03 | 2026-03 | room-nights |
| `available_bed_nights` | (fixed+extra beds) × days-open in reference month | `Ehoba_1_ano` / year sheets | by category | quarterly (as above) | 2008-03 | 2026-03 | bed-nights |
| `cpi_gba` | IPC Región GBA, Nivel general, index (base Dec-2016=100) — **primary deflator** | `sh_ipc_08_26.xls` / `Índices IPC Cobertura Nacional` (GBA block) + `IPC GBA Base dic 2016` bridge | GBA "Nivel general" row | monthly | 2016-04 | 2026-07 | index |
| `cpi_nac` | IPC Total nacional, Nivel general, index (base Dec-2016=100) — **robustness deflator** | `sh_ipc_08_26.xls` / `Índices IPC Cobertura Nacional` (Total nacional block) | "Nivel general" row | monthly | 2016-12 | 2026-07 | index |
| `cpi_resthot_gba` | IPC Región GBA, division "Restaurantes y hoteles", index — sector benchmark (optional) | `sh_ipc_08_26.xls` / same sheet | GBA "Restaurantes y hoteles" row | monthly | 2016-12 | 2026-07 | index |
| `inflation_mom` | 100·(CPI_t/CPI_{t−1}−1) | derived from `cpi_gba` (also `cpi_nac`) | — | monthly | 2017-01 | 2026-05 | % |
| `inflation_yoy` | 100·(CPI_t/CPI_{t−12}−1) | derived from `cpi_gba` (also `cpi_nac`) | — | monthly | 2017-04 | 2026-05 | % |
| `real_rate` | `average_rate` ÷ `cpi_gba` × 100 (base Dec-2016=100, documented) | derived | — | monthly | 2016-12 | 2026-05 | ARS (constant, Dec-2016 pesos) |

### Category availability by file

| Category | 02a room-occ | 03a rate | 04 bed-occ | VA travelers | 1_ano capacity |
|---|---|---|---|---|---|
| Total (hoteleros) | ✔ | ✗ **absent** | ✔ | ✔ | ✔ |
| 1 y 2 estrellas | ✔ | ✔ | ✔ | ✔ (1★+2★ unified) | ✔ |
| 3 estrellas | ✔ | ✔ | ✔ | ✔ | ✔ |
| 4 estrellas | ✔ | ✔ | ✔ | ✔ | ✔ |
| 5 estrellas | ✔ | ✔ | ✔ | ✔ | ✔ |
| Apart | ✔ | ✔ | ✔ | ✔ | ✔ |
| Boutique | ✔ | ✔ | ✔ | ✔ | ✔ |
| Total (parahoteleros) | ✔ | ✗ | ✔ | ✗ | ✔ |
| Hostel | ✗ (never published) | ✔ | ✔ | ✗ | rooms ✗ / beds ✔ |
| Otros/resto | ✔ | ✔ | ✔ | ✗ | ✔ |

**Consistently defined across the whole window and present in the price file:** `1 y 2 estrellas`, `3 estrellas`, `4 estrellas`, `5 estrellas`, `Apart`, `Boutique`. These six are the natural modeling set. `Hostel` and `Otros/resto` are defined but thin/asymmetric. `Total` has no price series.

---

## 4. Common-period analysis

| Combination | Overlapping monthly span (pre-COVID-adjustment) |
|---|---|
| rate + room-occ + bed-occ | 2008-01 → 2026-05 |
| + travelers | **2013-01 → 2026-05** |
| + capacity (quarterly) | quarterly points within 2013–2026 (2/3/4 per year) |
| All series, full category detail, COVID excluded | 2013-01 → 2020-02, then **2023-01 → 2026-05** (2022 usable for 3★/4★/5★/Apart/Boutique only; 2020-03→2021-12 unusable at category level) |

**Locked primary analysis window (§10): `2016-12 → 2026-05`** — the span with official CPI. Within it:
`travelers` starts 2013 so it is fully available; capacity is the quarterly sub-panel (4/yr) throughout;
the six star+Apart+Boutique categories carry rate + occupancy for every month except the COVID hole
(2020-03→2021-12) and the 2022 "1 y 2 estrellas" gap. Effective usable months per category ≈ 114
(≈ 90 once the COVID block and 2022 1–2★ gap are removed). Pre-2016 hotel data is kept for
**descriptive nominal charts only** (Plot 1, Chart A context) and never enters a CPI-deflated model.

---

## 5. Cleaning decisions required (none executed yet — for your sign-off)

1. **Parser:** read each monthly sheet with no header; take column names from row 4 (rate/occupancy) or rows 2–3 (VA); forward-fill the year from year-rows; parse Spanish month names; strip `*`; map `2020a`→2020. Drop the 4–5 footnote rows by detecting the first non-month row after data.
2. **Missing tokens** `---`, `-`, `///`, blank → `NaN`, with a companion `missing_reason` column (`covid_no_detail`, `hostel_not_published`, `provisional_gap`, `series_not_started`). **No imputation** without your approval.
3. **Long format:** melt to `date × hotel_category × variable`; keep the raw wide sheets as-is under `data/raw/`.
4. **`Total` rate:** the price file has no Total column. Default plan → report the five/​six category-level series individually; **additionally** build a capacity-weighted "all-hotels" average rate = Σ(rate_c × available_room_nights_c) / Σ(available_room_nights_c) using the quarterly capacity snapshots (so this composite is quarterly, clearly labelled derived). Occupancy/bed "Total (hoteleros)" columns are used as published. (Open for override.)
5. **COVID flagging:** add `covid_period` (2020-03 → 2021-12 hard block) and `covid_recovery` (2022-01 → 2022-12, partial categories) indicators; ensure estimators can exclude or dummy them (Part 4/12/13).
6. **Capacity merge:** keep quarterly; when a monthly panel needs capacity, either restrict to snapshot months or attach the nearest-prior snapshot **explicitly labelled `capacity_asof`** — never present as monthly-observed.
7. **Pre-2013 capacity taxonomy:** treat 2008 capacity as a separate regime or start capacity-based revenue proxy at 2009.
8. **Outlier register (not deletion):** 5★ rate Aug-2025; 2020-Dec establishments = 169.81. Flag, investigate, decide later.
9. **Units audit:** rate = nominal ARS; occupancy = %, convert to fraction only inside models; capacity = room-/bed-*nights per month* (already time-aggregated — do **not** multiply by days again).

---

## 6. Structural breaks / regime notes

- **COVID-19:** 2020-03 (17 March lockdown) → category detail returns 2023-01. Hard data hole 2020-03→2021-12; degraded 2022.
- **Survey/source change:** capacity pre-2013 from EOH (Dirección General de Estadística y Censos); 2013+ from EHOBA. Occupancy/rate/VA are EHOBA throughout.
- **Argentina macro regime shifts inside the analysis window** (to be dated precisely from `cpi_gba` MoM): 2018-04→2019 currency crisis and inflation step-up; Aug-2019 PASO devaluation; 2020 pandemic price freezes (Precios Máximos); **Dec-2023 devaluation → Jan-2024 IPC ≈ +20–25% MoM** (the single largest monthly shock in the series); 2024–2025 disinflation path (MoM from ~25% down toward ~2%). These become the natural inflation-regime cut points in Part 6.
- **Provisional tail:** 2026-02→05 across the hotel files (`*` datos provisorios); rate file additionally missing 2025-12 & 2026-01. CPI is final through ~2026-05 and provisional/partial for 2026-06/07 (beyond the hotel window anyway).

---

## 7. What is still missing (non-blocking)

1. **Pre-2016 CPI** — no official series exists for 2008-01 → 2016-11. Per your decision (§10) we do **not** splice; the analysis window simply starts 2016-12. If you later want the full 2008–2026 sample, a spliced non-official series (IPC San Luis / Congreso / CABA-DGEyC) would be required and clearly flagged.
2. **Hotel input-cost / wage index** — not supplied. Per your rule 5, Part 9 optimises **revenue, not profit**. The `Restaurantes y hoteles` CPI division (`cpi_resthot_gba`) is available as a partial cost proxy but is a price index, not a cost index, so it will be used only for context, not as `C_t`.

**Resolved since first audit:** price file present (`Ehoba_03a_0811.xlsx`); CPI present (`sh_ipc_08_26.xls`).

---

## 8. Next steps

1. Scaffold the repo per Part 15 (`data/raw`, `data/processed`, `src/01…08`, `outputs/figures`, `outputs/tables`, `requirements.txt`, `README.md`); copy the 6 source files into `data/raw/` untouched; `git init`.
2. Build `01_load_data.py` + `02_clean_data.py` per §5 and §9: structural parsers for the 6 EHOBA sheets + the 3 CPI sheets → one long-format monthly panel (`date × hotel_category × variable`) + a quarterly capacity panel, saved as Parquet, plus a machine-readable data dictionary and a full transformation/audit log.
3. `03_merge_data.py`: attach `cpi_gba`, `cpi_nac`, inflation transforms, `real_rate` (base Dec-2016=100), COVID flags, seasonal dummies; restrict to 2016-12 → 2026-05.
4. **Checkpoint — show you:** per-category coverage table, missing-value map, nominal vs real rate sanity plots, inflation series vs published INDEC headline (cross-check), and descriptive Table 1. No elasticity / pass-through / dynamic-pricing modelling until you sign off on that checkpoint (your rule 12).

### Decisions still open for your input
- §5.4 composite "all-hotels" rate — default is capacity-weighted quarterly; say if you'd rather just drop Total from price work entirely.
- Inflation-regime thresholds (Part 6): plan is data-driven terciles of MoM `cpi_gba` inflation within-window, **not** fixed cutoffs — flag if you want a specific scheme.
- COVID handling in estimation: plan is exclude 2020-03→2021-12 from fitting + include a 2022 recovery dummy; robustness runs both with and without.

---

## 9. CPI file audit — `data/sh_ipc_08_26.xls`

- **Origin:** INDEC, Dirección Nacional de Estadísticas de Precios. Old-style `.xls` (BIFF, CP-1252). Title: *"Índice de precios al consumidor con cobertura nacional. Resultados regionales según divisiones de la canasta…"*. Base period **Diciembre 2016 = 100**.
- **6 sheets:**

| Sheet | Content | Layout | Coverage |
|---|---|---|---|
| `Índices IPC Cobertura Nacional` | **Index levels** — the sheet we use | Stacked region blocks (Total nacional, then **Región GBA**, Pampeana, NOA, NEA, Cuyo, Patagonia). Each block: `Nivel general` + 12 COICOP divisions (incl. **`Restaurantes y hoteles`**) + 3 categorías (Estacional/Núcleo/Regulados) + Bienes/Servicios. Month **dates run across columns** as Excel serials in a header row (row 5 for Total nacional, row 35 for GBA); label in col A; data rows separated by blank rows. | **2016-12 → 2026-07**, monthly (116 months) |
| `Variación mensual IPC Nacional` | MoM % (already computed by INDEC) | same stacked-block, dates-across-columns | 2017-01 → 2026-07 |
| `Var. interanual IPC Nacional` | YoY % | same | 2017-12 → 2026-07 |
| `IPC GBA Base dic 2016` | GBA index **rebased to Dec-2016=100** — bridges GBA back before the national sheet starts | dates-across-columns | **2016-04 → 2016-12** (9 months) |
| `IPC GBA Abril 2016-Mayo 2017` | Original IPC-GBA, base Apr-2016=100 (historical reference) | dates-across-columns | 2016-04 → 2017-05 |
| `Ponderaciones` | COICOP division weights by region (Dec-2016 basket). GBA `Restaurantes y hoteles` weight = **0.108**. | small table | static |

- **Parsing notes:** transpose required (periods are columns, not rows); header rows carry Excel date serials (use `xldate_as_datetime`, `datemode` from workbook); each region block must be delimited by its header label (`Total nacional`, `Región GBA`, …) and the following blank row; strip the 3–4 trailing `Nota:` / `Fuente:` rows; `.xls` needs `xlrd` (installed) — `openpyxl` cannot read it.
- **Series we will extract:**
  - `cpi_gba` = GBA · Nivel general, spliced = `IPC GBA Base dic 2016` (2016-04…2016-11) + `Índices IPC Cobertura Nacional` GBA block (2016-12…2026-07). Both already on Dec-2016=100, so the join is a level continuation, not a re-scaling (still: verify the 2016-12 value = 100.0 in both).
  - `cpi_nac` = Total nacional · Nivel general (2016-12…2026-07).
  - `cpi_resthot_gba` = GBA · `Restaurantes y hoteles` division (2016-12…2026-07) — context/robustness only.
- **Cross-check planned:** recompute MoM from `cpi_gba` levels and compare to the `Variación mensual IPC Nacional` GBA row (tolerance ~0.1pp — INDEC rounds indices to 4 dp).
- **`Restaurantes y hoteles` is a CPI division, not a hotel cost index** — it includes restaurant meals and is a consumer-price, not producer-cost, measure. It does **not** unlock profit optimisation.

## 9b. Files removed from the project (user pasted, not relevant)

Deleted with your authorisation ("delete the rest"):

| File | What it was | Why removed |
|---|---|---|
| `indec_ipc_variacion_mensual.csv` | INDEC national IPC MoM, **only 2024-08 → 2026-07**, values as fractions | Redundant with `sh_ipc_08_26.xls` and far too short |
| `indec_ventas_supermercados_volumen.csv` | Supermarket sales volume index, 2024–2026 | Not an inflation or hotel variable |
| `indec_ventas_supermercados_volumen_sa.csv` | Same, seasonally adjusted | Not an inflation or hotel variable |
| `maestro-provincias.xlsx` | Province code lookup table | Not relevant to a CABA-only study |

`sh_ipc_08_26.xls` was **moved into `data/`** (kept).

---

## 10. Locked decisions (from your answers, 2026-09-06)

| Decision | Choice | Effect |
|---|---|---|
| **Analysis window** | **2016-12 → 2026-05** | The span with official CPI. No pre-2016 splice. Pre-2016 hotel data → descriptive nominal context only. |
| **CPI geography** | **Región GBA primary; Total nacional as robustness (Part 13)** | `real_rate`, pass-through, elasticity, dynamic pricing all run on `cpi_gba`; every headline result re-run on `cpi_nac` and reported side-by-side. |
| Deflator base | **Dec-2016 = 100** (the file's native base) | `real_rate_t = nominal_rate_t / cpi_gba_t × 100`, expressed in constant Dec-2016 pesos. Documented in README. |
| Profit vs revenue | **Revenue only** (no cost data) | Part 9 optimises `P·Q(P)`; profit left out per rule 5. |
| Categories in scope | `1 y 2 estrellas`, `3 estrellas`, `4 estrellas`, `5 estrellas` (core); `Apart`, `Boutique` (secondary); capacity-weighted composite for "all hotels" | `Hostel` rate excluded (never published for room-occ); `Otros/resto` reported but not modelled. |

No elasticity / pass-through / pricing modelling has run yet. Proceeding to repo scaffold + cleaning pipeline, then the §8.4 checkpoint.
