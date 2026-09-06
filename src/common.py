"""Shared helpers: audit-trail logging and small parsing utilities."""
from __future__ import annotations

import re
import unicodedata
from pathlib import Path

import pandas as pd

import config as C


# --------------------------------------------------------------------------- #
# Audit trail
# --------------------------------------------------------------------------- #
class AuditLog:
    """Accumulates one row per cleaning decision and appends to a shared CSV."""

    def __init__(self, step: str):
        self.step = step
        self.rows: list[dict] = []

    def log(self, action: str, target: str, n_obs: int | str = "", detail: str = ""):
        self.rows.append(
            {"step": self.step, "action": action, "target": target,
             "n_obs": n_obs, "detail": detail}
        )
        print(f"  [{self.step}] {action:<22} {target:<32} {n_obs!s:>8}  {detail}")

    def flush(self, path: Path = C.P_AUDIT_LOG):
        """Idempotent: replace any existing rows for this step, keep the rest,
        and re-order so steps appear in run order (01, 02, 03, ...)."""
        cols = ["step", "action", "target", "n_obs", "detail"]
        new = pd.DataFrame(self.rows, columns=cols)
        if path.exists():
            old = pd.read_csv(path, dtype=str).query("step != @self.step")
            out = pd.concat([old, new], ignore_index=True)
        else:
            out = new
        out = out.sort_values("step", kind="stable")
        out.to_csv(path, index=False)


# --------------------------------------------------------------------------- #
# Text / token helpers
# --------------------------------------------------------------------------- #
def strip_accents(s: str) -> str:
    return "".join(c for c in unicodedata.normalize("NFKD", s)
                   if not unicodedata.combining(c))


def norm_text(v) -> str:
    """Lower-case, collapse whitespace, drop a trailing footnote digit/asterisk."""
    if v is None:
        return ""
    s = str(v).replace("\xa0", " ").strip()
    s = re.sub(r"\s+", " ", s)
    return s


def is_na_token(v) -> bool:
    if v is None:
        return True
    if isinstance(v, float) and pd.isna(v):
        return True
    s = str(v).strip().lower()
    return s in C.NA_TOKENS


def to_number(v):
    """Coerce a cell to float; NA tokens and unparseable text -> NaN.

    The EHOBA and INDEC spreadsheets use '.' as the decimal separator and no
    thousands separator inside data cells, so parsing is deliberately simple.
    Returns (value, was_na_token, was_unparseable).
    """
    if isinstance(v, (int, float)):
        f = float(v)
        return (f if pd.notna(f) else float("nan"), pd.isna(f), False)
    if is_na_token(v):
        return (float("nan"), True, False)
    s = str(v).strip().replace("*", "").replace("\xa0", "").replace(" ", "")
    s = s.replace(",", "")           # stray grouping commas only; no decimal commas here
    try:
        return (float(s), False, False)
    except ValueError:
        return (float("nan"), False, True)


def year_from_label(v) -> int | None:
    """'2020a', ' 2019 ', '2013*' -> int year, else None."""
    if v is None:
        return None
    s = re.sub(r"[^0-9]", "", str(v))
    if len(s) == 4 and s.isdigit():
        y = int(s)
        if 2000 <= y <= 2035:
            return y
    return None


def month_from_label(v) -> int | None:
    s = norm_text(v).lower().replace("*", "").strip()
    if not s:
        return None
    key = s.split()[0]
    return C.MONTHS_ES.get(key)


def canon_category(raw_header: str) -> str | None:
    s = norm_text(raw_header).lower().replace("*", " ").strip()
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"(\d)$", "", s).strip()      # drop trailing footnote digit
    return C.CATEGORY_CANON.get(s)
