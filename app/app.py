import sys
import json
import base64
from pathlib import Path

import pandas as pd
import streamlit as st
import plotly.express as px

PROJECT_ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(PROJECT_ROOT))

from src.pipeline import run as run_pipeline  # noqa: E402


def _img_fixed(path: Path, caption: str, height_px: int = 340) -> None:
    """Fixed-height image tile for clean grids."""
    if not path.exists():
        st.warning(f"Missing figure: {path.name}")
        return
    b64 = base64.b64encode(path.read_bytes()).decode("utf-8")
    st.markdown(
        f"""
        <div style="border:1px solid rgba(49,51,63,0.15); border-radius:14px; padding:10px; background:white;">
          <img src="data:image/png;base64,{b64}" style="width:100%; height:{height_px}px; object-fit:contain; display:block;" />
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.caption(caption)


st.set_page_config(page_title="Workout Efficiency Benchmark Report", layout="wide")
st.title("Workout Efficiency Benchmark Report")
st.caption("Calories/min benchmarks + fairness-aware comparisons (present sessions only).")

DEFAULT_INPUT = PROJECT_ROOT / "data" / "raw" / "daily_gym_attendance_workout_data.csv"
OUT_DIR = PROJECT_ROOT / "outputs"
FIG_DIR = PROJECT_ROOT / "reports" / "figures"

with st.sidebar:
    st.header("Pipeline")
    uploaded = st.file_uploader("Upload CSV (optional)", type=["csv"])
    input_path = st.text_input("Or CSV path", value=str(DEFAULT_INPUT))
    fig_height = st.slider("Figure tile height", 260, 560, 360, 10)
    run_btn = st.button("Run / Refresh", type="primary")

effective_input = Path(input_path)
if uploaded is not None:
    tmp = PROJECT_ROOT / "data" / "raw" / "uploaded.csv"
    tmp.parent.mkdir(parents=True, exist_ok=True)
    tmp.write_bytes(uploaded.getbuffer())
    effective_input = tmp

if run_btn:
    with st.spinner("Building benchmark report..."):
        run_pipeline(
            input_path=str(effective_input),
            out_dir=str(OUT_DIR),
            figures_dir=str(FIG_DIR),
        )
    st.success("✅ Done! Outputs + figures refreshed.")

bench_path = OUT_DIR / "benchmark_table.csv"
gaps_path = OUT_DIR / "fairness_gaps.csv"
dq_path = OUT_DIR / "data_quality_report.json"
meta_path = OUT_DIR / "run_metadata.json"

if not bench_path.exists():
    st.info("Run the pipeline from the sidebar to generate the benchmark report.")
    st.stop()

bench = pd.read_csv(bench_path)
gaps = pd.read_csv(gaps_path) if gaps_path.exists() else pd.DataFrame()
dq = json.loads(dq_path.read_text(encoding="utf-8")) if dq_path.exists() else {}
meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}

tab_report, tab_bench, tab_fair, tab_dq, tab_notes = st.tabs(
    ["Report", "Benchmarks", "Fairness", "Data Quality", "Notes"]
)

with tab_report:
    st.subheader("Executive summary")
    c1, c2, c3, c4 = st.columns(4)
    c1.metric("Raw rows", f'{meta.get("rows_raw","-")}')
    c2.metric("Present sessions used", f'{meta.get("rows_present_used","-")}')
    c3.metric("Present rate used", f'{meta.get("present_rate_used",0):.2f}')
    c4.metric("Workout types", f'{bench["workout_type"].nunique()}')

    st.markdown("### Top workout types by median efficiency (kcal/min)")
    top = bench[["workout_type", "sessions", "median_eff_kcal_min", "iqr_eff"]].head(8)
    st.dataframe(top, width="stretch", hide_index=True)

    st.subheader("Figures")
    r1 = st.columns(2, gap="large")
    with r1[0]:
        _img_fixed(FIG_DIR / "efficiency_by_workout_type.png", "Efficiency distribution by workout type", height_px=fig_height)
    with r1[1]:
        _img_fixed(FIG_DIR / "calories_vs_duration.png", "Calories vs duration (present sessions)", height_px=fig_height)

    r2 = st.columns(2, gap="large")
    with r2[0]:
        _img_fixed(FIG_DIR / "heatmap_efficiency_workout_gender.png", "Mean efficiency by workout type × gender", height_px=fig_height)
    with r2[1]:
        _img_fixed(FIG_DIR / "efficiency_by_age_band.png", "Median efficiency by age band (with CI when available)", height_px=fig_height)

with tab_bench:
    st.subheader("Workout benchmarks (sortable)")
    st.dataframe(bench, width="stretch", hide_index=True)

    st.markdown("### Explore distributions")
    workout = st.selectbox("Workout type", sorted(bench["workout_type"].unique().tolist()))
    df = pd.read_csv(effective_input)
    present = df["attendance_status"].astype(str).str.lower().eq("present")
    dfp = df.loc[present].copy()
    dfp["efficiency_kcal_per_min"] = dfp["calories_burned"] / dfp["workout_duration_minutes"]
    dfp = dfp[dfp["workout_type"].astype(str).str.strip() == workout]

    if not dfp.empty:
        fig = px.histogram(dfp, x="efficiency_kcal_per_min", nbins=35, title=f"Efficiency distribution — {workout}")
        st.plotly_chart(fig, width="stretch")

        fig2 = px.box(dfp, x="gender", y="efficiency_kcal_per_min", points="outliers", title="Efficiency by gender (within workout)")
        st.plotly_chart(fig2, width="stretch")
    else:
        st.info("No rows found for this workout type in present sessions.")

with tab_fair:
    st.subheader("Fairness-aware gap analysis")
    st.caption("Gaps are descriptive: they show when global benchmarks can mislead. Use effect sizes and sample flags.")

    if gaps.empty:
        st.info("Fairness gaps not found. Re-run pipeline.")
    else:
        col = st.selectbox("Group dimension", sorted(gaps["group_col"].unique().tolist()))
        sub = gaps[gaps["group_col"] == col].copy()
        st.dataframe(sub, width="stretch", hide_index=True)

        sub2 = sub.sort_values("median_gap_vs_overall", ascending=False)
        fig = px.bar(
            sub2,
            x="group",
            y="median_gap_vs_overall",
            color="low_sample_flag",
            title=f"Median efficiency gap vs overall — {col}",
            labels={"median_gap_vs_overall": "Median gap (kcal/min)"},
        )
        st.plotly_chart(fig, width="stretch")

        st.markdown(
            """
### How to interpret gaps
- **Positive gap**: this group's median efficiency is above the overall median.
- **Negative gap**: below overall.
- **Low sample** rows are unstable — treat as exploratory.
- **Cliff's delta** is an effect size that reflects distribution separation.
            """.strip()
        )

with tab_dq:
    st.subheader("Data quality report")
    if not dq:
        st.info("No data quality report found.")
    else:
        st.json(dq)
        st.markdown(
            """
### What to do with inconsistencies?
If `absent_with_activity_rate` is high, two reasonable options exist:

1) **Treat Absent rows as scheduled-but-not-attended**  
   - keep for attendance analytics  
   - exclude from efficiency benchmarks (recommended)

2) **Treat Absent rows as mislabeled** (only if justified)  
   - relabel/filter using stronger rules  
   - document the decision in the report

This project uses option (1) by default.
            """.strip()
        )

with tab_notes:
    st.markdown(
        """
## Notes
- This report focuses on **fair benchmarking**, not medical inference.
- Efficiency (kcal/min) is interpretable, but influenced by many confounders.
- Treat segment gaps as a warning against unfair comparisons, not as proof of causality.

## Next upgrades (if you want to go deeper)
- Add a regression adjustment layer (control for workout type + time-of-day).
- Add trend analysis (monthly changes in efficiency per workout type).
- Add personal baselines (compare each member to themselves over time).
        """.strip()
    )
