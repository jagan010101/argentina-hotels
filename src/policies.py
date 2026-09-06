"""
Reusable inflation-aware repricing-policy engine.

A *policy* is a rule that decides, month by month, the hotel's **nominal** list
rate for one Buenos Aires hotel category, using only information available at the
decision date. INDEC releases month-t CPI in mid-month t+1, so a month-t price
may use CPI through **t-1** only.  All functions here are pure (no plotting, no
IO) so they can be unit-tested and called from any notebook.

Policies implemented (PROJECT_AUDIT.md sec 5, brief Part 4):
    policy0_frozen            nominal price never changes            -> real erosion reference
    policy1_monthly_cpi       index every month by last month's CPI  -> mechanical benchmark
    policy2_threshold(tau)    hold until cumulative inflation since the last change
                              reaches tau, then reset to restore the real price
    policy3_threshold_occ(tau, delta)
                              same trigger; at each reset scale the inflation
                              catch-up by an occupancy factor
                              (high occupancy -> fuller pass-through,
                               weak occupancy -> partial pass-through)

`simulate()` returns a tidy per-month frame; scoring lives in `pricing_eval.py`.
"""
from __future__ import annotations

from dataclasses import dataclass, field

import numpy as np
import pandas as pd

MONTHS_ES_NUM = list(range(1, 13))


# --------------------------------------------------------------------------- #
# Policy specs
# --------------------------------------------------------------------------- #
@dataclass(frozen=True)
class Policy:
    name: str
    kind: str                      # "frozen" | "monthly_cpi" | "threshold" | "threshold_occ"
    tau: float = 0.0               # cumulative-inflation trigger (fraction)
    delta: float = 0.0             # occupancy tilt band (fraction), policy3 only
    label: str = ""

    def __post_init__(self):
        if not self.label:
            object.__setattr__(self, "label", self.name)


def policy0_frozen() -> Policy:
    return Policy("P0_frozen", "frozen", label="P0 · frozen nominal")


def policy1_monthly_cpi() -> Policy:
    return Policy("P1_monthly_cpi", "monthly_cpi", label="P1 · monthly CPI index")


def policy2_threshold(tau: float) -> Policy:
    return Policy(f"P2_tau{tau*100:g}", "threshold", tau=tau,
                  label=f"P2 · threshold {tau:.0%}")


def policy3_threshold_occ(tau: float, delta: float) -> Policy:
    return Policy(f"P3_tau{tau*100:g}_d{delta*100:g}", "threshold_occ",
                  tau=tau, delta=delta,
                  label=f"P3 · threshold {tau:.0%} + occ tilt {delta:.0%}")


# --------------------------------------------------------------------------- #
# Seasonal occupancy norm (fit on training data only)
# --------------------------------------------------------------------------- #
def seasonal_occ_norm(train_df: pd.DataFrame, occ_col: str = "room_occupancy") -> dict:
    """Calendar-month multiplicative occupancy factors, mean-normalised to 1."""
    g = train_df.dropna(subset=[occ_col])
    if g.empty:
        return {m: 1.0 for m in MONTHS_ES_NUM}
    fac = (g.groupby(g["date"].dt.month)[occ_col].mean() / g[occ_col].mean())
    return {m: float(fac.get(m, 1.0)) for m in MONTHS_ES_NUM}


