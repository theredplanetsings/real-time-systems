import math
from math import gcd
from functools import reduce
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

# Task set: (Period, Computation Time)
tasks = [
    (6, 1),   # Task 1
    (10, 3),  # Task 2
    (12, 2),  # Task 3
    (15, 5)   # Task 4
]

print("=" * 80)
print("CYCLIC EXECUTIVE SCHEDULING")
print("=" * 80)
print("\nTask Set:")
for i, (T, C) in enumerate(tasks, 1):
    print(f"  Task {i}: (T={T:2d}, C={C})")
print()

# Part a: Calculate Hyperperiod (LCM of all periods)
def lcm(a, b):
    return abs(a * b) // gcd(a, b)

periods = [T for T, C in tasks]
hyperperiod = reduce(lcm, periods)

print("=" * 80)
print("PART A: HYPERPERIOD")
print("=" * 80)
print(f"\nPeriods: {periods}")
print(f"Hyperperiod H = LCM({', '.join(map(str, periods))}) = {hyperperiod}")
print()

# Calculate LCM step by step for clarity
print("Step-by-step calculation:")
print(f"  LCM(6, 10) = {lcm(6, 10)}")
print(f"  LCM(30, 12) = {lcm(lcm(6, 10), 12)}")
print(f"  LCM(60, 15) = {hyperperiod}")
print()

# Part b: Find valid frame sizes and choose one
print("=" * 80)
print("PART B: FRAME SIZE SELECTION")
print("=" * 80)
print("\nFrame Size Conditions:")
print("  1. f ≥ C_max (frame must accommodate largest task)")
print("  2. f divides H evenly (frames fit into hyperperiod)")
print("  3. 2f - gcd(T_i, f) ≤ T_i for all tasks (timing constraint)")
print()

# Condition 1: f >= C_max
C_max = max(C for T, C in tasks)
print(f"Condition 1: f ≥ C_max = {C_max}")
print()

# Condition 2: Find all divisors of hyperperiod
print(f"Condition 2: f must divide H = {hyperperiod}")
divisors = []
for i in range(1, hyperperiod + 1):
    if hyperperiod % i == 0:
        divisors.append(i)
print(f"Divisors of {hyperperiod}: {divisors}")
print()

# Filter divisors that satisfy condition 1
candidate_frames = [f for f in divisors if f >= C_max]
print(f"Divisors ≥ {C_max}: {candidate_frames}")
print()

# Condition 3: Check timing constraint for each candidate
print("Condition 3: Checking 2f - gcd(T_i, f) ≤ T_i for all tasks")
print("-" * 80)

valid_frames = []

for f in candidate_frames:
    print(f"\nTesting f = {f}:")
    all_satisfied = True
    
    for i, (T, C) in enumerate(tasks, 1):
        g = gcd(T, f)
        left_side = 2 * f - g
        satisfied = left_side <= T
        
        status = "✓" if satisfied else "✗"
        print(f"  Task {i} (T={T:2d}): 2({f}) - gcd({T:2d},{f}) = {2*f:2d} - {g:2d} = {left_side:2d} ≤ {T:2d}  {status}")
        
        if not satisfied:
            all_satisfied = False
    
    if all_satisfied:
        valid_frames.append(f)
        print(f"  → f = {f} is VALID ✓")
    else:
        print(f"  → f = {f} is INVALID ✗")

print()
print(f"Valid frame sizes: {valid_frames}")

# Choose the smallest valid frame size
chosen_frame = valid_frames[0] if valid_frames else None
print(f"\nChosen frame size: f = {chosen_frame}")
print(f"Number of frames in hyperperiod: {hyperperiod // chosen_frame}")
print()

# Part c: Create cyclic executive schedule
print("=" * 80)
print("PART C: CYCLIC EXECUTIVE SCHEDULE")
print("=" * 80)
print()

