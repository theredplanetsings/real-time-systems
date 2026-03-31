import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import namedtuple

# Task definition for RM: (period, computation_time)
TaskRM = namedtuple('TaskRM', ['id', 'period', 'computation'])

# Task definition for DM: (period, computation_time, deadline)
TaskDM = namedtuple('TaskDM', ['id', 'period', 'computation', 'deadline'])

# Job instance for tracking individual job releases
class Job:
    def __init__(self, task_id, release_time, remaining_time, deadline=None):
        self.task_id = task_id
        self.release_time = release_time
        self.remaining_time = remaining_time
        self.deadline = deadline
    
    def __repr__(self):
        return f"Job(T{self.task_id}, release={self.release_time}, remaining={self.remaining_time}, deadline={self.deadline})"


def rate_monotonic_schedule(tasks, end_time):
    """
    Schedule tasks using Rate Monotonic (RM) algorithm.
    Priority: Shorter period = Higher priority
    """
    print("=" * 70)
    print("RATE MONOTONIC SCHEDULING")
    print("=" * 70)
    print(f"{'Task':<8} {'Period':<10} {'Computation':<15} {'Priority':<10}")
    print("-" * 70)
    
    # Sort tasks by period (shorter period = higher priority)
    sorted_tasks = sorted(tasks, key=lambda t: t.period)
    for i, task in enumerate(sorted_tasks):
        print(f"T{task.id:<7} {task.period:<10} {task.computation:<15} {i+1} (highest)" if i == 0 
              else f"T{task.id:<7} {task.period:<10} {task.computation:<15} {i+1}")
    
    print("=" * 70)
    print()
    
    # Initialize ready queue
    ready_queue = []
    schedule = []  # (time, task_id or None)
    job_executions = []  # Track each job execution
    
    # Track next release time for each task
    next_release = {task.id: 0 for task in tasks}
    
    # Track currently executing job info
    current_execution = None
    
    # Simulate scheduling
    for t in range(end_time):
        # Release new jobs at their periods
        for task in tasks:
            if t == next_release[task.id]:
                absolute_deadline = t + task.period  # For RM, deadline = period
                ready_queue.append(Job(task.id, t, task.computation, absolute_deadline))
                next_release[task.id] += task.period
        
        # Sort ready queue by priority (period - shorter period first)
        ready_queue.sort(key=lambda job: next((task.period for task in tasks if task.id == job.task_id)))
        
        # Execute highest priority job
        if ready_queue:
            current_job = ready_queue[0]
            schedule.append((t, current_job.task_id))
            
            # Track execution start
            if current_execution is None or current_execution['task_id'] != current_job.task_id or current_execution['release'] != current_job.release_time:
                if current_execution is not None:
                    current_execution['finish'] = t - 1
                    job_executions.append(current_execution)
                
                task_info = next(task for task in tasks if task.id == current_job.task_id)
                current_execution = {
                    'task_id': current_job.task_id,
                    'start': t,
                    'release': current_job.release_time,
                    'rel_deadline': task_info.period,
                    'abs_deadline': current_job.deadline
                }
            
            current_job.remaining_time -= 1
            
            # Remove completed jobs
            if current_job.remaining_time == 0:
                current_execution['finish'] = t
                job_executions.append(current_execution)
                current_execution = None
                ready_queue.pop(0)
        else:
            if current_execution is not None:
                current_execution['finish'] = t - 1
                job_executions.append(current_execution)
                current_execution = None
            schedule.append((t, None))  # Idle
    
    # Close any pending execution
    if current_execution is not None:
        current_execution['finish'] = end_time - 1
        job_executions.append(current_execution)
    
    # Print schedule with detailed information
    print("Schedule (Each Task Execution):")
    print("=" * 95)
    print(f"{'Task':<8} {'Start':<8} {'Finish':<8} {'Release':<10} {'Rel DL':<10} {'Abs DL':<10}")
    print("-" * 95)
    for exec_info in job_executions:
        print(f"T{exec_info['task_id']:<7} {exec_info['start']:<8} {exec_info['finish']:<8} " +
              f"{exec_info['release']:<10} {exec_info['rel_deadline']:<10} {exec_info['abs_deadline']:<10}")
    print("=" * 95)
    print()
    
    return schedule


