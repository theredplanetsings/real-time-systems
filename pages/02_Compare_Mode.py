import streamlit as st
import pandas as pd
from st_helpers import cached_schedule_figure, render_task_inputs
from rt_utils import (
    COMPARE_ALGORITHMS,
    TaskSpec,
    build_task_dataframe,
    cyclic_executive_frames,
    cyclic_executive_schedule,
    schedule_png_bytes,
    simulate_global_dm,
    simulate_global_edf,
    simulate_global_rm,
    simulate_partitioned,
    simulate_uniprocessor,
    task_csv_bytes,
    task_json_bytes,
)

st.set_page_config(page_title="Compare Mode", layout="wide")
st.title("Compare Mode")
st.caption("Compare multiple algorithms across one or many task sets.")

def _default_assignment_matrix(task_set_count: int, algorithm_count: int, unique_default: bool) -> pd.DataFrame:
    rows = []
    for ts_index in range(task_set_count):
        row = {"Task Set": f"TS{ts_index + 1}"}
        for alg_index in range(algorithm_count):
            if unique_default:
                row[f"A{alg_index + 1}"] = ts_index == alg_index
            else:
                row[f"A{alg_index + 1}"] = ts_index == 0
        rows.append(row)
    return pd.DataFrame(rows)


def _strip_resources(tasks: list[TaskSpec]) -> list[TaskSpec]:
    return [
        TaskSpec(
            task_id=task.task_id,
            phase=task.phase,
            period=task.period,
            computation=task.computation,
            deadline=task.deadline,
            resources={},
        )
        for task in tasks
    ]


def _run_algorithm(
    algorithm: str,
    tasks: list[TaskSpec],
    horizon: int,
    protocol: str,
    resource_order: str,
    processors: int,
    strategy: str,
    metric: str,
) -> tuple[list[dict[str, object]], list[float], bool]:
    info = COMPARE_ALGORITHMS[algorithm]
    mode = info["mode"]
    family = info["family"]

    if mode == "uniprocessor":
        segments = simulate_uniprocessor(tasks, horizon, family, protocol, resource_order)
        return segments, [], False

    if mode == "global":
        cpu_only_tasks = _strip_resources(tasks)
        if family == "RM":
            segments = simulate_global_rm(cpu_only_tasks, horizon, processors)
        elif family == "EDF":
            segments = simulate_global_edf(cpu_only_tasks, horizon, processors)
        else:
            segments = simulate_global_dm(cpu_only_tasks, horizon, processors)
        return segments, [], False

    if mode == "cyclic":
        hyperperiod, valid_frames = cyclic_executive_frames(tasks)
        if not valid_frames:
            return [], [], False
        frame = valid_frames[0]
        segments = cyclic_executive_schedule(tasks, frame)
        return segments, [float(frame)], False

    segments, loads, overloaded = simulate_partitioned(
        tasks,
        horizon,
        processors,
        family,
        strategy,
        metric,
        protocol,
        resource_order,
    )
    return segments, loads, overloaded


def _summarize_run(segments: list[dict[str, object]], horizon: int) -> dict[str, int]:
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
        deadline = float(row.get("deadline", 0))
        deadlines[job_id] = deadline

        if row.get("phase") == "Blocked":
            continue

        remaining = float(row.get("remaining", 1))
        if remaining == 0:
            end_time = float(row.get("end", 0))
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


