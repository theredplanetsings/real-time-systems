import streamlit as st
import plotly.express as px
from st_helpers import render_schedulability, render_sidebar, render_task_inputs
from rt_utils import TaskSpec, build_task_dataframe, task_csv_bytes, time_demand_analysis

st.set_page_config(page_title="Time Demand", layout="wide")

st.title("Time Demand Analysis")

render_sidebar("Time Demand", show_protocol=True)

st.sidebar.header("Task Set")
num_tasks = st.sidebar.number_input("Number of tasks", min_value=1, max_value=12, value=3, step=1)
include_phase = st.sidebar.checkbox("Include phase", value=False)
include_period = st.sidebar.checkbox("Include period", value=True)
include_computation = st.sidebar.checkbox("Include computation", value=True)
resource_order = st.sidebar.selectbox("Execution order", ["CPU then resources", "Resources then CPU"])

default_period = st.sidebar.number_input("Default period", min_value=1, max_value=200, value=10, step=1)
default_computation = st.sidebar.number_input("Default computation", min_value=1, max_value=200, value=2, step=1)

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
    key_prefix="time_demand",
)

st.subheader("Schedulability")
render_schedulability(rows, "Time Demand")

horizon = st.number_input("Analysis horizon", min_value=1, max_value=200, value=50, step=1)

if st.button("Analyse time demand"):
    df = build_task_dataframe(rows, [])
    st.download_button(
        label="Download task set CSV",
        data=task_csv_bytes(df),
        file_name="task_set_gamma.csv",
        mime="text/csv",
    )

    target_task_id = st.selectbox("Target task", [task.task_id for task in rows])
    td_df = time_demand_analysis(rows, int(target_task_id), int(horizon))

    fig = px.line(td_df, x="time", y="demand", title="Time Demand Function")
    fig.add_scatter(x=td_df["time"], y=td_df["time"], mode="lines", name="t")
    st.plotly_chart(fig, use_container_width=True)