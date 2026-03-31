"""dm_pcp_scheduler.py

Deadline Monotonic (DM) scheduling with the Priority Ceiling Protocol (PCP).

This script is tailored for HW-style problems where each job executes:
  1) CPU-only work first
  2) then critical-section work requiring Resource A and/or Resource B

Execution is fully preemptive, but a resource is held until the job finishes
its resource-specific execution (i.e., the critical section length).

Priority convention:
- DM priority is the task relative deadline D (smaller D => higher priority).
- Numerically: smaller `priority` value means higher priority.

PCP rules implemented (immediate ceiling protocol style):
- Each resource has a ceiling equal to the highest priority (smallest number)
  among tasks that may lock it.
- The system ceiling is the highest priority among currently locked resources
  (i.e., the minimum of their ceilings).
- A job that does NOT hold a resource may execute only if it has higher
  priority than the system ceiling (strictly smaller priority value).
- A job that holds a resource may continue executing (even if its priority is
  not above the system ceiling).
- A job may lock a resource only if the resource is free and the job's priority
  is higher than the current system ceiling (strictly smaller).

Outputs:
- A per-time-unit schedule trace (t=0..end_time-1)
- A compact segment list
- A Gantt chart PNG saved next to this script
"""

from __future__ import annotations

import argparse
from dataclasses import dataclass
from typing import DefaultDict, Dict, List, Optional, Tuple

from collections import defaultdict

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches


@dataclass(frozen=True)
class Task:
    task_id: int
    phase: int
    period: int
    computation_time: int
    deadline: int
    resource_a_time: int
    resource_b_time: int

    @property
    def cpu_only_time(self) -> int:
        return self.computation_time - self.resource_a_time - self.resource_b_time

    @property
    def priority(self) -> int:
        # DM priority: smaller relative deadline => higher priority
        return self.deadline


class Job:
    def __init__(self, task: Task, arrival_time: int, job_number: int):
        self.task = task
        self.arrival_time = arrival_time
        self.job_number = job_number
        self.absolute_deadline = arrival_time + task.deadline

        self.remaining_cpu_only = task.cpu_only_time
        self.remaining_resource_a = task.resource_a_time
        self.remaining_resource_b = task.resource_b_time

        self.holding_resource_a = False
        self.holding_resource_b = False

    @property
    def is_complete(self) -> bool:
        return (
            self.remaining_cpu_only == 0
            and self.remaining_resource_a == 0
            and self.remaining_resource_b == 0
        )

    @property
    def holds_any_resource(self) -> bool:
        return self.holding_resource_a or self.holding_resource_b

    def __repr__(self) -> str:
        return f"Job({self.task.task_id}.{self.job_number})"

    @property
    def job_id(self) -> str:
        return f"{self.task.task_id}.{self.job_number}"

    def effective_priority(self, resource_ceilings: Dict[str, int]) -> int:
        """PCP/ICPP-style effective priority while holding resources.

        Under PCP, when a job locks a resource, its priority is raised to the
        ceiling of that resource. With our numeric convention (smaller is higher),
        this means taking the minimum of its base DM priority and any ceilings of
        resources it currently holds.
        """
        eff = self.task.priority
        if self.holding_resource_a:
            eff = min(eff, resource_ceilings["A"])
        if self.holding_resource_b:
            eff = min(eff, resource_ceilings["B"])
        return eff


def compute_resource_ceilings(tasks: List[Task]) -> Dict[str, int]:
    """Return ceilings as DM priority numbers (smaller => higher priority)."""
    ceilings: Dict[str, int] = {}

    users_a = [t for t in tasks if t.resource_a_time > 0]
    users_b = [t for t in tasks if t.resource_b_time > 0]

    if users_a:
        ceilings["A"] = min(t.priority for t in users_a)
    if users_b:
        ceilings["B"] = min(t.priority for t in users_b)

    return ceilings