def _deadline_miss_details(segments: list[dict[str, object]], horizon: int) -> pd.DataFrame:
    if not segments:
        return pd.DataFrame()

    df = pd.DataFrame(segments)
    if df.empty or "job" not in df.columns:
        return pd.DataFrame()

    releases = (
        df.groupby("job", as_index=False)["release"]
        .min()
        .rename(columns={"release": "Release"})
    )
    deadlines = (
        df.groupby("job", as_index=False)["deadline"]
        .max()
        .rename(columns={"deadline": "Deadline"})
    )

    completed_rows = df[(df.get("phase") != "Blocked") & (pd.to_numeric(df.get("remaining"), errors="coerce") == 0)]
    completions = (
        completed_rows.groupby("job", as_index=False)["end"]
        .min()
        .rename(columns={"end": "Finish"})
    )

    details = releases.merge(deadlines, on="job", how="outer").merge(completions, on="job", how="left")
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
        lambda row: (horizon - row["Deadline"]) if pd.isna(row["Finish"]) else (row["Finish"] - row["Deadline"]),
        axis=1,
    )
    details["Finish"] = details["Finish"].fillna("not finished")

    details = details.rename(columns={"job": "Job"})
    return details[["Job", "Release", "Deadline", "Finish", "Lateness"]].sort_values(by=["Deadline", "Job"])


st.sidebar.header("Compare Setup")
algorithm_count = int(st.sidebar.number_input("Algorithms to compare", min_value=2, max_value=8, value=2, step=1))
use_unique_default = st.sidebar.checkbox("Default to unique task set per algorithm", value=False)

default_task_set_count = algorithm_count if use_unique_default else 1
task_set_count = int(
    st.sidebar.number_input(
        "Task sets",
        min_value=1,
        max_value=12,
        value=default_task_set_count,
        step=1,
    )
)

st.sidebar.subheader("Global Simulation Window")
range_start = int(st.sidebar.number_input("Time range start", min_value=0, max_value=1000, value=0, step=1))
range_end = int(st.sidebar.number_input("Time range end", min_value=1, max_value=1000, value=30, step=1))
tick_step = int(st.sidebar.number_input("Time tick step", min_value=1, max_value=100, value=5, step=1))

st.subheader("Algorithms")
algorithm_cols = st.columns(min(algorithm_count, 4))
selected_algorithms: list[str] = []

algorithm_options = list(COMPARE_ALGORITHMS.keys())
default_pick_order = ["RM", "EDF", "DM", "Global RM", "Global EDF", "Global DM"]

for index in range(algorithm_count):
    col = algorithm_cols[index % len(algorithm_cols)]
    default_name = default_pick_order[index] if index < len(default_pick_order) else algorithm_options[index % len(algorithm_options)]
    default_idx = algorithm_options.index(default_name)
    selected = col.selectbox(
        f"Algorithm A{index + 1}",
        algorithm_options,
        index=default_idx,
        key=f"compare_algorithm_{index}",
    )
    selected_algorithms.append(selected)

st.subheader("Algorithm Runtime Options")
algorithm_runtime: list[dict[str, object]] = []

for index, algorithm in enumerate(selected_algorithms):
    info = COMPARE_ALGORITHMS[algorithm]
    mode = info["mode"]

    with st.expander(f"A{index + 1}: {algorithm} settings", expanded=False):
        protocol = "None"
        resource_order = "CPU then resources"
        processors = 1
        strategy = "First-fit decreasing"
        metric = "Utilisation"

        if mode in {"uniprocessor", "partitioned"}:
            protocol = st.selectbox(
                "Resource protocol",
                ["None", "PIP", "PCP", "NPP"],
                index=0,
                key=f"compare_protocol_{index}",
            )
            resource_order = st.selectbox(
                "Execution order",
                ["CPU then resources", "Resources then CPU"],
                index=0,
                key=f"compare_resource_order_{index}",
            )

        if mode in {"global", "partitioned"}:
            processors = int(
                st.number_input(
                    "Processors",
                    min_value=1,
                    max_value=16,
                    value=2,
                    step=1,
                    key=f"compare_processors_{index}",
                )
            )

        if mode == "cyclic":
            st.info("Cyclic Executive uses the smallest valid frame size for each task set.")

        if mode == "partitioned":
            strategy = st.selectbox(
                "Partitioning strategy",
                ["First-fit decreasing", "Best-fit", "Worst-fit"],
                index=0,
                key=f"compare_strategy_{index}",
            )
            metric = st.selectbox(
                "Packing metric",
                ["Utilisation", "Density"],
                index=0,
                key=f"compare_metric_{index}",
            )

        if mode == "global":
            st.info("Global variants in this project are CPU-only (resource segments are ignored).")

    algorithm_runtime.append(
        {
            "algorithm": algorithm,
            "protocol": protocol,
            "resource_order": resource_order,
            "processors": processors,
            "strategy": strategy,
            "metric": metric,
        }
    )

