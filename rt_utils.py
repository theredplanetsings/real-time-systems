from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple
import io
import math
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

@dataclass
class TaskSpec:
    task_id: int
    phase: int
    period: int
    computation: int
    deadline: int
    resources: Dict[str, int] = field(default_factory=dict)

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
    "Time Demand",
    "Priority Inversion",
]

PROTOCOLS = ["None", "PIP", "PCP", "NPP"]

def utilisation(tasks: List[TaskSpec]) -> float:
    if not tasks:
        return 0.0
    return sum(task.computation / task.period for task in tasks)

def density(tasks: List[TaskSpec]) -> float:
    if not tasks:
        return 0.0
    return sum(task.computation / min(task.deadline, task.period) for task in tasks)

def rm_bound(task_count: int) -> float:
    if task_count <= 0:
        return 1.0
    return task_count * (2 ** (1.0 / task_count) - 1.0)

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

    return summary

def compute_hyperperiod(periods: List[int]) -> int:
    def lcm(a: int, b: int) -> int:
        return abs(a * b) // math.gcd(a, b)

    hyper = 1
    for period in periods:
        hyper = lcm(hyper, period)
    return hyper

def build_task_dataframe(tasks: List[TaskSpec], resource_names: List[str]) -> pd.DataFrame:
    rows = []
    for task in tasks:
        row = {
            "task_id": task.task_id,
            "phase": task.phase,
            "period": task.period,
            "deadline": task.deadline,
            "computation": task.computation,
        }
        for res in resource_names:
            row[f"resource_{res}"] = task.resources.get(res, 0)
        rows.append(row)
    return pd.DataFrame(rows)

def task_csv_bytes(df: pd.DataFrame) -> bytes:
    buf = io.StringIO()
    df.to_csv(buf, index=False)
    return buf.getvalue().encode("utf-8")

def schedule_png_bytes(fig) -> Optional[bytes]:
    try:
        return fig.to_image(format="png")
    except (ValueError, RuntimeError):
        return None

def schedule_dataframe(segments: List[Dict[str, object]]) -> pd.DataFrame:
    return pd.DataFrame(segments)

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
    if "processor" in df.columns:
        hover_fields.insert(3, "processor")
    hover_labels = {
        "job": "Job",
        "phase": "Phase",
        "resource": "Resource",
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
    fig.update_layout(
        height=420,
        legend_title_text="Task",
        barmode="overlay",
        shapes=line_shapes,
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
) -> List[Dict[str, object]]:
    jobs = generate_jobs(tasks, horizon, resource_order)
    resource_names = sorted({res for task in tasks for res in task.resources})
    resource_holders = {res: None for res in resource_names}
    resource_ceilings = _resource_ceilings(tasks)

    ready: List[JobState] = []
    current: Optional[JobState] = None
    segments: List[Dict[str, object]] = []

    def select_job() -> Optional[JobState]:
        if not ready:
            return None
        if protocol == "PCP":
            sys_ceiling = _system_ceiling(resource_holders, resource_ceilings)
            eligible = [
                job
                for job in ready
                if job.holding_resource is not None
                or _priority_value(algorithm, job) < sys_ceiling
            ]
            if not eligible:
                return None
            return sorted(eligible, key=lambda j: _priority_value(algorithm, j))[0]
        return sorted(ready, key=lambda j: _priority_value(algorithm, j))[0]

    def apply_pip() -> None:
        if protocol != "PIP":
            return
        for holder in resource_holders.values():
            if holder is not None:
                holder.inherited_priority = None
        for job in ready:
            if job.current_phase != "cpu" and job.holding_resource is None:
                holder = resource_holders.get(job.current_phase)
                if holder is None:
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
            ready.append(jobs[job_index][1])
            job_index += 1

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
                current.holding_resource = resource
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
                "duration": 1,
                "release": current.release_time,
                "deadline": current.absolute_deadline,
                "remaining": remaining,
            }
        )

        if phase != "cpu" and resource is not None and current.remaining_resources[resource] == 0:
            resource_holders[resource] = None
            current.holding_resource = None

        if current.is_complete:
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