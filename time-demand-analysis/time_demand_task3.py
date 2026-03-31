import matplotlib.pyplot as plt
import numpy as np
import math

# Task set: (Period, Computation Time)
# Task 1: (8, 2) - highest priority
# Task 2: (17, 9)
# Task 3: (24, 4) - analyzing this task
# Task 4: (45, 2) - not included (lower priority)

T1, C1 = 8, 2
T2, C2 = 17, 9
T3, C3 = 24, 4

# Time demand function for Task 3:
# w_3(t) = ceil(t/T1)*C1 + ceil(t/T2)*C2 + ceil(t/T3)*C3
def time_demand(t):
    if t == 0:
        return 0
    return math.ceil(t / T1) * C1 + math.ceil(t / T2) * C2 + math.ceil(t / T3) * C3

# Calculate time demand for each time point
time_points = range(0, 48)
demands = [time_demand(t) for t in time_points]

# Find points where demand increases and identify which job(s) cause it
demand_changes = []
for t in range(1, 48):
    prev_demand = time_demand(t - 1) if t > 1 else 0
    curr_demand = time_demand(t)
    
    if curr_demand > prev_demand:
        jobs = []
        
        # Determine which task's ceiling function increased
        if t == 1:
            jobs.append("Task 1 job 1, Task 2 job 1, Task 3 job 1 (initial)")
        else:
            # Check Task 1: ceiling increases at t = k*T1 + 1 for k >= 1
            if (t - 1) % T1 == 0:
                job_num = (t - 1) // T1 + 1
                jobs.append(f"Task 1 job {job_num}")
            
            # Check Task 2: ceiling increases at t = k*T2 + 1 for k >= 1
            if (t - 1) % T2 == 0:
                job_num = (t - 1) // T2 + 1
                jobs.append(f"Task 2 job {job_num}")
            
            # Check Task 3: ceiling increases at t = k*T3 + 1 for k >= 1
            if (t - 1) % T3 == 0:
                job_num = (t - 1) // T3 + 1
                jobs.append(f"Task 3 job {job_num}")
        
        demand_changes.append((t, curr_demand, jobs))

# Find busy interval length (where w(t) = t)
busy_interval_length = None
for t in range(1, 48):
    w_t = time_demand(t)
    if w_t <= t:
        busy_interval_length = t
        break

print("Time Demand Analysis for Task 3")
print("=" * 60)
print(f"Task 1: T={T1}, C={C1} (Highest Priority)")
print(f"Task 2: T={T2}, C={C2}")
print(f"Task 3: T={T3}, C={C3} (Analyzing)")
print()

print("Time Demand Function: w_3(t) = ⌈t/8⌉×2 + ⌈t/17⌉×9 + ⌈t/24⌉×4")
print()

print("Demand Increases:")
print("-" * 60)
for t, demand, jobs in demand_changes:
    print(f"t={t:2d}: w(t)={demand:2d} - {', '.join(jobs)}")

print()
print(f"Busy Interval Length: {busy_interval_length}")
print()

# Verify the busy interval
if busy_interval_length:
    w_bi = time_demand(busy_interval_length)
    print(f"Verification: w({busy_interval_length}) = {w_bi}, t = {busy_interval_length}")
    print(f"Condition w(t) ≤ t satisfied: {w_bi} ≤ {busy_interval_length}")

# Create the graph
fig, ax = plt.subplots(figsize=(14, 8))

# Plot the time demand function (stepped)
ax.step(time_points, demands, where='post', linewidth=2, label='w₃(t) - Time Demand', color='blue')

# Plot the diagonal line y = t
ax.plot(time_points, time_points, 'r--', linewidth=1.5, label='t (available time)', alpha=0.7)

# Mark the busy interval
if busy_interval_length:
    ax.axvline(x=busy_interval_length, color='green', linestyle=':', linewidth=2, 
               label=f'Busy Interval End (t={busy_interval_length})')
    ax.plot(busy_interval_length, busy_interval_length, 'go', markersize=10, 
            markeredgewidth=2, markerfacecolor='lightgreen')

# Annotate key points where demand increases
annotation_offset = 0
for i, (t, demand, jobs) in enumerate(demand_changes):
    if t <= 47:
        # Alternate annotation positions to avoid overlap
        if i % 3 == 0:
            xytext = (10, 15)
        elif i % 3 == 1:
            xytext = (10, -25)
        else:
            xytext = (-40, 15)
        
        # Annotate all demand change points
        job_text = ', '.join(jobs) if isinstance(jobs, list) else jobs
        ax.annotate(f't={t}\n{job_text}', 
                   xy=(t, demand), 
                   xytext=xytext,
                   textcoords='offset points',
                   fontsize=7,
                   bbox=dict(boxstyle='round,pad=0.3', facecolor='yellow', alpha=0.7),
                       arrowprops=dict(arrowstyle='->', connectionstyle='arc3,rad=0', 
                                     color='black', lw=0.5))

# Add grid
ax.grid(True, alpha=0.3, linestyle='--')

# Labels and title
ax.set_xlabel('Time (t)', fontsize=12, fontweight='bold')
ax.set_ylabel('Demand w₃(t)', fontsize=12, fontweight='bold')
ax.set_title('Time Demand Analysis for Task 3\n(Including Task 3 and Higher Priority Tasks 1 & 2)', 
             fontsize=14, fontweight='bold')

# Set axis limits
ax.set_xlim(0, 47)
ax.set_ylim(0, max(max(demands), 47) + 5)

# Set tick marks at every integer
ax.set_xticks(range(0, 48))
ax.set_yticks(range(0, max(max(demands), 47) + 6))

# Add legend
ax.legend(loc='upper left', fontsize=10)

# Add text box with task information
task_info = f"Task 1: (T={T1}, C={C1})\nTask 2: (T={T2}, C={C2})\nTask 3: (T={T3}, C={C3})"
ax.text(0.98, 0.5, task_info, transform=ax.transAxes,
        fontsize=10, verticalalignment='center', horizontalalignment='right',
        bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8))

plt.tight_layout()
plt.savefig('/Users/chrisrutherford/Downloads/Csc-358/HW/time_demand_task3_graph.png', dpi=300, bbox_inches='tight')
print("\nGraph saved as 'time_demand_task3_graph.png'")
plt.show()