def system_ceiling(resource_holders: Dict[str, Optional[Job]], resource_ceilings: Dict[str, int]) -> int:
    """Return the current system ceiling (smaller => higher). If no locks, returns +inf."""
    locked = [res for res, holder in resource_holders.items() if holder is not None]
    if not locked:
        return 10**9
    return min(resource_ceilings[res] for res in locked)


def system_ceiling_excluding(
    resource_holders: Dict[str, Optional[Job]],
    resource_ceilings: Dict[str, int],
    exclude_job: Optional[Job],
) -> int:
    """System ceiling considering only resources locked by other jobs."""
    locked = [
        res
        for res, holder in resource_holders.items()
        if holder is not None and (exclude_job is None or holder is not exclude_job)
    ]
    if not locked:
        return 10**9
    return min(resource_ceilings[res] for res in locked)


def blocking_sources(
    resource_holders: Dict[str, Optional[Job]],
    resource_ceilings: Dict[str, int],
    sys_ceil: int,
) -> List[dict]:
    """Return a list of sources that induce the current system ceiling.

    Each source item is {resource: 'A'|'B', job_id: 'i.j'}.
    If no resources are locked (sys_ceil is effectively +inf), returns [].
    """
    if sys_ceil >= 10**8:
        return []

    sources: List[dict] = []
    for res, holder in resource_holders.items():
        if holder is None:
            continue
        if resource_ceilings.get(res) == sys_ceil:
            sources.append({"resource": res, "job_id": holder.job_id})
    return sources


def generate_jobs(tasks: List[Task], end_time: int) -> List[Tuple[int, Job]]:
    all_jobs: List[Tuple[int, Job]] = []
    for task in tasks:
        job_num = 0
        t = task.phase
        while t < end_time:
            all_jobs.append((t, Job(task, t, job_num)))
            t += task.period
            job_num += 1
    all_jobs.sort(key=lambda x: x[0])
    return all_jobs


def generate_jobs_with_metadata(tasks: List[Task], end_time: int) -> Tuple[List[Tuple[int, Job]], Dict[str, dict]]:
    """Generate jobs plus a metadata dict keyed by job_id for reporting/plotting."""
    jobs = generate_jobs(tasks, end_time)
    meta: Dict[str, dict] = {}
    for release_t, job in jobs:
        meta[job.job_id] = {
            "task_id": job.task.task_id,
            "job_id": job.job_id,
            "release": release_t,
            "abs_deadline": job.absolute_deadline,
            "start": None,
            "finish": None,  # last time unit executed (inclusive)
            "completion": None,  # completion instant (finish+1)
        }
    return jobs, meta


def is_runnable(job: Job, sys_ceil: int) -> bool:
    # NOTE: With PCP, the system ceiling is used to decide whether a job may
    # ENTER a critical section (lock a resource). It does not prevent CPU-only
    # execution. We keep this helper only for legacy callers; the main loop now
    # chooses a job based on whether it can make progress.
    return True


def try_lock(resource: str, job: Job, resource_holders: Dict[str, Optional[Job]], sys_ceil: int) -> bool:
    """Attempt to lock resource for job under PCP lock rule."""
    if resource_holders[resource] is not None and resource_holders[resource] is not job:
        return False

    # If already holding, ok.
    if (resource == "A" and job.holding_resource_a) or (resource == "B" and job.holding_resource_b):
        return True

    # Lock rule: must have higher priority than current system ceiling.
    if job.task.priority < sys_ceil:
        resource_holders[resource] = job
        if resource == "A":
            job.holding_resource_a = True
        else:
            job.holding_resource_b = True
        return True

    return False


def release_if_done(resource: str, job: Job, resource_holders: Dict[str, Optional[Job]]) -> None:
    if resource == "A" and job.remaining_resource_a == 0 and job.holding_resource_a:
        job.holding_resource_a = False
        if resource_holders["A"] is job:
            resource_holders["A"] = None
    if resource == "B" and job.remaining_resource_b == 0 and job.holding_resource_b:
        job.holding_resource_b = False
        if resource_holders["B"] is job:
            resource_holders["B"] = None


