import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import namedtuple, defaultdict

Task = namedtuple('Task', ['id', 'period', 'computation'])

class Job:
    def __init__(self, task_id, release_time, remaining_time, deadline, job_num):
        self.task_id = task_id
        self.release_time = release_time
        self.remaining_time = remaining_time
        self.deadline = deadline
        self.job_num = job_num

    def key(self):
        return (self.task_id, self.release_time)

    def __repr__(self):
        return f"Job(T{self.task_id}.{self.job_num}, r={self.release_time}, d={self.deadline}, rem={self.remaining_time})"


def simulate_grm(tasks, end_time, processors):
    """Simulate preemptive Global RM scheduling on m identical processors."""
    ready_queue = []
    next_release = {task.id: 0 for task in tasks}
    job_counters = {task.id: 0 for task in tasks}

    schedule = []  # list of {time, assignments: {proc: job or None}}

    for t in range(end_time):
        # Release new jobs
        for task in tasks:
            if t == next_release[task.id]:
                job_num = job_counters[task.id]
                job_counters[task.id] += 1
                ready_queue.append(
                    Job(task.id, t, task.computation, t + task.period, job_num)
                )
                next_release[task.id] += task.period

        # Sort by RM priority: shorter period = higher priority
        ready_queue.sort(key=lambda j: (next(task.period for task in tasks if task.id == j.task_id),
                                        j.release_time, j.task_id))

        assignments = {}
        for p in range(processors):
            if ready_queue:
                job = ready_queue.pop(0)
                assignments[p] = job
                job.remaining_time -= 1
                if job.remaining_time > 0:
                    ready_queue.append(job)
            else:
                assignments[p] = None

        schedule.append({'time': t, 'assignments': assignments})

    return schedule


def build_segments(schedule, processors):
    """Build execution segments per processor and per job."""
    segments = []
    job_segments = defaultdict(list)

    last_job = {p: None for p in range(processors)}
    last_start = {p: None for p in range(processors)}

    for entry in schedule:
        t = entry['time']
        for p in range(processors):
            job = entry['assignments'][p]
            if job is last_job[p]:
                continue
            # Close previous segment
            if last_job[p] is not None:
                seg = {
                    'proc': p,
                    'job': last_job[p],
                    'start': last_start[p],
                    'end': t
                }
                segments.append(seg)
                job_segments[last_job[p].key()].append(seg)
            # Start new segment
            last_job[p] = job
            last_start[p] = t

    # Close any open segments
    end_time = schedule[-1]['time'] + 1 if schedule else 0
    for p in range(processors):
        if last_job[p] is not None:
            seg = {
                'proc': p,
                'job': last_job[p],
                'start': last_start[p],
                'end': end_time
            }
            segments.append(seg)
            job_segments[last_job[p].key()].append(seg)

    return segments, job_segments


def enumerate_jobs(tasks, end_time):
    """Generate job instances within the horizon for plotting markers."""
    jobs = []
    for task in tasks:
        t = 0
        job_num = 0
        while t < end_time:
            jobs.append({
                'task_id': task.id,
                'release': t,
                'deadline': t + task.period,
                'job_num': job_num,
                'key': (task.id, t)
            })
            t += task.period
            job_num += 1
    return jobs


