import json
import random

import streamlit as st
from st_helpers import render_sidebar, render_task_inputs
from rt_utils import build_task_dataframe, compute_hyperperiod, task_csv_bytes, task_json_bytes

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


def _normalize_imported_rows(raw_tasks: object) -> list[dict[str, int]]:
    if not isinstance(raw_tasks, list):
        return []

    normalized: list[dict[str, int]] = []
    for item in raw_tasks:
        if not isinstance(item, dict):
            continue
        period = int(item.get("period", 10))
        computation = int(item.get("computation", 2))
        deadline = int(item.get("deadline", period))
        phase = int(item.get("phase", 0))
        normalized.append(
            {
                "phase": phase,
                "period": period,
                "computation": computation,
                "deadline": deadline,
            }
        )
    return normalized


def _generate_seeded_rows(
    count: int,
    seed: int,
    min_period: int,
    max_period: int,
    min_computation: int,
    max_computation: int,
) -> list[dict[str, int]]:
    rng = random.Random(seed)
    rows: list[dict[str, int]] = []
    for _ in range(count):
        period = rng.randint(min_period, max_period)
        period = max(period, min_computation)
        max_comp_bound = min(max_computation, period)
        computation = rng.randint(min_computation, max_comp_bound)
        deadline = rng.randint(computation, period)
        rows.append(
            {
                "phase": 0,
                "period": period,
                "computation": computation,
                "deadline": deadline,
            }
        )
    return rows

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

with st.expander("Seeded generator", expanded=False):
    g1, g2, g3 = st.columns(3)
    random_seed = int(g1.number_input("Seed", min_value=0, max_value=999_999, value=42, step=1))
    min_period = int(g2.number_input("Min period", min_value=1, max_value=200, value=5, step=1))
    max_period = int(g3.number_input("Max period", min_value=min_period, max_value=500, value=25, step=1))

    g4, g5 = st.columns(2)
    min_computation = int(g4.number_input("Min computation", min_value=1, max_value=200, value=1, step=1))
    max_computation = int(
        g5.number_input("Max computation", min_value=min_computation, max_value=200, value=6, step=1)
    )

    if st.button("Generate seeded task set"):
        generated_rows = _generate_seeded_rows(
            int(num_tasks),
            random_seed,
            min_period,
            max_period,
            min_computation,
            max_computation,
        )
        st.session_state["builder_seed_rows"] = generated_rows
        st.success(f"Generated {len(generated_rows)} task(s) with seed {random_seed}.")

include_phase = st.checkbox("Include phase", value=True)
include_period = st.checkbox("Include period", value=True)
include_computation = st.checkbox("Include computation", value=True)
include_deadline = st.checkbox("Include deadline", value=True)
include_resources = st.checkbox("Include resources", value=False)

st.caption("This page only builds task sets. Execution order is configured on the analysis pages that use it.")

uploaded_json = st.file_uploader("Import task set JSON", type=["json"])
if uploaded_json is not None:
    if st.button("Load JSON"):
        try:
            parsed = json.loads(uploaded_json.getvalue().decode("utf-8"))
            tasks_payload = parsed.get("tasks") if isinstance(parsed, dict) else parsed
            normalized_rows = _normalize_imported_rows(tasks_payload)
            if not normalized_rows:
                st.error("No valid tasks found in JSON.")
            else:
                st.session_state["builder_seed_rows"] = normalized_rows
                st.session_state["builder_num_tasks"] = len(normalized_rows)
                st.success(f"Loaded {len(normalized_rows)} task(s) from JSON.")
        except (UnicodeDecodeError, json.JSONDecodeError, ValueError, TypeError):
            st.error("Invalid JSON format.")

default_period = st.number_input("Default period", min_value=1, max_value=200, value=10, step=1)
default_computation = st.number_input("Default computation", min_value=1, max_value=200, value=2, step=1)
hyperperiod_threshold = int(
    st.number_input("Hyperperiod warning threshold", min_value=1, max_value=100_000, value=1000, step=1)
)

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

if "builder_scenarios" not in st.session_state:
    st.session_state["builder_scenarios"] = {}

st.subheader("Scenario Snapshots")
snap_cols = st.columns([2, 1, 1])
snapshot_name = snap_cols[0].text_input("Snapshot name", value="")
if snap_cols[1].button("Save snapshot") and snapshot_name.strip():
    st.session_state["builder_scenarios"][snapshot_name.strip()] = [
        {
            "phase": task.phase,
            "period": task.period,
            "computation": task.computation,
            "deadline": task.deadline,
        }
        for task in rows
    ]
    st.success(f"Saved snapshot '{snapshot_name.strip()}'.")

saved_names = sorted(st.session_state["builder_scenarios"].keys())
if saved_names:
    selected_snapshot = snap_cols[2].selectbox("Saved", saved_names)
    action_cols = st.columns(2)
    if action_cols[0].button("Load snapshot"):
        loaded_rows = st.session_state["builder_scenarios"][selected_snapshot]
        st.session_state["builder_seed_rows"] = loaded_rows
        st.session_state["builder_num_tasks"] = len(loaded_rows)
        st.success(f"Loaded snapshot '{selected_snapshot}'.")
    if action_cols[1].button("Delete snapshot"):
        del st.session_state["builder_scenarios"][selected_snapshot]
        st.success(f"Deleted snapshot '{selected_snapshot}'.")

df = build_task_dataframe(rows, resource_names)

periods = [task.period for task in rows if task.period > 0]
if periods:
    hyperperiod = compute_hyperperiod(periods)
    if hyperperiod > hyperperiod_threshold:
        st.warning(f"Hyperperiod is {hyperperiod}, which exceeds the threshold {hyperperiod_threshold}.")
    else:
        st.caption(f"Hyperperiod: {hyperperiod}")

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