def simulate_dm_pcp(tasks: List[Task], end_time: int) -> Tuple[List[dict], List[dict], List[dict], Dict[str, dict]]:
    """Simulate DM scheduling with PCP.

    Returns:
      trace: per-time-unit execution record
      ceiling_trace: per-time-unit system ceiling/locks
      block_trace: per-time-unit blocking records (can have multiple per t)
      job_meta: per-job release/start/finish/deadline info
    """

    resource_ceilings = compute_resource_ceilings(tasks)
    resource_holders: Dict[str, Optional[Job]] = {"A": None, "B": None}

    all_jobs, job_meta = generate_jobs_with_metadata(tasks, end_time)

    ready: List[Job] = []
    current: Optional[Job] = None
    job_index = 0

    trace: List[dict] = []
    ceiling_trace: List[dict] = []
    block_trace: List[dict] = []

    for t in range(end_time):
        # release jobs
        while job_index < len(all_jobs) and all_jobs[job_index][0] == t:
            ready.append(all_jobs[job_index][1])
            job_index += 1

        # re-queue current job if it didn't finish
        if current is not None and not current.is_complete:
            ready.append(current)
            current = None

        # purge completed jobs from ready list
        ready = [j for j in ready if not j.is_complete]

        sys_ceil = system_ceiling(resource_holders, resource_ceilings)
        ceiling_trace.append({"time": t, "system_ceiling": sys_ceil, "locks": {
            "A": resource_holders["A"],
            "B": resource_holders["B"],
        }})

        # Choose a job to execute for this tick.
        # Priority order uses EFFECTIVE priority (priority boosted to ceiling while holding a resource).
        # We then pick the first job in that order that can make progress this tick.
        def candidate_key(j: Job):
            return (
                j.effective_priority(resource_ceilings),
                j.task.priority,
                j.arrival_time,
                j.task.task_id,
                j.job_number,
            )

        ready.sort(key=candidate_key)

        current = None
        exec_type = "idle"

        for cand in list(ready):
            # CPU-only is always runnable.
            if cand.remaining_cpu_only > 0:
                current = cand
                exec_type = "cpu"
                break

            # Next: Resource A
            if cand.remaining_resource_a > 0:
                if cand.holding_resource_a:
                    current = cand
                    exec_type = "resource_a"
                    break

                # Attempt to lock under PCP rule, comparing against ceiling induced by OTHER jobs.
                sys_excl = system_ceiling_excluding(resource_holders, resource_ceilings, exclude_job=cand)
                if resource_holders["A"] is None and cand.task.priority < sys_excl:
                    resource_holders["A"] = cand
                    cand.holding_resource_a = True
                    current = cand
                    exec_type = "resource_a"
                    break

                # Blocked on acquiring A
                if resource_holders["A"] is not None:
                    holder = resource_holders["A"]
                    reason = f"RA held by {holder.job_id}"
                    block_type = "RA_resource_busy"
                    sources = [{"resource": "A", "job_id": holder.job_id}]
                else:
                    reason = f"lock rule: priority={cand.task.priority} not < system_ceiling(other)={sys_excl}"
                    block_type = "RA_ceiling_lock_rule"
                    sources = blocking_sources(resource_holders, resource_ceilings, sys_excl)
                block_trace.append({
                    "time": t,
                    "task_id": cand.task.task_id,
                    "job_id": cand.job_id,
                    "block_type": block_type,
                    "details": reason,
                    "blocked_by": sources,
                })
                continue

            # Next: Resource B
            if cand.remaining_resource_b > 0:
                if cand.holding_resource_b:
                    current = cand
                    exec_type = "resource_b"
                    break

                sys_excl = system_ceiling_excluding(resource_holders, resource_ceilings, exclude_job=cand)
                if resource_holders["B"] is None and cand.task.priority < sys_excl:
                    resource_holders["B"] = cand
                    cand.holding_resource_b = True
                    current = cand
                    exec_type = "resource_b"
                    break

                # Blocked on acquiring B
                if resource_holders["B"] is not None:
                    holder = resource_holders["B"]
                    reason = f"RB held by {holder.job_id}"
                    block_type = "RB_resource_busy"
                    sources = [{"resource": "B", "job_id": holder.job_id}]
                else:
                    reason = f"lock rule: priority={cand.task.priority} not < system_ceiling(other)={sys_excl}"
                    block_type = "RB_ceiling_lock_rule"
                    sources = blocking_sources(resource_holders, resource_ceilings, sys_excl)
                block_trace.append({
                    "time": t,
                    "task_id": cand.task.task_id,
                    "job_id": cand.job_id,
                    "block_type": block_type,
                    "details": reason,
                    "blocked_by": sources,
                })
                continue

        if current is not None:
            ready.remove(current)

        if current is None:
            trace.append({"time": t, "task_id": None, "job": None, "type": "idle"})
            continue

        # Record job start time if first time it executes
        meta = job_meta.get(current.job_id)
        if meta is not None and meta["start"] is None:
            meta["start"] = t

        # Execute 1 unit of selected demand
        if exec_type == "cpu":
            current.remaining_cpu_only -= 1
        elif exec_type == "resource_a":
            current.remaining_resource_a -= 1
            release_if_done("A", current, resource_holders)
        elif exec_type == "resource_b":
            current.remaining_resource_b -= 1
            release_if_done("B", current, resource_holders)

        # record
        trace.append({
            "time": t,
            "task_id": None if current is None else current.task.task_id,
            "job": None if current is None else current,
            "type": exec_type,
        })

        # If job completed exactly at end of this tick, clear for next tick
        if current is not None and current.is_complete:
            meta = job_meta.get(current.job_id)
            if meta is not None:
                meta["finish"] = t
                meta["completion"] = t + 1
            current = None

    return trace, ceiling_trace, block_trace, job_meta


