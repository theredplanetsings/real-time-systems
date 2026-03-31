"""
Part B: Task Priorities at t=4, t=6, and t=8 under DM with PIP
"""

print("="*90)
print("PART B: PRIORITIES AT SPECIFIC TIME POINTS")
print("="*90)

print("\nBaseline Priorities (DM - lower number = higher priority):")
print("  T1: 4  (Highest)")
print("  T3: 10")
print("  T2: 12")
print("  T4: 14 (Lowest)")

print("\n" + "="*90)
print("AT t = 4")
print("="*90)

print("\nSchedule context:")
print("  t=0: T4 starts Resource B (1/3)")
print("  t=1: T2 preempts, does CPU (1/1 done)")
print("  t=2: T2 acquires Resource A (1/3)")
print("  t=3: T3 preempts, does CPU (1/2)")
print("  t=4: T3 continues CPU (2/2 done) ← WE ARE HERE")

print("\nTask States at t=4:")
print("  T1: Not yet arrived (arrives at t=7)")
print("  T2: Ready - finished CPU work, holding Resource A, needs 2 more ResA units")
print("  T3: Executing - doing CPU work (will need ResB next)")
print("  T4: Ready - holding Resource B, needs 2 more ResB units")

print("\nPriorities at t=4:")
print("  T1: N/A (not arrived)")
print("  T2: 12 (baseline) - No inheritance")
print("  T3: 10 (baseline) - No inheritance (currently executing)")
print("  T4: 14 (baseline) - No inheritance yet")

print("\nNote: No inheritance at t=4 because:")
print("  - T3 is still doing CPU work, hasn't requested ResB yet")
print("  - No higher-priority task is blocked by a lower-priority resource holder")

print("\n" + "="*90)
print("AT t = 6")
print("="*90)

print("\nSchedule context:")
print("  t=5: T4 using Resource B (INHERITED) - T3 blocked on ResB")
print("  t=6: T4 using Resource B (still inherited, finishing up) ← WE ARE HERE")

print("\nTask States at t=6:")
print("  T1: Not yet arrived (arrives at t=7)")
print("  T2: Ready - holding Resource A, needs 1 more ResA unit")
print("  T3: Blocked - waiting for Resource B (which T4 holds)")
print("  T4: Executing - holding Resource B, will complete this time unit")

print("\nPriorities at t=6:")
print("  T1: N/A (not arrived)")
print("  T2: 12 (baseline) - No inheritance")
print("  T3: 10 (baseline) - Waiting for ResB")
print("  T4: 10 (INHERITED from T3) - Inherited because T3 (priority 10) is blocked waiting for ResB")

print("\nExplanation:")
print("  T4 normally has priority 14 (lowest)")
print("  T3 (priority 10) needs ResB but T4 holds it → T3 is blocked")
print("  PIP: T4 inherits T3's priority → T4's effective priority becomes 10")
print("  T4(10) = T3(10) > T2(12), so T4 continues executing")

print("\n" + "="*90)
print("AT t = 8")
print("="*90)

print("\nSchedule context:")
print("  t=7: T1 arrives, T2 using Resource A (INHERITED) - T1 blocked on ResA")
print("  t=8: T2 using Resource A (still inherited, finishing up) ← WE ARE HERE")

print("\nTask States at t=8:")
print("  T1: Blocked - arrived at t=7, needs Resource A (which T2 holds)")
print("  T2: Executing - holding Resource A, will complete this time unit")
print("  T3: Ready - waiting to acquire Resource B (T4 released it at end of t=6)")
print("  T4: Complete (finished at end of t=6)")

print("\nPriorities at t=8:")
print("  T1: 4 (baseline) - Blocked waiting for ResA")
print("  T2: 4 (INHERITED from T1) - Inherited because T1 (priority 4) is blocked waiting for ResA")
print("  T3: 10 (baseline) - No inheritance")
print("  T4: N/A (job complete)")

print("\nExplanation:")
print("  T2 normally has priority 12")
print("  T1 (priority 4, highest) needs ResA but T2 holds it → T1 is blocked")
print("  PIP: T2 inherits T1's priority → T2's effective priority becomes 4")
print("  T2(4) > T3(10), so T2 continues executing")

print("\n" + "="*90)
print("SUMMARY TABLE")
print("="*90)

print("\n┌──────┬────────────┬────────────┬────────────┬────────────┐")
print("│ Time │    T1      │    T2      │    T3      │    T4      │")
print("├──────┼────────────┼────────────┼────────────┼────────────┤")
print("│ t=4  │ N/A        │ 12 (base)  │ 10 (base)  │ 14 (base)  │")
print("│      │ not yet    │            │ executing  │            │")
print("│      │ arrived    │            │            │            │")
print("├──────┼────────────┼────────────┼────────────┼────────────┤")
print("│ t=6  │ N/A        │ 12 (base)  │ 10 (base)  │ 10 (INH)   │")
print("│      │ not yet    │            │ blocked    │ executing  │")
print("│      │ arrived    │            │            │ from T3    │")
print("├──────┼────────────┼────────────┼────────────┼────────────┤")
print("│ t=8  │ 4 (base)   │ 4 (INH)    │ 10 (base)  │ N/A        │")
print("│      │ blocked    │ executing  │            │ complete   │")
print("│      │            │ from T1    │            │            │")
print("└──────┴────────────┴────────────┴────────────┴────────────┘")

print("\n(base) = Baseline priority")
print("(INH) = Inherited priority via PIP")
print("N/A = Task not present/arrived or already complete")
