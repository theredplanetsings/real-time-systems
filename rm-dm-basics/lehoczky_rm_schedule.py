import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import namedtuple

# Task definition for RM: (period, computation_time)
TaskRM = namedtuple('TaskRM', ['id', 'period', 'computation'])

# Job instance for tracking individual job releases
class Job:
    def __init__(self, task_id, release_time, remaining_time, deadline):
        self.task_id = task_id
        self.release_time = release_time
        self.remaining_time = remaining_time
        self.deadline = deadline
        self.start_time = None
        self.finish_time = None
        self.completion_time = None
        self.response_time = None
    
    def __repr__(self):
        return f"Job(T{self.task_id}, release={self.release_time}, deadline={self.deadline})"


def rate_monotonic_schedule_lehoczky(tasks, end_time):
    """
    Schedule tasks using Rate Monotonic (RM) algorithm for Lehoczky's counterexample.
    Priority: Shorter period = Higher priority
    """
    print("=" * 80)
    print("LEHOCZKY'S COUNTEREXAMPLE - RATE MONOTONIC SCHEDULING")
    print("=" * 80)
    print(f"Task Set: (T, C) = (70, 26), (100, 62)")
    print(f"Schedule from t=0 to t={end_time}")
    print("=" * 80)
    print()
    
    print(f"{'Task':<8} {'Period (T)':<12} {'Computation (C)':<18} {'Priority':<10}")
    print("-" * 80)
    
    # Sort tasks by period (shorter period = higher priority)
    sorted_tasks = sorted(tasks, key=lambda t: t.period)
    for i, task in enumerate(sorted_tasks):
        priority_str = f"{i+1} (HIGHEST)" if i == 0 else str(i+1)
        print(f"T{task.id:<7} {task.period:<12} {task.computation:<18} {priority_str}")
    
    print("=" * 80)
    print()
    
    # Initialize ready queue
    ready_queue = []
    schedule = []  # (time, task_id or None)
    completed_jobs = []  # Track all completed jobs
    
    # Track next release time for each task
    next_release = {task.id: 0 for task in tasks}
    
    # Track all jobs created
    all_jobs = {1: [], 2: []}  # Jobs for each task
    
    # Simulate scheduling
    for t in range(end_time):
        # Release new jobs at their periods
        for task in tasks:
            if t == next_release[task.id]:
                absolute_deadline = t + task.period  # For RM, deadline = period
                job = Job(task.id, t, task.computation, absolute_deadline)
                ready_queue.append(job)
                all_jobs[task.id].append(job)
                next_release[task.id] += task.period
        
        # Sort ready queue by priority (period - shorter period first)
        ready_queue.sort(key=lambda job: next((task.period for task in tasks if task.id == job.task_id)))
        
        # Execute highest priority job
        if ready_queue:
            current_job = ready_queue[0]
            
            # Record start time if this is the first execution of this job
            if current_job.start_time is None:
                current_job.start_time = t
            
            schedule.append((t, current_job.task_id))
            current_job.remaining_time -= 1
            
            # Remove completed jobs
            if current_job.remaining_time == 0:
                current_job.finish_time = t
                current_job.completion_time = t + 1  # Completion time is end of current time unit
                current_job.response_time = current_job.completion_time - current_job.release_time
                completed_jobs.append(current_job)
                ready_queue.pop(0)
        else:
            schedule.append((t, None))  # Idle
    
    return schedule, all_jobs, completed_jobs


def print_detailed_job_info(all_jobs, completed_jobs, end_time):
    """Print detailed information about each job"""
    
    for task_id in sorted(all_jobs.keys()):
        jobs = all_jobs[task_id]
        print()
        print("=" * 110)
        print(f"TASK {task_id} - JOB DETAILS")
        print("=" * 110)
        print(f"{'Job #':<8} {'Release':<10} {'Start':<10} {'Finish':<10} {'Completion':<12} "
              f"{'Rel. DL':<10} {'Abs. DL':<10} {'Response':<12}")
        print("-" * 110)
        
        for i, job in enumerate(jobs, 1):
            if job in completed_jobs:
                print(f"{i:<8} {job.release_time:<10} {job.start_time:<10} {job.finish_time:<10} "
                      f"{job.completion_time:<12} {job.deadline - job.release_time:<10} "
                      f"{job.deadline:<10} {job.response_time:<12}")
            else:
                # Job not completed within the time window
                status = "INCOMPLETE" if job.start_time is None else f"Started at {job.start_time}, INCOMPLETE"
                print(f"{i:<8} {job.release_time:<10} {status}")


def print_gantt_table(schedule, tasks, end_time):
    """Print a text-based Gantt table showing the schedule"""
    
    print()
    print("=" * 110)
    print("GANTT CHART (TEXT REPRESENTATION)")
    print("=" * 110)
    print()
    
    # Group consecutive time units by task
    execution_blocks = []
    if schedule:
        current_task = schedule[0][1]
        start = 0
        
        for t, task_id in schedule[1:]:
            if task_id != current_task:
                execution_blocks.append((start, t - 1, current_task))
                current_task = task_id
                start = t
        execution_blocks.append((start, end_time - 1, current_task))
    
    # Print execution blocks
    print(f"{'Start':<10} {'End':<10} {'Task/Status':<15} {'Duration':<10}")
    print("-" * 110)
    for start, end, task_id in execution_blocks[:50]:  # Limit output
        task_str = f"T{task_id}" if task_id is not None else "IDLE"
        duration = end - start + 1
        print(f"{start:<10} {end:<10} {task_str:<15} {duration:<10}")
    
    if len(execution_blocks) > 50:
        print(f"... ({len(execution_blocks) - 50} more execution blocks)")
    print("=" * 110)