def compress_trace(trace: List[dict]) -> List[dict]:
    """Compress unit-time trace into execution segments."""
    segments: List[dict] = []
    if not trace:
        return segments

    def key(e: dict) -> Tuple[Optional[int], str, Optional[str]]:
        job = e.get("job")
        job_id = None if job is None else f"{job.task.task_id}.{job.job_number}"
        return (e.get("task_id"), e.get("type"), job_id)

    start = trace[0]["time"]
    prev = trace[0]

    for entry in trace[1:]:
        if key(entry) == key(prev):
            prev = entry
            continue
        segments.append({
            "start": start,
            "end": prev["time"] + 1,
            "task_id": prev.get("task_id"),
            "type": prev.get("type"),
            "job": prev.get("job"),
        })
        start = entry["time"]
        prev = entry

    segments.append({
        "start": start,
        "end": prev["time"] + 1,
        "task_id": prev.get("task_id"),
        "type": prev.get("type"),
        "job": prev.get("job"),
    })
    return segments


def compress_blocks(block_trace: List[dict]) -> List[dict]:
    """Compress blocking trace into segments per job+block_type."""
    if not block_trace:
        return []

    # Sort by time then stable
    entries = sorted(block_trace, key=lambda e: (e["time"], e["task_id"], e["job_id"], e["block_type"]))
    segments: List[dict] = []

    def key(e: dict) -> Tuple[int, str, str, str]:
        blocked_by = e.get("blocked_by") or []
        # canonical string so we can keep segments stable when blocker changes
        by_str = ";".join(f"{b.get('resource')}:{b.get('job_id')}" for b in blocked_by)
        return (e["task_id"], e["job_id"], e["block_type"], by_str)

    start = entries[0]["time"]
    prev = entries[0]
    for e in entries[1:]:
        if e["time"] == prev["time"] + 1 and key(e) == key(prev):
            prev = e
            continue
        segments.append({
            "start": start,
            "end": prev["time"] + 1,
            "task_id": prev["task_id"],
            "job_id": prev["job_id"],
            "block_type": prev["block_type"],
            "blocked_by": prev.get("blocked_by") or [],
        })
        start = e["time"]
        prev = e

    segments.append({
        "start": start,
        "end": prev["time"] + 1,
        "task_id": prev["task_id"],
        "job_id": prev["job_id"],
        "block_type": prev["block_type"],
        "blocked_by": prev.get("blocked_by") or [],
    })
    return segments


