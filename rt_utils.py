from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import io
import json
import math
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from scheduling_math import compute_hyperperiod, density, rm_bound, utilisation

@dataclass
class TaskSpec:
    task_id: int
    phase: int
    period: int
    computation: int
    deadline: int
    resources: Dict[str, int] = field(default_factory=dict)
    criticality: str = ""
    wcet_lo: Optional[int] = None
    wcet_hi: Optional[int] = None

    @property
    def cpu_only_time(self) -> int:
        res_total = sum(self.resources.values())
        return max(self.computation - res_total, 0)

@dataclass
class JobState:
    task: TaskSpec
    job_number: int
    release_time: int
    absolute_deadline: int
    remaining_cpu: int
    remaining_resources: Dict[str, int]
    current_phase: str
    phase_queue: List[str]
    holding_resource: Optional[str] = None
    held_resources: List[str] = field(default_factory=list)
    inherited_priority: Optional[int] = None
    non_preemptive: bool = False

    @property
    def job_id(self) -> str:
        return f"{self.task.task_id}.{self.job_number}"

    @property
    def is_complete(self) -> bool:
        return self.remaining_cpu == 0 and all(v == 0 for v in self.remaining_resources.values())

ALGORITHMS = [
    "EDF",
    "EDD",
    "RM",
    "DM",
    "Cyclic Executive",
    "Global RM",
    "Global EDF",
    "Global DM",
    "Time Demand",
    "Priority Inversion",
    "Partitioned EDF",
    "Partitioned RM",
    "Partitioned DM",
    "Slack Stealing",
]

ALGORITHM_FAMILIES: Dict[str, Dict[str, object]] = {
    "EDF": {
        "label": "Earliest Deadline First",
        "variants": {
            "Uniprocessor": {"algorithm": "EDF", "mode": "uniprocessor"},
            "Global": {"algorithm": "Global EDF", "mode": "global"},
            "Partitioned": {"algorithm": "Partitioned EDF", "mode": "partitioned"},
        },
    },
    "EDD": {
        "label": "Earliest Due Date",
        "variants": {
            "Uniprocessor": {"algorithm": "EDD", "mode": "uniprocessor"},
        },
    },
    "RM": {
        "label": "Rate Monotonic",
        "variants": {
            "Uniprocessor": {"algorithm": "RM", "mode": "uniprocessor"},
            "Global": {"algorithm": "Global RM", "mode": "global"},
            "Partitioned": {"algorithm": "Partitioned RM", "mode": "partitioned"},
        },
    },
    "DM": {
        "label": "Deadline Monotonic",
        "variants": {
            "Uniprocessor": {"algorithm": "DM", "mode": "uniprocessor"},
            "Global": {"algorithm": "Global DM", "mode": "global"},
            "Partitioned": {"algorithm": "Partitioned DM", "mode": "partitioned"},
        },
    },
}

PROTOCOLS = ["None", "PIP", "PCP", "NPP"]

COMPARE_ALGORITHMS: Dict[str, Dict[str, str]] = {
    "RM": {"mode": "uniprocessor", "family": "RM"},
    "DM": {"mode": "uniprocessor", "family": "DM"},
    "EDF": {"mode": "uniprocessor", "family": "EDF"},
    "EDD": {"mode": "uniprocessor", "family": "EDD"},
    "Cyclic Executive": {"mode": "cyclic", "family": "Cyclic Executive"},
    "Global RM": {"mode": "global", "family": "RM"},
    "Global EDF": {"mode": "global", "family": "EDF"},
    "Global DM": {"mode": "global", "family": "DM"},
    "Partitioned RM": {"mode": "partitioned", "family": "RM"},
    "Partitioned EDF": {"mode": "partitioned", "family": "EDF"},
    "Partitioned DM": {"mode": "partitioned", "family": "DM"},
}

def family_names() -> List[str]:
    return sorted(ALGORITHM_FAMILIES.keys())

def variants_for_family(family: str) -> List[str]:
    family_meta = ALGORITHM_FAMILIES.get(family, {})
    variants = family_meta.get("variants", {})
    if isinstance(variants, dict):
        return sorted(variants.keys())
    return []

def schedulability_summary(
    tasks: List[TaskSpec],
    algorithm: str,
    processors: int = 1,
) -> Dict[str, object]:
    total_util = utilisation(tasks)
    total_density = density(tasks)
    summary = {
        "algorithm": algorithm,
        "utilisation": total_util,
        "density": total_density,
        "status": "unknown",
        "detail": "",
        "metric": None,
        "limit": None,
        "value": None,
    }

    if algorithm in {"EDF", "EDD"}:
        if total_density <= 1.0:
            summary["status"] = "pass"
            summary["detail"] = "Density <= 1.0 (sufficient for schedulability)"
        else:
            summary["status"] = "warn"
            summary["detail"] = "Density > 1.0 (may be unschedulable)"
            summary["metric"] = "Density"
            summary["limit"] = 1.0
            summary["value"] = total_density
        return summary

    if algorithm == "RM":
        bound = rm_bound(len(tasks))
        if total_util <= bound:
            summary["status"] = "pass"
            summary["detail"] = f"Utilisation <= RM bound ({bound:.3f})"
        else:
            summary["status"] = "warn"
            summary["detail"] = f"Utilisation > RM bound ({bound:.3f})"
            summary["metric"] = "Utilisation"
            summary["limit"] = bound
            summary["value"] = total_util
        return summary

    if algorithm == "DM":
        if total_density <= 1.0:
            summary["status"] = "pass"
            summary["detail"] = "Density <= 1.0 (sufficient test)"
        else:
            summary["status"] = "warn"
            summary["detail"] = "Density > 1.0 (may be unschedulable)"
            summary["metric"] = "Density"
            summary["limit"] = 1.0
            summary["value"] = total_density
        return summary

    if algorithm == "Global RM":
        if total_util <= processors:
            summary["status"] = "pass"
            summary["detail"] = f"Utilisation <= {processors} (processors)"
        else:
            summary["status"] = "warn"
            summary["detail"] = f"Utilisation > {processors} (processors)"
            summary["metric"] = "Utilisation"
            summary["limit"] = float(processors)
            summary["value"] = total_util
        return summary

    if algorithm == "Global EDF":
        if total_density <= processors:
            summary["status"] = "pass"
            summary["detail"] = f"Density <= {processors} (processors)"
        else:
            summary["status"] = "warn"
            summary["detail"] = f"Density > {processors} (processors)"
            summary["metric"] = "Density"
            summary["limit"] = float(processors)
            summary["value"] = total_density
        return summary

    if algorithm == "Global DM":
        if total_density <= processors:
            summary["status"] = "pass"
            summary["detail"] = f"Density <= {processors} (processors)"
        else:
            summary["status"] = "warn"
            summary["detail"] = f"Density > {processors} (processors)"
            summary["metric"] = "Density"
            summary["limit"] = float(processors)
            summary["value"] = total_density
        return summary

    if algorithm == "Cyclic Executive":
        _, valid = cyclic_executive_frames(tasks)
        if valid:
            summary["status"] = "pass"
            summary["detail"] = "Valid frame sizes exist for this task set"
        else:
            summary["status"] = "warn"
            summary["detail"] = "No valid frame sizes found"
        return summary

    if algorithm == "Time Demand":
        summary["status"] = "info"
        summary["detail"] = "Use the demand curve to assess feasibility"
        return summary

    if algorithm == "Priority Inversion":
        summary["status"] = "info"
        summary["detail"] = "Feasibility depends on protocol and blocking"
        return summary

    if algorithm == "Slack Stealing":
        summary["status"] = "info"
        summary["detail"] = "Periodic jobs use EDF; aperiodic jobs execute in reclaimed slack."
        return summary

    return summary

