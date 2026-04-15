from __future__ import annotations
import pandas as pd


def _to_float(value: object, default: float = 0.0) -> float:
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def _normalize_horizon(horizon: int) -> int:
    return max(int(horizon), 0)


def summarize_run(segments: list[dict[str, object]], horizon: int) -> dict[str, int]:
    horizon = _normalize_horizon(horizon)
    if not segments:
        return {
            "jobs_seen": 0,
            "jobs_completed": 0,
            "deadline_misses": 0,
            "blocked_ticks": 0,
            "cpu_or_resource_ticks": 0,
        }

    df = pd.DataFrame(segments)
    if df.empty:
        return {
            "jobs_seen": 0,
            "jobs_completed": 0,
            "deadline_misses": 0,
            "blocked_ticks": 0,
            "cpu_or_resource_ticks": 0,
        }

    jobs_seen = df["job"].nunique() if "job" in df.columns else 0
    blocked_ticks = int((df["phase"] == "Blocked").sum()) if "phase" in df.columns else 0
    executed_df = df[df["phase"] != "Blocked"] if "phase" in df.columns else df
    cpu_or_resource_ticks = len(executed_df)

    completions: dict[str, tuple[float, float]] = {}
    deadlines: dict[str, float] = {}

    for _, row in df.iterrows():
        job_id = str(row.get("job", ""))
        if not job_id:
            continue
        deadline = _to_float(row.get("deadline", 0), 0.0)
        deadlines[job_id] = deadline

        if row.get("phase") == "Blocked":
            continue

        remaining = _to_float(row.get("remaining", 1), 1.0)
        if remaining == 0:
            end_time = _to_float(row.get("end", 0), 0.0)
            if job_id not in completions or end_time < completions[job_id][0]:
                completions[job_id] = (end_time, deadline)

    jobs_completed = len(completions)
    deadline_misses = sum(1 for end_time, deadline in completions.values() if end_time > deadline)

    for job_id, deadline in deadlines.items():
        if deadline <= horizon and job_id not in completions:
            deadline_misses += 1

    return {
        "jobs_seen": int(jobs_seen),
        "jobs_completed": int(jobs_completed),
        "deadline_misses": int(deadline_misses),
        "blocked_ticks": int(blocked_ticks),
        "cpu_or_resource_ticks": int(cpu_or_resource_ticks),
    }


def deadline_miss_details(segments: list[dict[str, object]], horizon: int) -> pd.DataFrame:
    horizon = _normalize_horizon(horizon)
    if not segments:
        return pd.DataFrame()

    df = pd.DataFrame(segments)
    if df.empty or "job" not in df.columns:
        return pd.DataFrame()
    if "release" not in df.columns or "deadline" not in df.columns:
        return pd.DataFrame()

    releases = (
        df.groupby("job", as_index=False)["release"].min().rename(columns={"release": "Release"})
    )
    deadlines = (
        df.groupby("job", as_index=False)["deadline"].max().rename(columns={"deadline": "Deadline"})
    )

    phase_series = df["phase"] if "phase" in df.columns else pd.Series("", index=df.index)
    remaining_series = (
        pd.to_numeric(df["remaining"], errors="coerce")
        if "remaining" in df.columns
        else pd.Series(float("nan"), index=df.index)
    )
    completed_rows = df[(phase_series != "Blocked") & (remaining_series == 0)]
    completions = (
        completed_rows.groupby("job", as_index=False)["end"].min().rename(columns={"end": "Finish"})
    )

    details = releases.merge(deadlines, on="job", how="outer").merge(
        completions, on="job", how="left"
    )
    details["Finish"] = pd.to_numeric(details["Finish"], errors="coerce")
    details["Deadline"] = pd.to_numeric(details["Deadline"], errors="coerce")
    details["Release"] = pd.to_numeric(details["Release"], errors="coerce")
    details["Missed"] = details.apply(
        lambda row: (pd.isna(row["Finish"]) and row["Deadline"] <= horizon)
        or (not pd.isna(row["Finish"]) and row["Finish"] > row["Deadline"]),
        axis=1,
    )
    details = details[details["Missed"]].copy()
    if details.empty:
        return details

    details["Lateness"] = details.apply(
        lambda row: (
            (horizon - row["Deadline"])
            if pd.isna(row["Finish"])
            else (row["Finish"] - row["Deadline"])
        ),
        axis=1,
    )
    details["Finish"] = details["Finish"].fillna("not finished")

    details = details.rename(columns={"job": "Job"})
    return details[["Job", "Release", "Deadline", "Finish", "Lateness"]].sort_values(
        by=["Deadline", "Job"]
    )