def deadline_monotonic_schedule(tasks, end_time):
    """
    Schedule tasks using Deadline Monotonic (DM) algorithm.
    Priority: Shorter deadline = Higher priority
    """
    print("=" * 70)
    print("DEADLINE MONOTONIC SCHEDULING")
    print("=" * 70)
    print(f"{'Task':<8} {'Period':<10} {'Computation':<15} {'Deadline':<12} {'Priority':<10}")
    print("-" * 70)
    
    # Sort tasks by deadline (shorter deadline = higher priority)
    sorted_tasks = sorted(tasks, key=lambda t: t.deadline)
    for i, task in enumerate(sorted_tasks):
        print(f"T{task.id:<7} {task.period:<10} {task.computation:<15} {task.deadline:<12} {i+1} (highest)" if i == 0 
              else f"T{task.id:<7} {task.period:<10} {task.computation:<15} {task.deadline:<12} {i+1}")
    
    print("=" * 70)
    print()
    
    # Initialize ready queue
    ready_queue = []
    schedule = []  # (time, task_id or None)
    job_executions = []  # Track each job execution
    
    # Track next release time for each task
    next_release = {task.id: 0 for task in tasks}
    
    # Track currently executing job info
    current_execution = None
    
    # Simulate scheduling
    for t in range(end_time):
        # Release new jobs at their periods
        for task in tasks:
            if t == next_release[task.id]:
                absolute_deadline = t + task.deadline
                ready_queue.append(Job(task.id, t, task.computation, absolute_deadline))
                next_release[task.id] += task.period
        
        # Sort ready queue by priority (deadline - shorter deadline first)
        ready_queue.sort(key=lambda job: next((task.deadline for task in tasks if task.id == job.task_id)))
        
        # Execute highest priority job
        if ready_queue:
            current_job = ready_queue[0]
            schedule.append((t, current_job.task_id))
            
            # Track execution start
            if current_execution is None or current_execution['task_id'] != current_job.task_id or current_execution['release'] != current_job.release_time:
                if current_execution is not None:
                    current_execution['finish'] = t - 1
                    job_executions.append(current_execution)
                
                task_info = next(task for task in tasks if task.id == current_job.task_id)
                current_execution = {
                    'task_id': current_job.task_id,
                    'start': t,
                    'release': current_job.release_time,
                    'rel_deadline': task_info.deadline,
                    'abs_deadline': current_job.deadline
                }
            
            current_job.remaining_time -= 1
            
            # Remove completed jobs
            if current_job.remaining_time == 0:
                current_execution['finish'] = t
                job_executions.append(current_execution)
                current_execution = None
                ready_queue.pop(0)
        else:
            if current_execution is not None:
                current_execution['finish'] = t - 1
                job_executions.append(current_execution)
                current_execution = None
            schedule.append((t, None))  # Idle
    
    # Close any pending execution
    if current_execution is not None:
        current_execution['finish'] = end_time - 1
        job_executions.append(current_execution)
    
    # Print schedule with detailed information
    print("Schedule (Each Task Execution):")
    print("=" * 95)
    print(f"{'Task':<8} {'Start':<8} {'Finish':<8} {'Release':<10} {'Rel DL':<10} {'Abs DL':<10}")
    print("-" * 95)
    for exec_info in job_executions:
        print(f"T{exec_info['task_id']:<7} {exec_info['start']:<8} {exec_info['finish']:<8} " +
              f"{exec_info['release']:<10} {exec_info['rel_deadline']:<10} {exec_info['abs_deadline']:<10}")
    print("=" * 95)
    print()
    
    return schedule