# --------------------------------------------------------------------------- #
# Simulation
# --------------------------------------------------------------------------- #
def simulate(policy: Policy,
             cat_df: pd.DataFrame,
             window: tuple[str, str],
             *,
             occ_norm: dict | None = None,
             anchor_price: float | None = None,
             rate_col: str = "average_rate",
             occ_col: str = "room_occupancy",
             cpi_col: str = "cpi_gba",
             occ_lookback: int = 3) -> pd.DataFrame:
    """
    Roll `policy` forward over [window] for one category.

    Parameters
    ----------
    cat_df : full monthly frame for ONE category, sorted by date, spanning at
        least `occ_lookback`+1 months before `window[0]` (for the anchor and the
        occupancy history). Needs columns: date, `rate_col`, `occ_col`, `cpi_col`,
        plus a monthly-inflation column `infl_mom` in FRACTION units
        (CPI_t/CPI_{t-1}-1). If `infl_mom` is absent it is derived from `cpi_col`.
    window : (start, end) inclusive month strings.
    occ_norm : calendar-month occupancy factors from `seasonal_occ_norm` on the
        TRAINING data. Required for policy3; ignored otherwise.
    anchor_price : if given, the policy path starts here instead of at the first
        observed rate. Pass `target_real * cpi_{anchor-1} / 100` to start every
        policy at the same *real* level, so the comparison is about repricing
        timing / stability rather than the starting price level.

    Returns
    -------
    DataFrame indexed 0..n-1 over the window months with columns:
        date, P (policy nominal rate), P_obs, cpi, real_P, real_P_obs,
        occ_obs, reprice (bool), months_since_reprice, cuminf_since_reprice
    Rows whose observed rate is missing are still emitted (the policy path is
    carried forward); scoring functions drop them where needed.
    """
    s = cat_df.sort_values("date").reset_index(drop=True)
    if "infl_mom" not in s.columns:
        s = s.assign(infl_mom=s[cpi_col].pct_change())

    w0, w1 = pd.Timestamp(window[0]), pd.Timestamp(window[1])
    win_mask = (s["date"] >= w0) & (s["date"] <= w1)
    if not win_mask.any():
        return pd.DataFrame()
    i_lo = int(np.flatnonzero(win_mask.to_numpy())[0])
    i_hi = int(np.flatnonzero(win_mask.to_numpy())[-1])

    date = s["date"].to_numpy()
    cpi = s[cpi_col].to_numpy(dtype=float)
    p_obs = s[rate_col].to_numpy(dtype=float)
    occ_obs = s[occ_col].to_numpy(dtype=float)
    infl = np.nan_to_num(s["infl_mom"].to_numpy(dtype=float))
    month = s["date"].dt.month.to_numpy()

    # anchor at the first month in the window with an observed rate
    anchor_candidates = np.flatnonzero(np.isfinite(p_obs[i_lo:i_hi + 1]))
    if len(anchor_candidates) == 0:
        return pd.DataFrame()
    a = i_lo + int(anchor_candidates[0])

    P = np.full(len(s), np.nan)
    P[a] = float(anchor_price) if anchor_price is not None else p_obs[a]
    last_reprice_i = a
    cpi_at_last_reprice = cpi[a - 1] if a >= 1 and np.isfinite(cpi[a - 1]) else cpi[a]
    reprice_flag = np.zeros(len(s), dtype=bool)
    reprice_flag[a] = True
    msr = np.zeros(len(s), dtype=float)
    cuminf = np.zeros(len(s), dtype=float)

    for i in range(a + 1, i_hi + 1):
        cpi_known = cpi[i - 1]                      # info <= t-1
        infl_known = infl[i - 1]
        prev = P[i - 1]
        if not np.isfinite(prev):                   # carry through a data gap
            fin = P[:i][np.isfinite(P[:i])]
            prev = fin[-1] if len(fin) else p_obs[a]

        cum = (cpi_known / cpi_at_last_reprice - 1.0) if np.isfinite(cpi_known) else 0.0
        cuminf[i] = cum
        msr[i] = i - last_reprice_i

        if policy.kind == "frozen":
            P[i] = P[a]

        elif policy.kind == "monthly_cpi":
            P[i] = prev * (1.0 + infl_known)
            reprice_flag[i] = abs(infl_known) > 1e-9

        elif policy.kind in ("threshold", "threshold_occ"):
            if cum >= policy.tau:
                base = P[last_reprice_i] * (cpi_known / cpi_at_last_reprice)   # restore real value
                if policy.kind == "threshold_occ":
                    lo = max(0, i - occ_lookback)
                    occ_trail = np.nanmean(occ_obs[lo:i])
                    norm = (occ_norm or {}).get(int(month[i]), 1.0)
                    ref = np.nanmean(occ_obs[:i][np.isfinite(occ_obs[:i])][-24:]) if i > 0 else occ_trail
                    ref = ref if np.isfinite(ref) and ref > 0 else occ_trail
                    # deviation of trailing occupancy from its seasonal norm, in [-1,1]
                    dev = np.tanh(((occ_trail / max(ref, 1e-6)) - norm) / max(norm, 1e-6) * 4)
                    tilt = 1.0 + policy.delta * dev
                    P[i] = base * tilt
                else:
                    P[i] = base
                reprice_flag[i] = True
                last_reprice_i = i
                cpi_at_last_reprice = cpi_known
                msr[i] = 0.0
                cuminf[i] = 0.0
            else:
                P[i] = prev
        else:
            raise ValueError(f"unknown policy kind {policy.kind!r}")

    idx = slice(a, i_hi + 1)
    out = pd.DataFrame({
        "date": date[idx],
        "P": P[idx],
        "P_obs": p_obs[idx],
        "cpi": cpi[idx],
        "occ_obs": occ_obs[idx],
        "reprice": reprice_flag[idx],
        "months_since_reprice": msr[idx],
        "cuminf_since_reprice": cuminf[idx],
    })
    out["real_P"] = out["P"] / out["cpi"] * 100.0
    out["real_P_obs"] = out["P_obs"] / out["cpi"] * 100.0
    return out.reset_index(drop=True)


def observed_path(cat_df: pd.DataFrame, window: tuple[str, str], **kw) -> pd.DataFrame:
    """What the hotels actually did, in the same frame shape as `simulate`."""
    s = cat_df.sort_values("date")
    w0, w1 = pd.Timestamp(window[0]), pd.Timestamp(window[1])
    s = s[(s["date"] >= w0) & (s["date"] <= w1)].copy()
    rate_col = kw.get("rate_col", "average_rate")
    occ_col = kw.get("occ_col", "room_occupancy")
    cpi_col = kw.get("cpi_col", "cpi_gba")
    d = pd.DataFrame({
        "date": s["date"].to_numpy(),
        "P": s[rate_col].to_numpy(dtype=float),
        "P_obs": s[rate_col].to_numpy(dtype=float),
        "cpi": s[cpi_col].to_numpy(dtype=float),
        "occ_obs": s[occ_col].to_numpy(dtype=float),
    })
    d["reprice"] = np.r_[True, np.abs(np.diff(d["P"].to_numpy())) > 1e-6] & np.isfinite(d["P"])
    d["months_since_reprice"] = np.nan
    d["cuminf_since_reprice"] = np.nan
    d["real_P"] = d["P"] / d["cpi"] * 100.0
    d["real_P_obs"] = d["real_P"]
    return d.reset_index(drop=True)
