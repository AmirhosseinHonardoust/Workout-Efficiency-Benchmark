from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Tuple

import numpy as np
import pandas as pd


def cliffs_delta(a: np.ndarray, b: np.ndarray) -> float:
    """
    Cliff's delta: probability that a random draw from a is greater than b
    minus probability that b is greater than a. Range [-1, 1].

    Robust effect size for non-normal distributions.
    """
    a = np.asarray(a)
    b = np.asarray(b)
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return np.nan

    gt = 0
    lt = 0
    for x in a:
        gt += np.sum(x > b)
        lt += np.sum(x < b)
    return (gt - lt) / (len(a) * len(b))


def bootstrap_diff(
    a: np.ndarray,
    b: np.ndarray,
    *,
    stat=np.median,
    n_boot: int = 1500,
    seed: int = 42,
    ci: float = 0.95,
) -> Tuple[float, float, float]:
    """
    Bootstrap CI for difference in statistic: stat(a) - stat(b).
    Returns (estimate, ci_low, ci_high).
    """
    rng = np.random.default_rng(seed)
    a = np.asarray(a)
    b = np.asarray(b)
    a = a[~np.isnan(a)]
    b = b[~np.isnan(b)]
    if len(a) == 0 or len(b) == 0:
        return np.nan, np.nan, np.nan

    est = float(stat(a) - stat(b))
    boots = []
    for _ in range(n_boot):
        aa = rng.choice(a, size=len(a), replace=True)
        bb = rng.choice(b, size=len(b), replace=True)
        boots.append(float(stat(aa) - stat(bb)))
    boots = np.sort(np.array(boots))
    alpha = (1.0 - ci) / 2.0
    lo = float(np.quantile(boots, alpha))
    hi = float(np.quantile(boots, 1.0 - alpha))
    return est, lo, hi


@dataclass
class FairnessResult:
    gaps: pd.DataFrame
    notes: Dict[str, str]

         
def group_gap_table(
    df_present: pd.DataFrame,
    group_col: str,
    *,
    min_n: int = 30,
) -> pd.DataFrame:
    """
    Compute a gap table for a group column.

    We report:
    - group median efficiency
    - overall median efficiency
    - median gap (median(group) - median(overall))
    - bootstrap CI for the gap (when sample is big enough)
    - Cliff's delta effect size
    - session count + low-sample flag
    """
    xcol = "efficiency_kcal_per_min"
    overall = df_present[xcol].to_numpy()
    overall_median = float(np.nanmedian(overall))

    rows = []
    for gval, sub in df_present.groupby(group_col, dropna=False, observed=False):
        vals = sub[xcol].to_numpy()
        n = int(np.sum(~np.isnan(vals)))

        if n < max(5, min_n // 3):
            est, lo, hi = (np.nan, np.nan, np.nan)
        else:
            est, lo, hi = bootstrap_diff(vals, overall, stat=np.median)

        cd = cliffs_delta(vals, overall)
        rows.append(
            {
                "group_col": group_col,
                "group": str(gval),
                "sessions": n,
                "median_eff": float(np.nanmedian(vals)) if n else np.nan,
                "overall_median_eff": overall_median,
                "median_gap_vs_overall": est,
                "gap_ci_low": lo,
                "gap_ci_high": hi,
                "cliffs_delta": cd,
                "low_sample_flag": bool(n < min_n),
            }
        )

    out = pd.DataFrame(rows).sort_values("median_gap_vs_overall", ascending=False, na_position="last")
    return out.reset_index(drop=True)


def run_fairness(df_present: pd.DataFrame) -> FairnessResult:
    gaps = pd.concat(
        [
            group_gap_table(df_present, "gender", min_n=40),
            group_gap_table(df_present, "age_band", min_n=40),
            group_gap_table(df_present, "membership_type", min_n=40),
        ],
        ignore_index=True,
    )

    notes = {
        "interpretation": (
            "These gaps are descriptive and fairness-aware: they show when global benchmarks can be misleading. "
            "They do NOT prove physiological causality. Large gaps suggest stratified benchmarks or controlled comparisons "
            "(workout type, time-of-day, membership mix)."
        ),
        "effect_size": (
            "Cliff's delta is a distribution-aware effect size. Rough guide: "
            "|delta| < 0.147 negligible, < 0.33 small, < 0.474 medium, otherwise large."
        ),
        "low_sample": (
            "Rows flagged as low_sample are unstable. Increase sample size or aggregate categories."
        ),
    }
    return FairnessResult(gaps=gaps, notes=notes)