def plot_schedule(tasks, schedule, segments, job_segments, end_time, processors):
    fig, ax = plt.subplots(figsize=(20, 8))

    # Task row positions (Task 1 at top)
    task_rows = {1: 2, 2: 1, 3: 0}

    # Processor colors
    proc_colors = {0: '#5B8FF9', 1: '#5AD8A6'}

    # Draw background rows
    for task_id, row in task_rows.items():
        ax.add_patch(mpatches.Rectangle((0, row - 0.4), end_time, 0.8,
                                        facecolor='#f7f7f7',
                                        edgecolor='#cccccc',
                                        linewidth=1,
                                        zorder=0))

    # Draw execution segments
    for seg in segments:
        job = seg['job']
        row = task_rows[job.task_id]
        color = proc_colors[seg['proc']]
        ax.barh(row, seg['end'] - seg['start'], left=seg['start'], height=0.6,
                color=color, edgecolor='black', linewidth=1.2)
        ax.text((seg['start'] + seg['end']) / 2, row, f"P{seg['proc'] + 1}",
                ha='center', va='center', fontsize=9, color='white', fontweight='bold')
        # Segment start/finish markers
        ax.vlines(seg['start'], row - 0.3, row + 0.3, color='darkgreen', linestyle='--', linewidth=1.8)
        ax.vlines(seg['end'], row - 0.3, row + 0.3, color='darkblue', linestyle='--', linewidth=1.8)

    # Draw release and deadline markers
    jobs = enumerate_jobs(tasks, end_time)
    for job in jobs:
        row = task_rows[job['task_id']]
        release = job['release']
        deadline = job['deadline']

        ax.annotate('', xy=(release, row + 0.35), xytext=(release, row - 0.35),
                    arrowprops=dict(arrowstyle='->', color='green', lw=2))
        ax.text(release, row - 0.55, 'R', fontsize=9, ha='center', color='green',
                fontweight='bold', bbox=dict(boxstyle='circle', facecolor='white',
                edgecolor='green', alpha=0.8))

        if deadline <= end_time:
            ax.annotate('', xy=(deadline, row - 0.35), xytext=(deadline, row + 0.35),
                        arrowprops=dict(arrowstyle='->', color='red', lw=2))
            ax.text(deadline, row + 0.55, 'D', fontsize=9, ha='center', color='red',
                    fontweight='bold', bbox=dict(boxstyle='circle', facecolor='white',
                    edgecolor='red', alpha=0.8))

    ax.set_xlim(0, end_time)
    ax.set_ylim(-0.6, 2.6)
    ax.set_xlabel('Time (t)', fontsize=12, fontweight='bold')
    ax.set_ylabel('Tasks', fontsize=12, fontweight='bold')
    ax.set_title('Global RM Schedule on 2 Processors (t=0 to t=15)\n'
                 'R=Release, D=Deadline, dashed lines=Segment Start/Finish',
                 fontsize=13, fontweight='bold')
    ax.set_yticks([0, 1, 2])
    ax.set_yticklabels(['Task 3', 'Task 2', 'Task 1'], fontsize=11)
    ax.set_xticks(range(0, end_time + 1))
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')
    ax.grid(True, axis='y', alpha=0.2, linestyle=':')

    legend_elements = [
        mpatches.Patch(facecolor=proc_colors[0], edgecolor='black', label='Processor 1'),
        mpatches.Patch(facecolor=proc_colors[1], edgecolor='black', label='Processor 2'),
        plt.Line2D([0], [0], color='green', lw=2, marker='^', label='Release Time (R)', markersize=8),
        plt.Line2D([0], [0], color='red', lw=2, marker='v', label='Deadline (D)', markersize=8),
        plt.Line2D([0], [0], color='darkgreen', lw=2, linestyle='--', label='Segment Start'),
        plt.Line2D([0], [0], color='darkblue', lw=2, linestyle='--', label='Segment Finish')
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9, ncol=2)

    plt.tight_layout()
    plt.savefig('/Users/chrisrutherford/Downloads/Csc-358/HW/grm_schedule.png',
                dpi=300, bbox_inches='tight')
    print("Schedule visualization saved as 'grm_schedule.png'")
    plt.show()


def print_job_table(tasks, job_segments, end_time):
    jobs = enumerate_jobs(tasks, end_time)
    print("=" * 90)
    print("G-RM JOB DETAILS (t=0 to t=15)")
    print("=" * 90)
    print(f"{'Job':<10} {'Release':<8} {'Deadline':<8} {'Start':<8} {'Finish':<8} {'Segments':<35}")
    print("-" * 90)

    for job in jobs:
        segs = job_segments.get(job['key'], [])
        if segs:
            start = min(seg['start'] for seg in segs)
            finish = max(seg['end'] for seg in segs)
            seg_text = ", ".join([f"P{seg['proc'] + 1}:{seg['start']}-{seg['end']}" for seg in segs])
        else:
            start = None
            finish = None
            seg_text = "-"

        job_label = f"T{job['task_id']}.{job['job_num']}"
        print(f"{job_label:<10} {job['release']:<8} {job['deadline']:<8} {str(start):<8} {str(finish):<8} {seg_text:<35}")

    print("=" * 90)


if __name__ == "__main__":
    tasks = [
        Task(1, 5, 2),
        Task(2, 9, 6),
        Task(3, 16, 9)
    ]
    end_time = 16  # simulate t=0..15
    processors = 2

    schedule = simulate_grm(tasks, end_time, processors)
    segments, job_segments = build_segments(schedule, processors)

    print_job_table(tasks, job_segments, end_time)
    plot_schedule(tasks, schedule, segments, job_segments, end_time, processors)
