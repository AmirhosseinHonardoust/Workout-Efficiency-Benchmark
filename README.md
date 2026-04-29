<div align="center">

# Workout Efficiency Benchmark Report  
**Calories per Minute (kcal/min) + fairness-aware comparisons (present sessions only)**
<p align="center">
  <img src="https://img.shields.io/badge/Python-3.10%2B-blue" alt="Python"/>
  <img src="https://img.shields.io/badge/Streamlit-App-FF4B4B" alt="Streamlit"/>
  <img src="https://img.shields.io/badge/Pandas-Data%20Wrangling-150458" alt="Pandas"/>
  <img src="https://img.shields.io/badge/Plotly-Interactive%20Charts-3F4F75" alt="Plotly"/>
  <img src="https://img.shields.io/badge/Status-Report%20Ready-success" alt="Status"/>
</p>
<p align="center">
  A decision-safe benchmarking report for gym activity data: <b>efficiency</b>, <b>distributions</b>, <b>segment gaps</b>, and <b>data quality</b>, shipped as a reproducible pipeline + a Streamlit dashboard.
</p>
 
</div>

---

## Why this project exists

**“Calories burned” alone is not a benchmark.**  
If one person burns 600 kcal in 60 minutes and another burns 600 kcal in 120 minutes, they produced the same total output but **very different efficiency**.

This project turns a noisy workout dataset into a **fairer** and **more interpretable** report by:

- Defining a simple benchmark metric: **efficiency = calories / minute**
- Comparing workout types on **robust statistics** (median + IQR, not just means)
- Showing how “global benchmarks” can mislead when segments differ
- Adding **fairness-aware “gap analysis”** with uncertainty + low-sample flags
- Producing a clean, navigable **Streamlit dashboard** and reproducible outputs

> This is **not medical advice** and not a physiological claim. It’s a **data product**: benchmarking and analytics.

---

## What you get (outputs)

When you run the pipeline, you get:

- **Figures** saved to: `reports/figures/`
- **Structured outputs** (JSON/CSV) saved to: `outputs/`
- A **Streamlit dashboard** to explore report + benchmarks + fairness + data quality

Example pipeline log (typical):
- Outputs: `outputs/`
- Figures: `reports/figures/`
- Present sessions used: `1250` (present rate ≈ `0.48`)

The report intentionally focuses on **present sessions only** so the efficiency metric stays meaningful.

---

## Metric definition (the core idea)

### Efficiency (kcal/min)

<img width="410" height="82" alt="Screenshot 2026-02-17 at 14-27-03 Math Equation Representation" src="https://github.com/user-attachments/assets/d238bade-ebb4-4b79-91e2-f1d11370ca56" />

Why this works:
- Normalizes for time (60 min vs 120 min become comparable)
- More stable as a *benchmarking* measure than raw calories
- Still interpretable: **“How many calories per minute did this session yield?”**

What it **does not** mean:
- It does **not** measure “fitness” or “effort” directly
- It is affected by confounders (intensity, body mass, workout goal, device error, etc.)

---

## Dataset notes (how the pipeline interprets rows)

Typical fields used:
- `visit_date`, `check_in_time`
- `workout_type`
- `workout_duration_minutes`
- `calories_burned`
- `gender`, `age`, `membership_type`
- A presence/attendance signal inferred from the row content

### “Present sessions only” rule
Efficiency is computed only when:
- duration is valid and > 0
- calories are valid and > 0
- the session is treated as **present**

Rows that look like “absent but still have activity fields” are handled via a **data quality report** (see below). The default behavior is conservative: **do not mix ambiguous/absent rows into efficiency benchmarking**.

---

## Quickstart

### 1) Install
```bash
pip install -r requirements.txt
````

### 2) Run the report pipeline

```bash
python -m src.pipeline --input data/raw/daily_gym_attendance_workout_data.csv
```

### 3) Launch the dashboard

```bash
streamlit run app/app.py
```

---

## Project structure

```text
workout-efficiency-benchmark/
├─ app/
│  └─ app.py
├─ data/
│  └─ raw/
│     └─ daily_gym_attendance_workout_data.csv
├─ outputs/
│  ├─ (report JSON/CSV artifacts written here)
├─ reports/
│  └─ figures/
│     ├─ calories_vs_duration.png
│     ├─ efficiency_by_age_band.png
│     ├─ efficiency_by_workout_type.png
│     └─ heatmap_efficiency_workout_gender.png
└─ src/
   ├─ pipeline.py
   ├─ clean.py
   ├─ fairness.py
   └─ plots.py
