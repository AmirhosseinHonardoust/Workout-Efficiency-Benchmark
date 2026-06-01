from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
 

def _ensure_dir(p: Path) -> None:
    p.mkdir(parents=True, exist_ok=True)


def plot_efficiency_by_workout_type(df_present: pd.DataFrame, outpath: Path) -> None:
    _ensure_dir(outpath.parent)

    order = (
        df_present.groupby("workout_type")["efficiency_kcal_per_min"]
        .median()
        .sort_values(ascending=False)
        .index.tolist()
    )
    data = [df_present.loc[df_present["workout_type"] == w, "efficiency_kcal_per_min"].values for w in order]

    plt.figure(figsize=(11, 6))
    plt.boxplot(data, labels=order, showfliers=False)
    plt.xticks(rotation=30, ha="right")
    plt.ylabel("Efficiency (kcal/min)")
    plt.title("Workout Efficiency Distribution by Workout Type (Present sessions only)")
    plt.tight_layout()
    plt.savefig(outpath, dpi=180)
    plt.close()


def plot_calories_vs_duration(df_present: pd.DataFrame, outpath: Path) -> None:
    _ensure_dir(outpath.parent)

    plt.figure(figsize=(8.5, 6))
    plt.scatter(
        df_present["workout_duration_minutes"].values,
        df_present["calories_burned"].values,
        s=14,
        alpha=0.35,
    )
    plt.xlabel("Workout duration (minutes)")
    plt.ylabel("Calories burned")
    plt.title("Calories vs Duration (Present sessions)")
    plt.tight_layout()
    plt.savefig(outpath, dpi=180)
    plt.close()


def plot_heatmap_efficiency_workout_gender(df_present: pd.DataFrame, outpath: Path) -> None:
    _ensure_dir(outpath.parent)

    pivot = df_present.pivot_table(
        index="workout_type",
        columns="gender",
        values="efficiency_kcal_per_min",
        aggfunc="mean",
        observed=False,
    )
    counts = df_present.pivot_table(
        index="workout_type",
        columns="gender",
        values="efficiency_kcal_per_min",
        aggfunc="count",
        observed=False,
    )

    fig, ax = plt.subplots(figsize=(9.5, 6))
    im = ax.imshow(pivot.values, aspect="auto")
    ax.set_xticks(range(pivot.shape[1]))
    ax.set_xticklabels(pivot.columns.tolist(), rotation=0)
    ax.set_yticks(range(pivot.shape[0]))
    ax.set_yticklabels(pivot.index.tolist())

    for i in range(pivot.shape[0]):
        for j in range(pivot.shape[1]):
            v = pivot.values[i, j]
            n = counts.values[i, j]
            if np.isfinite(v):
                ax.text(j, i, f"{v:.2f}\n(n={int(n)})", ha="center", va="center", fontsize=8)

    ax.set_title("Mean Efficiency (kcal/min) by Workout Type × Gender")
    cbar = fig.colorbar(im, ax=ax)
    cbar.set_label("Mean kcal/min")
    plt.tight_layout()
    plt.savefig(outpath, dpi=180)
    plt.close()


def plot_efficiency_by_age_band(df_present: pd.DataFrame, outpath: Path) -> None:
    _ensure_dir(outpath.parent)

    stats = (
        df_present.groupby("age_band", dropna=False, observed=False)["efficiency_kcal_per_min"]
        .agg(["count", "median"])
        .reset_index()
    )

    rng = np.random.default_rng(7)
    ci_lo = []
    ci_hi = []
    for _, row in stats.iterrows():
        band = row["age_band"]
        vals = df_present.loc[df_present["age_band"] == band, "efficiency_kcal_per_min"].dropna().values
        if len(vals) < 25:
            ci_lo.append(np.nan)
            ci_hi.append(np.nan)
            continue
        boots = []
        for _ in range(800):
            samp = rng.choice(vals, size=len(vals), replace=True)
            boots.append(np.median(samp))
        boots = np.sort(np.array(boots))
        ci_lo.append(float(np.quantile(boots, 0.025)))
        ci_hi.append(float(np.quantile(boots, 0.975)))

    stats["ci_low"] = ci_lo
    stats["ci_high"] = ci_hi

    plt.figure(figsize=(9, 5.3))
    x = np.arange(len(stats))
    y = stats["median"].values
    plt.plot(x, y, marker="o")
    for i in range(len(stats)):
        lo = stats["ci_low"].iloc[i]
        hi = stats["ci_high"].iloc[i]
        if np.isfinite(lo) and np.isfinite(hi):
            plt.vlines(i, lo, hi)

    plt.xticks(x, stats["age_band"].astype(str).tolist())
    plt.ylabel("Median efficiency (kcal/min)")
    plt.title("Median Workout Efficiency by Age Band (bootstrap CI when available)")
    plt.tight_layout()
    plt.savefig(outpath, dpi=180)
    plt.close()
