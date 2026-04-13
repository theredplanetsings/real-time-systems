import streamlit as st
from st_helpers import (
    cached_schedule_figure,
    render_schedulability,
    render_sidebar,
    render_task_inputs,
)
from rt_utils import (
    build_task_dataframe,
    cyclic_executive_frames,
    cyclic_executive_schedule,
    schedule_png_bytes,
    task_csv_bytes,
)

st.set_page_config(page_title="Cyclic Executive", layout="wide")

st.title("Cyclic Executive")

render_sidebar("Cyclic Executive", show_protocol=True)

st.sidebar.header("Task Set")
num_tasks = st.sidebar.number_input("Number of tasks", min_value=1, max_value=12, value=3, step=1)
include_phase = st.sidebar.checkbox("Include phase", value=False)
include_period = st.sidebar.checkbox("Include period", value=True)
include_computation = st.sidebar.checkbox("Include computation", value=True)
resource_order = st.sidebar.selectbox(
    "Execution order", ["CPU then resources", "Resources then CPU"]
)

default_period = st.sidebar.number_input(
    "Default period", min_value=1, max_value=200, value=10, step=1
)
default_computation = st.sidebar.number_input(
    "Default computation", min_value=1, max_value=200, value=2, step=1
)

st.subheader("Task Set Γ")
rows = render_task_inputs(
    int(num_tasks),
    include_phase,
    include_period,
    include_computation,
    include_deadline=False,
    include_resources=False,
    resource_names=[],
    default_period=int(default_period),
    default_computation=int(default_computation),
    key_prefix="cyclic",
)

st.subheader("Schedulability")
render_schedulability(rows, "Cyclic Executive")

if st.button("Analyse frame sizes"):
    df = build_task_dataframe(rows, [])
    st.download_button(
        label="Download task set CSV",
        data=task_csv_bytes(df),
        file_name="task_set_gamma.csv",
        mime="text/csv",
    )

    hyper, valid = cyclic_executive_frames(rows)
    st.write(f"Hyperperiod: {hyper}")
    st.write("Valid frame sizes:", valid)

    if valid:
        frame = st.number_input(
            "Frame size", min_value=1, max_value=hyper, value=int(valid[0]), step=1
        )
        range_start = st.number_input(
            "Time range start", min_value=0, max_value=hyper, value=0, step=1
        )
        range_end = st.number_input(
            "Time range end", min_value=1, max_value=hyper, value=min(25, hyper), step=1
        )
        tick_step = st.number_input("Time tick step", min_value=1, max_value=50, value=5, step=1)

        if int(range_end) <= int(range_start):
            st.warning("Time range end must be greater than start.")
            st.stop()

        segments = cyclic_executive_schedule(rows, int(frame))
        st.caption(f"Segments generated: {len(segments)}")
        if not segments:
            st.warning(
                "No scheduled jobs for the current frame. Adjust the frame size or task parameters."
            )
        fig = cached_schedule_figure(
            segments,
            "Cyclic Executive Schedule",
            tick_step=int(tick_step),
            range_start=int(range_start),
            range_end=int(range_end),
        )
        st.plotly_chart(fig, use_container_width=True)

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
                file_name="cyclic_executive_schedule.png",
                mime="image/png",
            )
    else:
        st.warning("No valid frame sizes found for this task set.")