st.subheader("Task Sets")
all_task_sets: list[list[TaskSpec]] = []
resource_names_for_task_set: list[list[str]] = []
task_set_validation_errors: list[tuple[int, list[str]]] = []

for ts_index in range(task_set_count):
    with st.expander(f"Task Set TS{ts_index + 1}", expanded=(ts_index == 0)):
        c1, c2, c3 = st.columns(3)
        num_tasks = int(c1.number_input("Number of tasks", min_value=1, max_value=20, value=3, step=1, key=f"ts_n_{ts_index}"))
        default_period = int(c2.number_input("Default period", min_value=1, max_value=500, value=10, step=1, key=f"ts_p_{ts_index}"))
        default_comp = int(c3.number_input("Default computation", min_value=1, max_value=500, value=2, step=1, key=f"ts_c_{ts_index}"))

        d1, d2, d3 = st.columns(3)
        include_phase = d1.checkbox("Include phase", value=True, key=f"ts_phase_{ts_index}")
        include_deadline = d2.checkbox("Include deadline", value=True, key=f"ts_deadline_{ts_index}")
        include_resources = d3.checkbox("Include resources", value=False, key=f"ts_resources_{ts_index}")

        default_phase = 0
        default_deadline = default_period
        default_resource_time = 0
        resource_names: list[str] = []

        if include_phase:
            default_phase = int(
                st.number_input(
                    "Default phase",
                    min_value=0,
                    max_value=500,
                    value=0,
                    step=1,
                    key=f"ts_phase_default_{ts_index}",
                )
            )

        if include_deadline:
            default_deadline = int(
                st.number_input(
                    "Default deadline",
                    min_value=1,
                    max_value=500,
                    value=default_period,
                    step=1,
                    key=f"ts_deadline_default_{ts_index}",
                )
            )

        if include_resources:
            r1, r2 = st.columns(2)
            resource_count = int(
                r1.number_input(
                    "Number of resources",
                    min_value=1,
                    max_value=4,
                    value=1,
                    step=1,
                    key=f"ts_resource_count_{ts_index}",
                )
            )
            default_resource_time = int(
                r2.number_input(
                    "Default resource time",
                    min_value=0,
                    max_value=100,
                    value=0,
                    step=1,
                    key=f"ts_resource_default_{ts_index}",
                )
            )
            resource_names = [chr(ord("A") + i) for i in range(resource_count)]

        tasks = render_task_inputs(
            num_tasks=num_tasks,
            include_phase=include_phase,
            include_period=True,
            include_computation=True,
            include_deadline=include_deadline,
            include_resources=include_resources,
            resource_names=resource_names,
            default_period=default_period,
            default_computation=default_comp,
            key_prefix=f"compare_ts_{ts_index}",
            default_phase=default_phase,
            default_deadline=default_deadline,
            default_resource_time=default_resource_time,
        )

        invalid_rows = []
        for task in tasks:
            if task.period <= 0:
                invalid_rows.append(f"T{task.task_id}: period must be > 0")
            if task.deadline <= 0:
                invalid_rows.append(f"T{task.task_id}: deadline must be > 0")
            if task.computation <= 0:
                invalid_rows.append(f"T{task.task_id}: computation must be > 0")
            if sum(task.resources.values()) > task.computation:
                invalid_rows.append(
                    f"T{task.task_id}: total resource time exceeds computation ({sum(task.resources.values())}>{task.computation})"
                )

        if invalid_rows:
            st.error("Validation issues in this task set:\n- " + "\n- ".join(invalid_rows))
            task_set_validation_errors.append((ts_index, invalid_rows))

        all_task_sets.append(tasks)
        resource_names_for_task_set.append(resource_names)

