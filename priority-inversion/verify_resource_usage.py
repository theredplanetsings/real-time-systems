"""
Detailed verification of Resource A usage for each job
"""

class Task:
    def __init__(self, task_id, phase, period, computation_time, resource_a_time):
        self.task_id = task_id
        self.phase = phase
        self.period = period
        self.computation_time = computation_time
        self.resource_a_time = resource_a_time
        self.cpu_only_time = computation_time - resource_a_time
        self.priority = period
        
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
        self.resource_a_used = 0  # Track how much Resource A this job has used
        
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
                    current_job.resource_a_used += 1
                    exec_type = 'resource_a'
                    
                    if current_job.remaining_resource_a == 0:
                        resource_a_holder = None
                        current_job.holding_resource_a = False
                        print(f"t={t}: {current_job} completes (used {current_job.resource_a_used} units of Resource A total)")
                else:
                    # Blocked
                    ready_queue.append(current_job)
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
                            current_job.resource_a_used += 1
                            exec_type = 'resource_a'
                            if current_job.remaining_resource_a == 0:
                                resource_a_holder = None
                                current_job.holding_resource_a = False
                                print(f"t={t}: {current_job} completes (used {current_job.resource_a_used} units of Resource A total)")
                    else:
                        exec_type = 'idle'
                        current_job = None
            
            if current_job and exec_type == 'resource_a':
                schedule.append({
                    'time': t,
                    'job': current_job,
                    'task_id': current_job.task.task_id,
                    'type': exec_type
                })
    
    return schedule

tasks = [
    Task(task_id=1, phase=5, period=10, computation_time=3, resource_a_time=2),
    Task(task_id=2, phase=3, period=15, computation_time=8, resource_a_time=2),
    Task(task_id=3, phase=0, period=20, computation_time=12, resource_a_time=10),
]

end_time = 35
print("Tracking Resource A usage by job:\n")
schedule = simulate_rm_no_pip(tasks, end_time)

print("\n\nResource A execution timeline:")
print("Time   Job")
print("-" * 20)
for entry in schedule:
    print(f"{entry['time']:<6} {entry['job']}")

print("\n\nVerifying t=28-33 (the 6 consecutive Resource A units):")
for t in range(28, 34):
    entries = [e for e in schedule if e['time'] == t]
    if entries:
        print(f"t={t}: {entries[0]['job']} uses Resource A")
