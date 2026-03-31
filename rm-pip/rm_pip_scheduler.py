"""
RM Scheduler with Priority Inheritance Protocol (PIP)
Schedules tasks with shared resource access using PIP to handle priority inversion.
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from collections import deque

class Task:
    def __init__(self, task_id, phase, period, computation_time, resource_time):
        self.task_id = task_id
        self.phase = phase
        self.period = period
        self.computation_time = computation_time
        self.resource_time = resource_time
        self.cpu_only_time = computation_time - resource_time
        self.priority = period  # RM: shorter period = higher priority (lower value)
        
    def __repr__(self):
        return f"Task{self.task_id}"

class Job:
    def __init__(self, task, arrival_time, job_number):
        self.task = task
        self.arrival_time = arrival_time
        self.deadline = arrival_time + task.period
        self.remaining_cpu_only = task.cpu_only_time
        self.remaining_resource = task.resource_time
        self.job_number = job_number
        self.holding_resource = False
        self.inherited_priority = None
        
    @property
    def effective_priority(self):
        """Return the effective priority (considering inheritance)"""
        if self.inherited_priority is not None:
            return min(self.inherited_priority, self.task.priority)
        return self.task.priority
    
    @property
    def is_complete(self):
        return self.remaining_cpu_only == 0 and self.remaining_resource == 0
    
    def __repr__(self):
        return f"Job({self.task.task_id}.{self.job_number})"

def simulate_rm_pip(tasks, end_time):
    """Simulate RM scheduling with PIP"""
    
    # Generate all jobs up to end_time
    all_jobs = []
    for task in tasks:
        job_num = 0
        t = task.phase
        while t < end_time:
            all_jobs.append((t, Job(task, t, job_num)))
            t += task.period
            job_num += 1
    
    # Sort by arrival time
    all_jobs.sort(key=lambda x: x[0])
    
    # Simulation state
    ready_queue = []
    current_job = None
    resource_holder = None
    schedule = []
    
    job_index = 0
    
    for t in range(end_time):
        # Release new jobs at this time
        while job_index < len(all_jobs) and all_jobs[job_index][0] == t:
            ready_queue.append(all_jobs[job_index][1])
            job_index += 1
        
        # Add current job back to ready queue if it exists and not complete
        if current_job and not current_job.is_complete:
            ready_queue.append(current_job)
            current_job = None
        
        # Apply PIP: Check if resource holder needs priority boost
        if resource_holder:
            resource_holder.inherited_priority = None  # Reset
            for job in ready_queue:
                # If a higher priority job is blocked waiting for the resource
                if (job.effective_priority < resource_holder.task.priority and
                    job.remaining_cpu_only == 0 and job.remaining_resource > 0):
                    # Inherit the highest priority among blocked jobs
                    if resource_holder.inherited_priority is None:
                        resource_holder.inherited_priority = job.effective_priority
                    else:
                        resource_holder.inherited_priority = min(
                            resource_holder.inherited_priority,
                            job.effective_priority
                        )
        
        # Select highest priority job from ready queue (considering effective priority)
        if ready_queue:
            ready_queue.sort(key=lambda j: j.effective_priority)
            current_job = ready_queue.pop(0)
        
        # Execute current job
        if current_job:
            exec_type = None
            
            # Determine what to execute
            if current_job.remaining_cpu_only > 0:
                # Execute CPU-only work
                current_job.remaining_cpu_only -= 1
                exec_type = 'cpu'
                
            elif current_job.remaining_resource > 0:
                # Need to use resource
                if resource_holder is None:
                    # Acquire resource
                    resource_holder = current_job
                    current_job.holding_resource = True
                
                if current_job.holding_resource:
                    # Execute with resource
                    current_job.remaining_resource -= 1
                    exec_type = 'resource'
                    
                    # Release resource if done with it
                    if current_job.remaining_resource == 0:
                        resource_holder = None
                        current_job.holding_resource = False
                        current_job.inherited_priority = None
                else:
                    # Blocked - can't acquire resource
                    # Put back in queue and find another job to run
                    ready_queue.append(current_job)
                    
                    # Find runnable job (CPU-only work or already holds resource)
                    runnable = [j for j in ready_queue 
                               if j.remaining_cpu_only > 0 or j.holding_resource]
                    
                    if runnable:
                        runnable.sort(key=lambda j: j.effective_priority)
                        current_job = runnable[0]
                        ready_queue.remove(current_job)
                        
                        # Execute the runnable job
                        if current_job.remaining_cpu_only > 0:
                            current_job.remaining_cpu_only -= 1
                            exec_type = 'cpu'
                        elif current_job.holding_resource:
                            current_job.remaining_resource -= 1
                            exec_type = 'resource'
                            if current_job.remaining_resource == 0:
                                resource_holder = None
                                current_job.holding_resource = False
                                current_job.inherited_priority = None
                    else:
                        # No runnable job - idle
                        exec_type = 'idle'
                        current_job = None
            
            # Record schedule
            if current_job and exec_type != 'idle':
                schedule.append({
                    'time': t,
                    'job': current_job,
                    'task_id': current_job.task.task_id,
                    'type': exec_type,
                    'inherited': current_job.inherited_priority is not None
                })
            else:
                schedule.append({'time': t, 'job': None, 'task_id': None, 
                               'type': 'idle', 'inherited': False})
        else:
            # Idle
            schedule.append({'time': t, 'job': None, 'task_id': None, 
                           'type': 'idle', 'inherited': False})
    
    return schedule

def draw_schedule(schedule, tasks, end_time):
    """Draw the schedule as a Gantt chart with separate rows for each task"""
    
    fig, ax = plt.subplots(figsize=(18, 8))
    
    # Colors for each task
    colors = {1: '#FF6B6B', 2: '#4ECDC4', 3: '#45B7D1'}
    resource_colors = {1: '#CC0000', 2: '#00AA99', 3: '#0088AA'}
    
    # Create mapping of task_id to row (inverted so Task 1 is on top)
    task_to_row = {1: 3, 2: 2, 3: 1}  # Higher priority tasks at top
    row_height = 0.8
    
    # Draw background for each task row
    for task_id, row in task_to_row.items():
        y_pos = row - 0.4
        ax.add_patch(mpatches.Rectangle((0, y_pos), end_time, row_height,
                                       facecolor='#f8f8f8',
                                       edgecolor='#cccccc',
                                       linewidth=1,
                                       zorder=0))
    
    # Track job executions to show when they complete
    job_executions = {}  # (task_id, job_num): [time_points]
    
    # Draw schedule - only show execution on the task's own row
    for entry in schedule:
        t = entry['time']
        task_id = entry['task_id']
        exec_type = entry['type']
        inherited = entry['inherited']
        job = entry.get('job')
        
        if exec_type != 'idle' and task_id is not None:
            row = task_to_row[task_id]
            y_pos = row - 0.4
            
            # Track this execution
            if job:
                job_key = (task_id, job.job_number)
                if job_key not in job_executions:
                    job_executions[job_key] = []
                job_executions[job_key].append(t)
            
            if exec_type == 'cpu':
                # Draw CPU-only execution
                color = colors[task_id]
                if inherited:
                    ax.add_patch(mpatches.Rectangle((t, y_pos), 1, row_height,
                                                   facecolor=color,
                                                   edgecolor='gold',
                                                   linewidth=3,
                                                   zorder=2))
                else:
                    ax.add_patch(mpatches.Rectangle((t, y_pos), 1, row_height,
                                                   facecolor=color,
                                                   edgecolor='black',
                                                   linewidth=1.5,
                                                   zorder=2))
                ax.text(t + 0.5, row, f'T{task_id}', ha='center', va='center',
                       fontsize=9, weight='bold', zorder=3)
                       
            elif exec_type == 'resource':
                # Draw resource execution with pattern
                color = resource_colors[task_id]
                if inherited:
                    ax.add_patch(mpatches.Rectangle((t, y_pos), 1, row_height,
                                                   facecolor=color,
                                                   edgecolor='gold',
                                                   linewidth=3,
                                                   hatch='///',
                                                   zorder=2))
                else:
                    ax.add_patch(mpatches.Rectangle((t, y_pos), 1, row_height,
                                                   facecolor=color,
                                                   edgecolor='black',
                                                   linewidth=1.5,
                                                   hatch='///',
                                                   zorder=2))
                ax.text(t + 0.5, row, f'T{task_id}*', ha='center', va='center',
                       fontsize=9, weight='bold', color='white', zorder=3)
            elif exec_type == 'blocked':
                # Draw blocked state
                ax.add_patch(mpatches.Rectangle((t, y_pos), 1, row_height,
                                               facecolor='#ffcccc',
                                               edgecolor='red',
                                               linewidth=1.5,
                                               alpha=0.5,
                                               zorder=2))
                ax.text(t + 0.5, row, 'B', ha='center', va='center',
                       fontsize=8, style='italic', zorder=3)
    
    # Draw releases (upward arrows) and deadlines (downward arrows) for each task
    for task in tasks:
        row = task_to_row[task.task_id]
        t = task.phase
        job_num = 0
        
        while t < end_time:
            # Release (upward arrow at bottom of task row)
            ax.annotate('', xy=(t, row - 0.4), xytext=(t, row - 0.7),
                       arrowprops=dict(arrowstyle='->', color='green', lw=2),
                       zorder=4)
            ax.text(t, row - 0.85, f'R', ha='center', fontsize=7,
                   color='green', weight='bold')
            
            # Deadline (downward arrow at top of task row)
            deadline = t + task.period
            if deadline <= end_time:
                ax.annotate('', xy=(deadline, row + 0.4), xytext=(deadline, row + 0.7),
                           arrowprops=dict(arrowstyle='->', color='red', lw=2),
                           zorder=4)
                ax.text(deadline, row + 0.85, f'D', ha='center', fontsize=7,
                       color='red', weight='bold')
            
            t += task.period
            job_num += 1
    
    # Mark job completions with a small marker
    for (task_id, job_num), times in job_executions.items():
        if times:
            completion_time = max(times) + 1  # End of last execution slot
            row = task_to_row[task_id]
            # Small completion marker
            ax.plot(completion_time, row, marker='o', color='black',
                   markersize=6, zorder=5, markerfacecolor='lime',
                   markeredgecolor='black', markeredgewidth=1.5)
    
    # Set axis properties
    ax.set_xlim(-0.5, end_time + 0.5)
    ax.set_ylim(0, 4.5)
    ax.set_xlabel('Time', fontsize=12, weight='bold')
    ax.set_ylabel('Tasks', fontsize=12, weight='bold')
    ax.set_yticks([1, 2, 3])
    ax.set_yticklabels(['Task 3\n(φ=0, T=10, C=3, δA=2)',
                        'Task 2\n(φ=2, T=8, C=2, δA=0)',
                        'Task 1\n(φ=3, T=6, C=2, δA=1)'],
                       fontsize=9)
    ax.set_xticks(range(end_time + 1))
    ax.grid(True, axis='x', alpha=0.3, linestyle='--', linewidth=0.5)
    
    # Add vertical lines at each time unit
    for t in range(end_time + 1):
        ax.axvline(x=t, color='gray', linestyle='-', linewidth=0.5, alpha=0.3, zorder=1)
    
    # Add legend
    legend_elements = [
        mpatches.Patch(facecolor=colors[1], edgecolor='black', label='CPU-only execution'),
        mpatches.Patch(facecolor=resource_colors[1], edgecolor='black', hatch='///',
                      label='Execution using Resource A'),
        mpatches.Patch(facecolor='white', edgecolor='gold', linewidth=3,
                      label='Priority Inherited'),
        mpatches.Patch(facecolor='#ffcccc', edgecolor='red', alpha=0.5, label='Blocked'),
        plt.Line2D([0], [0], marker='^', color='green', linewidth=0,
                  markerfacecolor='green', markersize=8, label='Release (↑)'),
        plt.Line2D([0], [0], marker='v', color='red', linewidth=0,
                  markerfacecolor='red', markersize=8, label='Deadline (↓)'),
        plt.Line2D([0], [0], marker='o', color='black', linewidth=0,
                  markerfacecolor='lime', markersize=8, markeredgewidth=1.5, label='Completion'),
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=9, ncol=2,
             bbox_to_anchor=(0, 1.02), framealpha=0.95)
    
    plt.title('RM Schedule with Priority Inheritance Protocol (PIP) - t=0 to t=16\n' +
             'Each task shown on separate row with releases (R/↑) and deadlines (D/↓)',
             fontsize=13, weight='bold', pad=20)
    plt.tight_layout()
    
    return fig

def print_schedule_table(schedule):
    """Print schedule in table format"""
    print("\nSchedule Trace:")
    print("-" * 80)
    print(f"{'Time':<6} {'Task':<10} {'Type':<15} {'Priority':<20}")
    print("-" * 80)
    
    for entry in schedule:
        t = entry['time']
        task_id = entry.get('task_id')
        exec_type = entry.get('type')
        
        if task_id is not None and exec_type is not None and exec_type != 'idle':
            inherited = " (INHERITED)" if entry.get('inherited', False) else ""
            
            if exec_type == 'cpu':
                type_str = "CPU-only"
            elif exec_type == 'resource':
                type_str = "Using Resource A"
            else:
                type_str = str(exec_type)
            
            print(f"{t:<6} T{task_id:<9} {type_str:<15} {inherited}")
        else:
            print(f"{t:<6} {'IDLE':<10} {'-':<15} {'-':<20}")
    print("-" * 80)

# Define the task set from the problem
tasks = [
    Task(task_id=1, phase=3, period=6, computation_time=2, resource_time=1),
    Task(task_id=2, phase=2, period=8, computation_time=2, resource_time=0),
    Task(task_id=3, phase=0, period=10, computation_time=3, resource_time=2),
]

# Simulate
end_time = 16
schedule = simulate_rm_pip(tasks, end_time)

# Print schedule
print("Task Set:")
print(f"{'Task':<6} {'φi':<6} {'Ti':<6} {'Ci':<6} {'δi,A':<8} {'Priority (RM)'}")
print("-" * 50)
for task in tasks:
    print(f"T{task.task_id:<5} {task.phase:<6} {task.period:<6} "
          f"{task.computation_time:<6} {task.resource_time:<8} "
          f"{task.priority} (rank {sorted([t.priority for t in tasks]).index(task.priority) + 1})")

print_schedule_table(schedule)

# Draw schedule
fig = draw_schedule(schedule, tasks, end_time)
plt.savefig('/Users/chrisrutherford/Downloads/Csc-358/HW/rm_pip_schedule.png', 
            dpi=300, bbox_inches='tight')
print("\nSchedule diagram saved to: rm_pip_schedule.png")
# plt.show()  # Commented out to avoid GUI hang
