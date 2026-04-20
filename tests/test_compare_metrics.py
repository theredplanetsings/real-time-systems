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


def test_summarize_run_handles_non_numeric_fields() -> None:
    segments = [
        {"job": "6.0", "phase": "CPU", "remaining": "done", "end": "n/a", "deadline": "oops"},
    ]
    result = summarize_run(segments, horizon=2)
    assert result["jobs_seen"] == 1
    assert result["jobs_completed"] == 0
    assert result["deadline_misses"] == 1


def test_summarize_run_ignores_rows_without_job() -> None:
    segments = [
        {"phase": "CPU", "remaining": 0, "end": 1, "deadline": 1},
    ]
    result = summarize_run(segments, horizon=2)
    assert result["jobs_seen"] == 0
    assert result["jobs_completed"] == 0


def test_deadline_miss_details_handles_missing_phase_and_remaining() -> None:
    segments = [
        {"job": "7.0", "release": 0, "deadline": 1, "end": 2},
    ]
    details = deadline_miss_details(segments, horizon=3)
    assert len(details) == 1
    assert details.iloc[0]["Finish"] == "not finished"


def test_deadline_miss_details_requires_release_and_deadline() -> None:
    segments = [
        {"job": "8.0", "phase": "CPU", "remaining": 0, "end": 2},
    ]
    details = deadline_miss_details(segments, horizon=3)
    assert details.empty


def test_summarize_run_normalizes_negative_horizon() -> None:
    segments = [
        {"job": "9.0", "phase": "CPU", "remaining": 1, "end": 1, "deadline": 0},
    ]
    result = summarize_run(segments, horizon=-5)
    assert result["deadline_misses"] == 1


def test_deadline_miss_details_normalizes_negative_horizon() -> None:
    segments = [
        {"job": "10.0", "phase": "CPU", "remaining": 1, "release": 0, "deadline": 1, "end": 1}
    ]
    details = deadline_miss_details(segments, horizon=-2)
    assert details.empty


def test_summarize_run_handles_non_numeric_horizon() -> None:
    segments = [
        {"job": "11.0", "phase": "CPU", "remaining": 1, "end": 1, "deadline": 0},
    ]
    result = summarize_run(segments, horizon="invalid")
    assert result["deadline_misses"] == 1


def test_summarize_run_ignores_blank_job_identifiers() -> None:
    segments = [
        {"job": "", "phase": "CPU", "remaining": 0, "end": 1, "deadline": 1},
        {"job": "   ", "phase": "CPU", "remaining": 0, "end": 1, "deadline": 1},
        {"job": None, "phase": "CPU", "remaining": 0, "end": 1, "deadline": 1},
    ]
    result = summarize_run(segments, horizon=2)
    assert result["jobs_seen"] == 0


def test_deadline_miss_details_uses_natural_job_sort_order() -> None:
    segments = [
        {
            "job": "10.0",
            "phase": "CPU",
            "remaining": 1,
            "release": 0,
            "deadline": 1,
            "end": 1,
        },
        {
            "job": "2.0",
            "phase": "CPU",
            "remaining": 1,
            "release": 0,
            "deadline": 1,
            "end": 1,
        },
    ]
    details = deadline_miss_details(segments, horizon=3)
    assert list(details["Job"]) == ["2.0", "10.0"]


def test_summarize_run_ignores_stringified_null_job_ids() -> None:
    segments = [
        {"job": "nan", "phase": "CPU", "remaining": 0, "end": 1, "deadline": 1},
        {"job": "NULL", "phase": "CPU", "remaining": 0, "end": 1, "deadline": 1},
        {"job": "None", "phase": "CPU", "remaining": 0, "end": 1, "deadline": 1},
    ]
    result = summarize_run(segments, horizon=2)
    assert result["jobs_seen"] == 0
    assert result["jobs_completed"] == 0


def test_deadline_miss_details_ignores_stringified_null_job_ids() -> None:
    segments = [
        {"job": " nan ", "phase": "CPU", "remaining": 1, "release": 0, "deadline": 1, "end": 1},
        {"job": "NULL", "phase": "CPU", "remaining": 1, "release": 0, "deadline": 1, "end": 1},
    ]
    details = deadline_miss_details(segments, horizon=2)
    assert details.empty
