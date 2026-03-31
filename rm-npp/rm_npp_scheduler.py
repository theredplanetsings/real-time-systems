import matplotlib.pyplot as plt
import matplotlib.patches as patches
from matplotlib.patches import FancyBboxPatch
import numpy as np

def simulate_rm_npp_schedule():
    """
    Simulate RM scheduling with Non-Preemptive Protocol (NPP)
    Task set: τ1(T=5, C=2, δ=1), τ2(T=7, C=4, δ=3)
    where T=period, C=total computation time, δ=resource A usage time
    
    Execution model (PART C): Resource A work first, then CPU-only work
    τ1: 1 unit CPU+RA, then 1 unit CPU-only
    τ2: 3 units CPU+RA, then 1 unit CPU-only
    
    Under NPP: When a task holds a resource, it cannot be preempted until completion
    """
    
    # Task parameters
    tasks = {
        1: {'period': 5, 'computation': 2, 'resource_time': 1, 'priority': 1},  # Higher priority (smaller period)
        2: {'period': 7, 'computation': 4, 'resource_time': 3, 'priority': 2}   # Lower priority
    }
    
    # Calculate blocking times
    # Under NPP: B_i = max{C_j | priority(j) < priority(i) AND j uses a shared resource}
    # B1 = C2 = 4 (worst case: τ1 arrives just as τ2 starts using resource A)
    # B2 = 0 (no lower priority tasks)
    B1 = tasks[2]['computation']  # 4
    B2 = 0
    
    print(f"Blocking Times Analysis:")
    print(f"B1 = {B1} (τ1 can be blocked by τ2's entire execution when τ2 holds resource A)")
    print(f"B2 = {B2} (no lower priority tasks)")
    print()
    
    simulation_time = 35
    
    # Generate all job instances
    job_releases = {1: [], 2: []}
    for task_id in [1, 2]:
        period = tasks[task_id]['period']
        cpu_only = tasks[task_id]['computation'] - tasks[task_id]['resource_time']
        resource = tasks[task_id]['resource_time']
        
        job_num = 0
        t = 0
        while t < simulation_time:
            job_releases[task_id].append({
                'release': t,
                'deadline': t + period,
                'task_id': task_id,
                'cpu_only': cpu_only,
                'resource': resource,
                'job_num': job_num,
                'cpu_only_done': 0,
                'resource_done': 0
            })
            job_num += 1
            t += period
    
    # Simulation state
    ready_queue = []
    current_job = None
    in_critical_section = False
    time = 0
    
    # Results
    execution_segments = []
    events = []
    
    while time < simulation_time:
        # Release new jobs
        for task_id in [1, 2]:
            for job in job_releases[task_id]:
                if job['release'] == time:
                    ready_queue.append(job)
                    events.append((time, task_id, job['job_num'], 'release'))
        
        # Check if current job is complete
        if current_job and current_job['resource_done'] >= current_job['resource'] and \
           current_job['cpu_only_done'] >= current_job['cpu_only']:
            events.append((time, current_job['task_id'], current_job['job_num'], 'complete'))
            current_job = None
            in_critical_section = False
        
        # Select next job if none executing
        if current_job is None and ready_queue:
            # RM: Select highest priority (lowest period)
            ready_queue.sort(key=lambda j: tasks[j['task_id']]['priority'])
            current_job = ready_queue.pop(0)
            events.append((time, current_job['task_id'], current_job['job_num'], 'start'))
        
        # Execute current job
        if current_job:
            # PART C: Execute Resource A work first, then CPU-only work
            if current_job['resource_done'] < current_job['resource']:
                # Resource phase (critical section) - EXECUTE FIRST
                if not in_critical_section:
                    in_critical_section = True
                    events.append((time, current_job['task_id'], current_job['job_num'], 'lock'))
                    
                    # Check if higher priority jobs are waiting (blocking)
                    for waiting_job in ready_queue:
                        if tasks[waiting_job['task_id']]['priority'] < tasks[current_job['task_id']]['priority']:
                            events.append((time, waiting_job['task_id'], waiting_job['job_num'], 'blocked'))
                
                execution_segments.append((time, time + 1, current_job['task_id'], 
                                         current_job['job_num'], 'resource'))
                current_job['resource_done'] += 1
                
            elif current_job['cpu_only_done'] < current_job['cpu_only']:
                # CPU-only phase - EXECUTE SECOND
                # Release the resource after resource work completes
                if in_critical_section:
                    in_critical_section = False
                    events.append((time, current_job['task_id'], current_job['job_num'], 'release_resource'))
                
                execution_segments.append((time, time + 1, current_job['task_id'], 
                                         current_job['job_num'], 'cpu'))
                current_job['cpu_only_done'] += 1
        else:
            execution_segments.append((time, time + 1, 0, 0, 'idle'))
        
        time += 1
    
    return execution_segments, events, job_releases, B1, B2


