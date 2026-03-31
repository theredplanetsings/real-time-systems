import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import namedtuple

# Task definition: (phase, period, computation_time, relative_deadline)
Task = namedtuple('Task', ['id', 'phase', 'period', 'computation', 'deadline'])

# Define the task set: (φ, T, C, D)
tasks = [
    Task(1, 0, 5, 1, 5),
    Task(2, 2, 8, 3, 8),
    Task(3, 0, 4, 1, 4),
    Task(4, 1, 6, 1, 6)
]

def density_test(tasks):
    """Apply the density test to determine schedulability"""
    print("=" * 60)
    print("DENSITY TEST")
    print("=" * 60)
    print(f"{'Task':<8} {'φ':<6} {'T':<6} {'C':<6} {'D':<6} {'min(D,T)':<10} {'Density':<10}")
    print("-" * 60)
    
    total_density = 0
    for task in tasks:
        min_dt = min(task.deadline, task.period)
        density = task.computation / min_dt
        total_density += density
        print(f"{task.id:<8} {task.phase:<6} {task.period:<6} {task.computation:<6} "
              f"{task.deadline:<6} {min_dt:<10} {density:.4f}")
    
    print("-" * 60)
    print(f"Total Density: {total_density:.4f}")
    
    if total_density <= 1:
        print("✓ Density test PASSED - Task set is schedulable")
    else:
        print("✗ Density test FAILED - Task set may not be schedulable")
    print("=" * 60)
    print()
    return total_density

# Job instance for tracking individual job releases
class Job:
    def __init__(self, task_id, release_time, absolute_deadline, remaining_time):
        self.task_id = task_id
        self.release_time = release_time
        self.absolute_deadline = absolute_deadline
        self.remaining_time = remaining_time
    
    def __repr__(self):
        return f"Job(T{self.task_id}, release={self.release_time}, deadline={self.absolute_deadline}, remaining={self.remaining_time})"

def edf_schedule_nonpreemptive(tasks, time_limit):
    """Simulate non-preemptive EDF scheduling"""
    schedule = []
    ready_queue = []
    current_time = 0
    current_job = None  # Track currently executing job
    
    # Generate all job releases within the time limit
    all_jobs = []
    for task in tasks:
        time = task.phase
        while time < time_limit:
            job = Job(task.id, time, time + task.deadline, task.computation)
            all_jobs.append(job)
            time += task.period
    
    all_jobs.sort(key=lambda j: j.release_time)
    job_index = 0
    
    while current_time < time_limit:
        # Add newly released jobs to ready queue
        while job_index < len(all_jobs) and all_jobs[job_index].release_time <= current_time:
            ready_queue.append(all_jobs[job_index])
            job_index += 1
        
        # If a job is currently executing, continue until completion
        if current_job is not None:
            exec_time = current_job.remaining_time
            schedule.append((f'T{current_job.task_id}', current_time, current_time + exec_time))
            current_time += exec_time
            current_job = None
            
            # After job completes, check for newly released jobs
            while job_index < len(all_jobs) and all_jobs[job_index].release_time <= current_time:
                ready_queue.append(all_jobs[job_index])
                job_index += 1
        
        if not ready_queue:
            # Idle time - find next job release
            if job_index < len(all_jobs):
                next_release = all_jobs[job_index].release_time
                schedule.append(('IDLE', current_time, next_release))
                current_time = next_release
            else:
                # No more jobs
                if current_time < time_limit:
                    schedule.append(('IDLE', current_time, time_limit))
                break
        else:
            # Sort ready queue by absolute deadline (EDF), then by release time for ties
            ready_queue.sort(key=lambda j: (j.absolute_deadline, j.release_time, j.task_id))
            
            # Start executing the job with earliest deadline (non-preemptive)
            current_job = ready_queue.pop(0)
    
    return schedule

