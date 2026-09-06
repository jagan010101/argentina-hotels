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
}

# Modelling scope (DATA_AUDIT.md sec 10)
CORE_CATEGORIES = ["stars_1_2", "stars_3", "stars_4", "stars_5"]
SECONDARY_CATEGORIES = ["apart", "boutique"]
MODEL_CATEGORIES = CORE_CATEGORIES + SECONDARY_CATEGORIES  # have a price series + stable definition

# --------------------------------------------------------------------------- #
# Analysis window & structural-break dates  (DATA_AUDIT.md sec 6 & 10)
# --------------------------------------------------------------------------- #
WINDOW_START = "2016-12-01"   # first month with official CPI
WINDOW_END = "2026-05-01"     # last hotel observation

# COVID: hard data hole (category detail unavailable) and degraded-recovery year
COVID_HOLE_START = "2020-03-01"
COVID_HOLE_END = "2021-12-01"
COVID_RECOVERY_START = "2022-01-01"
COVID_RECOVERY_END = "2022-12-01"

# Full nominal-only context window (descriptive plots only, never CPI-deflated)
NOMINAL_CONTEXT_START = "2008-01-01"

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