def print_trace(trace: List[dict]) -> None:
    print("\nSchedule Trace (DM + PCP)")
    print("-" * 80)
    print(f"{'t':<4} {'Exec':<10} {'Type':<12} {'Job':<10}")
    print("-" * 80)

    for e in trace:
        t = e["time"]
        tid = e["task_id"]
        etype = e["type"]
        job = e.get("job")
        job_str = "-" if job is None else f"{job.task.task_id}.{job.job_number}"
        exec_str = "IDLE" if tid is None else f"T{tid}"
        print(f"{t:<4} {exec_str:<10} {etype:<12} {job_str:<10}")


def print_block_trace(block_trace: List[dict]) -> None:
    print("\nBlocking Trace")
    print("-" * 120)
    print(f"{'t':<4} {'Task':<6} {'Job':<8} {'Block Type':<22} {'Blocked By':<20} {'Details'}")
    print("-" * 120)
    for e in sorted(block_trace, key=lambda x: (x["time"], x["task_id"], x["job_id"], x["block_type"])):
        blocked_by = e.get("blocked_by") or []
        if blocked_by:
            by_str = ",".join(f"{b['resource']}:{b['job_id']}" for b in blocked_by)
        else:
            by_str = "-"
        print(
            f"{e['time']:<4} "
            f"T{e['task_id']:<5} "
            f"{e['job_id']:<8} "
            f"{e['block_type']:<22} "
            f"{by_str:<20} "
            f"{e['details']}"
        )


def print_job_report(job_meta: Dict[str, dict]) -> None:
    print("\nJob Report (release/start/finish/deadline)")
    print("-" * 110)
    print(f"{'Job':<8} {'Rel':<6} {'Start':<6} {'Finish':<6} {'Comp':<6} {'AbsDL':<6} {'R':<6} {'Lateness':<9}")
    print("-" * 110)

    def safe_int(v):
        return "-" if v is None else str(v)

    items = list(job_meta.values())
    items.sort(key=lambda m: (m["release"], m["task_id"], m["job_id"]))
    for m in items:
        rel = m["release"]
        start = m["start"]
        finish = m["finish"]
        comp = m["completion"]
        dl = m["abs_deadline"]
        if comp is None:
            resp = None
            lateness = None
        else:
            resp = comp - rel
            lateness = comp - dl

        print(
            f"{m['job_id']:<8} {rel:<6} {safe_int(start):<6} {safe_int(finish):<6} "
            f"{safe_int(comp):<6} {dl:<6} {safe_int(resp):<6} {safe_int(lateness):<9}"
        )


def print_segments(segments: List[dict]) -> None:
    print("\nCompressed Segments")
    print("-" * 80)
    print(f"{'Start':<8} {'End':<8} {'Exec':<10} {'Type':<12} {'Job':<10}")
    print("-" * 80)

    for s in segments:
        tid = s["task_id"]
        exec_str = "IDLE" if tid is None else f"T{tid}"
        job = s.get("job")
        job_str = "-" if job is None else f"{job.task.task_id}.{job.job_number}"
        print(f"{s['start']:<8} {s['end']:<8} {exec_str:<10} {s['type']:<12} {job_str:<10}")