def visualize_schedule(schedule, tasks, time_limit):
    """Create a Gantt chart of the schedule with each task on its own row"""
    fig, ax = plt.subplots(figsize=(22, 10))
    
    # Color map for tasks
    colors = {
        'T1': '#FF6B6B',
        'T2': '#4ECDC4',
        'T3': '#45B7D1',
        'T4': '#FFA07A',
        'IDLE': '#E0E0E0'
    }
    
    # Y-position for each task (Task 1 at top, Task 4 at bottom)
    task_y_positions = {1: 3, 2: 2, 3: 1, 4: 0}
    
    # Track job instances for each task
    task_dict = {task.id: task for task in tasks}
    job_instances = {i: [] for i in range(1, 5)}
    
    # Generate job instances with their timing information
    for task in tasks:
        time = task.phase
        job_num = 1
        while time < time_limit:
            release_time = time
            absolute_deadline = time + task.deadline
            relative_deadline = task.deadline
            
            # Find actual start and finish times from schedule
            start_times = []
            finish_times = []
            for item, start, end in schedule:
                if item == f'T{task.id}' and start >= release_time and start < release_time + task.period:
                    start_times.append(start)
                    finish_times.append(end)
            
            actual_start = min(start_times) if start_times else None
            actual_finish = max(finish_times) if finish_times else None
            
            job_instances[task.id].append({
                'job_num': job_num,
                'release': release_time,
                'abs_deadline': absolute_deadline,
                'rel_deadline': relative_deadline,
                'start': actual_start,
                'finish': actual_finish
            })
            
            time += task.period
            job_num += 1
    
    # Draw the schedule bars - each task on its own row
    for item, start, end in schedule:
        if item != 'IDLE':
            task_id = int(item[1])  # Extract task number from 'T1', 'T2', etc.
            y_pos = task_y_positions[task_id]
            ax.barh(y_pos, end - start, left=start, height=0.6, 
                    color=colors[item],
                    edgecolor='black', linewidth=1.5)
            # Add execution marker in the middle
            if end - start > 0.5:
                ax.text((start + end) / 2, y_pos, '█', 
                       ha='center', va='center', fontsize=12, fontweight='bold', color='white')
    
    # Draw timing markers for each job instance
    for task_id, jobs in job_instances.items():
        y_pos = task_y_positions[task_id]
        
        for job in jobs:
            if job['release'] >= time_limit:
                continue
                
            release = job['release']
            abs_deadline = job['abs_deadline']
            start = job['start']
            finish = job['finish']
            
            # Release time (green upward arrow)
            ax.annotate('', xy=(release, y_pos + 0.35), xytext=(release, y_pos - 0.35),
                       arrowprops=dict(arrowstyle='->', color='green', lw=2.5))
            ax.text(release, y_pos - 0.55, f'R', 
                   fontsize=9, ha='center', color='green', fontweight='bold',
                   bbox=dict(boxstyle='circle', facecolor='white', edgecolor='green', alpha=0.8))
            
            # Absolute deadline (red downward arrow)
            if abs_deadline <= time_limit:
                ax.annotate('', xy=(abs_deadline, y_pos - 0.35), xytext=(abs_deadline, y_pos + 0.35),
                           arrowprops=dict(arrowstyle='->', color='red', lw=2.5))
                ax.text(abs_deadline, y_pos + 0.55, f'D', 
                       fontsize=9, ha='center', color='red', fontweight='bold',
                       bbox=dict(boxstyle='circle', facecolor='white', edgecolor='red', alpha=0.8))
            
            # Draw span showing release to absolute deadline with relative deadline label
            if abs_deadline <= time_limit:
                ax.plot([release, abs_deadline], [y_pos - 0.8, y_pos - 0.8], 
                       color=colors[f'T{task_id}'], linewidth=3, alpha=0.6)
                # Mark relative deadline
                mid_point = (release + abs_deadline) / 2
                ax.text(mid_point, y_pos - 0.95, f'd={job["rel_deadline"]}', 
                       fontsize=8, ha='center', style='italic', 
                       bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7))
            
            # Mark actual execution start time
            if start is not None:
                ax.axvline(x=start, ymin=(y_pos - 0.25) / 4, ymax=(y_pos + 0.25) / 4,
                          color='darkgreen', linewidth=2.5, linestyle='--', alpha=0.7)
            
            # Mark actual execution finish time
            if finish is not None:
                ax.axvline(x=finish, ymin=(y_pos - 0.25) / 4, ymax=(y_pos + 0.25) / 4,
                          color='darkblue', linewidth=2.5, linestyle='--', alpha=0.7)
    
    ax.set_xlim(0, time_limit)
    ax.set_ylim(-0.5, 3.5)
    ax.set_xlabel('Time (t)', fontsize=14, fontweight='bold')
    ax.set_ylabel('Tasks', fontsize=14, fontweight='bold')
    ax.set_title('Non-Preemptive EDF Schedule (t=0 to t=16)\nR=Release, D=Absolute Deadline, d=Relative Deadline\nGreen dashed=Start, Blue dashed=Finish', 
                fontsize=14, fontweight='bold')
    ax.set_yticks([0, 1, 2, 3])
    ax.set_yticklabels(['Task 4', 'Task 3', 'Task 2', 'Task 1'], fontsize=12)
    ax.set_xticks(range(0, time_limit + 1))
    ax.grid(True, axis='x', alpha=0.3, linestyle='--')
    ax.grid(True, axis='y', alpha=0.2, linestyle=':')
    
    # Create legend
    legend_elements = [
        mpatches.Patch(facecolor=colors[f'T{i}'], edgecolor='black', label=f'Task {i} Execution') 
        for i in range(1, 5)
    ]
    legend_elements.extend([
        plt.Line2D([0], [0], color='green', lw=2.5, marker='^', label='Release Time (R)', markersize=8),
        plt.Line2D([0], [0], color='red', lw=2.5, marker='v', label='Absolute Deadline (D)', markersize=8),
        plt.Line2D([0], [0], color='darkgreen', lw=2.5, linestyle='--', label='Execution Start'),
        plt.Line2D([0], [0], color='darkblue', lw=2.5, linestyle='--', label='Execution Finish'),
        plt.Line2D([0], [0], color='gray', lw=3, alpha=0.6, label='Release to Deadline Span (d)'),
    ])
    ax.legend(handles=legend_elements, loc='upper right', fontsize=10, ncol=2)
    
    plt.tight_layout()
    plt.savefig('/Users/chrisrutherford/Downloads/Csc-358/HW/edf_schedule.png', dpi=300, bbox_inches='tight')
    print("Schedule visualization saved as 'edf_schedule.png'")
    plt.show()

def print_schedule(schedule, time_limit):
    """Print the schedule in text format"""
    print("=" * 60)
    print(f"NON-PREEMPTIVE EDF SCHEDULE (t=0 to t={time_limit})")
    print("=" * 60)
    print(f"{'Task':<10} {'Start':<10} {'End':<10} {'Duration':<10}")
    print("-" * 60)
    
    for item, start, end in schedule:
        duration = end - start
        print(f"{item:<10} {start:<10} {end:<10} {duration:<10}")
    
    print("=" * 60)
    print()

# Main execution
if __name__ == "__main__":
    # Part 1: Density Test
    total_density = density_test(tasks)
    
    # Part 2: Non-Preemptive EDF Scheduling
    time_limit = 16
    schedule = edf_schedule_nonpreemptive(tasks, time_limit)
    print_schedule(schedule, time_limit)
    
    # Visualize
    visualize_schedule(schedule, tasks, time_limit)