def build_task_dataframe(tasks: List[TaskSpec], resource_names: List[str]) -> pd.DataFrame:
    rows = []
    include_crit = any(bool(task.criticality) for task in tasks)
    include_wcet = any(task.wcet_lo is not None or task.wcet_hi is not None for task in tasks)
    for task in tasks:
        row = {
            "task_id": task.task_id,
            "phase": task.phase,
            "period": task.period,
            "deadline": task.deadline,
            "computation": task.computation,
        }
        if include_crit:
            row["criticality"] = task.criticality
        if include_wcet:
            row["wcet_lo"] = task.wcet_lo if task.wcet_lo is not None else task.computation
            hi_default = task.wcet_lo if task.wcet_lo is not None else task.computation
            row["wcet_hi"] = task.wcet_hi if task.wcet_hi is not None else hi_default
        for res in resource_names:
            row[f"resource_{res}"] = task.resources.get(res, 0)
        rows.append(row)
    return pd.DataFrame(rows)

def _criticality_rank(label: str) -> int:
    value = (label or "").strip().lower()
    if not value:
        return 0

    word_map = {
        "low": 1,
        "medium": 2,
        "med": 2,
        "high": 3,
        "critical": 4,
    }
    if value in word_map:
        return word_map[value]

    if value.isdigit():
        return int(value)

    if len(value) == 1 and "a" <= value <= "z":
        return ord(value) - ord("a") + 1

    return 0

def _task_wcet_budgets(task: TaskSpec, is_hi_class: bool) -> Tuple[int, int]:
    c_lo = int(task.wcet_lo if task.wcet_lo is not None else task.computation)
    c_lo = max(c_lo, 1)
    c_hi_raw = int(task.wcet_hi if task.wcet_hi is not None else c_lo)
    c_hi = max(c_hi_raw, c_lo)
    if not is_hi_class:
        c_hi = c_lo
    return c_lo, c_hi

def simulate_mixed_criticality_uniprocessor(
    tasks: List[TaskSpec],
    horizon: int,
    algorithm: str,
    mixed_criticality_mode: str,
    adaptive_threshold: str,
) -> List[Dict[str, object]]:
    threshold_rank = _criticality_rank(adaptive_threshold)
    if threshold_rank <= 0:
        threshold_rank = 1

    def is_hi_task(task: TaskSpec) -> bool:
        return _criticality_rank(task.criticality) >= threshold_rank

    def priority_key(job: Dict[str, object]) -> Tuple[int, int, int, int]:
        task = job["task"]
        if algorithm == "RM":
            base = int(task.period)
        elif algorithm == "DM":
            base = int(task.deadline)
        else:
            base = int(job["absolute_deadline"])
        crit_rank = int(job["criticality_rank"])
        return (base, -crit_rank, int(job["release_time"]), int(task.task_id))

    mode = "LO"
    next_job_number: Dict[int, int] = {task.task_id: 0 for task in tasks}
    ready: List[Dict[str, object]] = []
    segments: List[Dict[str, object]] = []

    for time in range(horizon):
        for task in tasks:
            if time < task.phase:
                continue
            if (time - task.phase) % task.period != 0:
                continue

            hi_class = is_hi_task(task)
            if mode == "HI" and not hi_class and mixed_criticality_mode == "adaptive":
                continue

            c_lo, c_hi = _task_wcet_budgets(task, hi_class)
            budget = c_hi if hi_class else c_lo

            job_number = next_job_number[task.task_id]
            next_job_number[task.task_id] = job_number + 1
            ready.append(
                {
                    "task": task,
                    "job_number": job_number,
                    "release_time": time,
                    "absolute_deadline": time + task.deadline,
                    "remaining": budget,
                    "executed": 0,
                    "c_lo": c_lo,
                    "c_hi": c_hi,
                    "is_hi": hi_class,
                    "criticality_rank": _criticality_rank(task.criticality),
                }
            )

        if not ready:
            continue

        candidates = ready
        if mode == "HI" and mixed_criticality_mode == "adaptive":
            candidates = [job for job in ready if bool(job["is_hi"])]
            if not candidates:
                continue

        current = sorted(candidates, key=priority_key)[0]
        ready.remove(current)

        current["remaining"] = int(current["remaining"]) - 1
        current["executed"] = int(current["executed"]) + 1

        task = current["task"]
        segments.append(
            {
                "start": time,
                "end": time + 1,
                "lane": f"Task {task.task_id}",
                "task": f"T{task.task_id}",
                "job": f"{task.task_id}.{current['job_number']}",
                "phase": "CPU",
                "resource": "-",
                "criticality": task.criticality or "-",
                "mode": mode,
                "duration": 1,
                "release": int(current["release_time"]),
                "deadline": int(current["absolute_deadline"]),
                "remaining": int(current["remaining"]),
            }
        )

        if (
            mixed_criticality_mode == "adaptive"
            and mode == "LO"
            and bool(current["is_hi"])
            and int(current["executed"]) >= int(current["c_lo"])
            and int(current["remaining"]) > 0
        ):
            mode = "HI"
            ready = [job for job in ready if bool(job["is_hi"])]

        if int(current["remaining"]) > 0:
            ready.append(current)

    return segments

