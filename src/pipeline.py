from __future__ import annotations

import argparse
import json
from pathlib import Path

import pandas as pd

from .benchmarks import workout_type_benchmarks
from .clean import clean_and_features
from .fairness import run_fairness
from .plots import (
    plot_calories_vs_duration,
    plot_efficiency_by_age_band,
    plot_efficiency_by_workout_type,
    plot_heatmap_efficiency_workout_gender,
)


def run(input_path: str, out_dir: str, figures_dir: str) -> dict:
    input_path = str(input_path)
    out_dir_p = Path(out_dir)
    fig_dir_p = Path(figures_dir)
    out_dir_p.mkdir(parents=True, exist_ok=True)
    fig_dir_p.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(input_path)

    clean_res = clean_and_features(df)
    df_present = clean_res.df_present

    bench = workout_type_benchmarks(df_present)
    fair = run_fairness(df_present)

    bench_path = out_dir_p / "benchmark_table.csv"
    bench.to_csv(bench_path, index=False)

    gaps_path = out_dir_p / "fairness_gaps.csv"
    fair.gaps.to_csv(gaps_path, index=False)

    dq_path = out_dir_p / "data_quality_report.json"
    dq_path.write_text(json.dumps(clean_res.quality, indent=2), encoding="utf-8")

    meta = {
        "input_path": input_path,
        "rows_raw": int(clean_res.quality.get("rows", len(df))),
        "rows_present_used": int(clean_res.quality.get("present_rows_used", len(df_present))),
        "present_rate_used": float(clean_res.quality.get("present_rate_used", 0.0)),
        "figures_dir": str(fig_dir_p),
        "outputs_dir": str(out_dir_p),
        "notes": fair.notes,
    }
    (out_dir_p / "run_metadata.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")

    plot_efficiency_by_workout_type(df_present, fig_dir_p / "efficiency_by_workout_type.png")
    plot_calories_vs_duration(df_present, fig_dir_p / "calories_vs_duration.png")
    plot_heatmap_efficiency_workout_gender(df_present, fig_dir_p / "heatmap_efficiency_workout_gender.png")
    plot_efficiency_by_age_band(df_present, fig_dir_p / "efficiency_by_age_band.png")

    return {
        "outputs": {
            "benchmark_table": str(bench_path),
            "fairness_gaps": str(gaps_path),
            "data_quality_report": str(dq_path),
            "run_metadata": str(out_dir_p / "run_metadata.json"),
        },
        "figures": {
            "efficiency_by_workout_type": str(fig_dir_p / "efficiency_by_workout_type.png"),
            "calories_vs_duration": str(fig_dir_p / "calories_vs_duration.png"),
            "heatmap_efficiency_workout_gender": str(fig_dir_p / "heatmap_efficiency_workout_gender.png"),
            "efficiency_by_age_band": str(fig_dir_p / "efficiency_by_age_band.png"),
        },
        "meta": meta,
    }


def main() -> None:
    p = argparse.ArgumentParser(description="Workout efficiency benchmark pipeline")
    p.add_argument("--input", required=True, help="Path to daily gym attendance CSV")
    p.add_argument("--out-dir", default="outputs", help="Output directory for CSV/JSON artifacts")
    p.add_argument("--figures-dir", default="reports/figures", help="Directory for generated figures")
    args = p.parse_args()

    res = run(args.input, args.out_dir, args.figures_dir)

    print("\nDone! Benchmark report created.")
    print(f"Outputs: {args.out_dir}")
    print(f"Figures: {args.figures_dir}")
    print(f"Present sessions used: {res['meta']['rows_present_used']} (rate≈{res['meta']['present_rate_used']:.2f})")


if __name__ == "__main__":
    main()
