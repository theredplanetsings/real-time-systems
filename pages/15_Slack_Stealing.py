import streamlit as st
import pandas as pd
from st_helpers import cached_schedule_figure, render_schedulability, render_task_inputs
from rt_utils import (
    build_task_dataframe,
    schedule_png_bytes,
    simulate_slack_stealing,
    slack_stealing_stats,
    task_csv_bytes,
)

st.set_page_config(page_title="Slack Stealing", layout="wide")
st.title("Slack Stealing")
st.caption(
    "Periodic EDF tasks run first; ready aperiodic jobs reclaim slack when periodic demand is idle."
)
st.sidebar.header("Mode")
policy = st.sidebar.selectbox(
    "Slack policy",
    ["Idle-time reclamation"],
    index=0,
)
st.sidebar.caption(f"Policy: {policy}")
st.sidebar.header("Periodic Task Set")
num_tasks = st.sidebar.number_input(
    "Number of periodic tasks", min_value=1, max_value=12, value=3, step=1
)
include_phase = st.sidebar.checkbox("Include phase", value=True)
include_period = st.sidebar.checkbox("Include period", value=True)
include_computation = st.sidebar.checkbox("Include computation", value=True)
include_deadline = st.sidebar.checkbox("Include deadline", value=True)

default_phase = int(
    st.sidebar.number_input("Default phase", min_value=0, max_value=200, value=0, step=1)
)
default_period = int(
    st.sidebar.number_input("Default period", min_value=1, max_value=200, value=10, step=1)
)
default_computation = int(
    st.sidebar.number_input("Default computation", min_value=1, max_value=200, value=2, step=1)
)
default_deadline = int(
    st.sidebar.number_input(
        "Default deadline", min_value=1, max_value=200, value=default_period, step=1
    )
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
    key_prefix="slack_stealing_periodic",
    default_phase=default_phase,
    default_deadline=default_deadline,
)

st.subheader("Periodic Feasibility")
render_schedulability(periodic_rows, "EDF")
st.sidebar.header("Aperiodic Jobs")
num_aperiodic = int(
    st.sidebar.number_input("Number of aperiodic jobs", min_value=0, max_value=12, value=3, step=1)
)
aperiodic_defaults = []
for i in range(num_aperiodic):
    st.sidebar.markdown(f"**Aperiodic job {i + 1}**")
    release = int(
        st.sidebar.number_input(
            f"AP{i + 1} release",
            min_value=0,
            max_value=500,
            value=i * 4,
            step=1,
            key=f"slack_ap_release_{i}",
        )
    )
    computation = int(
        st.sidebar.number_input(
            f"AP{i + 1} computation",
            min_value=1,
            max_value=200,
            value=2,
            step=1,
            key=f"slack_ap_comp_{i}",
        )
    )
    rel_deadline = int(
        st.sidebar.number_input(
            f"AP{i + 1} relative deadline",
            min_value=1,
            max_value=500,
            value=max(5, computation + 1),
            step=1,
            key=f"slack_ap_deadline_{i}",
        )
    )
    aperiodic_defaults.append(
        {
            "job_id": i + 1,
            "release": release,
            "computation": computation,
            "deadline": release + rel_deadline,
        }
    )

if aperiodic_defaults:
    st.subheader("Aperiodic Queue")
    ap_df = pd.DataFrame(aperiodic_defaults)
    ap_df = ap_df.rename(columns={"job_id": "aperiodic_id", "deadline": "absolute_deadline"})
    st.dataframe(ap_df, use_container_width=True)

range_start = st.number_input("Time range start", min_value=0, max_value=500, value=0, step=1)
range_end = st.number_input("Time range end", min_value=1, max_value=500, value=40, step=1)
tick_step = st.number_input("Time tick step", min_value=1, max_value=50, value=5, step=1)

if st.button("Generate Slack Stealing schedule"):
    if int(range_end) <= int(range_start):
        st.warning("Time range end must be greater than start.")
        st.stop()

    periodic_df = build_task_dataframe(periodic_rows, [])
    st.download_button(
        label="Download periodic task set CSV",
        data=task_csv_bytes(periodic_df),
        file_name="slack_stealing_periodic_tasks.csv",
        mime="text/csv",
    )

    if aperiodic_defaults:
        ap_export_df = pd.DataFrame(aperiodic_defaults)
        st.download_button(
            label="Download aperiodic jobs CSV",
            data=task_csv_bytes(ap_export_df),
            file_name="slack_stealing_aperiodic_jobs.csv",
            mime="text/csv",
        )

    segments = simulate_slack_stealing(periodic_rows, aperiodic_defaults, int(range_end))
    st.caption(f"Segments generated: {len(segments)}")
    if not segments:
        st.warning(
            "No scheduled jobs for the current range. Increase the range or check task parameters."
        )

    fig = cached_schedule_figure(
        segments,
        "Slack Stealing Schedule",
        tick_step=int(tick_step),
        range_start=int(range_start),
        range_end=int(range_end),
    )
    st.plotly_chart(fig, use_container_width=True)

    metrics, stats_df = slack_stealing_stats(segments, aperiodic_defaults, int(range_end))

    st.subheader("Slack Stats")
    kpi_cols = st.columns(6)
    kpi_cols[0].metric("Total slack used", f"{metrics['total_slack_used']:.0f}")
    kpi_cols[1].metric("Completion ratio", f"{100.0 * metrics['completion_ratio']:.1f}%")
    kpi_cols[2].metric("Mean response", f"{metrics['mean_response_time']:.2f}")
    kpi_cols[3].metric("Mean waiting", f"{metrics['mean_waiting_time']:.2f}")
    kpi_cols[4].metric("Max waiting", f"{metrics['max_waiting_time']:.2f}")
    kpi_cols[5].metric("Deadline misses", f"{metrics['deadline_misses']:.0f}")

    if not stats_df.empty:
        st.caption("Aperiodic job outcomes")
        st.dataframe(stats_df, use_container_width=True)

    png, png_error = schedule_png_bytes(fig)
    if png is None:
        st.warning(
            png_error
            or "PNG export requires Kaleido. Install it with `pip install --upgrade kaleido`."
        )
    else:
        st.download_button(
            label="Download schedule PNG",
            data=png,
            file_name="slack_stealing_schedule.png",
            mime="image/png",
        )
