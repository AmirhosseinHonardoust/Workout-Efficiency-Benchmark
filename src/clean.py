from __future__ import annotations

from dataclasses import dataclass
                                      
import pandas as pd
                                                 
                                                             
@dataclass
class CleanResult:
    df_raw: pd.DataFrame
    df_present: pd.DataFrame
    quality: dict


def _parse_hour(check_in_time: pd.Series) -> pd.Series:
    """
    Parse hour from check_in_time strings robustly (handles '7:05', '07:05', '07:05:00').
    Returns Int64 hour (nullable). No pandas datetime inference -> no warnings.
    """
    s = check_in_time.astype(str).str.strip()

    # Capture the leading hour (1–2 digits) before ":" (or even if seconds exist)
    hour = pd.to_numeric(s.str.extract(r"^\s*(\d{1,2})\s*:")[0], errors="coerce")

    # Keep only valid hours
    hour = hour.where((hour >= 0) & (hour <= 23))

    return hour.astype("Int64")



def add_age_band(age: pd.Series) -> pd.Categorical:
    bins = [0, 24, 34, 44, 54, 64, 200]
    labels = ["18-24", "25-34", "35-44", "45-54", "55-64", "65+"]
    return pd.cut(age, bins=bins, labels=labels, right=True, include_lowest=True)


def clean_and_features(df: pd.DataFrame) -> CleanResult:
    out = df.copy()

    # Normalize strings
    for col in ["gender", "membership_type", "workout_type", "attendance_status"]:
        if col in out.columns:
            out[col] = out[col].astype(str).str.strip()

    # Parse date + hour
    out["visit_date"] = pd.to_datetime(out["visit_date"], errors="coerce")
    if "check_in_time" in out.columns:
        out["check_in_hour"] = _parse_hour(out["check_in_time"])
    else:
        out["check_in_hour"] = pd.Series([pd.NA] * len(out), dtype="Int64")

    # Data quality checks
    q = {}
    q["rows"] = int(len(out))
    q["missing_visit_date"] = int(out["visit_date"].isna().sum())
    q["missing_check_in_time"] = int(out["check_in_time"].isna().sum()) if "check_in_time" in out.columns else 0

    # Absent-but-has-activity inconsistency
    absent = out["attendance_status"].str.lower().eq("absent") if "attendance_status" in out.columns else pd.Series([False] * len(out))
    has_duration = out["workout_duration_minutes"].fillna(0) > 0
    has_calories = out["calories_burned"].fillna(0) > 0
    inconsistent = absent & (has_duration | has_calories)

    q["absent_with_activity_rows"] = int(inconsistent.sum())
    q["absent_with_activity_rate"] = float(inconsistent.mean()) if len(out) else 0.0

    # Efficiency analysis: use Present sessions only
    present = out["attendance_status"].str.lower().eq("present") if "attendance_status" in out.columns else pd.Series([True] * len(out))
    df_present = out.loc[present].copy()

    # Coerce numeric fields
    for col in ["workout_duration_minutes", "calories_burned", "age"]:
        df_present[col] = pd.to_numeric(df_present[col], errors="coerce")

    # Drop nonsensical values
    df_present = df_present.dropna(subset=["workout_duration_minutes", "calories_burned", "workout_type", "gender", "membership_type", "age"])
    df_present = df_present[(df_present["workout_duration_minutes"] > 0) & (df_present["calories_burned"] > 0)]

    # Features
    df_present["efficiency_kcal_per_min"] = df_present["calories_burned"] / df_present["workout_duration_minutes"]
    df_present["age_band"] = add_age_band(df_present["age"])
    df_present["dow"] = df_present["visit_date"].dt.day_name()
    df_present["month"] = df_present["visit_date"].dt.month_name()

    q["present_rows_used"] = int(len(df_present))
    q["present_rate_used"] = float(len(df_present) / len(out)) if len(out) else 0.0

    q["missingness_present"] = {
        c: float(df_present[c].isna().mean())
        for c in ["workout_type", "gender", "membership_type", "age", "workout_duration_minutes", "calories_burned"]
        if c in df_present.columns
    }

    return CleanResult(df_raw=out, df_present=df_present, quality=q)
