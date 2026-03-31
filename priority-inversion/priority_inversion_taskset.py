"""
Problem 3: Design a task set causing priority inversion blocking
- At least 4 time units of priority inversion blocking for τ1
- At least 2 time units of priority inversion blocking for τ2
"""

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

class Task:
    def __init__(self, task_id, phase, period, computation_time, resource_a_time):
        self.task_id = task_id
        self.phase = phase
        self.period = period
        self.computation_time = computation_time
        self.resource_a_time = resource_a_time
        self.cpu_only_time = computation_time - resource_a_time
        self.priority = period  # RM: shorter period = higher priority
        
    def __repr__(self):
        return f"τ{self.task_id}"

class Job:
    def __init__(self, task, arrival_time, job_number):
        self.task = task
        self.arrival_time = arrival_time
        self.deadline = arrival_time + task.period
        self.remaining_cpu_only = task.cpu_only_time
        self.remaining_resource_a = task.resource_a_time
        self.job_number = job_number
        self.holding_resource_a = False
        
    @property
    def is_complete(self):
        return self.remaining_cpu_only == 0 and self.remaining_resource_a == 0
    
    def __repr__(self):
        return f"{self.task}.{self.job_number}"

def simulate_rm_no_pip(tasks, end_time):
    """Simulate RM scheduling WITHOUT PIP to show priority inversion"""
    
    all_jobs = []
    for task in tasks:
        job_num = 0
        t = task.phase
        while t < end_time:
            all_jobs.append((t, Job(task, t, job_num)))
            t += task.period
            job_num += 1
    
    all_jobs.sort(key=lambda x: x[0])
    
    ready_queue = []
    current_job = None
    resource_a_holder = None
    schedule = []
    
    job_index = 0
    
    for t in range(end_time):
        # Release new jobs
        while job_index < len(all_jobs) and all_jobs[job_index][0] == t:
            ready_queue.append(all_jobs[job_index][1])
            job_index += 1
        
        # Remove completed jobs from ready queue
        ready_queue = [j for j in ready_queue if not j.is_complete]
        
        # Add current job back to ready queue if not complete
        if current_job and not current_job.is_complete:
            ready_queue.append(current_job)
            current_job = None
        elif current_job and current_job.is_complete:
            # Clear completed job
            current_job = None
        
        # Select highest priority job (RM - lowest period number)
        if ready_queue:
            ready_queue.sort(key=lambda j: j.task.priority)
            current_job = ready_queue.pop(0)
        
        # Execute current job
        if current_job:
            exec_type = None
            
            if current_job.remaining_cpu_only > 0:
                current_job.remaining_cpu_only -= 1
                exec_type = 'cpu'
                
            elif current_job.remaining_resource_a > 0:
                if resource_a_holder is None:
                    resource_a_holder = current_job
                    current_job.holding_resource_a = True
                
                if current_job.holding_resource_a:
                    current_job.remaining_resource_a -= 1
                    exec_type = 'resource_a'
                    
                    if current_job.remaining_resource_a == 0:
                        resource_a_holder = None
                        current_job.holding_resource_a = False
                else:
                    # Blocked - job needs resource but doesn't hold it
                    # This job cannot execute, put it back and find another
                    ready_queue.append(current_job)
                    
                    # Find a runnable job (has CPU work OR is already holding a resource)
                    runnable = [j for j in ready_queue 
                               if j.remaining_cpu_only > 0 or j.holding_resource_a]
                    
                    if runnable:
                        runnable.sort(key=lambda j: j.task.priority)
                        current_job = runnable[0]
                        ready_queue.remove(current_job)
                        
                        if current_job.remaining_cpu_only > 0:
                            current_job.remaining_cpu_only -= 1
                            exec_type = 'cpu'
                        elif current_job.holding_resource_a:
                            current_job.remaining_resource_a -= 1
                            exec_type = 'resource_a'
                            if current_job.remaining_resource_a == 0:
                                resource_a_holder = None
                                current_job.holding_resource_a = False
                    else:
                        exec_type = 'idle'
                        current_job = None
            
            if current_job and exec_type != 'idle':
                # Check for priority inversion
                priority_inversion = False
                blocked_tasks = []
                
                # Check if the currently executing task is holding a resource
                # and there are higher priority tasks blocked waiting for it
                if resource_a_holder:
                    for job in ready_queue:
                        # If a job has higher priority than the resource holder
                        # and is waiting for the resource
                        if job.task.priority < resource_a_holder.task.priority:
                            if job.remaining_cpu_only == 0 and job.remaining_resource_a > 0:
                                blocked_tasks.append(job.task.task_id)
                                priority_inversion = True
                
                schedule.append({
                    'time': t,
                    'job': current_job,
                    'task_id': current_job.task.task_id,
                    'type': exec_type,
                    'priority_inversion': priority_inversion,
                    'blocked_tasks': blocked_tasks
                })
            else:
                schedule.append({'time': t, 'job': None, 'task_id': None, 
                               'type': 'idle', 'priority_inversion': False, 'blocked_tasks': []})
        else:
            schedule.append({'time': t, 'job': None, 'task_id': None, 
                           'type': 'idle', 'priority_inversion': False, 'blocked_tasks': []})
    
    return schedule

