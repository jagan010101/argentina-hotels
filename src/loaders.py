"""
Structural parsers for the raw EHOBA / INDEC spreadsheets.

Pure functions — no logging, no IO beyond reading the given file. Each returns a
tidy long DataFrame; nothing is cleaned, filtered or window-restricted (that is
notebook 01's `02_clean` section). Missing-value tokens (`---`, `///`, `-`,
blank) are kept verbatim in `raw_value`.

`load_monthly_ehoba` attaches `df.attrs["unmapped"]` — header cells it could not
map to a canonical category (should be empty).
"""
from __future__ import annotations

import openpyxl
import pandas as pd
import xlrd

from common import canon_category, month_from_label, norm_text, year_from_label
import config as C


# --------------------------------------------------------------------------- #
def _band_forward_fill(ws, row, c_lo, c_hi):
    """{col -> band label}, filling merged-anchor values across columns."""
    out, cur = {}, ""
    for c in range(c_lo, c_hi + 1):
        v = norm_text(ws.cell(row=row, column=c).value)
        if v:
            cur = v.lower()
        out[c] = cur
    return out


def load_monthly_ehoba(path, sheet, *, header_row, band_row, first_data_row,
                       c_lo=2, c_hi=None, total_is_parahotel_band=True):
    """Monthly EHOBA sheet (rate / room-occ / bed-occ / travellers) -> long."""
    wb = openpyxl.load_workbook(path, data_only=True)   # full load: random .cell() is O(1)
    ws = wb[sheet]
    c_hi = c_hi or ws.max_column
    bands = (_band_forward_fill(ws, band_row, c_lo, c_hi)
             if band_row else {c: "" for c in range(c_lo, c_hi + 1)})

    col_cat, unmapped = {}, []
    for c in range(c_lo, c_hi + 1):
        raw = norm_text(ws.cell(row=header_row, column=c).value)
        if not raw:
            continue
        cat = canon_category(raw)
        if cat == "total_hoteleros" and total_is_parahotel_band and \
                "parahotel" in bands.get(c, ""):
            cat = C.CAT_TOTAL_PARAHOTEL
        if cat:
            col_cat[c] = cat
        else:
            unmapped.append((f"{sheet} col{c}", raw))

    records, cur_year = [], None
    for r in range(first_data_row, ws.max_row + 1):
        a = ws.cell(row=r, column=1).value
        y = year_from_label(a)
        if y is not None and all(ws.cell(row=r, column=c).value in (None, "")
                                 for c in list(col_cat)[:3]):
            cur_year = y
            continue
        m = month_from_label(a)
        if m is None or cur_year is None:
            continue
        prov = "*" in str(a)
        for c, cat in col_cat.items():
            raw = ws.cell(row=r, column=c).value
            records.append({
                "date": pd.Timestamp(cur_year, m, 1),
                "hotel_category": cat,
                "raw_value": "" if raw is None else str(raw),
                "cell_value": float(raw) if isinstance(raw, (int, float)) else float("nan"),
                "cell_is_numeric": isinstance(raw, (int, float)),
                "provisional": prov,
                "src_sheet": sheet, "src_row": r, "src_col": c,
            })
    wb.close()
    df = pd.DataFrame.from_records(records)
    df.attrs["unmapped"] = unmapped
    return df


# --------------------------------------------------------------------------- #
CAP_METRIC = {
    "establecimientos": "establishments",
    "hoteles": "establishments",
    "habitaciones o unidades disponibles": "available_room_nights",
    "plazas disponibles": "available_bed_nights",
}
CAP_MONTHS = dict(C.MONTHS_ES_UPPER)


def _cap_metric(label):
    s = norm_text(label).lower().rstrip(".")
    s = "".join(ch for ch in s if not ch.isdigit()).strip()
    for k, v in CAP_METRIC.items():
        if s.startswith(k):
            return v
    return None