if chosen_frame:
    num_frames = hyperperiod // chosen_frame
    
    # Calculate all job instances in the hyperperiod
    print("Job Instances in Hyperperiod:")
    print("-" * 80)
    
    all_jobs = []
    for task_id, (T, C) in enumerate(tasks, 1):
        num_jobs = hyperperiod // T
        print(f"\nTask {task_id} (T={T}, C={C}): {num_jobs} jobs")
        for job_num in range(num_jobs):
            release_time = job_num * T
            deadline = release_time + T
            all_jobs.append({
                'task_id': task_id,
                'job_num': job_num + 1,
                'release': release_time,
                'deadline': deadline,
                'computation': C,
                'period': T
            })
            print(f"  Job {task_id}.{job_num + 1}: Release={release_time:2d}, Deadline={deadline:2d}, C={C}")
    
    print()
    print("=" * 80)
    print("FRAME ALLOCATION")
    print("=" * 80)
    print()
    
    # Create frames
    frames = []
    for frame_num in range(num_frames):
        frame_start = frame_num * chosen_frame
        frame_end = frame_start + chosen_frame
        frames.append({
            'num': frame_num + 1,
            'start': frame_start,
            'end': frame_end,
            'jobs': [],
            'utilization': 0
        })
    
    # Sort jobs by release time, then by deadline
    all_jobs.sort(key=lambda x: (x['release'], x['deadline']))
    
    # Allocate jobs to frames
    # A job can be added to a frame if:
    # 1. Frame begins at or after job's release time
    # 2. Job's deadline is at the end of the frame or later
    
    scheduled_jobs = set()
    
    for job in all_jobs:
        job_id = f"{job['task_id']}.{job['job_num']}"
        
        # Find eligible frames for this job
        for frame in frames:
            # Check constraints
            if frame['start'] >= job['release'] and frame['end'] <= job['deadline']:
                # Check if there's enough capacity
                if frame['utilization'] + job['computation'] <= chosen_frame:
                    frame['jobs'].append(job)
                    frame['utilization'] += job['computation']
                    scheduled_jobs.add(job_id)
                    break
    
    # Display the schedule
    print("Schedule (Frame-by-Frame):")
    print("-" * 80)
    
    for frame in frames:
        print(f"\nFrame {frame['num']:2d} [t={frame['start']:2d} to t={frame['end']:2d}]:")
        if frame['jobs']:
            for job in frame['jobs']:
                print(f"  Task {job['task_id']}.{job['job_num']} (C={job['computation']}, "
                      f"Release={job['release']:2d}, Deadline={job['deadline']:2d})")
            print(f"  Total utilization: {frame['utilization']}/{chosen_frame}")
        else:
            print(f"  IDLE")
    
    print()
    print("=" * 80)
    print("SCHEDULE VISUALIZATION")
    print("=" * 80)
    print()
    
    # Create a timeline visualization
    timeline = ['.'] * hyperperiod
    task_symbols = ['1', '2', '3', '4']
    
    for frame in frames:
        time = frame['start']
        for job in frame['jobs']:
            symbol = str(job['task_id'])
            for _ in range(job['computation']):
                if time < hyperperiod:
                    timeline[time] = symbol
                    time += 1
    
    # Print timeline in chunks
    chunk_size = 30
    for i in range(0, hyperperiod, chunk_size):
        chunk = timeline[i:i+chunk_size]
        print(f"t={i:2d}-{min(i+chunk_size-1, hyperperiod-1):2d}: {''.join(chunk)}")
    
    print()
    print("Legend: 1=Task 1, 2=Task 2, 3=Task 3, 4=Task 4, .=Idle")
    print()
    
    # Verification
    print("=" * 80)
    print("VERIFICATION")
    print("=" * 80)
    print()
    
    total_computation = sum(job['computation'] for frame in frames for job in frame['jobs'])
    total_required = sum(C * (hyperperiod // T) for T, C in tasks)
    
    print(f"Total computation scheduled: {total_computation}")
    print(f"Total computation required: {total_required}")
    print(f"All jobs scheduled: {'Yes ✓' if total_computation == total_required else 'No ✗'}")
    print()
    
    # Check utilization
    utilization = sum(C / T for T, C in tasks)
    print(f"System utilization: {utilization:.3f} = {utilization*100:.1f}%")
    print(f"Schedulable: {'Yes ✓' if utilization <= 1.0 else 'No ✗'}")
    print()
    
    # Create detailed job table
    print("=" * 80)
    print("DETAILED JOB TABLE")
    print("=" * 80)
    print()
    print(f"{'Task(i)':<15} {'Release time(i)':<20} {'deadline(i)':<15}")
    print("-" * 80)
    
    # Sort all jobs for the table
    all_jobs_sorted = sorted(all_jobs, key=lambda x: (x['release'], x['task_id']))
    
    for job in all_jobs_sorted:
        task_label = f"Task {job['task_id']}.{job['job_num']}"
        print(f"{task_label:<15} {job['release']:<20} {job['deadline']:<15}")
    
    print()
    
    # Create visual graph
    print("=" * 80)
    print("CREATING VISUAL SCHEDULE GRAPH...")
    print("=" * 80)
    
    fig, ax = plt.subplots(figsize=(16, 6))
    
    # Task colors
    task_colors = {
        1: '#FF6B6B',  # Red
        2: '#4ECDC4',  # Teal
        3: '#45B7D1',  # Blue
        4: '#FFA07A'   # Orange
    }
    
    # Draw the schedule
    y_position = 0.5
    bar_height = 0.3
    
    # Track current time for each frame
    for frame in frames:
        current_time = frame['start']
        
        for job in frame['jobs']:
            # Draw task execution block
            rect = mpatches.Rectangle(
                (current_time, y_position - bar_height/2),
                job['computation'],
                bar_height,
                facecolor=task_colors[job['task_id']],
                edgecolor='black',
                linewidth=1.5
            )
            ax.add_patch(rect)
            
            # Add task label
            label_x = current_time + job['computation'] / 2
            ax.text(label_x, y_position, f"T{job['task_id']}.{job['job_num']}", 
                   ha='center', va='center', fontsize=8, fontweight='bold')
            
            current_time += job['computation']
    
    # Draw frame boundaries
    for i in range(num_frames + 1):
        frame_time = i * chosen_frame
        ax.axvline(x=frame_time, color='black', linewidth=2, linestyle='-')
        
        # Add frame labels
        if i < num_frames:
            ax.text(frame_time + chosen_frame/2, y_position + 0.35, 
                   f"Frame {i+1}", ha='center', va='bottom', 
                   fontsize=9, fontweight='bold', color='darkblue')
    
    # Draw release times and deadlines for each task (arrows below timeline)
    arrow_y_positions = {1: -0.3, 2: -0.5, 3: -0.7, 4: -0.9}
    
    for task_id in range(1, 5):
        task_jobs = [j for j in all_jobs if j['task_id'] == task_id]
        y_arrow = arrow_y_positions[task_id]
        
        for job in task_jobs:
            # Release time arrow (upward)
            ax.arrow(job['release'], y_arrow, 0, 0.05, 
                    head_width=0.8, head_length=0.03, 
                    fc=task_colors[task_id], ec=task_colors[task_id], alpha=0.6)
            
            # Deadline arrow (downward)
            ax.arrow(job['deadline'], y_arrow, 0, 0.05, 
                    head_width=0.8, head_length=0.03, 
                    fc=task_colors[task_id], ec=task_colors[task_id], 
                    alpha=0.3, linestyle='--')
    
    # Add legend for release/deadline arrows
    ax.text(-3, -0.3, "T1", fontsize=8, fontweight='bold', color=task_colors[1])
    ax.text(-3, -0.5, "T2", fontsize=8, fontweight='bold', color=task_colors[2])
    ax.text(-3, -0.7, "T3", fontsize=8, fontweight='bold', color=task_colors[3])
    ax.text(-3, -0.9, "T4", fontsize=8, fontweight='bold', color=task_colors[4])
    
    # Set axis properties
    ax.set_xlim(-4, hyperperiod + 2)
    ax.set_ylim(-1.2, 1.2)
    ax.set_xlabel('Time', fontsize=12, fontweight='bold')
    ax.set_ylabel('')
    ax.set_title('Cyclic Executive Schedule\n(Arrows below: Solid=Release, Dashed=Deadline)', 
                fontsize=14, fontweight='bold', pad=20)
    
    # Set x-axis ticks at every time unit
    ax.set_xticks(range(0, hyperperiod + 1, 6))
    ax.set_xticks(range(0, hyperperiod + 1, 1), minor=True)
    ax.grid(True, which='major', axis='x', alpha=0.5, linewidth=1)
    ax.grid(True, which='minor', axis='x', alpha=0.2, linewidth=0.5)
    
    # Remove y-axis
    ax.set_yticks([])
    ax.spines['left'].set_visible(False)
    ax.spines['right'].set_visible(False)
    ax.spines['top'].set_visible(False)
    
    # Add legend for tasks
    legend_elements = [mpatches.Patch(facecolor=task_colors[i], edgecolor='black', 
                                     label=f'Task {i} (T={tasks[i-1][0]}, C={tasks[i-1][1]})') 
                      for i in range(1, 5)]
    ax.legend(handles=legend_elements, loc='upper right', fontsize=9)
    
    # Add frame size info
    ax.text(hyperperiod/2, -1.1, f'Frame Size: {chosen_frame}  |  Hyperperiod: {hyperperiod}', 
           ha='center', fontsize=10, fontweight='bold', 
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('/Users/chrisrutherford/Downloads/Csc-358/HW/cyclic_executive_schedule_graph.png', 
               dpi=300, bbox_inches='tight')
    print("Graph saved as 'cyclic_executive_schedule_graph.png'")
    plt.show()

print()
print("=" * 80)
