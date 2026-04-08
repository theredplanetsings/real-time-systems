import time
import pandas as pd
import streamlit as st
from rt_utils import TaskSpec, simulate_uniprocessor

st.set_page_config(page_title="Benchmark Suite", layout="wide")
st.title("Benchmark Suite")
st.caption("Measure scheduler runtime and miss behavior on canned workloads.")

def _scenario_harmonic() -> list[TaskSpec]:
    return [
        TaskSpec(1, 0, 4, 1, 4),
        TaskSpec(2, 0, 8, 2, 8),
        TaskSpec(3, 0, 16, 3, 16),
    ]

def _scenario_tight() -> list[TaskSpec]:
    return [
        TaskSpec(1, 0, 6, 2, 4),
        TaskSpec(2, 0, 8, 2, 5),
        TaskSpec(3, 0, 12, 3, 6),
    ]

def _scenario_mixed_phase() -> list[TaskSpec]:
    return [
        TaskSpec(1, 0, 5, 1, 5),
        TaskSpec(2, 1, 7, 2, 7),
        TaskSpec(3, 2, 11, 3, 11),
    ]

def _misses(segments: list[dict[str, object]], horizon: int) -> int:
    seen: dict[str, float] = {}
    done: dict[str, float] = {}
    for seg in segments:
        job = str(seg.get("job", ""))
        if not job:
            continue
        seen[job] = float(seg.get("deadline", 0))
        if seg.get("phase") != "Blocked" and float(seg.get("remaining", 1)) == 0:
            done[job] = min(done.get(job, float("inf")), float(seg.get("end", 0)))

    misses = 0
    for job, dl in seen.items():
        if job in done and done[job] > dl:
            misses += 1
        if job not in done and dl <= horizon:
            misses += 1
    return misses

HORIZON = int(st.sidebar.number_input("Horizon", min_value=20, max_value=2000, value=200, step=10))
REPEATS = int(st.sidebar.number_input("Repeats", min_value=1, max_value=100, value=20, step=1))
RESOURCE_ORDER = st.sidebar.selectbox("Resource order", ["CPU then resources", "Resources then CPU"], index=0)

scenarios = {
    "Harmonic": _scenario_harmonic(),
    "Tight deadlines": _scenario_tight(),
    "Mixed phase": _scenario_mixed_phase(),
}
algorithms = ["RM", "DM", "EDF"]

if st.button("Run benchmark", type="primary"):
    rows = []
    for scenario_name, tasks in scenarios.items():
        for algorithm in algorithms:
            total_ms = 0.0
            misses = 0
            seg_count = 0
            for _ in range(REPEATS):
                start = time.perf_counter()
                segments = simulate_uniprocessor(tasks, HORIZON, algorithm, "None", RESOURCE_ORDER)
                elapsed_ms = (time.perf_counter() - start) * 1000.0
                total_ms += elapsed_ms
                misses = _misses(segments, HORIZON)
                seg_count = len(segments)

            rows.append(
                {
                    "Scenario": scenario_name,
                    "Algorithm": algorithm,
                    "Mean runtime (ms)": round(total_ms / REPEATS, 3),
                    "Segments": seg_count,
                    "Deadline misses": misses,
                }
            )

    df = pd.DataFrame(rows).sort_values(["Scenario", "Mean runtime (ms)"])
    st.dataframe(df, use_container_width=True)
    st.bar_chart(df, x="Scenario", y="Mean runtime (ms)", color="Algorithm")