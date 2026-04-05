import streamlit as st
import pandas as pd
from st_helpers import cached_schedule_figure, render_schedulability, render_task_inputs
from rt_utils import (
    build_task_dataframe,
    density,
    schedule_png_bytes,
    simulate_slack_stealing,
    slack_stealing_stats,
    simulate_uniprocessor,
    task_csv_bytes,
    utilisation,
)

st.set_page_config(page_title="Mixed Workload Analysis", layout="wide")
st.title("Mixed Workload Analysis")
st.caption("Compare baseline periodic EDF against slack stealing on the same workload.")
st.sidebar.header("Periodic Task Set")
num_tasks = st.sidebar.number_input("Number of periodic tasks", min_value=1, max_value=12, value=3, step=1)
include_phase = st.sidebar.checkbox("Include phase", value=True)
include_period = st.sidebar.checkbox("Include period", value=True)
include_computation = st.sidebar.checkbox("Include computation", value=True)
include_deadline = st.sidebar.checkbox("Include deadline", value=True)

default_phase = int(st.sidebar.number_input("Default phase", min_value=0, max_value=200, value=0, step=1))
default_period = int(st.sidebar.number_input("Default period", min_value=1, max_value=200, value=10, step=1))
default_computation = int(st.sidebar.number_input("Default computation", min_value=1, max_value=200, value=2, step=1))
default_deadline = int(
    st.sidebar.number_input("Default deadline", min_value=1, max_value=200, value=default_period, step=1)
)

st.subheader("Periodic Task Set Γ")
periodic_rows = render_task_inputs(
    int(num_tasks),
    include_phase,
    include_period,
    include_computation,
    include_deadline,
    include_resources=False,
    resource_names=[],
    default_period=default_period,
    default_computation=default_computation,
    key_prefix="mixed_workload_periodic",
    default_phase=default_phase,
    default_deadline=default_deadline,
)

st.subheader("Periodic Feasibility")
render_schedulability(periodic_rows, "EDF")
st.sidebar.header("Aperiodic Jobs")
num_aperiodic = int(st.sidebar.number_input("Number of aperiodic jobs", min_value=0, max_value=12, value=3, step=1))
aperiodic_defaults = []
for index in range(num_aperiodic):
    st.sidebar.markdown(f"**Aperiodic job {index + 1}**")
    release = int(
        st.sidebar.number_input(
            f"AP{index + 1} release",
            min_value=0,
            max_value=500,
            value=index * 4,
            step=1,
            key=f"mixed_ap_release_{index}",
        )
    )
    computation = int(
        st.sidebar.number_input(
            f"AP{index + 1} computation",
            min_value=1,
            max_value=200,
            value=2,
            step=1,
            key=f"mixed_ap_comp_{index}",
        )
    )
    rel_deadline = int(
        st.sidebar.number_input(
            f"AP{index + 1} relative deadline",
            min_value=1,
            max_value=500,
            value=max(5, computation + 1),
            step=1,
            key=f"mixed_ap_deadline_{index}",
        )
    )
    aperiodic_defaults.append(
        {
            "job_id": index + 1,
            "release": release,
            "computation": computation,
            "deadline": release + rel_deadline,
        }
    )

if aperiodic_defaults:
    st.subheader("Aperiodic Queue")
    ap_df = pd.DataFrame(aperiodic_defaults).rename(columns={"job_id": "aperiodic_id", "deadline": "absolute_deadline"})
    st.dataframe(ap_df, use_container_width=True)

st.sidebar.header("Analysis Window")
range_start = int(st.sidebar.number_input("Time range start", min_value=0, max_value=500, value=0, step=1))
range_end = int(st.sidebar.number_input("Time range end", min_value=1, max_value=500, value=40, step=1))
tick_step = int(st.sidebar.number_input("Time tick step", min_value=1, max_value=50, value=5, step=1))


def _summarize_segments(segments: list[dict[str, object]], horizon: int) -> dict[str, int]:
    if not segments:
        return {"jobs": 0, "completed": 0, "deadline_misses": 0, "ticks": 0}

    df = pd.DataFrame(segments)
    if df.empty:
        return {"jobs": 0, "completed": 0, "deadline_misses": 0, "ticks": 0}

    jobs = df["job"].nunique() if "job" in df.columns else 0
    executed_df = df[df["phase"] != "Blocked"] if "phase" in df.columns else df
    ticks = len(executed_df)
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
        if float(row.get("remaining", 1)) == 0:
            end_time = float(row.get("end", 0))
            if job_id not in completions or end_time < completions[job_id][0]:
                completions[job_id] = (end_time, deadline)

    deadline_misses = sum(1 for end_time, deadline in completions.values() if end_time > deadline)
    for job_id, deadline in deadlines.items():
        if deadline <= horizon and job_id not in completions:
            deadline_misses += 1

    return {"jobs": int(jobs), "completed": int(len(completions)), "deadline_misses": int(deadline_misses), "ticks": int(ticks)}