def draw_gantt(
    segments: List[dict],
    tasks: List[Task],
    end_time: int,
    out_path: str,
    job_meta: Dict[str, dict],
    block_segments: Optional[List[dict]] = None,
) -> None:
    fig, ax = plt.subplots(figsize=(14, 5))

    # Higher priority on top (smaller D)
    sorted_tasks = sorted(tasks, key=lambda t: t.priority)
    task_to_row = {task.task_id: i for i, task in enumerate(sorted_tasks)}

    row_height = 0.8
    y_ticks = []
    y_labels = []

    # background rows
    for task in sorted_tasks:
        row = task_to_row[task.task_id]
        y = row
        ax.add_patch(
            mpatches.Rectangle(
                (0, y - row_height / 2),
                end_time,
                row_height,
                facecolor="#f7f7f7",
                edgecolor="#cccccc",
                linewidth=1,
                zorder=0,
            )
        )
        y_ticks.append(y)
        y_labels.append(f"T{task.task_id} (D={task.deadline})")

    # colors
    cpu_color = "#4E79A7"
    a_color = "#F28E2B"
    b_color = "#E15759"
    idle_color = "#DDDDDD"
    block_color = "#7F7F7F"

    def segment_style(seg_type: str):
        if seg_type == "cpu":
            return dict(color=cpu_color, hatch=None, label="CPU")
        if seg_type == "resource_a":
            return dict(color=a_color, hatch="///", label="RA")
        if seg_type == "resource_b":
            return dict(color=b_color, hatch="\\\\\\", label="RB")
        return dict(color=idle_color, hatch=None, label="Idle")

    for seg in segments:
        if seg["type"] == "idle" or seg["task_id"] is None:
            continue

        row = task_to_row[seg["task_id"]]
        style = segment_style(seg["type"])
        ax.add_patch(
            mpatches.Rectangle(
                (seg["start"], row - row_height / 2),
                seg["end"] - seg["start"],
                row_height,
                facecolor=style["color"],
                edgecolor="black",
                linewidth=1.0,
                hatch=style["hatch"],
                zorder=2,
            )
        )
        job = seg.get("job")
        job_id = "" if job is None else job.job_id
        seg_type_label = seg["type"].replace("resource_", "R").upper()
        ax.text(
            (seg["start"] + seg["end"]) / 2,
            row,
            f"{job_id}\n{seg_type_label}",
            ha="center",
            va="center",
            fontsize=8,
            color="white",
            weight="bold",
            zorder=3,
        )

    # Overlay blocking segments (drawn behind execution but above background)
    if block_segments:
        for b in block_segments:
            row = task_to_row[b["task_id"]]
            ax.add_patch(
                mpatches.Rectangle(
                    (b["start"], row - row_height / 2),
                    b["end"] - b["start"],
                    row_height,
                    facecolor=block_color,
                    edgecolor="black",
                    linewidth=0.8,
                    alpha=0.35,
                    hatch="xx",
                    zorder=1.5,
                )
            )
            ax.text(
                (b["start"] + b["end"]) / 2,
                row,
                (
                    f"{b['job_id']}\nBLK" if not b.get("blocked_by")
                    else f"{b['job_id']}\nBLK by " + ",".join(f"{x['resource']}:{x['job_id']}" for x in b["blocked_by"])
                ),
                ha="center",
                va="center",
                fontsize=7,
                color="black",
                zorder=1.6,
            )

    # Release/deadline markers per job
    # - Release: green 'v' at release time
    # - Deadline: red 'x' at absolute deadline; if deadline exceeds horizon, pin to t=end_time
    #   and label with actual DL value.
    for m in job_meta.values():
        tid = m["task_id"]
        if tid not in task_to_row:
            continue
        row = task_to_row[tid]
        rel = m["release"]
        dl = m["abs_deadline"]
        # Release marker (green)
        if 0 <= rel <= end_time:
            ax.scatter(
                [rel],
                [row + row_height / 2 - 0.08],
                marker="v",
                s=45,
                c="#2CA02C",
                zorder=4,
                clip_on=False,
            )

        # Deadline marker (red)
        dl_x = dl if dl <= end_time else end_time
        ax.scatter(
            [dl_x],
            [row + row_height / 2 - 0.08],
            marker="x",
            s=55,
            c="#D62728",
            zorder=4,
            clip_on=False,
        )

        # Vertical line for deadlines within the horizon
        if 0 <= dl <= end_time:
            ax.axvline(dl, color="#D62728", linestyle=":", linewidth=1.0, alpha=0.5, zorder=1)

        # If deadline is beyond the plotted window, annotate its value at the right edge
        if dl > end_time:
            ax.text(
                end_time + 0.05,
                row + row_height / 2 - 0.12,
                f"DL={dl}",
                fontsize=7,
                color="#D62728",
                ha="left",
                va="center",
                zorder=4,
                clip_on=False,
            )

    # Extend slightly past end_time so markers at t=end_time are visible
    ax.set_xlim(0, end_time + 0.6)
    ax.set_ylim(-1, len(sorted_tasks))
    ax.set_yticks(y_ticks)
    ax.set_yticklabels(y_labels)
    ax.set_xticks(range(0, end_time + 1))
    ax.grid(axis="x", linestyle="--", alpha=0.4)

    ax.set_title("DM + PCP Schedule")
    ax.set_xlabel("Time")

    # legend
    legend_patches = [
        mpatches.Patch(facecolor=cpu_color, edgecolor="black", label="CPU"),
        mpatches.Patch(facecolor=a_color, edgecolor="black", hatch="///", label="RA"),
        mpatches.Patch(facecolor=b_color, edgecolor="black", hatch="\\\\\\", label="RB"),
        mpatches.Patch(facecolor=block_color, edgecolor="black", hatch="xx", alpha=0.35, label="Blocked"),
    ]
    ax.legend(handles=legend_patches, loc="upper right")

    plt.tight_layout()
    plt.savefig(out_path, dpi=250, bbox_inches="tight")


