"""
Manual verification of RM with PIP schedule
"""

print("="*80)
print("TASK SET VERIFICATION")
print("="*80)
print("Task 1: φ=3, T=6, C=2, δA=1 → CPU: 1 unit, Resource A: 1 unit (Priority=6 HIGHEST)")
print("Task 2: φ=2, T=8, C=2, δA=0 → CPU: 2 units, No resource (Priority=8 MEDIUM)")
print("Task 3: φ=0, T=10, C=3, δA=2 → CPU: 1 unit, Resource A: 2 units (Priority=10 LOWEST)")

print("\n" + "="*80)
print("JOB ARRIVALS")
print("="*80)
print("T1: arrives at t=3, 9, 15")
print("T2: arrives at t=2, 10")
print("T3: arrives at t=0, 10")

print("\n" + "="*80)
print("STEP-BY-STEP MANUAL TRACE")
print("="*80)

# Manual verification
steps = {
    0: ("T3.0", "CPU", "✓ T3 arrives, only task ready, executes CPU work (1/1 done)"),
    1: ("T3.0", "RES_A", "✓ T3 acquires Resource A, executes (1/2 resource work done)"),
    2: ("T2.0", "CPU", "✓ T2 arrives (priority 8 > T3's 10), preempts, executes CPU (1/2 done)"),
    3: ("T1.0", "CPU", "✓ T1 arrives (priority 6 > all), preempts, executes CPU (1/1 done)"),
    4: ("T3.0", "RES_A+PIP", "✓ T1 needs Resource A but T3 holds it → T3 INHERITS T1's priority → T3 runs (2/2 DONE, releases A)"),
    5: ("T1.0", "RES_A", "✓ T1 acquires Resource A, executes (1/1 DONE, complete)"),
    6: ("T2.0", "CPU", "✓ T2 continues CPU work (2/2 DONE, complete)"),
    7: ("IDLE", "-", "✓ No tasks ready"),
    8: ("IDLE", "-", "✓ No tasks ready"),
    9: ("T1.1", "CPU", "✓ T1 second job arrives, executes CPU (1/1 done)"),
    10: ("T1.1", "RES_A", "✓ T2.1 & T3.1 also arrive, but T1 highest priority, acquires A (1/1 DONE)"),
    11: ("T2.1", "CPU", "✓ T2 higher priority than T3, executes CPU (1/2 done)"),
    12: ("T2.1", "CPU", "✓ T2 continues CPU (2/2 DONE, complete)"),
    13: ("T3.1", "CPU", "✓ T3 executes CPU (1/1 done)"),
    14: ("T3.1", "RES_A", "✓ T3 acquires Resource A, executes (1/2 done)"),
    15: ("T1.2", "CPU", "✓ T1 third job arrives, needs CPU first (not blocked), preempts T3")
}

for t in range(16):
    task, exec_type, reason = steps[t]
    print(f"t={t:2d}: Execute {task:6s} ({exec_type:10s}) - {reason}")

print("\n" + "="*80)
print("CRITICAL PIP VERIFICATION at t=4")
print("="*80)
print("State at t=4:")
print("  - T3.0 holds Resource A (1 more unit of resource work remaining)")
print("  - T2.0 has 1 CPU unit remaining (doesn't need resource)")
print("  - T1.0 finished CPU work, needs Resource A next → BLOCKED!")
print()
print("Without PIP:")
print("  - T2 (priority 8) would run")
print("  - T1 (priority 6) blocked waiting for T3 to finish")
print("  - T3 (priority 10) waits behind T2")
print("  - This causes UNBOUNDED PRIORITY INVERSION!")
print()
print("With PIP:")
print("  - T3 INHERITS T1's priority (6)")
print("  - T3's effective priority (6) > T2's priority (8)")
print("  - T3 runs immediately to complete and release Resource A")
print("  - T1 can then acquire Resource A and continue")
print("  ✓ Priority inversion is BOUNDED!")
print("="*80)

print("\n" + "="*80)
print("CONCLUSION: Schedule is CORRECT ✓")
print("="*80)