st.subheader("Task Set -> Algorithm Assignment")
st.caption("Use checkboxes to choose which task sets run on which algorithms.")

matrix_seed_key = f"compare_seed_{task_set_count}_{algorithm_count}_{int(use_unique_default)}"
if st.session_state.get("compare_assignment_seed") != matrix_seed_key:
    st.session_state["compare_assignment_df"] = _default_assignment_matrix(
        task_set_count=task_set_count,
        algorithm_count=algorithm_count,
        unique_default=use_unique_default,
    )
    st.session_state["compare_assignment_seed"] = matrix_seed_key

assignment_df = st.session_state["compare_assignment_df"].copy()

# Keep matrix aligned with current dimensions.
assignment_df = assignment_df.iloc[:task_set_count].copy()
if len(assignment_df) < task_set_count:
    missing = _default_assignment_matrix(task_set_count - len(assignment_df), algorithm_count, use_unique_default)
    start_idx = len(assignment_df)
    missing["Task Set"] = [f"TS{i + 1}" for i in range(start_idx, task_set_count)]
    assignment_df = pd.concat([assignment_df, missing], ignore_index=True)

for ts_index in range(task_set_count):
    assignment_df.loc[ts_index, "Task Set"] = f"TS{ts_index + 1}"

for col_index in range(algorithm_count):
    base_col = f"A{col_index + 1}"
    if base_col not in assignment_df.columns:
        assignment_df[base_col] = (not use_unique_default and col_index >= 0)

drop_cols = [c for c in assignment_df.columns if c not in {"Task Set"} | {f"A{i + 1}" for i in range(algorithm_count)}]
if drop_cols:
    assignment_df = assignment_df.drop(columns=drop_cols)

rename_map = {f"A{i + 1}": f"A{i + 1}: {selected_algorithms[i]}" for i in range(algorithm_count)}
assignment_for_editor = assignment_df.rename(columns=rename_map)

edited = st.data_editor(
    assignment_for_editor,
    use_container_width=True,
    hide_index=True,
    disabled=["Task Set"],
    key="compare_assignment_editor",
)

save_df = edited.rename(columns={v: k for k, v in rename_map.items()})
for col_index in range(algorithm_count):
    col_name = f"A{col_index + 1}"
    save_df[col_name] = save_df[col_name].astype(bool)
st.session_state["compare_assignment_df"] = save_df

