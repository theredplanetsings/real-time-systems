import streamlit as st
from st_helpers import render_sidebar, render_task_inputs
from rt_utils import build_task_dataframe, task_csv_bytes, task_json_bytes

PRESET_TASK_SETS = {
    "Balanced Trio": [
        {"phase": 0, "period": 5, "computation": 1, "deadline": 5},
        {"phase": 0, "period": 10, "computation": 2, "deadline": 10},
        {"phase": 0, "period": 20, "computation": 4, "deadline": 20},
    ],
    "Tight Deadlines": [
        {"phase": 0, "period": 6, "computation": 2, "deadline": 4},
        {"phase": 0, "period": 8, "computation": 2, "deadline": 5},
        {"phase": 0, "period": 12, "computation": 3, "deadline": 6},
    ],
    "Harmonic Four": [
        {"phase": 0, "period": 4, "computation": 1, "deadline": 4},
        {"phase": 0, "period": 8, "computation": 2, "deadline": 8},
        {"phase": 0, "period": 16, "computation": 3, "deadline": 16},
        {"phase": 0, "period": 32, "computation": 5, "deadline": 32},
    ],
}

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
if "builder_num_tasks" not in st.session_state:
    st.session_state["builder_num_tasks"] = 3

preset_col, apply_col = st.columns([3, 1])
selected_preset = preset_col.selectbox("Preset", ["Custom"] + list(PRESET_TASK_SETS.keys()), index=0)
if apply_col.button("Load preset") and selected_preset != "Custom":
    st.session_state["builder_seed_rows"] = PRESET_TASK_SETS[selected_preset]
    st.session_state["builder_num_tasks"] = len(PRESET_TASK_SETS[selected_preset])

num_tasks = st.number_input(
    "Number of tasks",
    min_value=1,
    max_value=12,
    value=int(st.session_state["builder_num_tasks"]),
    step=1,
    key="builder_num_tasks",
)

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
    initial_rows=st.session_state.get("builder_seed_rows"),
)

st.session_state["builder_seed_rows"] = None

df = build_task_dataframe(rows, resource_names)
download_cols = st.columns(2)
with download_cols[0]:
    st.download_button(
        label="Download task set CSV",
        data=task_csv_bytes(df),
        file_name="task_set_gamma.csv",
        mime="text/csv",
    )
with download_cols[1]:
    st.download_button(
        label="Download task set JSON",
        data=task_json_bytes(df),
        file_name="task_set_gamma.json",
        mime="application/json",
    )