def _summarize_aperiodic_jobs(stats_df: pd.DataFrame) -> dict[str, int]:
    if stats_df.empty:
        return {"jobs": 0, "completed": 0, "deadline_misses": 0}

    completed = int(stats_df["completed"].sum()) if "completed" in stats_df.columns else 0
    deadline_misses = int(stats_df["deadline_missed"].sum()) if "deadline_missed" in stats_df.columns else 0
    return {"jobs": int(len(stats_df)), "completed": completed, "deadline_misses": deadline_misses}

if st.button("Run mixed workload analysis", type="primary"):
    if range_end <= range_start:
        st.error("Time range end must be greater than start.")
        st.stop()

    periodic_df = build_task_dataframe(periodic_rows, [])
    st.download_button(
        label="Download periodic task set CSV",
        data=task_csv_bytes(periodic_df),
        file_name="mixed_workload_periodic_tasks.csv",
        mime="text/csv",
    )

    if aperiodic_defaults:
        ap_export_df = pd.DataFrame(aperiodic_defaults)
        st.download_button(
            label="Download aperiodic jobs CSV",
            data=task_csv_bytes(ap_export_df),
            file_name="mixed_workload_aperiodic_jobs.csv",
            mime="text/csv",
        )

    baseline_segments = simulate_uniprocessor(periodic_rows, range_end, "EDF", "None", "CPU then resources")
    slack_segments = simulate_slack_stealing(periodic_rows, aperiodic_defaults, range_end)
    slack_metrics, slack_stats_df = slack_stealing_stats(slack_segments, aperiodic_defaults, range_end)
    baseline_summary = _summarize_segments(baseline_segments, range_end)
    aperiodic_summary = _summarize_aperiodic_jobs(slack_stats_df)

    st.subheader("Comparison Summary")
    st.caption("Baseline EDF measures the periodic workload; slack-stealing metrics reflect aperiodic jobs reclaimed in idle time.")
    summary_cols = st.columns(6)
    summary_cols[0].metric("Utilisation", f"{utilisation(periodic_rows):.3f}")
    summary_cols[1].metric("Density", f"{density(periodic_rows):.3f}")
    summary_cols[2].metric("Periodic EDF", f"{baseline_summary['completed']}/{baseline_summary['jobs']}")
    summary_cols[3].metric("Aperiodic jobs", f"{aperiodic_summary['completed']}/{aperiodic_summary['jobs']}")
    summary_cols[4].metric("Aperiodic completion", f"{100.0 * slack_metrics['completion_ratio']:.1f}%")
    summary_cols[5].metric("Slack used", f"{slack_metrics['total_slack_used']:.0f}")

    st.dataframe(
        pd.DataFrame(
            [
                {
                    "Run": "Baseline EDF",
                    "Scope": "Periodic jobs",
                    "Jobs Seen": baseline_summary["jobs"],
                    "Jobs Completed": baseline_summary["completed"],
                    "Deadline Misses": baseline_summary["deadline_misses"],
                    "Executed Ticks": baseline_summary["ticks"],
                },
                {
                    "Run": "Slack Stealing",
                    "Scope": "Aperiodic jobs",
                    "Jobs Seen": aperiodic_summary["jobs"],
                    "Jobs Completed": aperiodic_summary["completed"],
                    "Deadline Misses": aperiodic_summary["deadline_misses"],
                    "Executed Ticks": int(slack_metrics["total_slack_used"]),
                },
            ]
        ),
        use_container_width=True,
        hide_index=True,
    )

    st.subheader("Schedules")
    schedule_cols = st.columns(2)
    with schedule_cols[0]:
        st.markdown("**Baseline EDF**")
        if baseline_segments:
            baseline_fig = cached_schedule_figure(
                baseline_segments,
                "Baseline EDF Schedule",
                tick_step=tick_step,
                range_start=range_start,
                range_end=range_end,
            )
            st.plotly_chart(baseline_fig, use_container_width=True)
            png, png_error = schedule_png_bytes(baseline_fig)
            if png is not None:
                st.download_button(
                    label="Download baseline PNG",
                    data=png,
                    file_name="mixed_workload_edf.png",
                    mime="image/png",
                )
            elif png_error is not None:
                st.warning(png_error)
        else:
            st.warning("No periodic schedule was generated in the selected horizon.")

    with schedule_cols[1]:
        st.markdown("**Slack Stealing**")
        if slack_segments:
            slack_fig = cached_schedule_figure(
                slack_segments,
                "Slack Stealing Schedule",
                tick_step=tick_step,
                range_start=range_start,
                range_end=range_end,
            )
            st.plotly_chart(slack_fig, use_container_width=True)
            png, png_error = schedule_png_bytes(slack_fig)
            if png is not None:
                st.download_button(
                    label="Download slack PNG",
                    data=png,
                    file_name="mixed_workload_slack_stealing.png",
                    mime="image/png",
                )
            elif png_error is not None:
                st.warning(png_error)
        else:
            st.warning("No slack-stealing schedule was generated in the selected horizon.")

    st.subheader("Aperiodic Outcomes")
    if not slack_stats_df.empty:
        st.dataframe(slack_stats_df, use_container_width=True)
    else:
        st.info("Add aperiodic jobs to see per-job outcomes.")