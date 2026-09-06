"""
Central configuration for the Buenos Aires hotel dynamic-pricing project.

Every path, constant, category map, and modelling-window decision lives here so
the numbered pipeline scripts stay thin and the assumptions are auditable in one
place. See DATA_AUDIT.md sections 5, 9 and 10 for the rationale behind each value.
"""
from __future__ import annotations

from pathlib import Path

# --------------------------------------------------------------------------- #
# Paths
# --------------------------------------------------------------------------- #
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUT_FIG = ROOT / "outputs" / "figures"
OUT_TAB = ROOT / "outputs" / "tables"

for _p in (DATA_PROCESSED, OUT_FIG, OUT_TAB):
    _p.mkdir(parents=True, exist_ok=True)

# Raw source files (read-only inputs)
F_ROOM_OCC = DATA_RAW / "Ehoba_02a_0811.xlsx"   # tasa de ocupación de habitaciones (%)
F_RATE = DATA_RAW / "Ehoba_03a_0811.xlsx"       # tarifa promedio (pesos)  <-- price
F_BED_OCC = DATA_RAW / "Ehoba_04_0811.xlsx"     # tasa de ocupación de plazas (%)
F_TRAVELERS = DATA_RAW / "Ehoba_VA_0811.xlsx"   # viajeros hospedados (persons)
F_CAPACITY = DATA_RAW / "Ehoba_1_ano.xlsx"      # establecimientos / habitaciones / plazas
F_CPI = DATA_RAW / "sh_ipc_08_26.xls"           # INDEC IPC, base dic-2016 = 100

# Processed outputs
P_LOADED_DIR = DATA_PROCESSED / "01_loaded"        # one parquet per raw table, untouched shape
P_PANEL_LONG = DATA_PROCESSED / "02_panel_long.parquet"
P_CAPACITY_Q = DATA_PROCESSED / "02_capacity_quarterly.parquet"
P_CPI_MONTHLY = DATA_PROCESSED / "02_cpi_monthly.parquet"
P_ANALYSIS = DATA_PROCESSED / "03_analysis_panel.parquet"
P_DATA_DICT = OUT_TAB / "data_dictionary.csv"
P_AUDIT_LOG = DATA_PROCESSED / "cleaning_audit_log.csv"

# --------------------------------------------------------------------------- #
# Spanish month names -> month number
# --------------------------------------------------------------------------- #
MONTHS_ES = {
    "enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
    "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
    "noviembre": 11, "diciembre": 12,
}
MONTHS_ES_UPPER = {k.upper(): v for k, v in MONTHS_ES.items()}

# Tokens that mean "no value" in the government spreadsheets
NA_TOKENS = {"---", "--", "-", "///", "//", "/", "s/d", "s.d.", "nd", "n/d", "", "…", "..."}

# --------------------------------------------------------------------------- #
# Hotel category harmonisation
# Raw Spanish header text  ->  canonical snake_case key
# --------------------------------------------------------------------------- #
CATEGORY_CANON = {
    "total": "total_hoteleros",
    "total hoteleros": "total_hoteleros",
    "1 y 2 estrellas": "stars_1_2",
    "1 y 2 estrellas1": "stars_1_2",
    "1 y 2 *": "stars_1_2",
    "3 estrellas": "stars_3",
    "3 *": "stars_3",
    "4 estrellas": "stars_4",
    "4 *": "stars_4",
    "5 estrellas": "stars_5",
    "5 *": "stars_5",
    "apart": "apart",
    "apart hotel": "apart",
    "boutique": "boutique",
    "hostel": "hostel",
    "otros/resto": "otros_resto",
    "otros": "otros_resto",
    "resto": "otros_resto",
}
# Parahotel "Total" column: labelled just "Total" but sitting in the parahotel band.
# Handled positionally in the loader, mapped to this key.
CAT_TOTAL_PARAHOTEL = "total_parahoteleros"

# Human-readable labels for plots/tables
CATEGORY_LABELS = {
    "total_hoteleros": "Total hotels",
    "total_parahoteleros": "Total para-hotels",
    "stars_1_2": "1-2 star",
    "stars_3": "3 star",
    "stars_4": "4 star",
    "stars_5": "5 star",
    "apart": "Apart-hotel",
    "boutique": "Boutique",
    "hostel": "Hostel",
    "otros_resto": "Other / rest",
    "total_composite": "Total (composite)",
}