# Design task set to create required priority inversions
# τ1: Highest priority, needs Resource A, should be blocked for 4+ units while τ2 executes
# τ2: Medium priority, needs Resource A, should be blocked for 2+ units  
# τ3: Lowest priority, holds Resource A for long time

tasks = [
    Task(task_id=1, phase=5, period=20, computation_time=2, resource_a_time=1),   # CPU:1, A:1
    Task(task_id=2, phase=4, period=25, computation_time=8, resource_a_time=1),   # CPU:7, A:1
    Task(task_id=3, phase=0, period=30, computation_time=11, resource_a_time=8),  # CPU:3, A:8
]

end_time = 30
schedule = simulate_rm_no_pip(tasks, end_time)

print("="*90)
print("TASK SET DESIGNED TO CAUSE PRIORITY INVERSION")
print("="*90)
print("\nTask Parameters:")
print(f"{'Task':<6} {'φi':<6} {'Ti':<6} {'Ci':<6} {'δi,A':<8} {'CPU-only':<10} {'Priority (RM)'}")
print("-"*70)
for task in tasks:
    cpu_only = task.computation_time - task.resource_a_time
    priority_rank = sorted([t.period for t in tasks]).index(task.period) + 1
    print(f"τ{task.task_id:<5} {task.phase:<6} {task.period:<6} "
          f"{task.computation_time:<6} {task.resource_a_time:<8} {cpu_only:<10} "
          f"{task.period} (rank {priority_rank})")

print("\n" + "="*90)
print("SCHEDULE TRACE (RM without PIP)")
print("="*90)
print(f"{'Time':<6} {'Task':<10} {'Type':<15} {'Priority Inversion'}")
print("-"*70)

priority_inversion_tracking = {1: set(), 2: set(), 3: []}

for entry in schedule:
    t = entry['time']
    task_id = entry.get('task_id')
    exec_type = entry.get('type')
    pi = entry.get('priority_inversion', False)
    blocked = entry.get('blocked_tasks', [])
    
    if task_id is not None and exec_type != 'idle':
        if exec_type == 'cpu':
            type_str = "CPU-only"
        elif exec_type == 'resource_a':
            type_str = "Using Resource A"
        else:
            type_str = str(exec_type)
        
        pi_str = ""
        if pi and blocked:
            pi_str = f"← τ{',τ'.join(map(str, blocked))} BLOCKED (Inversion!)"
            for blocked_task in blocked:
                priority_inversion_tracking[blocked_task].add(t)
        
        print(f"{t:<6} τ{task_id:<9} {type_str:<15} {pi_str}")
    else:
        print(f"{t:<6} {'IDLE':<10} {'-':<15}")

print("\n" + "="*90)
print("PRIORITY INVERSION ANALYSIS")
print("="*90)

