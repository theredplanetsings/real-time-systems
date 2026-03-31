import streamlit as st
from st_helpers import render_schedulability, render_sidebar, render_task_inputs
from rt_utils import (
    TaskSpec,
    build_task_dataframe,
    schedule_figure,
    schedule_png_bytes,
    simulate_partitioned,
    task_csv_bytes,
)

st.set_page_config(page_title="Partitioned RM", layout="wide")

st.title("Partitioned RM Scheduling")

render_sidebar("Partitioned RM", show_protocol=True)

st.sidebar.header("Task Set")
num_tasks = st.sidebar.number_input("Number of tasks", min_value=1, max_value=12, value=3, step=1)
include_phase = st.sidebar.checkbox("Include phase", value=False)
include_period = st.sidebar.checkbox("Include period", value=True)
include_computation = st.sidebar.checkbox("Include computation", value=True)
include_deadline = st.sidebar.checkbox("Include deadline", value=True)
resource_order = st.sidebar.selectbox("Execution order", ["CPU then resources", "Resources then CPU"])

default_period = st.sidebar.number_input("Default period", min_value=1, max_value=200, value=10, step=1)
default_computation = st.sidebar.number_input("Default computation", min_value=1, max_value=200, value=2, step=1)

processors = st.sidebar.number_input("Processors", min_value=1, max_value=8, value=2, step=1)
strategy = st.sidebar.selectbox(
    "Partitioning strategy",
    ["First-fit decreasing", "Best-fit", "Worst-fit"],
)
metric = st.sidebar.selectbox("Packing metric", ["Utilisation", "Density"])

st.subheader("Task Set Γ")
rows = render_task_inputs(
    int(num_tasks),
    include_phase,
    include_period,
    include_computation,
    include_deadline,
    include_resources=False,
    resource_names=[],
    default_period=int(default_period),
    default_computation=int(default_computation),
    key_prefix="partitioned_rm",
)

st.subheader("Schedulability")
render_schedulability(rows, "Partitioned RM", processors=int(processors))

range_start = st.number_input("Time range start", min_value=0, max_value=500, value=0, step=1)
range_end = st.number_input("Time range end", min_value=1, max_value=500, value=25, step=1)
tick_step = st.number_input("Time tick step", min_value=1, max_value=50, value=5, step=1)

if st.button("Generate Partitioned RM schedule"):
    df = build_task_dataframe(rows, [])
    st.download_button(
        label="Download task set CSV",
        data=task_csv_bytes(df),
        file_name="task_set_gamma.csv",
        mime="text/csv",
    )

    if int(range_end) <= int(range_start):
        st.warning("Time range end must be greater than start.")
        st.stop()

    segments, loads, overloaded = simulate_partitioned(
        rows,
        int(range_end),
        int(processors),
        "RM",
        strategy,
        metric,
    )
    st.caption(f"Segments generated: {len(segments)}")
    if overloaded:
        st.warning("Partitioning exceeds per-processor capacity. Adjust tasks or processors.")
    if not segments:
        st.warning("No scheduled jobs for the current range. Increase the range or check task parameters.")
    fig = schedule_figure(
        segments,
        "Partitioned RM Schedule",
        tick_step=int(tick_step),
        range_start=int(range_start),
        range_end=int(range_end),
    )
    st.plotly_chart(fig, use_container_width=True)

    png = schedule_png_bytes(fig)
    if png is None:
        st.warning("PNG export requires Kaleido. Install it with `pip install --upgrade kaleido`.")
    else:
        st.download_button(
            label="Download schedule PNG",
            data=png,
            file_name="partitioned_rm_schedule.png",
            mime="image/png",
        )

    for idx, load in enumerate(loads, start=1):
        st.write(f"Processor P{idx} load ({metric.lower()}): {load:.3f}")