def visualize_schedule_detailed(schedule, tasks, end_time):
    """Visualize the schedule as a detailed Gantt chart - single chart for entire time range"""
    
    # Create a single large figure for the entire time range
    fig, ax = plt.subplots(figsize=(24, 8))
    
    # Color map for tasks
    colors = {1: '#FF6B6B', 2: '#4ECDC4', None: '#FFFFFF'}
    
    # Get unique task IDs from schedule
    unique_tasks = sorted(set(task_id for _, task_id in schedule if task_id is not None))
    num_tasks = len(unique_tasks)
    
    # Draw schedule - each task gets its own row
    for t, task_id in schedule:
        if task_id is not None:
            # Map task_id to row (0 = top task)
            row = unique_tasks.index(task_id)
            ax.barh(row, 1, left=t, height=0.8, 
                   color=colors.get(task_id, 'gray'), 
                   edgecolor='black', linewidth=0.1)
    
    # Add idle time indicators at the bottom
    idle_row = num_tasks
    for t, task_id in schedule:
        if task_id is None:
            ax.barh(idle_row, 1, left=t, height=0.8, 
                   color='#E0E0E0', edgecolor='black', linewidth=0.1)
    
    # Add release times and deadlines as vertical markers
    for task in tasks:
        row = unique_tasks.index(task.id)
        
        # Add release markers (green arrows pointing up)
        for release_t in range(0, end_time, task.period):
            ax.plot([release_t, release_t], [row - 0.45, row + 0.45], 
                   'g-', linewidth=1.5, alpha=0.7)
            ax.plot(release_t, row - 0.45, 'g^', markersize=6, alpha=0.7)
        
        # Add deadline markers (red arrows pointing down)
        for release_t in range(0, end_time, task.period):
            deadline_t = release_t + task.period
            if deadline_t <= end_time:
                ax.plot([deadline_t, deadline_t], [row - 0.45, row + 0.45], 
                       'r-', linewidth=1.5, alpha=0.7)
                ax.plot(deadline_t, row + 0.45, 'rv', markersize=6, alpha=0.7)
    
    # Formatting
    ax.set_xlim(0, end_time)
    ax.set_ylim(-0.5, num_tasks + 0.5)
    ax.set_xlabel('Time', fontsize=14, fontweight='bold')
    ax.set_ylabel('Tasks', fontsize=14, fontweight='bold')
    
    # Set x-axis ticks - use appropriate interval for readability
    tick_interval = 50 if end_time > 500 else (25 if end_time > 200 else 10)
    ax.set_xticks(range(0, end_time + 1, tick_interval))
    
    # Add minor ticks for better readability
    minor_tick_interval = 10 if end_time > 500 else 5
    ax.set_xticks(range(0, end_time + 1, minor_tick_interval), minor=True)
    
    # Y-axis labels
    ytick_labels = [f'Task {task_id}' for task_id in unique_tasks] + ['IDLE']
    ax.set_yticks(range(num_tasks + 1))
    ax.set_yticklabels(ytick_labels, fontsize=12)
    
    title = f"RM Schedule for Lehoczky's Counterexample (t=0 to t={end_time})"
    ax.set_title(title, fontsize=16, fontweight='bold', pad=20)
    ax.grid(True, axis='x', alpha=0.3, linestyle='--', which='major')
    ax.grid(True, axis='x', alpha=0.15, linestyle=':', which='minor')
    
    # Legend
    legend_elements = [
        mpatches.Patch(facecolor=colors[1], edgecolor='black', label='Task 1 (T=70, C=26)'),
        mpatches.Patch(facecolor=colors[2], edgecolor='black', label='Task 2 (T=100, C=62)'),
        mpatches.Patch(facecolor='#E0E0E0', edgecolor='black', label='IDLE'),
        plt.Line2D([0], [0], color='green', linestyle='-', marker='^', 
                   label='Release Time', markersize=6, linewidth=1.5, alpha=0.7),
        plt.Line2D([0], [0], color='red', linestyle='-', marker='v', 
                   label='Absolute Deadline', markersize=6, linewidth=1.5, alpha=0.7)
    ]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=11, 
             framealpha=0.9, edgecolor='black')
    
    plt.tight_layout()
    
    return fig


def main():
    print("\n" + "=" * 80)
    print("LEHOCZKY'S COUNTEREXAMPLE - RATE MONOTONIC SCHEDULING")
    print("=" * 80)
    print()
    
    # Lehoczky's counterexample: (T, C): (70, 26), (100, 62)
    tasks = [
        TaskRM(id=1, period=70, computation=26),
        TaskRM(id=2, period=100, computation=62)
    ]
    
    end_time = 700
    
    # Generate schedule
    schedule, all_jobs, completed_jobs = rate_monotonic_schedule_lehoczky(tasks, end_time)
    
    # Print detailed job information
    print_detailed_job_info(all_jobs, completed_jobs, end_time)
    
    # Print Gantt table
    print_gantt_table(schedule, tasks, end_time)
    
    # Create visualizations
    print()
    print("Generating visualizations...")
    visualize_schedule_detailed(schedule, tasks, end_time)
    plt.show()
    
    print()
    print("=" * 80)
    print("Analysis complete!")
    print("=" * 80)


if __name__ == "__main__":
    main()