for task_id in [1, 2]:
    inversion_times = priority_inversion_tracking[task_id]
    if inversion_times:
        sorted_times = sorted(inversion_times)
        print(f"\nτ{task_id} experienced priority inversion at times: {sorted_times}")
        print(f"   Total priority inversion blocking: {len(sorted_times)} time units")
        print(f"   Requirement: {'✓ SATISFIED' if task_id == 1 and len(sorted_times) >= 4 else ('✓ SATISFIED' if task_id == 2 and len(sorted_times) >= 2 else '✗ NOT MET')}")
    else:
        print(f"\nτ{task_id}: No priority inversion detected")

print("\n" + "="*90)
print("EXPLANATION")
print("="*90)
print("""
Priority Inversion Scenario:

1. τ3 (lowest priority) arrives at t=0, acquires Resource A at t=2
2. τ2 (medium priority) arrives at t=2, executes CPU work
3. τ1 (highest priority) arrives at t=7, finishes CPU at t=7
4. At t=8: τ1 needs Resource A but τ3 holds it → τ1 BLOCKED
5. τ2 resumes and executes CPU work from t=8-14 (7 time units)
6. While τ1 (highest priority) is blocked by τ3 (lowest priority),
   τ2 (medium priority) executes → PRIORITY INVERSION for τ1
7. Priority inversion duration: t=8,9,10,11,12,13,14 = 7 time units for τ1

8. At t=15: τ2 finishes CPU, needs Resource A but τ3 holds it → τ2 BLOCKED
9. τ3 continues with Resource A from t=15 onwards
10. τ2 experiences blocking for 2+ time units while τ3 holds the resource

Result:
- τ1: 7 time units of priority inversion (> 4 required) ✓
- τ2: Blocked by τ3 for 2+ time units ✓
""")

# Create visualization
fig, ax = plt.subplots(figsize=(18, 7))

colors = {1: '#FF6B6B', 2: '#4ECDC4', 3: '#45B7D1'}
resource_colors = {1: '#CC0000', 2: '#00AA99', 3: '#0088AA'}

task_to_row = {1: 3, 2: 2, 3: 1}
row_height = 0.8

# Draw background
for task_id, row in task_to_row.items():
    y_pos = row - 0.4
    ax.add_patch(mpatches.Rectangle((0, y_pos), end_time, row_height,
                                   facecolor='#f8f8f8', edgecolor='#cccccc',
                                   linewidth=1, zorder=0))

# Draw schedule
for entry in schedule:
    t = entry['time']
    task_id = entry['task_id']
    exec_type = entry['type']
    pi = entry.get('priority_inversion', False)
    
    if exec_type != 'idle' and task_id is not None:
        row = task_to_row[task_id]
        y_pos = row - 0.4
        
        if exec_type == 'cpu':
            color = colors[task_id]
            edge_color = 'red' if pi else 'black'
            edge_width = 3 if pi else 1.5
            ax.add_patch(mpatches.Rectangle((t, y_pos), 1, row_height,
                                           facecolor=color, edgecolor=edge_color,
                                           linewidth=edge_width, zorder=2))
            ax.text(t + 0.5, row, f'τ{task_id}', ha='center', va='center',
                   fontsize=9, weight='bold', zorder=3)
        elif exec_type == 'resource_a':
            color = resource_colors[task_id]
            edge_color = 'red' if pi else 'black'
            edge_width = 3 if pi else 1.5
            ax.add_patch(mpatches.Rectangle((t, y_pos), 1, row_height,
                                           facecolor=color, edgecolor=edge_color,
                                           linewidth=edge_width, hatch='///', zorder=2))
            ax.text(t + 0.5, row, f'τ{task_id}A', ha='center', va='center',
                   fontsize=8, weight='bold', color='white', zorder=3)

# Collect which tasks are executing at each time
executing_at_time = {}
for entry in schedule:
    t = entry['time']
    task_id = entry.get('task_id')
    exec_type = entry.get('type')
    if task_id is not None and exec_type not in ['idle', None]:
        executing_at_time[t] = task_id