def visualize_schedule(schedule, title, end_time, tasks=None):
    """Visualize the schedule as a Gantt chart with each task on its own row"""
    # Get unique task IDs from schedule
    unique_tasks = sorted(set(task_id for _, task_id in schedule if task_id is not None))
    num_tasks = len(unique_tasks)
    
    fig, ax = plt.subplots(figsize=(16, 2 + num_tasks * 1.2))
    
    # Color map for tasks
    colors = {1: 'red', 2: 'blue', 3: 'green', 4: 'orange', 5: 'purple'}
    
    # Track job executions for annotation
    job_info = {}  # key: (task_id, release_time), value: {'start': ..., 'finish': ..., 'release': ..., etc.}
    
    # Build job execution info from schedule
    current_job = {}  # track ongoing jobs per task
    for t, task_id in schedule:
        if task_id is not None:
            if task_id not in current_job:
                # New job starting
                if tasks:
                    # Get task info to calculate deadlines
                    task_info = next((task for task in tasks if task.id == task_id), None)
                    if hasattr(task_info, 'deadline'):
                        rel_dl = task_info.deadline
                    else:
                        rel_dl = task_info.period if task_info else 0
                    
                    # Find release time (look backwards for last release)
                    release = t
                    for prev_t in range(t, -1, -1):
                        if task_info and prev_t % task_info.period == 0:
                            release = prev_t
                            break
                    
                    abs_dl = release + rel_dl
                else:
                    release = t
                    rel_dl = 0
                    abs_dl = 0
                
                current_job[task_id] = {
                    'start': t,
                    'release': release,
                    'rel_dl': rel_dl,
                    'abs_dl': abs_dl
                }
            current_job[task_id]['finish'] = t
        
        # Check if job finished (next time unit has different task or is idle)
        if t < len(schedule) - 1:
            next_task = schedule[t + 1][1]
            if next_task != task_id and task_id is not None and task_id in current_job:
                # Job finished, store it
                job_key = (task_id, current_job[task_id]['release'])
                job_info[job_key] = current_job[task_id].copy()
                del current_job[task_id]
    
    # Store any remaining jobs
    for task_id, info in current_job.items():
        job_key = (task_id, info['release'])
        job_info[job_key] = info
    
    # Draw schedule - each task gets its own row
    for t, task_id in schedule:
        if task_id is not None:
            # Map task_id to row (0 = bottom task)
            row = unique_tasks.index(task_id)
            ax.barh(row, 1, left=t, height=0.7, color=colors.get(task_id, 'gray'), 
                   edgecolor='black', linewidth=0.5)
            ax.text(t + 0.5, row, f'T{task_id}', ha='center', va='center', 
                   fontsize=8, fontweight='bold')
    
    # Add release times and deadlines as vertical markers
    if tasks:
        for task in tasks:
            row = unique_tasks.index(task.id)
            # Add release markers (arrows pointing up)
            for release_t in range(0, end_time, task.period):
                ax.plot([release_t, release_t], [row - 0.4, row + 0.4], 
                       'g--', linewidth=1.5, alpha=0.7)
                ax.plot(release_t, row - 0.4, 'g^', markersize=8, alpha=0.7)
            
            # Add deadline markers
            if hasattr(task, 'deadline'):
                rel_dl = task.deadline
            else:
                rel_dl = task.period
            
            for release_t in range(0, end_time, task.period):
                deadline_t = release_t + rel_dl
                if deadline_t <= end_time:
                    ax.plot([deadline_t, deadline_t], [row - 0.4, row + 0.4], 
                           'r--', linewidth=1.5, alpha=0.7)
                    ax.plot(deadline_t, row + 0.4, 'rv', markersize=8, alpha=0.7)
    
    # Formatting
    ax.set_xlim(0, end_time)
    ax.set_ylim(-0.5, num_tasks - 0.5)
    ax.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax.set_ylabel('Tasks', fontsize=12, fontweight='bold')
    ax.set_xticks(range(0, end_time + 1, 1))  # Set x-axis ticks in increments of 1
    ax.set_yticks(range(num_tasks))
    ax.set_yticklabels([f'T{task_id}' for task_id in unique_tasks])
    ax.set_title(title, fontsize=14, fontweight='bold')
    ax.grid(True, axis='x', alpha=0.3)
    ax.invert_yaxis()  # Task 1 at top
    
    # Legend
    legend_elements = [
        mpatches.Patch(color=colors[i], label=f'Task {i}') 
        for i in unique_tasks
    ]
    legend_elements.extend([
        plt.Line2D([0], [0], color='green', linestyle='--', marker='^', 
                   label='Release', markersize=8, alpha=0.7),
        plt.Line2D([0], [0], color='red', linestyle='--', marker='v', 
                   label='Deadline', markersize=8, alpha=0.7)
    ])
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    plt.tight_layout()
    return fig


def main():
    print("\n" + "=" * 70)
    print("REAL-TIME TASK SCHEDULING SIMULATOR")
    print("=" * 70)
    print()
    
    # ==================== RATE MONOTONIC SCHEDULING ====================
    print("\n" + "#" * 70)
    print("# PROBLEM 1: Rate Monotonic Scheduling")
    print("#" * 70)
    print()
    
    # Task set 1: (T,C) = {(7,2), (5,1), (12,5)}
    rm_tasks = [
        TaskRM(id=1, period=7, computation=2),
        TaskRM(id=2, period=5, computation=1),
        TaskRM(id=3, period=12, computation=5)
    ]
    
    print("Task Set: (T,C) = {(7,2), (5,1), (12,5)}")
    print()
    
    rm_schedule = rate_monotonic_schedule(rm_tasks, end_time=20)
    rm_fig = visualize_schedule(rm_schedule, 'Rate Monotonic Schedule (t=0 to t=20)', 20, rm_tasks)
    
    # ==================== DEADLINE MONOTONIC SCHEDULING ====================
    print("\n" + "#" * 70)
    print("# PROBLEM 2: Deadline Monotonic Scheduling")
    print("#" * 70)
    print()
    
    # Task set 2: (T,C,D) = {(11,2,11), (7,2,6), (12,1,9), (8,2,8)}
    dm_tasks = [
        TaskDM(id=1, period=11, computation=2, deadline=11),
        TaskDM(id=2, period=7, computation=2, deadline=6),
        TaskDM(id=3, period=12, computation=1, deadline=9),
        TaskDM(id=4, period=8, computation=2, deadline=8)
    ]
    
    print("Task Set: (T,C,D) = {(11,2,11), (7,2,6), (12,1,9), (8,2,8)}")
    print()
    
    dm_schedule = deadline_monotonic_schedule(dm_tasks, end_time=28)
    dm_fig = visualize_schedule(dm_schedule, 'Deadline Monotonic Schedule (t=0 to t=28)', 28, dm_tasks)
    
    # Show both plots
    plt.show()


if __name__ == "__main__":
    main()