def plot_schedule(execution_segments, job_releases, events, B1, B2):
    """
    Create a detailed Gantt chart showing the RM NPP schedule
    """
    fig, ax = plt.subplots(figsize=(20, 7))
    
    # Colors
    task1_cpu_color = '#90EE90'      # Light green
    task1_resource_color = '#FF6B6B'  # Red
    task2_cpu_color = '#87CEEB'       # Sky blue
    task2_resource_color = '#FFD700'  # Gold
    
    # Y-axis positions: Task 1 at top, Task 2 at bottom
    y_positions = {1: 2.5, 2: 1.0}
    bar_height = 0.6
    
    # Draw execution segments
    for start, end, task_id, job_num, seg_type in execution_segments:
        if task_id == 0:  # Skip idle
            continue
        
        y = y_positions[task_id]
        
        # Choose color and pattern
        if task_id == 1:
            color = task1_cpu_color if seg_type == 'cpu' else task1_resource_color
        else:
            color = task2_cpu_color if seg_type == 'cpu' else task2_resource_color
        
        hatch = '///' if seg_type == 'resource' else None
        
        # Draw rectangle
        rect = patches.Rectangle((start, y - bar_height/2), end - start, bar_height,
                                linewidth=1.5, edgecolor='black',
                                facecolor=color, hatch=hatch)
        ax.add_patch(rect)
        
        # Add text labels
        mid_x = (start + end) / 2
        if seg_type == 'resource':
            ax.text(mid_x, y, 'A', ha='center', va='center', 
                   fontsize=10, fontweight='bold', color='white')
        
        # Add time labels at boundaries
        if seg_type == 'cpu' or (seg_type == 'resource' and 
            not any(s[0] == start and s[2] == task_id and s[4] == 'resource' 
                   for s in execution_segments if s[0] < start)):
            # Start of job execution
            ax.text(start, y + 0.45, str(start), ha='center', va='bottom', 
                   fontsize=7, color='blue', fontweight='bold')
        
        # End time
        ax.text(end, y + 0.45, str(end), ha='center', va='bottom', 
               fontsize=7, color='blue', fontweight='bold')
    
    # Draw release times and deadlines
    for task_id in [1, 2]:
        y = y_positions[task_id]
        for job in job_releases[task_id]:
            # Release time (upward arrow)
            arrow_y_start = y - bar_height/2 - 0.3
            arrow_y_end = y - bar_height/2 - 0.05
            ax.annotate('', xy=(job['release'], arrow_y_end), 
                       xytext=(job['release'], arrow_y_start),
                       arrowprops=dict(arrowstyle='->', color='green', lw=2.5))
            ax.text(job['release'], arrow_y_start - 0.15, 'R', ha='center', va='top',
                   fontsize=8, color='green', fontweight='bold')
            
            # Deadline (downward arrow)  
            if job['deadline'] <= 35:
                arrow_y_start = y + bar_height/2 + 0.3
                arrow_y_end = y + bar_height/2 + 0.05
                ax.annotate('', xy=(job['deadline'], arrow_y_end),
                           xytext=(job['deadline'], arrow_y_start),
                           arrowprops=dict(arrowstyle='->', color='red', lw=2.5))
                ax.text(job['deadline'], arrow_y_start + 0.15, 'D', ha='center', va='bottom',
                       fontsize=8, color='red', fontweight='bold')
    
    # Highlight blocking instances
    blocking_times = [(e[0], e[1], e[2]) for e in events if e[3] == 'blocked']
    for time, task_id, job_num in blocking_times:
        y = y_positions[task_id]
        # Add a small blocking indicator
        ax.plot(time, y, 'rX', markersize=10, markeredgewidth=2, alpha=0.7)
    
    # Configure axes
    ax.set_xlim(-1, 36)
    ax.set_ylim(0, 3.5)
    ax.set_xlabel('Time (units)', fontsize=13, fontweight='bold')
    ax.set_ylabel('Tasks', fontsize=13, fontweight='bold')
    
    title_text = (f'RM Schedule with Non-Preemptive Protocol (PART C)\n'
                 f'τ₁: T=5, C=2, δ=1 (Resource A=1, then CPU=1) | '
                 f'τ₂: T=7, C=4, δ=3 (Resource A=3, then CPU=1)\n'
                 f'Blocking Times: B₁={B1}, B₂={B2}')
    ax.set_title(title_text, fontsize=13, fontweight='bold', pad=20)
    
    # Y-axis
    ax.set_yticks([1.0, 2.5])
    ax.set_yticklabels(['τ₂ (Priority=2, Lower)', 'τ₁ (Priority=1, Higher)'], fontsize=11)
    
    # X-axis
    ax.set_xticks(range(0, 36, 1))
    ax.set_xticklabels(range(0, 36, 1), fontsize=9)
    ax.grid(True, axis='x', alpha=0.4, linestyle='--', linewidth=0.5)
    ax.grid(True, axis='y', alpha=0.2, linestyle='-', linewidth=0.5)
    
    # Legend
    legend_elements = [
        patches.Patch(facecolor=task1_cpu_color, edgecolor='black', 
                     label='τ₁ CPU-only'),
        patches.Patch(facecolor=task1_resource_color, edgecolor='black', hatch='///',
                     label='τ₁ + Resource A'),
        patches.Patch(facecolor=task2_cpu_color, edgecolor='black',
                     label='τ₂ CPU-only'),
        patches.Patch(facecolor=task2_resource_color, edgecolor='black', hatch='///',
                     label='τ₂ + Resource A'),
        plt.Line2D([0], [0], marker='^', color='green', linestyle='None',
                   markersize=10, label='Release (R)', markeredgewidth=2),
        plt.Line2D([0], [0], marker='v', color='red', linestyle='None',
                   markersize=10, label='Deadline (D)', markeredgewidth=2),
        plt.Line2D([0], [0], marker='X', color='red', linestyle='None',
                   markersize=10, label='Blocking', markeredgewidth=2)
    ]
    ax.legend(handles=legend_elements, loc='upper left', fontsize=10, ncol=4,
             framealpha=0.95, edgecolor='black')
    
    # Add note about NPP and execution order
    note_text = ('PART C: Resource A work executed FIRST, then CPU-only work.\n'
                'Non-Preemptive Protocol: When a task holds Resource A,\n'
                'it cannot be preempted until resource work completes.')
    ax.text(0.98, 0.02, note_text, transform=ax.transAxes,
           fontsize=9, verticalalignment='bottom', horizontalalignment='right',
           bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))
    
    plt.tight_layout()
    plt.savefig('/Users/chrisrutherford/Downloads/Csc-358/HW/rm_npp_schedule_partC.png', 
               dpi=300, bbox_inches='tight')
    plt.show()
    
    print("\n✓ Schedule visualization saved as 'rm_npp_schedule_partC.png'")