if st.button("Run Compare", type="primary"):
    if range_end <= range_start:
        st.error("Time range end must be greater than start.")
        st.stop()

    if task_set_validation_errors:
        error_lines = []
        for ts_index, invalid_rows in task_set_validation_errors:
            error_lines.append(f"TS{ts_index + 1}: " + "; ".join(invalid_rows))
        st.error("Fix validation issues before running Compare:\n- " + "\n- ".join(error_lines))
        st.stop()

    selected_pairs: list[tuple[int, int]] = []
    for ts_index in range(task_set_count):
        for alg_index in range(algorithm_count):
            if bool(save_df.loc[ts_index, f"A{alg_index + 1}"]):
                selected_pairs.append((ts_index, alg_index))

    if not selected_pairs:
        st.warning("No task set/algorithm assignments selected.")
        st.stop()

    results = []
    for ts_index, alg_index in selected_pairs:
        runtime = algorithm_runtime[alg_index]
        algorithm = str(runtime["algorithm"])
        tasks = all_task_sets[ts_index]

        segments, loads, overloaded = _run_algorithm(
            algorithm=algorithm,
            tasks=tasks,
            horizon=range_end,
            protocol=str(runtime["protocol"]),
            resource_order=str(runtime["resource_order"]),
            processors=int(runtime["processors"]),
            strategy=str(runtime["strategy"]),
            metric=str(runtime["metric"]),
        )

        summary = _summarize_run(segments, range_end)

        results.append(
            {
                "task_set_index": ts_index,
                "algorithm_index": alg_index,
                "algorithm": algorithm,
                "segments": segments,
                "loads": loads,
                "overloaded": overloaded,
                "summary": summary,
            }
        )

    if not results:
        st.warning("No results were generated.")
        st.stop()

    st.subheader("Comparison Summary")
    summary_rows = []
    for result in results:
        ts_index = result["task_set_index"]
        alg_index = result["algorithm_index"]
        runtime = algorithm_runtime[alg_index]
        summary = result["summary"]

        summary_rows.append(
            {
                "Task Set": f"TS{ts_index + 1}",
                "Algorithm Slot": f"A{alg_index + 1}",
                "Algorithm": result["algorithm"],
                "Jobs Seen": summary["jobs_seen"],
                "Jobs Completed": summary["jobs_completed"],
                "Deadline Misses": summary["deadline_misses"],
                "Blocked Ticks": summary["blocked_ticks"],
                "Executed Ticks": summary["cpu_or_resource_ticks"],
                "Processors": int(runtime["processors"]),
                "Protocol": runtime["protocol"],
                "Frame Size": f"{result['loads'][0]:.0f}" if runtime["algorithm"] == "Cyclic Executive" and result["loads"] else "",
            }
        )

    st.dataframe(pd.DataFrame(summary_rows), use_container_width=True)

    st.subheader("Schedules")
    for result in results:
        ts_index = result["task_set_index"]
        alg_index = result["algorithm_index"]
        runtime = algorithm_runtime[alg_index]
        segments = result["segments"]

        heading = f"TS{ts_index + 1} -> A{alg_index + 1} ({result['algorithm']})"
        with st.expander(heading, expanded=False):
            if not segments:
                st.warning("No scheduled jobs for this run in the selected horizon.")
                continue

            fig = cached_schedule_figure(
                segments,
                title=heading,
                tick_step=tick_step,
                range_start=range_start,
                range_end=range_end,
            )
            st.plotly_chart(fig, use_container_width=True)

            png, png_error = schedule_png_bytes(fig)
            if png is not None:
                st.download_button(
                    label="Download schedule PNG",
                    data=png,
                    file_name=f"compare_ts{ts_index + 1}_a{alg_index + 1}.png",
                    mime="image/png",
                    key=f"dl_png_{ts_index}_{alg_index}",
                )
            elif png_error is not None:
                st.warning(png_error)

            ts_csv = build_task_dataframe(all_task_sets[ts_index], resource_names_for_task_set[ts_index])
            export_cols = st.columns(2)
            with export_cols[0]:
                st.download_button(
                    label="Download task set CSV",
                    data=task_csv_bytes(ts_csv),
                    file_name=f"compare_taskset_{ts_index + 1}.csv",
                    mime="text/csv",
                    key=f"dl_csv_{ts_index}_{alg_index}",
                )
            with export_cols[1]:
                st.download_button(
                    label="Download task set JSON",
                    data=task_json_bytes(ts_csv),
                    file_name=f"compare_taskset_{ts_index + 1}.json",
                    mime="application/json",
                    key=f"dl_json_{ts_index}_{alg_index}",
                )

            miss_details = _deadline_miss_details(segments, range_end)
            if not miss_details.empty:
                st.caption("Deadline miss details")
                st.dataframe(miss_details, use_container_width=True)

            if runtime["algorithm"].startswith("Partitioned") and result["loads"]:
                load_metric = str(runtime["metric"]).lower()
                for p_index, load in enumerate(result["loads"], start=1):
                    st.write(f"Processor P{p_index} load ({load_metric}): {load:.3f}")
                if result["overloaded"]:
                    st.warning("Partitioning exceeded per-processor capacity for this run.")