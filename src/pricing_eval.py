"""
Scoring for repricing policies + Pareto / lambda-objective helpers.

Companion to `policies.py`. Everything is pure. The counterfactual demand
response uses a constant-elasticity form with an **assumed** beta (occupancy is
inelastic and not causally identified -- always report across `BETA_SCENARIOS`):

    occ_cf_t = occ_obs_t * (P_policy_t / P_obs_t) ** beta
    revpar_t = P_policy_t * occ_cf_t / 100          # RevPAR proxy, nominal pesos

No marginal-cost data -> we never claim a profit- or revenue-maximising price.
We compare policies on the frequency / real-stability / occupancy / revenue
trade-off and report the Pareto frontier.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


# --------------------------------------------------------------------------- #
def target_real_rate(cat_df: pd.DataFrame,
                     ref: tuple[str, str] = ("2018-01-01", "2019-12-01"),
                     rate_col: str = "average_rate",
                     cpi_col: str = "cpi_gba") -> float:
    """Pre-shock real-rate anchor: mean observed real rate over `ref`
    (default: the full 2018-19 pre-COVID period)."""
    s = cat_df.copy()
    real = s[rate_col] / s[cpi_col] * 100.0
    m = (s["date"] >= pd.Timestamp(ref[0])) & (s["date"] <= pd.Timestamp(ref[1]))
    v = real[m].dropna()
    if len(v) >= 6:
        return float(v.mean())
    pre = real[s["date"] < "2020-01-01"].dropna()
    return float(pre.tail(24).mean())


# --------------------------------------------------------------------------- #
def counterfactual(path: pd.DataFrame, beta: float) -> pd.DataFrame:
    d = path.copy()
    with np.errstate(invalid="ignore", divide="ignore"):
        ratio = d["P"] / d["P_obs"]
        d["occ_cf"] = d["occ_obs"] * ratio ** beta
    d["revpar"] = d["P"] * d["occ_cf"] / 100.0
    d["revpar_obs"] = d["P_obs"] * d["occ_obs"] / 100.0
    return d


# --------------------------------------------------------------------------- #
def score(path: pd.DataFrame, beta: float, target_real: float) -> dict:
    """One row of policy metrics for a simulated path over an eval window."""
    d = counterfactual(path, beta).dropna(subset=["P", "P_obs", "occ_obs", "cpi"])
    if len(d) < 3:
        return {k: np.nan for k in _COLS}
    tgt = target_real
    rp = d["real_P"].to_numpy()
    rev = d["revpar"].to_numpy()
    rev_obs = d["revpar_obs"].to_numpy()
    dP = np.diff(d["P"].to_numpy())
    dP_pct = np.abs(dP) / d["P"].to_numpy()[:-1]
    n_repr = int(d["reprice"].sum()) if d["reprice"].dtype == bool else int(
        (np.r_[True, np.abs(dP) > 1e-6]).sum())
    cum = np.cumsum(rev)
    run_max = np.maximum.accumulate(cum)
    dd = (cum - run_max) / np.where(run_max == 0, np.nan, run_max)

    reldev = rp / tgt - 1.0                      # real-price deviation from target
    return dict(
        n_months=len(d),
        n_reprice=n_repr,
        reprice_rate=n_repr / len(d),
        mean_abs_price_change_pct=float(np.nanmean(dP_pct) * 100) if len(dP_pct) else 0.0,
        share_price_up=float(np.mean(dP > 0)) if len(dP) else np.nan,
        mean_real_P=float(np.mean(rp)),
        real_P_cv_pct=float(np.std(rp) / np.mean(rp) * 100),
        real_dev_mean_pct=float(np.mean(reldev) * 100),          # + = above target
        real_dev_min_pct=float(np.min(reldev) * 100),            # most eroded month
        real_dev_max_pct=float(np.max(reldev) * 100),            # most overshot month
        mean_abs_real_dev_pct=float(np.mean(np.abs(reldev)) * 100),
        months_5pct_below_target=int(np.sum(rp < 0.95 * tgt)),
        mean_occ=float(np.nanmean(d["occ_cf"])),
        total_revpar=float(np.sum(rev)),
        mean_revpar=float(np.mean(rev)),
        revpar_cv_pct=float(np.std(rev) / np.mean(rev) * 100),
        revpar_max_drawdown_pct=float(np.nanmin(dd) * 100) if np.isfinite(np.nanmin(dd)) else 0.0,
        revpar_vs_obs_pct=float(np.sum(rev) / np.sum(rev_obs) - 1) * 100,
        cum_revpar=float(cum[-1]),
    )


_COLS = ["n_months", "n_reprice", "reprice_rate", "mean_abs_price_change_pct",
         "share_price_up", "mean_real_P", "real_P_cv_pct", "real_dev_mean_pct",
         "real_dev_min_pct", "real_dev_max_pct", "mean_abs_real_dev_pct",
         "months_5pct_below_target", "mean_occ", "total_revpar", "mean_revpar",
         "revpar_cv_pct", "revpar_max_drawdown_pct", "revpar_vs_obs_pct", "cum_revpar"]


# --------------------------------------------------------------------------- #
def objective(score_row: dict | pd.Series, lam: float) -> float:
    """Objective = total RevPAR - lam * N_reprice * (mean monthly RevPAR).

    `lam` is a fraction of mean monthly revenue charged per repricing event; it
    is an operational dial, NOT a calibrated monetary cost. Report the whole
    LAMBDA_GRID / the Pareto frontier, not a single lam.
    """
    return float(score_row["total_revpar"]
                 - lam * score_row["n_reprice"] * score_row["mean_revpar"])


# --------------------------------------------------------------------------- #
def pareto_mask(df: pd.DataFrame, xcol: str, ycol: str,
                minimise_x: bool = True, maximise_y: bool = True) -> np.ndarray:
    """Boolean mask of Pareto-efficient rows for the (x, y) objective pair."""
    x = df[xcol].to_numpy(dtype=float)
    y = df[ycol].to_numpy(dtype=float)
    xs = x if minimise_x else -x
    ys = y if maximise_y else -y
    n = len(df)
    eff = np.ones(n, dtype=bool)
    for i in range(n):
        if not np.isfinite(xs[i]) or not np.isfinite(ys[i]):
            eff[i] = False
            continue
        dominated = (xs <= xs[i]) & (ys >= ys[i]) & ((xs < xs[i]) | (ys > ys[i]))
        if dominated.any():
            eff[i] = False
    return eff