def task_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

def task_json_bytes(df: pd.DataFrame) -> bytes:
    payload = {"tasks": df.to_dict(orient="records")}
    return json.dumps(payload, indent=2).encode("utf-8")

def schedule_png_bytes(fig) -> Tuple[Optional[bytes], Optional[str]]:
    try:
        return fig.to_image(format="png"), None
    except (ImportError, ModuleNotFoundError, RuntimeError, ValueError, OSError) as exc:
        error_text = str(exc)
        if "requires Google Chrome" in error_text:
            return (
                None,
                "PNG export failed: Chrome/Chromium is missing. "
                "For Streamlit Cloud, add 'chromium' to packages.txt and redeploy.",
            )
        return None, f"PNG export failed: {error_text}"

def schedule_dataframe(segments: List[Dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(segments)

def mixed_criticality_stats(segments: List[Dict[str, object]]) -> Dict[str, object]:
    df = schedule_dataframe(segments)
    if df.empty or "mode" not in df.columns:
        return {
            "enabled": False,
            "mode_switch_times": [],
            "mode_switch_count": 0,
            "first_switch_time": None,
            "initial_mode": None,
            "final_mode": None,
            "lo_mode_time": 0,
            "hi_mode_time": 0,
        }

    df["start"] = pd.to_numeric(df["start"], errors="coerce")
    df["end"] = pd.to_numeric(df["end"], errors="coerce")
    df = df.dropna(subset=["start", "end", "mode"])
    if df.empty:
        return {
            "enabled": False,
            "mode_switch_times": [],
            "mode_switch_count": 0,
            "first_switch_time": None,
            "initial_mode": None,
            "final_mode": None,
            "lo_mode_time": 0,
            "hi_mode_time": 0,
        }

    timeline = (
        df.sort_values(["start", "end"])
        .groupby("start", as_index=False)
        .first()[["start", "mode"]]
        .sort_values("start")
    )

    switch_times: List[int] = []
    previous_mode: Optional[str] = None
    for _, row in timeline.iterrows():
        mode = str(row["mode"])
        t = int(row["start"])
        if previous_mode is None:
            previous_mode = mode
            continue
        if mode != previous_mode:
            switch_times.append(t)
            previous_mode = mode

    mode_time = (
        df.assign(duration=df["end"] - df["start"])
        .groupby("mode", as_index=True)["duration"]
        .sum()
        .to_dict()
    )

    initial_mode = str(timeline.iloc[0]["mode"])
    final_mode = str(timeline.iloc[-1]["mode"])
    return {
        "enabled": True,
        "mode_switch_times": switch_times,
        "mode_switch_count": len(switch_times),
        "first_switch_time": switch_times[0] if switch_times else None,
        "initial_mode": initial_mode,
        "final_mode": final_mode,
        "lo_mode_time": int(mode_time.get("LO", 0)),
        "hi_mode_time": int(mode_time.get("HI", 0)),
    }

def schedule_figure(
    segments: List[Dict[str, object]],
    title: str,
    tick_step: Optional[int] = None,
    range_start: Optional[int] = None,
    range_end: Optional[int] = None,
) -> "px.Figure":
    df = schedule_dataframe(segments)
    if df.empty:
        fig = px.scatter(title=title)
        fig.update_layout(height=250)
        return fig

    df["start"] = pd.to_numeric(df["start"], errors="coerce")
    df["end"] = pd.to_numeric(df["end"], errors="coerce")
    df = df.dropna(subset=["start", "end"])

    if range_start is not None and range_end is not None:
        df = df[(df["end"] > range_start) & (df["start"] < range_end)]
        if df.empty:
            fig = px.scatter(title=title)
            fig.update_layout(height=250)
            return fig

    category_order = sorted(df["lane"].unique())
    df["duration"] = df["end"] - df["start"]

    hover_fields = [
        "job",
        "phase",
        "resource",
        "duration",
        "start",
        "end",
        "deadline",
        "release",
        "remaining",
    ]
    if "mode" in df.columns:
        hover_fields.insert(3, "mode")
    if "criticality" in df.columns:
        hover_fields.insert(3, "criticality")
    if "processor" in df.columns:
        hover_fields.insert(3, "processor")
    hover_labels = {
        "job": "Job",
        "phase": "Phase",
        "resource": "Resource",
        "mode": "Mode",
        "criticality": "Criticality",
        "processor": "Processor",
        "duration": "Duration",
        "start": "Start",
        "end": "End",
        "deadline": "Deadline",
        "release": "Release",
        "remaining": "Remaining",
    }

    fig = go.Figure()
    blocked_df = df[df["phase"] == "Blocked"]
    main_df = df[df["phase"] != "Blocked"]
    tasks = sorted(main_df["task"].unique())
    palette = px.colors.qualitative.Plotly
    color_map = {task: palette[idx % len(palette)] for idx, task in enumerate(tasks)}

    for task in tasks:
        task_df = main_df[main_df["task"] == task]
        customdata = task_df[hover_fields].to_numpy()
        hover_lines = [
            f"{hover_labels[field]}: %{{customdata[{idx}]}}<br>"
            for idx, field in enumerate(hover_fields)
        ]
        hovertemplate = "Task: %{fullData.name}<br>" + "".join(hover_lines) + "<extra></extra>"
        fig.add_trace(
            go.Bar(
                x=task_df["duration"],
                base=task_df["start"],
                y=task_df["lane"],
                orientation="h",
                name=task,
                marker_color=color_map[task],
                customdata=customdata,
                hovertemplate=hovertemplate,
            )
        )

    if not blocked_df.empty:
        blocked_fields = ["job", "resource", "start", "end", "deadline", "release", "remaining"]
        blocked_custom = blocked_df[blocked_fields].to_numpy()
        blocked_lines = [
            f"{blocked_fields[idx].title()}: %{{customdata[{idx}]}}<br>"
            for idx in range(len(blocked_fields))
        ]
        blocked_template = "Blocked<br>" + "".join(blocked_lines) + "<extra></extra>"
        fig.add_trace(
            go.Bar(
                x=blocked_df["duration"],
                base=blocked_df["start"],
                y=blocked_df["lane"],
                orientation="h",
                name="Blocked",
                marker_color="#777",
                customdata=blocked_custom,
                hovertemplate=blocked_template,
            )
        )

    job_df = df.drop_duplicates(subset=["job"])
    fig.add_trace(
        go.Scatter(
            x=job_df["release"],
            y=job_df["lane"],
            mode="markers",
            name="Release",
            marker=dict(symbol="triangle-down", size=8, color="#444"),
            hovertemplate="Release: %{x}<br>Job: %{customdata[0]}<extra></extra>",
            customdata=job_df[["job"]].to_numpy(),
        )
    )
    fig.add_trace(
        go.Scatter(
            x=job_df["deadline"],
            y=job_df["lane"],
            mode="markers",
            name="Deadline",
            marker=dict(symbol="triangle-up", size=8, color="#444"),
            hovertemplate="Deadline: %{x}<br>Job: %{customdata[0]}<extra></extra>",
            customdata=job_df[["job"]].to_numpy(),
        )
    )

    fig.update_yaxes(
        autorange="reversed",
        categoryorder="array",
        categoryarray=category_order,
        tickson="boundaries",
        showgrid=True,
        gridcolor="rgba(0,0,0,0.35)",
        gridwidth=1.5,
    )
    line_shapes = [
        {
            "type": "line",
            "xref": "paper",
            "x0": 0,
            "x1": 1,
            "yref": "y",
            "y0": lane,
            "y1": lane,
            "line": {"color": "rgba(0,0,0,0.35)", "width": 1},
            "layer": "above",
        }
        for lane in category_order
    ]
    mc_stats = mixed_criticality_stats(segments)
    mode_switch_shapes = [
        {
            "type": "line",
            "xref": "x",
            "x0": t,
            "x1": t,
            "yref": "paper",
            "y0": 0,
            "y1": 1,
            "line": {"color": "#d62728", "width": 2, "dash": "dash"},
            "layer": "above",
        }
        for t in mc_stats["mode_switch_times"]
    ]
    mode_switch_annotations = [
        {
            "x": t,
            "y": 1.02,
            "xref": "x",
            "yref": "paper",
            "text": "LO->HI",
            "showarrow": False,
            "font": {"size": 11, "color": "#d62728"},
            "xanchor": "left",
        }
        for t in mc_stats["mode_switch_times"]
    ]
    fig.update_layout(
        height=420,
        legend_title_text="Task",
        barmode="overlay",
        shapes=line_shapes + mode_switch_shapes,
        annotations=mode_switch_annotations,
        plot_bgcolor="white",
    )
    fig.update_xaxes(type="linear")
    if range_start is not None and range_end is not None:
        fig.update_xaxes(range=[range_start, range_end])
    else:
        fig.update_xaxes(range=[0, df["end"].max()])
    if tick_step and tick_step > 0:
        fig.update_xaxes(dtick=tick_step)
    return fig

def _priority_value(algorithm: str, job: JobState) -> int:
    if algorithm == "RM":
        return job.task.period
    if algorithm == "DM":
        return job.task.deadline
    if algorithm == "EDF" or algorithm == "EDD":
        return job.absolute_deadline
    return job.task.period

def _resource_ceilings(tasks: List[TaskSpec]) -> Dict[str, int]:
    ceilings: Dict[str, int] = {}
    for task in tasks:
        for res in task.resources:
            prio = task.deadline
            ceilings[res] = min(ceilings.get(res, prio), prio)
    return ceilings

def _system_ceiling(resource_holders: Dict[str, Optional[JobState]], resource_ceilings: Dict[str, int]) -> int:
    locked = [res for res, holder in resource_holders.items() if holder is not None]
    if not locked:
        return 10**9
    return min(resource_ceilings[res] for res in locked)

def _build_phase_queue(resource_order: str, resources: List[str]) -> List[str]:
    if resource_order == "Resources then CPU":
        return resources + ["cpu"]
    return ["cpu"] + resources

def _next_phase(job: JobState) -> None:
    while job.phase_queue:
        next_phase = job.phase_queue[0]
        if next_phase == "cpu" and job.remaining_cpu == 0:
            job.phase_queue.pop(0)
            continue
        if next_phase != "cpu" and job.remaining_resources.get(next_phase, 0) == 0:
            job.phase_queue.pop(0)
            continue
        job.current_phase = next_phase
        return
    job.current_phase = "done"

def generate_jobs(tasks: List[TaskSpec], horizon: int, resource_order: str) -> List[Tuple[int, JobState]]:
    jobs: List[Tuple[int, JobState]] = []
    resource_names = sorted({res for task in tasks for res in task.resources})
    for task in tasks:
        release = task.phase
        job_num = 0
        while release < horizon:
            phase_queue = _build_phase_queue(resource_order, resource_names)
            remaining_resources = {res: task.resources.get(res, 0) for res in resource_names}
            job = JobState(
                task=task,
                job_number=job_num,
                release_time=release,
                absolute_deadline=release + task.deadline,
                remaining_cpu=task.cpu_only_time,
                remaining_resources=remaining_resources,
                current_phase=phase_queue[0] if phase_queue else "cpu",
                phase_queue=phase_queue,
            )
            _next_phase(job)
            jobs.append((release, job))
            release += task.period
            job_num += 1
    jobs.sort(key=lambda item: item[0])
    return jobs

def simulate_uniprocessor(
    tasks: List[TaskSpec],
    horizon: int,
    algorithm: str,
    protocol: str,
    resource_order: str,
    resource_access_mode: str = "Non-nested",
    mixed_criticality_mode: str = "none",
    adaptive_threshold: str = "high",
) -> List[Dict[str, object]]:
    if mixed_criticality_mode in {"static", "adaptive"}:
        return simulate_mixed_criticality_uniprocessor(
            tasks,
            horizon,
            algorithm,
            mixed_criticality_mode,
            adaptive_threshold,
        )

    jobs = generate_jobs(tasks, horizon, resource_order)
    resource_names = sorted({res for task in tasks for res in task.resources})
    resource_holders = {res: None for res in resource_names}
    resource_ceilings = _resource_ceilings(tasks)

    ready: List[JobState] = []
    current: Optional[JobState] = None
    segments: List[Dict[str, object]] = []
    hi_mode = False
    threshold_rank = _criticality_rank(adaptive_threshold)

    def job_rank(job: JobState) -> int:
        return _criticality_rank(job.task.criticality)

    def should_keep_in_hi_mode(job: JobState) -> bool:
        return job_rank(job) >= threshold_rank

    def has_future_resource_phase(job: JobState) -> bool:
        for next_phase in job.phase_queue[1:]:
            if next_phase == "cpu":
                continue
            if job.remaining_resources.get(next_phase, 0) > 0:
                return True
        return False

    def acquire_resource(job: JobState, resource: str) -> None:
        if resource not in job.held_resources:
            job.held_resources.append(resource)
        job.holding_resource = job.held_resources[-1] if job.held_resources else None

    def release_resource(job: JobState, resource: str) -> None:
        if resource in job.held_resources:
            job.held_resources.remove(resource)
        if resource_holders.get(resource) is job:
            resource_holders[resource] = None
        job.holding_resource = job.held_resources[-1] if job.held_resources else None

    def release_all_resources(job: JobState) -> None:
        for resource in list(job.held_resources):
            if resource_holders.get(resource) is job:
                resource_holders[resource] = None
        job.held_resources.clear()
        job.holding_resource = None

    def is_overload_risk(time_now: int) -> bool:
        if mixed_criticality_mode != "adaptive" or threshold_rank <= 0:
            return False
        active = ready.copy()
        if current is not None:
            active.append(current)
        for job in active:
            if job_rank(job) < threshold_rank:
                continue
            remaining = job.remaining_cpu + sum(job.remaining_resources.values())
            laxity = job.absolute_deadline - time_now - remaining
            if laxity <= 0:
                return True
        return False

    def select_job() -> Optional[JobState]:
        if not ready:
            return None
        candidate_jobs = ready
        if hi_mode and threshold_rank > 0:
            candidate_jobs = [job for job in ready if should_keep_in_hi_mode(job)]
            if not candidate_jobs:
                return None
        if protocol == "PCP":
            sys_ceiling = _system_ceiling(resource_holders, resource_ceilings)
            eligible = [
                job
                for job in candidate_jobs
                if job.held_resources
                or _priority_value(algorithm, job) < sys_ceiling
            ]
            if not eligible:
                return None
            return sorted(eligible, key=lambda j: (_priority_value(algorithm, j), -job_rank(j), j.release_time))[0]
        return sorted(candidate_jobs, key=lambda j: (_priority_value(algorithm, j), -job_rank(j), j.release_time))[0]

    def apply_pip() -> None:
        if protocol != "PIP":
            return
        for holder in resource_holders.values():
            if holder is not None:
                holder.inherited_priority = None
        for job in ready:
            if job.current_phase == "cpu":
                continue
            holder = resource_holders.get(job.current_phase)
            if holder is None or holder is job:
                continue
            blocked_prio = _priority_value(algorithm, job)
            if holder.inherited_priority is None:
                holder.inherited_priority = blocked_prio
            else:
                holder.inherited_priority = min(holder.inherited_priority, blocked_prio)

    def effective_priority(job: JobState) -> int:
        base = _priority_value(algorithm, job)
        if protocol == "PIP" and job.inherited_priority is not None:
            return min(base, job.inherited_priority)
        return base

    job_index = 0
    for time in range(horizon):
        while job_index < len(jobs) and jobs[job_index][0] == time:
            released_job = jobs[job_index][1]
            if not (hi_mode and threshold_rank > 0 and not should_keep_in_hi_mode(released_job)):
                ready.append(released_job)
            job_index += 1

        if not hi_mode and is_overload_risk(time):
            hi_mode = True
            if threshold_rank > 0:
                ready = [job for job in ready if should_keep_in_hi_mode(job)]
                if current is not None and not should_keep_in_hi_mode(current):
                    current = None

        if current is not None and not current.is_complete:
            if protocol == "NPP" and current.non_preemptive:
                pass
            else:
                ready.append(current)
                current = None

        apply_pip()

        if current is None:
            current = select_job()
            if current is not None:
                ready.remove(current)

        if current is None:
            continue

        _next_phase(current)
        phase = current.current_phase
        resource = None
        if phase != "cpu" and phase != "done":
            resource = phase

        if phase == "done":
            current = None
            continue

        if resource is not None:
            holder = resource_holders.get(resource)
            if holder is None:
                # PCP lock check
                if protocol == "PCP":
                    sys_ceiling = _system_ceiling(resource_holders, resource_ceilings)
                    if _priority_value(algorithm, current) >= sys_ceiling:
                        remaining = current.remaining_cpu + sum(current.remaining_resources.values())
                        segments.append(
                            {
                                "start": time,
                                "end": time + 1,
                                "lane": f"Task {current.task.task_id}",
                                "task": f"T{current.task.task_id}",
                                "job": current.job_id,
                                "phase": "Blocked",
                                "resource": resource,
                                "criticality": current.task.criticality or "-",
                                "duration": 1,
                                "release": current.release_time,
                                "deadline": current.absolute_deadline,
                                "remaining": remaining,
                            }
                        )
                        ready.append(current)
                        current = None
                        continue
                resource_holders[resource] = current
                acquire_resource(current, resource)
                if protocol == "NPP":
                    current.non_preemptive = True
            elif holder is not current:
                remaining = current.remaining_cpu + sum(current.remaining_resources.values())
                segments.append(
                    {
                        "start": time,
                        "end": time + 1,
                        "lane": f"Task {current.task.task_id}",
                        "task": f"T{current.task.task_id}",
                        "job": current.job_id,
                        "phase": "Blocked",
                        "resource": resource,
                        "criticality": current.task.criticality or "-",
                        "duration": 1,
                        "release": current.release_time,
                        "deadline": current.absolute_deadline,
                        "remaining": remaining,
                    }
                )
                # blocked
                ready.append(current)
                current = None
                continue

        # Execute one time unit
        if phase == "cpu":
            current.remaining_cpu = max(current.remaining_cpu - 1, 0)
        else:
            current.remaining_resources[resource] = max(current.remaining_resources[resource] - 1, 0)

        remaining = current.remaining_cpu + sum(current.remaining_resources.values())
        segments.append(
            {
                "start": time,
                "end": time + 1,
                "lane": f"Task {current.task.task_id}",
                "task": f"T{current.task.task_id}",
                "job": current.job_id,
                "phase": "CPU" if phase == "cpu" else "Resource",
                "resource": resource or "-",
                "criticality": current.task.criticality or "-",
                "duration": 1,
                "release": current.release_time,
                "deadline": current.absolute_deadline,
                "remaining": remaining,
            }
        )

        if phase != "cpu" and resource is not None and current.remaining_resources[resource] == 0:
            if resource_access_mode == "Nested" and has_future_resource_phase(current):
                pass
            elif resource_access_mode == "Nested":
                release_all_resources(current)
            else:
                release_resource(current, resource)

        if current.is_complete:
            release_all_resources(current)
            current.non_preemptive = False
            current = None

    return segments

def simulate_global_rm(tasks: List[TaskSpec], horizon: int, processors: int) -> List[Dict[str, object]]:
    jobs = generate_jobs(tasks, horizon, "CPU then resources")
    ready: List[JobState] = []
    job_index = 0
    segments: List[Dict[str, object]] = []

    for time in range(horizon):
        while job_index < len(jobs) and jobs[job_index][0] == time:
            ready.append(jobs[job_index][1])
            job_index += 1

        ready.sort(key=lambda j: j.task.period)
        assignments: List[Optional[JobState]] = []
        for _ in range(processors):
            assignments.append(ready.pop(0) if ready else None)

        for proc_id, job in enumerate(assignments, start=1):
            if job is None:
                continue
            job.remaining_cpu = max(job.remaining_cpu - 1, 0)
            segments.append(
                {
                    "start": time,
                    "end": time + 1,
                    "lane": f"Task {job.task.task_id}",
                    "task": f"T{job.task.task_id}",
                    "job": job.job_id,
                    "phase": "CPU",
                    "resource": "-",
                    "criticality": job.task.criticality or "-",
                    "processor": f"P{proc_id}",
                    "duration": 1,
                    "release": job.release_time,
                    "deadline": job.absolute_deadline,
                    "remaining": job.remaining_cpu,
                }
            )
            if job.remaining_cpu > 0:
                ready.append(job)

    return segments

def simulate_global_edf(tasks: List[TaskSpec], horizon: int, processors: int) -> List[Dict[str, object]]:
    jobs = generate_jobs(tasks, horizon, "CPU then resources")
    ready: List[JobState] = []
    job_index = 0
    segments: List[Dict[str, object]] = []

    for time in range(horizon):
        while job_index < len(jobs) and jobs[job_index][0] == time:
            ready.append(jobs[job_index][1])
            job_index += 1

        ready.sort(key=lambda j: j.absolute_deadline)
        assignments: List[Optional[JobState]] = []
        for _ in range(processors):
            assignments.append(ready.pop(0) if ready else None)

        for proc_id, job in enumerate(assignments, start=1):
            if job is None:
                continue
            job.remaining_cpu = max(job.remaining_cpu - 1, 0)
            segments.append(
                {
                    "start": time,
                    "end": time + 1,
                    "lane": f"Task {job.task.task_id}",
                    "task": f"T{job.task.task_id}",
                    "job": job.job_id,
                    "phase": "CPU",
                    "resource": "-",
                    "criticality": job.task.criticality or "-",
                    "processor": f"P{proc_id}",
                    "duration": 1,
                    "release": job.release_time,
                    "deadline": job.absolute_deadline,
                    "remaining": job.remaining_cpu,
                }
            )
            if job.remaining_cpu > 0:
                ready.append(job)

    return segments

def simulate_global_dm(tasks: List[TaskSpec], horizon: int, processors: int) -> List[Dict[str, object]]:
    jobs = generate_jobs(tasks, horizon, "CPU then resources")
    ready: List[JobState] = []
    job_index = 0
    segments: List[Dict[str, object]] = []

    for time in range(horizon):
        while job_index < len(jobs) and jobs[job_index][0] == time:
            ready.append(jobs[job_index][1])
            job_index += 1

        ready.sort(key=lambda j: j.task.deadline)
        assignments: List[Optional[JobState]] = []
        for _ in range(processors):
            assignments.append(ready.pop(0) if ready else None)

        for proc_id, job in enumerate(assignments, start=1):
            if job is None:
                continue
            job.remaining_cpu = max(job.remaining_cpu - 1, 0)
            segments.append(
                {
                    "start": time,
                    "end": time + 1,
                    "lane": f"Task {job.task.task_id}",
                    "task": f"T{job.task.task_id}",
                    "job": job.job_id,
                    "phase": "CPU",
                    "resource": "-",
                    "criticality": job.task.criticality or "-",
                    "processor": f"P{proc_id}",
                    "duration": 1,
                    "release": job.release_time,
                    "deadline": job.absolute_deadline,
                    "remaining": job.remaining_cpu,
                }
            )
            if job.remaining_cpu > 0:
                ready.append(job)

    return segments

def _task_weight(task: TaskSpec, metric: str) -> float:
    if metric == "Density":
        return task.computation / min(task.deadline, task.period)
    return task.computation / task.period

def partition_tasks(
    tasks: List[TaskSpec],
    processors: int,
    strategy: str,
    metric: str,
) -> Tuple[List[List[TaskSpec]], List[float], bool]:
    assignments: List[List[TaskSpec]] = [[] for _ in range(processors)]
    loads = [0.0 for _ in range(processors)]
    overloaded = False

    weighted = [(task, _task_weight(task, metric)) for task in tasks]
    weighted.sort(key=lambda item: item[1], reverse=True)

    for task, weight in weighted:
        fit_indices = [i for i in range(processors) if loads[i] + weight <= 1.0]
        if fit_indices:
            if strategy == "Best-fit":
                target = max(fit_indices, key=lambda i: loads[i])
            elif strategy == "Worst-fit":
                target = min(fit_indices, key=lambda i: loads[i])
            else:
                target = fit_indices[0]
        else:
            overloaded = True
            target = min(range(processors), key=lambda i: loads[i])

        assignments[target].append(task)
        loads[target] += weight

    return assignments, loads, overloaded

def simulate_partitioned(
    tasks: List[TaskSpec],
    horizon: int,
    processors: int,
    algorithm: str,
    strategy: str,
    metric: str,
    protocol: str = "None",
    resource_order: str = "CPU then resources",
    resource_access_mode: str = "Non-nested",
    mixed_criticality_mode: str = "none",
    adaptive_threshold: str = "high",
) -> Tuple[List[Dict[str, object]], List[float], bool]:
    assignments, loads, overloaded = partition_tasks(tasks, processors, strategy, metric)
    segments: List[Dict[str, object]] = []

    for idx, partition in enumerate(assignments, start=1):
        if not partition:
            continue
        part_segments = simulate_uniprocessor(
            partition,
            horizon,
            algorithm,
            protocol,
            resource_order,
            resource_access_mode,
            mixed_criticality_mode=mixed_criticality_mode,
            adaptive_threshold=adaptive_threshold,
        )
        for segment in part_segments:
            segment["processor"] = f"P{idx}"
        segments.extend(part_segments)

    return segments, loads, overloaded

def simulate_slack_stealing(
    periodic_tasks: List[TaskSpec],
    aperiodic_jobs: List[Dict[str, int]],
    horizon: int,
) -> List[Dict[str, object]]:
    """Simulate uniprocessor slack stealing using idle-time reclamation under EDF.

    Periodic jobs always have priority (EDF order). When no periodic job is ready,
    the processor executes the earliest-deadline ready aperiodic job.
    """
    periodic_jobs = generate_jobs(periodic_tasks, horizon, "CPU then resources")
    ready_periodic: List[JobState] = []
    ready_aperiodic: List[Dict[str, int]] = []
    segments: List[Dict[str, object]] = []

    normalized_aperiodic = sorted(
        [
            {
                "job_id": int(job["job_id"]),
                "release": int(job["release"]),
                "deadline": int(job["deadline"]),
                "remaining": int(job["computation"]),
            }
            for job in aperiodic_jobs
        ],
        key=lambda j: (j["release"], j["deadline"], j["job_id"]),
    )

    periodic_idx = 0
    aperiodic_idx = 0

    for time in range(horizon):
        while periodic_idx < len(periodic_jobs) and periodic_jobs[periodic_idx][0] == time:
            ready_periodic.append(periodic_jobs[periodic_idx][1])
            periodic_idx += 1

        while aperiodic_idx < len(normalized_aperiodic) and normalized_aperiodic[aperiodic_idx]["release"] == time:
            ready_aperiodic.append(normalized_aperiodic[aperiodic_idx])
            aperiodic_idx += 1

        ready_periodic = [job for job in ready_periodic if job.remaining_cpu > 0]
        ready_aperiodic = [job for job in ready_aperiodic if job["remaining"] > 0]

        if ready_periodic:
            ready_periodic.sort(key=lambda j: (j.absolute_deadline, j.task.task_id, j.job_number))
            job = ready_periodic[0]
            job.remaining_cpu = max(job.remaining_cpu - 1, 0)
            segments.append(
                {
                    "start": time,
                    "end": time + 1,
                    "lane": f"Task {job.task.task_id}",
                    "task": f"T{job.task.task_id}",
                    "job": job.job_id,
                    "phase": "CPU",
                    "resource": "-",
                    "duration": 1,
                    "release": job.release_time,
                    "deadline": job.absolute_deadline,
                    "remaining": job.remaining_cpu,
                }
            )
            continue

        if ready_aperiodic:
            ready_aperiodic.sort(key=lambda j: (j["deadline"], j["release"], j["job_id"]))
            job = ready_aperiodic[0]
            job["remaining"] = max(job["remaining"] - 1, 0)
            segments.append(
                {
                    "start": time,
                    "end": time + 1,
                    "lane": f"Aperiodic {job['job_id']}",
                    "task": "AP",
                    "job": f"AP{job['job_id']}",
                    "phase": "Slack",
                    "resource": "-",
                    "duration": 1,
                    "release": job["release"],
                    "deadline": job["deadline"],
                    "remaining": job["remaining"],
                }
            )

    return segments

def slack_stealing_stats(
    segments: List[Dict[str, object]],
    aperiodic_jobs: List[Dict[str, int]],
    horizon: int,
) -> Tuple[Dict[str, float], pd.DataFrame]:
    """Compute aggregate and per-job metrics for Slack Stealing runs."""
    jobs = []
    for job in aperiodic_jobs:
        jobs.append(
            {
                "job_id": int(job["job_id"]),
                "release": int(job["release"]),
                "deadline": int(job["deadline"]),
                "computation": int(job["computation"]),
            }
        )

    if not jobs:
        empty = pd.DataFrame(
            columns=[
                "job_id",
                "release",
                "deadline",
                "computation",
                "executed",
                "completion_time",
                "response_time",
                "waiting_time",
                "completed",
                "deadline_missed",
            ]
        )
        return (
            {
                "total_slack_used": 0.0,
                "completion_ratio": 0.0,
                "mean_response_time": 0.0,
                "mean_waiting_time": 0.0,
                "max_waiting_time": 0.0,
                "deadline_misses": 0.0,
            },
            empty,
        )

    ap_segments = [
        segment
        for segment in segments
        if str(segment.get("job", "")).startswith("AP") and segment.get("phase") == "Slack"
    ]

    executed_by_job: Dict[int, int] = {}
    finish_by_job: Dict[int, int] = {}
    total_slack_used = 0

    for segment in ap_segments:
        job_name = str(segment.get("job", ""))
        if not job_name.startswith("AP"):
            continue
        try:
            job_id = int(job_name[2:])
        except ValueError:
            continue

        duration = int(segment.get("duration", int(segment.get("end", 0)) - int(segment.get("start", 0))))
        end = int(segment.get("end", 0))

        executed_by_job[job_id] = executed_by_job.get(job_id, 0) + duration
        finish_by_job[job_id] = max(finish_by_job.get(job_id, 0), end)
        total_slack_used += duration

    rows = []
    completed_count = 0
    response_sum = 0
    waiting_sum = 0
    waiting_values: List[int] = []
    deadline_misses = 0

    for job in sorted(jobs, key=lambda item: item["job_id"]):
        job_id = job["job_id"]
        executed = executed_by_job.get(job_id, 0)
        completed = executed >= job["computation"]
        completion_time: Optional[int] = finish_by_job.get(job_id) if completed else None

        response_time: Optional[int] = None
        waiting_time: Optional[int] = None
        if completed and completion_time is not None:
            response_time = completion_time - job["release"]
            waiting_time = response_time - job["computation"]
            completed_count += 1
            response_sum += response_time
            waiting_sum += waiting_time
            waiting_values.append(waiting_time)

        missed = False
        if completed and completion_time is not None and completion_time > job["deadline"]:
            missed = True
        if not completed and job["deadline"] <= horizon:
            missed = True
        if missed:
            deadline_misses += 1

        rows.append(
            {
                "job_id": job_id,
                "release": job["release"],
                "deadline": job["deadline"],
                "computation": job["computation"],
                "executed": executed,
                "completion_time": completion_time,
                "response_time": response_time,
                "waiting_time": waiting_time,
                "completed": completed,
                "deadline_missed": missed,
            }
        )

    total_jobs = len(jobs)
    metrics = {
        "total_slack_used": float(total_slack_used),
        "completion_ratio": float(completed_count / total_jobs) if total_jobs else 0.0,
        "mean_response_time": float(response_sum / completed_count) if completed_count else 0.0,
        "mean_waiting_time": float(waiting_sum / completed_count) if completed_count else 0.0,
        "max_waiting_time": float(max(waiting_values)) if waiting_values else 0.0,
        "deadline_misses": float(deadline_misses),
    }

    return metrics, pd.DataFrame(rows)

def cyclic_executive_frames(tasks: List[TaskSpec]) -> Tuple[int, List[int]]:
    hyper = compute_hyperperiod([task.period for task in tasks])
    c_max = max(task.computation for task in tasks)
    divisors = [f for f in range(1, hyper + 1) if hyper % f == 0]
    candidates = [f for f in divisors if f >= c_max]

    valid = []
    for f in candidates:
        ok = True
        for task in tasks:
            lhs = 2 * f - math.gcd(task.period, f)
            if lhs > task.period:
                ok = False
                break
        if ok:
            valid.append(f)
    return hyper, valid

def cyclic_executive_schedule(tasks: List[TaskSpec], frame: int) -> List[Dict[str, object]]:
    hyper = compute_hyperperiod([task.period for task in tasks])
    frames = [{"start": t, "end": t + frame, "used": 0} for t in range(0, hyper, frame)]
    segments: List[Dict[str, object]] = []
    jobs = []
    for task in tasks:
        t = task.phase
        job_num = 0
        while t < hyper:
            jobs.append(
                {
                    "task": task,
                    "job_id": f"{task.task_id}.{job_num}",
                    "release": t,
                    "deadline": t + task.period,
                    "remaining": task.computation,
                }
            )
            t += task.period
            job_num += 1

    jobs.sort(key=lambda j: (j["release"], j["deadline"]))

    for job in jobs:
        for frame_slot in frames:
            if frame_slot["start"] >= job["release"] and frame_slot["end"] <= job["deadline"]:
                if frame_slot["used"] + job["remaining"] <= frame:
                    start = frame_slot["start"] + frame_slot["used"]
                    end = start + job["remaining"]
                    frame_slot["used"] += job["remaining"]
                    segments.append(
                        {
                            "start": start,
                            "end": end,
                            "lane": f"Frame {frame_slot['start'] // frame + 1}",
                            "task": f"T{job['task'].task_id}",
                            "job": job["job_id"],
                            "phase": "Frame",
                            "resource": "-",
                            "duration": job["remaining"],
                            "release": job["release"],
                            "deadline": job["deadline"],
                            "remaining": 0,
                        }
                    )
                    break

    return segments

def time_demand_analysis(tasks: List[TaskSpec], target_task_id: int, horizon: int) -> pd.DataFrame:
    target = next(task for task in tasks if task.task_id == target_task_id)
    higher = [task for task in tasks if task.period <= target.period and task.task_id != target_task_id]

    def w(t: int) -> int:
        if t == 0:
            return 0
        total = 0
        for task in higher + [target]:
            total += math.ceil(t / task.period) * task.computation
        return total

    rows = []
    for t in range(0, horizon + 1):
        rows.append({"time": t, "demand": w(t)})
    return pd.DataFrame(rows)