def load_capacity(path):
    """`Ehoba_1_ano.xlsx` — one sheet per year, 1-4 quarterly snapshot blocks."""
    wb = openpyxl.load_workbook(path, data_only=True)
    records = []
    for sheet in wb.sheetnames:
        if not sheet.strip().isdigit():
            continue
        year = int(sheet.strip())
        ws = wb[sheet]
        taxonomy = "2008_eoh" if year == 2008 else "ehoba"
        cur_month, col_cat, band = None, {}, {}
        for r in range(1, ws.max_row + 1):
            rowvals = [ws.cell(row=r, column=c).value for c in range(1, ws.max_column + 1)]
            for v in rowvals:
                mt = norm_text(v).upper().rstrip(" .")
                if mt in CAP_MONTHS:
                    cur_month = CAP_MONTHS[mt]
                    break
            joined = " ".join(norm_text(v).lower() for v in rowvals)
            if "hoteleros" in joined and "estrellas" not in joined:
                band = _band_forward_fill(ws, r, 1, ws.max_column)
            cats = {c: canon_category(norm_text(ws.cell(row=r, column=c).value))
                    for c in range(1, ws.max_column + 1)}
            mappable = {c: v for c, v in cats.items() if v}
            if len(mappable) >= 3:
                col_cat = {}
                for c, v in mappable.items():
                    if v == "total_hoteleros" and "parahotel" in band.get(c, ""):
                        v = C.CAT_TOTAL_PARAHOTEL
                    col_cat[c] = v
                continue
            metric = _cap_metric(ws.cell(row=r, column=1).value)
            if metric and col_cat and cur_month:
                for c, cat in col_cat.items():
                    raw = ws.cell(row=r, column=c).value
                    records.append({
                        "date": pd.Timestamp(year, cur_month, 1),
                        "snapshot_month": cur_month, "hotel_category": cat,
                        "metric": metric,
                        "raw_value": "" if raw is None else str(raw),
                        "cell_value": float(raw) if isinstance(raw, (int, float)) else float("nan"),
                        "cell_is_numeric": isinstance(raw, (int, float)),
                        "source_taxonomy": taxonomy,
                        "src_sheet": sheet, "src_row": r, "src_col": c,
                    })
    wb.close()
    return (pd.DataFrame.from_records(records)
            .drop_duplicates(subset=["date", "hotel_category", "metric"]))


# --------------------------------------------------------------------------- #
CPI_REGIONS = {
    "total nacional": "total_nacional",
    "región gba": "gba", "region gba": "gba",
    "región pampeana": "pampeana", "region pampeana": "pampeana",
    "región noroeste": "noa", "region noroeste": "noa", "noa": "noa",
    "región noreste": "nea", "region noreste": "nea", "nea": "nea",
    "región cuyo": "cuyo", "region cuyo": "cuyo",
    "región patagonia": "patagonia", "region patagonia": "patagonia",
}


def _xlrd_dates(sh, r, datemode):
    out = {}
    for c in range(1, sh.ncols):
        v = sh.cell_value(r, c)
        if isinstance(v, (int, float)) and v > 30000:
            out[c] = pd.Timestamp(xlrd.xldate.xldate_as_datetime(v, datemode))
    return out


def _parse_cpi_stacked(sh, datemode, sheet_name):
    rec, region, datevec = [], None, {}
    for r in range(sh.nrows):
        a = norm_text(sh.cell_value(r, 0))
        if a.lower() in CPI_REGIONS:
            region = CPI_REGIONS[a.lower()]
            datevec = _xlrd_dates(sh, r, datemode)
            continue
        if not a or region is None or not datevec:
            continue
        vals = {c: sh.cell_value(r, c) for c in datevec
                if isinstance(sh.cell_value(r, c), (int, float))
                and sh.cell_value(r, c) != ""}
        for c, v in vals.items():
            rec.append({"src_sheet": sheet_name, "region": region,
                        "series": a, "date": datevec[c], "value": float(v)})
    return rec


def load_cpi(path):
    """`sh_ipc_08_26.xls` (legacy BIFF) -> long: src_sheet, region, series, date, value."""
    wb = xlrd.open_workbook(path)
    dm = wb.datemode
    rec = _parse_cpi_stacked(wb.sheet_by_name(C.CPI_SHEET_INDEX), dm, "index_national")
    rec += _parse_cpi_stacked(wb.sheet_by_name(C.CPI_SHEET_MOM), dm, "mom_national")
    sh = wb.sheet_by_name(C.CPI_SHEET_GBA_BRIDGE)
    for r in range(sh.nrows):
        if norm_text(sh.cell_value(r, 0)).lower() in ("descripción", "descripcion", "apertura"):
            datevec = _xlrd_dates(sh, r, dm)
            for rr in range(r + 1, sh.nrows):
                lbl = norm_text(sh.cell_value(rr, 0))
                if not lbl:
                    continue
                if lbl.lower() in ("apertura", "descripción", "descripcion"):
                    break
                for c in datevec:
                    v = sh.cell_value(rr, c)
                    if isinstance(v, (int, float)):
                        rec.append({"src_sheet": "gba_bridge", "region": "gba",
                                    "series": lbl, "date": datevec[c], "value": float(v)})
            break
    return pd.DataFrame.from_records(rec)
