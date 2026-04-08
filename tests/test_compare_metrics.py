import pandas as pd
from compare_utils import deadline_miss_details, summarize_run

def test_summarize_run_counts_seen_completed_and_blocked() -> None:
    segments = [
        {"job": "1.0", "phase": "CPU", "remaining": 1, "end": 1, "deadline": 3},
        {"job": "1.0", "phase": "CPU", "remaining": 0, "end": 2, "deadline": 3},
        {"job": "2.0", "phase": "Blocked", "remaining": 2, "end": 1, "deadline": 2},
    ]
    result = summarize_run(segments, horizon=3)
    assert result["jobs_seen"] == 2
    assert result["jobs_completed"] == 1
    assert result["blocked_ticks"] == 1

def test_summarize_run_counts_unfinished_deadline_miss() -> None:
    segments = [
        {"job": "3.0", "phase": "CPU", "remaining": 2, "end": 1, "deadline": 1},
    ]
    result = summarize_run(segments, horizon=2)
    assert result["deadline_misses"] == 1

def test_deadline_miss_details_returns_expected_columns() -> None:
    segments = [
        {
            "job": "4.0",
            "phase": "CPU",
            "remaining": 0,
            "start": 0,
            "end": 5,
            "release": 0,
            "deadline": 3,
        }
    ]
    details = deadline_miss_details(segments, horizon=5)
    assert isinstance(details, pd.DataFrame)
    assert list(details.columns) == ["Job", "Release", "Deadline", "Finish", "Lateness"]
    assert len(details) == 1

def test_deadline_miss_details_flags_not_finished_jobs() -> None:
    segments = [
        {
            "job": "5.0",
            "phase": "CPU",
            "remaining": 1,
            "start": 0,
            "end": 1,
            "release": 0,
            "deadline": 1,
        }
    ]
    details = deadline_miss_details(segments, horizon=3)
    assert len(details) == 1
    assert details.iloc[0]["Finish"] == "not finished"