```

---

## Streamlit dashboard: what each tab is for

Below are the dashboard sections you captured. The goal is to keep a “decision-safe narrative”: **what we measured → how reliable it is → where comparisons break → what to do next**.

> Tip: Put your dashboard screenshots in `reports/screenshots/` and keep the file names stable, so the README stays evergreen.

### 1) Report

This is the “one-screen summary” you’d show to a stakeholder:

* total rows processed
* present sessions used (and present rate)
* number of workout types
* top workout types by **median efficiency**
* the core figures in a clean grid

<img width="1689" height="922" alt="Screenshot 2026-02-17 at 12-41-22 Workout Efficiency Benchmark Report" src="https://github.com/user-attachments/assets/d55ee3db-5027-4f0b-98c6-e27041c9328c" />

**How to read this page**

* If present rate is low (example: 0.48), it’s a warning: benchmarks are only for the subset that truly represents workouts.
* Rankings use **median efficiency**, not mean, because workout data usually has skew and outliers.

---

### 2) Benchmarks (sortable table + distribution exploration)

This is your “analyst workbench”:

* A sortable table summarizing each workout type:

  * sessions, members
  * duration stats (mean/median)
  * calories stats (mean/median)
  * efficiency stats (mean/median)
  * spread stats (IQR, percentiles)
* Distribution exploration:

  * efficiency histogram for a workout type
  * box/violin plots by segments (e.g., gender within a workout type)

<img width="1695" height="936" alt="Screenshot 2026-02-17 at 12-41-35 Workout Efficiency Benchmark Report" src="https://github.com/user-attachments/assets/c6024117-3f47-4e56-900f-e7f310970da7" />

**Why the table matters**
Two workout types can have similar *median efficiency* but different risk profiles:

* One might have tight IQR (predictable, stable sessions)
* Another might be wide (high variance: depends on intensity or session type)

---

### 3) Fairness (gap analysis)

This tab is designed to prevent a common analytics failure:

> “Global benchmarks become unfair benchmarks when populations differ.”

It provides:

* A group dimension selector (e.g., `age_band`, `gender`, `membership_type`)
* A group table:

  * sessions per group
  * group median efficiency
  * overall median efficiency
  * gap vs overall (directional)
  * uncertainty bounds (CI when available)
  * effect size (e.g., Cliff’s delta)
  * low-sample flags

<img width="1707" height="808" alt="Screenshot 2026-02-17 at 12-41-49 Workout Efficiency Benchmark Report" src="https://github.com/user-attachments/assets/f4f447d0-5bac-4cd9-85e0-03b0d67848c2" />

**How to interpret a “gap” correctly**

* A positive gap means that group’s median efficiency is above the overall median.
* A negative gap means it’s below.
* A gap is **descriptive**, not causal:

  * age is correlated with many factors (training goals, injury history, workout selection, schedule constraints)
* Low sample rows are explicitly flagged because they can “look dramatic” while being unreliable.

---

### 4) Data Quality (trust contract)

This tab answers: **“Can I trust these benchmarks?”**
It exposes:

* missingness in key columns
* how many rows appear absent or inconsistent
* the “present-only” filtering impact
* recommended actions when the data is messy

<img width="618" height="652" alt="Screenshot 2026-02-17 at 12-41-59 Workout Efficiency Benchmark Report" src="https://github.com/user-attachments/assets/9332f712-a452-4a83-8518-63d0e79882c9" />

**The key decision in this project**
If `absent_with_activity_rate` is high, you have two legitimate interpretations:

1. **Absent rows mean “scheduled but not attended”**

   * Keep for attendance analytics
   * Exclude from efficiency benchmarking (default)
2. **Absent rows are mislabeled**

   * Only flip them if you have external validation
   * Document the rule change explicitly

This is what makes the report decision-safe: it shows the ambiguity instead of hiding it.

---

### 5) Notes (guardrails + next upgrades)

This section is the “don’t misuse this report” page:

* It restates the intent: benchmarking, not medical inference
* It warns about confounders
* It suggests upgrades when you want deeper correctness

<img width="570" height="342" alt="Screenshot 2026-02-17 at 12-42-07 Workout Efficiency Benchmark Report" src="https://github.com/user-attachments/assets/b985ba57-488a-473b-82f5-81b452bf9f78" />

---

## Figures: what each one means

All figures are saved in `reports/figures/`. The dashboard arranges them as a clean grid, but the README explains them in detail.

---

### Figure 1 | Calories vs Duration (Present sessions)

**File:** `reports/figures/calories_vs_duration.png`

<img width="1530" height="1080" alt="calories_vs_duration" src="https://github.com/user-attachments/assets/c7ca5274-0263-4e0e-bb0d-8afb4e66beb3" />

**What it shows**

* Each point is a session (present only).
* X-axis: workout duration (minutes)
* Y-axis: calories burned

**What you should notice**

* The “cloud” usually slopes up: longer workouts burn more calories.
* The vertical spread at the same duration is real variance:

  * intensity differs
  * workout type differs
  * device estimation differs

**Why this figure is essential**
It reveals why you should not compare total calories directly:

* A person can burn high calories because they stayed longer, not because they were more efficient.
  This motivates the normalized metric: **kcal/min**.

**Common interpretation mistake**

* Mistake: “More calories burned means better workout.”
* Better framing: “Calories burned reflects *time × intensity*; efficiency isolates a benchmarkable rate.”

---

### Figure 2 | Efficiency distribution by workout type (boxplots)

**File:** `reports/figures/efficiency_by_workout_type.png`

<img width="1980" height="1080" alt="efficiency_by_workout_type" src="https://github.com/user-attachments/assets/8c564dec-56fc-45cb-9428-09bbdacf17bd" />

**What it shows**

* Each box summarizes sessions for one workout type.
* The line inside the box is the **median** kcal/min.
* The box height is the **IQR** (middle 50% of sessions).
* Whiskers show broader spread (often up to 1.5×IQR).

**Why median + IQR**
Workout data is often skewed:

* a few extreme sessions can pull the mean upward
* medians resist outliers and are more stable for benchmarking

**How to use it**

* If one workout type has a higher median efficiency AND similar IQR:

  * it’s consistently more “efficient” in this dataset
* If medians are similar but IQR differs:

  * one type is more predictable
  * another is “high variance” (sometimes very efficient, sometimes not)

**Decision-safe takeaway**
Use this to set **workout-type-specific benchmarks** instead of one global number.

---

### Figure 3 | Mean efficiency heatmap (workout type × gender)

**File:** `reports/figures/heatmap_efficiency_workout_gender.png`

<img width="1710" height="1080" alt="heatmap_efficiency_workout_gender" src="https://github.com/user-attachments/assets/fa05bb7d-90ef-4c68-91bd-8eba88f68abe" />

**What it shows**

* Rows: workout types
* Columns: gender categories
* Cell value: **mean** efficiency for that slice
* Often includes session counts (n=...) inside cells

**Why this exists**
A single overall benchmark can hide:

* workout selection patterns by group
* different distributions within workout types
* sample imbalance (small groups creating noisy means)

**How to interpret responsibly**

* Treat this as a *lens*, not a verdict.
* Always check:

  * sample size (n)
  * whether a slice is flagged low-sample in the fairness tab

**Why “mean” is okay here**
For a heatmap, mean works as a quick summary, but:

* fairness decisions should prioritize medians + uncertainty
* this is best used to spot “where to look deeper,” not to conclude.

---

### Figure 4 | Median efficiency by age band

**File:** `reports/figures/efficiency_by_age_band.png`

<img width="1620" height="954" alt="efficiency_by_age_band" src="https://github.com/user-attachments/assets/eb61de31-8bd4-4440-8e84-f79bc429b077" />

**What it shows**

* X-axis: age bands (e.g., 18–24, 25–34, …, 65+)
* Y-axis: **median** efficiency kcal/min
* Error bars: bootstrap confidence intervals (when available)

**Why age-band benchmarking is tricky**
Age correlates with:

* workout type preferences
* injury constraints
* training goals
* session duration and pacing
  So this is **not causal**, it’s descriptive.

**How to use this figure**

* If bands overlap heavily within CI:

  * differences are likely not stable
* If one band is clearly separated:

  * treat it as a prompt to investigate confounders
  * check workout-type composition within that band

**Why 65+ often has wider CI**
Usually because sample size is smaller, so uncertainty grows.
That’s exactly why this plot includes uncertainty: to prevent overconfident claims.

---

## Interpretation checklist (what to conclude vs what not to conclude)

Safe conclusions:

* “Efficiency varies by workout type; medians and spreads differ.”
* “Some segments have different medians vs overall; sample size affects confidence.”
* “Data quality issues (absent/inconsistent rows) materially change benchmarking.”

Unsafe conclusions:

* “Group X is fitter than Group Y.”
* “Workout type A is objectively better than B.”
* “Efficiency is a medical metric.”
