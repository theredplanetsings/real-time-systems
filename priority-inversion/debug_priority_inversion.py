"""
Debug version to trace τ1 execution
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
        
    @property
    def is_complete(self):
        return self.remaining_cpu_only == 0 and self.remaining_resource_a == 0
    
    def __repr__(self):
        return f"{self.task}.{self.job_number}(CPU:{self.remaining_cpu_only},A:{self.remaining_resource_a})"

tasks = [
    Task(task_id=1, phase=3, period=10, computation_time=3, resource_a_time=2),
    Task(task_id=2, phase=5, period=15, computation_time=7, resource_a_time=2),
    Task(task_id=3, phase=0, period=20, computation_time=10, resource_a_time=8),
]

# Generate all jobs
end_time = 30
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
job_index = 0

print("Tracing τ1 jobs:\n")

for t in range(30):
    # Release new jobs
    while job_index < len(all_jobs) and all_jobs[job_index][0] == t:
        job = all_jobs[job_index][1]
        ready_queue.append(job)
        if job.task.task_id == 1:
            print(f"t={t}: τ1.{job.job_number} arrives (CPU:{job.remaining_cpu_only}, A:{job.remaining_resource_a})")
        job_index += 1
    
    # Add current job back if not complete
    if current_job and not current_job.is_complete:
        ready_queue.append(current_job)
        current_job = None
    
    # Select highest priority job
    if ready_queue:
        ready_queue.sort(key=lambda j: j.task.priority)
        current_job = ready_queue.pop(0)
    
    # Execute
    if current_job:
        exec_type = None
        
        if current_job.remaining_cpu_only > 0:
            current_job.remaining_cpu_only -= 1
            exec_type = 'cpu'
            if current_job.task.task_id == 1:
                print(f"t={t}: {current_job} executes CPU-only (remaining CPU:{current_job.remaining_cpu_only})")
                
        elif current_job.remaining_resource_a > 0:
            if resource_a_holder is None:
                resource_a_holder = current_job
                current_job.holding_resource_a = True
                if current_job.task.task_id == 1:
                    print(f"t={t}: {current_job} acquires Resource A")
            
            if current_job.holding_resource_a:
                current_job.remaining_resource_a -= 1
                exec_type = 'resource_a'
                if current_job.task.task_id == 1:
                    print(f"t={t}: {current_job} uses Resource A (remaining A:{current_job.remaining_resource_a})")
                
                if current_job.remaining_resource_a == 0:
                    resource_a_holder = None
                    current_job.holding_resource_a = False
                    if current_job.task.task_id == 1:
                        print(f"t={t}: {current_job} releases Resource A and completes!")
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
                        exec_type = 'resource_a'
                        if current_job.remaining_resource_a == 0:
                            resource_a_holder = None
                            current_job.holding_resource_a = False
                else:
                    current_job = None
        
        # Check if τ1 is blocked
        if current_job and current_job.task.task_id != 1:
            for job in ready_queue:
                if job.task.task_id == 1:
                    print(f"t={t}: {job} is in ready_queue (blocked), while {current_job.task} executes")
                    break
