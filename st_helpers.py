from typing import List, Optional
import streamlit as st
import pandas as pd

from rt_utils import (
    ALGORITHM_FAMILIES,
    PROTOCOLS,
    TaskSpec,
    build_task_dataframe,
    family_names,
    schedulability_summary,
    schedule_figure,
    schedule_png_bytes,
    simulate_global_dm,
    simulate_global_edf,
    simulate_global_rm,
    simulate_partitioned,
    simulate_uniprocessor,
    task_csv_bytes,
    variants_for_family,
)

def render_sidebar(_current_algorithm: str, show_protocol: bool = True) -> Optional[str]:
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
    default_phase: int = 0,
    default_deadline: Optional[int] = None,
    default_resource_time: int = 0,
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
            row["phase"] = default_phase
        if include_period:
            row["period"] = default_period
        if include_computation:
            row["computation"] = default_computation
        if include_deadline:
            row["deadline"] = default_deadline if default_deadline is not None else default_period
        if include_resources:
            for res in resource_names:
                row[f"resource_{res}"] = default_resource_time
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


@st.cache_data(show_spinner=False)
def cached_schedule_figure(
    segments: list[dict[str, object]],
    title: str,
    tick_step: Optional[int] = None,
    range_start: Optional[int] = None,
    range_end: Optional[int] = None,
):
    return schedule_figure(
        segments,
        title,
        tick_step=tick_step,
        range_start=range_start,
        range_end=range_end,
    )