# Modelling scope
CORE_CATEGORIES = ["stars_1_2", "stars_3", "stars_4", "stars_5"]
SECONDARY_CATEGORIES = ["apart", "boutique"]
MODEL_CATEGORIES = CORE_CATEGORIES + SECONDARY_CATEGORIES
# "Total" has no rate column in the source -> a capacity-weighted composite is
# built in notebook 03 and appended as this key (quarterly-anchored, derived).
COMPOSITE_TOTAL = "total_composite"
PRESENT_CATEGORIES = CORE_CATEGORIES + [COMPOSITE_TOTAL]   # for the headline story

# --------------------------------------------------------------------------- #
# Sample windows & structural-break dates  (see PROJECT_AUDIT.md sec 4-5)
# --------------------------------------------------------------------------- #
# CPI coverage bound (GBA IPC via the dic-2016 bridge starts 2016-04)
CPI_MIN_DATE = "2016-04-01"
DATA_END = "2026-05-01"

# Long-run *nominal-only* context (never CPI-deflated below this only for plots)
LONGRUN_START = "2008-01-01"

# Main analysis sample: pre-COVID normal + post-COVID, COVID handled separately.
ANALYSIS_SEGMENTS = [("2018-01-01", "2019-12-01"),
                     ("2022-01-01", "2026-05-01")]

# COVID structural break: hard data hole + kept entirely out of the main sample
COVID_START = "2020-01-01"
COVID_END = "2021-12-01"
COVID_HOLE_START = "2020-03-01"   # category detail genuinely missing
COVID_HOLE_END = "2021-12-01"
# retained for backward compat with earlier notebooks
COVID_RECOVERY_START = "2022-01-01"
COVID_RECOVERY_END = "2022-12-01"
WINDOW_START, WINDOW_END = "2018-01-01", "2026-05-01"

# Temporal backtest split (PROJECT_AUDIT.md sec 4)
TRAIN_SEGMENTS = [("2018-01-01", "2019-12-01"), ("2022-01-01", "2022-12-01")]
VALID_SEGMENT = ("2023-01-01", "2023-12-01")
TEST_SEGMENT = ("2024-01-01", "2026-05-01")

# --------------------------------------------------------------------------- #
# Repricing-policy parameters
# --------------------------------------------------------------------------- #
# Cumulative-inflation repricing threshold tau (fraction, not %)
THRESHOLD_GRID = [0.01, 0.02, 0.03, 0.04, 0.05, 0.06, 0.07, 0.08, 0.10]

# Operational penalty for the Objective = Revenue - lambda * N_reprice sweep.
# lambda is expressed as a FRACTION of mean monthly revenue per repricing event;
# NOT a calibrated monetary cost -- report the whole range / the Pareto frontier.
LAMBDA_GRID = [0.0, 0.005, 0.01, 0.02, 0.03, 0.05, 0.08, 0.12]

# Occupancy tilt band for Policy 3 (fraction added/subtracted at a repricing)
OCC_TILT_GRID = [0.00, 0.02, 0.03, 0.05, 0.08]

# Demand-elasticity scenarios for policy evaluation (occupancy is inelastic and
# not causally identified -- results are reported as a function of assumed beta)
BETA_SCENARIOS = [0.0, -0.25, -0.50, -1.00]

# Inflation-regime cut points: data-driven terciles of GBA monthly inflation,
# computed within the analysis sample (see notebook 05).
REGIME_QUANTILES = [0.0, 1 / 3, 2 / 3, 1.0]
REGIME_LABELS = ["low", "mid", "high"]

# CPI deflator base period (native base of the INDEC file)
CPI_BASE_LABEL = "dic-2016 = 100"

# --------------------------------------------------------------------------- #
# CPI sheet structure (DATA_AUDIT.md sec 9)
# --------------------------------------------------------------------------- #
CPI_SHEET_INDEX = "Índices IPC Cobertura Nacional"
CPI_SHEET_MOM = "Variación mensual IPC Nacional"
CPI_SHEET_GBA_BRIDGE = "IPC GBA Base dic 2016"
# Region block header labels as they appear in column A of the index sheet
CPI_REGION_TOTAL = "Total nacional"
CPI_REGION_GBA = "Región GBA"
CPI_ROW_GENERAL = "Nivel general"
CPI_ROW_RESThOT = "Restaurantes y hoteles"

PLOT_DPI = 200