def main() -> None:
    parser = argparse.ArgumentParser(description="DM scheduling with PCP (Priority Ceiling Protocol)")
    parser.add_argument("--end-time", type=int, default=10, help="Simulate from t=0 up to this time (exclusive)")
    parser.add_argument("--no-plot", action="store_true", help="Skip saving the Gantt chart")
    args = parser.parse_args()

    # Task table from prompt:
    # (phi, T, C, D, deltaA, deltaB)
    tasks = [
        Task(task_id=1, phase=7, period=7, computation_time=1, deadline=3, resource_a_time=0, resource_b_time=1),
        Task(task_id=2, phase=3, period=10, computation_time=2, deadline=10, resource_a_time=1, resource_b_time=0),
        Task(task_id=3, phase=1, period=13, computation_time=2, deadline=11, resource_a_time=0, resource_b_time=1),
        Task(task_id=4, phase=0, period=13, computation_time=3, deadline=13, resource_a_time=3, resource_b_time=0),
    ]

    end_time = args.end_time

    ceilings = compute_resource_ceilings(tasks)
    print("Resource ceilings (DM priority numbers; smaller => higher priority):")
    print(f"  RA ceiling = {ceilings.get('A')}  (task with smallest D using RA)")
    print(f"  RB ceiling = {ceilings.get('B')}  (task with smallest D using RB)")

    trace, _ceiling_trace, block_trace, job_meta = simulate_dm_pcp(tasks, end_time=end_time)
    segments = compress_trace(trace)
    block_segments = compress_blocks(block_trace)

    print_trace(trace)
    print_segments(segments)
    print_job_report(job_meta)
    if block_trace:
        print_block_trace(block_trace)
    else:
        print("\nBlocking Trace: (none observed in this horizon)")

    if not args.no_plot:
        out_path = "dm_pcp_schedule.png"
        draw_gantt(
            segments,
            tasks,
            end_time=end_time,
            out_path=out_path,
            job_meta=job_meta,
            block_segments=block_segments,
        )
        print(f"\nSaved Gantt chart to: {out_path}")


if __name__ == "__main__":
    main()