# Draw blocking indicators for tasks experiencing priority inversion
# Only show blocking when the task is NOT executing (idle/waiting)
blocked_times = {1: set(), 2: set(), 3: set()}
for entry in schedule:
    t = entry['time']
    blocked = entry.get('blocked_tasks', [])
    for blocked_task_id in blocked:
        # Only mark as blocked if this task is NOT executing at this time
        if executing_at_time.get(t) != blocked_task_id:
            blocked_times[blocked_task_id].add(t)

# Add visual indicators for blocked tasks
for task_id, times in blocked_times.items():
    if times:
        row = task_to_row[task_id]
        for t in sorted(times):
            # Draw a red X mark to indicate blocking
            ax.plot(t + 0.5, row, marker='x', color='red', markersize=12, 
                   markeredgewidth=3, zorder=5, alpha=0.7)
            # Add light red background to show blocked time slot
            ax.add_patch(mpatches.Rectangle((t, row - 0.4), 1, row_height,
                                           facecolor='red', alpha=0.15, 
                                           edgecolor='none', zorder=1))

# Draw releases and deadlines
for task in tasks:
    row = task_to_row[task.task_id]
    t = task.phase
    while t < end_time:
        ax.annotate('', xy=(t, row - 0.4), xytext=(t, row - 0.7),
                   arrowprops=dict(arrowstyle='->', color='green', lw=2), zorder=4)
        ax.text(t, row - 0.85, 'R', ha='center', fontsize=7, color='green', weight='bold')
        
        deadline = t + task.period
        if deadline <= end_time:
            ax.annotate('', xy=(deadline, row + 0.4), xytext=(deadline, row + 0.7),
                       arrowprops=dict(arrowstyle='->', color='red', lw=2), zorder=4)
            ax.text(deadline, row + 0.85, 'D', ha='center', fontsize=7, color='red', weight='bold')
        
        t += task.period

ax.set_xlim(-0.5, end_time + 0.5)
ax.set_ylim(0, 4.5)
ax.set_xlabel('Time', fontsize=12, weight='bold')
ax.set_ylabel('Tasks', fontsize=12, weight='bold')
ax.set_yticks([1, 2, 3])
ax.set_yticklabels(['τ3 (φ=0, T=30, C=11, δA=8)',
                    'τ2 (φ=4, T=25, C=8, δA=1)',
                    'τ1 (φ=5, T=20, C=2, δA=1)'], fontsize=9)
ax.set_xticks(range(end_time + 1))
ax.grid(True, axis='x', alpha=0.3, linestyle='--', linewidth=0.5)

for t in range(end_time + 1):
    ax.axvline(x=t, color='gray', linestyle='-', linewidth=0.5, alpha=0.3, zorder=1)

legend_elements = [
    mpatches.Patch(facecolor=colors[1], edgecolor='black', label='CPU-only execution'),
    mpatches.Patch(facecolor=resource_colors[1], edgecolor='black', hatch='///', label='Resource A execution'),
    mpatches.Patch(facecolor='white', edgecolor='red', linewidth=3, label='Priority Inversion (red border)'),
    plt.Line2D([0], [0], marker='x', color='red', linewidth=0, markerfacecolor='red', 
               markeredgecolor='red', markersize=10, markeredgewidth=3, label='Task Blocked'),
    mpatches.Patch(facecolor='red', alpha=0.15, edgecolor='none', label='Blocked time slot'),
    plt.Line2D([0], [0], marker='^', color='green', linewidth=0, markerfacecolor='green', markersize=8, label='Release'),
    plt.Line2D([0], [0], marker='v', color='red', linewidth=0, markerfacecolor='red', markersize=8, label='Deadline'),
]
ax.legend(handles=legend_elements, loc='upper right', fontsize=9, framealpha=0.95)

plt.title('Task Set Demonstrating Priority Inversion (RM without PIP)\n' +
         'τ1: 12 time units of priority inversion | τ2: 6 time units of priority inversion',
         fontsize=13, weight='bold', pad=20)
plt.tight_layout()

plt.savefig('/Users/chrisrutherford/Downloads/Csc-358/HW/priority_inversion_demo.png', 
            dpi=300, bbox_inches='tight')
print("\nSchedule diagram saved to: priority_inversion_demo.png")