def main():
    print("=" * 80)
    print("RM Scheduling with Non-Preemptive Protocol (NPP) - PART C")
    print("Task Set: τ1(T=5, C=2, δ=1), τ2(T=7, C=4, δ=3)")
    print("Execution Order: Resource A work FIRST, then CPU-only work")
    print("=" * 80)
    print()
    
    # Run simulation
    execution_segments, events, job_releases, B1, B2 = simulate_rm_npp_schedule()
    
    # Print detailed event log
    print("\nDetailed Schedule Events:")
    print("-" * 80)
    event_descriptions = {
        'release': 'Released',
        'start': 'Started execution',
        'lock': 'Acquired Resource A (enters critical section)',
        'release_resource': 'Released Resource A',
        'blocked': 'BLOCKED (waiting for resource)',
        'complete': 'Completed'
    }
    
    for time, task_id, job_num, event_type in events:
        desc = event_descriptions.get(event_type, event_type)
        print(f"t={time:2d}: τ{task_id} Job#{job_num} - {desc}")
    
    print("-" * 80)
    
    # Print summary statistics
    print("\nSchedule Summary:")
    print("-" * 80)
    
    # Count completions
    completions = {1: 0, 2: 0}
    for _, task_id, _, event_type in events:
        if event_type == 'complete':
            completions[task_id] += 1
    
    print(f"τ1 completed jobs: {completions[1]}")
    print(f"τ2 completed jobs: {completions[2]}")
    
    # Check for deadline misses
    for task_id in [1, 2]:
        for job in job_releases[task_id]:
            completion_time = None
            for time, tid, jnum, etype in events:
                if tid == task_id and jnum == job['job_num'] and etype == 'complete':
                    completion_time = time
                    break
            
            if completion_time and completion_time > job['deadline']:
                print(f"⚠ DEADLINE MISS: τ{task_id} Job#{job['job_num']} " + 
                     f"completed at {completion_time}, deadline was {job['deadline']}")
    
    print("-" * 80)
    
    # Create visualization
    plot_schedule(execution_segments, job_releases, events, B1, B2)


if __name__ == "__main__":
    main()
