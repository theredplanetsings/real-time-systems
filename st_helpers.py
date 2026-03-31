from typing import List, Optional
import streamlit as st
import pandas as pd

from rt_utils import ALGORITHMS, PROTOCOLS, TaskSpec, schedulability_summary

PAGE_MAP = {
    "EDF": "pages/02_EDF.py",
    "EDD": "pages/03_EDD.py",
    "RM": "pages/04_RM.py",
    "DM": "pages/05_DM.py",
    "Cyclic Executive": "pages/06_Cyclic_Executive.py",
    "Global RM": "pages/07_Global_RM.py",
    "Global EDF": "pages/10_Global_EDF.py",
    "Time Demand": "pages/08_Time_Demand.py",
    "Priority Inversion": "pages/09_Priority_Inversion.py",
}

def render_sidebar(current_algorithm: str, show_protocol: bool = True) -> Optional[str]:
    protocol = None
    if show_protocol:
        st.sidebar.header("Protocol")
        protocol = st.sidebar.selectbox("Resource protocol", PROTOCOLS)

    return protocol

def render_task_inputs(
    num_tasks: int,
    include_phase: bool,
    include_period: bool,
    include_computation: bool,
    include_deadline: bool,
    include_resources: bool,
    resource_names: List[str],
    default_period: int,
    default_computation: int,
    key_prefix: str,
) -> List[TaskSpec]:
    columns = ["task_id"]
    if include_phase:
        columns.append("phase")
    if include_period:
        columns.append("period")
    if include_computation:
        columns.append("computation")
    if include_deadline:
        columns.append("deadline")
    if include_resources:
        columns.extend([f"resource_{res}" for res in resource_names])

    data = []
    for i in range(num_tasks):
        row = {"task_id": i + 1}
        if include_phase:
            row["phase"] = 0
        if include_period:
            row["period"] = default_period
        if include_computation:
            row["computation"] = default_computation
        if include_deadline:
            row["deadline"] = default_period
        if include_resources:
            for res in resource_names:
                row[f"resource_{res}"] = 0
        data.append(row)

    height = min(600, 50 + num_tasks * 35)
    edited = st.data_editor(
        data,
        num_rows="fixed",
        use_container_width=True,
        hide_index=True,
        key=f"{key_prefix}_task_editor",
        column_order=columns,
        height=height,
    )

    if isinstance(edited, list):
        df = pd.DataFrame(edited)
    else:
        df = edited

    rows: List[TaskSpec] = []
    for _, row in df.iterrows():
        task_id = int(row.get("task_id", 0))
        phase = int(row.get("phase", 0))
        period = int(row.get("period", default_period))
        computation = int(row.get("computation", default_computation))
        deadline = int(row.get("deadline", period))
        resources = {}
        if include_resources:
            for res in resource_names:
                resources[res] = int(row.get(f"resource_{res}", 0))
        rows.append(TaskSpec(task_id, phase, period, computation, deadline, resources))

    return rows

def render_schedulability(tasks: List[TaskSpec], algorithm: str, processors: int = 1) -> None:
    summary = schedulability_summary(tasks, algorithm, processors)
    util = summary["utilisation"]
    dens = summary["density"]

    cols = st.columns(3)
    cols[0].metric("Utilisation", f"{util:.3f}")
    cols[1].metric("Density", f"{dens:.3f}")
    cols[2].metric("Algorithm", summary["algorithm"])

    if summary["status"] == "pass":
        st.success(summary["detail"])
    elif summary["status"] == "warn":
        st.warning(summary["detail"])
        metric = summary.get("metric")
        limit = summary.get("limit")
        value = summary.get("value")
        if metric is not None and limit is not None and value is not None and limit == 1.0:
            st.error(
                f"{metric} {value:.3f} exceeds limit {limit:.3f}. "
                "Reduce computation or increase period/deadline."
            )
    else:
        st.info(summary["detail"])