def render_algorithm_workbench(
    *,
    initial_family: Optional[str] = None,
    initial_variant: Optional[str] = None,
    lock_selection: bool = False,
    show_retired_notice: bool = False,
) -> None:
    families = family_names()
    default_family = initial_family or st.session_state.get("explorer_family", families[0] if families else "EDF")
    family_index = families.index(default_family) if default_family in families else 0

    if lock_selection:
        family = families[family_index]
        st.write(f"Algorithm family: **{family}**")
    else:
        family = st.radio("Algorithm family", families, index=family_index, horizontal=True)
    st.session_state["explorer_family"] = family

    family_meta = ALGORITHM_FAMILIES[family]
    variants = variants_for_family(family)
    default_variant = initial_variant or st.session_state.get(
        "explorer_variant", variants[0] if variants else "Uniprocessor"
    )
    variant_index = variants.index(default_variant) if default_variant in variants else 0

    if lock_selection:
        variant = variants[variant_index]
        st.write(f"Variant: **{variant}**")
    else:
        variant = st.radio("Variant", variants, index=variant_index, horizontal=True)
    st.session_state["explorer_variant"] = variant

    if show_retired_notice:
        st.warning(
            "This page is retired. Use Algorithm Explorer for the streamlined workflow."
        )

    if len(variants) == 1 and not lock_selection:
        st.info("Only uniprocessor mode is currently available for this family.")

    variant_meta = family_meta["variants"][variant]
    algorithm_name = str(variant_meta["algorithm"])
    mode = str(variant_meta["mode"])

    st.write(f"Selected: **{family}** ({family_meta['label']}) -> **{variant}**")

    protocol = "None"

    st.sidebar.header("Task Set")
    num_tasks = st.sidebar.number_input("Number of tasks", min_value=1, max_value=12, value=3, step=1)

    st.sidebar.subheader("Included Parameters")
    include_phase_default = mode == "uniprocessor"
    include_phase = st.sidebar.checkbox("Include phase", value=include_phase_default)
    include_period = st.sidebar.checkbox("Include period", value=True)
    include_computation = st.sidebar.checkbox("Include computation", value=True)
    include_deadline = st.sidebar.checkbox("Include deadline", value=family in {"EDF", "EDD", "DM"})

    include_resources = st.sidebar.checkbox("Include resources", value=False)
    resource_order = "CPU then resources"
    resource_names: List[str] = []
    default_phase = 0
    default_period = 10
    default_computation = 2
    default_deadline = 10
    default_resource_time = 0

    st.sidebar.subheader("Default Values")
    if include_phase:
        default_phase = int(
            st.sidebar.number_input("Default phase", min_value=0, max_value=200, value=0, step=1)
        )

    if include_period:
        default_period = int(
            st.sidebar.number_input("Default period", min_value=1, max_value=200, value=10, step=1)
        )

    if include_computation:
        default_computation = int(
            st.sidebar.number_input("Default computation", min_value=1, max_value=200, value=2, step=1)
        )

    if include_deadline:
        default_deadline = int(
            st.sidebar.number_input(
                "Default deadline",
                min_value=1,
                max_value=200,
                value=default_period,
                step=1,
            )
        )

    if include_resources:
        resource_count = int(
            st.sidebar.number_input("Number of resources", min_value=1, max_value=4, value=1, step=1)
        )
        default_resource_time = int(
            st.sidebar.number_input("Default resource time", min_value=0, max_value=50, value=0, step=1)
        )
        resource_names = [chr(ord("A") + i) for i in range(resource_count)]

    if include_resources and mode in {"uniprocessor", "partitioned"}:
        st.sidebar.subheader("Resource Protocol")
        protocol = st.sidebar.radio("Resource protocol", PROTOCOLS, index=0, horizontal=True)
        resource_order = st.sidebar.selectbox("Execution order", ["CPU then resources", "Resources then CPU"])

    if mode == "global" and include_resources:
        st.sidebar.info("Global variants currently ignore resource execution segments.")

    processors = 1
    if mode in {"global", "partitioned"}:
        processors = int(st.sidebar.number_input("Processors", min_value=1, max_value=8, value=2, step=1))

    strategy = "First-fit decreasing"
    metric = "Utilisation"
    if mode == "partitioned":
        strategy = st.sidebar.selectbox("Partitioning strategy", ["First-fit decreasing", "Best-fit", "Worst-fit"])
        metric = st.sidebar.selectbox("Packing metric", ["Utilisation", "Density"])

    st.subheader("Task Set Γ")
    rows = render_task_inputs(
        int(num_tasks),
        include_phase,
        include_period,
        include_computation,
        include_deadline,
        include_resources,
        resource_names,
        default_period,
        default_computation,
        key_prefix=f"explorer_{family.lower()}_{variant.lower()}",
        default_phase=default_phase,
        default_deadline=default_deadline,
        default_resource_time=default_resource_time,
    )

    st.subheader("Schedulability")
    render_schedulability(rows, algorithm_name, processors=processors)

    range_start = st.number_input("Time range start", min_value=0, max_value=500, value=0, step=1)
    range_end = st.number_input("Time range end", min_value=1, max_value=500, value=25, step=1)
    tick_step = st.number_input("Time tick step", min_value=1, max_value=50, value=5, step=1)

    if st.button(f"Generate {algorithm_name} schedule"):
        df = build_task_dataframe(rows, resource_names)
        st.download_button(
            label="Download task set CSV",
            data=task_csv_bytes(df),
            file_name="task_set_gamma.csv",
            mime="text/csv",
        )

        if int(range_end) <= int(range_start):
            st.warning("Time range end must be greater than start.")
            st.stop()

        segments = []
        loads = []
        overloaded = False

        if mode == "uniprocessor":
            segments = simulate_uniprocessor(rows, int(range_end), family, protocol, resource_order)
        elif mode == "global":
            global_rows = rows
            if include_resources:
                # Global simulators are CPU-only in this project.
                global_rows = [
                    TaskSpec(
                        task.task_id,
                        task.phase,
                        task.period,
                        task.computation,
                        task.deadline,
                        {},
                    )
                    for task in rows
                ]
            global_simulators = {
                "EDF": simulate_global_edf,
                "RM": simulate_global_rm,
                "DM": simulate_global_dm,
            }
            simulator = global_simulators.get(family)
            if simulator is None:
                st.error("This global variant is not implemented for the selected family.")
                st.stop()
            segments = simulator(global_rows, int(range_end), processors)
        elif mode == "partitioned":
            segments, loads, overloaded = simulate_partitioned(
                rows,
                int(range_end),
                processors,
                family,
                strategy,
                metric,
                protocol,
                resource_order,
            )

        st.caption(f"Segments generated: {len(segments)}")
        if overloaded:
            st.warning("Partitioning exceeds per-processor capacity. Adjust tasks or processors.")
        if not segments:
            st.warning("No scheduled jobs for the current range. Increase the range or check task parameters.")

        fig = cached_schedule_figure(
            segments,
            f"{algorithm_name} Schedule",
            tick_step=int(tick_step),
            range_start=int(range_start),
            range_end=int(range_end),
        )
        st.plotly_chart(fig, use_container_width=True)

        png, png_error = schedule_png_bytes(fig)
        if png is None:
            st.warning(png_error or "PNG export requires Kaleido. Install it with `pip install --upgrade kaleido`.")
        else:
            st.download_button(
                label="Download schedule PNG",
                data=png,
                file_name=f"{algorithm_name.lower().replace(' ', '_')}_schedule.png",
                mime="image/png",
            )

        if mode == "partitioned":
            for idx, load in enumerate(loads, start=1):
                st.write(f"Processor P{idx} load ({metric.lower()}): {load:.3f}")