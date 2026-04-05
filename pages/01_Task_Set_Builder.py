import streamlit as st
from st_helpers import render_sidebar, render_task_inputs
from rt_utils import build_task_dataframe, task_csv_bytes

st.set_page_config(page_title="Task Set Builder", layout="wide")

st.title("Task Set Builder")

st.markdown(
    """
Create a custom task set and download it as CSV. Use the same structure on the
algorithm pages to generate schedules.
"""
)

render_sidebar("EDF", show_protocol=False)

st.subheader("Task Set Settings")
num_tasks = st.number_input("Number of tasks", min_value=1, max_value=12, value=3, step=1)

include_phase = st.checkbox("Include phase", value=True)
include_period = st.checkbox("Include period", value=True)
include_computation = st.checkbox("Include computation", value=True)
include_deadline = st.checkbox("Include deadline", value=True)
include_resources = st.checkbox("Include resources", value=False)

st.caption("This page only builds task sets. Execution order is configured on the analysis pages that use it.")

default_period = st.number_input("Default period", min_value=1, max_value=200, value=10, step=1)
default_computation = st.number_input("Default computation", min_value=1, max_value=200, value=2, step=1)

resource_count = 0
if include_resources:
    resource_count = st.number_input("Number of resources", min_value=1, max_value=4, value=1, step=1)

resource_names = [chr(ord("A") + i) for i in range(resource_count)]

st.subheader("Task Set Γ")
rows = render_task_inputs(
    int(num_tasks),
    include_phase,
    include_period,
    include_computation,
    include_deadline,
    include_resources,
    resource_names,
    int(default_period),
    int(default_computation),
    key_prefix="builder",
)

df = build_task_dataframe(rows, resource_names)
st.download_button(
    label="Download task set CSV",
    data=task_csv_bytes(df),
    file_name="task_set_gamma.csv",
    mime="text/csv",
)