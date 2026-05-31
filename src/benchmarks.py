from __future__ import annotations

import pandas as pd
  
 
def workout_type_benchmarks(df_present: pd.DataFrame) -> pd.DataFrame:
    """
    Build a benchmark table per workout_type using robust + interpretable stats.
    """
    g = df_present.groupby("workout_type", dropna=False)

    bench = g.agg(
        sessions=("workout_type", "size"),
        members=("member_id", "nunique"),
        mean_duration_min=("workout_duration_minutes", "mean"),
        median_duration_min=("workout_duration_minutes", "median"),
        mean_calories=("calories_burned", "mean"),
        median_calories=("calories_burned", "median"),
        mean_eff_kcal_min=("efficiency_kcal_per_min", "mean"),
        median_eff_kcal_min=("efficiency_kcal_per_min", "median"),
        p25_eff=("efficiency_kcal_per_min", lambda x: x.quantile(0.25)),
        p75_eff=("efficiency_kcal_per_min", lambda x: x.quantile(0.75)),
    ).reset_index()

    bench["iqr_eff"] = bench["p75_eff"] - bench["p25_eff"]
    bench = bench.sort_values("median_eff_kcal_min", ascending=False).reset_index(drop=True)
    return bench
